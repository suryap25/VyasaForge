"""DOCX compiler using Pandoc."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from src.handbook import resolve_chapter

OUTPUT_PATH = Path("output/AppSec_Authentication_Authorization_Handbook_Phase1.docx")
TITLE = "AppSec Authentication & Authorization Handbook v2.0"
SUBTITLE = "Phase 1: Foundations & JWT"


def markdown_body(markdown: str) -> str:
    """Return Markdown body, skipping YAML front matter at the top."""
    lines = markdown.splitlines()
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return "\n".join(lines[index + 1 :]).strip()
    return markdown.strip()


def pandoc_path() -> str:
    """Return the Pandoc executable path or fail with a user-facing message."""
    executable = shutil.which("pandoc")
    if executable is None:
        message = (
            "Pandoc is required for DOCX compilation and was not found on PATH. "
            "Install Pandoc, then rerun `python -m src.cli compile-docx --chapters 1`. "
            "The pipeline stopped without creating a fallback DOCX."
        )
        print(message)
        raise RuntimeError(message)
    return executable


def combined_markdown(chapter_paths: list[Path]) -> str:
    """Build one Markdown document for Pandoc conversion."""
    parts = [
        f"# {TITLE}",
        "",
        SUBTITLE,
        "",
        "\\newpage",
        "",
    ]

    for index, chapter_path in enumerate(chapter_paths):
        if index > 0:
            parts.extend(["", "\\newpage", ""])
        parts.append(markdown_body(chapter_path.read_text(encoding="utf-8")))

    return "\n".join(parts).strip() + "\n"


def compile_docx(chapters: list[int]) -> Path:
    """Compile final Markdown chapters into a native DOCX file with Pandoc."""
    chapter_paths = [resolve_chapter(chapter).final_path for chapter in chapters]
    for chapter_path in chapter_paths:
        if not chapter_path.exists():
            raise FileNotFoundError(f"Missing final chapter: {chapter_path}")

    pandoc = pandoc_path()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined_path = OUTPUT_PATH.parent / "pandoc-input.md"
    combined_path.write_text(combined_markdown(chapter_paths), encoding="utf-8")

    try:
        command = [
            pandoc,
            str(combined_path),
            "--standalone",
            "--from",
            "markdown",
            "--to",
            "docx",
            "--output",
            str(OUTPUT_PATH),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            raise RuntimeError(f"Pandoc DOCX compilation failed: {stderr or 'no error output'}")
    finally:
        combined_path.unlink(missing_ok=True)

    return OUTPUT_PATH
