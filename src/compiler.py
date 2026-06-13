"""DOCX compiler using Pandoc."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from src.handbook import load_handbook_registry
from src.handbook import resolve_chapter
from src.publish_gate import validate_publish_quality
from src.qa import qa_handbook, write_qa_report

OUTPUT_PATH = Path("output/AppSec_Authentication_Authorization_Handbook_Phase1.docx")
TITLE = "AppSec Authentication & Authorization Handbook v2.0"
SUBTITLE = "Phase 1: Foundations & JWT"
SUPPORTED_FORMATS = {"docx", "pdf"}


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


def chapter_markdown_for_compile(chapter: int, chapter_path: Path) -> str:
    """Return chapter Markdown prepared for compilation."""
    return markdown_body(chapter_path.read_text(encoding="utf-8"))


def combined_markdown(chapters: list[int], chapter_paths: list[Path]) -> str:
    """Build one Markdown document for Pandoc conversion."""
    registry = load_handbook_registry()
    parts = [
        "---",
        f"title: {registry.title}",
        f"subtitle: Version {registry.version}",
        "author: appsec-handbook-agent",
        "toc-title: Table of Contents",
        "---",
        "",
        f"# {registry.title}",
        "",
        f"Version {registry.version}",
        "",
        "\\newpage",
    ]

    for index, chapter_path in enumerate(chapter_paths):
        if index > 0:
            parts.extend(["", "\\newpage", ""])
        parts.append(chapter_markdown_for_compile(chapters[index], chapter_path))

    return "\n".join(parts).strip() + "\n"


def output_path_for(output_format: str) -> Path:
    """Return the v2 handbook compiler output path."""
    if output_format == "docx":
        return OUTPUT_PATH
    return Path("output/AppSec_Authentication_Authorization_Handbook_Phase1.pdf")


def compile_handbook(chapters: list[int], output_format: str = "docx") -> Path:
    """Compile final Markdown chapters into a native document with Pandoc."""
    if output_format not in SUPPORTED_FORMATS:
        available = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(f"Unsupported output format '{output_format}'. Available formats: {available}")

    chapter_paths = [resolve_chapter(chapter).final_path for chapter in chapters]
    for chapter_path in chapter_paths:
        if not chapter_path.exists():
            raise FileNotFoundError(f"Missing final chapter: {chapter_path}")

    qa_result = qa_handbook(chapters, stage="final")
    write_qa_report(qa_result)
    if not qa_result.passed:
        raise RuntimeError("Publish QA failed. See reports/handbook-qa.md for details.")

    for chapter, chapter_path in zip(chapters, chapter_paths):
        chapter_content = chapter_markdown_for_compile(chapter, chapter_path)
        gate_result = validate_publish_quality(chapter_content)
        if not gate_result.passed:
            raise RuntimeError(
                f"Compile-time publish gate failed for chapter {chapter}: "
                + "; ".join(gate_result.errors)
            )

    pandoc = pandoc_path()
    output_path = output_path_for(output_format)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined_path = output_path.parent / "pandoc-input.md"
    combined_content = combined_markdown(chapters, chapter_paths)
    gate_result = validate_publish_quality(
        combined_content,
        check_required_section_duplicates=False,
    )
    if not gate_result.passed:
        raise RuntimeError("Compile-time publish gate failed: " + "; ".join(gate_result.errors))
    combined_path.write_text(combined_content, encoding="utf-8")

    try:
        command = [
            pandoc,
            str(combined_path),
            "--standalone",
            "--from",
            "markdown",
            "--to",
            output_format,
            "--toc",
            "--number-sections",
            "--metadata",
            "link-citations=true",
            "--output",
            str(output_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        stderr = completed.stderr.strip()
        if completed.returncode != 0:
            raise RuntimeError(f"Pandoc {output_format.upper()} compilation failed: {stderr or 'no error output'}")
    finally:
        combined_path.unlink(missing_ok=True)

    return output_path


def compile_docx(chapters: list[int]) -> Path:
    """Compile final Markdown chapters into a native DOCX file with Pandoc."""
    return compile_handbook(chapters, output_format="docx")
