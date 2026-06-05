"""Chapter reviser for Milestone M6."""

from __future__ import annotations

from pathlib import Path

PROMPT_PATH = Path("prompts/chapter_revision.md")
DRAFTS_DIR = Path("chapters/drafts")
REVIEWS_DIR = Path("reviews")
REVIEWED_DIR = Path("chapters/reviewed")


def chapter_filename(chapter: int) -> str:
    """Return the standard chapter filename."""
    return f"chapter-{chapter:02d}.md"


def review_filename(chapter: int) -> str:
    """Return the standard review filename."""
    return f"chapter-{chapter:02d}-review.md"


def ensure_required_file(path: Path, label: str) -> None:
    """Raise a clear error if a required file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def revise_chapter(chapter: int) -> Path:
    """Revise a chapter draft using review comments."""
    prompt_path = PROMPT_PATH
    draft_path = DRAFTS_DIR / chapter_filename(chapter)
    review_path = REVIEWS_DIR / review_filename(chapter)
    revised_path = REVIEWED_DIR / chapter_filename(chapter)

    ensure_required_file(prompt_path, "chapter revision prompt")
    ensure_required_file(draft_path, "chapter draft")
    ensure_required_file(review_path, "chapter review")

    prompt = prompt_path.read_text(encoding="utf-8")
    draft = draft_path.read_text(encoding="utf-8")
    review = review_path.read_text(encoding="utf-8")

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": f"Revise this draft using the review comments.\n\nDraft:\n{draft}\n\nReview:\n{review}",
        },
    ]

    from src import llm_gateway

    revised = llm_gateway.call_llm(role="editor", messages=messages)

    REVIEWED_DIR.mkdir(parents=True, exist_ok=True)
    revised_path.write_text(revised, encoding="utf-8")
    return revised_path
