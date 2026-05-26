from __future__ import annotations

import json
from pathlib import Path
import subprocess

from yt_llm_auto.models import SemanticBeatPlan


def _safe_ffconcat_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", r"'\''")


def _motion_filter(index: int, duration: float, fps: int) -> str:
    frames = max(1, int(round(duration * fps)))
    if index % 4 == 1:
        return (
            f"scale=2200:1238:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='min(1.0+on*0.0012,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
        )
    if index % 4 == 2:
        return (
            f"scale=2200:1238:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='1.05':x='max(0,min(iw-iw/zoom,on*1.6))':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
        )
    if index % 4 == 3:
        return (
            f"scale=2200:1238:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='1.04':x='iw/2-(iw/zoom/2)':y='max(0,min(ih-ih/zoom,on*1.2))':d={frames}:s=1920x1080:fps={fps}"
        )
    return (
        f"scale=2200:1238:force_original_aspect_ratio=increase,"
        f"crop=1920:1080,"
        f"zoompan=z='max(1.12-on*0.0009,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    )


def render_clip(image_path: Path, target_path: Path, duration: float, index: int, fps: int = 30) -> None:
    vf = _motion_filter(index=index, duration=duration, fps=fps)
    command = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-t",
        f"{duration:.3f}",
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(target_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def build_preview_timeline(
    semantic_items: list[SemanticBeatPlan],
    images_dir: Path,
    clip_dir: Path,
    ffconcat_path: Path,
    timeline_path: Path,
    fps: int = 30,
) -> float:
    ffconcat_lines = ["ffconcat version 1.0"]
    timeline = []
    total_duration = 0.0

    for index, item in enumerate(semantic_items, start=1):
        image_path = images_dir / f"{item.beat_id}_V01.png"
        if not image_path.exists():
            raise FileNotFoundError(f"Missing generated image for {item.beat_id}: {image_path}")

        clip_path = clip_dir / f"{item.beat_id}_V01.mp4"
        render_clip(image_path=image_path, target_path=clip_path, duration=item.duration, index=index, fps=fps)
        ffconcat_lines.append(f"file '{_safe_ffconcat_path(clip_path)}'")
        timeline.append(
            {
                "beat_id": item.beat_id,
                "start": round(total_duration, 3),
                "end": round(total_duration + item.duration, 3),
                "duration": item.duration,
                "image_path": str(image_path),
                "clip_path": str(clip_path),
                "voiceover_excerpt": item.voiceover_excerpt,
            }
        )
        total_duration += item.duration

    ffconcat_path.write_text("\n".join(ffconcat_lines) + "\n", encoding="utf-8")
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    return total_duration


def mux_preview_video(ffconcat_path: Path, audio_path: Path, output_path: Path, total_duration: float) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(ffconcat_path),
        "-i",
        str(audio_path),
        "-t",
        f"{total_duration:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-shortest",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
