"""Chapter state persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.handbook import resolve_chapter
from src.validator import count_words

STATE_DIR = Path("chapters/state")


def state_path(chapter: int) -> Path:
    """Return the JSON state path for a chapter."""
    return STATE_DIR / f"chapter-{chapter:02d}.json"


def timestamp() -> str:
    """Return a UTC timestamp for state updates."""
    return datetime.now(timezone.utc).isoformat()


def empty_state(chapter: int) -> dict[str, Any]:
    """Return an empty state document for a registered chapter."""
    metadata = resolve_chapter(chapter)
    return {
        "chapter_id": metadata.chapter_id,
        "title": metadata.title,
        "draft": {"status": "not_started", "word_count": None, "updated_at": None},
        "review": {"status": "not_started", "updated_at": None},
        "revision": {"status": "not_started", "reason": None, "updated_at": None},
        "final": {"status": "not_started", "source": None, "word_count": None, "updated_at": None},
        "docx": {"status": "not_started", "updated_at": None},
    }


def load_state(chapter: int) -> dict[str, Any]:
    """Load chapter state, returning a schema-complete state if none exists."""
    path = state_path(chapter)
    if not path.exists():
        return empty_state(chapter)

    state = empty_state(chapter)
    saved_state = json.loads(path.read_text(encoding="utf-8"))
    for key in state:
        if key in saved_state:
            state[key] = saved_state[key]
    return state


def save_state(chapter: int, state: dict[str, Any]) -> Path:
    """Persist chapter state as formatted JSON."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = state_path(chapter)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def update_draft(chapter: int, status: str, path: Path | None = None) -> Path:
    """Update draft status and word count."""
    state = load_state(chapter)
    word_count = count_words(path.read_text(encoding="utf-8")) if path and path.exists() else None
    state["draft"] = {"status": status, "word_count": word_count, "updated_at": timestamp()}
    return save_state(chapter, state)


def update_review(chapter: int, status: str) -> Path:
    """Update review status."""
    state = load_state(chapter)
    state["review"] = {"status": status, "updated_at": timestamp()}
    return save_state(chapter, state)


def update_revision(chapter: int, status: str, reason: str | None = None) -> Path:
    """Update revision status and rejection reason."""
    state = load_state(chapter)
    state["revision"] = {"status": status, "reason": reason, "updated_at": timestamp()}
    return save_state(chapter, state)


def update_final(chapter: int, status: str, source: str | None = None, path: Path | None = None) -> Path:
    """Update final status, source, and word count."""
    state = load_state(chapter)
    word_count = count_words(path.read_text(encoding="utf-8")) if path and path.exists() else None
    state["final"] = {
        "status": status,
        "source": source,
        "word_count": word_count,
        "updated_at": timestamp(),
    }
    return save_state(chapter, state)


def update_docx(chapter: int, status: str) -> Path:
    """Update DOCX compilation status."""
    state = load_state(chapter)
    state["docx"] = {"status": status, "updated_at": timestamp()}
    return save_state(chapter, state)


def formatted_state(chapter: int) -> str:
    """Return formatted JSON state for display."""
    return json.dumps(load_state(chapter), indent=2, sort_keys=True)
