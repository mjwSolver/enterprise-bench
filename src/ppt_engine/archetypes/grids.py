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
    add_card_with_harmonized_icon, add_slide_footer, _interpolate_color, _get_contrast_text_color,
    _add_status_pill, _add_bullet_paragraph, _fit_image_in_box,
)

logger = logging.getLogger(__name__)

class SplitHeroBlock:
    """Content definition for a single narrative block in Split-Hero slide."""
    title: str                              # e.g. "Enterprise Data Ingestion"
    description: str                        # e.g. "Automated CDC pipelines and Snowpipe streaming..."
    metric_badge: Optional[str] = None      # e.g. "+98% Latency Drop"
    category_tag: Optional[str] = None      # e.g. "STREAM 01"
    badge_variant: Optional[str] = None     # e.g. "danger", "warning", "success", "accent"


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
    source: Optional[str] = None,
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

    # Inside Left Hero Card: Typographic Stat Frame
    h_tb = slide.shapes.add_textbox(hero_x + Inches(0.28), content_y + Inches(0.32), hero_w - Inches(0.56), Inches(1.85))
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

    # Native DrawingML Hairline Divider inside hero card (replaces broken text em-dash divider)
    hero_div_y = content_y + Inches(2.32)
    h_div = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        hero_x + Inches(0.28),
        hero_div_y,
        hero_w - Inches(0.56),
        Pt(0.75),
    )
    h_div.shadow.inherit = False
    h_div.fill.solid()
    h_div.fill.fore_color.rgb = hex_to_rgb("#334155")
    h_div.line.fill.background()

    # Subtext Narrative Frame
    if hero_stat_subtext:
        sub_tb = slide.shapes.add_textbox(
            hero_x + Inches(0.28),
            hero_div_y + Inches(0.18),
            hero_w - Inches(0.56),
            content_h - (hero_div_y - content_y) - Inches(0.36),
        )
        sub_tf = sub_tb.text_frame
        sub_tf.word_wrap = True
        sub_tf.margin_left = sub_tf.margin_right = sub_tf.margin_top = sub_tf.margin_bottom = 0
        p_sub = sub_tf.paragraphs[0]
        p_sub.text = hero_stat_subtext
        p_sub.font.name = theme.font_family
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = hex_to_rgb("#CBD5E1")

    # 2. Right 2/3 Unbordered Narrative Detail Area
    if not blocks:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
        return slide

    right_x = Inches(4.75)
    right_w = Inches(7.783)
    n_blocks = len(blocks)
    block_h = content_h / n_blocks

    for b_idx, block in enumerate(blocks):
        b_y = content_y + b_idx * block_h

        # ---------------------------------------------------------------------
        # Decoupled Title & Status Pill Layout (Zero Spatial Collision)
        # ---------------------------------------------------------------------
        has_badge = bool(block.metric_badge)
        pill_w = Inches(1.8) if has_badge else Inches(0)
        pill_h = Inches(0.34)
        pill_gap = Inches(0.20) if has_badge else Inches(0)

        title_w = right_w - pill_w - pill_gap if has_badge else right_w
        title_h = Inches(0.48)

        # Title Text Box (Strictly bounded to left of pill)
        title_tb = slide.shapes.add_textbox(right_x, b_y + Inches(0.08), title_w, title_h)
        title_tf = title_tb.text_frame
        title_tf.word_wrap = True
        title_tf.margin_left = title_tf.margin_right = title_tf.margin_top = title_tf.margin_bottom = 0

        p_title = title_tf.paragraphs[0]
        p_title.text = block.title
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(13.5)
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")

        # Metric Pill on the far right (Dynamic 3-Tier Semantic Severity)
        if has_badge and block.metric_badge:
            pill_x = right_x + right_w - pill_w
            pill_y = b_y + Inches(0.08)
            pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, pill_x, pill_y, pill_w, pill_h)
            pill.shadow.inherit = False
            pill.fill.solid()

            # Dynamic 3-Tier Semantic Severity Mapping
            b_text = block.metric_badge.upper()
            variant = getattr(block, "badge_variant", None) or ""

            if variant == "danger" or any(k in b_text for k in ("DEFECT", "P1", "BLOCKER", "CRITICAL", "ERROR", "BREACH")):
                fill_color = theme.get_rgb("badge_red_fill")
                border_color = theme.get_rgb("badge_red_text")
                text_color = theme.get_rgb("badge_red_text")
            elif variant == "warning" or any(k in b_text for k in ("LOCK", "WAIT", "BOTTLENECK", "WARNING", "DEBT", "RISK")):
                fill_color = theme.get_rgb("badge_amber_fill")
                border_color = theme.get_rgb("badge_amber_text")
                text_color = theme.get_rgb("badge_amber_text")
            elif variant == "success" or any(k in b_text for k in ("TARGET", "RESOLVED", "PARITY", "OPTIMAL", "SUCCESS")):
                fill_color = theme.get_rgb("badge_green_fill")
                border_color = theme.get_rgb("badge_green_text")
                text_color = theme.get_rgb("badge_green_text")
            else:
                fill_color = theme.get_rgb("badge_blue_fill")
                border_color = theme.get_rgb("accent")
                text_color = theme.get_rgb("primary")

            pill.fill.fore_color.rgb = fill_color
            pill.line.color.rgb = border_color
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
            p_pill.font.color.rgb = text_color

        # Description Body (Placed strictly below header row across full width)
        desc_y = b_y + Inches(0.62)
        desc_h = block_h - (desc_y - b_y) - Inches(0.12)
        desc_tb = slide.shapes.add_textbox(right_x, desc_y, right_w, desc_h)
        desc_tf = desc_tb.text_frame
        desc_tf.word_wrap = True
        desc_tf.margin_left = desc_tf.margin_right = desc_tf.margin_top = desc_tf.margin_bottom = 0

        p_desc = desc_tf.paragraphs[0]
        p_desc.text = ""
        append_formatted_runs(
            paragraph=p_desc,
            text=str(block.description or ""),
            font_name=theme.font_family,
            font_size_pt=10.5,
            font_color=theme.get_rgb("secondary"),
            lead_color=theme.get_rgb("primary"),
            auto_colon_lead=True,
        )

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

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


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
    metric: Optional[str] = None
    metric_label: Optional[str] = None
    widget: Optional[Dict[str, Any]] = None


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
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
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
    total_h = Inches(4.35) if takeaway else Inches(5.00)

    cols = max(1, min(columns, len(items)))
    rows = max(1, (len(items) + cols - 1) // cols)

    if cols == 1:
        gap_y = Inches(0.18)
        card_h = (total_h - (gap_y * (rows - 1))) / rows
        for idx, itm in enumerate(items):
            cy = content_top + idx * (card_h + gap_y)
            cx = content_left
            accent_rgb = theme.get_rgb(itm.accent_key)

            # Card container
            add_card(
                slide,
                theme,
                cx,
                cy,
                total_w,
                card_h,
                bg_color=theme.get_rgb("surface"),
                border_color=theme.get_rgb("border"),
                border_width_pt=1.0,
                force_rectangle=True,
            )
            # Left focus indicator bar
            left_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cy, Pt(4.5), card_h)
            left_stripe.shadow.inherit = False
            left_stripe.fill.solid()
            left_stripe.fill.fore_color.rgb = accent_rgb
            left_stripe.line.fill.background()

            # Left column: Title & Subtitle (w = 3.30")
            tb_title = slide.shapes.add_textbox(cx + Inches(0.25), cy + Inches(0.10), Inches(3.30), card_h - Inches(0.20))
            tf_title = tb_title.text_frame
            tf_title.word_wrap = True
            tf_title.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0

            p_t = tf_title.paragraphs[0]
            p_t.text = itm.title
            p_t.font.name = theme.font_family_header
            p_t.font.size = Pt(13.0)
            p_t.font.bold = True
            p_t.font.color.rgb = theme.get_rgb("primary")

            if itm.subtitle:
                p_s = tf_title.add_paragraph()
                p_s.text = itm.subtitle
                p_s.font.name = theme.font_family
                p_s.font.size = Pt(9.5)
                p_s.font.color.rgb = theme.get_rgb("secondary")
                p_s.space_before = Pt(4)

            # Center column: Metric Area directly on card canvas (no nested box, no stripe)
            met_box_x = cx + Inches(3.75)
            met_box_w = Inches(2.50)
            met_box_h = card_h - Inches(0.20)
            met_box_y = cy + Inches(0.10)

            # Vertical divider before metric
            div1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, met_box_x - Inches(0.15), cy + Inches(0.12), Pt(0.75), card_h - Inches(0.24))
            div1.shadow.inherit = False
            div1.fill.solid()
            div1.fill.fore_color.rgb = theme.get_rgb("border")
            div1.line.fill.background()

            met_tb = slide.shapes.add_textbox(met_box_x, met_box_y, met_box_w, met_box_h)
            met_tf = met_tb.text_frame
            met_tf.word_wrap = True
            met_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            met_tf.margin_left = met_tf.margin_right = met_tf.margin_top = met_tf.margin_bottom = 0

            p_met = met_tf.paragraphs[0]
            p_met.text = itm.metric or ""
            p_met.font.name = theme.font_family_header
            p_met.font.size = Pt(26.0)
            p_met.font.bold = True
            p_met.font.color.rgb = accent_rgb

            if itm.metric_label:
                p_ml = met_tf.add_paragraph()
                p_ml.text = itm.metric_label.upper()
                p_ml.font.name = theme.font_family_header
                p_ml.font.size = Pt(8.5)
                p_ml.font.bold = True
                p_ml.font.color.rgb = theme.get_rgb("secondary")
                p_ml.space_before = Pt(3)

            # Vertical divider before bullets
            div2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx + Inches(6.40), cy + Inches(0.12), Pt(0.75), card_h - Inches(0.24))
            div2.shadow.inherit = False
            div2.fill.solid()
            div2.fill.fore_color.rgb = theme.get_rgb("border")
            div2.line.fill.background()

            # Right column: Bullets (w = 4.93")
            bullets_x = cx + Inches(6.60)
            bullets_w = total_w - Inches(6.80)
            tb_b = slide.shapes.add_textbox(bullets_x, cy + Inches(0.10), bullets_w, card_h - Inches(0.20))
            tf_b = tb_b.text_frame
            tf_b.word_wrap = True
            tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0

            for b_idx, b in enumerate(itm.bullets):
                _add_bullet_paragraph(
                    tf_b,
                    b,
                    theme.font_family,
                    font_size_pt=10.0,
                    font_color=theme.get_rgb("secondary"),
                    space_before_pt=4.0 if b_idx > 0 else 0.0,
                )

        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

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

        has_header_elements = bool(itm.icon or itm.badge)
        if itm.icon:
            icon_dim = Inches(0.30)
            icon_x = cx + Inches(0.14)
            icon_y = cy + Inches(0.12)
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

        tb_y = cy + (Inches(0.46) if has_header_elements else Inches(0.18))

        if itm.metric:
            title_h = Inches(0.65) if itm.subtitle else Inches(0.35)
            tb = slide.shapes.add_textbox(cx + Inches(0.16), tb_y, card_w - Inches(0.32), title_h)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p_title = tf.paragraphs[0]
            p_title.text = itm.title
            p_title.font.name = theme.font_family_header
            p_title.font.size = Pt(13.5 if rows == 1 else (10.0 if rows <= 2 else 9.0))
            p_title.font.bold = True
            p_title.font.color.rgb = theme.get_rgb("primary")

            if itm.subtitle:
                p_sub = tf.add_paragraph()
                p_sub.text = itm.subtitle
                p_sub.font.name = theme.font_family_header
                p_sub.font.size = Pt(9.5 if rows == 1 else 8.0)
                p_sub.font.bold = True
                p_sub.font.color.rgb = accent_rgb
                p_sub.space_before = Pt(3)

            met_box_y = tb_y + title_h + (Inches(0.12) if rows == 1 else Inches(0.06))
            met_box_h = Inches(0.95) if rows == 1 else Inches(0.70)
            met_box_w = card_w - Inches(0.36)

            # High-Impact Hero Stat (Rendered DIRECTLY on card canvas — zero nested boxes or inner stripes)
            met_tb = slide.shapes.add_textbox(cx + Inches(0.18), met_box_y, met_box_w, met_box_h)
            met_tf = met_tb.text_frame
            met_tf.word_wrap = True
            met_tf.margin_left = met_tf.margin_right = met_tf.margin_top = met_tf.margin_bottom = 0

            p_met = met_tf.paragraphs[0]
            p_met.text = itm.metric
            p_met.font.name = theme.font_family_header
            p_met.font.size = Pt(34.0 if rows == 1 else (20.0 if rows <= 2 else 16.0))
            p_met.font.bold = True
            p_met.font.color.rgb = accent_rgb

            if itm.metric_label:
                p_ml = met_tf.add_paragraph()
                p_ml.text = itm.metric_label.upper()
                p_ml.font.name = theme.font_family_header
                p_ml.font.size = Pt(9.0 if rows == 1 else 7.5)
                p_ml.font.bold = True
                p_ml.font.color.rgb = theme.get_rgb("secondary")
                p_ml.space_before = Pt(3)

            # Hairline Divider under Hero Metric
            met_div_y = met_box_y + met_box_h + (Inches(0.08) if rows == 1 else Inches(0.04))
            met_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx + Inches(0.18), met_div_y, met_box_w, Pt(0.75))
            met_div.shadow.inherit = False
            met_div.fill.solid()
            met_div.fill.fore_color.rgb = theme.get_rgb("border")
            met_div.line.fill.background()

            bullets_start_y = met_div_y + (Inches(0.14) if rows == 1 else Inches(0.08))
            avail_bullets_h = (cy + card_h - Inches(0.16)) - bullets_start_y
            tb_b = slide.shapes.add_textbox(cx + Inches(0.18), bullets_start_y, met_box_w, avail_bullets_h)
            tf_b = tb_b.text_frame
            tf_b.word_wrap = True
            tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0

            bullet_font_sz = 11.0 if rows == 1 else (8.0 if rows <= 2 else 7.2)
            bullet_space_before = 8.0 if rows == 1 else 2.5
            for b in itm.bullets:
                _add_bullet_paragraph(
                    tf_b,
                    b,
                    theme.font_family,
                    font_size_pt=bullet_font_sz,
                    font_color=theme.get_rgb("secondary"),
                    space_before_pt=bullet_space_before,
                )
        else:
            tb_x = cx + Inches(0.14)
            tb_w = card_w - Inches(0.28)
            tb_h = card_h - Inches(0.50)

            tb = slide.shapes.add_textbox(tb_x, tb_y, tb_w, tb_h)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p_title = tf.paragraphs[0]
            p_title.text = itm.title
            p_title.font.name = theme.font_family_header
            p_title.font.size = Pt(13.5 if rows == 1 else (10.0 if rows <= 2 else 9.0))
            p_title.font.bold = True
            p_title.font.color.rgb = theme.get_rgb("primary")

            if itm.subtitle:
                p_sub = tf.add_paragraph()
                p_sub.text = itm.subtitle
                p_sub.font.name = theme.font_family
                p_sub.font.size = Pt(10.0 if rows == 1 else 8.0)
                p_sub.font.color.rgb = theme.get_rgb("secondary")
                p_sub.space_before = Pt(4 if rows == 1 else 2)

            bullet_font_sz = 10.5 if rows == 1 else (7.8 if rows <= 2 else 7.2)
            bullet_space_before = 7.0 if rows == 1 else 2.5
            for b in itm.bullets:
                _add_bullet_paragraph(
                    tf,
                    b,
                    theme.font_family,
                    font_size_pt=bullet_font_sz,
                    font_color=theme.get_rgb("secondary"),
                    space_before_pt=bullet_space_before,
                )

    if takeaway:
        syn_y = Inches(6.28)
        syn_h = Inches(0.54)
        syn_w = total_w
        col1_x = content_left

        add_card(
            slide,
            theme,
            col1_x,
            syn_y,
            syn_w,
            syn_h,
            force_rectangle=True,
            bg_color=hex_to_rgb("#F8FAFC"),
            border_color=hex_to_rgb("#BAE6FD"),
            border_width_pt=0.75,
        )

        stripe_syn = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col1_x, syn_y, Inches(0.06), syn_h)
        stripe_syn.shadow.inherit = False
        stripe_syn.fill.solid()
        stripe_syn.fill.fore_color.rgb = theme.get_rgb("accent")
        stripe_syn.line.fill.background()

        syn_tb = slide.shapes.add_textbox(col1_x + Inches(0.22), syn_y + Inches(0.04), syn_w - Inches(0.36), syn_h - Inches(0.08))
        syn_tf = syn_tb.text_frame
        syn_tf.word_wrap = True
        syn_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        syn_tf.margin_left = syn_tf.margin_right = syn_tf.margin_top = syn_tf.margin_bottom = 0
        p_syn = syn_tf.paragraphs[0]

        takeaway_text = takeaway if isinstance(takeaway, str) else str(takeaway.get("text", ""))
        if ":" in takeaway_text:
            t_lead, t_body = takeaway_text.split(":", 1)
            r_tl = p_syn.add_run()
            r_tl.text = f"{t_lead.strip()}: "
            r_tl.font.name = theme.font_family_header
            r_tl.font.size = Pt(10.0)
            r_tl.font.bold = True
            r_tl.font.color.rgb = theme.get_rgb("accent")

            r_tb = p_syn.add_run()
            r_tb.text = t_body.strip()
            r_tb.font.name = theme.font_family
            r_tb.font.size = Pt(10.0)
            r_tb.font.color.rgb = theme.get_rgb("primary")
        else:
            p_syn.text = takeaway_text
            p_syn.font.name = theme.font_family
            p_syn.font.size = Pt(10.0)
            p_syn.font.color.rgb = theme.get_rgb("primary")

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

