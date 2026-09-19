# Sprint 18 Implementation Runbook: Change Request Subsystem CLI & Closeout Gate

> **Sprint:** 18  
> **Status:** ✅ **COMPLETED** (2026-09-19T11:43:35+07:00 | Commit `7785eeb`)  
> **Target Subsystems:** `src/cli.py`, `src/core/change_request.py`, `src/xlsx_engine/ledger_models.py`, `presets/locales/`  
> **Estimated Execution Time:** ~30 minutes  
> **Operating Guardrail:** [`AGENTS.md`](../../AGENTS.md) (Strict **ZERO INTERMEDIATE UNIT TESTING**).

---

## 1. Objective & Scope

Operationalize five currently disconnected production master templates by wiring existing engine code directly into the unified `bench` CLI:
1. **Four Change Request Deliverables at Once:** Wire `ChangeRequestProcessor` (`src/core/change_request.py`) to a new `bench cr file` command.
2. **Project Closeout Gate:** Wire `update_closeout_checklist` (`src/xlsx_engine/ledger_models.py`) to `bench xlsx update-closeout`.
3. **Bilingual Status Dictionary:** Expand `presets/locales/en.yaml` and `id.yaml` to cover Change Request governance terms, statuses, and Indonesian month name formatters.

---

## 2. Implementation Tasks

### Task 1: Wire `bench cr file` into `src/cli.py`
- **Target File:** [`src/cli.py`](../../src/cli.py)
- **Target Section:** Core Sub-Apps & Command Groups (around lines 50–70 and new command group at bottom of file)

#### 1. Add `cr_app` Typer Sub-Application
```python
cr_app = typer.Typer(name="cr", help="Enterprise Change Request (CR) & Commercial Addendum Workflows", no_args_is_help=True)
# Register alongside existing sub-apps:
app.add_typer(cr_app, name="cr")
```

#### 2. Implement `@cr_app.command("file")`
```python
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
) -> None:
    """
    Intake, model, and generate a complete Enterprise Change Request package:
    1. Change_Request_Form.docx (governance & approval matrix)
    2. Change_Log_Ledger.xlsx (appends registration record)
    3. CR_Scoping_and_Mandays.xlsx (role effort & sizing)
    4. BAST_Change_Request.docx (handover addendum)
    """
    from src.core.change_request import ChangeRequestProcessor, CRSubmission

    processor = ChangeRequestProcessor(project_id=project_id)
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
```

---

### Task 2: Wire `bench xlsx update-closeout` into `src/cli.py`
- **Target File:** [`src/cli.py`](../../src/cli.py)
- **Target Section:** Spreadsheet Commands (`@xlsx_app`)

#### Implementation
```python
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
```

---

### Task 3: Expand Bilingual Catalogs for CR & Governance
- **Target Files:**
  - [`presets/locales/en.yaml`](../../presets/locales/en.yaml)
  - [`presets/locales/id.yaml`](../../presets/locales/id.yaml)

#### Additions to `en.yaml`
```yaml
governance:
  cr:
    title: "Project Change Request"
    categories:
      scope: "Scope Change"
      schedule: "Schedule Adjustment"
      requirement: "Requirement Enhancement"
      technical: "Technical Refactoring"
      bug_fix: "Defect Remediation"
    statuses:
      submitted: "SUBMITTED"
      under_review: "UNDER REVIEW"
      approved: "APPROVED"
      rejected: "REJECTED"
      deferred: "DEFERRED"
  closeout:
    checklist_title: "Project Closeout & Handover Checklist"
    sections:
      deliverables: "1. Core Deliverables"
      scope_verification: "2. Scope Verification"
      operational_handover: "3. Operational Handover"
```

#### Additions to `id.yaml`
```yaml
governance:
  cr:
    title: "Permohonan Perubahan Proyek (CR)"
    categories:
      scope: "Perubahan Ruang Lingkup"
      schedule: "Penyesuaian Jadwal"
      requirement: "Penyempurnaan Kebutuhan"
      technical: "Refaktorisasi Teknis"
      bug_fix: "Perbaikan Cacat Sistem"
    statuses:
      submitted: "DIAJUKAN"
      under_review: "SEDANG DITELAAH"
      approved: "DISETUJUI"
      rejected: "DITOLAK"
      deferred: "DITUNDA"
  closeout:
    checklist_title: "Daftar Periksa Penutupan & Serah Terima Proyek"
    sections:
      deliverables: "1. Hasil Akhir (Deliverables)"
      scope_verification: "2. Verifikasi Ruang Lingkup"
      operational_handover: "3. Serah Terima Operasional"
```

---

## 3. Verification Gate (No Pytest)

Validate CLI command registrations, help screens, and end-to-end dry generation:

```bash
# 1. Syntax compilation
uv run python -m py_compile src/cli.py src/core/change_request.py src/xlsx_engine/ledger_models.py

# 2. Verify CR CLI help screen
uv run bench cr --help
uv run bench cr file --help

# 3. Verify Closeout CLI help screen
uv run bench xlsx update-closeout --help

# 4. End-to-end file generation test
uv run bench cr file \
  --title "Automated GL Journal Posting Pipeline" \
  --requester "Budi Santoso, Finance Director" \
  --description "Add automated validation and ingestion for SAP GL Journal entries." \
  --scope "Snowflake Staging Lakehouse & dbt Core transformations" \
  --days 14 \
  --output-dir "output/test_cr_sprint18"

# 5. Verify generated artifacts
ls -lh output/test_cr_sprint18/
```

---

## 4. Definition of Done Checklist

- [x] `cr_app` sub-application and `file` command registered in `src/cli.py`.
- [x] `update-closeout` command registered under `xlsx_app` in `src/cli.py`.
- [x] `presets/locales/en.yaml` and `id.yaml` updated with governance CR entries.
- [x] Smoke run `bench cr file` creates all 4 deliverable documents without errors.
- [x] Closeout checklist update runs cleanly against template.
