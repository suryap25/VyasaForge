"""Chapter finalizer for Milestone M8."""

from __future__ import annotations

from pathlib import Path

from src.handbook import resolve_chapter


def metadata_header(chapter: int) -> str:
    """Return final chapter metadata."""
    return f"---\nchapter: {chapter}\nstage: final\ngenerated_by: appsec-handbook-agent\n---\n\n"


def finalize_chapter(chapter: int) -> Path:
    """Copy a reviewed chapter into the final stage with metadata."""
    metadata = resolve_chapter(chapter)
    reviewed_path = metadata.reviewed_path
    final_path = metadata.final_path

    if not reviewed_path.exists():
        raise FileNotFoundError(f"Missing reviewed chapter: {reviewed_path}")

    reviewed = reviewed_path.read_text(encoding="utf-8")

    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(metadata_header(chapter) + reviewed, encoding="utf-8")
    return final_path
