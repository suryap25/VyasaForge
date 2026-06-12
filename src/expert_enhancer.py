"""Expert-level chapter enrichment pass."""

from __future__ import annotations

from pathlib import Path

from src import llm_gateway
from src.handbook import resolve_chapter
from src.publish_gate import validate_publish_quality
from src.structural_qa import structural_qa_markdown
from src.validator import REQUIRED_SECTIONS, count_words, has_section

PROMPT_PATH = Path("prompts/chapter_expert_enhancement.md")
ENHANCED_DIR = Path("chapters/enhanced")
FAILED_DIR = Path("reviews")


def enhanced_path_for(chapter: int) -> Path:
    """Return the expert-enhanced chapter path."""
    return ENHANCED_DIR / f"chapter-{chapter:02d}.md"


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


def _missing_required_sections(markdown: str) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if not has_section(markdown, section)]


def enhance_chapter(chapter: int, source_path: Path) -> Path:
    """Create an expert-enhanced chapter artifact from a validated source."""
    metadata = resolve_chapter(chapter)
    if not source_path.exists():
        raise FileNotFoundError(f"Missing enhancement source chapter: {source_path}")
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Missing expert enhancement prompt: {PROMPT_PATH}")

    original = source_path.read_text(encoding="utf-8")
    original_word_count = count_words(original)
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Chapter: {metadata.title}\n\n"
                "Improve this chapter while preserving its structure:\n\n"
                f"{original}"
            ),
        },
    ]
    enhanced = _clean_markdown(
        llm_gateway.call_llm(role="expert", messages=messages, chapter=metadata.number)
    )

    failures: list[str] = []
    if count_words(enhanced) < int(original_word_count * 0.95):
        failures.append(
            f"enhanced chapter is shorter than 95% of source word count "
            f"(source: {original_word_count}, enhanced: {count_words(enhanced)})"
        )
    missing_sections = _missing_required_sections(enhanced)
    if missing_sections:
        failures.append("enhanced chapter is missing required sections: " + ", ".join(missing_sections))

    publish_result = validate_publish_quality(enhanced, allow_sketchnote_placeholder=True)
    if not publish_result.passed:
        failures.extend(publish_result.errors)

    structural_result = structural_qa_markdown(enhanced)
    if not structural_result.passed:
        failures.extend(structural_result.errors)

    if failures:
        FAILED_DIR.mkdir(parents=True, exist_ok=True)
        failed_path = FAILED_DIR / f"chapter-{chapter:02d}-enhancement-failed.md"
        failed_path.write_text(enhanced, encoding="utf-8")
        raise RuntimeError(
            "Expert enhancement rejected: "
            + "; ".join(failures)
            + f". Failed attempt saved to {failed_path}."
        )

    output_path = enhanced_path_for(chapter)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(enhanced, encoding="utf-8")
    return output_path
