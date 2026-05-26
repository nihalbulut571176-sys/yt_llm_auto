from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any
import urllib.request
import urllib.error

from yt_llm_auto.continuity import apply_continuity, continuity_bundle_to_dict
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
- primary_subject
- angle
- lighting
- atmosphere

Rules:
- Think like a premium documentary editor, not an object illustrator.
- Avoid generic stock-photo logic.
- Prefer mechanism, consequence, scale, evidence, or tension when appropriate.
- Keep prompt_seed concise but visually strong.
- Do not use real names or text-in-image ideas.
- If people recur across beats, keep them describable as the same recurring film characters.
- Return valid JSON only.
"""


def parse_json_loose(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Empty text where JSON was expected")
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


def build_continuity_prompt_context(bundle: dict[str, Any] | None) -> str:
    if not bundle:
        return ""
    lines = [
        f"Project continuity world: {bundle.get('continuity_world', '')}",
        f"Style summary: {bundle.get('style_summary', '')}",
    ]
    motifs = bundle.get("recurring_motifs", [])
    if motifs:
        lines.append("Recurring motifs: " + ", ".join(str(item) for item in motifs[:6]))
    rules = bundle.get("continuity_rules", [])
    if rules:
        lines.append("Continuity rules: " + " | ".join(str(item) for item in rules[:5]))
    chars = bundle.get("character_profiles", [])
    if chars:
        lines.append("Recurring characters:")
        for item in chars[:5]:
            lines.append(f"- {item.get('entity_id', '')}: {item.get('profile', '')}")
    objs = bundle.get("object_profiles", [])
    if objs:
        lines.append("Recurring objects:")
        for item in objs[:5]:
            lines.append(f"- {item.get('entity_id', '')}: {item.get('profile', '')}")
    locations = bundle.get("location_profiles", [])
    if locations:
        lines.append("Recurring locations:")
        for item in locations[:4]:
            lines.append(f"- {item.get('entity_id', '')}: {item.get('profile', '')}")
    return "\n".join(line for line in lines if line.strip())


def beat_to_user_prompt(
    beat: VisualBeat,
    previous_text: str = "",
    next_text: str = "",
    continuity_bundle: dict[str, Any] | None = None,
) -> str:
    context_lines = [
        f"Beat ID: {beat.beat_id}",
        f"Timing: {beat.start:.3f}-{beat.end:.3f}s",
        f"Duration: {beat.duration:.3f}s",
        f"Current narration: {beat.text}",
    ]
    continuity_context = build_continuity_prompt_context(continuity_bundle)
    if continuity_context:
        context_lines.append(continuity_context)
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

    def analyze(
        self,
        beat: VisualBeat,
        previous_text: str = "",
        next_text: str = "",
        continuity_bundle: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.endpoint}"
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": beat_to_user_prompt(beat, previous_text, next_text, continuity_bundle)},
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

    def analyze(
        self,
        beat: VisualBeat,
        previous_text: str = "",
        next_text: str = "",
        continuity_bundle: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.prompt_route}"
        prompt = "\n\n".join([SYSTEM_PROMPT, beat_to_user_prompt(beat, previous_text, next_text, continuity_bundle)])
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
            "parsed": parse_json_loose(raw["generated_text"]),
            "usage": raw.get("usage"),
        }


class FastGenOpenAIChatClient:
    def __init__(self, api_key: str, base_url: str, chat_route: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.chat_route = chat_route if chat_route.startswith("/") else f"/{chat_route}"
        self.model = model

    def analyze(
        self,
        beat: VisualBeat,
        previous_text: str = "",
        next_text: str = "",
        continuity_bundle: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{self.chat_route}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": beat_to_user_prompt(beat, previous_text, next_text, continuity_bundle)},
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
        return parse_json_loose(payload["output_text"])

    output = payload.get("output", [])
    for item in output:
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return parse_json_loose(content["text"])

    choices = payload.get("choices", [])
    if choices:
        text = choices[0].get("message", {}).get("content", "")
        if text:
            return parse_json_loose(text)

    raise ValueError("Could not parse JSON from provider response")


def build_semantic_plan(
    beats: list[VisualBeat],
    client: OpenAICompatibleClient | None = None,
    project_hint: str = "",
    continuity_bundle: dict[str, Any] | None = None,
) -> tuple[list[SemanticBeatPlan], list[dict[str, Any]], dict[str, Any]]:
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
                "primary_subject": "",
                "angle": "",
                "lighting": "",
                "atmosphere": "",
            }
            traces.append(
                {
                    "beat_id": beat.beat_id,
                    "mode": "dry_run",
                    "request_preview": beat_to_user_prompt(beat, previous_text, next_text, continuity_bundle),
                }
            )
        else:
            result = client.analyze(beat, previous_text, next_text, continuity_bundle)
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
                meaning=str(parsed.get("meaning", "")),
                viewer_emotion=str(parsed.get("viewer_emotion", "")),
                visual_function=str(parsed.get("visual_function", "")),
                visual_strategy=str(parsed.get("visual_strategy", "")),
                shot_type=str(parsed.get("shot_type", "")),
                environment=str(parsed.get("environment", "")),
                prompt_seed=str(parsed.get("prompt_seed", beat.text)),
                primary_subject=str(parsed.get("primary_subject", "")),
                angle=str(parsed.get("angle", "")),
                lighting=str(parsed.get("lighting", "")),
                atmosphere=str(parsed.get("atmosphere", "")),
            )
        )

    plans, resolved_continuity_bundle = apply_continuity(
        plans,
        project_hint=project_hint,
        generated_bundle=continuity_bundle,
    )
    return plans, traces, resolved_continuity_bundle


def export_semantic_bundle(
    plans: list[SemanticBeatPlan],
    traces: list[dict[str, Any]],
    continuity_bundle: dict[str, Any],
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    semantic_plan_path = output_dir / "semantic_plan.json"
    llm_trace_path = output_dir / "semantic_llm_trace.json"
    continuity_path = output_dir / "continuity_bundle.json"
    semantic_plan_path.write_text(json.dumps([asdict(item) for item in plans], ensure_ascii=False, indent=2), encoding="utf-8")
    llm_trace_path.write_text(json.dumps(traces, ensure_ascii=False, indent=2), encoding="utf-8")
    continuity_path.write_text(
        json.dumps(continuity_bundle_to_dict(continuity_bundle), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "semantic_plan_json": str(semantic_plan_path),
        "semantic_llm_trace_json": str(llm_trace_path),
        "continuity_bundle_json": str(continuity_path),
    }


def load_beats_from_alignment(alignment_json_path: Path) -> list[VisualBeat]:
    payload = json.loads(alignment_json_path.read_text(encoding="utf-8"))
    return [VisualBeat(**item) for item in payload.get("visual_beats", [])]
