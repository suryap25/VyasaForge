"""Chapter reviewer for Milestone M5."""

from __future__ import annotations

from pathlib import Path

PROMPT_PATH = Path("prompts/chapter_review.md")
DRAFTS_DIR = Path("chapters/drafts")
REVIEWS_DIR = Path("reviews")


def chapter_filename(chapter: int) -> str:
    """Return the standard chapter filename."""
    return f"chapter-{chapter:02d}.md"


def ensure_required_file(path: Path, label: str) -> None:
    """Raise a clear error if a required file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def review_chapter(chapter: int) -> Path:
    """Review a chapter draft using the configured reviewer model."""
    prompt_path = PROMPT_PATH
    draft_path = DRAFTS_DIR / chapter_filename(chapter)
    review_path = REVIEWS_DIR / f"chapter-{chapter:02d}-review.md"

    ensure_required_file(prompt_path, "chapter review prompt")
    ensure_required_file(draft_path, "chapter draft")

    prompt = prompt_path.read_text(encoding="utf-8")
    draft = draft_path.read_text(encoding="utf-8")

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Review this chapter draft:\n\n{draft}"},
    ]

    from src import llm_gateway

    review = llm_gateway.call_llm(role="reviewer", messages=messages)

    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    review_path.write_text(review, encoding="utf-8")
    return review_path
