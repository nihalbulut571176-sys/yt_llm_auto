from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from yt_llm_auto.models import SemanticBeatPlan


STYLE_SUMMARY = (
    "premium cinematic documentary still, photorealistic, realistic lens perspective, high detail, "
    "layered foreground and background storytelling, natural imperfections, motivated lighting, unified film look"
)

DEFAULT_RESTRICTIONS = [
    "no real-person names",
    "no text on image",
    "no subtitles",
    "no logos",
    "no watermark",
    "no fake UI",
    "no distorted hands",
    "no distorted anatomy",
    "no plastic skin",
    "no generic stock photo aesthetic",
    "no random replacement characters",
]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").replace("\n", " ")).strip()


def _profile_map(items: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {item["entity_id"]: item for item in items}


def infer_theme(project_hint: str, plans: list[SemanticBeatPlan]) -> str:
    blob = " ".join(
        [
            clean_text(project_hint).lower(),
            *[
                clean_text(" ".join([item.voiceover_excerpt, item.meaning, item.prompt_seed])).lower()
                for item in plans
            ],
        ]
    )
    if any(
        token in blob
        for token in (
            "panther",
            "розов",
            "jewel",
            "diamond",
            "boutique",
            "heist",
            "robbery",
            "tokyo",
            "бриллиант",
            "бутик",
            "колье",
        )
    ):
        return "luxury_jewel_heist_documentary"
    return "generic_documentary"


def jewel_heist_bundle() -> dict[str, Any]:
    return {
        "theme_hint": "luxury_jewel_heist_documentary",
        "continuity_world": (
            "A premium investigative documentary world built around luxury security, surveillance, glass reflections, "
            "disciplined architecture, and the human cost of a fast jewel theft."
        ),
        "continuity_rules": [
            "Repeat the same character and object descriptions verbatim whenever those entities return.",
            "Do not introduce random new faces if a recurring role already exists.",
            "Every prompt must include style, atmosphere, lighting, and angle.",
            "No visible text, logos, watermarks, or real-person names.",
        ],
        "recurring_motifs": [
            "glass reflections",
            "surveillance cameras",
            "silent luxury security systems",
            "investigative evidence fragments",
        ],
        "character_profiles": [
            {
                "entity_id": "lead_operator",
                "profile": "an anonymous Mediterranean-looking man in his late thirties, lean build, olive skin, short dark hair combed back, clean-shaven, calm expression, tailored charcoal suit, pale blue open-collar shirt, slim steel watch, black leather gloves when touching display surfaces",
            },
            {
                "entity_id": "support_operator",
                "profile": "an anonymous woman in her early thirties, slim athletic build, light olive skin, dark brown bob tucked behind one ear, composed expression, fitted ivory silk blouse under a camel tailored coat, narrow gold hoop earrings, thin black gloves when near the case",
            },
            {
                "entity_id": "boutique_attendant",
                "profile": "a boutique attendant in her late twenties, neat dark hair in a low bun, understated black uniform dress, white silk neck scarf, attentive professional posture, careful gloved handling near the jewelry case",
            },
            {
                "entity_id": "security_guard",
                "profile": "a security guard in his forties, broad build, shaved head, dark navy suit, coiled earpiece, alert posture, standing near entry chokepoints and camera sightlines",
            },
            {
                "entity_id": "investigator",
                "profile": "an anonymous investigator in neutral workwear, sleeves rolled, careful posture, handling evidence and route fragments without showing any readable text",
            },
        ],
        "object_profiles": [
            {
                "entity_id": "display_case",
                "profile": "a museum-grade jewelry vitrine with low-iron glass, brushed steel base, hidden magnetic lock, black velvet pedestal, immaculate reflections, no text labels",
            },
            {
                "entity_id": "signature_necklace",
                "profile": "a white-gold high-jewelry necklace with a massive clear central diamond, concentric rows of smaller diamonds, deep midnight velvet mount, museum-grade finish, no visible branding or text",
            },
            {
                "entity_id": "surveillance_network",
                "profile": "ceiling dome cameras, mirrored corner lenses, discreet sensors, brushed metal door hardware, silent luxury security infrastructure",
            },
            {
                "entity_id": "cream_jar_evidence",
                "profile": "an unbranded cream jar used as concealment evidence, matte lid, realistic cosmetic wear, a jewel compartment implied without readable packaging text",
            },
            {
                "entity_id": "route_fragments",
                "profile": "maps, transit fragments, architectural plans, and route traces arranged as cinematic evidence with no readable text",
            },
        ],
        "location_profiles": [
            {
                "entity_id": "tokyo_boutique",
                "profile": "a high-end Tokyo jewelry boutique with polished stone floors, smoked glass reflections, champagne metal frames, dark velvet display plinths, restrained warm luxury lighting, precise architectural symmetry",
            },
            {
                "entity_id": "boutique_threshold",
                "profile": "the boutique threshold and escape corridor just beyond the display floor, reflective stone, security hardware, compressed exit geometry, and the sense of delayed response",
            },
            {
                "entity_id": "tokyo_night_city",
                "profile": "Tokyo at night in 2004, layered expressways, sodium-lit facades, surveillance vantage points, humid urban air, and institutional scale without readable signage",
            },
            {
                "entity_id": "investigation_room",
                "profile": "a restrained investigative workspace with desk lamps, maps, route fragments, evidence trays, brushed metal surfaces, and no readable text",
            },
            {
                "entity_id": "evidence_table",
                "profile": "a forensic tabletop evidence setup with neutral surfaces, careful gloved handling, premium object detail, and no readable text or labels",
            },
            {
                "entity_id": "transnational_network_space",
                "profile": "a realistic transnational logistics and coordination environment combining transit fragments, anonymous operators, luggage traces, parked vehicles, and muted operational lighting without tutorial detail",
            },
        ],
    }


def generic_bundle() -> dict[str, Any]:
    return {
        "theme_hint": "generic_documentary",
        "continuity_world": (
            "A grounded documentary world with recurring people, objects, and locations that should stay visually stable "
            "from frame to frame."
        ),
        "continuity_rules": [
            "Repeat the same character and object descriptions verbatim whenever those entities return.",
            "Do not introduce random replacement people.",
            "Every prompt must include style, atmosphere, lighting, and angle.",
            "No visible text, logos, watermarks, or real-person names.",
        ],
        "recurring_motifs": [
            "layered foreground and background storytelling",
            "observational documentary realism",
            "coherent recurring locations",
        ],
        "character_profiles": [
            {
                "entity_id": "primary_subject",
                "profile": "an anonymous recurring documentary subject with consistent face shape, consistent hairstyle, grounded clothing, realistic posture, and no celebrity resemblance",
            }
        ],
        "object_profiles": [],
        "location_profiles": [
            {
                "entity_id": "primary_location",
                "profile": "a grounded real-world environment tied to the narration, realistic textures, motivated practical lighting, no visible text",
            }
        ],
    }


def _detect_flags(plan: SemanticBeatPlan) -> dict[str, bool]:
    lowered = clean_text(" ".join([plan.voiceover_excerpt, plan.meaning, plan.prompt_seed])).lower()
    return {
        "spray_attack": any(token in lowered for token in ["газ", "spray", "blinded", "mist", "ослеп"]),
        "open_case": any(token in lowered for token in ["витрина", "display case", "open case", "case open", "откры"]),
        "missing_jewel": any(token in lowered for token in ["колье", "necklace", "diamond", "missing", "исчез", "пропал"]),
        "operator_entry": any(token in lowered for token in ["entered", "двое", "pair", "operators", "клиент"]),
        "reaction_escape": any(token in lowered for token in ["too late", "trying to understand", "exit", "escape", "уходят", "слишком поздно"]),
        "historical_context": any(token in lowered for token in ["tokyo", "2004", "япони", "токио"]),
        "object_evidence": any(token in lowered for token in ["cream jar", "крем", "jar", "баноч"]),
        "network_scale": any(token in lowered for token in ["network", "балкан", "сеть", "transnational", "logistics"]),
        "investigation": any(token in lowered for token in ["investigation", "evidence", "investigator", "расслед", "доказатель"]),
        "security_system": any(token in lowered for token in ["security", "surveillance", "охрана", "камер"]),
    }


def _infer_shot_role(plan: SemanticBeatPlan) -> str:
    flags = _detect_flags(plan)
    if flags["spray_attack"]:
        return "assault_aftermath"
    if flags["open_case"] and flags["missing_jewel"]:
        return "empty_case_reveal"
    if flags["reaction_escape"]:
        return "operator_exit"
    if flags["historical_context"]:
        return "historical_context"
    if flags["object_evidence"]:
        return "object_evidence"
    if flags["network_scale"]:
        return "network_introduction"
    if flags["investigation"]:
        return "investigative_mechanism"
    if flags["operator_entry"]:
        return "operator_entry"
    if flags["security_system"]:
        return "security_system"
    if plan.visual_function == "hook":
        return "luxury_establishing"
    return "investigative_bridge"


def _blueprint_for_role(role: str) -> dict[str, str]:
    mapping = {
        "luxury_establishing": {
            "primary_subject": "the same protected luxury boutique environment centered on the display architecture and jewel-security system",
            "angle": "wide cinematic establishing angle",
            "lighting": "restrained warm luxury light with colder surveillance reflections",
            "atmosphere": "tense, polished, controlled",
        },
        "security_system": {
            "primary_subject": "the boutique security layer controlling access to the room",
            "angle": "high-angle documentary surveillance view",
            "lighting": "cold security light with reflective glass highlights",
            "atmosphere": "watchful, procedural, tense",
        },
        "operator_entry": {
            "primary_subject": "the same two operators moving through the boutique under surveillance",
            "angle": "over-the-shoulder documentary angle",
            "lighting": "mixed luxury interior light with cool reflected surveillance tones",
            "atmosphere": "composed, deceptive, controlled",
        },
        "assault_aftermath": {
            "primary_subject": "the boutique attendant reeling in the immediate aftermath while the same operators remain part of the space",
            "angle": "tight documentary reaction angle",
            "lighting": "hard boutique reflections with destabilized practical light",
            "atmosphere": "shocked, urgent, disorienting",
        },
        "empty_case_reveal": {
            "primary_subject": "the same display case now open with the necklace suddenly missing",
            "angle": "close-up evidence angle",
            "lighting": "sharp reflective showcase light with cold investigative spill",
            "atmosphere": "irreversible, alarming, forensic",
        },
        "operator_exit": {
            "primary_subject": "the same operators already slipping beyond the boutique while the reaction lags behind",
            "angle": "compressed exit-corridor documentary angle",
            "lighting": "cooler threshold light with boutique reflections dying behind them",
            "atmosphere": "efficient, cold, irreversible",
        },
        "historical_context": {
            "primary_subject": "Tokyo as a controlled night-time urban system connected to the heist",
            "angle": "wide elevated city documentary angle",
            "lighting": "night urban light with sodium and cool security tones",
            "atmosphere": "historical, analytical, tense",
        },
        "object_evidence": {
            "primary_subject": "a cream jar hiding a jewel as a concrete piece of criminal evidence",
            "angle": "macro forensic tabletop angle",
            "lighting": "soft top light with cool edge shadows and reflective highlights",
            "atmosphere": "forensic, surprising, precise",
        },
        "network_introduction": {
            "primary_subject": "a disciplined transnational organization expanding beyond a single robbery into a coordinated network",
            "angle": "medium-wide investigative ensemble angle",
            "lighting": "cold operational light with selective warm highlights",
            "atmosphere": "organized, transnational, controlled",
        },
        "investigative_mechanism": {
            "primary_subject": "the hidden operational mechanism behind the network and the slower institutional response",
            "angle": "over-the-shoulder investigative analysis angle",
            "lighting": "controlled desk light with cold ambient spill",
            "atmosphere": "analytical, uneasy, investigative",
        },
        "investigative_bridge": {
            "primary_subject": "a continuity-safe documentary bridge inside the same investigative world",
            "angle": "medium documentary transition angle",
            "lighting": "motivated continuity lighting",
            "atmosphere": "restrained, connective, secondary",
        },
    }
    return mapping[role]


def _active_entities_for_role(role: str, theme: str) -> tuple[list[str], str]:
    if theme != "luxury_jewel_heist_documentary":
        return ["primary_subject", "primary_location"], "preserve one coherent documentary world"

    active = ["surveillance_network"]
    focus = "preserve one coherent luxury-security world"
    if role in {"luxury_establishing", "security_system", "assault_aftermath", "empty_case_reveal"}:
        active.extend(["tokyo_boutique", "display_case"])
    if role in {"luxury_establishing", "empty_case_reveal"}:
        active.append("signature_necklace")
    if role in {"operator_entry", "assault_aftermath", "operator_exit", "network_introduction"}:
        active.extend(["lead_operator", "support_operator"])
    if role in {"assault_aftermath", "empty_case_reveal"}:
        active.append("boutique_attendant")
    if role in {"security_system", "historical_context"}:
        active.append("security_guard")
    if role == "historical_context":
        active.append("tokyo_night_city")
        focus = "shift from the boutique event to historical city context and institutional scale"
    if role in {"object_evidence"}:
        active.extend(["investigator", "cream_jar_evidence", "evidence_table"])
        focus = "hold object continuity and investigative realism rather than repeating boutique action"
    if role in {"investigative_mechanism", "investigative_bridge"}:
        active.extend(["investigator", "route_fragments", "investigation_room"])
        focus = "move from event imagery to evidence, routes, and investigative mechanism"
    if role == "network_introduction":
        active.extend(["route_fragments", "transnational_network_space"])
        focus = "expand from one robbery to a coordinated network without changing the recurring operators"
    if role == "operator_exit":
        active.append("boutique_threshold")
    return list(dict.fromkeys(active)), focus


def _resolve_environment(role: str, active_ids: list[str], location_map: dict[str, dict[str, str]], fallback: str) -> str:
    preferred_map = {
        "luxury_establishing": "tokyo_boutique",
        "security_system": "tokyo_boutique",
        "operator_entry": "tokyo_boutique",
        "assault_aftermath": "tokyo_boutique",
        "empty_case_reveal": "tokyo_boutique",
        "operator_exit": "boutique_threshold",
        "historical_context": "tokyo_night_city",
        "object_evidence": "evidence_table",
        "network_introduction": "transnational_network_space",
        "investigative_mechanism": "investigation_room",
        "investigative_bridge": "investigation_room",
    }
    preferred = preferred_map.get(role)
    if preferred and preferred in location_map:
        return location_map[preferred]["profile"]
    for entity_id in active_ids:
        if entity_id in location_map:
            return location_map[entity_id]["profile"]
    return fallback or "a grounded investigative documentary environment with no readable text"


def apply_continuity(plans: list[SemanticBeatPlan], project_hint: str = "") -> tuple[list[SemanticBeatPlan], dict[str, Any]]:
    theme = infer_theme(project_hint, plans)
    bundle = jewel_heist_bundle() if theme == "luxury_jewel_heist_documentary" else generic_bundle()
    char_map = _profile_map(bundle["character_profiles"])
    object_map = _profile_map(bundle["object_profiles"])
    location_map = _profile_map(bundle["location_profiles"])

    shot_roles: dict[str, str] = {}
    scene_entity_map: dict[str, Any] = {}

    for plan in plans:
        role = _infer_shot_role(plan)
        blueprint = _blueprint_for_role(role)
        active_ids, continuity_focus = _active_entities_for_role(role, theme)
        environment = _resolve_environment(role, active_ids, location_map, plan.environment)

        profiles: list[str] = []
        for entity_id in active_ids:
            if entity_id in char_map:
                profiles.append(f"{entity_id}: {char_map[entity_id]['profile']}")
            elif entity_id in object_map:
                profiles.append(f"{entity_id}: {object_map[entity_id]['profile']}")
            elif entity_id in location_map:
                profiles.append(f"{entity_id}: {location_map[entity_id]['profile']}")

        plan.primary_subject = plan.primary_subject or blueprint["primary_subject"]
        plan.angle = plan.angle or blueprint["angle"]
        plan.lighting = plan.lighting or blueprint["lighting"]
        plan.atmosphere = plan.atmosphere or blueprint["atmosphere"]
        plan.environment = environment
        plan.continuity_world = bundle["continuity_world"]
        plan.continuity_focus = continuity_focus
        plan.continuity_entity_ids = active_ids
        plan.continuity_profiles = profiles
        plan.style_summary = STYLE_SUMMARY
        plan.restrictions = list(DEFAULT_RESTRICTIONS)

        shot_roles[plan.beat_id] = role
        scene_entity_map[plan.beat_id] = {
            "active_entities": active_ids,
            "continuity_focus": continuity_focus,
        }

    return plans, {
        "theme_hint": bundle["theme_hint"],
        "continuity_world": bundle["continuity_world"],
        "continuity_rules": bundle["continuity_rules"],
        "recurring_motifs": bundle["recurring_motifs"],
        "character_profiles": bundle["character_profiles"],
        "object_profiles": bundle["object_profiles"],
        "location_profiles": bundle["location_profiles"],
        "shot_roles": shot_roles,
        "scene_entity_map": scene_entity_map,
        "style_summary": STYLE_SUMMARY,
        "default_restrictions": DEFAULT_RESTRICTIONS,
    }


def continuity_bundle_to_dict(bundle: dict[str, Any]) -> dict[str, Any]:
    serializable: dict[str, Any] = {}
    for key, value in bundle.items():
        if isinstance(value, list):
            serializable[key] = [asdict(item) if hasattr(item, "__dataclass_fields__") else item for item in value]
        else:
            serializable[key] = value
    return serializable
