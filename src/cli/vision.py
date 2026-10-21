"""
Vision & OCR CLI Router (`bench vision ...`)
===========================================
Extract text, code, and configurations from screenshots, images, and DOCX/PPTX media
using Apple Vision (Neural Engine) and Tesseract OCR.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from src.cli.utils import console
from src.vision.ocr_engine import VisionOCREngine

vision_app = typer.Typer(
    name="vision",
    help="Dual-Engine OCR & Document Screenshot Code Extractor",
    no_args_is_help=True,
)


@vision_app.command("ocr")
def ocr_command(
    target: Path = typer.Argument(
        ...,
        help="Path to image file, folder of images, or DOCX/PPTX document",
        exists=True,
    ),
    engine: str = typer.Option(
        "auto",
        "--engine",
        "-e",
        help="OCR engine: 'auto' (Apple Vision on macOS, else Tesseract), 'apple-vision', or 'tesseract'",
    ),
    code_only: bool = typer.Option(
        True,
        "--code-only/--all",
        help="Filter to records classified as code/SQL/config",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save structured records to JSON or Markdown file",
    ),
) -> None:
    """Scan images or document media to extract code, SQL queries, and configuration."""
    rprint(f"[bold blue]🔍 Scanning target:[/bold blue] {target}")
    rprint(f"[dim]  Engine: {engine} | Filter: {'Code/SQL Only' if code_only else 'All Text'}[/dim]")

    records = VisionOCREngine.scan_path(target, engine_mode=engine, filter_code_only=code_only)

    if not records:
        rprint("[yellow]⚠ No matching records extracted.[/yellow]")
        return

    rprint(f"[green]✓ Extracted {len(records)} record(s)[/green]\n")

    # Render summary table
    table = Table(title="Extracted Text & Code Snippets", show_lines=True)
    table.add_column("Source", style="cyan", no_wrap=True)
    table.add_column("Engine", style="magenta")
    table.add_column("Code?", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Preview Snippet", style="dim", max_width=60)

    for rec in records[:15]:
        preview = rec.extracted_text.replace("\n", " ")[:55]
        if len(rec.extracted_text) > 55:
            preview += "..."
        table.add_row(
            rec.source_file,
            rec.engine,
            "YES" if rec.is_code else "NO",
            str(rec.code_score),
            preview,
        )

    console.print(table)
    if len(records) > 15:
        rprint(f"[dim]... and {len(records) - 15} more records.[/dim]")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() == ".json":
            with open(output, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in records], f, indent=2)
            rprint(f"[bold green]✓ Saved JSON report to:[/bold green] {output}")
        elif output.suffix.lower() == ".md":
            with open(output, "w", encoding="utf-8") as f:
                f.write(f"# OCR Extraction Report\n\nTarget: `{target}`\nTotal Records: {len(records)}\n\n")
                for i, r in enumerate(records, 1):
                    f.write(f"### {i}. {r.source_file} (Engine: {r.engine}, Score: {r.code_score})\n")
                    f.write(f"```python\n{r.extracted_text}\n```\n\n")
            rprint(f"[bold green]✓ Saved Markdown report to:[/bold green] {output}")
