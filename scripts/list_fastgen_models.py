import json
from pathlib import Path
import sys
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yt_llm_auto.config import load_dotenv  # noqa: E402


def main() -> None:
    load_dotenv(ROOT / ".env")
    import os

    api_key = os.getenv("FAST_GEN_API_KEY")
    base_url = os.getenv("FAST_GEN_BASE_URL", "https://googler.fast-gen.ai").rstrip("/")
    if not api_key:
        raise RuntimeError("FAST_GEN_API_KEY is required")

    request = urllib.request.Request(
        f"{base_url}/v1/models",
        headers={"X-API-Key": api_key},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))

    for model in payload.get("data", []):
        print(
            json.dumps(
                {
                    "id": model.get("id"),
                    "name": model.get("name"),
                    "owned_by": model.get("owned_by"),
                    "context_length": model.get("context_length"),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
