"""
Consulting Slide Archetypes Subsystem
=====================================
Implements structured, executive-grade slide builders inspired by top
management consulting frameworks (BCG, McKinsey, Bain):

  1. BCG 3-Horizon Growth / Modernization Framework:
     - Horizon 1 (Core Business / Defend & Extend)
     - Horizon 2 (Emerging Engines / Scale High-Growth)
     - Horizon 3 (Transformational / Future Strategic Options)

  2. McKinsey MECE Hypothesis / Strategy Cascade:
     - Top Executive Problem Statement & Core Hypothesis Anchor
     - Mutually Exclusive, Collectively Exhaustive (MECE) Strategic Pillars
     - Actionable Proof Points, Validation Metrics & Decision Levers

  3. Executive Balanced Scorecard / KPI Matrix:
     - 4-Quadrant Executive Matrix (Financial, Customer, Operational, Growth/Resilience)
     - Large KPI typography, performance status badges, tinted visual accents

All archetypes strictly adhere to active `Theme` definitions (colors, corner radius,
typography scales, border weights, zero-margin text frames).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb


# ============================================================================
# 1. Slide Geometry & Core Primitive Helpers
# ============================================================================

def create_presentation(theme: Optional[Theme] = None) -> Presentation:
    """Initialize a standard 16:9 widescreen presentation deck."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_slide_with_background(prs: Presentation, theme: Theme) -> Any:
    """Create a blank slide with theme-defined canvas background fill."""
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
    bg.shadow.inherit = False
    bg.fill.solid()
    bg.fill.fore_color.rgb = theme.get_rgb("background")
    bg.line.fill.background()
    return slide


def add_slide_header(
    slide: Any,
    theme: Theme,
    tracker: str,
    action_title: str,
    subtitle: Optional[str] = None,
    tracker_color: Optional[RGBColor] = None,
) -> None:
    """Renders structured consulting header: Category Tracker, Action Headline, Subtitle."""
    thresholds = theme.typography_thresholds
    tracker_rgb = tracker_color or theme.get_rgb("accent")

    # 1. Tracker Breadcrumb
    tb_tr = slide.shapes.add_textbox(Inches(0.8), Inches(0.40), Inches(11.733), Inches(0.26))
    tf_tr = tb_tr.text_frame
    tf_tr.word_wrap = True
    tf_tr.margin_left = tf_tr.margin_right = tf_tr.margin_top = tf_tr.margin_bottom = 0
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = tracker.upper()
    p_tr.font.name = theme.font_family_header
    p_tr.font.size = Pt(thresholds.get("tracker_pt", 9.5))
    p_tr.font.bold = True
    p_tr.font.color.rgb = tracker_rgb

    # 2. Action Headline & Context Subtitle (Unified Text Frame for Consistent Spacing)
    tb_header = slide.shapes.add_textbox(Inches(0.8), Inches(0.66), Inches(11.733), Inches(0.95))
    tf_h = tb_header.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0

    p_t = tf_h.paragraphs[0]
    p_t.text = action_title
    p_t.font.name = theme.font_family_header
    base_title_pt = thresholds.get("action_title_pt", 18.0)
    if len(action_title) > 60:
        base_title_pt = min(base_title_pt, 16.5)
    p_t.font.size = Pt(base_title_pt)
    p_t.font.bold = True
    p_t.font.color.rgb = theme.get_rgb("primary")

    # 3. Context Subtitle (Flowed via paragraph offset to ensure consistent spacing at all times)
    if subtitle:
        p_s = tf_h.add_paragraph()
        p_s.text = subtitle
        p_s.font.name = theme.font_family
        p_s.font.size = Pt(thresholds.get("subtitle_pt", 11.0))
        p_s.font.color.rgb = theme.get_rgb("secondary")
        p_s.space_before = Pt(10)


def add_card(
    slide: Any,
    theme: Theme,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    bg_color: Optional[RGBColor] = None,
    border_color: Optional[RGBColor] = None,
    border_width_pt: Optional[float] = None,
    has_top_stripe: bool = False,
    force_rectangle: bool = False,
) -> Any:
    """
    Draws a card container respecting theme corner radius and borders.

    GEOMETRY INTEGRITY RULE:
    A card container that features a top accent line, stripe, or header bar
    MUST NEVER have rounded corners at the top. Overlapping a straight line across
    rounded corners creates severe geometric collision and visual defect.
    When has_top_stripe=True or force_rectangle=True, MSO_SHAPE.RECTANGLE is strictly enforced.
    """
    if has_top_stripe or force_rectangle or theme.corner_radius <= 0:
        shape_type = MSO_SHAPE.RECTANGLE
    else:
        shape_type = MSO_SHAPE.ROUNDED_RECTANGLE

    card = slide.shapes.add_shape(shape_type, left, top, width, height)
    card.shadow.inherit = False

    card.fill.solid()
    card.fill.fore_color.rgb = bg_color or theme.get_rgb("surface")

    b_color = border_color or theme.get_rgb("border")
    if b_color:
        card.line.color.rgb = b_color
        card.line.width = Pt(border_width_pt or theme.card_border_width_pt)
    else:
        card.line.fill.background()

    return card


