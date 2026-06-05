"""CLI entrypoint for the configurable LLM gateway."""

from pathlib import Path

import typer

from src.llm_gateway import call_llm
from src.writer import write_chapter as write_chapter_draft

app = typer.Typer(help="AppSec handbook agent utilities.")


@app.command()
def test_model(role: str = typer.Option("writer", "--role", help="Configured LLM role.")) -> None:
    """Send a tiny prompt through the configured model."""
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
    try:
        draft_path = write_chapter_draft(chapter)
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Wrote draft: {Path(draft_path)}")


if __name__ == "__main__":
    app()
