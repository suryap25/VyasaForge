"""CLI entrypoint for handbook utilities."""

from __future__ import annotations

import argparse
import os
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
    from src.state_manager import update_draft

    try:
        draft_path = write_chapter(chapter)
    except Exception as exc:
        update_draft(chapter, "failed")
        raise

    update_draft(chapter, "passed", Path(draft_path))
    print(f"Wrote draft: {Path(draft_path)}")


def _create_chapter(chapter: int, overwrite: bool = False) -> None:
    from src.briefs import create_chapter_brief

    brief_path = create_chapter_brief(chapter, overwrite=overwrite)
    print(f"Chapter brief ready: {Path(brief_path)}")


def _validate_chapter(chapter: int, stage: str = "drafts") -> None:
    from src.validator import resolve_chapter_stage_path, validate_chapter

    result = validate_chapter(chapter, stage=stage)
    chapter_path = resolve_chapter_stage_path(chapter, stage=stage)
    _print_validation_result(result, chapter_path, stage)

    if not result.passed:
        raise SystemExit(1)


def _print_validation_result(result: object, chapter_path: Path, stage: str) -> None:
    status = "PASS" if result.passed else "FAIL"

    print(f"{status}: {chapter_path}")
    print(f"Stage: {stage}")
    print(f"Word count: {result.word_count}")

    if result.missing_sections:
        print("Missing sections:")
        for section in result.missing_sections:
            print(f"- {section}")

    for error in result.errors:
        if not error.startswith("Missing required section:"):
            print(f"- {error}")


def _is_repairable_validation_failure(result: object, chapter_path: Path) -> bool:
    """Return true when validation failed only for section or word count issues."""
    if result.passed or not chapter_path.exists():
        return False
    return all(
        error.startswith("Missing required section:") or error.startswith("Word count is ")
        for error in result.errors
    )


def _review_chapter(chapter: int) -> None:
    from src.reviewer import review_chapter
    from src.state_manager import update_review

    try:
        review_path = review_chapter(chapter)
    except Exception as exc:
        update_review(chapter, "failed")
        raise

    update_review(chapter, "passed")
    print(f"Wrote review: {Path(review_path)}")


def _revise_chapter(chapter: int) -> None:
    from src.reviser import revise_chapter
    from src.state_manager import update_revision

    try:
        revised_path = revise_chapter(chapter)
    except Exception as exc:
        update_revision(chapter, "rejected", str(exc))
        raise

    update_revision(chapter, "passed")
    print(f"Wrote revised chapter: {Path(revised_path)}")


def _finalize_chapter(chapter: int, source: str = "reviewed") -> None:
    from src.finalizer import finalize_chapter
    from src.state_manager import update_final

    try:
        final_path = finalize_chapter(chapter, source=source)
    except Exception as exc:
        update_final(chapter, "failed", source=source)
        raise

    update_final(chapter, "passed", source=source, path=Path(final_path))
    print(f"Wrote final chapter: {Path(final_path)}")


def _compile_docx(chapters: str) -> None:
    from src.compiler import compile_docx
    from src.state_manager import update_docx

    try:
        chapter_numbers = [int(chapter.strip()) for chapter in chapters.split(",") if chapter.strip()]
    except ValueError as exc:
        raise ValueError("--chapters must contain chapter numbers, such as 1 or 1,2.") from exc

    if not chapter_numbers:
        raise ValueError("--chapters must include at least one chapter number.")

    try:
        output_path = compile_docx(chapter_numbers)
    except Exception as exc:
        for chapter in chapter_numbers:
            update_docx(chapter, "failed")
        raise

    for chapter in chapter_numbers:
        update_docx(chapter, "passed")
    print(f"Wrote DOCX: {Path(output_path)}")


def _repair_chapter(chapter: int, stage: str = "drafts") -> None:
    from src.repairer import repair_chapter

    chapter_path = repair_chapter(chapter, stage=stage)
    print(f"Repaired chapter: {Path(chapter_path)}")


