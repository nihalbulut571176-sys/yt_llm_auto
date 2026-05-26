import unittest

from yt_llm_auto.continuity import apply_continuity, infer_theme
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

    def test_apply_continuity_adds_recurring_profiles(self) -> None:
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
            )
        ]

        enriched, bundle = apply_continuity(plans, project_hint="Pink Panthers documentary")

        self.assertEqual(bundle["theme_hint"], "luxury_jewel_heist_documentary")
        self.assertIn("lead_operator", enriched[0].continuity_entity_ids)
        self.assertIn("support_operator", enriched[0].continuity_entity_ids)
        self.assertTrue(any("lead_operator:" in item for item in enriched[0].continuity_profiles))
        self.assertTrue(enriched[0].primary_subject)
        self.assertTrue(enriched[0].angle)


if __name__ == "__main__":
    unittest.main()
