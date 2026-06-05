"""CLI entrypoint for the configurable LLM gateway."""

import typer

from src.llm_gateway import call_llm

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


if __name__ == "__main__":
    app()
