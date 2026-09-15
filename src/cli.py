"""
Unified Enterprise Bench CLI
============================
Single entrypoint for presentations, documents, spreadsheets, diagrams, and compliance automations:
  bench ppt generate --theme brickred --output out.pptx
  bench ppt themes
  bench doc stamp --template BAST_Milestone_1_Template.docx --data data.json --output out.docx
  bench doc sanitize --input raw.docx --output clean.docx
  bench doc lint --file out.docx
  bench doc list-templates [--phase <phase>] [--query <query>]
  bench catalog [--phase <phase>] [--query <query>]
  bench xlsx calculate --template Cloud_Sizing_Calculator_Template.xlsx --data data.json --output out.xlsx
  bench diagram list project_master.drawio
  bench diagram add project_master.drawio --page "Doc A" --mermaid "graph TD; A-->B"
  bench diagram export project_master.drawio --page "Doc A" --output doc_a.png
  bench test --unit
  bench init-project <ProjectName>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.core.config import (
    ROOT_DIR,
    CLEAN_DIR,
    OUTPUT_DIR,
    THEMES_DIR,
    TEMPLATES_DIR,
    ensure_workspace_dirs,
    get_theme_path,
    get_template_path,
)
from src.core.theme import list_available_themes, EnterpriseTheme
from src.core.sanitizer import sanitize_docx, sanitize_text
from src.docx_engine.template_stamper import TemplateStamper
from src.docx_engine.document_linter import lint_document

console = Console()

app = typer.Typer(
    name="bench",
    help="Enterprise Workbench for Presentations, Documents, and Spreadsheets",
    no_args_is_help=True,
)

ppt_app = typer.Typer(name="ppt", help="Generative Consulting Presentation Engine", no_args_is_help=True)
doc_app = typer.Typer(name="doc", help="Deterministic Document Compliance Engine", no_args_is_help=True)
xlsx_app = typer.Typer(name="xlsx", help="Spreadsheet & Calculator Engine", no_args_is_help=True)
diagram_app = typer.Typer(name="diagram", help="Multi-Page Draw.io & Mermaid Diagram Engine", no_args_is_help=True)

app.add_typer(ppt_app, name="ppt")
app.add_typer(doc_app, name="doc")
app.add_typer(xlsx_app, name="xlsx")
app.add_typer(diagram_app, name="diagram")


# ============================================================================
# Core Commands
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
        # Default to fast unit tests (<1s) when --unit is passed or by default to prevent slow suite execution
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


# ============================================================================
# Presentation Commands (bench ppt ...)
# ============================================================================

@ppt_app.command("themes")
def list_themes() -> None:
    """List all available enterprise brand themes."""
    themes = list_available_themes()
    table = Table(title="Available Enterprise Themes")
    table.add_column("Theme Name", style="bold cyan")
    table.add_column("Accent Color", style="magenta")
    table.add_column("Background", style="green")

    for t_name in themes:
        try:
            t = EnterpriseTheme.from_yaml(t_name)
            table.add_row(t.name, t.accent_primary, t.bg_color)
        except Exception:
            table.add_row(t_name, "N/A", "N/A")

    console.print(table)


@ppt_app.command("generate")
def generate_ppt(
    theme: str = typer.Option("brickred", "--theme", "-t", help="Brand theme to apply"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .pptx path"),
    title: str = typer.Option("Enterprise Strategic Review", "--title", help="Deck title"),
    client: str = typer.Option("Enterprise Strategic Partner", "--client", help="Client name"),
) -> None:
    """Generate an executive consulting presentation deck."""
    ensure_workspace_dirs()
    out_path = Path(output) if output else OUTPUT_DIR / f"{theme}_deck" / "presentation.pptx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rprint(f"[cyan]ℹ Generating deck with theme:[/cyan] [bold]{theme}[/bold]")

    from src.ppt_engine.consulting_archetypes import (
        ConsultingDeckBuilder,
        create_presentation,
        HorizonColumnData,
        ScorecardQuadrantData,
        ScorecardMetric,
        build_bcg_3_horizon_slide,
        build_balanced_scorecard_slide,
    )
    from src.ppt_engine.theme_engine import get_theme

    active_theme = get_theme(theme)
    prs = create_presentation(active_theme)
    builder = ConsultingDeckBuilder(theme=active_theme)

    # Slide 1: BCG 3-Horizon Modernization
    h1 = HorizonColumnData(
        horizon_tag="HORIZON 1  |  0-6 MONTHS",
        title="Core Optimization",
        strategic_focus="Defend & Scale Baseline",
        metric_highlight="99.95%",
        metric_label="Availability Target",
        initiatives=["Consolidate shared databases", "Automate CI/CD gates", "Zero-downtime cutover"],
        status_tag="IN EXECUTION",
    )
    h2 = HorizonColumnData(
        horizon_tag="HORIZON 2  |  6-18 MONTHS",
        title="Distributed Acceleration",
        strategic_focus="Scale High-Growth Engines",
        metric_highlight="120k req/s",
        metric_label="Peak Event Throughput",
        initiatives=["Deploy Apache Kafka cluster", "Unify customer data schema", "Automate compliance audit"],
        status_tag="ACTIVE",
    )
    h3 = HorizonColumnData(
        horizon_tag="HORIZON 3  |  18-36 MONTHS",
        title="Autonomous Platform",
        strategic_focus="Future Strategic Levers",
        metric_highlight="85%",
        metric_label="Self-Healing Automation",
        initiatives=["Autonomous anomaly healing", "Real-time edge compute", "Global mesh routing"],
        status_tag="IN DESIGN",
    )
    build_bcg_3_horizon_slide(
        prs=prs,
        theme=active_theme,
        tracker="STRATEGIC TRANSFORMATION ROADMAP",
        action_title=f"{title}: 3-Horizon Modernization",
        subtitle="Strategic multi-phase roadmap sequencing foundational stabilization into autonomous capabilities.",
        horizons=[h1, h2, h3],
    )

    # Slide 2: Balanced Scorecard KPI Matrix
    q1 = ScorecardQuadrantData(
        quadrant_title="1. FINANCIAL EXCELLENCE",
        tagline="Capital Efficiency & Cloud TCO",
        metrics=[
            ScorecardMetric(label="TCO Reduction", value="-38%", status="EXCEEDED", description="Target: -30%"),
            ScorecardMetric(label="Annual Run-Rate", value="$4.2M", status="ON TRACK", description="Target: $5.0M"),
        ],
    )
    q2 = ScorecardQuadrantData(
        quadrant_title="2. CUSTOMER SATISFACTION",
        tagline="Client SLA & Frictionless Experience",
        metrics=[
            ScorecardMetric(label="API Availability", value="99.99%", status="ON TRACK", description="Target: 99.95%"),
            ScorecardMetric(label="Net Promoter Score", value="+68", status="EXCEEDED", description="Industry Benchmark: +45"),
        ],
    )
    q3 = ScorecardQuadrantData(
        quadrant_title="3. OPERATIONAL AGILITY",
        tagline="Delivery Velocity & Release Cadence",
        metrics=[
            ScorecardMetric(label="Release Frequency", value="24 / day", status="EXCEEDED", description="Baseline: 2 / week"),
            ScorecardMetric(label="Change Failure Rate", value="0.4%", status="HEALTHY", description="Target: < 1.0%"),
        ],
    )
    q4 = ScorecardQuadrantData(
        quadrant_title="4. RESILIENCE & GOVERNANCE",
        tagline="Zero-Trust Security & SOC-2 Compliance",
        metrics=[
            ScorecardMetric(label="Audit Readiness", value="100%", status="COMPLIANT", description="Target: 100%"),
            ScorecardMetric(label="Vulnerability MTTR", value="4.2 hrs", status="EXCEEDED", description="Target: < 24 hrs"),
        ],
    )
    build_balanced_scorecard_slide(
        prs=prs,
        theme=active_theme,
        tracker="EXECUTIVE PERFORMANCE BENCHMARK",
        action_title="Quarterly Enterprise Balanced Scorecard",
        subtitle="Multi-dimensional KPI tracking demonstrating accelerated delivery across financial and security vectors.",
        quadrants=[q1, q2, q3, q4],
    )

    prs.save(str(out_path))
    rprint(f"[green]✓ Presentation created successfully:[/green] [bold]{out_path}[/bold]")


@ppt_app.command("replace-image")
def replace_ppt_image(
    input_file: str = typer.Option(..., "--input", "-i", help="Path to input .pptx deck"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Path to save new .pptx deck"),
    new_image: str = typer.Option(..., "--new-image", "-n", help="Path to replacement image"),
    slide: Optional[int] = typer.Option(None, "--slide", "-s", help="Target slide number (1-indexed, default: all slides)"),
    fit: bool = typer.Option(True, "--fit/--stretch", help="Preserve aspect ratio within original bounding box"),
    open_deck: bool = typer.Option(False, "--open", help="Open generated presentation on desktop via Microsoft PowerPoint"),
) -> None:
    """Substitute preexisting images in a PowerPoint file with a new image and create a new presentation."""
    import subprocess
    from src.ppt_engine.image_engine import substitute_presentation_images

    in_path = Path(input_file)
    if not in_path.exists():
        rprint(f"[red]Error:[/red] Input PowerPoint file not found: {input_file}")
        raise typer.Exit(code=1)

    img_path = Path(new_image)
    if not img_path.exists():
        rprint(f"[red]Error:[/red] Replacement image not found: {new_image}")
        raise typer.Exit(code=1)

    out_path = Path(output_file) if output_file else in_path.parent / f"{in_path.stem}_substituted{in_path.suffix}"

    rprint(f"[cyan]ℹ Processing PowerPoint:[/cyan] [bold]{in_path}[/bold]")
    count, final_out = substitute_presentation_images(
        prs_or_path=in_path,
        new_image_path=img_path,
        output_path=out_path,
        slide_index=slide,
        preserve_aspect_ratio=fit,
    )

    rprint(f"[green]✓ Substituted {count} image(s) -> created:[/green] [bold]{final_out}[/bold]")

    if open_deck:
        cmd = f'open -a "Microsoft PowerPoint" "{final_out.resolve()}" && osascript -e \'tell application "Microsoft PowerPoint" to activate\''
        rprint(f"[cyan]ℹ Launching desktop PowerPoint:[/cyan] [bold]{final_out.name}[/bold]")
        subprocess.run(cmd, shell=True)


# ============================================================================
# Document Commands (bench doc ...)
# ============================================================================

@doc_app.command("stamp")
def stamp_doc(
    template: str = typer.Option(..., "--template", "-t", help="Template name or relative path in templates/"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Path to JSON data payload"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .docx destination path"),
) -> None:
    """Stamp a deterministic Word document template with JSON data."""
    context = {}
    if data:
        data_path = Path(data)
        if not data_path.exists():
            rprint(f"[red]Error:[/red] Data file not found: {data}")
            raise typer.Exit(code=1)
        with open(data_path, "r", encoding="utf-8") as f:
            context = json.load(f)

    out_p = Path(output) if output else OUTPUT_DIR / f"stamped_{Path(template).stem}.docx"

    stamper = TemplateStamper(template)
    out_file, report = stamper.render(context=context, output_path=out_p, auto_lint=True)

    rprint(f"[green]✓ Stamped document generated:[/green] [bold]{out_file}[/bold]")
    if report and not report.passed:
        rprint(f"[yellow]⚠ Document linter identified {report.total_issues} issues (e.g. unrendered tags).[/yellow]")


@doc_app.command("sanitize")
def sanitize_doc(
    input_file: str = typer.Option(..., "--input", "-i", help="Path to input .docx file"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Path to output cleaned .docx file"),
) -> None:
    """Scrub sensitive client/vendor PII from a .docx file and insert Jinja tags."""
    in_p = Path(input_file)
    if not in_p.exists():
        rprint(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(code=1)

    out_p = Path(output_file) if output_file else in_p.parent / f"{in_p.stem}_sanitized.docx"
    result = sanitize_docx(in_p, out_p)
    rprint(f"[green]✓ Sanitized document saved to:[/green] [bold]{result}[/bold]")


@doc_app.command("purge")
def purge_doc(
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to .docx file to purge"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Directory of .docx files to batch purge"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output path (default: in-place overwrite)"),
    comments: bool = typer.Option(True, "--comments/--no-comments", help="Purge comments and review parts"),
    highlights: bool = typer.Option(True, "--highlights/--no-highlights", help="Purge text highlighting"),
    revisions: bool = typer.Option(True, "--revisions/--no-revisions", help="Accept insertions, remove deletions and change markers"),
) -> None:
    """Purge comments, text highlights, and tracked changes from Word (.docx) documents."""
    from src.core.docx_purger import purge_docx_elements, purge_directory_elements

    if not file and not directory:
        rprint("[red]Error:[/red] Specify either --file <path.docx> or --dir <directory>")
        raise typer.Exit(code=1)

    if file:
        f_p = Path(file)
        if not f_p.exists():
            rprint(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(code=1)
        rep = purge_docx_elements(
            f_p, output or f_p,
            purge_comments=comments,
            purge_highlights=highlights,
            accept_revisions=revisions,
        )
        if rep.success:
            rprint(f"[green]✓ Purged document:[/green] [bold]{rep.file_path}[/bold]")
            rprint(f"  Comments: {rep.comments_removed} | Highlights: {rep.highlights_removed} | Revisions: {rep.revisions_removed}")
        else:
            rprint(f"[red]✗ Purge failed:[/red] {rep.error_message}")
            raise typer.Exit(code=1)

    if directory:
        d_p = Path(directory)
        if not d_p.exists():
            rprint(f"[red]Error:[/red] Directory not found: {directory}")
            raise typer.Exit(code=1)
        reps = purge_directory_elements(
            d_p,
            purge_comments=comments,
            purge_highlights=highlights,
            accept_revisions=revisions,
        )
        tot_c = sum(r.comments_removed for r in reps)
        tot_h = sum(r.highlights_removed for r in reps)
        tot_r = sum(r.revisions_removed for r in reps)
        rprint(f"[green]✓ Batch purged {len(reps)} documents in:[/green] [bold]{directory}[/bold]")
        rprint(f"  Comments removed: {tot_c} | Highlights: {tot_h} | Revisions normalized: {tot_r}")


@doc_app.command("lint")
def lint_doc(
    file: str = typer.Option(..., "--file", "-f", help="Path to .docx file to inspect"),
) -> None:
    """Perform automated QA inspection on a .docx document."""
    report = lint_document(file)
    if report.passed:
        rprint(f"[green]✓ Document Passed QA Inspection with 0 critical errors:[/green] {file}")
    else:
        rprint(f"[red]✗ Lint Failed ({report.total_issues} issues found):[/red] {file}")
        for iss in report.issues:
            rprint(f"  [[bold]{iss.severity}[/bold]] {iss.location}: {iss.message}")
        raise typer.Exit(code=1)


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


@doc_app.command("list-templates")
def list_templates(
    phase: Optional[str] = typer.Option(None, "--phase", "-p", help="Filter templates by phase (e.g. 07, initiating)"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Filter templates by filename substring (e.g. bast)"),
) -> None:
    """List available document and enterprise templates across project phases."""
    display_template_catalog(phase=phase, query=query)


@app.command("catalog")
def catalog(
    phase: Optional[str] = typer.Option(None, "--phase", "-p", help="Filter templates by phase (e.g. 07, initiating)"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Filter templates by filename substring (e.g. bast)"),
) -> None:
    """Browse and discover enterprise deliverable templates across project phases."""
    display_template_catalog(phase=phase, query=query)


# ============================================================================
# Spreadsheet Commands (bench xlsx ...)
# ============================================================================

@xlsx_app.command("calculate")
def calculate_xlsx(
    template: str = typer.Option(..., "--template", "-t", help="Template name or path to .xlsx file"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Path to JSON data payload for calculation/population"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Inject calculations or data updates into an Excel spreadsheet template."""
    from src.xlsx_engine.calculator_stamper import calculate_spreadsheet

    payload = {}
    if data:
        data_path = Path(data)
        if not data_path.exists():
            rprint(f"[red]Error:[/red] Data file not found: {data}")
            raise typer.Exit(code=1)
        with open(data_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

    try:
        out_p = calculate_spreadsheet(template=template, data=payload, output_path=output)
        rprint(f"[green]✓ Spreadsheet calculated and saved:[/green] [bold]{out_p}[/bold]")
    except Exception as e:
        rprint(f"[red]Error calculating spreadsheet:[/red] {e}")
        raise typer.Exit(code=1)


# ============================================================================
# Diagram Commands (bench diagram ...)
# ============================================================================

@diagram_app.command("list")
def list_diagram_pages(
    file: str = typer.Argument(..., help="Path to .drawio project file"),
) -> None:
    """List all diagram tabs/pages in a multi-page Draw.io project."""
    from src.ppt_engine.diagram_engine import DrawIOProject

    p = Path(file)
    if not p.exists():
        rprint(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    proj = DrawIOProject.load(p)
    pages = proj.list_pages()

    if not pages:
        rprint(f"[yellow]No diagram pages found in:[/yellow] {file}")
        return

    table = Table(title=f"Draw.io Pages: {p.name}")
    table.add_column("Index", justify="right", style="cyan")
    table.add_column("Page Name", style="bold green")
    table.add_column("Page ID", style="dim")
    table.add_column("Nodes", justify="right")
    table.add_column("Edges", justify="right")
    table.add_column("Containers", justify="right")

    for pg in pages:
        table.add_row(
            str(pg["index"]),
            pg["name"],
            pg["id"],
            str(pg["node_count"]),
            str(pg["edge_count"]),
            str(pg["container_count"]),
        )

    console.print(table)


@diagram_app.command("add")
def add_diagram_page(
    file: str = typer.Argument(..., help="Path to .drawio project file (created if not existing)"),
    page: str = typer.Option(..., "--page", "-p", help="Name of the diagram page/tab"),
    mermaid: Optional[str] = typer.Option(None, "--mermaid", "-m", help="Mermaid flowchart code snippet"),
    input_file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to .mmd or .txt file containing Mermaid code"),
    theme: str = typer.Option("modern_consulting", "--theme", "-t", help="Brand theme preset (modern_consulting, corporate_navy, executive_tech, warm_amber)"),
) -> None:
    """Add or update a diagram page in a multi-page Draw.io file from Mermaid syntax."""
    from src.ppt_engine.diagram_engine import DrawIOProject

    code = ""
    if mermaid:
        code = mermaid
    elif input_file:
        fpath = Path(input_file)
        if not fpath.exists():
            rprint(f"[red]Error:[/red] Input file not found: {input_file}")
            raise typer.Exit(code=1)
        code = fpath.read_text(encoding="utf-8")
    else:
        rprint("[red]Error:[/red] Provide either --mermaid <code> or --file <path.mmd>")
        raise typer.Exit(code=1)

    target = Path(file)
    proj = DrawIOProject.load(target)
    page_id = proj.add_mermaid_page(name=page, mermaid_code=code, theme=theme)
    proj.save(target)

    rprint(f"[green]✓ Saved page:[/green] [bold]{page}[/bold] (ID: {page_id}) -> [bold]{target}[/bold]")


@diagram_app.command("export")
def export_diagram_page(
    file: str = typer.Argument(..., help="Path to .drawio project file"),
    page: str = typer.Option(..., "--page", "-p", help="Page name or 0-based page index to export"),
    output: str = typer.Option(..., "--output", "-o", help="Destination path for exported image (.png or .svg)"),
    format: str = typer.Option("png", "--format", help="Export format: 'png' or 'svg'"),
    scale: float = typer.Option(3.0, "--scale", "-s", help="Rasterization scale/zoom factor for PNG"),
    theme: str = typer.Option("modern_consulting", "--theme", "-t", help="Theme preset if regenerating vectors"),
    transparent: bool = typer.Option(False, "--transparent", help="Export with transparent background (ideal for PPT slides)"),
    white_bg: bool = typer.Option(False, "--white-bg", help="Force solid pure white (#FFFFFF) background"),
) -> None:
    """Export a specific diagram page from a multi-page Draw.io project to PNG or SVG."""
    from src.ppt_engine.diagram_engine import DrawIOProject

    target = Path(file)
    if not target.exists():
        rprint(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    proj = DrawIOProject.load(target)
    page_ref = int(page) if page.isdigit() else page
    canvas_bg = "#FFFFFF" if white_bg else None

    try:
        out_p = proj.export_page(
            name_or_index=page_ref,
            output_path=output,
            format=format,
            scale=scale,
            theme=theme,
            transparent=transparent,
            canvas_bg=canvas_bg,
        )
        rprint(f"[green]✓ Exported page '{page}' to:[/green] [bold]{out_p}[/bold]")
    except Exception as e:
        rprint(f"[red]Error exporting page:[/red] {e}")
        raise typer.Exit(code=1)


@diagram_app.command("delete")
def delete_diagram_page(
    file: str = typer.Argument(..., help="Path to .drawio project file"),
    page: str = typer.Option(..., "--page", "-p", help="Page name or 0-based index to delete"),
) -> None:
    """Delete a diagram page/tab from a multi-page Draw.io project."""
    from src.ppt_engine.diagram_engine import DrawIOProject

    target = Path(file)
    if not target.exists():
        rprint(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    proj = DrawIOProject.load(target)
    page_ref = int(page) if page.isdigit() else page
    removed = proj.delete_page(page_ref)

    if removed:
        proj.save(target)
        rprint(f"[green]✓ Removed page '{page}' from:[/green] [bold]{target}[/bold]")
    else:
        rprint(f"[yellow]Page '{page}' not found in:[/yellow] {target}")


if __name__ == "__main__":
    app()

