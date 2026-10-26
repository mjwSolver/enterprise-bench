"""
Deterministic Document Compliance Engine CLI Router (`bench doc ...`)
======================================================================
Template stamping, spec compilation, PII sanitization, OpenXML purging,
aspect ratio linting, and automated document QA.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

from src.core.config import OUTPUT_DIR
from src.core.sanitizer import sanitize_docx
from src.cli.utils import console, open_desktop_review, display_template_catalog

doc_app = typer.Typer(
    name="doc",
    help="Deterministic Document Compliance Engine",
    no_args_is_help=True,
)


@doc_app.command("stamp")
def stamp_doc(
    template: str = typer.Option(..., "--template", "-t", help="Template name or relative path in templates/"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Path to JSON data payload"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .docx destination path"),
) -> None:
    """Stamp a deterministic Word document template with JSON data."""
    # Lazy import to ensure docxtpl is only loaded when stamping
    from src.docx_engine.template_stamper import TemplateStamper

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
    # Lazy import to ensure docxtpl is only loaded when linting
    from src.docx_engine.document_linter import lint_document

    report = lint_document(file)
    if report.passed:
        rprint(f"[green]✓ Document Passed QA Inspection with 0 critical errors:[/green] {file}")
    else:
        rprint(f"[red]✗ Lint Failed ({report.total_issues} issues found):[/red] {file}")
        for iss in report.issues:
            rprint(f"  [[bold]{iss.severity}[/bold]] {iss.location}: {iss.message}")
        raise typer.Exit(code=1)


@doc_app.command("list-templates")
def list_templates(
    phase: Optional[str] = typer.Option(None, "--phase", "-p", help="Filter templates by phase (e.g. 07, initiating)"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Filter templates by filename substring (e.g. bast)"),
) -> None:
    """List available document and enterprise templates across project phases."""
    display_template_catalog(phase=phase, query=query)


@doc_app.command("view")
def view_doc(
    file: str = typer.Argument(..., help="Path to Word .docx document file"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: 'markdown' or 'json'"),
    full: bool = typer.Option(False, "--full", help="Show paragraph content preview"),
) -> None:
    """Inspect document structure, heading hierarchy, tables, and token metrics (L1 Read)."""
    import json
    from src.docx_engine.document_inspector import DocumentInspector

    p_in = Path(file)
    if not p_in.exists():
        rprint(f"[red]Error:[/red] Word file not found: {file}")
        raise typer.Exit(code=1)

    try:
        inspector = DocumentInspector(p_in)
        info = inspector.inspect()
    except Exception as e:
        rprint(f"[red]Error inspecting document:[/red] {e}")
        raise typer.Exit(code=1)

    if format == "json":
        print(json.dumps(info.to_dict(), indent=2))
    else:
        print(info.to_markdown(full=full))

