"""
Alias Linter & Identity Pre-Flight Checker
==========================================
Scans deliverables (.docx, .pptx, .xlsx) before shipping to verify that all
ROLE_* aliases, CLIENT_* handles, and template tokens have been cleanly rehydrated
with actual human names from the local vault.
Prevents shipping embarrassing placeholder roles (e.g. "ROLE_LEAD_ARCHITECT").
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from src.core.vault_builder import TeamVaultBuilder

# Regex patterns identifying un-rehydrated role handles or template tags
ROLE_PATTERN = re.compile(r"\bROLE_[A-Z0-9_]+\b")
CLIENT_PATTERN = re.compile(r"\bCLIENT_[A-Z0-9_]+\b")
STAFF_PATTERN = re.compile(r"\bSTAFF-[0-9]{3}\b")
JINJA_PATTERN = re.compile(r"\{\{\s*[a-zA-Z0-9_]+\s*\}\}")


class AliasFinding(BaseModel):
    """An un-rehydrated alias discovered in a document."""
    alias: str
    location: str
    finding_type: str = Field("ROLE_ALIAS", description="ROLE_ALIAS, CLIENT_HANDLE, JINJA_TAG")
    status_in_vault: str = Field(..., description="ASSIGNED_BUT_NOT_STAMPED or UNASSIGNED_IN_VAULT")
    suggested_action: str


class AliasAuditReport(BaseModel):
    """Audit report verifying deliverable readiness before shipping."""
    target_file: str
    is_ready_to_ship: bool
    total_unresolved: int = 0
    missing_practitioners: List[str] = Field(default_factory=list)
    findings: List[AliasFinding] = Field(default_factory=list)


class AliasLinter:
    """Audits documents for un-rehydrated aliases and verifies team completeness."""

    @classmethod
    def audit_document(
        cls,
        document_path: Path | str,
        project_id: Optional[str] = None,
    ) -> AliasAuditReport:
        """
        Scan a Word, PowerPoint, or Excel document for any lingering ROLE_*,
        CLIENT_*, STAFF-*, or Jinja {{ ... }} tokens.
        """
        p = Path(document_path)
        if not p.exists():
            raise FileNotFoundError(f"Target document not found: {p}")

        vault_replacements = TeamVaultBuilder.get_replacement_map(project_id)
        unassigned_in_vault = set(TeamVaultBuilder.list_unassigned_roles(project_id))

        findings: List[AliasFinding] = []
        ext = p.suffix.lower()

        # 1. Extract text nodes based on format
        nodes = cls._extract_text_nodes(p, ext)

        # 2. Check each node for lingering aliases
        for location, text in nodes:
            # Check ROLE_*
            for m in ROLE_PATTERN.finditer(text):
                raw_alias = m.group(0)
                status = "ASSIGNED_BUT_NOT_STAMPED" if raw_alias in vault_replacements else "UNASSIGNED_IN_VAULT"
                action = (
                    f"Run rehydration to replace with '{vault_replacements[raw_alias]}'"
                    if raw_alias in vault_replacements
                    else f"Assign a real practitioner name to {raw_alias} in team_vault.local.json"
                )
                findings.append(
                    AliasFinding(
                        alias=raw_alias,
                        location=location,
                        finding_type="ROLE_ALIAS",
                        status_in_vault=status,
                        suggested_action=action,
                    )
                )

            # Check CLIENT_*
            for m in CLIENT_PATTERN.finditer(text):
                raw_alias = m.group(0)
                status = "ASSIGNED_BUT_NOT_STAMPED" if raw_alias in vault_replacements else "UNASSIGNED_IN_VAULT"
                action = (
                    f"Run rehydration to replace with '{vault_replacements[raw_alias]}'"
                    if raw_alias in vault_replacements
                    else f"Assign real client contact to {raw_alias} in team_vault.local.json"
                )
                findings.append(
                    AliasFinding(
                        alias=raw_alias,
                        location=location,
                        finding_type="CLIENT_HANDLE",
                        status_in_vault=status,
                        suggested_action=action,
                    )
                )

            # Check unrendered Jinja tags
            for m in JINJA_PATTERN.finditer(text):
                raw_tag = m.group(0)
                findings.append(
                    AliasFinding(
                        alias=raw_tag,
                        location=location,
                        finding_type="JINJA_TAG",
                        status_in_vault="UNRENDERED_VARIABLE",
                        suggested_action="Supply missing variable in document context payload",
                    )
                )

        # Calculate distinct missing practitioners
        missing = sorted(list({f.alias for f in findings if f.status_in_vault == "UNASSIGNED_IN_VAULT"}))
        is_ready = len(findings) == 0

        return AliasAuditReport(
            target_file=str(p),
            is_ready_to_ship=is_ready,
            total_unresolved=len(findings),
            missing_practitioners=missing,
            findings=findings,
        )

    @classmethod
    def rehydrate_document(
        cls,
        input_path: Path | str,
        output_path: Optional[Path | str] = None,
        project_id: Optional[str] = None,
    ) -> Path:
        """
        Replaces all known ROLE_* and CLIENT_* aliases with actual names
        from the local identity vault, creating a clean deliverable ready for client presentation.
        """
        in_p = Path(input_path)
        out_p = Path(output_path) if output_path else in_p.parent / f"{in_p.stem}_rehydrated{in_p.suffix}"

        replacements = TeamVaultBuilder.get_replacement_map(project_id)
        if not replacements:
            print("Warning: No identity bindings found in local vault. Document unchanged.")
            return in_p

        ext = in_p.suffix.lower()
        if ext == ".docx":
            from src.core.pii.handlers.docx_handler import DocxHandler
            handler = DocxHandler()
            handler.apply_replacements(in_p, out_p, replacements=replacements, strip_metadata=False)
        elif ext == ".pptx":
            from src.core.pii.handlers.pptx_handler import PptxHandler
            handler = PptxHandler()
            handler.apply_replacements(in_p, out_p, replacements=replacements, strip_metadata=False)
        elif ext in [".xlsx", ".xlsm"]:
            from src.core.pii.handlers.xlsx_handler import XlsxHandler
            handler = XlsxHandler()
            handler.apply_replacements(in_p, out_p, replacements=replacements, strip_metadata=False)
        else:
            raise ValueError(f"Unsupported format for rehydration: {ext}")

        return out_p

    @classmethod
    def _extract_text_nodes(cls, path: Path, ext: str) -> List[tuple[str, str]]:
        nodes: List[tuple[str, str]] = []
        if ext == ".docx":
            import docx
            doc = docx.Document(str(path))
            for i, p in enumerate(doc.paragraphs):
                if p.text.strip():
                    nodes.append((f"Body > Para {i + 1}", p.text.strip()))
            for t_idx, t in enumerate(doc.tables):
                for r_idx, r in enumerate(t.rows):
                    for c_idx, c in enumerate(r.cells):
                        if c.text.strip():
                            nodes.append((f"Table {t_idx + 1} > R{r_idx + 1}C{c_idx + 1}", c.text.strip()))
        elif ext == ".pptx":
            import pptx
            prs = pptx.Presentation(str(path))
            for s_idx, s in enumerate(prs.slides):
                for shp_idx, shp in enumerate(s.shapes):
                    if shp.has_text_frame and shp.text_frame.text.strip():
                        nodes.append((f"Slide {s_idx + 1} > Shape {shp_idx + 1}", shp.text_frame.text.strip()))
                    if shp.has_table:
                        for r_idx, r in enumerate(shp.table.rows):
                            for c_idx, c in enumerate(r.cells):
                                if c.text_frame.text.strip():
                                    nodes.append((f"Slide {s_idx + 1} > Table R{r_idx + 1}C{c_idx + 1}", c.text_frame.text.strip()))
        elif ext in [".xlsx", ".xlsm"]:
            import openpyxl
            wb = openpyxl.load_workbook(str(path), data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=False):
                    for cell in row:
                        if cell.value and isinstance(cell.value, str) and cell.value.strip():
                            nodes.append((f"Sheet '{ws.title}' > Cell {cell.coordinate}", cell.value.strip()))
            wb.close()
        return nodes
