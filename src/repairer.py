"""Append-only chapter repair for missing required sections."""

from __future__ import annotations

from pathlib import Path

from src.validator import validate_chapter


def repair_chapter(chapter: int, stage: str = "drafts") -> Path:
    """Append missing required sections to an existing chapter file."""
    result = validate_chapter(chapter, stage=stage)
    if not result.chapter_path.exists():
        raise FileNotFoundError(f"Missing {stage} chapter file: {result.chapter_path}")

    if not result.missing_sections:
        return result.chapter_path

    existing = result.chapter_path.read_text(encoding="utf-8")
    missing_headings = "\n".join(f"## {section}" for section in result.missing_sections)
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
    result.chapter_path.write_text(existing.rstrip() + "\n\n" + repair.strip() + "\n", encoding="utf-8")
    return result.chapter_path
