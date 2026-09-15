"""
Enterprise Presentation Deck Builder
====================================
Generates a consulting-grade 3-slide widescreen (16:9) presentation for an
Enterprise Cloud Architecture & Operational Workflow strategy.

Orchestrates:
  1. diagram_engine: Compiles Mermaid architecture, data pipeline, and state diagrams to Draw.io (.drawio) + PNG.
  2. icon_engine: Searches, tints brand-specific SVG/PNG icons with badge containers.
  3. image_engine: Generates 3D procedural hero visuals and applies presentation framing (rounded corners, hairline border, shadow).
  4. python-pptx: Places explicit coordinate layout containers, cards, typography, and visual assets.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from typing import Dict, List, Optional, Tuple, Any

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Local engine subsystems
from src.ppt_engine.diagram_engine import DiagramEngine, compile_mermaid
from src.ppt_engine.icon_engine import IconEngine, get_brand_icon
from src.ppt_engine.image_engine import ImageEngine, frame_slide_image


# ============================================================================
# 1. Design System & 60-30-10 Consulting Palette
# ============================================================================

class Palette:
    # 60% Canvas / Neutral background
    CANVAS_BG = RGBColor(248, 250, 252)       # #F8FAFC
    CARD_BG = RGBColor(255, 255, 255)         # #FFFFFF
    CARD_MUTED = RGBColor(241, 245, 249)      # #F1F5F9
    BORDER_LIGHT = RGBColor(226, 232, 240)    # #E2E8F0
    BORDER_ACCENT = RGBColor(191, 219, 254)   # #BFDBFE

    # 30% Primary / Secondary Structural Slate & Navy
    TEXT_PRIMARY = RGBColor(15, 23, 42)       # #0F172A (Deep Slate)
    TEXT_SECONDARY = RGBColor(71, 85, 105)    # #475569 (Slate Gray)
    TEXT_MUTED = RGBColor(148, 163, 184)      # #94A3B8 (Light Slate)
    NAVY_CONTAINER = RGBColor(30, 41, 59)     # #1E293B

    # 10% High-Contrast Brand Accents
    BRAND_BLUE = RGBColor(37, 99, 235)        # #2563EB
    BRAND_BLUE_HEX = "#2563EB"
    BRAND_CYAN = RGBColor(14, 165, 233)       # #0EA5E9
    BRAND_CYAN_HEX = "#0EA5E9"
    BRAND_TEAL = RGBColor(15, 118, 110)       # #0F766E
    BRAND_TEAL_HEX = "#0F766E"
    SUCCESS_GREEN = RGBColor(22, 163, 74)     # #16A34A
    SUCCESS_GREEN_HEX = "#16A34A"
    WARNING_AMBER = RGBColor(217, 119, 6)     # #D97706
    WARNING_AMBER_HEX = "#D97706"

    # Badge Fills
    BADGE_BLUE_FILL = RGBColor(239, 246, 255) # #EFF6FF
    BADGE_GREEN_FILL = RGBColor(240, 253, 244)# #F0FDF4
    BADGE_AMBER_FILL = RGBColor(254, 243, 199)# #FEF3C7


# ============================================================================
# 2. Slide Geometry & Container Layout Helpers
# ============================================================================

def create_deck() -> Presentation:
    """Initialize standard 16:9 widescreen presentation deck."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_slide_with_background(prs: Presentation) -> Any:
    """Add a blank slide with consulting canvas background fill."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Base background shape
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0),
        Inches(0),
        prs.slide_width,
        prs.slide_height,
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = Palette.CANVAS_BG
    bg.line.fill.background()

    return slide


def add_slide_header(
    slide: Any,
    tracker: str,
    action_title: str,
    subtitle: Optional[str] = None,
    tracker_color: RGBColor = Palette.BRAND_BLUE,
) -> None:
    """Renders consulting header block: Category Tracker, Action Headline, and Context Subtitle."""
    # 1. Breadcrumb Tracker Pill / Text
    tracker_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.733), Inches(0.28))
    tf_tr = tracker_box.text_frame
    tf_tr.word_wrap = True
    tf_tr.margin_left = tf_tr.margin_right = tf_tr.margin_top = tf_tr.margin_bottom = 0
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = tracker.upper()
    p_tr.font.size = Pt(9.5)
    p_tr.font.bold = True
    p_tr.font.color.rgb = tracker_color

    # 2. Action-driven Headline & Subtitle (Unified Frame for Consistent Spacing)
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.95))
    tf_h = header_box.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0
    p_t = tf_h.paragraphs[0]
    p_t.text = action_title
    p_t.font.size = Pt(20)
    p_t.font.bold = True
    p_t.font.color.rgb = Palette.TEXT_PRIMARY

    # 3. Context Subtitle (Flowed via paragraph offset)
    if subtitle:
        p_s = tf_h.add_paragraph()
        p_s.text = subtitle
        p_s.font.size = Pt(11)
        p_s.font.color.rgb = Palette.TEXT_SECONDARY
        p_s.space_before = Pt(10)


def add_card(
    slide: Any,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    bg_color: RGBColor = Palette.CARD_BG,
    border_color: RGBColor = Palette.BORDER_LIGHT,
    border_width: Pt = Pt(1),
    has_top_stripe: bool = False,
) -> Any:
    """Draws a card container. Enforces sharp 90-degree rectangle if has_top_stripe=True."""
    shape_type = MSO_SHAPE.RECTANGLE if has_top_stripe else MSO_SHAPE.ROUNDED_RECTANGLE
    card = slide.shapes.add_shape(shape_type, left, top, width, height)
    card.shadow.inherit = False
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = border_width
    else:
        card.line.fill.background()
    return card


def add_slide_footer(slide: Any, current_idx: int, total_slides: int = 3) -> None:
    """Renders bottom metadata rule, date/confidentiality notice, and slide pagination."""
    # Hairline divider
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.8),
        Inches(7.05),
        Inches(11.733),
        Inches(0.015),
    )
    divider.shadow.inherit = False
    divider.fill.solid()
    divider.fill.fore_color.rgb = Palette.BORDER_LIGHT
    divider.line.fill.background()

    # Footer Notice
    f_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(8.0), Inches(0.25))
    tf_f = f_box.text_frame
    tf_f.margin_left = tf_f.margin_right = tf_f.margin_top = tf_f.margin_bottom = 0
    p_f = tf_f.paragraphs[0]
    p_f.text = "Enterprise Architecture Group  |  Confidential & Proprietary"
    p_f.font.size = Pt(8.5)
    p_f.font.color.rgb = Palette.TEXT_MUTED

    # Page number
    p_box = slide.shapes.add_textbox(Inches(10.533), Inches(7.12), Inches(2.0), Inches(0.25))
    tf_p = p_box.text_frame
    tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0
    p_p = tf_p.paragraphs[0]
    p_p.text = f"{current_idx:02d} / {total_slides:02d}"
    p_p.font.size = Pt(8.5)
    p_p.font.bold = True
    p_p.alignment = PP_ALIGN.RIGHT
    p_p.font.color.rgb = Palette.TEXT_MUTED


# ============================================================================
# 3. Slide 1 Builder: Executive Architecture & Cloud Migration Strategy
# ============================================================================

def build_slide_1(prs: Presentation, assets_map: Dict[str, Path]) -> None:
    """
    Slide 1: Executive Architecture & Cloud Migration Strategy
    Features:
      - 3 Metric KPI Cards with tinted brand icons
      - Generated Draw.io Architecture Diagram from Mermaid
      - Framed 3D visual card asset
      - Key Strategic Principles card
    """
    slide = add_slide_with_background(prs)
    add_slide_header(
        slide=slide,
        tracker="Enterprise Cloud Modernization  |  Executive Architecture Strategy",
        action_title="Decoupled Multi-Region Mesh Architecture Accelerates Migration Velocity by 4.2x",
        subtitle="Zero-downtime microservices platform unifying legacy on-prem core systems with elastic cloud-native clusters.",
    )

    # -------------------------------------------------------------------------
    # Row 1: 3 KPI Metric Cards (Top Section, Y=1.72", Height=1.10")
    # -------------------------------------------------------------------------
    kpis = [
        {
            "icon": assets_map["icon_shield"],
            "value": "99.999%",
            "label": "Target SLA Reliability",
            "desc": "Multi-region automated failover",
            "accent": Palette.BRAND_BLUE,
        },
        {
            "icon": assets_map["icon_zap"],
            "value": "4.2x",
            "label": "Deployment Velocity",
            "desc": "Automated blue-green pipelines",
            "accent": Palette.SUCCESS_GREEN,
        },
        {
            "icon": assets_map["icon_trend"],
            "value": "-68%",
            "label": "Infra TCO Reduction",
            "desc": "Dynamic node autoscale & tiered storage",
            "accent": Palette.BRAND_TEAL,
        },
    ]

    card_w = Inches(3.72)
    card_gap = Inches(0.28)
    start_x = Inches(0.8)
    row1_y = Inches(1.72)
    row1_h = Inches(1.10)

    for i, kpi in enumerate(kpis):
        cx = start_x + i * (card_w + card_gap)
        # Background card
        add_card(slide, cx, row1_y, card_w, row1_h, bg_color=Palette.CARD_BG)

        # Icon image
        slide.shapes.add_picture(str(kpi["icon"]), cx + Inches(0.18), row1_y + Inches(0.20), width=Inches(0.70), height=Inches(0.70))

        # Metric Value & Label text box
        tb = slide.shapes.add_textbox(cx + Inches(0.98), row1_y + Inches(0.15), card_w - Inches(1.05), row1_h - Inches(0.25))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = kpi["value"]
        p1.font.size = Pt(17)
        p1.font.bold = True
        p1.font.color.rgb = kpi["accent"]

        p2 = tf.add_paragraph()
        p2.text = kpi["label"]
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = Palette.TEXT_PRIMARY
        p2.space_before = Pt(1)

        p3 = tf.add_paragraph()
        p3.text = kpi["desc"]
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = Palette.TEXT_SECONDARY

    # -------------------------------------------------------------------------
    # Row 2: Architecture Diagram (Left) + Framed Visual & Bullet Pillars (Right)
    # -------------------------------------------------------------------------
    row2_y = Inches(2.98)
    row2_h = Inches(3.92)

    # Left Card Container: Draw.io Architecture Diagram
    diag_w = Inches(7.50)
    add_card(slide, Inches(0.8), row2_y, diag_w, row2_h, bg_color=Palette.CARD_BG)

    # Diagram Header Badge
    diag_tb = slide.shapes.add_textbox(Inches(1.05), row2_y + Inches(0.18), diag_w - Inches(0.5), Inches(0.4))
    diag_tf = diag_tb.text_frame
    diag_tf.margin_left = diag_tf.margin_right = diag_tf.margin_top = diag_tf.margin_bottom = 0
    p_dh = diag_tf.paragraphs[0]
    p_dh.text = "TARGET ARCHITECTURE TOPOLOGY (DRAW.IO ENGINE)"
    p_dh.font.size = Pt(10)
    p_dh.font.bold = True
    p_dh.font.color.rgb = Palette.BRAND_BLUE

    # Draw.io Compiled Diagram PNG
    diag_img_path = assets_map["diag_arch_png"]
    slide.shapes.add_picture(
        str(diag_img_path),
        Inches(1.0),
        row2_y + Inches(0.58),
        width=diag_w - Inches(0.4),
        height=row2_h - Inches(0.75),
    )

    # Right Card: Framed 3D Visual + Strategic Migration Pillars
    right_x = Inches(8.55)
    right_w = Inches(3.98)
    add_card(slide, right_x, row2_y, right_w, row2_h, bg_color=Palette.CARD_BG)

    # Framed Visual Hero Graphic
    hero_img_path = assets_map["framed_cloud_hero"]
    slide.shapes.add_picture(
        str(hero_img_path),
        right_x + Inches(0.20),
        row2_y + Inches(0.18),
        width=right_w - Inches(0.40),
        height=Inches(1.55),
    )

    # Strategic Pillars Content Box
    strat_tb = slide.shapes.add_textbox(
        right_x + Inches(0.25),
        row2_y + Inches(1.85),
        right_w - Inches(0.50),
        row2_h - Inches(1.95),
    )
    strat_tf = strat_tb.text_frame
    strat_tf.word_wrap = True
    strat_tf.margin_left = strat_tf.margin_right = strat_tf.margin_top = strat_tf.margin_bottom = 0

    p_st = strat_tf.paragraphs[0]
    p_st.text = "Core Architectural Pillars"
    p_st.font.size = Pt(12)
    p_st.font.bold = True
    p_st.font.color.rgb = Palette.TEXT_PRIMARY
    p_st.space_after = Pt(6)

    pillars = [
        ("Zero-Downtime Cutover", "Continuous dual-write CDC pipeline keeps legacy & cloud DBs synchronized."),
        ("Microsegmentation", "Granular service-mesh policies isolate blast radiuses across all VPCs."),
        ("Telemetry & Auto-Healing", "Distributed tracing triggers automated node failover in < 2 seconds."),
    ]

    for title, desc in pillars:
        p_item = strat_tf.add_paragraph()
        p_item.text = f"• {title}: "
        p_item.font.bold = True
        p_item.font.size = Pt(9.5)
        p_item.font.color.rgb = Palette.BRAND_BLUE

        run = p_item.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = Palette.TEXT_SECONDARY
        p_item.space_after = Pt(4)

    add_slide_footer(slide, current_idx=1, total_slides=3)


# ============================================================================
# 4. Slide 2 Builder: Data Pipeline & Zero-Trust Verification
# ============================================================================

def build_slide_2(prs: Presentation, assets_map: Dict[str, Path]) -> None:
    """
    Slide 2: Data Pipeline & Zero-Trust Verification
    Features:
      - Horizontal Process Flow Pipeline Diagram (Draw.io from Mermaid flowchart LR)
      - 3-Card Security & Throughput Metric Callout Row
      - Framed Zero-Trust Visual Asset & Policy Checklist
    """
    slide = add_slide_with_background(prs)
    add_slide_header(
        slide=slide,
        tracker="Data Platform & Cyber Resilience  |  Zero-Trust Ingestion Engine",
        action_title="End-to-End Cryptographic Attestation Guarantees Sub-45ms Real-Time Ingestion",
        subtitle="Continuous mTLS validation, automated policy enforcement, and distributed lakehouse analytics streaming 1.2B events/day.",
    )

    # -------------------------------------------------------------------------
    # Top Section: Horizontal Process Pipeline Diagram (Y=1.72", Height=2.65")
    # -------------------------------------------------------------------------
    pipe_x = Inches(0.8)
    pipe_y = Inches(1.72)
    pipe_w = Inches(11.733)
    pipe_h = Inches(2.65)

    add_card(slide, pipe_x, pipe_y, pipe_w, pipe_h, bg_color=Palette.CARD_BG)

    # Diagram Header & Label
    tb_diag_title = slide.shapes.add_textbox(pipe_x + Inches(0.25), pipe_y + Inches(0.15), pipe_w - Inches(0.5), Inches(0.35))
    tf_dt = tb_diag_title.text_frame
    tf_dt.margin_left = tf_dt.margin_right = tf_dt.margin_top = tf_dt.margin_bottom = 0
    p_dt = tf_dt.paragraphs[0]
    p_dt.text = "REAL-TIME ZERO-TRUST DATA INGESTION PIPELINE (HORIZONTAL DRAW.IO FLOW)"
    p_dt.font.size = Pt(10)
    p_dt.font.bold = True
    p_dt.font.color.rgb = Palette.BRAND_BLUE

    # Draw.io Horizontal Pipeline PNG
    pipeline_img_path = assets_map["diag_pipeline_png"]
    slide.shapes.add_picture(
        str(pipeline_img_path),
        pipe_x + Inches(0.20),
        pipe_y + Inches(0.48),
        width=pipe_w - Inches(0.40),
        height=pipe_h - Inches(0.60),
    )

    # -------------------------------------------------------------------------
    # Bottom Section: 3-Card Metric & Verification Framework Row (Y=4.52", Height=2.38")
    # -------------------------------------------------------------------------
    row2_y = Inches(4.52)
    row2_h = Inches(2.38)
    col_w = Inches(3.72)
    col_gap = Inches(0.28)

    cards_data = [
        {
            "icon": assets_map["icon_lock"],
            "tag": "SECURITY & ATTESTATION",
            "metric": "100% mTLS",
            "title": "Strict Zero-Trust Perimeter",
            "bullets": [
                "Ephemeral SPIFFE/SPIRE identity tokens",
                "Automated cert rotation every 24 hours",
                "Zero open inbound management ports",
            ],
            "accent": Palette.BRAND_BLUE,
        },
        {
            "icon": assets_map["icon_activity"],
            "tag": "STREAM PERFORMANCE",
            "metric": "< 45ms",
            "title": "Sub-Second Ingestion P99",
            "bullets": [
                "Kafka distributed partition streaming",
                "Backpressure self-throttling buffer",
                "Sub-10ms schema validation engine",
            ],
            "accent": Palette.BRAND_TEAL,
        },
        {
            "icon": assets_map["icon_server"],
            "tag": "LAKEHOUSE SCALE",
            "metric": "1.2B Evts/Day",
            "title": "Elastic Analytical Storage",
            "bullets": [
                "Columnar Parquet tiered cold storage",
                "Real-time vector index embedding",
                "Zero data loss with triple replication",
            ],
            "accent": Palette.BRAND_CYAN,
        },
    ]

    for i, cdata in enumerate(cards_data):
        cx = Inches(0.8) + i * (col_w + col_gap)
        add_card(slide, cx, row2_y, col_w, row2_h, bg_color=Palette.CARD_BG, has_top_stripe=True)

        # Top Accent Stripe
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, row2_y, col_w, Inches(0.08))
        stripe.shadow.inherit = False
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = cdata["accent"]
        stripe.line.fill.background()

        # Icon
        slide.shapes.add_picture(
            str(cdata["icon"]),
            cx + Inches(0.18),
            row2_y + Inches(0.18),
            width=Inches(0.55),
            height=Inches(0.55),
        )

        # Content Box
        cb = slide.shapes.add_textbox(
            cx + Inches(0.85),
            row2_y + Inches(0.15),
            col_w - Inches(0.95),
            row2_h - Inches(0.25),
        )
        c_tf = cb.text_frame
        c_tf.word_wrap = True
        c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0

        # Metric & Tag
        p_top = c_tf.paragraphs[0]
        p_top.text = f"{cdata['metric']}  |  {cdata['tag']}"
        p_top.font.size = Pt(9)
        p_top.font.bold = True
        p_top.font.color.rgb = cdata["accent"]

        p_t = c_tf.add_paragraph()
        p_t.text = cdata["title"]
        p_t.font.size = Pt(11.5)
        p_t.font.bold = True
        p_t.font.color.rgb = Palette.TEXT_PRIMARY
        p_t.space_before = Pt(2)
        p_t.space_after = Pt(4)

        for b in cdata["bullets"]:
            p_b = c_tf.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.size = Pt(8.8)
            p_b.font.color.rgb = Palette.TEXT_SECONDARY
            p_b.space_after = Pt(2)

    add_slide_footer(slide, current_idx=2, total_slides=3)


# ============================================================================
# 5. Slide 3 Builder: Milestone Delivery & Q3 Operational Roadmap
# ============================================================================

def build_slide_3(prs: Presentation, assets_map: Dict[str, Path]) -> None:
    """
    Slide 3: Milestone Delivery & Q3 Operational Roadmap
    Features:
      - Draw.io State / Milestone Progression Diagram (from Mermaid flowchart LR)
      - 3 Structured Roadmap Cards with Status Badges and Tinted Icons
      - Operational Readiness & Governance Framework
    """
    slide = add_slide_with_background(prs)
    add_slide_header(
        slide=slide,
        tracker="Program Execution & Governance  |  Q3 Operational Roadmap",
        action_title="Gated Multi-Phase Rollout Concludes Global Cloud Migration in Q3",
        subtitle="Rigorous security gates, telemetry validation, and blue-green production cutovers ensuring zero service disruption.",
    )

    # -------------------------------------------------------------------------
    # Top Section: State & Milestone Transition Diagram (Y=1.72", Height=1.70")
    # -------------------------------------------------------------------------
    milestone_x = Inches(0.8)
    milestone_y = Inches(1.72)
    milestone_w = Inches(11.733)
    milestone_h = Inches(1.70)

    add_card(slide, milestone_x, milestone_y, milestone_w, milestone_h, bg_color=Palette.CARD_BG)

    # Header text
    m_tb = slide.shapes.add_textbox(milestone_x + Inches(0.25), milestone_y + Inches(0.12), milestone_w - Inches(0.5), Inches(0.28))
    m_tf = m_tb.text_frame
    m_tf.margin_left = m_tf.margin_right = m_tf.margin_top = m_tf.margin_bottom = 0
    p_mh = m_tf.paragraphs[0]
    p_mh.text = "PHASED STATE TRANSITION & GOVERNANCE GATES (DRAW.IO COMPILED)"
    p_mh.font.size = Pt(9.5)
    p_mh.font.bold = True
    p_mh.font.color.rgb = Palette.BRAND_BLUE

    # Draw.io State Diagram PNG
    state_img_path = assets_map["diag_state_png"]
    slide.shapes.add_picture(
        str(state_img_path),
        milestone_x + Inches(0.20),
        milestone_y + Inches(0.40),
        width=milestone_w - Inches(0.40),
        height=milestone_h - Inches(0.50),
    )

    # -------------------------------------------------------------------------
    # Bottom Section: 3 Structured Roadmap Phase Cards (Y=3.58", Height=3.32")
    # -------------------------------------------------------------------------
    row2_y = Inches(3.58)
    row2_h = Inches(3.32)
    card_w = Inches(3.72)
    card_gap = Inches(0.28)

    phases = [
        {
            "phase": "PHASE 01  |  Q1-Q2",
            "status": "COMPLETED",
            "status_bg": Palette.BADGE_GREEN_FILL,
            "status_color": Palette.SUCCESS_GREEN,
            "icon": assets_map["icon_check"],
            "title": "Foundation & Core Mesh",
            "summary": "Multi-region VPC provisioning and identity federations.",
            "deliverables": [
                "Terraform IaC multi-region baseline",
                "SPIFFE/SPIRE zero-trust auth cluster",
                "Automated CI/CD security scanning gates",
                "Dual-write database CDC pipelines live",
            ],
            "accent": Palette.SUCCESS_GREEN,
        },
        {
            "phase": "PHASE 02  |  Q2-Q3",
            "status": "IN PROGRESS",
            "status_bg": Palette.BADGE_BLUE_FILL,
            "status_color": Palette.BRAND_BLUE,
            "icon": assets_map["icon_refresh"],
            "title": "Microservices Migration",
            "summary": "Decoupling tier-1 monolithic services into K8s mesh.",
            "deliverables": [
                "Canary routing via Envoy API gateway",
                "Distributed OpenTelemetry tracing mesh",
                "Automated disaster recovery drills (RTO < 60s)",
                "Sub-50ms streaming pipeline certification",
            ],
            "accent": Palette.BRAND_BLUE,
        },
        {
            "phase": "PHASE 03  |  Q3-Q4",
            "status": "UPCOMING",
            "status_bg": Palette.BADGE_AMBER_FILL,
            "status_color": Palette.WARNING_AMBER,
            "icon": assets_map["icon_flag"],
            "title": "Global GA & Cutover",
            "summary": "Complete legacy decommission & 100% production traffic.",
            "deliverables": [
                "Final DNS blue-green global traffic swing",
                "Legacy on-prem hardware deprecation",
                "SOC-2 Type II and ISO 27001 audit sign-off",
                "Enterprise 24/7 SRE NOC handover",
            ],
            "accent": Palette.WARNING_AMBER,
        },
    ]

    for i, phase in enumerate(phases):
        cx = Inches(0.8) + i * (card_w + card_gap)
        add_card(slide, cx, row2_y, card_w, row2_h, bg_color=Palette.CARD_BG, has_top_stripe=True)

        # Top Accent Stripe
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, row2_y, card_w, Inches(0.08))
        stripe.shadow.inherit = False
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = phase["accent"]
        stripe.line.fill.background()

        # Status Pill background
        status_pill = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            cx + card_w - Inches(1.35),
            row2_y + Inches(0.18),
            Inches(1.15),
            Inches(0.28),
        )
        status_pill.shadow.inherit = False
        status_pill.fill.solid()
        status_pill.fill.fore_color.rgb = phase["status_bg"]
        status_pill.line.color.rgb = phase["status_color"]
        status_pill.line.width = Pt(0.75)
        st_tf = status_pill.text_frame
        st_tf.margin_left = st_tf.margin_right = st_tf.margin_top = st_tf.margin_bottom = 0
        p_st = st_tf.paragraphs[0]
        p_st.text = phase["status"]
        p_st.font.size = Pt(8)
        p_st.font.bold = True
        p_st.alignment = PP_ALIGN.CENTER
        p_st.font.color.rgb = phase["status_color"]

        # Icon
        slide.shapes.add_picture(
            str(phase["icon"]),
            cx + Inches(0.20),
            row2_y + Inches(0.18),
            width=Inches(0.48),
            height=Inches(0.48),
        )

        # Header Details
        h_tb = slide.shapes.add_textbox(
            cx + Inches(0.75),
            row2_y + Inches(0.16),
            card_w - Inches(2.15),
            Inches(0.50),
        )
        h_tf = h_tb.text_frame
        h_tf.word_wrap = True
        h_tf.margin_left = h_tf.margin_right = h_tf.margin_top = h_tf.margin_bottom = 0

        p_ph = h_tf.paragraphs[0]
        p_ph.text = phase["phase"]
        p_ph.font.size = Pt(8.5)
        p_ph.font.bold = True
        p_ph.font.color.rgb = phase["accent"]

        p_pt = h_tf.add_paragraph()
        p_pt.text = phase["title"]
        p_pt.font.size = Pt(11.5)
        p_pt.font.bold = True
        p_pt.font.color.rgb = Palette.TEXT_PRIMARY

        # Summary & Deliverables Box
        deliv_tb = slide.shapes.add_textbox(
            cx + Inches(0.20),
            row2_y + Inches(0.78),
            card_w - Inches(0.40),
            row2_h - Inches(0.88),
        )
        deliv_tf = deliv_tb.text_frame
        deliv_tf.word_wrap = True
        deliv_tf.margin_left = deliv_tf.margin_right = deliv_tf.margin_top = deliv_tf.margin_bottom = 0

        p_sum = deliv_tf.paragraphs[0]
        p_sum.text = phase["summary"]
        p_sum.font.size = Pt(9)
        p_sum.font.color.rgb = Palette.TEXT_SECONDARY
        p_sum.space_after = Pt(6)

        p_del_hdr = deliv_tf.add_paragraph()
        p_del_hdr.text = "KEY DELIVERABLES:"
        p_del_hdr.font.size = Pt(8)
        p_del_hdr.font.bold = True
        p_del_hdr.font.color.rgb = Palette.TEXT_MUTED
        p_del_hdr.space_after = Pt(3)

        for d in phase["deliverables"]:
            p_d = deliv_tf.add_paragraph()
            p_d.text = f"• {d}"
            p_d.font.size = Pt(8.8)
            p_d.font.color.rgb = Palette.TEXT_PRIMARY
            p_d.space_after = Pt(2.5)

    add_slide_footer(slide, current_idx=3, total_slides=3)


# ============================================================================
# 6. Orchestration Pipeline: Generate All Assets & PPTX Presentation
# ============================================================================

def generate_demo_deck(project_name: str = "demo_deck") -> Path:
    """
    End-to-end presentation generator pipeline:
      1. Prepares sandboxed directory in project_outputs/demo_deck/.
      2. Compiles 3 Draw.io & PNG architecture diagrams from Mermaid syntax.
      3. Retrieves and tints brand vector icons.
      4. Generates procedural 3D hero cards with presentation framing.
      5. Constructs the 3-slide PPTX deck with consulting-grade positioning.
      6. Saves presentation.pptx and returns output path.
    """
    base_dir = Path.cwd()
    output_dir = base_dir / "project_outputs" / project_name
    diag_dir = output_dir / "diagrams"
    assets_dir = output_dir / "assets"

    diag_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🚀 Initializing Enterprise Demo Deck Builder...")
    print(f"📁 Target Output Directory: {output_dir}")
    print("=" * 70)

    assets_map: Dict[str, Path] = {}

    # -------------------------------------------------------------------------
    # Step 1: Generate Diagrams via diagram_engine
    # -------------------------------------------------------------------------
    print("\n[1/4] Compiling Draw.io Architecture Diagrams from Mermaid...")
    diag_engine = DiagramEngine(workspace_root=base_dir)

    # Diagram 1: System Cloud Architecture
    mermaid_arch = """
    flowchart LR
        subgraph Ingress ["Edge & Ingress Layer"]
            DNS[Global Cloud DNS] --> WAF[Cloud Armor / WAF]
            WAF --> APIGW[Kong API Gateway]
        end

        subgraph Mesh ["Microservices Mesh (Kubernetes)"]
            APIGW --> AuthSvc[Auth & Policy Svc]
            APIGW --> CoreSvc[Core Business Engine]
            CoreSvc --> AnalyticsSvc[Analytics Stream Svc]
        end

        subgraph Persistence ["Data & Event Persistence"]
            CoreSvc --> DB[(Multi-Region PostgreSQL)]
            AnalyticsSvc --> Kafka[Event Stream Kafka]
            AnalyticsSvc --> Lakehouse[(Vector Lakehouse)]
        end
    """
    res_arch = diag_engine.compile(
        mermaid_code=mermaid_arch,
        project_name=project_name,
        diagram_name="architecture_system_topology",
        theme="corporate_navy",
        scale=3.0,
    )
    assets_map["diag_arch_drawio"] = res_arch["drawio"]
    assets_map["diag_arch_png"] = res_arch["png"]
    print(f"  ✓ Slide 1 Diagram compiled: {res_arch['png'].name} & {res_arch['drawio'].name}")

    # Diagram 2: Horizontal Real-time Pipeline
    mermaid_pipeline = """
    flowchart LR
        Edge[Edge Sensors & Apps] --> Ingest[Kafka Ingestion Hub]
        Ingest --> ZeroTrust[Zero-Trust Policy Engine]
        ZeroTrust --> Flink[Real-time Stream Engine]
        Flink --> VectorStore[(Vector Embeddings Lake)]
        Flink --> Dashboard[Real-time Exec Dashboard]
    """
    res_pipeline = diag_engine.compile(
        mermaid_code=mermaid_pipeline,
        project_name=project_name,
        diagram_name="horizontal_data_pipeline",
        theme="corporate_navy",
        scale=3.0,
    )
    assets_map["diag_pipeline_drawio"] = res_pipeline["drawio"]
    assets_map["diag_pipeline_png"] = res_pipeline["png"]
    print(f"  ✓ Slide 2 Diagram compiled: {res_pipeline['png'].name} & {res_pipeline['drawio'].name}")

    # Diagram 3: State & Milestone Transition Roadmap
    mermaid_state = """
    flowchart LR
        P1[Phase 1: Foundation Baseline] --> G1{Gate 1: Security Audit}
        G1 --> P2[Phase 2: Pilot Cluster Mesh]
        P2 --> G2{Gate 2: Perf & SLA Check}
        G2 --> P3[Phase 3: Global Production Cutover]
        P3 --> GA([GA Full Rollout Complete])
    """
    res_state = diag_engine.compile(
        mermaid_code=mermaid_state,
        project_name=project_name,
        diagram_name="state_milestone_progression",
        theme="corporate_navy",
        scale=3.0,
    )
    assets_map["diag_state_drawio"] = res_state["drawio"]
    assets_map["diag_state_png"] = res_state["png"]
    print(f"  ✓ Slide 3 Diagram compiled: {res_state['png'].name} & {res_state['drawio'].name}")

    # -------------------------------------------------------------------------
    # Step 2: Tint & Export Brand Icons via icon_engine
    # -------------------------------------------------------------------------
    print("\n[2/4] Generating Tinted Brand Icons...")
    icon_engine = IconEngine(cache_dir=assets_dir)

    icons_to_generate = [
        ("icon_shield", "lucide:shield-check", Palette.BRAND_BLUE_HEX, Palette.BADGE_BLUE_FILL),
        ("icon_zap", "lucide:zap", Palette.SUCCESS_GREEN_HEX, Palette.BADGE_GREEN_FILL),
        ("icon_trend", "lucide:trending-up", Palette.BRAND_TEAL_HEX, Palette.BADGE_BLUE_FILL),
        ("icon_lock", "lucide:lock", Palette.BRAND_BLUE_HEX, Palette.BADGE_BLUE_FILL),
        ("icon_activity", "lucide:activity", Palette.BRAND_TEAL_HEX, Palette.BADGE_GREEN_FILL),
        ("icon_server", "lucide:server", Palette.BRAND_CYAN_HEX, Palette.BADGE_BLUE_FILL),
        ("icon_check", "lucide:check-circle", Palette.SUCCESS_GREEN_HEX, Palette.BADGE_GREEN_FILL),
        ("icon_refresh", "lucide:refresh-cw", Palette.BRAND_BLUE_HEX, Palette.BADGE_BLUE_FILL),
        ("icon_flag", "lucide:flag", Palette.WARNING_AMBER_HEX, Palette.BADGE_AMBER_FILL),
    ]

    for key, identifier, brand_hex, bg_color in icons_to_generate:
        out_png = assets_dir / f"{key}.png"
        bg_hex = f"#{bg_color[0]:02X}{bg_color[1]:02X}{bg_color[2]:02X}" if isinstance(bg_color, (tuple, list, RGBColor)) else "#EFF6FF"
        icon_path = icon_engine.get_icon(
            identifier=identifier,
            color=brand_hex,
            size=256,
            output_path=out_png,
            badge_bg=bg_hex,
            badge_radius=40,
            save_svg=True,
        )
        assets_map[key] = icon_path
        print(f"  ✓ Tinted Icon: {key} ({identifier}) -> {icon_path.name}")

    # -------------------------------------------------------------------------
    # Step 3: Procedural 3D Visual Cards & Framing via image_engine
    # -------------------------------------------------------------------------
    print("\n[3/4] Generating & Framing 3D Visual Assets...")
    image_engine = ImageEngine(cache_dir=assets_dir)

    # Cloud Architecture Hero Card
    raw_cloud_card = image_engine.generate_procedural_3d_card(
        title="Enterprise Cloud Mesh",
        primary_color=Palette.BRAND_BLUE_HEX,
        accent_color=Palette.BRAND_CYAN_HEX,
        size=(1600, 900),
    )
    framed_cloud_path = assets_dir / "framed_cloud_hero.png"
    frame_slide_image(
        image_input=raw_cloud_card,
        aspect_ratio="16:9",
        corner_radius=20,
        border_width=1,
        border_color="#CBD5E1",
        shadow=True,
        output_path=framed_cloud_path,
    )
    assets_map["framed_cloud_hero"] = framed_cloud_path
    print(f"  ✓ Framed 3D Visual: {framed_cloud_path.name}")

    # -------------------------------------------------------------------------
    # Step 4: Build PPTX Presentation Deck
    # -------------------------------------------------------------------------
    print("\n[4/4] Constructing Presentation Deck with python-pptx...")
    prs = create_deck()

    print("  • Building Slide 1: Executive Architecture & Cloud Migration Strategy...")
    build_slide_1(prs, assets_map)

    print("  • Building Slide 2: Data Pipeline & Zero-Trust Verification...")
    build_slide_2(prs, assets_map)

    print("  • Building Slide 3: Milestone Delivery & Q3 Operational Roadmap...")
    build_slide_3(prs, assets_map)

    pptx_output_path = output_dir / "presentation.pptx"
    prs.save(str(pptx_output_path))
    print(f"\n✨ Successfully created presentation: {pptx_output_path}")

    return pptx_output_path


if __name__ == "__main__":
    generate_demo_deck()
