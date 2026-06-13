"""Append-only chapter repair for missing required sections."""

from __future__ import annotations

from pathlib import Path

from src.handbook import resolve_chapter
from src.publish_gate import code_fence_count
from src.validator import has_section, resolve_chapter_stage_path, validate_chapter


def deterministic_section_markdown(section: str) -> str:
    """Return a small deterministic fallback for a missing required section."""
    if section == "Interview Questions":
        return (
            "## Interview Questions\n\n"
            "- What problem does this chapter help the reader solve?\n"
            "- What assumptions must hold true for the recommended approach to work?\n"
            "- What tradeoffs should practitioners consider before implementation?\n"
            "- How would you evaluate whether the guidance was applied correctly?\n"
            "- What failure modes should reviewers look for?"
        )
    if section == "Key Takeaways":
        return (
            "## Key Takeaways\n\n"
            "- Strong documents explain the concept, the implementation path, and the evaluation criteria.\n"
            "- Practical guidance should name assumptions, tradeoffs, and common failure modes.\n"
            "- Reader-facing examples should match the topic, audience, and document purpose.\n"
            "- Evaluation guidance helps reviewers confirm that recommendations were applied correctly.\n"
            "- Vendor-neutral design keeps the document reusable across tools and environments."
        )
    return (
        f"## {section}\n\n"
        "This section requires additional handbook content. Cover the topic with vendor-neutral guidance, "
        "practical examples, implementation considerations, and evaluation notes."
    )


def append_section(path: Path, section_markdown: str) -> None:
    """Append Markdown to a chapter file."""
    existing = path.read_text(encoding="utf-8")
    path.write_text(existing.rstrip() + "\n\n" + section_markdown.strip() + "\n", encoding="utf-8")


def repair_code_fence(path: Path) -> bool:
    """Close a dangling fenced code block if the file has an odd fence count."""
    existing = path.read_text(encoding="utf-8")
    if code_fence_count(existing) % 2 == 0:
        return False
    path.write_text(existing.rstrip() + "\n```\n", encoding="utf-8")
    return True


def repair_chapter(chapter: int, stage: str = "drafts") -> Path:
    """Append missing required sections to an existing chapter file."""
    metadata = resolve_chapter(chapter)
    chapter_path = resolve_chapter_stage_path(chapter, stage=stage)
    if not chapter_path.exists():
        raise FileNotFoundError(f"Missing {stage} chapter file: {chapter_path}")

    repair_code_fence(chapter_path)
    result = validate_chapter(chapter, stage=stage)

    if not result.missing_sections:
        return chapter_path

    existing = chapter_path.read_text(encoding="utf-8")
    llm_sections = list(result.missing_sections)
    missing_headings = "\n".join(f"## {section}" for section in llm_sections)
    messages = [
        {
            "role": "system",
            "content": (
                "You repair technical document chapters by generating only missing sections. "
                "Do not rewrite existing content. Do not summarize. Keep the content vendor-neutral unless the brief requires otherwise."
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate ONLY these missing Markdown sections, using the exact headings shown. "
                "Use practical topic-appropriate examples and substantive guidance.\n\n"
                f"Missing sections:\n{missing_headings}\n\n"
                f"Existing chapter for context:\n\n{existing}"
            ),
        },
    ]

    from src import llm_gateway

    try:
        repair = llm_gateway.call_llm(role="writer", messages=messages, chapter=metadata.number)
    except RuntimeError:
        repair = "\n\n".join(deterministic_section_markdown(section) for section in llm_sections)
    chapter_path.write_text(existing.rstrip() + "\n\n" + repair.strip() + "\n", encoding="utf-8")
    repair_code_fence(chapter_path)

    repaired = chapter_path.read_text(encoding="utf-8")
    for section in result.missing_sections:
        if not has_section(repaired, section):
            append_section(chapter_path, deterministic_section_markdown(section))
            repair_code_fence(chapter_path)
            repaired = chapter_path.read_text(encoding="utf-8")

    return chapter_path
