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

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.util import Inches, Pt
from PIL import Image

from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb, rgb_to_hex
from src.ppt_engine.icon_engine import (
    get_brand_icon,
    normalize_color,
    resolve_brand_color,
    recolor_svg,
    render_svg_to_png,
)

logger = logging.getLogger(__name__)


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
    action_title: Optional[str] = None,
    subtitle: Optional[str] = None,
    tracker_color: Optional[RGBColor] = None,
    title: Optional[str] = None,
) -> None:
    """Renders structured consulting header: Category Tracker, Action Headline, Subtitle."""
    thresholds = theme.typography_thresholds
    tracker_rgb = tracker_color or theme.get_rgb("accent")
    resolved_title = action_title or title or ""

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
    p_t.text = resolved_title
    p_t.font.name = theme.font_family_header
    base_title_pt = thresholds.get("action_title_pt", 18.0)
    if len(resolved_title) > 60:
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


def add_card_with_harmonized_icon(
    slide: Any,
    theme: Theme,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    accent_color: Union[str, RGBColor, Tuple[int, ...]],
    icon: Optional[Union[str, Path]] = None,
    icon_size_in: float = 0.36,
    icon_pos: Optional[Tuple[float, float]] = None,
    has_badge_container: bool = False,
    bg_color: Optional[RGBColor] = None,
    border_color: Optional[RGBColor] = None,
    border_width_pt: Optional[float] = None,
    stripe_height_in: Optional[float] = None,
) -> Tuple[Any, Any, Optional[Any]]:
    """
    Draws a sharp rectangular card container with an integrated flush top accent stripe
    and a dynamically tinted icon perfectly color-harmonized with the accent color.

    Guarantees:
    1. Zero geometric distortion: Card container and top stripe are sharp MSO_SHAPE.RECTANGLE.
    2. Color synchronization: Container top stripe, border/badge, and icon glyph all share
       the exact same resolved brand accent color.
    3. Graceful degradation: If icon retrieval fails or is None, returns (card, stripe, None).

    Returns:
        (card_shape, stripe_shape, icon_shape_or_badge)
    """
    # 1. Resolve accent color
    if isinstance(accent_color, RGBColor):
        accent_rgb = accent_color
        accent_hex = rgb_to_hex(accent_color)
    elif isinstance(accent_color, (tuple, list)):
        accent_rgb = RGBColor(int(accent_color[0]), int(accent_color[1]), int(accent_color[2]))
        accent_hex = normalize_color(accent_color, theme=theme)
    else:
        accent_hex = normalize_color(accent_color, theme=theme)
        try:
            accent_rgb = theme.get_rgb(accent_color)
        except Exception:
            accent_rgb = hex_to_rgb(accent_hex)

    # 2. Draw card container and top accent stripe
    card, stripe = add_card_with_top_stripe(
        slide=slide,
        theme=theme,
        left=left,
        top=top,
        width=width,
        height=height,
        accent_rgb=accent_rgb,
        bg_color=bg_color or theme.get_rgb("surface"),
        border_color=border_color or theme.get_rgb("border"),
        border_width_pt=border_width_pt,
        stripe_height_in=stripe_height_in,
    )

    if not icon:
        return card, stripe, None

    # 3. Position calculation
    dx_in, dy_in = icon_pos if icon_pos is not None else (0.20, 0.16)
    icon_left = left + Inches(dx_in)
    icon_top = top + Inches(dy_in)
    icon_dim = Inches(icon_size_in)

    # 4. Optional Badge Container behind the icon
    badge_shape = None
    if has_badge_container:
        badge_pad = Inches(0.04)
        badge_w = icon_dim + (badge_pad * 2)
        badge_h = icon_dim + (badge_pad * 2)
        badge_x = icon_left - badge_pad
        badge_y = icon_top - badge_pad
        badge_shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE,
            badge_x,
            badge_y,
            badge_w,
            badge_h,
        )
        badge_shape.shadow.inherit = False
        badge_shape.fill.solid()
        badge_shape.fill.fore_color.rgb = theme.get_rgb("surface_muted")
        badge_shape.line.color.rgb = accent_rgb
        badge_shape.line.width = Pt(1.0)

    # 5. Resolve and dynamically tint the icon
    icon_pic = None
    try:
        icon_path_to_use: Optional[Path] = None
        icon_str = str(icon).strip()

        p = Path(icon_str)
        if p.exists():
            if p.suffix.lower() == ".svg":
                from src.ppt_engine.icon_engine import _default_engine
                svg_content = p.read_text(encoding="utf-8")
                recolored_svg = recolor_svg(svg_content, accent_hex, theme=theme)
                dest_png = _default_engine.cache_dir / "custom" / f"{p.stem}_{accent_hex.lstrip('#')}.png"
                dest_png.parent.mkdir(parents=True, exist_ok=True)
                render_svg_to_png(recolored_svg, output_path=dest_png, size=512)
                icon_path_to_use = dest_png
            else:
                stem = p.stem
                if "_" in stem and ("0052CC" in stem or "2563EB" in stem):
                    clean_name = stem.split("_")[0]
                    icon_path_to_use = get_brand_icon(clean_name, brand_color=accent_hex, theme=theme)
                else:
                    icon_path_to_use = p
        else:
            clean_name = icon_str
            if "_" in clean_name and any(c.isupper() or c.isdigit() for c in clean_name):
                clean_name = clean_name.split("_")[0]
            icon_path_to_use = get_brand_icon(clean_name, brand_color=accent_hex, theme=theme)

        if icon_path_to_use and Path(icon_path_to_use).exists():
            icon_pic = slide.shapes.add_picture(
                str(icon_path_to_use),
                icon_left,
                icon_top,
                width=icon_dim,
                height=icon_dim,
            )
    except Exception as e:
        logger.warning(f"Failed to add harmonized icon '{icon}': {e}")

    return card, stripe, (icon_pic or badge_shape)


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
    icon: Optional[str] = None  # Semantic icon identifier (e.g. "shield", "zap", "star")
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
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
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
                status_tag="CORE  |  H1",
                status_bg_key="badge_blue_fill",
                status_text_key="badge_blue_text",
                icon="shield",
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
                accent_key="primary",
                status_tag="SCALE  |  H2",
                status_bg_key="badge_blue_fill",
                status_text_key="badge_blue_text",
                icon="zap",
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
                accent_key="accent_secondary",
                status_tag="FUTURE  |  H3",
                status_bg_key="badge_red_fill",
                status_text_key="badge_red_text",
                icon="star",
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

        # 3. Status Badge Pill
        status_w = Inches(1.22)
        status_h = Inches(0.24)
        status_x = cx + card_w - status_w - Inches(0.18)
        status_y = row_y + Inches(0.14)

        status_pill = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE,
            status_x,
            status_y,
            status_w,
            status_h,
        )
        status_pill.shadow.inherit = False
        status_pill.fill.solid()
        status_pill.fill.fore_color.rgb = theme.get_rgb(h_data.status_bg_key)
        status_pill.line.color.rgb = theme.get_rgb(h_data.status_text_key)
        status_pill.line.width = Pt(0.75)

        st_tf = status_pill.text_frame
        st_tf.word_wrap = False
        st_tf.margin_left = st_tf.margin_right = st_tf.margin_top = st_tf.margin_bottom = 0
        p_st = st_tf.paragraphs[0]
        p_st.text = h_data.status_tag
        p_st.font.name = theme.font_family_header
        p_st.font.size = Pt(8.0)
        p_st.font.bold = True
        p_st.alignment = PP_ALIGN.CENTER
        p_st.font.color.rgb = theme.get_rgb(h_data.status_text_key)

        # 4. Column Header: Horizon Tag & Title
        icon_to_use = h_data.icon or h_data.icon_path
        icon_offset_x = Inches(0.0)
        if icon_to_use:
            try:
                p = Path(str(icon_to_use))
                if p.exists() and p.suffix.lower() == ".png" and "_" not in p.stem:
                    icon_pic_path = p
                else:
                    stem = p.stem
                    clean_id = stem.split("_")[0] if "_" in stem else stem
                    icon_pic_path = get_brand_icon(clean_id, brand_color=accent_rgb, theme=theme)
                if icon_pic_path and Path(icon_pic_path).exists():
                    slide.shapes.add_picture(
                        str(icon_pic_path),
                        cx + Inches(0.18),
                        row_y + Inches(0.14),
                        width=Inches(0.34),
                        height=Inches(0.34),
                    )
                    icon_offset_x = Inches(0.40)
            except Exception as e:
                logger.warning(f"Failed to render horizon icon '{icon_to_use}': {e}")

        # Tag line (sits between icon and status pill, single line guaranteed)
        tag_w = card_w - status_w - Inches(0.26) - icon_offset_x
        tag_tb = slide.shapes.add_textbox(cx + Inches(0.18) + icon_offset_x, row_y + Inches(0.14), tag_w, Inches(0.26))
        tag_tf = tag_tb.text_frame
        tag_tf.word_wrap = True
        tag_tf.margin_left = tag_tf.margin_right = tag_tf.margin_top = tag_tf.margin_bottom = 0
        p_tag = tag_tf.paragraphs[0]
        p_tag.text = h_data.horizon_tag
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(9.0)
        p_tag.font.bold = True
        p_tag.font.color.rgb = accent_rgb

        # Title line (spans full card width below tag row)
        title_tb = slide.shapes.add_textbox(cx + Inches(0.18), row_y + Inches(0.48), card_w - Inches(0.36), Inches(0.48))
        title_tf = title_tb.text_frame
        title_tf.word_wrap = True
        title_tf.margin_left = title_tf.margin_right = title_tf.margin_top = title_tf.margin_bottom = 0
        p_title = title_tf.paragraphs[0]
        p_title.text = h_data.title
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(thresholds.get("card_title_pt", 13.5))
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")

        # 5. Metric Highlight Callout Container
        metric_box_y = row_y + Inches(1.02)
        metric_box_h = Inches(0.82)
        m_card = add_card(
            slide,
            theme,
            cx + Inches(0.18),
            metric_box_y,
            card_w - Inches(0.36),
            metric_box_h,
            bg_color=theme.get_rgb("surface_muted"),
            border_color=theme.get_rgb("border"),
            border_width_pt=0.75,
        )

        m_tb = slide.shapes.add_textbox(cx + Inches(0.28), metric_box_y + Inches(0.08), card_w - Inches(0.56), metric_box_h - Inches(0.16))
        m_tf = m_tb.text_frame
        m_tf.word_wrap = True
        m_tf.margin_left = m_tf.margin_right = m_tf.margin_top = m_tf.margin_bottom = 0

        p_mval = m_tf.paragraphs[0]
        p_mval.text = h_data.metric_highlight
        p_mval.font.name = theme.font_family_header
        base_metric_pt = thresholds.get("metric_large_pt", 22.0)
        if len(h_data.metric_highlight) > 12:
            base_metric_pt = 15.5
        elif len(h_data.metric_highlight) > 8:
            base_metric_pt = 18.0
        p_mval.font.size = Pt(base_metric_pt)
        p_mval.font.bold = True
        p_mval.font.color.rgb = accent_rgb

        p_mlbl = m_tf.add_paragraph()
        p_mlbl.text = h_data.metric_label
        p_mlbl.font.name = theme.font_family
        p_mlbl.font.size = Pt(thresholds.get("caption_pt", 10.5))
        p_mlbl.font.color.rgb = theme.get_rgb("secondary")
        p_mlbl.space_before = Pt(2)

        # 6. Unified Strategic Focus & Deliverables Text Frame (Zero Coordinate Collision)
        # Sequential paragraphs inside the same frame guarantees zero overlap between narrative and bullets.
        content_top = metric_box_y + metric_box_h + Inches(0.12)
        content_h = card_h - (content_top - row_y) - Inches(0.12)
        content_tb = slide.shapes.add_textbox(
            cx + Inches(0.18),
            content_top,
            card_w - Inches(0.36),
            content_h,
        )
        content_tf = content_tb.text_frame
        content_tf.word_wrap = True
        content_tf.margin_left = content_tf.margin_right = content_tf.margin_top = content_tf.margin_bottom = 0

        # Strategic Focus narrative
        p_f = content_tf.paragraphs[0]
        p_f.text = h_data.strategic_focus
        p_f.font.name = theme.font_family
        p_f.font.size = Pt(thresholds.get("body_pt", 11.0))
        p_f.font.color.rgb = theme.get_rgb("secondary")

        # Deliverables Section Header (flows naturally below narrative)
        p_ih = content_tf.add_paragraph()
        p_ih.text = "KEY STRATEGIC DELIVERABLES:"
        p_ih.font.name = theme.font_family_header
        p_ih.font.size = Pt(thresholds.get("caption_pt", 9.5))
        p_ih.font.bold = True
        p_ih.font.color.rgb = theme.get_rgb("muted")
        p_ih.space_before = Pt(8)
        p_ih.space_after = Pt(4)

        for init_item in h_data.initiatives:
            p_bullet = content_tf.add_paragraph()
            p_bullet.text = f"• {init_item}"
            p_bullet.font.name = theme.font_family
            p_bullet.font.size = Pt(thresholds.get("bullet_pt", 10.5))
            p_bullet.font.color.rgb = theme.get_rgb("primary")
            p_bullet.space_after = Pt(2.5)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
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
    icon: Optional[str] = None  # Semantic icon identifier (e.g. "layers", "shield-check", "trend-up")
    icon_path: Optional[Union[str, Path]] = None

# Backwards-compatibility alias
StrategicPillarData = StrategyPillarData


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
                icon="layers",
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
                icon="shield-check",
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
                icon="trend-up",
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

        # Pillar Header Box & Harmonized Icon
        icon_to_use = pillar.icon or pillar.icon_path
        icon_offset_x = Inches(0.0)
        if icon_to_use:
            try:
                p = Path(str(icon_to_use))
                if p.exists() and p.suffix.lower() == ".png" and "_" not in p.stem:
                    icon_pic_path = p
                else:
                    stem = p.stem
                    clean_id = stem.split("_")[0] if "_" in stem else stem
                    icon_pic_path = get_brand_icon(clean_id, brand_color=accent_rgb, theme=theme)
                if icon_pic_path and Path(icon_pic_path).exists():
                    slide.shapes.add_picture(
                        str(icon_pic_path),
                        cx + Inches(0.20),
                        pillar_y + Inches(0.18),
                        width=Inches(0.42),
                        height=Inches(0.42),
                    )
                    icon_offset_x = Inches(0.50)
            except Exception as e:
                logger.warning(f"Failed to render pillar icon '{icon_to_use}': {e}")

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
    icon: Optional[str] = None  # Semantic icon identifier (e.g. "dollar-sign", "users", "zap", "shield-check")
    icon_path: Optional[Union[str, Path]] = None

# Backwards-compatibility alias
QuadrantData = ScorecardQuadrantData


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
                icon="dollar-sign",
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
                icon="users",
                metrics=[
                    ScorecardMetric(
                        label="Core API Availability SLA",
                        value="99.999%",
                        status="ON TRACK",
                        description="Zero downtime during Q2 cutover events.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                    ScorecardMetric(
                        label="P99 Global Request Latency",
                        value="42ms",
                        status="ON TRACK",
                        description="Sub-50ms SLA achieved across all geos.",
                        status_bg_key="badge_green_fill",
                        status_text_key="badge_green_text",
                    ),
                ],
                accent_key="accent_secondary",
            ),
            ScorecardQuadrantData(
                quadrant_title="3. INTERNAL PROCESS EXCELLENCE",
                tagline="Velocity, Quality & Automation",
                icon="zap",
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
                accent_key="accent_teal",
            ),
            ScorecardQuadrantData(
                quadrant_title="4. ORGANIZATIONAL & CYBER RESILIENCE",
                tagline="Zero-Trust & Compliance Posture",
                icon="shield-check",
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
                accent_key="primary",
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

    glyph_labels = ["[ $ ]", "[ ★ ]", "[ ⚙ ]", "[ 🛡 ]"]

    for idx, quad_data in enumerate(quadrants[:4]):
        qx, qy = positions[idx]
        accent_rgb = theme.get_rgb(quad_data.accent_key)

        # 1. Main Quadrant Card, Top Accent Stripe & Harmonized Brand Icon
        semantic_defaults = ["dollar-sign", "users", "zap", "shield-check"]
        icon_to_use = quad_data.icon or quad_data.icon_path or (semantic_defaults[idx] if idx < len(semantic_defaults) else None)

        card, stripe, icon_elem = add_card_with_harmonized_icon(
            slide=slide,
            theme=theme,
            left=qx,
            top=qy,
            width=quad_w,
            height=quad_h,
            accent_color=quad_data.accent_key,
            icon=icon_to_use,
            icon_size_in=0.36,
            icon_pos=(0.20, 0.16),
            has_badge_container=True,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
        )

        content_offset_x = Inches(0.70)
        if icon_elem is None:
            # Fallback text glyph badge if icon rendering failed
            glyph_text = glyph_labels[idx] if idx < len(glyph_labels) else "[ • ]"
            icon_badge = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                qx + Inches(0.20),
                qy + Inches(0.16),
                Inches(0.44),
                Inches(0.44),
            )
            icon_badge.shadow.inherit = False
            icon_badge.fill.solid()
            icon_badge.fill.fore_color.rgb = theme.get_rgb("surface_muted")
            icon_badge.line.color.rgb = accent_rgb
            icon_badge.line.width = Pt(1.0)
            ib_tf = icon_badge.text_frame
            ib_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            ib_tf.margin_left = ib_tf.margin_right = ib_tf.margin_top = ib_tf.margin_bottom = 0
            p_ib = ib_tf.paragraphs[0]
            p_ib.text = glyph_text
            p_ib.font.name = theme.font_family_header
            p_ib.font.size = Pt(8.5)
            p_ib.font.bold = True
            p_ib.alignment = PP_ALIGN.CENTER
            p_ib.font.color.rgb = accent_rgb

        # 4. Quadrant Header Text
        qh_tb = slide.shapes.add_textbox(qx + content_offset_x, qy + Inches(0.14), quad_w - content_offset_x - Inches(0.20), Inches(0.45))
        qh_tf = qh_tb.text_frame
        qh_tf.word_wrap = True
        qh_tf.margin_left = qh_tf.margin_right = qh_tf.margin_top = qh_tf.margin_bottom = 0

        p_qt = qh_tf.paragraphs[0]
        p_qt.text = quad_data.quadrant_title
        p_qt.font.name = theme.font_family_header
        title_pt = 13.5
        if len(quad_data.quadrant_title) > 32:
            title_pt = 12.0
        p_qt.font.size = Pt(title_pt)
        p_qt.font.bold = True
        p_qt.font.color.rgb = theme.get_rgb("primary")

        p_qtag = qh_tf.add_paragraph()
        p_qtag.text = quad_data.tagline
        p_qtag.font.name = theme.font_family
        p_qtag.font.size = Pt(10.5)
        p_qtag.font.color.rgb = theme.get_rgb("secondary")

        # 5. Metric Rows
        metrics_start_y = qy + Inches(0.66)
        row_h = Inches(0.88)
        row_gap = Inches(0.04)

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

            # Left Value Callout (compact width to maximize middle description text)
            val_w = Inches(1.08)
            val_tb = slide.shapes.add_textbox(mx + Inches(0.08), my + Inches(0.04), val_w, row_h - Inches(0.08))
            val_tf = val_tb.text_frame
            val_tf.word_wrap = True
            val_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            val_tf.margin_left = val_tf.margin_right = val_tf.margin_top = val_tf.margin_bottom = 0

            p_v = val_tf.paragraphs[0]
            p_v.text = metric.value
            p_v.font.name = theme.font_family_header
            base_v_pt = 17.0
            if len(metric.value) >= 6:
                base_v_pt = 13.0
            p_v.font.size = Pt(base_v_pt)
            p_v.font.bold = True
            p_v.font.color.rgb = accent_rgb

            # Status Badge Pill (pinned to right of sub-card, vertically centered)
            badge_w = Inches(0.95)
            badge_h = Inches(0.25)
            badge_x = mx + mw - badge_w - Inches(0.10)
            badge_y = my + (row_h - badge_h) / 2

            # Right Label, Description (generous width between value and status badge)
            desc_x = mx + Inches(1.18)
            desc_w = badge_x - desc_x - Inches(0.06)
            desc_tb = slide.shapes.add_textbox(desc_x, my + Inches(0.04), desc_w, row_h - Inches(0.08))
            desc_tf = desc_tb.text_frame
            desc_tf.word_wrap = True
            desc_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            desc_tf.margin_left = desc_tf.margin_right = desc_tf.margin_top = desc_tf.margin_bottom = 0

            p_dlbl = desc_tf.paragraphs[0]
            p_dlbl.text = metric.label
            p_dlbl.font.name = theme.font_family_header
            lbl_pt = 11.0
            if len(metric.label) > 28:
                lbl_pt = 10.0
            p_dlbl.font.size = Pt(lbl_pt)
            p_dlbl.font.bold = True
            p_dlbl.font.color.rgb = theme.get_rgb("primary")

            p_ddesc = desc_tf.add_paragraph()
            p_ddesc.text = metric.description
            p_ddesc.font.name = theme.font_family
            p_ddesc.font.size = Pt(9.0)
            p_ddesc.font.color.rgb = theme.get_rgb("secondary")
            p_ddesc.space_before = Pt(2)

            # Resolve status badge color deterministically
            status_bg_key, status_text_key = theme.resolve_status_badge_keys(metric.status)

            badge_shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE
            bp = slide.shapes.add_shape(badge_shape_type, badge_x, badge_y, badge_w, badge_h)
            bp.shadow.inherit = False
            bp.fill.solid()
            bp.fill.fore_color.rgb = theme.get_rgb(status_bg_key)
            bp.line.color.rgb = theme.get_rgb(status_text_key)
            bp.line.width = Pt(0.75)

            bp_tf = bp.text_frame
            bp_tf.word_wrap = False
            bp_tf.margin_left = bp_tf.margin_right = bp_tf.margin_top = bp_tf.margin_bottom = 0
            p_b = bp_tf.paragraphs[0]
            p_b.text = metric.status
            p_b.font.name = theme.font_family_header
            p_b.font.size = Pt(9.5)
            p_b.font.bold = True
            p_b.alignment = PP_ALIGN.CENTER
            p_b.font.color.rgb = theme.get_rgb(status_text_key)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)
    return slide


