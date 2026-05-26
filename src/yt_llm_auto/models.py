from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class WordAlignment:
    word: str
    start: float
    end: float
    probability: float | None = None


@dataclass(slots=True)
class SegmentAlignment:
    segment_id: int
    start: float
    end: float
    text: str
    words: list[WordAlignment] = field(default_factory=list)


@dataclass(slots=True)
class VisualBeat:
    beat_id: str
    start: float
    end: float
    duration: float
    text: str
    source_segment_ids: list[int]


@dataclass(slots=True)
class SemanticBeatPlan:
    beat_id: str
    start: float
    end: float
    duration: float
    voiceover_excerpt: str
    meaning: str
    viewer_emotion: str
    visual_function: str
    visual_strategy: str
    shot_type: str
    environment: str
    prompt_seed: str


def to_dict_list(items: list[object]) -> list[dict]:
    return [asdict(item) for item in items]
