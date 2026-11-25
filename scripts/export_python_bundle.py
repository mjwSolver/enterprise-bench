"""Export a clean, version-stamped Python-only distribution zip of enterprise-bench.

Includes:
  - pyproject.toml, uv.lock, .gitignore, and a bundle-scoped README.md
  - src/ and tests/ (excluding caches and generated project_outputs)
  - Runtime-required presets/, vendor_packs/, assets/icons/, and assets/logos/
    (excluding private vaults like *vault*.json, *.local.json, and client logos)

Excludes:
  - AI/agent docs (.agents/, AGENTS.md, HANDOVER.md, docs/, etc.)
  - Local workspaces & bloat (clean_workspace/, output/, assets/images/, etc.)

Usage:
  uv run python scripts/export_python_bundle.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import tomllib
import zipfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

IGNORE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".git",
    ".venv",
    "project_outputs",
}

IGNORE_FILES = {".DS_Store"}

CLIENT_LOGO_EXCLUSIONS = {"morula_ivf.png"}


def _read_version() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _ignore_common(_dir: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in IGNORE_DIRS or name in IGNORE_FILES:
            ignored.add(name)
        elif name.endswith((".pyc", ".pyo", ".pyd", ".local.json")):
            ignored.add(name)
        elif "vault" in name and name.endswith(".json"):
            ignored.add(name)
    return ignored


def _ignore_logos(directory: str, names: list[str]) -> set[str]:
    ignored = _ignore_common(directory, names)
    ignored.update(n for n in names if n in CLIENT_LOGO_EXCLUSIONS)
    return ignored


def _bundle_readme(version: str) -> str:
    return f"""# Enterprise Workbench (`enterprise-bench` v{version})

Universal, multi-engine Python workbench for enterprise presentations, Word documents, spreadsheets, and diagrams.

## 1. Prerequisites

1. **Python 3.11+** and [`uv`](https://docs.astral.sh/uv/)
2. **System Cairo library** (required by `cairosvg` for SVG icon and diagram rasterization):
   - macOS: `brew install cairo`
   - Debian/Ubuntu: `sudo apt-get install -y libcairo2`

## 2. Setup

```bash
uv sync --all-extras
uv run bench --help
```

## 3. Core CLI Commands

```bash
# Provision a new project workspace under output/<project_name>
uv run bench init-project AcmeDigital --client "Acme Corp" --vendor "Partner LLC"

# Presentations & Diagrams
uv run bench ppt themes
uv run bench ppt generate --theme snowblue --output output/AcmeDigital/presentations/deck.pptx
uv run bench diagram v2 --help

# Word Documents (bring your own .docx template)
uv run bench doc sanitize --input path/to/template.docx --output output/Sanitized.docx
uv run bench doc stamp --template output/Sanitized.docx --data payload.json --output output/Final.docx
uv run bench doc lint --file output/Final.docx

# Spreadsheets & Tests
uv run bench xlsx --help
uv run pytest
```
"""


def build_bundle(output_dir: Path | None = None) -> Path:
    version = _read_version()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_root_name = f"enterprise-bench-v{version}"
    target_dir = output_dir or (REPO_ROOT / "output")
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / f"enterprise-bench-python-v{version}_{timestamp}.zip"

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / bundle_root_name
        stage.mkdir(parents=True, exist_ok=True)

        for fname in ("pyproject.toml", "uv.lock", ".gitignore"):
            shutil.copy2(REPO_ROOT / fname, stage / fname)

        (stage / "README.md").write_text(_bundle_readme(version), encoding="utf-8")

        shutil.copytree(REPO_ROOT / "src", stage / "src", ignore=_ignore_common)
        shutil.copytree(REPO_ROOT / "tests", stage / "tests", ignore=_ignore_common)
        shutil.copytree(REPO_ROOT / "presets", stage / "presets", ignore=_ignore_common)
        shutil.copytree(REPO_ROOT / "vendor_packs", stage / "vendor_packs", ignore=_ignore_common)
        shutil.copytree(REPO_ROOT / "assets" / "icons", stage / "assets" / "icons", ignore=_ignore_common)
        shutil.copytree(REPO_ROOT / "assets" / "logos", stage / "assets" / "logos", ignore=_ignore_logos)

        subprocess.run(["zip", "-rq", str(zip_path), bundle_root_name], cwd=tmp, check=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"Corrupted zip entry detected: {bad}")
        entries = len(zf.namelist())

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Created: {zip_path}")
    print(f"Size:    {size_mb:.2f} MB ({entries} entries)")
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export clean Python-only enterprise-bench zip.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Override output directory (default: output/)")
    parser.add_argument("--reveal", action="store_true", help="Reveal the generated zip in macOS Finder")
    args = parser.parse_args()

    zip_path = build_bundle(args.output_dir)
    if args.reveal:
        subprocess.run(["open", "-R", str(zip_path)], check=False)


if __name__ == "__main__":
    main()