# ============================================================================
# 5. Modern Chapter Divider / Section Header Archetype
# ============================================================================

def build_chapter_divider_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    hero_image_path: Optional[Union[str, Path]] = None,
    logo_path: Optional[Union[str, Path]] = None,
    action_title: Optional[str] = None,
    division_tag: Optional[str] = "BAS Division  |  Data & AI Practice",
    tagline: Optional[str] = None,
    scrim_alpha: float = 0.45,
    scrim_color: Optional[RGBColor] = None,
    tracker_color: Optional[RGBColor] = None,
    current_idx: Optional[int] = None,
    total_slides: Optional[int] = None,
    show_footer: bool = False,
) -> Any:
    """
    Builds a modern, de-squared chapter divider / section header slide.

    Layout Architecture:
      - 1/3 Left Typographic Narrative Panel (x=0.8", y=2.0", w=3.6", h=4.0"):
        Unified text box frame housing Tracker breadcrumb, high-contrast Action Title,
        and optional context Subtitle/synopsis without floating box collisions.
      - 2/3 Right Photographic Hero Panel (x=4.8", y=0.0", w=8.533", h=7.5"):
        High-res photographic plate scaled/cropped to bleed edge.
        If photo is missing, gracefully falls back to a deep primary solid container.
      - Translucent Scrim Overlay:
        OpenXML DrawingML 45% alpha dark overlay (<a:alpha val="45000"/>) over
        the photographic hero panel ensuring high-contrast readability.
      - Centered Division / Logo Lockup:
        Metrodata square mark (x≈7.87", y≈2.4", w=2.4", h=2.1") and white division tag.
        If logo is missing, gracefully falls back to a typographic badge ([ METRODATA ]).
      - Strict Geometry:
        Zero rounded corners on containers with top stripes/overlays; sharp rectangular
        panels (MSO_SHAPE.RECTANGLE) throughout.
    """
    effective_title = title or action_title or ""
    thresholds = theme.typography_thresholds

    # 1. Base slide with canvas background
    slide = add_slide_with_background(prs, theme)

    # 2. Left 1/3 Typographic Narrative Panel (Unified Text Frame)
    # x=0.8", y=2.0", w=3.6", h=4.0"
    narrative_tb = slide.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(3.6), Inches(4.0))
    tf = narrative_tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    # Paragraph 1: Tracker Breadcrumb (10pt bold uppercase, theme accent)
    p_tr = tf.paragraphs[0]
    p_tr.text = tracker.upper()
    p_tr.font.name = theme.font_family_header
    p_tr.font.size = Pt(thresholds.get("tracker_pt", 10.0))
    p_tr.font.bold = True
    p_tr.font.color.rgb = tracker_color or theme.get_rgb("accent")

    # Paragraph 2: Action Title (32-36pt bold, theme primary, space_before=12pt)
    p_ti = tf.add_paragraph()
    p_ti.text = effective_title
    p_ti.font.name = theme.font_family_header
    base_title_pt = 34.0 if len(effective_title) <= 45 else 30.0
    p_ti.font.size = Pt(base_title_pt)
    p_ti.font.bold = True
    p_ti.font.color.rgb = theme.get_rgb("primary")
    p_ti.space_before = Pt(12)

    # Paragraph 3: Context Synopsis / Subtitle (11.5pt regular, theme secondary, space_before=14pt)
    if subtitle:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = theme.font_family
        p_sub.font.size = Pt(thresholds.get("subtitle_pt", 11.5))
        p_sub.font.color.rgb = theme.get_rgb("secondary")
        p_sub.space_before = Pt(14)

    # 3. Right 2/3 Photographic Hero Panel (x=4.8", y=0.0", w=8.533", h=7.5")
    resolved_hero: Optional[Path] = None
    if hero_image_path is not None:
        p = Path(hero_image_path)
        if p.is_file():
            resolved_hero = p
    else:
        from src.ppt_engine.resource_manager import get_resource_manager
        resolved_hero = get_resource_manager().resolve_asset(
            "stock_chapter_photo",
            impacted_slide="Chapter Divider",
        )
        if resolved_hero is None:
            # Check secondary local candidates before falling back to solid color
            candidate_paths = [
                Path("assets/images/datacenter_stock.jpg"),
                Path("assets/images/noc_operations_stock.jpg"),
            ]
            for cand in candidate_paths:
                if cand.is_file():
                    resolved_hero = cand
                    break

    panel_x = Inches(4.8)
    panel_y = Inches(0.0)
    panel_w = Inches(8.533)
    panel_h = Inches(7.5)

    if resolved_hero is not None:
        try:
            with Image.open(resolved_hero) as im:
                iw, ih = im.size
            target_ratio = 8.533 / 7.5
            cur_ratio = iw / ih if ih > 0 else target_ratio

            pic = slide.shapes.add_picture(str(resolved_hero), panel_x, panel_y, panel_w, panel_h)
            if cur_ratio > target_ratio:
                excess = 1.0 - (target_ratio / cur_ratio)
                pic.crop_left = excess / 2.0
                pic.crop_right = excess / 2.0
            elif cur_ratio < target_ratio:
                excess = 1.0 - (cur_ratio / target_ratio)
                pic.crop_top = excess / 2.0
                pic.crop_bottom = excess / 2.0
        except Exception:
            fallback_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, panel_x, panel_y, panel_w, panel_h)
            fallback_bg.shadow.inherit = False
            fallback_bg.line.fill.background()
            fallback_bg.fill.solid()
            fallback_bg.fill.fore_color.rgb = hex_to_rgb("#0F172A")
    else:
        # Photo missing (Fallback): Solid rectangle filled with deep primary color (#0F172A)
        fallback_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, panel_x, panel_y, panel_w, panel_h)
        fallback_bg.shadow.inherit = False
        fallback_bg.line.fill.background()
        fallback_bg.fill.solid()
        fallback_bg.fill.fore_color.rgb = hex_to_rgb("#0F172A")

    # 4. Dark Translucent Scrim Overlay (45% alpha via OpenXML DrawingML)
    scrim = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, panel_x, panel_y, panel_w, panel_h)
    scrim.shadow.inherit = False
    scrim.line.fill.background()
    scrim.fill.solid()
    scrim.fill.fore_color.rgb = scrim_color or hex_to_rgb("#0B132B")

    try:
        alpha_val = int(round(scrim_alpha * 100000))
        solid_fill = scrim._element.spPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
        if solid_fill is not None:
            srgb_clr = solid_fill.find("{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
            if srgb_clr is not None:
                alpha_elem = parse_xml(
                    f'<a:alpha xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" val="{alpha_val}"/>'
                )
                srgb_clr.append(alpha_elem)
    except Exception:
        pass

    # 5. Logo & Division Lockup
    resolved_logo: Optional[Path] = None
    if logo_path is not None:
        lp = Path(logo_path)
        if lp.is_file():
            resolved_logo = lp
    else:
        from src.ppt_engine.resource_manager import get_resource_manager
        resolved_logo = get_resource_manager().resolve_asset(
            "logo_metrodata_square",
            impacted_slide="Chapter Divider",
        )

    logo_w = Inches(2.4)
    logo_h = Inches(2.1)
    logo_x = Inches(9.0665) - (logo_w / 2)
    logo_y = Inches(2.35)

    if resolved_logo is not None:
        slide.shapes.add_picture(str(resolved_logo), logo_x, logo_y, logo_w, logo_h)
    else:
        # Fallback: High-contrast white typographic pill badge ([ METRODATA ])
        badge_w = Inches(2.8)
        badge_h = Inches(0.65)
        badge_x = Inches(9.0665) - (badge_w / 2)
        badge_y = Inches(2.80)

        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, badge_x, badge_y, badge_w, badge_h)
        badge.shadow.inherit = False
        badge.fill.solid()
        badge.fill.fore_color.rgb = RGBColor(255, 255, 255)
        badge.line.fill.background()

        badge_tf = badge.text_frame
        badge_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        badge_tf.margin_left = badge_tf.margin_right = badge_tf.margin_top = badge_tf.margin_bottom = 0
        p_bg = badge_tf.paragraphs[0]
        p_bg.text = "METRODATA"
        p_bg.font.name = theme.font_family_header
        p_bg.font.size = Pt(14.0)
        p_bg.font.bold = True
        p_bg.alignment = PP_ALIGN.CENTER
        p_bg.font.color.rgb = hex_to_rgb("#0B132B")

    # Division Lockup / Capability Tag below logo
    div_y = Inches(4.70)
    div_tb = slide.shapes.add_textbox(Inches(5.0), div_y, Inches(8.133), Inches(0.9))
    div_tf = div_tb.text_frame
    div_tf.word_wrap = True
    div_tf.margin_left = div_tf.margin_right = div_tf.margin_top = div_tf.margin_bottom = 0

    if division_tag:
        p_div = div_tf.paragraphs[0]
        p_div.text = division_tag
        p_div.font.name = theme.font_family_header
        p_div.font.size = Pt(12.0)
        p_div.font.bold = True
        p_div.alignment = PP_ALIGN.CENTER
        p_div.font.color.rgb = RGBColor(255, 255, 255)

    if tagline:
        p_tag = div_tf.add_paragraph() if division_tag else div_tf.paragraphs[0]
        p_tag.text = tagline
        p_tag.font.name = theme.font_family
        p_tag.font.size = Pt(10.5)
        p_tag.font.bold = False
        p_tag.alignment = PP_ALIGN.CENTER
        p_tag.font.color.rgb = RGBColor(226, 232, 240)
        if division_tag:
            p_tag.space_before = Pt(4)

    # Optional footer (defaults to False for chapter dividers)
    if show_footer and current_idx is not None and total_slides is not None:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)

    return slide


# ============================================================================
# 6. Helper Primitives for Advanced Layouts & Color Interpolation
# ============================================================================

def _add_contained_image(
    slide: Any,
    img_path: Union[str, Path],
    x: Inches,
    y: Inches,
    max_w: Inches,
    max_h: Inches,
) -> Optional[Any]:
    """
    Renders an image scaled proportionally within a bounding box, preserving aspect ratio.
    Guarantees zero distortion and zero container overflow.
    """
    p = Path(img_path)
    if not p.is_file():
        return None
    try:
        with Image.open(p) as im:
            iw, ih = im.size
        if iw <= 0 or ih <= 0:
            return None
        aspect = iw / ih
        box_aspect = max_w / max_h
        if aspect > box_aspect:
            render_w = max_w
            render_h = max_w / aspect
        else:
            render_h = max_h
            render_w = max_h * aspect

        offset_x = x + (max_w - render_w) / 2
        offset_y = y + (max_h - render_h) / 2
        return slide.shapes.add_picture(str(p), offset_x, offset_y, render_w, render_h)
    except Exception:
        return None


def _interpolate_color(c1: RGBColor, c2: RGBColor, factor: float) -> RGBColor:
    """Linearly interpolates between two RGBColors. factor=0 -> c1, factor=1 -> c2."""
    factor = max(0.0, min(1.0, factor))
    r = int(round(c1[0] + (c2[0] - c1[0]) * factor))
    g = int(round(c1[1] + (c2[1] - c1[1]) * factor))
    b = int(round(c1[2] + (c2[2] - c1[2]) * factor))
    return RGBColor(r, g, b)


def _get_contrast_text_color(bg_color: RGBColor) -> RGBColor:
    """Computes high-contrast text color (white or dark slate) based on background luminance."""
    brightness = (bg_color[0] * 299 + bg_color[1] * 587 + bg_color[2] * 114) / 1000
    if brightness < 140:
        return RGBColor(255, 255, 255)
    return hex_to_rgb("#0F172A")


# ============================================================================
# 7. Archetype 5: Executive Cover Slide with Typographic Metadata & Dual Branding
# ============================================================================

def build_cover_slide(
    prs: Presentation,
    theme: Theme,
    title: str,
    subtitle: Optional[str] = None,
    client: str = "Enterprise Client",
    vendor: str = "Metrodata Consulting",
    product: Optional[str] = "Snowflake AI Data Cloud",
    date_str: Optional[str] = None,
    tracker: str = "ENTERPRISE TRANSFORMATION BLUEPRINT  |  PROJECT ENGAGEMENT",
    client_logo_path: Optional[Union[str, Path]] = None,
    vendor_logo_path: Optional[Union[str, Path]] = None,
    product_logo_path: Optional[Union[str, Path]] = None,
    client_sublabel: str = "Steering Committee & Executive Sponsors",
    vendor_sublabel: str = "Data & AI Modernization Practice",
    prepared_for_label: str = "PREPARED FOR",
    engagement_partner_label: str = "ENGAGEMENT PARTNER",
    date_classification_label: str = "DATE & CLASSIFICATION",
    confidential_label: str = "STRICTLY CONFIDENTIAL",
) -> Any:
    """
    Renders a modern, unboxed executive cover slide respecting AGENTS.md conventions:
      - Left accent bar framing title block cleanly.
      - Unified header text frame for Title & Subtitle (zero coordinate collision).
      - Triple co-branding lockup in header zone: [ CLIENT LOGO ] | [ PRODUCT ] | [ METRODATA ].
      - Typographic multi-column metadata layout (PREPARED FOR, ENGAGEMENT PARTNER, DATE/CONFIDENTIAL).
      - Zero boxed card containers for metadata.
      - Zero slide footer bars or pagination on cover slide.
    """
    slide = add_slide_with_background(prs, theme)

    # 1. Dual Metrodata Crimson Red & Blue Accent Bands framing title block
    # Stacked side-by-side with zero gap, mirroring Metrodata's emblem ratio (1 Red : 2 Blue).
    stripe_h = Inches(2.6)
    stripe_y = Inches(1.8)
    red_w = Inches(0.045)
    blue_w = Inches(0.090)  # Blue is double the thickness of red, reflecting 1:2 logo geometry

    # 1a. Left Band: Metrodata Crimson Red
    red_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.80),
        stripe_y,
        red_w,
        stripe_h,
    )
    red_bar.shadow.inherit = False
    red_bar.fill.solid()
    red_bar.fill.fore_color.rgb = theme.get_rgb("accent_secondary", default="#DC2626")
    red_bar.line.fill.background()

    # 1b. Right Band: Metrodata Blue (immediately adjacent, 2x thickness)
    blue_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.80) + red_w,
        stripe_y,
        blue_w,
        stripe_h,
    )
    blue_bar.shadow.inherit = False
    blue_bar.fill.solid()
    blue_bar.fill.fore_color.rgb = theme.get_rgb("accent", default="#0052CC")
    blue_bar.line.fill.background()

    # 2. Category Tracker Breadcrumb
    tb_cat = slide.shapes.add_textbox(Inches(1.15), Inches(1.8), Inches(7.5), Inches(0.35))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = tracker.upper()
    p_cat.font.name = theme.font_family_header
    p_cat.font.size = Pt(10.5)
    p_cat.font.bold = True
    p_cat.font.color.rgb = theme.get_rgb("accent")

    # 3. Main Title & Subtitle (Unified Frame for Consistent Spacing)
    tb_header = slide.shapes.add_textbox(Inches(1.15), Inches(2.22), Inches(7.5), Inches(2.35))
    tf_h = tb_header.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0

    p_title = tf_h.paragraphs[0]
    p_title.text = title
    p_title.font.name = theme.font_family_header
    base_title_pt = 28.0 if len(title) <= 50 else 24.0
    p_title.font.size = Pt(base_title_pt)
    p_title.font.bold = True
    p_title.font.color.rgb = theme.get_rgb("primary")

    if subtitle:
        p_sub = tf_h.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = theme.font_family
        p_sub.font.size = Pt(12.5)
        p_sub.font.color.rgb = theme.get_rgb("secondary")
        p_sub.space_before = Pt(12)

    # 4. Subtle structural baseline divider
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.15),
        Inches(4.9),
        Inches(11.383),
        Inches(0.015),
    )
    divider.shadow.inherit = False
    divider.fill.solid()
    divider.fill.fore_color.rgb = theme.get_rgb("border")
    divider.line.fill.background()

    # 5. Top-Right Co-Branding Lockup (Header Zone: Client + Product + Metrodata)
    # Available zone: y=0.70", h=0.55", spanning x=6.7" to 12.533"
    from src.ppt_engine.resource_manager import get_resource_manager
    rm = get_resource_manager()

    resolved_vendor_logo: Optional[Path] = None
    if vendor_logo_path is not None:
        p_v = Path(vendor_logo_path)
        if p_v.is_file():
            resolved_vendor_logo = p_v
    else:
        resolved_vendor_logo = rm.resolve_asset(
            "logo_metrodata_square",
            impacted_slide="Cover",
        )

    resolved_client_logo: Optional[Path] = None
    if client_logo_path is not None:
        p_c = Path(client_logo_path)
        if p_c.is_file():
            resolved_client_logo = p_c

    resolved_product_logo: Optional[Path] = None
    if product_logo_path is not None:
        p_p = Path(product_logo_path)
        if p_p.is_file():
            resolved_product_logo = p_p
    else:
        resolved_product_logo = rm.resolve_asset(
            "logo_snowflake_official",
            impacted_slide="Cover",
        )

    client_x = Inches(6.70)
    client_w = Inches(1.75)
    slot_y = Inches(0.70)
    slot_h = Inches(0.55)

    sep1_x = Inches(8.60)
    prod_x = Inches(8.75)
    prod_w = Inches(1.85)

    sep2_x = Inches(10.75)
    vendor_x = Inches(10.90)
    vendor_w = Inches(1.633)

    # 5a. Client Slot (Placeholder by default; custom image if provided)
    if resolved_client_logo:
        _add_contained_image(slide, resolved_client_logo, client_x, slot_y, client_w, slot_h)
    else:
        c_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, client_x, slot_y + Inches(0.05), client_w, slot_h - Inches(0.10))
        c_box.shadow.inherit = False
        c_box.fill.solid()
        c_box.fill.fore_color.rgb = theme.get_rgb("surface")
        c_box.line.color.rgb = theme.get_rgb("border")
        c_box.line.width = Pt(0.75)
        c_tf = c_box.text_frame
        c_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0
        p_cb = c_tf.paragraphs[0]
        p_cb.text = "[ CLIENT LOGO ]"
        p_cb.font.name = theme.font_family_header
        p_cb.font.size = Pt(8.5)
        p_cb.font.bold = True
        p_cb.alignment = PP_ALIGN.CENTER
        p_cb.font.color.rgb = theme.get_rgb("muted")

    # Separator 1: Client | Product
    sep1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, sep1_x, slot_y + Inches(0.08), Inches(0.015), slot_h - Inches(0.16))
    sep1.shadow.inherit = False
    sep1.fill.solid()
    sep1.fill.fore_color.rgb = theme.get_rgb("border")
    sep1.line.fill.background()

    # 5b. Product Slot (Official Brand Logo e.g. Snowflake)
    if resolved_product_logo:
        _add_contained_image(slide, resolved_product_logo, prod_x, slot_y, prod_w, slot_h)
    else:
        p_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, prod_x, slot_y + Inches(0.05), prod_w, slot_h - Inches(0.10))
        p_box.shadow.inherit = False
        p_box.fill.solid()
        p_box.fill.fore_color.rgb = theme.get_rgb("surface")
        p_box.line.color.rgb = theme.get_rgb("border")
        p_box.line.width = Pt(0.75)
        p_tf = p_box.text_frame
        p_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_tf.margin_left = p_tf.margin_right = p_tf.margin_top = p_tf.margin_bottom = 0
        p_pb = p_tf.paragraphs[0]
        p_pb.text = f"[ {(product or 'Snowflake').upper()} ]"
        p_pb.font.name = theme.font_family_header
        p_pb.font.size = Pt(8.5)
        p_pb.font.bold = True
        p_pb.alignment = PP_ALIGN.CENTER
        p_pb.font.color.rgb = theme.get_rgb("accent")

    # Separator 2: Product | Vendor
    sep2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, sep2_x, slot_y + Inches(0.08), Inches(0.015), slot_h - Inches(0.16))
    sep2.shadow.inherit = False
    sep2.fill.solid()
    sep2.fill.fore_color.rgb = theme.get_rgb("border")
    sep2.line.fill.background()

    # 5c. Vendor Slot (Metrodata)
    if resolved_vendor_logo:
        _add_contained_image(slide, resolved_vendor_logo, vendor_x, slot_y, vendor_w, slot_h)
    else:
        v_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, vendor_x, slot_y + Inches(0.05), vendor_w, slot_h - Inches(0.10))
        v_badge.shadow.inherit = False
        v_badge.fill.solid()
        v_badge.fill.fore_color.rgb = theme.get_rgb("surface")
        v_badge.line.color.rgb = theme.get_rgb("border")
        v_badge.line.width = Pt(0.75)
        v_tf = v_badge.text_frame
        v_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        v_tf.margin_left = v_tf.margin_right = v_tf.margin_top = v_tf.margin_bottom = 0
        p_vb = v_tf.paragraphs[0]
        p_vb.text = vendor.upper()
        p_vb.font.name = theme.font_family_header
        p_vb.font.size = Pt(9.5)
        p_vb.font.bold = True
        p_vb.alignment = PP_ALIGN.CENTER
        p_vb.font.color.rgb = theme.get_rgb("primary")

    # 6. Typographic Multi-Column Metadata (No Boxed Containers)
    meta_y = Inches(5.2)

    # Column 1: Client Sponsor
    tb_c1 = slide.shapes.add_textbox(Inches(1.15), meta_y, Inches(4.5), Inches(1.3))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    tf_c1.margin_left = tf_c1.margin_right = tf_c1.margin_top = tf_c1.margin_bottom = 0

    p1_lbl = tf_c1.paragraphs[0]
    p1_lbl.text = prepared_for_label
    p1_lbl.font.name = theme.font_family_header
    p1_lbl.font.size = Pt(10.0)
    p1_lbl.font.bold = True
    p1_lbl.font.color.rgb = theme.get_rgb("accent")

    p1_val = tf_c1.add_paragraph()
    p1_val.text = client
    p1_val.font.name = theme.font_family_header
    p1_val.font.size = Pt(14.5)
    p1_val.font.bold = True
    p1_val.font.color.rgb = theme.get_rgb("primary")
    p1_val.space_before = Pt(2)

    p1_sub = tf_c1.add_paragraph()
    p1_sub.text = client_sublabel
    p1_sub.font.name = theme.font_family
    p1_sub.font.size = Pt(11.0)
    p1_sub.font.color.rgb = theme.get_rgb("secondary")
    p1_sub.space_before = Pt(2)

    # Column 2: Engagement Partner
    tb_c2 = slide.shapes.add_textbox(Inches(6.0), meta_y, Inches(3.8), Inches(1.3))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    tf_c2.margin_left = tf_c2.margin_right = tf_c2.margin_top = tf_c2.margin_bottom = 0

    p2_lbl = tf_c2.paragraphs[0]
    p2_lbl.text = engagement_partner_label
    p2_lbl.font.name = theme.font_family_header
    p2_lbl.font.size = Pt(10.0)
    p2_lbl.font.bold = True
    p2_lbl.font.color.rgb = theme.get_rgb("accent")

    p2_val = tf_c2.add_paragraph()
    p2_val.text = vendor
    p2_val.font.name = theme.font_family_header
    p2_val.font.size = Pt(14.5)
    p2_val.font.bold = True
    p2_val.font.color.rgb = theme.get_rgb("primary")
    p2_val.space_before = Pt(2)

    p2_sub = tf_c2.add_paragraph()
    p2_sub.text = vendor_sublabel
    p2_sub.font.name = theme.font_family
    p2_sub.font.size = Pt(11.0)
    p2_sub.font.color.rgb = theme.get_rgb("secondary")
    p2_sub.space_before = Pt(2)

    # Column 3: Date & Classification
    tb_c3 = slide.shapes.add_textbox(Inches(10.1), meta_y, Inches(2.433), Inches(1.3))
    tf_c3 = tb_c3.text_frame
    tf_c3.word_wrap = True
    tf_c3.margin_left = tf_c3.margin_right = tf_c3.margin_top = tf_c3.margin_bottom = 0

    p3_lbl = tf_c3.paragraphs[0]
    p3_lbl.text = date_classification_label
    p3_lbl.font.name = theme.font_family_header
    p3_lbl.font.size = Pt(10.0)
    p3_lbl.font.bold = True
    p3_lbl.font.color.rgb = theme.get_rgb("accent")

    p3_val = tf_c3.add_paragraph()
    p3_val.text = date_str or "September 2026"
    p3_val.font.name = theme.font_family_header
    p3_val.font.size = Pt(13.5)
    p3_val.font.bold = True
    p3_val.font.color.rgb = theme.get_rgb("primary")
    p3_val.space_before = Pt(2)

    p3_sub = tf_c3.add_paragraph()
    p3_sub.text = confidential_label
    p3_sub.font.name = theme.font_family
    p3_sub.font.size = Pt(10.5)
    p3_sub.font.bold = True
    p3_sub.font.color.rgb = theme.get_rgb("muted")
    p3_sub.space_before = Pt(2)

    return slide


