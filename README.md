# yt_llm_auto

Clean-room YouTube documentary visual pipeline focused on two redesigned first stages:

1. precise audio alignment with local word timestamps
2. semantic scene analysis through an LLM

The old repository remains a reference only. This repository starts from a clean architecture with small, testable modules.

## Current Scope

- local alignment via `faster-whisper` or `openai-whisper`
- normalized word and segment timeline export
- visual beat extraction from aligned speech
- LLM-ready semantic analysis stage with FastGen prompt tokens or OpenAI-compatible chat
- optional LLM-generated `continuity_bible.json` for project-wide recurring cast and visual world
- Python orchestration layer that validates LLM-authored continuity and prompt outputs without taking over visual authorship
- FastGen image generation from semantic beats
- project docs for future FastGen image generation and final render integration

## Why This Repo Exists

The old pipeline proved that:

- FastGen image generation works
- FFmpeg slideshow assembly works

The weak points were earlier in the chain:

- alignment was segment-level, not word-level
- semantics were rule-based, not LLM-authored

This repo fixes those two stages first.

## Suggested Local Strategy

- Baseline local path: `faster-whisper` with `word_timestamps=True`
- Higher-accuracy optional path: `WhisperX`
- Avoid `aeneas` as the primary path unless we have a strong reason to support it

## Quick Start

1. Create `.env` from `.env.example`
2. Install the package in a virtual environment
3. Run alignment
4. Run semantic analysis

Example:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python scripts/align_audio.py --audio "C:\path\voiceover.mp3" --output-dir ".\outputs\demo"
python scripts/generate_continuity_bible.py --alignment-json ".\outputs\demo\alignment.json" --output-dir ".\outputs\demo" --project-hint "Pink Panthers documentary"
python scripts/semantic_analyze.py --alignment-json ".\outputs\demo\alignment.json" --output-dir ".\outputs\demo" --project-hint "Pink Panthers documentary" --continuity-bible ".\outputs\demo\continuity_bible.json"
python scripts/generate_images.py --semantic-plan ".\outputs\demo\semantic_plan.json" --output-dir ".\outputs\demo\images" --start 1 --end 2
```

## Layout

```text
docs/
runs/
scripts/
src/yt_llm_auto/
tests/
```

Production-style results should go into `runs/<run_id>/...`.
Use `outputs/` only for temporary scratch experiments.

Semantic analysis now exports:

- `continuity_bible.json` from the optional project-level LLM stage
- `continuity_bible_trace.json` from the optional project-level LLM stage
- `semantic_plan.json`
- `semantic_llm_trace.json`
- `continuity_bundle.json`

Each semantic beat is intended to be LLM-authored and may include:

- `active_entity_ids`
- `continuity_notes`
- `exact_image_prompt`

## Notes

- FastGen image generation is intentionally not reimplemented first here.
- FastGen docs expose both `POST /api/v5/prompts/generate` and `POST /v1/chat/completions`; both count against the prompt-token hourly limit.
