"""Reference enrichment pass for handbook chapters."""

from __future__ import annotations

import re
from pathlib import Path

from src import llm_gateway
from src.handbook import resolve_chapter
from src.publish_gate import validate_publish_quality
from src.structural_qa import structural_qa_markdown
from src.validator import REQUIRED_SECTIONS, count_words, has_section
from src.workspace import workspace_path

PROMPT_PATH = Path("prompts/chapter_references.md")


def referenced_path_for(chapter: int) -> Path:
    """Return the reference-enriched chapter path."""
    return workspace_path("chapters", "referenced", f"chapter-{chapter:02d}.md")


def _clean_markdown(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _reference_count(markdown: str) -> int:
    match = re.search(r"(?ims)^##\s+References\s*$(.*?)(?=^##\s+|\Z)", markdown)
    if not match:
        return 0
    return len(re.findall(r"(?m)^\s*[-*]\s+", match.group(1)))


def _missing_required_sections(markdown: str) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if not has_section(markdown, section)]


def add_references(chapter: int, source_path: Path) -> Path:
    """Create a reference-enriched chapter artifact from a validated source."""
    metadata = resolve_chapter(chapter)
    if not source_path.exists():
        raise FileNotFoundError(f"Missing reference source chapter: {source_path}")
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Missing references prompt: {PROMPT_PATH}")

    original = source_path.read_text(encoding="utf-8")
    original_word_count = count_words(original)
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Chapter: {metadata.title}\n\n"
                "Add a references section to this chapter:\n\n"
                f"{original}"
            ),
        },
    ]
    referenced = _clean_markdown(
        llm_gateway.call_llm(role="fact_checker", messages=messages, chapter=metadata.number)
    )

    failures: list[str] = []
    if count_words(referenced) < original_word_count:
        failures.append(
            f"referenced chapter is shorter than source word count "
            f"(source: {original_word_count}, referenced: {count_words(referenced)})"
        )
    missing_sections = _missing_required_sections(referenced)
    if missing_sections:
        failures.append("referenced chapter is missing required sections: " + ", ".join(missing_sections))
    if _reference_count(referenced) < 3:
        failures.append("referenced chapter has fewer than 3 reference entries")

    publish_result = validate_publish_quality(referenced)
    if not publish_result.passed:
        failures.extend(publish_result.errors)

    structural_result = structural_qa_markdown(referenced)
    structural_errors = [
        error for error in structural_result.errors
        if not error.startswith("Duplicate heading: References")
    ]
    if structural_errors:
        failures.extend(structural_errors)

    if failures:
        failed_path = workspace_path("reviews", f"chapter-{chapter:02d}-references-failed.md")
        failed_path.parent.mkdir(parents=True, exist_ok=True)
        failed_path.write_text(referenced, encoding="utf-8")
        raise RuntimeError(
            "Reference enrichment rejected: "
            + "; ".join(failures)
            + f". Failed attempt saved to {failed_path}."
        )

    output_path = referenced_path_for(chapter)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(referenced, encoding="utf-8")
    return output_path
