"""Small YAML helper for the handbook registry schema.

This is intentionally limited. PyYAML remains preferred when installed.
"""

from __future__ import annotations

from typing import Any


def _scalar(value: str) -> Any:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def _parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index

    is_list = lines[index][0] == indent and lines[index][1].startswith("- ")
    if is_list:
        values = []
        while index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
            values.append(_scalar(lines[index][1][2:]))
            index += 1
        return values, index

    values: dict[str, Any] = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"Unexpected indentation near: {content}")
        if ":" not in content:
            raise ValueError(f"Invalid YAML line: {content}")

        key, raw_value = content.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        index += 1
        if raw_value:
            values[key] = _scalar(raw_value)
        else:
            child_indent = indent + 2
            if index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- "):
                child_indent = indent
            values[key], index = _parse_block(lines, index, child_indent)
    return values, index


def safe_load(text: str) -> Any:
    """Parse the limited YAML subset used by handbook.yaml."""
    lines = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, raw_line.strip()))
    parsed, index = _parse_block(lines, 0, 0)
    if index != len(lines):
        raise ValueError("Could not parse full YAML document.")
    return parsed


def _format_scalar(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if text == "":
        return "''"
    if text.replace(".", "", 1).isdigit():
        return f'"{text}"'
    return text


def _dump_value(value: Any, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_value(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_scalar(item)}")
        return lines
    if isinstance(value, list):
        return [f"{prefix}- {_format_scalar(item)}" for item in value]
    return [f"{prefix}{_format_scalar(value)}"]


def safe_dump(value: Any, sort_keys: bool = False, allow_unicode: bool = False) -> str:
    """Dump the limited YAML subset used by handbook.yaml."""
    return "\n".join(_dump_value(value, 0)) + "\n"
