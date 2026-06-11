"""Chapter reviewer for Milestone M5."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from src.handbook import resolve_chapter
from src.validator import REQUIRED_SECTIONS

PROMPT_PATH = Path("prompts/chapter_review.md")


def ensure_required_file(path: Path, label: str) -> None:
    """Raise a clear error if a required file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


@dataclass(frozen=True)
class ReviewFinding:
    """Machine-readable review finding."""

    section: str
    severity: str
    issue_type: str
    message: str
    recommended_action: str


def review_findings_path(chapter: int) -> Path:
    """Return the structured review findings path."""
    return Path("reviews") / f"chapter-{chapter:02d}-review.json"


def _sentence_for_section(review: str, section: str) -> str | None:
    """Return a short review sentence that mentions a section."""
    for sentence in re.split(r"(?<=[.!?])\s+", review):
        if section.lower() in sentence.lower():
            return sentence.strip()
    return None


def _issue_type(message: str) -> str:
    lower = message.lower()
    if "missing" in lower:
        return "missing_material"
    if "unclear" in lower or "clar" in lower:
        return "unclear_explanation"
    if "weak" in lower:
        return "weak_section"
    if "hallucination" in lower or "vendor" in lower:
        return "trust_risk"
    return "section_improvement"


def extract_structured_findings(review: str) -> list[ReviewFinding]:
    """Extract conservative structured findings from a Markdown review."""
    findings: list[ReviewFinding] = []
    for section in REQUIRED_SECTIONS:
        sentence = _sentence_for_section(review, section)
        if sentence is None:
            continue
        findings.append(
            ReviewFinding(
                section=section,
                severity="medium",
                issue_type=_issue_type(sentence),
                message=sentence[:500],
                recommended_action=f"Patch the {section} section in place without adding editorial notes.",
            )
        )

    if not findings and review.strip():
        findings.append(
            ReviewFinding(
                section="chapter",
                severity="low",
                issue_type="general_review",
                message="Review contains general improvement guidance but no specific required section was detected.",
                recommended_action="Apply only clear, reader-facing improvements; do not append editorial notes.",
            )
        )
    return findings


def write_structured_findings(chapter: int, review: str) -> Path:
    """Write review findings as JSON for deterministic repair/revision."""
    path = review_findings_path(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "chapter": chapter,
        "findings": [asdict(finding) for finding in extract_structured_findings(review)],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def review_chapter(chapter: int) -> Path:
    """Review a chapter draft using the configured reviewer model."""
    metadata = resolve_chapter(chapter)
    prompt_path = PROMPT_PATH
    draft_path = metadata.draft_path
    review_path = metadata.review_path

    ensure_required_file(prompt_path, "chapter review prompt")
    ensure_required_file(draft_path, "chapter draft")

    prompt = prompt_path.read_text(encoding="utf-8")
    draft = draft_path.read_text(encoding="utf-8")

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Review this chapter draft:\n\n{draft}"},
    ]

    from src import llm_gateway

    review = llm_gateway.call_llm(role="reviewer", messages=messages, chapter=metadata.number)

    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(review, encoding="utf-8")
    write_structured_findings(metadata.number, review)
    return review_path
