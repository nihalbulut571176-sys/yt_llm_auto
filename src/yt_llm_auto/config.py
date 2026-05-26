from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def load_dotenv(dotenv_path: Path | None = None) -> None:
    path = dotenv_path or Path(".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(slots=True)
class AlignmentSettings:
    engine: str = "faster_whisper"
    model: str = "small"
    language: str = "ru"
    device: str = "cpu"
    compute_type: str = "int8"
    vad_filter: bool = True
    word_timestamps: bool = True


@dataclass(slots=True)
class SemanticLLMSettings:
    provider: str = "fastgen_prompts_v5"
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    endpoint: str = "/responses"
    model: str = "gpt-4.1-mini"
    fastgen_prompt_route: str = "/api/v5/prompts/generate"
    fastgen_chat_route: str = "/v1/chat/completions"


def load_alignment_settings() -> AlignmentSettings:
    load_dotenv()
    return AlignmentSettings(
        engine=os.getenv("DEFAULT_ALIGNMENT_ENGINE", "faster_whisper"),
        model=os.getenv("DEFAULT_ALIGNMENT_MODEL", "small"),
        language=os.getenv("DEFAULT_ALIGNMENT_LANGUAGE", "ru"),
    )


def load_semantic_llm_settings() -> SemanticLLMSettings:
    load_dotenv()
    provider = os.getenv("SEMANTIC_LLM_PROVIDER", "fastgen_prompts_v5")
    api_key = os.getenv("SEMANTIC_LLM_API_KEY")
    base_url = os.getenv("SEMANTIC_LLM_BASE_URL", "https://api.openai.com/v1")

    if provider in {"fastgen_prompts_v5", "fastgen_openai_chat"}:
        api_key = os.getenv("FAST_GEN_API_KEY") or api_key
        base_url = os.getenv("FAST_GEN_BASE_URL", "https://googler.fast-gen.ai")

    return SemanticLLMSettings(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        endpoint=os.getenv("SEMANTIC_LLM_ENDPOINT", "/responses"),
        model=os.getenv("FASTGEN_CHAT_MODEL", os.getenv("SEMANTIC_LLM_MODEL", "gpt-4.1-mini")),
        fastgen_prompt_route=os.getenv("FAST_GEN_PROMPT_ROUTE", "/api/v5/prompts/generate"),
        fastgen_chat_route=os.getenv("FAST_GEN_CHAT_ROUTE", "/v1/chat/completions"),
    )
