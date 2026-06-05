"""Chapter writer for Milestone M3."""

from __future__ import annotations

from pathlib import Path

from src import llm_gateway
from src.handbook import resolve_chapter

CONFIG_PATH = Path("configs/phase1.example.json")
PROMPT_PATH = Path("prompts/chapter_generation.md")


def ensure_required_file(path: Path, label: str) -> None:
    """Raise a clear error if a required file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def write_chapter(chapter: int) -> Path:
    """Write a chapter draft using the configured writer model."""
    metadata = resolve_chapter(chapter)
    config_path = CONFIG_PATH
    prompt_path = PROMPT_PATH
    brief_path = metadata.brief_path
    draft_path = metadata.draft_path

    ensure_required_file(config_path, "model configuration")
    ensure_required_file(prompt_path, "chapter generation prompt")
    ensure_required_file(brief_path, "chapter brief")

    prompt = prompt_path.read_text(encoding="utf-8")
    brief = brief_path.read_text(encoding="utf-8")

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Write the chapter from this brief:\n\n{brief}"},
    ]
    draft = llm_gateway.call_llm(role="writer", messages=messages, chapter=metadata.number)

    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(draft, encoding="utf-8")
    return draft_path
