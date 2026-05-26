# Architecture V2

## Goal

Redesign the first two stages of the documentary pipeline:

1. alignment
2. semantic analysis

Keep FastGen image generation and final render decoupled until the upstream timing and scene logic are trustworthy.

## Stage 1: Alignment

### Inputs

- `input/transcript.txt` or approved script
- `input/voiceover.mp3`

### Output

`alignment.json`

Contains:

- metadata
- segment-level timing
- word-level timing
- timing confidence notes
- a normalized text stream ready for beat extraction

### Default Engine

`faster-whisper`

### Optional Engines

- `openai-whisper`
- `whisperx`

## Stage 2: Beat Extraction

Turn aligned speech into 5-10 second visual beats using:

- punctuation boundaries
- silence boundaries when available
- max beat duration
- minimum duration guardrails

Output:

- `visual_beats.json`

## Stage 3: Semantic Analysis

Each beat is sent to an LLM-oriented scene authoring layer.

This stage should produce:

- meaning
- viewer emotion
- visual function
- visual strategy
- documentary visual direction
- prompt seed

Output:

- `semantic_plan.json`

## Why Separate Beat Extraction From LLM Analysis

- timing should not depend on the LLM
- beats need deterministic regeneration
- LLM retries should not force re-alignment

## Provider Strategy

The semantic module is provider-configurable and currently supports:

- FastGen V5 prompt generation
- FastGen OpenAI-compatible chat completions
- generic OpenAI-compatible chat

This is deliberate because:

- OpenAI has a stable official path
- FastGen image docs are known from the old repo
- public text-generation docs for FastGen were not clearly exposed during this pass

FastGen docs currently expose:

- `POST /api/v5/prompts/generate`
- `POST /v1/chat/completions`
- `GET /v1/models`

That lets us use FastGen prompt tokens directly for semantic authoring without changing beat extraction.
