import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yt_llm_auto.alignment import build_visual_beats, export_alignment_bundle, transcribe_audio
from yt_llm_auto.config import load_alignment_settings


def main() -> None:
    defaults = load_alignment_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--engine", default=defaults.engine, choices=["faster_whisper", "openai_whisper"])
    parser.add_argument("--model", default=defaults.model)
    parser.add_argument("--language", default=defaults.language)
    parser.add_argument("--device", default=defaults.device)
    parser.add_argument("--compute-type", default=defaults.compute_type)
    parser.add_argument("--min-beat-duration", type=float, default=5.0)
    parser.add_argument("--max-beat-duration", type=float, default=10.0)
    args = parser.parse_args()

    audio_path = Path(args.audio).resolve()
    output_dir = Path(args.output_dir).resolve()

    segments, meta = transcribe_audio(
        audio_path=audio_path,
        engine=args.engine,
        model_name=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
    )
    beats = build_visual_beats(
        segments=segments,
        min_duration=args.min_beat_duration,
        max_duration=args.max_beat_duration,
    )
    outputs = export_alignment_bundle(
        audio_path=audio_path,
        segments=segments,
        beats=beats,
        meta=meta,
        output_dir=output_dir,
    )

    for path in outputs.values():
        print(path)


if __name__ == "__main__":
    main()
