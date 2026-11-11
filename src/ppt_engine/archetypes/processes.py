from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.util import Inches, Pt

from src.ppt_engine.icon_engine import (
    get_brand_icon,
    normalize_color,
    recolor_svg,
    render_svg_to_png,
    resolve_brand_color,
)
from src.ppt_engine.text_formatting import append_formatted_runs, set_formatted_text
from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb, rgb_to_hex, strip_shape_shadows

from .common import (
    add_slide_with_background, add_slide_header, resolve_content_top, add_card, add_card_with_top_stripe,
    add_slide_footer, add_takeaway_bar, _interpolate_color, _get_contrast_text_color, _add_status_pill, _add_bullet_paragraph,
)

logger = logging.getLogger(__name__)

@dataclass
class ProcessChevronStep:
    """Content definition for a single phase in the Stepped Process Chevron Flow."""
    phase_number: str                       # e.g. "01", "PHASE 1"
    title: str                              # e.g. "Discovery & Scoping"
    duration_badge: Optional[str] = None    # e.g. "WEEKS 1-3"
    deliverables: List[str] = field(default_factory=list)
    status: Optional[str] = None            # e.g. "COMPLETED", "IN PROGRESS", "PLANNED"
    accent_color: Optional[RGBColor] = None # Optional override for chevron fill
    is_current: bool = False                # Explicit active-phase marker
    pin_label: Optional[str] = None         # Custom marker text
    pin_color: Optional[str] = None         # Theme color key or hex override