def add_card_with_top_stripe(
    slide: Any,
    theme: Theme,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    accent_rgb: RGBColor,
    bg_color: Optional[RGBColor] = None,
    border_color: Optional[RGBColor] = None,
    border_width_pt: Optional[float] = None,
    stripe_height_in: Optional[float] = None,
) -> Tuple[Any, Any]:
    """
    Draws a card container with an integrated flush top accent stripe.
    Guarantees strict geometric alignment: both card container and stripe are sharp
    rectangles (MSO_SHAPE.RECTANGLE) with zero rounded top corner artifacts.
    """
    card = add_card(
        slide,
        theme,
        left,
        top,
        width,
        height,
        bg_color=bg_color,
        border_color=border_color,
        border_width_pt=border_width_pt,
        has_top_stripe=True,
    )
    st_h = Inches(stripe_height_in or theme.accent_stripe_height_in)
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, st_h)
    stripe.shadow.inherit = False
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = accent_rgb
    stripe.line.fill.background()
    return card, stripe


def add_slide_footer(
    slide: Any,
    theme: Theme,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> None:
    """Renders bottom divider line, confidentiality notice, and slide pagination."""
    thresholds = theme.typography_thresholds

    # Divider line
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.8),
        Inches(7.05),
        Inches(11.733),
        Inches(0.015),
    )
    divider.shadow.inherit = False
    divider.fill.solid()
    divider.fill.fore_color.rgb = theme.get_rgb("border")
    divider.line.fill.background()

    # Notice text
    tb_n = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(8.0), Inches(0.25))
    tf_n = tb_n.text_frame
    tf_n.margin_left = tf_n.margin_right = tf_n.margin_top = tf_n.margin_bottom = 0
    p_n = tf_n.paragraphs[0]
    p_n.text = notice
    p_n.font.name = theme.font_family
    p_n.font.size = Pt(thresholds.get("caption_pt", 8.5))
    p_n.font.color.rgb = theme.get_rgb("muted")

    # Slide number
    tb_p = slide.shapes.add_textbox(Inches(10.533), Inches(7.12), Inches(2.0), Inches(0.25))
    tf_p = tb_p.text_frame
    tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0
    p_p = tf_p.paragraphs[0]
    p_p.text = f"{current_idx:02d} / {total_slides:02d}"
    p_p.font.name = theme.font_family
    p_p.font.size = Pt(thresholds.get("caption_pt", 8.5))
    p_p.font.bold = True
    p_p.alignment = PP_ALIGN.RIGHT
    p_p.font.color.rgb = theme.get_rgb("muted")


# ============================================================================
# 2. Archetype 1: BCG 3-Horizon Growth / Modernization Framework
# ============================================================================

@dataclass
class HorizonColumnData:
    """Content definition for a single Horizon column in BCG 3-Horizon model."""
    horizon_tag: str            # e.g. "HORIZON 1  |  0-12 MONTHS"
    title: str                  # e.g. "Protect & Extend Core"
    strategic_focus: str        # e.g. "Immediate Cash Flow & Operational Efficiency"
    metric_highlight: str       # e.g. "+18% Core EBITDA"
    metric_label: str           # e.g. "Near-term target efficiency"
    initiatives: List[str]      # Bullet points of key projects/actions
    accent_key: str = "accent"  # Theme palette key for highlight color
    status_tag: str = "IN EXECUTION"  # e.g. "ACTIVE", "IN DESIGN", "DISCOVERY"
    status_bg_key: str = "badge_blue_fill"
    status_text_key: str = "badge_blue_text"
    icon_path: Optional[Union[str, Path]] = None


