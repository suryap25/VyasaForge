"""Chapter reviser for Milestone M6."""

from __future__ import annotations

from pathlib import Path

from src.handbook import resolve_chapter
from src.validator import REQUIRED_SECTIONS, count_words, has_section

PROMPT_PATH = Path("prompts/chapter_revision.md")
MIN_REVISED_WORD_RATIO = 0.8


def ensure_required_file(path: Path, label: str) -> None:
    """Raise a clear error if a required file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def missing_required_sections(markdown: str) -> list[str]:
    """Return required handbook sections missing from Markdown."""
    return [section for section in REQUIRED_SECTIONS if not has_section(markdown, section)]


def revise_chapter(chapter: int) -> Path:
    """Revise a chapter draft using review comments."""
    metadata = resolve_chapter(chapter)
    prompt_path = PROMPT_PATH
    draft_path = metadata.draft_path
    review_path = metadata.review_path
    revised_path = metadata.reviewed_path
    failed_revision_path = review_path.parent / f"chapter-{metadata.number:02d}-revision-failed.md"

    ensure_required_file(prompt_path, "chapter revision prompt")
    ensure_required_file(draft_path, "chapter draft")
    ensure_required_file(review_path, "chapter review")

    prompt = prompt_path.read_text(encoding="utf-8")
    draft = draft_path.read_text(encoding="utf-8")
    review = review_path.read_text(encoding="utf-8")
    original_word_count = count_words(draft)

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                "INPUTS:\n\n"
                "Original Chapter:\n"
                f"{draft}\n\n"
                "Review Comments:\n"
                f"{review}\n\n"
                "INSTRUCTION:\n"
                "Improve the chapter.\n\n"
                "Do not remove sections.\n"
                "Do not shorten content.\n"
                "Do not rewrite from scratch.\n\n"
                "Preserve:\n"
                "- structure\n"
                "- headings\n"
                "- examples\n"
                "- existing content\n\n"
                "Only:\n"
                "- fix issues\n"
                "- add missing material\n"
                "- improve weak sections\n"
            ),
        },
    ]

    from src import llm_gateway

    revised = llm_gateway.call_llm(role="editor", messages=messages)
    revised_word_count = count_words(revised)
    missing_sections = missing_required_sections(revised)
    too_short = revised_word_count < original_word_count * MIN_REVISED_WORD_RATIO

    if too_short or missing_sections:
        failed_revision_path.parent.mkdir(parents=True, exist_ok=True)
        failed_revision_path.write_text(revised, encoding="utf-8")
        failures = []
        if too_short:
            failures.append(
                "revised chapter is less than 80% of original word count "
                f"(original: {original_word_count}, revised: {revised_word_count})"
            )
        if missing_sections:
            failures.append("revised chapter is missing required sections: " + ", ".join(missing_sections))
        raise RuntimeError(
            "Revision safety gate failed: "
            + "; ".join(failures)
            + ". "
            f"Failed attempt saved to {failed_revision_path}."
        )

    revised_path.parent.mkdir(parents=True, exist_ok=True)
    revised_path.write_text(revised, encoding="utf-8")
    return revised_path
