"""
Core Configuration & Path Registry
===================================
Centralized directory paths, environment variables, and sandbox boundaries
for enterprise-bench.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Base repository root: <repo_root>/src/core/config.py -> parent.parent.parent
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent

# Core subdirectories & Intake Pipelines
RAW_SOURCE_DIR: Path = ROOT_DIR / "raw_source_files"
CLEAN_DIR: Path = ROOT_DIR / "clean_workspace"
TEMPLATES_DIR: Path = CLEAN_DIR  # Future workshops strictly consume from clean_workspace
PRESETS_DIR: Path = ROOT_DIR / "presets"
THEMES_DIR: Path = PRESETS_DIR / "themes"
DECK_CONFIGS_DIR: Path = PRESETS_DIR / "deck_configs"
ASSETS_DIR: Path = ROOT_DIR / "assets"
ICONS_DIR: Path = ASSETS_DIR / "icons"
IMAGES_DIR: Path = ASSETS_DIR / "images"
OUTPUT_DIR: Path = ROOT_DIR / "output"


class WorkspaceSecurityError(PermissionError):
    """Raised when an operation attempts to read un-sanitized raw source files."""
    pass


def validate_clean_path(path: Path | str) -> Path:
    """
    Enforce the workspace isolation boundary:
    Operations are strictly prohibited from reading un-sanitized files from raw_source_files/.
    All template consumption and document stamping must read from clean_workspace/.
    """
    p = Path(path).resolve()
    raw_resolved = RAW_SOURCE_DIR.resolve()
    if raw_resolved in p.parents or p == raw_resolved:
        raise WorkspaceSecurityError(
            f"SECURITY BOUNDARY VIOLATION: Reading un-sanitized raw files is strictly prohibited ({p}). "
            f"Future workshops and automation engines must only read from: {CLEAN_DIR}"
        )
    return p


def ensure_workspace_dirs() -> None:
    """Ensure standard workspace directories exist."""
    for d in [
        RAW_SOURCE_DIR,
        CLEAN_DIR,
        PRESETS_DIR,
        THEMES_DIR,
        DECK_CONFIGS_DIR,
        ASSETS_DIR,
        ICONS_DIR,
        IMAGES_DIR,
        OUTPUT_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def get_theme_path(theme_name: str) -> Path:
    """Resolve theme path by name with fallback extensions."""
    name = theme_name.strip()
    candidates = [
        THEMES_DIR / f"{name}.yaml",
        THEMES_DIR / f"{name}.yml",
        THEMES_DIR / name,
    ]
    for c in candidates:
        if c.exists():
            return c
    return THEMES_DIR / f"{name}.yaml"


def get_template_path(template_name: str, project_id: Optional[str] = None) -> Optional[Path]:
    """
    Find a template strictly within clean_workspace/.
    If project_id is provided, searches that project's clean folder first.
    Falls back to legacy templates/ only if clean_workspace has not yet been populated.
    """
    # 1. If project_id provided, search that project's clean folder
    if project_id:
        proj_clean = CLEAN_DIR / "projects" / project_id
        if proj_clean.exists():
            direct = proj_clean / template_name
            if direct.exists():
                return validate_clean_path(direct)
            for p in proj_clean.rglob("*"):
                if p.is_file() and not p.name.startswith("."):
                    if p.name.lower() == template_name.lower() or template_name.lower() in p.name.lower():
                        return validate_clean_path(p)

    # 2. Search clean_workspace/ globally (primary boundary)
    direct = CLEAN_DIR / template_name
    if direct.exists():
        return validate_clean_path(direct)

    for p in CLEAN_DIR.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            if p.name.lower() == template_name.lower() or template_name.lower() in p.name.lower():
                return validate_clean_path(p)

    # 3. Legacy fallback if clean_workspace is not yet initialized
    legacy_dir = ROOT_DIR / "templates"
    if legacy_dir.exists():
        for p in legacy_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                if p.name.lower() == template_name.lower() or template_name.lower() in p.name.lower():
                    return p

    return None

