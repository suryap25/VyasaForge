"""Chapter reviser for Milestone M6."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.handbook import resolve_chapter
from src.publish_gate import validate_publish_quality
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


def review_findings_path(chapter: int) -> Path:
    """Return structured review findings path."""
    return Path("reviews") / f"chapter-{chapter:02d}-review.json"


def extract_json_payload(text: str) -> object:
    """Extract a JSON payload from raw model text."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = min(
        [index for index in [stripped.find("{"), stripped.find("[")] if index >= 0],
        default=-1,
    )
    if start > 0:
        stripped = stripped[start:]
    return json.loads(stripped)


def load_review_findings(chapter: int) -> list[dict[str, str]]:
    """Load machine-readable review findings if available."""
    path = review_findings_path(chapter)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        return []
    return [finding for finding in findings if isinstance(finding, dict)]


def section_pattern(section: str) -> str:
    """Return a regex pattern for one H2 section."""
    return rf"(?ims)^##\s+{re.escape(section)}\s*$.*?(?=^##\s+|\Z)"


def get_section(markdown: str, section: str) -> str | None:
    """Return a section including its H2 heading."""
    match = re.search(section_pattern(section), markdown)
    return match.group(0).strip() if match else None


def replace_section(markdown: str, section: str, replacement: str) -> str:
    """Replace one H2 section in Markdown."""
    replacement = replacement.strip()
    if not replacement.startswith(f"## {section}"):
        replacement = f"## {section}\n\n{replacement}"
    if re.search(section_pattern(section), markdown):
        return re.sub(section_pattern(section), replacement, markdown, count=1)
    return markdown.rstrip() + "\n\n" + replacement + "\n"


def normalize_patches(payload: object) -> list[dict[str, str]]:
    """Normalize patch JSON into section/content dictionaries."""
    if isinstance(payload, dict):
        raw_patches = payload.get("patches", [])
    else:
        raw_patches = payload
    if not isinstance(raw_patches, list):
        raise ValueError("Revision response must contain a JSON list of patches.")

    patches: list[dict[str, str]] = []
    for raw_patch in raw_patches:
        if not isinstance(raw_patch, dict):
            continue
        section = str(raw_patch.get("section", "")).strip()
        content = str(raw_patch.get("content_markdown", raw_patch.get("content", ""))).strip()
        if section in REQUIRED_SECTIONS and content:
            patches.append({"section": section, "content": content})
    return patches


def revise_chapter(chapter: int) -> Path:
    """Revise a chapter draft by patching reviewed sections in place."""
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
    findings = load_review_findings(metadata.number)
    original_word_count = count_words(draft)
    target_sections = sorted(
        {
            finding.get("section", "")
            for finding in findings
            if finding.get("section") in REQUIRED_SECTIONS
        },
        key=REQUIRED_SECTIONS.index,
    )
    if not target_sections:
        target_sections = [section for section in REQUIRED_SECTIONS if section != "Sketchnote Placeholder"]

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                "INPUTS:\n\n"
                "Original Chapter:\n"
                f"{draft}\n\n"
                "Structured Review Findings JSON:\n"
                f"{json.dumps(findings, indent=2)}\n\n"
                "Human Review Comments:\n"
                f"{review}\n\n"
                "Target Sections:\n"
                + "\n".join(f"- {section}" for section in target_sections)
                + "\n\n"
                "INSTRUCTION:\n"
                "Patch the chapter in place by returning only replacement content for target sections.\n"
                "Do not append a Revision Additions section.\n"
                "Do not include editorial labels such as Correction, Enhancement, Location, or Add after.\n"
                "Each replacement must be reader-facing handbook content.\n"
                "Each replacement must preserve the section heading as Markdown H2.\n\n"
                "Return strictly valid JSON in this shape:\n"
                "{\n"
                '  "patches": [\n'
                '    {"section": "Developer Lens", "content_markdown": "## Developer Lens\\n\\n..."}\n'
                "  ]\n"
                "}\n"
            ),
        },
    ]

    from src import llm_gateway

    patch_response = llm_gateway.call_llm(role="editor", messages=messages, chapter=metadata.number)
    try:
        patches = normalize_patches(extract_json_payload(patch_response))
    except Exception as exc:
        failed_revision_path.parent.mkdir(parents=True, exist_ok=True)
        failed_revision_path.write_text(patch_response, encoding="utf-8")
        raise RuntimeError(f"Revision patch response was not valid JSON. Failed attempt saved to {failed_revision_path}.") from exc

    if not patches:
        failed_revision_path.parent.mkdir(parents=True, exist_ok=True)
        failed_revision_path.write_text(patch_response, encoding="utf-8")
        raise RuntimeError(f"Revision returned no usable section patches. Failed attempt saved to {failed_revision_path}.")

    revised = draft
    for patch in patches:
        revised = replace_section(revised, patch["section"], patch["content"])

    revised_word_count = count_words(revised)
    missing_sections = missing_required_sections(revised)
    too_short = revised_word_count < original_word_count * MIN_REVISED_WORD_RATIO
    publish_result = validate_publish_quality(revised, allow_sketchnote_placeholder=True)

    if too_short or missing_sections or not publish_result.passed:
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
        if not publish_result.passed:
            failures.append("publish gate failed: " + "; ".join(publish_result.errors))
        raise RuntimeError(
            "Revision safety gate failed: "
            + "; ".join(failures)
            + ". "
            f"Failed attempt saved to {failed_revision_path}."
        )

    revised_path.parent.mkdir(parents=True, exist_ok=True)
    revised_path.write_text(revised, encoding="utf-8")
    return revised_path
