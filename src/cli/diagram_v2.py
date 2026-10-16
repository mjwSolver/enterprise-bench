"""
Diagram Engine V2 Subsystem CLI Router (`bench diagram v2 ...`)
==============================================================
Declarative YAML topology compiler (Draw.io XML, SVG, PNG, native PPTX),
spec validation, template emitter, Tier 1 collision linter, and
Tier 2 adversarial visual QA.
"""

from __future__ import annotations

import subprocess
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
    open_deck: bool = typer.Option(False, "--open", help="Proactively launch generated PPTX slide deck on desktop"),
) -> None:
    """Compile a declarative YAML specification deterministically into Draw.io XML, SVG, PNG, and native PowerPoint slides."""
    from src.ppt_engine.diagram_v2 import compile_diagram

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec}")
        raise typer.Exit(code=1)

    try:
        formats_list = [f.strip() for f in format.split(",") if f.strip()]
        result = compile_diagram(spec_path_or_dict=spec_p, output_dir_or_file=output, formats=formats_list, open_deck=open_deck)
        rprint(f"[green]✓ Successfully compiled Diagram V2 topology:[/green] [bold]{result.spec.name}[/bold]")
        if result.drawio_path:
            rprint(f"  • Draw.io XML:  [bold]{result.drawio_path}[/bold]")
        if result.svg_path:
            rprint(f"  • Vector SVG:   [bold]{result.svg_path}[/bold]")
        if result.png_path:
            rprint(f"  • High-DPI PNG: [bold]{result.png_path}[/bold]")
        if result.pptx_path:
            rprint(f"  • Native PPTX:  [bold]{result.pptx_path}[/bold]")
    except Exception as e:
        rprint(f"[red]Error compiling diagram specification:[/red] {e}")
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
    name: str = typer.Option("aws_lambda", "--name", "-n", help="Sample template name: 'aws_lambda', 'cdsw', or 'interwoven'"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Destination path to write sample YAML"),
) -> None:
    """Emit a production-grade sample declarative diagram YAML specification."""
    sample_dir = ROOT_DIR / "src" / "ppt_engine" / "diagram_v2" / "samples"
    file_map = {
        "aws_lambda": sample_dir / "proposed_aws_lambda.yaml",
        "cdsw": sample_dir / "cdsw_legacy_batch.yaml",
        "interwoven": sample_dir / "interwoven_migration.yaml",
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


@diagram_v2_app.command("audit")
def audit_diagram_v2_cli(
    spec: str = typer.Argument(..., help="Path to declarative diagram YAML specification"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if any critical issues or warnings are found"),
) -> None:
    """Run Tier 1 geometric collision and clearance linting on a declarative diagram specification."""
    from src.ppt_engine.diagram_v2 import load_diagram_spec, Tier1GeometricLinter

    spec_p = Path(spec)
    if not spec_p.exists():
        rprint(f"[red]Error:[/red] Diagram specification file not found: {spec}")
        raise typer.Exit(code=1)

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
    out_dir = Path(output) if output else Path("TEMP/visual_qa") / diagram_spec.id

    if tier_mode == "1":
        linter = Tier1GeometricLinter(diagram_spec)
        issues = linter.lint()
        table = Table(title=f"Tier 1 Geometric Collision Audit: {diagram_spec.name}")
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Category", style="cyan", width=28)
        table.add_column("Element ID", style="magenta", width=22)
        table.add_column("Description", style="white")
        table.add_column("Suggested Fix", style="dim green")
        for iss in issues:
            sev_styled = "[red]CRITICAL[/red]" if iss.severity == "CRITICAL" else "[yellow]WARNING[/yellow]"
            table.add_row(sev_styled, iss.category, iss.element_id, iss.description, iss.suggested_fix)
        console.print(table)
        crit = sum(1 for i in issues if i.severity == "CRITICAL")
        if crit > 0 or (strict and len(issues) > 0):
            raise typer.Exit(code=1)
        return

    rprint(f"[cyan]ℹ Running Tier 1 & Tier 2 Adversarial Visual QA Verification on:[/cyan] [bold]{diagram_spec.name}[/bold]")
    verifier = Tier2VisualVerifier(diagram_spec)
    result = verifier.verify(output_dir=out_dir)

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
) -> None:
    """
    Reconcile PowerPoint DrawingML slide mutations against declarative YAML AST (Topic 11).
    Diffs live shapes against specification, pruning deleted nodes and orphan flows,
    updating mutated text, and triggering automatic 4-way re-compilation.
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
        )
    except Exception as e:
        rprint(f"[red]Reconciliation failed:[/red] {e}")
        raise typer.Exit(code=1)

    if not res.has_changes:
        rprint(f"\n[green]✓ Clean Parity:[/green] PowerPoint slide and YAML specification are [bold]100% in sync[/bold]. Zero mutations or prunings detected.")
        return

    table = Table(title=f"Topic 11 Reconciliation Diff: {res.spec_path.name} ⟷ {res.pptx_path.name}")
    table.add_column("Category", style="cyan", width=14)
    table.add_column("Element ID", style="magenta", width=24)
    table.add_column("Action", style="bold", width=12)
    table.add_column("Property", style="dim white", width=14)
    table.add_column("Previous Value (YAML)", style="white")
    table.add_column("Reconciled Value (PPTX)", style="bold green")

    for c in res.changes:
        if c.change_type.startswith("pruned_"):
            action_styled = "[red]PRUNED[/red]"
            cat = c.element_type.title()
            table.add_row(cat, c.element_id, action_styled, "existence", str(c.old_value or ""), "[dim]REMOVED[/dim]")
        elif c.change_type == "mutated_text":
            action_styled = "[green]MUTATED[/green]"
            cat = c.element_type.title()
            table.add_row(cat, c.element_id, action_styled, c.field_name or "text", str(c.old_value or "[dim]None[/dim]"), str(c.new_value or "[dim]None[/dim]"))

    console.print(table)
    rprint(f"\n[bold]Reconciliation Summary:[/bold] {len(res.pruned_nodes)} node(s) pruned, {len(res.pruned_flows)} flow(s) pruned, {len(res.mutated_texts)} text field(s) updated.")

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
