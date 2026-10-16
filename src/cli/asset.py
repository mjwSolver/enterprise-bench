"""
Deterministic Vector Asset Harvester & Diagram Icon Registry CLI Router (`bench asset ...`)
==========================================================================================
Deterministic icon resolver, stencil harvester (Databricks, Cloudera, Snowflake),
icon library browser, and external Draw.io <mxlibrary> package importer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from src.cli.utils import console

asset_app = typer.Typer(
    name="asset",
    help="Deterministic Vector Asset Harvester & Diagram Icon Registry",
    no_args_is_help=True,
)


@asset_app.command("resolve")
def resolve_asset_cli(
    key: str = typer.Argument(..., help="Icon identifier, alias, or path (e.g. 'databricks', 'cloudera:cdsw', 'dbx:unity_catalog')"),
    as_json: bool = typer.Option(False, "--json", help="Output resolution result in JSON format"),
    strict: bool = typer.Option(False, "--strict", help="Exit with code 1 if the asset cannot be resolved"),
) -> None:
    """Deterministically resolve an asset key, vendor alias, or path without web scraping."""
    from src.ppt_engine.asset_harvester import AssetHarvester

    res = AssetHarvester.resolve_asset(key)
    if not res:
        if as_json:
            import json
            print(json.dumps({"resolved": False, "key": key}))
        else:
            rprint(f"[red]✗ Asset could not be resolved:[/red] [bold]{key}[/bold]")
            rprint("[dim]  Query was checked against manifest.json, vendor packs, and local icon roots with zero web scraping.[/dim]")
        if strict:
            raise typer.Exit(code=1)
        return

    if as_json:
        import json
        print(json.dumps({"resolved": True, **res.to_dict()}, indent=2))
        return

    table = Table(title=f"Asset Resolution: {key}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold green")

    table.add_row("Status", "[green]✓ RESOLVED[/green]")
    table.add_row("Query Key", key)
    table.add_row("Canonical ID", res.id)
    table.add_row("Title", res.title)
    table.add_row("Pack", res.pack)
    table.add_row("Category", res.category)
    table.add_row("Format", res.format.upper())
    table.add_row("Brand Weight", res.weight)
    table.add_row("Relative Path", res.file)
    table.add_row("File Size", f"{res.size_bytes:,} bytes")
    table.add_row("Absolute Path", str(res.absolute_path))

    console.print(table)


@asset_app.command("harvest")
def harvest_assets_cli(
    pack: str = typer.Option("all", "--pack", "-p", help="Pack to harvest ('databricks', 'cloudera', or 'all')"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-harvest of stencils even if present locally"),
) -> None:
    """Harvest official vector stencils and vendor packs into local assets catalog."""
    from src.ppt_engine.asset_harvester import AssetHarvester

    pack_lower = pack.lower().strip()
    rprint(f"[cyan]ℹ Harvesting vector assets for pack:[/cyan] [bold]{pack_lower}[/bold]")

    if pack_lower in ("databricks", "dbx", "all"):
        rprint("[dim]  • Ingesting Databricks architecture stencils...[/dim]")
        res_dbx = AssetHarvester.harvest_databricks_stencils(force=force)
        rprint(f"[green]✓ Databricks:[/green] Ingested {res_dbx['total_harvested']} vector stencils into {res_dbx['dest_dir']}")

    if pack_lower in ("cloudera", "all"):
        rprint("[dim]  • Standardizing Cloudera CDP & CDSW marks...[/dim]")
        res_cld = AssetHarvester.harvest_cloudera_pack()
        rprint(f"[green]✓ Cloudera:[/green] Verified {res_cld['total_registered']} modern marks and CDSW product emblems")

    rprint("[green]✓ Asset harvesting completed successfully.[/green]")


@asset_app.command("list")
def list_assets_cli(
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
    table.add_column("Category", style="blue")
    table.add_column("File Path", style="dim")

    for ic in icons:
        table.add_row(
            ic["id"],
            ic.get("title", ""),
            ic.get("pack", "logos"),
            ic.get("format", "svg"),
            ic.get("category", "general"),
            ic.get("file", ""),
        )

    console.print(table)


@asset_app.command("import-library")
def import_asset_library_cli(
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
    except Exception as e:
        rprint(f"[red]Error importing library:[/red] {e}")
        raise typer.Exit(code=1)