def build_hero_cover_slide(
    prs: Presentation,
    theme: Theme,
    title: str,
    subtitle: Optional[str] = None,
    client: str = "[CLIENT_COMPANY_NAME]",
    vendor: str = "PT Metrodata Electronics Tbk",
    product: Optional[str] = "Snowflake AI Data Cloud",
    date_str: Optional[str] = "September 2026",
    tracker: str = "ENTERPRISE TRANSFORMATION BLUEPRINT  |  PROJECT ENGAGEMENT",
    hero_image_path: Optional[Union[str, Path]] = None,
    hero_height: float = 3.65,
    scrim_alpha: float = 0.28,
    scrim_color: Optional[RGBColor] = None,
    client_logo_path: Optional[Union[str, Path]] = None,
    vendor_logo_path: Optional[Union[str, Path]] = None,
    product_logo_path: Optional[Union[str, Path]] = None,
    client_sublabel: str = "Steering Committee & Executive Sponsors",
    vendor_sublabel: str = "Data & AI Modernization Practice",
    prepared_for_label: str = "PREPARED FOR",
    engagement_partner_label: str = "ENGAGEMENT PARTNER",
) -> Any:
    """
    Renders a cinematic top-half photo hero cover slide respecting AGENTS.md conventions:
      - Top full-bleed photo plate (13.333" x hero_height") with aspect-preserved center crop.
      - OpenXML DrawingML dark translucent scrim overlay (<a:alpha val="28000"/>).
      - Bottom clean white canvas featuring:
        * Dual Metrodata Crimson Red & Blue Accent Bands (1 Red : 2 Blue ratio).
        * Category tracker breadcrumb.
        * Unified header text frame for Title & Subtitle (zero coordinate collision).
        * Clean typographic multi-column metadata layout (PREPARED FOR, ENGAGEMENT PARTNER).
        * Authentic dual vector lockup (Snowflake cyan mark + Metrodata logo) on bottom right.
      - Zero boxed card containers for metadata.
      - Zero slide footer bars or pagination on cover slide.
    """
    slide = add_slide_with_background(prs, theme)

    # 1. Resolve Hero Image
    from src.ppt_engine.resource_manager import get_resource_manager
    rm = get_resource_manager()

    resolved_hero: Optional[Path] = None
    if hero_image_path is not None:
        p_hero = Path(hero_image_path)
        if p_hero.is_file():
            resolved_hero = p_hero
    if resolved_hero is None:
        resolved_hero = rm.resolve_asset(
            "hero_cloud_interchange_night",
            impacted_slide="Hero Cover",
        )
    if resolved_hero is None:
        candidates = [
            Path("assets/images/hero/cloud_interchange_night.jpg"),
            Path("assets/images/stock/chapter_hero.jpg"),
            Path("assets/images/datacenter_stock_hero.png"),
        ]
        for cand in candidates:
            if cand.is_file():
                resolved_hero = cand
                break

    # 2. Hero Image Plate (Top Full-Bleed)
    plate_x = Inches(0.0)
    plate_y = Inches(0.0)
    plate_w = Inches(13.333)
    plate_h = Inches(hero_height)

    if resolved_hero is not None:
        try:
            with Image.open(resolved_hero) as im:
                iw, ih = im.size
            target_ratio = 13.333 / hero_height
            cur_ratio = iw / ih if ih > 0 else target_ratio

            pic = slide.shapes.add_picture(str(resolved_hero), plate_x, plate_y, plate_w, plate_h)
            if cur_ratio > target_ratio:
                excess = 1.0 - (target_ratio / cur_ratio)
                pic.crop_left = excess / 2.0
                pic.crop_right = excess / 2.0
            elif cur_ratio < target_ratio:
                excess = 1.0 - (cur_ratio / target_ratio)
                pic.crop_top = excess / 2.0
                pic.crop_bottom = excess / 2.0
        except Exception:
            fallback_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, plate_x, plate_y, plate_w, plate_h)
            fallback_bg.shadow.inherit = False
            fallback_bg.line.fill.background()
            fallback_bg.fill.solid()
            fallback_bg.fill.fore_color.rgb = hex_to_rgb("#0B132B")
    else:
        fallback_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, plate_x, plate_y, plate_w, plate_h)
        fallback_bg.shadow.inherit = False
        fallback_bg.line.fill.background()
        fallback_bg.fill.solid()
        fallback_bg.fill.fore_color.rgb = hex_to_rgb("#0B132B")

    # 3. Translucent Dark Scrim Overlay (DrawingML Alpha)
    scrim = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, plate_x, plate_y, plate_w, plate_h)
    scrim.shadow.inherit = False
    scrim.line.fill.background()
    scrim.fill.solid()
    scrim.fill.fore_color.rgb = scrim_color or hex_to_rgb("#0B132B")

    try:
        alpha_val = int(round(scrim_alpha * 100000))
        solid_fill = scrim._element.spPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
        if solid_fill is not None:
            srgb_clr = solid_fill.find("{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
            if srgb_clr is not None:
                alpha_elem = parse_xml(
                    f'<a:alpha xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" val="{alpha_val}"/>'
                )
                srgb_clr.append(alpha_elem)
    except Exception:
        pass

    # 4. Content Area Layout (Bottom half starting at plate_h)
    content_top = Inches(hero_height + 0.28)
    stripe_h = Inches(1.85)
    red_w = Inches(0.045)
    blue_w = Inches(0.090)

    # 4a. Left Brand Accent Stripes (1 Red : 2 Blue)
    red_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.80), content_top, red_w, stripe_h)
    red_bar.shadow.inherit = False
    red_bar.fill.solid()
    red_bar.fill.fore_color.rgb = theme.get_rgb("accent_secondary", default="#DC2626")
    red_bar.line.fill.background()

    blue_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.80) + red_w, content_top, blue_w, stripe_h)
    blue_bar.shadow.inherit = False
    blue_bar.fill.solid()
    blue_bar.fill.fore_color.rgb = theme.get_rgb("accent", default="#0052CC")
    blue_bar.line.fill.background()

    # 4b. Category Tracker Breadcrumb
    tb_cat = slide.shapes.add_textbox(Inches(1.15), content_top, Inches(11.383), Inches(0.28))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = tracker.upper()
    p_cat.font.name = theme.font_family_header
    p_cat.font.size = Pt(10.0)
    p_cat.font.bold = True
    p_cat.font.color.rgb = theme.get_rgb("accent")

    # 4c. Main Title & Subtitle (Unified Text Frame)
    tb_header = slide.shapes.add_textbox(Inches(1.15), content_top + Inches(0.32), Inches(11.383), Inches(1.50))
    tf_h = tb_header.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0

    p_title = tf_h.paragraphs[0]
    p_title.text = title
    p_title.font.name = theme.font_family_header
    base_title_pt = 26.0 if len(title) <= 55 else 22.0
    p_title.font.size = Pt(base_title_pt)
    p_title.font.bold = True
    p_title.font.color.rgb = theme.get_rgb("primary")

    if subtitle:
        p_sub = tf_h.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = theme.font_family
        p_sub.font.size = Pt(11.5)
        p_sub.font.color.rgb = theme.get_rgb("secondary")
        p_sub.space_before = Pt(8)

    # 5. Structural Baseline Divider
    divider_y = Inches(5.95)
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.80),
        divider_y,
        Inches(11.733),
        Inches(0.015),
    )
    divider.shadow.inherit = False
    divider.fill.solid()
    divider.fill.fore_color.rgb = theme.get_rgb("border")
    divider.line.fill.background()

    # 6. Typographic Multi-Column Metadata & Co-Branding Lockup
    meta_y = Inches(6.12)

    # Column 1: Client Sponsor
    tb_c1 = slide.shapes.add_textbox(Inches(1.15), meta_y, Inches(3.6), Inches(1.1))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    tf_c1.margin_left = tf_c1.margin_right = tf_c1.margin_top = tf_c1.margin_bottom = 0
    p1_lbl = tf_c1.paragraphs[0]
    p1_lbl.text = prepared_for_label
    p1_lbl.font.name = theme.font_family_header
    p1_lbl.font.size = Pt(9.0)
    p1_lbl.font.bold = True
    p1_lbl.font.color.rgb = theme.get_rgb("accent")

    p1_val = tf_c1.add_paragraph()
    p1_val.text = client
    p1_val.font.name = theme.font_family_header
    p1_val.font.size = Pt(13.0)
    p1_val.font.bold = True
    p1_val.font.color.rgb = theme.get_rgb("primary")
    p1_val.space_before = Pt(2)

    p1_sub = tf_c1.add_paragraph()
    p1_sub.text = client_sublabel
    p1_sub.font.name = theme.font_family
    p1_sub.font.size = Pt(10.0)
    p1_sub.font.color.rgb = theme.get_rgb("secondary")
    p1_sub.space_before = Pt(2)

    # Column 2: Engagement Partner
    tb_c2 = slide.shapes.add_textbox(Inches(5.0), meta_y, Inches(3.6), Inches(1.1))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    tf_c2.margin_left = tf_c2.margin_right = tf_c2.margin_top = tf_c2.margin_bottom = 0
    p2_lbl = tf_c2.paragraphs[0]
    p2_lbl.text = engagement_partner_label
    p2_lbl.font.name = theme.font_family_header
    p2_lbl.font.size = Pt(9.0)
    p2_lbl.font.bold = True
    p2_lbl.font.color.rgb = theme.get_rgb("accent")

    p2_val = tf_c2.add_paragraph()
    p2_val.text = vendor
    p2_val.font.name = theme.font_family_header
    p2_val.font.size = Pt(13.0)
    p2_val.font.bold = True
    p2_val.font.color.rgb = theme.get_rgb("primary")
    p2_val.space_before = Pt(2)

    p2_sub = tf_c2.add_paragraph()
    p2_sub.text = vendor_sublabel
    p2_sub.font.name = theme.font_family
    p2_sub.font.size = Pt(10.0)
    p2_sub.font.color.rgb = theme.get_rgb("secondary")
    p2_sub.space_before = Pt(2)

    # Column 3: Co-Branding Lockup (Metrodata + Snowflake)
    resolved_vendor_logo: Optional[Path] = None
    if vendor_logo_path is not None:
        p_v = Path(vendor_logo_path)
        if p_v.is_file():
            resolved_vendor_logo = p_v
    else:
        resolved_vendor_logo = rm.resolve_asset(
            "logo_metrodata_square",
            impacted_slide="Hero Cover",
        )

    resolved_product_logo: Optional[Path] = None
    if product_logo_path is not None:
        p_p = Path(product_logo_path)
        if p_p.is_file():
            resolved_product_logo = p_p
    else:
        resolved_product_logo = rm.resolve_asset(
            "logo_snowflake_official",
            impacted_slide="Hero Cover",
        )

    slot_y = Inches(6.15)
    slot_h = Inches(0.85)

    # Metrodata Logo slot
    if resolved_vendor_logo:
        _add_contained_image(slide, resolved_vendor_logo, Inches(8.90), slot_y, Inches(1.80), slot_h)

    # Divider between logos
    logo_sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(10.85), slot_y + Inches(0.12), Inches(0.015), slot_h - Inches(0.24))
    logo_sep.shadow.inherit = False
    logo_sep.fill.solid()
    logo_sep.fill.fore_color.rgb = theme.get_rgb("border")
    logo_sep.line.fill.background()

    # Snowflake Product Logo slot
    if resolved_product_logo:
        _add_contained_image(slide, resolved_product_logo, Inches(11.00), slot_y, Inches(1.50), slot_h)

    return slide


# ============================================================================
# 8. Archetype 6: Stepped Process Chevron Flow with Progressive Saturation
# ============================================================================

@dataclass
class ProcessChevronStep:
    """Content definition for a single phase in the Stepped Process Chevron Flow."""
    phase_number: str                       # e.g. "01", "PHASE 1"
    title: str                              # e.g. "Discovery & Scoping"
    duration_badge: Optional[str] = None    # e.g. "WEEKS 1-3"
    deliverables: List[str] = field(default_factory=list)
    status: Optional[str] = None            # e.g. "COMPLETED", "IN PROGRESS", "PLANNED"
    accent_color: Optional[RGBColor] = None # Optional override for chevron fill


def build_chevron_process_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "Execution Roadmap & Delivery Phases",
    action_title: str = "Phased Execution Roadmap Delivers Accelerated Value Across Four Controlled Horizons",
    subtitle: Optional[str] = "Sequential progression transitions foundation infrastructure into production analytics.",
    steps: Optional[List[ProcessChevronStep]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an executive stepped process flow using interconnected horizontal chevrons.
      - Distinct chevron headers with progressive color saturation.
      - Sharp rectangular card containers below each chevron (zero corner distortion).
      - Structured deliverable checklists with status pills.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

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

    n_steps = len(steps)
    total_w = Inches(11.733)
    start_x = Inches(0.8)
    chevron_y = Inches(2.18)
    chevron_h = Inches(0.58)
    gap = Inches(0.12)
    step_w = (total_w - (n_steps - 1) * gap) / n_steps
    card_y = chevron_y + chevron_h + Inches(0.08)
    card_h = Inches(4.06)

    base_primary = theme.get_rgb("primary")
    light_tint = _interpolate_color(RGBColor(241, 245, 249), base_primary, 0.28)

    for i, step in enumerate(steps):
        cur_x = start_x + i * (step_w + gap)

        # 1. Consistent Cohesive Chevron Color across all steps (Metrodata Blue)
        step_color = theme.get_rgb("accent")

        # 1b. Floating "WE ARE HERE" Location Marker Shape (Unmistakable visual indicator)
        if step.status == "IN PROGRESS":
            pin_w = Inches(2.65)
            pin_h = Inches(0.26)
            pin_x = cur_x + (step_w - pin_w) / 2
            pin_y = chevron_y - pin_h - Inches(0.06)

            pin_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, pin_x, pin_y, pin_w, pin_h)
            pin_badge.shadow.inherit = False
            pin_badge.fill.solid()
            pin_badge.fill.fore_color.rgb = hex_to_rgb("#DC2626")  # Metrodata Crimson Red!
            pin_badge.line.fill.background()

            pin_tf = pin_badge.text_frame
            pin_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            pin_tf.word_wrap = False
            pin_tf.margin_left = pin_tf.margin_right = pin_tf.margin_top = pin_tf.margin_bottom = 0
            p_pin = pin_tf.paragraphs[0]
            p_pin.text = "[ CURRENT: WE ARE HERE ]"
            p_pin.font.name = theme.font_family_header
            p_pin.font.size = Pt(9.5)
            p_pin.font.bold = True
            p_pin.alignment = PP_ALIGN.CENTER
            p_pin.font.color.rgb = RGBColor(255, 255, 255)

        # 2. Render top directional chevron banner
        chevron = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, cur_x, chevron_y, step_w, chevron_h)
        chevron.shadow.inherit = False
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

        # 3. Render body card container underneath (Highlight active sprint card)
        is_active = step.status == "IN PROGRESS"
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

        # Duration Badge (Consistent styling across all columns)
        p_badge = inner_tf.paragraphs[0]
        p_badge.text = step.duration_badge or ""
        p_badge.font.name = theme.font_family_header
        p_badge.font.size = Pt(10.5)
        p_badge.font.bold = True
        p_badge.font.color.rgb = theme.get_rgb("primary")

        # Status Pill Row (Clean ASCII to prevent headless font glyph box □)
        p_st = inner_tf.add_paragraph()
        if step.status == "COMPLETED":
            p_st.text = "[ COMPLETED ]"
            p_st.font.color.rgb = hex_to_rgb("#059669")
        elif step.status == "IN PROGRESS":
            p_st.text = "[ IN PROGRESS • ACTIVE SPRINT ]"
            p_st.font.color.rgb = hex_to_rgb("#0052CC")
        else:
            p_st.text = "[ PLANNED ]"
            p_st.font.color.rgb = hex_to_rgb("#64748B")
        p_st.font.name = theme.font_family_header
        p_st.font.size = Pt(9.5)
        p_st.font.bold = True
        p_st.space_before = Pt(2)

        # Deliverables Section Header
        p_dh = inner_tf.add_paragraph()
        p_dh.text = "KEY DELIVERABLES"
        p_dh.font.name = theme.font_family_header
        p_dh.font.size = Pt(10.0)
        p_dh.font.bold = True
        p_dh.font.color.rgb = theme.get_rgb("accent")
        p_dh.space_before = Pt(8)

        # Deliverables Checklist (Double-digit 11pt typography)
        for deliv in step.deliverables:
            p_item = inner_tf.add_paragraph()
            p_item.space_before = Pt(6)
            p_item.font.name = theme.font_family
            p_item.font.size = Pt(11.0)

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

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 9. Archetype 7: Split-Hero 1/3 Stat Callout + 2/3 Narrative Detail
# ============================================================================