def build_bcg_3_horizon_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "Growth Strategy & Portfolio Architecture  |  BCG 3-Horizon Framework",
    action_title: str = "Balanced Portfolio Allocation Fuels Core Modernization while Incubating Future Engines",
    subtitle: Optional[str] = "Phased sequencing balances near-term cash generation with disruptive 3-5 year platform bets.",
    horizons: Optional[List[HorizonColumnData]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
) -> Any:
    """
    Builds a BCG 3-Horizon Growth / Modernization Slide.
    Divides the content area into 3 structured horizon columns with metrics,
    initiatives, and status badges.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    thresholds = theme.typography_thresholds

    if not horizons:
        # Default BCG 3-Horizon Dataset
        horizons = [
            HorizonColumnData(
                horizon_tag="HORIZON 1  |  0-12 MONTHS",
                title="Core Modernization",
                strategic_focus="Defend market leadership, optimize margins & reduce legacy debt.",
                metric_highlight="+18% Margin",
                metric_label="Immediate Core EBITDA expansion",
                initiatives=[
                    "Automate manual business operational workflows",
                    "Migrate monolithic database to managed cloud cluster",
                    "Decommission redundant on-prem licensing footprint",
                    "Establish continuous compliance governance baseline",
                ],
                accent_key="accent",
                status_tag="IN EXECUTION",
                status_bg_key="badge_blue_fill",
                status_text_key="badge_blue_text",
            ),
            HorizonColumnData(
                horizon_tag="HORIZON 2  |  1-3 YEARS",
                title="Emerging Growth Engines",
                strategic_focus="Scale high-growth digital channels, API ecosystem & partnerships.",
                metric_highlight="3.5x ARR Growth",
                metric_label="Next-gen service stream revenue",
                initiatives=[
                    "Launch modular B2B developer API marketplace",
                    "Roll out real-time streaming analytics platform",
                    "Implement multi-region active-active cloud mesh",
                    "Expand into high-margin adjacent enterprise verticals",
                ],
                accent_key="accent_teal",
                status_tag="SCALING",
                status_bg_key="badge_green_fill",
                status_text_key="badge_green_text",
            ),
            HorizonColumnData(
                horizon_tag="HORIZON 3  |  3-5 YEARS",
                title="Transformational Options",
                strategic_focus="Incubate disruptive AI agents, autonomous platforms & new markets.",
                metric_highlight="10x TAM Expansion",
                metric_label="Long-term market creation potential",
                initiatives=[
                    "Pilot autonomous decision-intelligence agent mesh",
                    "Explore decentralized identity and privacy compute",
                    "Venture partnerships & M&A capability tuck-ins",
                    "Pioneer zero-marginal-cost delivery infrastructure",
                ],
                accent_key="warning",
                status_tag="INCUBATION",
                status_bg_key="badge_amber_fill",
                status_text_key="badge_amber_text",
            ),
        ]

    # Layout Coordinates
    start_x = Inches(0.8)
    row_y = Inches(1.72)
    card_w = Inches(3.72)
    card_gap = Inches(0.28)
    card_h = Inches(5.15)

    for i, h_data in enumerate(horizons[:3]):
        cx = start_x + i * (card_w + card_gap)
        accent_rgb = theme.get_rgb(h_data.accent_key)

        # 1. Main Background Card & 2. Top Accent Stripe (Strict Geometry Rule: NEVER rounded corners at top)
        add_card_with_top_stripe(
            slide,
            theme,
            cx,
            row_y,
            card_w,
            card_h,
            accent_rgb=accent_rgb,
            bg_color=theme.get_rgb("surface"),
        )

        # 3. Status Badge (Pill)
        status_w = Inches(1.20)
        status_h = Inches(0.26)
        status_x = cx + card_w - status_w - Inches(0.20)
        status_y = row_y + Inches(0.18)

        status_shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE
        status_pill = slide.shapes.add_shape(status_shape_type, status_x, status_y, status_w, status_h)
        status_pill.shadow.inherit = False
        status_pill.fill.solid()
        status_pill.fill.fore_color.rgb = theme.get_rgb(h_data.status_bg_key)
        status_pill.line.color.rgb = theme.get_rgb(h_data.status_text_key)
        status_pill.line.width = Pt(0.75)

        st_tf = status_pill.text_frame
        st_tf.margin_left = st_tf.margin_right = st_tf.margin_top = st_tf.margin_bottom = 0
        p_st = st_tf.paragraphs[0]
        p_st.text = h_data.status_tag
        p_st.font.name = theme.font_family_header
        p_st.font.size = Pt(thresholds.get("badge_pt", 8.0))
        p_st.font.bold = True
        p_st.alignment = PP_ALIGN.CENTER
        p_st.font.color.rgb = theme.get_rgb(h_data.status_text_key)

        # 4. Column Header: Horizon Tag & Title
        icon_offset_x = Inches(0.0)
        if h_data.icon_path and Path(h_data.icon_path).exists():
            slide.shapes.add_picture(
                str(h_data.icon_path),
                cx + Inches(0.20),
                row_y + Inches(0.16),
                width=Inches(0.36),
                height=Inches(0.36),
            )
            icon_offset_x = Inches(0.44)

        # Tag line (sits between icon and status pill)
        tag_tb = slide.shapes.add_textbox(cx + Inches(0.20) + icon_offset_x, row_y + Inches(0.18), card_w - status_w - Inches(0.45) - icon_offset_x, Inches(0.28))
        tag_tf = tag_tb.text_frame
        tag_tf.word_wrap = True
        tag_tf.margin_left = tag_tf.margin_right = tag_tf.margin_top = tag_tf.margin_bottom = 0
        p_tag = tag_tf.paragraphs[0]
        p_tag.text = h_data.horizon_tag
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(thresholds.get("tracker_pt", 8.5))
        p_tag.font.bold = True
        p_tag.font.color.rgb = accent_rgb

        # Title line (spans full card width below status row)
        title_tb = slide.shapes.add_textbox(cx + Inches(0.20), row_y + Inches(0.56), card_w - Inches(0.40), Inches(0.44))
        title_tf = title_tb.text_frame
        title_tf.word_wrap = True
        title_tf.margin_left = title_tf.margin_right = title_tf.margin_top = title_tf.margin_bottom = 0
        p_title = title_tf.paragraphs[0]
        p_title.text = h_data.title
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(thresholds.get("card_title_pt", 12.0))
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")

        # 5. Metric Highlight Callout Container
        metric_box_y = row_y + Inches(1.08)
        metric_box_h = Inches(0.88)
        m_card = add_card(
            slide,
            theme,
            cx + Inches(0.20),
            metric_box_y,
            card_w - Inches(0.40),
            metric_box_h,
            bg_color=theme.get_rgb("surface_muted"),
            border_color=theme.get_rgb("border"),
            border_width_pt=0.75,
        )

        m_tb = slide.shapes.add_textbox(cx + Inches(0.32), metric_box_y + Inches(0.12), card_w - Inches(0.64), metric_box_h - Inches(0.20))
        m_tf = m_tb.text_frame
        m_tf.word_wrap = True
        m_tf.margin_left = m_tf.margin_right = m_tf.margin_top = m_tf.margin_bottom = 0

        p_mval = m_tf.paragraphs[0]
        p_mval.text = h_data.metric_highlight
        p_mval.font.name = theme.font_family_header
        p_mval.font.size = Pt(thresholds.get("metric_large_pt", 20.0))
        p_mval.font.bold = True
        p_mval.font.color.rgb = accent_rgb

        p_mlbl = m_tf.add_paragraph()
        p_mlbl.text = h_data.metric_label
        p_mlbl.font.name = theme.font_family
        p_mlbl.font.size = Pt(thresholds.get("caption_pt", 8.5))
        p_mlbl.font.color.rgb = theme.get_rgb("secondary")
        p_mlbl.space_before = Pt(1)

        # 6. Strategic Focus Description
        f_tb = slide.shapes.add_textbox(cx + Inches(0.22), row_y + Inches(2.05), card_w - Inches(0.44), Inches(0.60))
        f_tf = f_tb.text_frame
        f_tf.word_wrap = True
        f_tf.margin_left = f_tf.margin_right = f_tf.margin_top = f_tf.margin_bottom = 0

        p_f = f_tf.paragraphs[0]
        p_f.text = h_data.strategic_focus
        p_f.font.name = theme.font_family
        p_f.font.size = Pt(thresholds.get("body_pt", 9.5))
        p_f.font.color.rgb = theme.get_rgb("secondary")

        # 7. Initiatives Section
        i_tb = slide.shapes.add_textbox(cx + Inches(0.22), row_y + Inches(2.75), card_w - Inches(0.44), card_h - Inches(2.85))
        i_tf = i_tb.text_frame
        i_tf.word_wrap = True
        i_tf.margin_left = i_tf.margin_right = i_tf.margin_top = i_tf.margin_bottom = 0

        p_ih = i_tf.paragraphs[0]
        p_ih.text = "KEY STRATEGIC DELIVERABLES:"
        p_ih.font.name = theme.font_family_header
        p_ih.font.size = Pt(thresholds.get("caption_pt", 8.0))
        p_ih.font.bold = True
        p_ih.font.color.rgb = theme.get_rgb("muted")
        p_ih.space_after = Pt(4)

        for init_item in h_data.initiatives:
            p_bullet = i_tf.add_paragraph()
            p_bullet.text = f"• {init_item}"
            p_bullet.font.name = theme.font_family
            p_bullet.font.size = Pt(thresholds.get("bullet_pt", 9.0))
            p_bullet.font.color.rgb = theme.get_rgb("primary")
            p_bullet.space_after = Pt(3.5)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)
    return slide


# ============================================================================
# 3. Archetype 2: McKinsey MECE Hypothesis / Strategy Cascade
# ============================================================================

@dataclass
class StrategyPillarData:
    """Definition for a single MECE Pillar in the McKinsey Strategy Cascade."""
    pillar_number: str          # e.g. "PILLAR 01"
    title: str                  # e.g. "Architectural Decoupling"
    target_kpi: str             # e.g. "Target: 4.2x Deployment Velocity"
    proof_points: List[Tuple[str, str]]  # List of (Key Lever, Supporting Evidence / Target)
    accent_key: str = "accent"
    icon_path: Optional[Union[str, Path]] = None


def build_mckinsey_cascade_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "Corporate Transformation & Strategy Cascade  |  McKinsey MECE Model",
    action_title: str = "Structured Hypothesis Cascade Unlocks $42M in Sustainable Operational Alpha",
    subtitle: Optional[str] = "Three mutually exclusive strategic pillars resolve core platform constraints and optimize cost-to-serve.",
    hypothesis_statement: str = "CORE HYPOTHESIS: By decoupling tier-1 core applications into autonomous cloud microservices and instituting zero-trust attestation, the enterprise can lower infrastructure TCO by 35% while multiplying deployment frequency by 4x.",
    pillars: Optional[List[StrategyPillarData]] = None,
    synthesis_conclusion: Optional[str] = "STRATEGIC IMPLICATION: Direct capital expenditure into automated pipeline governance to validate H1 cost savings before executing legacy hardware decommissioning.",
    current_idx: int = 1,
    total_slides: int = 1,
) -> Any:
    """
    Builds a McKinsey MECE Hypothesis / Strategy Cascade Slide.
    Structure: Top Hypothesis Anchor Box -> 3 Vertical MECE Pillar Cards -> Bottom Synthesis Banner.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    thresholds = theme.typography_thresholds

    if not pillars:
        pillars = [
            StrategyPillarData(
                pillar_number="PILLAR 01",
                title="Monolith Decoupling",
                target_kpi="SLA: 99.999% Reliability",
                proof_points=[
                    ("Micro-Mesh Routing", "Traffic canary shifting isolates blast radius and eliminates maintenance windows."),
                    ("Data Partitioning", "Distributed CQRS pattern removes cross-database transactional lockups."),
                    ("Auto-Healing Nodes", "Cluster self-recovery reduces critical incident MTTR below 60 seconds."),
                ],
                accent_key="accent",
            ),
            StrategyPillarData(
                pillar_number="PILLAR 02",
                title="Zero-Trust Pipeline",
                target_kpi="Attestation: Sub-45ms P99",
                proof_points=[
                    ("SPIFFE/SPIRE Identity", "Automated cryptographic identity issuance for all intra-service RPCs."),
                    ("Continuous Validation", "Inline policy engine blocks unverified schema changes before deployment."),
                    ("Immutable Audit Logs", "Tamper-proof event journal satisfies strict Tier-1 banking compliance."),
                ],
                accent_key="accent_teal",
            ),
            StrategyPillarData(
                pillar_number="PILLAR 03",
                title="Value & FinOps Governance",
                target_kpi="TCO Reduction: -35%",
                proof_points=[
                    ("Elastic Autoscale", "Workload bin-packing slashes idle compute allocations during off-peak hours."),
                    ("Tiered Lakehouse Storage", "Cold historical telemetry compressed into ultra-low-cost object stores."),
                    ("Unit Cost Transparency", "Real-time cost telemetry mapped directly to product business lines."),
                ],
                accent_key="success",
            ),
        ]

    # 1. Top Hypothesis Anchor Card (Y=1.70", Height=0.85")
    hypo_y = Inches(1.70)
    hypo_h = Inches(0.85)
    hypo_w = Inches(11.733)
    add_card(
        slide,
        theme,
        Inches(0.8),
        hypo_y,
        hypo_w,
        hypo_h,
        bg_color=theme.get_rgb("surface_muted"),
        border_color=theme.get_rgb("border_accent"),
    )

    hypo_tb = slide.shapes.add_textbox(Inches(1.0), hypo_y + Inches(0.12), hypo_w - Inches(0.4), hypo_h - Inches(0.20))
    hypo_tf = hypo_tb.text_frame
    hypo_tf.word_wrap = True
    hypo_tf.margin_left = hypo_tf.margin_right = hypo_tf.margin_top = hypo_tf.margin_bottom = 0

    p_hh = hypo_tf.paragraphs[0]
    p_hh.text = "EXECUTIVE PROBLEM STATEMENT & CORE HYPOTHESIS"
    p_hh.font.name = theme.font_family_header
    p_hh.font.size = Pt(thresholds.get("tracker_pt", 9.0))
    p_hh.font.bold = True
    p_hh.font.color.rgb = theme.get_rgb("accent")

    p_hb = hypo_tf.add_paragraph()
    p_hb.text = hypothesis_statement
    p_hb.font.name = theme.font_family
    p_hb.font.size = Pt(thresholds.get("body_pt", 9.8))
    p_hb.font.color.rgb = theme.get_rgb("primary")
    p_hb.space_before = Pt(2)

    # 2. Middle Row: 3 MECE Strategy Pillars (Y=2.68", Height=3.45")
    pillar_y = Inches(2.68)
    pillar_h = Inches(3.45)
    card_w = Inches(3.72)
    card_gap = Inches(0.28)
    start_x = Inches(0.8)

    for i, pillar in enumerate(pillars[:3]):
        cx = start_x + i * (card_w + card_gap)
        accent_rgb = theme.get_rgb(pillar.accent_key)

        # Card container & Top Accent Stripe (Strict Geometry Rule: NEVER rounded corners at top)
        add_card_with_top_stripe(
            slide,
            theme,
            cx,
            pillar_y,
            card_w,
            pillar_h,
            accent_rgb=accent_rgb,
            bg_color=theme.get_rgb("surface"),
        )

        # Pillar Header Box
        icon_offset_x = Inches(0.0)
        if pillar.icon_path and Path(pillar.icon_path).exists():
            slide.shapes.add_picture(
                str(pillar.icon_path),
                cx + Inches(0.20),
                pillar_y + Inches(0.18),
                width=Inches(0.42),
                height=Inches(0.42),
            )
            icon_offset_x = Inches(0.50)

        ph_tb = slide.shapes.add_textbox(cx + Inches(0.20) + icon_offset_x, pillar_y + Inches(0.16), card_w - Inches(0.40) - icon_offset_x, Inches(0.65))
        ph_tf = ph_tb.text_frame
        ph_tf.word_wrap = True
        ph_tf.margin_left = ph_tf.margin_right = ph_tf.margin_top = ph_tf.margin_bottom = 0

        p_pnum = ph_tf.paragraphs[0]
        p_pnum.text = f"{pillar.pillar_number}  |  {pillar.target_kpi}"
        p_pnum.font.name = theme.font_family_header
        p_pnum.font.size = Pt(thresholds.get("tracker_pt", 8.8))
        p_pnum.font.bold = True
        p_pnum.font.color.rgb = accent_rgb

        p_ptit = ph_tf.add_paragraph()
        p_ptit.text = pillar.title
        p_ptit.font.name = theme.font_family_header
        p_ptit.font.size = Pt(thresholds.get("card_title_pt", 11.5))
        p_ptit.font.bold = True
        p_ptit.font.color.rgb = theme.get_rgb("primary")
        p_ptit.space_before = Pt(2)

        # Proof Points List Box
        pp_tb = slide.shapes.add_textbox(cx + Inches(0.20), pillar_y + Inches(1.18), card_w - Inches(0.40), pillar_h - Inches(1.28))
        pp_tf = pp_tb.text_frame
        pp_tf.word_wrap = True
        pp_tf.margin_left = pp_tf.margin_right = pp_tf.margin_top = pp_tf.margin_bottom = 0

        p_pphdr = pp_tf.paragraphs[0]
        p_pphdr.text = "PROOF POINTS & VALIDATION LEVERS:"
        p_pphdr.font.name = theme.font_family_header
        p_pphdr.font.size = Pt(thresholds.get("caption_pt", 8.0))
        p_pphdr.font.bold = True
        p_pphdr.font.color.rgb = theme.get_rgb("muted")
        p_pphdr.space_after = Pt(4)

        for lever_title, lever_desc in pillar.proof_points:
            p_item = pp_tf.add_paragraph()
            p_item.text = f"• {lever_title}: "
            p_item.font.name = theme.font_family_header
            p_item.font.bold = True
            p_item.font.size = Pt(thresholds.get("bullet_pt", 9.0))
            p_item.font.color.rgb = accent_rgb

            run = p_item.add_run()
            run.text = lever_desc
            run.font.name = theme.font_family
            run.font.bold = False
            run.font.color.rgb = theme.get_rgb("secondary")
            p_item.space_after = Pt(3.5)

    # 3. Bottom Synthesis Banner (Y=6.25", Height=0.65")
    if synthesis_conclusion:
        synth_y = Inches(6.25)
        synth_h = Inches(0.65)
        add_card(
            slide,
            theme,
            Inches(0.8),
            synth_y,
            hypo_w,
            synth_h,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            border_width_pt=0.75,
        )

        s_tb = slide.shapes.add_textbox(Inches(1.0), synth_y + Inches(0.12), hypo_w - Inches(0.4), synth_h - Inches(0.20))
        s_tf = s_tb.text_frame
        s_tf.word_wrap = True
        s_tf.margin_left = s_tf.margin_right = s_tf.margin_top = s_tf.margin_bottom = 0

        p_s = s_tf.paragraphs[0]
        p_s.text = synthesis_conclusion
        p_s.font.name = theme.font_family
        p_s.font.size = Pt(thresholds.get("body_pt", 9.5))
        p_s.font.bold = True
        p_s.font.color.rgb = theme.get_rgb("primary")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)
    return slide


