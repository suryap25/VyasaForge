"""Diagram artifact registry for chapter sketchnotes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from src.handbook import resolve_chapter

DIAGRAMS_DIR = Path("diagrams")


@dataclass(frozen=True)
class DiagramArtifact:
    """One planned/generated diagram artifact."""

    diagram_id: str
    chapter: int
    section: str
    title: str
    prompt_path: str
    image_path: str
    image_type: str
    diagram_type: str
    caption: str
    status: str


def diagram_registry_path(chapter: int) -> Path:
    """Return the diagram registry path for a chapter."""
    return DIAGRAMS_DIR / f"chapter-{chapter:02d}.json"


def write_diagram_registry(chapter: int, artifacts: list[DiagramArtifact]) -> Path:
    """Write the chapter diagram artifact registry."""
    metadata = resolve_chapter(chapter)
    path = diagram_registry_path(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "chapter": chapter,
        "chapter_id": metadata.chapter_id,
        "title": metadata.title,
        "diagrams": [asdict(artifact) for artifact in artifacts],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_diagram_registry(chapter: int) -> dict[str, object]:
    """Load a chapter diagram registry."""
    path = diagram_registry_path(chapter)
    if not path.exists():
        raise FileNotFoundError(f"Missing diagram registry: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
