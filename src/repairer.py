"""Append-only chapter repair for missing required sections."""

from __future__ import annotations

from pathlib import Path

from src.validator import has_section, resolve_chapter_stage_path, validate_chapter

SKETCHNOTE_SECTION = "Sketchnote Placeholder"
SKETCHNOTE_MARKDOWN = "## Sketchnote Placeholder\n\n[SKETCHNOTE DIAGRAM PLACEHOLDER]"


def append_section(path: Path, section_markdown: str) -> None:
    """Append Markdown to a chapter file."""
    existing = path.read_text(encoding="utf-8")
    path.write_text(existing.rstrip() + "\n\n" + section_markdown.strip() + "\n", encoding="utf-8")


def repair_chapter(chapter: int, stage: str = "drafts") -> Path:
    """Append missing required sections to an existing chapter file."""
    chapter_path = resolve_chapter_stage_path(chapter, stage=stage)
    result = validate_chapter(chapter, stage=stage)
    if not chapter_path.exists():
        raise FileNotFoundError(f"Missing {stage} chapter file: {chapter_path}")

    if not result.missing_sections:
        return chapter_path

    if result.missing_sections == [SKETCHNOTE_SECTION]:
        append_section(chapter_path, SKETCHNOTE_MARKDOWN)
        return chapter_path

    existing = chapter_path.read_text(encoding="utf-8")
    llm_sections = [section for section in result.missing_sections if section != SKETCHNOTE_SECTION]
    missing_headings = "\n".join(f"## {section}" for section in llm_sections)
    messages = [
        {
            "role": "system",
            "content": (
                "You repair AppSec handbook chapters by generating only missing sections. "
                "Do not rewrite existing content. Do not summarize. Keep the content vendor-neutral."
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate ONLY these missing Markdown sections, using the exact headings shown. "
                "Use practical AppSec examples and substantive guidance.\n\n"
                f"Missing sections:\n{missing_headings}\n\n"
                f"Existing chapter for context:\n\n{existing}"
            ),
        },
    ]

    from src import llm_gateway

    repair = llm_gateway.call_llm(role="writer", messages=messages)
    chapter_path.write_text(existing.rstrip() + "\n\n" + repair.strip() + "\n", encoding="utf-8")

    repaired = chapter_path.read_text(encoding="utf-8")
    if SKETCHNOTE_SECTION in result.missing_sections and not has_section(repaired, SKETCHNOTE_SECTION):
        append_section(chapter_path, SKETCHNOTE_MARKDOWN)

    return chapter_path
