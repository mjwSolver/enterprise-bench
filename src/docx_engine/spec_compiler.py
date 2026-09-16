"""
Modular Technical Specification Compiler
========================================
Compiles modular Markdown documents (FSD, TSD, SIT/UAT test scenario matrices,
user manuals) into professional, audit-compliant Microsoft Word (.docx) deliverables.

Key Features:
- Corporate Theme Integration: Inherits brand palettes from EnterpriseTheme.
- Frontmatter & Metadata Extraction: Cover page with Metrodata dual-stripe branding,
  document control history, and approval matrices.
- Shaded Code Callouts: Single-cell OpenXML callout cards with monospace Consolas,
  light slate background, and left accent border bar.
- Automated Mermaid Diagram Compilation: Automatically compiles ```mermaid blocks
  into high-DPI PNG figures via DiagramEngine and embeds them with centered captions.
- Styled Enterprise Tables: Table styling with repeating headers (<w:tblHeader/>),
  row split prevention (<w:cantSplit/>), and scenario status badges (PASSED, FAILED, PENDING).
- Advisory Callout Blocks: Transforms GitHub-style alerts (> [!NOTE], > [!WARNING])
  into shaded advisory cards.
- Modular Directory Compilation: Sequentially compiles ordered markdown sections
  (01_overview.md, 02_ddl.md, etc.) into a cohesive master deliverable.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table, _Cell, _Row
import yaml

from src.core.config import OUTPUT_DIR
from src.core.theme import EnterpriseTheme, parse_hex
from src.docx_engine.table_engine import (
    make_row_header,
    prevent_row_split,
    set_cell_background,
    set_cell_margins,
    style_table,
)


# ============================================================================
# OpenXML XML Helper Functions
# ============================================================================

def _set_cell_borders(
    cell: _Cell,
    top: Optional[Dict[str, Any]] = None,
    bottom: Optional[Dict[str, Any]] = None,
    left: Optional[Dict[str, Any]] = None,
    right: Optional[Dict[str, Any]] = None,
) -> None:
    """Apply custom OpenXML borders to a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')

    borders = [("top", top), ("bottom", bottom), ("left", left), ("right", right)]
    for edge_name, edge_cfg in borders:
        if edge_cfg is None:
            tag = f'<w:{edge_name} {nsdecls("w")} w:val="none"/>'
        elif edge_cfg == "nil":
            tag = f'<w:{edge_name} {nsdecls("w")} w:val="nil"/>'
        elif isinstance(edge_cfg, dict):
            val = edge_cfg.get("val", "single")
            sz = edge_cfg.get("sz", 4)
            space = edge_cfg.get("space", 0)
            color = edge_cfg.get("color", "auto")
            tag = f'<w:{edge_name} {nsdecls("w")} w:val="{val}" w:sz="{sz}" w:space="{space}" w:color="{color}"/>'
        else:
            continue
        tcBorders.append(parse_xml(tag))

    tcPr.append(tcBorders)


def _add_page_number_to_run(run) -> None:
    """Inject a dynamic PAGE field code into a Word run."""
    fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
    fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
    fldChar3 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)


# ============================================================================
# Data Models for Spec Compilation
# ============================================================================

@dataclass
class SpecMetadata:
    """Metadata extracted from frontmatter or metadata configuration."""
    title: str = "Technical Specification Document"
    subtitle: str = "Enterprise Architecture & System Design"
    client: str = "[CLIENT_COMPANY_NAME]"
    vendor: str = "[VENDOR_COMPANY_NAME]"
    version: str = "1.0"
    date: str = "September 2026"
    status: str = "Draft"
    confidentiality: str = "CONFIDENTIAL & PROPRIETARY"
    authors: List[str] = field(default_factory=lambda: ["Solutions Architecture Team"])
    reviewers: List[Dict[str, str]] = field(default_factory=list)
    document_control: List[Dict[str, str]] = field(default_factory=list)
    reference_documents: List[Dict[str, str]] = field(default_factory=list)
    theme: str = "metrodata"


# ============================================================================
# Main Spec Compiler Engine
# ============================================================================

