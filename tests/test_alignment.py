import unittest

from yt_llm_auto.alignment import build_visual_beats, format_srt_timestamp
from yt_llm_auto.models import SegmentAlignment


class AlignmentTests(unittest.TestCase):
    def test_format_srt_timestamp(self) -> None:
        self.assertEqual(format_srt_timestamp(65.432), "00:01:05,432")

    def test_build_visual_beats_respects_sentence_boundaries(self) -> None:
        segments = [
            SegmentAlignment(segment_id=1, start=0.0, end=2.0, text="First idea", words=[]),
            SegmentAlignment(segment_id=2, start=2.0, end=5.5, text="ends here.", words=[]),
            SegmentAlignment(segment_id=3, start=5.5, end=8.0, text="Second idea", words=[]),
            SegmentAlignment(segment_id=4, start=8.0, end=11.0, text="finishes now.", words=[]),
        ]

        beats = build_visual_beats(segments, min_duration=5.0, max_duration=10.0)

        self.assertEqual(len(beats), 2)
        self.assertEqual(beats[0].beat_id, "B0001")
        self.assertEqual(beats[0].source_segment_ids, [1, 2])
        self.assertEqual(beats[1].source_segment_ids, [3, 4])


if __name__ == "__main__":
    unittest.main()
