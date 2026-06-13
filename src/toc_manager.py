"""Handbook TOC planning and update utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src import llm_gateway
from src.handbook import load_handbook_registry
from src.workspace import active_registry_path, registry_path_for, set_active_handbook, workspace_path, workspace_slug

PLANNING_PROMPT_PATH = Path("prompts/handbook_planning.md")
TOC_CLARIFICATION_PROMPT_PATH = Path("prompts/toc_clarification.md")
TOC_UPDATE_PROMPT_PATH = Path("prompts/toc_update.md")


def _load_yaml() -> Any:
    try:
        import yaml
    except ImportError:
        from src import simple_yaml as yaml
    return yaml


def _extract_yaml(text: str) -> str:
    """Extract YAML from a plain or fenced LLM response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def _extract_json(text: str) -> str:
    """Extract JSON from a plain or fenced LLM response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def _chapter_paths(number: int) -> dict[str, str]:
    chapter_file = f"chapter-{number:02d}.md"
    return {
        "brief_path": f"chapters/briefs/{chapter_file}",
        "draft_path": f"chapters/drafts/{chapter_file}",
        "reviewed_path": f"chapters/reviewed/{chapter_file}",
        "final_path": f"chapters/final/{chapter_file}",
        "review_path": f"reviews/chapter-{number:02d}-review.md",
    }


def _normalize_registry(raw_registry: dict[str, Any]) -> dict[str, Any]:
    """Ensure generated registry YAML has all required pipeline fields."""
    handbook = raw_registry.get("handbook")
    if not isinstance(handbook, dict):
        raise ValueError("Generated registry must contain a 'handbook' mapping.")

    chapters = handbook.get("chapters")
    if not isinstance(chapters, dict) or not chapters:
        raise ValueError("Generated registry must contain handbook.chapters.")

    normalized_chapters = {}
    for index, (_, settings) in enumerate(chapters.items(), start=1):
        if not isinstance(settings, dict):
            raise ValueError(f"Chapter {index} must be a mapping.")
        chapter_id = f"chapter_{index:02d}"
        title = str(settings.get("title", f"Chapter {index:02d}")).strip()
        chapter_settings = {"number": index, "title": title}
        chapter_settings.update(_chapter_paths(index))
        normalized_chapters[chapter_id] = chapter_settings

    handbook["chapters"] = normalized_chapters
    handbook.setdefault("version", "1.0")
    handbook.setdefault("audience", ["Technical Practitioners"])
    handbook["recommended_chapter_count"] = len(normalized_chapters)
    handbook.setdefault(
        "recommendation_reason",
        "Selected to provide practical, non-overlapping coverage for the topic.",
    )
    if not handbook.get("title"):
        raise ValueError("Generated registry must include handbook.title.")
    return {"handbook": handbook}


def _registry_to_yaml(raw_registry: dict[str, Any]) -> str:
    yaml = _load_yaml()
    return yaml.safe_dump(raw_registry, sort_keys=False, allow_unicode=False)


def _save_registry(raw_registry: dict[str, Any], output_path: Path) -> Path:
    """Validate and save handbook registry YAML."""
    normalized = _normalize_registry(raw_registry)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_registry_to_yaml(normalized), encoding="utf-8")
    load_handbook_registry.cache_clear()
    load_handbook_registry(str(output_path))
    return output_path


def _load_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing prompt: {path}")
    return path.read_text(encoding="utf-8")


def _parse_yaml_response(response: str) -> dict[str, Any]:
    yaml = _load_yaml()
    parsed = yaml.safe_load(_extract_yaml(response))
    if not isinstance(parsed, dict):
        raise ValueError("LLM response did not contain a YAML mapping.")
    return parsed


def _parse_json_response(response: str) -> dict[str, Any]:
    parsed = json.loads(_extract_json(response))
    if not isinstance(parsed, dict):
        raise ValueError("LLM response did not contain a JSON object.")
    return parsed


def _planning_request(
    topic: str,
    chapters: int | None = None,
    audience: str | None = None,
    depth: str | None = None,
    pages: int | None = None,
) -> str:
    lines = [f"Topic: {topic}"]
    if chapters is None:
        lines.append("Chapter count: choose the best count for the topic.")
    else:
        lines.append(f"Chapter count: exactly {chapters}")
    if audience:
        lines.append(f"Audience: {audience}")
    if depth:
        lines.append(f"Depth: {depth}")
    if pages is not None:
        lines.append(f"Target pages: {pages}")
    return "\n".join(lines)


def plan_handbook(
    topic: str,
    chapters: int | None = None,
    audience: str | None = None,
    depth: str | None = None,
    pages: int | None = None,
    output_path: Path | None = None,
) -> Path:
    """Generate a handbook registry from a topic."""
    workspace_name = workspace_slug(topic)
    registry_output_path = output_path or registry_path_for(workspace_name)
    prompt = _load_prompt(PLANNING_PROMPT_PATH)
    response = llm_gateway.call_llm(
        role="planner",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": _planning_request(topic, chapters, audience, depth, pages)},
        ],
    )
    registry = _parse_yaml_response(response)
    registry_path = _save_registry(registry, output_path=registry_output_path)
    set_active_handbook(workspace_name)
    load_handbook_registry.cache_clear()
    load_handbook_registry(str(registry_path))
    return registry_path


def _write_clarification_questions(
    requirements_path: Path,
    questions: list[str],
    reason: str,
) -> Path:
    lines = [
        "# Handbook TOC Clarification Questions",
        "",
        f"Input file: {requirements_path}",
        "",
        "The requested TOC update was not applied because it requires clarification.",
        "",
        f"Reason: {reason}",
        "",
        "## Questions",
        "",
    ]
    lines.extend(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    lines.extend(
        [
            "",
            "Update the requirements file with answers, then rerun:",
            "",
            f"python -m src.cli update-toc --input {requirements_path}",
            "",
        ]
    )
    clarification_path = workspace_path("configs", "handbook-clarification-questions.md")
    clarification_path.parent.mkdir(parents=True, exist_ok=True)
    clarification_path.write_text("\n".join(lines), encoding="utf-8")
    return clarification_path


def _requirements_are_clear(
    current_registry: str,
    requirements: str,
    requirements_path: Path,
) -> tuple[bool, Path | None]:
    prompt = _load_prompt(TOC_CLARIFICATION_PROMPT_PATH)
    response = llm_gateway.call_llm(
        role="toc_editor",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Existing handbook.yaml:\n\n"
                    f"{current_registry}\n\n"
                    "Requested changes:\n\n"
                    f"{requirements}"
                ),
            },
        ],
    )
    analysis = _parse_json_response(response)
    status = str(analysis.get("status", "")).strip()
    if status == "clear":
        return (True, None)

    questions = analysis.get("questions")
    if not isinstance(questions, list) or not questions:
        questions = ["What exact TOC change should be applied without guessing?"]
    reason = str(analysis.get("reason", "The request requires clarification."))
    clarification_path = _write_clarification_questions(requirements_path, [str(q) for q in questions], reason)
    return (False, clarification_path)


def update_toc(requirements_path: Path, output_path: Path | None = None) -> tuple[Path, Path]:
    """Update the handbook registry using a user requirements file."""
    if not requirements_path.exists():
        raise FileNotFoundError(f"Missing user requirements file: {requirements_path}")

    registry_output_path = output_path or active_registry_path()
    current_registry = registry_output_path.read_text(encoding="utf-8")
    requirements = requirements_path.read_text(encoding="utf-8")
    clear, clarification_path = _requirements_are_clear(current_registry, requirements, requirements_path)
    if not clear:
        raise RuntimeError(f"TOC update needs clarification. Questions written to {clarification_path}.")

    prompt = _load_prompt(TOC_UPDATE_PROMPT_PATH)
    response = llm_gateway.call_llm(
        role="toc_editor",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Existing handbook.yaml:\n\n"
                    f"{current_registry}\n\n"
                    "Requested changes:\n\n"
                    f"{requirements}"
                ),
            },
        ],
    )
    registry = _parse_yaml_response(response)
    registry_path = _save_registry(registry, output_path=registry_output_path)
    change_summary_path = workspace_path("configs", "handbook-change-summary.md")
    change_summary_path.parent.mkdir(parents=True, exist_ok=True)
    change_summary_path.write_text(
        "# Handbook TOC Change Summary\n\n"
        f"Input file: {requirements_path}\n\n"
        "Applied requested TOC updates and validated the registry schema.\n",
        encoding="utf-8",
    )
    return registry_path, change_summary_path