def build_chevron_process_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Phased Execution Roadmap Delivers Accelerated Value Across Four Controlled Horizons",
    subtitle: Optional[str] = None,
    steps: Optional[List[ProcessChevronStep]] = None,
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
    pin_color: str = "accent",
    pin_label: str = "[ CURRENT: WE ARE HERE ]",
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
) -> Any:
    """
    Renders an executive stepped process flow using interconnected horizontal chevrons.
      - Opt-in active pin indicator (customizable color, drawn only when a step is active/current).
      - Sharp rectangular card containers below each chevron.
      - Strictly conditional status brackets (static/planning workflows render cleanly without status noise).
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if steps is None:
        steps = [
            ProcessChevronStep(
                phase_number="01",
                title="Discovery & Architecture",
                duration_badge="WEEKS 1-3",
                status="COMPLETED",
                deliverables=[
                    "Current-State Assessment: Audit data pipelines and legacy warehouse.",
                    "Architecture Blueprint: Formulate target lakehouse topology.",
                    "Security & RBAC Matrix: Define column/row masking policy.",
                ],
            ),
            ProcessChevronStep(
                phase_number="02",
                title="Foundation & Ingestion",
                duration_badge="WEEKS 4-7",
                status="IN PROGRESS",
                deliverables=[
                    "Snowflake Warehouses: Provision multi-cluster virtual compute.",
                    "Kafka & Snowpipe Pipeline: Implement streaming ingestion topics.",
                    "CDC Connector Ingress: Establish sub-minute database replication.",
                ],
            ),
            ProcessChevronStep(
                phase_number="03",
                title="Analytics & Modeling",
                duration_badge="WEEKS 8-11",
                status="PLANNED",
                deliverables=[
                    "dbt Transformation Layer: Build curated semantic data models.",
                    "Semantic KPI Metrics: Standardize business analytics definitions.",
                    "Executive BI Dashboard: Deliver real-time operational views.",
                ],
            ),
            ProcessChevronStep(
                phase_number="04",
                title="UAT & Cutover",
                duration_badge="WEEKS 12-14",
                status="PLANNED",
                deliverables=[
                    "End-to-End SIT/UAT: Complete business user validation.",
                    "Disaster Recovery Drill: Verify automated failover telemetry.",
                    "Production Cutover: Final signoff and operational handover.",
                ],
            ),
        ]

    if not steps:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    n_steps = len(steps)
    total_w = Inches(11.733)
    start_x = Inches(0.8)
    has_pin = any(
        getattr(s, "is_current", False) or str(s.status or "").strip().upper() == "IN PROGRESS"
        for s in steps
    )
    chevron_y = resolve_content_top(header_bottom, gap_in=(0.38 if has_pin else 0.18))
    chevron_h = Inches(0.56)
    gap = Inches(0.12)
    step_w = (total_w - (n_steps - 1) * gap) / n_steps
    card_y = chevron_y + chevron_h + Inches(0.08)
    bottom_limit = Inches(6.14 if takeaway else 6.86)
    card_h = max(Inches(3.20), bottom_limit - card_y)

    base_primary = theme.get_rgb("primary")
    light_tint = _interpolate_color(RGBColor(241, 245, 249), base_primary, 0.28)

    for i, step in enumerate(steps):
        cur_x = start_x + i * (step_w + gap)
        step_status_u = str(step.status or "").strip().upper()
        is_active = bool(getattr(step, "is_current", False) or step_status_u == "IN PROGRESS")

        # 1. Consistent Cohesive Chevron Color across all steps
        step_color = step.accent_color or theme.get_rgb("accent")

        # 1b. Opt-in Active Location Marker Shape (customizable color; never hardcoded alarm red)
        if is_active:
            pin_w = Inches(2.20)
            pin_h = Inches(0.24)
            pin_x = cur_x + (step_w - pin_w) / 2
            pin_y = chevron_y - pin_h - Inches(0.04)

            p_col_key = getattr(step, "pin_color", None) or pin_color
            pin_fill = hex_to_rgb(p_col_key) if str(p_col_key).startswith("#") else theme.get_rgb(str(p_col_key))
            pin_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, pin_x, pin_y, pin_w, pin_h)
            pin_badge.shadow.inherit = False
            strip_shape_shadows(pin_badge)
            pin_badge.fill.solid()
            pin_badge.fill.fore_color.rgb = pin_fill
            pin_badge.line.fill.background()

            pin_tf = pin_badge.text_frame
            pin_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            pin_tf.word_wrap = False
            pin_tf.margin_left = pin_tf.margin_right = pin_tf.margin_top = pin_tf.margin_bottom = 0
            p_pin = pin_tf.paragraphs[0]
            p_pin.text = str(getattr(step, "pin_label", None) or pin_label)
            p_pin.font.name = theme.font_family_header
            p_pin.font.size = Pt(9.5)
            p_pin.font.bold = True
            p_pin.alignment = PP_ALIGN.CENTER
            p_pin.font.color.rgb = RGBColor(255, 255, 255)

        # 2. Render top directional chevron banner
        chevron = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, cur_x, chevron_y, step_w, chevron_h)
        chevron.shadow.inherit = False
        strip_shape_shadows(chevron)
        chevron.fill.solid()
        chevron.fill.fore_color.rgb = step_color
        chevron.line.fill.background()

        # Chevron header text
        c_tf = chevron.text_frame
        c_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        c_tf.word_wrap = True
        c_tf.margin_left = Inches(0.12)
        c_tf.margin_right = Inches(0.25)  # Offset for chevron arrow tip
        c_tf.margin_top = c_tf.margin_bottom = 0

        p_ch = c_tf.paragraphs[0]
        p_ch.text = f"{step.phase_number}  |  {step.title}"
        p_ch.font.name = theme.font_family_header
        p_ch.font.size = Pt(11.0)
        p_ch.font.bold = True
        p_ch.font.color.rgb = RGBColor(255, 255, 255)

        # 3. Render body card container underneath
        card = add_card(
            slide,
            theme,
            cur_x,
            card_y,
            step_w,
            card_h,
            force_rectangle=True,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("accent") if is_active else theme.get_rgb("border"),
            border_width_pt=2.0 if is_active else 1.0,
        )

        # 4. Populate Card Content
        inner_tb = slide.shapes.add_textbox(cur_x + Inches(0.15), card_y + Inches(0.18), step_w - Inches(0.30), card_h - Inches(0.36))
        inner_tf = inner_tb.text_frame
        inner_tf.word_wrap = True
        inner_tf.margin_left = inner_tf.margin_right = inner_tf.margin_top = inner_tf.margin_bottom = 0

        has_card_head = False
        if step.duration_badge:
            p_badge = inner_tf.paragraphs[0]
            p_badge.text = step.duration_badge
            p_badge.font.name = theme.font_family_header
            p_badge.font.size = Pt(10.5)
            p_badge.font.bold = True
            p_badge.font.color.rgb = theme.get_rgb("primary")
            has_card_head = True

        # Strictly Conditional Status Row (omitted cleanly when step.status is unset)
        if step.status and str(step.status).strip():
            p_st = inner_tf.add_paragraph() if has_card_head else inner_tf.paragraphs[0]
            if step_status_u == "COMPLETED":
                p_st.text = "[ COMPLETED ]"
                p_st.font.color.rgb = hex_to_rgb("#059669")
            elif step_status_u == "IN PROGRESS":
                p_st.text = "[ IN PROGRESS ]"
                p_st.font.color.rgb = hex_to_rgb("#0052CC")
            else:
                p_st.text = f"[ {step_status_u} ]"
                p_st.font.color.rgb = hex_to_rgb("#64748B")
            p_st.font.name = theme.font_family_header
            p_st.font.size = Pt(9.5)
            p_st.font.bold = True
            if has_card_head:
                p_st.space_before = Pt(2)
            has_card_head = True

        # Deliverables Section Header
        p_dh = inner_tf.add_paragraph() if has_card_head else inner_tf.paragraphs[0]
        p_dh.text = "KEY DELIVERABLES"
        p_dh.font.name = theme.font_family_header
        p_dh.font.size = Pt(10.0)
        p_dh.font.bold = True
        p_dh.font.color.rgb = theme.get_rgb("accent")
        p_dh.space_before = Pt(8 if has_card_head else 0)

        # Deliverables Checklist (Balanced 9.5pt typography)
        for deliv in step.deliverables:
            p_item = inner_tf.add_paragraph()
            p_item.space_before = Pt(4)
            p_item.font.name = theme.font_family
            p_item.font.size = Pt(9.5)

            if ":" in deliv:
                lead, desc = deliv.split(":", 1)
                r_lead = p_item.add_run()
                r_lead.text = f"•  {lead.strip()}: "
                r_lead.font.bold = True
                r_lead.font.color.rgb = theme.get_rgb("primary")

                r_desc = p_item.add_run()
                r_desc.text = desc.strip()
                r_desc.font.bold = False
                r_desc.font.color.rgb = theme.get_rgb("secondary")
            else:
                r_all = p_item.add_run()
                r_all.text = f"•  {deliv.strip()}"
                r_all.font.bold = False
                r_all.font.color.rgb = theme.get_rgb("secondary")

    if takeaway:
        add_takeaway_bar(slide, theme, takeaway, top_y=Inches(6.28), left_x=start_x, width=total_w, height=Inches(0.54))

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


@dataclass
class GanttTask:
    """Represents a discrete task or milestone phase in a delivery timeline."""
    name: str
    start_period: float              # e.g., 1.0 (start of Week 1)
    end_period: float                # e.g., 4.0 (end of Week 4)
    progress_pct: float = 100.0      # 0 to 100%
    status: str = "COMPLETED"        # COMPLETED, IN_PROGRESS, PLANNED, DELAYED
    owner: Optional[str] = None
    is_milestone: bool = False       # If True, renders as a milestone diamond marker

@dataclass
class GanttWorkstream:
    """Represents a major functional delivery track / workstream."""
    category: str                    # e.g., "Workstream 1: Ingestion & Core Lakehouse"
    badge: str                       # e.g., "DATA PLATFORM"
    accent_color: str = "primary"    # primary, secondary, accent, or hex
    tasks: List[GanttTask] = field(default_factory=list)

@dataclass
class GanttTimelineData:
    """Complete dataset for an executive consulting delivery roadmap."""
    time_scale_label: str = "WEEKS"
    total_periods: int = 12
    period_labels: Optional[List[str]] = None
    current_period_marker: Optional[float] = 6.0
    workstreams: List[GanttWorkstream] = field(default_factory=list)
    footnote: str = "*) Timeline reflects target PMO sprint velocity and scheduled governance gates."


def _default_gantt_data() -> GanttTimelineData:
    return GanttTimelineData(
        time_scale_label="WEEKS",
        total_periods=12,
        period_labels=[f"W{i}" for i in range(1, 13)],
        current_period_marker=6.0,
        workstreams=[
            GanttWorkstream(
                category="Foundation & Ingestion",
                badge="CORE LAKEHOUSE",
                accent_color="primary",
                tasks=[
                    GanttTask("Snowflake Accounts & RBAC Setup", 1.0, 3.0, 100.0, "COMPLETED"),
                    GanttTask("SAP & ERP CDC Ingestion Pipeline", 2.0, 5.0, 100.0, "COMPLETED"),
                    GanttTask("Data Ingestion Gate", 5.0, 5.0, 100.0, "COMPLETED", is_milestone=True),
                ],
            ),
            GanttWorkstream(
                category="Transformation & Marts",
                badge="DBT PIPELINES",
                accent_color="accent",
                tasks=[
                    GanttTask("Silver Cleansing & Deduplication", 3.0, 7.0, 80.0, "IN_PROGRESS"),
                    GanttTask("Gold Analytical Views & Marts", 5.0, 9.0, 20.0, "IN_PROGRESS"),
                    GanttTask("Transformation Gate", 9.0, 9.0, 0.0, "PLANNED", is_milestone=True),
                ],
            ),
            GanttWorkstream(
                category="Serving & Executive BI",
                badge="STREAMLIT & AI",
                accent_color="secondary",
                tasks=[
                    GanttTask("Streamlit Dashboard Wireframes", 6.0, 8.0, 40.0, "IN_PROGRESS"),
                    GanttTask("Cortex AI Copilot Integration", 8.0, 11.0, 0.0, "PLANNED"),
                    GanttTask("SIT / UAT Acceptance Sign-off", 10.0, 12.0, 0.0, "PLANNED"),
                    GanttTask("Production Go-Live (BAST)", 12.0, 12.0, 0.0, "PLANNED", is_milestone=True),
                ],
            ),
        ],
    )


def build_timeline_gantt_slide(
    prs_or_slide: Any,
    theme: Optional[Theme] = None,
    tracker: Optional[str] = None,
    action_title: str = "Phased Execution Plan Ensures Iterative Milestone Realization Across 12 Weeks",
    subtitle: Optional[str] = None,
    gantt_data: Optional[GanttTimelineData] = None,
    current_idx: int = 4,
    total_slides: int = 10,
    notice: Optional[str] = None,
) -> Any:
    """
    Renders an executive delivery Gantt timeline slide with calendar column axis,
    workstream streams, duration bars, milestone diamonds, and current progress indicator.
    """
    if theme is None:
        theme = get_theme("default")

    if hasattr(prs_or_slide, "slides"):
        slide = prs_or_slide.slides.add_slide(prs_or_slide.slide_layouts[6])
    else:
        slide = prs_or_slide

    data = gantt_data or _default_gantt_data()

    # 1. Background Fill
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.50))
    bg.fill.solid()
    bg.fill.fore_color.rgb = theme.get_rgb("background")
    bg.line.fill.background()

    # 2. Unified Header Frame
    header_bottom = add_slide_header(slide, theme, tracker=tracker, title=action_title, subtitle=subtitle)

    # 3. Canvas Bounds
    left_x = Inches(0.80)
    grid_left = Inches(3.85)
    grid_width = Inches(8.68)
    header_y = resolve_content_top(header_bottom, gap_in=(0.34 if data.current_period_marker is not None else 0.20))
    header_h = Inches(0.35)

    num_periods = max(1, data.total_periods)
    col_width = grid_width / num_periods

    # Time Axis Header Bar
    t_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, grid_left, header_y, grid_width, header_h)
    t_bar.shadow.inherit = False
    strip_shape_shadows(t_bar)
    t_bar.fill.solid()
    t_bar.fill.fore_color.rgb = theme.get_rgb("primary")
    t_bar.line.fill.background()

    labels = data.period_labels or [f"P{i}" for i in range(1, num_periods + 1)]
    for col_idx in range(num_periods):
        col_x = grid_left + col_idx * col_width
        tb = slide.shapes.add_textbox(col_x, header_y, col_width, header_h)
        tf = tb.text_frame
        tf.word_wrap = False
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        lbl = labels[col_idx] if col_idx < len(labels) else f"P{col_idx + 1}"
        p.text = lbl
        p.font.name = theme.font_family_header
        p.font.size = Pt(11.0)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    # 4. Workstream Rows
    row_top = header_y + header_h + Inches(0.12)
    num_ws = len(data.workstreams)
    avail_h = Inches(4.25)
    row_gap = Inches(0.12)
    row_h = (avail_h - (num_ws - 1) * row_gap) / max(1, num_ws)

    status_colors = {
        "COMPLETED": theme.get_rgb("primary"),
        "IN_PROGRESS": theme.get_rgb("accent"),
        "PLANNED": RGBColor(203, 213, 225),  # Slate-300
        "DELAYED": RGBColor(220, 38, 38),     # Red-600
    }

    for ws_idx, ws in enumerate(data.workstreams):
        cur_y = row_top + ws_idx * (row_h + row_gap)

        # Left label container (Sharp Rectangle)
        ws_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, cur_y, Inches(2.90), row_h)
        ws_card.shadow.inherit = False
        strip_shape_shadows(ws_card)
        ws_card.fill.solid()
        ws_card.fill.fore_color.rgb = RGBColor(255, 255, 255)
        ws_card.line.color.rgb = RGBColor(226, 232, 240)
        ws_card.line.width = Pt(1.0)

        # Left accent stripe (Sharp Rectangle)
        accent_key = ws.accent_color
        acc_rgb = theme.get_rgb(accent_key) if accent_key in ("primary", "secondary", "accent") else theme.get_rgb("accent")
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, cur_y, Inches(0.08), row_h)
        stripe.shadow.inherit = False
        strip_shape_shadows(stripe)
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = acc_rgb
        stripe.line.fill.background()

        tf_ws = ws_card.text_frame
        tf_ws.word_wrap = True
        tf_ws.margin_left = Inches(0.18)
        tf_ws.margin_right = Inches(0.08)
        tf_ws.margin_top = Inches(0.06)
        p_badge = tf_ws.paragraphs[0]
        p_badge.text = ws.badge.upper()
        p_badge.font.name = theme.font_family_header
        p_badge.font.size = Pt(11.0)
        p_badge.font.bold = True
        p_badge.font.color.rgb = acc_rgb

        p_title = tf_ws.add_paragraph()
        p_title.text = ws.category
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(11.0)
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")
        p_title.space_before = Pt(2)

        # Grid row background
        row_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, grid_left, cur_y, grid_width, row_h)
        row_bg.shadow.inherit = False
        strip_shape_shadows(row_bg)
        row_bg.fill.solid()
        row_bg.fill.fore_color.rgb = RGBColor(248, 250, 252) if ws_idx % 2 == 0 else RGBColor(255, 255, 255)
        row_bg.line.color.rgb = RGBColor(226, 232, 240)
        row_bg.line.width = Pt(0.75)

        # Draw vertical grid column dividers inside row
        for c_idx in range(1, num_periods):
            cx = grid_left + c_idx * col_width
            vline = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cur_y, Pt(1), row_h)
            vline.shadow.inherit = False
            strip_shape_shadows(vline)
            vline.fill.solid()
            vline.fill.fore_color.rgb = RGBColor(226, 232, 240)
            vline.line.fill.background()

        # Render tasks inside this workstream
        num_tasks = len(ws.tasks)
        if num_tasks > 0:
            task_gap = Inches(0.04)
            task_margin = Inches(0.06)
            task_h = (row_h - 2 * task_margin - (num_tasks - 1) * task_gap) / num_tasks
            task_h = max(Inches(0.22), min(Inches(0.36), task_h))

            for t_idx, task in enumerate(ws.tasks):
                ty = cur_y + task_margin + t_idx * (task_h + task_gap)
                s_p = max(0.0, min(float(num_periods), task.start_period - 1.0))
                e_p = max(s_p + 0.1, min(float(num_periods), task.end_period))
                bar_x = grid_left + s_p * col_width
                bar_w = max(Inches(0.18), (e_p - s_p) * col_width)

                fill_rgb = status_colors.get(task.status, theme.get_rgb("primary"))

                if task.is_milestone:
                    # Milestone diamond marker
                    diam_size = task_h * 1.15
                    mx = bar_x + (bar_w - diam_size) / 2.0
                    my = ty + (task_h - diam_size) / 2.0
                    m_shape = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, mx, my, diam_size, diam_size)
                    m_shape.shadow.inherit = False
                    strip_shape_shadows(m_shape)
                    m_shape.fill.solid()
                    m_shape.fill.fore_color.rgb = theme.get_rgb("accent")
                    m_shape.line.color.rgb = theme.get_rgb("primary")
                    m_shape.line.width = Pt(1.5)

                    # Dynamic label placement (flip leftwards if near right margin)
                    label_w = Inches(2.20)
                    if mx + diam_size + label_w > Inches(12.70):
                        tb_m = slide.shapes.add_textbox(mx - label_w - Inches(0.06), ty - Inches(0.02), label_w, task_h)
                        tf_m = tb_m.text_frame
                        tf_m.word_wrap = True
                        p_m = tf_m.paragraphs[0]
                        p_m.alignment = PP_ALIGN.RIGHT
                    else:
                        tb_m = slide.shapes.add_textbox(mx + diam_size + Inches(0.06), ty - Inches(0.02), label_w, task_h)
                        tf_m = tb_m.text_frame
                        tf_m.word_wrap = True
                        p_m = tf_m.paragraphs[0]
                        p_m.alignment = PP_ALIGN.LEFT

                    p_m.text = task.name
                    p_m.font.name = theme.font_family_header
                    p_m.font.size = Pt(11.0)
                    p_m.font.bold = True
                    p_m.font.color.rgb = theme.get_rgb("primary")
                else:
                    # Task duration bar (Sharp Rectangle)
                    t_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bar_x, ty, bar_w, task_h)
                    t_shape.shadow.inherit = False
                    strip_shape_shadows(t_shape)
                    t_shape.fill.solid()
                    t_shape.fill.fore_color.rgb = fill_rgb
                    t_shape.line.color.rgb = RGBColor(255, 255, 255)
                    t_shape.line.width = Pt(0.75)

                    if bar_w < Inches(1.10):
                        # Narrow bar: place label to the right of the bar to prevent clipping
                        t_tb = slide.shapes.add_textbox(bar_x + bar_w + Inches(0.06), ty - Inches(0.02), Inches(2.20), task_h)
                        t_tf = t_tb.text_frame
                        t_tf.word_wrap = False
                        t_tf.margin_left = t_tf.margin_right = t_tf.margin_top = t_tf.margin_bottom = 0
                        p_t = t_tf.paragraphs[0]
                        p_t.text = task.name
                        p_t.font.name = theme.font_family_header
                        p_t.font.size = Pt(11.0)
                        p_t.font.bold = True
                        p_t.font.color.rgb = theme.get_rgb("primary")
                    else:
                        tf_t = t_shape.text_frame
                        tf_t.word_wrap = False
                        tf_t.margin_left = Inches(0.06)
                        tf_t.margin_right = Inches(0.06)
                        tf_t.margin_top = Inches(0.01)
                        p_t = tf_t.paragraphs[0]
                        p_t.text = task.name
                        p_t.font.name = theme.font_family_header
                        p_t.font.size = Pt(11.0)
                        p_t.font.bold = True
                        p_t.font.color.rgb = RGBColor(255, 255, 255) if task.status != "PLANNED" else theme.get_rgb("primary")

    # 5. Current Period "TODAY / SPRINT" Indicator
    if data.current_period_marker is not None and 0.0 <= data.current_period_marker <= float(num_periods):
        marker_x = grid_left + (data.current_period_marker - 1.0) * col_width
        total_grid_h = num_ws * (row_h + row_gap)
        m_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, marker_x, header_y, Pt(2), header_h + Inches(0.12) + total_grid_h)
        m_line.shadow.inherit = False
        strip_shape_shadows(m_line)
        m_line.fill.solid()
        m_line.fill.fore_color.rgb = RGBColor(220, 38, 38)  # Crimson Red
        m_line.line.fill.background()

        # Marker tag on top
        tag_w = Inches(0.95)
        tag_h = Inches(0.24)
        tag_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, marker_x - tag_w / 2.0, header_y - Inches(0.26), tag_w, tag_h)
        tag_box.shadow.inherit = False
        strip_shape_shadows(tag_box)
        tag_box.fill.solid()
        tag_box.fill.fore_color.rgb = RGBColor(220, 38, 38)
        tag_box.line.fill.background()
        tf_tag = tag_box.text_frame
        p_tag = tf_tag.paragraphs[0]
        p_tag.alignment = PP_ALIGN.CENTER
        p_tag.text = "CURRENT"
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(11.0)
        p_tag.font.bold = True
        p_tag.font.color.rgb = RGBColor(255, 255, 255)

    # 6. Bottom Legend & Footnote
    legend_y = Inches(6.62)
    legend_items = [
        ("●", theme.get_rgb("primary"), "Completed Phase"),
        ("●", theme.get_rgb("accent"), "Active / In-Progress"),
        ("●", RGBColor(203, 213, 225), "Planned Baseline"),
        ("◆", theme.get_rgb("accent"), "Key Milestone Gate"),
    ]
    cur_lx = left_x
    for symbol, sym_color, sym_label in legend_items:
        tb_leg = slide.shapes.add_textbox(cur_lx, legend_y, Inches(2.2), Inches(0.28))
        tf_l = tb_leg.text_frame
        p_l = tf_l.paragraphs[0]
        r_sym = p_l.add_run()
        r_sym.text = f"{symbol} "
        r_sym.font.name = theme.font_family_header
        r_sym.font.size = Pt(11.0)
        r_sym.font.bold = True
        r_sym.font.color.rgb = sym_color

        r_lbl = p_l.add_run()
        r_lbl.text = sym_label
        r_lbl.font.name = theme.font_family
        r_lbl.font.size = Pt(11.0)
        r_lbl.font.color.rgb = theme.get_rgb("secondary")
        cur_lx += Inches(2.05)

    if data.footnote:
        tb_fn = slide.shapes.add_textbox(grid_left, legend_y, grid_width, Inches(0.28))
        tf_fn = tb_fn.text_frame
        p_fn = tf_fn.paragraphs[0]
        p_fn.alignment = PP_ALIGN.RIGHT
        p_fn.text = data.footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(11.0)
        p_fn.font.italic = True
    # 7. Slide Footer
    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)

    # Enforce flat vector geometry by stripping drop shadows across all slide shapes
    for sh in slide.shapes:
        strip_shape_shadows(sh)

    return slide


@dataclass
class PICRowData:
    """Row in the named counterpart (PIC) governance matrix."""
    discipline: str
    vendor_pic: str
    client_pic: str
    accountability: str
    status: str = "CONFIRMED"
    status_bg_key: str = "badge_green_fill"
    status_text_key: str = "badge_green_text"


@dataclass
class RunbookQuadrantData:
    """Definition of one quadrant in the 4-Quadrant Workstream Runbook."""
    title: str
    tagline: str
    items: List[str]
    accent_key: str = "accent"
    badge: Optional[str] = None
    icon: Optional[str] = None


@dataclass
class DenseWorkstreamRunbookData:
    """Structured data model for a dense technical workstream runbook slide (Gear 3)."""
    workstream_id: str = "WS1"
    workstream_name: str = "AWS Landing Zone Foundation"
    phase: str = "PHASE 1  |  SPRINTS 1-3"
    sla_target: str = "99.99% Availability"
    objective: Optional[RunbookQuadrantData] = None
    vendor_actions: Optional[RunbookQuadrantData] = None
    client_actions: Optional[RunbookQuadrantData] = None
    dependencies: Optional[RunbookQuadrantData] = None
    pic_matrix: Optional[List[PICRowData]] = None
    notice: Optional[str] = None


def build_dense_workstream_runbook_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "WORKSTREAM RUNBOOK  |  WS1: AWS LANDING ZONE FOUNDATION",
    action_title: str = "AWS Landing Zone Foundation Establishes Multi-Account Isolation and Transit Mesh",
    subtitle: Optional[str] = "Contractual engineering execution runbook defining technical deliverables, counterpart PICs, and cross-stream dependencies.",
    runbook_data: Optional[DenseWorkstreamRunbookData] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Architecture & Modernization Practice  |  Confidential & Contractual",
) -> Any:
    """
    Builds a Gear 3 Technical Workstream Runbook slide (Workstream Runbook pattern).
    Enforces the 4-quadrant container discipline (Objective, MII Actions, Client Actions,
    Cross-Stream Dependencies) plus a bottom Named Counterpart (PIC) Accountability Matrix.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)
    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)

    # Resolve Default Dataset if not provided
    if runbook_data is None:
        runbook_data = DenseWorkstreamRunbookData(
            workstream_id="WS1",
            workstream_name="AWS Landing Zone Foundation",
            phase="PHASE 1  |  SPRINTS 1-3",
            sla_target="99.99% Availability",
            objective=RunbookQuadrantData(
                title="1. OBJECTIVE & ARCHITECTURE SCOPE",
                tagline="Multi-account topology, Transit Gateway mesh & security baseline",
                accent_key="primary",
                badge="WS1 MANDATE",
                items=[
                    "Dedicated VPC topology with isolated CIDR /20 blocks per workload tier",
                    "AWS Organizations multi-account hierarchy with strict SCP boundary enforcement",
                    "Centralized Transit Gateway routing for on-premises DirectConnect peering",
                    "Automated Terraform Landing Zone modules with zero-trust IAM baselines",
                ],
            ),
            dependencies=RunbookQuadrantData(
                title="2. CROSS-STREAM DEPENDENCIES & PREREQUISITES",
                tagline="Upstream inputs, change advisory windows & platform blockers",
                accent_key="danger",
                badge="CRITICAL PATH",
                items=[
                    "Network Team: Dedicated 10 Gbps DirectConnect circuit termination & BGP route peering",
                    "Security / CISO: KMS customer-managed key (CMK) policy approval & KMS key custodians",
                    "Enterprise CAB: Scheduled production change freeze window waiver for Transit Gateway cutover",
                    "WS2 Ingress Sync: Schema registry & private VPC interface endpoints deployed prior to sprint 4",
                ],
            ),
            vendor_actions=RunbookQuadrantData(
                title="3. MII ACTIONS & ENGINEERING DELIVERABLES",
                tagline="Lead delivery responsibilities, automation scripts & configuration runbooks",
                accent_key="accent",
                badge="VENDOR SOW",
                items=[
                    "Deploy modular Terraform IaC for Core Network, Security Hub & Audit Logging accounts",
                    "Configure AWS Network Firewall with stateful inspection rules for outbound internet egress",
                    "Provision AWS Secrets Manager with automatic credential rotation for lakehouse service roles",
                    "Conduct automated CIS AWS Benchmark security compliance assessment and deliver BAST evidence",
                ],
            ),
            client_actions=RunbookQuadrantData(
                title="4. CLIENT ACTIONS & GOVERNANCE APPROVALS",
                tagline="Client counterpart responsibilities, enterprise approvals & boundary prerequisites",
                accent_key="warning",
                badge="CLIENT PIC",
                items=[
                    "Allocate non-overlapping corporate IP CIDR subnets (/20 range) in Enterprise IPAM",
                    "Authorize Active Directory Federation Service (ADFS) / SAML 2.0 integration for enterprise SSO",
                    "Assign designated enterprise security and network engineering counterparts for weekly standups",
                    "Execute User Acceptance Testing (UAT) signoff and issue formal BAST milestone certificate",
                ],
            ),
            pic_matrix=[
                PICRowData(
                    discipline="Cloud & Network Architecture",
                    vendor_pic="Dewi Lestari (Lead Architect)",
                    client_pic="Budi Santoso (VP Enterprise Infra)",
                    accountability="Transit Gateway, VPC Topology & DirectConnect",
                    status="CONFIRMED",
                    status_bg_key="badge_green_fill",
                    status_text_key="badge_green_text",
                ),
                PICRowData(
                    discipline="Cyber Security & IAM Governance",
                    vendor_pic="Agus Pratama (Security Engineer)",
                    client_pic="Hendra Wijaya (Head of Cyber Defense)",
                    accountability="SCP Guardrails, IAM Roles & KMS Encryption",
                    status="CONFIRMED",
                    status_bg_key="badge_green_fill",
                    status_text_key="badge_green_text",
                ),
                PICRowData(
                    discipline="Infrastructure as Code (Terraform)",
                    vendor_pic="Rizky Setiawan (DevOps Specialist)",
                    client_pic="Ferry Kurniawan (Lead Cloud Ops)",
                    accountability="Terraform State Pipeline & CI/CD Deployment",
                    status="CONFIRMED",
                    status_bg_key="badge_green_fill",
                    status_text_key="badge_green_text",
                ),
                PICRowData(
                    discipline="Program PMO & Governance",
                    vendor_pic="Siti Nurhaliza (Engagement PM)",
                    client_pic="Ratna Sari (Enterprise PMO Lead)",
                    accountability="Sprint Gates, BAST Milestone Approval & CAB",
                    status="ACTION REQ",
                    status_bg_key="badge_amber_fill",
                    status_text_key="badge_amber_text",
                ),
            ],
        )

    # 1. Workstream Status Strip (Pills)
    strip_y = Inches(1.36)
    pills = [
        (f"WORKSTREAM: {runbook_data.workstream_id}", "accent"),
        (f"PHASE: {runbook_data.phase}", "secondary"),
        (f"SLA: {runbook_data.sla_target}", "success"),
        ("COMPLEXITY: GEAR 3 (TECHNICAL RUNBOOK)", "neutral"),
    ]
    cur_x = Inches(0.80)
    for text, c_key in pills:
        pill_w = Inches(0.12 * len(text) + 0.40)
        _add_status_pill(
            slide,
            theme,
            left=cur_x,
            top=strip_y,
            width=pill_w,
            height=Inches(0.24),
            status=text,
            font_size_pt=8.0,
            override_color_key=c_key,
        )
        cur_x += pill_w + Inches(0.10)

    # 2. 4-Quadrant Container Grid
    # Col 1: Left (0.80"), Col 2: Right (6.766"), Width: 5.766", Gap: 0.20"
    col1_x = Inches(0.80)
    col2_x = Inches(6.766)
    quad_w = Inches(5.766)
    quad_h = Inches(1.68)
    row1_y = Inches(1.68)
    row2_y = Inches(3.46)

    quadrants = [
        (runbook_data.objective, col1_x, row1_y, "primary", RGBColor(30, 41, 59)),
        (runbook_data.dependencies, col2_x, row1_y, "danger", RGBColor(220, 38, 38)),
        (runbook_data.vendor_actions, col1_x, row2_y, "accent", RGBColor(2, 132, 199)),
        (runbook_data.client_actions, col2_x, row2_y, "warning", RGBColor(217, 119, 6)),
    ]

    for q_data, q_x, q_y, accent_key, stripe_rgb in quadrants:
        if not q_data:
            continue
        # Strict sharp rectangle geometry for containers with top stripes
        add_card_with_top_stripe(
            slide=slide,
            theme=theme,
            left=q_x,
            top=q_y,
            width=quad_w,
            height=quad_h,
            accent_rgb=stripe_rgb,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            stripe_height_in=0.045,
        )

        # Content Text Box (Zero internal margins for tight technical density)
        tb = slide.shapes.add_textbox(q_x + Inches(0.16), q_y + Inches(0.10), quad_w - Inches(0.32), quad_h - Inches(0.18))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        # Title line
        p_title = tf.paragraphs[0]
        p_title.text = q_data.title
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(10.0)
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")

        # Tagline / Subtitle
        p_tag = tf.add_paragraph()
        p_tag.text = q_data.tagline
        p_tag.font.name = theme.font_family
        p_tag.font.size = Pt(8.0)
        p_tag.font.color.rgb = theme.get_rgb("muted")
        p_tag.space_before = Pt(1.5)

        # Bullet items (tight 8.5pt micro-typography)
        for itm in q_data.items[:4]:
            p_itm = tf.add_paragraph()
            p_itm.text = f"•  {itm}"
            p_itm.font.name = theme.font_family
            p_itm.font.size = Pt(8.5)
            p_itm.font.color.rgb = theme.get_rgb("secondary")
            p_itm.space_before = Pt(2.0)

    # 3. Bottom Row: Named Counterpart & PIC Accountability Matrix
    table_x = Inches(0.80)
    table_y = Inches(5.24)
    table_w = Inches(11.733)
    table_h = Inches(1.70)

    add_card_with_top_stripe(
        slide=slide,
        theme=theme,
        left=table_x,
        top=table_y,
        width=table_w,
        height=table_h,
        accent_rgb=RGBColor(22, 163, 74),  # Reconciled Target State Green
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("border"),
        stripe_height_in=0.045,
    )

    # Section Header inside PIC Container
    h_tb = slide.shapes.add_textbox(table_x + Inches(0.16), table_y + Inches(0.10), table_w - Inches(0.32), Inches(0.24))
    h_tf = h_tb.text_frame
    h_tf.word_wrap = True
    h_tf.margin_left = h_tf.margin_right = h_tf.margin_top = h_tf.margin_bottom = 0
    hp = h_tf.paragraphs[0]
    hp.text = "5. GOVERNANCE & NAMED COUNTERPART (PIC) ACCOUNTABILITY MATRIX"
    hp.font.name = theme.font_family_header
    hp.font.size = Pt(10.0)
    hp.font.bold = True
    hp.font.color.rgb = theme.get_rgb("primary")

    # Table Column Grid Coordinates:
    # Discipline (2.2"), Vendor PIC (2.3"), Client PIC (2.3"), Scope (3.5"), Status (1.1")
    col_x_offsets = [Inches(0.16), Inches(2.36), Inches(4.76), Inches(7.16), Inches(10.46)]
    col_widths = [Inches(2.10), Inches(2.30), Inches(2.30), Inches(3.20), Inches(1.10)]
    headers = [
        "TECHNICAL DISCIPLINE",
        "VENDOR PIC (MII)",
        "CLIENT PIC (BANK)",
        "CONTRACTUAL SCOPE & DELIVERABLES",
        "STATUS",
    ]

    # Render Header Row
    header_row_y = table_y + Inches(0.36)
    for c_idx, (off_x, c_w, h_text) in enumerate(zip(col_x_offsets, col_widths, headers)):
        th_box = slide.shapes.add_textbox(table_x + off_x, header_row_y, c_w, Inches(0.20))
        th_tf = th_box.text_frame
        th_tf.margin_left = th_tf.margin_right = th_tf.margin_top = th_tf.margin_bottom = 0
        p_th = th_tf.paragraphs[0]
        p_th.text = h_text
        p_th.font.name = theme.font_family_header
        p_th.font.size = Pt(8.0)
        p_th.font.bold = True
        p_th.font.color.rgb = theme.get_rgb("muted")

    # Render Separator Hairline
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_x + Inches(0.16), header_row_y + Inches(0.20), table_w - Inches(0.32), Pt(0.75))
    sep.shadow.inherit = False
    strip_shape_shadows(sep)
    sep.fill.solid()
    sep.fill.fore_color.rgb = theme.get_rgb("border")
    sep.line.fill.background()

    # Render PIC Data Rows
    row_start_y = header_row_y + Inches(0.24)
    row_height = Inches(0.26)
    if runbook_data.pic_matrix:
        for r_idx, row in enumerate(runbook_data.pic_matrix[:4]):
            curr_y = row_start_y + (r_idx * row_height)
            row_vals = [row.discipline, row.vendor_pic, row.client_pic, row.accountability]

            for c_idx, (off_x, c_w, val) in enumerate(zip(col_x_offsets[:4], col_widths[:4], row_vals)):
                r_box = slide.shapes.add_textbox(table_x + off_x, curr_y, c_w, Inches(0.22))
                r_tf = r_box.text_frame
                r_tf.margin_left = r_tf.margin_right = r_tf.margin_top = r_tf.margin_bottom = 0
                p_r = r_tf.paragraphs[0]
                p_r.text = val
                p_r.font.name = theme.font_family
                p_r.font.size = Pt(8.0)
                if c_idx == 0:
                    p_r.font.bold = True
                    p_r.font.color.rgb = theme.get_rgb("primary")
                else:
                    p_r.font.color.rgb = theme.get_rgb("secondary")

            # Status Pill in Col 5
            _add_status_pill(
                slide,
                theme,
                left=table_x + col_x_offsets[4],
                top=curr_y,
                width=col_widths[4],
                height=Inches(0.20),
                status=row.status,
                font_size_pt=8.0,
                override_color_key="success" if "CONFIRM" in row.status else "warning",
            )

    return slide


