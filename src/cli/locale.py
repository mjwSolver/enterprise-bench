"""
Bilingual & Hybrid Localization Engine CLI Router (`bench locale ...`)
======================================================================
Inspect locale catalogs (en, id), retrieve localized UI/governance strings,
and execute hybrid translations preserving canonical cloud & tech terms.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from src.cli.utils import console

locale_app = typer.Typer(
    name="locale",
    help="Bilingual & Hybrid Localization Engine",
    no_args_is_help=True,
)


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
