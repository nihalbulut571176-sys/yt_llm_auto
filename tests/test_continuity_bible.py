import unittest

from yt_llm_auto.continuity import apply_continuity
from yt_llm_auto.continuity_bible import build_project_context_prompt
from yt_llm_auto.models import SemanticBeatPlan, VisualBeat


class ContinuityBibleTests(unittest.TestCase):
    def test_build_project_context_prompt_includes_project_hint(self) -> None:
        beats = [VisualBeat(beat_id="B0001", start=0.0, end=4.0, duration=4.0, text="A diamond vanishes in Tokyo.", source_segment_ids=[1])]
        prompt = build_project_context_prompt(beats=beats, project_hint="Pink Panthers documentary")
        self.assertIn("Pink Panthers documentary", prompt)
        self.assertIn("B0001", prompt)

    def test_generated_bundle_overrides_profiles(self) -> None:
        plans = [
            SemanticBeatPlan(
                beat_id="B0001",
                start=0.0,
                end=5.0,
                duration=5.0,
                voiceover_excerpt="Two operators enter the boutique.",
                meaning="Operators enter",
                viewer_emotion="tension",
                visual_function="hook",
                visual_strategy="human_consequence",
                shot_type="medium",
                environment="boutique",
                prompt_seed="two operators under surveillance",
            )
        ]
        generated = {
            "theme_hint": "luxury_jewel_heist_documentary",
            "continuity_world": "A cold luxury-crime documentary world.",
            "style_summary": "premium documentary",
            "character_profiles": [
                {"entity_id": "lead_operator", "role": "lead", "profile": "the same calm man in charcoal suit", "usage_notes": ""},
                {"entity_id": "support_operator", "role": "support", "profile": "the same woman in camel coat", "usage_notes": ""},
            ],
            "object_profiles": [],
            "location_profiles": [
                {"entity_id": "tokyo_boutique", "role": "boutique", "profile": "the same Tokyo boutique", "usage_notes": ""}
            ],
            "continuity_rules": ["repeat recurring cast verbatim"],
            "recurring_motifs": ["glass reflections"],
            "default_restrictions": ["no text on image"],
        }
        enriched, bundle = apply_continuity(plans, project_hint="Pink Panthers documentary", generated_bundle=generated)
        self.assertEqual(bundle["continuity_world"], "A cold luxury-crime documentary world.")
        self.assertIn("lead_operator", enriched[0].continuity_entity_ids)
        self.assertTrue(any("the same calm man in charcoal suit" in item for item in enriched[0].continuity_profiles))


if __name__ == "__main__":
    unittest.main()
