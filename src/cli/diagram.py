"""
Multi-Page Draw.io & Mermaid Diagram Engine CLI Router (`bench diagram ...`)
=============================================================================
Manage Draw.io pages, render Mermaid syntax, export high-DPI plates,
compile native PowerPoint DrawingML slides, and browse vector icon registries.
Mounts Diagram V2 Subsystem under `bench diagram v2 ...`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from src.cli.utils import console, open_desktop_review
from src.cli.diagram_v2 import diagram_v2_app

diagram_app = typer.Typer(
    name="diagram",
    help="Multi-Page Draw.io & Mermaid Diagram Engine",
    no_args_is_help=True,
)

diagram_app.add_typer(diagram_v2_app, name="v2")


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


@diagram_app.command("export-pptx")
def export_diagram_pptx_cli(
    output: str = typer.Option("output/presentations/architecture_evolution_cdsw_to_lambda.pptx", "--output", "-o", help="Destination path for native .pptx deck"),
    open_deck: bool = typer.Option(False, "--open", help="Launch presentation in Microsoft PowerPoint on macOS"),
) -> None:
    """Compile architecture evolution diagrams into 100% native, fully editable PowerPoint DrawingML slides."""
    from src.ppt_engine.pptx_diagram_compiler import PowerPointDiagramCompiler

    compiler = PowerPointDiagramCompiler()
    out_p = compiler.compile_presentation(output)
    rprint(f"[green]✓ Native PowerPoint presentation generated:[/green] [bold]{out_p}[/bold]")
    if open_deck:
        open_desktop_review(out_p, "Microsoft PowerPoint")


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
