"""Command-line interface scaffolding."""

from pathlib import Path

import typer

from appsec_handbook_agent.models import ChapterRequest, ProjectConfig

app = typer.Typer(help="AppSec handbook agent scaffolding.")


@app.callback()
def main() -> None:
    """AppSec handbook agent command group."""


@app.command()
def config_schema() -> None:
    """Print the current project config schema."""
    typer.echo(ProjectConfig.model_json_schema())


@app.command()
def chapter_request_schema() -> None:
    """Print the current chapter request schema."""
    typer.echo(ChapterRequest.model_json_schema())


@app.command()
def generate_chapter(
    chapter_id: str = typer.Argument(..., help="Chapter identifier to scaffold."),
    output: Path = typer.Option(
        Path("chapters"),
        "--output",
        "-o",
        help="Directory where generated chapters will eventually be written.",
    ),
) -> None:
    """Placeholder for Phase 1 chapter generation."""
    request = ChapterRequest(chapter_id=chapter_id, output_dir=output)
    typer.echo(f"Phase 1 scaffold ready for chapter: {request.chapter_id}")
