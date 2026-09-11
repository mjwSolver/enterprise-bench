"""
Unit Test: Dependency & Module Isolation Verification
=====================================================
Ensures:
1. Pure headless isolation: Importing `src.core` does NOT leak or import
   heavy engine extras (`pptx`, `matplotlib`, `docxtpl`, `openpyxl`, `pandas`).
2. Declared dependency parity: All packages listed in `pyproject.toml`
   [project.dependencies] are resolvable and importable.
3. Optional extras integrity: Engine-specific groups (`ppt`, `docx`, `xlsx`)
   can be imported without circular references or broken bindings.
4. CLI router integrity: `src.cli:app` registers all expected sub-commands.
"""

from __future__ import annotations

import importlib
import sys
import tomllib
from pathlib import Path

import pytest

# Workspace root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_core_module_import_isolation():
    """Verify src.core does not trigger heavy optional engine dependencies."""
    forbidden_engine_modules = [
        "pptx",
        "matplotlib",
        "docx",
        "docxtpl",
        "openpyxl",
        "pandas",
    ]

    # Clean out any cached imports for testing
    for mod in list(sys.modules.keys()):
        if any(mod == f or mod.startswith(f"{f}.") for f in forbidden_engine_modules):
            sys.modules.pop(mod, None)

    # Re-import core package
    if "src.core" in sys.modules:
        del sys.modules["src.core"]
    import src.core  # noqa: F401

    # Assert none of the forbidden engine modules were pulled in
    leaked = [
        mod for mod in forbidden_engine_modules
        if mod in sys.modules
    ]
    assert not leaked, f"Core package leaked engine-specific dependencies: {leaked}"


def test_declared_core_dependencies():
    """Verify all base dependencies in pyproject.toml can be imported."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing from root"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    assert deps, "No core dependencies declared in pyproject.toml"

    # Map package distribution names to top-level import module names
    pkg_to_module = {
        "pydantic": "pydantic",
        "jinja2": "jinja2",
        "rich": "rich",
        "typer": "typer",
        "python-dotenv": "dotenv",
        "pillow": "PIL",
        "pyyaml": "yaml",
        "requests": "requests",
        "cairosvg": "cairosvg",
    }

    for dep_spec in deps:
        pkg_name = dep_spec.split(">=")[0].split("==")[0].split("<")[0].split("~=")[0].strip()
        mod_name = pkg_to_module.get(pkg_name, pkg_name)

        imported = importlib.import_module(mod_name)
        assert imported is not None, f"Failed to import core dependency: {mod_name} ({pkg_name})"


def test_optional_engine_extras_importable():
    """Verify engine extras (ppt, docx, xlsx) declared in pyproject.toml can be imported."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    extras = data.get("project", {}).get("optional-dependencies", {})

    engine_import_mapping = {
        "ppt": ["pptx", "matplotlib", "numpy"],
        "docx": ["docx", "docxtpl"],
        "xlsx": ["openpyxl", "pandas"],
    }

    for group, expected_modules in engine_import_mapping.items():
        if group in extras:
            for mod_name in expected_modules:
                mod = importlib.import_module(mod_name)
                assert mod is not None, f"Failed to import engine dependency {mod_name} for extra [{group}]"


def test_cli_entrypoint_and_router_structure():
    """Verify CLI entrypoint src.cli:app defines required sub-apps."""
    import typer
    from src.cli import app

    assert isinstance(app, typer.Typer), "CLI app is not a Typer instance"

    registered_commands = [c.name for c in app.registered_commands]
    registered_groups = [g.name for g in app.registered_groups]

    assert "init-project" in registered_commands, "Missing 'init-project' command on root CLI"
    assert "test" in registered_commands, "Missing 'test' command on root CLI"
    assert "ppt" in registered_groups, "Missing 'ppt' router on root CLI"
    assert "doc" in registered_groups, "Missing 'doc' router on root CLI"
    assert "xlsx" in registered_groups, "Missing 'xlsx' router on root CLI"
