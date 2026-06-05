"""Chapter state persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = Path("chapters/state")


def state_path(chapter: int) -> Path:
    """Return the JSON state path for a chapter."""
    return STATE_DIR / f"chapter-{chapter:02d}.json"


def load_state(chapter: int) -> dict[str, Any]:
    """Load chapter state, returning an empty state if none exists."""
    path = state_path(chapter)
    if not path.exists():
        return {"chapter": chapter, "stages": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(chapter: int, state: dict[str, Any]) -> Path:
    """Persist chapter state as formatted JSON."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = state_path(chapter)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def update_stage(chapter: int, stage: str, status: str, details: dict[str, Any] | None = None) -> Path:
    """Update one pipeline stage for a chapter."""
    state = load_state(chapter)
    state["chapter"] = chapter
    state.setdefault("stages", {})
    state["stages"][stage] = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }
    return save_state(chapter, state)


def formatted_state(chapter: int) -> str:
    """Return formatted JSON state for display."""
    return json.dumps(load_state(chapter), indent=2, sort_keys=True)
