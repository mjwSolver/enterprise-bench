"""
Diagram Engine V2 Subsystem CLI Router (`bench diagram v2 ...`)
==============================================================
Declarative YAML topology compiler (Draw.io XML, SVG, PNG, native PPTX),
spec validation, template emitter, Tier 1 collision linter, and
Tier 2 adversarial visual QA.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from src.core.config import ROOT_DIR
from src.cli.utils import console, open_desktop_review

diagram_v2_app = typer.Typer(
    name="v2",
    help="Diagram Engine V2 Subsystem (Declarative YAML to Draw.io, SVG, PPTX)",
    no_args_is_help=True,
)


@diagram_v2_app.command("compile")
def compile_diagram_v2_cli(
    spec: str = typer.Argument(..., help="Path to declarative diagram YAML specification"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Destination file or directory for generated artifacts"),
    format: str = typer.Option("all", "--format", "-f", help="Target output format: 'all', 'drawio', 'svg', 'png', or 'pptx'"),
    target: Optional[str] = typer.Option(None, "--target", "-t", help="Target PPTX presentation path for in-situ single-slide replacement"),
    slide: int = typer.Option(1, "--slide", help="1-based slide index targeted for in-situ replacement"),
    pop: bool = typer.Option(False, "--pop", help="Atomic desktop hot-reload: preflight audit, close clean PowerPoint deck, atomic replace, and activate"),
    force: bool = typer.Option(False, "--force", help="Force-close unsaved PowerPoint presentation during hot-reload"),
    strict: bool = typer.Option(False, "--strict", help="Treat Tier 1 WARNING audit findings as blocking preflight failures"),
    skip_audit: bool = typer.Option(False, "--skip-audit", help="Skip Phase 1 Tier 1 geometric audit preflight gate"),
    open_deck: bool = typer.Option(False, "--open", help="Proactively launch generated PPTX slide deck on desktop"),
    preview_ascii: bool = typer.Option(False, "--ascii", help="Print ASCII layout wireframe before compiling"),
) -> None:
    """Compile a declarative YAML specification deterministically into Draw.io XML, SVG, PNG, and native PowerPoint slides."""
    from src.ppt_engine.diagram_v2 import compile_diagram, load_diagram_spec, Tier1GeometricLinter
    from src.ppt_engine.diagram_v2.powerpoint_desktop import PowerPointDesktopManager, PowerPointDirtyError
    from src.ppt_engine.diagram_v2.pptx_compiler import replace_slide_in_presentation

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec}")
        raise typer.Exit(code=1)

    if preview_ascii:
        import yaml
        from rich.markup import escape
        from src.ppt_engine.diagram_v2.ideas import render_ascii_wireframe
        try:
            raw_spec = yaml.safe_load(spec_p.read_text(encoding="utf-8"))
            console.print(escape(render_ascii_wireframe(raw_spec)))
        except Exception as err:
            rprint(f"[dim](ASCII wireframe preview unavailable: {err})[/dim]")

    try:
        formats_list = [f.strip() for f in format.split(",") if f.strip()]
        wants_pptx = bool(target) or any(f.lower() in ("all", "pptx") for f in formats_list)
        if pop and not wants_pptx:
            rprint(
                f"[yellow]⚠ --pop skipped: no --target specified and requested format(s) '{format}' do not include pptx.[/yellow]"
            )
        hot_reload_mode = bool((target or pop) and wants_pptx)

        if hot_reload_mode:
            # Phase 1: Headless Preflight & Tier 1 Geometric Audit Gate
            ds = load_diagram_spec(spec_p)
            if not skip_audit:
                issues = Tier1GeometricLinter(ds).lint()
                blocking = [
                    iss for iss in issues
                    if iss.severity == "CRITICAL" or (strict and iss.severity == "WARNING")
                ]
                if blocking:
                    rprint(f"[red]✗ Phase 1 Preflight Audit Failed ({len(blocking)} blocking issue(s)):[/red]")
                    for iss in blocking:
                        rprint(f"  [red]• [{iss.severity}] {iss.category}[/red] ({iss.element_id}): {iss.description}")
                    raise typer.Exit(code=1)

            # Resolve target PPTX path
            if target:
                target_p = Path(target)
            elif output and Path(output).suffix.lower() == ".pptx":
                target_p = Path(output)
            else:
                out_dir = Path(output) if output else Path("output/diagrams_v2")
                target_p = out_dir / f"{ds.id or spec_p.stem}.pptx"

            # Phase 2: AppleScript PowerPoint State Inspection & Graceful Close
            try:
                closed = PowerPointDesktopManager.close_presentation_if_open(target_p, force=force)
                if closed:
                    rprint(f"[cyan]ℹ Closed open PowerPoint presentation cleanly:[/cyan] [bold]{target_p.name}[/bold]")
            except PowerPointDirtyError as dirty_err:
                rprint(f"[bold red]Unsaved Edits Guard:[/bold red] {dirty_err}")
                raise typer.Exit(code=1)

            # Phase 3: Safe Atomic OpenXML Slide Replacement / Compilation
            if target:
                replace_slide_in_presentation(ds, target_p, slide_index=slide)
                non_pptx = [f for f in formats_list if f.lower() not in ("pptx", "all")]
                rprint(f"[green]✓ Successfully compiled Diagram V2 topology:[/green] [bold]{ds.name}[/bold]")
                rprint(f"  • Native PPTX:  [bold]{target_p}[/bold] (Slide {slide} replaced atomically)")
                if non_pptx:
                    comp_res = compile_diagram(spec_path_or_dict=ds, output_dir_or_file=output or target_p.parent, formats=non_pptx, open_deck=False)
                    if comp_res.drawio_path:
                        rprint(f"  • Draw.io XML:  [bold]{comp_res.drawio_path}[/bold]")
                    if comp_res.svg_path:
                        rprint(f"  • Vector SVG:   [bold]{comp_res.svg_path}[/bold]")
                    if comp_res.png_path:
                        rprint(f"  • High-DPI PNG: [bold]{comp_res.png_path}[/bold]")
            else:
                result = compile_diagram(spec_path_or_dict=ds, output_dir_or_file=output, formats=formats_list, open_deck=False)
                if result.pptx_path:
                    target_p = result.pptx_path
                rprint(f"[green]✓ Successfully compiled Diagram V2 topology:[/green] [bold]{result.spec.name}[/bold]")
                if result.drawio_path:
                    rprint(f"  • Draw.io XML:  [bold]{result.drawio_path}[/bold]")
                if result.svg_path:
                    rprint(f"  • Vector SVG:   [bold]{result.svg_path}[/bold]")
                if result.png_path:
                    rprint(f"  • High-DPI PNG: [bold]{result.png_path}[/bold]")
                if result.pptx_path:
                    rprint(f"  • Native PPTX:  [bold]{result.pptx_path}[/bold]")

            # Phase 4: Instant macOS Desktop Activation (--pop / --open)
            if pop or open_deck:
                activated = PowerPointDesktopManager.activate_presentation(target_p, slide_index=slide)
                if not activated:
                    rprint("[dim]Desktop launch skipped: AppleScript not available on this platform[/dim]")
            return

        effective_open = bool(open_deck and wants_pptx)
        result = compile_diagram(spec_path_or_dict=spec_p, output_dir_or_file=output, formats=formats_list, open_deck=effective_open)
        rprint(f"[green]✓ Successfully compiled Diagram V2 topology:[/green] [bold]{result.spec.name}[/bold]")
        if result.drawio_path:
            rprint(f"  • Draw.io XML:  [bold]{result.drawio_path}[/bold]")
        if result.svg_path:
            rprint(f"  • Vector SVG:   [bold]{result.svg_path}[/bold]")
        if result.png_path:
            rprint(f"  • High-DPI PNG: [bold]{result.png_path}[/bold]")
        if result.pptx_path:
            rprint(f"  • Native PPTX:  [bold]{result.pptx_path}[/bold]")
    except typer.Exit:
        raise
    except Exception as e:
        rprint(f"[red]Error compiling diagram specification:[/red] {e}")
        raise typer.Exit(code=1)


@diagram_v2_app.command("layout")
def layout_diagram_v2_cli(
    spec: str = typer.Argument(..., help="Path to declarative diagram YAML specification (with or without explicit coordinates)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Destination YAML file path for solved coordinates (prints to stdout if omitted)"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if Tier 1 audit reports any critical or warning issues"),
) -> None:
    """Resolve omitted coordinates via the 2D constraint & flexbox auto-layout solver and audit the result."""
    import yaml
    from src.ppt_engine.diagram_v2 import load_diagram_spec, Tier1GeometricLinter, dump_diagram_yaml

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec}")
        raise typer.Exit(code=1)

    try:
        ds = load_diagram_spec(spec_p)
        solved_dict = ds.model_dump(exclude_none=True)

        if output:
            out_p = dump_diagram_yaml(solved_dict, output)
            rprint(f"[green]✓ Solved diagram layout written to:[/green] [bold]{out_p}[/bold]")
        else:
            console.print(yaml.safe_dump(solved_dict, sort_keys=False, allow_unicode=True))
    except Exception as e:
        rprint(f"[red]Error loading or solving diagram specification:[/red] {e}")
        raise typer.Exit(code=1)

    issues = Tier1GeometricLinter(ds).lint()
    crit_count = sum(1 for i in issues if i.severity == "CRITICAL")
    warn_count = sum(1 for i in issues if i.severity == "WARNING")
    if crit_count == 0 and warn_count == 0:
        rprint(f"[green]✓ Tier 1 Geometric Audit Passed:[/green] Zero issues across {len(ds.nodes)} node(s) and {len(ds.containers)} container(s).")
    else:
        rprint(f"[yellow]⚠ Tier 1 Audit after layout:[/yellow] {crit_count} CRITICAL, {warn_count} WARNING.")
        for iss in issues:
            rprint(f"  • [{iss.severity}] {iss.category} ({iss.element_id}): {iss.description}")
        if crit_count > 0 or (strict and warn_count > 0):
            raise typer.Exit(code=1)


@diagram_v2_app.command("ingest")
def ingest_mermaid_v2_cli(
    mermaid: Optional[str] = typer.Option(None, "--mermaid", "-m", help="Path to .mmd file or inline Mermaid flowchart text"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Destination YAML file path (prints to stdout if omitted)"),
    diagram_id: Optional[str] = typer.Option(None, "--id", help="Diagram slug ID (defaults to input filename stem)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Diagram title / action headline"),
    theme: str = typer.Option("metrodata", "--theme", help="Theme name"),
    audit: bool = typer.Option(True, "--audit/--no-audit", help="Run Tier 1 geometric audit on transpiled YAML"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if Tier 1 audit reports any critical or warning issues"),
) -> None:
    """Transpile a Mermaid flowchart (.mmd or inline snippet) into an audit-compliant Diagram V2 YAML spec."""
    from src.ppt_engine.diagram_v2 import Tier1GeometricLinter
    from src.ppt_engine.diagram_v2.mermaid_transpiler import transpile_mermaid_to_yaml

    if not mermaid:
        rprint("[red]Error:[/red] Provide --mermaid <path.mmd or inline Mermaid code>.")
        raise typer.Exit(code=1)

    is_file = False
    m_path = None
    try:
        m_path = Path(mermaid)
        is_file = m_path.exists() and m_path.is_file()
    except OSError:
        is_file = False

    if is_file and m_path is not None:
        code = m_path.read_text(encoding="utf-8")
        resolved_id = diagram_id or m_path.stem
    else:
        code = mermaid
        resolved_id = diagram_id or (Path(output).stem if output else "mermaid_diagram")

    try:
        spec_obj, yaml_text = transpile_mermaid_to_yaml(
            mermaid_code=code,
            diagram_id=resolved_id,
            name=name,
            theme=theme,
            output_path=output,
        )
    except ValueError as err:
        rprint(f"[red]Error transpiling Mermaid input:[/red] {err}")
        raise typer.Exit(code=1)

    if output:
        rprint(f"[green]✓ Transpiled Mermaid AST to V2 YAML:[/green] [bold]{output}[/bold]")
        rprint(f"  • Containers: {len(spec_obj.containers)} | Nodes: {len(spec_obj.nodes)} | Flows: {len(spec_obj.flows)}")
    else:
        console.print(yaml_text)

    if audit or strict:
        issues = Tier1GeometricLinter(spec_obj).lint()
        crit = sum(1 for i in issues if i.severity == "CRITICAL")
        warn = sum(1 for i in issues if i.severity == "WARNING")
        if crit == 0 and warn == 0:
            rprint("[green]✓ Tier 1 Geometric Audit Passed:[/green] Zero collisions or clearance violations.")
        else:
            rprint(f"[yellow]⚠ Tier 1 Audit Summary:[/yellow] {crit} CRITICAL, {warn} WARNING.")
            for iss in issues:
                rprint(f"  • [{iss.severity}] {iss.category} ({iss.element_id}): {iss.description}")
            if crit > 0 or (strict and warn > 0):
                raise typer.Exit(code=1)


@diagram_v2_app.command("validate")
def validate_diagram_v2_cli(
    spec: str = typer.Argument(..., help="Path to declarative diagram YAML specification"),
) -> None:
    """Validate a declarative diagram YAML specification schema and check icon assets."""
    from src.ppt_engine.diagram_v2 import validate_diagram_spec

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec}")
        raise typer.Exit(code=1)

    is_valid, issues, validated = validate_diagram_spec(spec_p)
    if is_valid and validated:
        rprint(f"[green]✓ Specification is valid:[/green] [bold]{validated.name}[/bold] (ID: {validated.id})")
        rprint(f"  • Containers: {len(validated.containers)}")
        rprint(f"  • Nodes:      {len(validated.nodes)}")
        rprint(f"  • Flows:      {len(validated.flows)}")
        rprint(f"  • Badges:     {len(validated.badges)}")
    else:
        rprint(f"[red]✗ Specification validation failed with {len(issues)} issue(s):[/red]")
        for iss in issues:
            rprint(f"  [red]•[/red] {iss}")
        raise typer.Exit(code=1)


@diagram_v2_app.command("sample")
def sample_diagram_v2_cli(
    name: str = typer.Option("aws_lambda", "--name", "-n", help="Sample template name: 'aws_lambda', 'cdsw', 'interwoven', 'medallion', 'active_active_dr', or 'streaming_cdc'"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Destination path to write sample YAML"),
) -> None:
    """Emit a production-grade sample declarative diagram YAML specification."""
    sample_dir = ROOT_DIR / "src" / "ppt_engine" / "diagram_v2" / "samples"
    diagrams_dir = ROOT_DIR / "specs" / "diagrams"
    file_map = {
        "aws_lambda": sample_dir / "proposed_aws_lambda.yaml",
        "cdsw": sample_dir / "cdsw_legacy_batch.yaml",
        "interwoven": sample_dir / "interwoven_migration.yaml",
        "medallion": diagrams_dir / "template_medallion_architecture.yaml",
        "active_active_dr": diagrams_dir / "template_active_active_dr.yaml",
        "streaming_cdc": diagrams_dir / "template_streaming_cdc_telemetry.yaml",
    }
    src_file = file_map.get(name.lower())
    if not src_file or not src_file.exists():
        rprint(f"[red]Error:[/red] Unknown sample '{name}'. Available: {list(file_map.keys())}")
        raise typer.Exit(code=1)

    content = src_file.read_text(encoding="utf-8")
    if output:
        out_p = Path(output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(content, encoding="utf-8")
        rprint(f"[green]✓ Sample YAML written to:[/green] [bold]{out_p}[/bold]")
    else:
        console.print(content)


@diagram_v2_app.command("ideas")
def ideas_diagram_v2_cli(
    action: str = typer.Argument("list", help="Action: 'list', 'preview', or 'scaffold'"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="Pattern name (e.g. '3-swimlane', 'interwoven-hub', 'data-pipeline', 'runbook-grid')"),
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Path to existing YAML spec to preview in ASCII"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Destination path for scaffolded YAML"),
) -> None:
    """Explore proven consulting layout patterns, preview ASCII wireframes, or scaffold starting specs."""
    from src.ppt_engine.diagram_v2.ideas import list_idea_patterns, get_pattern, render_ascii_wireframe

    act = action.lower().strip()
    if act == "list":
        patterns = list_idea_patterns()
        table = Table(title="Diagram Engine V2 - Canonical Layout Patterns", show_header=True, header_style="bold cyan")
        table.add_column("Pattern ID", style="bold green", width=18)
        table.add_column("Name", style="bold white", width=32)
        table.add_column("Node Capacity", style="yellow", width=22)
        table.add_column("Description", style="dim", width=45)
        for p in patterns:
            table.add_row(p["id"], p["name"], p["recommended_nodes"], p["description"])
        console.print(table)
        rprint("\n[dim]To view ASCII wireframe: [bold]bench diagram v2 ideas preview -p <pattern>[/bold][/dim]")
        rprint("[dim]To scaffold starter YAML: [bold]bench diagram v2 ideas scaffold -p <pattern> -o specs/my_slide.yaml[/bold][/dim]")

    elif act == "preview":
        from rich.markup import escape
        if spec:
            spec_p = Path(spec)
            if not spec_p.exists():
                rprint(f"[red]Error:[/red] Spec file not found: {spec}")
                raise typer.Exit(code=1)
            import yaml
            raw = yaml.safe_load(spec_p.read_text(encoding="utf-8"))
            console.print(escape(render_ascii_wireframe(raw)))
        elif pattern:
            pat = get_pattern(pattern)
            if not pat:
                rprint(f"[red]Error:[/red] Unknown pattern '{pattern}'. Run 'bench diagram v2 ideas list' to see available.")
                raise typer.Exit(code=1)
            rprint(f"[bold cyan]Wireframe Draft: {pat['name']}[/bold cyan]")
            console.print(escape(pat.get("ascii_wireframe", "(No wireframe)")))
        else:
            rprint("[yellow]Specify --pattern <name> or --spec <path.yaml> to preview.[/yellow]")

    elif act == "scaffold":
        if not pattern:
            pattern = "3-swimlane"
        pat = get_pattern(pattern)
        if not pat or not pat.get("yaml_template"):
            rprint(f"[red]Error:[/red] Template for pattern '{pattern}' not found. Available: '3-swimlane', 'interwoven-hub'")
            raise typer.Exit(code=1)

        template_yaml = pat["yaml_template"]
        if output:
            out_p = Path(output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(template_yaml, encoding="utf-8")
            rprint(f"[green]✓ Scaffolded YAML written to:[/green] [bold]{out_p}[/bold]")
        else:
            console.print(template_yaml)
    else:
        rprint(f"[red]Unknown action '{action}'. Use 'list', 'preview', or 'scaffold'.[/red]")
        raise typer.Exit(code=1)


@diagram_v2_app.command("audit")
def audit_diagram_v2_cli(
    spec: str = typer.Argument(..., help="Path to declarative diagram YAML specification or directory of specs"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if any critical issues or warnings are found"),
) -> None:
    """Run Tier 1 geometric collision and clearance linting on a declarative diagram specification or multi-slide directory."""
    from src.ppt_engine.diagram_v2 import load_diagram_spec, Tier1GeometricLinter
    from src.ppt_engine.diagram_v2.stray_consolidator import validate_bundle_headers

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file or directory not found: {spec}")
        raise typer.Exit(code=1)

    if spec_p.is_dir():
        yaml_files = sorted([
            p for p in spec_p.glob("*.yaml")
            if p.is_file() and not p.name.startswith(".")
        ])
        if not yaml_files:
            yaml_files = sorted([
                p for p in spec_p.glob("*.yml")
                if p.is_file() and not p.name.startswith(".")
            ])

        if not yaml_files:
            rprint(f"[red]Error:[/red] No YAML diagram specifications found in directory: {spec_p}")
            raise typer.Exit(code=1)

        rprint(f"[cyan]ℹ Running Tier 1 Geometric Audit & Bundle Header Linter on directory:[/cyan] [bold]{spec_p}[/bold] ({len(yaml_files)} specs)")

        all_issues: List[Tuple[str, Any]] = []
        loaded_specs = []

        for yf in yaml_files:
            try:
                ds = load_diagram_spec(yf)
                loaded_specs.append(ds)
                linter = Tier1GeometricLinter(ds)
                for iss in linter.lint():
                    all_issues.append((yf.name, iss))
            except Exception as e:
                rprint(f"[yellow]⚠ Failed to load specification '{yf.name}':[/yellow] {e}")
                from src.ppt_engine.diagram_v2.auditor import AuditIssue
                all_issues.append((
                    yf.name,
                    AuditIssue(
                        severity="CRITICAL",
                        category="SPEC_LOAD_FAILURE",
                        element_id=yf.name,
                        description=f"Failed to parse or validate specification: {e}",
                        suggested_fix="Fix YAML syntax or schema errors according to DiagramEngineV2 spec.",
                    ),
                ))

        # Run multi-slide bundle header verification across all loaded specs
        bundle_issues = validate_bundle_headers(loaded_specs)
        for b_iss in bundle_issues:
            all_issues.append(("bundle", b_iss))

        if not all_issues:
            rprint(f"[green]✓ Tier 1 Geometric Audit Passed:[/green] Zero collisions, occlusions, or clearance violations across all {len(loaded_specs)} specifications in [bold]{spec_p.name}[/bold].")
            return

        table = Table(title=f"Tier 1 Geometric Collision & Bundle Audit: {spec_p.name} ({len(loaded_specs)} specs)")
        table.add_column("Spec / File", style="dim cyan", width=24)
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Category", style="cyan", width=28)
        table.add_column("Element ID", style="magenta", width=22)
        table.add_column("Description", style="white")
        table.add_column("Suggested Fix", style="dim green")

        critical_count = 0
        warning_count = 0

        for source_name, iss in all_issues:
            if iss.severity == "CRITICAL":
                sev_styled = "[red]CRITICAL[/red]"
                critical_count += 1
            elif iss.severity == "WARNING":
                sev_styled = "[yellow]WARNING[/yellow]"
                warning_count += 1
            else:
                sev_styled = "[cyan]INFO[/cyan]"

            table.add_row(source_name, sev_styled, iss.category, iss.element_id, iss.description, iss.suggested_fix)

        console.print(table)
        rprint(f"\n[bold]Audit Summary:[/bold] {critical_count} critical issue(s), {warning_count} warning(s) across {len(loaded_specs)} specifications")

        if critical_count > 0 or (strict and warning_count > 0):
            rprint("[red]✗ Tier 1 geometric audit failed.[/red]")
            raise typer.Exit(code=1)
        else:
            rprint("[yellow]⚠ Tier 1 geometric audit passed with warnings.[/yellow]")
        return

    # Single-file audit
    try:
        diagram_spec = load_diagram_spec(spec_p)
    except Exception as e:
        rprint(f"[red]Error loading diagram specification:[/red] {e}")
        raise typer.Exit(code=1)

    rprint(f"[cyan]ℹ Running Tier 1 Geometric Collision & Clearance Linter on:[/cyan] [bold]{diagram_spec.name}[/bold]")
    linter = Tier1GeometricLinter(diagram_spec)
    issues = linter.lint()

    if not issues:
        rprint(f"[green]✓ Tier 1 Geometric Audit Passed:[/green] Zero collisions, occlusions, or clearance violations in [bold]{diagram_spec.name}[/bold].")
        return

    table = Table(title=f"Tier 1 Geometric Collision Audit: {diagram_spec.name} ({diagram_spec.id})")
    table.add_column("Severity", style="bold", width=12)
    table.add_column("Category", style="cyan", width=28)
    table.add_column("Element ID", style="magenta", width=22)
    table.add_column("Description", style="white")
    table.add_column("Suggested Fix", style="dim green")

    critical_count = 0
    warning_count = 0

    for iss in issues:
        if iss.severity == "CRITICAL":
            sev_styled = "[red]CRITICAL[/red]"
            critical_count += 1
        elif iss.severity == "WARNING":
            sev_styled = "[yellow]WARNING[/yellow]"
            warning_count += 1
        else:
            sev_styled = "[cyan]INFO[/cyan]"

        table.add_row(sev_styled, iss.category, iss.element_id, iss.description, iss.suggested_fix)

    console.print(table)
    rprint(f"\n[bold]Audit Summary:[/bold] {critical_count} critical issue(s), {warning_count} warning(s)")

    if critical_count > 0 or (strict and warning_count > 0):
        rprint("[red]✗ Tier 1 geometric audit failed.[/red]")
        raise typer.Exit(code=1)
    else:
        rprint("[yellow]⚠ Tier 1 geometric audit passed with warnings.[/yellow]")


@diagram_v2_app.command("visual-qa")
def visual_qa_diagram_v2_cli(
    spec: str = typer.Argument(..., help="Path to declarative diagram YAML specification"),
    tier: str = typer.Option("both", "--tier", "-t", help="Verification tier to run: '1' (geometric), '2' (adversarial visual), or 'both'"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Directory to save visual QA reports and rendered plates"),
    open_plate: bool = typer.Option(False, "--open", help="Launch rendered raster image on desktop upon completion"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if any critical defect or FAIL verdict"),
) -> None:
    """Run Tier 1 geometric collision linting and Tier 2 adversarial Visual QA subagent verification per Milestone 33 post-mortem."""
    from src.ppt_engine.diagram_v2 import load_diagram_spec, Tier1GeometricLinter, Tier2VisualVerifier

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec}")
        raise typer.Exit(code=1)

    try:
        diagram_spec = load_diagram_spec(spec_p)
    except Exception as e:
        rprint(f"[red]Error loading diagram specification:[/red] {e}")
        raise typer.Exit(code=1)

    tier_mode = tier.lower().strip()
    if tier_mode not in {"1", "2", "both"}:
        rprint(f"[red]Error:[/red] Invalid --tier '{tier}'. Allowed values: '1', '2', 'both'.")
        raise typer.Exit(code=1)

    safe_id = Path(str(diagram_spec.id)).name or "diagram"
    out_dir = Path(output) if output else Path("TEMP/visual_qa") / safe_id

    if tier_mode == "1":
        linter = Tier1GeometricLinter(diagram_spec)
        issues = linter.lint()
        if not issues:
            rprint(f"[green]✓ Tier 1 Geometric Audit Passed:[/green] Zero collisions, occlusions, or clearance violations in [bold]{diagram_spec.name}[/bold].")
            return
        table = Table(title=f"Tier 1 Geometric Collision Audit: {diagram_spec.name}")
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Category", style="cyan", width=28)
        table.add_column("Element ID", style="magenta", width=22)
        table.add_column("Description", style="white")
        table.add_column("Suggested Fix", style="dim green")
        crit = 0
        warn = 0
        for iss in issues:
            if iss.severity == "CRITICAL":
                sev_styled = "[red]CRITICAL[/red]"
                crit += 1
            elif iss.severity == "WARNING":
                sev_styled = "[yellow]WARNING[/yellow]"
                warn += 1
            else:
                sev_styled = "[cyan]INFO[/cyan]"
            table.add_row(sev_styled, iss.category, iss.element_id, iss.description, iss.suggested_fix)
        console.print(table)
        if crit > 0 or (strict and warn > 0):
            raise typer.Exit(code=1)
        return

    rprint(f"[cyan]ℹ Running Tier 1 & Tier 2 Adversarial Visual QA Verification on:[/cyan] [bold]{diagram_spec.name}[/bold]")
    try:
        verifier = Tier2VisualVerifier(diagram_spec)
        result = verifier.verify(output_dir=out_dir)
    except Exception as e:
        rprint(f"[red]Error running Visual QA verification:[/red] {e}")
        raise typer.Exit(code=1)

    verdict_colors = {
        "VERIFIED_PASS": "green",
        "CONDITIONAL_PASS": "yellow",
        "REVISE_REQUIRED": "magenta",
        "FAIL": "red",
    }
    v_color = verdict_colors.get(result.verdict, "white")

    rprint(f"\n[bold]Visual QA Verdict:[/bold] [{v_color} bold]{result.verdict}[/{v_color} bold] | [bold]Adversarial Score:[/bold] [{v_color}]{result.score:.1f}/100[/{v_color}]")

    dim_table = Table(title="Adversarial Dimension Scorecard (Milestone 33 Standards)")
    dim_table.add_column("Evaluation Dimension", style="cyan")
    dim_table.add_column("Score", style="bold")
    dim_table.add_column("Status", style="bold")

    for dim, score in result.dimension_scores.items():
        status = "[green]EXCELLENT[/green]" if score >= 90 else ("[yellow]ADEQUATE[/yellow]" if score >= 75 else "[red]DEFECTIVE[/red]")
        dim_table.add_row(dim.replace("_", " ").title(), f"{score:.1f}", status)

    console.print(dim_table)

    all_findings = result.tier2_findings
    if all_findings:
        find_table = Table(title=f"Adversarial Visual Findings ({len(all_findings)} total)")
        find_table.add_column("Severity", style="bold", width=12)
        find_table.add_column("Dimension", style="cyan", width=26)
        find_table.add_column("Element / Region", style="magenta", width=22)
        find_table.add_column("Observable Flaw", style="white")
        find_table.add_column("Prescriptive YAML Fix", style="dim green")

        for f in all_findings:
            sev = f"[red]{f.severity}[/red]" if f.severity == "CRITICAL" else (f"[yellow]{f.severity}[/yellow]" if f.severity == "WARNING" else f"[dim]{f.severity}[/dim]")
            find_table.add_row(sev, f.dimension, f.element_or_region, f.flaw_description, f.prescriptive_fix)

        console.print(find_table)
    else:
        rprint("[green]✓ Zero adversarial defects or optical imbalances detected.[/green]")

    if result.raster_image_path:
        rprint(f"\n  • High-DPI Render:     [bold]{result.raster_image_path}[/bold]")
    if result.subagent_prompt_path:
        rprint(f"  • Subagent Briefing:   [bold]{result.subagent_prompt_path}[/bold]")

    if open_plate and result.raster_image_path and result.raster_image_path.exists():
        open_desktop_review(result.raster_image_path, "Preview")

    if strict and (result.verdict == "FAIL" or result.total_critical_count > 0):
        rprint(f"[red]✗ Visual QA verification failed with {result.total_critical_count} critical defect(s).[/red]")
        raise typer.Exit(code=1)


@diagram_v2_app.command("reconcile")
def reconcile_diagram_v2_cli(
    target: str = typer.Argument(..., help="Path to declarative diagram YAML specification or PowerPoint presentation (.pptx)"),
    pptx: Optional[str] = typer.Option(None, "--pptx", "-p", help="Path to edited PowerPoint presentation (.pptx)"),
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Path to declarative diagram YAML specification (if target is PPTX)"),
    slide_index: int = typer.Option(1, "--slide", help="Slide index (1-based) to inspect in presentation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report detected differences without modifying YAML or recompiling"),
    no_recompile: bool = typer.Option(False, "--no-recompile", help="Update YAML AST but skip triggering 4-way re-compilation"),
    format: str = typer.Option("all", "--format", "-f", help="Target formats when re-compiling: 'all', 'drawio', 'svg', 'png', 'pptx'"),
    snap: float = typer.Option(0.05, "--snap", help="Geometric grid snap increment in inches (default: 0.05\")"),
    threshold: float = typer.Option(0.02, "--threshold", help="Minimum shift delta in inches to trigger reconciliation (default: 0.02\")"),
    skip_pptx: bool = typer.Option(False, "--skip-pptx", help="Skip PPTX re-compilation to prevent cyclic write triggers"),
) -> None:
    """
    Reconcile PowerPoint DrawingML slide mutations against declarative YAML AST (Topic 11).
    Diffs live shapes against specification, pruning deleted nodes and orphan flows,
    updating mutated text, snapping altered coordinates to grid, and triggering automatic re-compilation.
    """
    from src.ppt_engine.diagram_v2 import reconcile_diagram

    target_p = Path(target)
    if not target_p.exists():
        rprint(f"[red]Error:[/red] Target file not found: {target}")
        raise typer.Exit(code=1)

    spec_p: Path
    pptx_p: Optional[Path] = None

    if target_p.suffix.lower() == ".pptx":
        pptx_p = target_p
        if spec:
            spec_p = Path(spec)
        else:
            candidates = [
                Path("specs/diagrams") / f"{pptx_p.stem}.yaml",
                Path("specs/diagrams") / f"{pptx_p.stem}.yml",
                pptx_p.parent / f"{pptx_p.stem}.yaml",
                pptx_p.parent / f"{pptx_p.stem}.yml",
            ]
            found = next((c for c in candidates if c.exists()), None)
            if not found:
                rprint(f"[red]Error:[/red] Could not auto-locate YAML specification for '{pptx_p.name}'. Please specify --spec <path.yaml>.")
                raise typer.Exit(code=1)
            spec_p = found
    else:
        spec_p = target_p
        if pptx:
            pptx_p = Path(pptx)

    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec_p}")
        raise typer.Exit(code=1)
    if pptx_p and not pptx_p.exists():
        rprint(f"[red]Error:[/red] PowerPoint presentation file not found: {pptx_p}")
        raise typer.Exit(code=1)

    rprint(f"[cyan]ℹ Running Bidirectional PowerPoint Decompiler & YAML Reconciliation Engine:[/cyan]")
    rprint(f"  • YAML Spec:  [bold]{spec_p}[/bold]")
    if pptx_p:
        rprint(f"  • PPTX Slide: [bold]{pptx_p}[/bold] (Slide {slide_index})")

    formats_list = [f.strip() for f in format.split(",") if f.strip()]

    try:
        res = reconcile_diagram(
            spec_path=spec_p,
            pptx_path=pptx_p,
            slide_index=slide_index,
            dry_run=dry_run,
            no_recompile=no_recompile,
            formats=formats_list,
            skip_pptx=skip_pptx,
            snap_grid=snap,
            snap_threshold=threshold,
        )
    except Exception as e:
        rprint(f"[red]Reconciliation failed:[/red] {e}")
        raise typer.Exit(code=1)

    if not res.has_changes:
        rprint(f"\n[green]✓ Clean Parity:[/green] PowerPoint slide and YAML specification are [bold]100% in sync[/bold]. Zero mutations or prunings detected.")
        return

    pptx_name = res.pptx_path.name if res.pptx_path else "N/A"
    spec_name = res.spec_path.name if res.spec_path else spec_p.name
    table = Table(title=f"Topic 11 Reconciliation Diff: {spec_name} ⟷ {pptx_name}")
    table.add_column("Category", style="cyan", width=14)
    table.add_column("Element ID", style="magenta", width=24)
    table.add_column("Action", style="bold", width=12)
    table.add_column("Property", style="dim white", width=14)
    table.add_column("Previous Value (YAML)", style="white")
    table.add_column("Reconciled Value (PPTX)", style="bold green")

    for c in res.changes:
        old_val_str = "[dim]None[/dim]" if c.old_value is None else str(c.old_value)
        new_val_str = "[dim]None[/dim]" if c.new_value is None else str(c.new_value)
        cat = c.element_type.title() if c.element_type else "Element"
        if c.change_type.startswith("pruned_"):
            action_styled = "[red]PRUNED[/red]"
            table.add_row(cat, c.element_id, action_styled, "existence", "" if c.old_value is None else str(c.old_value), "[dim]REMOVED[/dim]")
        elif c.change_type == "mutated_text":
            action_styled = "[green]MUTATED[/green]"
            table.add_row(cat, c.element_id, action_styled, c.field_name or "text", old_val_str, new_val_str)
        elif c.change_type == "mutated_geometry":
            action_styled = "[cyan]GEOMETRY[/cyan]"
            table.add_row(cat, c.element_id, action_styled, c.field_name or "geometry", old_val_str, new_val_str)
        else:
            action_styled = f"[yellow]{c.change_type.upper()}[/yellow]"
            table.add_row(cat, c.element_id, action_styled, c.field_name or "property", old_val_str, new_val_str)

    console.print(table)
    summary_parts = []
    if res.pruned_nodes:
        summary_parts.append(f"{len(res.pruned_nodes)} node(s) pruned")
    if res.pruned_flows:
        summary_parts.append(f"{len(res.pruned_flows)} flow(s) pruned")
    if res.mutated_texts:
        summary_parts.append(f"{len(res.mutated_texts)} text field(s) updated")
    if res.mutated_geometries:
        summary_parts.append(f"{len(res.mutated_geometries)} coordinate(s) snapped")
    rprint(f"\n[bold]Reconciliation Summary:[/bold] {', '.join(summary_parts) if summary_parts else 'Zero changes'}.")

    if dry_run:
        rprint("[yellow]⚠ Dry-run complete. Specification and deliverables were not modified.[/yellow]")
    else:
        rprint(f"[green]✓ Successfully reconciled YAML AST:[/green] [bold]{res.spec_path}[/bold]")
        if res.recompiled and res.recompile_result:
            rprint(f"[cyan]ℹ Automatic 4-way re-compilation completed:[/cyan]")
            if res.recompile_result.drawio_path:
                rprint(f"  • Draw.io XML:  [bold]{res.recompile_result.drawio_path}[/bold]")
            if res.recompile_result.svg_path:
                rprint(f"  • Vector SVG:   [bold]{res.recompile_result.svg_path}[/bold]")
            if res.recompile_result.png_path:
                rprint(f"  • High-DPI PNG: [bold]{res.recompile_result.png_path}[/bold]")
            if res.recompile_result.pptx_path:
                rprint(f"  • Native PPTX:  [bold]{res.recompile_result.pptx_path}[/bold]")


@diagram_v2_app.command("watch")
def watch_diagram_v2_cli(
    spec: str = typer.Argument(..., help="Path to declarative diagram YAML specification"),
    pptx: Optional[str] = typer.Option(None, "--pptx", "-p", help="Path to PowerPoint presentation (.pptx) to monitor (auto-located if omitted)"),
    slide_index: int = typer.Option(1, "--slide", "-s", help="Slide index (1-based) to inspect in presentation"),
    debounce: float = typer.Option(0.5, "--debounce", "-d", help="Debounce silence window in seconds (default: 0.5s)"),
    snap: float = typer.Option(0.05, "--snap", help="Geometric grid snap increment in inches (default: 0.05\")"),
    threshold: float = typer.Option(0.02, "--threshold", help="Minimum shift delta in inches to trigger reconciliation (default: 0.02\")"),
    skip_pptx: bool = typer.Option(True, "--skip-pptx/--no-skip-pptx", help="Skip PPTX compilation to prevent cyclic write loops (default: True)"),
    format: str = typer.Option("drawio,svg,png", "--format", "-f", help="Companion formats to regenerate upon PowerPoint save"),
    remote_drift: bool = typer.Option(False, "--remote-drift", help="Poll remote Google Drive pins every 30s and warn on out-of-band edits"),
    receipt: Optional[str] = typer.Option(None, "--receipt", "-r", help="Optional path to .sync_receipt.json for remote drift checks"),
) -> None:
    """
    Autonomous PPTX File Watcher & Reverse Geometric Synchronization Daemon.
    Monitors presentation saves (Cmd+S), debounces atomic writes (500ms), reconciles
    shape coordinates and text into YAML AST, snaps to 0.05" grid, and regenerates
    companion artifacts headlessly without cyclic write loops.
    """
    from src.ppt_engine.diagram_v2.watcher import PPTXWatcher

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec}")
        raise typer.Exit(code=1)

    formats_list = [f.strip() for f in format.split(",") if f.strip()]

    def on_change(p_path: Path) -> None:
        rprint(f"\n[cyan]⚡ Save event detected on:[/cyan] [bold]{p_path.name}[/bold] — debouncing {debounce:.1f}s...")

    def on_reconciled(res: Any) -> None:
        if not res.has_changes:
            rprint(f"[dim]✓ PPTX verified in sync with {spec_p.name} (zero mutations).[/dim]")
            return

        table = Table(title=f"Autonomous Synchronization: {res.spec_path.name} ⟷ {res.pptx_path.name}")
        table.add_column("Category", style="cyan", width=14)
        table.add_column("Element ID", style="magenta", width=24)
        table.add_column("Action", style="bold", width=12)
        table.add_column("Property", style="dim white", width=14)
        table.add_column("Previous Value (YAML)", style="white")
        table.add_column("Reconciled Value (PPTX)", style="bold green")

        for c in res.changes:
            old_val_str = "[dim]None[/dim]" if c.old_value is None else str(c.old_value)
            new_val_str = "[dim]None[/dim]" if c.new_value is None else str(c.new_value)
            cat = c.element_type.title() if c.element_type else "Element"
            if c.change_type.startswith("pruned_"):
                action_styled = "[red]PRUNED[/red]"
                table.add_row(cat, c.element_id, action_styled, "existence", "" if c.old_value is None else str(c.old_value), "[dim]REMOVED[/dim]")
            elif c.change_type == "mutated_text":
                action_styled = "[green]MUTATED[/green]"
                table.add_row(cat, c.element_id, action_styled, c.field_name or "text", old_val_str, new_val_str)
            elif c.change_type == "mutated_geometry":
                action_styled = "[cyan]GEOMETRY[/cyan]"
                table.add_row(cat, c.element_id, action_styled, c.field_name or "geometry", old_val_str, new_val_str)
            else:
                action_styled = f"[yellow]{c.change_type.upper()}[/yellow]"
                table.add_row(cat, c.element_id, action_styled, c.field_name or "property", old_val_str, new_val_str)

        console.print(table)
        summary_parts = []
        if res.pruned_nodes:
            summary_parts.append(f"{len(res.pruned_nodes)} node(s) pruned")
        if res.pruned_flows:
            summary_parts.append(f"{len(res.pruned_flows)} flow(s) pruned")
        if res.mutated_texts:
            summary_parts.append(f"{len(res.mutated_texts)} text field(s) updated")
        if res.mutated_geometries:
            summary_parts.append(f"{len(res.mutated_geometries)} coordinate(s) snapped")
        rprint(f"[bold]Reconciliation Summary:[/bold] {', '.join(summary_parts)}.")
        rprint(f"[green]✓ Successfully synchronized YAML AST:[/green] [bold]{res.spec_path}[/bold]")
        if res.recompiled and res.recompile_result:
            rprint(f"[cyan]ℹ Companion re-compilation completed:[/cyan]")
            if res.recompile_result.drawio_path:
                rprint(f"  • Draw.io XML:  [bold]{res.recompile_result.drawio_path}[/bold]")
            if res.recompile_result.svg_path:
                rprint(f"  • Vector SVG:   [bold]{res.recompile_result.svg_path}[/bold]")
            if res.recompile_result.png_path:
                rprint(f"  • High-DPI PNG: [bold]{res.recompile_result.png_path}[/bold]")

    try:
        watcher = PPTXWatcher(
            spec_path=spec_p,
            pptx_path=pptx,
            slide_index=slide_index,
            debounce_seconds=debounce,
            snap_grid=snap,
            snap_threshold=threshold,
            skip_pptx=skip_pptx,
            formats=formats_list,
            on_reconciled=on_reconciled,
            on_change_detected=on_change,
            remote_drift=remote_drift,
            receipt_path=receipt,
        )
    except Exception as e:
        rprint(f"[red]Error initializing PPTX watcher:[/red] {e}")
        raise typer.Exit(code=1)

    rprint(f"[cyan]🚀 Starting Diagram Engine V2 Autonomous File Watcher Daemon[/cyan]")
    rprint(f"  • YAML Spec:     [bold]{watcher.spec_path}[/bold]")
    rprint(f"  • Monitoring:    [bold]{watcher.pptx_path}[/bold] (Slide {slide_index})")
    rprint(f"  • Debounce:      [bold]{debounce:.2f}s[/bold] | Snap Grid: [bold]{snap:.2f}\"[/bold] (threshold: {threshold:.2f}\")")
    rprint(f"  • Cyclic Guard:  [bold]{'--skip-pptx ACTIVE' if skip_pptx else 'OFF'}[/bold]")
    rprint(f"  • Companion:     [bold]{', '.join(formats_list)}[/bold]")
    rprint(f"[dim]Waiting for Microsoft PowerPoint save events (Cmd+S)... Press Ctrl+C to stop.[/dim]\n")

    try:
        watcher.watch()
    except KeyboardInterrupt:
        watcher.stop()
        rprint(f"\n[yellow]Watcher stopped by user. Clean shutdown complete.[/yellow]")


@diagram_v2_app.command("consolidate")
def diagram_v2_consolidate(
    workspace: str = typer.Option(".", "--workspace", "-w", help="Workspace root directory to scan for stray visualizations."),
    no_rename: bool = typer.Option(False, "--no-rename", help="Skip renaming files with LATEST_ / OUTDATED_ prefixes."),
    no_archive: bool = typer.Option(False, "--no-archive", help="Keep standalone 1-slide PPTX files in place instead of moving to .archive/strays/."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview theme clustering, LATEST/OUTDATED lineage, and merges without modifying disk."),
) -> None:
    """
    Model 2.1 Stray Visualization Harvester & Theme Consolidator.
    Auto-clusters stray visualizations by theme, prefixes files with LATEST_ / OUTDATED_,
    merges slides into 1 PPTX per domain theme, archives standalone PPTXs, and writes STRAY_BACKLOG.md.
    """
    from src.ppt_engine.diagram_v2 import consolidate_stray_visualizations

    ws_path = Path(workspace).resolve()
    if not ws_path.exists():
        rprint(f"[red]Error:[/red] Workspace path not found: {workspace}")
        raise typer.Exit(code=1)

    rprint(f"[cyan]ℹ Running Model 2.1 Stray Visualization Harvester & Consolidator:[/cyan] [bold]{ws_path}[/bold]")
    try:
        report = consolidate_stray_visualizations(
            workspace=ws_path,
            rename_files=not no_rename,
            archive_pptx=not no_archive,
            dry_run=dry_run,
        )
    except Exception as e:
        rprint(f"[red]Error consolidating stray visualizations:[/red] {e}")
        raise typer.Exit(code=1)

    if not report.clusters:
        rprint("[yellow]No stray visualizations discovered in workspace.[/yellow]")
        return

    table = Table(title="Model 2.1 Domain Theme Clusters & Evolutionary Lineage")
    table.add_column("Domain Theme", style="bold cyan", width=22)
    table.add_column("Lifecycle Status", style="bold", width=14)
    table.add_column("Visualization Stem", style="white", width=32)
    table.add_column("Variant / Scope", style="magenta", width=22)
    table.add_column("Target Theme Bundle", style="green")

    for cluster in report.clusters:
        bundle_rel = (
            cluster.bundle_pptx_path.relative_to(ws_path)
            if cluster.bundle_pptx_path and cluster.bundle_pptx_path.is_relative_to(ws_path)
            else cluster.bundle_pptx_path
        )
        for idx, pod in enumerate(cluster.pods):
            status_badge = "[bold green]LATEST[/bold green]" if pod.status == "LATEST" else "[yellow]OUTDATED[/yellow]"
            table.add_row(
                cluster.theme_slug if idx == 0 else "",
                status_badge,
                pod.base_stem,
                pod.variant_kind,
                f"{bundle_rel} (Slide {idx + 1})",
            )

    console.print(table)
    rprint(
        f"\n[bold]Summary:[/bold] {len(report.clusters)} theme bundle(s), "
        f"{len(report.renamed_files)} file(s) prefixed with LATEST_/OUTDATED_, "
        f"{len(report.archived_pptx_files)} standalone PPTX(s) archived to .archive/strays/."
    )
    if report.backlog_path:
        rprint(f"  • Triage Backlog: [bold]{report.backlog_path}[/bold]")
    if dry_run:
        rprint("[yellow]⚠ Dry-run complete. No files were renamed, merged, or archived.[/yellow]")

