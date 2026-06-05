"""CLI entrypoint for handbook utilities."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

try:
    import typer
except ImportError:
    typer = None


def _test_model(role: str) -> None:
    from src.llm_gateway import call_llm

    response = call_llm(
        role=role,
        messages=[
            {
                "role": "user",
                "content": "Reply with one short sentence confirming the model is reachable.",
            }
        ],
    )
    print(response)


def _write_chapter(chapter: int) -> None:
    from src.writer import write_chapter

    draft_path = write_chapter(chapter)
    print(f"Wrote draft: {Path(draft_path)}")


def _validate_chapter(chapter: int, stage: str = "drafts") -> None:
    from src.validator import validate_chapter

    result = validate_chapter(chapter, stage=stage)
    status = "PASS" if result.passed else "FAIL"

    print(f"{status}: {result.chapter_path}")
    print(f"Stage: {result.stage}")
    print(f"Word count: {result.word_count}")

    if result.missing_sections:
        print("Missing sections:")
        for section in result.missing_sections:
            print(f"- {section}")

    for error in result.errors:
        if not error.startswith("Missing required section:"):
            print(f"- {error}")

    if not result.passed:
        raise SystemExit(1)


def _review_chapter(chapter: int) -> None:
    from src.reviewer import review_chapter

    review_path = review_chapter(chapter)
    print(f"Wrote review: {Path(review_path)}")


def _revise_chapter(chapter: int) -> None:
    from src.reviser import revise_chapter

    revised_path = revise_chapter(chapter)
    print(f"Wrote revised chapter: {Path(revised_path)}")


def _finalize_chapter(chapter: int) -> None:
    from src.finalizer import finalize_chapter

    final_path = finalize_chapter(chapter)
    print(f"Wrote final chapter: {Path(final_path)}")


def _compile_docx(chapters: str) -> None:
    from src.compiler import compile_docx

    try:
        chapter_numbers = [int(chapter.strip()) for chapter in chapters.split(",") if chapter.strip()]
    except ValueError as exc:
        raise ValueError("--chapters must contain chapter numbers, such as 1 or 1,2.") from exc

    if not chapter_numbers:
        raise ValueError("--chapters must include at least one chapter number.")

    output_path = compile_docx(chapter_numbers)
    print(f"Wrote DOCX: {Path(output_path)}")


def _run_argparse() -> None:
    parser = argparse.ArgumentParser(description="AppSec handbook agent utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    test_model_parser = subparsers.add_parser("test-model")
    test_model_parser.add_argument("--role", default="writer")

    write_parser = subparsers.add_parser("write-chapter")
    write_parser.add_argument("--chapter", type=int, required=True)

    validate_parser = subparsers.add_parser("validate-chapter")
    validate_parser.add_argument("--chapter", type=int, required=True)
    validate_parser.add_argument("--stage", default="drafts")

    review_parser = subparsers.add_parser("review-chapter")
    review_parser.add_argument("--chapter", type=int, required=True)

    revise_parser = subparsers.add_parser("revise-chapter")
    revise_parser.add_argument("--chapter", type=int, required=True)

    finalize_parser = subparsers.add_parser("finalize-chapter")
    finalize_parser.add_argument("--chapter", type=int, required=True)

    compile_parser = subparsers.add_parser("compile-docx")
    compile_parser.add_argument("--chapters", required=True)

    args = parser.parse_args()
    commands: dict[str, Callable[[], None]] = {
        "test-model": lambda: _test_model(args.role),
        "write-chapter": lambda: _write_chapter(args.chapter),
        "validate-chapter": lambda: _validate_chapter(args.chapter, args.stage),
        "review-chapter": lambda: _review_chapter(args.chapter),
        "revise-chapter": lambda: _revise_chapter(args.chapter),
        "finalize-chapter": lambda: _finalize_chapter(args.chapter),
        "compile-docx": lambda: _compile_docx(args.chapters),
    }

    try:
        commands[args.command]()
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.exit(status=1, message=f"ERROR: {exc}\n")


if typer is not None:
    app = typer.Typer(help="AppSec handbook agent utilities.")

    @app.command()
    def test_model(role: str = typer.Option("writer", "--role", help="Configured LLM role.")) -> None:
        """Send a tiny prompt through the configured model."""
        try:
            _test_model(role)
        except (RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def write_chapter(chapter: int = typer.Option(..., "--chapter", help="Chapter number to write.")) -> None:
        """Write a Markdown chapter draft."""
        try:
            _write_chapter(chapter)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def validate_chapter(
        chapter: int = typer.Option(..., "--chapter", help="Chapter number to validate."),
        stage: str = typer.Option("drafts", "--stage", help="Chapter stage: drafts, reviewed, or final."),
    ) -> None:
        """Validate a Markdown chapter file."""
        try:
            _validate_chapter(chapter, stage)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def review_chapter(chapter: int = typer.Option(..., "--chapter", help="Chapter number to review.")) -> None:
        """Review a Markdown chapter draft."""
        try:
            _review_chapter(chapter)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def revise_chapter(chapter: int = typer.Option(..., "--chapter", help="Chapter number to revise.")) -> None:
        """Revise a Markdown chapter draft using review comments."""
        try:
            _revise_chapter(chapter)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def finalize_chapter(chapter: int = typer.Option(..., "--chapter", help="Chapter number to finalize.")) -> None:
        """Copy a reviewed chapter into the final stage."""
        try:
            _finalize_chapter(chapter)
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def compile_docx(chapters: str = typer.Option(..., "--chapters", help="Comma-separated chapter numbers.")) -> None:
        """Compile final Markdown chapters into a DOCX file."""
        try:
            _compile_docx(chapters)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc


if __name__ == "__main__":
    if typer is None:
        _run_argparse()
    else:
        app()
