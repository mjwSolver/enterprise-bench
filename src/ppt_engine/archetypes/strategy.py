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
    add_card_with_harmonized_icon, add_slide_footer, add_takeaway_bar, _interpolate_color, _get_contrast_text_color,
    _add_status_pill, _add_bullet_paragraph, _fit_image_in_box,
)

logger = logging.getLogger(__name__)

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
    tracker: Optional[str] = None,
    action_title: str = "Balanced Portfolio Allocation Fuels Core Modernization while Incubating Future Engines",
    subtitle: Optional[str] = None,
    horizons: Optional[List[HorizonColumnData]] = None,
    takeaway: Optional[str] = None,
    source: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
) -> Any:
    """
    Builds a BCG 3-Horizon Growth / Modernization Slide.
    Divides the content area into 3 structured horizon columns with metrics,
    initiatives, status badges, and an optional executive synthesis takeaway bar.
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

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
    timeline_y = resolve_content_top(header_bottom, gap_in=0.22)
    timeline_h = Inches(0.36)
    row_y = timeline_y + timeline_h + Inches(0.16)
    card_w = Inches(3.72)
    card_gap = Inches(0.28)
    bottom_limit = Inches(5.96 if takeaway else 6.86)
    card_h = max(Inches(3.60), bottom_limit - row_y)

    for i, h_data in enumerate(horizons[:3]):
        cx = start_x + i * (card_w + card_gap)
        accent_rgb = theme.get_rgb(h_data.accent_key)

        # ---------------------------------------------------------------------
        # 1. Horizontal Timeline Stepper Rail (Unmistakable Temporal Flow)
        # ---------------------------------------------------------------------
        step_pill = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE if theme.corner_radius > 0 else MSO_SHAPE.RECTANGLE,
            cx,
            timeline_y,
            card_w,
            timeline_h,
        )
        step_pill.shadow.inherit = False
        strip_shape_shadows(step_pill)
        step_pill.fill.solid()
        step_pill.fill.fore_color.rgb = theme.get_rgb(h_data.status_bg_key)
        step_pill.line.color.rgb = theme.get_rgb(h_data.status_text_key)
        step_pill.line.width = Pt(0.75)

        s_tf = step_pill.text_frame
        s_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        s_tf.margin_left = Inches(0.14)
        s_tf.margin_right = Inches(0.14)
        s_tf.margin_top = s_tf.margin_bottom = 0
        p_step = s_tf.paragraphs[0]
        p_step.alignment = PP_ALIGN.CENTER

        r_tag = p_step.add_run()
        r_tag.text = h_data.horizon_tag.upper()
        r_tag.font.name = theme.font_family_header
        r_tag.font.size = Pt(8.5)
        r_tag.font.bold = True
        r_tag.font.color.rgb = theme.get_rgb(h_data.status_text_key)

        r_sep = p_step.add_run()
        r_sep.text = "  •  "
        r_sep.font.name = theme.font_family
        r_sep.font.size = Pt(8.0)
        r_sep.font.color.rgb = theme.get_rgb("muted")

        r_stat = p_step.add_run()
        r_stat.text = h_data.status_tag.upper()
        r_stat.font.name = theme.font_family_header
        r_stat.font.size = Pt(8.5)
        r_stat.font.bold = True
        r_stat.font.color.rgb = theme.get_rgb(h_data.status_text_key)

        # Directional Timeline Connector Arrow between columns (Native Vector Shape)
        if i < 2:
            arr_dim = Inches(0.16)
            arrow_x = cx + card_w + (card_gap - arr_dim) / 2
            arrow_y = timeline_y + (timeline_h - arr_dim) / 2
            arr_shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, arrow_x, arrow_y, arr_dim, arr_dim)
            arr_shape.shadow.inherit = False
            strip_shape_shadows(arr_shape)
            arr_shape.fill.solid()
            arr_shape.fill.fore_color.rgb = hex_to_rgb("#94A3B8")
            arr_shape.line.fill.background()

        # ---------------------------------------------------------------------
        # 2. Clean Surface Container (Zero Top Stripe, Generous Whitespace)
        # ---------------------------------------------------------------------
        add_card(
            slide,
            theme,
            cx,
            row_y,
            card_w,
            card_h,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            border_width_pt=0.75,
            force_rectangle=True,
        )

        # ---------------------------------------------------------------------
        # 3. Column Header: Title & Strategic Focus
        # ---------------------------------------------------------------------
        pad_x = Inches(0.28)
        content_w = card_w - Inches(0.56)

        title_tb = slide.shapes.add_textbox(cx + pad_x, row_y + Inches(0.22), content_w, Inches(0.68))
        title_tf = title_tb.text_frame
        title_tf.word_wrap = True
        title_tf.margin_left = title_tf.margin_right = title_tf.margin_top = title_tf.margin_bottom = 0
        p_title = title_tf.paragraphs[0]
        p_title.text = h_data.title
        p_title.font.name = theme.font_family_header
        p_title.font.size = Pt(thresholds.get("card_title_pt", 14.5))
        p_title.font.bold = True
        p_title.font.color.rgb = theme.get_rgb("primary")

        has_focus = bool(h_data.strategic_focus and h_data.strategic_focus.strip())
        if has_focus:
            p_f = title_tf.add_paragraph()
            p_f.text = h_data.strategic_focus
            p_f.font.name = theme.font_family
            p_f.font.size = Pt(thresholds.get("caption_pt", 9.5))
            p_f.font.color.rgb = theme.get_rgb("secondary")
            p_f.space_before = Pt(3)
            metric_top_y = row_y + (Inches(1.04) if takeaway else Inches(1.20))
            divider_y = row_y + (Inches(1.92) if takeaway else Inches(2.16))
        else:
            metric_top_y = row_y + (Inches(0.86) if takeaway else Inches(1.02))
            divider_y = row_y + (Inches(1.76) if takeaway else Inches(2.00))

        # ---------------------------------------------------------------------
        # 4. Open-Air Floating Hero Metric (Typographic Scale Contrast)
        # ---------------------------------------------------------------------
        metric_h = Inches(0.72)
        m_tb = slide.shapes.add_textbox(cx + pad_x, metric_top_y, content_w, metric_h)
        m_tf = m_tb.text_frame
        m_tf.word_wrap = True
        m_tf.margin_left = m_tf.margin_right = m_tf.margin_top = m_tf.margin_bottom = 0

        p_mval = m_tf.paragraphs[0]
        p_mval.text = h_data.metric_highlight
        p_mval.font.name = theme.font_family_header
        base_metric_pt = 28.0
        if len(h_data.metric_highlight) > 14:
            base_metric_pt = 18.0
        elif len(h_data.metric_highlight) > 9:
            base_metric_pt = 22.0
        p_mval.font.size = Pt(base_metric_pt)
        p_mval.font.bold = True
        p_mval.font.color.rgb = accent_rgb

        p_mlbl = m_tf.add_paragraph()
        p_mlbl.text = h_data.metric_label
        p_mlbl.font.name = theme.font_family
        p_mlbl.font.size = Pt(9.5)
        p_mlbl.font.color.rgb = theme.get_rgb("muted")
        p_mlbl.space_before = Pt(3)

        # ---------------------------------------------------------------------
        # 5. Subtle Editorial Hairline Divider
        # ---------------------------------------------------------------------
        div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx + pad_x, divider_y, content_w, Pt(0.75))
        div.shadow.inherit = False
        strip_shape_shadows(div)
        div.fill.solid()
        div.fill.fore_color.rgb = theme.get_rgb("border")
        div.line.fill.background()

        # ---------------------------------------------------------------------
        # 6. Strategic Deliverables (Direct Bullet Flow, Dynamic Vertical Spacing)
        # ---------------------------------------------------------------------
        content_top = divider_y + (Inches(0.18) if takeaway else Inches(0.24))
        content_h = card_h - (content_top - row_y) - Inches(0.14)
        content_tb = slide.shapes.add_textbox(
            cx + pad_x,
            content_top,
            content_w,
            content_h,
        )
        content_tf = content_tb.text_frame
        content_tf.word_wrap = True
        content_tf.margin_left = content_tf.margin_right = content_tf.margin_top = content_tf.margin_bottom = 0

        n_inits = len(h_data.initiatives)
        if n_inits <= 2:
            bullet_size_pt = 10.5 if takeaway else 11.0
            bullet_space_before = 12.0 if takeaway else 18.0
        elif n_inits == 3:
            bullet_size_pt = 10.0 if takeaway else 10.5
            bullet_space_before = 8.0 if takeaway else 12.0
        else:
            bullet_size_pt = thresholds.get("bullet_pt", 9.5)
            bullet_space_before = 6.0 if takeaway else 7.0

        for b_idx, init_item in enumerate(h_data.initiatives):
            _add_bullet_paragraph(
                content_tf,
                text=init_item,
                font_name=theme.font_family,
                font_size_pt=bullet_size_pt,
                font_color=theme.get_rgb("secondary"),
                lead_color=theme.get_rgb("primary"),
                space_before_pt=bullet_space_before if b_idx > 0 else 2.0,
            )

    # -------------------------------------------------------------------------
    # 7. Executive Takeaway Bar at Bottom (Harmonized Anchor)
    # -------------------------------------------------------------------------
    if takeaway:
        add_takeaway_bar(slide, theme, takeaway, top_y=Inches(6.10), left_x=start_x, width=Inches(11.733), height=Inches(0.68), font_size_pt=10.5)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
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
    tracker: Optional[str] = None,
    action_title: str = "Structured Hypothesis Cascade Unlocks $42M in Sustainable Operational Alpha",
    subtitle: Optional[str] = None,
    hypothesis_statement: str = "CORE HYPOTHESIS: By decoupling tier-1 core applications into autonomous cloud microservices and instituting zero-trust attestation, the enterprise can lower infrastructure TCO by 35% while multiplying deployment frequency by 4x.",
    pillars: Optional[List[StrategyPillarData]] = None,
    synthesis_conclusion: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
) -> Any:
    """
    Builds a McKinsey MECE Hypothesis / Strategy Cascade Slide.
    Structure: Top Hypothesis Anchor Box -> 3 Vertical MECE Pillar Cards -> Optional Synthesis Banner.
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

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

    # 1. Top Hypothesis Anchor Card
    hypo_y_in = resolve_content_top(header_bottom, gap_in=0.16)
    hypo_y = Inches(hypo_y_in)
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

    # 2. Middle Row: 3 MECE Strategy Pillars
    pillar_y_in = hypo_y_in + 0.85 + 0.14
    pillar_y = Inches(pillar_y_in)
    bottom_limit = 6.12 if synthesis_conclusion else 6.85
    pillar_h = Inches(max(2.60, bottom_limit - pillar_y_in))
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
    quadrant_title: str = ""         # e.g. "1. FINANCIAL & COMMERCIAL"
    tagline: str = ""                # e.g. "TCO Reduction & Capital Optimization"
    metrics: List[ScorecardMetric] = field(default_factory=list)
    accent_key: str = "accent"
    icon: Optional[str] = None  # Semantic icon identifier (e.g. "dollar-sign", "users", "zap", "shield-check")
    icon_path: Optional[Union[str, Path]] = None
    title: Optional[str] = None

    def __post_init__(self) -> None:
        if self.title and not self.quadrant_title:
            self.quadrant_title = self.title
        elif not self.title and self.quadrant_title:
            self.title = self.quadrant_title

