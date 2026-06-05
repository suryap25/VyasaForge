"""Chapter finalizer for Milestone M8."""

from __future__ import annotations

from pathlib import Path

REVIEWED_DIR = Path("chapters/reviewed")
FINAL_DIR = Path("chapters/final")


def chapter_filename(chapter: int) -> str:
    """Return the standard chapter filename."""
    return f"chapter-{chapter:02d}.md"


def metadata_header(chapter: int) -> str:
    """Return final chapter metadata."""
    return f"---\nchapter: {chapter}\nstage: final\ngenerated_by: appsec-handbook-agent\n---\n\n"


def finalize_chapter(chapter: int) -> Path:
    """Copy a reviewed chapter into the final stage with metadata."""
    reviewed_path = REVIEWED_DIR / chapter_filename(chapter)
    final_path = FINAL_DIR / chapter_filename(chapter)

    if not reviewed_path.exists():
        raise FileNotFoundError(f"Missing reviewed chapter: {reviewed_path}")

    reviewed = reviewed_path.read_text(encoding="utf-8")

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    final_path.write_text(metadata_header(chapter) + reviewed, encoding="utf-8")
    return final_path