@dataclass
class SwimlaneNodeData:
    """A single service or component node within an architecture swimlane."""
    title: str
    subtitle: str
    category: Optional[str] = None
    icon: Optional[str] = None
    is_out_of_scope: bool = False
    status_badge: Optional[str] = None
    badge_bg_key: str = "badge_blue_fill"
    badge_text_key: str = "badge_blue_text"


@dataclass
class SwimlanePathConnector:
    """Workstream path routing connector between swimlanes."""
    workstream_tag: str
    label: str
    from_swimlane: str
    to_swimlane: str
    latency_sla: Optional[str] = None


@dataclass
class ArchitectureSwimlaneColumn:
    """Definition of one boundary swimlane column in the 3-column target architecture."""
    swimlane_title: str
    tagline: str
    nodes: List[SwimlaneNodeData] = field(default_factory=list)
    accent_key: str = "primary"
    is_target_platform: bool = False
    boundary_notice: Optional[str] = None


@dataclass
class TargetArchitectureSwimlaneData:
    """Structured data model for a 3-column target architecture swimlane slide (Gear 2)."""
    columns: Optional[List[ArchitectureSwimlaneColumn]] = None
    workstream_connectors: Optional[List[SwimlanePathConnector]] = None
    out_of_scope_callout: Optional[str] = None
    show_top_stripes: bool = False


