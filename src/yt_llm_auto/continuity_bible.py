from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import urllib.request

from yt_llm_auto.config import SemanticLLMSettings
from yt_llm_auto.continuity import DEFAULT_RESTRICTIONS, STYLE_SUMMARY, normalize_generated_bundle
from yt_llm_auto.models import SemanticBeatPlan, VisualBeat
from yt_llm_auto.semantic_analysis import parse_json_loose


WORLD_BIBLE_SYSTEM_PROMPT = """You are a documentary visual director.

Return valid JSON only with this exact compact structure:
{
  "project_hint": "string",
  "theme_hint": "string",
  "main_subject": "string",
  "subject_type": "string",
  "continuity_world": "string",
  "style_summary": "string",
  "prompt_language": "English",
  "recurring_motifs": ["string"],
  "continuity_rules": ["string"],
  "forbidden_mistakes": ["string"],
  "default_restrictions": ["string"]
}

Rules:
- Keep every string compact.
- theme_hint must be a machine-friendly slug like luxury_jewel_heist_documentary.
- recurring_motifs: 4 to 6 items.
- continuity_rules: 4 to 6 items.
- forbidden_mistakes: 4 to 6 items.
- No real-person names.
- No text inside images.
- Keep all free-text output in English.
"""

CHARACTER_BIBLE_SYSTEM_PROMPT = """You are a documentary visual continuity director.

Return valid JSON only with this exact structure:
{
  "character_profiles": [
    {
      "entity_id": "string",
      "role": "string",
      "profile": "string",
      "usage_notes": "string"
    }
  ]
}

Rules:
- character_profiles: at most 4 items.
- Keep every profile compact but visually repeatable.
- usage_notes must be short.
- No real-person names.
- Keep all free-text output in English.

If the story is a luxury jewel heist documentary, prefer exact ids like:
lead_operator, support_operator, boutique_attendant, security_guard, investigator.
"""

OBJECT_BIBLE_SYSTEM_PROMPT = """You are a documentary visual continuity director.

Return valid JSON only with this exact structure:
{
  "object_profiles": [
    {
      "entity_id": "string",
      "role": "string",
      "profile": "string",
      "usage_notes": "string"
    }
  ]
}

Rules:
- object_profiles: at most 5 items.
- Keep every profile compact but visually repeatable.
- usage_notes must be short.
- No readable brand names or text.
- Keep all free-text output in English.

If the story is a luxury jewel heist documentary, prefer exact ids like:
display_case, signature_necklace, surveillance_network, cream_jar_evidence, route_fragments.
"""

LOCATION_BIBLE_SYSTEM_PROMPT = """You are a documentary visual continuity director.

Return valid JSON only with this exact structure:
{
  "location_profiles": [
    {
      "entity_id": "string",
      "role": "string",
      "profile": "string",
      "usage_notes": "string"
    }
  ]
}

Rules:
- location_profiles: at most 4 items.
- Keep every profile compact but visually repeatable.
- usage_notes must be short.
- Keep all free-text output in English.

If the story is a luxury jewel heist documentary, prefer exact ids like:
tokyo_boutique, boutique_threshold, tokyo_night_city, investigation_room, evidence_table, transnational_network_space.
"""