class SpecCompiler:
    """
    High-fidelity Markdown to OpenXML Word compiler designed for
    enterprise technical specifications and test execution matrices.
    """

    def __init__(
        self,
        theme: Union[str, EnterpriseTheme] = "metrodata",
        metadata: Optional[SpecMetadata] = None,
        base_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        if isinstance(theme, str):
            try:
                self.theme = EnterpriseTheme.from_yaml(theme)
            except Exception:
                self.theme = EnterpriseTheme(name="metrodata", accent_primary="#1E3A8A", accent_secondary="#0284C7")
        else:
            self.theme = theme

        self.metadata = metadata or SpecMetadata()
        self.base_dir = Path(base_dir) if base_dir else None
        self.doc = docx.Document()
        self._init_page_geometry()
        self._init_styles()

    def _init_page_geometry(self) -> None:
        """Set standard Letter page with 0.8 inch margins."""
        for section in self.doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)
            section.different_first_page_header_footer = True

            # Setup body footer (starts on page 2)
            footer = section.footer
            f_p = footer.paragraphs[0]
            f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            f_p.paragraph_format.space_before = Pt(8)
            f_p.paragraph_format.space_after = Pt(0)
            
            # Left disclaimer, right page number
            r_disc = f_p.add_run(f"{self.metadata.confidentiality}  |  ")
            r_disc.font.name = self.theme.font_body
            r_disc.font.size = Pt(8.5)
            r_disc.font.color.rgb = RGBColor(148, 163, 184)

            r_page = f_p.add_run("Page ")
            r_page.font.name = self.theme.font_body
            r_page.font.size = Pt(8.5)
            r_page.font.color.rgb = RGBColor(148, 163, 184)
            _add_page_number_to_run(r_page)

    def _init_styles(self) -> None:
        """Configure standard typography styles matching corporate tokens."""
        styles = self.doc.styles

        # Normal paragraph style
        normal_style = styles["Normal"]
        normal_style.font.name = self.theme.font_body
        normal_style.font.size = Pt(10.5)
        normal_style.font.color.rgb = RGBColor(*parse_hex(self.theme.text_primary))
        normal_style.paragraph_format.line_spacing = 1.2
        normal_style.paragraph_format.space_after = Pt(6)

        # Heading 1: Primary accent, 16pt, Bold
        h1 = styles["Heading 1"]
        h1.font.name = self.theme.font_header
        h1.font.size = Pt(16)
        h1.font.bold = True
        h1.font.color.rgb = RGBColor(*parse_hex(self.theme.accent_primary))
        h1.paragraph_format.space_before = Pt(16)
        h1.paragraph_format.space_after = Pt(6)
        h1.paragraph_format.keep_with_next = True

        # Heading 2: Secondary accent, 13pt, Bold
        h2 = styles["Heading 2"]
        h2.font.name = self.theme.font_header
        h2.font.size = Pt(13)
        h2.font.bold = True
        h2.font.color.rgb = RGBColor(*parse_hex(self.theme.accent_secondary))
        h2.paragraph_format.space_before = Pt(12)
        h2.paragraph_format.space_after = Pt(4)
        h2.paragraph_format.keep_with_next = True

        # Heading 3: Dark primary, 11pt, Bold
        h3 = styles["Heading 3"]
        h3.font.name = self.theme.font_header
        h3.font.size = Pt(11)
        h3.font.bold = True
        h3.font.color.rgb = RGBColor(*parse_hex(self.theme.text_primary))
        h3.paragraph_format.space_before = Pt(10)
        h3.paragraph_format.space_after = Pt(3)
        h3.paragraph_format.keep_with_next = True

        # Heading 4: Muted slate, 10.5pt, Bold
        if "Heading 4" in styles:
            h4 = styles["Heading 4"]
            h4.font.name = self.theme.font_header
            h4.font.size = Pt(10.5)
            h4.font.bold = True
            h4.font.color.rgb = RGBColor(*parse_hex(self.theme.text_secondary))
            h4.paragraph_format.space_before = Pt(8)
            h4.paragraph_format.space_after = Pt(2)
            h4.paragraph_format.keep_with_next = True

    # ========================================================================
    # Cover Page & Governance Page Generators
    # ========================================================================

    def add_cover_page(self) -> None:
        """
        Build an executive cover page conforming strictly to repository cover conventions:
        - Dual vertical brand accent stripes (1 Red : 2 Blue ratio) flush on the left margin.
        - Large clean title and subtitle.
        - Clean typographic metadata columns (Client, Vendor, Date, Version) directly on background.
        - Zero boxed metadata cards.
        """
        top_spacer = self.doc.add_paragraph()
        top_spacer.paragraph_format.space_before = Pt(48)
        top_spacer.paragraph_format.space_after = Pt(0)

        # Dual Vertical Brand Accent Table (Red stripe 0.045", Blue stripe 0.090")
        stripe_tbl = self.doc.add_table(rows=1, cols=2)
        stripe_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
        stripe_tbl.autofit = False
        prevent_row_split(stripe_tbl.rows[0])
        
        c_red = stripe_tbl.rows[0].cells[0]
        c_blue = stripe_tbl.rows[0].cells[1]
        c_red.width = Inches(0.045)
        c_blue.width = Inches(0.090)
        set_cell_background(c_red, "DC2626")  # Crimson Red
        set_cell_background(c_blue, "1E3A8A")  # Metrodata Blue
        set_cell_margins(c_red, top=10, bottom=10, left=10, right=10)
        set_cell_margins(c_blue, top=10, bottom=10, left=10, right=10)

        # Title Paragraph
        p_title = self.doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(24)
        p_title.paragraph_format.space_after = Pt(6)
        r_title = p_title.add_run(self.metadata.title)
        r_title.font.name = self.theme.font_header
        r_title.font.size = Pt(26)
        r_title.font.bold = True
        r_title.font.color.rgb = RGBColor(*parse_hex(self.theme.accent_primary))

        # Subtitle Paragraph
        if self.metadata.subtitle:
            p_sub = self.doc.add_paragraph()
            p_sub.paragraph_format.space_before = Pt(0)
            p_sub.paragraph_format.space_after = Pt(36)
            r_sub = p_sub.add_run(self.metadata.subtitle)
            r_sub.font.name = self.theme.font_body
            r_sub.font.size = Pt(13)
            r_sub.font.color.rgb = RGBColor(*parse_hex(self.theme.text_secondary))

        # Divider Hairline
        p_div = self.doc.add_paragraph()
        p_div.paragraph_format.space_before = Pt(40)
        p_div.paragraph_format.space_after = Pt(24)
        r_div = p_div.add_run("―" * 48)
        r_div.font.size = Pt(9)
        r_div.font.color.rgb = RGBColor(226, 232, 240)

        # Typographic Multi-Column Metadata Table (Unboxed, clean)
        meta_tbl = self.doc.add_table(rows=2, cols=2)
        meta_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
        meta_tbl.autofit = False
        prevent_row_split(meta_tbl.rows[0])
        prevent_row_split(meta_tbl.rows[1])

        c_cl_lbl = meta_tbl.rows[0].cells[0]
        c_vn_lbl = meta_tbl.rows[0].cells[1]
        c_cl_val = meta_tbl.rows[1].cells[0]
        c_vn_val = meta_tbl.rows[1].cells[1]

        c_cl_lbl.width = Inches(3.4)
        c_vn_lbl.width = Inches(3.4)
        c_cl_val.width = Inches(3.4)
        c_vn_val.width = Inches(3.4)

        # Labels
        p_cl_l = c_cl_lbl.paragraphs[0]
        p_cl_l.paragraph_format.space_after = Pt(2)
        r_cl_l = p_cl_l.add_run("PREPARED FOR:")
        r_cl_l.font.size = Pt(8.5)
        r_cl_l.font.bold = True
        r_cl_l.font.color.rgb = RGBColor(148, 163, 184)

        p_vn_l = c_vn_lbl.paragraphs[0]
        p_vn_l.paragraph_format.space_after = Pt(2)
        r_vn_l = p_vn_l.add_run("PREPARED BY:")
        r_vn_l.font.size = Pt(8.5)
        r_vn_l.font.bold = True
        r_vn_l.font.color.rgb = RGBColor(148, 163, 184)

        # Values
        p_cl_v = c_cl_val.paragraphs[0]
        r_cl_name = p_cl_v.add_run(f"{self.metadata.client}\n")
        r_cl_name.font.size = Pt(11)
        r_cl_name.font.bold = True
        r_cl_name.font.color.rgb = RGBColor(*parse_hex(self.theme.text_primary))
        r_cl_det = p_cl_v.add_run(f"Project Stakeholders & Engineering\nDate: {self.metadata.date}")
        r_cl_det.font.size = Pt(9.5)
        r_cl_det.font.color.rgb = RGBColor(*parse_hex(self.theme.text_secondary))

        p_vn_v = c_vn_val.paragraphs[0]
        r_vn_name = p_vn_v.add_run(f"{self.metadata.vendor}\n")
        r_vn_name.font.size = Pt(11)
        r_vn_name.font.bold = True
        r_vn_name.font.color.rgb = RGBColor(*parse_hex(self.theme.text_primary))
        r_vn_det = p_vn_v.add_run(f"Solutions & Architecture Practice\nVersion: {self.metadata.version} ({self.metadata.status})")
        r_vn_det.font.size = Pt(9.5)
        r_vn_det.font.color.rgb = RGBColor(*parse_hex(self.theme.text_secondary))

        self.doc.add_page_break()

    def add_governance_section(self) -> None:
        """Render Document Control and Reviews & Acceptance tables."""
        # Heading: Document Control
        self.doc.add_heading("Document Control & History", level=1)
        self.doc.add_paragraph("This document undergoes formal version control and stakeholder review cycles.")

        # Document Control Table
        ctrl_rows = self.metadata.document_control or [
            {"date": self.metadata.date, "version": self.metadata.version, "author": "Solutions Architecture", "description": "Initial specification release"}
        ]
        tbl_ctrl = self.doc.add_table(rows=len(ctrl_rows) + 1, cols=4)
        style_table(tbl_ctrl, header_bg=self.theme.accent_primary.lstrip("#"), header_text_color="#FFFFFF")

        headers = ["Date / Tanggal", "Version / Versi", "Author / Penulis", "Change Description / Modifikasi"]
        for idx, text in enumerate(headers):
            tbl_ctrl.rows[0].cells[idx].paragraphs[0].text = text
            tbl_ctrl.rows[0].cells[idx].paragraphs[0].runs[0].font.bold = True

        for r_idx, row_data in enumerate(ctrl_rows, start=1):
            cells = tbl_ctrl.rows[r_idx].cells
            cells[0].paragraphs[0].text = str(row_data.get("date", ""))
            cells[1].paragraphs[0].text = str(row_data.get("version", ""))
            cells[2].paragraphs[0].text = str(row_data.get("author", ""))
            cells[3].paragraphs[0].text = str(row_data.get("description", ""))

        self.doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # Reviews & Acceptance Sign-off Matrix
        self.doc.add_heading("Reviews & Acceptance Sign-Off", level=2)
        reviewers = self.metadata.reviewers or [
            {"role": "Lead Architect", "name": "Principal Solutions Architect", "status": "APPROVED", "date": self.metadata.date},
            {"role": "Client Project Sponsor", "name": "VP / Head of Data & Analytics", "status": "PENDING", "date": "TBD"},
            {"role": "Project Manager", "name": "Engagement PMO", "status": "APPROVED", "date": self.metadata.date},
        ]

        tbl_rev = self.doc.add_table(rows=len(reviewers) + 1, cols=4)
        style_table(tbl_rev, header_bg=self.theme.accent_secondary.lstrip("#"), header_text_color="#FFFFFF")

        rev_headers = ["Role / Tanggung Jawab", "Stakeholder Name", "Status", "Sign-Off Date"]
        for idx, text in enumerate(rev_headers):
            tbl_rev.rows[0].cells[idx].paragraphs[0].text = text
            tbl_rev.rows[0].cells[idx].paragraphs[0].runs[0].font.bold = True

        for r_idx, rev in enumerate(reviewers, start=1):
            cells = tbl_rev.rows[r_idx].cells
            cells[0].paragraphs[0].text = str(rev.get("role", ""))
            cells[1].paragraphs[0].text = str(rev.get("name", ""))
            cells[2].paragraphs[0].text = str(rev.get("status", ""))
            cells[3].paragraphs[0].text = str(rev.get("date", ""))
            self._apply_status_badge(cells[2], str(rev.get("status", "")))

        self.doc.add_page_break()

    # ========================================================================
    # OpenXML Element Generators (Code Callouts, Alerts, Tables, Diagrams)
    # ========================================================================

    def add_code_callout(self, code_text: str, language: str = "") -> None:
        """
        Render a fenced code block into a single-cell OpenXML callout card:
        - Light slate background (#F8FAFC)
        - Left accent bar (#2563EB)
        - Consolas 9pt monospace typography with line spacing
        - <w:cantSplit/>
        """
        tbl = self.doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        row = tbl.rows[0]
        prevent_row_split(row)
        cell = row.cells[0]
        cell.width = Inches(6.8)

        set_cell_background(cell, "F8FAFC")
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)

        # Border styling: Left primary accent stripe, subtle outline
        accent_hex = self.theme.accent_primary.lstrip("#")
        _set_cell_borders(
            cell,
            top={"val": "single", "sz": 4, "color": "E2E8F0"},
            bottom={"val": "single", "sz": 4, "color": "E2E8F0"},
            left={"val": "single", "sz": 24, "color": accent_hex},
            right={"val": "single", "sz": 4, "color": "E2E8F0"},
        )

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15

        if language:
            r_lang = p.add_run(f"// {language.upper()}\n")
            r_lang.font.name = "Consolas"
            r_lang.font.size = Pt(8)
            r_lang.font.bold = True
            r_lang.font.color.rgb = RGBColor(148, 163, 184)

        r_code = p.add_run(code_text.rstrip())
        r_code.font.name = "Consolas"
        r_code.font.size = Pt(9)
        r_code.font.color.rgb = RGBColor(30, 41, 59)

        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(4)

    def add_callout_alert(self, text: str, alert_type: str = "NOTE") -> None:
        """
        Render a GitHub-style alert callout box:
        > [!NOTE] or > [!WARNING] or > [!IMPORTANT]
        """
        type_upper = alert_type.upper()
        colors = {
            "NOTE": {"border": "2563EB", "bg": "EFF6FF", "title": "NOTE"},
            "IMPORTANT": {"border": "7C3AED", "bg": "F5F3FF", "title": "IMPORTANT"},
            "WARNING": {"border": "F59E0B", "bg": "FFFBEB", "title": "WARNING"},
            "CAUTION": {"border": "EF4444", "bg": "FEF2E2", "title": "CAUTION"},
            "TIP": {"border": "10B981", "bg": "ECFDF5", "title": "TIP"},
        }
        cfg = colors.get(type_upper, colors["NOTE"])

        tbl = self.doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        row = tbl.rows[0]
        prevent_row_split(row)
        cell = row.cells[0]
        cell.width = Inches(6.8)

        set_cell_background(cell, cfg["bg"])
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        _set_cell_borders(
            cell,
            top={"val": "single", "sz": 4, "color": "E2E8F0"},
            bottom={"val": "single", "sz": 4, "color": "E2E8F0"},
            left={"val": "single", "sz": 24, "color": cfg["border"]},
            right={"val": "single", "sz": 4, "color": "E2E8F0"},
        )

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.2

        r_badge = p.add_run(f"[{cfg['title']}] ")
        r_badge.font.name = self.theme.font_header
        r_badge.font.size = Pt(9.5)
        r_badge.font.bold = True
        r_badge.font.color.rgb = RGBColor(*parse_hex(cfg["border"]))

        r_body = p.add_run(text)
        r_body.font.name = self.theme.font_body
        r_body.font.size = Pt(9.5)
        r_body.font.color.rgb = RGBColor(*parse_hex(self.theme.text_primary))

        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(4)

    def add_mermaid_diagram(self, mermaid_code: str, caption: str = "System Architecture Diagram") -> None:
        """Compile Mermaid syntax to high-DPI PNG and embed with centered caption."""
        try:
            from src.ppt_engine.diagram_engine import DiagramEngine
            engine = DiagramEngine()
            
            clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", caption.lower())[:30]
            res = engine.compile(
                mermaid_code=mermaid_code,
                diagram_name=f"spec_{clean_name}",
                formats=("png",),
            )
            png_path = res.get("png")
            if png_path and Path(png_path).exists():
                p_img = self.doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(12)
                p_img.paragraph_format.space_after = Pt(4)
                run_img = p_img.add_run()
                run_img.add_picture(str(png_path), width=Inches(6.2))

                p_cap = self.doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(2)
                p_cap.paragraph_format.space_after = Pt(12)
                r_cap = p_cap.add_run(f"Figure: {caption}")
                r_cap.font.name = self.theme.font_body
                r_cap.font.size = Pt(8.5)
                r_cap.font.italic = True
                r_cap.font.color.rgb = RGBColor(100, 116, 139)
                return
        except Exception as e:
            # Fallback to code callout if compilation fails
            self.add_code_callout(mermaid_code, language="mermaid")
            p_err = self.doc.add_paragraph(f"[Diagram rendering fallback: {e}]")
            p_err.runs[0].font.size = Pt(8)
            p_err.runs[0].font.italic = True

    def add_image(self, image_path: Union[str, Path], caption: Optional[str] = None) -> bool:
        """Embed an external or generated image with centered alignment and optional caption."""
        path_obj = Path(image_path)
        if not path_obj.is_absolute():
            if self.base_dir and (self.base_dir / path_obj).exists():
                path_obj = self.base_dir / path_obj
            elif (Path.cwd() / path_obj).exists():
                path_obj = Path.cwd() / path_obj
            elif Path(path_obj).exists():
                path_obj = Path(path_obj)

        if not path_obj.exists():
            self.add_callout_alert(f"Image not found: {image_path}", alert_type="WARNING")
            return False

        try:
            p_img = self.doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(12)
            p_img.paragraph_format.space_after = Pt(4)
            run_img = p_img.add_run()
            run_img.add_picture(str(path_obj), width=Inches(6.2))

            if caption:
                p_cap = self.doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(2)
                p_cap.paragraph_format.space_after = Pt(12)
                r_cap = p_cap.add_run(f"Figure: {caption}")
                r_cap.font.name = self.theme.font_body
                r_cap.font.size = Pt(8.5)
                r_cap.font.italic = True
                r_cap.font.color.rgb = RGBColor(100, 116, 139)
            return True
        except Exception as e:
            self.add_callout_alert(f"Failed to embed image '{image_path}': {e}", alert_type="WARNING")
            return False

    def add_markdown_table(self, rows_data: List[List[str]]) -> None:
        """Parse pipe-table rows and apply unified enterprise table styling."""
        if not rows_data:
            return

        cols = len(rows_data[0])
        table = self.doc.add_table(rows=len(rows_data), cols=cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        style_table(
            table,
            header_bg=self.theme.accent_primary.lstrip("#"),
            header_text_color="#FFFFFF",
            zebra_even_bg="#F8FAFC",
            zebra_odd_bg="#FFFFFF",
        )

        for r_idx, row in enumerate(rows_data):
            for c_idx, val in enumerate(row):
                if c_idx < cols:
                    cell = table.rows[r_idx].cells[c_idx]
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.15
                    self._format_inline_text(p, val.strip())

                    if r_idx == 0:
                        for run in p.runs:
                            run.font.bold = True
                    else:
                        self._apply_status_badge(cell, val.strip())

        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(6)

    def _apply_status_badge(self, cell: _Cell, text: str) -> None:
        """Highlight scenario status badges: PASSED, FAILED, PENDING, BLOCKED."""
        clean = text.strip().upper()
        badges = {
            "PASSED": {"bg": "DCFCE7", "color": "15803D"},   # Green
            "PASS": {"bg": "DCFCE7", "color": "15803D"},
            "APPROVED": {"bg": "DCFCE7", "color": "15803D"},
            "FAILED": {"bg": "FEE2E2", "color": "B91C1C"},   # Red
            "FAIL": {"bg": "FEE2E2", "color": "B91C1C"},
            "REJECTED": {"bg": "FEE2E2", "color": "B91C1C"},
            "PENDING": {"bg": "FEF3C7", "color": "B45309"},  # Amber
            "IN PROGRESS": {"bg": "FEF3C7", "color": "B45309"},
            "BLOCKED": {"bg": "F3E8FF", "color": "6B21A8"},  # Purple
        }
        if clean in badges:
            cfg = badges[clean]
            set_cell_background(cell, cfg["bg"])
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.bold = True
                    r.font.size = Pt(9)
                    r.font.color.rgb = RGBColor(*parse_hex(cfg["color"]))

    # ========================================================================
    # Inline Markdown Parser (Bold, Italic, Monospace Code, Links)
    # ========================================================================

    def _format_inline_text(self, paragraph, raw_text: str) -> None:
        """Parse inline Markdown formatting tokens (**bold**, *italic*, `code`)."""
        pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))")
        tokens = pattern.split(raw_text)

        for tok in tokens:
            if not tok:
                continue
            if tok.startswith("`") and tok.endswith("`") and len(tok) >= 2:
                r = paragraph.add_run(tok[1:-1])
                r.font.name = "Consolas"
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(194, 65, 12)  # Terracotta accent
            elif tok.startswith("**") and tok.endswith("**") and len(tok) >= 4:
                r = paragraph.add_run(tok[2:-2])
                r.font.name = self.theme.font_body
                r.font.size = Pt(10)
                r.font.bold = True
            elif tok.startswith("*") and tok.endswith("*") and len(tok) >= 2:
                r = paragraph.add_run(tok[1:-1])
                r.font.name = self.theme.font_body
                r.font.size = Pt(10)
                r.font.italic = True
            elif tok.startswith("[") and "](" in tok and tok.endswith(")"):
                m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", tok)
                if m:
                    label, url = m.groups()
                    r = paragraph.add_run(label)
                    r.font.name = self.theme.font_body
                    r.font.size = Pt(10)
                    r.font.underline = True
                    r.font.color.rgb = RGBColor(*parse_hex(self.theme.accent_secondary))
            else:
                r = paragraph.add_run(tok)
                r.font.name = self.theme.font_body
                r.font.size = Pt(10)
                r.font.color.rgb = RGBColor(*parse_hex(self.theme.text_primary))

    # ========================================================================
    # Markdown Block Parser
    # ========================================================================

    def parse_markdown_content(self, md_content: str) -> None:
        """Parse structured Markdown string and render AST nodes into the document."""
        lines = md_content.splitlines()
        idx = 0
        total_lines = len(lines)

        in_code_block = False
        code_buffer: List[str] = []
        code_lang = ""

        in_table = False
        table_buffer: List[List[str]] = []

        while idx < total_lines:
            line = lines[idx]
            stripped = line.strip()

            # 1. Code Block Processing (```lang ... ```)
            if stripped.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_lang = stripped.lstrip("`").strip()
                    code_buffer = []
                else:
                    in_code_block = False
                    full_code = "\n".join(code_buffer)
                    if code_lang.lower() == "mermaid":
                        self.add_mermaid_diagram(full_code)
                    else:
                        self.add_code_callout(full_code, language=code_lang)
                    code_buffer = []
                idx += 1
                continue

            if in_code_block:
                code_buffer.append(line)
                idx += 1
                continue

            # 2. Markdown Pipe Tables (| col1 | col2 |)
            if stripped.startswith("|") and stripped.endswith("|"):
                row_cells = [c.strip() for c in stripped.strip("|").split("|")]
                # Ignore separator row (|---|---|)
                if not all(re.match(r"^:?-+:?$", c) for c in row_cells if c):
                    table_buffer.append(row_cells)
                in_table = True
                idx += 1
                continue
            else:
                if in_table:
                    self.add_markdown_table(table_buffer)
                    table_buffer = []
                    in_table = False

            # Empty lines
            if not stripped:
                idx += 1
                continue

            # 3. Headings (# H1, ## H2, ### H3, #### H4)
            if stripped.startswith("#"):
                m = re.match(r"^(#{1,4})\s+(.+)$", stripped)
                if m:
                    level_hashes, title_text = m.groups()
                    level = len(level_hashes)
                    # Section page break for H1 if not at very beginning of section
                    if level == 1 and len(self.doc.paragraphs) > 5:
                        self.doc.add_page_break()
                    h = self.doc.add_heading(level=level)
                    self._format_inline_text(h, title_text)
                    idx += 1
                    continue

            # 4. GitHub-Style Alert / Callout Quotes (> [!NOTE])
            if stripped.startswith(">"):
                quote_text = stripped.lstrip(">").strip()
                alert_m = re.match(r"^\[!(NOTE|IMPORTANT|WARNING|CAUTION|TIP)\]\s*(.*)$", quote_text, re.IGNORECASE)
                if alert_m:
                    alert_type, alert_body = alert_m.groups()
                    idx += 1
                    body_lines = [alert_body] if alert_body else []
                    while idx < total_lines and lines[idx].strip().startswith(">"):
                        body_lines.append(lines[idx].strip().lstrip(">").strip())
                        idx += 1
                    self.add_callout_alert(" ".join(body_lines), alert_type=alert_type)
                    continue
                else:
                    self.add_callout_alert(quote_text, alert_type="NOTE")
                    idx += 1
                    continue

            # 5. Bullet & Numbered Lists
            if stripped.startswith(("- ", "* ", "• ")):
                p = self.doc.add_paragraph(style="List Bullet")
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.15
                self._format_inline_text(p, stripped[2:].strip())
                idx += 1
                continue

            num_m = re.match(r"^(\d+)\.\s+(.+)$", stripped)
            if num_m:
                _, num_text = num_m.groups()
                p = self.doc.add_paragraph(style="List Number")
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.15
                self._format_inline_text(p, num_text.strip())
                idx += 1
                continue

            # 6. Markdown Images (![Caption](path/to/image.png))
            img_m = re.match(r"^!\[(.*?)\]\((.+?)\)$", stripped)
            if img_m:
                caption_text, img_rel_path = img_m.groups()
                img_clean_path = img_rel_path.strip().split(" ")[0].strip("\"'")
                self.add_image(img_clean_path, caption=caption_text or None)
                idx += 1
                continue

            # 7. Horizontal Rules (---)
            if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
                p_hr = self.doc.add_paragraph()
                p_hr.paragraph_format.space_before = Pt(8)
                p_hr.paragraph_format.space_after = Pt(8)
                r_hr = p_hr.add_run("―" * 54)
                r_hr.font.size = Pt(8)
                r_hr.font.color.rgb = RGBColor(226, 232, 240)
                idx += 1
                continue

            # 7. Standard Paragraph
            p = self.doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.2
            self._format_inline_text(p, stripped)
            idx += 1

        # Flush any trailing table
        if in_table and table_buffer:
            self.add_markdown_table(table_buffer)

    def save(
        self,
        output_path: Union[str, Path],
        engagement_context: Optional[Any] = None,
    ) -> Path:
        """Save the compiled Word document to disk, substituting slugs if engagement_context is provided."""
        if engagement_context is not None:
            from src.core.slug_registry import substitute_slugs_in_document
            substitute_slugs_in_document(self.doc, engagement_context)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(out))
        return out


