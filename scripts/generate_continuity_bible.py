import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yt_llm_auto.config import load_semantic_llm_settings  # noqa: E402
from yt_llm_auto.continuity_bible import (  # noqa: E402
    export_continuity_bible,
    generate_continuity_bible,
    load_continuity_bible,
)
from yt_llm_auto.fastgen_images import load_semantic_plan  # noqa: E402
from yt_llm_auto.semantic_analysis import load_beats_from_alignment  # noqa: E402


def main() -> None:
    settings = load_semantic_llm_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--project-hint", default="")
    parser.add_argument("--alignment-json", default="")
    parser.add_argument("--semantic-plan", default="")
    parser.add_argument(
        "--provider",
        default=settings.provider,
        choices=["fastgen_prompts_v5", "fastgen_openai_chat", "openai_compatible"],
    )
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    existing_path = output_dir / "continuity_bible.json"
    if args.reuse_existing and existing_path.exists():
        print(str(existing_path))
        return

    if not settings.api_key:
        raise RuntimeError("SEMANTIC_LLM_API_KEY or FAST_GEN_API_KEY is required for continuity bible generation")

    beats = load_beats_from_alignment(Path(args.alignment_json).resolve()) if args.alignment_json else []
    semantic_plans = load_semantic_plan(Path(args.semantic_plan).resolve()) if args.semantic_plan else []

    bible, trace = generate_continuity_bible(
        settings=settings,
        provider=args.provider,
        project_hint=args.project_hint,
        beats=beats,
        semantic_plans=semantic_plans,
    )
    outputs = export_continuity_bible(output_dir, bible, trace)
    for path in outputs.values():
        print(path)


if __name__ == "__main__":
    main()
