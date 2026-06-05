"""Basic chapter validator for Milestone M4."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

MIN_WORD_COUNT = 1500
DRAFTS_DIR = Path("chapters/drafts")
REQUIRED_SECTIONS = [
    "Learning Objectives",
    "Conceptual Foundation",
    "Architecture Perspective",
    "AppSec Lens",
    "Developer Lens",
    "Pentest Lens",
    "Common Findings",
    "Secure Design Guidance",
    "Interview Questions",
    "Key Takeaways",
    "Sketchnote Placeholder",
]


def chapter_filename(chapter: int) -> str:
    """Return the standard chapter filename."""
    return f"chapter-{chapter:02d}.md"


@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome for a chapter draft."""

    draft_path: Path
    passed: bool
    word_count: int
    missing_sections: list[str]
    errors: list[str]


def count_words(text: str) -> int:
    """Count words in Markdown text."""
    return len(re.findall(r"\b[\w'-]+\b", text))


def has_section(text: str, section: str) -> bool:
    """Return true if a required Markdown heading exists."""
    pattern = rf"(?im)^#+\s+{re.escape(section)}\s*$"
    return re.search(pattern, text) is not None


def validate_chapter(chapter: int) -> ValidationResult:
    """Validate a chapter draft without calling the LLM."""
    draft_path = DRAFTS_DIR / chapter_filename(chapter)
    errors: list[str] = []
    missing_sections: list[str] = []

    if not draft_path.exists():
        return ValidationResult(
            draft_path=draft_path,
            passed=False,
            word_count=0,
            missing_sections=[],
            errors=[f"Missing draft file: {draft_path}"],
        )

    draft = draft_path.read_text(encoding="utf-8")
    word_count = count_words(draft)
    if word_count < MIN_WORD_COUNT:
        errors.append(f"Word count is {word_count}; expected at least {MIN_WORD_COUNT}.")

    missing_sections = [section for section in REQUIRED_SECTIONS if not has_section(draft, section)]
    for section in missing_sections:
        errors.append(f"Missing required section: {section}")

    return ValidationResult(
        draft_path=draft_path,
        passed=not errors,
        word_count=word_count,
        missing_sections=missing_sections,
        errors=errors,
    )