def _show_state(chapter: int) -> None:
    from src.state_manager import formatted_state

    print(formatted_state(chapter))


def _display_status(status: str | None, generated_label: bool = False) -> str:
    """Return compact dashboard status text."""
    if status == "passed":
        return "GENERATED" if generated_label else "PASS"
    if status == "failed":
        return "FAIL"
    if status == "rejected":
        return "REJECTED"
    if status == "not_started" or status is None:
        return "-"
    return status.upper()


def _handbook_status() -> None:
    import json

    state_dir = Path("chapters/state")
    rows = []
    completed = 0

    for state_file in sorted(state_dir.glob("chapter-*.json")):
        state = json.loads(state_file.read_text(encoding="utf-8"))
        final_status = _display_status(state.get("final", {}).get("status"))
        docx_status = _display_status(state.get("docx", {}).get("status"), generated_label=True)
        if final_status == "PASS" and docx_status == "GENERATED":
            completed += 1

        rows.append(
            [
                state.get("chapter_id", state_file.stem),
                state.get("title", "-"),
                _display_status(state.get("draft", {}).get("status")),
                _display_status(state.get("review", {}).get("status")),
                _display_status(state.get("revision", {}).get("status")),
                final_status,
                docx_status,
            ]
        )

    headers = ["Chapter", "Title", "Draft", "Review", "Revision", "Final", "DOCX"]
    widths = [
        max(len(str(row[index])) for row in rows + [headers])
        for index in range(len(headers))
    ]
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))
    print(f"\nTotal completed chapters: {completed}")


def _diff_chapter(chapter: int = 1, from_stage: str = "drafts", to_stage: str = "reviewed") -> None:
    from src.diff import diff_chapter

    result = diff_chapter(chapter=chapter, from_stage=from_stage, to_stage=to_stage)
    status = "FAIL" if result.required_sections_removed else "PASS"
    stage_labels = {"drafts": "Draft", "reviewed": "Reviewed", "final": "Final"}
    from_label = stage_labels.get(from_stage, from_stage.title())
    to_label = stage_labels.get(to_stage, to_stage.title())
    print(f"Chapter: {chapter}")
    print(f"From: {from_stage}")
    print(f"To: {to_stage}")
    print(f"{from_label} Words: {result.from_word_count}")
    print(f"{to_label} Words: {result.to_word_count}")
    print(f"Absolute Delta: {result.word_count_delta:+d}")
    print(f"Percent Delta: {result.percent_delta:+.2f}%")
    print("Headings removed:")
    for heading in result.headings_removed:
        print(f"- {heading}")
    print("Headings added:")
    for heading in result.headings_added:
        print(f"- {heading}")
    print("Required sections removed:")
    for section in result.required_sections_removed:
        print(f"- {section}")
    print(f"Result: {status}")


def _run_step(name: str, action: Callable[[], None]) -> None:
    """Run one pipeline step with progress output."""
    print(f"START: {name}")
    action()
    print(f"DONE: {name}")


def _run_chapter(chapter: int) -> None:
    """Run the single-chapter pipeline."""
    from src.handbook import resolve_chapter
    from src.validator import resolve_chapter_stage_path, validate_chapter

    metadata = resolve_chapter(chapter)
    print(f"Running chapter pipeline for {metadata.chapter_id}: {metadata.title}")
    _run_step("write-chapter", lambda: _write_chapter(chapter))

    print("START: validate-chapter --stage drafts")
    draft_result = validate_chapter(chapter, stage="drafts")
    draft_path = resolve_chapter_stage_path(chapter, stage="drafts")
    _print_validation_result(draft_result, draft_path, "drafts")
    if draft_result.passed:
        print("DONE: validate-chapter --stage drafts")
    elif _is_repairable_validation_failure(draft_result, draft_path):
        print("DONE: validate-chapter --stage drafts")
        _run_step("repair-chapter --stage drafts", lambda: _repair_chapter(chapter, "drafts"))
        _run_step("validate-chapter --stage drafts", lambda: _validate_chapter(chapter, "drafts"))
    else:
        raise SystemExit(1)

    _run_step("review-chapter", lambda: _review_chapter(chapter))

    final_source = "reviewed"
    try:
        _run_step("revise-chapter", lambda: _revise_chapter(chapter))
        _run_step("validate-chapter --stage reviewed", lambda: _validate_chapter(chapter, "reviewed"))
    except (RuntimeError, SystemExit) as exc:
        final_source = "drafts"
        print(f"Revision unavailable or rejected; falling back to validated draft. Reason: {exc}")

    _run_step("finalize-chapter", lambda: _finalize_chapter(chapter, final_source))
    _run_step("validate-chapter --stage final", lambda: _validate_chapter(chapter, "final"))
    _run_step("compile-docx", lambda: _compile_docx(str(chapter)))
    _handbook_status()
    print(f"Chapter pipeline complete for chapter {chapter}")


