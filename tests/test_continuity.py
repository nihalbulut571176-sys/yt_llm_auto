import unittest

from yt_llm_auto.continuity import enrich_plans_from_bible, infer_theme
from yt_llm_auto.models import SemanticBeatPlan


class ContinuityTests(unittest.TestCase):
    def test_infers_pink_panthers_theme(self) -> None:
        plans = [
            SemanticBeatPlan(
                beat_id="B0001",
                start=0.0,
                end=5.0,
                duration=5.0,
                voiceover_excerpt="In Tokyo a diamond necklace vanished from the boutique.",
                meaning="A jewel heist in Tokyo",
                viewer_emotion="tension",
                visual_function="hook",
                visual_strategy="mechanism_view",
                shot_type="wide",
                environment="luxury boutique",
                prompt_seed="diamond necklace in a boutique",
            )
        ]
        self.assertEqual(infer_theme("Pink Panthers documentary", plans), "luxury_jewel_heist_documentary")

    def test_enrich_plans_from_bible_adds_recurring_profiles(self) -> None:
        plans = [
            SemanticBeatPlan(
                beat_id="B0001",
                start=0.0,
                end=5.0,
                duration=5.0,
                voiceover_excerpt="Two operators move through the boutique under surveillance.",
                meaning="Introduce the operators entering the boutique",
                viewer_emotion="tension",
                visual_function="hook",
                visual_strategy="human_consequence",
                shot_type="over-the-shoulder",
                environment="boutique interior",
                prompt_seed="two operators under surveillance",
                active_entity_ids=["lead_operator", "support_operator", "tokyo_boutique"],
            )
        ]

        bundle = {
            "theme_hint": "luxury_jewel_heist_documentary",
            "continuity_world": "A premium investigative documentary world.",
            "style_summary": "premium cinematic documentary",
            "character_profiles": [
                {"entity_id": "lead_operator", "profile": "the same calm man in a charcoal suit"},
                {"entity_id": "support_operator", "profile": "the same woman in a camel coat"},
            ],
            "object_profiles": [],
            "location_profiles": [
                {"entity_id": "tokyo_boutique", "profile": "the same high-end Tokyo jewelry boutique"},
            ],
            "default_restrictions": ["no text on image"],
        }
        enriched, bundle = enrich_plans_from_bible(plans, bundle, project_hint="Pink Panthers documentary")

        self.assertEqual(bundle["theme_hint"], "luxury_jewel_heist_documentary")
        self.assertIn("lead_operator", enriched[0].continuity_entity_ids)
        self.assertIn("support_operator", enriched[0].continuity_entity_ids)
        self.assertTrue(any("lead_operator:" in item for item in enriched[0].continuity_profiles))
        self.assertEqual(enriched[0].style_summary, "premium cinematic documentary")


if __name__ == "__main__":
    unittest.main()
