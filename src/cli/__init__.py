"""
Unified Enterprise Bench CLI Router
===================================
Root Typer application mounting domain engines:
  bench ppt       - Generative Consulting Presentation Engine
  bench doc       - Deterministic Document Compliance Engine
  bench xlsx      - Spreadsheet & Calculator Engine
  bench diagram   - Multi-Page Draw.io & Mermaid Diagram Engine (includes `v2`)
  bench asset     - Deterministic Vector Asset Harvester & Diagram Icon Registry
  bench pii       - Universal PII Sanitization & Slug Linter
  bench locale    - Bilingual & Hybrid Localization Engine
  bench cr        - Enterprise Change Request (CR) & Commercial Addendum Workflows
  bench stage     - Collaborative Delivery Staging, Locks, Badges, and Manifests

Root commands:
  bench init-project <ProjectName>
  bench catalog [--phase <phase>] [--query <query>]
  bench test [--unit] [--integration] [--marker <m>]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint

from src.core.config import OUTPUT_DIR
from src.cli.utils import console, display_template_catalog

# Sub-app routers
from src.cli.ppt import ppt_app
from src.cli.doc import doc_app
from src.cli.xlsx import xlsx_app
from src.cli.diagram import diagram_app
from src.cli.diagram_v2 import diagram_v2_app
from src.cli.asset import asset_app
from src.cli.pii import pii_app
from src.cli.locale import locale_app
from src.cli.cr import cr_app
from src.cli.stage import stage_app

app = typer.Typer(
    name="bench",
    help="Enterprise Workbench for Presentations, Documents, Spreadsheets, and Delivery Staging",
    no_args_is_help=True,
)

# Mount modular sub-applications
app.add_typer(ppt_app, name="ppt")
app.add_typer(doc_app, name="doc")
app.add_typer(xlsx_app, name="xlsx")
app.add_typer(diagram_app, name="diagram")
app.add_typer(asset_app, name="asset")
app.add_typer(pii_app, name="pii")
app.add_typer(locale_app, name="locale")
app.add_typer(cr_app, name="cr")
app.add_typer(stage_app, name="stage")


# ============================================================================
# Root Commands
# ============================================================================

@app.command("init-project")
def init_project(
    project_name: str = typer.Argument(..., help="Name of the enterprise project"),
    client: str = typer.Option("Enterprise Client Inc.", "--client", "-c", help="Client name"),
    vendor: str = typer.Option("Consulting Partner LLC", "--vendor", "-v", help="Vendor name"),
    client_lead: str = typer.Option("Client Sponsor", "--client-lead", help="Client project sponsor or lead"),
    vendor_lead: str = typer.Option("Engagement Lead", "--vendor-lead", help="Vendor engagement lead or PM"),
) -> None:
    """Provision a new project workspace inside output/<project_name>."""
    from src.core.scaffold import create_project_scaffold

    proj_dir = OUTPUT_DIR / project_name
    for sub in ["presentations", "documents", "diagrams", "assets"]:
        (proj_dir / sub).mkdir(parents=True, exist_ok=True)

    scaffold = create_project_scaffold(
        project_name=project_name,
        client=client,
        vendor=vendor,
        client_lead=client_lead,
        vendor_lead=vendor_lead,
    )

    meta_path = proj_dir / "project.json"
    project_config = {
        "project_name": scaffold["project_name"],
        "client_name": scaffold["client_name"],
        "client_lead": scaffold["client_lead"],
        "vendor_name": scaffold["vendor_name"],
        "vendor_lead": scaffold["vendor_lead"],
        "created_at": scaffold["created_at"],
        "milestones": scaffold["milestones"],
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(project_config, f, indent=2)

    payload_path = proj_dir / "project_payload.json"
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(scaffold, f, indent=2)

    rprint(f"[green]✓ Provisioned enterprise project:[/green] [bold]{project_name}[/bold]")
    rprint(f"  Directory: {proj_dir}")
    rprint(f"  Configuration: {meta_path}")
    rprint(f"  Payload: {payload_path}")


@app.command("catalog")
def catalog(
    phase: Optional[str] = typer.Option(None, "--phase", "-p", help="Filter templates by phase (e.g. 07, initiating)"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Filter templates by filename substring (e.g. bast)"),
) -> None:
    """Browse and discover enterprise deliverable templates across project phases."""
    display_template_catalog(phase=phase, query=query)


@app.command("test")
def run_tests(
    unit: bool = typer.Option(False, "--unit", "-u", help="Run fast in-memory unit tests (<1s)"),
    integration: bool = typer.Option(False, "--integration", "-i", help="Run integration test suite"),
    marker: Optional[str] = typer.Option(None, "--marker", "-m", help="Custom pytest marker filter (e.g. ppt, docx, xlsx, core)"),
    all_tests: bool = typer.Option(False, "--all", "-a", help="Run all tests without marker filtering"),
    extra_args: Optional[List[str]] = typer.Argument(None, help="Additional arguments forwarded to pytest"),
) -> None:
    """Run fast unit tests (<1s) or full verification gates via pytest."""
    import subprocess

    cmd = [sys.executable, "-m", "pytest"]
    if all_tests:
        pass
    elif unit or (not integration and not marker):
        cmd.extend(["-m", "unit"])
    elif integration:
        cmd.extend(["-m", "integration"])
    elif marker:
        cmd.extend(["-m", marker])

    if extra_args:
        cmd.extend(extra_args)

    rprint(f"[cyan]ℹ Running verification:[/cyan] [bold]{' '.join(cmd)}[/bold]")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        raise typer.Exit(code=res.returncode)


__all__ = [
    "app",
    "ppt_app",
    "doc_app",
    "xlsx_app",
    "diagram_app",
    "diagram_v2_app",
    "asset_app",
    "pii_app",
    "locale_app",
    "cr_app",
    "stage_app",
    "init_project",
    "catalog",
    "run_tests",
]