def _provider_env_var(model: str) -> tuple[str, str | None]:
    """Return the likely provider and required environment variable for a model."""
    model_name = model.lower()
    if model_name.startswith("ollama/"):
        return ("ollama", None)
    if model_name.startswith("anthropic/") or "claude" in model_name:
        return ("anthropic", "ANTHROPIC_API_KEY")
    if model_name.startswith("openai/") or "gpt" in model_name:
        return ("openai", "OPENAI_API_KEY")
    if model_name.startswith("gemini/") or "gemini" in model_name:
        return ("gemini", "GEMINI_API_KEY")
    return ("unknown", None)


def _doctor() -> None:
    """Print provider and configuration diagnostics without calling the LLM."""
    phase1_config = Path("configs/phase1.example.json")
    handbook_config = Path("configs/handbook.yaml")

    print("Config files:")
    print(f"- {phase1_config}: {'FOUND' if phase1_config.exists() else 'MISSING'}")
    print(f"- {handbook_config}: {'FOUND' if handbook_config.exists() else 'MISSING'}")

    from src.llm_gateway import load_config

    config = load_config(phase1_config)
    print("LLM roles:")
    for role, role_config in sorted(config.llm.roles.items()):
        provider, env_var = _provider_env_var(role_config.model)
        print(f"- {role}: {role_config.model}")
        print(f"  provider: {provider}")
        if env_var is None:
            expected_env = "none" if provider == "ollama" else "unknown"
            env_present = "yes" if provider == "ollama" else "no"
        else:
            expected_env = env_var
            env_present = "yes" if os.environ.get(env_var) else "no"
        print(f"  expected_env: {expected_env}")
        print(f"  env_var_present: {env_present}")


