# Run Layout

All production-style test runs should live under:

```text
runs/<run_id>/
  input/
    voiceover.mp3
  alignment/
    alignment.json
    segments.json
    words.json
    visual_beats.json
    subtitles.srt
  semantic/
    semantic_plan.json
    semantic_llm_trace.json
  images/
    generated/
      B0001_V01.png
      ...
    meta/
      B0001_V01.json
      ...
    generation_manifest.json
    generation_log.jsonl
  render/
    clips/
      B0001_V01.mp4
      ...
    preview_first10.ffconcat
    preview_first10_timeline.json
    preview_first10.mp4
  logs/
```

## Rule

Do not place real run outputs directly in `outputs/` anymore.

Use `outputs/` only for quick scratch experiments.
Use `runs/` for anything the user may want to keep, inspect, or build on.