# ============================================================================
# High-Level Orchestration Helpers
# ============================================================================

def compile_markdown_to_docx(
    markdown_path: Union[str, Path],
    output_path: Union[str, Path],
    theme: str = "metrodata",
    metadata: Optional[SpecMetadata] = None,
    engagement_context: Optional[Any] = None,
) -> Path:
    """Compile a single Markdown file into a styled Word deliverable."""
    md_p = Path(markdown_path)
    if not md_p.exists():
        raise FileNotFoundError(f"Markdown spec file not found: {markdown_path}")

    raw_content = md_p.read_text(encoding="utf-8")

    # Extract YAML frontmatter if present
    extracted_meta = metadata or SpecMetadata()
    if raw_content.startswith("---"):
        parts = raw_content.split("---", 2)
        if len(parts) >= 3:
            fm = yaml.safe_load(parts[1]) or {}
            if isinstance(fm, dict):
                extracted_meta.title = fm.get("title", extracted_meta.title)
                extracted_meta.subtitle = fm.get("subtitle", extracted_meta.subtitle)
                extracted_meta.client = fm.get("client", extracted_meta.client)
                extracted_meta.vendor = fm.get("vendor", extracted_meta.vendor)
                extracted_meta.version = fm.get("version", extracted_meta.version)
                extracted_meta.date = fm.get("date", extracted_meta.date)
                extracted_meta.confidentiality = fm.get("confidentiality", extracted_meta.confidentiality)
                extracted_meta.document_control = fm.get("document_control", extracted_meta.document_control)
                extracted_meta.reviewers = fm.get("reviewers", extracted_meta.reviewers)
            raw_content = parts[2]

    compiler = SpecCompiler(theme=theme, metadata=extracted_meta, base_dir=md_p.parent)
    compiler.add_cover_page()
    compiler.add_governance_section()
    compiler.parse_markdown_content(raw_content)
    return compiler.save(output_path, engagement_context=engagement_context)