@dataclass
class SplitHeroBlock:
    """Content definition for a single narrative block in Split-Hero slide."""
    title: str                              # e.g. "Enterprise Data Ingestion"
    description: str                        # e.g. "Automated CDC pipelines and Snowpipe streaming..."
    metric_badge: Optional[str] = None      # e.g. "+98% Latency Drop"
    category_tag: Optional[str] = None      # e.g. "STREAM 01"


def build_split_hero_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "Executive Synthesis & Core Impact",
    action_title: str = "Modern Data Architecture Unlocks High-Yield Operational Transformation",
    subtitle: Optional[str] = "Centralized lakehouse foundation drives immediate cost avoidance and predictive analytics velocity.",
    hero_stat: str = "$14.8M",
    hero_stat_label: str = "Annualized Business Value",
    hero_stat_subtext: Optional[str] = "Projected 3-year cumulative ROI with 4.2x payback across supply chain and analytics operations.",
    blocks: Optional[List[SplitHeroBlock]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an asymmetric split-screen consulting layout:
      - Left 1/3: Deep high-contrast hero card with 42pt numeric impact callout.
      - Right 2/3: Unbordered horizontal narrative streams separated by hairline dividers.
      - Eliminates repetitive 3-card/4-card box fatigue.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if blocks is None:
        blocks = [
            SplitHeroBlock(
                title="Real-Time Streaming & Ingestion",
                description="Sub-second CDC streaming via Snowpipe Streaming eliminates overnight batch latency, delivering live business telemetry to operations teams.",
                metric_badge="+98% Latency Drop",
                category_tag="STREAM 01  |  INGESTION",
            ),
            SplitHeroBlock(
                title="Unified Semantic Modeling & Transformation",
                description="Centralized dbt transformation models standardize metrics across ERP, CRM, and Supply Chain, eliminating reconciliation overhead and reporting drift.",
                metric_badge="100% Data Parity",
                category_tag="STREAM 02  |  TRANSFORMATION",
            ),
            SplitHeroBlock(
                title="Automated Governance & Audit Security",
                description="Integrated role-based access control (RBAC), tag-based data masking, and automated access logs ensure continuous SOC2 and GDPR compliance.",
                metric_badge="Zero Audit Findings",
                category_tag="STREAM 03  |  SECURITY",
            ),
        ]

    content_y = Inches(1.85)
    content_h = Inches(5.05)

    # 1. Left 1/3 High-Contrast Hero Card (Sharp Rectangle)
    hero_x = Inches(0.8)
    hero_w = Inches(3.6)
    add_card(
        slide,
        theme,
        hero_x,
        content_y,
        hero_w,
        content_h,
        bg_color=theme.get_rgb("primary"),
        border_color=theme.get_rgb("primary"),
        force_rectangle=True,
    )

    # Inside Left Hero Card: Typographic Content
    h_tb = slide.shapes.add_textbox(hero_x + Inches(0.28), content_y + Inches(0.32), hero_w - Inches(0.56), content_h - Inches(0.64))
    h_tf = h_tb.text_frame
    h_tf.word_wrap = True
    h_tf.margin_left = h_tf.margin_right = h_tf.margin_top = h_tf.margin_bottom = 0

    # Eyebrow Tag
    p_eye = h_tf.paragraphs[0]
    p_eye.text = "EXECUTIVE VALUE THESIS"
    p_eye.font.name = theme.font_family_header
    p_eye.font.size = Pt(9.5)
    p_eye.font.bold = True
    p_eye.font.color.rgb = theme.get_rgb("accent")

    # Huge Metric Stat Callout
    p_stat = h_tf.add_paragraph()
    p_stat.text = hero_stat
    p_stat.font.name = theme.font_family_header
    p_stat.font.size = Pt(40.0)
    p_stat.font.bold = True
    p_stat.font.color.rgb = RGBColor(255, 255, 255)
    p_stat.space_before = Pt(14)

    # Metric Label
    p_lbl = h_tf.add_paragraph()
    p_lbl.text = hero_stat_label
    p_lbl.font.name = theme.font_family_header
    p_lbl.font.size = Pt(13.0)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = RGBColor(241, 245, 249)
    p_lbl.space_before = Pt(4)

    # Hairline divider within hero card
    p_sep = h_tf.add_paragraph()
    p_sep.text = "—" * 28
    p_sep.font.size = Pt(7.0)
    p_sep.font.color.rgb = hex_to_rgb("#475569")
    p_sep.space_before = Pt(16)

    # Subtext Narrative
    if hero_stat_subtext:
        p_sub = h_tf.add_paragraph()
        p_sub.text = hero_stat_subtext
        p_sub.font.name = theme.font_family
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = hex_to_rgb("#CBD5E1")
        p_sub.space_before = Pt(14)

    # 2. Right 2/3 Unbordered Narrative Detail Area
    right_x = Inches(4.75)
    right_w = Inches(7.783)
    n_blocks = len(blocks)
    block_h = content_h / n_blocks

    for b_idx, block in enumerate(blocks):
        b_y = content_y + b_idx * block_h

        # Narrative Content Text Box
        b_tb = slide.shapes.add_textbox(right_x, b_y + Inches(0.12), right_w, block_h - Inches(0.24))
        b_tf = b_tb.text_frame
        b_tf.word_wrap = True
        b_tf.margin_left = b_tf.margin_right = b_tf.margin_top = b_tf.margin_bottom = 0

        # Row Header: Category Tag
        p_head = b_tf.paragraphs[0]
        if block.category_tag:
            p_head.text = block.category_tag.upper()
            p_head.font.name = theme.font_family_header
            p_head.font.size = Pt(9.0)
            p_head.font.bold = True
            p_head.font.color.rgb = theme.get_rgb("accent")

        # Title Paragraph + Right Metric Badge
        p_title = b_tf.add_paragraph() if block.category_tag else p_head
        p_title.text = block.title
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(14.0)
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")
        if block.category_tag:
            p_title.space_before = Pt(2)

        # Description Body
        p_desc = b_tf.add_paragraph()
        p_desc.text = block.description
        p_desc.font.name = theme.font_family
        p_desc.font.size = Pt(11.0)
        p_desc.font.color.rgb = theme.get_rgb("secondary")
        p_desc.space_before = Pt(6)

        # Metric Pill on the far right (if present)
        if block.metric_badge:
            pill_w = Inches(1.8)
            pill_h = Inches(0.38)
            pill_x = right_x + right_w - pill_w
            pill_y = b_y + Inches(0.12)
            pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, pill_x, pill_y, pill_w, pill_h)
            pill.shadow.inherit = False
            pill.fill.solid()
            pill.fill.fore_color.rgb = hex_to_rgb("#EFF6FF")
            pill.line.color.rgb = theme.get_rgb("accent")
            pill.line.width = Pt(1.0)

            pill_tf = pill.text_frame
            pill_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            pill_tf.margin_left = pill_tf.margin_right = pill_tf.margin_top = pill_tf.margin_bottom = 0
            p_pill = pill_tf.paragraphs[0]
            p_pill.text = block.metric_badge
            p_pill.font.name = theme.font_family_header
            p_pill.font.size = Pt(9.5)
            p_pill.font.bold = True
            p_pill.alignment = PP_ALIGN.CENTER
            p_pill.font.color.rgb = theme.get_rgb("primary")

        # Hairline Divider between blocks (skip after final block)
        if b_idx < n_blocks - 1:
            div = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                right_x,
                b_y + block_h - Inches(0.04),
                right_w,
                Inches(0.012),
            )
            div.shadow.inherit = False
            div.fill.solid()
            div.fill.fore_color.rgb = theme.get_rgb("border")
            div.line.fill.background()

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 10. Archetype 8: Gap Analysis & Solution Transformation
# ============================================================================

@dataclass
class GapDimensionData:
    """Content definition for a single dimension in Gap Analysis slide."""
    dimension: str                          # e.g. "Data Latency & Ingestion"
    as_is_state: str                        # e.g. "Nightly batch ETL runs overnight with 12-hour lag."
    to_be_state: str                        # e.g. "Sub-second Kafka streaming and Snowpipe micro-batching."
    transition_lever: Optional[str] = None  # e.g. "Snowpipe Streaming"
    impact_delta: Optional[str] = None      # e.g. "98% Latency Reduction"
    deficit_tag: Optional[str] = None       # e.g. "BOTTLENECK"


def build_gap_analysis_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "Architecture Gap Analysis  |  Current vs. Target State",
    action_title: str = "Modernization Closes Critical Gaps Between Legacy Constraints and Future Target State",
    subtitle: Optional[str] = "Systematic transformation resolves batch latency, data silos, and manual governance overhead.",
    dimensions: Optional[List[GapDimensionData]] = None,
    as_is_header: str = "CURRENT STATE (AS-IS)",
    to_be_header: str = "TARGET ARCHITECTURE (TO-BE)",
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders a consulting Gap Analysis comparison slide:
      - Left column: As-Is legacy deficit with warning status indicators.
      - Center column: Directional transformation lever badge.
      - Right column: To-Be target capabilities with positive delta badges.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if dimensions is None:
        dimensions = [
            GapDimensionData(
                dimension="Data Latency & Freshness",
                as_is_state="Nightly batch ETL runs overnight with 12-hour data lag, impairing morning executive operational decisions.",
                to_be_state="Real-time Kafka streaming and Snowpipe micro-batching deliver continuous updates with sub-minute query readiness.",
                transition_lever="Snowpipe Streaming",
                impact_delta="98% Latency Reduction",
                deficit_tag="BOTTLENECK",
            ),
            GapDimensionData(
                dimension="Scalability & Compute Concurrency",
                as_is_state="Monolithic on-premise data warehouse encounters severe query queuing during month-end reporting spikes.",
                to_be_state="Elastic multi-cluster Snowflake compute auto-scales instant capacity with zero query contention and zero spill-to-disk.",
                transition_lever="Multi-Cluster Warehouses",
                impact_delta="10x Concurrency",
                deficit_tag="CAPACITY CEILING",
            ),
            GapDimensionData(
                dimension="Governance & Security Control",
                as_is_state="Manual spreadsheet tracking of table permissions with static exports prone to data leakage and compliance failure.",
                to_be_state="Centralized Tag-Based Masking, Row-Level Security, and automated audit trails enforce continuous compliance.",
                transition_lever="Dynamic Masking & RBAC",
                impact_delta="SOC2 / GDPR Compliant",
                deficit_tag="AUDIT RISK",
            ),
        ]

    # Geometry Layout
    header_y = Inches(1.85)
    header_h = Inches(0.38)
    col1_x = Inches(0.8)
    col1_w = Inches(4.75)
    center_x = Inches(5.72)
    center_w = Inches(1.88)
    col2_x = Inches(7.77)
    col2_w = Inches(4.75)

    # 1. Column Headers
    # As-Is Header (Muted slate fill)
    h1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col1_x, header_y, col1_w, header_h)
    h1.shadow.inherit = False
    h1.fill.solid()
    h1.fill.fore_color.rgb = hex_to_rgb("#F1F5F9")
    h1.line.color.rgb = hex_to_rgb("#CBD5E1")
    h1.line.width = Pt(1.0)
    h1_tf = h1.text_frame
    h1_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    h1_tf.margin_left = Inches(0.15)
    p_h1 = h1_tf.paragraphs[0]
    p_h1.text = as_is_header.upper()
    p_h1.font.name = theme.font_family_header
    p_h1.font.size = Pt(11.0)
    p_h1.font.bold = True
    p_h1.font.color.rgb = hex_to_rgb("#475569")

    # Center Lever Header
    hc = slide.shapes.add_textbox(center_x, header_y, center_w, header_h)
    hc_tf = hc.text_frame
    hc_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    hc_tf.margin_left = hc_tf.margin_right = hc_tf.margin_top = hc_tf.margin_bottom = 0
    p_hc = hc_tf.paragraphs[0]
    p_hc.text = "TRANSITION LEVER"
    p_hc.font.name = theme.font_family_header
    p_hc.font.size = Pt(10.0)
    p_hc.font.bold = True
    p_hc.alignment = PP_ALIGN.CENTER
    p_hc.font.color.rgb = theme.get_rgb("muted")

    # To-Be Header (Brand accent tint)
    h2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col2_x, header_y, col2_w, header_h)
    h2.shadow.inherit = False
    h2.fill.solid()
    h2.fill.fore_color.rgb = hex_to_rgb("#EFF6FF")
    h2.line.color.rgb = theme.get_rgb("accent")
    h2.line.width = Pt(1.0)
    h2_tf = h2.text_frame
    h2_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    h2_tf.margin_left = Inches(0.15)
    p_h2 = h2_tf.paragraphs[0]
    p_h2.text = to_be_header.upper()
    p_h2.font.name = theme.font_family_header
    p_h2.font.size = Pt(11.0)
    p_h2.font.bold = True
    p_h2.font.color.rgb = theme.get_rgb("primary")

    # 2. Content Rows
    n_dim = len(dimensions)
    content_y = Inches(2.32)
    available_h = Inches(4.60)
    gap_y = Inches(0.10)
    row_h = (available_h - (n_dim - 1) * gap_y) / n_dim

    for r_idx, dim in enumerate(dimensions):
        cur_y = content_y + r_idx * (row_h + gap_y)

        # Left Card: As-Is Deficit Container
        card_l = add_card(
            slide,
            theme,
            col1_x,
            cur_y,
            col1_w,
            row_h,
            force_rectangle=True,
            bg_color=RGBColor(255, 255, 255),
            border_color=hex_to_rgb("#CBD5E1"),
            border_width_pt=1.0,
        )
        # Left prominent accent stripe on As-Is card (Metrodata crimson red for deficits)
        stripe_l = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col1_x, cur_y, Inches(0.08), row_h)
        stripe_l.shadow.inherit = False
        stripe_l.fill.solid()
        stripe_l.fill.fore_color.rgb = hex_to_rgb("#DC2626")
        stripe_l.line.fill.background()

        # Left Card Unified Text Frame (Zero coordinate collision)
        tb_l = slide.shapes.add_textbox(col1_x + Inches(0.18), cur_y + Inches(0.08), col1_w - Inches(0.34), row_h - Inches(0.16))
        tf_l = tb_l.text_frame
        tf_l.word_wrap = True
        tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0

        # Paragraph 0: Deficit Badge Callout (or Dimension Title if no deficit tag)
        p_def = tf_l.paragraphs[0]
        if dim.deficit_tag:
            p_def.text = f"[CRITICAL DEFICIT: {dim.deficit_tag.upper()}]"
            p_def.font.name = theme.font_family_header
            p_def.font.size = Pt(10.5)
            p_def.font.bold = True
            p_def.font.color.rgb = hex_to_rgb("#DC2626")  # Metrodata Crimson Red

        # Paragraph 1: Dimension Title
        p_dim = tf_l.add_paragraph() if dim.deficit_tag else p_def
        p_dim.text = dim.dimension
        p_dim.font.name = theme.font_family_header
        p_dim.font.size = Pt(14.0)
        p_dim.font.bold = True
        p_dim.font.color.rgb = theme.get_rgb("primary")
        if dim.deficit_tag:
            p_dim.space_before = Pt(2)

        # Paragraph 2: As-Is Narrative Description (Double-digit 11.5pt filling card volume)
        p_as = tf_l.add_paragraph()
        p_as.text = dim.as_is_state
        p_as.font.name = theme.font_family
        p_as.font.size = Pt(11.5)
        p_as.font.color.rgb = theme.get_rgb("secondary")
        p_as.space_before = Pt(4)

        # Center Transition Lever Badge
        lever_h = Inches(0.62)
        lever_y = cur_y + (row_h - lever_h) / 2
        lever_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, center_x, lever_y, center_w, lever_h)
        lever_badge.shadow.inherit = False
        lever_badge.fill.solid()
        lever_badge.fill.fore_color.rgb = hex_to_rgb("#EFF6FF")
        lever_badge.line.color.rgb = theme.get_rgb("accent")
        lever_badge.line.width = Pt(1.25)

        l_tf = lever_badge.text_frame
        l_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        l_tf.word_wrap = True
        l_tf.margin_left = Inches(0.06)
        l_tf.margin_right = Inches(0.06)
        l_tf.margin_top = l_tf.margin_bottom = 0
        p_lv = l_tf.paragraphs[0]
        lever_name = dim.transition_lever or "Transition Lever"
        p_lv.text = f"{lever_name} ->"
        p_lv.font.name = theme.font_family_header
        p_lv.font.size = Pt(9.5)
        p_lv.font.bold = True
        p_lv.alignment = PP_ALIGN.CENTER
        p_lv.font.color.rgb = theme.get_rgb("accent")

        # Right Card: To-Be Target Capability
        card_r = add_card(
            slide,
            theme,
            col2_x,
            cur_y,
            col2_w,
            row_h,
            force_rectangle=True,
            bg_color=RGBColor(255, 255, 255),
            border_color=theme.get_rgb("border"),
            border_width_pt=1.0,
        )
        # Left prominent accent stripe on To-Be card (emerald green for quantitative targets)
        stripe_r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col2_x, cur_y, Inches(0.08), row_h)
        stripe_r.shadow.inherit = False
        stripe_r.fill.solid()
        stripe_r.fill.fore_color.rgb = hex_to_rgb("#059669")
        stripe_r.line.fill.background()

        tb_r = slide.shapes.add_textbox(col2_x + Inches(0.18), cur_y + Inches(0.08), col2_w - Inches(0.34), row_h - Inches(0.16))
        tf_r = tb_r.text_frame
        tf_r.word_wrap = True
        tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0

        # Breakthrough Target Delta Headline (High-impact bold green single-line anchor)
        p_top_r = tf_r.paragraphs[0]
        if dim.impact_delta:
            r_eye = p_top_r.add_run()
            r_eye.text = "TARGET BENEFIT:  "
            r_eye.font.name = theme.font_family_header
            r_eye.font.size = Pt(9.5)
            r_eye.font.bold = True
            r_eye.font.color.rgb = hex_to_rgb("#047857")

            r_delta = p_top_r.add_run()
            r_delta.text = dim.impact_delta.upper()
            r_delta.font.name = theme.font_family_header
            r_delta.font.size = Pt(14.0)
            r_delta.font.bold = True
            r_delta.font.color.rgb = hex_to_rgb("#059669")

        # Supporting Architecture Narrative
        p_to = tf_r.add_paragraph() if dim.impact_delta else p_top_r
        p_to.text = dim.to_be_state
        p_to.font.name = theme.font_family
        p_to.font.size = Pt(11.5)
        p_to.font.color.rgb = theme.get_rgb("primary")
        if dim.impact_delta:
            p_to.space_before = Pt(5)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide



# ============================================================================
# 11. Archetype 9: Corporate Equity & Shareholding Tree
# ============================================================================

@dataclass
class EquityEntityNode:
    """Represents a single corporate entity in the equity structure tree."""
    name: str                           # e.g., "PT Mitra Integrasi Informatika"
    code: str                           # e.g., "MII"
    percentage: str                     # e.g., "99.99%"
    business_domain: str                # e.g., "ICT SOLUTIONS"
    tier: int = 1                       # 1 = Direct Subsidiary, 2 = Secondary JV
    parent_code: Optional[str] = None   # Parent entity code (for orthogonal routing)
    accent_color: Optional[str] = None  # Brand accent override


@dataclass
class EquityTreeData:
    """Complete dataset for an equity holding structure."""
    parent_company: str = "PT Metrodata Electronics Tbk"
    parent_ticker: str = "MTDL"
    parent_subtitle: str = "Holding & Listed Investment Company"
    tier1_nodes: List[EquityEntityNode] = field(default_factory=list)
    tier2_nodes: List[EquityEntityNode] = field(default_factory=list)
    footnote: str = "*) Reflects legal equity shareholding percentages as of latest PMO baseline."


