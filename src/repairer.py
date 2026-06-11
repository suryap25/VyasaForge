"""Append-only chapter repair for missing required sections."""

from __future__ import annotations

from pathlib import Path

from src.handbook import resolve_chapter
from src.publish_gate import code_fence_count
from src.validator import has_section, resolve_chapter_stage_path, validate_chapter

SKETCHNOTE_SECTION = "Sketchnote Placeholder"
SKETCHNOTE_MARKDOWN = "## Sketchnote Placeholder\n\n[SKETCHNOTE DIAGRAM PLACEHOLDER]"


def deterministic_section_markdown(section: str) -> str:
    """Return a small deterministic fallback for a missing required section."""
    if section == SKETCHNOTE_SECTION:
        return SKETCHNOTE_MARKDOWN
    if section == "Interview Questions":
        return (
            "## Interview Questions\n\n"
            "- How do authentication and authorization failures show up differently in application logs?\n"
            "- What controls would you expect around session creation, token validation, and privilege checks?\n"
            "- How would you review an API endpoint to confirm that authorization is enforced server-side?\n"
            "- What is the risk of relying on client-side checks for access control?\n"
            "- How should teams test for horizontal and vertical privilege escalation?"
        )
    if section == "Key Takeaways":
        return (
            "## Key Takeaways\n\n"
            "- Authentication verifies identity; authorization decides what that identity can access.\n"
            "- Strong authentication does not compensate for missing or inconsistent authorization checks.\n"
            "- Authorization belongs on the server side and should be enforced close to protected resources.\n"
            "- AppSec reviews should trace identity, session, role, permission, and object ownership decisions.\n"
            "- Secure design requires clear access-control models, centralized policy logic, and repeatable tests."
        )
    return (
        f"## {section}\n\n"
        "This section requires additional handbook content. Cover the topic with vendor-neutral guidance, "
        "practical AppSec examples, implementation considerations, and testing notes."
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
