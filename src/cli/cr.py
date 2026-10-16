"""
Enterprise Change Request (CR) CLI Router (`bench cr ...`)
==========================================================
Commercial addendum workflows, mandays effort calculation,
governance approval package generation, and BAST amendment stamping.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich import print as rprint

from src.cli.utils import console

cr_app = typer.Typer(
    name="cr",
    help="Enterprise Change Request (CR) & Commercial Addendum Workflows",
    no_args_is_help=True,
)


@cr_app.command("file")
def file_change_request_cli(
    title: str = typer.Option(..., "--title", "-t", help="Title of the Change Request"),
    requester: str = typer.Option(..., "--requester", "-r", help="Name and title of the CR requester"),
    description: str = typer.Option(..., "--description", "-d", help="Detailed requirement description"),
    scope_impact: str = typer.Option(..., "--scope", "-s", help="Impacted technical components / architecture"),
    category: str = typer.Option("Scope", "--category", "-c", help="Category: Scope, Schedule, Requirement, Technical, Bug Fix"),
    priority: str = typer.Option("High", "--priority", "-p", help="Priority: Low, Medium, High, Critical"),
    department: str = typer.Option("Consolidated Accounting", "--dept", help="Requester business unit"),
    schedule_days: int = typer.Option(15, "--days", help="Estimated schedule calendar days required"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Target output folder for CR package"),
    project_id: str = typer.Option("TTI_Snowflake_Analytics", "--project", help="Project identifier"),
    client: Optional[str] = typer.Option(None, "--client", help="Client organization slug/name"),
) -> None:
    """
    Intake, model, and generate a complete Enterprise Change Request package:
    1. Change_Request_Form.docx (governance & approval matrix)
    2. Change_Log_Ledger.xlsx (appends registration record)
    3. CR_Scoping_and_Mandays.xlsx (role effort & sizing)
    4. BAST_Change_Request.docx (handover addendum)
    """
    from src.core.change_request import ChangeRequestProcessor, CRSubmission
    from src.core.slug_registry import EngagementContext

    ctx = EngagementContext.from_client_name(client) if client else EngagementContext.default_ngl()
    processor = ChangeRequestProcessor(project_id=project_id, context=ctx)
    submission = CRSubmission(
        title=title,
        requester=requester,
        description=description,
        scope_impact=scope_impact,
        category=category,
        priority=priority,
        department=department,
        schedule_days=schedule_days,
    )

    rprint(f"[cyan]ℹ Processing Change Request:[/cyan] [bold]{title}[/bold]")
    res = processor.file_change_request(submission=submission, output_dir=output_dir)

    rprint(f"[green]✓ Change Request filed successfully:[/green] [bold]CR-{res.cr_id}[/bold]")
    rprint(f"  CR Form:          {res.cr_form_path}")
    rprint(f"  Mandays Scoping:  {res.mandays_sheet_path}")
    rprint(f"  BAST CR Draft:    {res.bast_draft_path}")
    rprint(f"  Total Mandays:    {res.total_mandays} days")
