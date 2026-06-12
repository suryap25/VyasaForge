"""Provider profile configuration for LLM role switching."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROVIDERS_PATH = Path("configs/providers.yaml")
PROFILE_ENV_VAR = "LLM_PROFILE"


@dataclass(frozen=True)
class ProviderRoleConfig:
    """Model settings for a role in one provider profile."""

    model: str
    temperature: float | None = None
    max_tokens: int | None = None
    max_output_tokens: int | None = None


@dataclass(frozen=True)
class ProviderProfile:
    """One provider profile with role-specific model settings."""

    name: str
    provider: str
    env_var: str | None
    roles: dict[str, ProviderRoleConfig]


@dataclass(frozen=True)
class ProviderConfig:
    """Provider profile registry."""

    active_profile: str
    profiles: dict[str, ProviderProfile]


def _yaml_module() -> Any:
    try:
        import yaml
    except ImportError:
        from src import simple_yaml as yaml
    return yaml


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def load_provider_config(path: Path = PROVIDERS_PATH) -> ProviderConfig:
    """Load provider profiles from YAML."""
    if not path.exists():
        raise FileNotFoundError(f"Missing provider profile config: {path}")

    yaml = _yaml_module()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw_profiles = raw.get("profiles", {})
    profiles: dict[str, ProviderProfile] = {}
    for name, settings in raw_profiles.items():
        roles = {
            role: ProviderRoleConfig(
                model=role_settings["model"],
                temperature=_float_or_none(role_settings.get("temperature")),
                max_tokens=_int_or_none(role_settings.get("max_tokens")),
                max_output_tokens=_int_or_none(role_settings.get("max_output_tokens")),
            )
            for role, role_settings in settings.get("roles", {}).items()
        }
        env_var = settings.get("env_var") or None
        profiles[name] = ProviderProfile(
            name=name,
            provider=settings.get("provider", "unknown"),
            env_var=env_var,
            roles=roles,
        )

    active_profile = raw.get("active_profile")
    if not active_profile:
        raise ValueError(f"Missing active_profile in {path}")
    if active_profile not in profiles:
        available = ", ".join(sorted(profiles))
        raise ValueError(f"Unknown active provider profile '{active_profile}'. Available profiles: {available}")
    return ProviderConfig(active_profile=active_profile, profiles=profiles)


def selected_profile_name(path: Path = PROVIDERS_PATH) -> str | None:
    """Return the effective provider profile name, if provider profiles are configured."""
    if not path.exists():
        return None
    env_profile = os.getenv(PROFILE_ENV_VAR)
    if env_profile:
        return env_profile
    return load_provider_config(path).active_profile


def active_provider_profile(path: Path = PROVIDERS_PATH) -> ProviderProfile | None:
    """Return the effective provider profile, honoring LLM_PROFILE override."""
    if not path.exists():
        return None
    config = load_provider_config(path)
    profile_name = os.getenv(PROFILE_ENV_VAR) or config.active_profile
    profile = config.profiles.get(profile_name)
    if profile is None:
        available = ", ".join(sorted(config.profiles))
        raise ValueError(f"Unknown provider profile '{profile_name}'. Available profiles: {available}")
    return profile


def set_active_profile(profile_name: str, path: Path = PROVIDERS_PATH) -> Path:
    """Persist the active provider profile in providers.yaml."""
    config = load_provider_config(path)
    if profile_name not in config.profiles:
        available = ", ".join(sorted(config.profiles))
        raise ValueError(f"Unknown provider profile '{profile_name}'. Available profiles: {available}")

    yaml = _yaml_module()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["active_profile"] = profile_name
    path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def provider_env_present(profile: ProviderProfile) -> bool:
    """Return true if the profile's required environment variable is present."""
    if not profile.env_var:
        return True
    return bool(os.getenv(profile.env_var))
