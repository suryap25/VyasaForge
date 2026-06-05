"""Chapter finalizer for Milestone M8."""

from __future__ import annotations

from pathlib import Path

from src.handbook import resolve_chapter

SOURCE_FIELDS = {"drafts": "draft_path", "reviewed": "reviewed_path"}


def metadata_header(chapter: int, source: str) -> str:
    """Return final chapter metadata."""
    return (
        "---\n"
        f"chapter: {chapter}\n"
        "stage: final\n"
        f"source: {source}\n"
        "generated_by: appsec-handbook-agent\n"
        "---\n\n"
    )


def finalize_chapter(chapter: int, source: str = "reviewed") -> Path:
    """Copy a selected chapter source into the final stage with metadata."""
    metadata = resolve_chapter(chapter)
    source_field = SOURCE_FIELDS.get(source)
    if source_field is None:
        available_sources = ", ".join(sorted(SOURCE_FIELDS))
        raise ValueError(f"Unknown finalizer source '{source}'. Available sources: {available_sources}")

    source_path = getattr(metadata, source_field)
    final_path = metadata.final_path

    if not source_path.exists():
        raise FileNotFoundError(f"Missing {source} chapter: {source_path}")

    source_content = source_path.read_text(encoding="utf-8")

    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(metadata_header(chapter, source) + source_content, encoding="utf-8")
    return final_path
