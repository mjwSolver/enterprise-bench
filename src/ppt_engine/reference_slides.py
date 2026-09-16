"""
Enterprise Reference Slides Subsystem
======================================
Permanent, consulting-grade reference slides providing standardized engagement
governance and official Snowflake solution blueprints:

  1. Project Organization Structure (Slide 33 Reference)
     - Tree-like hierarchical organizational chart with native vector connector lines.
     - Dual-Pillar Joint Governance: Joint Steering Committee -> PMO Level ->
       4 Execution Pods (Client BPO, Client IT, Metrodata Engineering, Metrodata Analytics).
     - Fully parameterized using '[CLIENT_COMPANY_NAME]' slug for zero PII exposure.

  2. Change Request Procedure (Slide 35 Reference)
     - Procedural workflow pipeline with directional transition indicators.
     - Bi-level Decision Gate (PMO Fast-Track vs. Steering Committee Escalation)
       with clear branch pathways and contractual deliverable linkages.

  3. Snowflake Platform Architecture (Slide 17 Reference)
     - Official high-resolution Snowflake Platform Architecture blueprint
       curated from Snowflake Data Cloud assets.

  4. Snowflake End-to-End Solution Architecture (Slide 18 Reference)
     - Official Snowflake Data Warehouse & Analytics solution flow
       curated from Snowflake presales engineering assets.

Strictly enforces:
  - Zero overlapping top lines on rounded cards (MSO_SHAPE.RECTANGLE on all striped containers).
  - Unified title and subtitle frames (single text frame, space_before = Pt(10)).
  - Clean typographic hierarchy and 60-30-10 palette distribution.
  - Native DrawingML hanging indents on bullet items.
  - Synchronized bottom pagination and slide footer notices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from src.ppt_engine.consulting_archetypes import (
    EquityEntityNode,
    EquityTreeData,
    add_card,
    add_card_with_top_stripe,
    add_slide_footer,
    add_slide_header,
    add_slide_with_background,
    build_cover_slide,
    build_equity_corporate_tree_slide,
    build_hero_cover_slide,
    create_presentation,
)
from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb

logger = logging.getLogger(__name__)

# Official Asset Paths
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "images"
OFFICIAL_SNOWFLAKE_PLATFORM_IMG = ASSETS_DIR / "snowflake_platform_architecture_official.png"
OFFICIAL_SNOWFLAKE_FLOW_IMG = ASSETS_DIR / "snowflake_data_warehouse_flow_official.png"


# ============================================================================
# Helper Utilities
# ============================================================================

def _add_status_pill(
    slide: Any,
    theme: Theme,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    status: str,
    font_size_pt: float = 8.5,
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
        elif override_color_key == "accent":
            bg_key, text_key = ("badge_blue_fill", "badge_blue_text")
        else:
            bg_key, text_key = ("surface_muted", "primary")
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


def _add_bullet_paragraph(
    tf: Any,
    text: str,
    font_name: str,
    font_size_pt: float = 10.0,
    font_color: Optional[RGBColor] = None,
    space_before_pt: float = 5.0,
    bullet_char: str = "•",
) -> Any:
    """Appends a bullet paragraph with DrawingML hanging indent."""
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

    buChar = OxmlElement("a:buChar")
    buChar.set("char", bullet_char)
    pPr.append(buChar)
    return p


def _draw_h_line(
    slide: Any,
    x1: Inches,
    x2: Inches,
    y: Inches,
    color: RGBColor,
    width_pt: float = 1.5,
) -> Any:
    """Draws a crisp horizontal connector bar that renders identically in native PPT and headless PIL."""
    left = min(x1, x2)
    w = abs(x2 - x1)
    h = Pt(width_pt)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, y, w, h)
    line.shadow.inherit = False
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line


def _draw_v_line(
    slide: Any,
    x: Inches,
    y1: Inches,
    y2: Inches,
    color: RGBColor,
    width_pt: float = 1.5,
) -> Any:
    """Draws a crisp vertical connector bar that renders identically in native PPT and headless PIL."""
    top = min(y1, y2)
    h = abs(y2 - y1)
    w = Pt(width_pt)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, top, w, h)
    line.shadow.inherit = False
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line


def _fit_image_in_box(
    img_path: Union[str, Path],
    box_left: Inches,
    box_top: Inches,
    box_width: Inches,
    box_height: Inches,
) -> Tuple[Inches, Inches, Inches, Inches]:
    """
    Calculates coordinates (left, top, width, height) to fit an image inside
    a bounding box while strictly preserving its natural aspect ratio and centering it.
    """
    from PIL import Image

    try:
        with Image.open(img_path) as im:
            orig_w, orig_h = im.size
        img_ratio = orig_w / float(orig_h)

        bw_in = box_width / 914400.0
        bh_in = box_height / 914400.0
        bl_in = box_left / 914400.0
        bt_in = box_top / 914400.0

        box_ratio = bw_in / bh_in
        if img_ratio > box_ratio:
            final_w_in = bw_in
            final_h_in = bw_in / img_ratio
        else:
            final_h_in = bh_in
            final_w_in = bh_in * img_ratio

        final_l_in = bl_in + (bw_in - final_w_in) / 2.0
        final_t_in = bt_in + (bh_in - final_h_in) / 2.0
        return Inches(final_l_in), Inches(final_t_in), Inches(final_w_in), Inches(final_h_in)
    except Exception as exc:
        logger.warning(f"Could not calculate aspect ratio for {img_path}: {exc}")
        return box_left, box_top, box_width, box_height


# ============================================================================
# 1. Slide 33: Project Organization Structure Slide (Tree-Like Hierarchy)
# ============================================================================

def build_governance_org_structure_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "PROJECT GOVERNANCE | ORGANIZATIONAL STRUCTURE",
    action_title: str = "Joint Dual-Pillar Governance Matrix Establishes Clear Escalation & Delivery Ownership",
    subtitle: Optional[str] = "Hierarchical project structure connects executive steering committees, PMO leads, and specialized execution pods.",
    client_name: str = "[CLIENT_COMPANY_NAME]",
    vendor_name: str = "PT Metrodata Electronics Tbk",
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders permanent reference Slide 33 as a true tree-like hierarchical org chart:
      - Top Node: Joint Steering Committee (Executive Sponsorship)
      - Connecting Trunks & Distribution Bus
      - Mid Nodes: Client PMO <-> Vendor PMO
      - Sub-Distribution Bus & Connecting Drop Lines
      - Base Nodes: 4 Functional Execution Pods
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    c_primary = theme.get_rgb("primary")
    c_secondary = theme.get_rgb("secondary")
    c_muted = theme.get_rgb("muted")
    c_accent = theme.get_rgb("accent")
    c_accent_sec = theme.get_rgb("accent_secondary")
    c_surface = theme.get_rgb("surface")
    c_border = theme.get_rgb("border")
    c_line = theme.get_rgb("accent")

    # ------------------------------------------------------------------------
    # TIER 1: Joint Steering Committee (Centered Top Node)
    # ------------------------------------------------------------------------
    sc_left = Inches(1.80)
    sc_top = Inches(1.80)
    sc_width = Inches(9.733)
    sc_height = Inches(1.15)

    add_card_with_top_stripe(
        slide, theme, sc_left, sc_top, sc_width, sc_height,
        accent_rgb=c_accent,
        bg_color=c_surface,
    )
    _add_status_pill(slide, theme, sc_left + sc_width - Inches(2.20), sc_top + Inches(0.10), Inches(2.05), Inches(0.24), "EXECUTIVE GOVERNANCE", font_size_pt=8.0, override_color_key="accent")

    tb_sc = slide.shapes.add_textbox(sc_left + Inches(0.20), sc_top + Inches(0.10), sc_width - Inches(2.40), sc_height - Inches(0.15))
    tf_sc = tb_sc.text_frame
    tf_sc.word_wrap = True
    tf_sc.margin_left = tf_sc.margin_right = tf_sc.margin_top = tf_sc.margin_bottom = 0

    p_sc_header = tf_sc.paragraphs[0]
    p_sc_header.text = "TIER 1: JOINT STEERING COMMITTEE (PROJECT SPONSORSHIP)"
    p_sc_header.font.name = theme.font_family_header
    p_sc_header.font.size = Pt(10.5)
    p_sc_header.font.bold = True
    p_sc_header.font.color.rgb = c_accent

    p_sc1 = tf_sc.add_paragraph()
    p_sc1.space_before = Pt(2)
    r1 = p_sc1.add_run()
    r1.text = f"{client_name} Sponsors: "
    r1.font.name = theme.font_family
    r1.font.size = Pt(9.0)
    r1.font.bold = True
    r1.font.color.rgb = c_primary
    r1_sub = p_sc1.add_run()
    r1_sub.text = "C-Level Leadership (Strategic vision, budget authorization, stage-gate sign-offs)"
    r1_sub.font.name = theme.font_family
    r1_sub.font.size = Pt(8.5)
    r1_sub.font.color.rgb = c_secondary

    p_sc2 = tf_sc.add_paragraph()
    p_sc2.space_before = Pt(1)
    r2 = p_sc2.add_run()
    r2.text = f"{vendor_name} Leadership: "
    r2.font.name = theme.font_family
    r2.font.size = Pt(9.0)
    r2.font.bold = True
    r2.font.color.rgb = c_primary
    r2_sub = p_sc2.add_run()
    r2_sub.text = "Consulting Practice Director & Partner (Delivery assurance, executive SLA oversight)"
    r2_sub.font.name = theme.font_family
    r2_sub.font.size = Pt(8.5)
    r2_sub.font.color.rgb = c_secondary

    # ------------------------------------------------------------------------
    # HIERARCHY TREE CONNECTOR LINES: TIER 1 -> TIER 2
    # ------------------------------------------------------------------------
    # Vertical trunk dropping from Steering Committee bottom center
    center_x = Inches(6.666)
    bus_y1 = Inches(3.18)
    _draw_v_line(slide, center_x, sc_top + sc_height, bus_y1, c_line, width_pt=1.5)

    # Horizontal bus line across Tier 2
    pm1_center_x = Inches(3.66)
    pm2_center_x = Inches(9.67)
    _draw_h_line(slide, pm1_center_x, pm2_center_x, bus_y1, c_line, width_pt=1.5)

    # Vertical drops into Tier 2 cards
    pmo_top = Inches(3.40)
    _draw_v_line(slide, pm1_center_x, bus_y1, pmo_top, c_line, width_pt=1.5)
    _draw_v_line(slide, pm2_center_x, bus_y1, pmo_top, c_line, width_pt=1.5)

    # ------------------------------------------------------------------------
    # TIER 2: Project Management Office (PMO) - Two Columns
    # ------------------------------------------------------------------------
    pmo_width = Inches(5.72)
    pmo_height = Inches(1.40)

    # Client PM Card
    pm1_left = Inches(0.80)
    add_card_with_top_stripe(
        slide, theme, pm1_left, pmo_top, pmo_width, pmo_height,
        accent_rgb=c_accent_sec,
        bg_color=c_surface,
    )
    _add_status_pill(slide, theme, pm1_left + pmo_width - Inches(1.35), pmo_top + Inches(0.10), Inches(1.15), Inches(0.22), "CLIENT PMO", font_size_pt=8.0, override_color_key="danger")

    tb_pm1 = slide.shapes.add_textbox(pm1_left + Inches(0.20), pmo_top + Inches(0.10), pmo_width - Inches(1.60), pmo_height - Inches(0.18))
    tf_pm1 = tb_pm1.text_frame
    tf_pm1.word_wrap = True
    tf_pm1.margin_left = tf_pm1.margin_right = tf_pm1.margin_top = tf_pm1.margin_bottom = 0

    p_pm1_h = tf_pm1.paragraphs[0]
    p_pm1_h.text = f"{client_name} Project Manager"
    p_pm1_h.font.name = theme.font_family_header
    p_pm1_h.font.size = Pt(11.0)
    p_pm1_h.font.bold = True
    p_pm1_h.font.color.rgb = c_primary

    _add_bullet_paragraph(tf_pm1, "Facilitates business access, requirements sign-off, and UAT scheduling.", theme.font_family, font_size_pt=8.5, font_color=c_secondary, space_before_pt=3)
    _add_bullet_paragraph(tf_pm1, "Manages internal stakeholder communications and stage-gate readiness.", theme.font_family, font_size_pt=8.5, font_color=c_secondary, space_before_pt=2)
    _add_bullet_paragraph(tf_pm1, "Primary escalation point for cross-department data governance approvals.", theme.font_family, font_size_pt=8.5, font_color=c_secondary, space_before_pt=2)

    # Metrodata PM Card
    pm2_left = Inches(6.813)
    add_card_with_top_stripe(
        slide, theme, pm2_left, pmo_top, pmo_width, pmo_height,
        accent_rgb=c_accent,
        bg_color=c_surface,
    )
    _add_status_pill(slide, theme, pm2_left + pmo_width - Inches(1.50), pmo_top + Inches(0.10), Inches(1.30), Inches(0.22), "VENDOR PMO", font_size_pt=8.0, override_color_key="accent")

    tb_pm2 = slide.shapes.add_textbox(pm2_left + Inches(0.20), pmo_top + Inches(0.10), pmo_width - Inches(1.75), pmo_height - Inches(0.18))
    tf_pm2 = tb_pm2.text_frame
    tf_pm2.word_wrap = True
    tf_pm2.margin_left = tf_pm2.margin_right = tf_pm2.margin_top = tf_pm2.margin_bottom = 0

    p_pm2_h = tf_pm2.paragraphs[0]
    p_pm2_h.text = f"{vendor_name} Project Manager & Lead"
    p_pm2_h.font.name = theme.font_family_header
    p_pm2_h.font.size = Pt(11.0)
    p_pm2_h.font.bold = True
    p_pm2_h.font.color.rgb = c_primary

    _add_bullet_paragraph(tf_pm2, "Drives daily delivery cadence, sprint backlogs, and milestone tracking.", theme.font_family, font_size_pt=8.5, font_color=c_secondary, space_before_pt=3)
    _add_bullet_paragraph(tf_pm2, "Maintains RAID logs, weekly progress S-curves, and formal Change Requests.", theme.font_family, font_size_pt=8.5, font_color=c_secondary, space_before_pt=2)
    _add_bullet_paragraph(tf_pm2, "Coordinates specialized Snowflake architects, engineers, and data scientists.", theme.font_family, font_size_pt=8.5, font_color=c_secondary, space_before_pt=2)

    # ------------------------------------------------------------------------
    # HIERARCHY TREE CONNECTOR LINES: TIER 2 -> TIER 3
    # ------------------------------------------------------------------------
    bus_y2 = Inches(4.98)
    pod_top = Inches(5.15)
    pod_width = Inches(2.78)
    pod_gap = Inches(0.20)

    # Left Tree: Client PM -> Pod 0 (BPO) and Pod 1 (IT) [Client Red Theme]
    p0_cx = Inches(0.80) + pod_width / 2.0
    p1_cx = Inches(0.80) + pod_width + pod_gap + pod_width / 2.0
    _draw_v_line(slide, pm1_center_x, pmo_top + pmo_height, bus_y2, c_accent_sec, width_pt=1.5)
    _draw_h_line(slide, p0_cx, p1_cx, bus_y2, c_accent_sec, width_pt=1.5)
    _draw_v_line(slide, p0_cx, bus_y2, pod_top, c_accent_sec, width_pt=1.5)
    _draw_v_line(slide, p1_cx, bus_y2, pod_top, c_accent_sec, width_pt=1.5)

    # Right Tree: Vendor PM -> Pod 2 (Snowflake Eng) and Pod 3 (Analytics/AI) [Vendor Blue Theme]
    p2_cx = Inches(0.80) + 2 * (pod_width + pod_gap) + pod_width / 2.0
    p3_cx = Inches(0.80) + 3 * (pod_width + pod_gap) + pod_width / 2.0
    _draw_v_line(slide, pm2_center_x, pmo_top + pmo_height, bus_y2, c_line, width_pt=1.5)
    _draw_h_line(slide, p2_cx, p3_cx, bus_y2, c_line, width_pt=1.5)
    _draw_v_line(slide, p2_cx, bus_y2, pod_top, c_line, width_pt=1.5)
    _draw_v_line(slide, p3_cx, bus_y2, pod_top, c_line, width_pt=1.5)

    # ------------------------------------------------------------------------
    # TIER 3: Execution Pods (4 Nodes across bottom)
    # ------------------------------------------------------------------------
    pod_height = Inches(1.72)

    pods_data = [
        {
            "title": "Business Process Owners",
            "org": client_name,
            "badge": "CLIENT BPO",
            "badge_color": "danger",
            "stripe_color": c_accent_sec,
            "bullets": [
                "Validates KPI formulas and logic.",
                "Provides baseline data inputs.",
                "Executes functional UAT test cases.",
                "Signs off user acceptance results.",
            ],
        },
        {
            "title": "IT & Infrastructure Lead",
            "org": client_name,
            "badge": "CLIENT IT",
            "badge_color": "danger",
            "stripe_color": c_accent_sec,
            "bullets": [
                "Provisions network, VPN & VPC.",
                "Configures enterprise IAM / SSO.",
                "Authorizes source ERP/DB extracts.",
                "Reviews security and compliance.",
            ],
        },
        {
            "title": "Snowflake Platform Lead",
            "org": vendor_name,
            "badge": "ENGINEERING",
            "badge_color": "accent",
            "stripe_color": c_accent,
            "bullets": [
                "Deploys Snowflake DDL & schemas.",
                "Builds dbt transformation pipelines.",
                "Configures RBAC & data masking.",
                "Optimizes virtual warehouse compute.",
            ],
        },
        {
            "title": "Analytics & AI Specialists",
            "org": vendor_name,
            "badge": "ANALYTICS / BI",
            "badge_color": "accent",
            "stripe_color": c_accent,
            "bullets": [
                "Builds Streamlit executive portals.",
                "Develops semantic data models.",
                "Implements ML/Cortex AI pipelines.",
                "Conducts technical knowledge transfer.",
            ],
        },
    ]

    for idx, pod in enumerate(pods_data):
        p_left = Inches(0.80) + idx * (pod_width + pod_gap)
        add_card_with_top_stripe(
            slide, theme, p_left, pod_top, pod_width, pod_height,
            accent_rgb=pod["stripe_color"],
            bg_color=c_surface,
        )
        _add_status_pill(slide, theme, p_left + Inches(0.14), pod_top + Inches(0.08), Inches(1.10), Inches(0.20), pod["badge"], font_size_pt=7.0, override_color_key=pod["badge_color"])

        tb_pod = slide.shapes.add_textbox(p_left + Inches(0.14), pod_top + Inches(0.32), pod_width - Inches(0.28), pod_height - Inches(0.36))
        tf_pod = tb_pod.text_frame
        tf_pod.word_wrap = True
        tf_pod.margin_left = tf_pod.margin_right = tf_pod.margin_top = tf_pod.margin_bottom = 0

        p_h = tf_pod.paragraphs[0]
        p_h.text = pod["title"]
        p_h.font.name = theme.font_family_header
        p_h.font.size = Pt(9.5)
        p_h.font.bold = True
        p_h.font.color.rgb = c_primary

        p_sub = tf_pod.add_paragraph()
        p_sub.text = pod["org"]
        p_sub.font.name = theme.font_family
        p_sub.font.size = Pt(7.5)
        p_sub.font.color.rgb = c_muted
        p_sub.space_before = Pt(1)

        for b_text in pod["bullets"]:
            _add_bullet_paragraph(tf_pod, b_text, theme.font_family, font_size_pt=8.0, font_color=c_secondary, space_before_pt=1.5)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 2. Slide 35: Change Request (CR) Procedure Slide (Procedural Flow & Decision Gate)
# ============================================================================

def build_change_request_procedure_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "PROJECT GOVERNANCE | SCOPE & CHANGE CONTROL",
    action_title: str = "Structured Change Request Procedure Governs Scope Adjustments Through Defined Decision Gates",
    subtitle: Optional[str] = "Sequential 4-stage governance pipeline with bi-level escalation thresholds and auditable legal sign-offs.",
    current_idx: int = 2,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders permanent reference Slide 35 as an interconnected procedural flow:
      - Continuous Horizontal Process Pipeline with directional connectors
      - Phase 1: Request & Intake -> Phase 2: Technical Assessment ->
        Phase 3: Bifurcated Decision Gate (PMO Fast-Track vs Steering Committee) ->
        Phase 4: Contractual BAST & Deployment
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    c_primary = theme.get_rgb("primary")
    c_secondary = theme.get_rgb("secondary")
    c_muted = theme.get_rgb("muted")
    c_accent = theme.get_rgb("accent")
    c_surface = theme.get_rgb("surface")

    c_accent_sec = theme.get_rgb("accent_secondary")

    card_top = Inches(2.62)
    card_width = Inches(2.62)
    card_height = Inches(2.96)
    card_gap = Inches(0.42)

    # ------------------------------------------------------------------------
    # STEP SQUARES & PROCESS RUNNER TRACK (Unified Metrodata Blue)
    # ------------------------------------------------------------------------
    sq_size = Inches(0.80)
    sq_top = Inches(1.65)
    sq_cy = sq_top + sq_size / 2.0

    # Horizontal runner line connecting the step squares
    x_start = Inches(0.80) + card_width / 2.0
    x_end = Inches(0.80) + 3 * (card_width + card_gap) + card_width / 2.0
    _draw_h_line(slide, x_start, x_end, sq_cy, theme.get_rgb("border"), width_pt=2.0)

    phases = [
        {
            "step_num": "1",
            "title": "Identification & Request",
            "actor": "CLIENT BPO / LEAD",
            "desc": "New scope item or change identified from business need or architectural shift.",
            "actions": [
                "Draft formal Change Request Form.",
                "Define business rationale & objectives.",
                "Register in PMO intake queue.",
            ],
            "artifact": "4.4_Change_Request_Form.docx",
            "status": "SUBMITTED",
        },
        {
            "step_num": "2",
            "title": "Impact & Manday Scoping",
            "actor": "METRODATA TECH TEAM",
            "desc": "Delivery architects evaluate technical complexity, manday effort, and timeline impact.",
            "actions": [
                "Estimate required mandays by role.",
                "Model schedule & S-curve variance.",
                "Determine risk & cost exposure.",
            ],
            "artifact": "CR_Scoping_and_Mandays.xlsx",
            "status": "EVALUATED",
        },
        {
            "step_num": "3",
            "title": "Bi-Level Decision Gate",
            "actor": "PMO & STEERING COMMITTEE",
            "desc": "Bifurcated threshold gateway prevents budget creep and uncontrolled slippage.",
            "actions": [
                "Path A: < 5 Mandays -> PMO Approval.",
                "Path B: ≥ 5 Mandays -> SteerCo Review.",
                "Outcome: Approved / Deferred / Rejected.",
            ],
            "artifact": "4.4_Change_Log_Ledger.xlsx",
            "status": "APPROVED",
        },
        {
            "step_num": "4",
            "title": "Contract Baseline & Build",
            "actor": "DELIVERY POD & LEGAL PMO",
            "desc": "Approved scope incorporated into development sprints and contractual deliverables.",
            "actions": [
                "Execute formal BAST Change Request.",
                "Re-baseline project schedule in PPM.",
                "Deploy feature into target sprint.",
            ],
            "artifact": "BAST_Change_Request.docx",
            "status": "IMPLEMENTED",
        },
    ]

    for idx, ph in enumerate(phases):
        c_left = Inches(0.80) + idx * (card_width + card_gap)
        c_center_x = c_left + card_width / 2.0
        stripe_c = c_accent  # Unified Signature Metrodata Blue

        # 1. Prominent Separate Step Square (Metrodata Blue)
        sq_left = c_center_x - sq_size / 2.0
        sq_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, sq_left, sq_top, sq_size, sq_size)
        sq_shape.shadow.inherit = False
        sq_shape.fill.solid()
        sq_shape.fill.fore_color.rgb = stripe_c
        sq_shape.line.fill.background()

        tf_sq = sq_shape.text_frame
        tf_sq.word_wrap = False
        tf_sq.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_sq.margin_left = tf_sq.margin_right = tf_sq.margin_top = tf_sq.margin_bottom = 0

        p_s1 = tf_sq.paragraphs[0]
        p_s1.text = "STEP"
        p_s1.alignment = PP_ALIGN.CENTER
        p_s1.font.name = theme.font_family_header
        p_s1.font.size = Pt(8.0)
        p_s1.font.bold = True
        p_s1.font.color.rgb = RGBColor(255, 255, 255)

        p_s2 = tf_sq.add_paragraph()
        p_s2.text = ph["step_num"]
        p_s2.alignment = PP_ALIGN.CENTER
        p_s2.font.name = theme.font_family_header
        p_s2.font.size = Pt(18.0)
        p_s2.font.bold = True
        p_s2.font.color.rgb = RGBColor(255, 255, 255)
        p_s2.space_before = Pt(0)

        # 2. Vertical drop line connecting Step Square to Card Top
        _draw_v_line(slide, c_center_x, sq_top + sq_size, card_top, stripe_c, width_pt=2.0)

        # 3. Inter-Step Chevrons along runner track & between cards (Signature Crimson Red)
        if idx < 3:
            # Runner Track Chevron (Crimson Red)
            next_center_x = c_left + card_width + card_gap + card_width / 2.0
            mid_sq_x = (c_center_x + next_center_x) / 2.0
            top_ch = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, mid_sq_x - Inches(0.12), sq_cy - Inches(0.13), Inches(0.24), Inches(0.26))
            top_ch.shadow.inherit = False
            top_ch.fill.solid()
            top_ch.fill.fore_color.rgb = c_accent_sec
            top_ch.line.fill.background()

            # Mid-Card Chevron between card bodies (Crimson Red)
            mid_arr_x = c_left + card_width + (card_gap - Inches(0.26)) / 2.0
            mid_arr_y = card_top + Inches(1.30)
            mid_arr = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, mid_arr_x, mid_arr_y, Inches(0.26), Inches(0.36))
            mid_arr.shadow.inherit = False
            mid_arr.fill.solid()
            mid_arr.fill.fore_color.rgb = c_accent_sec
            mid_arr.line.fill.background()

        # 4. Detail Content Card (Top Stripe: Metrodata Blue)
        add_card_with_top_stripe(
            slide, theme, c_left, card_top, card_width, card_height,
            accent_rgb=stripe_c,
            bg_color=c_surface,
        )

        # Content Textbox (From card top to above bottom status pill)
        tb_height = card_height - Inches(0.50)
        tb = slide.shapes.add_textbox(c_left + Inches(0.14), card_top + Inches(0.14), card_width - Inches(0.28), tb_height)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_title = tf.paragraphs[0]
        p_title.text = ph["title"]
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(10.0)
        p_title.font.bold = True
        p_title.font.color.rgb = c_primary

        p_actor = tf.add_paragraph()
        p_actor.text = f"OWNER: {ph['actor']}"
        p_actor.font.name = theme.font_family
        p_actor.font.size = Pt(7.5)
        p_actor.font.bold = True
        p_actor.font.color.rgb = stripe_c
        p_actor.space_before = Pt(2)

        p_desc = tf.add_paragraph()
        p_desc.text = ph["desc"]
        p_desc.font.name = theme.font_family
        p_desc.font.size = Pt(8.0)
        p_desc.font.color.rgb = c_secondary
        p_desc.space_before = Pt(3)

        p_act_lbl = tf.add_paragraph()
        p_act_lbl.text = "PROCEDURAL CHECKLIST:"
        p_act_lbl.font.name = theme.font_family
        p_act_lbl.font.size = Pt(7.0)
        p_act_lbl.font.bold = True
        p_act_lbl.font.color.rgb = c_primary
        p_act_lbl.space_before = Pt(4)

        for act in ph["actions"]:
            _add_bullet_paragraph(tf, act, theme.font_family, font_size_pt=7.5, font_color=c_secondary, space_before_pt=1.5)

        p_art = tf.add_paragraph()
        p_art.text = "OUTPUT ARTIFACT:"
        p_art.font.name = theme.font_family
        p_art.font.size = Pt(7.0)
        p_art.font.bold = True
        p_art.font.color.rgb = c_muted
        p_art.space_before = Pt(4)

        p_art_val = tf.add_paragraph()
        p_art_val.text = ph["artifact"]
        p_art_val.font.name = theme.font_family
        p_art_val.font.size = Pt(7.5)
        p_art_val.font.bold = True
        p_art_val.font.color.rgb = c_accent
        p_art_val.space_before = Pt(1)

        # 5. Standardized Stage Status Badge Anchored at Bottom of Card
        pill_w = Inches(1.30)
        pill_h = Inches(0.22)
        pill_left = c_left + (card_width - pill_w) / 2.0
        pill_top = card_top + card_height - pill_h - Inches(0.12)
        _add_status_pill(
            slide,
            theme,
            pill_left,
            pill_top,
            pill_w,
            pill_h,
            ph["status"],
            font_size_pt=7.5,
            override_color_key="accent",
        )

    # ------------------------------------------------------------------------
    # Bottom Callout Card: Governance Decision Thresholds
    # ------------------------------------------------------------------------
    bot_left = Inches(0.80)
    bot_top = Inches(5.72)
    bot_width = Inches(11.733)
    bot_height = Inches(1.15)

    add_card_with_top_stripe(
        slide, theme, bot_left, bot_top, bot_width, bot_height,
        accent_rgb=theme.get_rgb("primary"),
        bg_color=c_surface,
    )

    tb_bot = slide.shapes.add_textbox(bot_left + Inches(0.25), bot_top + Inches(0.12), bot_width - Inches(0.50), bot_height - Inches(0.20))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    tf_bot.margin_left = tf_bot.margin_right = tf_bot.margin_top = tf_bot.margin_bottom = 0

    p_bh = tf_bot.paragraphs[0]
    p_bh.text = "CHANGE REQUEST ESCALATION THRESHOLDS & GOVERNANCE RULES"
    p_bh.font.name = theme.font_family_header
    p_bh.font.size = Pt(10.0)
    p_bh.font.bold = True
    p_bh.font.color.rgb = c_primary

    _add_bullet_paragraph(
        tf_bot,
        "Fast-Track Level 1 Gate (PMO Joint Sign-Off): Scope adjustments within contingency buffers (< 5 mandays) with zero impact on milestone delivery dates. Recorded in Change Log without commercial addendum.",
        theme.font_family,
        font_size_pt=8.5,
        font_color=c_secondary,
        space_before_pt=3.0,
    )
    _add_bullet_paragraph(
        tf_bot,
        "Escalated Level 2 Gate (Joint Steering Committee): Any change impacting contract value, baseline completion dates, or architecture topology. Requires formal BAST CR addendum signed by C-level sponsors.",
        theme.font_family,
        font_size_pt=8.5,
        font_color=c_secondary,
        space_before_pt=2.0,
    )

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 3. Slide 17: Snowflake Platform Architecture Slide (Official Graphic)
# ============================================================================

def build_snowflake_platform_architecture_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "TECHNOLOGY PLATFORM BLUEPRINT | SNOWFLAKE DATA CLOUD",
    action_title: str = "Fully-Managed Unified Platform Eliminates Data Silos Across Multi-Cloud Environments",
    subtitle: Optional[str] = "Official Snowflake platform blueprint showing decoupled storage, elastic compute, and Horizon governance.",
    current_idx: int = 3,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders permanent reference Slide 17 by cleanly embedding the official,
    vector-rendered Snowflake Platform Architecture graphic under our standard consulting frame.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # Frame Container for Official Graphic
    frame_left = Inches(1.00)
    frame_top = Inches(1.80)
    frame_width = Inches(11.333)
    frame_height = Inches(5.05)

    # Background card to frame image cleanly
    add_card(
        slide,
        theme,
        frame_left,
        frame_top,
        frame_width,
        frame_height,
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("border"),
    )

    # Embed official graphic with strict aspect ratio preservation
    if OFFICIAL_SNOWFLAKE_PLATFORM_IMG.exists():
        inner_left = frame_left + Inches(0.15)
        inner_top = frame_top + Inches(0.15)
        inner_width = frame_width - Inches(0.30)
        inner_height = frame_height - Inches(0.30)

        img_l, img_t, img_w, img_h = _fit_image_in_box(
            OFFICIAL_SNOWFLAKE_PLATFORM_IMG,
            inner_left,
            inner_top,
            inner_width,
            inner_height,
        )
        slide.shapes.add_picture(
            str(OFFICIAL_SNOWFLAKE_PLATFORM_IMG),
            img_l,
            img_t,
            width=img_w,
            height=img_h,
        )
    else:
        logger.warning(f"Official Snowflake graphic not found at: {OFFICIAL_SNOWFLAKE_PLATFORM_IMG}")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 4. Slide 18: Building Data Warehouse with Snowflake (Official Graphic)
# ============================================================================

def build_snowflake_data_pipeline_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "SOLUTION ARCHITECTURE | END-TO-END DATA PIPELINE",
    action_title: str = "Modern Data Pipeline Streamlines Continuous Ingestion into Governed Analytics Consumption",
    subtitle: Optional[str] = "Official end-to-end data flow: transactional ERP/IoT sources into Snowflake core, virtual warehouses, and delivery channels.",
    current_idx: int = 4,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders permanent reference Slide 18 by cleanly embedding the official
    Snowflake solution architecture dataflow graphic under our standard consulting frame.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # Frame Container for Official Graphic
    frame_left = Inches(1.00)
    frame_top = Inches(1.80)
    frame_width = Inches(11.333)
    frame_height = Inches(5.05)

    # Background card to frame image cleanly
    add_card(
        slide,
        theme,
        frame_left,
        frame_top,
        frame_width,
        frame_height,
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("border"),
    )

    # Embed official graphic with strict aspect ratio preservation
    if OFFICIAL_SNOWFLAKE_FLOW_IMG.exists():
        inner_left = frame_left + Inches(0.15)
        inner_top = frame_top + Inches(0.15)
        inner_width = frame_width - Inches(0.30)
        inner_height = frame_height - Inches(0.30)

        img_l, img_t, img_w, img_h = _fit_image_in_box(
            OFFICIAL_SNOWFLAKE_FLOW_IMG,
            inner_left,
            inner_top,
            inner_width,
            inner_height,
        )
        slide.shapes.add_picture(
            str(OFFICIAL_SNOWFLAKE_FLOW_IMG),
            img_l,
            img_t,
            width=img_w,
            height=img_h,
        )
    else:
        logger.warning(f"Official Snowflake data flow graphic not found at: {OFFICIAL_SNOWFLAKE_FLOW_IMG}")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 5. Master Reference Deck Builder Subsystem
# ============================================================================

class ReferenceDeckBuilder:
    """
    Assembles permanent engagement governance and technical solution reference decks.
    """

    def __init__(self, theme: Union[str, Theme] = "metrodata", locale: str = "en") -> None:
        self.theme: Theme = get_theme(theme) if isinstance(theme, str) else theme
        self.locale: str = locale.lower()
        from src.core.locale_engine import get_locale_engine
        self.loc_engine = get_locale_engine(self.locale)
        self.prs: Presentation = create_presentation(self.theme)

    def add_cover(
        self,
        title: str = "ENTERPRISE BENCHMARK REFERENCE SLIDES",
        subtitle: str = "Permanent Engagement Governance & Snowflake Platform Architecture Blueprints",
        client: str = "[CLIENT_COMPANY_NAME]",
        vendor: str = "PT Metrodata Electronics Tbk",
        product: str = "Snowflake AI Data Cloud",
        date_str: str = "September 2026",
        hero_image_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> Any:
        if hero_image_path is not None:
            return self.add_hero_cover(
                title=title,
                subtitle=subtitle,
                client=client,
                vendor=vendor,
                product=product,
                date_str=date_str,
                hero_image_path=hero_image_path,
                **kwargs,
            )
        return build_cover_slide(
            prs=self.prs,
            theme=self.theme,
            title=title,
            subtitle=subtitle,
            client=client,
            vendor=vendor,
            product=product,
            date_str=date_str,
            tracker="ENTERPRISE BENCHMARK REFERENCE COLLATERAL",
            client_sublabel="Project Steering Committee & Sponsors",
            vendor_sublabel="Data & AI Practice Lead",
        )

    def add_hero_cover(
        self,
        title: str = "ENTERPRISE BENCHMARK REFERENCE SLIDES",
        subtitle: str = "Permanent Engagement Governance & Snowflake Platform Architecture Blueprints",
        client: str = "[CLIENT_COMPANY_NAME]",
        vendor: str = "PT Metrodata Electronics Tbk",
        product: str = "Snowflake AI Data Cloud",
        date_str: str = "September 2026",
        tracker: str = "ENTERPRISE BENCHMARK REFERENCE COLLATERAL",
        hero_image_path: Optional[Union[str, Path]] = None,
        hero_height: float = 3.65,
        scrim_alpha: float = 0.28,
        **kwargs: Any,
    ) -> Any:
        return build_hero_cover_slide(
            prs=self.prs,
            theme=self.theme,
            title=title,
            subtitle=subtitle,
            client=client,
            vendor=vendor,
            product=product,
            date_str=date_str,
            tracker=tracker,
            hero_image_path=hero_image_path,
            hero_height=hero_height,
            scrim_alpha=scrim_alpha,
            client_sublabel=kwargs.get("client_sublabel", "Project Steering Committee & Sponsors"),
            vendor_sublabel=kwargs.get("vendor_sublabel", "Data & AI Practice Lead"),
        )

    def add_governance_org_structure(self, **kwargs: Any) -> Any:
        idx = len(self.prs.slides) + 1
        return build_governance_org_structure_slide(
            prs=self.prs,
            theme=self.theme,
            current_idx=idx,
            total_slides=idx,
            **kwargs,
        )

    def add_change_request_procedure(self, **kwargs: Any) -> Any:
        idx = len(self.prs.slides) + 1
        return build_change_request_procedure_slide(
            prs=self.prs,
            theme=self.theme,
            current_idx=idx,
            total_slides=idx,
            **kwargs,
        )

    def add_snowflake_platform_architecture(self, **kwargs: Any) -> Any:
        idx = len(self.prs.slides) + 1
        return build_snowflake_platform_architecture_slide(
            prs=self.prs,
            theme=self.theme,
            current_idx=idx,
            total_slides=idx,
            **kwargs,
        )

    def add_snowflake_data_pipeline(self, **kwargs: Any) -> Any:
        idx = len(self.prs.slides) + 1
        return build_snowflake_data_pipeline_slide(
            prs=self.prs,
            theme=self.theme,
            current_idx=idx,
            total_slides=idx,
            **kwargs,
        )

    def add_equity_corporate_tree(
        self,
        tracker: str = "CORPORATE GOVERNANCE | EQUITY STRUCTURE",
        action_title: str = "Metrodata Group Operates Multi-Tier Operating Subsidiaries and Specialized JVs",
        subtitle: Optional[str] = "PT Metrodata Electronics Tbk (MTDL) maintains controlling equity across core ICT distribution, solutions, and digital consulting entities.",
        tree_data: Optional[EquityTreeData] = None,
        **kwargs: Any,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_equity_corporate_tree_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            tree_data=tree_data,
            current_idx=idx,
            total_slides=idx,
            **kwargs,
        )

    def build_all(
        self,
        client_name: str = "[CLIENT_COMPANY_NAME]",
        vendor_name: str = "PT Metrodata Electronics Tbk",
    ) -> None:
        """Builds canonical 5-slide reference deck (Cover + 4 reference slides)."""
        self.add_cover(client=client_name, vendor=vendor_name)
        self.add_governance_org_structure(client_name=client_name, vendor_name=vendor_name)
        self.add_change_request_procedure()
        self.add_snowflake_platform_architecture()
        self.add_snowflake_data_pipeline()
        self.update_pagination()

    def update_pagination(self) -> None:
        """Synchronizes bottom slide numbers (e.g. '02 / 05')."""
        import re
        total = len(self.prs.slides)
        for s_idx, slide in enumerate(self.prs.slides, start=1):
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for p in shape.text_frame.paragraphs:
                        text_clean = p.text.strip()
                        if re.match(r"^\d{2}\s*/\s*\d{2}$", text_clean):
                            new_str = f"{s_idx:02d} / {total:02d}"
                            if p.runs:
                                r0 = p.runs[0]
                                fn = r0.font.name
                                fs = r0.font.size
                                fb = r0.font.bold
                                fc = r0.font.color.rgb if (r0.font.color and r0.font.color.type == 1) else None
                                p.text = new_str
                                if p.runs:
                                    nr = p.runs[0]
                                    nr.font.name = fn
                                    nr.font.size = fs
                                    nr.font.bold = fb
                                    if fc:
                                        nr.font.color.rgb = fc
                            else:
                                p.text = new_str

    def save(
        self,
        output_path: Union[str, Path],
        engagement_context: Optional[Any] = None,
    ) -> Path:
        """Saves presentation deck to target path after synchronizing pagination and substituting slugs."""
        self.update_pagination()
        if engagement_context is not None:
            from src.core.slug_registry import substitute_slugs_in_presentation
            substitute_slugs_in_presentation(self.prs, engagement_context)
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(p))
        return p

    @classmethod
    def from_yaml(
        cls,
        yaml_path: Union[str, Path],
        theme_override: Optional[str] = None,
        locale_override: Optional[str] = None,
    ) -> "ReferenceDeckBuilder":
        """Instantiates and configures a ReferenceDeckBuilder from a declarative YAML specification."""
        p = Path(yaml_path)
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        theme_name = theme_override or data.get("theme", "metrodata")
        locale_name = (locale_override or data.get("locale", "en")).lower()
        builder = cls(theme=theme_name, locale=locale_name)
        loc = builder.loc_engine

        meta = data.get("metadata", {})
        client_name = meta.get("client_name", "[CLIENT_COMPANY_NAME]")
        vendor_name = meta.get("vendor_name", "PT Metrodata Electronics Tbk")

        for slide_cfg in data.get("slides", []):
            archetype = slide_cfg.get("archetype", "")
            if archetype in ("cover", "hero_cover", "cinematic_cover"):
                hero_img = slide_cfg.get("hero_image_path")
                t_title = slide_cfg.get(f"title_{locale_name}") or (
                    loc.t("reference_slides.cover.title") if locale_name != "en" and not slide_cfg.get("title")
                    else (loc.t("reference_slides.cover.title") if locale_name != "en" and slide_cfg.get("title") == "ENTERPRISE BENCHMARK REFERENCE COLLATERAL" else slide_cfg.get("title", loc.t("reference_slides.cover.title")))
                )
                t_sub = slide_cfg.get(f"subtitle_{locale_name}") or (
                    loc.t("reference_slides.cover.subtitle") if locale_name != "en" and not slide_cfg.get("subtitle")
                    else (loc.t("reference_slides.cover.subtitle") if locale_name != "en" and "Permanent Project Governance" in str(slide_cfg.get("subtitle", "")) else slide_cfg.get("subtitle", loc.t("reference_slides.cover.subtitle")))
                )
                t_tr = slide_cfg.get(f"tracker_{locale_name}") or loc.t("reference_slides.cover.tracker", slide_cfg.get("tracker", "ENTERPRISE BENCHMARK REFERENCE COLLATERAL"))

                if archetype in ("hero_cover", "cinematic_cover") or hero_img:
                    builder.add_hero_cover(
                        title=t_title,
                        subtitle=t_sub,
                        client=slide_cfg.get("client", client_name),
                        vendor=slide_cfg.get("vendor", vendor_name),
                        product=slide_cfg.get("product", "Snowflake AI Data Cloud"),
                        date_str=slide_cfg.get("date_str", "September 2026"),
                        tracker=t_tr,
                        hero_image_path=hero_img,
                        hero_height=float(slide_cfg.get("hero_height", 3.65)),
                        scrim_alpha=float(slide_cfg.get("scrim_alpha", 0.28)),
                    )
                else:
                    builder.add_cover(
                        title=t_title,
                        subtitle=t_sub,
                        client=slide_cfg.get("client", client_name),
                        vendor=slide_cfg.get("vendor", vendor_name),
                        product=slide_cfg.get("product", "Snowflake AI Data Cloud"),
                        date_str=slide_cfg.get("date_str", "September 2026"),
                    )
            elif archetype in ("governance_org_structure", "org_structure"):
                t_tr = slide_cfg.get(f"tracker_{locale_name}") or (loc.t("reference_slides.governance_org.tracker") if locale_name != "en" else slide_cfg.get("tracker", loc.t("reference_slides.governance_org.tracker")))
                t_title = slide_cfg.get(f"title_{locale_name}") or (loc.t("reference_slides.governance_org.title") if locale_name != "en" else slide_cfg.get("title", loc.t("reference_slides.governance_org.title")))
                t_sub = slide_cfg.get(f"subtitle_{locale_name}") or (loc.t("reference_slides.governance_org.subtitle") if locale_name != "en" else slide_cfg.get("subtitle", loc.t("reference_slides.governance_org.subtitle")))

                builder.add_governance_org_structure(
                    tracker=t_tr,
                    action_title=t_title,
                    subtitle=t_sub,
                    client_name=slide_cfg.get("client_name", client_name),
                    vendor_name=slide_cfg.get("vendor_name", vendor_name),
                )
            elif archetype in ("change_request_procedure", "change_request"):
                t_tr = slide_cfg.get(f"tracker_{locale_name}") or (loc.t("reference_slides.change_request.tracker") if locale_name != "en" else slide_cfg.get("tracker", loc.t("reference_slides.change_request.tracker")))
                t_title = slide_cfg.get(f"title_{locale_name}") or (loc.t("reference_slides.change_request.title") if locale_name != "en" else slide_cfg.get("title", loc.t("reference_slides.change_request.title")))
                t_sub = slide_cfg.get(f"subtitle_{locale_name}") or (loc.t("reference_slides.change_request.subtitle") if locale_name != "en" else slide_cfg.get("subtitle", loc.t("reference_slides.change_request.subtitle")))

                builder.add_change_request_procedure(
                    tracker=t_tr,
                    action_title=t_title,
                    subtitle=t_sub,
                )
            elif archetype in ("snowflake_platform_architecture", "platform_architecture"):
                t_tr = slide_cfg.get(f"tracker_{locale_name}") or (loc.t("reference_slides.platform_arch.tracker") if locale_name != "en" else slide_cfg.get("tracker", loc.t("reference_slides.platform_arch.tracker")))
                t_title = slide_cfg.get(f"title_{locale_name}") or (loc.t("reference_slides.platform_arch.title") if locale_name != "en" else slide_cfg.get("title", loc.t("reference_slides.platform_arch.title")))
                t_sub = slide_cfg.get(f"subtitle_{locale_name}") or (loc.t("reference_slides.platform_arch.subtitle") if locale_name != "en" else slide_cfg.get("subtitle", loc.t("reference_slides.platform_arch.subtitle")))

                builder.add_snowflake_platform_architecture(
                    tracker=t_tr,
                    action_title=t_title,
                    subtitle=t_sub,
                )
            elif archetype in ("snowflake_data_pipeline", "data_pipeline"):
                t_tr = slide_cfg.get(f"tracker_{locale_name}") or (loc.t("reference_slides.data_pipeline.tracker") if locale_name != "en" else slide_cfg.get("tracker", loc.t("reference_slides.data_pipeline.tracker")))
                t_title = slide_cfg.get(f"title_{locale_name}") or (loc.t("reference_slides.data_pipeline.title") if locale_name != "en" else slide_cfg.get("title", loc.t("reference_slides.data_pipeline.title")))
                t_sub = slide_cfg.get(f"subtitle_{locale_name}") or (loc.t("reference_slides.data_pipeline.subtitle") if locale_name != "en" else slide_cfg.get("subtitle", loc.t("reference_slides.data_pipeline.subtitle")))

                builder.add_snowflake_data_pipeline(
                    tracker=t_tr,
                    action_title=t_title,
                    subtitle=t_sub,
                )
            elif archetype in ("corporate_equity_tree", "equity_tree", "corporate_structure"):
                t_tr = slide_cfg.get(f"tracker_{locale_name}") or slide_cfg.get("tracker", "CORPORATE GOVERNANCE | EQUITY STRUCTURE")
                t_title = slide_cfg.get(f"title_{locale_name}") or slide_cfg.get("title", "Metrodata Group Operates Multi-Tier Operating Subsidiaries and Specialized JVs")
                t_sub = slide_cfg.get(f"subtitle_{locale_name}") or slide_cfg.get("subtitle", "PT Metrodata Electronics Tbk (MTDL) maintains controlling equity across core ICT distribution, solutions, and digital consulting entities.")

                tree_cfg = slide_cfg.get("tree_data")
                tree_data = None
                if isinstance(tree_cfg, dict):
                    t1_nodes = [EquityEntityNode(**n) for n in tree_cfg.get("tier1_nodes", [])]
                    t2_nodes = [EquityEntityNode(**n) for n in tree_cfg.get("tier2_nodes", [])]
                    tree_data = EquityTreeData(
                        parent_company=tree_cfg.get("parent_company", "PT Metrodata Electronics Tbk"),
                        parent_ticker=tree_cfg.get("parent_ticker", "MTDL"),
                        parent_subtitle=tree_cfg.get("parent_subtitle", "Holding & Listed Investment Company"),
                        tier1_nodes=t1_nodes,
                        tier2_nodes=t2_nodes,
                        footnote=tree_cfg.get("footnote", slide_cfg.get("footnote", "*) Reflects legal equity shareholding percentages as of latest PMO baseline.")),
                    )
                elif "footnote" in slide_cfg:
                    from src.ppt_engine.consulting_archetypes import _default_equity_tree_data
                    tree_data = _default_equity_tree_data()
                    tree_data.footnote = slide_cfg["footnote"]

                builder.add_equity_corporate_tree(
                    tracker=t_tr,
                    action_title=t_title,
                    subtitle=t_sub,
                    tree_data=tree_data,
                )
        builder.update_pagination()
        return builder