# ============================================================================
# 4. Archetype 3: Executive Balanced Scorecard / KPI Matrix
# ============================================================================

@dataclass
class ScorecardMetric:
    """Individual Metric entry within a Balanced Scorecard Quadrant."""
    label: str                  # e.g. "Multi-Region Target SLA"
    value: str                  # e.g. "99.999%"
    status: str                 # e.g. "ON TRACK", "EXCEEDED", "MONITORED", "AT RISK"
    description: str            # e.g. "Automated zone failover validated"
    status_bg_key: str = "badge_green_fill"
    status_text_key: str = "badge_green_text"


@dataclass
class ScorecardQuadrantData:
    """Definition for one quadrant in the 4-Quadrant Balanced Scorecard."""
    quadrant_title: str         # e.g. "1. FINANCIAL & COMMERCIAL"
    tagline: str                # e.g. "TCO Reduction & Capital Optimization"
    metrics: List[ScorecardMetric]
    accent_key: str = "accent"
    icon_path: Optional[Union[str, Path]] = None


def build_balanced_scorecard_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "Executive Governance & Performance  |  Balanced Scorecard",
    action_title: str = "Target Performance Exceeds Benchmark SLAs Across All Four Operational Dimensions",
    subtitle: Optional[str] = "Comprehensive KPI matrix tracking financial returns, customer value, process speed, and organizational resilience.",
    quadrants: Optional[List[ScorecardQuadrantData]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
) -> Any:
    """
    Builds an Executive Balanced Scorecard / KPI Matrix Slide (4-Quadrant 2x2 Grid).
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    thresholds = theme.typography_thresholds

    if not quadrants:
        quadrants = [
            ScorecardQuadrantData(
                quadrant_title="1. FINANCIAL & COMMERCIAL",
                tagline="Capital Optimization & TCO",
                metrics=[
                    ScorecardMetric(
                        label="Infrastructure TCO Reduction",
                        value="-35%",
                        status="ON TRACK",
                        description="Down from $12.4M baseline via autoscale.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                    ScorecardMetric(
                        label="Licensing Cost Avoidance",
                        value="$4.8M",
                        status="EXCEEDED",
                        description="Complete deprecation of legacy licenses.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                ],
                accent_key="accent",
            ),
            ScorecardQuadrantData(
                quadrant_title="2. CUSTOMER & MARKET VALUE",
                tagline="Reliability, Latency & Experience",
                metrics=[
                    ScorecardMetric(
                        label="Core API Availability SLA",
                        value="99.999%",
                        status="ON TRACK",
                        description="Zero downtime during Q2 cutover events.",
                        status_bg_key="badge_blue_fill",
                        status_text_key="badge_blue_text",
                    ),
                    ScorecardMetric(
                        label="P99 Global Request Latency",
                        value="42ms",
                        status="ON TRACK",
                        description="Sub-50ms SLA achieved across all geos.",
                        status_bg_key="badge_blue_fill",
                        status_text_key="badge_blue_text",
                    ),
                ],
                accent_key="accent_teal",
            ),
            ScorecardQuadrantData(
                quadrant_title="3. INTERNAL PROCESS EXCELLENCE",
                tagline="Velocity, Quality & Automation",
                metrics=[
                    ScorecardMetric(
                        label="Deployment Release Velocity",
                        value="4.2x",
                        status="EXCEEDED",
                        description="Blue-green automated pipelines in production.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                    ScorecardMetric(
                        label="Mean Time To Recover (MTTR)",
                        value="< 45s",
                        status="ON TRACK",
                        description="Self-healing telemetry auto-swings nodes.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                ],
                accent_key="accent_secondary",
            ),
            ScorecardQuadrantData(
                quadrant_title="4. ORGANIZATIONAL & CYBER RESILIENCE",
                tagline="Zero-Trust & Compliance Posture",
                metrics=[
                    ScorecardMetric(
                        label="Zero-Trust Mutual TLS Attestation",
                        value="100%",
                        status="ON TRACK",
                        description="SPIFFE/SPIRE federated cryptographic certs.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                    ScorecardMetric(
                        label="SOC-2 / ISO Compliance Audits",
                        value="100%",
                        status="PASSED",
                        description="Clean audit sign-off with zero findings.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                ],
                accent_key="warning",
            ),
        ]

    # Grid Dimensions (2 columns x 2 rows)
    grid_x = Inches(0.8)
    grid_y = Inches(1.68)
    quad_w = Inches(5.72)
    quad_h = Inches(2.50)
    gap_x = Inches(0.29)
    gap_y = Inches(0.18)

    positions = [
        (grid_x, grid_y),                                   # Q1: Top-Left
        (grid_x + quad_w + gap_x, grid_y),                 # Q2: Top-Right
        (grid_x, grid_y + quad_h + gap_y),                 # Q3: Bottom-Left
        (grid_x + quad_w + gap_x, grid_y + quad_h + gap_y) # Q4: Bottom-Right
    ]

    for idx, quad_data in enumerate(quadrants[:4]):
        qx, qy = positions[idx]
        accent_rgb = theme.get_rgb(quad_data.accent_key)

        # 1. Main Quadrant Card & 2. Top Accent Stripe (Strict Geometry Rule: NEVER rounded corners at top)
        add_card_with_top_stripe(
            slide,
            theme,
            qx,
            qy,
            quad_w,
            quad_h,
            accent_rgb=accent_rgb,
            bg_color=theme.get_rgb("surface"),
        )

        # 3. Optional Icon
        content_offset_x = Inches(0.20)
        if quad_data.icon_path and Path(quad_data.icon_path).exists():
            slide.shapes.add_picture(
                str(quad_data.icon_path),
                qx + Inches(0.20),
                qy + Inches(0.18),
                width=Inches(0.42),
                height=Inches(0.42),
            )
            content_offset_x = Inches(0.70)

        # 4. Quadrant Header Text
        qh_tb = slide.shapes.add_textbox(qx + content_offset_x, qy + Inches(0.14), quad_w - content_offset_x - Inches(0.20), Inches(0.45))
        qh_tf = qh_tb.text_frame
        qh_tf.word_wrap = True
        qh_tf.margin_left = qh_tf.margin_right = qh_tf.margin_top = qh_tf.margin_bottom = 0

        p_qt = qh_tf.paragraphs[0]
        p_qt.text = quad_data.quadrant_title
        p_qt.font.name = theme.font_family_header
        p_qt.font.size = Pt(thresholds.get("card_title_pt", 11.5))
        p_qt.font.bold = True
        p_qt.font.color.rgb = theme.get_rgb("primary")

        p_qtag = qh_tf.add_paragraph()
        p_qtag.text = quad_data.tagline
        p_qtag.font.name = theme.font_family
        p_qtag.font.size = Pt(thresholds.get("caption_pt", 8.5))
        p_qtag.font.color.rgb = theme.get_rgb("secondary")

        # 5. Metric Rows
        metrics_start_y = qy + Inches(0.68)
        row_h = Inches(0.80)
        row_gap = Inches(0.08)

        for m_idx, metric in enumerate(quad_data.metrics[:2]):
            my = metrics_start_y + m_idx * (row_h + row_gap)
            mw = quad_w - Inches(0.40)
            mx = qx + Inches(0.20)

            # Metric background sub-card
            add_card(
                slide,
                theme,
                mx,
                my,
                mw,
                row_h,
                bg_color=theme.get_rgb("surface_muted"),
                border_color=theme.get_rgb("border"),
                border_width_pt=0.5,
            )

            # Left Value Callout
            val_tb = slide.shapes.add_textbox(mx + Inches(0.12), my + Inches(0.10), Inches(1.50), row_h - Inches(0.20))
            val_tf = val_tb.text_frame
            val_tf.word_wrap = True
            val_tf.margin_left = val_tf.margin_right = val_tf.margin_top = val_tf.margin_bottom = 0

            p_v = val_tf.paragraphs[0]
            p_v.text = metric.value
            p_v.font.name = theme.font_family_header
            p_v.font.size = Pt(thresholds.get("metric_medium_pt", 16.0))
            p_v.font.bold = True
            p_v.font.color.rgb = accent_rgb

            # Right Label, Description & Status Badge
            desc_tb = slide.shapes.add_textbox(mx + Inches(1.55), my + Inches(0.10), mw - Inches(2.70), row_h - Inches(0.20))
            desc_tf = desc_tb.text_frame
            desc_tf.word_wrap = True
            desc_tf.margin_left = desc_tf.margin_right = desc_tf.margin_top = desc_tf.margin_bottom = 0

            p_dlbl = desc_tf.paragraphs[0]
            p_dlbl.text = metric.label
            p_dlbl.font.name = theme.font_family_header
            p_dlbl.font.size = Pt(thresholds.get("body_pt", 9.5))
            p_dlbl.font.bold = True
            p_dlbl.font.color.rgb = theme.get_rgb("primary")

            p_ddesc = desc_tf.add_paragraph()
            p_ddesc.text = metric.description
            p_ddesc.font.name = theme.font_family
            p_ddesc.font.size = Pt(thresholds.get("caption_pt", 8.2))
            p_ddesc.font.color.rgb = theme.get_rgb("secondary")
            p_ddesc.space_before = Pt(1)

            # Status Badge Pill
            badge_w = Inches(0.95)
            badge_h = Inches(0.24)
            badge_x = mx + mw - badge_w - Inches(0.12)
            badge_y = my + Inches(0.14)

            badge_shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE
            bp = slide.shapes.add_shape(badge_shape_type, badge_x, badge_y, badge_w, badge_h)
            bp.shadow.inherit = False
            bp.fill.solid()
            bp.fill.fore_color.rgb = theme.get_rgb(metric.status_bg_key)
            bp.line.color.rgb = theme.get_rgb(metric.status_text_key)
            bp.line.width = Pt(0.75)

            bp_tf = bp.text_frame
            bp_tf.margin_left = bp_tf.margin_right = bp_tf.margin_top = bp_tf.margin_bottom = 0
            p_b = bp_tf.paragraphs[0]
            p_b.text = metric.status
            p_b.font.name = theme.font_family_header
            p_b.font.size = Pt(thresholds.get("badge_pt", 7.8))
            p_b.font.bold = True
            p_b.alignment = PP_ALIGN.CENTER
            p_b.font.color.rgb = theme.get_rgb(metric.status_text_key)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)
    return slide


# ============================================================================
# 5. High-Level Consulting Archetype Deck Generator
# ============================================================================

class ConsultingDeckBuilder:
    """High-level builder for assembling full multi-slide consulting decks."""

    def __init__(self, theme: Union[str, Theme] = "default") -> None:
        if isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = theme
        self.prs = create_presentation(self.theme)

    def add_bcg_3_horizon_slide(
        self,
        tracker: str = "Growth Strategy & Modernization  |  BCG 3-Horizon Framework",
        action_title: str = "Balanced Portfolio Allocation Fuels Core Modernization while Incubating Future Engines",
        subtitle: Optional[str] = "Phased sequencing balances near-term cash generation with disruptive 3-5 year platform bets.",
        horizons: Optional[List[HorizonColumnData]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_bcg_3_horizon_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            horizons=horizons,
            current_idx=idx,
            total_slides=3,
        )

    def add_mckinsey_cascade_slide(
        self,
        tracker: str = "Corporate Transformation & Strategy Cascade  |  McKinsey MECE Model",
        action_title: str = "Structured Hypothesis Cascade Unlocks $42M in Sustainable Operational Alpha",
        subtitle: Optional[str] = "Three mutually exclusive strategic pillars resolve core platform constraints and optimize cost-to-serve.",
        hypothesis_statement: Optional[str] = None,
        pillars: Optional[List[StrategyPillarData]] = None,
        synthesis_conclusion: Optional[str] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        kwargs: Dict[str, Any] = {
            "prs": self.prs,
            "theme": self.theme,
            "tracker": tracker,
            "action_title": action_title,
            "subtitle": subtitle,
            "pillars": pillars,
            "current_idx": idx,
            "total_slides": 3,
        }
        if hypothesis_statement:
            kwargs["hypothesis_statement"] = hypothesis_statement
        if synthesis_conclusion:
            kwargs["synthesis_conclusion"] = synthesis_conclusion

        return build_mckinsey_cascade_slide(**kwargs)

    def add_balanced_scorecard_slide(
        self,
        tracker: str = "Executive Governance & Performance  |  Balanced Scorecard",
        action_title: str = "Target Performance Exceeds Benchmark SLAs Across All Four Operational Dimensions",
        subtitle: Optional[str] = "Comprehensive KPI matrix tracking financial returns, customer value, process speed, and organizational resilience.",
        quadrants: Optional[List[ScorecardQuadrantData]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_balanced_scorecard_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            quadrants=quadrants,
            current_idx=idx,
            total_slides=3,
        )

    def save(self, output_path: Union[str, Path]) -> Path:
        """Save presentation deck to the specified path."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(p))
        return p
