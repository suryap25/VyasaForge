"""Deterministic handbook quality checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.handbook import resolve_chapter
from src.validator import REQUIRED_SECTIONS, ValidationResult, validate_chapter

REPORT_PATH = Path("reports/handbook-qa.md")


@dataclass(frozen=True)
class ChapterQAResult:
    """Quality checks for one chapter."""

    chapter: int
    title: str
    stage: str
    validation: ValidationResult
    weak_interview_questions: bool
    sketchnote_missing_placeholder: bool
    repeated_headings: list[str]
    passed: bool


@dataclass(frozen=True)
class HandbookQAResult:
    """Book-level quality report."""

    stage: str
    chapter_results: list[ChapterQAResult]
    duplicate_titles: list[str]
    word_count_min: int
    word_count_max: int
    length_imbalance: bool
    passed: bool


def _without_fenced_code(markdown: str) -> str:
    return re.sub(r"(?ms)^```.*?^```", "", markdown)


def _heading_titles(markdown: str) -> list[str]:
    body = _without_fenced_code(markdown)
    return [match.group(1).strip() for match in re.finditer(r"(?m)^#{2,3}\s+(.+?)\s*$", body)]


def _section_text(markdown: str, section: str) -> str:
    pattern = rf"(?ims)^#+\s+{re.escape(section)}\s*$(.*?)(?=^#+\s+|\Z)"
    match = re.search(pattern, markdown)
    return match.group(1).strip() if match else ""


def _repeated(items: list[str]) -> list[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for item in items:
        key = item.casefold()
        if key in seen:
            repeated.add(item)
        seen.add(key)
    return sorted(repeated)


def _chapter_path(chapter: int, stage: str) -> Path:
    metadata = resolve_chapter(chapter)
    if stage == "drafts":
        return metadata.draft_path
    if stage == "reviewed":
        return metadata.reviewed_path
    if stage == "final":
        return metadata.final_path
    raise ValueError("QA stage must be drafts, reviewed, or final.")


def qa_chapter(chapter: int, stage: str = "final") -> ChapterQAResult:
    """Run deterministic quality checks for one chapter."""
    metadata = resolve_chapter(chapter)
    validation = validate_chapter(chapter, stage=stage)
    chapter_path = _chapter_path(chapter, stage)
    markdown = chapter_path.read_text(encoding="utf-8") if chapter_path.exists() else ""
    headings = _heading_titles(markdown)
    interview_text = _section_text(markdown, "Interview Questions")
    sketchnote_text = _section_text(markdown, "Sketchnote Placeholder")
    repeated_headings = [
        heading for heading in _repeated(headings)
        if heading not in REQUIRED_SECTIONS
    ]
    weak_interview_questions = bool(interview_text) and interview_text.count("?") < 3
    sketchnote_missing_placeholder = bool(sketchnote_text) and "[SKETCHNOTE DIAGRAM PLACEHOLDER]" not in sketchnote_text
    passed = (
        validation.passed
        and not weak_interview_questions
        and not sketchnote_missing_placeholder
        and not repeated_headings
    )
    return ChapterQAResult(
        chapter=chapter,
        title=metadata.title,
        stage=stage,
        validation=validation,
        weak_interview_questions=weak_interview_questions,
        sketchnote_missing_placeholder=sketchnote_missing_placeholder,
        repeated_headings=repeated_headings,
        passed=passed,
    )


def qa_handbook(chapters: list[int], stage: str = "final") -> HandbookQAResult:
    """Run deterministic book-level QA checks."""
    chapter_results = [qa_chapter(chapter, stage=stage) for chapter in chapters]
    titles = [result.title for result in chapter_results]
    duplicate_titles = _repeated(titles)
    word_counts = [result.validation.word_count for result in chapter_results if result.validation.word_count > 0]
    word_count_min = min(word_counts) if word_counts else 0
    word_count_max = max(word_counts) if word_counts else 0
    length_imbalance = bool(word_counts) and word_count_min > 0 and word_count_max > word_count_min * 2
    passed = (
        all(result.passed for result in chapter_results)
        and not duplicate_titles
        and not length_imbalance
    )
    return HandbookQAResult(
        stage=stage,
        chapter_results=chapter_results,
        duplicate_titles=duplicate_titles,
        word_count_min=word_count_min,
        word_count_max=word_count_max,
        length_imbalance=length_imbalance,
        passed=passed,
    )


def render_qa_report(result: HandbookQAResult) -> str:
    """Render QA result as Markdown."""
    lines = [
        "# Handbook QA Report",
        "",
        f"Stage: {result.stage}",
        f"Result: {'PASS' if result.passed else 'FAIL'}",
        "",
        "## Book-Level Checks",
        f"- Duplicate chapter titles: {', '.join(result.duplicate_titles) if result.duplicate_titles else 'none'}",
        f"- Word count range: {result.word_count_min} - {result.word_count_max}",
        f"- Length imbalance: {'yes' if result.length_imbalance else 'no'}",
        "",
        "## Chapter Checks",
    ]

    for chapter_result in result.chapter_results:
        lines.extend(
            [
                "",
                f"### Chapter {chapter_result.chapter:02d}: {chapter_result.title}",
                f"- Result: {'PASS' if chapter_result.passed else 'FAIL'}",
                f"- Word count: {chapter_result.validation.word_count}",
                f"- Missing sections: {', '.join(chapter_result.validation.missing_sections) if chapter_result.validation.missing_sections else 'none'}",
                f"- Weak interview questions: {'yes' if chapter_result.weak_interview_questions else 'no'}",
                f"- Sketchnote placeholder issue: {'yes' if chapter_result.sketchnote_missing_placeholder else 'no'}",
                f"- Repeated headings: {', '.join(chapter_result.repeated_headings) if chapter_result.repeated_headings else 'none'}",
            ]
        )
        for error in chapter_result.validation.errors:
            lines.append(f"- Validator error: {error}")

    return "\n".join(lines).strip() + "\n"


def write_qa_report(result: HandbookQAResult, path: Path = REPORT_PATH) -> Path:
    """Write QA report to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_qa_report(result), encoding="utf-8")
    return path
