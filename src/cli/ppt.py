"""
Generative Presentation Engine CLI Router (`bench ppt ...`)
===========================================================
Themes, automated consulting deck builders, mockup framing,
visual QA linter, and slide export.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional, Union

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

    rprint(f"[cyan]ℹ Generating deck with theme:[/cyan] [bold]{theme}[/bold]")

    from src.ppt_engine.consulting_archetypes import (
        create_presentation,
        HorizonColumnData,
        ScorecardQuadrantData,
        ScorecardMetric,
        build_bcg_3_horizon_slide,
        build_balanced_scorecard_slide,
    )
    from src.ppt_engine.theme_engine import get_theme

    active_theme = get_theme(theme)
    out_path = Path(output) if output else OUTPUT_DIR / f"{theme}_deck" / "presentation.pptx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prs = create_presentation(active_theme)

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
        quadrant_title="Financial Health",
        tagline="Capital Optimization & TCO",
        metrics=[
            ScorecardMetric("TCO Reduction", "34.2%", "ON TRACK", "Positive trajectory via workload right-sizing"),
            ScorecardMetric("Cloud ROI", "2.8x", "EXCEEDED", "Realized return over 18-month depreciation window"),
        ],
    )
    q2 = ScorecardQuadrantData(
        quadrant_title="Operational Velocity",
        tagline="Release Cadence & Recovery",
        metrics=[
            ScorecardMetric("Deployment Frequency", "24/wk", "ON TRACK", "Shift-left release cadence achieved"),
            ScorecardMetric("Mean Time to Recovery", "14 min", "ON TRACK", "Target SLA: < 15 min across Tier 1 apps"),
        ],
    )
    q3 = ScorecardQuadrantData(
        quadrant_title="Customer & Domain Impact",
        tagline="Stakeholder Experience & Latency",
        metrics=[
            ScorecardMetric("Domain NPS", "+48", "EXCEEDED", "Business unit stakeholder feedback score"),
            ScorecardMetric("Query Latency", "120ms", "MONITORED", "P95 response time across self-service marts"),
        ],
    )
    q4 = ScorecardQuadrantData(
        quadrant_title="Risk & Security Posture",
        tagline="Compliance & Vulnerability Hygiene",
        metrics=[
            ScorecardMetric("Compliance Posture", "100%", "ON TRACK", "Zero high/critical CVEs in core staging images"),
            ScorecardMetric("Audit Readiness", "Tier 1", "PASSED", "Passed annual regulatory security inspection"),
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

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except Exception as e:
        rprint(f"[red]Error parsing YAML config '{config}':[/red] {e}")
        raise typer.Exit(code=1)

    if not isinstance(config_data, dict):
        rprint(f"[red]Error:[/red] Deck configuration in '{config}' must be a YAML mapping/dictionary.")
        raise typer.Exit(code=1)

    deck_type = config_data.get("deck_type", "weekly_progress")
    out_path = Path(output) if output else OUTPUT_DIR / "presentations" / f"{config_path.stem}.pptx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    engagement_ctx = None
    if context_file:
        ctx_p = Path(context_file)
        if not ctx_p.exists():
            rprint(f"[red]Error:[/red] Engagement context file not found: {context_file}")
            raise typer.Exit(code=1)
        engagement_ctx = load_engagement_context(context_file)
    elif isinstance(config_data.get("context"), dict):
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

    saved_file = Path(saved_file)
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

    if slide is not None and slide < 1:
        rprint(f"[red]Error:[/red] Slide number must be >= 1 (1-indexed), got {slide}.")
        raise typer.Exit(code=1)

    out_path = Path(output_file) if output_file else in_path.parent / f"{in_path.stem}_substituted{in_path.suffix}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rprint(f"[cyan]ℹ Processing PowerPoint:[/cyan] [bold]{in_path}[/bold]")
    try:
        count, final_out = substitute_presentation_images(
            prs_or_path=in_path,
            new_image_path=img_path,
            output_path=out_path,
            slide_index=slide,
            preserve_aspect_ratio=fit,
        )
    except Exception as e:
        rprint(f"[red]Error substituting presentation images:[/red] {e}")
        raise typer.Exit(code=1)

    final_out = Path(final_out)
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

    if dpi < 200:
        rprint(f"[red]Error:[/red] Target DPI must be >= 200, got {dpi}.")
        raise typer.Exit(code=1)
    if width_in <= 0:
        rprint(f"[red]Error:[/red] Target mockup width (--width-in) must be > 0, got {width_in}.")
        raise typer.Exit(code=1)

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
    capture_live: bool = typer.Option(False, "--capture-live/--no-capture-live", help="Capture live window screenshots from Microsoft PowerPoint if running on macOS"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Directory to save preview screenshots"),
    strict: bool = typer.Option(False, "--strict", help="Exit with error code on critical or warning issues"),
) -> None:
    """Run automated visual inspection and DrawingML collision linting on PowerPoint slides."""
    from src.ppt_engine.visual_qa import PPTVisualLinter, PowerPointScreenCaptureEngine

    p_in = Path(file)
    if not p_in.exists():
        rprint(f"[red]Error:[/red] PowerPoint file not found: {file}")
        raise typer.Exit(code=1)

    out_dir = Path(output_dir) if output_dir else p_in.parent / "previews"

    rprint(f"[cyan]ℹ Running DrawingML Spatial Collision & Text Overflow Linter on:[/cyan] [bold]{p_in.name}[/bold]")
    linter = PPTVisualLinter(p_in)
    issues = linter.lint_presentation()

    crit = 0
    warn = 0
    if issues:
        rprint(f"[yellow]⚠ Found {len(issues)} spatial issue(s):[/yellow]")
        for issue in issues:
            if issue.severity == "CRITICAL":
                color = "red"
                crit += 1
            else:
                color = "yellow"
                warn += 1
            rprint(f"  • [Slide {issue.slide_index}] [{color} bold]{issue.issue_type}[/{color} bold] on [bold]{issue.shape_name}[/bold]: {issue.description}")
            rprint(f"    [dim]↳ Fix: {issue.suggested_fix}[/dim]")
    else:
        rprint("[green]✓ Zero spatial collisions or text overflow hazards detected.[/green]")

    if capture_live and PowerPointScreenCaptureEngine.is_powerpoint_running():
        out_dir.mkdir(parents=True, exist_ok=True)
        rprint(f"[cyan]ℹ Capturing live window screenshots from Microsoft PowerPoint...[/cyan]")
        captured = PowerPointScreenCaptureEngine.capture_live_slides(p_in, out_dir)
        rprint(f"[green]✓ Captured {len(captured)} slide image(s) to:[/green] [bold]{out_dir}[/bold]")
        for c in captured:
            rprint(f"  • {c.name}")

    if strict and (crit > 0 or warn > 0):
        raise typer.Exit(code=1)


@ppt_app.command("lint")
def ppt_lint_cli(
    files: Optional[list[str]] = typer.Argument(None, help="Specific script files to lint"),
) -> None:
    """Run mechanical guardrail verifying adherence to Declarative YAML-First Architecture (Directive 5 & ADR)."""
    import subprocess
    cmd = [sys.executable, "scripts/lint_declarative_architecture.py"]
    if files:
        cmd.extend(files)
    res = subprocess.run(cmd)
    if res.returncode != 0:
        raise typer.Exit(code=res.returncode)


@ppt_app.command("view")
def view_ppt(
    file: str = typer.Argument(..., help="Path to PowerPoint .pptx presentation file"),
    slide: Optional[int] = typer.Option(None, "--slide", "-s", help="Inspect only a specific slide (1-indexed)"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: 'markdown', 'table', or 'json'"),
    full: bool = typer.Option(False, "--full", help="Display full text and table cell contents without truncation"),
) -> None:
    """Inspect presentation structure, shape hierarchies, text copy, and token metrics (L1 Read)."""
    import json
    from src.ppt_engine.presentation_inspector import PresentationInspector

    p_in = Path(file)
    if not p_in.exists():
        rprint(f"[red]Error:[/red] PowerPoint file not found: {file}")
        raise typer.Exit(code=1)

    try:
        inspector = PresentationInspector(p_in)
        info = inspector.inspect()
    except Exception as e:
        rprint(f"[red]Error inspecting presentation:[/red] {e}")
        raise typer.Exit(code=1)

    if format == "json":
        print(json.dumps(info.to_dict(), indent=2))
    elif format == "table":
        table = Table(title=f"Presentation Overview: {p_in.name}")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="green")
        table.add_row("Canvas Size", f"{info.slide_width:.2f}\" x {info.slide_height:.2f}\"")
        table.add_row("Total Slides", str(info.total_slides))
        table.add_row("Total Shapes", str(info.total_shapes))
        table.add_row("Total Words", f"{info.total_words:,}")
        table.add_row("Estimated Tokens", f"~{info.estimated_tokens:,}")
        console.print(table)

        target_slides = info.slides if slide is None else [s for s in info.slides if s.slide_index == slide]
        for s in target_slides:
            s_table = Table(title=f"Slide {s.slide_index}: {s.title or '(Untitled)'}")
            s_table.add_column("ID", style="dim", width=6)
            s_table.add_column("Shape Name", style="bold")
            s_table.add_column("Type", style="magenta")
            s_table.add_column("Bounds [x,y,w,h]", style="cyan")
            s_table.add_column("Content Preview", style="white")

            for sh in s.shapes:
                preview = sh.text[:40] + "..." if (not full and len(sh.text) > 40) else sh.text
                if sh.table_data:
                    preview = f"Table ({len(sh.table_data)}x{len(sh.table_data[0]) if sh.table_data else 0})"
                elif sh.image_info:
                    preview = f"Image ({sh.image_info.get('content_type', '')})"
                s_table.add_row(str(sh.shape_id), sh.name, sh.shape_type, sh.bounds_str, preview or "*(empty)*")
            console.print(s_table)
    else:  # markdown
        print(info.to_markdown(full=full, slide_index=slide))


@ppt_app.command("patch")
def patch_ppt(
    file: str = typer.Argument(..., help="Path to PowerPoint .pptx presentation file"),
    find: Optional[str] = typer.Option(None, "--find", help="Text string to find and replace"),
    replace: Optional[str] = typer.Option(None, "--replace", help="Replacement text string"),
    shape: Optional[str] = typer.Option(None, "--shape", help="Target shape name or shape ID"),
    set_text: Optional[str] = typer.Option(None, "--set-text", help="Set entire text content of target shape"),
    image: Optional[str] = typer.Option(None, "--image", help="Replacement image path for target picture shape"),
    slide: Optional[int] = typer.Option(None, "--slide", "-s", help="Restrict patch to a specific slide (1-indexed)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .pptx path (defaults to <stem>_patched.pptx)"),
    in_place: bool = typer.Option(False, "--in-place", "-i", help="Safely overwrite source file in-place"),
) -> None:
    """Targeted in-situ DOM micro-patching of text and images (L2 Micro-Patch)."""
    from src.ppt_engine.presentation_patcher import PresentationPatcher

    p_in = Path(file)
    if not p_in.exists():
        rprint(f"[red]Error:[/red] PowerPoint file not found: {file}")
        raise typer.Exit(code=1)

    if not find and not set_text and not image:
        rprint("[red]Error:[/red] Must specify at least one operation: --find/--replace, --set-text, or --image.")
        raise typer.Exit(code=1)

    if find and replace is None:
        rprint("[red]Error:[/red] When using --find, --replace must be provided.")
        raise typer.Exit(code=1)

    if set_text and not shape:
        rprint("[red]Error:[/red] When using --set-text, --shape <name_or_id> must be specified.")
        raise typer.Exit(code=1)

    if image and not shape:
        rprint("[red]Error:[/red] When using --image, --shape <name_or_id> must be specified.")
        raise typer.Exit(code=1)

    try:
        patcher = PresentationPatcher(p_in)

        if find and replace is not None:
            shape_id = int(shape) if shape and shape.isdigit() else None
            shape_name = shape if shape and not shape.isdigit() else None
            count = patcher.replace_text(
                find_text=find,
                replace_text=replace,
                slide_index=slide,
                shape_name=shape_name,
                shape_id=shape_id,
            )
            rprint(f"[cyan]ℹ Found and replaced {count} occurrence(s) of '{find}'[/cyan]")

        if set_text and shape:
            ok = patcher.set_shape_text(target=shape, new_text=set_text, slide_index=slide)
            if ok:
                rprint(f"[cyan]ℹ Set shape '{shape}' text successfully[/cyan]")
            else:
                rprint(f"[yellow]⚠ Target shape '{shape}' not found or had no text frame[/yellow]")

        if image and shape:
            ok = patcher.replace_shape_image(target=shape, new_image_path=image, slide_index=slide)
            if ok:
                rprint(f"[cyan]ℹ Replaced image in shape '{shape}' successfully[/cyan]")
            else:
                rprint(f"[yellow]⚠ Target picture shape '{shape}' not found[/yellow]")

        report = patcher.save(output_path=output, in_place=in_place)
        rprint(f"[green]✓ Micro-patch complete:[/green] [bold]{report.output_path}[/bold]")
        if report.impacted_slides:
            rprint(f"  • Impacted slide(s): {report.impacted_slides}")
        for op in report.details:
            rprint(f"  • {op}")

    except Exception as e:
        rprint(f"[red]Error patching presentation:[/red] {e}")
        raise typer.Exit(code=1)


