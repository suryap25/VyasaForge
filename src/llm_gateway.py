"""Provider-agnostic LLM gateway backed by LiteLLM."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("configs/phase1.example.json")
USAGE_LOG_PATH = Path("logs/llm-usage.jsonl")


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
    """Load effective LLM configuration.

    Provider profiles in configs/providers.yaml take precedence. The older
    phase1.example.json file remains as a fallback for backward compatibility.
    """
    try:
        from src.provider_profiles import active_provider_profile

        profile = active_provider_profile()
    except FileNotFoundError:
        profile = None

    if profile is not None:
        roles = {
            role: LLMRoleConfig(
                model=settings.model,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                max_output_tokens=settings.max_output_tokens,
            )
            for role, settings in profile.roles.items()
        }
        return Phase1Config(llm=LLMConfig(roles=roles))

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


def _usage_value(usage: Any, *keys: str) -> int | None:
    """Extract a token usage value from dict-like or attribute-like usage."""
    for key in keys:
        if isinstance(usage, dict) and key in usage:
            return usage[key]
        if hasattr(usage, key):
            return getattr(usage, key)
    return None


def _usage_object(response: Any) -> Any:
    """Return the most likely token usage object from a provider response."""
    usage = response.get("usage") if isinstance(response, dict) else getattr(response, "usage", None)
    if usage is not None:
        return usage

    usage = response.get("usage_metadata") if isinstance(response, dict) else getattr(response, "usage_metadata", None)
    if usage is not None:
        return usage

    hidden_params = (
        response.get("_hidden_params")
        if isinstance(response, dict)
        else getattr(response, "_hidden_params", None)
    )
    if hidden_params is None:
        return None

    for key in ("usage", "usage_metadata", "token_usage"):
        nested_usage = _usage_value(hidden_params, key)
        if nested_usage is not None:
            return nested_usage
    return None


def _response_usage(response: Any) -> tuple[int | None, int | None, int | None]:
    """Extract input, output, and total token counts when available."""
    usage = _usage_object(response)
    if usage is None:
        return (None, None, None)

    input_tokens = _usage_value(
        usage,
        "input_tokens",
        "prompt_tokens",
        "prompt_token_count",
        "input_token_count",
    )
    output_tokens = _usage_value(
        usage,
        "output_tokens",
        "completion_tokens",
        "candidates_token_count",
        "output_token_count",
    )
    total_tokens = _usage_value(usage, "total_tokens", "total_token_count")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    return (input_tokens, output_tokens, total_tokens)


def _log_usage(
    chapter: int | None,
    role: str,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
) -> None:
    """Append one LLM usage record as JSONL."""
    USAGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chapter": chapter,
        "role": role,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }
    with USAGE_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, sort_keys=True) + "\n")


def call_llm(role: str, messages: list[dict[str, Any]], chapter: int | None = None) -> str:
    """Call the configured model for a role and return text content."""
    config = load_config()
    role_config = config.llm.roles.get(role)
    if role_config is None:
        available_roles = ", ".join(sorted(config.llm.roles))
        raise ValueError(f"Unknown LLM role '{role}'. Available roles: {available_roles}")

    try:
        from litellm import completion
    except ImportError as exc:
        _log_usage(chapter, role, role_config.model, None, None, None)
        raise RuntimeError("LiteLLM is required. Install project dependencies with `pip install -e .`.") from exc

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
        _log_usage(chapter, role, role_config.model, None, None, None)
        raise RuntimeError(
            f"LLM call failed for role '{role}' using model '{role_config.model}'. "
            "Check the provider API key environment variable and model configuration."
        ) from exc

    input_tokens, output_tokens, total_tokens = _response_usage(response)
    _log_usage(chapter, role, role_config.model, input_tokens, output_tokens, total_tokens)

    content = response.choices[0].message.content
    return content or ""
