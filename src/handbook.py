"""Handbook chapter registry."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.workspace import active_registry_path

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


def _resolve_artifact_path(registry_path: Path, value: str) -> Path:
    """Resolve registry artifact paths under the handbook workspace."""
    path = Path(value)
    if path.is_absolute():
        return path
    try:
        is_legacy_registry = registry_path.resolve() == REGISTRY_PATH.resolve()
    except OSError:
        is_legacy_registry = registry_path == REGISTRY_PATH
    base = Path(".") if is_legacy_registry else registry_path.parent
    return base / path


@lru_cache(maxsize=8)
def load_handbook_registry(path: str | None = None) -> HandbookRegistry:
    """Load handbook chapter metadata from YAML."""
    try:
        import yaml
    except ImportError:
        from src import simple_yaml as yaml

    registry_path = Path(path) if path is not None else active_registry_path()
    if not registry_path.exists():
        raise FileNotFoundError(f"Missing handbook registry: {registry_path}")

    raw_registry: dict[str, Any] = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    handbook = raw_registry["handbook"]
    chapters = {
        chapter_id: ChapterMetadata(
            chapter_id=chapter_id,
            number=settings["number"],
            title=settings["title"],
            brief_path=_resolve_artifact_path(registry_path, settings["brief_path"]),
            draft_path=_resolve_artifact_path(registry_path, settings["draft_path"]),
            reviewed_path=_resolve_artifact_path(registry_path, settings["reviewed_path"]),
            final_path=_resolve_artifact_path(registry_path, settings["final_path"]),
            review_path=_resolve_artifact_path(registry_path, settings["review_path"]),
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
