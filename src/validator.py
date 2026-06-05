"""Basic chapter validator for Milestone M4."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.handbook import resolve_chapter

MIN_WORD_COUNT = 1500
STAGE_FIELDS = {"drafts": "draft_path", "reviewed": "reviewed_path", "final": "final_path"}
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

@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome for a chapter draft."""

    chapter_path: Path
    stage: str
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


def validate_chapter(chapter: int, stage: str = "drafts") -> ValidationResult:
    """Validate a chapter Markdown file without calling the LLM."""
    stage_field = STAGE_FIELDS.get(stage)
    if stage_field is None:
        available_stages = ", ".join(sorted(STAGE_FIELDS))
        raise ValueError(f"Unknown validation stage '{stage}'. Available stages: {available_stages}")

    metadata = resolve_chapter(chapter)
    chapter_path = getattr(metadata, stage_field)
    errors: list[str] = []
    missing_sections: list[str] = []

    if not chapter_path.exists():
        return ValidationResult(
            chapter_path=chapter_path,
            stage=stage,
            passed=False,
            word_count=0,
            missing_sections=[],
            errors=[f"Missing {stage} chapter file: {chapter_path}"],
        )

    chapter_text = chapter_path.read_text(encoding="utf-8")
    word_count = count_words(chapter_text)
    if word_count < MIN_WORD_COUNT:
        errors.append(f"Word count is {word_count}; expected at least {MIN_WORD_COUNT}.")

    missing_sections = [section for section in REQUIRED_SECTIONS if not has_section(chapter_text, section)]
    for section in missing_sections:
        errors.append(f"Missing required section: {section}")

    return ValidationResult(
        chapter_path=chapter_path,
        stage=stage,
        passed=not errors,
        word_count=word_count,
        missing_sections=missing_sections,
        errors=errors,
    )
