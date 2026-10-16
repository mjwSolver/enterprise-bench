"""
Universal Slug Registry & Engagement Context
============================================
Authoritative catalog of standardized variable slugs across presentations,
Word documents, and spreadsheets, with automated pre-render substitution
and PII leak detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# ============================================================================
# 1. Authoritative Slug Taxonomy
# ============================================================================

STANDARD_SLUG_MAP: Dict[str, str] = {
    # Corporate & Institutional Entities
    "[CLIENT_COMPANY_NAME]": "client_company_name",
    "[CLIENT_SHORT_NAME]": "client_short_name",
    "[CLIENT_ADDRESS]": "client_address",
    "[VENDOR_COMPANY_NAME]": "vendor_company_name",
    "[VENDOR_SHORT_NAME]": "vendor_short_name",
    "[VENDOR_DIVISION]": "vendor_division",

    # Project Governance & Contractual
    "[PROJECT_NAME]": "project_name",
    "[PROJECT_CODE]": "project_code",
    "[CONTRACT_NUMBER]": "contract_number",
    "[MILESTONE_NAME]": "milestone_name",
    "[BAST_NUMBER]": "bast_number",
    "[REPORT_DATE]": "report_date",
    "[REPORTING_PERIOD]": "reporting_period",

    # RACI Governance & Personnel
    "[CLIENT_SPONSOR_NAME]": "client_sponsor_name",
    "[CLIENT_SPONSOR_TITLE]": "client_sponsor_title",
    "[CLIENT_PM_NAME]": "client_pm_name",
    "[CLIENT_BPO_LEAD]": "client_bpo_lead",
    "[CLIENT_IT_LEAD]": "client_it_lead",
    "[VENDOR_PARTNER_NAME]": "vendor_partner_name",
    "[VENDOR_PM_NAME]": "vendor_pm_name",
    "[LEAD_ARCHITECT_NAME]": "lead_architect_name",
}

DEFAULT_CLIENT_COMPANY_NAME = "Nusantara Global Logistics"
DEFAULT_CLIENT_SHORT_NAME = "NGL"
DEFAULT_CLIENT_ADDRESS = "Gedung Cyber 2, Lt. 18, Jl. H.R. Rasuna Said, Jakarta Selatan"
DEFAULT_PROJECT_NAME = "Enterprise Financial Intelligence & Cloud Analytics Platform"
DEFAULT_VENDOR_COMPANY_NAME = "PT Metrodata Electronics Tbk"
DEFAULT_VENDOR_SHORT_NAME = "Metrodata"
DEFAULT_VENDOR_DIVISION = "Data & AI Modernization Practice"

# Forbidden Legacy Entities for PII Leak Audits
DEFAULT_FORBIDDEN_PATTERNS: List[str] = [
    r"\bToyota\b",
    r"\bTsusho\b",
    r"\bTTI\b",
    r"\bTTLC\b",
]

_COMPILED_FORBIDDEN_PATTERNS: List[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in DEFAULT_FORBIDDEN_PATTERNS
]

_LEGACY_ENTITY_PATTERNS: Dict[str, re.Pattern[str]] = {
    "pt_tti": re.compile(r"\bPT\.?[\s\u00a0]+Toyota[\s\u00a0]+Ts?h?usho[\s\u00a0]+Indonesia\b", re.IGNORECASE),
    "tti_full": re.compile(r"\bToyota[\s\u00a0]+Ts?h?usho[\s\u00a0]+Indonesia\b", re.IGNORECASE),
    "toyota_tsusho": re.compile(r"\bToyota[\s\u00a0]+(Ts?h?usho|Susho)\b", re.IGNORECASE),
    "toyota_short": re.compile(r"\b(Toyota|Tsusho|Tshuso)\b", re.IGNORECASE),
    "ttlc": re.compile(r"(?<![A-Za-z0-9])TTLC(?![A-Za-z0-9])"),
    "tti": re.compile(r"(?<![A-Za-z0-9])TTI(?![A-Za-z0-9])"),
    "tti_domain": re.compile(r"@tti\.co\.id\b", re.IGNORECASE),
    "fredric": re.compile(r"\bFredric[\s\u00a0]+Retanubun\b", re.IGNORECASE),
    "tadahiko": re.compile(r"\bTadahiko[\s\u00a0]+Onaka\b", re.IGNORECASE),
    "debby": re.compile(r"\bDebby[\s\u00a0]+Lutfi[\s\u00a0]+Adria?nto\b", re.IGNORECASE),
    "agus": re.compile(r"\bAgus[\s\u00a0]+Pramono\b", re.IGNORECASE),
    "arif": re.compile(r"\bArif[\s\u00a0]+Nanda[\s\u00a0]+Hermawan\b", re.IGNORECASE),
}


# ============================================================================
# 2. Engagement Context Model
# ============================================================================

class EngagementContext(BaseModel):
    """Complete engagement parameterization for multi-asset deliverable branding."""
    client_company_name: str = Field(DEFAULT_CLIENT_COMPANY_NAME, description="Full client legal name")
    client_short_name: str = Field(DEFAULT_CLIENT_SHORT_NAME, description="Client abbreviation or acronym")
    client_address: str = Field(DEFAULT_CLIENT_ADDRESS, description="Client address")
    vendor_company_name: str = Field(DEFAULT_VENDOR_COMPANY_NAME, description="Implementation partner name")
    vendor_short_name: str = Field(DEFAULT_VENDOR_SHORT_NAME, description="Vendor short name")
    vendor_division: str = Field(DEFAULT_VENDOR_DIVISION, description="Consulting practice name")

    project_name: str = Field(DEFAULT_PROJECT_NAME, description="Project title")
    project_code: str = Field("ENG-2000-NGL-01", description="PMO engagement tracking code")
    contract_number: str = Field("015/PKS/NGL-MII/XII/1999", description="PKS contract reference")
    milestone_name: str = Field("Milestone 1 — Assessment & Architecture Design", description="Current milestone")
    bast_number: str = Field("001/BAST/NGL-MII/I/2000", description="Handover certificate number")
    report_date: str = Field("05 Jan 2000", description="Publication date string")
    reporting_period: str = Field("15 Dec 1999 - 02 Jan 2000", description="Progress period")

    client_sponsor_name: str = Field("Hendra Setiawan", description="Executive sponsor")
    client_sponsor_title: str = Field("VP Finance & Technology", description="Sponsor title")
    client_pm_name: str = Field("Dewi Lestari", description="Client Project Manager")
    client_bpo_lead: str = Field("Agus Pramono", description="Business Process Owner")
    client_it_lead: str = Field("Bambang Wijaya", description="IT Infrastructure Lead")
    vendor_partner_name: str = Field("Agustino", description="Vendor Engagement Partner")
    vendor_pm_name: str = Field("Budi Pratama, PMP", description="Vendor Project Manager")
    lead_architect_name: str = Field("Fajar Nugraha", description="Lead Solution Architect")

    @classmethod
    def default_ngl(cls) -> "EngagementContext":
        """Return the canonical system-wide default engagement context."""
        return cls()

    @classmethod
    def from_client_name(cls, client_name: str) -> "EngagementContext":
        """Construct an EngagementContext from a client slug or company name."""
        if not client_name or client_name.strip().upper() in ("NGL", "NUSANTARA GLOBAL LOGISTICS"):
            return cls.default_ngl()
        return cls(client_company_name=client_name, client_short_name=client_name)

    def substitute(self, text: str) -> str:
        """Replace all slug tokens and forbidden legacy client entities in text with contextual values."""
        if not text:
            return text
        rep = self.to_slug_replacement_dict()
        for slug, val in rep.items():
            if slug in text:
                text = text.replace(slug, str(val))
        # Universal normalization of legacy client entities, domains & known personnel
        text = _LEGACY_ENTITY_PATTERNS["pt_tti"].sub(self.client_company_name, text)
        text = _LEGACY_ENTITY_PATTERNS["tti_full"].sub(self.client_company_name, text)
        text = _LEGACY_ENTITY_PATTERNS["toyota_tsusho"].sub(self.client_company_name, text)
        text = _LEGACY_ENTITY_PATTERNS["toyota_short"].sub(self.client_short_name, text)
        text = _LEGACY_ENTITY_PATTERNS["ttlc"].sub(self.client_short_name, text)
        text = _LEGACY_ENTITY_PATTERNS["tti"].sub(self.client_short_name, text)
        text = _LEGACY_ENTITY_PATTERNS["tti_domain"].sub(f"@{self.client_short_name.lower()}.co.id", text)
        text = _LEGACY_ENTITY_PATTERNS["fredric"].sub(self.client_pm_name, text)
        text = _LEGACY_ENTITY_PATTERNS["tadahiko"].sub(self.client_sponsor_name, text)
        text = _LEGACY_ENTITY_PATTERNS["debby"].sub(self.client_bpo_lead, text)
        text = _LEGACY_ENTITY_PATTERNS["agus"].sub(self.client_bpo_lead, text)
        text = _LEGACY_ENTITY_PATTERNS["arif"].sub(self.client_sponsor_name, text)
        return text

    def to_slug_replacement_dict(self) -> Dict[str, str]:
        """Convert fields into [SLUG] -> value dictionary."""
        d = self.model_dump()
        rep: Dict[str, str] = {}
        for slug, field_key in STANDARD_SLUG_MAP.items():
            rep[slug] = str(d.get(field_key, slug))
        return rep


# ============================================================================
# 3. PII & Slug Audit Engine
# ============================================================================

@dataclass
class PIIFinding:
    file_path: Path
    pattern: str
    match_snippet: str
    location: str


@dataclass
class PIIAuditReport:
    total_files_scanned: int
    findings: List[PIIFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.findings) == 0


def audit_pii_in_file(
    file_path: Path,
    forbidden_patterns: Optional[List[str]] = None,
) -> List[PIIFinding]:
    """Scan a document (.docx, .xlsx, .pptx, or text) for forbidden legacy entities."""
    patterns = (
        [re.compile(p, re.IGNORECASE) for p in forbidden_patterns]
        if forbidden_patterns is not None
        else _COMPILED_FORBIDDEN_PATTERNS
    )
    findings: List[PIIFinding] = []

    ext = file_path.suffix.lower()

    if ext == ".docx":
        import docx
        try:
            doc = docx.Document(str(file_path))
            for p_idx, p in enumerate(doc.paragraphs):
                for pat in patterns:
                    m = pat.search(p.text)
                    if m:
                        findings.append(
                            PIIFinding(
                                file_path=file_path,
                                pattern=pat.pattern,
                                match_snippet=p.text[max(0, m.start() - 20):min(len(p.text), m.end() + 20)].strip(),
                                location=f"Paragraph {p_idx + 1}",
                            )
                        )
            for t_idx, table in enumerate(doc.tables):
                for r_idx, row in enumerate(table.rows):
                    for c_idx, cell in enumerate(row.cells):
                        for pat in patterns:
                            m = pat.search(cell.text)
                            if m:
                                findings.append(
                                    PIIFinding(
                                        file_path=file_path,
                                        pattern=pat.pattern,
                                        match_snippet=cell.text[max(0, m.start() - 20):min(len(cell.text), m.end() + 20)].strip(),
                                        location=f"Table {t_idx + 1} R{r_idx + 1}C{c_idx + 1}",
                                    )
                                )
            for s_idx, section in enumerate(doc.sections, start=1):
                for hf_name, hf in (("Header", section.header), ("Footer", section.footer)):
                    if hf is None:
                        continue
                    for p_idx, p in enumerate(hf.paragraphs, start=1):
                        for pat in patterns:
                            m = pat.search(p.text)
                            if m:
                                findings.append(
                                    PIIFinding(
                                        file_path=file_path,
                                        pattern=pat.pattern,
                                        match_snippet=p.text[max(0, m.start() - 20):min(len(p.text), m.end() + 20)].strip(),
                                        location=f"Section {s_idx} {hf_name} Paragraph {p_idx}",
                                    )
                                )
                    for t_idx, table in enumerate(hf.tables, start=1):
                        for r_idx, row in enumerate(table.rows, start=1):
                            for c_idx, cell in enumerate(row.cells, start=1):
                                for pat in patterns:
                                    m = pat.search(cell.text)
                                    if m:
                                        findings.append(
                                            PIIFinding(
                                                file_path=file_path,
                                                pattern=pat.pattern,
                                                match_snippet=cell.text[max(0, m.start() - 20):min(len(cell.text), m.end() + 20)].strip(),
                                                location=f"Section {s_idx} {hf_name} Table {t_idx} R{r_idx}C{c_idx}",
                                            )
                                        )
        except Exception:
            pass

    elif ext == ".pptx":
        from pptx import Presentation
        try:
            prs = Presentation(str(file_path))

            def _scan_ppt_shape(sh: Any, s_idx: int) -> None:
                if sh.has_text_frame:
                    for p in sh.text_frame.paragraphs:
                        for pat in patterns:
                            m = pat.search(p.text)
                            if m:
                                findings.append(
                                    PIIFinding(
                                        file_path=file_path,
                                        pattern=pat.pattern,
                                        match_snippet=p.text[max(0, m.start() - 20):min(len(p.text), m.end() + 20)].strip(),
                                        location=f"Slide {s_idx} Shape '{sh.name}'",
                                    )
                                )
                if sh.has_table:
                    for r_idx, row in enumerate(sh.table.rows, start=1):
                        for c_idx, cell in enumerate(row.cells, start=1):
                            for pat in patterns:
                                m = pat.search(cell.text)
                                if m:
                                    findings.append(
                                        PIIFinding(
                                            file_path=file_path,
                                            pattern=pat.pattern,
                                            match_snippet=cell.text[max(0, m.start() - 20):min(len(cell.text), m.end() + 20)].strip(),
                                            location=f"Slide {s_idx} Table '{sh.name}' R{r_idx}C{c_idx}",
                                        )
                                    )
                if hasattr(sh, "shapes"):
                    for sub_sh in sh.shapes:
                        _scan_ppt_shape(sub_sh, s_idx)

            for s_idx, slide in enumerate(prs.slides, start=1):
                for sh in slide.shapes:
                    _scan_ppt_shape(sh, s_idx)
        except Exception:
            pass

    elif ext == ".xlsx":
        import openpyxl
        try:
            wb = openpyxl.load_workbook(str(file_path), data_only=True, read_only=True)
            try:
                for sheetname in wb.sheetnames:
                    ws = wb[sheetname]
                    for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                        for c_idx, val in enumerate(row, start=1):
                            if isinstance(val, str):
                                for pat in patterns:
                                    m = pat.search(val)
                                    if m:
                                        findings.append(
                                            PIIFinding(
                                                file_path=file_path,
                                                pattern=pat.pattern,
                                                match_snippet=val[max(0, m.start() - 20):min(len(val), m.end() + 20)].strip(),
                                                location=f"Sheet '{sheetname}' R{r_idx}C{c_idx}",
                                            )
                                        )
            finally:
                wb.close()
        except Exception:
            pass

    else:
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line_idx, line in enumerate(lines, start=1):
                for pat in patterns:
                    m = pat.search(line)
                    if m:
                        findings.append(
                            PIIFinding(
                                file_path=file_path,
                                pattern=pat.pattern,
                                match_snippet=line[max(0, m.start() - 20):min(len(line), m.end() + 20)].strip(),
                                location=f"Line {line_idx}",
                            )
                        )
        except Exception:
            pass

    return findings


def audit_directory_pii(
    directory: Path,
    forbidden_patterns: Optional[List[str]] = None,
) -> PIIAuditReport:
    """Recursively scan directory for PII leak violations across deliverables."""
    findings: List[PIIFinding] = []
    scanned = 0
    valid_exts = {".docx", ".pptx", ".xlsx", ".json", ".yaml", ".yml", ".md"}

    for p in directory.rglob("*"):
        if p.is_file() and p.suffix.lower() in valid_exts:
            scanned += 1
            f_list = audit_pii_in_file(p, forbidden_patterns=forbidden_patterns)
            findings.extend(f_list)

    return PIIAuditReport(total_files_scanned=scanned, findings=findings)


# ============================================================================
# 4. Universal Slug Substitution Middleware
# ============================================================================

def load_engagement_context(path: Union[str, Path]) -> EngagementContext:
    """Load EngagementContext from JSON or YAML file."""
    import json
    import yaml

    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Engagement context file not found: {p}")

    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    return EngagementContext(**data)


def substitute_slugs_in_presentation(
    prs: Any,
    replacement_map: Union[EngagementContext, Dict[str, str]],
) -> int:
    """
    Scans all slides, shapes, group shapes, tables, and text frames in a Presentation,
    substituting slug tokens (e.g. [CLIENT_COMPANY_NAME]) with parameter values.
    Returns the total number of substitutions made.
    """
    context: Optional[EngagementContext] = replacement_map if isinstance(replacement_map, EngagementContext) else None
    if context:
        rep = context.to_slug_replacement_dict()
    else:
        rep = replacement_map

    total_subs = 0

    def _substitute_paragraph(paragraph: Any) -> int:
        subs = 0
        for slug, val in rep.items():
            if slug in paragraph.text:
                found_in_runs = False
                for run in paragraph.runs:
                    if slug in run.text:
                        run.text = run.text.replace(slug, str(val))
                        subs += 1
                        found_in_runs = True
                if not found_in_runs and slug in paragraph.text:
                    paragraph.text = paragraph.text.replace(slug, str(val))
                    subs += 1
        if context:
            target = context.substitute(paragraph.text)
            if paragraph.text != target:
                run_subs = 0
                for run in paragraph.runs:
                    if run.text:
                        norm_r = context.substitute(run.text)
                        if norm_r != run.text:
                            run.text = norm_r
                            run_subs += 1
                if paragraph.text != target or paragraph.text != context.substitute(paragraph.text):
                    paragraph.text = target
                    subs += 1
                else:
                    subs += run_subs
        return subs

    def _process_shape(shape: Any) -> int:
        subs = 0
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                subs += _substitute_paragraph(paragraph)

        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    for paragraph in cell.text_frame.paragraphs:
                        subs += _substitute_paragraph(paragraph)

        if hasattr(shape, "shapes"):
            for sub_shape in shape.shapes:
                subs += _process_shape(sub_shape)

        return subs

    for slide in prs.slides:
        for shape in slide.shapes:
            total_subs += _process_shape(shape)

    return total_subs


def substitute_slugs_in_document(
    doc: Any,
    replacement_map: Union[EngagementContext, Dict[str, str]],
) -> int:
    """
    Scans body paragraphs, tables, headers, and footers in a python-docx Document,
    substituting slug tokens with parameter values.
    """
    context: Optional[EngagementContext] = replacement_map if isinstance(replacement_map, EngagementContext) else None
    if context:
        rep = context.to_slug_replacement_dict()
    else:
        rep = replacement_map

    total_subs = 0

    def _substitute_paragraph(p: Any) -> int:
        subs = 0
        for slug, val in rep.items():
            if slug in p.text:
                for r in p.runs:
                    if slug in r.text:
                        r.text = r.text.replace(slug, str(val))
                        subs += 1
                if slug in p.text:
                    p.text = p.text.replace(slug, str(val))
                    subs += 1
        if context:
            target = context.substitute(p.text)
            if p.text != target:
                run_subs = 0
                for r in p.runs:
                    if r.text:
                        norm_r = context.substitute(r.text)
                        if norm_r != r.text:
                            r.text = norm_r
                            run_subs += 1
                if p.text != target or p.text != context.substitute(p.text):
                    p.text = target
                    subs += 1
                else:
                    subs += run_subs
        return subs

    # Body paragraphs
    for p in doc.paragraphs:
        total_subs += _substitute_paragraph(p)

    # Tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    total_subs += _substitute_paragraph(p)

    # Headers & Footers
    for section in doc.sections:
        for hf in (section.header, section.footer):
            if hf is None:
                continue
            for p in hf.paragraphs:
                total_subs += _substitute_paragraph(p)
            for table in hf.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            total_subs += _substitute_paragraph(p)

    return total_subs


def substitute_slugs_in_workbook(
    wb: Any,
    replacement_map: Union[EngagementContext, Dict[str, str]],
) -> int:
    """
    Scans all cells across sheets in an openpyxl Workbook, substituting slug tokens.
    Preserves formulas and data types.
    """
    context: Optional[EngagementContext] = replacement_map if isinstance(replacement_map, EngagementContext) else None
    if context:
        rep = context.to_slug_replacement_dict()
    else:
        rep = replacement_map

    total_subs = 0

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    for slug, val in rep.items():
                        if slug in cell.value:
                            cell.value = cell.value.replace(slug, str(val))
                            total_subs += 1
                    if context:
                        orig = cell.value
                        normalized = context.substitute(orig)
                        if orig != normalized:
                            cell.value = normalized
                            total_subs += 1

    return total_subs