def _default_equity_tree_data() -> EquityTreeData:
    """Generates canonical Metrodata Group equity shareholding structure dataset."""
    return EquityTreeData(
        parent_company="PT Metrodata Electronics Tbk",
        parent_ticker="MTDL",
        parent_subtitle="Holding & Listed Investment Company",
        tier1_nodes=[
            EquityEntityNode(
                name="PT Mitra Integrasi Informatika",
                code="MII",
                percentage="99.99%",
                business_domain="ICT SOLUTIONS",
                tier=1,
                parent_code="MTDL",
                accent_color="primary",
            ),
            EquityEntityNode(
                name="PT Sinergi Transformasi Digital",
                code="SINERGI",
                percentage="95.00%",
                business_domain="ICT SOLUTIONS",
                tier=1,
                parent_code="MTDL",
                accent_color="primary",
            ),
            EquityEntityNode(
                name="PT Soltius Indonesia",
                code="SI",
                percentage="99.99%",
                business_domain="ICT CONSULTING",
                tier=1,
                parent_code="MTDL",
                accent_color="accent",
            ),
            EquityEntityNode(
                name="PT Synnex Metrodata Indonesia",
                code="SMI",
                percentage="50.00%",
                business_domain="ICT DISTRIBUTION",
                tier=1,
                parent_code="MTDL",
                accent_color="danger",
            ),
        ],
        tier2_nodes=[
            EquityEntityNode(
                name="PT FPT Metrodata Indonesia",
                code="FMI",
                percentage="60.00%",
                business_domain="SECURITY SOLUTIONS",
                tier=2,
                parent_code="MII",
                accent_color="accent",
            ),
            EquityEntityNode(
                name="PT CacaFly Metrodata Indonesia",
                code="CMI",
                percentage="49.00%",
                business_domain="DIGITAL MARKETING SOLUTIONS",
                tier=2,
                parent_code="MII",
                accent_color="accent",
            ),
            EquityEntityNode(
                name="PT Packet Systems Indonesia",
                code="PSI",
                percentage="20.50%",
                business_domain="ICT BROADBAND & SOLUTION NETWORK",
                tier=2,
                parent_code="MII",
                accent_color="accent",
            ),
            EquityEntityNode(
                name="PT My Icon Technology",
                code="MIT",
                percentage="99.99%",
                business_domain="ICT E-COMMERCE",
                tier=2,
                parent_code="SMI",
                accent_color="danger",
            ),
            EquityEntityNode(
                name="PT Synnex Metrodata Technology & Services",
                code="SMTS",
                percentage="99.60%",
                business_domain="ICT ASSEMBLY",
                tier=2,
                parent_code="SMI",
                accent_color="danger",
            ),
        ],
        footnote="*) Reflects legal equity shareholding percentages as of latest PMO baseline.",
    )


def _draw_h_line(
    slide: Any,
    x1: Inches,
    x2: Inches,
    y: Inches,
    color: RGBColor,
    width_pt: float = 1.5,
) -> Any:
    """Draws a crisp horizontal connector bar using a sharp rectangle."""
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
    """Draws a crisp vertical connector bar using a sharp rectangle."""
    top = min(y1, y2)
    h = abs(y2 - y1)
    w = Pt(width_pt)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, top, w, h)
    line.shadow.inherit = False
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line


def _resolve_equity_color_palette(theme: Theme, color_val: Optional[str]) -> Tuple[RGBColor, RGBColor, RGBColor, RGBColor]:
    """
    Resolves (accent_rgb, pill_bg_rgb, pill_border_rgb, pill_text_rgb) for equity nodes.
    """
    c_val = (color_val or "primary").lower()
    if c_val in ("primary", "blue"):
        accent = theme.get_rgb("primary")
        pill_bg = RGBColor(0xEF, 0xF6, 0xFF)
        pill_border = RGBColor(0xBF, 0xDB, 0xFE)
        pill_text = RGBColor(0x1D, 0x4E, 0xD8)
    elif c_val in ("accent", "cyan", "info"):
        accent = RGBColor(0x02, 0x84, 0xC7)
        pill_bg = RGBColor(0xF0, 0xF9, 0xFF)
        pill_border = RGBColor(0xBA, 0xE6, 0xFD)
        pill_text = RGBColor(0x03, 0x69, 0xA1)
    elif c_val in ("danger", "red", "accent_secondary"):
        accent = RGBColor(0xDC, 0x26, 0x26)
        pill_bg = RGBColor(0xFE, 0xF2, 0xF2)
        pill_border = RGBColor(0xFE, 0xCA, 0xCA)
        pill_text = RGBColor(0xB9, 0x1C, 0x1C)
    elif c_val in ("warning", "amber"):
        accent = RGBColor(0xD9, 0x77, 0x06)
        pill_bg = RGBColor(0xFF, 0xFB, 0xEB)
        pill_border = RGBColor(0xFD, 0xE6, 0x8A)
        pill_text = RGBColor(0xB4, 0x53, 0x09)
    elif c_val in ("success", "green"):
        accent = RGBColor(0x16, 0xA3, 0x4A)
        pill_bg = RGBColor(0xF0, 0xFD, 0xF4)
        pill_border = RGBColor(0xBB, 0xF7, 0xD0)
        pill_text = RGBColor(0x15, 0x80, 0x3D)
    elif c_val.startswith("#"):
        accent = hex_to_rgb(c_val)
        pill_bg = RGBColor(0xF8, 0xFA, 0xFC)
        pill_border = RGBColor(0xEA, 0xE8, 0xE8)
        pill_text = accent
    else:
        accent = theme.get_rgb(c_val)
        pill_bg = RGBColor(0xF8, 0xFA, 0xFC)
        pill_border = RGBColor(0xEA, 0xE8, 0xE8)
        pill_text = accent
    return accent, pill_bg, pill_border, pill_text


def _render_equity_node_card(
    slide: Any,
    theme: Theme,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    node: EquityEntityNode,
) -> None:
    """
    Renders an individual corporate equity entity card strictly enforcing AGENTS.md geometry:
      - Sharp rectangles (MSO_SHAPE.RECTANGLE) for all containers and top ownership pills.
      - Flush top accent stripe.
      - Centered formal entity name and acronym.
      - Functional business domain badge at bottom.
    """
    accent_rgb, pill_bg_rgb, pill_border_rgb, pill_text_rgb = _resolve_equity_color_palette(theme, node.accent_color)

    # 1. Main Card Container (Strict Sharp Rectangle)
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    card.shadow.inherit = False
    card.fill.solid()
    card.fill.fore_color.rgb = theme.get_rgb("surface")
    card.line.color.rgb = theme.get_rgb("border")
    card.line.width = Pt(theme.card_border_width_pt)

    # 2. Flush Top Accent Stripe (Strict Sharp Rectangle)
    stripe_h = Inches(0.06)
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, stripe_h)
    stripe.shadow.inherit = False
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = accent_rgb
    stripe.line.fill.background()

    # 3. Top Ownership % Pill (Strict Sharp Rectangle)
    pill_w = width - Inches(0.24)
    pill_h = Inches(0.22)
    pill_left = left + Inches(0.12)
    pill_top = top + Inches(0.12)
    pill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, pill_left, pill_top, pill_w, pill_h)
    pill.shadow.inherit = False
    pill.fill.solid()
    pill.fill.fore_color.rgb = pill_bg_rgb
    pill.line.color.rgb = pill_border_rgb
    pill.line.width = Pt(0.75)

    tf_pill = pill.text_frame
    tf_pill.word_wrap = False
    tf_pill.margin_left = tf_pill.margin_right = tf_pill.margin_top = tf_pill.margin_bottom = 0
    p_pill = tf_pill.paragraphs[0]
    pct_text = node.percentage if "[" in node.percentage else f"[ {node.percentage} ]"
    p_pill.text = pct_text
    p_pill.alignment = PP_ALIGN.CENTER
    p_pill.font.name = theme.font_family
    p_pill.font.size = Pt(9.5)
    p_pill.font.bold = True
    p_pill.font.color.rgb = pill_text_rgb

    # 4. Body Area: Entity Name & Code
    tb_body = slide.shapes.add_textbox(left + Inches(0.08), top + Inches(0.38), width - Inches(0.16), height - Inches(0.72))
    tf_body = tb_body.text_frame
    tf_body.word_wrap = True
    tf_body.margin_left = tf_body.margin_right = tf_body.margin_top = tf_body.margin_bottom = 0

    p_name = tf_body.paragraphs[0]
    p_name.text = node.name
    p_name.font.name = theme.font_family_header
    p_name.font.size = Pt(9.0 if len(node.name) > 28 else 9.5)
    p_name.font.bold = True
    p_name.font.color.rgb = theme.get_rgb("primary")
    p_name.alignment = PP_ALIGN.CENTER

    p_code = tf_body.add_paragraph()
    p_code.text = f"({node.code})"
    p_code.font.name = theme.font_family
    p_code.font.size = Pt(8.5)
    p_code.font.bold = True
    p_code.font.color.rgb = theme.get_rgb("secondary")
    p_code.space_before = Pt(2)
    p_code.alignment = PP_ALIGN.CENTER

    # 5. Bottom Business Line Pill (Strict Sharp Rectangle)
    domain_h = Inches(0.20)
    domain_top = top + height - domain_h - Inches(0.08)
    domain_pill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + Inches(0.08), domain_top, width - Inches(0.16), domain_h)
    domain_pill.shadow.inherit = False
    domain_pill.fill.solid()
    domain_pill.fill.fore_color.rgb = theme.get_rgb("surface_muted")
    domain_pill.line.fill.background()

    tf_domain = domain_pill.text_frame
    tf_domain.word_wrap = True
    tf_domain.margin_left = tf_domain.margin_right = tf_domain.margin_top = tf_domain.margin_bottom = 0
    p_domain = tf_domain.paragraphs[0]
    p_domain.text = node.business_domain.upper()
    p_domain.alignment = PP_ALIGN.CENTER
    p_domain.font.name = theme.font_family
    p_domain.font.size = Pt(7.0 if len(node.business_domain) > 24 else 7.5)
    p_domain.font.bold = True
    p_domain.font.color.rgb = theme.get_rgb("secondary")


def build_equity_corporate_tree_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "CORPORATE GOVERNANCE | EQUITY STRUCTURE",
    action_title: str = "Metrodata Group Operates Multi-Tier Operating Subsidiaries and Specialized JVs",
    subtitle: Optional[str] = "PT Metrodata Electronics Tbk (MTDL) maintains controlling equity across core ICT distribution, solutions, and digital consulting entities.",
    tree_data: Optional[EquityTreeData] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders the Corporate Equity & Shareholding Tree Archetype (Slide 3 Benchmark):
      - Top Node: Parent Holding Company (PT Metrodata Electronics Tbk - MTDL)
      - Top Bus Connector: Vertical stem from parent dropping into horizontal trunk
      - Tier 1 Nodes: 4 Direct Operating Subsidiaries (MII 99.99%, SINERGI 95%, SI 99.99%, SMI 50%)
      - Branch Connectors: Native orthogonal connector lines from MII to Branch A and SMI to Branch B
      - Tier 2 Nodes: 5 Secondary Entities (FMI 60%, CMI 49%, PSI 20.50%, MIT 99.99%, SMTS 99.60%)

    Strictly adheres to AGENTS.md geometry:
      - Sharp rectangles (MSO_SHAPE.RECTANGLE) across all containers, stripes, and pills.
      - Unified text frame for action title and subtitle (space_before = Pt(10)).
      - Native orthogonal DrawingML vector lines.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if tree_data is None:
        tree_data = _default_equity_tree_data()
    else:
        if not tree_data.tier1_nodes or not tree_data.tier2_nodes:
            default_data = _default_equity_tree_data()
            if not tree_data.tier1_nodes:
                tree_data.tier1_nodes = default_data.tier1_nodes
            if not tree_data.tier2_nodes:
                tree_data.tier2_nodes = default_data.tier2_nodes

    c_primary = theme.get_rgb("primary")
    c_accent = theme.get_rgb("accent")
    c_muted = theme.get_rgb("muted")

    # ------------------------------------------------------------------------
    # 1. Top Parent Entity: Holding Level (Row 1)
    # ------------------------------------------------------------------------
    parent_w = Inches(5.00)
    parent_h = Inches(0.74)
    parent_top = Inches(1.68)
    parent_left = (prs.slide_width - parent_w) / 2.0  # Exactly centered at x = 4.166"

    # Container Card (Strict Sharp Rectangle)
    card_p = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, parent_left, parent_top, parent_w, parent_h)
    card_p.shadow.inherit = False
    card_p.fill.solid()
    card_p.fill.fore_color.rgb = c_primary
    card_p.line.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    card_p.line.width = Pt(1.0)

    # Top Accent Stripe (Strict Sharp Rectangle)
    stripe_p = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, parent_left, parent_top, parent_w, Inches(0.06))
    stripe_p.shadow.inherit = False
    stripe_p.fill.solid()
    stripe_p.fill.fore_color.rgb = c_accent
    stripe_p.line.fill.background()

    # Parent Text Box
    tb_p = slide.shapes.add_textbox(parent_left + Inches(0.20), parent_top + Inches(0.12), parent_w - Inches(0.40), parent_h - Inches(0.16))
    tf_p = tb_p.text_frame
    tf_p.word_wrap = True
    tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0

    p_p_title = tf_p.paragraphs[0]
    p_p_title.text = f"{tree_data.parent_company.upper()} ({tree_data.parent_ticker})"
    p_p_title.font.name = theme.font_family_header
    p_p_title.font.size = Pt(11.5)
    p_p_title.font.bold = True
    p_p_title.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p_p_title.alignment = PP_ALIGN.CENTER

    p_p_sub = tf_p.add_paragraph()
    p_p_sub.text = tree_data.parent_subtitle
    p_p_sub.font.name = theme.font_family
    p_p_sub.font.size = Pt(8.5)
    p_p_sub.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p_p_sub.space_before = Pt(2)
    p_p_sub.alignment = PP_ALIGN.CENTER

    # ------------------------------------------------------------------------
    # 2. Geometry Configuration for Tier 1 and Tier 2
    # ------------------------------------------------------------------------
    card_w = Inches(1.78)
    t1_top = Inches(2.80)
    t1_h = Inches(1.50)

    t2_top = Inches(4.85)
    t2_h = Inches(1.45)

    # Pre-calibrated center coordinates aligned with Slide 3 benchmark
    # Tier 1 Centers: MII (3.90"), SINERGI (5.79"), SI (7.70"), SMI (9.57")
    t1_centers = [Inches(3.90), Inches(5.79), Inches(7.70), Inches(9.57)]
    # Tier 2 Centers: FMI (2.88"), CMI (4.79"), PSI (6.72"), MIT (8.65"), SMTS (10.56")
    t2_centers = [Inches(2.88), Inches(4.79), Inches(6.72), Inches(8.65), Inches(10.56)]

    # If non-standard node counts are provided, compute dynamically
    if len(tree_data.tier1_nodes) != 4:
        n1 = len(tree_data.tier1_nodes)
        gap = Inches(0.20)
        total_w = n1 * card_w + (n1 - 1) * gap
        start_x = (prs.slide_width - total_w) / 2.0
        t1_centers = [start_x + i * (card_w + gap) + card_w / 2.0 for i in range(n1)]

    if len(tree_data.tier2_nodes) != 5:
        n2 = len(tree_data.tier2_nodes)
        gap = Inches(0.15)
        total_w = n2 * card_w + (n2 - 1) * gap
        start_x = (prs.slide_width - total_w) / 2.0
        t2_centers = [start_x + i * (card_w + gap) + card_w / 2.0 for i in range(n2)]

    # ------------------------------------------------------------------------
    # 3. Hierarchy Connector Lines: Parent (Row 1) -> Tier 1 (Row 2)
    # ------------------------------------------------------------------------
    parent_center_x = parent_left + parent_w / 2.0  # 6.666"
    parent_bottom_y = parent_top + parent_h          # 2.42"
    trunk_y = Inches(2.60)

    c_trunk = c_accent

    # Vertical stem from Parent bottom center to horizontal trunk
    _draw_v_line(slide, parent_center_x, parent_bottom_y, trunk_y, c_trunk, width_pt=1.5)

    # Horizontal trunk spanning leftmost to rightmost Tier 1 node
    _draw_h_line(slide, t1_centers[0], t1_centers[-1], trunk_y, c_trunk, width_pt=1.5)

    # Vertical drops into each Tier 1 card
    for cx in t1_centers:
        _draw_v_line(slide, cx, trunk_y, t1_top, c_trunk, width_pt=1.5)

    # ------------------------------------------------------------------------
    # 4. Render Tier 1 Cards (Row 2)
    # ------------------------------------------------------------------------
    for idx, node in enumerate(tree_data.tier1_nodes):
        cx = t1_centers[idx]
        left_pos = cx - card_w / 2.0
        _render_equity_node_card(slide, theme, left_pos, t1_top, card_w, t1_h, node)

    # ------------------------------------------------------------------------
    # 5. Hierarchy Connector Lines: Tier 1 -> Tier 2
    # ------------------------------------------------------------------------
    t1_bottom_y = t1_top + t1_h  # 4.30"
    branch_bus_y = Inches(4.58)

    # Branch A: Under MII -> FMI, CMI, PSI (3 entities)
    # Uses Primary Blue connector lines matching MII
    c_branch_a = theme.get_rgb("primary")
    mii_center_x = t1_centers[0]  # 3.90"
    _draw_v_line(slide, mii_center_x, t1_bottom_y, branch_bus_y, c_branch_a, width_pt=1.5)
    _draw_h_line(slide, t2_centers[0], t2_centers[2], branch_bus_y, c_branch_a, width_pt=1.5)
    for i in range(3):
        _draw_v_line(slide, t2_centers[i], branch_bus_y, t2_top, c_branch_a, width_pt=1.5)

    # Branch B: Under SMI -> MIT, SMTS (2 entities)
    # Uses Crimson Red connector lines matching SMI
    c_branch_b = RGBColor(0xDC, 0x26, 0x26)
    smi_center_x = t1_centers[-1]  # 9.57"
    _draw_v_line(slide, smi_center_x, t1_bottom_y, branch_bus_y, c_branch_b, width_pt=1.5)
    _draw_h_line(slide, t2_centers[3], t2_centers[4], branch_bus_y, c_branch_b, width_pt=1.5)
    for i in (3, 4):
        _draw_v_line(slide, t2_centers[i], branch_bus_y, t2_top, c_branch_b, width_pt=1.5)

    # ------------------------------------------------------------------------
    # 6. Render Tier 2 Cards (Row 3)
    # ------------------------------------------------------------------------
    for idx, node in enumerate(tree_data.tier2_nodes):
        cx = t2_centers[idx]
        left_pos = cx - card_w / 2.0
        _render_equity_node_card(slide, theme, left_pos, t2_top, card_w, t2_h, node)

    # ------------------------------------------------------------------------
    # 7. Footnote Notice & Slide Footer
    # ------------------------------------------------------------------------
    if tree_data.footnote:
        tb_fn = slide.shapes.add_textbox(Inches(0.80), Inches(6.52), Inches(11.733), Inches(0.25))
        tf_fn = tb_fn.text_frame
        tf_fn.word_wrap = True
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = tree_data.footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.0)
        p_fn.font.italic = True
        p_fn.font.color.rgb = c_muted

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 11. High-Fidelity Browser Mockup & Window Chrome Container Slide Archetype
# ============================================================================

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


