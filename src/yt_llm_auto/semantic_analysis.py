from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any
import urllib.request
import urllib.error

from yt_llm_auto.models import SemanticBeatPlan, VisualBeat


SYSTEM_PROMPT = """You are a documentary visual analyst.

For each beat, return a compact JSON object with these fields:
- meaning
- viewer_emotion
- visual_function
- visual_strategy
- shot_type
- environment
- prompt_seed

Rules:
- Think like a premium documentary editor, not an object illustrator.
- Avoid generic stock-photo logic.
- Prefer mechanism, consequence, scale, evidence, or tension when appropriate.
- Keep prompt_seed concise but visually strong.
- Return valid JSON only.
"""


def beat_to_user_prompt(beat: VisualBeat, previous_text: str = "", next_text: str = "") -> str:
    context_lines = [
        f"Beat ID: {beat.beat_id}",
        f"Timing: {beat.start:.3f}-{beat.end:.3f}s",
        f"Duration: {beat.duration:.3f}s",
        f"Current narration: {beat.text}",
    ]
    if previous_text:
        context_lines.append(f"Previous context: {previous_text}")
    if next_text:
        context_lines.append(f"Next context: {next_text}")
    context_lines.append("Respond with JSON only.")
    return "\n".join(context_lines)


class OpenAICompatibleClient:
    def __init__(self, api_key: str, base_url: str, endpoint: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        self.model = model

    def analyze(self, beat: VisualBeat, previous_text: str = "", next_text: str = "") -> dict[str, Any]:
        url = f"{self.base_url}{self.endpoint}"
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": beat_to_user_prompt(beat, previous_text, next_text)},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return {
            "request": payload,
            "response": raw,
            "parsed": parse_openai_compatible_response(raw),
        }


class FastGenPromptClient:
    def __init__(self, api_key: str, base_url: str, prompt_route: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.prompt_route = prompt_route if prompt_route.startswith("/") else f"/{prompt_route}"

    def analyze(self, beat: VisualBeat, previous_text: str = "", next_text: str = "") -> dict[str, Any]:
        url = f"{self.base_url}{self.prompt_route}"
        prompt = "\n\n".join([SYSTEM_PROMPT, beat_to_user_prompt(beat, previous_text, next_text)])
        payload = {"user_prompt": prompt}
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return {
            "request": payload,
            "response": raw,
            "parsed": json.loads(raw["generated_text"]),
            "usage": raw.get("usage"),
        }


class FastGenOpenAIChatClient:
    def __init__(self, api_key: str, base_url: str, chat_route: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chat_route = chat_route if chat_route.startswith("/") else f"/{chat_route}"
        self.model = model

    def analyze(self, beat: VisualBeat, previous_text: str = "", next_text: str = "") -> dict[str, Any]:
        url = f"{self.base_url}{self.chat_route}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": beat_to_user_prompt(beat, previous_text, next_text)},
            ],
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return {
            "request": payload,
            "response": raw,
            "parsed": parse_openai_compatible_response(raw),
            "usage": raw.get("usage"),
        }


def parse_openai_compatible_response(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return json.loads(payload["output_text"])

    output = payload.get("output", [])
    for item in output:
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return json.loads(content["text"])

    choices = payload.get("choices", [])
    if choices:
        text = choices[0].get("message", {}).get("content", "")
        if text:
            return json.loads(text)

    raise ValueError("Could not parse JSON from provider response")


def build_semantic_plan(
    beats: list[VisualBeat],
    client: OpenAICompatibleClient | None = None,
) -> tuple[list[SemanticBeatPlan], list[dict[str, Any]]]:
    plans: list[SemanticBeatPlan] = []
    traces: list[dict[str, Any]] = []

    for index, beat in enumerate(beats):
        previous_text = beats[index - 1].text if index > 0 else ""
        next_text = beats[index + 1].text if index + 1 < len(beats) else ""

        if client is None:
            parsed = {
                "meaning": "LLM call not executed yet",
                "viewer_emotion": "pending",
                "visual_function": "pending",
                "visual_strategy": "pending",
                "shot_type": "pending",
                "environment": "pending",
                "prompt_seed": beat.text,
            }
            traces.append(
                {
                    "beat_id": beat.beat_id,
                    "mode": "dry_run",
                    "request_preview": beat_to_user_prompt(beat, previous_text, next_text),
                }
            )
        else:
            result = client.analyze(beat, previous_text, next_text)
            parsed = result["parsed"]
            traces.append(
                {
                    "beat_id": beat.beat_id,
                    "mode": "live",
                    "request": result["request"],
                    "response": result["response"],
                    "usage": result.get("usage"),
                }
            )

        plans.append(
            SemanticBeatPlan(
                beat_id=beat.beat_id,
                start=beat.start,
                end=beat.end,
                duration=beat.duration,
                voiceover_excerpt=beat.text,
                meaning=str(parsed["meaning"]),
                viewer_emotion=str(parsed["viewer_emotion"]),
                visual_function=str(parsed["visual_function"]),
                visual_strategy=str(parsed["visual_strategy"]),
                shot_type=str(parsed["shot_type"]),
                environment=str(parsed["environment"]),
                prompt_seed=str(parsed["prompt_seed"]),
            )
        )

    return plans, traces


def export_semantic_bundle(
    plans: list[SemanticBeatPlan],
    traces: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    semantic_plan_path = output_dir / "semantic_plan.json"
    llm_trace_path = output_dir / "semantic_llm_trace.json"
    semantic_plan_path.write_text(json.dumps([asdict(item) for item in plans], ensure_ascii=False, indent=2), encoding="utf-8")
    llm_trace_path.write_text(json.dumps(traces, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "semantic_plan_json": str(semantic_plan_path),
        "semantic_llm_trace_json": str(llm_trace_path),
    }


def load_beats_from_alignment(alignment_json_path: Path) -> list[VisualBeat]:
    payload = json.loads(alignment_json_path.read_text(encoding="utf-8"))
    return [VisualBeat(**item) for item in payload.get("visual_beats", [])]