def _run_argparse() -> None:
    parser = argparse.ArgumentParser(description="AppSec handbook agent utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    test_model_parser = subparsers.add_parser("test-model")
    test_model_parser.add_argument("--role", default="writer")

    create_parser = subparsers.add_parser("create-chapter")
    create_parser.add_argument("--chapter", type=int, required=True)
    create_parser.add_argument("--overwrite", action="store_true")

    write_parser = subparsers.add_parser("write-chapter")
    write_parser.add_argument("--chapter", type=int, required=True)

    validate_parser = subparsers.add_parser("validate-chapter")
    validate_parser.add_argument("--chapter", type=int, required=True)
    validate_parser.add_argument("--stage", default="drafts")

    repair_parser = subparsers.add_parser("repair-chapter")
    repair_parser.add_argument("--chapter", type=int, required=True)
    repair_parser.add_argument("--stage", default="drafts")

    review_parser = subparsers.add_parser("review-chapter")
    review_parser.add_argument("--chapter", type=int, required=True)

    revise_parser = subparsers.add_parser("revise-chapter")
    revise_parser.add_argument("--chapter", type=int, required=True)

    finalize_parser = subparsers.add_parser("finalize-chapter")
    finalize_parser.add_argument("--chapter", type=int, required=True)
    finalize_parser.add_argument("--source", default="reviewed")

    compile_parser = subparsers.add_parser("compile-docx")
    compile_parser.add_argument("--chapters", required=True)

    show_state_parser = subparsers.add_parser("show-state")
    show_state_parser.add_argument("--chapter", type=int, required=True)

    subparsers.add_parser("handbook-status")

    diff_parser = subparsers.add_parser("diff-chapter")
    diff_parser.add_argument("--chapter", type=int, default=1)
    diff_parser.add_argument("--from-stage", default="drafts")
    diff_parser.add_argument("--to-stage", default="reviewed")

    run_parser = subparsers.add_parser("run-chapter")
    run_parser.add_argument("--chapter", type=int, required=True)

    subparsers.add_parser("doctor")

    args = parser.parse_args()
    commands: dict[str, Callable[[], None]] = {
        "test-model": lambda: _test_model(args.role),
        "create-chapter": lambda: _create_chapter(args.chapter, args.overwrite),
        "write-chapter": lambda: _write_chapter(args.chapter),
        "validate-chapter": lambda: _validate_chapter(args.chapter, args.stage),
        "repair-chapter": lambda: _repair_chapter(args.chapter, args.stage),
        "review-chapter": lambda: _review_chapter(args.chapter),
        "revise-chapter": lambda: _revise_chapter(args.chapter),
        "finalize-chapter": lambda: _finalize_chapter(args.chapter, args.source),
        "compile-docx": lambda: _compile_docx(args.chapters),
        "show-state": lambda: _show_state(args.chapter),
        "handbook-status": _handbook_status,
        "diff-chapter": lambda: _diff_chapter(args.chapter, args.from_stage, args.to_stage),
        "run-chapter": lambda: _run_chapter(args.chapter),
        "doctor": _doctor,
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
    def create_chapter(
        chapter: int = typer.Option(..., "--chapter", help="Chapter number to create a brief for."),
        overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite an existing chapter brief."),
    ) -> None:
        """Create a structured chapter brief from the handbook registry."""
        try:
            _create_chapter(chapter, overwrite)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
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
    def repair_chapter(
        chapter: int = typer.Option(..., "--chapter", help="Chapter number to repair."),
        stage: str = typer.Option("drafts", "--stage", help="Chapter stage: drafts, reviewed, or final."),
    ) -> None:
        """Append missing required sections to a chapter file."""
        try:
            _repair_chapter(chapter, stage)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
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
    def finalize_chapter(
        chapter: int = typer.Option(..., "--chapter", help="Chapter number to finalize."),
        source: str = typer.Option("reviewed", "--source", help="Source stage: drafts or reviewed."),
    ) -> None:
        """Copy a selected chapter source into the final stage."""
        try:
            _finalize_chapter(chapter, source)
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def compile_docx(chapters: str = typer.Option(..., "--chapters", help="Comma-separated chapter numbers.")) -> None:
        """Compile final Markdown chapters into a DOCX file."""
        try:
            _compile_docx(chapters)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def show_state(chapter: int = typer.Option(..., "--chapter", help="Chapter number to show state for.")) -> None:
        """Print persisted chapter state as JSON."""
        _show_state(chapter)

    @app.command()
    def handbook_status() -> None:
        """Print compact handbook state dashboard."""
        _handbook_status()

    @app.command()
    def diff_chapter(
        chapter: int = typer.Option(1, "--chapter", help="Chapter number to compare."),
        from_stage: str = typer.Option("drafts", "--from-stage", help="Source stage to compare from."),
        to_stage: str = typer.Option("reviewed", "--to-stage", help="Target stage to compare to."),
    ) -> None:
        """Compare two chapter stages structurally."""
        try:
            _diff_chapter(chapter, from_stage, to_stage)
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def run_chapter(chapter: int = typer.Option(..., "--chapter", help="Chapter number to run.")) -> None:
        """Run the single-chapter pipeline."""
        try:
            _run_chapter(chapter)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @app.command()
    def doctor() -> None:
        """Print provider and configuration diagnostics."""
        try:
            _doctor()
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc


if __name__ == "__main__":
    if typer is None:
        _run_argparse()
    else:
        app()