# ============================================================================
# 12. Delivery Gantt & Roadmap Archetype
# ============================================================================

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
    tracker: str = "DELIVERY ROADMAP | PROJECT EXECUTION",
    action_title: str = "Phased Execution Plan Ensures Iterative Milestone Realization Across 12 Weeks",
    subtitle: Optional[str] = "Integrated schedule coordinating foundational lakehouse infrastructure, dbt transformations, and Streamlit delivery.",
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

    # 2. Unified Header Frame (AGENTS.md Zero Collision Rule)
    add_slide_header(slide, theme, tracker=tracker, title=action_title, subtitle=subtitle)

    # 3. Canvas Bounds
    left_x = Inches(0.80)
    grid_left = Inches(3.85)
    grid_width = Inches(8.68)
    header_y = Inches(1.85)
    header_h = Inches(0.35)

    num_periods = max(1, data.total_periods)
    col_width = grid_width / num_periods

    # Time Axis Header Bar
    t_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, grid_left, header_y, grid_width, header_h)
    t_bar.fill.solid()
    t_bar.fill.fore_color.rgb = theme.get_rgb("primary")
    t_bar.line.fill.background()

    labels = data.period_labels or [f"P{i}" for i in range(1, num_periods + 1)]
    for col_idx in range(num_periods):
        col_x = grid_left + col_idx * col_width
        tb = slide.shapes.add_textbox(col_x, header_y, col_width, header_h)
        tf = tb.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        lbl = labels[col_idx] if col_idx < len(labels) else f"P{col_idx + 1}"
        p.text = lbl
        p.font.name = theme.font_family_header
        p.font.size = Pt(8.5)
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
        ws_card.fill.solid()
        ws_card.fill.fore_color.rgb = RGBColor(255, 255, 255)
        ws_card.line.color.rgb = RGBColor(226, 232, 240)
        ws_card.line.width = Pt(1.0)

        # Left accent stripe (Sharp Rectangle)
        accent_key = ws.accent_color
        acc_rgb = theme.get_rgb(accent_key) if accent_key in ("primary", "secondary", "accent") else theme.get_rgb("accent")
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, cur_y, Inches(0.08), row_h)
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = acc_rgb
        stripe.line.fill.background()

        tf_ws = ws_card.text_frame
        tf_ws.word_wrap = True
        tf_ws.margin_left = Inches(0.18)
        tf_ws.margin_right = Inches(0.08)
        tf_ws.margin_top = Inches(0.10)
        p_badge = tf_ws.paragraphs[0]
        p_badge.text = ws.badge.upper()
        p_badge.font.name = theme.font_family_header
        p_badge.font.size = Pt(7.5)
        p_badge.font.bold = True
        p_badge.font.color.rgb = acc_rgb

        p_title = tf_ws.add_paragraph()
        p_title.text = ws.category
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(9.5)
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")
        p_title.space_before = Pt(2)

        # Grid row background
        row_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, grid_left, cur_y, grid_width, row_h)
        row_bg.fill.solid()
        row_bg.fill.fore_color.rgb = RGBColor(248, 250, 252) if ws_idx % 2 == 0 else RGBColor(255, 255, 255)
        row_bg.line.color.rgb = RGBColor(226, 232, 240)
        row_bg.line.width = Pt(0.75)

        # Draw vertical grid column dividers inside row
        for c_idx in range(1, num_periods):
            cx = grid_left + c_idx * col_width
            vline = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cur_y, Pt(1), row_h)
            vline.fill.solid()
            vline.fill.fore_color.rgb = RGBColor(226, 232, 240)
            vline.line.fill.background()

        # Render tasks inside this workstream
        num_tasks = len(ws.tasks)
        if num_tasks > 0:
            task_gap = Inches(0.04)
            task_margin = Inches(0.06)
            task_h = (row_h - 2 * task_margin - (num_tasks - 1) * task_gap) / num_tasks
            task_h = max(Inches(0.20), min(Inches(0.32), task_h))

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
                    m_shape.fill.solid()
                    m_shape.fill.fore_color.rgb = theme.get_rgb("accent")
                    m_shape.line.color.rgb = theme.get_rgb("primary")
                    m_shape.line.width = Pt(1.5)

                    # Label next to diamond
                    tb_m = slide.shapes.add_textbox(mx + diam_size + Inches(0.05), ty - Inches(0.02), Inches(2.2), task_h)
                    tf_m = tb_m.text_frame
                    tf_m.word_wrap = True
                    p_m = tf_m.paragraphs[0]
                    p_m.text = task.name
                    p_m.font.name = theme.font_family_header
                    p_m.font.size = Pt(7.5)
                    p_m.font.bold = True
                    p_m.font.color.rgb = theme.get_rgb("primary")
                else:
                    # Task duration bar (Sharp Rectangle)
                    t_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bar_x, ty, bar_w, task_h)
                    t_shape.fill.solid()
                    t_shape.fill.fore_color.rgb = fill_rgb
                    t_shape.line.color.rgb = RGBColor(255, 255, 255)
                    t_shape.line.width = Pt(0.75)

                    tf_t = t_shape.text_frame
                    tf_t.word_wrap = False
                    tf_t.margin_left = Inches(0.06)
                    tf_t.margin_right = Inches(0.06)
                    tf_t.margin_top = Inches(0.01)
                    p_t = tf_t.paragraphs[0]
                    p_t.text = task.name
                    p_t.font.name = theme.font_family_header
                    p_t.font.size = Pt(7.5)
                    p_t.font.bold = True
                    p_t.font.color.rgb = RGBColor(255, 255, 255) if task.status != "PLANNED" else theme.get_rgb("primary")

    # 5. Current Period "TODAY / SPRINT" Indicator
    if data.current_period_marker is not None and 0.0 <= data.current_period_marker <= float(num_periods):
        marker_x = grid_left + (data.current_period_marker - 1.0) * col_width
        total_grid_h = num_ws * (row_h + row_gap)
        m_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, marker_x, header_y, Pt(2), header_h + Inches(0.12) + total_grid_h)
        m_line.fill.solid()
        m_line.fill.fore_color.rgb = RGBColor(220, 38, 38)  # Crimson Red
        m_line.line.fill.background()

        # Marker tag on top
        tag_w = Inches(0.85)
        tag_h = Inches(0.22)
        tag_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, marker_x - tag_w / 2.0, header_y - Inches(0.24), tag_w, tag_h)
        tag_box.fill.solid()
        tag_box.fill.fore_color.rgb = RGBColor(220, 38, 38)
        tag_box.line.fill.background()
        tf_tag = tag_box.text_frame
        p_tag = tf_tag.paragraphs[0]
        p_tag.alignment = PP_ALIGN.CENTER
        p_tag.text = "CURRENT"
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(7.0)
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
        tb_leg = slide.shapes.add_textbox(cur_lx, legend_y, Inches(1.8), Inches(0.25))
        tf_l = tb_leg.text_frame
        p_l = tf_l.paragraphs[0]
        r_sym = p_l.add_run()
        r_sym.text = f"{symbol} "
        r_sym.font.name = theme.font_family_header
        r_sym.font.size = Pt(9.0)
        r_sym.font.bold = True
        r_sym.font.color.rgb = sym_color

        r_lbl = p_l.add_run()
        r_lbl.text = sym_label
        r_lbl.font.name = theme.font_family
        r_lbl.font.size = Pt(8.0)
        r_lbl.font.color.rgb = theme.get_rgb("secondary")
        cur_lx += Inches(1.75)

    if data.footnote:
        tb_fn = slide.shapes.add_textbox(grid_left, legend_y, grid_width, Inches(0.25))
        tf_fn = tb_fn.text_frame
        p_fn = tf_fn.paragraphs[0]
        p_fn.alignment = PP_ALIGN.RIGHT
        p_fn.text = data.footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(7.5)
        p_fn.font.italic = True
        p_fn.font.color.rgb = RGBColor(148, 163, 184)

    # 7. Slide Footer
    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 13. Feature Evaluation Matrix & Harvey Balls Archetype
# ============================================================================

@dataclass
class FeatureScorecardRow:
    """Represents an evaluation criterion row in a comparison matrix."""
    category: str
    criteria: str
    scores: Dict[str, str]           # platform -> "FULL", "HALF", "EMPTY", "N/A" or glyphs "●", "◐", "○"
    business_impact: str = "HIGH"

@dataclass
class FeatureMatrixData:
    """Dataset for an executive platform scorecard with Harvey Balls."""
    columns: List[str] = field(default_factory=list)
    rows: List[FeatureScorecardRow] = field(default_factory=list)
    recommendation_badge: str = "RECOMMENDED ARCHITECTURE"
    recommended_column: str = "Snowflake Data Cloud"
    footnote: str = "Harvey Balls: ● Full Native Support | ◐ Partial / Requires Extension | ○ Complex / Unsupported"


def _default_feature_matrix_data() -> FeatureMatrixData:
    return FeatureMatrixData(
        columns=["Snowflake Data Cloud", "AWS Redshift Serverless", "Google BigQuery"],
        recommended_column="Snowflake Data Cloud",
        rows=[
            FeatureScorecardRow(
                category="Storage & Compute",
                criteria="Decoupled Multi-Cluster Compute Scaling",
                scores={"Snowflake Data Cloud": "●", "AWS Redshift Serverless": "◐", "Google BigQuery": "●"},
                business_impact="CRITICAL",
            ),
            FeatureScorecardRow(
                category="Data Sharing",
                criteria="Secure Direct Cross-Region Data Sharing",
                scores={"Snowflake Data Cloud": "●", "AWS Redshift Serverless": "◐", "Google BigQuery": "○"},
                business_impact="HIGH",
            ),
            FeatureScorecardRow(
                category="Data Governance",
                criteria="Unified Dynamic Masking & Horizon Governance",
                scores={"Snowflake Data Cloud": "●", "AWS Redshift Serverless": "○", "Google BigQuery": "◐"},
                business_impact="CRITICAL",
            ),
            FeatureScorecardRow(
                category="AI & Semantic Layer",
                criteria="Native Streamlit & Cortex LLM Integration",
                scores={"Snowflake Data Cloud": "●", "AWS Redshift Serverless": "○", "Google BigQuery": "◐"},
                business_impact="HIGH",
            ),
            FeatureScorecardRow(
                category="Cost Efficiency",
                criteria="Per-Second Elastic Warehouse Auto-Suspend",
                scores={"Snowflake Data Cloud": "●", "AWS Redshift Serverless": "◐", "Google BigQuery": "◐"},
                business_impact="MEDIUM",
            ),
        ],
    )


def build_feature_matrix_slide(
    prs_or_slide: Any,
    theme: Optional[Theme] = None,
    tracker: str = "ARCHITECTURE EVALUATION | PLATFORM BENCHMARK",
    action_title: str = "Snowflake AI Data Cloud Demonstrates Superior Capabilities Across Core Evaluation Criteria",
    subtitle: Optional[str] = "Multi-dimensional comparative assessment evaluating compute elasticity, data governance, and native AI integration.",
    matrix_data: Optional[FeatureMatrixData] = None,
    current_idx: int = 5,
    total_slides: int = 10,
    notice: Optional[str] = None,
) -> Any:
    """
    Renders an executive feature evaluation matrix slide utilizing Harvey Balls glyphs
    (●, ◐, ○) and highlighting the recommended platform choice.
    """
    if theme is None:
        theme = get_theme("default")

    if hasattr(prs_or_slide, "slides"):
        slide = prs_or_slide.slides.add_slide(prs_or_slide.slide_layouts[6])
    else:
        slide = prs_or_slide

    data = matrix_data or _default_feature_matrix_data()

    # 1. Background Fill
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.50))
    bg.fill.solid()
    bg.fill.fore_color.rgb = theme.get_rgb("background")
    bg.line.fill.background()

    # 2. Unified Header Frame
    add_slide_header(slide, theme, tracker=tracker, title=action_title, subtitle=subtitle)

    # 3. Canvas Table Layout Bounds
    table_left = Inches(0.80)
    table_top = Inches(1.85)
    table_w = Inches(11.733)
    hdr_h = Inches(0.42)
    row_h = Inches(0.70)

    platforms = data.columns
    cat_w = Inches(2.20)
    crit_w = Inches(3.30)
    impact_w = Inches(1.233)
    plat_w = (table_w - cat_w - crit_w - impact_w) / max(1, len(platforms))

    # Header Row (Sharp Rectangle)
    hdr_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left, table_top, table_w, hdr_h)
    hdr_bg.fill.solid()
    hdr_bg.fill.fore_color.rgb = theme.get_rgb("primary")
    hdr_bg.line.fill.background()

    # Header cell labels
    def _add_hdr_txt(x: Inches, w: Inches, text: str, align=PP_ALIGN.LEFT, is_rec: bool = False):
        tb = slide.shapes.add_textbox(x, table_top, w, hdr_h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.08)
        p = tf.paragraphs[0]
        p.alignment = align
        p.text = text
        p.font.name = theme.font_family_header
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = theme.get_rgb("accent") if is_rec else RGBColor(255, 255, 255)

    _add_hdr_txt(table_left + Inches(0.12), cat_w - Inches(0.12), "DOMAIN / CATEGORY")
    _add_hdr_txt(table_left + cat_w + Inches(0.10), crit_w - Inches(0.10), "EVALUATION CRITERIA")

    for p_idx, plat in enumerate(platforms):
        px = table_left + cat_w + crit_w + p_idx * plat_w
        is_rec = (plat == data.recommended_column)
        _add_hdr_txt(px, plat_w, plat.upper(), align=PP_ALIGN.CENTER, is_rec=is_rec)

    _add_hdr_txt(table_left + cat_w + crit_w + len(platforms) * plat_w, impact_w, "IMPACT", align=PP_ALIGN.CENTER)

    # 4. Rows
    harvey_glyph_map = {
        "FULL": "●",
        "●": "●",
        "HALF": "◐",
        "◐": "◐",
        "EMPTY": "○",
        "○": "○",
        "N/A": "-",
    }

    cur_y = table_top + hdr_h + Inches(0.06)
    for r_idx, row in enumerate(data.rows):
        # Row card container (Sharp Rectangle)
        rc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left, cur_y, table_w, row_h)
        rc.fill.solid()
        rc.fill.fore_color.rgb = RGBColor(255, 255, 255) if r_idx % 2 == 0 else RGBColor(248, 250, 252)
        rc.line.color.rgb = RGBColor(226, 232, 240)
        rc.line.width = Pt(0.75)

        # Category cell
        tb_cat = slide.shapes.add_textbox(table_left + Inches(0.12), cur_y + Inches(0.12), cat_w - Inches(0.18), row_h - Inches(0.20))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        p_c = tf_cat.paragraphs[0]
        p_c.text = row.category
        p_c.font.name = theme.font_family_header
        p_c.font.size = Pt(9.0)
        p_c.font.bold = True
        p_c.font.color.rgb = theme.get_rgb("primary")

        # Criteria cell
        tb_crit = slide.shapes.add_textbox(table_left + cat_w + Inches(0.10), cur_y + Inches(0.12), crit_w - Inches(0.20), row_h - Inches(0.20))
        tf_crit = tb_crit.text_frame
        tf_crit.word_wrap = True
        p_cr = tf_crit.paragraphs[0]
        p_cr.text = row.criteria
        p_cr.font.name = theme.font_family
        p_cr.font.size = Pt(9.5)
        p_cr.font.color.rgb = theme.get_rgb("secondary")

        # Platform scores
        for p_idx, plat in enumerate(platforms):
            px = table_left + cat_w + crit_w + p_idx * plat_w
            score_raw = row.scores.get(plat, "○")
            glyph = harvey_glyph_map.get(score_raw.upper() if isinstance(score_raw, str) else "", "○")

            is_rec = (plat == data.recommended_column)
            if is_rec:
                col_hl = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px + Inches(0.04), cur_y + Inches(0.04), plat_w - Inches(0.08), row_h - Inches(0.08))
                col_hl.fill.solid()
                col_hl.fill.fore_color.rgb = RGBColor(241, 245, 249)
                col_hl.line.fill.background()

            tb_sc = slide.shapes.add_textbox(px, cur_y + Inches(0.14), plat_w, Inches(0.35))
            tf_sc = tb_sc.text_frame
            p_s = tf_sc.paragraphs[0]
            p_s.alignment = PP_ALIGN.CENTER
            p_s.text = glyph
            p_s.font.name = theme.font_family_header
            p_s.font.size = Pt(16.0)
            p_s.font.bold = True
            if glyph == "●":
                p_s.font.color.rgb = RGBColor(16, 185, 129) if is_rec else theme.get_rgb("primary")
            elif glyph == "◐":
                p_s.font.color.rgb = RGBColor(245, 158, 11)  # Amber
            else:
                p_s.font.color.rgb = RGBColor(148, 163, 184)  # Slate-400

        # Impact Badge
        tb_imp = slide.shapes.add_textbox(table_left + cat_w + crit_w + len(platforms) * plat_w, cur_y + Inches(0.16), impact_w, Inches(0.35))
        tf_imp = tb_imp.text_frame
        p_im = tf_imp.paragraphs[0]
        p_im.alignment = PP_ALIGN.CENTER
        p_im.text = row.business_impact.upper()
        p_im.font.name = theme.font_family_header
        p_im.font.size = Pt(8.0)
        p_im.font.bold = True
        if row.business_impact.upper() in ("CRITICAL", "HIGH"):
            p_im.font.color.rgb = RGBColor(220, 38, 38)
        else:
            p_im.font.color.rgb = theme.get_rgb("accent")

        cur_y += row_h + Inches(0.06)

    # 5. Recommendation callout & Footnote
    foot_y = cur_y + Inches(0.15)
    tb_fn = slide.shapes.add_textbox(table_left, foot_y, table_w, Inches(0.30))
    tf_fn = tb_fn.text_frame
    p_fn = tf_fn.paragraphs[0]
    p_fn.text = data.footnote
    p_fn.font.name = theme.font_family
    p_fn.font.size = Pt(8.0)
    p_fn.font.italic = True
    p_fn.font.color.rgb = RGBColor(100, 116, 139)

    # 6. Slide Footer
    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


# ============================================================================
# 14. Technology Logo Grids, Capability Matrices & Iceberg Concepts
# ============================================================================

def _add_status_pill(
    slide: Any,
    theme: Theme,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    status: str,
    font_size_pt: float = 8.0,
    override_color_key: Optional[str] = None,
) -> Any:
    """Renders a standalone rounded status badge pill with theme-resolved colors."""
    if override_color_key:
        if override_color_key in ("danger", "red"):
            bg_key, text_key = ("badge_red_fill", "badge_red_text")
        elif override_color_key in ("warning", "amber", "orange"):
            bg_key, text_key = ("badge_amber_fill", "badge_amber_text")
        elif override_color_key in ("success", "green"):
            bg_key, text_key = ("badge_green_fill", "badge_green_text")
        elif override_color_key in ("accent", "blue", "primary"):
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
    font_size_pt: float = 9.0,
    font_color: Optional[RGBColor] = None,
    space_before_pt: float = 4.0,
    bullet_char: str = "•",
) -> Any:
    """Appends a bullet paragraph with DrawingML hanging indent (marL/indent)."""
    from pptx.oxml.xmlchemy import OxmlElement

    p = tf.add_paragraph()
    clean_text = text.lstrip("•\t -*").strip()
    p.text = clean_text
    p.font.name = font_name
    p.font.size = Pt(font_size_pt)
    if font_color:
        p.font.color.rgb = font_color
    p.space_before = Pt(space_before_pt)

    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", "288000")
    pPr.set("indent", "-288000")

    buChar = OxmlElement("a:buChar")
    buChar.set("char", bullet_char)
    pPr.append(buChar)
    return p


def _fit_image_in_box(
    img_path: Union[str, Path],
    box_left: Inches,
    box_top: Inches,
    box_width: Inches,
    box_height: Inches,
) -> Tuple[Inches, Inches, Inches, Inches]:
    """Calculates coordinates to fit an image inside a bounding box while preserving aspect ratio."""
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


@dataclass
class TechLogoItem:
    name: str
    category: str
    tier_badge: str = "CORE"
    logo: Optional[str] = None
    accent_key: str = "accent"
    description: Optional[str] = None


@dataclass
class CardGridItem:
    title: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    bullets: List[str] = field(default_factory=list)
    accent_key: str = "accent"
    badge: Optional[str] = None


@dataclass
class BadgeMatrixSection:
    section_title: str
    accent_key: str = "accent"
    badge_count_label: Optional[str] = None
    items: List[Dict[str, str]] = field(default_factory=list)


