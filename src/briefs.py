"""Chapter brief creation utilities."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from src.handbook import load_handbook_registry, resolve_chapter
from src.validator import REQUIRED_SECTIONS


class ChapterBrief(BaseModel):
    """Execution contract for generating one handbook chapter."""

    chapter_id: str
    chapter_number: int = Field(gt=0)
    handbook_title: str
    title: str
    goal: str
    audience: list[str]
    target_word_count: str
    required_sections: list[str]
    must_cover_topics: list[str]
    examples_required: list[str]
    interview_questions_required: bool = True
    references_needed: str
    diagram_placeholder: str


def build_chapter_brief(chapter: int) -> ChapterBrief:
    """Build a default structured brief from handbook registry metadata."""
    registry = load_handbook_registry()
    metadata = resolve_chapter(chapter)
    title = metadata.title

    must_cover_topics = [
        f"Core concepts for {title}",
        f"Architecture considerations for {title}",
        f"Application security risks related to {title}",
        f"Developer implementation guidance for {title}",
        f"Testing and assessment guidance for {title}",
    ]

    return ChapterBrief(
        chapter_id=metadata.chapter_id,
        chapter_number=metadata.number,
        handbook_title=registry.title,
        title=title,
        goal=f"Write a practical, vendor-neutral handbook chapter about {title}.",
        audience=["AppSec Engineers", "Developers", "Security Champions"],
        target_word_count="3000-4500 words",
        required_sections=REQUIRED_SECTIONS,
        must_cover_topics=must_cover_topics,
        examples_required=[
            "At least one practical implementation example",
            "At least one common failure mode",
            "At least one secure design pattern",
            "At least one testing or review checklist",
        ],
        references_needed="Include vendor-neutral standards or concepts when useful; do not invent citations.",
        diagram_placeholder="Include the required Sketchnote Placeholder section.",
    )


def render_chapter_brief(brief: ChapterBrief) -> str:
    """Render a chapter brief as Markdown."""
    lines = [
        "---",
        f"chapter_id: {brief.chapter_id}",
        f"chapter_number: {brief.chapter_number}",
        f"title: {brief.title}",
        f"handbook_title: {brief.handbook_title}",
        "---",
        "",
        f"# Chapter {brief.chapter_number:02d}: {brief.title}",
        "",
        "## Goal",
        brief.goal,
        "",
        "## Audience",
        *[f"- {item}" for item in brief.audience],
        "",
        "## Target Word Count",
        brief.target_word_count,
        "",
        "## Required Sections",
        *[f"- {section}" for section in brief.required_sections],
        "",
        "## Must-Cover Topics",
        *[f"- {topic}" for topic in brief.must_cover_topics],
        "",
        "## Examples Required",
        *[f"- {example}" for example in brief.examples_required],
        "",
        "## Interview Questions Required",
        "Yes" if brief.interview_questions_required else "No",
        "",
        "## References Needed",
        brief.references_needed,
        "",
        "## Diagram Placeholder",
        brief.diagram_placeholder,
        "",
    ]
    return "\n".join(lines)


def create_chapter_brief(chapter: int, overwrite: bool = False) -> Path:
    """Create a chapter brief file from the registry."""
    metadata = resolve_chapter(chapter)
    brief_path = metadata.brief_path
    if brief_path.exists() and not overwrite:
        return brief_path

    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief = build_chapter_brief(chapter)
    brief_path.write_text(render_chapter_brief(brief), encoding="utf-8")
    return brief_path
