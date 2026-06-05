"""CLI entrypoint for the configurable LLM gateway."""

from pathlib import Path

import typer

app = typer.Typer(help="AppSec handbook agent utilities.")


@app.command()
def test_model(role: str = typer.Option("writer", "--role", help="Configured LLM role.")) -> None:
    """Send a tiny prompt through the configured model."""
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
    typer.echo(response)


@app.command()
def write_chapter(chapter: int = typer.Option(..., "--chapter", help="Chapter number to write.")) -> None:
    """Write a Markdown chapter draft."""
    from src.writer import write_chapter as write_chapter_draft

    try:
        draft_path = write_chapter_draft(chapter)
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Wrote draft: {Path(draft_path)}")


@app.command()
def validate_chapter(chapter: int = typer.Option(..., "--chapter", help="Chapter number to validate.")) -> None:
    """Validate a Markdown chapter draft."""
    from src.validator import validate_chapter as validate_chapter_draft

    result = validate_chapter_draft(chapter)
    status = "PASS" if result.passed else "FAIL"

    typer.echo(f"{status}: {result.draft_path}")
    typer.echo(f"Word count: {result.word_count}")

    if result.missing_sections:
        typer.echo("Missing sections:")
        for section in result.missing_sections:
            typer.echo(f"- {section}")

    for error in result.errors:
        if not error.startswith("Missing required section:"):
            typer.echo(f"- {error}")

    if not result.passed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