def _request_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def _call_provider(settings: SemanticLLMSettings, system_prompt: str, user_prompt: str, provider: str) -> dict[str, Any]:
    if provider == "fastgen_prompts_v5":
        raw = _request_json(
            f"{settings.base_url.rstrip('/')}{settings.fastgen_prompt_route}",
            {"X-API-Key": settings.api_key or "", "Content-Type": "application/json"},
            {"user_prompt": f"{system_prompt}\n\n{user_prompt}"},
        )
        return {
            "request": {"user_prompt": f"{system_prompt}\n\n{user_prompt}"},
            "response": raw,
            "parsed": parse_json_loose(raw["generated_text"]),
            "usage": raw.get("usage"),
        }

    if provider == "fastgen_openai_chat":
        payload = {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        raw = _request_json(
            f"{settings.base_url.rstrip('/')}{settings.fastgen_chat_route}",
            {"X-API-Key": settings.api_key or "", "Content-Type": "application/json"},
            payload,
        )
        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"request": payload, "response": raw, "parsed": parse_json_loose(content), "usage": raw.get("usage")}

    payload = {
        "model": settings.model,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    raw = _request_json(
        f"{settings.base_url.rstrip('/')}{settings.endpoint}",
        {"Authorization": f"Bearer {settings.api_key or ''}", "Content-Type": "application/json"},
        payload,
    )
    output_text = raw.get("output_text")
    if not output_text:
        for item in raw.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    output_text = content["text"]
                    break
            if output_text:
                break
    return {"request": payload, "response": raw, "parsed": parse_json_loose(output_text or ""), "usage": raw.get("usage")}


def build_project_context_prompt(
    beats: list[VisualBeat] | None = None,
    semantic_plans: list[SemanticBeatPlan] | None = None,
    project_hint: str = "",
    max_items: int = 18,
    max_chars: int = 140,
) -> str:
    beats = beats or []
    semantic_plans = semantic_plans or []
    lines = [f"Project hint: {project_hint or 'Unknown documentary project'}"]
    if semantic_plans:
        lines.append("Beat summaries:")
        for item in semantic_plans[:max_items]:
            lines.append(f"- {item.beat_id}: meaning={item.meaning[:max_chars]} | excerpt={item.voiceover_excerpt[:max_chars]}")
    elif beats:
        lines.append("Narration beats:")
        for beat in beats[:max_items]:
            lines.append(f"- {beat.beat_id}: {beat.text[:max_chars]}")
    return "\n".join(lines)


def _build_world_prompt(
    beats: list[VisualBeat] | None = None,
    semantic_plans: list[SemanticBeatPlan] | None = None,
    project_hint: str = "",
) -> str:
    return build_project_context_prompt(
        beats=beats,
        semantic_plans=semantic_plans,
        project_hint=project_hint,
        max_items=16,
        max_chars=120,
    ) + "\nDefine the global documentary world, atmosphere, motifs, mistakes to avoid, and default restrictions."


def _build_entity_prompt(
    beats: list[VisualBeat] | None = None,
    semantic_plans: list[SemanticBeatPlan] | None = None,
    project_hint: str = "",
    world_bundle: dict[str, Any] | None = None,
    entity_kind: str = "characters",
) -> str:
    lines = [
        build_project_context_prompt(
            beats=beats,
            semantic_plans=semantic_plans,
            project_hint=project_hint,
            max_items=12,
            max_chars=100,
        )
    ]
    if world_bundle:
        lines.append(f"Theme hint: {world_bundle.get('theme_hint', '')}")
        lines.append(f"Continuity world: {world_bundle.get('continuity_world', '')}")
        motifs = world_bundle.get("recurring_motifs", [])
        if motifs:
            lines.append("Recurring motifs: " + ", ".join(str(item) for item in motifs[:5]))
    lines.append(f"Define only the recurring {entity_kind} that should stay visually identical across prompts.")
    return "\n".join(lines)


def generate_continuity_bible(
    settings: SemanticLLMSettings,
    provider: str,
    project_hint: str = "",
    beats: list[VisualBeat] | None = None,
    semantic_plans: list[SemanticBeatPlan] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    world_result = _call_provider(
        settings=settings,
        system_prompt=WORLD_BIBLE_SYSTEM_PROMPT,
        user_prompt=_build_world_prompt(beats=beats, semantic_plans=semantic_plans, project_hint=project_hint),
        provider=provider,
    )
    world_bundle = dict(world_result["parsed"])
    character_result = _call_provider(
        settings=settings,
        system_prompt=CHARACTER_BIBLE_SYSTEM_PROMPT,
        user_prompt=_build_entity_prompt(
            beats=beats,
            semantic_plans=semantic_plans,
            project_hint=project_hint,
            world_bundle=world_bundle,
            entity_kind="characters",
        ),
        provider=provider,
    )
    object_result = _call_provider(
        settings=settings,
        system_prompt=OBJECT_BIBLE_SYSTEM_PROMPT,
        user_prompt=_build_entity_prompt(
            beats=beats,
            semantic_plans=semantic_plans,
            project_hint=project_hint,
            world_bundle=world_bundle,
            entity_kind="objects",
        ),
        provider=provider,
    )
    location_result = _call_provider(
        settings=settings,
        system_prompt=LOCATION_BIBLE_SYSTEM_PROMPT,
        user_prompt=_build_entity_prompt(
            beats=beats,
            semantic_plans=semantic_plans,
            project_hint=project_hint,
            world_bundle=world_bundle,
            entity_kind="locations",
        ),
        provider=provider,
    )
    combined = normalize_generated_bundle(
        {
            "project_hint": project_hint,
            "theme_hint": world_bundle.get("theme_hint", "generic_documentary"),
            "main_subject": world_bundle.get("main_subject", ""),
            "subject_type": world_bundle.get("subject_type", ""),
            "continuity_world": world_bundle.get("continuity_world", ""),
            "style_summary": world_bundle.get("style_summary", STYLE_SUMMARY),
            "prompt_language": world_bundle.get("prompt_language", "English"),
            "recurring_motifs": world_bundle.get("recurring_motifs", []),
            "continuity_rules": world_bundle.get("continuity_rules", []),
            "forbidden_mistakes": world_bundle.get("forbidden_mistakes", []),
            "default_restrictions": world_bundle.get("default_restrictions", list(DEFAULT_RESTRICTIONS)),
            "character_profiles": character_result["parsed"].get("character_profiles", []),
            "object_profiles": object_result["parsed"].get("object_profiles", []),
            "location_profiles": location_result["parsed"].get("location_profiles", []),
        }
    )
    trace = {
        "world_stage": world_result,
        "character_stage": character_result,
        "object_stage": object_result,
        "location_stage": location_result,
    }
    return combined, trace


def load_continuity_bible(path: Path) -> dict[str, Any]:
    return normalize_generated_bundle(json.loads(path.read_text(encoding="utf-8")))


def export_continuity_bible(output_dir: Path, bible: dict[str, Any], trace: dict[str, Any]) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    bible_path = output_dir / "continuity_bible.json"
    trace_path = output_dir / "continuity_bible_trace.json"
    bible_path.write_text(json.dumps(bible, ensure_ascii=False, indent=2), encoding="utf-8")
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"continuity_bible_json": str(bible_path), "continuity_bible_trace_json": str(trace_path)}
