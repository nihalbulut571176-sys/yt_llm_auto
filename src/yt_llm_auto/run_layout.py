from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(slots=True)
class RunPaths:
    root: Path
    input_dir: Path
    alignment_dir: Path
    semantic_dir: Path
    images_dir: Path
    images_generated_dir: Path
    images_meta_dir: Path
    render_dir: Path
    render_clips_dir: Path
    logs_dir: Path


def create_run_layout(base_dir: Path, run_id: str) -> RunPaths:
    root = base_dir / run_id
    paths = RunPaths(
        root=root,
        input_dir=root / "input",
        alignment_dir=root / "alignment",
        semantic_dir=root / "semantic",
        images_dir=root / "images",
        images_generated_dir=root / "images" / "generated",
        images_meta_dir=root / "images" / "meta",
        render_dir=root / "render",
        render_clips_dir=root / "render" / "clips",
        logs_dir=root / "logs",
    )
    for path in [
        paths.root,
        paths.input_dir,
        paths.alignment_dir,
        paths.semantic_dir,
        paths.images_dir,
        paths.images_generated_dir,
        paths.images_meta_dir,
        paths.render_dir,
        paths.render_clips_dir,
        paths.logs_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return paths


def copy_if_missing(source: Path, destination: Path) -> None:
    if destination.exists():
        return
    shutil.copy2(source, destination)
