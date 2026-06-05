"""Structural chapter diff utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.validator import REQUIRED_SECTIONS, count_words, resolve_chapter_stage_path


@dataclass(frozen=True)
class StructuralDiff:
    """Structural differences between two chapter stages."""

    from_word_count: int
    to_word_count: int
    word_count_delta: int
    percent_delta: float
    headings_removed: list[str]
    headings_added: list[str]
    required_sections_removed: list[str]


def extract_headings(markdown: str) -> list[str]:
    """Extract Markdown heading text in document order."""
    headings = []
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1))
    return headings


def diff_chapter(chapter: int = 1, from_stage: str = "drafts", to_stage: str = "reviewed") -> StructuralDiff:
    """Compare two registered chapter stages without calling the LLM."""
    from_path = resolve_chapter_stage_path(chapter, from_stage)
    to_path = resolve_chapter_stage_path(chapter, to_stage)

    if not from_path.exists():
        raise FileNotFoundError(f"Missing {from_stage} chapter file: {from_path}")
    if not to_path.exists():
        raise FileNotFoundError(f"Missing {to_stage} chapter file: {to_path}")

    from_markdown = from_path.read_text(encoding="utf-8")
    to_markdown = to_path.read_text(encoding="utf-8")
    from_word_count = count_words(from_markdown)
    to_word_count = count_words(to_markdown)
    from_headings = extract_headings(from_markdown)
    to_headings = extract_headings(to_markdown)

    headings_removed = [heading for heading in from_headings if heading not in to_headings]
    headings_added = [heading for heading in to_headings if heading not in from_headings]
    required_sections_removed = [section for section in REQUIRED_SECTIONS if section in headings_removed]

    word_count_delta = to_word_count - from_word_count
    percent_delta = (word_count_delta / from_word_count * 100) if from_word_count else 0.0

    return StructuralDiff(
        from_word_count=from_word_count,
        to_word_count=to_word_count,
        word_count_delta=word_count_delta,
        percent_delta=percent_delta,
        headings_removed=headings_removed,
        headings_added=headings_added,
        required_sections_removed=required_sections_removed,
    )