def build_tech_logo_grid_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "TECHNOLOGY PORTFOLIO | ENTERPRISE ECOSYSTEM",
    action_title: str = "Curated Best-of-Breed Technology Stack Delivers Governed High-Performance Analytics",
    subtitle: Optional[str] = "Standardized technology matrix spanning ingestion, lakehouse storage, transformation, and semantic delivery.",
    items: Optional[List[TechLogoItem]] = None,
    columns: int = 4,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """Renders a structured grid of normalized technology cards with top stripes and badges."""
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if not items:
        items = [
            TechLogoItem("Snowflake", "AI Data Cloud & Lakehouse", tier_badge="CORE PLATFORM", logo="snowflake.svg", accent_key="accent"),
            TechLogoItem("dbt Labs", "Semantic Transformation & DDL", tier_badge="MODELING", logo="dbt.svg", accent_key="accent_secondary"),
            TechLogoItem("Apache Kafka", "Event Streaming & CDC", tier_badge="INGESTION", logo="kafka.svg", accent_key="primary"),
            TechLogoItem("Amazon S3", "Scalable Object Storage", tier_badge="STORAGE", logo="amazons3.svg", accent_key="accent"),
            TechLogoItem("HashiCorp Vault", "Secrets & Key Management", tier_badge="SECURITY", logo="vault.svg", accent_key="danger"),
            TechLogoItem("Streamlit", "Interactive Data Applications", tier_badge="SERVING", logo="trending-up", accent_key="accent"),
            TechLogoItem("Tableau", "Enterprise BI & Visualizations", tier_badge="ANALYTICS", logo="chart", accent_key="accent_secondary"),
            TechLogoItem("Python", "Advanced Analytics & Machine Learning", tier_badge="COMPUTE", logo="cpu", accent_key="primary"),
        ]

    content_left = Inches(0.80)
    content_top = Inches(1.80)
    total_w = Inches(11.733)
    total_h = Inches(5.00)

    cols = max(1, min(columns, len(items)))
    rows = max(1, (len(items) + cols - 1) // cols)

    gap_x = Inches(0.24)
    gap_y = Inches(0.22)
    card_w = (total_w - (gap_x * (cols - 1))) / cols
    card_h = (total_h - (gap_y * (rows - 1))) / rows

    for idx, itm in enumerate(items):
        r_idx = idx // cols
        c_idx = idx % cols
        cx = content_left + (c_idx * (card_w + gap_x))
        cy = content_top + (r_idx * (card_h + gap_y))

        accent_rgb = theme.get_rgb(itm.accent_key)
        card, stripe = add_card_with_top_stripe(
            slide,
            theme,
            cx,
            cy,
            card_w,
            card_h,
            accent_rgb=accent_rgb,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
        )

        # 1. Top right status pill
        pill_w = Inches(1.15)
        pill_h = Inches(0.22)
        _add_status_pill(
            slide,
            theme,
            cx + card_w - pill_w - Inches(0.12),
            cy + Inches(0.10),
            pill_w,
            pill_h,
            itm.tier_badge,
            font_size_pt=7.5,
            override_color_key=itm.accent_key,
        )

        # 2. Logo / Emblem Slot (top left)
        logo_w = Inches(1.10)
        logo_h = Inches(0.40)
        logo_left = cx + Inches(0.14)
        logo_top = cy + Inches(0.10)

        resolved_img = None
        if itm.logo:
            p_logo = Path("assets/logos") / itm.logo
            if not p_logo.exists():
                p_logo = Path(itm.logo)
            if p_logo.exists():
                if p_logo.suffix.lower() == ".svg":
                    try:
                        dest_png = Path("output/cache/logos") / f"{p_logo.stem}.png"
                        dest_png.parent.mkdir(parents=True, exist_ok=True)
                        if not dest_png.exists():
                            render_svg_to_png(p_logo.read_text(encoding="utf-8"), output_path=dest_png, size=256)
                        resolved_img = dest_png
                    except Exception as e:
                        logger.warning(f"Could not render svg logo {p_logo}: {e}")
                else:
                    resolved_img = p_logo

        if resolved_img and resolved_img.exists():
            img_l, img_t, img_w, img_h = _fit_image_in_box(resolved_img, logo_left, logo_top, logo_w, logo_h)
            slide.shapes.add_picture(str(resolved_img), img_l, img_t, width=img_w, height=img_h)
        else:
            badge_sh = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE,
                logo_left, logo_top, logo_w, logo_h
            )
            badge_sh.shadow.inherit = False
            badge_sh.fill.solid()
            badge_sh.fill.fore_color.rgb = theme.get_rgb("surface_muted")
            badge_sh.line.color.rgb = accent_rgb
            badge_sh.line.width = Pt(0.75)
            btf = badge_sh.text_frame
            btf.margin_left = btf.margin_right = btf.margin_top = btf.margin_bottom = 0
            bp = btf.paragraphs[0]
            bp.text = itm.name.upper()[:12]
            bp.alignment = PP_ALIGN.CENTER
            bp.font.name = theme.font_family_header
            bp.font.size = Pt(8.0)
            bp.font.bold = True
            bp.font.color.rgb = accent_rgb

        # 3. Card Typography
        tb_y = cy + Inches(0.56)
        tb_h = card_h - Inches(0.62)
        tb = slide.shapes.add_textbox(cx + Inches(0.14), tb_y, card_w - Inches(0.28), tb_h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_t = tf.paragraphs[0]
        p_t.text = itm.name
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(11.0 if rows <= 2 else 9.5)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")

        p_c = tf.add_paragraph()
        p_c.text = itm.category
        p_c.font.name = theme.font_family
        p_c.font.size = Pt(8.5 if rows <= 2 else 8.0)
        p_c.font.color.rgb = theme.get_rgb("secondary")
        p_c.space_before = Pt(2)

        if itm.description:
            p_d = tf.add_paragraph()
            p_d.text = itm.description
            p_d.font.name = theme.font_family
            p_d.font.size = Pt(8.0)
            p_d.font.color.rgb = theme.get_rgb("muted")
            p_d.space_before = Pt(4)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


def build_card_grid_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "STRATEGIC CAPABILITIES | CORE SERVICE OFFERINGS",
    action_title: str = "Comprehensive Enterprise Solutions Span Modern Infrastructure to Autonomous Intelligence",
    subtitle: Optional[str] = "Eight integrated core pillars deliver complete lifecycle support from strategic advisory to operational execution.",
    items: Optional[List[CardGridItem]] = None,
    columns: int = 4,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """Renders an N x M grid of structured capability cards with harmonized icons, top stripes, and bullets."""
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if not items:
        items = [
            CardGridItem("Cloud Infrastructure", "Multi-cloud architecture & migration", "cloud", ["Hybrid cloud orchestration", "Cost optimization (FinOps)", "Automated landing zones"], "accent", "PILLAR 01"),
            CardGridItem("Data & Artificial Intelligence", "Modern data stack & machine learning", "database", ["Snowflake AI Data Cloud", "dbt semantic engineering", "Cortex GenAI solutions"], "accent", "PILLAR 02"),
            CardGridItem("Cyber Security", "Zero-trust identity & governance", "shield", ["Enterprise RBAC & masking", "Threat posture defense", "SOC2 compliance auditing"], "danger", "PILLAR 03"),
            CardGridItem("Digital Workplace", "Modern collaboration platforms", "users", ["Microsoft 365 & Power Platform", "Streamlined B2B workflows", "Hybrid workforce agility"], "primary", "PILLAR 04"),
            CardGridItem("Enterprise Applications", "ERP & core transaction backbones", "layers", ["SAP ERP modernization", "CRM customer 360 views", "Supply chain integration"], "accent_secondary", "PILLAR 05"),
            CardGridItem("Business Process Automation", "Intelligent robotic workflow automation", "cpu", ["RPA process discovery", "Low-code application hubs", "End-to-end task automation"], "accent", "PILLAR 06"),
            CardGridItem("Managed IT Services", "24/7 mission-critical operations", "activity", ["SLA performance monitoring", "Preventative maintenance", "Incident remediation"], "primary", "PILLAR 07"),
            CardGridItem("IT Advisory & Consulting", "Strategic technology alignment", "target", ["Digital maturity assessment", "Cloud transition roadmaps", "Program governance assurance"], "accent", "PILLAR 08"),
        ]

    content_left = Inches(0.80)
    content_top = Inches(1.80)
    total_w = Inches(11.733)
    total_h = Inches(5.00)

    cols = max(1, min(columns, len(items)))
    rows = max(1, (len(items) + cols - 1) // cols)

    gap_x = Inches(0.24)
    gap_y = Inches(0.22)
    card_w = (total_w - (gap_x * (cols - 1))) / cols
    card_h = (total_h - (gap_y * (rows - 1))) / rows

    for idx, itm in enumerate(items):
        r_idx = idx // cols
        c_idx = idx % cols
        cx = content_left + (c_idx * (card_w + gap_x))
        cy = content_top + (r_idx * (card_h + gap_y))

        accent_rgb = theme.get_rgb(itm.accent_key)
        card, stripe = add_card_with_top_stripe(
            slide,
            theme,
            cx,
            cy,
            card_w,
            card_h,
            accent_rgb=accent_rgb,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
        )

        icon_dim = Inches(0.30)
        icon_x = cx + Inches(0.14)
        icon_y = cy + Inches(0.12)
        if itm.icon:
            try:
                icon_path = get_brand_icon(itm.icon, brand_color=accent_rgb, theme=theme)
                if icon_path and Path(icon_path).exists():
                    slide.shapes.add_picture(str(icon_path), icon_x, icon_y, width=icon_dim, height=icon_dim)
            except Exception as e:
                logger.warning(f"Failed to add card icon {itm.icon}: {e}")

        if itm.badge:
            pill_w = Inches(0.95)
            pill_h = Inches(0.20)
            _add_status_pill(
                slide,
                theme,
                cx + card_w - pill_w - Inches(0.12),
                cy + Inches(0.10),
                pill_w,
                pill_h,
                itm.badge,
                font_size_pt=7.0,
                override_color_key=itm.accent_key,
            )

        tb_x = cx + Inches(0.14)
        tb_y = cy + Inches(0.46)
        tb_w = card_w - Inches(0.28)
        tb_h = card_h - Inches(0.50)

        tb = slide.shapes.add_textbox(tb_x, tb_y, tb_w, tb_h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_title = tf.paragraphs[0]
        p_title.text = itm.title
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(10.0 if rows <= 2 else 9.0)
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")

        if itm.subtitle:
            p_sub = tf.add_paragraph()
            p_sub.text = itm.subtitle
            p_sub.font.name = theme.font_family
            p_sub.font.size = Pt(8.0)
            p_sub.font.color.rgb = theme.get_rgb("secondary")
            p_sub.space_before = Pt(2)

        for b in itm.bullets:
            _add_bullet_paragraph(
                tf,
                b,
                theme.font_family,
                font_size_pt=7.8 if rows <= 2 else 7.2,
                font_color=theme.get_rgb("secondary"),
                space_before_pt=2.5,
            )

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


def build_badge_matrix_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "COMPETENCY & CREDENTIALS | PARTNERSHIP TIERS",
    action_title: str = "Certified Industry Expertise Assures Technical Excellence and Rapid Delivery",
    subtitle: Optional[str] = "Tiered competency matrix validates advanced specialization across hyperscalers, lakehouse platforms, and governance frameworks.",
    sections: Optional[List[BadgeMatrixSection]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """Renders a clustered multi-column matrix of partner certifications and credentials."""
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if not sections:
        sections = [
            BadgeMatrixSection(
                section_title="Cloud & Data Lakehouse",
                accent_key="accent",
                badge_count_label="TIER 1 STATUS",
                items=[
                    {"name": "Snowflake", "level": "Select Services Partner", "domain": "Data Cloud & Analytics", "icon": "snowflake"},
                    {"name": "Amazon Web Services", "level": "Advanced Tier Services", "domain": "Cloud Migration & Storage", "icon": "aws"},
                    {"name": "Microsoft Azure", "level": "Solutions Partner", "domain": "Data & AI Modernization", "icon": "layers"},
                ]
            ),
            BadgeMatrixSection(
                section_title="Data Transformation & BI",
                accent_key="accent_secondary",
                badge_count_label="CERTIFIED PRACTICE",
                items=[
                    {"name": "dbt Labs", "level": "Preferred Partner", "domain": "Semantic Modeling", "icon": "dbt"},
                    {"name": "Tableau", "level": "Gold Reseller & Services", "domain": "Visual Intelligence", "icon": "trending-up"},
                    {"name": "Power BI", "level": "Enterprise Delivery Certified", "domain": "Self-Service Analytics", "icon": "activity"},
                ]
            ),
            BadgeMatrixSection(
                section_title="Security, Governance & CDC",
                accent_key="primary",
                badge_count_label="REGULATORY ASSURED",
                items=[
                    {"name": "HashiCorp Vault", "level": "Security Certified", "domain": "Secrets & Key Management", "icon": "lock"},
                    {"name": "Apache Kafka", "level": "Streaming Architecture", "domain": "Real-time CDC Pipelines", "icon": "zap"},
                    {"name": "SOC 2 Type II", "level": "Audited Controls", "domain": "Information Security Assurance", "icon": "shield"},
                ]
            ),
        ]

    content_left = Inches(0.80)
    content_top = Inches(1.80)
    total_w = Inches(11.733)
    total_h = Inches(5.00)

    num_cols = len(sections)
    gap_x = Inches(0.28)
    col_w = (total_w - (gap_x * (num_cols - 1))) / num_cols
    col_h = total_h

    for c_idx, sec in enumerate(sections):
        cx = content_left + (c_idx * (col_w + gap_x))
        cy = content_top

        accent_rgb = theme.get_rgb(sec.accent_key)
        card, stripe = add_card_with_top_stripe(
            slide,
            theme,
            cx,
            cy,
            col_w,
            col_h,
            accent_rgb=accent_rgb,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
        )

        hdr_tb = slide.shapes.add_textbox(cx + Inches(0.18), cy + Inches(0.14), col_w - Inches(0.36), Inches(0.60))
        htf = hdr_tb.text_frame
        htf.word_wrap = True
        htf.margin_left = htf.margin_right = htf.margin_top = htf.margin_bottom = 0

        hp1 = htf.paragraphs[0]
        hp1.text = sec.section_title
        hp1.font.name = theme.font_family_header
        hp1.font.size = Pt(11.0)
        hp1.font.bold = True
        hp1.font.color.rgb = theme.get_rgb("primary")

        if sec.badge_count_label:
            _add_status_pill(
                slide,
                theme,
                cx + col_w - Inches(1.60),
                cy + Inches(0.12),
                Inches(1.42),
                Inches(0.24),
                sec.badge_count_label,
                font_size_pt=7.5,
                override_color_key=sec.accent_key,
            )

        item_y = cy + Inches(0.85)
        item_gap = Inches(0.16)
        avail_h = col_h - Inches(1.00)
        num_items = len(sec.items)
        item_h = min(Inches(1.18), (avail_h - (item_gap * max(1, num_items - 1))) / max(1, num_items))

        for itm in sec.items:
            icard = add_card(
                slide,
                theme,
                cx + Inches(0.16),
                item_y,
                col_w - Inches(0.32),
                item_h,
                bg_color=theme.get_rgb("surface_muted"),
                border_color=theme.get_rgb("border"),
            )

            icon_w = Inches(0.32)
            icon_x = cx + Inches(0.28)
            icon_y = item_y + Inches(0.16)
            icon_name = itm.get("icon")
            if icon_name:
                try:
                    ipath = get_brand_icon(icon_name, brand_color=accent_rgb, theme=theme)
                    if ipath and Path(ipath).exists():
                        slide.shapes.add_picture(str(ipath), icon_x, icon_y, width=icon_w, height=icon_w)
                except Exception:
                    pass

            itb = slide.shapes.add_textbox(
                cx + Inches(0.68),
                item_y + Inches(0.10),
                col_w - Inches(0.90),
                item_h - Inches(0.20),
            )
            itf = itb.text_frame
            itf.word_wrap = True
            itf.margin_left = itf.margin_right = itf.margin_top = itf.margin_bottom = 0

            p_inm = itf.paragraphs[0]
            p_inm.text = itm.get("name", "")
            p_inm.font.name = theme.font_family_header
            p_inm.font.size = Pt(10.0)
            p_inm.font.bold = True
            p_inm.font.color.rgb = theme.get_rgb("primary")

            p_ilvl = itf.add_paragraph()
            p_ilvl.text = itm.get("level", "")
            p_ilvl.font.name = theme.font_family
            p_ilvl.font.size = Pt(8.5)
            p_ilvl.font.bold = True
            p_ilvl.font.color.rgb = accent_rgb
            p_ilvl.space_before = Pt(1.5)

            p_idom = itf.add_paragraph()
            p_idom.text = itm.get("domain", "")
            p_idom.font.name = theme.font_family
            p_idom.font.size = Pt(8.0)
            p_idom.font.color.rgb = theme.get_rgb("secondary")
            p_idom.space_before = Pt(1.5)

            item_y += item_h + item_gap

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

    _add_status_pill(
        slide,
        theme,
        left_x + iceberg_w - Inches(1.40),
        top_y + Inches(0.08),
        Inches(1.25),
        Inches(0.22),
        "VISIBLE INTERFACE",
        font_size_pt=7.0,
        override_color_key="accent",
    )

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

    _add_status_pill(
        slide,
        theme,
        left_x + iceberg_w - Inches(1.55),
        below_y + Inches(0.08),
        Inches(1.40),
        Inches(0.22),
        "CRITICAL FOUNDATION",
        font_size_pt=7.0,
        override_color_key="danger",
    )

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

    _add_status_pill(
        slide,
        theme,
        takeaway_x + takeaway_w - Inches(1.30),
        top_y + Inches(0.12),
        Inches(1.15),
        Inches(0.24),
        "KEY LESSON",
        font_size_pt=7.5,
        override_color_key="accent",
    )

    for bullet in takeaways:
        _add_bullet_paragraph(
            ttf,
            bullet,
            theme.font_family,
            font_size_pt=8.5,
            font_color=theme.get_rgb("secondary"),
            space_before_pt=8.0,
        )


# ============================================================================
# 14b. Project Kick-off, Agenda, Tabular Matrix & Closing Archetypes
# ============================================================================

@dataclass
class AgendaItem:
    num: str
    title: str
    description: Optional[str] = None
    badge: Optional[str] = None
    accent_key: str = "accent"


def build_agenda_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "PROJECT ALIGNMENT | EXECUTIVE AGENDA",
    action_title: str = "Comprehensive Project Alignment Across Governance, Deliverables, and Timelines",
    subtitle: Optional[str] = "Structured discussion sequence establishing strategic consensus and stage-gate readiness.",
    items: Optional[List[AgendaItem]] = None,
    columns: int = 2,
    current_idx: int = 2,
    total_slides: int = 19,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an executive table of contents / agenda slide with balanced multi-column cards.
    Each item features a crisp rectangular card, accent-tinted number box, bold title, and optional description.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if not items:
        items = [
            AgendaItem("01", "Project Initiation & Context", "Background, drivers, and executive sponsorship."),
            AgendaItem("02", "Strategic Objectives", "Core transformation goals and business value targets."),
            AgendaItem("03", "Stakeholders & Governance Roles", "Steering committee and PMO responsibilities."),
            AgendaItem("04", "Project Team & RACI", "Joint organization hierarchy and delivery pods."),
            AgendaItem("05", "Scope of Work & Workstreams", "Phased implementation boundaries and modules."),
            AgendaItem("06", "Deliverables & Artifacts", "Milestone acceptance documents and specs."),
            AgendaItem("07", "Project Assumptions", "Technical and operational baseline conditions."),
            AgendaItem("08", "Target Solution Architecture", "Snowflake platform and Streamlit serving tiers."),
            AgendaItem("09", "High-Level Phased Timeline", "Delivery roadmap from kick-off to go-live."),
            AgendaItem("10", "Detailed Execution Gantt", "Weekly activity scheduling and critical path."),
            AgendaItem("11", "Stage-Gate Milestones", "Contractual milestone dates and sign-off criteria."),
            AgendaItem("12", "Project Prerequisites", "Environment setup, credentials, and connectivity."),
            AgendaItem("13", "Communication & Collaboration", "Meeting cadence, status reporting, and channels."),
            AgendaItem("14", "Risk Register & Mitigations", "Active risk controls, mitigations, and owners."),
            AgendaItem("15", "Change Request Procedure", "Scope change governance and escalation gates."),
            AgendaItem("16", "Q&A & Executive Discussion", "Open forum for clarification and final alignment."),
        ]

    total_items = len(items)
    cols = max(1, min(columns, 4))
    items_per_col = (total_items + cols - 1) // cols

    canvas_w = Inches(11.733)
    start_x = Inches(0.80)
    start_y = Inches(1.80)
    avail_h = Inches(5.00)

    gap_x = Inches(0.35)
    col_w = (canvas_w - (cols - 1) * gap_x) / cols

    row_gap = Inches(0.08) if items_per_col > 6 else Inches(0.12)
    card_h = min(Inches(1.05), (avail_h - (items_per_col - 1) * row_gap) / items_per_col)

    for i, item in enumerate(items):
        c_idx = i // items_per_col
        r_idx = i % items_per_col

        card_x = start_x + c_idx * (col_w + gap_x)
        card_y = start_y + r_idx * (card_h + row_gap)

        # Card container
        add_card(
            slide,
            theme,
            card_x,
            card_y,
            col_w,
            card_h,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            force_rectangle=True,
        )

        # Left Number Box
        num_w = Inches(0.65) if cols <= 2 else Inches(0.55)
        num_bg = theme.get_rgb("surface_muted")
        num_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, card_x, card_y, num_w, card_h)
        num_box.shadow.inherit = False
        num_box.fill.solid()
        num_box.fill.fore_color.rgb = num_bg
        num_box.line.fill.background()

        ntf = num_box.text_frame
        ntf.word_wrap = False
        ntf.margin_left = ntf.margin_right = ntf.margin_top = ntf.margin_bottom = 0
        np = ntf.paragraphs[0]
        np.text = str(item.num)
        np.alignment = PP_ALIGN.CENTER
        np.font.name = theme.font_family_header
        np.font.size = Pt(11.0 if cols > 2 or items_per_col > 6 else 12.5)
        np.font.bold = True
        np.font.color.rgb = theme.get_rgb(item.accent_key if item.accent_key else "accent")

        # Text container
        tb_left = card_x + num_w + Inches(0.12)
        tb_w = col_w - num_w - Inches(0.20)
        if item.badge:
            tb_w -= Inches(1.20)

        tb = slide.shapes.add_textbox(tb_left, card_y + Inches(0.04), tb_w, card_h - Inches(0.08))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        tp = tf.paragraphs[0]
        tp.text = item.title
        tp.font.name = theme.font_family_header
        title_font_pt = 10.0 if (items_per_col > 7 or cols > 2) else 11.0
        tp.font.size = Pt(title_font_pt)
        tp.font.bold = True
        tp.font.color.rgb = theme.get_rgb("primary")

        if item.description:
            dp = tf.add_paragraph()
            dp.text = item.description
            dp.font.name = theme.font_family
            desc_font_pt = 8.0 if (items_per_col > 7 or cols > 2) else 8.5
            dp.font.size = Pt(desc_font_pt)
            dp.font.color.rgb = theme.get_rgb("secondary")
            dp.space_before = Pt(1)

        if item.badge:
            _add_status_pill(
                slide,
                theme,
                card_x + col_w - Inches(1.15),
                card_y + (card_h - Inches(0.22)) / 2,
                Inches(1.05),
                Inches(0.22),
                item.badge,
                font_size_pt=7.5,
            )

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


@dataclass
class TableColumnDef:
    header: str
    width: float  # In inches
    align: str = "LEFT"  # "LEFT", "CENTER", "RIGHT"
    is_status: bool = False
    is_index: bool = False


def build_table_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "PROJECT GOVERNANCE | STAGE-GATE REGISTER",
    action_title: str = "Structured Governance Register Establishes Accountabilities and Timelines",
    subtitle: Optional[str] = "Detailed tracking matrix with designated owners, baseline targets, and delivery statuses.",
    columns: Optional[List[TableColumnDef]] = None,
    rows: Optional[List[List[Any]]] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an executive consulting table/matrix slide using sharp vector cards.
    Includes primary color header band, alternating row shading, dynamic status pills, and footnotes.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if not columns or not rows:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    start_x = Inches(0.80)
    total_w = Inches(11.733)
    header_y = Inches(1.72)
    header_h = Inches(0.38)

    # Normalize column widths to sum exactly to total_w
    col_widths_sum = sum(c.width for c in columns)
    scale_w = (total_w.inches / col_widths_sum) if col_widths_sum > 0 else 1.0
    scaled_widths = [Inches(c.width * scale_w) for c in columns]

    # Header Band
    hdr_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, header_y, total_w, header_h)
    hdr_card.shadow.inherit = False
    hdr_card.fill.solid()
    hdr_card.fill.fore_color.rgb = theme.get_rgb("primary")
    hdr_card.line.fill.background()

    cur_x = start_x
    for c_idx, col in enumerate(columns):
        cw = scaled_widths[c_idx]
        tb = slide.shapes.add_textbox(cur_x + Inches(0.08), header_y + Inches(0.06), cw - Inches(0.16), header_h - Inches(0.12))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = col.header.upper()
        if col.align == "CENTER":
            p.alignment = PP_ALIGN.CENTER
        elif col.align == "RIGHT":
            p.alignment = PP_ALIGN.RIGHT
        else:
            p.alignment = PP_ALIGN.LEFT
        p.font.name = theme.font_family_header
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        cur_x += cw

    # Rows
    num_rows = len(rows)
    avail_row_h = Inches(4.70) if not footnote else Inches(4.45)
    row_gap = Inches(0.05) if num_rows > 8 else Inches(0.07)
    row_h = min(Inches(0.46), max(Inches(0.28), (avail_row_h - (num_rows - 1) * row_gap) / num_rows))

    row_start_y = header_y + header_h + Inches(0.08)

    status_keywords = {
        "COMPLETE", "COMPLETED", "IN PROGRESS", "ON TRACK", "RESCHEDULED", "PLANNED",
        "CRITICAL GATE", "MILESTONE GATE", "HIGH", "MEDIUM", "LOW", "SIGNED-OFF",
        "MUTUAL", "DAILY", "WEEKLY", "AS NEEDED", "OPEN", "RESOLVED"
    }

    font_size_pt = 9.0 if num_rows > 9 else (9.5 if num_rows > 6 else 10.5)

    for r_idx, row in enumerate(rows):
        cur_ry = row_start_y + r_idx * (row_h + row_gap)
        is_alt = (r_idx % 2 != 0)
        bg_color = theme.get_rgb("surface_muted") if is_alt else theme.get_rgb("surface")

        add_card(
            slide,
            theme,
            start_x,
            cur_ry,
            total_w,
            row_h,
            bg_color=bg_color,
            border_color=theme.get_rgb("border"),
            force_rectangle=True,
        )

        cur_cx = start_x
        for c_idx, col in enumerate(columns):
            cw = scaled_widths[c_idx]
            cell_val = row[c_idx] if c_idx < len(row) else ""
            cell_str = str(cell_val).strip()

            is_status_col = col.is_status or (cell_str.upper() in status_keywords and len(cell_str) <= 20)

            if is_status_col and cell_str:
                pill_w = min(cw - Inches(0.20), Inches(1.55))
                pill_h = min(row_h - Inches(0.08), Inches(0.25))
                pill_x = cur_cx + (cw - pill_w) / 2
                pill_y = cur_ry + (row_h - pill_h) / 2
                _add_status_pill(
                    slide=slide,
                    theme=theme,
                    left=pill_x,
                    top=pill_y,
                    width=pill_w,
                    height=pill_h,
                    status=cell_str,
                    font_size_pt=max(7.0, font_size_pt - 1.5),
                )
            else:
                tb = slide.shapes.add_textbox(cur_cx + Inches(0.08), cur_ry + Inches(0.04), cw - Inches(0.16), row_h - Inches(0.08))
                tf = tb.text_frame
                tf.word_wrap = True
                tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
                p = tf.paragraphs[0]
                p.text = cell_str
                if col.align == "CENTER":
                    p.alignment = PP_ALIGN.CENTER
                elif col.align == "RIGHT":
                    p.alignment = PP_ALIGN.RIGHT
                else:
                    p.alignment = PP_ALIGN.LEFT

                if col.is_index or (c_idx == 0 and cell_str.isdigit()):
                    p.font.name = theme.font_family_header
                    p.font.size = Pt(font_size_pt + 0.5)
                    p.font.bold = True
                    p.font.color.rgb = theme.get_rgb("accent")
                else:
                    p.font.name = theme.font_family
                    p.font.size = Pt(font_size_pt)
                    if c_idx == 1:
                        p.font.bold = True
                        p.font.color.rgb = theme.get_rgb("primary")
                    else:
                        p.font.color.rgb = theme.get_rgb("secondary")

            cur_cx += cw

    if footnote:
        foot_y = row_start_y + num_rows * (row_h + row_gap) + Inches(0.04)
        tb_fn = slide.shapes.add_textbox(start_x, foot_y, total_w, Inches(0.25))
        tf_fn = tb_fn.text_frame
        tf_fn.word_wrap = False
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.5)
        p_fn.font.color.rgb = theme.get_rgb("muted")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


def build_thank_you_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "ENGAGEMENT WRAP-UP | THANK YOU",
    title: str = "Thank You",
    subtitle: Optional[str] = "Partnering to accelerate enterprise data modernization with Snowflake AI Data Cloud.",
    contacts: Optional[List[Dict[str, str]]] = None,
    company: str = "PT Metrodata Electronics Tbk  |  PT Mitra Integrasi Informatika",
    office: str = "APL Tower 37th Floor, Jl. Letjen S. Parman Kav. 28, Jakarta Barat 11470",
    current_idx: int = 19,
    total_slides: int = 19,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
) -> Any:
    """
    Renders an executive corporate closing slide featuring dual brand vertical stripes
    (1 red : 2 blue ratio), prominent typography, contact cards with top stripes, and corporate footer.
    """
    slide = add_slide_with_background(prs, theme)

    stripe_top = Inches(1.80)
    stripe_height = Inches(4.50)
    stripe_left = Inches(0.80)
    red_w = Inches(0.045)
    blue_w = Inches(0.090)

    # 1. Dual Vertical Brand Stripes (1 Red : 2 Blue ratio)
    s_red = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, stripe_left, stripe_top, red_w, stripe_height)
    s_red.shadow.inherit = False
    s_red.fill.solid()
    s_red.fill.fore_color.rgb = theme.get_rgb("accent_secondary", "#DC2626")
    s_red.line.fill.background()

    s_blue = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, stripe_left + red_w, stripe_top, blue_w, stripe_height)
    s_blue.shadow.inherit = False
    s_blue.fill.solid()
    s_blue.fill.fore_color.rgb = theme.get_rgb("accent", "#0052CC")
    s_blue.line.fill.background()

    # 2. Text Content Area
    text_left = stripe_left + red_w + blue_w + Inches(0.35)
    text_width = Inches(11.20)
    tb = slide.shapes.add_textbox(text_left, Inches(1.80), text_width, Inches(1.70))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    p_tr = tf.paragraphs[0]
    p_tr.text = tracker.upper()
    p_tr.font.name = theme.font_family_header
    p_tr.font.size = Pt(11.0)
    p_tr.font.bold = True
    p_tr.font.color.rgb = theme.get_rgb("accent")

    p_t = tf.add_paragraph()
    p_t.text = title
    p_t.font.name = theme.font_family_header
    p_t.font.size = Pt(36.0)
    p_t.font.bold = True
    p_t.font.color.rgb = theme.get_rgb("primary")
    p_t.space_before = Pt(6)

    p_s = tf.add_paragraph()
    p_s.text = subtitle or "Delivering Data-Driven Value & Predictive Intelligence with Cloud Analytics Platform."
    p_s.font.name = theme.font_family
    p_s.font.size = Pt(13.0)
    p_s.font.color.rgb = theme.get_rgb("secondary")
    p_s.space_before = Pt(10)

    # 3. Contact Cards
    if not contacts:
        contacts = [
            {"name": "Agus Suhanto", "role": "Project Manager, MII", "email": "agus.suhanto@mii.co.id"},
            {"name": "Dian Eka Kusumawati", "role": "Account Manager, MII", "email": "dian.eka@mii.co.id"},
            {"name": "Vicko Bhayyu", "role": "Technical Lead, MII", "email": "vicko.bhayyu@mii.co.id"},
        ]

    num_c = len(contacts)
    card_gap = Inches(0.25)
    card_w = min(Inches(5.40), (text_width - (num_c - 1) * card_gap) / num_c)
    card_h = Inches(1.50)
    card_y = Inches(3.85)

    for i, c in enumerate(contacts[:4]):
        cx = text_left + i * (card_w + card_gap)
        acc_key = c.get("accent_key", "accent" if i == 0 else "accent_teal")
        acc_col = theme.get_rgb(acc_key, "#0052CC")

        add_card_with_top_stripe(
            slide=slide,
            theme=theme,
            left=cx,
            top=card_y,
            width=card_w,
            height=card_h,
            accent_rgb=acc_col,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            stripe_height_in=0.06,
        )

        ctb = slide.shapes.add_textbox(cx + Inches(0.18), card_y + Inches(0.16), card_w - Inches(0.36), card_h - Inches(0.25))
        ctf = ctb.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0

        cp1 = ctf.paragraphs[0]
        cp1.text = c.get("name", "")
        cp1.font.name = theme.font_family_header
        cp1.font.size = Pt(13.0)
        cp1.font.bold = True
        cp1.font.color.rgb = theme.get_rgb("primary")

        cp2 = ctf.add_paragraph()
        cp2.text = c.get("role", "")
        cp2.font.name = theme.font_family
        cp2.font.size = Pt(10.5)
        cp2.font.color.rgb = theme.get_rgb("accent")
        cp2.space_before = Pt(3)

        if c.get("email"):
            cp3 = ctf.add_paragraph()
            cp3.text = f"Email: {c['email']}"
            cp3.font.name = theme.font_family
            cp3.font.size = Pt(10.0)
            cp3.font.color.rgb = theme.get_rgb("secondary")
            cp3.space_before = Pt(4)

    # 4. Corporate Address Footer
    otb = slide.shapes.add_textbox(text_left, Inches(5.65), text_width, Inches(0.60))
    otf = otb.text_frame
    otf.word_wrap = True
    otf.margin_left = otf.margin_right = otf.margin_top = otf.margin_bottom = 0
    op1 = otf.paragraphs[0]
    op1.text = f"{company}  |  {office}"
    op1.font.name = theme.font_family
    op1.font.size = Pt(10.0)
    op1.font.color.rgb = theme.get_rgb("secondary")

    op2 = otf.add_paragraph()
    op2.text = notice
    op2.font.name = theme.font_family
    op2.font.size = Pt(9.0)
    op2.font.color.rgb = theme.get_rgb("muted")
    op2.space_before = Pt(3)

    return slide