# Backwards-compatibility alias
QuadrantData = ScorecardQuadrantData


def build_balanced_scorecard_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Target Performance Exceeds Benchmark SLAs Across All Four Operational Dimensions",
    subtitle: Optional[str] = None,
    quadrants: Optional[List[ScorecardQuadrantData]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
) -> Any:
    """
    Builds an Executive Balanced Scorecard / KPI Matrix Slide (4-Quadrant 2x2 Grid).
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

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
    grid_y = resolve_content_top(header_bottom, gap_in=0.20)
    quad_w = Inches(5.72)
    gap_x = Inches(0.29)
    gap_y = Inches(0.18)
    quad_h = min(Inches(2.58), max(Inches(2.25), (Inches(6.90) - grid_y - gap_y) / 2))

    positions = [
        (grid_x, grid_y),                                   # Q1: Top-Left
        (grid_x + quad_w + gap_x, grid_y),                 # Q2: Top-Right
        (grid_x, grid_y + quad_h + gap_y),                 # Q3: Bottom-Left
        (grid_x + quad_w + gap_x, grid_y + quad_h + gap_y) # Q4: Bottom-Right
    ]

    glyph_labels = ["01", "02", "03", "04"]

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
            strip_shape_shadows(icon_badge)
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
            strip_shape_shadows(bp)
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
    tracker: Optional[str] = None,
    action_title: str = "Modernization Closes Critical Gaps Between Legacy Constraints and Future Target State",
    subtitle: Optional[str] = None,
    dimensions: Optional[List[GapDimensionData]] = None,
    as_is_header: str = "CURRENT STATE (AS-IS)",
    to_be_header: str = "TARGET ARCHITECTURE (TO-BE)",
    left_title: Optional[str] = None,
    left_subtitle: Optional[str] = None,
    left_items: Optional[List[str]] = None,
    left_eyebrow: Optional[str] = None,
    right_title: Optional[str] = None,
    right_subtitle: Optional[str] = None,
    right_items: Optional[List[str]] = None,
    right_eyebrow: Optional[str] = None,
    takeaway: Optional[str] = None,
    source: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
) -> Any:
    """
    Renders a consulting Gap Analysis / Comparative Transformation slide:
      - 2-Column Mode (left_items & right_items): Before vs After comparative cards with directional connector.
      - Row Mode (dimensions): Directional right-pointing triangle anchors by default, or pill badges when transition_lever text is supplied.
      - Optional Executive Synthesis Bar at bottom (`takeaway=None` by default).
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)
    thresholds = theme.typography_thresholds

    # =========================================================================
    # Mode A: 2-Column Comparative Matrix (Before vs After)
    # =========================================================================
    if left_items and right_items:
        card_y = resolve_content_top(header_bottom, gap_in=0.22)
        bottom_limit = Inches(6.14 if takeaway else 6.88)
        card_h = max(Inches(3.60), bottom_limit - card_y)
        col_w = Inches(5.60)
        col1_x = Inches(0.80)
        col2_x = Inches(6.93)
        center_x = Inches(6.40)
        center_w = Inches(0.53)
        pad_x = Inches(0.28)
        content_w = col_w - Inches(0.56)

        # 1. Left Card: BEFORE (Clean Surface, subtle neutral border)
        add_card(
            slide,
            theme,
            col1_x,
            card_y,
            col_w,
            card_h,
            force_rectangle=True,
            bg_color=theme.get_rgb("surface"),
            border_color=hex_to_rgb("#CBD5E1"),
            border_width_pt=0.75,
        )

        resolved_left_raw = left_title or as_is_header
        resolved_left_eyebrow = left_eyebrow or ("AS-IS BASELINE" if resolved_left_raw.upper().startswith("BEFORE:") else None)
        resolved_left_title = resolved_left_raw.split(":", 1)[1].strip() if (resolved_left_eyebrow and ":" in resolved_left_raw) else resolved_left_raw

        tb_l = slide.shapes.add_textbox(col1_x + pad_x, card_y + Inches(0.14), content_w, Inches(0.78))
        tf_l = tb_l.text_frame
        tf_l.word_wrap = True
        tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0

        if resolved_left_eyebrow:
            p_leye = tf_l.paragraphs[0]
            p_leye.text = resolved_left_eyebrow.upper()
            p_leye.font.name = theme.font_family_header
            p_leye.font.size = Pt(8.5)
            p_leye.font.bold = True
            p_leye.font.color.rgb = theme.get_rgb("muted")
            p_lt = tf_l.add_paragraph()
            p_lt.space_before = Pt(2)
        else:
            p_lt = tf_l.paragraphs[0]

        p_lt.text = resolved_left_title
        p_lt.font.name = theme.font_family_header
        p_lt.font.size = Pt(thresholds.get("card_title_pt", 14.0))
        p_lt.font.bold = True
        p_lt.font.color.rgb = theme.get_rgb("primary")

        if left_subtitle:
            p_ls = tf_l.add_paragraph()
            p_ls.text = left_subtitle
            p_ls.font.name = theme.font_family
            p_ls.font.size = Pt(thresholds.get("caption_pt", 9.5))
            p_ls.font.color.rgb = theme.get_rgb("muted")
            p_ls.space_before = Pt(3)

        div_l = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col1_x + pad_x, card_y + Inches(0.96), content_w, Pt(0.75))
        div_l.shadow.inherit = False
        strip_shape_shadows(div_l)
        div_l.fill.solid()
        div_l.fill.fore_color.rgb = hex_to_rgb("#E2E8F0")
        div_l.line.fill.background()

        list_tb_l = slide.shapes.add_textbox(col1_x + pad_x, card_y + Inches(1.08), content_w, card_h - Inches(1.22))
        list_tf_l = list_tb_l.text_frame
        list_tf_l.word_wrap = True
        list_tf_l.margin_left = list_tf_l.margin_right = list_tf_l.margin_top = list_tf_l.margin_bottom = 0

        n_items_l = len(left_items)
        bullet_pt_l = 11.0 if n_items_l <= 2 else thresholds.get("bullet_pt", 10.0)
        bullet_gap_l = 22.0 if n_items_l <= 2 else (14.0 if n_items_l == 3 else 10.5)

        for b_idx, item in enumerate(left_items):
            _add_bullet_paragraph(
                list_tf_l,
                text=item,
                font_name=theme.font_family,
                font_size_pt=bullet_pt_l,
                font_color=theme.get_rgb("secondary"),
                lead_color=theme.get_rgb("primary"),
                space_before_pt=bullet_gap_l if b_idx > 0 else 4.0,
            )

        # 2. Center Directional Transition Arrow with Subtle Neutral Disc Frame
        disc_dim = Inches(0.40)
        disc_x = center_x + (center_w - disc_dim) / 2
        disc_y = card_y + (card_h - disc_dim) / 2
        disc_shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, disc_x, disc_y, disc_dim, disc_dim)
        disc_shape.shadow.inherit = False
        strip_shape_shadows(disc_shape)
        disc_shape.fill.solid()
        disc_shape.fill.fore_color.rgb = hex_to_rgb("#F1F5F9")
        disc_shape.line.color.rgb = hex_to_rgb("#CBD5E1")
        disc_shape.line.width = Pt(0.75)

        arr_dim = Inches(0.18)
        arr_x = center_x + (center_w - arr_dim) / 2
        arr_y = card_y + (card_h - arr_dim) / 2
        arr_shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, arr_x, arr_y, arr_dim, arr_dim)
        arr_shape.shadow.inherit = False
        strip_shape_shadows(arr_shape)
        arr_shape.fill.solid()
        arr_shape.fill.fore_color.rgb = theme.get_rgb("accent")
        arr_shape.line.fill.background()

        # 3. Right Card: AFTER (Clean Surface, subtle accent border)
        add_card(
            slide,
            theme,
            col2_x,
            card_y,
            col_w,
            card_h,
            force_rectangle=True,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border_accent"),
            border_width_pt=1.0,
        )

        resolved_right_raw = right_title or to_be_header
        resolved_right_eyebrow = right_eyebrow or ("TARGET ARCHITECTURE" if resolved_right_raw.upper().startswith("AFTER:") else None)
        resolved_right_title = resolved_right_raw.split(":", 1)[1].strip() if (resolved_right_eyebrow and ":" in resolved_right_raw) else resolved_right_raw

        tb_r = slide.shapes.add_textbox(col2_x + pad_x, card_y + Inches(0.14), content_w, Inches(0.78))
        tf_r = tb_r.text_frame
        tf_r.word_wrap = True
        tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0

        if resolved_right_eyebrow:
            p_reye = tf_r.paragraphs[0]
            p_reye.text = resolved_right_eyebrow.upper()
            p_reye.font.name = theme.font_family_header
            p_reye.font.size = Pt(8.5)
            p_reye.font.bold = True
            p_reye.font.color.rgb = theme.get_rgb("accent")
            p_rt = tf_r.add_paragraph()
            p_rt.space_before = Pt(2)
        else:
            p_rt = tf_r.paragraphs[0]

        p_rt.text = resolved_right_title
        p_rt.font.name = theme.font_family_header
        p_rt.font.size = Pt(thresholds.get("card_title_pt", 14.0))
        p_rt.font.bold = True
        p_rt.font.color.rgb = theme.get_rgb("accent")

        if right_subtitle:
            p_rs = tf_r.add_paragraph()
            p_rs.text = right_subtitle
            p_rs.font.name = theme.font_family
            p_rs.font.size = Pt(thresholds.get("caption_pt", 9.5))
            p_rs.font.color.rgb = theme.get_rgb("muted")
            p_rs.space_before = Pt(3)

        div_r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col2_x + pad_x, card_y + Inches(0.96), content_w, Pt(0.75))
        div_r.shadow.inherit = False
        strip_shape_shadows(div_r)
        div_r.fill.solid()
        div_r.fill.fore_color.rgb = hex_to_rgb("#BAE6FD")
        div_r.line.fill.background()

        list_tb_r = slide.shapes.add_textbox(col2_x + pad_x, card_y + Inches(1.08), content_w, card_h - Inches(1.22))
        list_tf_r = list_tb_r.text_frame
        list_tf_r.word_wrap = True
        list_tf_r.margin_left = list_tf_r.margin_right = list_tf_r.margin_top = list_tf_r.margin_bottom = 0

        n_items_r = len(right_items)
        bullet_pt_r = 11.0 if n_items_r <= 2 else thresholds.get("bullet_pt", 10.0)
        bullet_gap_r = 22.0 if n_items_r <= 2 else (14.0 if n_items_r == 3 else 10.5)

        for b_idx, item in enumerate(right_items):
            _add_bullet_paragraph(
                list_tf_r,
                text=item,
                font_name=theme.font_family,
                font_size_pt=bullet_pt_r,
                font_color=theme.get_rgb("secondary"),
                lead_color=theme.get_rgb("primary"),
                space_before_pt=bullet_gap_r if b_idx > 0 else 4.0,
            )

        # 4. Optional Executive Synthesis Bar at Bottom (strictly opt-in)
        if takeaway:
            add_takeaway_bar(
                slide,
                theme,
                takeaway,
                top_y=Inches(6.10),
                left_x=col1_x,
                width=Inches(11.73),
                height=Inches(0.78),
                font_size_pt=10.5,
            )

        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
        return slide

    # =========================================================================
    # Mode B: 3-Row Dimension Table (Zero Red/Green Side Stripes!)
    # =========================================================================
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

    if not dimensions:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    # Geometry Layout
    has_levers = any(bool(getattr(d, "transition_lever", None)) for d in dimensions)
    header_y = resolve_content_top(header_bottom, gap_in=0.22)
    header_h = Inches(0.38)
    col1_x = Inches(0.8)
    if has_levers:
        col1_w = Inches(4.75)
        center_x = Inches(5.72)
        center_w = Inches(1.88)
        col2_x = Inches(7.77)
        col2_w = Inches(4.75)
    else:
        col1_w = Inches(5.40)
        center_x = Inches(6.28)
        center_w = Inches(0.77)
        col2_x = Inches(7.13)
        col2_w = Inches(5.40)

    # 1. Column Headers (Clean, subtle styling)
    h1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col1_x, header_y, col1_w, header_h)
    h1.shadow.inherit = False
    strip_shape_shadows(h1)
    h1.fill.solid()
    h1.fill.fore_color.rgb = hex_to_rgb("#F1F5F9")
    h1.line.color.rgb = hex_to_rgb("#CBD5E1")
    h1.line.width = Pt(0.75)
    h1_tf = h1.text_frame
    h1_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    h1_tf.margin_left = Inches(0.15)
    p_h1 = h1_tf.paragraphs[0]
    p_h1.text = as_is_header.upper()
    p_h1.font.name = theme.font_family_header
    p_h1.font.size = Pt(11.0)
    p_h1.font.bold = True
    p_h1.font.color.rgb = hex_to_rgb("#475569")

    if has_levers:
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

    h2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col2_x, header_y, col2_w, header_h)
    h2.shadow.inherit = False
    strip_shape_shadows(h2)
    h2.fill.solid()
    h2.fill.fore_color.rgb = hex_to_rgb("#EFF6FF")
    h2.line.color.rgb = theme.get_rgb("accent")
    h2.line.width = Pt(0.75)
    h2_tf = h2.text_frame
    h2_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    h2_tf.margin_left = Inches(0.15)
    p_h2 = h2_tf.paragraphs[0]
    p_h2.text = to_be_header.upper()
    p_h2.font.name = theme.font_family_header
    p_h2.font.size = Pt(11.0)
    p_h2.font.bold = True
    p_h2.font.color.rgb = theme.get_rgb("primary")

    n_dim = len(dimensions)
    content_y = header_y + header_h + Inches(0.10)
    bottom_limit = Inches(6.14 if takeaway else 6.88)
    available_h = max(Inches(3.20), bottom_limit - content_y)
    gap_y = Inches(0.10)
    row_h = (available_h - (n_dim - 1) * gap_y) / n_dim

    for r_idx, dim in enumerate(dimensions):
        cur_y = content_y + r_idx * (row_h + gap_y)

        # Left Card: As-Is Deficit Container (NO RED SIDE STRIPE!)
        add_card(
            slide,
            theme,
            col1_x,
            cur_y,
            col1_w,
            row_h,
            force_rectangle=True,
            bg_color=RGBColor(255, 255, 255),
            border_color=hex_to_rgb("#CBD5E1"),
            border_width_pt=0.75,
        )

        tb_l = slide.shapes.add_textbox(col1_x + Inches(0.18), cur_y + Inches(0.08), col1_w - Inches(0.34), row_h - Inches(0.16))
        tf_l = tb_l.text_frame
        tf_l.word_wrap = True
        tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0

        p_def = tf_l.paragraphs[0]
        if dim.deficit_tag:
            p_def.text = f"[{dim.deficit_tag.upper()}]"
            p_def.font.name = theme.font_family_header
            p_def.font.size = Pt(9.5)
            p_def.font.bold = True
            p_def.font.color.rgb = theme.get_rgb("muted")

        p_dim = tf_l.add_paragraph() if dim.deficit_tag else p_def
        p_dim.text = dim.dimension
        p_dim.font.name = theme.font_family_header
        p_dim.font.size = Pt(13.5)
        p_dim.font.bold = True
        p_dim.font.color.rgb = theme.get_rgb("primary")
        if dim.deficit_tag:
            p_dim.space_before = Pt(2)

        p_as = tf_l.add_paragraph()
        p_as.text = dim.as_is_state
        p_as.font.name = theme.font_family
        p_as.font.size = Pt(11.0)
        p_as.font.color.rgb = theme.get_rgb("secondary")
        p_as.space_before = Pt(4)

        # Center Transition Indicator: Pill when lever text exists, otherwise clean right-pointing triangle
        if dim.transition_lever:
            lever_h = Inches(0.56)
            lever_y = cur_y + (row_h - lever_h) / 2
            lever_badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, center_x, lever_y, center_w, lever_h)
            lever_badge.shadow.inherit = False
            strip_shape_shadows(lever_badge)
            lever_badge.fill.solid()
            lever_badge.fill.fore_color.rgb = hex_to_rgb("#EFF6FF")
            lever_badge.line.color.rgb = theme.get_rgb("accent")
            lever_badge.line.width = Pt(1.0)

            l_tf = lever_badge.text_frame
            l_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            l_tf.word_wrap = True
            l_tf.margin_left = Inches(0.06)
            l_tf.margin_right = Inches(0.06)
            l_tf.margin_top = l_tf.margin_bottom = 0
            p_lv = l_tf.paragraphs[0]
            p_lv.text = f"{dim.transition_lever} ->"
            p_lv.font.name = theme.font_family_header
            p_lv.font.size = Pt(9.5)
            p_lv.font.bold = True
            p_lv.alignment = PP_ALIGN.CENTER
            p_lv.font.color.rgb = theme.get_rgb("accent")
        else:
            tri_size = min(Inches(0.36), row_h * 0.34)
            tri_x = center_x + (center_w - tri_size) / 2
            tri_y = cur_y + (row_h - tri_size) / 2
            tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, tri_x, tri_y, tri_size, tri_size)
            tri.rotation = 90.0
            tri.shadow.inherit = False
            strip_shape_shadows(tri)
            tri.fill.solid()
            tri.fill.fore_color.rgb = theme.get_rgb("accent")
            tri.line.fill.background()

        # Right Card: To-Be Target Capability (NO GREEN SIDE STRIPE!)
        add_card(
            slide,
            theme,
            col2_x,
            cur_y,
            col2_w,
            row_h,
            force_rectangle=True,
            bg_color=RGBColor(255, 255, 255),
            border_color=theme.get_rgb("border"),
            border_width_pt=0.75,
        )

        tb_r = slide.shapes.add_textbox(col2_x + Inches(0.18), cur_y + Inches(0.08), col2_w - Inches(0.34), row_h - Inches(0.16))
        tf_r = tb_r.text_frame
        tf_r.word_wrap = True
        tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0

        p_top_r = tf_r.paragraphs[0]
        if dim.impact_delta:
            r_eye = p_top_r.add_run()
            r_eye.text = "TARGET BENEFIT:  "
            r_eye.font.name = theme.font_family_header
            r_eye.font.size = Pt(10.5)
            r_eye.font.bold = True
            r_eye.font.color.rgb = theme.get_rgb("muted")

            r_delta = p_top_r.add_run()
            r_delta.text = dim.impact_delta.upper()
            r_delta.font.name = theme.font_family_header
            r_delta.font.size = Pt(13.5)
            r_delta.font.bold = True
            r_delta.font.color.rgb = theme.get_rgb("accent")

        p_to = tf_r.add_paragraph() if dim.impact_delta else p_top_r
        p_to.text = dim.to_be_state
        p_to.font.name = theme.font_family
        p_to.font.size = Pt(11.0)
        p_to.font.color.rgb = theme.get_rgb("primary")
        if dim.impact_delta:
            p_to.space_before = Pt(4)

    if takeaway:
        add_takeaway_bar(slide, theme, takeaway, top_y=Inches(6.28), left_x=col1_x, width=Inches(11.733), height=Inches(0.54))

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


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
    footnote: Optional[str] = None


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
    strip_shape_shadows(line)
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
    strip_shape_shadows(line)
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
    strip_shape_shadows(card)
    card.fill.solid()
    card.fill.fore_color.rgb = theme.get_rgb("surface")
    card.line.color.rgb = theme.get_rgb("border")
    card.line.width = Pt(theme.card_border_width_pt)

    # 2. Flush Top Accent Stripe (Strict Sharp Rectangle)
    stripe_h = Inches(0.06)
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, stripe_h)
    stripe.shadow.inherit = False
    strip_shape_shadows(stripe)
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
    strip_shape_shadows(pill)
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
    strip_shape_shadows(domain_pill)
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
    p_domain.font.size = Pt(8.0)
    p_domain.font.bold = True
    p_domain.font.color.rgb = theme.get_rgb("secondary")


def build_equity_corporate_tree_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Metrodata Group Operates Multi-Tier Operating Subsidiaries and Specialized JVs",
    subtitle: Optional[str] = None,
    tree_data: Optional[EquityTreeData] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
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
    strip_shape_shadows(card_p)
    card_p.fill.solid()
    card_p.fill.fore_color.rgb = c_primary
    card_p.line.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    card_p.line.width = Pt(1.0)

    # Top Accent Stripe (Strict Sharp Rectangle)
    stripe_p = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, parent_left, parent_top, parent_w, Inches(0.06))
    stripe_p.shadow.inherit = False
    strip_shape_shadows(stripe_p)
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

