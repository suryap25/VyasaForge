"""Provider-agnostic LLM gateway backed by LiteLLM."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("configs/phase1.example.json")


class LLMRoleConfig:
    """Model settings for a configured role."""

    def __init__(
        self,
        model: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_output_tokens = max_output_tokens


class LLMConfig:
    """Provider-agnostic LLM role configuration."""

    def __init__(self, roles: dict[str, LLMRoleConfig]) -> None:
        self.roles = roles


class Phase1Config:
    """Subset of Phase 1 configuration needed by the LLM gateway."""

    def __init__(self, llm: LLMConfig) -> None:
        self.llm = llm


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> Phase1Config:
    """Load LLM configuration from the Phase 1 config file."""
    with config_path.open("r", encoding="utf-8") as config_file:
        raw_config = json.load(config_file)

    try:
        roles_config = raw_config["llm"]["roles"]
    except KeyError as exc:
        raise ValueError(f"Missing LLM configuration key: {exc}") from exc

    roles = {
        role: LLMRoleConfig(
            model=settings["model"],
            temperature=settings.get("temperature"),
            max_tokens=settings.get("max_tokens"),
            max_output_tokens=settings.get("max_output_tokens"),
        )
        for role, settings in roles_config.items()
    }
    return Phase1Config(llm=LLMConfig(roles=roles))


def call_llm(role: str, messages: list[dict[str, Any]]) -> str:
    """Call the configured model for a role and return text content."""
    try:
        from litellm import completion
    except ImportError as exc:
        raise RuntimeError("LiteLLM is required. Install project dependencies with `pip install -e .`.") from exc

    config = load_config()
    role_config = config.llm.roles.get(role)
    if role_config is None:
        available_roles = ", ".join(sorted(config.llm.roles))
        raise ValueError(f"Unknown LLM role '{role}'. Available roles: {available_roles}")

    request_args = {
        "model": role_config.model,
        "messages": messages,
        "temperature": role_config.temperature,
    }
    if role_config.max_tokens is not None:
        request_args["max_tokens"] = role_config.max_tokens
    if role_config.max_output_tokens is not None:
        request_args["max_output_tokens"] = role_config.max_output_tokens

    try:
        response = completion(**request_args)
    except Exception as exc:
        raise RuntimeError(
            f"LLM call failed for role '{role}' using model '{role_config.model}'. "
            "Check the provider API key environment variable and model configuration."
        ) from exc

    content = response.choices[0].message.content
    return content or ""
