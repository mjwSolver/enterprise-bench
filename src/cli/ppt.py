"""
Generative Presentation Engine CLI Router (`bench ppt ...`)
===========================================================
Themes, automated consulting deck builders, mockup framing,
visual QA linter, and slide export.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import typer
from rich import print as rprint
from rich.table import Table

from src.core.config import ROOT_DIR, OUTPUT_DIR, ensure_workspace_dirs
from src.core.theme import list_available_themes, EnterpriseTheme
from src.cli.utils import console, open_desktop_review

ppt_app = typer.Typer(
    name="ppt",
    help="Generative Consulting Presentation Engine",
    no_args_is_help=True,
)


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
        title="Data Mesh & Cloud Scale",
        strategic_focus="Federate Domain Ownership",
        metric_highlight="4.2x",
        metric_label="Ingestion Throughput",
        initiatives=["Domain product contracts", "Federated data governance", "Event-driven micro-pipelines"],
        status_tag="PLANNED",
    )
    h3 = HorizonColumnData(
        horizon_tag="HORIZON 3  |  18-36 MONTHS",
        title="Predictive Intelligence",
        strategic_focus="Autonomous Operations",
        metric_highlight="$2.8M",
        metric_label="Run-Rate Savings",
        initiatives=["Self-healing clusters", "Cognitive query optimization", "Real-time AI telemetry"],
        status_tag="VISION",
    )
    build_bcg_3_horizon_slide(
        prs=prs,
        theme=active_theme,
        tracker="STRATEGIC PLATFORM ROADMAP",
        action_title="Enterprise Modernization Trajectory",
        subtitle="Three-stage transformation sequencing immediate operational stabilization with autonomous AI capability.",
        horizons=[h1, h2, h3],
    )

    # Slide 2: Balanced Scorecard
    q1 = ScorecardQuadrantData(
        title="Financial Health",
        metrics=[
            ScorecardMetric("TCO Reduction", "34.2%", "Positive trajectory via workload right-sizing", "positive"),
            ScorecardMetric("Cloud ROI", "2.8x", "Realized return over 18-month depreciation window", "positive"),
        ],
    )
    q2 = ScorecardQuadrantData(
        title="Operational Velocity",
        metrics=[
            ScorecardMetric("Deployment Frequency", "24/wk", "Shift-left release cadence achieved", "positive"),
            ScorecardMetric("Mean Time to Recovery", "14 min", "Target SLA: < 15 min across Tier 1 apps", "positive"),
        ],
    )
    q3 = ScorecardQuadrantData(
        title="Customer & Domain Impact",
        metrics=[
            ScorecardMetric("Domain NPS", "+48", "Business unit stakeholder feedback score", "positive"),
            ScorecardMetric("Query Latency", "120ms", "P95 response time across self-service marts", "neutral"),
        ],
    )
    q4 = ScorecardQuadrantData(
        title="Risk & Security Posture",
        metrics=[
            ScorecardMetric("Compliance Posture", "100%", "Zero high/critical CVEs in core staging images", "positive"),
            ScorecardMetric("Audit Readiness", "Tier 1", "Passed annual regulatory security inspection", "positive"),
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
        open_desktop_review(saved_file, "Microsoft PowerPoint")
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
        open_desktop_review(final_out, "Microsoft PowerPoint")


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
        open_desktop_review(out_path, "Preview")
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
        open_desktop_review(images[0], "Preview")


@ppt_app.command("visual-qa")
def visual_qa_cli(
    file: str = typer.Option("output/presentations/architecture_evolution_cdsw_to_lambda.pptx", "--file", "-f", help="Path to .pptx presentation file"),
    capture_live: bool = typer.Option(True, "--capture-live/--no-capture-live", help="Capture live window screenshots from Microsoft PowerPoint if running on macOS"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Directory to save preview screenshots"),
) -> None:
    """Run automated visual inspection and DrawingML collision linting on PowerPoint slides."""
    from src.ppt_engine.visual_qa import PPTVisualLinter, PowerPointScreenCaptureEngine

    p_in = Path(file)
    if not p_in.exists():
        rprint(f"[red]Error:[/red] PowerPoint file not found: {file}")
        raise typer.Exit(code=1)

    out_dir = Path(output_dir) if output_dir else p_in.parent / "previews"
    out_dir.mkdir(parents=True, exist_ok=True)

    rprint(f"[cyan]ℹ Running DrawingML Spatial Collision & Text Overflow Linter on:[/cyan] [bold]{p_in.name}[/bold]")
    linter = PPTVisualLinter(p_in)
    issues = linter.lint_presentation()

    if issues:
        rprint(f"[yellow]⚠ Found {len(issues)} spatial issue(s):[/yellow]")
        for issue in issues:
            color = "red" if issue.severity == "CRITICAL" else "yellow"
            rprint(f"  • [Slide {issue.slide_index}] [{color} bold]{issue.issue_type}[/{color} bold] on [bold]{issue.shape_name}[/bold]: {issue.description}")
            rprint(f"    [dim]↳ Fix: {issue.suggested_fix}[/dim]")
    else:
        rprint("[green]✓ Zero spatial collisions or text overflow hazards detected.[/green]")

    if capture_live and PowerPointScreenCaptureEngine.is_powerpoint_running():
        rprint(f"[cyan]ℹ Capturing live window screenshots from Microsoft PowerPoint...[/cyan]")
        captured = PowerPointScreenCaptureEngine.capture_live_slides(p_in, out_dir)
        rprint(f"[green]✓ Captured {len(captured)} slide image(s) to:[/green] [bold]{out_dir}[/bold]")
        for c in captured:
            rprint(f"  • {c.name}")
