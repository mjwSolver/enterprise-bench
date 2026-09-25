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
  bench xlsx s-curve [--template <template>] [--weeks 12] [--distribution sigmoid] [--output out.xlsx]
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
pii_app = typer.Typer(name="pii", help="Universal PII Sanitization & Slug Linter", no_args_is_help=True)
locale_app = typer.Typer(name="locale", help="Bilingual & Hybrid Localization Engine", no_args_is_help=True)
cr_app = typer.Typer(name="cr", help="Enterprise Change Request (CR) & Commercial Addendum Workflows", no_args_is_help=True)

app.add_typer(ppt_app, name="ppt")
app.add_typer(doc_app, name="doc")
app.add_typer(xlsx_app, name="xlsx")
app.add_typer(diagram_app, name="diagram")
app.add_typer(pii_app, name="pii")
app.add_typer(locale_app, name="locale")
app.add_typer(cr_app, name="cr")


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


@ppt_app.command("build-deck")
def build_ppt_deck(
    config: str = typer.Option(..., "--config", "-c", help="Path to declarative YAML deck configuration"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .pptx destination path"),
    theme: Optional[str] = typer.Option(None, "--theme", "-t", help="Optional brand theme override (e.g. metrodata, brickred, snowblue)"),
    open_deck: bool = typer.Option(False, "--open", help="Open generated presentation on desktop via Microsoft PowerPoint"),
    context_file: Optional[str] = typer.Option(None, "--context", "-ctx", help="Path to JSON/YAML engagement context file for slug replacement"),
    locale: Optional[str] = typer.Option(None, "--locale", "-l", help="Locale override for bilingual decks (e.g. en, id)"),
    slides: Optional[int] = typer.Option(None, "--slides", "-s", help="Limit number of slides to generate (e.g. 18 for Phase 1)"),
    sync_xlsx: bool = typer.Option(False, "--sync-xlsx", "-sx", help="Synchronize presentation data directly with project spreadsheets (S-curve, RAID logs)"),
    timeline: Optional[str] = typer.Option(None, "--timeline", help="Override timeline spreadsheet path for weekly deck"),
    risks: Optional[str] = typer.Option(None, "--risks", help="Override risk register spreadsheet path for weekly deck"),
    issues: Optional[str] = typer.Option(None, "--issues", help="Override issue log spreadsheet path for weekly deck"),
    checklist: Optional[str] = typer.Option(None, "--checklist", help="Override closeout checklist spreadsheet path for closing deck"),
    chart_mode: bool = typer.Option(False, "--chart-mode", help="Embed high-DPI S-Curve line chart on Slide 4"),
    client: Optional[str] = typer.Option(None, "--client", help="Optional client name override for engagement context"),
) -> None:
    """Build a multi-slide executive consulting presentation deck from a YAML specification."""
    import subprocess
    import yaml
    from src.ppt_engine.weekly_progress_deck import WeeklyProgressDeckBuilder
    from src.core.slug_registry import EngagementContext, load_engagement_context

    config_path = Path(config)
    if not config_path.exists():
        rprint(f"[red]Error:[/red] Config file not found: {config}")
        raise typer.Exit(code=1)

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    deck_type = config_data.get("deck_type", "weekly_progress")
    out_path = Path(output) if output else OUTPUT_DIR / "presentations" / f"{config_path.stem}.pptx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    engagement_ctx = None
    if context_file:
        engagement_ctx = load_engagement_context(context_file)
    elif "context" in config_data:
        engagement_ctx = EngagementContext(**config_data["context"])

    if client:
        if engagement_ctx is None:
            engagement_ctx = EngagementContext.default_ngl()
        engagement_ctx.client_company_name = client
        short = "".join(w[0] for w in client.split() if w[0].isalnum()).upper()
        if short:
            engagement_ctx.client_short_name = short

    rprint(f"[cyan]ℹ Building presentation deck:[/cyan] [bold]{deck_type}[/bold] from [bold]{config_path.name}[/bold]")

    if deck_type in (
        "presales_pitch_deck",
        "pitch_deck",
        "modernize_data_platform",
        "kickoff_deck",
        "kickoff",
        "project_kickoff",
        "declarative",
        "uat_briefing",
        "uat_deck",
        "sosialisasi_uat",
        "uat",
    ):
        from src.ppt_engine.pitch_deck import PitchDeckBuilder
        builder = PitchDeckBuilder.from_yaml(config_path, theme_override=theme)
        builder.build_all(slide_limit=slides)
        saved_file = builder.save(out_path, engagement_context=engagement_ctx)
    elif deck_type in ("reference_slides", "reference_deck"):
        from src.ppt_engine.reference_slides import ReferenceDeckBuilder
        builder = ReferenceDeckBuilder.from_yaml(config_path, theme_override=theme, locale_override=locale)
        saved_file = builder.save(out_path, engagement_context=engagement_ctx)
    elif deck_type in ("weekly_progress", "weekly_deck", "progress_deck"):
        builder = WeeklyProgressDeckBuilder.from_yaml(config_path, theme_override=theme)
        if sync_xlsx or config_data.get("sync_xlsx") or "spreadsheets" in config_data:
            rprint("[cyan]ℹ Synchronizing with project spreadsheets (Timeline S-Curve, Risk Register, Issue Log)...[/cyan]")
            sync_info = builder.sync_with_spreadsheets(
                timeline_path=timeline,
                risk_path=risks,
                issue_path=issues,
                chart_mode=chart_mode or config_data.get("chart_mode", False),
            )
            if sync_info.get("timeline_synced"):
                rprint(f"  [dim]• S-Curve period: {sync_info.get('current_period')} (Variance: {sync_info.get('variance_pct', 0.0):+.1f}%)[/dim]")
            if sync_info.get("s_curve_chart_generated"):
                rprint(f"  [dim]• S-Curve chart rendered: {sync_info.get('chart_path')}[/dim]")
            if sync_info.get("risks_synced"):
                rprint(f"  [dim]• Risks parsed: {sync_info.get('risk_count', 0)} active risks[/dim]")
            if sync_info.get("issues_synced"):
                rprint(f"  [dim]• Issues parsed: {sync_info.get('issue_count', 0)} active issues[/dim]")
        builder.build_all()
        saved_file = builder.save(out_path, engagement_context=engagement_ctx)
    elif deck_type in ("closing_deck", "project_closing", "closing", "maintenance_transition"):
        from src.ppt_engine.closing_deck import ClosingDeckBuilder
        builder = ClosingDeckBuilder.from_yaml(config_path, theme_override=theme)
        if sync_xlsx or config_data.get("sync_xlsx") or "spreadsheets" in config_data:
            rprint("[cyan]ℹ Synchronizing with project closeout checklist spreadsheet...[/cyan]")
            sync_info = builder.sync_with_spreadsheets(checklist_path=checklist)
            if sync_info.get("checklist_synced"):
                rprint(f"  [dim]• Closeout checklist gates: {sync_info.get('checklist_count', 0)} verification items[/dim]")
            if sync_info.get("deliverables_synced"):
                rprint(f"  [dim]• Contractual deliverables: {sync_info.get('deliverables_count', 0)} inventory items[/dim]")
            if sync_info.get("download_link"):
                rprint(f"  [dim]• Deliverables download URL: {sync_info.get('download_link')[:45]}...[/dim]")
        builder.build_all()
        saved_file = builder.save(out_path, engagement_context=engagement_ctx)
    else:
        builder = WeeklyProgressDeckBuilder.from_yaml(config_path, theme_override=theme)
        builder.build_all()
        saved_file = builder.save(out_path, engagement_context=engagement_ctx)

    total_slides = len(builder.prs.slides)
    rprint(f"[green]✓ Generated consulting presentation ({total_slides} slides):[/green] [bold]{saved_file}[/bold]")

    if open_deck:
        rprint(f"[cyan]ℹ Launching desktop PowerPoint:[/cyan] [bold]{saved_file.name}[/bold]")
        try:
            subprocess.run(["open", "-a", "Microsoft PowerPoint", str(saved_file.resolve())], check=False)
            subprocess.run(["osascript", "-e", 'tell application "Microsoft PowerPoint" to activate'], check=False)
        except Exception as e:
            rprint(f"[yellow]⚠ Could not activate Microsoft PowerPoint: {e}[/yellow]")
    else:
        rprint(f"[dim]Tip: View in PowerPoint via desktop review: `open -a \"Microsoft PowerPoint\" \"{saved_file}\"`[/dim]")



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
        rprint(f"[cyan]ℹ Launching desktop PowerPoint:[/cyan] [bold]{final_out.name}[/bold]")
        try:
            subprocess.run(["open", "-a", "Microsoft PowerPoint", str(final_out.resolve())], check=False)
            subprocess.run(["osascript", "-e", 'tell application "Microsoft PowerPoint" to activate'], check=False)
        except Exception as e:
            rprint(f"[yellow]⚠ Could not activate Microsoft PowerPoint: {e}[/yellow]")


@ppt_app.command("check-resources")
def check_ppt_resources(
    download: bool = typer.Option(True, "--download/--no-download", help="Attempt silent download for missing assets"),
    clean_report: bool = typer.Option(True, "--clean/--no-clean", help="Clean missing_resources.md if all assets are present"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if any resource is missing"),
) -> None:
    """Verify or download all registered presentation assets and update missing_resources.md."""
    from src.ppt_engine.resource_manager import get_resource_manager

    rm = get_resource_manager()
    results = rm.check_resources(download=download)

    table = Table(title="Enterprise Presentation Resource Registry")
    table.add_column("Resource Key", style="bold cyan")
    table.add_column("Expected Path", style="dim")
    table.add_column("Status", style="bold")
    table.add_column("Fallback Mode", style="magenta")
    table.add_column("Impacted Slide(s)", style="yellow")

    has_missing = False
    for key, info in results.items():
        spec = info["spec"]
        if info["present"]:
            status_str = "[green]✓ Present[/green]" if not info["downloaded"] else "[green]✓ Downloaded[/green]"
        else:
            status_str = "[red]✗ Missing (Fallback Active)[/red]"
            has_missing = True

        slides_str = ", ".join(spec.impacted_slides) if spec.impacted_slides else "N/A"
        try:
            rel_p = spec.target_path.relative_to(ROOT_DIR).as_posix()
        except ValueError:
            rel_p = spec.target_path.as_posix()

        table.add_row(key, rel_p, status_str, spec.fallback_type, slides_str)

    console.print(table)

    if has_missing:
        rprint(f"[yellow]⚠ One or more resources are missing. Diagnostic report written to: {rm.missing_report_path}[/yellow]")
        if strict:
            raise typer.Exit(code=1)
    else:
        if clean_report:
            rm.clean_missing_report(remove=True)
        rprint("[green]✓ All registered presentation resources are verified and ready.[/green]")


@ppt_app.command("frame-mockup")
def frame_mockup_cli(
    input_image: Optional[str] = typer.Option(None, "--input", "-i", help="Path to input screenshot image (defaults to pitch deck sample if omitted)"),
    output_image: Optional[str] = typer.Option(None, "--output", "-o", help="Path to save framed mockup PNG"),
    url: str = typer.Option("https://finance.snowflakecomputing.com/streamlit/app", "--url", "-u", help="URL displayed in browser pill"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Window title"),
    theme: str = typer.Option("light", "--theme", help="Browser chrome theme: 'light' or 'dark'"),
    dpi: int = typer.Option(300, "--dpi", help="Target DPI scaling (minimum 200)"),
    width_in: float = typer.Option(8.0, "--width-in", "-w", help="Target mockup width in inches on slide"),
    aspect_ratio: Optional[str] = typer.Option("16:9", "--aspect-ratio", "-a", help="Content aspect ratio crop (16:9, 16:10, 4:3, preserve)"),
    badges: Optional[str] = typer.Option(None, "--badges", "-b", help="Comma-separated telemetry badges (e.g. 'Snowflake AI,Real-Time Ingestion')"),
    shadow: bool = typer.Option(True, "--shadow/--no-shadow", help="Include ambient elevated drop shadow"),
    border: bool = typer.Option(True, "--border/--no-border", help="Include subtle hairline border"),
    open_image: bool = typer.Option(False, "--open", help="Open generated mockup in desktop Preview application"),
) -> None:
    """Frame raw enterprise UI screenshots inside a high-DPI macOS desktop browser mockup."""
    import subprocess
    from src.ppt_engine.image_engine import frame_browser_mockup, ImageEngine

    # 1. Resolve source image
    src_input: Union[Path, Any]
    src_label: str
    if input_image:
        inp_p = Path(input_image)
        if not inp_p.exists():
            rprint(f"[red]Error:[/red] Input screenshot not found: {input_image}")
            raise typer.Exit(code=1)
        src_input = inp_p
        src_label = str(inp_p)
    else:
        # Check standard template preview samples
        candidates = [
            OUTPUT_DIR / "template_previews" / "pitch_deck" / "slide_20.png",
            OUTPUT_DIR / "template_previews" / "pitch_deck" / "slide_28.png",
            OUTPUT_DIR / "template_previews" / "pitch_deck" / "slide_29.png",
        ]
        found_candidate = None
        for c in candidates:
            if c.exists():
                found_candidate = c
                break

        if found_candidate:
            src_input = found_candidate
            src_label = f"Auto-detected sample ({found_candidate.name})"
        else:
            # Fallback to procedural high-res UI card
            img_engine = ImageEngine()
            src_input = img_engine.generate_procedural_3d_card(title="Analytics Platform")
            src_label = "Procedural Analytics UI Visual"

    # 2. Resolve destination path
    if output_image:
        out_path = Path(output_image)
    else:
        stem = src_input.stem if isinstance(src_input, Path) else "procedural"
        out_path = OUTPUT_DIR / "mockups" / f"{stem}_mockup_{theme}.png"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Parse telemetry badges
    if badges is not None:
        parsed_badges = [b.strip() for b in badges.split(",") if b.strip()]
    else:
        parsed_badges = [
            "🏷️ Snowflake Cortex AI Engine",
            "⚡ Real-Time Ingestion",
            "📊 Daily Reconciled",
        ]

    # 4. Generate framed mockup
    rprint(f"[cyan]ℹ Framing browser mockup:[/cyan] [bold]{src_label}[/bold]")
    rprint(f"[dim]  • Chrome: {theme.upper()} | URL: {url} | Target DPI: {dpi} (w={width_in}\")[/dim]")

    framed_img = frame_browser_mockup(
        image_input=src_input,
        url=url,
        title=title,
        theme_mode=theme,
        target_dpi=dpi,
        target_width_in=width_in,
        aspect_ratio=aspect_ratio,
        hairline_border=border,
        shadow=shadow,
        telemetry_badges=parsed_badges,
        output_path=out_path,
    )

    rprint(f"[green]✓ Browser mockup generated ({framed_img.width}×{framed_img.height} px, {dpi} DPI):[/green] [bold]{out_path}[/bold]")

    # 5. Native desktop preview
    if open_image:
        rprint(f"[cyan]ℹ Launching desktop Preview:[/cyan] [bold]{out_path.name}[/bold]")
        subprocess.run(["open", "-a", "Preview", str(out_path.resolve())], check=False)
    else:
        rprint(f'[dim]Tip: View in Preview via desktop review: `open -a "Preview" "{out_path}"`[/dim]')


@ppt_app.command("export-preview")
def export_preview_cli(
    pptx_path: str = typer.Option(..., "--pptx", "-p", help="Path to PowerPoint .pptx file"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory for slide preview PNGs"),
    backend: str = typer.Option("python", "--backend", "-b", help="Exporter backend: 'python' (headless Pillow), 'keynote', 'powerpoint', 'libreoffice', or 'auto'"),
    dpi: int = typer.Option(150, "--dpi", help="DPI resolution for rendered slides"),
    open_first: bool = typer.Option(False, "--open", help="Open first slide preview in macOS Preview"),
) -> None:
    """Export PowerPoint presentation slides to crisp preview PNG images."""
    import subprocess
    from src.ppt_engine.slide_exporter import export_deck_to_images

    p_in = Path(pptx_path)
    if not p_in.exists():
        rprint(f"[red]Error:[/red] PowerPoint file not found: {pptx_path}")
        raise typer.Exit(code=1)

    out_dir = Path(output_dir) if output_dir else p_in.parent / "previews"
    out_dir.mkdir(parents=True, exist_ok=True)

    rprint(f"[cyan]ℹ Exporting slide previews ({backend} backend, {dpi} DPI):[/cyan] [bold]{p_in}[/bold]")
    images = export_deck_to_images(p_in, output_dir=out_dir, backend=backend, dpi=dpi)

    rprint(f"[green]✓ Exported {len(images)} slide preview(s) to:[/green] [bold]{out_dir}[/bold]")
    for img in images:
        rprint(f"  • {img.name}")

    if open_first and images:
        rprint(f"[cyan]ℹ Launching desktop Preview:[/cyan] [bold]{images[0].name}[/bold]")
        subprocess.run(["open", "-a", "Preview", str(images[0].resolve())], check=False)



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


@doc_app.command("compile-spec")
def compile_spec_cli(
    input_path: str = typer.Option(..., "--input", "-i", help="Path to a markdown file or directory of modular spec markdown files"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .docx destination path"),
    theme: str = typer.Option("metrodata", "--theme", "-t", help="Brand theme name or path to YAML theme"),
    client: Optional[str] = typer.Option(None, "--client", "-c", help="Client name override"),
    vendor: Optional[str] = typer.Option(None, "--vendor", "-v", help="Vendor name override"),
    title: Optional[str] = typer.Option(None, "--title", help="Document title override"),
    context_file: Optional[str] = typer.Option(None, "--context", "-ctx", help="Path to JSON/YAML engagement context file for slug replacement"),
) -> None:
    """Compile modular Markdown specs into a styled, audit-ready Word document (.docx)."""
    from src.core.slug_registry import load_engagement_context
    from src.docx_engine.spec_compiler import (
        SpecCompiler,
        SpecMetadata,
        compile_markdown_to_docx,
        compile_spec_directory,
    )

    in_p = Path(input_path)
    if not in_p.exists():
        rprint(f"[red]Error:[/red] Input path not found: {input_path}")
        raise typer.Exit(code=1)

    if not output:
        stem = in_p.stem if in_p.is_file() else in_p.name
        out_p = OUTPUT_DIR / f"{stem}_compiled.docx"
    else:
        out_p = Path(output)

    engagement_ctx = load_engagement_context(context_file) if context_file else None

    try:
        if in_p.is_dir():
            res = compile_spec_directory(in_p, out_p, theme=theme, engagement_context=engagement_ctx)
        else:
            meta = SpecMetadata()
            if client:
                meta.client = client
            if vendor:
                meta.vendor = vendor
            if title:
                meta.title = title
            res = compile_markdown_to_docx(in_p, out_p, theme=theme, metadata=meta, engagement_context=engagement_ctx)

        rprint(f"[green]✓ Specification compiled successfully:[/green] [bold]{res}[/bold]")
        rprint(f"Tip: Preview in Microsoft Word via desktop review: [cyan]`open -a \"Microsoft Word\" \"{res}\"`[/cyan]")
    except Exception as e:
        rprint(f"[red]Error compiling specification:[/red] {e}")
        raise typer.Exit(code=1)


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


@doc_app.command("check-aspect")
def check_image_aspect(
    file: str = typer.Option(..., "--file", "-f", help="Path to .docx file to inspect for image distortion"),
    tolerance: float = typer.Option(3.0, "--tolerance", "-t", help="Distortion tolerance percentage (default: 3%)"),
) -> None:
    """Audit embedded drawings in a .docx file for aspect ratio squish or distortion."""
    from src.core.image_aspect import ImageAspectEngine
    engine = ImageAspectEngine(tolerance_pct=tolerance)
    reports = engine.audit_docx(file)
    distorted = [r for r in reports if r.is_distorted]
    if not reports:
        rprint(f"[cyan]ℹ No embedded drawings found in:[/cyan] {file}")
        return
    if not distorted:
        rprint(f"[green]✓ All {len(reports)} embedded image(s) maintain perfect aspect ratio (0% squish):[/green] {file}")
        for r in reports:
            rprint(f"  • {r.media_path}: {r.container_width_in:.2f}\" x {r.container_height_in:.2f}\" (ratio {r.container_aspect_ratio:.2f}:1)")
    else:
        rprint(f"[yellow]⚠ Found {len(distorted)} distorted image(s) in:[/yellow] {file}")
        for r in distorted:
            rprint(f"  • [bold]{r.media_path}[/bold] (rId: {r.rel_id}): Container {r.container_width_in:.2f}\" x {r.container_height_in:.2f}\" (ratio {r.container_aspect_ratio:.2f}) vs Natural {r.natural_width_px}x{r.natural_height_px} (ratio {r.natural_aspect_ratio:.2f}) -> [red]{r.distortion_pct}% distortion[/red]. Suggested height: {r.suggested_height_in:.2f}\"")
        raise typer.Exit(code=1)


@doc_app.command("fix-aspect")
def fix_image_aspect(
    file: str = typer.Option(..., "--file", "-f", help="Path to .docx file to correct"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional output path (defaults to in-place)"),
    max_width: float = typer.Option(6.5, "--max-width", "-w", help="Maximum image width in inches (default: 6.5\")"),
) -> None:
    """Automatically correct squished or distorted image extents in a .docx file."""
    from src.core.image_aspect import ImageAspectEngine
    engine = ImageAspectEngine()
    count, reports = engine.fix_docx(file, output_path=output, max_width_in=max_width)
    target = output or file
    if count == 0:
        rprint(f"[green]✓ No distortion detected, document is already proportional:[/green] {target}")
    else:
        rprint(f"[green]✓ Successfully corrected aspect ratio on {count} image frame(s) in:[/green] [bold]{target}[/bold]")
        for r in reports:
            rprint(f"  • {r.media_path}: {r.container_width_in:.2f}\" x {r.container_height_in:.2f}\" (ratio {r.container_aspect_ratio:.2f}:1)")


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


@xlsx_app.command("s-curve")
def generate_scurve_cli(
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Base .xlsx template name or path to inject into (optional)"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Path to JSON data payload defining periods, planned, actual, milestones"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
    weeks: int = typer.Option(12, "--weeks", "-w", help="Number of project weeks/periods to generate if data not provided"),
    distribution: str = typer.Option("sigmoid", "--distribution", help="Mathematical distribution: sigmoid, polynomial, cubic, linear"),
    current_week: Optional[int] = typer.Option(None, "--current-week", help="Current week index (1-based) for actual progress cut-off"),
    lag: float = typer.Option(0.0, "--lag", help="Simulated actual lag factor relative to plan (e.g. -0.05 for 5% behind)"),
    sheet_name: str = typer.Option("S-Curve", "--sheet-name", "-s", help="Target worksheet name"),
    title: str = typer.Option("Project S-Curve: Planned vs Actual Cumulative Progress", "--title", help="Chart title"),
    project: str = typer.Option("Enterprise Modernization Project", "--project", "-p", help="Project name for header"),
) -> None:
    """Generate an S-curve cumulative progress curve and inject an openpyxl LineChart."""
    from src.xlsx_engine.s_curve_generator import SCurveGenerator

    payload: dict = {}
    if data:
        data_path = Path(data)
        if not data_path.exists():
            rprint(f"[red]Error:[/red] Data file not found: {data}")
            raise typer.Exit(code=1)
        with open(data_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

    periods = payload.get("periods")
    planned_pct = payload.get("planned_pct")
    actual_pct = payload.get("actual_pct")
    milestones = payload.get("milestones")
    dist = payload.get("distribution", distribution)
    proj_name = payload.get("project_name", project)
    s_name = payload.get("sheet_name", sheet_name)
    c_title = payload.get("chart_title", title)

    c_period_idx = None
    if current_week is not None:
        c_period_idx = current_week - 1
    elif "current_week" in payload:
        c_period_idx = int(payload["current_week"]) - 1
    elif "current_period_idx" in payload:
        c_period_idx = int(payload["current_period_idx"])

    lag_factor = payload.get("lag_factor", lag)

    try:
        generator = SCurveGenerator(template=template, project_name=proj_name)
        out_p = generator.generate(
            output_path=output,
            periods=periods,
            num_periods=weeks,
            planned_pct=planned_pct,
            actual_pct=actual_pct,
            distribution=dist,
            milestones=milestones,
            current_period_idx=c_period_idx,
            lag_factor=lag_factor,
            sheet_name=s_name,
            chart_title=c_title,
        )
        rprint(f"[green]✓ Project S-curve successfully generated:[/green] [bold]{out_p}[/bold]")
    except Exception as e:
        rprint(f"[red]Error generating S-curve:[/red] {e}")
        raise typer.Exit(code=1)


@xlsx_app.command("append-risk")
def append_risk_cli(
    title: str = typer.Option(..., "--title", "-t", help="Title of the project risk"),
    desc: str = typer.Option(..., "--desc", "-d", help="Description of the risk event and root cause"),
    impact: str = typer.Option(..., "--impact", "-i", help="Operational and schedule impact statement"),
    category: str = typer.Option("Scope", "--category", "-c", help="Category: Scope, Data, Resource, Schedule, Quality"),
    owner: str = typer.Option("Project Manager", "--owner", help="Accountable mitigation owner"),
    prob: str = typer.Option("Medium", "--prob", help="Probability level: Low, Medium, High"),
    impact_level: str = typer.Option("Medium", "--impact-level", help="Impact level: Low, Medium, High"),
    status: str = typer.Option("Open", "--status", help="Status: Open, Mitigated, Closed"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append a risk entry into the project Risk Register spreadsheet."""
    from src.xlsx_engine.ledger_models import RiskEntry, append_risk_to_register

    risk = RiskEntry(
        title=title,
        description=desc,
        impact_statement=impact,
        category=category,
        owner=owner,
        probability=prob,
        impact_level=impact_level,
        status=status,
    )
    out_p = append_risk_to_register(risk, output_path=output)
    rprint(f"[green]✓ Risk entry appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("append-issue")
def append_issue_cli(
    title: str = typer.Option(..., "--title", "-t", help="Title of the blocker/issue"),
    desc: str = typer.Option(..., "--desc", "-d", help="Description of the roadblock"),
    category: str = typer.Option("Technical", "--category", "-c", help="Category: Resource, Requirement, Technical, Environment"),
    owner: str = typer.Option("Lead Data Engineer", "--owner", help="PIC accountable for resolution"),
    reported_by: str = typer.Option("Project Lead", "--reported-by", help="Originator who flagged the issue"),
    area: str = typer.Option("Timeline", "--area", help="Impacted area: Timeline, Scope, Budget, Resource, Quality"),
    severity: str = typer.Option("Medium", "--severity", "-s", help="Severity: Low, Medium, High, Critical"),
    status: str = typer.Option("Open", "--status", help="Status: Open, In Progress, Closed"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append an issue entry into the project Issue Log spreadsheet."""
    from src.xlsx_engine.ledger_models import IssueEntry, append_issue_to_log

    issue = IssueEntry(
        title=title,
        description=desc,
        category=category,
        owner=owner,
        reported_by=reported_by,
        impacted_area=area,
        severity=severity,
        status=status,
    )
    out_p = append_issue_to_log(issue, output_path=output)
    rprint(f"[green]✓ Issue entry appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("append-defect")
def append_defect_cli(
    summary: str = typer.Option(..., "--summary", "-s", help="Summary title of the defect"),
    desc: str = typer.Option(..., "--desc", "-d", help="Detailed description of the bug"),
    module: str = typer.Option("A. Sales", "--module", "-m", help="Module or component"),
    activity: str = typer.Option("B. SIT", "--activity", "-a", help="Testing phase: A. Unit Testing, B. SIT, C. UAT"),
    severity: str = typer.Option("2. Major", "--severity", help="Severity: 1. Critical, 2. Major, 3. Medium, 4. Low"),
    priority: str = typer.Option("2. Medium", "--priority", help="Priority: 1. High, 2. Medium, 3. Low"),
    status: str = typer.Option("Open", "--status", help="Status: Open, Assigned, In Progress, Resolved, Closed"),
    pic: str = typer.Option("Data Dev", "--pic", help="Person in charge of fixing"),
    test_case: str = typer.Option("TC-01", "--test-case", help="Test Case ID reference"),
    expected: str = typer.Option("", "--expected", help="Expected correct result"),
    actual: str = typer.Option("", "--actual", help="Observed actual defect result"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append a defect row into the 3.6_Defect_List_Template.xlsx tracker."""
    from src.xlsx_engine.ledger_models import DefectEntry, append_defect_to_list

    defect = DefectEntry(
        summary=summary,
        description=desc,
        module=module,
        activity=activity,
        severity=severity,
        priority=priority,
        status=status,
        pic=pic,
        test_case=test_case,
        expected_result=expected,
        actual_result=actual,
    )
    out_p = append_defect_to_list(defect, output_path=output)
    rprint(f"[green]✓ Defect entry appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("append-stakeholder")
def append_stakeholder_cli(
    name: str = typer.Option(..., "--name", "-n", help="Full name and title of stakeholder"),
    email: str = typer.Option(..., "--email", "-e", help="Email address"),
    company: str = typer.Option("Client Corp", "--company", "-c", help="Organization / Employer"),
    phone: str = typer.Option("+62-811-0000-000", "--phone", help="Contact phone number"),
    department: str = typer.Option("Finance", "--dept", help="Department or business unit"),
    role: str = typer.Option("Project Manager", "--role", "-r", help="Project governance role"),
    active: str = typer.Option("Y", "--active", help="Active flag: Y / N"),
    notes: Optional[str] = typer.Option("", "--notes", help="Context or additional responsibilities"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append a stakeholder entry into 1.3_Stakeholders_Register_Template.xlsx."""
    from src.xlsx_engine.ledger_models import StakeholderEntry, append_stakeholder_to_register

    entry = StakeholderEntry(
        name=name,
        email=email,
        company=company,
        phone=phone,
        department=department,
        project_role=role,
        is_active=active,
        notes=notes or "",
    )
    out_p = append_stakeholder_to_register(entry, output_path=output)
    rprint(f"[green]✓ Stakeholder appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("cloud-sizing")
def cloud_sizing_cli(
    client: str = typer.Option("Enterprise Client", "--client", "-c", help="Client name"),
    storage: float = typer.Option(1.0, "--storage", help="Storage in TB"),
    cortex: float = typer.Option(3660.0, "--cortex", help="Cortex AI annual USD"),
    training: float = typer.Option(1500.0, "--training", help="Training cost USD"),
    fx: float = typer.Option(16500.0, "--fx", help="USD to IDR exchange rate"),
    config: Optional[str] = typer.Option(None, "--config", help="Optional JSON or YAML sizing spec"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Calculate Snowflake infrastructure sizing and stamp Cloud_Sizing_Calculator_Template.xlsx."""
    import json
    import yaml
    from src.xlsx_engine.cloud_sizing import CloudSizingConfig, calculate_cloud_sizing

    if config and Path(config).exists():
        p = Path(config)
        raw = p.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) if p.suffix.lower() in (".yaml", ".yml") else json.loads(raw)
        cfg = CloudSizingConfig(**data)
    else:
        cfg = CloudSizingConfig(
            client_name=client,
            storage_tb=storage,
            cortex_ai_annual_usd=cortex,
            training_seats_usd=training,
            exchange_rate_idr=fx,
        )

    res = calculate_cloud_sizing(cfg, output_path=output)
    rprint(f"[cyan]{res.summary_table()}[/cyan]")
    rprint(f"[green]✓ Cloud sizing stamped successfully:[/green] [bold]{res.output_path}[/bold]")


@xlsx_app.command("sync-s-curve")
def sync_s_curve_cli(
    timeline: Optional[str] = typer.Option(None, "--timeline", "-t", help="Path to 4.2_Weekly_Progress_Timeline_Update_Template.xlsx"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
    chunk_days: int = typer.Option(7, "--chunk-days", help="Days per weekly progress interval"),
) -> None:
    """Extract daily progression from timeline workbook and inject executive S-curve line chart tab."""
    from src.xlsx_engine.timeline_aggregator import TimelineAggregator

    agg = TimelineAggregator(timeline_path=timeline)
    analysis = agg.extract_s_curve(chunk_days=chunk_days)
    out_p = agg.synchronize_and_chart(output_path=output, chunk_days=chunk_days)

    rprint(f"[bold cyan]S-Curve Extracted from Timeline:[/bold cyan]")
    rprint(f"  • Current Period: [bold]{analysis.current_period}[/bold]")
    rprint(f"  • Planned Progress: [bold]{(analysis.current_planned_pct or 0.0) * 100:.1f}%[/bold]")
    rprint(f"  • Actual Progress: [bold]{(analysis.current_actual_pct or 0.0) * 100:.1f}%[/bold]")
    rprint(f"  • Variance: [bold]{analysis.current_variance_pct or 0.0:+.2f}%[/bold]")
    rprint(f"  • Overall Health: [bold]{analysis.overall_health}[/bold] (SPI: {analysis.spi})")
    rprint(f"[green]✓ S-Curve Analysis tab with LineChart injected:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("update-closeout")
def update_closeout_cli(
    item: str = typer.Option(..., "--item", "-i", help="Deliverable or checklist item name (substring match)"),
    status: str = typer.Option("Delivered", "--status", "-s", help="Gate status: Delivered, Done, Yes, Partial, TBD"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Path to 5.2_Project_Closeout_Checklist_Template.xlsx"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Update deliverable sign-off statuses in 5.2_Project_Closeout_Checklist_Template.xlsx."""
    from src.xlsx_engine.ledger_models import update_closeout_checklist

    updates = [{"item_name": item, "status": status}]
    try:
        out_p = update_closeout_checklist(updates=updates, template_path=template, output_path=output)
        rprint(f"[green]✓ Closeout checklist updated:[/green] [bold]{out_p}[/bold]")
        rprint(f"  Item: '{item}' -> Status: [bold cyan]{status}[/bold cyan]")
    except Exception as e:
        rprint(f"[red]Error updating closeout checklist:[/red] {e}")
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
    file: str = typer.Argument(..., help="Path to .drawio project file or .yaml diagram specification"),
    page: str = typer.Option(..., "--page", "-p", help="Page name or 0-based page index to export"),
    output: str = typer.Option(..., "--output", "-o", help="Destination path for exported image (.png or .svg)"),
    format: str = typer.Option("png", "--format", help="Export format: 'png' or 'svg'"),
    scale: float = typer.Option(3.0, "--scale", "-s", help="Rasterization scale/zoom factor for PNG"),
    theme: str = typer.Option("modern_consulting", "--theme", "-t", help="Theme preset if regenerating vectors"),
    transparent: bool = typer.Option(False, "--transparent", help="Export with transparent background (ideal for PPT slides)"),
    white_bg: bool = typer.Option(False, "--white-bg", help="Force solid pure white (#FFFFFF) background"),
) -> None:
    """Export a specific diagram page from a multi-page Draw.io project or YAML spec to PNG or SVG."""
    from src.ppt_engine.diagram_engine import DrawIOProject

    target = Path(file)
    if not target.exists():
        rprint(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    if target.suffix.lower() in (".yaml", ".yml"):
        proj = DrawIOProject.from_yaml(target)
    else:
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


@diagram_app.command("export-all")
def export_all_diagram_pages(
    file: str = typer.Argument(..., help="Path to .drawio project file or .yaml diagram specification"),
    output_dir: str = typer.Option("output/diagrams", "--output-dir", "-o", help="Destination folder for exported images"),
    format: str = typer.Option("png", "--format", help="Export format: 'png' or 'svg'"),
    scale: float = typer.Option(3.0, "--scale", "-s", help="Rasterization scale/zoom factor for PNG"),
    theme: str = typer.Option("modern_consulting", "--theme", "-t", help="Theme preset if regenerating vectors"),
    transparent: bool = typer.Option(False, "--transparent", help="Export with transparent background"),
    white_bg: bool = typer.Option(False, "--white-bg", help="Force solid pure white (#FFFFFF) background"),
) -> None:
    """Export all diagram pages from a multi-page Draw.io project or YAML spec to individual PNG or SVG files."""
    from src.ppt_engine.diagram_engine import DrawIOProject

    target = Path(file)
    if not target.exists():
        rprint(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    if target.suffix.lower() in (".yaml", ".yml"):
        proj = DrawIOProject.from_yaml(target)
    else:
        proj = DrawIOProject.load(target)
    canvas_bg = "#FFFFFF" if white_bg else None

    try:
        exported_files = proj.export_all_pages(
            output_dir=output_dir,
            format=format,
            scale=scale,
            theme=theme,
            transparent=transparent,
            canvas_bg=canvas_bg,
        )
        rprint(f"[green]✓ Exported {len(exported_files)} pages to directory:[/green] [bold]{output_dir}[/bold]")
        for ef in exported_files:
            rprint(f"  • {ef.name}")
    except Exception as e:
        rprint(f"[red]Error exporting pages:[/red] {e}")
        raise typer.Exit(code=1)


@diagram_app.command("build-project")
def build_diagram_project(
    config: str = typer.Option(..., "--config", "-c", help="Path to YAML diagram project specification"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Path to output .drawio project file"),
) -> None:
    """Build a multi-page Draw.io project from a declarative YAML specification."""
    from src.ppt_engine.diagram_engine import DrawIOProject

    cfg_path = Path(config)
    if not cfg_path.exists():
        rprint(f"[red]Error:[/red] Config file not found: {config}")
        raise typer.Exit(code=1)

    try:
        proj = DrawIOProject.build_from_config(cfg_path, output_path=output)
        out_file = proj.file_path
        rprint(f"[green]✓ Built multi-page Draw.io project:[/green] [bold]{out_file}[/bold]")
        pages = proj.list_pages()
        for p in pages:
            rprint(f"  • Tab {p['index'] + 1}: [bold]{p['name']}[/bold] ({p['node_count']} nodes, {p['edge_count']} edges)")
    except Exception as e:
        rprint(f"[red]Error building diagram project:[/red] {e}")
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


@diagram_app.command("import-library")
def import_diagram_library(
    file: str = typer.Argument(..., help="Path to Draw.io .xml library file (<mxlibrary>)"),
    pack: str = typer.Option(..., "--pack", "-p", help="Pack name / vendor category (e.g. cloudera, snowflake, databricks)"),
) -> None:
    """Import an external Draw.io <mxlibrary> XML package, extract SVGs, and register into icon catalog."""
    from src.ppt_engine.library_importer import import_drawio_library

    lib_p = Path(file)
    if not lib_p.exists():
        rprint(f"[red]Error:[/red] Library file not found: {file}")
        raise typer.Exit(code=1)

    try:
        res = import_drawio_library(lib_p, pack_name=pack)
        rprint(f"[green]✓ Successfully imported {res['imported']} icons into pack '[bold]{pack}[/bold]'![/green]")
        table = Table(title=f"Imported Icons: {pack}")
        table.add_column("Icon ID", style="cyan")
        table.add_column("Title", style="bold green")
        table.add_column("Format", style="yellow")
        table.add_column("Relative Path", style="dim")

        for ic in res["icons"]:
            table.add_row(ic["id"], ic["title"], ic["format"], ic["file"])

        console.print(table)
    except Exception as e:
        rprint(f"[red]Error importing library:[/red] {e}")
        raise typer.Exit(code=1)


@diagram_app.command("list-icons")
def list_diagram_icons(
    pack: Optional[str] = typer.Option(None, "--pack", "-p", help="Filter by pack/category name"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query on icon title or ID"),
) -> None:
    """List or search all registered technology icons available in the workbench."""
    from src.ppt_engine.library_importer import IconRegistry

    icons = IconRegistry.list_icons(pack=pack, query=query)
    if not icons:
        rprint(f"[yellow]No icons found matching query '{query or ''}' in pack '{pack or 'all'}'[/yellow]")
        return

    table = Table(title=f"Registered Diagram Icons ({len(icons)} total)")
    table.add_column("Icon ID / Key", style="cyan")
    table.add_column("Title", style="bold green")
    table.add_column("Pack", style="magenta")
    table.add_column("Format", style="yellow")
    table.add_column("File Path", style="dim")

    for ic in icons:
        table.add_row(ic["id"], ic.get("title", ""), ic.get("pack", "logos"), ic.get("format", "svg"), ic.get("file", ""))

    console.print(table)


# ============================================================================
# PII & Slug Audit Commands (bench pii ...)
# ============================================================================

@pii_app.command("audit")
def audit_pii_cli(
    path: str = typer.Option("output", "--path", "-p", help="Directory or file path to scan for PII leaks"),
    fail_on_findings: bool = typer.Option(False, "--strict", help="Exit with error code 1 if forbidden entities found"),
) -> None:
    """Scan generated deliverables (.docx, .pptx, .xlsx) for forbidden legacy entities."""
    from src.core.slug_registry import PIIAuditReport, audit_directory_pii, audit_pii_in_file

    target = Path(path)
    if not target.exists():
        rprint(f"[red]Error:[/red] Target path not found: {path}")
        raise typer.Exit(code=1)

    if target.is_dir():
        report = audit_directory_pii(target)
    else:
        findings = audit_pii_in_file(target)
        report = PIIAuditReport(total_files_scanned=1, findings=findings)

    if report.passed:
        rprint(f"[green]✓ PII Audit Passed:[/green] Scanned {report.total_files_scanned} files in [bold]{path}[/bold] — 0 forbidden entities found.")
    else:
        rprint(f"[red]✗ PII Audit Failed:[/red] Found {len(report.findings)} potential leaks across {report.total_files_scanned} files scanned:")
        table = Table(title=f"PII Leak Findings in {path}")
        table.add_column("File", style="cyan")
        table.add_column("Location", style="yellow")
        table.add_column("Pattern", style="magenta")
        table.add_column("Matched Snippet", style="bold red")

        for f in report.findings:
            table.add_row(f.file_path.name, f.location, f.pattern, f.match_snippet)

        console.print(table)
        if fail_on_findings:
            raise typer.Exit(code=1)


# ==========================================
# Locale / Bilingual Subsystem Commands
# ==========================================


@locale_app.command("list")
def list_locales_cmd() -> None:
    """List all available localization dictionaries and supported locales."""
    from src.core.locale_engine import list_available_locales, get_locale_engine

    locales = list_available_locales()
    if not locales:
        rprint("[yellow]No locale catalogs found in presets/locales/.[/yellow]")
        return

    table = Table(title="Enterprise Workbench Locales")
    table.add_column("Locale Code", style="cyan", justify="center")
    table.add_column("Name / Description", style="green")
    table.add_column("Key Count", style="magenta", justify="right")
    table.add_column("Catalog File", style="dim")

    names = {
        "en": "English (Canonical / International Tech Standards)",
        "id": "Bahasa Indonesia (Formal Enterprise Governance & Flows)",
    }

    for loc in locales:
        engine = get_locale_engine(loc)
        sections = len(engine._catalogs.get(loc, {}))
        desc = names.get(loc, f"Locale catalog for '{loc}'")
        catalog_name = f"presets/locales/{loc}.yaml"
        table.add_row(loc, desc, f"{sections} sections", catalog_name)

    console.print(table)


@locale_app.command("get")
def get_locale_string_cmd(
    key: str = typer.Argument(..., help="Dot-notation key to lookup (e.g. reference_slides.governance_org.title)"),
    locale: str = typer.Option("en", "--locale", "-l", help="Target locale code (en, id)"),
) -> None:
    """Retrieve a localized string or structure by its dot-notation key."""
    from src.core.locale_engine import get_locale_engine

    engine = get_locale_engine(locale)
    val = engine.get(key)
    if val is None:
        rprint(f"[red]Key not found:[/red] '{key}' in locale '{locale}'")
        raise typer.Exit(code=1)

    rprint(f"[cyan][{locale}][/cyan] [bold]{key}[/bold]:")
    if isinstance(val, (dict, list)):
        import json
        rprint(json.dumps(val, indent=2, ensure_ascii=False))
    else:
        rprint(f"  [green]{val}[/green]")


@locale_app.command("translate")
def translate_hybrid_cmd(
    text: str = typer.Argument(..., help="Text to translate hybridly"),
    target_locale: str = typer.Option("id", "--to", "-t", help="Target locale code (id, en)"),
) -> None:
    """Perform hybrid enterprise translation (preserving cloud & tech terms)."""
    from src.core.locale_engine import get_locale_engine

    engine = get_locale_engine(target_locale)
    result = engine.translate_hybrid(text)
    rprint(f"[bold cyan]Input:[/bold cyan]  {text}")
    rprint(f"[bold green]Output:[/bold green] {result}")


# ============================================================================
# Change Request Commands (bench cr ...)
# ============================================================================

@cr_app.command("file")
def file_change_request_cli(
    title: str = typer.Option(..., "--title", "-t", help="Title of the Change Request"),
    requester: str = typer.Option(..., "--requester", "-r", help="Name and title of the CR requester"),
    description: str = typer.Option(..., "--description", "-d", help="Detailed requirement description"),
    scope_impact: str = typer.Option(..., "--scope", "-s", help="Impacted technical components / architecture"),
    category: str = typer.Option("Scope", "--category", "-c", help="Category: Scope, Schedule, Requirement, Technical, Bug Fix"),
    priority: str = typer.Option("High", "--priority", "-p", help="Priority: Low, Medium, High, Critical"),
    department: str = typer.Option("Consolidated Accounting", "--dept", help="Requester business unit"),
    schedule_days: int = typer.Option(15, "--days", help="Estimated schedule calendar days required"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Target output folder for CR package"),
    project_id: str = typer.Option("TTI_Snowflake_Analytics", "--project", help="Project identifier"),
    client: Optional[str] = typer.Option(None, "--client", help="Client organization slug/name"),
) -> None:
    """
    Intake, model, and generate a complete Enterprise Change Request package:
    1. Change_Request_Form.docx (governance & approval matrix)
    2. Change_Log_Ledger.xlsx (appends registration record)
    3. CR_Scoping_and_Mandays.xlsx (role effort & sizing)
    4. BAST_Change_Request.docx (handover addendum)
    """
    from src.core.change_request import ChangeRequestProcessor, CRSubmission
    from src.core.slug_registry import EngagementContext

    ctx = EngagementContext.from_client_name(client) if client else EngagementContext.default_ngl()
    processor = ChangeRequestProcessor(project_id=project_id, context=ctx)
    submission = CRSubmission(
        title=title,
        requester=requester,
        description=description,
        scope_impact=scope_impact,
        category=category,
        priority=priority,
        department=department,
        schedule_days=schedule_days,
    )

    rprint(f"[cyan]ℹ Processing Change Request:[/cyan] [bold]{title}[/bold]")
    res = processor.file_change_request(submission=submission, output_dir=output_dir)

    rprint(f"[green]✓ Change Request filed successfully:[/green] [bold]CR-{res.cr_id}[/bold]")
    rprint(f"  CR Form:          {res.cr_form_path}")
    rprint(f"  Mandays Scoping:  {res.mandays_sheet_path}")
    rprint(f"  BAST CR Draft:    {res.bast_draft_path}")
    rprint(f"  Total Mandays:    {res.total_mandays} days")


if __name__ == "__main__":
    app()


