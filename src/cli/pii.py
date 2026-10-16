"""
Universal PII Sanitization & Slug Linter CLI Router (`bench pii ...`)
=====================================================================
Scan generated deliverables (.docx, .pptx, .xlsx) for forbidden legacy
client/vendor entity leaks and un-slugified terms.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table

from src.cli.utils import console

pii_app = typer.Typer(
    name="pii",
    help="Universal PII Sanitization & Slug Linter",
    no_args_is_help=True,
)


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