def build_target_architecture_swimlane_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Target Lakehouse Architecture Establishes Unified Medallion Ingestion and Semantic Serving",
    subtitle: Optional[str] = None,
    swimlane_data: Optional[TargetArchitectureSwimlaneData] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
) -> Any:
    """
    Builds a Gear 2 Target Architecture Swimlane slide (Swimlane Architecture pattern).
    Enforces a 3-column boundary topology (Source Ingress -> Target Lakehouse -> Consumers),
    with strictly opt-in workstream routing banner and top stripes.
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)
    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)

    # Resolve Default Dataset if not provided
    if swimlane_data is None:
        swimlane_data = TargetArchitectureSwimlaneData(
            columns=[
                ArchitectureSwimlaneColumn(
                    swimlane_title="1. ON-PREMISES & SOURCES",
                    tagline="Core banking databases, file feeds & transactional message queues",
                    accent_key="neutral",
                    is_target_platform=False,
                    boundary_notice="Boundary: Private DirectConnect 10 Gbps",
                    nodes=[
                        SwimlaneNodeData(
                            title="Core Banking Oracle DB",
                            subtitle="Primary OLTP database running transactional deposits & GL",
                            category="DATABASE",
                            status_badge="ACTIVE SOURCE",
                        ),
                        SwimlaneNodeData(
                            title="Enterprise Kafka Stream",
                            subtitle="Event message bus streaming real-time debit card telemetry",
                            category="STREAMING BUS",
                            status_badge="REAL-TIME",
                        ),
                        SwimlaneNodeData(
                            title="Legacy Batch File Shares",
                            subtitle="End-of-day balance reconciliations & external partner CSVs",
                            category="SFTP / NFS",
                            is_out_of_scope=True,
                            status_badge="OUT OF SCOPE",
                        ),
                    ],
                ),
                ArchitectureSwimlaneColumn(
                    swimlane_title="2. TARGET CLOUD LAKEHOUSE (CORE)",
                    tagline="Centralized AWS/Databricks/Snowflake governed medallion architecture",
                    accent_key="primary",
                    is_target_platform=True,
                    boundary_notice="Unity Catalog / Cross-Account IAM Mesh",
                    nodes=[
                        SwimlaneNodeData(
                            title="Bronze Ingestion Landing Zone",
                            subtitle="Raw append-only storage with automated schema drift validation",
                            category="RAW INGESTION",
                            status_badge="WS2: CDC INGEST",
                        ),
                        SwimlaneNodeData(
                            title="Silver Curated Lakehouse Tier",
                            subtitle="Cleaned, deduplicated & validated conformance tables (dbt Core)",
                            category="CURATED ENGINE",
                            status_badge="WS3: DBT MODELING",
                        ),
                        SwimlaneNodeData(
                            title="Gold Dimensional Data Marts",
                            subtitle="Business domain star schemas, aggregation marts & feature stores",
                            category="SEMANTIC CORE",
                            status_badge="TARGET STATE",
                        ),
                    ],
                ),
                ArchitectureSwimlaneColumn(
                    swimlane_title="3. ANALYTICS & CONSUMERS",
                    tagline="Executive dashboards, machine learning endpoints & regulatory reporting",
                    accent_key="accent",
                    is_target_platform=False,
                    boundary_notice="Role-Based Row/Column Security",
                    nodes=[
                        SwimlaneNodeData(
                            title="Executive Power BI Dashboards",
                            subtitle="Direct Lake semantic models providing sub-second KPI exploration",
                            category="BI / REPORTING",
                            status_badge="WS4: SERVING",
                        ),
                        SwimlaneNodeData(
                            title="AI / ML Feature Serving Core",
                            subtitle="Real-time credit scoring, fraud classification & inference APIs",
                            category="DATA SCIENCE",
                            status_badge="WS4: SERVING",
                        ),
                        SwimlaneNodeData(
                            title="OJK Regulatory Compliance Marts",
                            subtitle="Standardized statutory reporting feeds and automated audit extracts",
                            category="REGULATORY",
                            status_badge="AUDITED",
                        ),
                    ],
                ),
            ],
            workstream_connectors=[
                SwimlanePathConnector(
                    workstream_tag="WS1",
                    label="AWS Landing Zone & Transit Gateway Mesh (DirectConnect 10 Gbps)",
                    from_swimlane="On-Premises",
                    to_swimlane="Cloud Platform",
                    latency_sla="< 5ms Latency",
                ),
                SwimlanePathConnector(
                    workstream_tag="WS2",
                    label="Debezium CDC Streaming & Batch File Ingestion Pipeline",
                    from_swimlane="Source Databases",
                    to_swimlane="Bronze Storage",
                    latency_sla="Near Real-Time",
                ),
                SwimlanePathConnector(
                    workstream_tag="WS3",
                    label="dbt Core Automated Medallion Transformations (Bronze ➔ Silver ➔ Gold)",
                    from_swimlane="Bronze Layer",
                    to_swimlane="Gold Marts",
                    latency_sla="Hourly / Daily",
                ),
                SwimlanePathConnector(
                    workstream_tag="WS4",
                    label="Semantic Delivery to Executive Power BI & Real-Time ML APIs",
                    from_swimlane="Gold Data Marts",
                    to_swimlane="Consumers",
                    latency_sla="Sub-Second SQL",
                ),
            ],
            out_of_scope_callout="* Out-of-scope boundaries (e.g., Legacy Batch File Shares) remain client-managed under separate CAB change control.",
        )

    # 1. 3-Column Swimlane Geometry
    # Left: 0.80", Widths: Col1 3.40", Col2 4.80" (Hero), Col3 3.133", Gaps 0.20"
    col_x_list = [Inches(0.80), Inches(4.40), Inches(9.40)]
    col_w_list = [Inches(3.40), Inches(4.80), Inches(3.133)]
    has_connectors = bool(swimlane_data.workstream_connectors)
    use_top_stripes = bool(getattr(swimlane_data, "show_top_stripes", False))
    lane_y_in = resolve_content_top(header_bottom, gap_in=0.14)
    lane_y = Inches(lane_y_in)
    bottom_limit = 6.10 if has_connectors else 6.85
    lane_h = Inches(max(3.60, bottom_limit - lane_y_in))

    stripe_colors = [
        RGBColor(71, 85, 105),   # Slate for Ingress
        RGBColor(2, 132, 199),   # Sky Blue for Target Lakehouse
        RGBColor(16, 185, 129),  # Emerald/Teal for Consumers
    ]

    for c_idx, col_data in enumerate(swimlane_data.columns[:3]):
        cx = col_x_list[c_idx]
        cw = col_w_list[c_idx]
        st_color = stripe_colors[c_idx]

        # Background container for swimlane
        bg_tint = theme.get_rgb("surface") if col_data.is_target_platform else theme.get_rgb("surface_muted")
        b_color = theme.get_rgb("primary") if col_data.is_target_platform else theme.get_rgb("border")

        if use_top_stripes:
            add_card_with_top_stripe(
                slide=slide,
                theme=theme,
                left=cx,
                top=lane_y,
                width=cw,
                height=lane_h,
                accent_rgb=st_color,
                bg_color=bg_tint,
                border_color=b_color,
                border_width_pt=1.5 if col_data.is_target_platform else 1.0,
                stripe_height_in=0.05,
            )
        else:
            add_card(
                slide=slide,
                theme=theme,
                left=cx,
                top=lane_y,
                width=cw,
                height=lane_h,
                bg_color=bg_tint,
                border_color=b_color,
                border_width_pt=1.5 if col_data.is_target_platform else 1.0,
                force_rectangle=True,
            )

        # Swimlane Header
        h_tb = slide.shapes.add_textbox(cx + Inches(0.16), lane_y + Inches(0.10), cw - Inches(0.32), Inches(0.48))
        h_tf = h_tb.text_frame
        h_tf.word_wrap = True
        h_tf.margin_left = h_tf.margin_right = h_tf.margin_top = h_tf.margin_bottom = 0

        p1 = h_tf.paragraphs[0]
        p1.text = col_data.swimlane_title
        p1.font.name = theme.font_family_header
        p1.font.size = Pt(10.5)
        p1.font.bold = True
        p1.font.color.rgb = theme.get_rgb("primary")

        p2 = h_tf.add_paragraph()
        p2.text = col_data.tagline
        p2.font.name = theme.font_family
        p2.font.size = Pt(8.0)
        p2.font.color.rgb = theme.get_rgb("muted")
        p2.space_before = Pt(1.5)

        # Component Node Cards inside Swimlane
        node_start_y = lane_y + Inches(0.66)
        node_h = Inches(1.18)
        node_gap = Inches(0.12)
        node_w = cw - Inches(0.32)
        node_x = cx + Inches(0.16)

        for n_idx, node in enumerate(col_data.nodes[:3]):
            curr_node_y = node_start_y + (n_idx * (node_h + node_gap))

            # Out of scope border styling (Amber dashed or warning badge)
            if node.is_out_of_scope:
                n_border_rgb = RGBColor(217, 119, 6)
                n_bg_rgb = theme.get_rgb("badge_amber_fill")
            else:
                n_border_rgb = theme.get_rgb("border")
                n_bg_rgb = theme.get_rgb("surface")

            node_card = add_card(
                slide=slide,
                theme=theme,
                left=node_x,
                top=curr_node_y,
                width=node_w,
                height=node_h,
                bg_color=n_bg_rgb,
                border_color=n_border_rgb,
                force_rectangle=True,
            )

            # Text content inside node card
            n_tb = slide.shapes.add_textbox(node_x + Inches(0.14), curr_node_y + Inches(0.10), node_w - Inches(0.28), node_h - Inches(0.18))
            n_tf = n_tb.text_frame
            n_tf.word_wrap = True
            n_tf.margin_left = n_tf.margin_right = n_tf.margin_top = n_tf.margin_bottom = 0

            # Category Tag
            if node.category:
                p_cat = n_tf.paragraphs[0]
                p_cat.text = node.category.upper()
                p_cat.font.name = theme.font_family_header
                p_cat.font.size = Pt(8.0)
                p_cat.font.bold = True
                p_cat.font.color.rgb = theme.get_rgb("accent")

                p_ntitle = n_tf.add_paragraph()
            else:
                p_ntitle = n_tf.paragraphs[0]

            # Node Title
            p_ntitle.text = node.title
            p_ntitle.font.name = theme.font_family_header
            p_ntitle.font.size = Pt(9.5)
            p_ntitle.font.bold = True
            p_ntitle.font.color.rgb = theme.get_rgb("primary")
            if node.category:
                p_ntitle.space_before = Pt(1.5)

            # Node Subtitle
            p_nsub = n_tf.add_paragraph()
            p_nsub.text = node.subtitle
            p_nsub.font.name = theme.font_family
            p_nsub.font.size = Pt(8.0)
            p_nsub.font.color.rgb = theme.get_rgb("secondary")
            p_nsub.space_before = Pt(2.0)

    # 2. Bottom Banner: Opt-In Workstream Routing Pathways
    if has_connectors:
        banner_x = Inches(0.80)
        banner_y = Inches(6.18)
        banner_w = Inches(11.733)
        banner_h = Inches(0.78)

        add_card_with_top_stripe(
            slide=slide,
            theme=theme,
            left=banner_x,
            top=banner_y,
            width=banner_w,
            height=banner_h,
            accent_rgb=RGBColor(2, 132, 199),  # Sky Blue
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            stripe_height_in=0.035,
        )

        # Banner Header
        b_tb = slide.shapes.add_textbox(banner_x + Inches(0.14), banner_y + Inches(0.06), banner_w - Inches(0.28), Inches(0.20))
        b_tf = b_tb.text_frame
        b_tf.margin_left = b_tf.margin_right = b_tf.margin_top = b_tf.margin_bottom = 0
        bp = b_tf.paragraphs[0]
        bp.text = "WORKSTREAM INTEGRATION & ROUTING PATHWAYS"
        bp.font.name = theme.font_family_header
        bp.font.size = Pt(8.5)
        bp.font.bold = True
        bp.font.color.rgb = theme.get_rgb("primary")

        # Render Workstream Connectors as 4 Horizontal Flow Blocks
        flow_x_offsets = [Inches(0.14), Inches(2.98), Inches(5.82), Inches(8.66)]
        flow_w = Inches(2.70)
        flow_y = banner_y + Inches(0.28)

        for f_idx, conn in enumerate(swimlane_data.workstream_connectors[:4]):
            fx = banner_x + flow_x_offsets[f_idx]
            f_box = slide.shapes.add_textbox(fx, flow_y, flow_w, Inches(0.42))
            f_tf = f_box.text_frame
            f_tf.word_wrap = True
            f_tf.margin_left = f_tf.margin_right = f_tf.margin_top = f_tf.margin_bottom = 0

            # Line 1: [WS1] Tag + From -> To
            fp1 = f_tf.paragraphs[0]
            fp1.text = f"[{conn.workstream_tag}]  {conn.from_swimlane} ➔ {conn.to_swimlane}"
            fp1.font.name = theme.font_family_header
            fp1.font.size = Pt(8.0)
            fp1.font.bold = True
            fp1.font.color.rgb = theme.get_rgb("accent")

            # Line 2: Label / Protocol
            fp2 = f_tf.add_paragraph()
            fp2.text = conn.label
            fp2.font.name = theme.font_family
            fp2.font.size = Pt(8.0)
            fp2.font.color.rgb = theme.get_rgb("secondary")
            fp2.space_before = Pt(1.0)

    return slide

