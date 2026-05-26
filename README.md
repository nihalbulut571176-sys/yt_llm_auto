# yt_llm_auto

Clean-room YouTube documentary visual pipeline focused on two redesigned first stages:

1. precise audio alignment with local word timestamps
2. semantic scene analysis through an LLM

The old repository remains a reference only. This repository starts from a clean architecture with small, testable modules.

## Current Scope

- local alignment via `faster-whisper` or `openai-whisper`
- normalized word and segment timeline export
- visual beat extraction from aligned speech
- LLM-ready semantic analysis stage with an OpenAI-compatible interface
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
python scripts/semantic_analyze.py --alignment-json ".\outputs\demo\alignment.json" --output-dir ".\outputs\demo" --dry-run
```

## Layout

```text
docs/
scripts/
src/yt_llm_auto/
tests/
```

## Notes

- FastGen image generation is intentionally not reimplemented first here.
- Public FastGen pricing currently shows `200,000 prompt-generation tokens/hour`, but public text-generation API docs were not clearly discoverable during this pass, so the semantic LLM layer is provider-configurable instead of hard-coupled to FastGen.
