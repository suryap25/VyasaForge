"""Handbook workspace resolution.

Global model/provider config stays in configs/. Handbook-specific artifacts live
under handbooks/<workspace-name>/.
"""

from __future__ import annotations

import re
from pathlib import Path

HANDBOOKS_DIR = Path("handbooks")
ACTIVE_HANDBOOK_PATH = Path("configs/active-handbook.txt")
LEGACY_REGISTRY_PATH = Path("configs/handbook.yaml")


def workspace_slug(value: str) -> str:
    """Return a stable, readable workspace slug for a handbook topic or title."""
    text = value.casefold()
    words = re.findall(r"[a-z0-9]+", text)
    if {"aws", "cloud", "security"}.issubset(set(words)):
        return "aws-cloud-security"
    if {"azure", "cloud", "security"}.issubset(set(words)):
        return "azure-cloud-security"
    if {"gcp", "cloud", "security"}.issubset(set(words)) or {"google", "cloud", "security"}.issubset(set(words)):
        return "gcp-cloud-security"

    stopwords = {
        "a",
        "an",
        "and",
        "for",
        "focus",
        "focused",
        "focusing",
        "handbook",
        "in",
        "of",
        "on",
        "the",
        "to",
        "with",
    }
    meaningful = [word for word in words if word not in stopwords]
    return "-".join(meaningful[:6]) or "handbook"


def workspace_root(name: str) -> Path:
    """Return the root folder for a named handbook workspace."""
    return HANDBOOKS_DIR / workspace_slug(name)


def registry_path_for(name: str) -> Path:
    """Return the handbook registry path for a named workspace."""
    return workspace_root(name) / "handbook.yaml"


def set_active_handbook(name: str) -> Path:
    """Persist the active handbook workspace name."""
    slug = workspace_slug(name)
    ACTIVE_HANDBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_HANDBOOK_PATH.write_text(slug + "\n", encoding="utf-8")
    return workspace_root(slug)


def active_handbook_name() -> str | None:
    """Return the active handbook workspace name, if configured."""
    if not ACTIVE_HANDBOOK_PATH.exists():
        return None
    name = ACTIVE_HANDBOOK_PATH.read_text(encoding="utf-8").strip()
    return name or None


def active_workspace_root() -> Path:
    """Return active handbook root, or project root for legacy compatibility."""
    name = active_handbook_name()
    return workspace_root(name) if name else Path(".")


def active_registry_path() -> Path:
    """Return the active handbook registry path."""
    name = active_handbook_name()
    if name:
        return registry_path_for(name)
    return LEGACY_REGISTRY_PATH


def workspace_path(*parts: str) -> Path:
    """Return a path under the active handbook workspace."""
    return active_workspace_root().joinpath(*parts)


def list_handbook_workspaces() -> list[str]:
    """Return available handbook workspace names."""
    if not HANDBOOKS_DIR.exists():
        return []
    return sorted(path.name for path in HANDBOOKS_DIR.iterdir() if path.is_dir() and (path / "handbook.yaml").exists())
