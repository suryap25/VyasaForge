"""Deterministic structural QA for generated chapters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.publish_gate import strip_fenced_code, strip_front_matter
from src.validator import REQUIRED_SECTIONS, count_words


@dataclass(frozen=True)
class StructuralQAResult:
    """Structural quality result for one Markdown chapter."""

    passed: bool
    word_count: int
    duplicate_headings: list[str]
    duplicate_required_sections: list[str]
    required_sections_out_of_order: list[str]
    hierarchy_errors: list[str]
    repeated_diagram_patterns: bool
    errors: list[str]


def heading_entries(markdown: str) -> list[tuple[int, str]]:
    """Return Markdown heading levels and titles outside fenced code."""
    body = strip_fenced_code(strip_front_matter(markdown))
    return [
        (len(match.group(1)), match.group(2).strip())
        for match in re.finditer(r"(?m)^(#{1,6})\s+(.+?)\s*$", body)
    ]


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    original_case: dict[str, str] = {}
    for value in values:
        key = value.casefold()
        original_case.setdefault(key, value)
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    return [original_case[key] for key in sorted(duplicates)]


def _required_order_errors(headings: list[str]) -> list[str]:
    positions: list[tuple[str, int]] = []
    for section in REQUIRED_SECTIONS:
        try:
            positions.append((section, headings.index(section)))
        except ValueError:
            continue

    errors: list[str] = []
    previous_position = -1
    previous_section = ""
    for section, position in positions:
        if position < previous_position:
            errors.append(f"{section} appears before {previous_section}")
        previous_position = position
        previous_section = section
    return errors


def _hierarchy_errors(entries: list[tuple[int, str]]) -> list[str]:
    errors: list[str] = []
    previous_level: int | None = None
    for level, title in entries:
        if previous_level is not None and level > previous_level + 1:
            errors.append(f"Heading '{title}' jumps from H{previous_level} to H{level}")
        previous_level = level
    return errors


def _repeated_diagram_patterns(markdown: str) -> bool:
    images = re.findall(
        r"!\[[^\]]*(?:Sketchnote|Architecture diagram)[^\]]*\]\(([^)]+)\)",
        markdown,
        flags=re.IGNORECASE,
    )
    if len(images) < 3:
        return False
    normalized = [Path(image).name.replace("chapter-", "").replace(".png", "").replace(".svg", "") for image in images]
    return len(set(normalized)) <= 2


def structural_qa_markdown(markdown: str) -> StructuralQAResult:
    """Run deterministic structural QA against chapter Markdown."""
    body = strip_front_matter(markdown)
    entries = heading_entries(body)
    h2_headings = [title for level, title in entries if level == 2]

    duplicate_headings = _duplicates(h2_headings)
    duplicate_required_sections = [
        section
        for section in REQUIRED_SECTIONS
        if sum(1 for heading in h2_headings if heading == section) > 1
    ]
    required_sections_out_of_order = _required_order_errors(h2_headings)
    hierarchy_errors = _hierarchy_errors(entries)
    repeated_diagram_patterns = _repeated_diagram_patterns(body)

    errors: list[str] = []
    for heading in duplicate_headings:
        errors.append(f"Duplicate heading: {heading}")
    for section in duplicate_required_sections:
        errors.append(f"Duplicate required section: {section}")
    for order_error in required_sections_out_of_order:
        errors.append(f"Required section order issue: {order_error}")
    errors.extend(hierarchy_errors)
    if repeated_diagram_patterns:
        errors.append("Repeated diagram image pattern detected.")

    return StructuralQAResult(
        passed=not errors,
        word_count=count_words(body),
        duplicate_headings=duplicate_headings,
        duplicate_required_sections=duplicate_required_sections,
        required_sections_out_of_order=required_sections_out_of_order,
        hierarchy_errors=hierarchy_errors,
        repeated_diagram_patterns=repeated_diagram_patterns,
        errors=errors,
    )


def structural_qa_file(path: Path) -> StructuralQAResult:
    """Run structural QA against a Markdown file."""
    if not path.exists():
        return StructuralQAResult(
            passed=False,
            word_count=0,
            duplicate_headings=[],
            duplicate_required_sections=[],
            required_sections_out_of_order=[],
            hierarchy_errors=[],
            repeated_diagram_patterns=False,
            errors=[f"Missing chapter file: {path}"],
        )
    return structural_qa_markdown(path.read_text(encoding="utf-8"))