# ============================================================================
# 15. High-Level Consulting Archetype Deck Generator
# ============================================================================

class ConsultingDeckBuilder:
    """High-level builder for assembling full multi-slide consulting decks."""

    def __init__(self, theme: Union[str, Theme] = "default") -> None:
        if isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = theme
        self.prs = create_presentation(self.theme)

    def add_cover_slide(
        self,
        title: str = "Enterprise Modernization Blueprint",
        subtitle: Optional[str] = "Strategic cloud transformation, data lakehouse architecture, and operational runbook.",
        client: str = "Enterprise Client",
        vendor: str = "Metrodata Consulting",
        product: Optional[str] = "Snowflake AI Data Cloud",
        date_str: Optional[str] = None,
        tracker: str = "STRATEGIC ENGAGEMENT DELIVERABLE",
        client_logo_path: Optional[Union[str, Path]] = None,
        vendor_logo_path: Optional[Union[str, Path]] = None,
        product_logo_path: Optional[Union[str, Path]] = None,
        client_sublabel: str = "Steering Committee & Executive Sponsors",
        vendor_sublabel: str = "Data & AI Modernization Practice",
    ) -> Any:
        return build_cover_slide(
            prs=self.prs,
            theme=self.theme,
            title=title,
            subtitle=subtitle,
            client=client,
            vendor=vendor,
            product=product,
            date_str=date_str,
            tracker=tracker,
            client_logo_path=client_logo_path,
            vendor_logo_path=vendor_logo_path,
            product_logo_path=product_logo_path,
            client_sublabel=client_sublabel,
            vendor_sublabel=vendor_sublabel,
        )

    def add_hero_cover_slide(
        self,
        title: str = "Enterprise Modernization Blueprint",
        subtitle: Optional[str] = "Strategic cloud transformation, data lakehouse architecture, and operational runbook.",
        client: str = "[CLIENT_COMPANY_NAME]",
        vendor: str = "PT Metrodata Electronics Tbk",
        product: Optional[str] = "Snowflake AI Data Cloud",
        date_str: Optional[str] = "September 2026",
        tracker: str = "ENTERPRISE TRANSFORMATION BLUEPRINT  |  PROJECT ENGAGEMENT",
        hero_image_path: Optional[Union[str, Path]] = None,
        hero_height: float = 3.65,
        scrim_alpha: float = 0.28,
        client_logo_path: Optional[Union[str, Path]] = None,
        vendor_logo_path: Optional[Union[str, Path]] = None,
        product_logo_path: Optional[Union[str, Path]] = None,
        client_sublabel: str = "Steering Committee & Executive Sponsors",
        vendor_sublabel: str = "Data & AI Modernization Practice",
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
            client_logo_path=client_logo_path,
            vendor_logo_path=vendor_logo_path,
            product_logo_path=product_logo_path,
            client_sublabel=client_sublabel,
            vendor_sublabel=vendor_sublabel,
        )

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
            total_slides=idx,
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
            "total_slides": idx,
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
            total_slides=idx,
        )

    def add_chapter_divider_slide(
        self,
        tracker: str = "PHASE 02: ARCHITECTURE & PLANNING",
        title: str = "Modern Cloud Data Platform Architecture",
        subtitle: Optional[str] = "End-to-end data pipelines, staging lakehouse, and analytics delivery.",
        hero_image_path: Optional[Union[str, Path]] = None,
        logo_path: Optional[Union[str, Path]] = None,
        division_tag: Optional[str] = "BAS Division  |  Data & AI Practice",
        tagline: Optional[str] = None,
        scrim_alpha: float = 0.45,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_chapter_divider_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            title=title,
            subtitle=subtitle,
            hero_image_path=hero_image_path,
            logo_path=logo_path,
            division_tag=division_tag,
            tagline=tagline,
            scrim_alpha=scrim_alpha,
            current_idx=idx,
            total_slides=idx,
            show_footer=False,
        )

    def add_chevron_process_slide(
        self,
        tracker: str = "Execution Roadmap & Delivery Phases",
        action_title: str = "Phased Execution Roadmap Delivers Accelerated Value Across Four Controlled Horizons",
        subtitle: Optional[str] = "Sequential progression transitions foundation infrastructure into production analytics.",
        steps: Optional[List[ProcessChevronStep]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_chevron_process_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            steps=steps,
            current_idx=idx,
            total_slides=idx,
        )

    def add_split_hero_slide(
        self,
        tracker: str = "Executive Synthesis & Core Impact",
        action_title: str = "Modern Data Architecture Unlocks High-Yield Operational Transformation",
        subtitle: Optional[str] = "Centralized lakehouse foundation drives immediate cost avoidance and predictive analytics velocity.",
        hero_stat: str = "$14.8M",
        hero_stat_label: str = "Annualized Business Value",
        hero_stat_subtext: Optional[str] = "Projected 3-year cumulative ROI with 4.2x payback across supply chain and analytics operations.",
        blocks: Optional[List[SplitHeroBlock]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_split_hero_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            hero_stat=hero_stat,
            hero_stat_label=hero_stat_label,
            hero_stat_subtext=hero_stat_subtext,
            blocks=blocks,
            current_idx=idx,
            total_slides=idx,
        )

    def add_gap_analysis_slide(
        self,
        tracker: str = "Architecture Gap Analysis  |  Current vs. Target State",
        action_title: str = "Modernization Closes Critical Gaps Between Legacy Constraints and Future Target State",
        subtitle: Optional[str] = "Systematic transformation resolves batch latency, data silos, and manual governance overhead.",
        dimensions: Optional[List[GapDimensionData]] = None,
        as_is_header: str = "CURRENT STATE (AS-IS)",
        to_be_header: str = "TARGET ARCHITECTURE (TO-BE)",
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_gap_analysis_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            dimensions=dimensions,
            as_is_header=as_is_header,
            to_be_header=to_be_header,
            current_idx=idx,
            total_slides=idx,
        )

    def add_equity_corporate_tree_slide(
        self,
        tracker: str = "CORPORATE GOVERNANCE | EQUITY STRUCTURE",
        action_title: str = "Metrodata Group Operates Multi-Tier Operating Subsidiaries and Specialized JVs",
        subtitle: Optional[str] = "PT Metrodata Electronics Tbk (MTDL) maintains controlling equity across core ICT distribution, solutions, and digital consulting entities.",
        tree_data: Optional[EquityTreeData] = None,
        footnote: Optional[str] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        if tree_data and footnote:
            tree_data.footnote = footnote
        return build_equity_corporate_tree_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            tree_data=tree_data,
            current_idx=idx,
            total_slides=idx,
        )

    def add_browser_mockup_slide(
        self,
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
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_browser_mockup_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            screenshot_path=screenshot_path,
            url=url,
            telemetry_badges=telemetry_badges,
            theme_mode=theme_mode,
            aspect_ratio=aspect_ratio,
            target_dpi=target_dpi,
            takeaways_title=takeaways_title,
            takeaways=takeaways,
            current_idx=idx,
            total_slides=idx,
        )

    def add_timeline_gantt_slide(
        self,
        tracker: str = "DELIVERY ROADMAP | PROJECT EXECUTION",
        action_title: str = "Phased Execution Plan Ensures Iterative Milestone Realization Across 12 Weeks",
        subtitle: Optional[str] = "Integrated schedule coordinating foundational lakehouse infrastructure, dbt transformations, and Streamlit delivery.",
        gantt_data: Optional[GanttTimelineData] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_timeline_gantt_slide(
            prs_or_slide=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            gantt_data=gantt_data,
            current_idx=idx,
            total_slides=idx,
        )

    def add_feature_matrix_slide(
        self,
        tracker: str = "ARCHITECTURE EVALUATION | PLATFORM BENCHMARK",
        action_title: str = "Snowflake AI Data Cloud Demonstrates Superior Capabilities Across Core Evaluation Criteria",
        subtitle: Optional[str] = "Multi-dimensional comparative assessment evaluating compute elasticity, data governance, and native AI integration.",
        matrix_data: Optional[FeatureMatrixData] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_feature_matrix_slide(
            prs_or_slide=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            matrix_data=matrix_data,
            current_idx=idx,
            total_slides=idx,
        )

    def add_tech_logo_grid_slide(
        self,
        tracker: str = "TECHNOLOGY PORTFOLIO | ENTERPRISE ECOSYSTEM",
        action_title: str = "Curated Best-of-Breed Technology Stack Delivers Governed High-Performance Analytics",
        subtitle: Optional[str] = "Standardized technology matrix spanning ingestion, lakehouse storage, transformation, and semantic delivery.",
        items: Optional[List[TechLogoItem]] = None,
        columns: int = 4,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_tech_logo_grid_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            items=items,
            columns=columns,
            current_idx=idx,
            total_slides=idx,
        )

    def add_card_grid_slide(
        self,
        tracker: str = "STRATEGIC CAPABILITIES | CORE SERVICE OFFERINGS",
        action_title: str = "Comprehensive Enterprise Solutions Span Modern Infrastructure to Autonomous Intelligence",
        subtitle: Optional[str] = "Eight integrated core pillars deliver complete lifecycle support from strategic advisory to operational execution.",
        items: Optional[List[CardGridItem]] = None,
        columns: int = 4,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_card_grid_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            items=items,
            columns=columns,
            current_idx=idx,
            total_slides=idx,
        )

    def add_badge_matrix_slide(
        self,
        tracker: str = "COMPETENCY & CREDENTIALS | PARTNERSHIP TIERS",
        action_title: str = "Certified Industry Expertise Assures Technical Excellence and Rapid Delivery",
        subtitle: Optional[str] = "Tiered competency matrix validates advanced specialization across hyperscalers, lakehouse platforms, and governance frameworks.",
        sections: Optional[List[BadgeMatrixSection]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_badge_matrix_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            sections=sections,
            current_idx=idx,
            total_slides=idx,
        )

    def add_iceberg_concept_slide(
        self,
        tracker: str = "STRATEGIC RATIONALE | ARCHITECTURE FOUNDATION",
        action_title: str = "Modern Data Platform Architecture Solves the Critical Subsurface Foundation Gap",
        subtitle: Optional[str] = "While executives interact with surface dashboards, 85% of analytical resilience depends on robust foundation engineering.",
        visible_items: Optional[List[Dict[str, str]]] = None,
        subsurface_items: Optional[List[Dict[str, str]]] = None,
        takeaways: Optional[List[str]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_iceberg_concept_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            visible_items=visible_items,
            subsurface_items=subsurface_items,
            takeaways=takeaways,
            current_idx=idx,
            total_slides=idx,
        )

    def update_pagination(self) -> None:
        """
        Post-processes all slides to ensure bottom footer pagination (e.g. '02 / 07')
        accurately reflects the total slide count across the entire deck.
        Preserves existing font styling, size, boldness, and color.
        """
        import re
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
        """Save presentation deck to the specified path after synchronizing pagination and substituting slugs."""
        self.update_pagination()
        if engagement_context is not None:
            from src.core.slug_registry import substitute_slugs_in_presentation
            substitute_slugs_in_presentation(self.prs, engagement_context)
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(p))
        return p

