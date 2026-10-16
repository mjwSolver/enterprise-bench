"""
Spreadsheet & Calculator Engine CLI Router (`bench xlsx ...`)
=============================================================
Calculations, S-Curve progression charts, RAID register appends,
cloud sizing estimations, and closeout checklist synchronization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

from src.cli.utils import console

xlsx_app = typer.Typer(
    name="xlsx",
    help="Spreadsheet & Calculator Engine",
    no_args_is_help=True,
)


@xlsx_app.command("calculate")
def calculate_xlsx(
    template: str = typer.Option(..., "--template", "-t", help="Template name or path to .xlsx file"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Path to JSON data payload for calculation/population"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Inject calculations or data updates into an Excel spreadsheet template."""
    from src.xlsx_engine.calculator_stamper import calculate_spreadsheet

    payload = {}
    if data:
        data_path = Path(data)
        if not data_path.exists():
            rprint(f"[red]Error:[/red] Data file not found: {data}")
            raise typer.Exit(code=1)
        with open(data_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

    try:
        out_p = calculate_spreadsheet(template=template, data=payload, output_path=output)
        rprint(f"[green]✓ Spreadsheet calculated and saved:[/green] [bold]{out_p}[/bold]")
    except Exception as e:
        rprint(f"[red]Error calculating spreadsheet:[/red] {e}")
        raise typer.Exit(code=1)


@xlsx_app.command("s-curve")
def generate_scurve_cli(
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Base .xlsx template name or path to inject into (optional)"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Path to JSON data payload defining periods, planned, actual, milestones"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
    weeks: int = typer.Option(12, "--weeks", "-w", help="Number of project weeks/periods to generate if data not provided"),
    distribution: str = typer.Option("sigmoid", "--distribution", help="Mathematical distribution: sigmoid, polynomial, cubic, linear"),
    current_week: Optional[int] = typer.Option(None, "--current-week", help="Current week index (1-based) for actual progress cut-off"),
    lag: float = typer.Option(0.0, "--lag", help="Simulated actual lag factor relative to plan (e.g. -0.05 for 5% behind)"),
    sheet_name: str = typer.Option("S-Curve", "--sheet-name", "-s", help="Target worksheet name"),
    title: str = typer.Option("Project S-Curve: Planned vs Actual Cumulative Progress", "--title", help="Chart title"),
    project: str = typer.Option("Enterprise Modernization Project", "--project", "-p", help="Project name for header"),
) -> None:
    """Generate an S-curve cumulative progress curve and inject an openpyxl LineChart."""
    from src.xlsx_engine.s_curve_generator import SCurveGenerator

    payload: dict = {}
    if data:
        data_path = Path(data)
        if not data_path.exists():
            rprint(f"[red]Error:[/red] Data file not found: {data}")
            raise typer.Exit(code=1)
        with open(data_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

    periods = payload.get("periods")
    planned_pct = payload.get("planned_pct")
    actual_pct = payload.get("actual_pct")
    milestones = payload.get("milestones")
    dist = payload.get("distribution", distribution)
    proj_name = payload.get("project_name", project)
    s_name = payload.get("sheet_name", sheet_name)
    c_title = payload.get("chart_title", title)

    c_period_idx = None
    if current_week is not None:
        c_period_idx = current_week - 1
    elif "current_week" in payload:
        c_period_idx = int(payload["current_week"]) - 1
    elif "current_period_idx" in payload:
        c_period_idx = int(payload["current_period_idx"])

    lag_factor = payload.get("lag_factor", lag)

    try:
        generator = SCurveGenerator(template=template, project_name=proj_name)
        out_p = generator.generate(
            output_path=output,
            periods=periods,
            num_periods=weeks,
            planned_pct=planned_pct,
            actual_pct=actual_pct,
            distribution=dist,
            milestones=milestones,
            current_period_idx=c_period_idx,
            lag_factor=lag_factor,
            sheet_name=s_name,
            chart_title=c_title,
        )
        rprint(f"[green]✓ Project S-curve successfully generated:[/green] [bold]{out_p}[/bold]")
    except Exception as e:
        rprint(f"[red]Error generating S-curve:[/red] {e}")
        raise typer.Exit(code=1)


@xlsx_app.command("append-risk")
def append_risk_cli(
    title: str = typer.Option(..., "--title", "-t", help="Title of the project risk"),
    desc: str = typer.Option(..., "--desc", "-d", help="Description of the risk event and root cause"),
    impact: str = typer.Option(..., "--impact", "-i", help="Operational and schedule impact statement"),
    category: str = typer.Option("Scope", "--category", "-c", help="Category: Scope, Data, Resource, Schedule, Quality"),
    owner: str = typer.Option("Project Manager", "--owner", help="Accountable mitigation owner"),
    prob: str = typer.Option("Medium", "--prob", help="Probability level: Low, Medium, High"),
    impact_level: str = typer.Option("Medium", "--impact-level", help="Impact level: Low, Medium, High"),
    status: str = typer.Option("Open", "--status", help="Status: Open, Mitigated, Closed"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append a risk entry into the project Risk Register spreadsheet."""
    from src.xlsx_engine.ledger_models import RiskEntry, append_risk_to_register

    risk = RiskEntry(
        title=title,
        description=desc,
        impact_statement=impact,
        category=category,
        owner=owner,
        probability=prob,
        impact_level=impact_level,
        status=status,
    )
    out_p = append_risk_to_register(risk, output_path=output)
    rprint(f"[green]✓ Risk entry appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("append-issue")
def append_issue_cli(
    title: str = typer.Option(..., "--title", "-t", help="Title of the blocker/issue"),
    desc: str = typer.Option(..., "--desc", "-d", help="Description of the roadblock"),
    category: str = typer.Option("Technical", "--category", "-c", help="Category: Resource, Requirement, Technical, Environment"),
    owner: str = typer.Option("Lead Data Engineer", "--owner", help="PIC accountable for resolution"),
    reported_by: str = typer.Option("Project Lead", "--reported-by", help="Originator who flagged the issue"),
    area: str = typer.Option("Timeline", "--area", help="Impacted area: Timeline, Scope, Budget, Resource, Quality"),
    severity: str = typer.Option("Medium", "--severity", "-s", help="Severity: Low, Medium, High, Critical"),
    status: str = typer.Option("Open", "--status", help="Status: Open, In Progress, Closed"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append an issue entry into the project Issue Log spreadsheet."""
    from src.xlsx_engine.ledger_models import IssueEntry, append_issue_to_log

    issue = IssueEntry(
        title=title,
        description=desc,
        category=category,
        owner=owner,
        reported_by=reported_by,
        impacted_area=area,
        severity=severity,
        status=status,
    )
    out_p = append_issue_to_log(issue, output_path=output)
    rprint(f"[green]✓ Issue entry appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("append-defect")
def append_defect_cli(
    summary: str = typer.Option(..., "--summary", "-s", help="Summary title of the defect"),
    desc: str = typer.Option(..., "--desc", "-d", help="Detailed description of the bug"),
    module: str = typer.Option("A. Sales", "--module", "-m", help="Module or component"),
    activity: str = typer.Option("B. SIT", "--activity", "-a", help="Testing phase: A. Unit Testing, B. SIT, C. UAT"),
    severity: str = typer.Option("2. Major", "--severity", help="Severity: 1. Critical, 2. Major, 3. Medium, 4. Low"),
    priority: str = typer.Option("2. Medium", "--priority", help="Priority: 1. High, 2. Medium, 3. Low"),
    status: str = typer.Option("Open", "--status", help="Status: Open, Assigned, In Progress, Resolved, Closed"),
    pic: str = typer.Option("Data Dev", "--pic", help="Person in charge of fixing"),
    test_case: str = typer.Option("TC-01", "--test-case", help="Test Case ID reference"),
    expected: str = typer.Option("", "--expected", help="Expected correct result"),
    actual: str = typer.Option("", "--actual", help="Observed actual defect result"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append a defect row into the 3.6_Defect_List_Template.xlsx tracker."""
    from src.xlsx_engine.ledger_models import DefectEntry, append_defect_to_list

    defect = DefectEntry(
        summary=summary,
        description=desc,
        module=module,
        activity=activity,
        severity=severity,
        priority=priority,
        status=status,
        pic=pic,
        test_case=test_case,
        expected_result=expected,
        actual_result=actual,
    )
    out_p = append_defect_to_list(defect, output_path=output)
    rprint(f"[green]✓ Defect entry appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("append-stakeholder")
def append_stakeholder_cli(
    name: str = typer.Option(..., "--name", "-n", help="Full name and title of stakeholder"),
    email: str = typer.Option(..., "--email", "-e", help="Email address"),
    company: str = typer.Option("Client Corp", "--company", "-c", help="Organization / Employer"),
    phone: str = typer.Option("+62-811-0000-000", "--phone", help="Contact phone number"),
    department: str = typer.Option("Finance", "--dept", help="Department or business unit"),
    role: str = typer.Option("Project Manager", "--role", "-r", help="Project governance role"),
    active: str = typer.Option("Y", "--active", help="Active flag: Y / N"),
    notes: Optional[str] = typer.Option("", "--notes", help="Context or additional responsibilities"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Safely append a stakeholder entry into 1.3_Stakeholders_Register_Template.xlsx."""
    from src.xlsx_engine.ledger_models import StakeholderEntry, append_stakeholder_to_register

    entry = StakeholderEntry(
        name=name,
        email=email,
        company=company,
        phone=phone,
        department=department,
        project_role=role,
        is_active=active,
        notes=notes or "",
    )
    out_p = append_stakeholder_to_register(entry, output_path=output)
    rprint(f"[green]✓ Stakeholder appended successfully:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("cloud-sizing")
def cloud_sizing_cli(
    client: str = typer.Option("Enterprise Client", "--client", "-c", help="Client name"),
    storage: float = typer.Option(1.0, "--storage", help="Storage in TB"),
    cortex: float = typer.Option(3660.0, "--cortex", help="Cortex AI annual USD"),
    training: float = typer.Option(1500.0, "--training", help="Training cost USD"),
    fx: float = typer.Option(16500.0, "--fx", help="USD to IDR exchange rate"),
    config: Optional[str] = typer.Option(None, "--config", help="Optional JSON or YAML sizing spec"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Calculate Snowflake infrastructure sizing and stamp Cloud_Sizing_Calculator_Template.xlsx."""
    import yaml
    from src.xlsx_engine.cloud_sizing import CloudSizingConfig, calculate_cloud_sizing

    if config and Path(config).exists():
        p = Path(config)
        raw = p.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) if p.suffix.lower() in (".yaml", ".yml") else json.loads(raw)
        cfg = CloudSizingConfig(**data)
    else:
        cfg = CloudSizingConfig(
            client_name=client,
            storage_tb=storage,
            cortex_ai_annual_usd=cortex,
            training_seats_usd=training,
            exchange_rate_idr=fx,
        )

    res = calculate_cloud_sizing(cfg, output_path=output)
    rprint(f"[cyan]{res.summary_table()}[/cyan]")
    rprint(f"[green]✓ Cloud sizing stamped successfully:[/green] [bold]{res.output_path}[/bold]")


@xlsx_app.command("sync-s-curve")
def sync_s_curve_cli(
    timeline: Optional[str] = typer.Option(None, "--timeline", "-t", help="Path to 4.2_Weekly_Progress_Timeline_Update_Template.xlsx"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
    chunk_days: int = typer.Option(7, "--chunk-days", help="Days per weekly progress interval"),
) -> None:
    """Extract daily progression from timeline workbook and inject executive S-curve line chart tab."""
    from src.xlsx_engine.timeline_aggregator import TimelineAggregator

    agg = TimelineAggregator(timeline_path=timeline)
    analysis = agg.extract_s_curve(chunk_days=chunk_days)
    out_p = agg.synchronize_and_chart(output_path=output, chunk_days=chunk_days)

    rprint(f"[bold cyan]S-Curve Extracted from Timeline:[/bold cyan]")
    rprint(f"  • Current Period: [bold]{analysis.current_period}[/bold]")
    rprint(f"  • Planned Progress: [bold]{(analysis.current_planned_pct or 0.0) * 100:.1f}%[/bold]")
    rprint(f"  • Actual Progress: [bold]{(analysis.current_actual_pct or 0.0) * 100:.1f}%[/bold]")
    rprint(f"  • Variance: [bold]{analysis.current_variance_pct or 0.0:+.2f}%[/bold]")
    rprint(f"  • Overall Health: [bold]{analysis.overall_health}[/bold] (SPI: {analysis.spi})")
    rprint(f"[green]✓ S-Curve Analysis tab with LineChart injected:[/green] [bold]{out_p}[/bold]")


@xlsx_app.command("update-closeout")
def update_closeout_cli(
    item: str = typer.Option(..., "--item", "-i", help="Deliverable or checklist item name (substring match)"),
    status: str = typer.Option("Delivered", "--status", "-s", help="Gate status: Delivered, Done, Yes, Partial, TBD"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Path to 5.2_Project_Closeout_Checklist_Template.xlsx"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output .xlsx destination path"),
) -> None:
    """Update deliverable sign-off statuses in 5.2_Project_Closeout_Checklist_Template.xlsx."""
    from src.xlsx_engine.ledger_models import update_closeout_checklist

    updates = [{"item_name": item, "status": status}]
    try:
        out_p = update_closeout_checklist(updates=updates, template_path=template, output_path=output)
        rprint(f"[green]✓ Closeout checklist updated:[/green] [bold]{out_p}[/bold]")
        rprint(f"  Item: '{item}' -> Status: [bold cyan]{status}[/bold cyan]")
    except Exception as e:
        rprint(f"[red]Error updating closeout checklist:[/red] {e}")
        raise typer.Exit(code=1)
