import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yt_llm_auto.fastgen_images import load_semantic_plan  # noqa: E402
from yt_llm_auto.preview_render import build_preview_timeline, mux_preview_video  # noqa: E402
from yt_llm_auto.run_layout import copy_if_missing, create_run_layout  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-audio", required=True)
    parser.add_argument("--source-alignment-dir", required=True)
    parser.add_argument("--source-semantic-plan", required=True)
    parser.add_argument("--source-semantic-trace", required=True)
    parser.add_argument("--source-images-dir", required=True)
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()

    runs_dir = ROOT / "runs"
    layout = create_run_layout(runs_dir, args.run_id)

    source_audio = Path(args.source_audio).resolve()
    source_alignment_dir = Path(args.source_alignment_dir).resolve()
    source_semantic_plan = Path(args.source_semantic_plan).resolve()
    source_semantic_trace = Path(args.source_semantic_trace).resolve()
    source_images_dir = Path(args.source_images_dir).resolve()

    audio_target = layout.input_dir / "voiceover.mp3"
    copy_if_missing(source_audio, audio_target)

    for name in ["alignment.json", "segments.json", "words.json", "visual_beats.json", "subtitles.srt"]:
        copy_if_missing(source_alignment_dir / name, layout.alignment_dir / name)

    semantic_items = load_semantic_plan(source_semantic_plan)[: args.count]
    (layout.semantic_dir / "semantic_plan.json").write_text(
        json.dumps([asdict(item) for item in semantic_items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    copy_if_missing(source_semantic_trace, layout.semantic_dir / "semantic_llm_trace.json")

    for item in semantic_items:
        image_name = f"{item.beat_id}_V01.png"
        copy_if_missing(source_images_dir / image_name, layout.images_generated_dir / image_name)

    ffconcat_path = layout.render_dir / "preview_first10.ffconcat"
    timeline_path = layout.render_dir / "preview_first10_timeline.json"
    preview_path = layout.render_dir / "preview_first10.mp4"

    total_duration = build_preview_timeline(
        semantic_items=semantic_items,
        images_dir=layout.images_generated_dir,
        clip_dir=layout.render_clips_dir,
        ffconcat_path=ffconcat_path,
        timeline_path=timeline_path,
        fps=30,
    )
    mux_preview_video(
        ffconcat_path=ffconcat_path,
        audio_path=audio_target,
        output_path=preview_path,
        total_duration=total_duration,
    )

    print(str(layout.root))
    print(str(layout.images_generated_dir))
    print(str(preview_path))


if __name__ == "__main__":
    main()
