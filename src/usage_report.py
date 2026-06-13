"""LLM usage reporting utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

USAGE_LOG_PATH = Path("logs/llm-usage.jsonl")


def load_usage_records(path: Path | None = None) -> list[dict[str, Any]]:
    """Load LLM usage JSONL records."""
    if path is None:
        try:
            from src.workspace import workspace_path

            path = workspace_path("logs", "llm-usage.jsonl")
        except Exception:
            path = USAGE_LOG_PATH
    if not path.exists():
        return []

    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def usage_summary(chapter: int | None = None) -> str:
    """Return a formatted usage summary grouped by role and model."""
    records = load_usage_records()
    if chapter is not None:
        records = [record for record in records if record.get("chapter") == chapter]

    if not records:
        scope = f"chapter {chapter}" if chapter is not None else "all chapters"
        return f"No LLM usage records found for {scope}."

    rows: dict[tuple[str, str], dict[str, int | str | None]] = {}
    unknown_records = 0
    for record in records:
        role = str(record.get("role", "-"))
        model = str(record.get("model", "-"))
        key = (role, model)
        row = rows.setdefault(
            key,
            {
                "role": role,
                "model": model,
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
        )
        row["calls"] = int(row["calls"]) + 1

        input_tokens = record.get("input_tokens")
        output_tokens = record.get("output_tokens")
        total_tokens = record.get("total_tokens")
        if input_tokens is None or output_tokens is None or total_tokens is None:
            unknown_records += 1

        row["input_tokens"] = int(row["input_tokens"]) + int(input_tokens or 0)
        row["output_tokens"] = int(row["output_tokens"]) + int(output_tokens or 0)
        row["total_tokens"] = int(row["total_tokens"]) + int(total_tokens or 0)

    headers = ["Role", "Model", "Calls", "Input", "Output", "Total"]
    data_rows = [
        [
            row["role"],
            row["model"],
            row["calls"],
            row["input_tokens"],
            row["output_tokens"],
            row["total_tokens"],
        ]
        for row in rows.values()
    ]
    widths = [max(len(str(row[index])) for row in data_rows + [headers]) for index in range(len(headers))]
    lines = [
        " | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)),
        "-+-".join("-" * width for width in widths),
    ]
    for row in data_rows:
        lines.append(" | ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))

    total_input = sum(int(row[3]) for row in data_rows)
    total_output = sum(int(row[4]) for row in data_rows)
    total_tokens = sum(int(row[5]) for row in data_rows)
    lines.extend(
        [
            "",
            f"Total input tokens: {total_input}",
            f"Total output tokens: {total_output}",
            f"Total tokens: {total_tokens}",
        ]
    )
    if unknown_records:
        lines.append(f"Records with unavailable token data: {unknown_records}")
    return "\n".join(lines)
