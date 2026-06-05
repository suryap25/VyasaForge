"""Handbook chapter registry."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path("configs/handbook.yaml")


@dataclass(frozen=True)
class ChapterMetadata:
    """Registered metadata and file paths for one chapter."""

    chapter_id: str
    number: int
    title: str
    brief_path: Path
    draft_path: Path
    reviewed_path: Path
    final_path: Path
    review_path: Path


@dataclass(frozen=True)
class HandbookRegistry:
    """Registered handbook metadata."""

    title: str
    version: str
    chapters: dict[str, ChapterMetadata]


def chapter_id_for(chapter: int | str) -> str:
    """Return the registry chapter ID for a chapter number or ID."""
    if isinstance(chapter, int):
        return f"chapter_{chapter:02d}"
    if chapter.startswith("chapter_"):
        return chapter
    return f"chapter_{int(chapter):02d}"


@lru_cache(maxsize=1)
def load_handbook_registry(path: str = str(REGISTRY_PATH)) -> HandbookRegistry:
    """Load handbook chapter metadata from YAML."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install project dependencies with `pip install -e .`.") from exc

    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"Missing handbook registry: {registry_path}")

    raw_registry: dict[str, Any] = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    handbook = raw_registry["handbook"]
    chapters = {
        chapter_id: ChapterMetadata(
            chapter_id=chapter_id,
            number=settings["number"],
            title=settings["title"],
            brief_path=Path(settings["brief_path"]),
            draft_path=Path(settings["draft_path"]),
            reviewed_path=Path(settings["reviewed_path"]),
            final_path=Path(settings["final_path"]),
            review_path=Path(settings["review_path"]),
        )
        for chapter_id, settings in handbook["chapters"].items()
    }

    return HandbookRegistry(title=handbook["title"], version=str(handbook["version"]), chapters=chapters)


def resolve_chapter(chapter: int | str) -> ChapterMetadata:
    """Resolve chapter metadata from the handbook registry."""
    registry = load_handbook_registry()
    chapter_id = chapter_id_for(chapter)
    metadata = registry.chapters.get(chapter_id)
    if metadata is None:
        available = ", ".join(sorted(registry.chapters))
        raise ValueError(f"Unknown chapter '{chapter}'. Available chapters: {available}")
    return metadata
