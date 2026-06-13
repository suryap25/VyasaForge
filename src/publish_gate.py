"""Publish-quality structural checks for chapter Markdown."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

EDITORIAL_MARKER_PATTERNS = [
    r"(?im)^#{1,6}\s+Revision Additions\s*$",
    r"(?im)^#{1,6}\s+Corrections?\s*$",
    r"(?im)^#{1,6}\s+Enhancements?\s*$",
    r"(?im)^#{1,6}\s+Revision Notes?\s*$",
    r"(?im)^\s*(Correction|Enhancement|Location|Recommended Action)\s*:",
    r"(?im)\b(add|insert|place)\s+(this|the following)\s+(after|before|under)\b",
    r"(?im)\bTODO\b|\bFIXME\b",
]
REQUIRED_SECTION_NAMES = [
    "Learning Objectives",
    "Conceptual Foundation",
    "Architecture Perspective",
    "AppSec Lens",
    "Developer Lens",
    "Pentest Lens",
    "Common Findings",
    "Secure Design Guidance",
    "Interview Questions",
    "Key Takeaways",
]


@dataclass(frozen=True)
class PublishGateResult:
    """Publish gate result for one Markdown artifact."""

    passed: bool
    word_count: int
    errors: list[str]


def strip_front_matter(markdown: str) -> str:
    """Remove YAML front matter when present."""
    lines = markdown.splitlines()
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return "\n".join(lines[index + 1 :])
    return markdown


def heading_counts(markdown: str) -> dict[str, int]:
    """Return counts for H2 required-section headings."""
    markdown = strip_fenced_code(markdown)
    counts = {section: 0 for section in REQUIRED_SECTION_NAMES}
    for match in re.finditer(r"(?m)^##\s+(.+?)\s*$", markdown):
        heading = match.group(1).strip()
        if heading in counts:
            counts[heading] += 1
    return counts


def count_markdown_words(text: str) -> int:
    """Count words in Markdown text without importing the chapter validator."""
    return len(re.findall(r"\b[\w'-]+\b", text))


def code_fence_count(markdown: str) -> int:
    """Return the number of fenced code markers."""
    return len(re.findall(r"(?m)^```", markdown))


def strip_fenced_code(markdown: str) -> str:
    """Remove fenced code blocks for structural heading checks."""
    return re.sub(r"(?ms)^```.*?^```", "", markdown)


def has_heading_hierarchy_jump(markdown: str) -> bool:
    """Return true if heading levels jump by more than one."""
    markdown = strip_fenced_code(markdown)
    levels = [len(match.group(1)) for match in re.finditer(r"(?m)^(#{1,6})\s+", markdown)]
    previous = None
    for level in levels:
        if previous is not None and level > previous + 1:
            return True
        previous = level
    return False


def editorial_marker_errors(markdown: str) -> list[str]:
    """Return editorial artifact errors."""
    markdown = strip_fenced_code(markdown)
    errors = []
    for pattern in EDITORIAL_MARKER_PATTERNS:
        match = re.search(pattern, markdown)
        if match:
            marker = re.sub(r"\s+", " ", match.group(0).strip())
            errors.append(f"Forbidden editorial marker found: {marker}")
    return errors


def validate_publish_quality(
    markdown: str,
    check_required_section_duplicates: bool = True,
) -> PublishGateResult:
    """Validate Markdown is clean enough for final publication."""
    body = strip_front_matter(markdown)
    errors: list[str] = []

    if code_fence_count(body) % 2 != 0:
        errors.append("Unbalanced fenced code block markers.")

    if has_heading_hierarchy_jump(body):
        errors.append("Heading hierarchy jumps by more than one level.")

    if check_required_section_duplicates:
        for section, count in heading_counts(body).items():
            if count > 1:
                errors.append(f"Required section appears more than once: {section}")

    errors.extend(editorial_marker_errors(body))

    return PublishGateResult(
        passed=not errors,
        word_count=count_markdown_words(body),
        errors=errors,
    )


def validate_publish_file(path: Path) -> PublishGateResult:
    """Validate a Markdown file for publication."""
    if not path.exists():
        return PublishGateResult(False, 0, [f"Missing publish file: {path}"])
    return validate_publish_quality(path.read_text(encoding="utf-8"))


def assert_publishable(path: Path) -> None:
    """Raise a clear error if a Markdown file fails the publish gate."""
    result = validate_publish_file(path)
    if result.passed:
        return
    raise RuntimeError("Publish gate failed for " + str(path) + ": " + "; ".join(result.errors))