def compile_spec_directory(
    spec_dir: Union[str, Path],
    output_path: Union[str, Path],
    theme: str = "metrodata",
    metadata_file: Optional[str] = "00_metadata.yaml",
    engagement_context: Optional[Any] = None,
) -> Path:
    """
    Compile a modular directory of Markdown files (e.g. 01_*.md, 02_*.md)
    into a unified master specification Word deliverable.
    """
    s_dir = Path(spec_dir)
    if not s_dir.exists() or not s_dir.is_dir():
        raise NotADirectoryError(f"Specification directory not found: {spec_dir}")

    # Load metadata file if present
    meta = SpecMetadata()
    meta_path = s_dir / (metadata_file or "00_metadata.yaml")
    if meta_path.exists():
        fm = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        if isinstance(fm, dict):
            meta.title = fm.get("title", meta.title)
            meta.subtitle = fm.get("subtitle", meta.subtitle)
            meta.client = fm.get("client", meta.client)
            meta.vendor = fm.get("vendor", meta.vendor)
            meta.version = fm.get("version", meta.version)
            meta.date = fm.get("date", meta.date)
            meta.confidentiality = fm.get("confidentiality", meta.confidentiality)
            meta.document_control = fm.get("document_control", meta.document_control)
            meta.reviewers = fm.get("reviewers", meta.reviewers)

    compiler = SpecCompiler(theme=theme, metadata=meta, base_dir=s_dir)
    compiler.add_cover_page()
    compiler.add_governance_section()

    # Gather ordered markdown files (excluding metadata files)
    md_files = sorted([f for f in s_dir.glob("*.md") if not f.name.startswith("00_")])
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        compiler.parse_markdown_content(content)

    return compiler.save(output_path, engagement_context=engagement_context)
