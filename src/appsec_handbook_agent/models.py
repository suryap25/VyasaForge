"""Pydantic models for project configuration scaffolding."""

from pathlib import Path

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Filesystem locations used by the project."""

    configs_dir: Path = Field(default=Path("configs"))
    prompts_dir: Path = Field(default=Path("prompts"))
    chapters_dir: Path = Field(default=Path("chapters"))


class ChapterRequest(BaseModel):
    """Inputs for a single chapter generation request."""

    chapter_id: str = Field(description="Stable identifier for the chapter.")
    output_dir: Path = Field(default=Path("chapters"))
