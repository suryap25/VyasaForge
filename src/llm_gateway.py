"""Provider-agnostic LLM gateway backed by LiteLLM."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from litellm import completion
from pydantic import BaseModel, Field

DEFAULT_CONFIG_PATH = Path("configs/phase1.example.json")


class LLMRoleConfig(BaseModel):
    """Model settings for a configured role."""

    model: str = Field(description="LiteLLM-compatible model identifier.")
    temperature: float | None = None
    max_tokens: int | None = None


class LLMConfig(BaseModel):
    """Provider-agnostic LLM role configuration."""

    roles: dict[str, LLMRoleConfig]


class Phase1Config(BaseModel):
    """Subset of Phase 1 configuration needed by the LLM gateway."""

    llm: LLMConfig


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> Phase1Config:
    """Load LLM configuration from the Phase 1 config file."""
    with config_path.open("r", encoding="utf-8") as config_file:
        raw_config = json.load(config_file)
    return Phase1Config.model_validate(raw_config)


def call_llm(role: str, messages: list[dict[str, Any]]) -> str:
    """Call the configured model for a role and return text content."""
    config = load_config()
    role_config = config.llm.roles.get(role)
    if role_config is None:
        available_roles = ", ".join(sorted(config.llm.roles))
        raise ValueError(f"Unknown LLM role '{role}'. Available roles: {available_roles}")

    response = completion(
        model=role_config.model,
        messages=messages,
        temperature=role_config.temperature,
        max_tokens=role_config.max_tokens,
    )
    content = response.choices[0].message.content
    return content or ""
