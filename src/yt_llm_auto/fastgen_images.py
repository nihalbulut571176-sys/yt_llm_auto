from __future__ import annotations

from dataclasses import asdict
import base64
import json
from pathlib import Path
import time
import urllib.request
from typing import Any

from yt_llm_auto.config import load_dotenv
from yt_llm_auto.models import GeneratedImageRecord, SemanticBeatPlan


def _request_json(url: str, method: str = "GET", headers: dict[str, str] | None = None, data: bytes | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {}, data=data, method=method)
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def _request_json_with_retries(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    attempts: int = 3,
    sleep_seconds: float = 5.0,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _request_json(url=url, method=method, headers=headers, data=data)
        except Exception as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(sleep_seconds * attempt)
    assert last_error is not None
    raise last_error


def load_fastgen_env(project_root: Path) -> tuple[str, str]:
    load_dotenv(project_root / ".env")
    import os

    api_key = os.getenv("FAST_GEN_API_KEY", "").strip()
    base_url = os.getenv("FAST_GEN_BASE_URL", "https://googler.fast-gen.ai").strip().rstrip("/")
    if not api_key:
        raise RuntimeError("FAST_GEN_API_KEY not found in .env")
    return api_key, base_url


def load_semantic_plan(path: Path) -> list[SemanticBeatPlan]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [SemanticBeatPlan(**item) for item in payload]


def compose_image_prompt(item: SemanticBeatPlan) -> str:
    return "\n".join(
        [
            "Create a premium cinematic documentary still in 16:9.",
            "",
            f"Scene meaning: {item.meaning}",
            f"Visual function: {item.visual_function}",
            f"Viewer emotion: {item.viewer_emotion}",
            f"Visual strategy: {item.visual_strategy}",
            f"Shot type: {item.shot_type}",
            f"Environment: {item.environment}",
            f"Prompt seed: {item.prompt_seed}",
            f"Narration context: {item.voiceover_excerpt}",
            "",
            "Style: photorealistic, premium cinematic documentary, realistic lens perspective, natural imperfections, layered depth, no text, no watermark.",
            "Restrictions: no subtitles, no fake UI, no visible captions, no generic stock photo aesthetic, no distorted anatomy, no plastic skin.",
        ]
    )


def compose_policy_safe_prompt(item: SemanticBeatPlan) -> str:
    return "\n".join(
        [
            "Create a premium cinematic documentary still in 16:9.",
            "",
            f"Scene meaning: Show the investigative aftermath and immediate evidence of {item.meaning.lower()} without depicting the harmful act itself.",
            "Visual function: documentary evidence and immediate consequence, not instructional action.",
            f"Viewer emotion: {item.viewer_emotion}",
            "Visual strategy: focus on aftermath, open display, shocked stillness, surveillance perspective, reflective surfaces, and missing-object evidence.",
            "Shot type: investigative close-up or controlled over-the-shoulder documentary frame.",
            f"Environment: {item.environment}",
            f"Prompt seed: {item.prompt_seed}, but framed as aftermath and evidence only.",
            f"Narration context: {item.voiceover_excerpt}",
            "",
            "Style: photorealistic, premium cinematic documentary, realistic lens perspective, natural imperfections, layered depth, no text, no watermark.",
            "Restrictions: no active assault, no weapon use, no harmful spray depiction, no step-by-step crime action, no subtitles, no fake UI, no visible captions, no generic stock photo aesthetic, no distorted anatomy, no plastic skin.",
        ]
    )


def create_image_operation(api_key: str, base_url: str, prompt: str, aspect_ratio: str = "16:9") -> dict[str, Any]:
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
    }
    return _request_json_with_retries(
        url=f"{base_url}/api/v4/openai/image/generate",
        method="POST",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
    )


def get_operation_status(api_key: str, base_url: str, operation_id: str) -> dict[str, Any]:
    return _request_json_with_retries(
        url=f"{base_url}/api/v4/operations/{operation_id}",
        method="GET",
        headers={"X-API-Key": api_key},
    )


def wait_for_image_result(
    api_key: str,
    base_url: str,
    operation_id: str,
    poll_seconds: float = 3.0,
    max_polls: int = 120,
) -> dict[str, Any]:
    for _ in range(max_polls):
        status = get_operation_status(api_key, base_url, operation_id)
        if status["status"] == "success":
            return status
        if status["status"] == "error":
            raise RuntimeError(json.dumps(status, ensure_ascii=False))
        time.sleep(poll_seconds)
    raise TimeoutError(f"Image polling timed out: {operation_id}")


def write_data_uri_image(data_uri: str, target_path: Path) -> None:
    if not data_uri.startswith("data:image/"):
        raise ValueError("Expected image data URI in operation result")
    _, encoded = data_uri.split(",", 1)
    target_path.write_bytes(base64.b64decode(encoded))


def export_generation_logs(output_dir: Path, records: list[GeneratedImageRecord]) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "generation_manifest.json"
    jsonl_path = output_dir / "generation_log.jsonl"
    manifest_path.write_text(json.dumps([asdict(item) for item in records], ensure_ascii=False, indent=2), encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for item in records:
            handle.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
    return {
        "manifest_json": str(manifest_path),
        "log_jsonl": str(jsonl_path),
    }
