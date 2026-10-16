"""
Enterprise Workbench CLI Utilities & Shared Infrastructure
==========================================================
Centralized Rich console, desktop application preview helper,
and common display routines.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.core.config import CLEAN_DIR, ROOT_DIR

console = Console()


def open_desktop_review(path: Path | str, app_name: Optional[str] = None) -> bool:
    """Launch local desktop application to review the deliverable natively on macOS.

    Uses `open -a "<app_name>" "<path>"` and activates the application via AppleScript.
    """
    target = Path(path)
    if not target.exists():
        console.print(f"[red]Error:[/red] Deliverable not found for review: {target}")
        return False

    try:
        if app_name:
            cmd = ["open", "-a", app_name, str(target.resolve())]
            subprocess.run(cmd, check=True)
            script = f'tell application "{app_name}" to activate'
            subprocess.run(
                ["osascript", "-e", script],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(["open", str(target.resolve())], check=True)
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not launch desktop application '{app_name}': {e}[/yellow]")
        return False


def handle_cli_error(e: Exception, verbose: bool = False) -> None:
    """Standardized error display handler for CLI commands."""
    console.print(f"[bold red]Error:[/bold red] {e}")
    if verbose:
        console.print_exception()


def display_template_catalog(
    phase: Optional[str] = None,
    query: Optional[str] = None,
) -> None:
    """Scan clean_workspace/projects for deliverable templates and render a Rich table."""
    projects_dir = CLEAN_DIR / "projects"
    if not projects_dir.exists():
        projects_dir = ROOT_DIR / "clean_workspace" / "projects"

    valid_exts = {".docx", ".pptx", ".xlsx", ".drawio", ".mpp"}
    templates: List[Tuple[str, str, str]] = []

    if projects_dir.exists():
        for p in projects_dir.rglob("*"):
            if not p.is_file() or p.name.startswith((".", "~$")):
                continue
            if p.suffix.lower() not in valid_exts:
                continue

            rel = p.relative_to(projects_dir)
            tmpl_phase = rel.parts[1] if len(rel.parts) >= 3 else rel.parts[0]
            tmpl_name = p.name
            tmpl_format = p.suffix.upper().lstrip(".")

            if phase and phase.lower() not in tmpl_phase.lower():
                continue
            if query and query.lower() not in tmpl_name.lower():
                continue

            templates.append((tmpl_phase, tmpl_name, tmpl_format))

    # Sort templates by phase, then template name
    templates.sort(key=lambda x: (x[0], x[1]))

    title = "Enterprise Template Master Catalog"
    if phase or query:
        filter_parts = []
        if phase:
            filter_parts.append(f"phase='{phase}'")
        if query:
            filter_parts.append(f"query='{query}'")
        title += f" [Filter: {', '.join(filter_parts)}]"

    table = Table(title=title)
    table.add_column("Phase", style="cyan", no_wrap=True)
    table.add_column("Template Name", style="bold")
    table.add_column("Format", style="green", no_wrap=True)

    for item_phase, item_name, item_format in templates:
        table.add_row(item_phase, item_name, item_format)

    console.print(table)
    if not templates:
        rprint("[yellow]No templates found matching the specified criteria.[/yellow]")
