import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yt_llm_auto.config import load_semantic_llm_settings
from yt_llm_auto.semantic_analysis import (
    OpenAICompatibleClient,
    build_semantic_plan,
    export_semantic_bundle,
    load_beats_from_alignment,
)


def main() -> None:
    settings = load_semantic_llm_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--alignment-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    alignment_json = Path(args.alignment_json).resolve()
    output_dir = Path(args.output_dir).resolve()
    beats = load_beats_from_alignment(alignment_json)

    client = None
    if not args.dry_run:
        if not settings.api_key:
            raise RuntimeError("SEMANTIC_LLM_API_KEY is required for live semantic analysis")
        client = OpenAICompatibleClient(
            api_key=settings.api_key,
            base_url=settings.base_url,
            endpoint=settings.endpoint,
            model=settings.model,
        )

    plans, traces = build_semantic_plan(beats, client=client)
    outputs = export_semantic_bundle(plans, traces, output_dir)
    for path in outputs.values():
        print(path)


if __name__ == "__main__":
    main()
