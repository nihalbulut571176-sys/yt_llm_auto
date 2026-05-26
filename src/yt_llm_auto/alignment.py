from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
from typing import Any

from yt_llm_auto.models import SegmentAlignment, VisualBeat, WordAlignment


SENTENCE_END_RE = re.compile(r'[.!?…]["\')\]]?$')


def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def write_srt(segments: list[SegmentAlignment], output_path: Path) -> None:
    lines: list[str] = []
    for segment in segments:
        lines.extend(
            [
                str(segment.segment_id),
                f"{format_srt_timestamp(segment.start)} --> {format_srt_timestamp(segment.end)}",
                segment.text.strip(),
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\n", " ")).strip()


def transcribe_with_faster_whisper(
    audio_path: Path,
    model_name: str,
    language: str,
    device: str,
    compute_type: str,
    vad_filter: bool,
) -> tuple[list[SegmentAlignment], dict[str, Any]]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=vad_filter,
        word_timestamps=True,
    )

    segments: list[SegmentAlignment] = []
    for segment in segments_iter:
        words = [
            WordAlignment(
                word=(item.word or "").strip(),
                start=float(item.start),
                end=float(item.end),
                probability=float(item.probability) if item.probability is not None else None,
            )
            for item in (segment.words or [])
            if (item.word or "").strip()
        ]
        segments.append(
            SegmentAlignment(
                segment_id=int(segment.id) + 1,
                start=float(segment.start),
                end=float(segment.end),
                text=_normalize_text(segment.text),
                words=words,
            )
        )

    meta = {
        "engine": "faster_whisper",
        "model": model_name,
        "language": getattr(info, "language", language),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "duration_after_vad": getattr(info, "duration_after_vad", None),
        "word_timestamps": True,
    }
    return segments, meta


def transcribe_with_openai_whisper(
    audio_path: Path,
    model_name: str,
    language: str,
) -> tuple[list[SegmentAlignment], dict[str, Any]]:
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(
        str(audio_path),
        language=language,
        word_timestamps=True,
        verbose=False,
    )

    segments: list[SegmentAlignment] = []
    for raw_segment in result.get("segments", []):
        words = [
            WordAlignment(
                word=_normalize_text(item.get("word", "")),
                start=float(item["start"]),
                end=float(item["end"]),
                probability=float(item["probability"]) if item.get("probability") is not None else None,
            )
            for item in raw_segment.get("words", [])
            if _normalize_text(item.get("word", ""))
        ]
        segments.append(
            SegmentAlignment(
                segment_id=int(raw_segment["id"]) + 1,
                start=float(raw_segment["start"]),
                end=float(raw_segment["end"]),
                text=_normalize_text(raw_segment.get("text", "")),
                words=words,
            )
        )

    meta = {
        "engine": "openai_whisper",
        "model": model_name,
        "language": result.get("language", language),
        "duration": segments[-1].end if segments else 0.0,
        "word_timestamps": True,
    }
    return segments, meta


def transcribe_audio(
    audio_path: Path,
    engine: str,
    model_name: str,
    language: str,
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = True,
) -> tuple[list[SegmentAlignment], dict[str, Any]]:
    if engine == "faster_whisper":
        return transcribe_with_faster_whisper(
            audio_path=audio_path,
            model_name=model_name,
            language=language,
            device=device,
            compute_type=compute_type,
            vad_filter=vad_filter,
        )
    if engine == "openai_whisper":
        return transcribe_with_openai_whisper(
            audio_path=audio_path,
            model_name=model_name,
            language=language,
        )
    raise ValueError(f"Unsupported alignment engine: {engine}")


def build_visual_beats(
    segments: list[SegmentAlignment],
    min_duration: float = 5.0,
    max_duration: float = 10.0,
) -> list[VisualBeat]:
    beats: list[VisualBeat] = []
    buffer: list[SegmentAlignment] = []

    def flush() -> None:
        if not buffer:
            return
        start = buffer[0].start
        end = buffer[-1].end
        text = _normalize_text(" ".join(item.text for item in buffer))
        beats.append(
            VisualBeat(
                beat_id=f"B{len(beats) + 1:04d}",
                start=start,
                end=end,
                duration=round(end - start, 3),
                text=text,
                source_segment_ids=[item.segment_id for item in buffer],
            )
        )
        buffer.clear()

    for segment in segments:
        proposed = buffer + [segment]
        proposed_duration = proposed[-1].end - proposed[0].start
        end_of_sentence = bool(SENTENCE_END_RE.search(segment.text.strip()))

        if buffer and proposed_duration > max_duration:
            flush()

        buffer.append(segment)
        current_duration = buffer[-1].end - buffer[0].start

        if current_duration >= min_duration and end_of_sentence:
            flush()
        elif current_duration >= max_duration:
            flush()

    flush()
    return beats


def export_alignment_bundle(
    audio_path: Path,
    segments: list[SegmentAlignment],
    beats: list[VisualBeat],
    meta: dict[str, Any],
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    alignment_json = output_dir / "alignment.json"
    segments_json = output_dir / "segments.json"
    words_json = output_dir / "words.json"
    beats_json = output_dir / "visual_beats.json"
    subtitles_srt = output_dir / "subtitles.srt"

    word_rows = []
    for segment in segments:
        for word in segment.words:
            word_rows.append(
                {
                    "segment_id": segment.segment_id,
                    **asdict(word),
                }
            )

    alignment_json.write_text(
        json.dumps(
            {
                "audio_path": str(audio_path),
                "meta": meta,
                "segments": [asdict(item) for item in segments],
                "visual_beats": [asdict(item) for item in beats],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    segments_json.write_text(json.dumps([asdict(item) for item in segments], ensure_ascii=False, indent=2), encoding="utf-8")
    words_json.write_text(json.dumps(word_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    beats_json.write_text(json.dumps([asdict(item) for item in beats], ensure_ascii=False, indent=2), encoding="utf-8")
    write_srt(segments, subtitles_srt)

    return {
        "alignment_json": str(alignment_json),
        "segments_json": str(segments_json),
        "words_json": str(words_json),
        "beats_json": str(beats_json),
        "subtitles_srt": str(subtitles_srt),
    }
