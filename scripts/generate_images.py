import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yt_llm_auto.fastgen_images import (  # noqa: E402
    compose_image_prompt,
    compose_policy_safe_prompt,
    create_image_operation,
    export_generation_logs,
    load_fastgen_env,
    load_semantic_plan,
    wait_for_image_result,
    write_data_uri_image,
)
from yt_llm_auto.models import GeneratedImageRecord  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic-plan", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=0)
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--poll-seconds", type=float, default=3.0)
    parser.add_argument("--max-polls", type=int, default=120)
    args = parser.parse_args()

    semantic_plan_path = Path(args.semantic_plan).resolve()
    output_dir = Path(args.output_dir).resolve()
    images_dir = output_dir / "images"
    meta_dir = output_dir / "meta"
    images_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    api_key, base_url = load_fastgen_env(ROOT)
    items = load_semantic_plan(semantic_plan_path)
    end = args.end if args.end > 0 else len(items)
    selected = items[args.start - 1 : end]

    records: list[GeneratedImageRecord] = []
    for index, item in enumerate(selected, start=args.start):
        image_id = f"{item.beat_id}_V01"
        image_path = images_dir / f"{image_id}.png"
        prompt = compose_image_prompt(item)

        try:
            active_prompt = prompt
            created = create_image_operation(
                api_key=api_key,
                base_url=base_url,
                prompt=active_prompt,
                aspect_ratio=args.aspect_ratio,
            )
            operation_id = created["operation_id"]
            try:
                status = wait_for_image_result(
                    api_key=api_key,
                    base_url=base_url,
                    operation_id=operation_id,
                    poll_seconds=args.poll_seconds,
                    max_polls=args.max_polls,
                )
            except Exception as exc:
                message = str(exc)
                if "content polic" not in message.lower():
                    raise
                active_prompt = compose_policy_safe_prompt(item)
                created = create_image_operation(
                    api_key=api_key,
                    base_url=base_url,
                    prompt=active_prompt,
                    aspect_ratio=args.aspect_ratio,
                )
                operation_id = created["operation_id"]
                status = wait_for_image_result(
                    api_key=api_key,
                    base_url=base_url,
                    operation_id=operation_id,
                    poll_seconds=args.poll_seconds,
                    max_polls=args.max_polls,
                )
            result = status.get("result") or []
            if not result:
                raise RuntimeError(f"No result returned for {operation_id}")
            write_data_uri_image(result[0], image_path)
            (meta_dir / f"{image_id}.json").write_text(
                __import__("json").dumps(
                    {
                        "beat_id": item.beat_id,
                        "image_id": image_id,
                        "operation_id": operation_id,
                        "status": status.get("status"),
                        "provider": status.get("provider"),
                        "model": status.get("model"),
                        "file_path": str(image_path),
                        "prompt": active_prompt,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            records.append(
                GeneratedImageRecord(
                    beat_id=item.beat_id,
                    image_id=image_id,
                    prompt=active_prompt,
                    aspect_ratio=args.aspect_ratio,
                    operation_id=operation_id,
                    status="generated",
                    file_path=str(image_path),
                )
            )
            print(str(image_path))
        except Exception as exc:
            records.append(
                GeneratedImageRecord(
                    beat_id=item.beat_id,
                    image_id=image_id,
                    prompt=prompt,
                    aspect_ratio=args.aspect_ratio,
                    operation_id=None,
                    status="failed",
                    file_path=None,
                    error=str(exc),
                )
            )
            print(f"FAILED {image_id}: {exc}")

    outputs = export_generation_logs(output_dir, records)
    for path in outputs.values():
        print(path)


if __name__ == "__main__":
    main()
