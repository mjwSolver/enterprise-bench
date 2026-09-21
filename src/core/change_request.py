"""
Change Request (CR) Processing Subsystem
=========================================
Automates the intake, impact analysis modeling, document stamping, and ledger
registration for enterprise Change Requests (CRs).
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import docx
import openpyxl
from pydantic import BaseModel, Field

from src.core.config import CLEAN_DIR, validate_clean_path
from src.core.slug_registry import EngagementContext, DEFAULT_CLIENT_SHORT_NAME
from src.core.workspace import WorkspaceRouter


def _substitute_docx(doc: Any, context: EngagementContext) -> None:
    """Substitutes legacy slugs and placeholders across paragraphs and table cells."""
    for p in doc.paragraphs:
        if p.text:
            new_text = context.substitute(p.text)
            if new_text != p.text:
                p.text = new_text
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text:
                        new_text = context.substitute(p.text)
                        if new_text != p.text:
                            p.text = new_text


def _substitute_xlsx(wb: Any, context: EngagementContext) -> None:
    """Substitutes legacy slugs across all sheets and cells in an openpyxl workbook."""
    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    new_val = context.substitute(cell.value)
                    if new_val != cell.value:
                        cell.value = new_val


class CRSubmission(BaseModel):
    """Payload representing an incoming enterprise Change Request."""
    cr_id: Optional[str] = Field(None, description="Identifier (e.g. '7' or 'CR-07'). Auto-increments if omitted.")
    title: str = Field(..., description="Concise title of the change request")
    category: str = Field("Scope", description="Scope, Schedule, Requirement, Design, Technical, Bug Fix")
    priority: str = Field("High", description="Low, Medium, High, Critical")
    requester: str = Field(..., description="Name and title of requester")
    department: str = Field("Consolidated Accounting", description="Department / Role")
    submission_date: str = Field(default_factory=lambda: datetime.now().strftime("%d %B %Y"))
    description: str = Field(..., description="Detailed functional and business requirement")
    reason: str = Field("Business user operational requirement", description="Justification / Business driver")
    scope_impact: str = Field(..., description="Technical & architectural components affected")
    schedule_days: int = Field(15, description="Estimated calendar days required")
    buffer_days: int = Field(2, description="Buffer days for regression testing")
    cost_estimate: str = Field("To be quoted via commercial addendum", description="Cost / Billing estimate")
    mandays_breakdown: Dict[str, int] = Field(
        default_factory=lambda: {
            "analysis_pm": 4,
            "development": 10,
            "testing": 6,
            "deployment": 2,
        },
        description="Effort breakdown by role/phase",
    )
    risk_impact: str = Field("Low - isolated feature addition, minimal regression risk", description="Risk assessment")
    quality_impact: str = Field("Positive - enhances data accuracy and user reporting agility", description="Quality impact")


class CRProcessingResult(BaseModel):
    """Outcome of processing a Change Request submission."""
    cr_id: str
    project_id: str
    cr_form_path: str
    ledger_updated: bool
    mandays_sheet_path: Optional[str] = None
    bast_draft_path: Optional[str] = None
    total_mandays: int
    summary: str


class ChangeRequestProcessor:
    """Orchestrates document generation, ledger logging, and scoping for Change Requests."""

    def __init__(
        self,
        project_id: str = "TTI_Snowflake_Analytics",
        context: Optional[EngagementContext] = None,
    ):
        self.context = context or EngagementContext.default_ngl()
        self.project_id = project_id
        self.project = WorkspaceRouter.get_project(project_id)

    def _get_next_cr_id(self) -> str:
        """Inspect the current ledger to determine the next sequential CR ID."""
        ledger_path = self.project.resolve_clean_file("4.4_Change_Log_Ledger_Template.xlsx")
        if not ledger_path or not ledger_path.exists():
            return "7"

        wb = openpyxl.load_workbook(str(ledger_path), data_only=True)
        ws = wb["Change Log"] if "Change Log" in wb.sheetnames else wb.active
        max_id = 0
        for row in list(ws.iter_rows(values_only=True))[2:]:
            first_cell = row[0]
            if first_cell is not None:
                try:
                    val = int(str(first_cell).strip().replace("CR-", "").replace("CR", ""))
                    if val > max_id:
                        max_id = val
                except ValueError:
                    pass
        wb.close()
        return str(max_id + 1 if max_id > 0 else 7)

    def file_change_request(
        self,
        submission: CRSubmission,
        output_dir: Optional[Path | str] = None,
    ) -> CRProcessingResult:
        """
        Process a complete Change Request:
        1. Formats and stamps Change_Request_Form.docx
        2. Appends registration row to Change_Log_Ledger.xlsx
        3. Generates CR_Scoping_and_Mandays.xlsx
        4. Prepares draft BAST_Change_Request.docx
        """
        cr_id = submission.cr_id or self._get_next_cr_id()
        if output_dir:
            out_p = Path(output_dir)
        else:
            client_prefix = self.context.client_short_name if self.context else DEFAULT_CLIENT_SHORT_NAME
            out_p = Path("output") / f"{client_prefix}_Snowflake_Analytics" / "change_requests" / f"CR_{cr_id.zfill(2)}"
        out_p.mkdir(parents=True, exist_ok=True)

        total_mandays = sum(submission.mandays_breakdown.values())

        # 1. Generate Change_Request_Form.docx
        form_template = self.project.resolve_clean_file("4.4_Change_Request_Form_Template.docx")
        if not form_template:
            raise FileNotFoundError("4.4_Change_Request_Form_Template.docx not found in clean workspace.")

        doc = docx.Document(str(form_template))

        # Table 0: Metadata
        if len(doc.tables) > 0:
            t0 = doc.tables[0]
            t0.rows[0].cells[2].text = cr_id
            t0.rows[1].cells[2].text = submission.submission_date
            t0.rows[2].cells[2].text = submission.requester
            t0.rows[3].cells[2].text = submission.department

        # Table 1: Change Details
        if len(doc.tables) > 1:
            t1 = doc.tables[1]
            t1.rows[0].cells[2].text = submission.title
            t1.rows[1].cells[2].text = submission.category
            t1.rows[2].cells[2].text = submission.priority
            t1.rows[3].cells[2].text = submission.description
            t1.rows[4].cells[2].text = submission.reason

        # Table 2: Impact Analysis
        if len(doc.tables) > 2:
            t2 = doc.tables[2]
            t2.rows[0].cells[2].text = submission.scope_impact
            t2.rows[1].cells[2].text = f"Estimasi waktu pelaksanaan: {submission.schedule_days} hari + {submission.buffer_days} hari buffer."
            t2.rows[2].cells[2].text = submission.cost_estimate
            t2.rows[3].cells[2].text = f"Total estimasi kebutuhan sumber daya: {total_mandays} mandays."
            t2.rows[4].cells[2].text = submission.risk_impact
            t2.rows[5].cells[2].text = submission.quality_impact

        # Table 3: Effort Breakdown
        if len(doc.tables) > 3:
            t3 = doc.tables[3]
            t3.rows[0].cells[2].text = f"{submission.mandays_breakdown.get('analysis_pm', 0)} mandays"
            t3.rows[1].cells[2].text = f"{submission.mandays_breakdown.get('development', 0)} mandays"
            t3.rows[2].cells[2].text = f"{submission.mandays_breakdown.get('testing', 0)} mandays"
            t3.rows[3].cells[2].text = f"{submission.mandays_breakdown.get('deployment', 0)} mandays"
            t3.rows[4].cells[2].text = f"{total_mandays} mandays"

        doc_out_path = out_p / f"Change_Request_Form_CR_{cr_id.zfill(2)}.docx"
        _substitute_docx(doc, self.context)
        doc.save(str(doc_out_path))

        # 2. Append to Change_Log_Ledger.xlsx
        ledger_template = self.project.resolve_clean_file("4.4_Change_Log_Ledger_Template.xlsx")
        ledger_out_path = out_p / f"Change_Log_Ledger_Updated_CR_{cr_id.zfill(2)}.xlsx"
        ledger_updated = False

        if ledger_template and ledger_template.exists():
            wb = openpyxl.load_workbook(str(ledger_template))
            ws = wb["Change Log"] if "Change Log" in wb.sheetnames else wb.active
            new_row = [
                int(cr_id) if cr_id.isdigit() else cr_id,
                datetime.now().strftime("%Y-%m-%d"),
                submission.title,
                submission.description[:250] + ("..." if len(submission.description) > 250 else ""),
                submission.category,
                "Business Request",
                submission.requester,
                submission.reason,
                submission.scope_impact[:120],
                f"{submission.schedule_days} hari",
                submission.cost_estimate,
                f"{total_mandays} mandays",
                "Impact Analysis Completed",
                "Under Review",
            ]
            ws.append(new_row)
            _substitute_xlsx(wb, self.context)
            wb.save(str(ledger_out_path))
            wb.close()
            ledger_updated = True

        # 3. Generate CR_Scoping_and_Mandays.xlsx
        scoping_template = self.project.resolve_clean_file("CR_Scoping_and_Mandays_Template.xlsx")
        scoping_out_path = out_p / f"CR_Scoping_and_Mandays_CR_{cr_id.zfill(2)}.xlsx"
        if scoping_template and scoping_template.exists():
            wb_sc = openpyxl.load_workbook(str(scoping_template))
            ws_gen = wb_sc["General"] if "General" in wb_sc.sheetnames else wb_sc.active
            ws_gen.cell(row=1, column=2, value=f"CR-{cr_id}: {submission.title}")
            ws_gen.cell(row=2, column=2, value=f"Total Mandays: {total_mandays}")
            ws_gen.cell(row=3, column=2, value=submission.description[:150])

            # Create specific detail sheet for this CR
            ws_cr = wb_sc.create_sheet(title=f"CR{cr_id} Breakdown")
            ws_cr.append(["Activity / Workstream", "Role / Team", "Estimated Mandays"])
            ws_cr.append(["Analysis, Design & Governance", "Project Manager / BA", submission.mandays_breakdown.get("analysis_pm", 0)])
            ws_cr.append(["Snowflake Engineering & UI Dev", "Data & Streamlit Devs", submission.mandays_breakdown.get("development", 0)])
            ws_cr.append(["Integration & Regression Testing", "QA Engineer", submission.mandays_breakdown.get("testing", 0)])
            ws_cr.append(["Deployment & Operational Handover", "DevOps Engineer", submission.mandays_breakdown.get("deployment", 0)])
            ws_cr.append(["Total Committed Effort", "All Teams", total_mandays])

            _substitute_xlsx(wb_sc, self.context)
            wb_sc.save(str(scoping_out_path))
            wb_sc.close()

        # 4. Generate draft BAST_Change_Request.docx
        bast_template = self.project.resolve_clean_file("BAST_Change_Request_Template.docx")
        bast_out_path = out_p / f"BAST_Change_Request_Draft_CR_{cr_id.zfill(2)}.docx"
        if bast_template and bast_template.exists():
            doc_bast = docx.Document(str(bast_template))
            # Insert CR title in paragraph 2
            if len(doc_bast.paragraphs) > 1:
                p = doc_bast.paragraphs[1]
                p.text = f"Pekerjaan : Jasa Implementasi Snowflake - Change Request #{cr_id} ({submission.title})"
            _substitute_docx(doc_bast, self.context)
            doc_bast.save(str(bast_out_path))

        summary = (
            f"Successfully filed Change Request #{cr_id}: '{submission.title}'\n"
            f"- Form: {doc_out_path}\n"
            f"- Ledger: {ledger_out_path}\n"
            f"- Scoping: {scoping_out_path}\n"
            f"- BAST Draft: {bast_out_path}\n"
            f"- Total Effort: {total_mandays} mandays across {submission.schedule_days} calendar days."
        )

        return CRProcessingResult(
            cr_id=cr_id,
            project_id=self.project_id,
            cr_form_path=str(doc_out_path),
            ledger_updated=ledger_updated,
            mandays_sheet_path=str(scoping_out_path),
            bast_draft_path=str(bast_out_path),
            total_mandays=total_mandays,
            summary=summary,
        )
