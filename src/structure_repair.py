"""Deterministic Markdown structure normalization."""

from __future__ import annotations

import re

from src.publish_gate import strip_front_matter
from src.validator import REQUIRED_SECTIONS


def _front_matter(markdown: str) -> tuple[str, str]:
    lines = markdown.splitlines()
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return "\n".join(lines[: index + 1]).strip() + "\n\n", "\n".join(lines[index + 1 :])
    return "", markdown


def _heading_title(line: str) -> str | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return None
    return match.group(2).strip().strip("#").strip()


def _demote_internal_headings(lines: list[str]) -> list[str]:
    output: list[str] = []
    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            output.append(line)
            continue

        level = len(match.group(1))
        title = match.group(2).strip().strip("#").strip()
        if title in REQUIRED_SECTIONS:
            continue
        if level <= 2:
            output.append(f"### {title}")
        else:
            output.append(line)
    return output


def normalize_required_sections(markdown: str) -> str:
    """Canonicalize required handbook sections as one ordered set of H2 headings."""
    front_matter, body = _front_matter(markdown)
    lines = strip_front_matter(body).splitlines()
    required_set = set(REQUIRED_SECTIONS)
    first_required_index = next(
        (index for index, line in enumerate(lines) if _heading_title(line) in required_set),
        None,
    )
    if first_required_index is None:
        return markdown.strip() + "\n"

    preamble = lines[:first_required_index]
    sections: dict[str, list[list[str]]] = {section: [] for section in REQUIRED_SECTIONS}
    current_section: str | None = None
    current_lines: list[str] = []

    for line in lines[first_required_index:]:
        title = _heading_title(line)
        if title in required_set:
            if current_section is not None:
                sections[current_section].append(current_lines)
            current_section = title
            current_lines = []
            continue
        current_lines.append(line)

    if current_section is not None:
        sections[current_section].append(current_lines)

    output: list[str] = [line for line in preamble if line.strip()]
    for section in REQUIRED_SECTIONS:
        blocks = sections.get(section, [])
        if not blocks:
            continue
        output.extend(["", f"## {section}", ""])
        section_lines: list[str] = []
        for block in blocks:
            cleaned = _demote_internal_headings(block)
            while cleaned and not cleaned[0].strip():
                cleaned = cleaned[1:]
            while cleaned and not cleaned[-1].strip():
                cleaned = cleaned[:-1]
            if cleaned:
                if section_lines:
                    section_lines.append("")
                section_lines.extend(cleaned)
        output.extend(section_lines)

    normalized = "\n".join(output).strip() + "\n"
    return front_matter + normalized
