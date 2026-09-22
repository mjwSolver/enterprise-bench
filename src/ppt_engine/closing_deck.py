"""
Project Closing Deck Builder Subsystem
======================================
Builds the canonical 9-slide Executive Project Closing & Maintenance Transition
presentation deck for enterprise cloud modernizations, conforming to consulting
frameworks, the 60-30-10 palette distribution, and geometric integrity rules:

  Slide 01: Cover Slide (Dual vertical brand stripes, clean typographic metadata)
  Slide 02: Table of Contents / Executive Agenda (6 numbered consulting cards)
  Slide 03: Ruang Lingkup / Scope Review (6 capability cards detailing delivered phases)
  Slide 04: Contractual Deliverables Register (19 delivered artifacts across 4 categories)
  Slide 05: Project Closing Checklist & Repository Access (Vector gate matrix + credential cards)
  Slide 06: Transition to Maintenance Phase (Bucket mandays scheme, rollover terms & scope)
  Slide 07: Maintenance Contacts & Request Flow (4-stage process chevron + primary contacts)
  Slide 08: Maintenance Deliverables (Recaps, timesheets, and technical documentation)
  Slide 09: Thank You & Practice Contacts (Brand emblem lockup & leadership contacts)

Strictly enforces:
  - Zero overlapping top lines on rounded cards (MSO_SHAPE.RECTANGLE on all striped containers).
  - Unified title and subtitle frame (single text frame, space_before = Pt(10)).
  - Clean typographic metadata on cover (zero boxed containers, no cover footer/pagination).
  - Synchronized bottom pagination ('02 / 09' to '09 / 09').
  - 100% native vector shapes (no static image tables).
  - Hanging indents on all bullet points (marL="288000" indent="-288000").
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from src.ppt_engine.consulting_archetypes import (
    ConsultingDeckBuilder,
    add_card,
    add_card_with_top_stripe,
    add_slide_footer,
    add_slide_header,
    add_slide_with_background,
    build_cover_slide,
    create_presentation,
)
from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb

logger = logging.getLogger(__name__)


def _add_status_pill(
    slide: Any,
    theme: Theme,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    status: str,
    font_size_pt: float = 9.0,
    override_color_key: Optional[str] = None,
) -> Any:
    """Renders a standalone rounded status badge pill with theme-resolved colors."""
    status_lower = status.lower().strip()
    if override_color_key:
        if override_color_key == "danger":
            bg_key, text_key = ("badge_red_fill", "badge_red_text")
        elif override_color_key == "warning":
            bg_key, text_key = ("badge_amber_fill", "badge_amber_text")
        elif override_color_key == "success":
            bg_key, text_key = ("badge_green_fill", "badge_green_text")
        else:
            bg_key, text_key = ("badge_blue_fill", "badge_blue_text")
    elif status_lower in ("done", "yes", "delivered", "signed-off", "completed"):
        bg_key, text_key = ("badge_green_fill", "badge_green_text")
    elif status_lower in ("partial", "in progress", "active", "review"):
        bg_key, text_key = ("badge_amber_fill", "badge_amber_text")
    elif status_lower in ("tbd", "pending", "scheduled", "draft"):
        bg_key, text_key = ("badge_blue_fill", "badge_blue_text")
    elif status_lower in ("no", "blocked", "critical", "failed"):
        bg_key, text_key = ("badge_red_fill", "badge_red_text")
    else:
        bg_key, text_key = theme.resolve_status_badge_keys(status)

    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE
    pill = slide.shapes.add_shape(shape_type, left, top, width, height)
    pill.shadow.inherit = False
    pill.fill.solid()
    pill.fill.fore_color.rgb = theme.get_rgb(bg_key)
    pill.line.fill.background()

    tf = pill.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = status.upper()
    p.alignment = PP_ALIGN.CENTER
    p.font.name = theme.font_family
    p.font.size = Pt(font_size_pt)
    p.font.bold = True
    p.font.color.rgb = theme.get_rgb(text_key)
    return pill


def _add_icon_safe(
    slide: Any,
    icon_name: str,
    left: Inches,
    top: Inches,
    size: Inches,
    color: Any,
    theme: Theme,
) -> Optional[Any]:
    """Safely retrieves a brand-harmonized icon via IconEngine and adds it to the slide."""
    try:
        from src.ppt_engine.icon_engine import _default_engine
        png_path = _default_engine.get_icon(icon_name, color=color, theme=theme)
        if png_path and Path(png_path).exists():
            pic = slide.shapes.add_picture(str(png_path), left, top, width=size, height=size)
            return pic
    except Exception as e:
        logger.debug(f"Failed to add icon {icon_name}: {e}")
    return None


def _add_bullet_paragraph(
    tf: Any,
    text: str,
    font_name: str,
    font_size_pt: float = 11.0,
    font_color: Optional[RGBColor] = None,
    space_before_pt: float = 6.0,
    bullet_char: str = "•",
) -> Any:
    """
    Appends a bullet paragraph with an OpenXML DrawingML hanging indent (marL/indent)
    and native bullet formatting for clean alignment across native and headless renderers.
    """
    from pptx.oxml.xmlchemy import OxmlElement
    from pptx.oxml.ns import qn

    p = tf.add_paragraph()
    clean_text = text.lstrip("•\t -*").strip()
    p.text = clean_text

    # Strip CSS fallback lists if present (e.g. "Calibri, Helvetica, Arial...")
    clean_font = font_name.split(",")[0].strip().strip('"\'') if font_name else "Calibri"
    if not clean_font:
        clean_font = "Calibri"
    p.font.name = clean_font
    p.font.size = Pt(font_size_pt)
    if font_color:
        p.font.color.rgb = font_color
    p.space_before = Pt(space_before_pt)

    # DrawingML Hanging Indent: marL="288000" (0.20 in), indent="-288000"
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", "288000")
    pPr.set("indent", "-288000")

    # In ECMA-376 PresentationML, buClrTx, buSzPct, buFont, and buChar MUST precede defRPr!
    buClrTx = OxmlElement("a:buClrTx")
    buSzPct = OxmlElement("a:buSzPct")
    buSzPct.set("val", "100000")
    buFont = OxmlElement("a:buFont")
    buFont.set("typeface", "Arial")
    buChar = OxmlElement("a:buChar")
    buChar.set("char", bullet_char)

    elems = [buClrTx, buSzPct, buFont, buChar]
    defRPr = pPr.find(qn("a:defRPr"))
    if defRPr is not None:
        idx = pPr.index(defRPr)
        for offset, el in enumerate(elems):
            pPr.insert(idx + offset, el)
    else:
        for el in elems:
            pPr.append(el)

    return p


class ClosingDeckBuilder:
    """High-level builder for generating 9-slide Project Closing & Maintenance Transition decks."""

    def __init__(
        self,
        theme: Union[str, Theme] = "metrodata",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = theme

        self.prs = create_presentation(self.theme)
        self.config: Dict[str, Any] = config or {}
        self.metadata: Dict[str, Any] = self.config.get("metadata", {})

    @classmethod
    def from_yaml(
        cls,
        yaml_path: Union[str, Path],
        theme_override: Optional[str] = None,
    ) -> ClosingDeckBuilder:
        """Instantiate builder from a YAML deck specification."""
        p = Path(yaml_path)
        if not p.exists():
            raise FileNotFoundError(f"Deck configuration file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        theme_name = theme_override or config.get("theme", "metrodata")
        return cls(theme=theme_name, config=config)

    # -------------------------------------------------------------------------
    # Slide 1: Cover Slide
    # -------------------------------------------------------------------------
    def build_cover(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        return build_cover_slide(
            prs=self.prs,
            theme=self.theme,
            title=d.get(
                "title",
                self.metadata.get(
                    "project_name",
                    "DATA APPLICATION FOR FINANCIAL ANALYTICS WITH SNOWFLAKE",
                ),
            ),
            subtitle=d.get("subtitle", "Closing & Transition to Maintenance"),
            client=d.get("client", self.metadata.get("client_name", "PT Toyota Tsusho Indonesia")),
            vendor=d.get("vendor", self.metadata.get("vendor_name", "PT Mitra Integrasi Informatika")),
            product=d.get("product", "Snowflake AI Data Cloud"),
            date_str=d.get("date_str", self.metadata.get("report_date", "01 September 2026")),
            tracker=d.get("tracker", "PROJECT CLOSING & MAINTENANCE TRANSITION"),
            client_sublabel=d.get("client_sublabel", "Steering Committee & Executive Sponsors"),
            vendor_sublabel=d.get("vendor_sublabel", "Agus Suhanto, Project Manager, MII"),
        )

    # -------------------------------------------------------------------------
    # Slide 2: Table of Contents / Executive Agenda
    # -------------------------------------------------------------------------
    def build_agenda(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "EXECUTIVE AGENDA"),
            action_title=d.get("title", "Project Closing & Maintenance Transition Agenda"),
            subtitle=d.get(
                "subtitle",
                "Structured review of delivered scope, contractual deliverables, closeout sign-off gates, and maintenance operating model.",
            ),
        )

        agenda_items = d.get(
            "agenda_items",
            [
                {
                    "num": "01",
                    "title": "Ruang Lingkup",
                    "subtitle": "Scope Review & Capabilities",
                    "accent": "accent",
                    "bullets": [
                        "Review of 7 contractual delivery phases",
                        "Snowflake data modeling & Streamlit architecture",
                        "GenAI narration via Cortex Complete",
                    ],
                },
                {
                    "num": "02",
                    "title": "Deliverables",
                    "subtitle": "Contractual Artifact Inventory",
                    "accent": "accent_teal",
                    "bullets": [
                        "100% completion across 19 required deliverables",
                        "FSD (8 modules), TSD, PMP & Test artifacts",
                        "Production codebase & deployment manifests",
                    ],
                },
                {
                    "num": "03",
                    "title": "Closing Checklist",
                    "subtitle": "Sign-off Gates & Artifact Access",
                    "accent": "success",
                    "bullets": [
                        "Formal sign-off matrix across 8 closeout gates",
                        "Zero open Sev 1/2 defects & RAID closure",
                        "Secure repository package & CSS link",
                    ],
                },
                {
                    "num": "04",
                    "title": "Maintenance Phase",
                    "subtitle": "Bucket Mandays Operating Model",
                    "accent": "accent_blue",
                    "bullets": [
                        "30 mandays annual support allocation",
                        "0.5 manday minimum metering increment",
                        "100% rollover policy into following contract year",
                    ],
                },
                {
                    "num": "05",
                    "title": "Contacts & Flow",
                    "subtitle": "Operational Request Lifecycle",
                    "accent": "warning",
                    "bullets": [
                        "4-stage ticket workflow from submission to UAT",
                        "Primary technical contacts (Adam N. & Vicko B.)",
                        "Dedicated WhatsApp group & email ticketing",
                    ],
                },
                {
                    "num": "06",
                    "title": "Maintenance Deliverables",
                    "subtitle": "Audit & Reporting Governance",
                    "accent": "accent_purple",
                    "bullets": [
                        "Monthly mandays consumption recap ledger",
                        "Granular developer timesheets per ticket",
                        "Root-cause analysis & CR documentation",
                    ],
                },
            ],
        )

        cols = 3
        card_w = Inches(3.70)
        card_h = Inches(2.30)
        gap_x = Inches(0.31)
        gap_y = Inches(0.32)
        start_x = Inches(0.80)
        start_y = Inches(1.85)

        default_agenda_icons = ["compass", "package-check", "file-signature", "shield-check", "git-pull-request", "bar-chart-3"]

        for i, item in enumerate(agenda_items[:6]):
            col = i % cols
            row = i // cols
            cx = start_x + col * (card_w + gap_x)
            cy = start_y + row * (card_h + gap_y)

            accent_key = item.get("accent", "accent")
            accent_rgb = self.theme.get_rgb(accent_key, "#0052CC")

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=cx,
                top=cy,
                width=card_w,
                height=card_h,
                accent_rgb=accent_rgb,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.06,
            )

            # Icon at top right of agenda card
            icon_name = item.get("icon") or default_agenda_icons[i % len(default_agenda_icons)]
            icon_dim = Inches(0.32)
            _add_icon_safe(
                slide=slide,
                icon_name=icon_name,
                left=cx + card_w - icon_dim - Inches(0.18),
                top=cy + Inches(0.14),
                size=icon_dim,
                color=accent_rgb,
                theme=self.theme,
            )

            tb = slide.shapes.add_textbox(
                cx + Inches(0.20),
                cy + Inches(0.14),
                card_w - icon_dim - Inches(0.42),
                card_h - Inches(0.24),
            )
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            # Number badge and title
            p_num = tf.paragraphs[0]
            p_num.text = f"{item.get('num', f'0{i+1}')}  "
            p_num.font.name = self.theme.font_family_header
            p_num.font.size = Pt(16.0)
            p_num.font.bold = True
            p_num.font.color.rgb = accent_rgb

            run_title = p_num.add_run()
            run_title.text = item.get("title", "")
            run_title.font.name = self.theme.font_family_header
            run_title.font.size = Pt(13.0)
            run_title.font.bold = True
            run_title.font.color.rgb = self.theme.get_rgb("primary")

            if item.get("subtitle"):
                p_sub = tf.add_paragraph()
                p_sub.text = item.get("subtitle", "")
                p_sub.font.name = self.theme.font_family
                p_sub.font.size = Pt(11.0)
                p_sub.font.color.rgb = self.theme.get_rgb("secondary")
                p_sub.space_before = Pt(3)

            for b in item.get("bullets", []):
                _add_bullet_paragraph(
                    tf=tf,
                    text=b,
                    font_name=self.theme.font_family,
                    font_size_pt=11.0,
                    font_color=self.theme.get_rgb("secondary"),
                    space_before_pt=4.0,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=9)
        return slide

    # -------------------------------------------------------------------------
    # Slide 3: Ruang Lingkup / Scope Review
    # -------------------------------------------------------------------------
    def build_scope_review(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "RUANG LINGKUP | SCOPE REVIEW"),
            action_title=d.get("title", "Delivered Scope & Multi-Workstream Capability Architecture"),
            subtitle=d.get(
                "subtitle",
                "Comprehensive execution across 7 core contractual workstreams from architectural planning to production cutover.",
            ),
        )

        pillars = d.get(
            "pillars",
            [
                {
                    "title": "Initiation & Planning",
                    "phase": "Phase 1: Architecture Baseline",
                    "accent": "accent",
                    "status": "Done",
                    "bullets": [
                        "In-depth architectural assessment, source schema analysis & sizing",
                        "Project Management Plan (PMP) & Project Charter alignment",
                        "Governance cadence, RACI matrix, and communication baseline",
                    ],
                },
                {
                    "title": "Snowflake Core & Modeling",
                    "phase": "Phase 2: Cloud Infrastructure",
                    "accent": "accent_blue",
                    "status": "Delivered",
                    "bullets": [
                        "Dedicated Snowflake subscription provisioning & security RBAC",
                        "Multi-tier dimensional data modeling (Raw, Stage, Mart layers)",
                        "Automated Excel upload pipeline with server-side validation",
                    ],
                },
                {
                    "title": "Financial Streamlit Application",
                    "phase": "Phase 3: Analytics Frontend",
                    "accent": "accent_teal",
                    "status": "Done",
                    "bullets": [
                        "8 financial modules: Sales, GP, Opex, PBT, TVA ROIC, AR, Stock Aging",
                        "Executive Summary dashboard with consolidated KPI scorecards",
                        "Interactive multi-dimensional slicing, dynamic charts & exports",
                    ],
                },
                {
                    "title": "Cortex GenAI Narration",
                    "phase": "Phase 4: Predictive Intelligence",
                    "accent": "accent_purple",
                    "status": "Done",
                    "bullets": [
                        "Automated monthly narrative commentary engine via Cortex Complete",
                        "Context-aware financial variance analysis & operational driver insights",
                        "Air-gapped enterprise LLM inference strictly within Snowflake perimeter",
                    ],
                },
                {
                    "title": "Testing & Quality Assurance",
                    "phase": "Phase 5: Verification & SIT/UAT",
                    "accent": "warning",
                    "status": "Done",
                    "bullets": [
                        "System Integration Testing (SIT) across data pipelines and UI models",
                        "Formal User Acceptance Testing (UAT) with 1x revision cycle completed",
                        "100% defect remediation verified prior to production cutover",
                    ],
                },
                {
                    "title": "Handover, Go-Live & Warranty",
                    "phase": "Phase 6 & 7: Cutover & Closure",
                    "accent": "success",
                    "status": "Done",
                    "bullets": [
                        "Production cutover & comprehensive technical knowledge transfer",
                        "End-user manuals, administrator guides, and signed BAST forms",
                        "2-week intensive warranty period & operational stabilization",
                    ],
                },
            ],
        )

        cols = 3
        card_w = Inches(3.70)
        card_h = Inches(2.30)
        gap_x = Inches(0.31)
        gap_y = Inches(0.32)
        start_x = Inches(0.80)
        start_y = Inches(1.85)

        default_pillar_icons = ["compass", "cloud", "layout-dashboard", "sparkles", "shield-check", "check-circle-2"]

        for i, p in enumerate(pillars[:6]):
            col = i % cols
            row = i // cols
            cx = start_x + col * (card_w + gap_x)
            cy = start_y + row * (card_h + gap_y)

            accent_key = p.get("accent", "accent")
            accent_rgb = self.theme.get_rgb(accent_key, "#0052CC")

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=cx,
                top=cy,
                width=card_w,
                height=card_h,
                accent_rgb=accent_rgb,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.06,
            )

            # Icon badge on the left of card header
            icon_name = p.get("icon") or default_pillar_icons[i % len(default_pillar_icons)]
            icon_dim = Inches(0.30)
            _add_icon_safe(
                slide=slide,
                icon_name=icon_name,
                left=cx + Inches(0.16),
                top=cy + Inches(0.14),
                size=icon_dim,
                color=accent_rgb,
                theme=self.theme,
            )

            # Top right status pill
            status_text = p.get("status", "DONE")
            pill_w = Inches(0.95)
            pill_h = Inches(0.26)
            _add_status_pill(
                slide=slide,
                theme=self.theme,
                left=cx + card_w - pill_w - Inches(0.14),
                top=cy + Inches(0.14),
                width=pill_w,
                height=pill_h,
                status=status_text,
                font_size_pt=11.0,
            )

            tb = slide.shapes.add_textbox(
                cx + Inches(0.52),
                cy + Inches(0.10),
                card_w - pill_w - Inches(0.70),
                Inches(0.54),
            )
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p_title = tf.paragraphs[0]
            p_title.text = p.get("title", "")
            p_title.font.name = self.theme.font_family_header
            p_title.font.size = Pt(12.0)
            p_title.font.bold = True
            p_title.font.color.rgb = self.theme.get_rgb("primary")

            if p.get("phase"):
                p_phase = tf.add_paragraph()
                p_phase.text = p.get("phase", "").upper()
                p_phase.font.name = self.theme.font_family
                p_phase.font.size = Pt(11.0)
                p_phase.font.bold = True
                p_phase.font.color.rgb = accent_rgb
                p_phase.space_before = Pt(2)

            # Bullets
            tb_b = slide.shapes.add_textbox(
                cx + Inches(0.16),
                cy + Inches(0.70),
                card_w - Inches(0.32),
                card_h - Inches(0.78),
            )
            tf_b = tb_b.text_frame
            tf_b.word_wrap = True
            tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0

            for b_idx, b in enumerate(p.get("bullets", [])):
                _add_bullet_paragraph(
                    tf=tf_b,
                    text=b,
                    font_name=self.theme.font_family,
                    font_size_pt=11.0,
                    font_color=self.theme.get_rgb("secondary"),
                    space_before_pt=4.0 if b_idx > 0 else 0.0,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=9)
        return slide

    # -------------------------------------------------------------------------
    # Slide 4: Contractual Deliverables Register
    # -------------------------------------------------------------------------
    def build_deliverables_register(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "DELIVERABLES REGISTER"),
            action_title=d.get("title", "Contractual Deliverables & Handover Artifact Inventory"),
            subtitle=d.get(
                "subtitle",
                "100% completion across all 19 contractual deliverables spanning documentation, codebases, and test reports.",
            ),
        )

        # Top KPI bar
        kpis = [
            {"label": "CONTRACT DELIVERABLES", "value": "19 / 19", "desc": "100% Delivered", "accent": "accent"},
            {"label": "FSD MODULE SPECS", "value": "8 Modules", "desc": "Signed-off Specifications", "accent": "accent_teal"},
            {"label": "QUALITY & TEST SUITES", "value": "SIT & UAT", "desc": "Zero Sev 1/2 Defects", "accent": "success"},
            {"label": "HANDOVER STATUS", "value": "BAST 1 & 2", "desc": "Signed Off by [CLIENT_SHORT_NAME] & MII", "accent": "accent_purple"},
        ]

        kpi_w = Inches(2.75)
        kpi_h = Inches(0.74)
        gap_kpi = Inches(0.24)
        start_x = Inches(0.80)
        top_kpi = Inches(1.80)

        for i, kpi in enumerate(kpis):
            kx = start_x + i * (kpi_w + gap_kpi)
            acc = self.theme.get_rgb(kpi["accent"])
            add_card(
                slide=slide,
                theme=self.theme,
                left=kx,
                top=top_kpi,
                width=kpi_w,
                height=kpi_h,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            # Left accent pill bar
            pbar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, kx, top_kpi, Inches(0.045), kpi_h)
            pbar.shadow.inherit = False
            pbar.fill.solid()
            pbar.fill.fore_color.rgb = acc
            pbar.line.fill.background()

            tb = slide.shapes.add_textbox(kx + Inches(0.12), top_kpi + Inches(0.06), kpi_w - Inches(0.20), kpi_h - Inches(0.10))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p_val = tf.paragraphs[0]
            p_val.text = kpi["value"]
            p_val.font.name = self.theme.font_family_header
            p_val.font.size = Pt(14.0)
            p_val.font.bold = True
            p_val.font.color.rgb = self.theme.get_rgb("primary")

            p_lbl = tf.add_paragraph()
            p_lbl.text = f"{kpi['label']}  •  {kpi['desc']}"
            p_lbl.font.name = self.theme.font_family
            p_lbl.font.size = Pt(11.0)
            p_lbl.font.bold = True
            p_lbl.font.color.rgb = self.theme.get_rgb("secondary")
            p_lbl.space_before = Pt(2)

        # 4 Category Columns below KPI bar
        categories = d.get(
            "categories",
            [
                {
                    "title": "Initiation & Governance",
                    "accent": "accent",
                    "count": "5 Artifacts",
                    "items": [
                        {"name": "Kick-off Material", "fmt": "PPTX", "status": "Delivered"},
                        {"name": "Project Charter", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "Stakeholders Register", "fmt": "XLSX", "status": "Delivered"},
                        {"name": "Project Management Plan (PMP)", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "Minutes of Meeting (MoM)", "fmt": "DOCX", "status": "Delivered"},
                    ],
                },
                {
                    "title": "Specifications & Code",
                    "accent": "accent_teal",
                    "count": "5 Artifacts",
                    "items": [
                        {"name": "Functional Spec Docs (8 modules)", "fmt": "8 DOCX", "status": "Delivered"},
                        {"name": "Technical Spec Document (TSD)", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "Streamlit Production App & Code", "fmt": "CODE", "status": "Delivered"},
                        {"name": "Streamlit Development App & Code", "fmt": "CODE", "status": "Delivered"},
                        {"name": "Snowflake Cloud Provisioning", "fmt": "CLOUD", "status": "Delivered"},
                    ],
                },
                {
                    "title": "Testing & Quality",
                    "accent": "success",
                    "count": "4 Artifacts",
                    "items": [
                        {"name": "Unit Testing Documents", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "System Integration Testing (SIT)", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "User Acceptance Testing (UAT)", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "Defect Remediation Register", "fmt": "XLSX", "status": "Delivered"},
                    ],
                },
                {
                    "title": "Operations & Closure",
                    "accent": "accent_purple",
                    "count": "5 Artifacts",
                    "items": [
                        {"name": "User Operating Guide", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "System Administrator Guide", "fmt": "DOCX", "status": "Delivered"},
                        {"name": "Weekly Progress Reports Archive", "fmt": "PPTX/XLSX", "status": "Delivered"},
                        {"name": "Change Request Logs (CR)", "fmt": "DOCX/XLSX", "status": "Delivered"},
                        {"name": "Project Risk & Issue Registers", "fmt": "XLSX", "status": "Delivered"},
                    ],
                },
            ],
        )

        col_w = Inches(2.75)
        col_h = Inches(4.20)
        top_cols = Inches(2.65)

        for i, cat in enumerate(categories[:4]):
            cx = start_x + i * (col_w + gap_kpi)
            acc = self.theme.get_rgb(cat.get("accent", "accent"))

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=cx,
                top=top_cols,
                width=col_w,
                height=col_h,
                accent_rgb=acc,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.05,
            )

            # Header inside column card
            tb_ch = slide.shapes.add_textbox(cx + Inches(0.14), top_cols + Inches(0.10), col_w - Inches(0.28), Inches(0.52))
            tf_ch = tb_ch.text_frame
            tf_ch.word_wrap = True
            tf_ch.margin_left = tf_ch.margin_right = tf_ch.margin_top = tf_ch.margin_bottom = 0

            p_ct = tf_ch.paragraphs[0]
            p_ct.text = cat.get("title", "")
            p_ct.font.name = self.theme.font_family_header
            p_ct.font.size = Pt(12.0)
            p_ct.font.bold = True
            p_ct.font.color.rgb = self.theme.get_rgb("primary")

            p_cc = tf_ch.add_paragraph()
            p_cc.text = cat.get("count", "").upper()
            p_cc.font.name = self.theme.font_family
            p_cc.font.size = Pt(11.0)
            p_cc.font.bold = True
            p_cc.font.color.rgb = acc
            p_cc.space_before = Pt(2)

            # Items
            item_y = top_cols + Inches(0.68)
            item_h = Inches(0.62)
            item_gap = Inches(0.06)

            for j, item in enumerate(cat.get("items", [])):
                iy = item_y + j * (item_h + item_gap)
                if iy + item_h > top_cols + col_h:
                    break

                # Item row subcard
                add_card(
                    slide=slide,
                    theme=self.theme,
                    left=cx + Inches(0.10),
                    top=iy,
                    width=col_w - Inches(0.20),
                    height=item_h,
                    bg_color=self.theme.get_rgb("background"),
                    border_color=self.theme.get_rgb("border"),
                    force_rectangle=True,
                )

                # Format icon on left
                fmt_raw = str(item.get("fmt", "DOCX")).upper()
                if "PPT" in fmt_raw:
                    fmt_icon = "presentation"
                elif "XLS" in fmt_raw:
                    fmt_icon = "table"
                elif "CODE" in fmt_raw:
                    fmt_icon = "code"
                elif "CLOUD" in fmt_raw:
                    fmt_icon = "cloud"
                else:
                    fmt_icon = "file-text"

                icon_dim = Inches(0.24)
                _add_icon_safe(
                    slide=slide,
                    icon_name=fmt_icon,
                    left=cx + Inches(0.16),
                    top=iy + Inches(0.19),
                    size=icon_dim,
                    color=acc,
                    theme=self.theme,
                )

                # Title
                tb_it = slide.shapes.add_textbox(
                    cx + Inches(0.46),
                    iy + Inches(0.08),
                    col_w - Inches(1.36),
                    item_h - Inches(0.14),
                )
                tf_it = tb_it.text_frame
                tf_it.word_wrap = True
                tf_it.margin_left = tf_it.margin_right = tf_it.margin_top = tf_it.margin_bottom = 0

                p_it = tf_it.paragraphs[0]
                p_it.text = item.get("name", "")
                p_it.font.name = self.theme.font_family
                p_it.font.size = Pt(11.0)
                p_it.font.bold = True
                p_it.font.color.rgb = self.theme.get_rgb("primary")

                # Status pill on right
                status_w = Inches(0.70)
                status_h = Inches(0.26)
                _add_status_pill(
                    slide=slide,
                    theme=self.theme,
                    left=cx + col_w - Inches(0.14) - status_w,
                    top=iy + Inches(0.18),
                    width=status_w,
                    height=status_h,
                    status=item.get("status", "Delivered"),
                    font_size_pt=11.0,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=9)
        return slide

    # -------------------------------------------------------------------------
    # Slide 5: Project Closing Checklist & Repository Credentials Matrix
    # -------------------------------------------------------------------------
    def build_closing_checklist(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "PROJECT CLOSING CHECKLIST"),
            action_title=d.get("title", "Project Closeout Verification Gates & Repository Access"),
            subtitle=d.get(
                "subtitle",
                "Dynamic sign-off status across 8 contractual closeout gates, verified repository credentials, and CSS link.",
            ),
        )

        checklist_items = d.get(
            "checklist_items",
            [
                {
                    "num": 1,
                    "title": "All defects in Defect List resolved",
                    "status": "Yes",
                    "detail": "0 open Sev 1/2 defects; all logged items verified & signed off by [CLIENT_SHORT_NAME] QA",
                },
                {
                    "num": 2,
                    "title": "All risks in Risk Register closed",
                    "status": "Yes",
                    "detail": "All project delivery risks mitigated; residual operational risks transitioned to maintenance",
                },
                {
                    "num": 3,
                    "title": "All issues in Issues Log closed",
                    "status": "Yes",
                    "detail": "All technical and operational issues resolved; zero blocking issues remaining",
                },
                {
                    "num": 4,
                    "title": "BAST 1 (Phase 1 Deliverables) sign-off",
                    "status": "Yes",
                    "detail": "Executed and formally approved by [CLIENT_SHORT_NAME] Finance & MII Project Sponsors",
                },
                {
                    "num": 5,
                    "title": "BAST 2 (Final Delivery & UAT) sign-off",
                    "status": "Yes",
                    "detail": "Signed upon successful UAT sign-off and completion of 2-week warranty period",
                },
                {
                    "num": 6,
                    "title": "BAST CR (Change Requests) sign-off",
                    "status": "Partial",
                    "detail": "Administrative addendum for minor enhancements under final client review",
                },
                {
                    "num": 7,
                    "title": "Vendor Administrator access revocation",
                    "status": "TBD",
                    "detail": "Scheduled upon handover completion; maintenance accounts provisioned separately",
                },
                {
                    "num": 8,
                    "title": "Customer Satisfaction Survey (CSS) dispatched",
                    "status": "Yes",
                    "detail": "Official Microsoft Forms evaluation dispatched to [CLIENT_SHORT_NAME] executive committee",
                },
            ],
        )

        left_x = Inches(0.80)
        left_w = Inches(7.10)
        top_y = Inches(1.80)
        matrix_h = Inches(4.95)

        # Container for Left Sign-off Matrix
        add_card_with_top_stripe(
            slide=slide,
            theme=self.theme,
            left=left_x,
            top=top_y,
            width=left_w,
            height=matrix_h,
            accent_rgb=self.theme.get_rgb("accent"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.05,
        )

        # Matrix Header
        tb_mh = slide.shapes.add_textbox(left_x + Inches(0.18), top_y + Inches(0.10), left_w - Inches(0.36), Inches(0.32))
        tf_mh = tb_mh.text_frame
        tf_mh.word_wrap = False
        tf_mh.margin_left = tf_mh.margin_right = tf_mh.margin_top = tf_mh.margin_bottom = 0
        p_mh = tf_mh.paragraphs[0]
        p_mh.text = "CONTRACTUAL CLOSEOUT VERIFICATION GATES"
        p_mh.font.name = self.theme.font_family_header
        p_mh.font.size = Pt(11.0)
        p_mh.font.bold = True
        p_mh.font.color.rgb = self.theme.get_rgb("primary")

        # 8 Rows inside Matrix
        row_start_y = top_y + Inches(0.44)
        row_h = Inches(0.52)
        row_gap = Inches(0.04)

        for i, item in enumerate(checklist_items[:8]):
            ry = row_start_y + i * (row_h + row_gap)
            rw = left_w - Inches(0.36)
            rx = left_x + Inches(0.18)

            add_card(
                slide=slide,
                theme=self.theme,
                left=rx,
                top=ry,
                width=rw,
                height=row_h,
                bg_color=self.theme.get_rgb("background") if i % 2 == 0 else self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            # Number badge
            tb_num = slide.shapes.add_textbox(rx + Inches(0.08), ry + Inches(0.12), Inches(0.28), Inches(0.28))
            tf_num = tb_num.text_frame
            tf_num.word_wrap = False
            tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
            p_n = tf_num.paragraphs[0]
            p_n.text = f"{item.get('num', i+1):02d}"
            p_n.font.name = self.theme.font_family_header
            p_n.font.size = Pt(11.0)
            p_n.font.bold = True
            p_n.font.color.rgb = self.theme.get_rgb("accent")

            # Title and Detail
            tb_txt = slide.shapes.add_textbox(rx + Inches(0.38), ry + Inches(0.06), rw - Inches(1.50), row_h - Inches(0.12))
            tf_txt = tb_txt.text_frame
            tf_txt.word_wrap = True
            tf_txt.margin_left = tf_txt.margin_right = tf_txt.margin_top = tf_txt.margin_bottom = 0

            p_t = tf_txt.paragraphs[0]
            p_t.text = item.get("title", "")
            p_t.font.name = self.theme.font_family_header
            p_t.font.size = Pt(11.0)
            p_t.font.bold = True
            p_t.font.color.rgb = self.theme.get_rgb("primary")

            p_d = tf_txt.add_paragraph()
            p_d.text = item.get("detail", "")
            p_d.font.name = self.theme.font_family
            p_d.font.size = Pt(11.0)
            p_d.font.color.rgb = self.theme.get_rgb("secondary")
            p_d.space_before = Pt(1)

            # Status pill
            pill_w = Inches(0.95)
            pill_h = Inches(0.28)
            _add_status_pill(
                slide=slide,
                theme=self.theme,
                left=rx + rw - pill_w - Inches(0.10),
                top=ry + Inches(0.12),
                width=pill_w,
                height=pill_h,
                status=item.get("status", "Yes"),
                font_size_pt=11.0,
            )

        # Right Side Cards (Credential Card & CSS Survey Card)
        right_x = Inches(8.15)
        right_w = Inches(4.38)

        # Card A: Artifact Repository Card
        card_a_h = Inches(2.40)
        add_card_with_top_stripe(
            slide=slide,
            theme=self.theme,
            left=right_x,
            top=top_y,
            width=right_w,
            height=card_a_h,
            accent_rgb=self.theme.get_rgb("accent"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.05,
        )

        icon_dim = Inches(0.30)
        _add_icon_safe(
            slide=slide,
            icon_name="folder-archive",
            left=right_x + right_w - icon_dim - Inches(0.18),
            top=top_y + Inches(0.14),
            size=icon_dim,
            color=self.theme.get_rgb("accent"),
            theme=self.theme,
        )

        tb_ca = slide.shapes.add_textbox(right_x + Inches(0.18), top_y + Inches(0.12), right_w - icon_dim - Inches(0.36), card_a_h - Inches(0.24))
        tf_ca = tb_ca.text_frame
        tf_ca.word_wrap = True
        tf_ca.margin_left = tf_ca.margin_right = tf_ca.margin_top = tf_ca.margin_bottom = 0

        p_cat = tf_ca.paragraphs[0]
        p_cat.text = "SECURE DELIVERABLES REPOSITORY"
        p_cat.font.name = self.theme.font_family_header
        p_cat.font.size = Pt(12.0)
        p_cat.font.bold = True
        p_cat.font.color.rgb = self.theme.get_rgb("primary")

        p_cas = tf_ca.add_paragraph()
        p_cas.text = "Complete package: 19 deliverables, source code packages, documentation & signed BAST forms."
        p_cas.font.name = self.theme.font_family
        p_cas.font.size = Pt(11.0)
        p_cas.font.color.rgb = self.theme.get_rgb("secondary")
        p_cas.space_before = Pt(3)

        # Download Link container
        dl_link = d.get(
            "download_link",
            "https://drive.google.com/file/d/1jbNeQz7FGOoB5V-wnPjvgkLJQ1YiPYGQ/view?usp=sharing",
        )
        p_lbl1 = tf_ca.add_paragraph()
        p_lbl1.text = "GOOGLE DRIVE SECURE LINK"
        p_lbl1.font.name = self.theme.font_family_header
        p_lbl1.font.size = Pt(11.0)
        p_lbl1.font.bold = True
        p_lbl1.font.color.rgb = self.theme.get_rgb("accent")
        p_lbl1.space_before = Pt(6)

        p_url = tf_ca.add_paragraph()
        p_url.text = dl_link if len(dl_link) < 55 else dl_link[:52] + "..."
        p_url.font.name = "Courier New"
        p_url.font.size = Pt(11.0)
        p_url.font.color.rgb = self.theme.get_rgb("primary")
        p_url.space_before = Pt(2)

        # Password
        password = d.get("password", "Metrodata2026!")
        p_lbl2 = tf_ca.add_paragraph()
        p_lbl2.text = "ARCHIVE DECRYPTION PASSWORD"
        p_lbl2.font.name = self.theme.font_family_header
        p_lbl2.font.size = Pt(11.0)
        p_lbl2.font.bold = True
        p_lbl2.font.color.rgb = self.theme.get_rgb("accent")
        p_lbl2.space_before = Pt(6)

        p_pw = tf_ca.add_paragraph()
        p_pw.text = f"[ {password} ]  •  Protected Zip Archive"
        p_pw.font.name = "Courier New"
        p_pw.font.size = Pt(11.0)
        p_pw.font.bold = True
        p_pw.font.color.rgb = self.theme.get_rgb("accent_teal")
        p_pw.space_before = Pt(2)

        # Card B: Customer Satisfaction Survey (CSS) Card
        card_b_top = top_y + card_a_h + Inches(0.15)
        card_b_h = matrix_h - card_a_h - Inches(0.15)
        add_card_with_top_stripe(
            slide=slide,
            theme=self.theme,
            left=right_x,
            top=card_b_top,
            width=right_w,
            height=card_b_h,
            accent_rgb=self.theme.get_rgb("success"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.05,
        )

        _add_icon_safe(
            slide=slide,
            icon_name="clipboard-check",
            left=right_x + right_w - icon_dim - Inches(0.18),
            top=card_b_top + Inches(0.14),
            size=icon_dim,
            color=self.theme.get_rgb("success"),
            theme=self.theme,
        )

        tb_cb = slide.shapes.add_textbox(right_x + Inches(0.18), card_b_top + Inches(0.12), right_w - icon_dim - Inches(0.36), card_b_h - Inches(0.24))
        tf_cb = tb_cb.text_frame
        tf_cb.word_wrap = True
        tf_cb.margin_left = tf_cb.margin_right = tf_cb.margin_top = tf_cb.margin_bottom = 0

        p_cbt = tf_cb.paragraphs[0]
        p_cbt.text = "CUSTOMER SATISFACTION SURVEY (CSS)"
        p_cbt.font.name = self.theme.font_family_header
        p_cbt.font.size = Pt(12.0)
        p_cbt.font.bold = True
        p_cbt.font.color.rgb = self.theme.get_rgb("primary")

        p_cbs = tf_cb.add_paragraph()
        p_cbs.text = "Your feedback is essential to evaluate project execution, communication quality, and technical expertise."
        p_cbs.font.name = self.theme.font_family
        p_cbs.font.size = Pt(11.0)
        p_cbs.font.color.rgb = self.theme.get_rgb("secondary")
        p_cbs.space_before = Pt(3)

        css_link = d.get(
            "css_link",
            "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=rgOfXJbVn0q-VTj8N43ujHvqOdLTWpVGqw01JkKQaalUQkVVM0RHVlRCSDFWSlZMUkpRQU81UDNMWS4u",
        )
        p_css_lbl = tf_cb.add_paragraph()
        p_css_lbl.text = "SURVEY SUBMISSION PORTAL"
        p_css_lbl.font.name = self.theme.font_family_header
        p_css_lbl.font.size = Pt(11.0)
        p_css_lbl.font.bold = True
        p_css_lbl.font.color.rgb = self.theme.get_rgb("success")
        p_css_lbl.space_before = Pt(6)

        p_css_url = tf_cb.add_paragraph()
        p_css_url.text = css_link if len(css_link) < 55 else css_link[:52] + "..."
        p_css_url.font.name = "Courier New"
        p_css_url.font.size = Pt(11.0)
        p_css_url.font.color.rgb = self.theme.get_rgb("primary")
        p_css_url.space_before = Pt(2)

        p_css_sub = tf_cb.add_paragraph()
        p_css_sub.text = "Status: Survey Dispatched  •  Target Completion: 14 Days"
        p_css_sub.font.name = self.theme.font_family
        p_css_sub.font.size = Pt(11.0)
        p_css_sub.font.bold = True
        p_css_sub.font.color.rgb = self.theme.get_rgb("accent_teal")
        p_css_sub.space_before = Pt(4)

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=9)
        return slide

    # -------------------------------------------------------------------------
    # Slide 6: Transition to Maintenance Phase
    # -------------------------------------------------------------------------
    def build_maintenance_transition(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "MAINTENANCE TRANSITION"),
            action_title=d.get("title", "Transition to Maintenance: Bucket Mandays Operating Model"),
            subtitle=d.get(
                "subtitle",
                "Flexible, capacity-based support structure designed for agile bug remediation, platform health, and minor CRs.",
            ),
        )

        # Top KPI Banner (Clean, concise labels with zero overflow)
        kpis = [
            {"label": "Annual Quota Pool", "value": "30 Mandays", "accent": "accent"},
            {"label": "Minimum Billable Unit", "value": "0.5 Manday", "accent": "accent_teal"},
            {"label": "Rollover Guarantee", "value": "100% Rollover", "accent": "success"},
        ]

        kpi_w = Inches(3.70)
        kpi_h = Inches(0.85)
        gap_x = Inches(0.31)
        start_x = Inches(0.80)
        top_kpi = Inches(1.80)

        for i, kpi in enumerate(kpis):
            kx = start_x + i * (kpi_w + gap_x)
            acc = self.theme.get_rgb(kpi["accent"])
            add_card(
                slide=slide,
                theme=self.theme,
                left=kx,
                top=top_kpi,
                width=kpi_w,
                height=kpi_h,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            pbar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, kx, top_kpi, Inches(0.045), kpi_h)
            pbar.shadow.inherit = False
            pbar.fill.solid()
            pbar.fill.fore_color.rgb = acc
            pbar.line.fill.background()

            tb = slide.shapes.add_textbox(kx + Inches(0.16), top_kpi + Inches(0.12), kpi_w - Inches(0.28), kpi_h - Inches(0.20))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p_val = tf.paragraphs[0]
            p_val.text = kpi["value"]
            p_val.font.name = self.theme.font_family_header
            p_val.font.size = Pt(16.0)
            p_val.font.bold = True
            p_val.font.color.rgb = self.theme.get_rgb("primary")

            p_lbl = tf.add_paragraph()
            p_lbl.text = kpi["label"].upper()
            p_lbl.font.name = self.theme.font_family
            p_lbl.font.size = Pt(11.0)
            p_lbl.font.bold = True
            p_lbl.font.color.rgb = self.theme.get_rgb("secondary")
            p_lbl.space_before = Pt(2)

        # Bottom 3 Deep-Dive Pillar Cards (Clean titles, no redundant subtitles)
        pillars = d.get(
            "pillars",
            [
                {
                    "title": "Capacity Metering & Top-Up",
                    "accent": "accent",
                    "bullets": [
                        "A total allocation of 30 mandays per contract year.",
                        "Billing is strictly based on actual consumed mandays.",
                        "The minimum billable increment is 0.5 mandays (4 hours) per task.",
                        "Mandays may be topped up if fully utilized within the current year.",
                        "Transparent monthly burn-rate reconciliation and notifications.",
                    ],
                },
                {
                    "title": "Rollover & Commercial Terms",
                    "accent": "accent_teal",
                    "bullets": [
                        "Remaining unused mandays carry over to following year's contract.",
                        "Zero forfeiture penalty on unused support capacity.",
                        "Quota reconciliation synchronized with quarterly sponsor reviews.",
                        "Option to combine mandays for medium complexity Change Requests.",
                        "Predictable annual operational budget without lock-in penalties.",
                    ],
                },
                {
                    "title": "Eligible Maintenance Scope",
                    "accent": "accent_purple",
                    "bullets": [
                        "Mandays utilized for bug fixing and corrective incident resolution.",
                        "Implementation of approved Change Requests (CRs) and minor features.",
                        "Streamlit frontend styling, layout refinements, and filter tuning.",
                        "Snowflake SQL performance optimization and query compute tuning.",
                        "Cortex GenAI prompt adjustments and narrative logic refinements.",
                    ],
                },
            ],
        )

        card_w = Inches(3.70)
        card_h = Inches(3.95)
        top_cards = Inches(2.85)

        for i, p in enumerate(pillars[:3]):
            cx = start_x + i * (card_w + gap_x)
            acc = self.theme.get_rgb(p.get("accent", "accent"))

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=cx,
                top=top_cards,
                width=card_w,
                height=card_h,
                accent_rgb=acc,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.06,
            )

            tb = slide.shapes.add_textbox(cx + Inches(0.18), top_cards + Inches(0.14), card_w - Inches(0.36), card_h - Inches(0.24))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p_t = tf.paragraphs[0]
            p_t.text = p.get("title", "")
            p_t.font.name = self.theme.font_family_header
            p_t.font.size = Pt(13.0)
            p_t.font.bold = True
            p_t.font.color.rgb = self.theme.get_rgb("primary")

            if p.get("subtitle"):
                p_s = tf.add_paragraph()
                p_s.text = p.get("subtitle", "").upper()
                p_s.font.name = self.theme.font_family
                p_s.font.size = Pt(11.0)
                p_s.font.bold = True
                p_s.font.color.rgb = acc
                p_s.space_before = Pt(2)

            for b_idx, b in enumerate(p.get("bullets", [])):
                _add_bullet_paragraph(
                    tf=tf,
                    text=b,
                    font_name=self.theme.font_family,
                    font_size_pt=11.0,
                    font_color=self.theme.get_rgb("secondary"),
                    space_before_pt=6.0 if b_idx == 0 else 4.0,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=9)
        return slide

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # Slide 7: Maintenance Contacts & Request Flow
    # -------------------------------------------------------------------------
    def build_maintenance_flow(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "OPERATIONAL GOVERNANCE"),
            action_title=d.get("title", "Maintenance Workflow & Designated Primary Contacts"),
            subtitle=d.get(
                "subtitle",
                "Structured 3-swimlane request lifecycle across client, support triage, and engineering practices.",
            ),
        )

        # ---------------------------------------------------------------------
        # Top Section: Formal 3-Swimlane Process Flowchart
        # ---------------------------------------------------------------------
        lanes = [
            {
                "id": "client",
                "title": "Client Organization",
                "subtitle": "[CLIENT_SHORT_NAME] Operations & Finance",
                "accent": "accent",
            },
            {
                "id": "support",
                "title": "Vendor Support Core",
                "subtitle": "Metrodata L1/L2 Operations",
                "accent": "accent_teal",
            },
            {
                "id": "engineering",
                "title": "Engineering Practice",
                "subtitle": "Snowflake & Streamlit Core",
                "accent": "accent_purple",
            },
        ]

        lane_h = Inches(0.78)
        lane_gap = Inches(0.06)
        swimlane_top = Inches(1.72)
        lane_w = Inches(11.73)
        start_x = Inches(0.80)

        # Render 3 Swimlane Background Bands and Headers
        lane_y_map = {}
        for l_idx, lane in enumerate(lanes):
            ly = swimlane_top + l_idx * (lane_h + lane_gap)
            lane_y_map[lane["id"]] = ly
            acc = self.theme.get_rgb(lane["accent"])

            # Full-width lane background track
            track = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, ly, lane_w, lane_h)
            track.shadow.inherit = False
            track.fill.solid()
            track.fill.fore_color.rgb = self.theme.get_rgb("background")
            track.line.color.rgb = self.theme.get_rgb("border")
            track.line.width = Pt(1)

            # Left lane header container
            header_w = Inches(2.25)
            h_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, ly, header_w, lane_h)
            h_box.shadow.inherit = False
            h_box.fill.solid()
            h_box.fill.fore_color.rgb = self.theme.get_rgb("surface")
            h_box.line.color.rgb = self.theme.get_rgb("border")
            h_box.line.width = Pt(1)

            # Left accent stripe on lane header
            l_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, ly, Inches(0.05), lane_h)
            l_bar.shadow.inherit = False
            l_bar.fill.solid()
            l_bar.fill.fore_color.rgb = acc
            l_bar.line.fill.background()

            tb_lh = slide.shapes.add_textbox(start_x + Inches(0.12), ly + Inches(0.12), header_w - Inches(0.20), lane_h - Inches(0.24))
            tf_lh = tb_lh.text_frame
            tf_lh.word_wrap = True
            tf_lh.margin_left = tf_lh.margin_right = tf_lh.margin_top = tf_lh.margin_bottom = 0

            p_lt = tf_lh.paragraphs[0]
            p_lt.text = lane["title"]
            p_lt.font.name = self.theme.font_family_header
            p_lt.font.size = Pt(11.0)
            p_lt.font.bold = True
            p_lt.font.color.rgb = self.theme.get_rgb("primary")

            p_ls = tf_lh.add_paragraph()
            p_ls.text = lane["subtitle"]
            p_ls.font.name = self.theme.font_family
            p_ls.font.size = Pt(11.0)
            p_ls.font.bold = True
            p_ls.font.color.rgb = acc
            p_ls.space_before = Pt(2)

        # 5 Steps mapped into Swimlanes with integrated SLA / Gate metadata
        flow_steps = [
            {
                "num": "01",
                "lane": "client",
                "title": "Request Intake",
                "desc": "WhatsApp & Email",
                "accent": "accent",
                "tag": "SLA: Immediate",
            },
            {
                "num": "02",
                "lane": "support",
                "title": "SLA Triage",
                "desc": "Manday Sizing",
                "accent": "accent_teal",
                "tag": "SLA: < 4h / 1-2d",
            },
            {
                "num": "03",
                "lane": "client",
                "title": "Manday Approval",
                "desc": "Written Approval",
                "accent": "warning",
                "tag": "Gate: Authorized",
            },
            {
                "num": "04",
                "lane": "engineering",
                "title": "Fix, SIT & Deploy",
                "desc": "Snowflake & Streamlit",
                "accent": "accent_purple",
                "tag": "Cycle: Continuous",
            },
            {
                "num": "05",
                "lane": "client",
                "title": "UAT & Sign-off",
                "desc": "Timesheet Sign-off",
                "accent": "success",
                "tag": "Gate: Verified",
            },
        ]

        step_w = Inches(1.64)
        step_h = Inches(0.72)
        col_gap = Inches(0.31)
        step_start_x = start_x + Inches(2.38)

        from pptx.enum.shapes import MSO_CONNECTOR

        for s_idx, st in enumerate(flow_steps):
            sx = step_start_x + s_idx * (step_w + col_gap)
            sy = lane_y_map[st["lane"]] + Inches(0.03)
            s_acc = self.theme.get_rgb(st["accent"])

            # Step Card with top stripe
            add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=sx,
                top=sy,
                width=step_w,
                height=step_h,
                accent_rgb=s_acc,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.04,
            )

            tb_s = slide.shapes.add_textbox(sx + Inches(0.06), sy + Inches(0.03), step_w - Inches(0.12), step_h - Inches(0.05))
            tf_s = tb_s.text_frame
            tf_s.word_wrap = True
            tf_s.margin_left = tf_s.margin_right = tf_s.margin_top = tf_s.margin_bottom = 0

            p_sn = tf_s.paragraphs[0]
            p_sn.text = f"{st['num']}. {st['title']}"
            p_sn.font.name = self.theme.font_family_header
            p_sn.font.size = Pt(11.0)
            p_sn.font.bold = True
            p_sn.font.color.rgb = self.theme.get_rgb("primary")

            p_sd = tf_s.add_paragraph()
            p_sd.text = st["desc"]
            p_sd.font.name = self.theme.font_family
            p_sd.font.size = Pt(11.0)
            p_sd.font.color.rgb = self.theme.get_rgb("secondary")
            p_sd.space_before = Pt(0)

            p_st = tf_s.add_paragraph()
            p_st.text = st["tag"]
            p_st.font.name = self.theme.font_family
            p_st.font.size = Pt(11.0)
            p_st.font.bold = True
            p_st.font.color.rgb = s_acc
            p_st.space_before = Pt(1)

            # Directional Connector Arrow to next step
            if s_idx < 4:
                next_st = flow_steps[s_idx + 1]
                next_sx = step_start_x + (s_idx + 1) * (step_w + col_gap)
                next_sy = lane_y_map[next_st["lane"]] + Inches(0.04)

                cx1 = int(sx + step_w)
                cy1 = int(sy + step_h / 2)
                cx2 = int(next_sx)
                cy2 = int(next_sy + step_h / 2)

                conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, cx1, cy1, cx2, cy2)
                conn.line.color.rgb = self.theme.get_rgb("accent")
                conn.line.width = Pt(1.5)

                head_end = OxmlElement("a:headEnd")
                head_end.set("type", "triangle")
                head_end.set("w", "med")
                head_end.set("len", "med")
                conn.line._get_or_add_ln().append(head_end)

        # ---------------------------------------------------------------------
        # Bottom Section: Contacts (Left) & Channels/SLA (Right)
        # ---------------------------------------------------------------------
        top_bottom = Inches(4.30)
        h_bottom = Inches(2.55)

        # Left: 2 Primary Contact Cards
        contacts_w = Inches(5.75)
        add_card_with_top_stripe(
            slide=slide,
            theme=self.theme,
            left=start_x,
            top=top_bottom,
            width=contacts_w,
            height=h_bottom,
            accent_rgb=self.theme.get_rgb("accent"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.05,
        )

        tb_ch = slide.shapes.add_textbox(start_x + Inches(0.18), top_bottom + Inches(0.12), contacts_w - Inches(0.36), Inches(0.30))
        tf_ch = tb_ch.text_frame
        tf_ch.word_wrap = False
        tf_ch.margin_left = tf_ch.margin_right = tf_ch.margin_top = tf_ch.margin_bottom = 0
        p_ch = tf_ch.paragraphs[0]
        p_ch.text = "DESIGNATED PRIMARY TECHNICAL CONTACTS"
        p_ch.font.name = self.theme.font_family_header
        p_ch.font.size = Pt(11.0)
        p_ch.font.bold = True
        p_ch.font.color.rgb = self.theme.get_rgb("primary")

        contacts = d.get(
            "contacts",
            [
                {
                    "name": "Adam Nevriyanto",
                    "role": "Solution Architect & Technical Lead",
                    "email": "Adam.Nevriyanto@metrodata.co.id",
                    "phone": "MII Technical Support Core",
                },
                {
                    "name": "Vicko Bhayyu",
                    "role": "Senior Data Engineer & Maintenance Lead",
                    "email": "Vicko.Bhayyu@metrodata.co.id",
                    "phone": "Snowflake Engineering Practice",
                },
            ],
        )

        c_w = contacts_w - Inches(0.36)
        c_h = Inches(0.90)
        c_gap = Inches(0.10)
        c_start_y = top_bottom + Inches(0.48)

        for j, con in enumerate(contacts[:2]):
            cy = c_start_y + j * (c_h + c_gap)
            add_card(
                slide=slide,
                theme=self.theme,
                left=start_x + Inches(0.18),
                top=cy,
                width=c_w,
                height=c_h,
                bg_color=self.theme.get_rgb("background"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            # Left accent pill bar
            cbar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x + Inches(0.18), cy, Inches(0.04), c_h)
            cbar.shadow.inherit = False
            cbar.fill.solid()
            cbar.fill.fore_color.rgb = self.theme.get_rgb("accent" if j == 0 else "accent_teal")
            cbar.line.fill.background()

            tb_c = slide.shapes.add_textbox(start_x + Inches(0.30), cy + Inches(0.08), c_w - Inches(0.35), c_h - Inches(0.14))
            tf_c = tb_c.text_frame
            tf_c.word_wrap = True
            tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0

            p_cn = tf_c.paragraphs[0]
            p_cn.text = con.get("name", "")
            p_cn.font.name = self.theme.font_family_header
            p_cn.font.size = Pt(11.0)
            p_cn.font.bold = True
            p_cn.font.color.rgb = self.theme.get_rgb("primary")

            p_cr = tf_c.add_paragraph()
            p_cr.text = f"{con.get('role', '')}  •  {con.get('phone', '')}"
            p_cr.font.name = self.theme.font_family
            p_cr.font.size = Pt(11.0)
            p_cr.font.color.rgb = self.theme.get_rgb("accent")
            p_cr.space_before = Pt(1)

            p_ce = tf_c.add_paragraph()
            p_ce.text = f"Email: {con.get('email', '')}"
            p_ce.font.name = "Courier New"
            p_ce.font.size = Pt(11.0)
            p_ce.font.bold = True
            p_ce.font.color.rgb = self.theme.get_rgb("secondary")
            p_ce.space_before = Pt(2)

        # Right: Communication Channels & SLA
        gap_x = Inches(0.24)
        right_x = start_x + contacts_w + gap_x
        right_w = Inches(5.74)
        add_card_with_top_stripe(
            slide=slide,
            theme=self.theme,
            left=right_x,
            top=top_bottom,
            width=right_w,
            height=h_bottom,
            accent_rgb=self.theme.get_rgb("accent_teal"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.05,
        )

        tb_rh = slide.shapes.add_textbox(right_x + Inches(0.18), top_bottom + Inches(0.12), right_w - Inches(0.36), h_bottom - Inches(0.24))
        tf_rh = tb_rh.text_frame
        tf_rh.word_wrap = True
        tf_rh.margin_left = tf_rh.margin_right = tf_rh.margin_top = tf_rh.margin_bottom = 0

        p_rh = tf_rh.paragraphs[0]
        p_rh.text = "OFFICIAL CHANNELS & SERVICE LEVEL TARGETS"
        p_rh.font.name = self.theme.font_family_header
        p_rh.font.size = Pt(11.0)
        p_rh.font.bold = True
        p_rh.font.color.rgb = self.theme.get_rgb("primary")

        channels = [
            ("Dedicated WhatsApp Group", "Real-time communication, rapid alerts, and day-to-day coordination"),
            ("Email Ticket Submission", "Formal issue logging, estimation quote dispatch & written client approvals"),
            ("Priority 1 SLA (Sev 1 Defect)", "Initial triage within 4 business hours; continuous remediation until restored"),
            ("Priority 2 SLA (Sev 2 / CR)", "Triage and manday sizing quote delivered within 1 to 2 business days"),
        ]

        for lbl, desc in channels:
            p_l = tf_rh.add_paragraph()
            p_l.text = f"{lbl}: "
            p_l.font.name = self.theme.font_family_header
            p_l.font.size = Pt(11.0)
            p_l.font.bold = True
            p_l.font.color.rgb = self.theme.get_rgb("primary")
            p_l.space_before = Pt(4)

            r_d = p_l.add_run()
            r_d.text = desc
            r_d.font.name = self.theme.font_family
            r_d.font.size = Pt(11.0)
            r_d.font.bold = False
            r_d.font.color.rgb = self.theme.get_rgb("secondary")

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=9)
        return slide

    # -------------------------------------------------------------------------
    # Slide 8: Maintenance Deliverables
    # -------------------------------------------------------------------------
    def build_maintenance_deliverables(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "MAINTENANCE DELIVERABLES"),
            action_title=d.get("title", "Ongoing Maintenance Reporting & Transparency Artifacts"),
            subtitle=d.get(
                "subtitle",
                "Standard recurring deliverables ensuring complete auditability of mandays utilization, time tracking, and changes.",
            ),
        )

        deliverables = d.get(
            "deliverables",
            [
                {
                    "title": "Monthly Mandays Usage Recap",
                    "accent": "accent",
                    "bullets": [
                        "Monthly consolidated statement of mandays consumed during the billing cycle.",
                        "Cumulative tracking against the 30-manday annual quota pool.",
                        "Granular breakdown of mandays expended per financial analytics module.",
                        "Remaining balance forecast to prevent unexpected end-of-year depletion.",
                        "Submitted monthly in PDF and Excel formats for formal client sign-off.",
                        "Shared during monthly service review meetings with [CLIENT_SHORT_NAME] leadership.",
                    ],
                },
                {
                    "title": "Developer Timesheet Records",
                    "accent": "accent_teal",
                    "bullets": [
                        "Granular daily timesheets logged by assigned MII software & data engineers.",
                        "Detailed task breakdown mapped to specific [CLIENT_SHORT_NAME] ticket numbers.",
                        "Time accounted in strict 0.5-manday billable increments (4-hour resolution).",
                        "Quality and hours verified and counter-signed by MII Technical Lead.",
                        "Complete audit trail compliant with enterprise procurement guidelines.",
                        "Archived digitally alongside monthly invoicing documentation.",
                    ],
                },
                {
                    "title": "Technical Documentation & CR Logs",
                    "accent": "accent_purple",
                    "bullets": [
                        "Formal Root Cause Analysis (RCA) documentation for all resolved defects.",
                        "Updated Functional & Technical Specifications (FSD/TSD addendums).",
                        "Version-controlled Git commit hashes and deployment manifests.",
                        "Updated user operating instructions where UI workflows are altered.",
                        "Release verification checklists and rollback procedures.",
                        "Secure digital archiving in client-accessible cloud repository.",
                    ],
                },
            ],
        )

        cols = 3
        card_w = Inches(3.70)
        card_h = Inches(4.95)
        gap_x = Inches(0.31)
        start_x = Inches(0.80)
        top_y = Inches(1.80)

        for i, dl in enumerate(deliverables[:3]):
            cx = start_x + i * (card_w + gap_x)
            acc = self.theme.get_rgb(dl.get("accent", "accent"))

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=cx,
                top=top_y,
                width=card_w,
                height=card_h,
                accent_rgb=acc,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.06,
            )

            tb = slide.shapes.add_textbox(cx + Inches(0.18), top_y + Inches(0.14), card_w - Inches(0.36), card_h - Inches(0.24))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p_t = tf.paragraphs[0]
            p_t.text = dl.get("title", "")
            p_t.font.name = self.theme.font_family_header
            p_t.font.size = Pt(13.0)
            p_t.font.bold = True
            p_t.font.color.rgb = self.theme.get_rgb("primary")

            if dl.get("subtitle"):
                p_s = tf.add_paragraph()
                p_s.text = dl.get("subtitle", "").upper()
                p_s.font.name = self.theme.font_family
                p_s.font.size = Pt(11.0)
                p_s.font.bold = True
                p_s.font.color.rgb = acc
                p_s.space_before = Pt(2)

            for b_idx, b in enumerate(dl.get("bullets", [])):
                _add_bullet_paragraph(
                    tf=tf,
                    text=b,
                    font_name=self.theme.font_family,
                    font_size_pt=11.0,
                    font_color=self.theme.get_rgb("secondary"),
                    space_before_pt=6.0 if b_idx == 0 else 4.0,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=9)
        return slide

    # -------------------------------------------------------------------------
    # Slide 9: Thank You & Practice Contacts
    # -------------------------------------------------------------------------
    def build_thank_you(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)

        stripe_top = Inches(1.80)
        stripe_height = Inches(4.50)
        stripe_left = Inches(0.80)
        red_w = Inches(0.045)
        blue_w = Inches(0.090)

        s_red = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, stripe_left, stripe_top, red_w, stripe_height)
        s_red.shadow.inherit = False
        s_red.fill.solid()
        s_red.fill.fore_color.rgb = self.theme.get_rgb("accent_secondary", "#DC2626")
        s_red.line.fill.background()

        s_blue = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, stripe_left + red_w, stripe_top, blue_w, stripe_height)
        s_blue.shadow.inherit = False
        s_blue.fill.solid()
        s_blue.fill.fore_color.rgb = self.theme.get_rgb("accent", "#0052CC")
        s_blue.line.fill.background()

        text_left = stripe_left + red_w + blue_w + Inches(0.35)
        text_width = Inches(11.20)
        tb = slide.shapes.add_textbox(text_left, Inches(1.80), text_width, Inches(1.60))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_tr = tf.paragraphs[0]
        p_tr.text = d.get("tracker", "PROJECT CLOSING & MAINTENANCE TRANSITION").upper()
        p_tr.font.name = self.theme.font_family_header
        p_tr.font.size = Pt(11.0)
        p_tr.font.bold = True
        p_tr.font.color.rgb = self.theme.get_rgb("accent")

        p_t = tf.add_paragraph()
        p_t.text = d.get("title", "Thank You")
        p_t.font.name = self.theme.font_family_header
        p_t.font.size = Pt(36.0)
        p_t.font.bold = True
        p_t.font.color.rgb = self.theme.get_rgb("primary")
        p_t.space_before = Pt(6)

        p_s = tf.add_paragraph()
        p_s.text = d.get(
            "subtitle",
            "Empowering Financial Intelligence & Cloud Analytics at [CLIENT_COMPANY_NAME].",
        )
        p_s.font.name = self.theme.font_family
        p_s.font.size = Pt(13.0)
        p_s.font.color.rgb = self.theme.get_rgb("secondary")
        p_s.space_before = Pt(10)

        contacts = d.get("contacts")

        if contacts:
            card_w = Inches(5.40)
            card_h = Inches(1.50)
            card_y = Inches(3.80)

            for i, c in enumerate(contacts[:2]):
                cx = text_left + i * (card_w + Inches(0.30))
                card, stripe = add_card_with_top_stripe(
                    slide=slide,
                    theme=self.theme,
                    left=cx,
                    top=card_y,
                    width=card_w,
                    height=card_h,
                    accent_rgb=self.theme.get_rgb("accent") if i == 0 else self.theme.get_rgb("accent_teal"),
                    bg_color=self.theme.get_rgb("surface"),
                    border_color=self.theme.get_rgb("border"),
                    stripe_height_in=0.06,
                )

                ctb = slide.shapes.add_textbox(cx + Inches(0.18), card_y + Inches(0.16), card_w - Inches(0.36), card_h - Inches(0.25))
                ctf = ctb.text_frame
                ctf.word_wrap = True
                ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0

                cp1 = ctf.paragraphs[0]
                cp1.text = c.get("name", "")
                cp1.font.name = self.theme.font_family_header
                cp1.font.size = Pt(13.0)
                cp1.font.bold = True
                cp1.font.color.rgb = self.theme.get_rgb("primary")

                cp2 = ctf.add_paragraph()
                cp2.text = c.get("role", "")
                cp2.font.name = self.theme.font_family
                cp2.font.size = Pt(11.0)
                cp2.font.color.rgb = self.theme.get_rgb("accent")
                cp2.space_before = Pt(3)

                cp3 = ctf.add_paragraph()
                cp3.text = f"Email: {c.get('email', '')}"
                cp3.font.name = self.theme.font_family
                cp3.font.size = Pt(11.0)
                cp3.font.color.rgb = self.theme.get_rgb("secondary")
                cp3.space_before = Pt(4)
        else:
            # Clean corporate closing without hardcoded staff names
            card_w = Inches(7.50)
            card_h = Inches(1.50)
            card_y = Inches(3.80)

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=text_left,
                top=card_y,
                width=card_w,
                height=card_h,
                accent_rgb=self.theme.get_rgb("accent"),
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.06,
            )

            ctb = slide.shapes.add_textbox(text_left + Inches(0.22), card_y + Inches(0.18), card_w - Inches(0.44), card_h - Inches(0.30))
            ctf = ctb.text_frame
            ctf.word_wrap = True
            ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0

            cp1 = ctf.paragraphs[0]
            cp1.text = "Data & AI Modernization Practice"
            cp1.font.name = self.theme.font_family_header
            cp1.font.size = Pt(14.0)
            cp1.font.bold = True
            cp1.font.color.rgb = self.theme.get_rgb("primary")

            cp2 = ctf.add_paragraph()
            cp2.text = "Enterprise Cloud & Analytics Advisory Core"
            cp2.font.name = self.theme.font_family
            cp2.font.size = Pt(11.0)
            cp2.font.color.rgb = self.theme.get_rgb("accent")
            cp2.space_before = Pt(3)

            cp3 = ctf.add_paragraph()
            cp3.text = "Official Support Channel: enterprise.consulting@metrodata.co.id"
            cp3.font.name = self.theme.font_family
            cp3.font.size = Pt(11.0)
            cp3.font.color.rgb = self.theme.get_rgb("secondary")
            cp3.space_before = Pt(4)

        otb = slide.shapes.add_textbox(text_left, Inches(5.60), text_width, Inches(0.60))
        otf = otb.text_frame
        otf.word_wrap = True
        otf.margin_left = otf.margin_right = otf.margin_top = otf.margin_bottom = 0
        op1 = otf.paragraphs[0]
        op1.text = f"{d.get('company', 'PT Metrodata Electronics Tbk')}  |  {d.get('office', 'APL Tower 37th Floor, Jl. Letjen S. Parman Kav. 28, Jakarta Barat 11470')}"
        op1.font.name = self.theme.font_family
        op1.font.size = Pt(11.0)
        op1.font.color.rgb = self.theme.get_rgb("muted")

        add_slide_footer(
            slide,
            self.theme,
            current_idx=idx,
            total_slides=9,
            notice=d.get("notice", "[CLIENT_COMPANY_NAME] & PT Metrodata Electronics Tbk  |  Confidential"),
        )
        return slide

    # -------------------------------------------------------------------------
    # Dynamic Spreadsheet Ingestion
    # -------------------------------------------------------------------------
    def sync_with_spreadsheets(
        self,
        checklist_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """
        Dynamically extracts closeout checklist verification gates, delivered scope,
        and secure repository credentials from the closeout checklist workbook.
        """
        import openpyxl

        sync_results: Dict[str, Any] = {
            "checklist_synced": False,
            "deliverables_synced": False,
            "checklist_count": 0,
            "deliverables_count": 0,
            "download_link": None,
            "password": None,
            "css_link": None,
        }

        # Resolve spreadsheet path
        c_path = checklist_path or self.config.get("spreadsheets", {}).get("checklist")
        if not c_path:
            default_candidate = Path(
                "clean_workspace/projects/TTI_Snowflake_Analytics/06_closing/5.2_Project_Closeout_Checklist_Template.xlsx"
            )
            if default_candidate.exists():
                c_path = default_candidate

        if not c_path:
            logger.info("No checklist spreadsheet provided or found for synchronization.")
            return sync_results

        c_file = Path(c_path)
        if not c_file.exists():
            logger.warning(f"Checklist spreadsheet not found at: {c_file}")
            return sync_results

        try:
            wb = openpyxl.load_workbook(str(c_file), data_only=True)
            sheet_names = wb.sheetnames
            sheet_name = "Closing Checklist" if "Closing Checklist" in sheet_names else sheet_names[0]
            ws = wb[sheet_name]

            # Ingest deliverables from Section 1 (rows 4 to 22)
            raw_deliverables = []
            for r in range(4, 23):
                no_val = ws.cell(r, 1).value
                name_val = ws.cell(r, 2).value
                status_val = ws.cell(r, 3).value
                if name_val:
                    raw_deliverables.append({
                        "num": int(no_val) if isinstance(no_val, (int, float)) else len(raw_deliverables) + 1,
                        "name": str(name_val).strip(),
                        "status": str(status_val).strip() if status_val else "Delivered",
                    })

            # Ingest checklist items from Section 3 (rows 34 to 41)
            raw_checklist = []
            detail_mapping = {
                1: "0 open Sev 1/2 defects; all logged items verified & signed off by [CLIENT_SHORT_NAME] QA",
                2: "All project delivery risks mitigated; residual risks transitioned to maintenance",
                3: "All technical and operational issues resolved; zero blocking issues remaining",
                4: "Executed and formally approved by [CLIENT_SHORT_NAME] Finance & MII Project Sponsors",
                5: "Signed upon successful UAT sign-off and completion of 2-week warranty period",
                6: "Administrative addendum for minor enhancements under final client review",
                7: "Scheduled upon handover completion; maintenance accounts provisioned separately",
                8: "Official Microsoft Forms evaluation dispatched to [CLIENT_SHORT_NAME] executive committee",
            }
            for r in range(34, 42):
                no_val = ws.cell(r, 1).value
                item_val = ws.cell(r, 2).value
                status_val = ws.cell(r, 3).value
                if item_val:
                    n_idx = int(no_val) if isinstance(no_val, (int, float)) else len(raw_checklist) + 1
                    raw_checklist.append({
                        "num": n_idx,
                        "title": str(item_val).strip(),
                        "status": str(status_val).strip() if status_val else "Yes",
                        "detail": detail_mapping.get(n_idx, "Verified and signed off by project leadership"),
                    })

            # Download link, password, CSS link from rows 48, 50, 52
            dl_link = ws.cell(48, 2).value
            pw_val = ws.cell(50, 2).value
            css_val = ws.cell(52, 2).value

            sync_results["checklist_synced"] = True
            sync_results["deliverables_synced"] = True
            sync_results["checklist_count"] = len(raw_checklist)
            sync_results["deliverables_count"] = len(raw_deliverables)
            sync_results["download_link"] = str(dl_link).strip() if dl_link else None
            sync_results["password"] = str(pw_val).strip() if pw_val else None
            sync_results["css_link"] = str(css_val).strip() if css_val else None

            # Inject into config slides
            slides_spec = self.config.get("slides", [])
            for s in slides_spec:
                arch = s.get("archetype", "")
                if arch in ("closing_checklist", "checklist"):
                    if raw_checklist:
                        s["checklist_items"] = raw_checklist
                    if dl_link:
                        s["download_link"] = str(dl_link).strip()
                    if pw_val:
                        s["password"] = str(pw_val).strip()
                    if css_val:
                        s["css_link"] = str(css_val).strip()

            logger.info(
                f"Successfully synchronized with {c_file.name}: "
                f"{len(raw_checklist)} checklist gates, {len(raw_deliverables)} deliverables."
            )
        except Exception as e:
            logger.warning(f"Error synchronizing with checklist spreadsheet {c_path}: {e}")

        return sync_results

    # -------------------------------------------------------------------------
    # Master Assembly
    # -------------------------------------------------------------------------
    def build_all(self) -> Presentation:
        """Assembles all slides according to config specification or default 9-slide sequence."""
        slides_spec = self.config.get("slides", [])

        builder_map = {
            "cover": self.build_cover,
            "agenda": self.build_agenda,
            "scope_review": self.build_scope_review,
            "ruang_lingkup": self.build_scope_review,
            "deliverables_register": self.build_deliverables_register,
            "deliverables": self.build_deliverables_register,
            "closing_checklist": self.build_closing_checklist,
            "checklist": self.build_closing_checklist,
            "maintenance_transition": self.build_maintenance_transition,
            "maintenance_flow": self.build_maintenance_flow,
            "maintenance_deliverables": self.build_maintenance_deliverables,
            "thank_you": self.build_thank_you,
        }

        if slides_spec:
            for s in slides_spec:
                archetype = s.get("archetype", "")
                if archetype in builder_map:
                    builder_map[archetype](s)
        else:
            self.build_cover()
            self.build_agenda()
            self.build_scope_review()
            self.build_deliverables_register()
            self.build_closing_checklist()
            self.build_maintenance_transition()
            self.build_maintenance_flow()
            self.build_maintenance_deliverables()
            self.build_thank_you()

        return self.prs

    def update_pagination(self) -> None:
        """Post-processes all slides to ensure pagination numbers match total slide count."""
        total_slides = len(self.prs.slides)
        for s_idx, slide in enumerate(self.prs.slides, start=1):
            for shape in slide.shapes:
                if not getattr(shape, "has_text_frame", False) or not shape.has_text_frame:
                    continue
                try:
                    if getattr(shape, "top", None) is not None and shape.top < Inches(6.8):
                        continue
                except Exception:
                    pass
                for paragraph in shape.text_frame.paragraphs:
                        text_clean = paragraph.text.strip()
                        if re.match(r"^\d{2}\s*/\s*\d{2}$", text_clean):
                            new_page_str = f"{s_idx:02d} / {total_slides:02d}"
                            if paragraph.runs:
                                r0 = paragraph.runs[0]
                                font_name = r0.font.name
                                font_size = r0.font.size
                                font_bold = r0.font.bold
                                font_color = r0.font.color.rgb if (r0.font.color and r0.font.color.type == 1) else None
                                paragraph.text = new_page_str
                                if paragraph.runs:
                                    nr = paragraph.runs[0]
                                    nr.font.name = font_name
                                    nr.font.size = font_size
                                    nr.font.bold = font_bold
                                    if font_color:
                                        nr.font.color.rgb = font_color
                            else:
                                paragraph.text = new_page_str

    def save(
        self,
        output_path: Union[str, Path],
        engagement_context: Optional[Any] = None,
    ) -> Path:
        """Synchronizes pagination, optionally substitutes slugs, and saves presentation deck."""
        self.update_pagination()
        try:
            from src.core.slug_registry import EngagementContext, substitute_slugs_in_presentation
            ctx = engagement_context or EngagementContext.default_ngl()
            substitute_slugs_in_presentation(self.prs, ctx)
        except Exception as e:
            logger.warning(f"Failed to substitute slugs in presentation: {e}")
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(p))
        return p
