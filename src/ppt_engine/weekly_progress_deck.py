"""
Weekly Progress Deck Builder Subsystem
======================================
Builds the canonical 11-slide Executive Weekly Progress Report presentation
deck for enterprise cloud modernizations, conforming to consulting frameworks,
the 60-30-10 palette distribution, and geometric integrity rules:

  Slide 01: Cover Slide (Dual vertical brand stripes, clean typographic metadata)
  Slide 02: Table of Contents / Executive Agenda (Structured numbered cards)
  Slide 03: Executive Summary / Project Management Plan (4 pillars with icon header badges)
  Slide 04: Overall Progress & S-Curve Performance (4 KPI metrics + phase delivery rows)
  Slide 05: Weekly Activity Detail (Chronological: Phase 1 Left -> Phase 2 Middle -> Phase 3 Right)
  Slide 06: Two-Week Lookahead Plan (2 weekly horizon cards + dependency callout)
  Slide 07: Contractual Milestone Status (Native vector row cards with rounded status pills)
  Slide 08: Risk Register (3-Tier Columns: Red, Orange, Yellow with 3-Box Scaling Meters)
  Slide 09: Issue Log & Corrective Action (Detailed root cause & impact breakdown)
  Slide 10: Section Divider / Q&A (Chapter divider archetype with translucent scrim)
  Slide 11: Thank You & Practice Contacts (Brand emblem lockup & team contacts)

Strictly enforces:
  - Zero overlapping top lines on rounded cards (MSO_SHAPE.RECTANGLE on all striped containers).
  - Unified title and subtitle frame (single text frame, space_before = Pt(10)).
  - Clean typographic metadata on cover (zero boxed containers, no cover footer/pagination).
  - Synchronized bottom pagination ('02 / 11' to '11 / 11').
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
from pptx.util import Inches, Pt

from src.ppt_engine.consulting_archetypes import (
    ConsultingDeckBuilder,
    add_card,
    add_card_with_top_stripe,
    add_slide_footer,
    add_slide_header,
    add_slide_with_background,
    build_chapter_divider_slide,
    build_cover_slide,
    create_presentation,
)
from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb

logger = logging.getLogger(__name__)


def generate_s_curve_chart_image(
    points: List[Any],
    output_path: Union[str, Path],
    theme: Optional[Theme] = None,
    title: str = "Cumulative S-Curve Progression (Weekly Intervals)",
) -> Path:
    """
    Renders a high-DPI (200 DPI) consulting S-curve chart from cumulative progression points.
    Matches corporate color palette (Planned: #0052CC, Actual: #10B981, Variance: #EF4444).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.8, 3.0), dpi=200, facecolor="#FFFFFF")
    ax.set_facecolor("#F8FAFC")

    periods = [getattr(p, "period", str(p)).split(" ")[0] for p in points]
    planned = [getattr(p, "planned_pct", 0.0) * 100 for p in points]
    actuals = [
        getattr(p, "actual_pct", None) * 100
        if getattr(p, "actual_pct", None) is not None
        else None
        for p in points
    ]

    actual_x = [i for i, v in enumerate(actuals) if v is not None]
    actual_y = [v for v in actuals if v is not None]

    # Primary Line: Planned Baseline (PV)
    ax.plot(
        range(len(periods)),
        planned,
        color="#0052CC",
        linewidth=2.5,
        marker="o",
        markersize=4,
        label="Planned Baseline (PV)",
        zorder=3,
    )

    # Secondary Line: Actual Progress (EV)
    if actual_x:
        ax.plot(
            actual_x,
            actual_y,
            color="#10B981",
            linewidth=2.8,
            marker="s",
            markersize=5,
            label="Actual Progress (EV)",
            zorder=4,
        )
        planned_slice = [planned[i] for i in actual_x]
        ax.fill_between(
            actual_x,
            actual_y,
            planned_slice,
            color="#EF4444",
            alpha=0.18,
            label="Schedule Variance (SV)",
            zorder=2,
        )

    ax.set_ylim(0, 105)
    ax.set_ylabel("Progress (%)", fontsize=9, fontweight="bold", color="#1E293B")
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0F172A", pad=8)
    ax.grid(True, linestyle="--", alpha=0.5, color="#CBD5E1", zorder=1)

    step = max(1, len(periods) // 10)
    tick_indices = list(range(0, len(periods), step))
    if (len(periods) - 1) not in tick_indices:
        tick_indices.append(len(periods) - 1)
    ax.set_xticks(tick_indices)
    ax.set_xticklabels([periods[i] for i in tick_indices], fontsize=8, color="#475569")
    ax.tick_params(colors="#475569", labelsize=8)

    for spine in ax.spines.values():
        spine.set_color("#E2E8F0")

    ax.legend(
        loc="upper left",
        fontsize=8,
        framealpha=0.95,
        facecolor="#FFFFFF",
        edgecolor="#E2E8F0",
    )
    plt.tight_layout()
    fig.savefig(str(out_p), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_p


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
    if override_color_key:
        if override_color_key == "danger":
            bg_key, text_key = ("badge_red_fill", "badge_red_text")
        elif override_color_key == "warning":
            bg_key, text_key = ("badge_amber_fill", "badge_amber_text")
        elif override_color_key == "success":
            bg_key, text_key = ("badge_green_fill", "badge_green_text")
        else:
            bg_key, text_key = ("badge_blue_fill", "badge_blue_text")
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


def _get_tinted_icon(
    theme: Theme,
    icon_name: str,
    color_key_or_hex: str,
) -> Optional[Path]:
    """
    Dynamically fetch, tint, and render a vector icon matching the container's accent color.
    Resolves theme color keys ('danger', 'warning', 'accent') or raw hex strings ('#DC2626').
    """
    if color_key_or_hex.startswith("#"):
        target_hex = color_key_or_hex
    else:
        target_hex = theme.get_hex(color_key_or_hex, default="#0052CC")

    try:
        from src.ppt_engine.icon_engine import get_brand_icon
        return get_brand_icon(identifier=icon_name, brand_color=target_hex, size=512)
    except Exception as e:
        logger.warning(f"Failed to dynamically tint icon {icon_name} with {target_hex}: {e}")
        fallback = Path(f"assets/icons/lucide/{icon_name}.png")
        return fallback if fallback.exists() else None


def _add_bullet_paragraph(
    tf: Any,
    text: str,
    font_name: str,
    font_size_pt: float = 12.0,
    font_color: Optional[RGBColor] = None,
    space_before_pt: float = 8.0,
    bullet_char: str = "•",
) -> Any:
    """
    Appends a bullet paragraph with an OpenXML DrawingML hanging indent (marL/indent)
    and native bullet formatting, guaranteeing that wrapped text cleanly aligns to the right
    of the bullet glyph across both native PowerPoint and headless exporters.
    """
    from pptx.oxml.xmlchemy import OxmlElement

    p = tf.add_paragraph()
    clean_text = text.lstrip("•\t -*").strip()
    p.text = clean_text
    p.font.name = font_name
    p.font.size = Pt(font_size_pt)
    if font_color:
        p.font.color.rgb = font_color
    p.space_before = Pt(space_before_pt)

    # DrawingML Hanging Indent: marL="288000" (0.20 in), indent="-288000"
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", "288000")
    pPr.set("indent", "-288000")

    # Native DrawingML bullet element
    buChar = OxmlElement("a:buChar")
    buChar.set("char", bullet_char)
    pPr.append(buChar)
    return p


def _draw_3_box_meter(
    slide: Any,
    left: Inches,
    top: Inches,
    label: str,
    filled_count: int,
    active_color: RGBColor,
    border_color: RGBColor,
    font_family: str,
) -> None:
    """Renders a 3-box visual scaling meter (e.g. [■] [■] [□]) with a bold label."""
    tb = slide.shapes.add_textbox(left, top, Inches(1.90), Inches(0.24))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = label
    p.font.name = font_family
    p.font.size = Pt(9.0)
    p.font.bold = True
    p.font.color.rgb = active_color

    box_start_x = left + Inches(1.95)
    box_size = Inches(0.18)
    box_gap = Inches(0.06)
    for b_idx in range(3):
        bx = box_start_x + b_idx * (box_size + box_gap)
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, top + Inches(0.02), box_size, box_size)
        box.shadow.inherit = False
        box.fill.solid()
        if b_idx < filled_count:
            box.fill.fore_color.rgb = active_color
            box.line.color.rgb = active_color
        else:
            box.fill.fore_color.rgb = RGBColor(241, 245, 249)
            box.line.color.rgb = border_color
        box.line.width = Pt(1.0)


class WeeklyProgressDeckBuilder:
    """High-level builder for generating 11-slide Weekly Progress consulting decks."""

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
    ) -> WeeklyProgressDeckBuilder:
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
            title=d.get("title", self.metadata.get("project_name", "ENTERPRISE FINANCIAL INTELLIGENCE & CLOUD ANALYTICS PLATFORM")),
            subtitle=d.get("subtitle", f"Weekly Progress Report #{self.metadata.get('report_number', '01')}"),
            client=d.get("client", self.metadata.get("client_name", "Nusantara Global Logistics")),
            vendor=d.get("vendor", self.metadata.get("vendor_name", "PT Metrodata Electronics Tbk")),
            product=d.get("product", "Snowflake AI Data Cloud"),
            date_str=d.get("date_str", self.metadata.get("report_date", "05 Jan 2000")),
            tracker=d.get("tracker", "PROJECT GOVERNANCE & WEEKLY STATUS"),
            client_sublabel=d.get("client_sublabel", "Steering Committee & Executive Sponsors"),
            vendor_sublabel=d.get("vendor_sublabel", "Data & AI Modernization Practice"),
        )

    # -------------------------------------------------------------------------
    # Slide 2: Table of Contents / Agenda
    # -------------------------------------------------------------------------
    def build_agenda(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "EXECUTIVE SUMMARY | AGENDA"),
            action_title=d.get("title", "Project Status & Governance Agenda"),
            subtitle=d.get("subtitle", "Structured weekly review covering delivery progress, milestones, lookahead, and RAID governance."),
        )

        items = d.get("items", [])
        if not items:
            items = [
                {"num": "01", "title": "Project Management Plan", "description": "Tata kelola proyek, peran tim, dan baseline manajemen."},
                {"num": "02", "title": "Overall Progress & S-Curve", "description": "Evaluasi progres durasi, bobot pekerjaan, dan deviasi."},
                {"num": "03", "title": "Detail Aktivitas Mingguan", "description": "Pencapaian aktivitas pada periode pelaporan aktif."},
                {"num": "04", "title": "Rencana Aktivitas Minggu Depan", "description": "Prioritas kerja dan target delivery 2 pekan mendatang."},
                {"num": "05", "title": "Status Milestone", "description": "Tracking capaian target milestone kontrak dan delivery."},
                {"num": "06", "title": "Risk Register & Issue Log", "description": "Manajemen risiko aktif, mitigasi, dan resolusi issue."},
                {"num": "07", "title": "Q&A & Diskusi Terbuka", "description": "Forum koordinasi, klarifikasi teknis, dan keputusan."},
            ]

        col_w = Inches(5.70)
        card_h = Inches(1.10)
        gap_y = Inches(0.18)
        left_col_x = Inches(0.80)
        right_col_x = Inches(6.833)
        start_y = Inches(1.85)

        half = (len(items) + 1) // 2
        for i, item in enumerate(items):
            is_right = i >= half
            col_x = right_col_x if is_right else left_col_x
            row_idx = i - half if is_right else i
            card_y = start_y + row_idx * (card_h + gap_y)

            card = add_card(
                slide,
                self.theme,
                col_x,
                card_y,
                col_w,
                card_h,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            num_w = Inches(0.85)
            badge_bg = self.theme.get_rgb("accent") if i == 0 else self.theme.get_rgb("surface_muted")
            num_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col_x, card_y, num_w, card_h)
            num_box.shadow.inherit = False
            num_box.fill.solid()
            num_box.fill.fore_color.rgb = badge_bg
            num_box.line.fill.background()

            ntf = num_box.text_frame
            ntf.word_wrap = False
            ntf.margin_left = ntf.margin_right = ntf.margin_top = ntf.margin_bottom = 0
            np = ntf.paragraphs[0]
            np.text = str(item.get("num", f"{i+1:02d}"))
            np.alignment = PP_ALIGN.CENTER
            np.font.name = self.theme.font_family_header
            np.font.size = Pt(18.0)
            np.font.bold = True
            np.font.color.rgb = RGBColor(255, 255, 255) if i == 0 else self.theme.get_rgb("primary")

            tb = slide.shapes.add_textbox(col_x + num_w + Inches(0.18), card_y + Inches(0.12), col_w - num_w - Inches(0.30), card_h - Inches(0.24))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            tp = tf.paragraphs[0]
            tp.text = item.get("title", "")
            tp.font.name = self.theme.font_family_header
            tp.font.size = Pt(14.5)
            tp.font.bold = True
            tp.font.color.rgb = self.theme.get_rgb("primary")

            dp = tf.add_paragraph()
            dp.text = item.get("description", "")
            dp.font.name = self.theme.font_family
            dp.font.size = Pt(11.0)
            dp.font.color.rgb = self.theme.get_rgb("secondary")
            dp.space_before = Pt(4)

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 3: Executive Summary / Project Management Plan (Scaled-up Typography & Icons)
    # -------------------------------------------------------------------------
    def build_exec_summary(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "GOVERNANCE FRAMEWORK | SECTION 01"),
            action_title=d.get("title", "Project Management Plan Establishes Governance & Quality Baselines"),
            subtitle=d.get("subtitle", "Penyampaian singkat dokumen Project Management Plan dan kerangka kerja eksekusi."),
        )

        cards = d.get("cards", [])
        if not cards:
            cards = [
                {
                    "title": "Scope & Deliverables",
                    "tag": "SCOPE BASELINE",
                    "icon_name": "target",
                    "summary": "Modernisasi analitik data finansial berbasis platform cloud enterprise.",
                    "points": ["Definisi 4 use case analitik finansial.", "Staging, dbt transformation pipelines.", "Integrasi reporting BI dan summarization."],
                },
                {
                    "title": "Team Governance & RACI",
                    "tag": "TEAM ALIGNMENT",
                    "icon_name": "users",
                    "summary": "Struktur tim gabungan NGL dan MII beroperasi dengan peran yang jelas.",
                    "points": ["Project Manager memimpin koordinasi harian.", "Lead Data Architect mengawal arsitektur.", "Weekly Progress Review berkala."],
                },
                {
                    "title": "Quality & Acceptance Gate",
                    "tag": "QUALITY ASSURANCE",
                    "icon_name": "shield-check",
                    "summary": "Verifikasi bertingkat sebelum sign-off dan serah terima resmi.",
                    "points": ["SIT internal dengan zero critical defect.", "UAT bersama Business Owner NGL.", "Sign-off formal BAST per termin."],
                },
                {
                    "title": "Communication & Reporting",
                    "tag": "COMMUNICATION PROTOCOL",
                    "icon_name": "radio",
                    "summary": "Transparansi status melalui pelaporan berkala dan dokumentasi terpusat.",
                    "points": ["Weekly Progress Report setiap hari Senin.", "MoM formal untuk clarification meeting.", "Eskalasi issue ke Steering Committee."],
                },
            ]

        card_count = len(cards)
        gap_x = Inches(0.22)
        total_w = Inches(11.733)
        card_w = (total_w - (card_count - 1) * gap_x) / card_count
        card_h = Inches(4.95)
        card_y = Inches(1.60)

        for i, c in enumerate(cards):
            card_x = Inches(0.80) + i * (card_w + gap_x)
            acc_key = "accent" if i % 2 == 0 else "accent_secondary"
            accent_rgb = self.theme.get_rgb(acc_key)
            accent_hex = self.theme.get_hex(acc_key)

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=card_x,
                top=card_y,
                width=card_w,
                height=card_h,
                accent_rgb=accent_rgb,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.08,
            )

            # 1. Top Icon Badge Container (0.52" x 0.52")
            icon_key = c.get("icon_name", ["target", "users", "shield-check", "radio"][i % 4])
            badge_fill_key = "badge_blue_fill" if i % 2 == 0 else "badge_red_fill"

            icon_box_w = Inches(0.52)
            icon_box_h = Inches(0.52)
            icon_box_x = card_x + Inches(0.18)
            icon_box_y = card_y + Inches(0.16)

            icon_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                icon_box_x,
                icon_box_y,
                icon_box_w,
                icon_box_h,
            )
            icon_box.shadow.inherit = False
            icon_box.fill.solid()
            icon_box.fill.fore_color.rgb = self.theme.get_rgb(badge_fill_key, default="#F8FAFC")
            icon_box.line.color.rgb = accent_rgb
            icon_box.line.width = Pt(1.0)

            icon_file = _get_tinted_icon(self.theme, icon_key, accent_hex)
            if icon_file and icon_file.exists():
                slide.shapes.add_picture(
                    str(icon_file),
                    icon_box_x + Inches(0.08),
                    icon_box_y + Inches(0.08),
                    width=Inches(0.36),
                    height=Inches(0.36),
                )

            # Prominent Section Tag on the right of icon badge
            tag_box_x = icon_box_x + icon_box_w + Inches(0.08)
            tag_box_y = icon_box_y
            tag_box_w = card_w - (icon_box_w + Inches(0.18) + Inches(0.08) + Inches(0.08))
            tag_box_h = icon_box_h

            tag_box = slide.shapes.add_textbox(tag_box_x, tag_box_y, tag_box_w, tag_box_h)
            tag_tf = tag_box.text_frame
            tag_tf.word_wrap = True
            tag_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tag_tf.margin_left = tag_tf.margin_right = tag_tf.margin_top = tag_tf.margin_bottom = 0
            tag_p = tag_tf.paragraphs[0]
            tag_p.text = c.get("tag", f"PILLAR {i+1:02d}").upper()
            tag_p.font.name = self.theme.font_family_header
            tag_p.font.size = Pt(8.5)
            tag_p.font.bold = True
            tag_p.font.color.rgb = accent_rgb

            # 2. Main Narrative & Bullet Points below icon
            content_top = icon_box_y + icon_box_h + Inches(0.12)
            title_h = Inches(0.58)

            # Dedicated Title Box (fixed height for uniform baseline alignment across all cards)
            title_box = slide.shapes.add_textbox(card_x + Inches(0.18), content_top, card_w - Inches(0.36), title_h)
            title_tf = title_box.text_frame
            title_tf.word_wrap = True
            title_tf.margin_left = title_tf.margin_right = title_tf.margin_top = title_tf.margin_bottom = 0

            t_p = title_tf.paragraphs[0]
            t_p.text = c.get("title", "")
            t_p.font.name = self.theme.font_family_header
            t_p.font.size = Pt(15.5)
            t_p.font.bold = True
            t_p.font.color.rgb = self.theme.get_rgb("primary")

            # Dedicated Body Box (Summary + Bullets) aligned across all cards
            body_top = content_top + title_h + Inches(0.06)
            body_h = card_h - (body_top - card_y) - Inches(0.16)
            body_box = slide.shapes.add_textbox(card_x + Inches(0.18), body_top, card_w - Inches(0.36), body_h)
            tf = body_box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            # Column Summary (12.0pt italic)
            s_p = tf.paragraphs[0]
            s_p.text = c.get("summary", "")
            s_p.font.name = self.theme.font_family
            s_p.font.size = Pt(12.0)
            s_p.font.italic = True
            s_p.font.color.rgb = self.theme.get_rgb("secondary")

            # Bullet points with OpenXML Hanging Indents (11.5pt)
            points = c.get("points", [])
            for pt in points:
                _add_bullet_paragraph(
                    tf=tf,
                    text=pt,
                    font_name=self.theme.font_family,
                    font_size_pt=11.5,
                    font_color=self.theme.get_rgb("primary"),
                    space_before_pt=7.0,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 4: Overall Progress & S-Curve KPI (Native Vector Phase Rows)
    # -------------------------------------------------------------------------
    def build_overall_progress(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "OVERALL PROGRESS | S-CURVE & SCHEDULE PERFORMANCE"),
            action_title=d.get("title", "Progress Tracks Within Tolerable Variance with Phase 1 Transition Underway"),
            subtitle=d.get("subtitle", "Planned duration 12.6% vs actual completion 12.0% (Gap: -0.6% variance managed under Issue #1)."),
        )

        # 1. Top Row: 4 Metric Cards
        kpis = d.get("kpis", [
            {"label": "Planned Progress", "value": "12.6%", "subtext": "Baseline Target Week 03", "status": "PLANNED"},
            {"label": "Actual Progress", "value": "12.0%", "subtext": "Cumulative Completed", "status": "ON TRACK"},
            {"label": "Schedule Variance", "value": "-0.6%", "subtext": "Tolerance: +/- 2.0%", "status": "AT RISK"},
            {"label": "Overall Health", "value": "AMBER", "subtext": "Minor delay; Go-Live protected", "status": "AT RISK"},
        ])
        kpi_count = len(kpis)
        gap_kpi = Inches(0.20)
        total_w = Inches(11.733)
        kpi_w = (total_w - (kpi_count - 1) * gap_kpi) / kpi_count
        kpi_h = Inches(1.35)
        kpi_y = Inches(1.60)

        for i, k in enumerate(kpis):
            kx = Inches(0.80) + i * (kpi_w + gap_kpi)
            kcard = add_card(
                slide,
                self.theme,
                kx,
                kpi_y,
                kpi_w,
                kpi_h,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            _add_status_pill(
                slide=slide,
                theme=self.theme,
                left=kx + kpi_w - Inches(1.02),
                top=kpi_y + Inches(0.12),
                width=Inches(0.90),
                height=Inches(0.24),
                status=k.get("status", "ON TRACK"),
                font_size_pt=8.0,
            )

            tb_lbl = slide.shapes.add_textbox(kx + Inches(0.14), kpi_y + Inches(0.12), kpi_w - Inches(1.06), Inches(0.22))
            tf_lbl = tb_lbl.text_frame
            tf_lbl.word_wrap = False
            tf_lbl.margin_left = tf_lbl.margin_right = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
            lp = tf_lbl.paragraphs[0]
            lp.text = k.get("label", "").upper()
            lp.font.name = self.theme.font_family_header
            lp.font.size = Pt(8.0)
            lp.font.bold = True
            lp.font.color.rgb = self.theme.get_rgb("muted")

            tb_val = slide.shapes.add_textbox(kx + Inches(0.14), kpi_y + Inches(0.42), kpi_w - Inches(0.28), kpi_h - Inches(0.46))
            tf_val = tb_val.text_frame
            tf_val.word_wrap = False
            tf_val.margin_left = tf_val.margin_right = tf_val.margin_top = tf_val.margin_bottom = 0

            vp = tf_val.paragraphs[0]
            vp.text = k.get("value", "")
            vp.font.name = self.theme.font_family_header
            vp.font.size = Pt(24.0)
            vp.font.bold = True
            val_color = self.theme.get_rgb("primary")
            if "AMBER" in k.get("value", "") or "-" in k.get("value", ""):
                val_color = self.theme.get_rgb("warning")
            vp.font.color.rgb = val_color

            sp = tf_val.add_paragraph()
            sp.text = k.get("subtext", "")
            sp.font.name = self.theme.font_family
            sp.font.size = Pt(9.0)
            sp.font.color.rgb = self.theme.get_rgb("secondary")
            sp.space_before = Pt(2)

        # 2. Bottom Row: Split Container
        bottom_y = kpi_y + kpi_h + Inches(0.20)
        bottom_h = Inches(3.40)
        left_w = Inches(4.50)
        right_w = total_w - left_w - Inches(0.25)

        # Left Card: Executive Observations
        left_card, _ = add_card_with_top_stripe(
            slide,
            self.theme,
            Inches(0.80),
            bottom_y,
            left_w,
            bottom_h,
            accent_rgb=self.theme.get_rgb("accent"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.08,
        )

        ltb = slide.shapes.add_textbox(Inches(0.80) + Inches(0.18), bottom_y + Inches(0.20), left_w - Inches(0.36), bottom_h - Inches(0.35))
        ltf = ltb.text_frame
        ltf.word_wrap = True
        ltf.margin_left = ltf.margin_right = ltf.margin_top = ltf.margin_bottom = 0

        lp1 = ltf.paragraphs[0]
        lp1.text = "EXECUTIVE OBSERVATIONS & VARIANCE CONTEXT"
        lp1.font.name = self.theme.font_family_header
        lp1.font.size = Pt(11.0)
        lp1.font.bold = True
        lp1.font.color.rgb = self.theme.get_rgb("accent")

        narrative = d.get(
            "status_narrative",
            "Keterlambatan minor pada beberapa aktivitas asesmen FSD, namun buffer jadwal fase development memastikan target Go-Live tetap aman sesuai baseline awal."
        )
        lp2 = ltf.add_paragraph()
        lp2.text = narrative
        lp2.font.name = self.theme.font_family
        lp2.font.size = Pt(11.5)
        lp2.font.color.rgb = self.theme.get_rgb("primary")
        lp2.space_before = Pt(8)

        _add_bullet_paragraph(ltf, "Deviasi jadwal (-0.6%) terlokalisasi pada dokumen FSD modul akuntansi.", self.theme.font_family, 11.0, self.theme.get_rgb("secondary"), 8.0)
        _add_bullet_paragraph(ltf, "Penyesuaian jadwal asesmen ke tanggal 09 Jan 2000 telah disepakati bersama user.", self.theme.font_family, 11.0, self.theme.get_rgb("secondary"), 6.0)
        _add_bullet_paragraph(ltf, "Tidak ada pergeseran target Go-Live (13 Mar 2000) maupun final BAST (27 Mar 2000).", self.theme.font_family, 11.0, self.theme.get_rgb("secondary"), 6.0)

        # Right Card: Phase Rows or Embedded S-Curve Chart
        right_x = Inches(0.80) + left_w + Inches(0.25)
        chart_path = d.get("chart_image")
        right_title = "CUMULATIVE S-CURVE & SCHEDULE VARIANCE" if chart_path else "DELIVERY PHASE EXECUTION PROGRESS"

        right_card, _ = add_card_with_top_stripe(
            slide,
            self.theme,
            right_x,
            bottom_y,
            right_w,
            bottom_h,
            accent_rgb=self.theme.get_rgb("accent_secondary"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.08,
        )

        rtb = slide.shapes.add_textbox(right_x + Inches(0.18), bottom_y + Inches(0.20), right_w - Inches(0.36), Inches(0.30))
        rtf = rtb.text_frame
        rtf.word_wrap = True
        rtf.margin_left = rtf.margin_right = rtf.margin_top = rtf.margin_bottom = 0
        rp1 = rtf.paragraphs[0]
        rp1.text = right_title
        rp1.font.name = self.theme.font_family_header
        rp1.font.size = Pt(11.0)
        rp1.font.bold = True
        rp1.font.color.rgb = self.theme.get_rgb("accent_secondary")

        if chart_path and Path(chart_path).exists():
            chart_x = right_x + Inches(0.15)
            chart_y = bottom_y + Inches(0.55)
            chart_w = right_w - Inches(0.30)
            chart_h = bottom_h - Inches(0.70)
            slide.shapes.add_picture(
                str(chart_path),
                chart_x,
                chart_y,
                width=chart_w,
                height=chart_h,
            )
        else:
            phases = d.get("phases", [
                {"phase": "Phase 1: Project Initiation & Charter", "planned": "100%", "actual": "100%", "status": "COMPLETED"},
                {"phase": "Phase 2: Architecture & FSD Assessment", "planned": "90%", "actual": "85%", "status": "IN PROGRESS"},
                {"phase": "Phase 3: Cloud Platform Setup & Staging", "planned": "25%", "actual": "25%", "status": "ON TRACK"},
                {"phase": "Phase 4: Data Modeling & ETL Pipelines", "planned": "0%", "actual": "0%", "status": "PLANNED"},
                {"phase": "Phase 5: SIT, UAT & Go-Live Cutover", "planned": "0%", "actual": "0%", "status": "PLANNED"},
            ])

            row_y_start = bottom_y + Inches(0.55)
            phase_row_h = Inches(0.48)
            gap_pr = Inches(0.06)

            for p_idx, ph in enumerate(phases):
                pry = row_y_start + p_idx * (phase_row_h + gap_pr)
                pr_card = add_card(
                    slide,
                    self.theme,
                    right_x + Inches(0.15),
                    pry,
                    right_w - Inches(0.30),
                    phase_row_h,
                    bg_color=self.theme.get_rgb("surface_muted") if p_idx % 2 == 0 else self.theme.get_rgb("surface"),
                    border_color=self.theme.get_rgb("border"),
                    force_rectangle=True,
                )

                ptb = slide.shapes.add_textbox(right_x + Inches(0.25), pry + Inches(0.08), right_w - Inches(1.80), phase_row_h - Inches(0.16))
                ptf = ptb.text_frame
                ptf.word_wrap = True
                ptf.margin_left = ptf.margin_right = ptf.margin_top = ptf.margin_bottom = 0

                pp0 = ptf.paragraphs[0]
                pp0.text = ph.get("phase", "")
                pp0.font.name = self.theme.font_family_header
                pp0.font.size = Pt(10.5)
                pp0.font.bold = True
                pp0.font.color.rgb = self.theme.get_rgb("primary")

                pp_m = ptf.add_paragraph()
                pp_m.text = f"Planned: {ph.get('planned', '0%')}   |   Actual: {ph.get('actual', '0%')}"
                pp_m.font.name = self.theme.font_family
                pp_m.font.size = Pt(9.5)
                pp_m.font.color.rgb = self.theme.get_rgb("secondary")

                _add_status_pill(
                    slide=slide,
                    theme=self.theme,
                    left=right_x + right_w - Inches(1.45),
                    top=pry + Inches(0.10),
                    width=Inches(1.20),
                    height=Inches(0.28),
                    status=ph.get("status", "ON TRACK"),
                    font_size_pt=8.5,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 5: Weekly Activity Detail (Chronological with Hanging Indents)
    # -------------------------------------------------------------------------
    def build_weekly_detail(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", f"DETAIL AKTIVITAS MINGGUAN | {self.metadata.get('reporting_period', 'CURRENT WEEK')}"),
            action_title=d.get("title", "Completed Activities Focus on Governance Sign-Off & Architecture Assessment"),
            subtitle=d.get("subtitle", "Pencapaian aktivitas utama fase inisiasi dan asesmen teknis selama periode pelaporan."),
        )

        streams = d.get("workstreams", [])
        if not streams:
            streams = [
                {
                    "stream": "Project Governance & Admin",
                    "badge": "PHASE 01",
                    "items": [
                        "Kick-off meeting resmi bersama Steering Committee dan Business Owner NGL.",
                        "Penerbitan MoM inisiasi dan baseline Project Charter bertandatangan.",
                        "Registrasi risiko awal dan kesepakatan tata kelola eskalasi.",
                        "Setup repository dokumentasi terpusat dan kanal koordinasi harian.",
                    ],
                },
                {
                    "stream": "Architecture & Assessment (FSD)",
                    "badge": "PHASE 02",
                    "items": [
                        "Wawancara kebutuhan modul Financial Summary dan Journal Entries.",
                        "Penyusunan draft awal Functional Specification Document (FSD v0.8).",
                        "Identifikasi struktur data source dan relasi database eksisting.",
                        "Review data dictionary dan katalog entitas akuntansi NGL.",
                    ],
                },
                {
                    "stream": "Platform Infrastructure & Setup",
                    "badge": "PHASE 03",
                    "items": [
                        "Provisioning akun Cloud Data Platform Enterprise Edition di AWS region.",
                        "Konfigurasi Virtual Warehouse (Compute XS/S) dan Resource Monitors.",
                        "Penyusunan baseline Role-Based Access Control (RBAC) dan network policy.",
                        "Pemberian akses developer dan integrasi authentication SSO.",
                    ],
                },
            ]

        col_count = len(streams)
        gap_x = Inches(0.24)
        total_w = Inches(11.733)
        col_w = (total_w - (col_count - 1) * gap_x) / col_count
        col_h = Inches(4.95)
        col_y = Inches(1.60)

        for i, s in enumerate(streams):
            col_x = Inches(0.80) + i * (col_w + gap_x)
            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=col_x,
                top=col_y,
                width=col_w,
                height=col_h,
                accent_rgb=self.theme.get_rgb("accent") if i == 0 else (self.theme.get_rgb("accent_teal") if i == 1 else self.theme.get_rgb("secondary")),
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.08,
            )

            _add_status_pill(
                slide=slide,
                theme=self.theme,
                left=col_x + col_w - Inches(1.15),
                top=col_y + Inches(0.16),
                width=Inches(0.96),
                height=Inches(0.26),
                status=s.get("badge", f"PHASE 0{i+1}"),
                font_size_pt=8.5,
            )

            tb_title = slide.shapes.add_textbox(col_x + Inches(0.18), col_y + Inches(0.14), col_w - Inches(1.40), Inches(0.65))
            tf_title = tb_title.text_frame
            tf_title.word_wrap = True
            tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0

            tp = tf_title.paragraphs[0]
            tp.text = s.get("stream", "")
            tp.font.name = self.theme.font_family_header
            tp.font.size = Pt(14.5)
            tp.font.bold = True
            tp.font.color.rgb = self.theme.get_rgb("primary")

            tb_b = slide.shapes.add_textbox(col_x + Inches(0.18), col_y + Inches(0.92), col_w - Inches(0.36), col_h - Inches(1.05))
            tf_b = tb_b.text_frame
            tf_b.word_wrap = True
            tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0

            # Checklists with hanging indents
            items = s.get("items", [])
            for item_text in items:
                _add_bullet_paragraph(
                    tf=tf_b,
                    text=item_text,
                    font_name=self.theme.font_family,
                    font_size_pt=11.5,
                    font_color=self.theme.get_rgb("primary"),
                    space_before_pt=6.0,
                )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 6: Lookahead Plan (Scaled-up with Hanging Indents)
    # -------------------------------------------------------------------------
    def build_lookahead_plan(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "RENCANA AKTIVITAS MINGGU DEPAN | 2-WEEK LOOKAHEAD"),
            action_title=d.get("title", "Two-Week Lookahead Prioritizes FSD Finalization & Data Ingestion Staging"),
            subtitle=d.get("subtitle", "Rencana eksekusi terfokus pada finalisasi asesmen use case dan persiapan environment staging."),
        )

        periods = d.get("periods", [])
        if not periods:
            periods = [
                {
                    "period_label": "Pekan 1: 05 Jan - 09 Jan 2000",
                    "target_milestone": "FSD Assessment Finalization",
                    "tasks": [
                        "Lanjutan meeting asesmen use-case automated analytics dengan key user (09 Jan 2000).",
                        "Finalisasi data dictionary dan mapping tabel transaksi keuangan.",
                        "Review kapasitas komputasi warehouse dan konfigurasi storage integration.",
                        "Penyusunan draft final FSD untuk review internal stakeholder.",
                    ],
                },
                {
                    "period_label": "Pekan 2: 12 Jan - 16 Jan 2000",
                    "target_milestone": "FSD Sign-Off & Pipeline Kickoff",
                    "tasks": [
                        "Walkthrough komprehensif FSD bersama project owner dan tim business NGL.",
                        "Persetujuan dan formal sign-off dokumen FSD (Target: 19 Jan 2000).",
                        "Kick-off sprint ingestion staging pipeline menggunakan dbt.",
                        "Verifikasi network connectivity dan secure tunnel ke on-premise source.",
                    ],
                },
            ]

        col_w = Inches(5.72)
        top_h = Inches(3.40)
        top_y = Inches(1.60)

        for i, p in enumerate(periods[:2]):
            col_x = Inches(0.80) + i * (col_w + Inches(0.29))
            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=col_x,
                top=top_y,
                width=col_w,
                height=top_h,
                accent_rgb=self.theme.get_rgb("accent") if i == 0 else self.theme.get_rgb("accent_teal"),
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.08,
            )

            _add_status_pill(
                slide=slide,
                theme=self.theme,
                left=col_x + col_w - Inches(2.35),
                top=top_y + Inches(0.16),
                width=Inches(2.20),
                height=Inches(0.26),
                status=p.get("target_milestone", "MILESTONE TARGET"),
                font_size_pt=8.5,
            )

            tb_title = slide.shapes.add_textbox(col_x + Inches(0.18), top_y + Inches(0.14), col_w - Inches(2.45), Inches(0.35))
            tf_title = tb_title.text_frame
            tf_title.word_wrap = True
            tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0

            pp = tf_title.paragraphs[0]
            pp.text = p.get("period_label", "")
            pp.font.name = self.theme.font_family_header
            pp.font.size = Pt(15.0)
            pp.font.bold = True
            pp.font.color.rgb = self.theme.get_rgb("primary")

            tb_tasks = slide.shapes.add_textbox(col_x + Inches(0.18), top_y + Inches(0.55), col_w - Inches(0.36), top_h - Inches(0.65))
            tf_tasks = tb_tasks.text_frame
            tf_tasks.word_wrap = True
            tf_tasks.margin_left = tf_tasks.margin_right = tf_tasks.margin_top = tf_tasks.margin_bottom = 0

            tasks = p.get("tasks", [])
            for t_idx, task_text in enumerate(tasks, start=1):
                _add_bullet_paragraph(
                    tf=tf_tasks,
                    text=f"{task_text}",
                    font_name=self.theme.font_family,
                    font_size_pt=11.5,
                    font_color=self.theme.get_rgb("primary"),
                    space_before_pt=6.0,
                )

        # Bottom Callout: Critical Dependencies
        callout_y = top_y + top_h + Inches(0.18)
        callout_h = Inches(1.35)
        callout_w = Inches(11.733)

        c_card = add_card(
            slide=slide,
            theme=self.theme,
            left=Inches(0.80),
            top=callout_y,
            width=callout_w,
            height=callout_h,
            bg_color=self.theme.get_rgb("surface_muted"),
            border_color=self.theme.get_rgb("accent"),
            border_width_pt=1.5,
            force_rectangle=True,
        )

        ctb = slide.shapes.add_textbox(Inches(0.98), callout_y + Inches(0.12), callout_w - Inches(0.36), callout_h - Inches(0.24))
        ctf = ctb.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0

        cp1 = ctf.paragraphs[0]
        cp1.text = "CRITICAL PATH DEPENDENCY & STAKEHOLDER ACTIONS REQUIRED"
        cp1.font.name = self.theme.font_family_header
        cp1.font.size = Pt(11.0)
        cp1.font.bold = True
        cp1.font.color.rgb = self.theme.get_rgb("accent")

        cp2 = ctf.add_paragraph()
        cp2.text = (
            "1. Kesiapan key business user NGL untuk review FSD analytics pada tanggal 09 Jan 2000.\n"
            "2. Akses VPN / credential firewall dari client team untuk network connectivity staging cloud platform."
        )
        cp2.font.name = self.theme.font_family
        cp2.font.size = Pt(10.5)
        cp2.font.color.rgb = self.theme.get_rgb("secondary")
        cp2.space_before = Pt(4)

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 7: Milestone Status (Native Vector Row Cards + Status Pills)
    # -------------------------------------------------------------------------
    def build_milestone_status(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "STATUS MILESTONE | CONTRACTUAL DELIVERY SCHEDULE"),
            action_title=d.get("title", "Baseline Milestones Remain Protected with FSD Buffer Absorption"),
            subtitle=d.get("subtitle", "Pergeseran jadwal FSD diserap oleh buffer fase development tanpa menggeser target Go-Live."),
        )

        milestones = d.get("milestones", [
            {"num": "01", "name": "Kick-off Meeting", "target_date": "16 Dec 2025", "actual_date": "16 Dec 2025", "status": "COMPLETED"},
            {"num": "02", "name": "Functional Specification Document (FSD) Sign-off", "target_date": "02 Jan 2026", "actual_date": "19 Jan 2026", "status": "RESCHEDULED"},
            {"num": "03", "name": "Cloud Platform Subscription Started", "target_date": "02 Jan 2026", "actual_date": "02 Jan 2026", "status": "COMPLETED"},
            {"num": "04", "name": "Core Data Pipeline Development Complete", "target_date": "13 Feb 2026", "actual_date": "13 Feb 2026", "status": "ON TRACK"},
            {"num": "05", "name": "System Integration Testing (SIT) Sign-off", "target_date": "24 Feb 2026", "actual_date": "24 Feb 2026", "status": "ON TRACK"},
            {"num": "06", "name": "User Acceptance Testing (UAT) Sign-off", "target_date": "31 Mar 2026", "actual_date": "31 Mar 2026", "status": "ON TRACK"},
            {"num": "07", "name": "Go-Live & Production Cutover", "target_date": "01 Apr 2026", "actual_date": "01 Apr 2026", "status": "ON TRACK"},
            {"num": "08", "name": "Technical Specification Document (TSD) Sign-off", "target_date": "08 Apr 2026", "actual_date": "08 Apr 2026", "status": "ON TRACK"},
            {"num": "09", "name": "Knowledge Transfer Complete", "target_date": "16 Apr 2026", "actual_date": "16 Apr 2026", "status": "ON TRACK"},
            {"num": "10", "name": "2-Months Guarantee Period Complete", "target_date": "02 Jun 2026", "actual_date": "02 Jun 2026", "status": "ON TRACK"},
            {"num": "11", "name": "Project Closing & Handover (BAST Final)", "target_date": "02 Jun 2026", "actual_date": "02 Jun 2026", "status": "ON TRACK"},
        ])

        start_x = Inches(0.80)
        total_w = Inches(11.733)
        header_y = Inches(1.60)
        header_h = Inches(0.40)

        # Header Band Card
        hdr_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, header_y, total_w, header_h)
        hdr_card.shadow.inherit = False
        hdr_card.fill.solid()
        hdr_card.fill.fore_color.rgb = self.theme.get_rgb("primary")
        hdr_card.line.fill.background()

        col_defs = [
            ("NO.", Inches(0.70), PP_ALIGN.CENTER),
            ("MILESTONE DESCRIPTION", Inches(5.00), PP_ALIGN.LEFT),
            ("BASELINE TARGET", Inches(1.90), PP_ALIGN.CENTER),
            ("ACTUAL / FORECAST", Inches(2.05), PP_ALIGN.CENTER),
            ("DELIVERY STATUS", Inches(2.083), PP_ALIGN.CENTER),
        ]

        cur_x = start_x
        for label, width, align in col_defs:
            tb = slide.shapes.add_textbox(cur_x, header_y + Inches(0.08), width, header_h - Inches(0.16))
            tf = tb.text_frame
            tf.word_wrap = False
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = label
            p.alignment = align
            p.font.name = self.theme.font_family_header
            p.font.size = Pt(11.0)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255)
            cur_x += width

        row_y = header_y + header_h + Inches(0.08)
        n_rows = len(milestones)
        max_bottom_y = Inches(6.82)
        available_h = max_bottom_y - row_y

        if n_rows <= 8:
            row_h = Inches(0.48)
            row_gap = Inches(0.06)
            font_no_pt = 11.5
            font_desc_pt = 11.0
            font_date_pt = 11.0
            font_act_pt = 11.0
            font_pill_pt = 11.0
            pill_h = Inches(0.28)
        else:
            row_gap = Inches(0.04)
            row_h = (available_h - row_gap * (n_rows - 1)) / n_rows
            font_no_pt = 11.0
            font_desc_pt = 11.0
            font_date_pt = 11.0
            font_act_pt = 11.0
            font_pill_pt = 11.0
            pill_h = Inches(0.28)

        for r_idx, m in enumerate(milestones):
            cur_ry = row_y + r_idx * (row_h + row_gap)
            is_alt = (r_idx % 2 != 0)
            row_card = add_card(
                slide,
                self.theme,
                start_x,
                cur_ry,
                total_w,
                row_h,
                bg_color=self.theme.get_rgb("surface_muted") if is_alt else self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            # Col 0: Number (Centered, Middle-aligned)
            x0 = start_x
            tb0 = slide.shapes.add_textbox(x0, cur_ry, Inches(0.70), row_h)
            tf0 = tb0.text_frame
            tf0.word_wrap = False
            tf0.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf0.margin_left = tf0.margin_right = tf0.margin_top = tf0.margin_bottom = 0
            p0 = tf0.paragraphs[0]
            p0.text = str(m.get("num", f"{r_idx+1:02d}"))
            p0.alignment = PP_ALIGN.CENTER
            p0.font.name = self.theme.font_family_header
            p0.font.size = Pt(font_no_pt)
            p0.font.bold = True
            p0.font.color.rgb = self.theme.get_rgb("accent")

            # Col 1: Milestone Name (Left-aligned, Middle-aligned)
            x1 = x0 + Inches(0.70)
            tb1 = slide.shapes.add_textbox(x1 + Inches(0.12), cur_ry, Inches(4.88), row_h)
            tf1 = tb1.text_frame
            tf1.word_wrap = True
            tf1.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
            p1 = tf1.paragraphs[0]
            p1.text = m.get("name", "")
            p1.font.name = self.theme.font_family
            p1.font.size = Pt(font_desc_pt)
            p1.font.bold = True
            p1.font.color.rgb = self.theme.get_rgb("primary")

            # Col 2: Baseline Target (Centered, Middle-aligned)
            x2 = x1 + Inches(5.00)
            tb2 = slide.shapes.add_textbox(x2, cur_ry, Inches(1.90), row_h)
            tf2 = tb2.text_frame
            tf2.word_wrap = False
            tf2.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
            p2 = tf2.paragraphs[0]
            p2.text = m.get("target_date", "")
            p2.alignment = PP_ALIGN.CENTER
            p2.font.name = self.theme.font_family
            p2.font.size = Pt(font_date_pt)
            p2.font.color.rgb = self.theme.get_rgb("secondary")

            # Col 3: Actual / Projected (Centered, Middle-aligned)
            x3 = x2 + Inches(1.90)
            tb3 = slide.shapes.add_textbox(x3, cur_ry, Inches(2.05), row_h)
            tf3 = tb3.text_frame
            tf3.word_wrap = False
            tf3.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
            p3 = tf3.paragraphs[0]
            p3.text = m.get("actual_date", "")
            p3.alignment = PP_ALIGN.CENTER
            p3.font.name = self.theme.font_family
            p3.font.size = Pt(font_act_pt)
            p3.font.bold = True
            p3.font.color.rgb = self.theme.get_rgb("primary")

            # Col 4: Rounded Status Badge Pill
            x4 = x3 + Inches(2.05)
            pill_w = Inches(1.60)
            pill_x = x4 + (Inches(2.083) - pill_w) / 2
            pill_y = cur_ry + (row_h - pill_h) / 2
            _add_status_pill(
                slide=slide,
                theme=self.theme,
                left=pill_x,
                top=pill_y,
                width=pill_w,
                height=pill_h,
                status=m.get("status", "ON TRACK"),
                font_size_pt=font_pill_pt,
            )

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 8: Risk Register (3-Tier Column Architecture with Icons & 3-Box Meters)
    # -------------------------------------------------------------------------
    def build_risk_register(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "RISK GOVERNANCE & CONTROL MATRIX | 3-TIER ESCALATION"),
            action_title=d.get("title", "Proactive Risk Controls Safeguard Schedule Buffer & Data Readiness"),
            subtitle=d.get("subtitle", "Structured 3-tier risk governance categorizing active risks with visual scaling meters and preventive mitigations."),
        )

        tiers = d.get("risk_tiers", [])
        if not tiers:
            tiers = [
                {
                    "tier_name": "CRITICAL / OCCURRED",
                    "accent_color": "danger",
                    "icon_name": "zap",
                    "risk_id": "R-04",
                    "title": "Year-End Assessment Schedule Shift",
                    "prob_label": "PROBABILITY: HIGH",
                    "prob_boxes": 3,
                    "impact_label": "IMPACT: MEDIUM",
                    "impact_boxes": 2,
                    "description": "FSD assessment schedule shift due to year-end holiday calendar alignment.",
                    "mitigations": [
                        "Rescheduled assessment workshop to 09 Jan 2026.",
                        "Allocated backup engineering resource for Financial General Ledger module.",
                        "Accelerated review via preliminary wireframes and component mockups.",
                    ],
                    "contingency": "Full absorption of the 17-day shift within internal development buffer without affecting Go-Live.",
                    "owner": "Budi Pratama (PM)",
                },
                {
                    "tier_name": "MANAGED / HIGH IMPACT",
                    "accent_color": "warning",
                    "icon_name": "shield-check",
                    "risk_id": "R-01",
                    "title": "Scope Creep Beyond FSD Baseline",
                    "prob_label": "PROBABILITY: MEDIUM",
                    "prob_boxes": 2,
                    "impact_label": "IMPACT: HIGH",
                    "impact_boxes": 3,
                    "description": "Requests for additional analytics features beyond the agreed 4 core financial use cases.",
                    "mitigations": [
                        "Formally freeze FSD v1.0 baseline as the binding delivery benchmark.",
                        "Communicate scope boundaries across all project executive stakeholders.",
                        "Enforce formal Change Request (CR) governance for any newly submitted enhancements.",
                    ],
                    "contingency": "Perform rigorous cost/schedule impact sizing and escalate CR decisions to Steering Committee.",
                    "owner": "Budi Pratama (PM)",
                },
                {
                    "tier_name": "MONITORED / DATA QUALITY",
                    "accent_color": "accent",
                    "icon_name": "target",
                    "risk_id": "R-02",
                    "title": "Incomplete Source Schema & Key Discrepancies",
                    "prob_label": "PROBABILITY: MEDIUM",
                    "prob_boxes": 2,
                    "impact_label": "IMPACT: HIGH",
                    "impact_boxes": 3,
                    "description": "Potential unvalidated data type anomalies and foreign key relations in staging risk automated ingestion errors.",
                    "mitigations": [
                        "Define enterprise data dictionary and catalog during architecture planning.",
                        "Execute automated data profiling scripts across staging environments.",
                        "Establish data quality threshold with a minimum 98% pass rate requirement.",
                    ],
                    "contingency": "Focus initial data cleansing on mandatory attributes; escalate schema deviations to source data team.",
                    "owner": "Lead Data Architect",
                },
            ]

        col_count = len(tiers)
        gap_x = Inches(0.28)
        total_w = Inches(11.733)
        col_w = (total_w - (col_count - 1) * gap_x) / col_count
        col_h = Inches(4.95)
        col_y = Inches(1.60)

        for i, t in enumerate(tiers[:3]):
            col_x = Inches(0.80) + i * (col_w + gap_x)

            # Determine theme accent color
            acc_key = t.get("accent_color", "accent")
            accent_rgb = self.theme.get_rgb(acc_key, "#0052CC")
            accent_hex = self.theme.get_hex(acc_key, "#0052CC")

            card, stripe = add_card_with_top_stripe(
                slide=slide,
                theme=self.theme,
                left=col_x,
                top=col_y,
                width=col_w,
                height=col_h,
                accent_rgb=accent_rgb,
                bg_color=self.theme.get_rgb("surface"),
                border_color=self.theme.get_rgb("border"),
                stripe_height_in=0.08,
            )

            # Determine badge/box fill key to mirror the tier color
            badge_fill_key = "badge_blue_fill"
            if acc_key == "danger":
                badge_fill_key = "badge_red_fill"
            elif acc_key == "warning":
                badge_fill_key = "badge_amber_fill"
            elif acc_key == "success":
                badge_fill_key = "badge_green_fill"

            # 1. Header Row inside card: Icon badge + Tier Pill
            icon_box_w = Inches(0.48)
            icon_box_h = Inches(0.48)
            icon_box_x = col_x + Inches(0.18)
            icon_box_y = col_y + Inches(0.16)

            ib = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, icon_box_x, icon_box_y, icon_box_w, icon_box_h)
            ib.shadow.inherit = False
            ib.fill.solid()
            ib.fill.fore_color.rgb = self.theme.get_rgb(badge_fill_key, default="#F8FAFC")
            ib.line.color.rgb = accent_rgb
            ib.line.width = Pt(1.0)

            icon_file = _get_tinted_icon(self.theme, t.get("icon_name", "zap"), accent_hex)
            if icon_file and icon_file.exists():
                slide.shapes.add_picture(
                    str(icon_file),
                    icon_box_x + Inches(0.07),
                    icon_box_y + Inches(0.07),
                    width=Inches(0.34),
                    height=Inches(0.34),
                )

            # Tier Name Pill (Pinned to upper right)
            _add_status_pill(
                slide=slide,
                theme=self.theme,
                left=col_x + col_w - Inches(1.95),
                top=icon_box_y + Inches(0.10),
                width=Inches(1.75),
                height=Inches(0.26),
                status=t.get("tier_name", "MANAGED"),
                font_size_pt=11.0,
                override_color_key=acc_key,
            )

            # 2. Card Content Text Frame (Title & Description)
            content_top = icon_box_y + icon_box_h + Inches(0.10)
            tb = slide.shapes.add_textbox(col_x + Inches(0.18), content_top, col_w - Inches(0.36), Inches(0.85))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            # Title (14.5pt bold)
            t_p = tf.paragraphs[0]
            t_p.text = f"[{t.get('risk_id', 'R-00')}] {t.get('title', '')}"
            t_p.font.name = self.theme.font_family_header
            t_p.font.size = Pt(14.5)
            t_p.font.bold = True
            t_p.font.color.rgb = self.theme.get_rgb("primary")

            # Description (11.0pt)
            d_p = tf.add_paragraph()
            d_p.text = t.get("description", "")
            d_p.font.name = self.theme.font_family
            d_p.font.size = Pt(11.0)
            d_p.font.color.rgb = self.theme.get_rgb("secondary")
            d_p.space_before = Pt(4)

            # 3. 3-Box Visual Scaling Meters
            meter_y = col_y + Inches(1.90)
            _draw_3_box_meter(
                slide=slide,
                left=col_x + Inches(0.18),
                top=meter_y,
                label=t.get("prob_label", "PROBABILITY: MED"),
                filled_count=t.get("prob_boxes", 2),
                active_color=accent_rgb,
                border_color=self.theme.get_rgb("border"),
                font_family=self.theme.font_family_header,
            )

            _draw_3_box_meter(
                slide=slide,
                left=col_x + Inches(0.18),
                top=meter_y + Inches(0.28),
                label=t.get("impact_label", "IMPACT: HIGH"),
                filled_count=t.get("impact_boxes", 3),
                active_color=accent_rgb,
                border_color=self.theme.get_rgb("border"),
                font_family=self.theme.font_family_header,
            )

            # 4. Mitigation Actions & Contingency
            actions_y = meter_y + Inches(0.60)
            atb = slide.shapes.add_textbox(col_x + Inches(0.18), actions_y, col_w - Inches(0.36), Inches(1.50))
            atf = atb.text_frame
            atf.word_wrap = True
            atf.margin_left = atf.margin_right = atf.margin_top = atf.margin_bottom = 0

            # Subheading
            sh = atf.paragraphs[0]
            sh.text = "PREVENTIVE MITIGATION CONTROLS"
            sh.font.name = self.theme.font_family_header
            sh.font.size = Pt(11.0)
            sh.font.bold = True
            sh.font.color.rgb = accent_rgb

            # Mitigation bullets with hanging indents (11.0pt)
            for m_item in t.get("mitigations", []):
                _add_bullet_paragraph(
                    tf=atf,
                    text=m_item,
                    font_name=self.theme.font_family,
                    font_size_pt=11.0,
                    font_color=self.theme.get_rgb("primary"),
                    space_before_pt=5.0,
                )

            # Contingency & Owner Footnote
            foot_y = col_y + col_h - Inches(0.38)
            ftb = slide.shapes.add_textbox(col_x + Inches(0.18), foot_y, col_w - Inches(0.36), Inches(0.30))
            ftf = ftb.text_frame
            ftf.word_wrap = True
            ftf.margin_left = ftf.margin_right = ftf.margin_top = ftf.margin_bottom = 0

            fp = ftf.paragraphs[0]
            fp.text = f"Owner: {t.get('owner', 'Project Manager')}"
            fp.font.name = self.theme.font_family_header
            fp.font.size = Pt(11.0)
            fp.font.bold = True
            fp.font.color.rgb = self.theme.get_rgb("secondary")

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 9: Issue Log
    # -------------------------------------------------------------------------
    def build_issue_log(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        slide = add_slide_with_background(self.prs, self.theme)
        idx = len(self.prs.slides)
        add_slide_header(
            slide=slide,
            theme=self.theme,
            tracker=d.get("tracker", "ISSUE GOVERNANCE | ACTIVE ISSUE LOG"),
            action_title=d.get("title", "Issue #1 Resolution Plan Confines FSD Delay Without Slipping Milestone 4"),
            subtitle=d.get("subtitle", "Root cause resolved via rescheduled assessment sessions; downstream target go-live protected."),
        )

        issues = d.get("issues", [])
        if not issues:
            issues = [
                {
                    "id": "ISSUE-01",
                    "date": "02-Jan-26",
                    "title": "FSD Assessment Completion Shift from Year-End Holiday Interval",
                    "owner": "Budi Pratama",
                    "severity": "Medium",
                    "status": "Open",
                    "root_cause": "Key client and vendor stakeholders unavailable during year-end holiday period; analytics assessment sessions rescheduled to 09 Jan 2026.",
                    "impact": "FSD final sign-off rescheduled from 02 Jan 2026 to 19 Jan 2026 (+17 calendar days), fully contained within development buffer without downstream milestone slip.",
                    "action_plan": "Conduct rescheduled assessment session on 09 Jan 2026; complete FSD consolidation by 15 Jan 2026; secure final executive sign-off on 19 Jan 2026.",
                    "target_date": "19-Jan-26",
                }
            ]

        iss = issues[0]

        strip_y = Inches(1.60)
        strip_h = Inches(0.55)
        strip_w = Inches(11.733)

        scard = add_card(
            slide,
            self.theme,
            Inches(0.80),
            strip_y,
            strip_w,
            strip_h,
            bg_color=self.theme.get_rgb("surface_muted"),
            border_color=self.theme.get_rgb("border"),
            force_rectangle=True,
        )

        stb = slide.shapes.add_textbox(Inches(0.98), strip_y + Inches(0.12), strip_w - Inches(0.36), strip_h - Inches(0.24))
        stf = stb.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_right = stf.margin_top = stf.margin_bottom = 0
        sp = stf.paragraphs[0]
        sp.text = f"ACTIVE ISSUE OVERVIEW: Total Active: 1  |  Severity: MEDIUM  |  Status: OPEN  |  Target Resolution: {iss.get('target_date', '19-Jan-26')}  |  Owner: {iss.get('owner', 'Budi Pratama')}"
        sp.font.name = self.theme.font_family_header
        sp.font.size = Pt(11.0)
        sp.font.bold = True
        sp.font.color.rgb = self.theme.get_rgb("accent")

        main_y = strip_y + strip_h + Inches(0.18)
        main_h = Inches(4.22)

        mcard, stripe = add_card_with_top_stripe(
            slide=slide,
            theme=self.theme,
            left=Inches(0.80),
            top=main_y,
            width=strip_w,
            height=main_h,
            accent_rgb=self.theme.get_rgb("warning"),
            bg_color=self.theme.get_rgb("surface"),
            border_color=self.theme.get_rgb("border"),
            stripe_height_in=0.08,
        )

        mtb = slide.shapes.add_textbox(Inches(1.00), main_y + Inches(0.18), strip_w - Inches(0.40), Inches(0.60))
        mtf = mtb.text_frame
        mtf.word_wrap = True
        mtf.margin_left = mtf.margin_right = mtf.margin_top = mtf.margin_bottom = 0
        mp1 = mtf.paragraphs[0]
        mp1.text = f"[{iss.get('id', 'ISSUE-01')}] {iss.get('title', '')}"
        mp1.font.name = self.theme.font_family_header
        mp1.font.size = Pt(14.0)
        mp1.font.bold = True
        mp1.font.color.rgb = self.theme.get_rgb("primary")

        col_3w = (strip_w - Inches(0.80)) / 3
        col_3y = main_y + Inches(0.85)
        col_3h = main_h - Inches(1.05)

        sections = [
            ("ROOT CAUSE & ANALYSIS", iss.get("root_cause", ""), self.theme.get_rgb("muted")),
            ("SCHEDULE & DELIVERY IMPACT", iss.get("impact", ""), self.theme.get_rgb("danger")),
            ("CORRECTIVE RESOLUTION PLAN", iss.get("action_plan", ""), self.theme.get_rgb("success")),
        ]

        for c_idx, (sec_title, sec_text, sec_color) in enumerate(sections):
            cx = Inches(1.00) + c_idx * (col_3w + Inches(0.20))
            subcard = add_card(
                slide,
                self.theme,
                cx,
                col_3y,
                col_3w,
                col_3h,
                bg_color=self.theme.get_rgb("surface_muted"),
                border_color=self.theme.get_rgb("border"),
                force_rectangle=True,
            )

            ctb = slide.shapes.add_textbox(cx + Inches(0.18), col_3y + Inches(0.18), col_3w - Inches(0.36), col_3h - Inches(0.36))
            ctf = ctb.text_frame
            ctf.word_wrap = True
            ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0

            p_h = ctf.paragraphs[0]
            p_h.text = sec_title
            p_h.font.name = self.theme.font_family_header
            p_h.font.size = Pt(11.5)
            p_h.font.bold = True
            p_h.font.color.rgb = sec_color

            p_b = ctf.add_paragraph()
            p_b.text = sec_text
            p_b.font.name = self.theme.font_family
            p_b.font.size = Pt(11.5)
            p_b.font.color.rgb = self.theme.get_rgb("primary")
            p_b.space_before = Pt(8)

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Slide 10: Section Divider / Q&A
    # -------------------------------------------------------------------------
    def build_qa_discussion(self, data: Optional[Dict[str, Any]] = None) -> Any:
        d = data or {}
        idx = len(self.prs.slides) + 1
        return build_chapter_divider_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=d.get("tracker", "ENGAGEMENT REVIEW & OPEN FORUM"),
            title=d.get("title", "Questions & Executive Discussion"),
            subtitle=d.get("subtitle", "Steering Committee feedback, operational alignments, and immediate decision items."),
            division_tag=d.get("division_tag", "BAS Division  |  Data & AI Practice"),
            tagline=d.get("tagline", "PT Metrodata Electronics Tbk"),
            current_idx=idx,
            total_slides=11,
            show_footer=False,
        )

    # -------------------------------------------------------------------------
    # Slide 11: Thank You Slide
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
        p_tr.text = d.get("tracker", "ENGAGEMENT WRAP-UP | THANK YOU").upper()
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
        p_s.text = d.get("subtitle", "Delivering Data-Driven Value & Predictive Intelligence with Cloud Analytics Platform.")
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
        op1.text = f"{d.get('company', 'PT Metrodata Electronics Tbk')}  |  {d.get('office', 'APL Tower 37th Floor, Jakarta')}"
        op1.font.name = self.theme.font_family
        op1.font.size = Pt(11.0)
        op1.font.color.rgb = self.theme.get_rgb("muted")

        add_slide_footer(slide, self.theme, current_idx=idx, total_slides=11, notice=self.metadata.get("confidentiality", "Confidential"))
        return slide

    # -------------------------------------------------------------------------
    # Spreadsheet Synchronization Engine
    # -------------------------------------------------------------------------
    def sync_with_spreadsheets(
        self,
        timeline_path: Optional[Union[str, Path]] = None,
        risk_path: Optional[Union[str, Path]] = None,
        issue_path: Optional[Union[str, Path]] = None,
        chart_mode: bool = False,
        chart_output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronizes deck specification directly with project XLSX spreadsheets:
          - Timeline & S-Curve (4.2_Weekly_Progress_Timeline_Update_Template.xlsx):
            Extracts active period, planned %, actual %, variance %, overall health,
            SPI, delivery phase progress rows, and optionally renders high-DPI S-Curve line chart.
          - Risk Register (4.5_Risk_Register_Template.xlsx):
            Extracts active project risks, probability/impact meters, mitigations, and owners.
          - Issue Log (4.6_Issue_Log_Template.xlsx):
            Extracts active issues, severity, root cause, schedule impact, and action plans.
        """
        sync_results: Dict[str, Any] = {
            "timeline_synced": False,
            "s_curve_chart_generated": False,
            "risks_synced": False,
            "issues_synced": False,
        }

        # 1. Timeline & S-Curve Sync
        t_path = (
            timeline_path
            or self.config.get("spreadsheets", {}).get("timeline")
            or "clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Timeline_Update_Template.xlsx"
        )
        if t_path and Path(t_path).exists():
            try:
                import openpyxl
                from src.xlsx_engine.timeline_aggregator import TimelineAggregator

                agg = TimelineAggregator(t_path)
                analysis = agg.extract_s_curve()

                # Find overall_progress slide spec
                for s in self.config.get("slides", []):
                    if s.get("archetype") == "overall_progress":
                        planned_str = f"{(analysis.current_planned_pct or 0.0) * 100:.1f}%"
                        actual_str = f"{(analysis.current_actual_pct or 0.0) * 100:.1f}%"
                        var_str = f"{(analysis.current_variance_pct or 0.0):+.1f}%"
                        health_status = analysis.overall_health or "ON TRACK"

                        s["kpis"] = [
                            {"label": "Planned Progress", "value": planned_str, "subtext": f"Baseline Target {analysis.current_period or ''}".strip(), "status": "PLANNED"},
                            {"label": "Actual Progress", "value": actual_str, "subtext": "Cumulative Completed", "status": health_status if health_status in ("COMPLETED", "ON TRACK") else "ON TRACK"},
                            {"label": "Schedule Variance", "value": var_str, "subtext": "Tolerance: +/- 2.0%", "status": "ON TRACK" if (analysis.current_variance_pct or 0.0) >= 0 else "AT RISK"},
                            {"label": "Overall Health", "value": health_status, "subtext": f"SPI: {analysis.spi:.3f} (Go-Live protected)", "status": health_status},
                        ]

                        # Check chart mode or config flag
                        should_chart = chart_mode or s.get("show_chart") or self.config.get("chart_mode", False)
                        if should_chart:
                            c_dir = Path(chart_output_dir or "output/presentations/charts")
                            c_dir.mkdir(parents=True, exist_ok=True)
                            c_path = c_dir / "s_curve_weekly.png"
                            generate_s_curve_chart_image(analysis.points, c_path, self.theme)
                            s["chart_image"] = str(c_path)
                            sync_results["s_curve_chart_generated"] = True
                            sync_results["chart_path"] = str(c_path)

                        # Extract Phase 1 to Phase 5 rows
                        wb = openpyxl.load_workbook(str(t_path), data_only=True)
                        ws = wb.active
                        phase_rows_map = [
                            (6, "Phase 1: Project Initiation & Charter"),
                            (33, "Phase 2: Architecture & FSD Assessment"),
                            (57, "Phase 3: Cloud Platform Setup & Staging"),
                            (105, "Phase 4: Data Modeling & ETL Pipelines"),
                            (132, "Phase 5: SIT, UAT & Go-Live Cutover"),
                        ]
                        extracted_phases = []
                        for r_num, phase_title in phase_rows_map:
                            p_vals = [ws.cell(r_num, col).value for col in range(5, ws.max_column + 1)]
                            a_vals = [ws.cell(r_num + 1, col).value for col in range(5, ws.max_column + 1)]
                            p_sum = sum(v for v in p_vals if isinstance(v, (int, float)))
                            a_sum = sum(v for v in a_vals if isinstance(v, (int, float)))
                            pct = (a_sum / p_sum * 100) if p_sum > 0 else 0.0
                            status_p = "COMPLETED" if pct >= 99.9 else ("IN PROGRESS" if pct > 0 else "PLANNED")
                            extracted_phases.append({
                                "phase": phase_title,
                                "planned": "100%" if pct >= 99.9 else f"{min(100.0, p_sum):.0f}%",
                                "actual": f"{pct:.0f}%",
                                "status": status_p,
                            })
                        wb.close()
                        if extracted_phases and not s.get("phases"):
                            s["phases"] = extracted_phases

                sync_results["timeline_synced"] = True
                sync_results["current_period"] = analysis.current_period
                sync_results["planned_pct"] = analysis.current_planned_pct
                sync_results["actual_pct"] = analysis.current_actual_pct
                sync_results["variance_pct"] = analysis.current_variance_pct
            except Exception as e:
                logger.warning(f"Error synchronizing with timeline spreadsheet {t_path}: {e}")

        # 2. Risk Register Sync
        r_path = (
            risk_path
            or self.config.get("spreadsheets", {}).get("risks")
            or "clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.5_Risk_Register_Template.xlsx"
        )
        if r_path and Path(r_path).exists():
            try:
                import openpyxl
                wb_r = openpyxl.load_workbook(str(r_path), data_only=True)
                ws_r = wb_r["Risk Register"]
                raw_risks = []
                for r in range(4, ws_r.max_row + 1):
                    title_val = ws_r.cell(r, 4).value
                    if not title_val:
                        continue
                    raw_risks.append({
                        "id": f"R-{len(raw_risks)+1:02d}",
                        "title": str(title_val).strip().rstrip("."),
                        "description": str(ws_r.cell(r, 5).value or "").strip(),
                        "impact": str(ws_r.cell(r, 6).value or "").strip(),
                        "category": str(ws_r.cell(r, 7).value or "").strip(),
                        "owner": str(ws_r.cell(r, 8).value or "Project Manager").strip(),
                        "probability": str(ws_r.cell(r, 9).value or "Medium").strip(),
                        "impact_level": str(ws_r.cell(r, 10).value or "Medium").strip(),
                        "status": str(ws_r.cell(r, 11).value or "Open").strip(),
                        "mitigations": [m.strip().lstrip("þ*•- o\t") for m in str(ws_r.cell(r, 12).value or "").split("\n") if m.strip()],
                        "contingency": str(ws_r.cell(r, 13).value or "").strip().replace("\n", " ").lstrip("*•- "),
                    })
                wb_r.close()

                if raw_risks:
                    for s in self.config.get("slides", []):
                        if s.get("archetype") == "risk_register":
                            if not s.get("risk_tiers"):
                                tiers = []
                                tier_configs = [
                                    ("CRITICAL / OCCURRED", "danger", "zap"),
                                    ("MANAGED / HIGH IMPACT", "warning", "shield-check"),
                                    ("MONITORED / DATA QUALITY", "accent", "target"),
                                ]
                                for idx_rk, rk in enumerate(raw_risks[:3]):
                                    t_name, t_color, t_icon = tier_configs[idx_rk % 3]
                                    prob_b = 3 if "high" in rk["probability"].lower() else (2 if "med" in rk["probability"].lower() else 1)
                                    imp_b = 3 if "high" in rk["impact_level"].lower() else (2 if "med" in rk["impact_level"].lower() else 1)
                                    tiers.append({
                                        "tier_name": t_name,
                                        "accent_color": t_color,
                                        "icon_name": t_icon,
                                        "risk_id": rk["id"],
                                        "title": rk["title"],
                                        "prob_label": f"PROBABILITY: {rk['probability'].upper()}",
                                        "prob_boxes": prob_b,
                                        "impact_label": f"IMPACT: {rk['impact_level'].upper()}",
                                        "impact_boxes": imp_b,
                                        "description": rk["description"][:120] + "..." if len(rk["description"]) > 120 else rk["description"],
                                        "mitigations": rk["mitigations"][:3] or ["Review berkala terhadap baseline."],
                                        "contingency": rk["contingency"][:140] if rk["contingency"] else "Lakukan eskalasi ke Steering Committee.",
                                        "owner": rk["owner"],
                                    })
                                s["risk_tiers"] = tiers
                    sync_results["risks_synced"] = True
                    sync_results["risk_count"] = len(raw_risks)
            except Exception as e:
                logger.warning(f"Error synchronizing with risk register {r_path}: {e}")

        # 3. Issue Log Sync
        i_path = (
            issue_path
            or self.config.get("spreadsheets", {}).get("issues")
            or "clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.6_Issue_Log_Template.xlsx"
        )
        if i_path and Path(i_path).exists():
            try:
                import openpyxl
                wb_i = openpyxl.load_workbook(str(i_path), data_only=True)
                ws_i = wb_i["Issue Log"]
                raw_issues = []
                for r in range(4, ws_i.max_row + 1):
                    title_val = ws_i.cell(r, 4).value
                    if not title_val:
                        continue
                    dt_val = ws_i.cell(r, 3).value
                    dt_str = str(dt_val)[:10] if dt_val else "02-Jan-00"
                    raw_issues.append({
                        "id": f"ISSUE-{len(raw_issues)+1:02d}",
                        "date": dt_str,
                        "title": str(title_val).strip(),
                        "owner": str(ws_i.cell(r, 7).value or "Project Manager").strip(),
                        "severity": str(ws_i.cell(r, 10).value or "Medium").strip(),
                        "status": str(ws_i.cell(r, 11).value or "Open").strip(),
                        "root_cause": str(ws_i.cell(r, 12).value or "").strip().replace("\n", " "),
                        "impact": str(ws_i.cell(r, 13).value or "").strip().replace("\n", " "),
                        "action_plan": str(ws_i.cell(r, 14).value or "").strip().replace("\n", " "),
                        "target_date": "19-Jan-2026",
                    })
                wb_i.close()

                if raw_issues:
                    for s in self.config.get("slides", []):
                        if s.get("archetype") == "issue_log":
                            if not s.get("issues"):
                                s["issues"] = raw_issues
                    sync_results["issues_synced"] = True
                    sync_results["issue_count"] = len(raw_issues)
            except Exception as e:
                logger.warning(f"Error synchronizing with issue log {i_path}: {e}")

        return sync_results

    # -------------------------------------------------------------------------
    # Master Assembly
    # -------------------------------------------------------------------------
    def build_all(self) -> Presentation:
        """Assembles all slides according to config specification or default 11-slide sequence."""
        slides_spec = self.config.get("slides", [])

        builder_map = {
            "cover": self.build_cover,
            "agenda": self.build_agenda,
            "exec_summary": self.build_exec_summary,
            "overall_progress": self.build_overall_progress,
            "weekly_detail": self.build_weekly_detail,
            "lookahead_plan": self.build_lookahead_plan,
            "milestone_status": self.build_milestone_status,
            "risk_register": self.build_risk_register,
            "issue_log": self.build_issue_log,
            "chapter_divider": self.build_qa_discussion,
            "qa_discussion": self.build_qa_discussion,
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
            self.build_exec_summary()
            self.build_overall_progress()
            self.build_weekly_detail()
            self.build_lookahead_plan()
            self.build_milestone_status()
            self.build_risk_register()
            self.build_issue_log()
            self.build_qa_discussion()
            self.build_thank_you()

        return self.prs

    def update_pagination(self) -> None:
        """Post-processes all slides to ensure pagination numbers match total slide count."""
        total_slides = len(self.prs.slides)
        for s_idx, slide in enumerate(self.prs.slides, start=1):
            for shape in slide.shapes:
                if shape.has_text_frame:
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
