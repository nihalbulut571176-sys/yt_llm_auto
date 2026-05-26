# Alignment Options

## Bottom Line

For this project, the best first production path is:

1. `faster-whisper` with `word_timestamps=True` as the default local engine
2. `WhisperX` as the higher-accuracy optional upgrade path
3. keep forced-alignment tooling as a secondary track, not the first implementation target

## What Works Locally

### `faster-whisper`

- already installed on this machine
- supports local transcription
- supports `word_timestamps=True`
- practical for CPU-first development
- easy to integrate in Python

Weakness:

- timestamps are still Whisper-derived estimates, not a phoneme-level aligner

### `openai-whisper`

- also installed locally
- supports `word_timestamps=True`
- useful as a reference implementation

Weakness:

- slower than `faster-whisper` for local use
- word timings are still not the same as dedicated forced alignment

### `WhisperX`

- designed specifically for better word-level timestamps
- combines Whisper/faster-whisper ASR with wav2vec2 alignment
- better fit if we want more accurate scene boundaries and future diarization

Weakness:

- now installed in the local dev environment
- typically happier on Python 3.11/3.12 and often benefits from GPU
- heavier dependency chain than the baseline path

### Forced Alignment Libraries

Forced alignment means:

- you already have transcript text
- you align that text against audio more strictly than ordinary ASR
- output can be word or phone level timing

Two common directions:

- `Montreal Forced Aligner`
- `aeneas`

#### Montreal Forced Aligner

Pros:

- serious alignment tool
- better long-term candidate than `aeneas`

Cons:

- heavier setup
- separate acoustic/dictionary model workflow
- more ops overhead for a first clean-room repo

#### aeneas

Pros:

- simple idea
- historically used for text/audio synchronization

Cons:

- outdated installation experience
- weak first impression in local preflight
- less attractive as the default production path

## Recommendation

### Phase 1

Use `faster-whisper` locally with word timestamps and build the pipeline around its normalized output.

### Phase 2

Add `WhisperX` as an optional engine for projects that need tighter word boundaries.

### Phase 3

Only add classic forced alignment if we prove Whisper-based timing is not sufficient for our beat extraction quality target.
