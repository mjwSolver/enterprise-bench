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
    add_slide_with_background, add_slide_header, add_card, add_card_with_top_stripe,
    add_card_with_harmonized_icon, add_slide_footer, add_takeaway_bar, _interpolate_color, _get_contrast_text_color,
    _add_bullet_paragraph, _fit_image_in_box,
)

logger = logging.getLogger(__name__)

def build_browser_mockup_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "System Architecture & Interface Validation",
    action_title: str = "Modernized Analytics Platform Eliminates ERP Latency and Siloed Data Exports",
    subtitle: Optional[str] = "High-fidelity interface preview running directly on Snowflake Cortex AI and Streamlit serving tiers.",
    screenshot_path: Optional[Union[str, Path]] = None,
    url: str = "https://finance.snowflakecomputing.com/streamlit/app",
    telemetry_badges: Optional[List[str]] = None,
    theme_mode: str = "light",
    aspect_ratio: Optional[str] = "16:9",
    target_dpi: int = 300,
    takeaways_title: str = "KEY OBSERVATIONS & DRIVERS",
    takeaways: Optional[List[Dict[str, Any]]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
    output_temp_dir: Optional[Path] = None,
) -> Any:
    """
    Renders an executive presentation slide featuring a high-DPI browser mockup container
    on the left (w=7.60") paired with structured observation cards on the right (w=3.88").
    """
    from src.ppt_engine.image_engine import frame_browser_mockup, ImageEngine

    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # 1. Resolve source image or generate high-fidelity fallback
    if screenshot_path and Path(screenshot_path).exists():
        src_img: Union[str, Path, Image.Image] = Path(screenshot_path)
    else:
        engine = ImageEngine()
        src_img = engine.generate_procedural_3d_card(
            title="Enterprise Analytics Platform",
            primary_color=theme.get_hex("primary"),
            accent_color=theme.get_hex("accent"),
        )

    # 2. Render Mockup Container
    if telemetry_badges is None:
        telemetry_badges = [
            "🏷️ Snowflake Cortex AI",
            "⚡ Real-Time Ingestion",
            "📊 Daily Reconciled",
        ]

    save_dir = Path(output_temp_dir) if output_temp_dir else Path("output/mockups")
    save_dir.mkdir(parents=True, exist_ok=True)
    temp_mockup_path = save_dir / f"slide_mockup_{current_idx}_{theme_mode}.png"

    frame_browser_mockup(
        image_input=src_img,
        url=url,
        theme_mode=theme_mode,
        target_dpi=target_dpi,
        target_width_in=7.6,
        aspect_ratio=aspect_ratio,
        telemetry_badges=telemetry_badges,
        output_path=temp_mockup_path,
    )

    # 3. Add Framed Mockup Image Picture to Slide
    mockup_x = Inches(0.80)
    mockup_y = Inches(1.85)
    mockup_w = Inches(7.60)
    slide.shapes.add_picture(str(temp_mockup_path), mockup_x, mockup_y, width=mockup_w)

    # 4. Right Column: Structured Takeaways & Observation Cards
    right_x = Inches(8.65)
    right_w = Inches(3.88)
    right_y = Inches(1.85)

    if takeaways is None:
        takeaways = [
            {
                "title": "Continuous Data Ingestion",
                "body": "Replaces 12-hour nightly batch jobs with Snowpipe micro-batching, delivering sub-minute analytical readiness.",
                "tag": "LATENCY REDUCTION",
                "tag_color": "accent",
            },
            {
                "title": "Automated Dynamic Masking",
                "body": "Role-based access control (RBAC) masks sensitive enterprise PII without requiring manual spreadsheet scrubbers.",
                "tag": "SECURITY & AUDIT",
                "tag_color": "secondary",
            },
            {
                "title": "Executive Self-Service Serving",
                "body": "Streamlit app gives finance leadership real-time margin drill-downs without waiting for IT ticket resolution.",
                "tag": "BUSINESS AGILITY",
                "tag_color": "primary",
            },
        ]

    # Render Right Column Section Header Badge
    hdr_h = Inches(0.32)
    h_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x, right_y, right_w, hdr_h)
    h_card.shadow.inherit = False
    h_card.fill.solid()
    h_card.fill.fore_color.rgb = theme.get_rgb("primary")
    h_card.line.fill.background()

    tf_h = h_card.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = Inches(0.12)
    tf_h.margin_top = Inches(0.06)
    p_h = tf_h.paragraphs[0]
    p_h.text = takeaways_title.upper()
    p_h.font.name = theme.font_family_header
    p_h.font.size = Pt(9.5)
    p_h.font.bold = True
    p_h.font.color.rgb = RGBColor(255, 255, 255)

    # Stack observation cards
    card_gap = Inches(0.14)
    num_cards = len(takeaways)
    total_card_space = Inches(4.35)
    card_h = (total_card_space - (num_cards - 1) * card_gap) / max(1, num_cards)

    cur_card_y = right_y + hdr_h + Inches(0.12)
    for t_item in takeaways:
        accent_key = t_item.get("tag_color", "accent")
        accent_rgb = theme.get_rgb(accent_key) if accent_key in ("primary", "secondary", "accent") else theme.get_rgb("accent")
        c_card, _ = add_card_with_top_stripe(
            slide=slide,
            theme=theme,
            left=right_x,
            top=cur_card_y,
            width=right_w,
            height=card_h,
            accent_rgb=accent_rgb,
            stripe_height_in=0.035,
        )
        tf_c = c_card.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = Inches(0.16)
        tf_c.margin_right = Inches(0.16)
        tf_c.margin_top = Inches(0.10)
        tf_c.margin_bottom = Inches(0.08)

        # Tag
        p_tag = tf_c.paragraphs[0]
        p_tag.text = t_item.get("tag", "OBSERVATION").upper()
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(8.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = accent_rgb

        # Title
        p_tit = tf_c.add_paragraph()
        p_tit.text = t_item.get("title", "")
        p_tit.font.name = theme.font_family_header
        p_tit.font.size = Pt(11.0)
        p_tit.font.bold = True
        p_tit.font.color.rgb = theme.get_rgb("primary")
        p_tit.space_before = Pt(3)

        # Body / Bullets
        body_val = t_item.get("body") or t_item.get("desc") or t_item.get("description") or ""
        if isinstance(body_val, list):
            for b_item in body_val:
                p_b = tf_c.add_paragraph()
                p_b.text = f"•  {b_item}"
                p_b.font.name = theme.font_family
                p_b.font.size = Pt(8.5)
                p_b.font.color.rgb = theme.get_rgb("secondary")
                p_b.space_before = Pt(2)
        else:
            p_bod = tf_c.add_paragraph()
            p_bod.text = str(body_val)
            p_bod.font.name = theme.font_family
            p_bod.font.size = Pt(9.0)
            p_bod.font.color.rgb = theme.get_rgb("secondary")
            p_bod.space_before = Pt(3)

        cur_card_y += card_h + card_gap

    # 5. Slide Footer
    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


def build_iceberg_concept_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "STRATEGIC RATIONALE | ARCHITECTURE FOUNDATION",
    action_title: str = "Modern Data Platform Architecture Solves the Critical Subsurface Foundation Gap",
    subtitle: Optional[str] = "While executives interact with surface dashboards, 85% of analytical resilience depends on robust foundation engineering.",
    visible_items: Optional[List[Dict[str, str]]] = None,
    subsurface_items: Optional[List[Dict[str, str]]] = None,
    takeaways: Optional[List[str]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """Renders the Iceberg Concept: Visible 15% Business Interface vs. Subsurface 85% Data Platform Foundation."""
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if not visible_items:
        visible_items = [
            {"title": "Executive KPI Dashboards", "desc": "Tableau & Power BI visual summaries for C-level tracking."},
            {"title": "Streamlit Financial Apps", "desc": "Interactive margin, opex, and scenario analysis portals."},
            {"title": "Cortex GenAI Summaries", "desc": "Natural language automated performance reporting."},
        ]

    if not subsurface_items:
        subsurface_items = [
            {"title": "Snowflake AI Data Cloud", "desc": "Decoupled cloud storage and multi-cluster elastic compute engines."},
            {"title": "Automated CDC Pipelines", "desc": "Continuous Kafka/dbt ingestion capturing ERP transactions without downtime."},
            {"title": "dbt Semantic Models", "desc": "Standardized star-schema data marts eliminating query divergence."},
            {"title": "RBAC & Dynamic Masking", "desc": "Granular PII protection, column dynamic masking, and audit logging."},
            {"title": "Automated Orchestration", "desc": "Dependency-aware DAG pipelines with alerting and SLA triggers."},
            {"title": "FinOps & Cost Governance", "desc": "Warehouse auto-suspend/resume preventing runaway compute spend."},
        ]

    if not takeaways:
        takeaways = [
            "Dashboard failures originate in broken upstream data pipelines, not visualization design.",
            "Legacy point-to-point ETL creates untraceable data lineage and reporting discrepancies.",
            "Snowflake's decoupled storage-compute architecture guarantees 99.99% uptime and zero contention.",
            "Investing in subsurface foundation data engineering reduces maintenance overhead by 70%.",
        ]

    left_x = Inches(0.80)
    top_y = Inches(1.80)
    iceberg_w = Inches(7.70)
    iceberg_h = Inches(5.00)

    takeaway_x = left_x + iceberg_w + Inches(0.30)
    takeaway_w = Inches(11.733) - iceberg_w - Inches(0.30)
    takeaway_h = iceberg_h

    # 1. Above the Waterline Container (Top 28% of left panel)
    above_h = Inches(1.50)
    add_card(
        slide,
        theme,
        left_x,
        top_y,
        iceberg_w,
        above_h,
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("accent"),
        border_width_pt=1.5,
    )

    atb = slide.shapes.add_textbox(left_x + Inches(0.16), top_y + Inches(0.08), iceberg_w - Inches(0.32), Inches(0.26))
    atf = atb.text_frame
    atf.margin_left = atf.margin_right = atf.margin_top = atf.margin_bottom = 0
    ap = atf.paragraphs[0]
    ap.text = "ABOVE THE WATERLINE  |  WHAT THE BUSINESS SEES (15% OF EFFORT)"
    ap.font.name = theme.font_family_header
    ap.font.size = Pt(8.5)
    ap.font.bold = True
    ap.font.color.rgb = theme.get_rgb("accent")

    col_w_above = (iceberg_w - Inches(0.32) - (Inches(0.12) * 2)) / 3.0
    for i, itm in enumerate(visible_items[:3]):
        ix = left_x + Inches(0.16) + (i * (col_w_above + Inches(0.12)))
        iy = top_y + Inches(0.38)
        ih = above_h - Inches(0.48)

        add_card(
            slide,
            theme,
            ix,
            iy,
            col_w_above,
            ih,
            bg_color=theme.get_rgb("surface_muted"),
            border_color=theme.get_rgb("border"),
        )
        tb_i = slide.shapes.add_textbox(ix + Inches(0.08), iy + Inches(0.08), col_w_above - Inches(0.16), ih - Inches(0.16))
        tf_i = tb_i.text_frame
        tf_i.word_wrap = True
        tf_i.margin_left = tf_i.margin_right = tf_i.margin_top = tf_i.margin_bottom = 0
        p_it = tf_i.paragraphs[0]
        p_it.text = itm.get("title", "")
        p_it.font.name = theme.font_family_header
        p_it.font.size = Pt(8.5)
        p_it.font.bold = True
        p_it.font.color.rgb = theme.get_rgb("primary")

        p_id = tf_i.add_paragraph()
        p_id.text = itm.get("desc", "")
        p_id.font.name = theme.font_family
        p_id.font.size = Pt(7.5)
        p_id.font.color.rgb = theme.get_rgb("secondary")
        p_id.space_before = Pt(2)

    # 2. Waterline Divider Bar
    waterline_y = top_y + above_h + Inches(0.08)
    waterline_h = Inches(0.26)
    wl_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, waterline_y, iceberg_w, waterline_h)
    wl_bar.shadow.inherit = False
    wl_bar.fill.solid()
    wl_bar.fill.fore_color.rgb = theme.get_rgb("accent")
    wl_bar.line.fill.background()

    wl_tf = wl_bar.text_frame
    wl_tf.margin_left = wl_tf.margin_right = wl_tf.margin_top = wl_tf.margin_bottom = 0
    wl_p = wl_tf.paragraphs[0]
    wl_p.text = "---  THE WATERLINE: ARCHITECTURAL FOUNDATION BOUNDARY  ---"
    wl_p.alignment = PP_ALIGN.CENTER
    wl_p.font.name = theme.font_family_header
    wl_p.font.size = Pt(8.5)
    wl_p.font.bold = True
    wl_p.font.color.rgb = RGBColor(255, 255, 255)

    # 3. Below the Waterline Container
    below_y = waterline_y + waterline_h + Inches(0.08)
    below_h = iceberg_h - (below_y - top_y)
    add_card(
        slide,
        theme,
        left_x,
        below_y,
        iceberg_w,
        below_h,
        bg_color=RGBColor(15, 23, 42),
        border_color=theme.get_rgb("accent"),
        border_width_pt=1.5,
    )

    btb = slide.shapes.add_textbox(left_x + Inches(0.16), below_y + Inches(0.08), iceberg_w - Inches(0.32), Inches(0.26))
    btf = btb.text_frame
    btf.margin_left = btf.margin_right = btf.margin_top = btf.margin_bottom = 0
    bp = btf.paragraphs[0]
    bp.text = "BELOW THE WATERLINE  |  DATA PLATFORM FOUNDATION (85% OF ARCHITECTURAL INVESTMENT)"
    bp.font.name = theme.font_family_header
    bp.font.size = Pt(8.5)
    bp.font.bold = True
    bp.font.color.rgb = RGBColor(147, 197, 253)

    b_cols = 2
    b_rows = 3
    b_gap_x = Inches(0.14)
    b_gap_y = Inches(0.10)
    b_item_w = (iceberg_w - Inches(0.32) - (b_gap_x * (b_cols - 1))) / b_cols
    b_item_h = (below_h - Inches(0.44) - (b_gap_y * (b_rows - 1))) / b_rows

    for i, itm in enumerate(subsurface_items[:6]):
        r_i = i // b_cols
        c_i = i % b_cols
        bx = left_x + Inches(0.16) + (c_i * (b_item_w + b_gap_x))
        by = below_y + Inches(0.36) + (r_i * (b_item_h + b_gap_y))

        add_card(
            slide,
            theme,
            bx,
            by,
            b_item_w,
            b_item_h,
            bg_color=RGBColor(30, 41, 59),
            border_color=RGBColor(51, 65, 85),
            border_width_pt=0.75,
        )

        tb_bi = slide.shapes.add_textbox(bx + Inches(0.08), by + Inches(0.06), b_item_w - Inches(0.16), b_item_h - Inches(0.12))
        tf_bi = tb_bi.text_frame
        tf_bi.word_wrap = True
        tf_bi.margin_left = tf_bi.margin_right = tf_bi.margin_top = tf_bi.margin_bottom = 0

        p_bit = tf_bi.paragraphs[0]
        p_bit.text = itm.get("title", "")
        p_bit.font.name = theme.font_family_header
        p_bit.font.size = Pt(8.5)
        p_bit.font.bold = True
        p_bit.font.color.rgb = RGBColor(241, 245, 249)

        p_bid = tf_bi.add_paragraph()
        p_bid.text = itm.get("desc", "")
        p_bid.font.name = theme.font_family
        p_bid.font.size = Pt(7.5)
        p_bid.font.color.rgb = RGBColor(148, 163, 184)
        p_bid.space_before = Pt(1.5)

    # RIGHT PANEL: STRATEGIC TAKEAWAY
    add_card_with_top_stripe(
        slide,
        theme,
        takeaway_x,
        top_y,
        takeaway_w,
        takeaway_h,
        accent_rgb=theme.get_rgb("accent"),
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("border"),
    )

    ttb = slide.shapes.add_textbox(
        takeaway_x + Inches(0.18),
        top_y + Inches(0.14),
        takeaway_w - Inches(0.36),
        takeaway_h - Inches(0.28),
    )
    ttf = ttb.text_frame
    ttf.word_wrap = True
    ttf.margin_left = ttf.margin_right = ttf.margin_top = ttf.margin_bottom = 0

    tp1 = ttf.paragraphs[0]
    tp1.text = "STRATEGIC TAKEAWAY"
    tp1.font.name = theme.font_family_header
    tp1.font.size = Pt(12.0)
    tp1.font.bold = True
    tp1.font.color.rgb = theme.get_rgb("primary")

    tp2 = ttf.add_paragraph()
    tp2.text = "Why Foundation Data Engineering Outweighs UI Styling"
    tp2.font.name = theme.font_family
    tp2.font.size = Pt(9.0)
    tp2.font.color.rgb = theme.get_rgb("secondary")
    tp2.space_before = Pt(2)

    for bullet in takeaways:
        _add_bullet_paragraph(
            ttf,
            bullet,
            theme.font_family,
            font_size_pt=8.5,
            font_color=theme.get_rgb("secondary"),
            space_before_pt=8.0,
        )


def build_open_telemetry_flow_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "CLINICAL AI GOVERNANCE | REAL-TIME TELEMETRY & GATE VERIFICATION",
    action_title: str = "Dual-Engine Pipeline Telemetry Validates 99.4% Model Fidelity and Enforces Sub-Second Inference SLAs",
    subtitle: Optional[str] = "Real-time Snowflake Cortex inference audits confirm automated compliance gates across all 4 production reproductive medicine prediction models.",
    pipeline_steps: Optional[List[Dict[str, Any]]] = None,
    hero_metrics: Optional[List[Dict[str, Any]]] = None,
    mockup_config: Optional[Dict[str, Any]] = None,
    left_title: Optional[str] = "Production Model Serving Console",
    left_subtitle: Optional[str] = "Snowflake Snowpark Container Services & Streamlit HUD",
    right_title: Optional[str] = "Automated Production Quality Gates",
    right_subtitle: Optional[str] = "Continuous Model Validation & Regulatory Threshold Tracking",
    gate_matrix: Optional[Dict[str, Any]] = None,
    footnote: Optional[str] = "Audit Window: 30-day rolling inference window across 12 Morula IVF clinic branches.",
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Architecture Practice  |  Clinical AI Telemetry Gate Demo",
) -> Any:
    """
    Renders an open-canvas technical architecture slide breaking away from standard
    boxed cards with top stripes, leveraging geometric primitives (lines, circles, triangles):
    - Top Continuous 3-Stage Pipeline Axis (Circular nodes, bus hairlines, directional chevrons)
    - Left Container-Free Serving Telemetry (Radial circular donut gauge, metric chips, floating macOS window)
    - Right Container-Free Cleveland Target Ray Matrix (Horizontal datum rays, circular target beads, downward triangular gate needles)
    """
    from src.ppt_engine.widgets.macos_window import render_macos_window

    def _resolve_color(col: Any, theme_ref: Theme, default_hex: str = "#DC2626") -> RGBColor:
        if isinstance(col, RGBColor):
            return col
        clean = str(col or "").strip().lower()
        if clean.startswith("#"):
            return hex_to_rgb(clean)
        named = {
            "emerald": "#10B981", "green": "#16A34A", "amber": "#D97706", "warning": "#F59E0B",
            "red": "#DC2626", "brickred": "#DC2626", "danger": "#DC2626", "blue": "#0284C7",
            "slate": "#64748B", "muted": "#94A3B8", "neutral": "#64748B", "gray": "#64748B",
        }
        if clean in named:
            return hex_to_rgb(named[clean])
        if hasattr(theme_ref, "palette") and clean in theme_ref.palette:
            try:
                return theme_ref.get_rgb(clean)
            except Exception:
                pass
        if clean == "accent":
            return theme_ref.get_rgb("accent")
        return hex_to_rgb(default_hex)

    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # =========================================================================
    # 1. Top Continuous Process Highway (Lines + Circles + Triangles)
    # =========================================================================
    steps = pipeline_steps or [
        {"num": "01", "title": "STREAM INGESTION", "desc": "Snowpark Containers", "color": "blue"},
        {"num": "02", "title": "CORTEX INFERENCE", "desc": "Real-Time Serving HUD", "color": "accent"},
        {"num": "03", "title": "QUALITY GATE MATRIX", "desc": "Continuous Multi-SLA Verification", "color": "emerald"},
    ]

    pipe_nodes = [
        {"x": Inches(0.80), "step": steps[0]},
        {"x": Inches(4.55), "step": steps[1]},
        {"x": Inches(8.30), "step": steps[2]},
    ]

    for p_idx, node in enumerate(pipe_nodes):
        st = node["step"]
        nx = node["x"]
        c_rgb = _resolve_color(st.get("color", "accent"), theme, default_hex="#DC2626")

        # Circular Stage Node
        circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, nx, Inches(1.38), Inches(0.32), Inches(0.32))
        circ.fill.solid()
        if p_idx == 0:
            circ.fill.fore_color.rgb = RGBColor(224, 242, 254)
        elif p_idx == 1:
            circ.fill.fore_color.rgb = RGBColor(254, 226, 226)
        else:
            circ.fill.fore_color.rgb = RGBColor(220, 252, 231)
        circ.line.color.rgb = c_rgb
        circ.line.width = Pt(1.0)
        strip_shape_shadows(circ)

        tf_c = circ.text_frame
        tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
        p_num = tf_c.paragraphs[0]
        p_num.text = str(st.get("num", f"0{p_idx+1}"))
        p_num.font.name = theme.font_family_header
        p_num.font.size = Pt(8.5)
        p_num.font.bold = True
        p_num.font.color.rgb = c_rgb
        p_num.alignment = PP_ALIGN.CENTER

        # Stage Label Textbox
        tb_st = slide.shapes.add_textbox(nx + Inches(0.38), Inches(1.32), Inches(2.35), Inches(0.44))
        tf_st = tb_st.text_frame
        tf_st.word_wrap = True
        tf_st.margin_left = tf_st.margin_right = tf_st.margin_top = tf_st.margin_bottom = 0
        p1 = tf_st.paragraphs[0]
        p1.text = str(st.get("title", ""))
        p1.font.name = theme.font_family_header
        p1.font.size = Pt(8.8)
        p1.font.bold = True
        p1.font.color.rgb = RGBColor(15, 23, 42)

        p2 = tf_st.add_paragraph()
        p2.text = str(st.get("desc", ""))
        p2.font.name = theme.font_family
        p2.font.size = Pt(7.5)
        p2.font.color.rgb = RGBColor(100, 116, 139)

    # Connecting Conduits with Directional Chevrons (Triangles + Lines)
    conduits = [
        {"x_start": Inches(3.70), "w": Inches(0.70), "tri_x": Inches(3.98), "color": _resolve_color("accent", theme)},
        {"x_start": Inches(7.45), "w": Inches(0.70), "tri_x": Inches(7.73), "color": _resolve_color("emerald", theme)},
    ]
    for cond in conduits:
        l_sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cond["x_start"], Inches(1.53), cond["w"], Inches(0.018))
        l_sh.fill.solid()
        l_sh.fill.fore_color.rgb = RGBColor(203, 213, 225)
        l_sh.line.fill.background()
        strip_shape_shadows(l_sh)

        tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, cond["tri_x"], Inches(1.465), Inches(0.12), Inches(0.14))
        tri.rotation = 90.0
        tri.fill.solid()
        tri.fill.fore_color.rgb = cond["color"]
        tri.line.fill.background()
        strip_shape_shadows(tri)

    # Technical Blueprint Axis Line under pipeline
    axis_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.80), Inches(1.88), Inches(11.733), Inches(0.015))
    axis_line.fill.solid()
    axis_line.fill.fore_color.rgb = RGBColor(226, 232, 240)
    axis_line.line.fill.background()
    strip_shape_shadows(axis_line)

    # =========================================================================
    # 2. Central Vertical Dividing Datum Line (Fine Hairline + Circular Hub)
    # =========================================================================
    v_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.58), Inches(2.05), Inches(0.015), Inches(4.85))
    v_line.fill.solid()
    v_line.fill.fore_color.rgb = RGBColor(226, 232, 240)
    v_line.line.fill.background()
    strip_shape_shadows(v_line)

    hub_outer = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6.52), Inches(4.42), Inches(0.14), Inches(0.14))
    hub_outer.fill.solid()
    hub_outer.fill.fore_color.rgb = RGBColor(255, 255, 255)
    hub_outer.line.color.rgb = RGBColor(148, 163, 184)
    hub_outer.line.width = Pt(1.0)
    strip_shape_shadows(hub_outer)

    hub_inner = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(6.56), Inches(4.46), Inches(0.06), Inches(0.06))
    hub_inner.fill.solid()
    hub_inner.fill.fore_color.rgb = RGBColor(100, 116, 139)
    hub_inner.line.fill.background()
    strip_shape_shadows(hub_inner)

    # =========================================================================
    # 3. Left Section: Live Serving Telemetry & Interface
    # =========================================================================
    # Section Header
    tb_lh = slide.shapes.add_textbox(Inches(0.80), Inches(2.02), Inches(5.50), Inches(0.60))
    tf_lh = tb_lh.text_frame
    tf_lh.word_wrap = True
    tf_lh.margin_left = tf_lh.margin_right = tf_lh.margin_top = tf_lh.margin_bottom = 0
    p_le = tf_lh.paragraphs[0]
    p_le.text = "01 / RUNTIME HUD & CORTEX ENGINE"
    p_le.font.name = theme.font_family_header
    p_le.font.size = Pt(8.0)
    p_le.font.bold = True
    p_le.font.color.rgb = theme.get_rgb("accent")

    p_lt = tf_lh.add_paragraph()
    p_lt.text = str(left_title or "Production Model Serving Console")
    p_lt.font.name = theme.font_family_header
    p_lt.font.size = Pt(13.0)
    p_lt.font.bold = True
    p_lt.font.color.rgb = RGBColor(15, 23, 42)

    p_ls = tf_lh.add_paragraph()
    p_ls.text = str(left_subtitle or "Snowflake Snowpark Container Services & Streamlit HUD")
    p_ls.font.name = theme.font_family
    p_ls.font.size = Pt(8.5)
    p_ls.font.color.rgb = RGBColor(100, 116, 139)

    # Radial Donut Ring Gauge for Model Fidelity (Circles!)
    gauge_x = Inches(0.82)
    gauge_y = Inches(2.70)
    gauge_d = Inches(1.02)
    rg_out = slide.shapes.add_shape(MSO_SHAPE.OVAL, gauge_x, gauge_y, gauge_d, gauge_d)
    rg_out.fill.solid()
    rg_out.fill.fore_color.rgb = RGBColor(254, 226, 226)
    rg_out.line.color.rgb = theme.get_rgb("accent")
    rg_out.line.width = Pt(2.0)
    strip_shape_shadows(rg_out)

    cutout_d = Inches(0.80)
    rg_in = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        gauge_x + (gauge_d - cutout_d) / 2.0,
        gauge_y + (gauge_d - cutout_d) / 2.0,
        cutout_d,
        cutout_d,
    )
    rg_in.fill.solid()
    rg_in.fill.fore_color.rgb = RGBColor(255, 255, 255)
    rg_in.line.fill.background()
    strip_shape_shadows(rg_in)

    tb_g = slide.shapes.add_textbox(gauge_x, gauge_y + Inches(0.12), gauge_d, Inches(0.78))
    tf_g = tb_g.text_frame
    tf_g.margin_left = tf_g.margin_right = tf_g.margin_top = tf_g.margin_bottom = 0
    p_gv = tf_g.paragraphs[0]
    p_gv.text = "99.4%"
    p_gv.font.name = theme.font_family_header
    p_gv.font.size = Pt(13.5)
    p_gv.font.bold = True
    p_gv.font.color.rgb = theme.get_rgb("accent")
    p_gv.alignment = PP_ALIGN.CENTER

    p_gl = tf_g.add_paragraph()
    p_gl.text = "F1 SCORE"
    p_gl.font.name = theme.font_family_header
    p_gl.font.size = Pt(6.5)
    p_gl.font.bold = True
    p_gl.font.color.rgb = RGBColor(100, 116, 139)
    p_gl.alignment = PP_ALIGN.CENTER

    # Latency Telemetry Chip (Triangles + Lines)
    tb_m1 = slide.shapes.add_textbox(Inches(2.02), Inches(2.70), Inches(1.70), Inches(0.98))
    tf_m1 = tb_m1.text_frame
    tf_m1.margin_left = tf_m1.margin_right = tf_m1.margin_top = tf_m1.margin_bottom = 0
    p_m1_v = tf_m1.paragraphs[0]
    p_m1_v.text = "142ms"
    p_m1_v.font.name = theme.font_family_header
    p_m1_v.font.size = Pt(16.5)
    p_m1_v.font.bold = True
    p_m1_v.font.color.rgb = RGBColor(15, 23, 42)

    p_m1_d = tf_m1.add_paragraph()
    p_m1_d.text = "▼ -28ms under SLA"
    p_m1_d.font.name = theme.font_family_header
    p_m1_d.font.size = Pt(7.5)
    p_m1_d.font.bold = True
    p_m1_d.font.color.rgb = RGBColor(22, 163, 74)

    p_m1_l = tf_m1.add_paragraph()
    p_m1_l.text = "P99 INFERENCE LATENCY"
    p_m1_l.font.name = theme.font_family_header
    p_m1_l.font.size = Pt(7.0)
    p_m1_l.font.bold = True
    p_m1_l.font.color.rgb = RGBColor(100, 116, 139)

    div_m1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.02), Inches(3.72), Inches(1.65), Inches(0.015))
    div_m1.fill.solid()
    div_m1.fill.fore_color.rgb = RGBColor(226, 232, 240)
    div_m1.line.fill.background()
    strip_shape_shadows(div_m1)

    # Drift Telemetry Chip (Circles + Lines)
    tb_m2 = slide.shapes.add_textbox(Inches(3.88), Inches(2.70), Inches(1.70), Inches(0.98))
    tf_m2 = tb_m2.text_frame
    tf_m2.margin_left = tf_m2.margin_right = tf_m2.margin_top = tf_m2.margin_bottom = 0
    p_m2_v = tf_m2.paragraphs[0]
    p_m2_v.text = "0 Fail"
    p_m2_v.font.name = theme.font_family_header
    p_m2_v.font.size = Pt(16.5)
    p_m2_v.font.bold = True
    p_m2_v.font.color.rgb = RGBColor(15, 23, 42)

    p_m2_d = tf_m2.add_paragraph()
    p_m2_d.text = "● 100% Attestation"
    p_m2_d.font.name = theme.font_family_header
    p_m2_d.font.size = Pt(7.5)
    p_m2_d.font.bold = True
    p_m2_d.font.color.rgb = RGBColor(22, 163, 74)

    p_m2_l = tf_m2.add_paragraph()
    p_m2_l.text = "PRODUCTION DRIFT BREACHES"
    p_m2_l.font.name = theme.font_family_header
    p_m2_l.font.size = Pt(7.0)
    p_m2_l.font.bold = True
    p_m2_l.font.color.rgb = RGBColor(100, 116, 139)

    div_m2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(3.88), Inches(3.72), Inches(1.65), Inches(0.015))
    div_m2.fill.solid()
    div_m2.fill.fore_color.rgb = RGBColor(226, 232, 240)
    div_m2.line.fill.background()
    strip_shape_shadows(div_m2)

    # Floating Streamlit Interface Mockup (No Card Container!)
    w_cfg = mockup_config or {
        "url": "https://snowflake.morulaivf.co.id/cortex/clinical-models/live",
        "theme_mode": "light",
        "telemetry_badges": ["Snowflake Cortex", "Streamlit Serving", "Zero PII Leak"],
    }
    render_macos_window(slide, theme, left=0.80, top=3.88, width=5.50, height=3.02, config=w_cfg)

    # =========================================================================
    # 4. Right Section: Multi-Gate Cleveland Target Ray Matrix (Lines + Circles + Triangles)
    # =========================================================================
    # Section Header
    tb_rh = slide.shapes.add_textbox(Inches(6.85), Inches(2.02), Inches(5.68), Inches(0.60))
    tf_rh = tb_rh.text_frame
    tf_rh.word_wrap = True
    tf_rh.margin_left = tf_rh.margin_right = tf_rh.margin_top = tf_rh.margin_bottom = 0
    p_re = tf_rh.paragraphs[0]
    p_re.text = "02 / MULTI-STAGE COMPLIANCE MATRIX"
    p_re.font.name = theme.font_family_header
    p_re.font.size = Pt(8.0)
    p_re.font.bold = True
    p_re.font.color.rgb = theme.get_rgb("accent")

    p_rt = tf_rh.add_paragraph()
    p_rt.text = str(right_title or "Automated Production Quality Gates")
    p_rt.font.name = theme.font_family_header
    p_rt.font.size = Pt(13.0)
    p_rt.font.bold = True
    p_rt.font.color.rgb = RGBColor(15, 23, 42)

    p_rs = tf_rh.add_paragraph()
    p_rs.text = str(right_subtitle or "Continuous Model Validation & Regulatory Threshold Tracking")
    p_rs.font.name = theme.font_family
    p_rs.font.size = Pt(8.5)
    p_rs.font.color.rgb = RGBColor(100, 116, 139)

    # Target Ray Layout Parameters
    lbl_w = Inches(1.95)
    col_gap = Inches(0.12)
    bar_track_w = Inches(1.95)
    bar_x = Inches(6.85) + lbl_w + col_gap
    val_x = bar_x + bar_track_w + col_gap
    val_w = Inches(1.54)

    chart_y = Inches(3.22)
    row_h = Inches(0.46)
    row_gap = Inches(0.30)

    # Data series
    raw_series = (gate_matrix.get("series") if gate_matrix else None) or [
        {"label": "EMBRYO_VIABILITY_SCORE", "value": 0.994, "display_value": "99.4%", "subtext": "(42.8k calls)", "status": "PASS", "bar_color": "accent"},
        {"label": "IVF_CYCLE_ATTRITION", "value": 0.962, "display_value": "96.2%", "subtext": "(18.4k calls)", "status": "PASS", "bar_color": "accent"},
        {"label": "CLINICAL_PROTOCOL_REC", "value": 0.887, "display_value": "88.7%", "subtext": "(6.2k calls)", "status": "WARN", "bar_color": "amber"},
        {"label": "PATIENT_RESPONSE_ETL", "value": 0.741, "display_value": "74.1%", "subtext": "(92.1k rows)", "status": "AUDIT", "bar_color": "slate"},
    ]

    total_matrix_h = len(raw_series) * row_h + (len(raw_series) - 1) * row_gap

    # Threshold Gate Needles (Triangles + Lines)
    th_specs = [
        {"pct": 0.85, "label": "85% CLINICAL SLA", "color": "amber", "rgb": _resolve_color("amber", theme), "pill_x": Inches(9.50), "pill_w": Inches(1.15)},
        {"pct": 0.95, "label": "95% REGULATORY GATE", "color": "emerald", "rgb": _resolve_color("emerald", theme), "pill_x": Inches(10.68), "pill_w": Inches(1.22)},
    ]

    for th in th_specs:
        th_line_x = bar_x + (bar_track_w * th["pct"])

        # Floating Pill Badge
        th_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, th["pill_x"], Inches(2.74), th["pill_w"], Inches(0.20))
        th_pill.fill.solid()
        if th["color"] == "amber":
            th_pill.fill.fore_color.rgb = RGBColor(254, 243, 199)
        else:
            th_pill.fill.fore_color.rgb = RGBColor(236, 253, 245)
        th_pill.line.color.rgb = th["rgb"]
        th_pill.line.width = Pt(0.75)
        strip_shape_shadows(th_pill)

        tf_p = th_pill.text_frame
        tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_p.word_wrap = False
        tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0
        p_th = tf_p.paragraphs[0]
        p_th.text = th["label"]
        p_th.font.name = theme.font_family_header
        p_th.font.size = Pt(6.8)
        p_th.font.bold = True
        p_th.font.color.rgb = th["rgb"]
        p_th.alignment = PP_ALIGN.CENTER

        # Downward Needle Triangle (Triangles!)
        tri_gate = slide.shapes.add_shape(
            MSO_SHAPE.ISOSCELES_TRIANGLE,
            th_line_x - Inches(0.07),
            Inches(2.96),
            Inches(0.14),
            Inches(0.11),
        )
        tri_gate.rotation = 180.0
        tri_gate.fill.solid()
        tri_gate.fill.fore_color.rgb = th["rgb"]
        tri_gate.line.fill.background()
        strip_shape_shadows(tri_gate)

        # Vertical Gate Hairline
        g_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            th_line_x,
            Inches(3.07),
            Inches(0.015),
            total_matrix_h + Inches(0.25),
        )
        g_line.fill.solid()
        g_line.fill.fore_color.rgb = th["rgb"]
        g_line.line.fill.background()
        strip_shape_shadows(g_line)

    # Series Rows: Cleveland Target Rays with Circular Target Beads (Lines + Circles!)
    for idx, s in enumerate(raw_series):
        curr_y = chart_y + idx * (row_h + row_gap)
        lbl_text = str(s.get("label", f"Series {idx+1}"))
        raw_val = float(s.get("value", 0.0))
        val_pct = raw_val if raw_val <= 1.0 else (raw_val / 100.0)
        disp_val = s.get("display_value", f"{val_pct*100:.1f}%")
        subtext = s.get("subtext", "")
        status_tag = s.get("status", "PASS")

        bar_rgb = _resolve_color(s.get("bar_color", "accent"), theme, default_hex="#DC2626")
        status_rgb = _resolve_color(
            s.get("status_color", "emerald" if status_tag == "PASS" else ("amber" if status_tag == "WARN" else "slate")),
            theme,
            default_hex="#10B981",
        )

        # 1. Row Label (Strictly 1 font type and 1 font size across all series)
        tb_lbl = slide.shapes.add_textbox(Inches(6.85), curr_y, lbl_w, row_h)
        tf_lbl = tb_lbl.text_frame
        tf_lbl.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_lbl.word_wrap = False
        tf_lbl.margin_left = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
        tf_lbl.margin_right = Pt(4)
        p_lbl = tf_lbl.paragraphs[0]
        p_lbl.text = lbl_text
        p_lbl.font.name = theme.font_family_header
        p_lbl.font.size = Pt(8.5)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = RGBColor(30, 41, 59)

        # 2. Horizontal Datum Baseline (Line)
        baseline = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            bar_x,
            curr_y + Inches(0.22),
            bar_track_w,
            Inches(0.025),
        )
        baseline.fill.solid()
        baseline.fill.fore_color.rgb = RGBColor(226, 232, 240)
        baseline.line.fill.background()
        strip_shape_shadows(baseline)

        # 3. Active Measurement Ray (Line)
        fill_w = Inches(1.95 * val_pct)
        ray = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            bar_x,
            curr_y + Inches(0.215),
            fill_w,
            Inches(0.035),
        )
        ray.fill.solid()
        ray.fill.fore_color.rgb = bar_rgb
        ray.line.fill.background()
        strip_shape_shadows(ray)

        # 4. Circular Target Acquisition Bead (Circles!)
        cx = bar_x + fill_w
        cy = curr_y + Inches(0.232)
        dot_out = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            cx - Inches(0.09),
            cy - Inches(0.09),
            Inches(0.18),
            Inches(0.18),
        )
        dot_out.fill.solid()
        dot_out.fill.fore_color.rgb = bar_rgb
        dot_out.line.fill.background()
        strip_shape_shadows(dot_out)

        dot_in = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            cx - Inches(0.04),
            cy - Inches(0.04),
            Inches(0.08),
            Inches(0.08),
        )
        dot_in.fill.solid()
        dot_in.fill.fore_color.rgb = RGBColor(255, 255, 255)
        dot_in.line.fill.background()
        strip_shape_shadows(dot_in)

        # 5. Gate Clearance Diamond Checkpoint (Diamonds!)
        for th in th_specs:
            if val_pct >= th["pct"]:
                th_x = bar_x + (bar_track_w * th["pct"])
                dia = slide.shapes.add_shape(
                    MSO_SHAPE.DIAMOND,
                    th_x - Inches(0.04),
                    cy - Inches(0.04),
                    Inches(0.08),
                    Inches(0.08),
                )
                dia.fill.solid()
                dia.fill.fore_color.rgb = th["rgb"]
                dia.line.fill.background()
                strip_shape_shadows(dia)

        # 6. Value Readout & Status Symbol on Right
        tb_val = slide.shapes.add_textbox(val_x, curr_y, val_w, row_h)
        tf_val = tb_val.text_frame
        tf_val.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_val.word_wrap = False
        tf_val.margin_left = Pt(4)
        tf_val.margin_right = tf_val.margin_top = tf_val.margin_bottom = 0
        p_val = tf_val.paragraphs[0]
        p_val.text = f"{disp_val} "
        p_val.font.name = theme.font_family_header
        p_val.font.size = Pt(9.0)
        p_val.font.bold = True
        p_val.font.color.rgb = RGBColor(15, 23, 42)

        if subtext:
            r_sub = p_val.add_run()
            r_sub.text = f"{subtext} "
            r_sub.font.size = Pt(7.8)
            r_sub.font.color.rgb = RGBColor(100, 116, 139)

        r_tag = p_val.add_run()
        sym = "●" if status_tag == "PASS" else ("▲" if status_tag == "WARN" else "■")
        r_tag.text = f"{sym} [{status_tag}]"
        r_tag.font.bold = True
        r_tag.font.size = Pt(8.2)
        r_tag.font.color.rgb = status_rgb

    # Technical Baseline Footnote (Lines + Crosshairs)
    fn_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.85), Inches(6.36), Inches(5.68), Inches(0.015))
    fn_line.fill.solid()
    fn_line.fill.fore_color.rgb = RGBColor(226, 232, 240)
    fn_line.line.fill.background()
    strip_shape_shadows(fn_line)

    tb_fn = slide.shapes.add_textbox(Inches(6.85), Inches(6.42), Inches(5.68), Inches(0.24))
    tf_fn = tb_fn.text_frame
    tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
    p_fn = tf_fn.paragraphs[0]
    p_fn.text = f"+ {footnote} +"
    p_fn.font.name = theme.font_family
    p_fn.font.size = Pt(8.0)
    p_fn.font.color.rgb = RGBColor(100, 116, 139)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide



# ============================================================================
# 15. Gate Validation & Empirical Threshold Review Slide Archetype
# ============================================================================

def build_gate_validation_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "EMPIRICAL DATA RECONNAISSANCE & LIMITATIONS",
    action_title: str = "Historical Volume Is Viable for Baseline, but Heavily Concentrated",
    subtitle: Optional[str] = "11,950 labelled rows across 27 months with 21% no-show rate; billing and SOAP clear 90% join threshold.",
    kpis: Optional[List[Dict[str, Any]]] = None,
    chart_data: Optional[Dict[str, Any]] = None,
    constraints_card: Optional[Dict[str, Any]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an executive presentation slide featuring:
    - Top KPI Strip (3-4 metric cards with semantic accent stripes)
    - Left Container: Horizontal bar chart with vertical gate lines (threshold_bars widget)
    - Right Container: Core constraints card with hero stat block, bold bullets, and takeaway box
    """
    from src.ppt_engine.widgets.threshold_bars import render_threshold_bars

    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # 1. Top KPI Banner
    if kpis is None:
        kpis = [
            {"stat": "11,950", "label": "Labelled Cohort Rows", "subtext": "2024-07 to 2026-09 Encounters", "color": "accent"},
            {"stat": "21.0%", "label": "Baseline No-Show Rate", "subtext": "Stable Operational Class Rate", "color": "accent"},
            {"stat": "27 Mos", "label": "Historical Window", "subtext": "Longitudinal Depth on PROD", "color": "accent"},
            {"stat": "6 of 6", "label": "Quality Gates Passed", "subtext": "Zero Schema or Null Blockers", "color": "emerald"},
        ]

    kpi_top = Inches(1.80)
    kpi_h = Inches(1.05)
    total_w = Inches(11.733)
    n_kpis = max(1, len(kpis))
    card_gap = Inches(0.20)
    card_w = (total_w - (card_gap * (n_kpis - 1))) / n_kpis

    for idx, k_item in enumerate(kpis):
        kpi_x = Inches(0.80) + idx * (card_w + card_gap)
        col_key = k_item.get("color", "accent")
        col_rgb = theme.get_rgb(col_key) if hasattr(theme, "get_rgb") else RGBColor(2, 132, 199)

        # Card Background
        card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, kpi_x, kpi_top, card_w, kpi_h)
        card.fill.solid()
        card.fill.fore_color.rgb = theme.get_rgb("surface")
        card.line.color.rgb = theme.get_rgb("border")
        card.line.width = Pt(1.0)
        strip_shape_shadows(card)

        # Top Accent Stripe
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, kpi_x, kpi_top, card_w, Inches(0.06))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = col_rgb
        stripe.line.fill.background()
        strip_shape_shadows(stripe)

        # Text Frame
        tf = card.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = Inches(0.15)
        tf.margin_top = tf.margin_bottom = Inches(0.08)

        p1 = tf.paragraphs[0]
        p1.text = str(k_item.get("stat", ""))
        p1.font.name = theme.font_family_header
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = col_rgb
        p1.alignment = PP_ALIGN.LEFT

        p2 = tf.add_paragraph()
        p2.text = str(k_item.get("label", "")).upper()
        p2.font.name = theme.font_family_header
        p2.font.size = Pt(9.5)
        p2.font.bold = True
        p2.font.color.rgb = theme.get_rgb("primary")
        p2.space_before = Pt(2)

        if k_item.get("subtext"):
            p3 = tf.add_paragraph()
            p3.text = str(k_item.get("subtext", ""))
            p3.font.name = theme.font_family
            p3.font.size = Pt(8.5)
            p3.font.color.rgb = theme.get_rgb("secondary")
            p3.space_before = Pt(1)

    # 2. Bottom Section: Split Screen
    bottom_top = Inches(3.02)
    bottom_h = Inches(3.90)

    # Left Container: Join Coverage / Threshold Bars (width 6.60")
    left_x = Inches(0.80)
    left_w = Inches(6.60)

    if chart_data is None:
        chart_data = {
            "title": "Join Coverage to Cohort",
            "subtitle": "Empirical PROD join rates.",
            "series": [
                {"label": "FACT_TRANSACTION", "value": 0.999, "display_value": "99.9%", "subtext": "(8.68M)", "status": "PASS", "bar_color": "accent", "status_color": "emerald"},
                {"label": "FACT_SOAP_PATIENT", "value": 0.958, "display_value": "95.8%", "subtext": "(193.7K)", "status": "PASS", "bar_color": "accent", "status_color": "emerald"},
                {"label": "FACT_CHAT", "value": 0.664, "display_value": "66.4%", "subtext": "(Starts 2025)", "status": "EXCL", "bar_color": "muted", "status_color": "secondary"},
                {"label": "FACT_CALL_CENTER", "value": 0.253, "display_value": "25.3%", "subtext": "(8.8K rows)", "status": "EXCL", "bar_color": "danger", "status_color": "danger"},
            ],
            "thresholds": [
                {"value": 0.90, "label": ">=90% GATE", "color": "emerald"},
                {"value": 0.60, "label": "<60% EXCL", "color": "amber"},
            ],
            "footnote": "Audit Finding: Billing & SOAP exceed quality bar; Chat/Calls excluded due to short history.",
        }

    render_threshold_bars(slide, theme, left_x, bottom_top, left_w, bottom_h, chart_data)

    # Right Container: Constraints Card (width 4.933")
    right_x = Inches(7.60)
    right_w = Inches(4.933)

    bg_right = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x, bottom_top, right_w, bottom_h)
    bg_right.fill.solid()
    bg_right.fill.fore_color.rgb = theme.get_rgb("surface")
    bg_right.line.color.rgb = theme.get_rgb("border")
    bg_right.line.width = Pt(1.0)
    strip_shape_shadows(bg_right)

    stripe_r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x, bottom_top, right_w, Inches(0.06))
    stripe_r.fill.solid()
    stripe_r.fill.fore_color.rgb = theme.get_rgb("warning", default="#D97706")
    stripe_r.line.fill.background()
    strip_shape_shadows(stripe_r)

    if constraints_card is None:
        constraints_card = {
            "title": "What Limits the Data (Core Constraints)",
            "subtitle": "Three operational realities governing production generalization.",
            "hero_stat": "94.9% Concentration",
            "hero_stat_label": "MIJ Menteng Branch Dominance",
            "bullets": [
                "Branch Skew: MIJ Menteng holds 94.9% of rows; requires branch calibration for regional clinics.",
                "Snapshot Grain: Appointment table reflects final status only; cancellation lead time is unrecorded.",
                "Proxy Label: REALISASI serves as proxy; clinic front-desk cancellation interviews pending.",
            ],
            "takeaway": "TAKEAWAY: Sufficient for initial POC; regional generalization requires multi-clinic data.",
        }

    # Right Header
    tb_rh = slide.shapes.add_textbox(right_x + Inches(0.25), bottom_top + Inches(0.14), right_w - Inches(0.50), Inches(0.50))
    tf_rh = tb_rh.text_frame
    tf_rh.word_wrap = True
    tf_rh.margin_left = tf_rh.margin_right = tf_rh.margin_top = tf_rh.margin_bottom = 0
    p_rh1 = tf_rh.paragraphs[0]
    p_rh1.text = str(constraints_card.get("title", "Core Constraints"))
    p_rh1.font.name = theme.font_family_header
    p_rh1.font.size = Pt(13)
    p_rh1.font.bold = True
    p_rh1.font.color.rgb = theme.get_rgb("primary")

    if constraints_card.get("subtitle"):
        p_rh2 = tf_rh.add_paragraph()
        p_rh2.text = str(constraints_card.get("subtitle"))
        p_rh2.font.name = theme.font_family
        p_rh2.font.size = Pt(9.5)
        p_rh2.font.color.rgb = theme.get_rgb("secondary")

    # Big Concentration Stat Card
    hero_stat = constraints_card.get("hero_stat")
    hero_offset_y = 0.0
    if hero_stat:
        stat_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x + Inches(0.25), bottom_top + Inches(0.78), right_w - Inches(0.50), Inches(0.65))
        stat_card.fill.solid()
        stat_card.fill.fore_color.rgb = RGBColor(254, 243, 199)
        stat_card.line.color.rgb = RGBColor(245, 158, 11)
        stat_card.line.width = Pt(0.75)
        strip_shape_shadows(stat_card)

        tf_sc = stat_card.text_frame
        tf_sc.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_sc.margin_left = tf_sc.margin_right = Inches(0.15)
        p_sc = tf_sc.paragraphs[0]
        p_sc.text = f"{hero_stat}  "
        p_sc.font.name = theme.font_family_header
        p_sc.font.size = Pt(17)
        p_sc.font.bold = True
        p_sc.font.color.rgb = RGBColor(180, 83, 9)

        if constraints_card.get("hero_stat_label"):
            r_sc = p_sc.add_run()
            r_sc.text = str(constraints_card.get("hero_stat_label"))
            r_sc.font.size = Pt(9.5)
            r_sc.font.bold = True
            r_sc.font.color.rgb = theme.get_rgb("primary")
        hero_offset_y = 0.77

    # Bullets
    bullets_y = bottom_top + Inches(0.78 + hero_offset_y)
    bullets_h = Inches(1.45 if hero_stat else 2.10)
    tb_b = slide.shapes.add_textbox(right_x + Inches(0.25), bullets_y, right_w - Inches(0.50), bullets_h)
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0

    c_bullets = constraints_card.get("bullets") or []
    for b_i, b_item in enumerate(c_bullets):
        _add_bullet_paragraph(
            tf_b,
            b_item,
            theme.font_family,
            font_size_pt=9.0,
            font_color=theme.get_rgb("secondary"),
            space_before_pt=6.0 if b_i > 0 else 0.0,
        )

    # Takeaway Container
    takeaway_text = constraints_card.get("takeaway")
    if takeaway_text:
        tb_rtake = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x + Inches(0.25), bottom_top + bottom_h - Inches(0.68), right_w - Inches(0.50), Inches(0.58))
        tb_rtake.fill.solid()
        tb_rtake.fill.fore_color.rgb = RGBColor(241, 245, 249)
        tb_rtake.line.color.rgb = RGBColor(203, 213, 225)
        tb_rtake.line.width = Pt(0.75)
        strip_shape_shadows(tb_rtake)
        tf_rt = tb_rtake.text_frame
        tf_rt.word_wrap = True
        tf_rt.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_rt.margin_left = tf_rt.margin_right = Inches(0.12)
        p_rt = tf_rt.paragraphs[0]
        p_rt.text = str(takeaway_text)
        p_rt.font.name = theme.font_family_header
        p_rt.font.size = Pt(8.5)
        p_rt.font.bold = True
        p_rt.font.color.rgb = RGBColor(30, 41, 59)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 16. CRISP-DM Stage Gate & Data Preparation Flow Slide Archetype
# ============================================================================

def build_crisp_dm_gate_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "CRISP-DM LIFECYCLE & UC-1 DATA PREPARATION",
    action_title: str = "Data Preparation Is the Active Gate Deciding Machine Learning Feasibility",
    subtitle: Optional[str] = "Phases 1 & 2 complete; Phase 3 holds the operational line before any model training begins.",
    crisp_phases: Optional[List[Dict[str, Any]]] = None,
    prep_cards: Optional[List[Dict[str, Any]]] = None,
    takeaway: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an executive presentation slide featuring:
    - Top CRISP-DM 6-Stage Process Bar (highlighting Data Preparation as the active gate)
    - Bottom 4 Data Preparation Cards (Cohort, Label, Feature Store, Leakage Gate)
    - Bottom Takeaway Bar asserting the governance invariant
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    left_x = Inches(0.80)
    total_w = Inches(11.733)

    # 1. Top CRISP-DM 6-Stage Process Stepper Rail
    if crisp_phases is None:
        crisp_phases = [
            {"num": "01", "name": "Business Understanding", "status": "DONE", "color": "emerald"},
            {"num": "02", "name": "Data Understanding", "status": "DONE", "color": "emerald"},
            {"num": "03", "name": "Data Preparation", "status": "ACTIVE PHASE", "color": "amber", "highlight": True},
            {"num": "04", "name": "Modeling", "status": "PENDING", "color": "muted"},
            {"num": "05", "name": "Evaluation", "status": "PLANNED", "color": "muted"},
            {"num": "06", "name": "Deployment", "status": "PLANNED", "color": "muted"},
        ]

    n_phases = len(crisp_phases)
    active_idx = 2
    for p_i, p_obj in enumerate(crisp_phases):
        if p_obj.get("highlight", False) or "ACTIVE" in p_obj.get("status", "").upper():
            active_idx = p_i
            break

    # Calculate horizontal node positions
    phase_slot_w = total_w / n_phases
    node_xs = [left_x + i * phase_slot_w + phase_slot_w / 2 for i in range(n_phases)]

    rail_y = Inches(1.92)
    rail_h = Inches(0.04)

    # Base continuous muted track (across all stages)
    base_track = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        node_xs[0],
        rail_y - rail_h / 2,
        node_xs[-1] - node_xs[0],
        rail_h,
    )
    base_track.fill.solid()
    base_track.fill.fore_color.rgb = RGBColor(226, 232, 240)  # Slate-200
    base_track.line.fill.background()
    strip_shape_shadows(base_track)

    # Completed active track line (from start up to active node)
    if active_idx > 0:
        active_track = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            node_xs[0],
            rail_y - Inches(0.025),
            node_xs[active_idx] - node_xs[0],
            Inches(0.05),
        )
        active_track.fill.solid()
        active_track.fill.fore_color.rgb = theme.get_rgb("accent")  # Metrodata Blue #0284C7
        active_track.line.fill.background()
        strip_shape_shadows(active_track)

    for idx, p in enumerate(crisp_phases):
        cx = node_xs[idx]
        is_hl = (idx == active_idx)
        is_done = (idx < active_idx)

        # Floating Location Pin Badge for the Active Phase
        if is_hl:
            pin_w = Inches(1.85)
            pin_h = Inches(0.22)
            pin_x = cx - pin_w / 2
            pin_y = rail_y - Inches(0.44)

            pin_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, pin_x, pin_y, pin_w, pin_h)
            pin_badge.fill.solid()
            pin_badge.fill.fore_color.rgb = RGBColor(217, 119, 6)  # Calibrated Amber #D97706
            pin_badge.line.fill.background()
            strip_shape_shadows(pin_badge)

            pin_tf = pin_badge.text_frame
            pin_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            pin_tf.word_wrap = False
            pin_tf.margin_left = pin_tf.margin_right = pin_tf.margin_top = pin_tf.margin_bottom = 0
            p_pin = pin_tf.paragraphs[0]
            p_pin.text = "[ ACTIVE SPRINT ]"
            p_pin.font.name = theme.font_family_header
            p_pin.font.size = Pt(8.0)
            p_pin.font.bold = True
            p_pin.alignment = PP_ALIGN.CENTER
            p_pin.font.color.rgb = RGBColor(255, 255, 255)

        # Milestone Node Shapes
        if is_done:
            # Completed node: filled circle with phase number
            n_r = Inches(0.14)
            node = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - n_r, rail_y - n_r, n_r * 2, n_r * 2)
            node.fill.solid()
            node.fill.fore_color.rgb = theme.get_rgb("accent")
            node.line.fill.background()
            strip_shape_shadows(node)

            ntf = node.text_frame
            ntf.vertical_anchor = MSO_ANCHOR.MIDDLE
            ntf.word_wrap = False
            ntf.margin_left = ntf.margin_right = ntf.margin_top = ntf.margin_bottom = 0
            np = ntf.paragraphs[0]
            np.text = p.get("num", f"{idx+1:02d}")
            np.font.name = theme.font_family_header
            np.font.size = Pt(7.5)
            np.font.bold = True
            np.font.color.rgb = RGBColor(255, 255, 255)
            np.alignment = PP_ALIGN.CENTER
        elif is_hl:
            # Active node: concentric pulse hub (outer halo + inner dot)
            halo_r = Inches(0.19)
            halo = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - halo_r, rail_y - halo_r, halo_r * 2, halo_r * 2)
            halo.fill.solid()
            halo.fill.fore_color.rgb = RGBColor(254, 243, 199)  # Soft Amber tint
            halo.line.color.rgb = RGBColor(217, 119, 6)
            halo.line.width = Pt(1.5)
            strip_shape_shadows(halo)

            core_r = Inches(0.11)
            core = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - core_r, rail_y - core_r, core_r * 2, core_r * 2)
            core.fill.solid()
            core.fill.fore_color.rgb = RGBColor(217, 119, 6)
            core.line.fill.background()
            strip_shape_shadows(core)

            ctf = core.text_frame
            ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
            ctf.word_wrap = False
            ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0
            cp = ctf.paragraphs[0]
            cp.text = p.get("num", f"{idx+1:02d}")
            cp.font.name = theme.font_family_header
            cp.font.size = Pt(7.5)
            cp.font.bold = True
            cp.font.color.rgb = RGBColor(255, 255, 255)
            cp.alignment = PP_ALIGN.CENTER
        else:
            # Planned future node: hollow circle with subtle border
            n_r = Inches(0.12)
            node = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - n_r, rail_y - n_r, n_r * 2, n_r * 2)
            node.fill.solid()
            node.fill.fore_color.rgb = RGBColor(255, 255, 255)
            node.line.color.rgb = RGBColor(148, 163, 184)  # Slate-400
            node.line.width = Pt(1.2)
            strip_shape_shadows(node)

            ntf = node.text_frame
            ntf.vertical_anchor = MSO_ANCHOR.MIDDLE
            ntf.word_wrap = False
            ntf.margin_left = ntf.margin_right = ntf.margin_top = ntf.margin_bottom = 0
            np = ntf.paragraphs[0]
            np.text = p.get("num", f"{idx+1:02d}")
            np.font.name = theme.font_family_header
            np.font.size = Pt(7.0)
            np.font.bold = True
            np.font.color.rgb = RGBColor(148, 163, 184)
            np.alignment = PP_ALIGN.CENTER

        # Labels below the node (clean gap below outer halo)
        label_w = phase_slot_w - Inches(0.10)
        label_y = rail_y + Inches(0.24)
        label_tb = slide.shapes.add_textbox(cx - label_w / 2, label_y, label_w, Inches(0.44))
        label_tf = label_tb.text_frame
        label_tf.word_wrap = True
        label_tf.margin_left = label_tf.margin_right = label_tf.margin_top = label_tf.margin_bottom = 0

        lp1 = label_tf.paragraphs[0]
        lp1.text = f"{p.get('num', f'{idx+1:02d}')}. {p.get('name', '')}"
        lp1.font.name = theme.font_family_header
        lp1.font.size = Pt(8.5)
        lp1.font.bold = True
        lp1.font.color.rgb = RGBColor(180, 83, 9) if is_hl else (theme.get_rgb("primary") if is_done else RGBColor(100, 116, 139))
        lp1.alignment = PP_ALIGN.CENTER

        lp2 = label_tf.add_paragraph()
        st_tag = p.get("status", "PLANNED")
        lp2.text = f"[{st_tag}]"
        lp2.font.name = theme.font_family_header
        lp2.font.size = Pt(7.2)
        lp2.font.bold = True
        lp2.font.color.rgb = RGBColor(217, 119, 6) if is_hl else (theme.get_rgb("accent") if is_done else RGBColor(148, 163, 184))
        lp2.alignment = PP_ALIGN.CENTER
        lp2.space_before = Pt(2)

    # Focus Bracket / Transition Banner into Phase 03 Workstream
    section_y = Inches(2.72)
    section_h = Inches(0.24)
    sec_tb = slide.shapes.add_textbox(left_x, section_y, total_w, section_h)
    sec_tf = sec_tb.text_frame
    sec_tf.word_wrap = False
    sec_tf.margin_left = sec_tf.margin_right = sec_tf.margin_top = sec_tf.margin_bottom = 0
    sp1 = sec_tf.paragraphs[0]
    sp1.text = "PHASE 03 DATA PREPARATION WORKSTREAM  |  FOUR SEQUENTIAL PRE-MODELING VERIFICATIONS"
    sp1.font.name = theme.font_family_header
    sp1.font.size = Pt(8.5)
    sp1.font.bold = True
    sp1.font.color.rgb = RGBColor(71, 85, 105)  # Slate-600

    # 2. Bottom 4 Data Preparation Flow Cards
    if prep_cards is None:
        prep_cards = [
            {
                "title": "Cohort Extraction",
                "subtitle": "Verified patient encounters",
                "metric": "11.9K",
                "metric_label": "VERIFIED COHORT",
                "accent_key": "primary",
                "bullets": [
                    "Clinical Spine: July 2024–Sept 2026 verified appointments.",
                    "Cleaned Grain: Eliminates dummy test rows and admin accounts.",
                ],
            },
            {
                "title": "Target Label Resolution",
                "subtitle": "Silent no-show proxy resolution",
                "metric": "21.0%",
                "metric_label": "NO-SHOW BASELINE",
                "accent_key": "accent",
                "bullets": [
                    "Operational Proxy: REALISASI = 0 indicates patient absence.",
                    "Separated Cancels: Distinguishes silent no-shows from notified cancels.",
                ],
            },
            {
                "title": "Feature Store Assembly",
                "subtitle": "Multi-domain predictive signals",
                "metric": "4 Tiers",
                "metric_label": "SIGNAL DOMAINS",
                "accent_key": "primary",
                "bullets": [
                    "Clinical Lead Time: Booking horizon, branch, and specialty.",
                    "Billing History: Transaction count, invoice volume, and cadence.",
                ],
            },
            {
                "title": "Leakage Audit Gate",
                "subtitle": "Zero-leakage threshold",
                "metric": "0 Rows",
                "metric_label": "LEAKAGE TOLERANCE",
                "accent_key": "danger",
                "bullets": [
                    "Temporal Cutoff: Zero consultation signals past appointment.",
                    "Zero-Tolerance: Pipeline aborts if leakage count exceeds zero.",
                ],
            },
        ]

    cards_top = Inches(3.02)
    cards_h = Inches(3.38) if takeaway else Inches(3.96)
    n_cards = len(prep_cards)
    card_gap = Inches(0.22)
    card_w = (total_w - card_gap * (n_cards - 1)) / n_cards

    for c_i, c in enumerate(prep_cards):
        cx = left_x + c_i * (card_w + card_gap)
        acc_k = c.get("accent_key", "primary")
        acc_rgb = theme.get_rgb(acc_k)
        is_danger = (acc_k == "danger")

        # Directional Chevron Bridge between cards (High-Contrast Metrodata Accent)
        if c_i > 0:
            chv_w = Inches(0.13)
            chv_h = Inches(0.24)
            chv_x = cx - card_gap / 2 - chv_w / 2
            chv_y = cards_top + Inches(1.15)

            arrow = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, chv_x, chv_y, chv_w, chv_h)
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = theme.get_rgb("accent")  # Metrodata Blue #0284C7 for sharp contrast
            arrow.line.fill.background()
            strip_shape_shadows(arrow)

        # Card container
        card_shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cards_top, card_w, cards_h)
        card_shp.fill.solid()
        card_shp.fill.fore_color.rgb = RGBColor(254, 242, 242) if is_danger else theme.get_rgb("surface")
        card_shp.line.color.rgb = RGBColor(220, 38, 38) if is_danger else theme.get_rgb("border")
        card_shp.line.width = Pt(1.2) if is_danger else Pt(0.75)
        strip_shape_shadows(card_shp)

        # Top Accent Stripe
        stripe_c = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cards_top, card_w, Inches(0.06))
        stripe_c.fill.solid()
        stripe_c.fill.fore_color.rgb = acc_rgb
        stripe_c.line.fill.background()
        strip_shape_shadows(stripe_c)

        # Step Sequence Eyebrow inside Card
        eyebrow_tb = slide.shapes.add_textbox(cx + Inches(0.14), cards_top + Inches(0.10), card_w - Inches(0.28), Inches(0.18))
        etf = eyebrow_tb.text_frame
        etf.word_wrap = False
        etf.margin_left = etf.margin_right = etf.margin_top = etf.margin_bottom = 0
        ep = etf.paragraphs[0]
        ep.text = f"STEP 0{c_i + 1} OF 04"
        ep.font.name = theme.font_family_header
        ep.font.size = Pt(7.5)
        ep.font.bold = True
        ep.font.color.rgb = acc_rgb

        # Title & Subtitle
        tb_t = slide.shapes.add_textbox(cx + Inches(0.14), cards_top + Inches(0.28), card_w - Inches(0.28), Inches(0.50))
        tf_t = tb_t.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
        pt1 = tf_t.paragraphs[0]
        pt1.text = str(c.get("title", ""))
        pt1.font.name = theme.font_family_header
        pt1.font.size = Pt(11.5)
        pt1.font.bold = True
        pt1.font.color.rgb = theme.get_rgb("primary")

        if c.get("subtitle"):
            pt2 = tf_t.add_paragraph()
            pt2.text = str(c.get("subtitle", ""))
            pt2.font.name = theme.font_family
            pt2.font.size = Pt(8.0)
            pt2.font.color.rgb = theme.get_rgb("secondary")
            pt2.space_before = Pt(1)

        # Hero Stat
        met_val = c.get("metric")
        if met_val:
            met_tb = slide.shapes.add_textbox(cx + Inches(0.14), cards_top + Inches(0.80), card_w - Inches(0.28), Inches(0.72))
            met_tf = met_tb.text_frame
            met_tf.word_wrap = True
            met_tf.margin_left = met_tf.margin_right = met_tf.margin_top = met_tf.margin_bottom = 0
            pm1 = met_tf.paragraphs[0]
            pm1.text = str(met_val)
            pm1.font.name = theme.font_family_header
            pm1.font.size = Pt(24.0)
            pm1.font.bold = True
            pm1.font.color.rgb = acc_rgb

            if c.get("metric_label"):
                pm2 = met_tf.add_paragraph()
                pm2.text = str(c.get("metric_label", "")).upper()
                pm2.font.name = theme.font_family_header
                pm2.font.size = Pt(7.5)
                pm2.font.bold = True
                pm2.font.color.rgb = theme.get_rgb("secondary")
                pm2.space_before = Pt(1)

            # Hairline Divider
            div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx + Inches(0.14), cards_top + Inches(1.56), card_w - Inches(0.28), Pt(0.75))
            div.fill.solid()
            div.fill.fore_color.rgb = theme.get_rgb("border")
            div.line.fill.background()
            strip_shape_shadows(div)

        # Bullets
        bullets_y = cards_top + Inches(1.68 if met_val else 0.85)
        bullets_h = cards_h - (bullets_y - cards_top) - Inches(0.08)
        tb_blt = slide.shapes.add_textbox(cx + Inches(0.14), bullets_y, card_w - Inches(0.28), bullets_h)
        tf_blt = tb_blt.text_frame
        tf_blt.word_wrap = True
        tf_blt.margin_left = tf_blt.margin_right = tf_blt.margin_top = tf_blt.margin_bottom = 0

        for b_idx, b_item in enumerate(c.get("bullets") or []):
            _add_bullet_paragraph(
                tf_blt,
                b_item,
                theme.font_family,
                font_size_pt=8.0,
                font_color=theme.get_rgb("secondary"),
                space_before_pt=3.5 if b_idx > 0 else 0.0,
            )

    # 3. Bottom Takeaway Bar
    if takeaway:
        add_takeaway_bar(slide, theme, takeaway, top_y=Inches(6.42), left_x=left_x, width=total_w, height=Inches(0.54))

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 17. Stacked Medallion Data Tiers Slide Archetype
# ============================================================================

def build_medallion_tiers_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "MEDALLION DATA TIER ELIGIBILITY ROSTER",
    action_title: str = "Silver Tables Provide Clean Feature Coverage; Bronze Requires Written Reason",
    subtitle: Optional[str] = "Three stacked medallion tiers classify approved training sources, conditional audit replay, and barred marts.",
    tiers: Optional[List[Dict[str, Any]]] = None,
    takeaway: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an executive presentation slide featuring:
    - 3 Stacked Horizontal Medallion Bands (Silver approved, Bronze conditional, Gold barred)
    - 3-column internal layout per band: Tier Badge/Metric | Table Breakdown | Governance Safeguard
    - Bottom Takeaway Bar asserting medallion data integrity rules
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    left_x = Inches(0.80)
    total_w = Inches(11.733)

    if tiers is None:
        tiers = [
            {
                "tier_name": "Silver Analytical Tables",
                "tier_badge": "SILVER: APPROVED STEP 1",
                "metric": "8.9M Rows",
                "metric_label": "APPROVED CORPUS",
                "color": "emerald",
                "tables": [
                    "FACT_PATIENT_APPOINTMENT (30,761 rows): Core booking cohort spine.",
                    "FACT_SOAP_PATIENT (193,694 rows): 95.8% clinical encounter join coverage.",
                    "FACT_TRANSACTION (8.68M rows): 99.9% billing cadence and payment history.",
                ],
                "excluded_note": "FACT_CHAT (126.5K) and CALL_CENTER (8.8K) excluded due to late 2025 start.",
            },
            {
                "tier_name": "Bronze Ingestion Tables",
                "tier_badge": "BRONZE: CONDITIONAL STEP 2",
                "metric": "266K Ver",
                "metric_label": "RAW AUDIT VERSIONS",
                "color": "amber",
                "tables": [
                    "TERAmedik Appointment Logs (19,327 live rows + 266,013 historical audit versions).",
                    "Holds reschedule timestamps and cancellation audit trail uncaptured in Silver snapshot.",
                ],
                "excluded_note": "Gated Ingestion: Requires formal DE rationale, written sign-off, and JSON parsing.",
            },
            {
                "tier_name": "Gold Reporting Marts",
                "tier_badge": "GOLD: STRICTLY FORBIDDEN [BARRED]",
                "metric": "0% Allowed",
                "metric_label": "PRE-AGGREGATED MARTS",
                "color": "danger",
                "tables": [
                    "Pre-aggregated BI clinic summary tables and executive dashboard reporting marts.",
                    "Direct Target Leakage: Monthly aggregates embed future outcome totals into past features.",
                ],
                "excluded_note": "Physical RBAC Lock: Target role denies SELECT on all Gold marts and schemas.",
            },
        ]

    band_top = Inches(1.80)
    band_gap = Inches(0.14)
    total_band_h = Inches(4.55) if takeaway else Inches(5.10)
    band_h = (total_band_h - band_gap * (len(tiers) - 1)) / len(tiers)

    for idx, t in enumerate(tiers):
        by = band_top + idx * (band_h + band_gap)
        col_key = t.get("color") or t.get("stripe_color") or t.get("accent_key") or "primary"
        stripe_rgb = theme.get_rgb(col_key) if hasattr(theme, "get_rgb") else RGBColor(2, 132, 199)

        # Outer band container: pure surface white, zero muddy green tint
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, by, total_w, band_h)
        band.fill.solid()
        band.fill.fore_color.rgb = theme.get_rgb("surface")
        if col_key == "danger":
            band.line.color.rgb = RGBColor(252, 165, 165)
        elif col_key in ("amber", "warning"):
            band.line.color.rgb = RGBColor(252, 211, 77)
        elif col_key in ("emerald", "success", "green"):
            band.line.color.rgb = RGBColor(110, 231, 183)
        else:
            band.line.color.rgb = RGBColor(203, 213, 225)
        band.line.width = Pt(1.0)
        strip_shape_shadows(band)

        # Left focus indicator bar
        left_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, by, Pt(5.0), band_h)
        left_stripe.fill.solid()
        left_stripe.fill.fore_color.rgb = stripe_rgb
        left_stripe.line.fill.background()
        strip_shape_shadows(left_stripe)

        # Column 1: Tier Identity & Metric (w = 2.35")
        col1_w = Inches(2.35)
        tb_c1 = slide.shapes.add_textbox(left_x + Inches(0.20), by + Inches(0.10), col1_w, band_h - Inches(0.20))
        tf_c1 = tb_c1.text_frame
        tf_c1.word_wrap = True
        tf_c1.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_c1.margin_left = tf_c1.margin_right = tf_c1.margin_top = tf_c1.margin_bottom = 0

        p1 = tf_c1.paragraphs[0]
        p1.text = str(t.get("tier_badge", "")).upper()
        p1.font.name = theme.font_family_header
        p1.font.size = Pt(9.0)
        p1.font.bold = True
        p1.font.color.rgb = stripe_rgb

        p2 = tf_c1.add_paragraph()
        p2.text = str(t.get("metric", ""))
        p2.font.name = theme.font_family_header
        p2.font.size = Pt(26.0)
        p2.font.bold = True
        p2.font.color.rgb = stripe_rgb
        p2.space_before = Pt(2)

        p3 = tf_c1.add_paragraph()
        p3.text = str(t.get("metric_label", "")).upper()
        p3.font.name = theme.font_family_header
        p3.font.size = Pt(8.5)
        p3.font.bold = True
        p3.font.color.rgb = theme.get_rgb("primary")

        # Vertical Divider 1
        div1_x = left_x + Inches(2.65)
        div1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, div1_x, by + Inches(0.12), Pt(0.75), band_h - Inches(0.24))
        div1.fill.solid()
        div1.fill.fore_color.rgb = RGBColor(226, 232, 240)
        div1.line.fill.background()
        strip_shape_shadows(div1)

        # Column 2: Approved / Source Tables Breakdown (w = 5.50", expanded & balanced typography)
        col2_x = div1_x + Inches(0.20)
        col2_w = Inches(5.50)
        tb_c2 = slide.shapes.add_textbox(col2_x, by + Inches(0.10), col2_w, band_h - Inches(0.20))
        tf_c2 = tb_c2.text_frame
        tf_c2.word_wrap = True
        tf_c2.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_c2.margin_left = tf_c2.margin_right = tf_c2.margin_top = tf_c2.margin_bottom = 0

        n_tables = len(t.get("tables") or [])
        tbl_font_pt = 10.0 if n_tables >= 3 else 10.5
        tbl_spacing_pt = 3.5 if n_tables >= 3 else 5.0

        for r_idx, tbl_line in enumerate(t.get("tables") or []):
            _add_bullet_paragraph(
                tf_c2,
                tbl_line,
                theme.font_family,
                font_size_pt=tbl_font_pt,
                font_color=theme.get_rgb("secondary"),
                space_before_pt=tbl_spacing_pt if r_idx > 0 else 0.0,
            )

        # Vertical Divider 2
        div2_x = col2_x + col2_w + Inches(0.18)
        div2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, div2_x, by + Inches(0.12), Pt(0.75), band_h - Inches(0.24))
        div2.fill.solid()
        div2.fill.fore_color.rgb = RGBColor(226, 232, 240)
        div2.line.fill.background()
        strip_shape_shadows(div2)

        # Column 3: Governance Safeguard & Rationale (w = 2.80", balanced typography)
        col3_x = div2_x + Inches(0.20)
        col3_w = (left_x + total_w) - col3_x - Inches(0.15)
        tb_c3 = slide.shapes.add_textbox(col3_x, by + Inches(0.10), col3_w, band_h - Inches(0.20))
        tf_c3 = tb_c3.text_frame
        tf_c3.word_wrap = True
        tf_c3.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_c3.margin_left = tf_c3.margin_right = tf_c3.margin_top = tf_c3.margin_bottom = 0

        p_gov = tf_c3.paragraphs[0]
        p_gov.text = "GOVERNANCE SAFEGUARD"
        p_gov.font.name = theme.font_family_header
        p_gov.font.size = Pt(8.5)
        p_gov.font.bold = True
        p_gov.font.color.rgb = theme.get_rgb("primary")

        p_gov_sub = tf_c3.add_paragraph()
        p_gov_sub.text = str(t.get("excluded_note", ""))
        p_gov_sub.font.name = theme.font_family
        p_gov_sub.font.size = Pt(9.5)
        p_gov_sub.font.color.rgb = RGBColor(51, 65, 85)
        p_gov_sub.space_before = Pt(3.5)

    # 3. Bottom Takeaway Bar
    if takeaway:
        add_takeaway_bar(slide, theme, takeaway, top_y=Inches(6.42), left_x=left_x, width=total_w, height=Inches(0.54))

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide

