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
    add_slide_with_background, add_slide_header, resolve_content_top, add_card, add_slide_footer, add_takeaway_bar,
    _interpolate_color, _add_status_pill, _add_bullet_paragraph, _get_contrast_text_color,
    resolve_accent_color, draw_hairline,
)

logger = logging.getLogger(__name__)

@dataclass
class FeatureScorecardRow:
    """Represents an evaluation criterion row in a comparison matrix."""
    category: str
    criteria: str
    scores: Dict[str, str]           # platform -> "FULL", "PARTIAL", "HALF", "NONE", "EMPTY", "N/A" or glyphs "●", "◐", "○"
    business_impact: Optional[str] = None

@dataclass
class FeatureMatrixData:
    """Dataset for an executive platform scorecard."""
    columns: List[str] = field(default_factory=list)
    rows: List[FeatureScorecardRow] = field(default_factory=list)
    recommendation_badge: Optional[str] = None
    recommended_column: Optional[str] = None
    footnote: Optional[str] = None


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
    tracker: Optional[str] = None,
    action_title: str = "Snowflake AI Data Cloud Demonstrates Superior Capabilities Across Core Evaluation Criteria",
    subtitle: Optional[str] = None,
    matrix_data: Optional[FeatureMatrixData] = None,
    current_idx: int = 5,
    total_slides: int = 10,
    notice: Optional[str] = None,
) -> Any:
    """
    Renders an executive feature evaluation matrix slide (supports Harvey Balls or plain labels)
    with strictly opt-in recommendation highlighting and footnote legends.
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
    strip_shape_shadows(bg)

    # 2. Unified Header Frame
    header_bottom = add_slide_header(slide, theme, tracker=tracker, title=action_title, subtitle=subtitle)

    # 3. Canvas Table Layout Bounds (Contiguous row_gap = 0.0, opt-in IMPACT column & footnote)
    table_left = Inches(0.80)
    table_top = resolve_content_top(header_bottom, gap_in=0.20)
    table_w = Inches(11.733)
    hdr_h = Inches(0.46)
    footnote_str = str(data.footnote).strip() if data.footnote and str(data.footnote).strip() else ""
    foot_reserve = (Inches(0.52) if len(footnote_str) > 95 else Inches(0.42)) if footnote_str else Inches(0.0)
    bottom_limit = Inches(6.86) - foot_reserve
    n_rows = max(1, len(data.rows))
    avail_rows_h = max(Inches(2.40), bottom_limit - table_top - hdr_h)
    row_h = min(Inches(0.76), max(Inches(0.42), avail_rows_h / n_rows))

    platforms = data.columns
    has_impact = any(bool(r.business_impact and str(r.business_impact).strip()) for r in data.rows)
    cat_w = Inches(2.00)
    crit_w = Inches(3.20) if has_impact else Inches(3.45)
    impact_w = Inches(1.15) if has_impact else Inches(0.0)
    plat_w = (table_w - cat_w - crit_w - impact_w) / max(1, len(platforms))

    # Header Band (Single-Line Rule: Muted slate surface + hairline divider, highlighted recommended column in #1E3A8A)
    hdr_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left, table_top, table_w, hdr_h)
    hdr_bg.fill.solid()
    hdr_bg.fill.fore_color.rgb = theme.get_rgb("surface_muted")
    hdr_bg.line.fill.background()
    strip_shape_shadows(hdr_bg)

    hdr_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left, table_top + hdr_h, table_w, Pt(1.0))
    hdr_div.fill.solid()
    hdr_div.fill.fore_color.rgb = theme.get_rgb("border")
    hdr_div.line.fill.background()
    strip_shape_shadows(hdr_div)

    # Header cell labels
    def _add_hdr_txt(x: Inches, w: Inches, text: str, align=PP_ALIGN.LEFT, is_rec: bool = False):
        if is_rec:
            hdr_hl = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, table_top, w, hdr_h)
            hdr_hl.fill.solid()
            hdr_hl.fill.fore_color.rgb = hex_to_rgb("#1E3A8A")
            hdr_hl.line.fill.background()
            strip_shape_shadows(hdr_hl)
        tb = slide.shapes.add_textbox(x + Inches(0.04), table_top + Inches(0.04), max(Inches(0.40), w - Inches(0.08)), hdr_h - Inches(0.08))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = Pt(3)
        tf.margin_top = tf.margin_bottom = Pt(1)
        p = tf.paragraphs[0]
        p.alignment = align
        p.text = text
        p.font.name = theme.font_family_header
        p.font.size = Pt(9.0)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255) if is_rec else theme.get_rgb("primary")

    _add_hdr_txt(table_left + Inches(0.08), cat_w - Inches(0.08), "DOMAIN / CATEGORY")
    _add_hdr_txt(table_left + cat_w + Inches(0.06), crit_w - Inches(0.06), "EVALUATION CRITERIA")

    for p_idx, plat in enumerate(platforms):
        px = table_left + cat_w + crit_w + p_idx * plat_w
        is_rec = bool(data.recommended_column and plat == data.recommended_column)
        _add_hdr_txt(px, plat_w, plat.upper(), align=PP_ALIGN.CENTER, is_rec=is_rec)

    if has_impact:
        _add_hdr_txt(table_left + cat_w + crit_w + len(platforms) * plat_w, impact_w, "IMPACT", align=PP_ALIGN.CENTER)

    # 4. Contiguous Rows (row_gap = 0.0, zebra fills, hairline dividers, flush highlight column)
    harvey_glyph_map = {
        "FULL": "●",
        "●": "●",
        "PARTIAL": "◐",
        "HALF": "◐",
        "◐": "◐",
        "NONE": "○",
        "EMPTY": "○",
        "○": "○",
        "N/A": "-",
    }

    cur_y = table_top + hdr_h
    for r_idx, row in enumerate(data.rows):
        # Flush alternating row background (white on even rows, muted slate on odd rows)
        row_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left, cur_y, table_w, row_h)
        row_bg.fill.solid()
        row_bg.fill.fore_color.rgb = RGBColor(255, 255, 255) if r_idx % 2 == 0 else theme.get_rgb("surface_muted")
        row_bg.line.fill.background()
        strip_shape_shadows(row_bg)

        # Highlight recommended column as flush full-height band (preserving subtle zebra rhythm)
        for p_idx, plat in enumerate(platforms):
            if data.recommended_column and plat == data.recommended_column:
                px = table_left + cat_w + crit_w + p_idx * plat_w
                col_hl = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px, cur_y, plat_w, row_h)
                col_hl.fill.solid()
                col_hl.fill.fore_color.rgb = RGBColor(239, 246, 255) if r_idx % 2 == 0 else RGBColor(219, 234, 254)
                col_hl.line.fill.background()
                strip_shape_shadows(col_hl)

        # Flush bottom hairline divider
        row_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left, cur_y + row_h, table_w, Pt(0.5))
        row_div.fill.solid()
        row_div.fill.fore_color.rgb = theme.get_rgb("border")
        row_div.line.fill.background()
        strip_shape_shadows(row_div)

        # Category cell
        tb_cat = slide.shapes.add_textbox(table_left + Inches(0.10), cur_y + Inches(0.04), cat_w - Inches(0.16), row_h - Inches(0.08))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_cat.margin_left = tf_cat.margin_right = Pt(4)
        tf_cat.margin_top = tf_cat.margin_bottom = Pt(2)
        p_c = tf_cat.paragraphs[0]
        p_c.text = row.category
        p_c.font.name = theme.font_family_header
        p_c.font.size = Pt(10.0)
        p_c.font.bold = True
        p_c.font.color.rgb = theme.get_rgb("primary")

        # Criteria cell
        tb_crit = slide.shapes.add_textbox(table_left + cat_w + Inches(0.08), cur_y + Inches(0.04), crit_w - Inches(0.16), row_h - Inches(0.08))
        tf_crit = tb_crit.text_frame
        tf_crit.word_wrap = True
        tf_crit.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_crit.margin_left = tf_crit.margin_right = Pt(4)
        tf_crit.margin_top = tf_crit.margin_bottom = Pt(2)
        p_cr = tf_crit.paragraphs[0]
        p_cr.text = row.criteria
        p_cr.font.name = theme.font_family
        p_cr.font.size = Pt(10.0)
        p_cr.font.color.rgb = theme.get_rgb("secondary")

        # Platform scores
        for p_idx, plat in enumerate(platforms):
            px = table_left + cat_w + crit_w + p_idx * plat_w
            score_raw = row.scores.get(plat, "-")
            mapped = harvey_glyph_map.get(score_raw.upper().strip() if isinstance(score_raw, str) else "")
            glyph = mapped if mapped is not None else str(score_raw)
            is_rec = bool(data.recommended_column and plat == data.recommended_column)
            is_harvey = glyph in ("●", "◐", "○")

            if is_harvey:
                ball_d = Inches(0.20)
                bx = px + (plat_w - ball_d) / 2
                by = cur_y + (row_h - ball_d) / 2
                if glyph == "●":
                    ball = slide.shapes.add_shape(MSO_SHAPE.OVAL, bx, by, ball_d, ball_d)
                    ball.fill.solid()
                    ball.fill.fore_color.rgb = RGBColor(16, 185, 129) if is_rec else theme.get_rgb("primary")
                    ball.line.fill.background()
                    strip_shape_shadows(ball)
                elif glyph == "◐":
                    ring_color = RGBColor(217, 119, 6)
                    # Layer 1: Crisp solid white base disc
                    base_ball = slide.shapes.add_shape(MSO_SHAPE.OVAL, bx, by, ball_d, ball_d)
                    base_ball.fill.solid()
                    base_ball.fill.fore_color.rgb = RGBColor(255, 255, 255)
                    base_ball.line.fill.background()
                    strip_shape_shadows(base_ball)

                    # Layer 2: Left 180-deg semicircle fill (OOXML pie uses 1/60,000 deg; python-pptx scales *100,000 -> 54.0=90deg, 162.0=270deg)
                    half_pie = slide.shapes.add_shape(MSO_SHAPE.PIE, bx, by, ball_d, ball_d)
                    half_pie.adjustments[0] = 54.0
                    half_pie.adjustments[1] = 162.0
                    half_pie.fill.solid()
                    half_pie.fill.fore_color.rgb = ring_color
                    half_pie.line.fill.background()
                    strip_shape_shadows(half_pie)

                    # Layer 3: Transparent circular ring border on top for clean edge alignment
                    outer_ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, bx, by, ball_d, ball_d)
                    outer_ring.fill.background()
                    outer_ring.line.color.rgb = ring_color
                    outer_ring.line.width = Pt(1.5)
                    strip_shape_shadows(outer_ring)
                else:
                    empty_ball = slide.shapes.add_shape(MSO_SHAPE.OVAL, bx, by, ball_d, ball_d)
                    empty_ball.fill.solid()
                    empty_ball.fill.fore_color.rgb = RGBColor(255, 255, 255)
                    empty_ball.line.color.rgb = RGBColor(148, 163, 184)
                    empty_ball.line.width = Pt(1.5)
                    strip_shape_shadows(empty_ball)
            else:
                tb_sc = slide.shapes.add_textbox(px + Inches(0.04), cur_y + Inches(0.04), max(Inches(0.35), plat_w - Inches(0.08)), row_h - Inches(0.08))
                tf_sc = tb_sc.text_frame
                tf_sc.word_wrap = True
                tf_sc.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf_sc.margin_left = tf_sc.margin_right = Pt(3)
                tf_sc.margin_top = tf_sc.margin_bottom = Pt(2)
                p_s = tf_sc.paragraphs[0]
                p_s.alignment = PP_ALIGN.CENTER
                p_s.text = glyph
                p_s.font.name = theme.font_family_header
                p_s.font.size = Pt(10.0)
                p_s.font.bold = True
                p_s.font.color.rgb = hex_to_rgb("#1E3A8A") if is_rec else theme.get_rgb("primary")

        # Opt-in Impact Column with calibrated 3-tier severity
        if has_impact:
            imp_str = str(row.business_impact or "").strip().upper()
            tb_imp = slide.shapes.add_textbox(table_left + cat_w + crit_w + len(platforms) * plat_w + Inches(0.04), cur_y + Inches(0.04), impact_w - Inches(0.08), row_h - Inches(0.08))
            tf_imp = tb_imp.text_frame
            tf_imp.word_wrap = True
            tf_imp.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_imp.margin_left = tf_imp.margin_right = Pt(3)
            tf_imp.margin_top = tf_imp.margin_bottom = Pt(2)
            p_im = tf_imp.paragraphs[0]
            p_im.alignment = PP_ALIGN.CENTER
            p_im.text = imp_str or "-"
            p_im.font.name = theme.font_family_header
            p_im.font.size = Pt(9.5)
            p_im.font.bold = True
            if imp_str in ("CRITICAL", "BLOCKER"):
                p_im.font.color.rgb = RGBColor(220, 38, 38)
            elif imp_str in ("HIGH", "WARNING"):
                p_im.font.color.rgb = RGBColor(217, 119, 6)
            elif imp_str == "MEDIUM":
                p_im.font.color.rgb = theme.get_rgb("accent")
            else:
                p_im.font.color.rgb = theme.get_rgb("muted")

        cur_y += row_h

    # 5. Strictly Opt-In Footnote / Legend
    if footnote_str:
        foot_y = cur_y + Inches(0.12)
        tb_fn = slide.shapes.add_textbox(table_left, foot_y, table_w, Inches(0.42))
        tf_fn = tb_fn.text_frame
        tf_fn.word_wrap = True
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = footnote_str
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.5)
        p_fn.font.italic = True
        p_fn.font.color.rgb = RGBColor(100, 116, 139)

    # 6. Slide Footer
    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide



@dataclass
class TableColumnDef:
    header: str
    width: float  # In inches
    align: str = "LEFT"  # "LEFT", "CENTER", "RIGHT"
    is_status: bool = False
    is_index: bool = False
    is_highlight: bool = False


def _render_table_row(
    slide: Any,
    theme: Theme,
    columns: List[TableColumnDef],
    scaled_widths: List[Inches],
    row: List[Any],
    start_x: Inches,
    cur_ry: Inches,
    total_w: Inches,
    row_h: Inches,
    font_size_pt: float,
    status_keywords: set[str],
    is_alt: bool = False,
    is_detached: bool = False,
) -> None:
    """Render one table data row, either contiguous or highlighted as a detached addendum row."""
    if is_detached:
        card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, cur_ry, total_w, row_h)
        card.shadow.inherit = False
        card.fill.solid()
        card.fill.fore_color.rgb = hex_to_rgb("#F0F9FF")
        card.line.color.rgb = theme.get_rgb("accent")
        card.line.width = Pt(1.25)
        strip_shape_shadows(card)

        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, cur_ry, Pt(4.0), row_h)
        stripe.shadow.inherit = False
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = theme.get_rgb("accent")
        stripe.line.fill.background()
        strip_shape_shadows(stripe)
    else:
        if is_alt:
            row_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, cur_ry, total_w, row_h)
            row_bg.fill.solid()
            row_bg.fill.fore_color.rgb = theme.get_rgb("surface_muted")
            row_bg.line.fill.background()
            strip_shape_shadows(row_bg)

        row_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, cur_ry + row_h, total_w, Pt(0.5))
        row_div.fill.solid()
        row_div.fill.fore_color.rgb = theme.get_rgb("border")
        row_div.line.fill.background()
        strip_shape_shadows(row_div)

    cur_cx = start_x
    dim_idx = 1 if (columns and columns[0].is_index) else 0
    for c_idx, col in enumerate(columns):
        cw = scaled_widths[c_idx]
        is_highlighted = getattr(col, "is_highlight", False)
        if is_highlighted and not is_detached:
            cell_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cur_cx, cur_ry, cw, row_h)
            cell_card.fill.solid()
            cell_card.fill.fore_color.rgb = RGBColor(238, 246, 255)
            cell_card.line.fill.background()
            strip_shape_shadows(cell_card)

        cell_val = row[c_idx] if c_idx < len(row) else ""
        cell_color_override: Optional[str] = None
        if isinstance(cell_val, dict):
            cell_str = str(cell_val.get("text") or cell_val.get("label") or cell_val.get("status") or "").strip()
            raw_ov = cell_val.get("color") or cell_val.get("status_color") or cell_val.get("badge_color")
            if isinstance(raw_ov, str) and raw_ov.strip():
                cell_color_override = raw_ov.strip().lower()
        else:
            cell_str = str(cell_val).strip()
        is_status_col = col.is_status or (cell_str.upper() in status_keywords and len(cell_str) <= 24)

        if is_status_col and cell_str:
            pill_w = min(cw - Inches(0.16), max(Inches(1.80), cw * 0.92))
            pill_h = min(row_h - Inches(0.14), Inches(0.30))
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
                font_size_pt=max(8.0, font_size_pt - 1.5),
                override_color_key=cell_color_override or ("accent" if is_detached else None),
            )
        else:
            is_idx_col = col.is_index or (c_idx == 0 and cell_str.isdigit())
            tb = slide.shapes.add_textbox(
                cur_cx + (Inches(0.02) if is_idx_col else Inches(0.08)),
                cur_ry + Inches(0.02),
                cw - (Inches(0.04) if is_idx_col else Inches(0.16)),
                row_h - Inches(0.04),
            )
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = Pt(1) if is_idx_col else Pt(6)
            tf.margin_right = Pt(1) if is_idx_col else Pt(6)
            tf.margin_top = Pt(2)
            tf.margin_bottom = Pt(2)
            p = tf.paragraphs[0]
            p.text = cell_str
            p.alignment = PP_ALIGN.CENTER if col.align == "CENTER" else (PP_ALIGN.RIGHT if col.align == "RIGHT" else PP_ALIGN.LEFT)

            if is_idx_col:
                p.font.name = theme.font_family_header
                p.font.size = Pt(font_size_pt + 0.5)
                p.font.bold = True
                p.font.color.rgb = theme.get_rgb("accent")
            elif is_highlighted:
                p.font.name = theme.font_family_header
                p.font.size = Pt(font_size_pt)
                p.font.bold = True
                p.font.color.rgb = hex_to_rgb("#1E3A8A")
            elif c_idx == dim_idx:
                p.font.name = theme.font_family_header
                p.font.size = Pt(font_size_pt)
                p.font.bold = True
                p.font.color.rgb = theme.get_rgb("primary")
            else:
                p.font.name = theme.font_family
                p.font.size = Pt(font_size_pt)
                p.font.color.rgb = theme.get_rgb("primary" if is_detached else "secondary")

        cur_cx += cw


def build_table_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Structured Governance Register Establishes Accountabilities and Timelines",
    subtitle: Optional[str] = None,
    columns: Optional[List[TableColumnDef]] = None,
    rows: Optional[List[List[Any]]] = None,
    detached_rows: Optional[List[List[Any]]] = None,
    detached_connector_symbol: str = "+",
    footnote: Optional[str] = None,
    takeaway: Optional[Dict[str, Any]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    Renders an executive consulting table/matrix slide using sharp vector cards.
    Includes primary color header band, alternating row shading, dynamic status pills, and footnotes.
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    if not columns or not rows:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    start_x = Inches(0.80)
    total_w = Inches(11.733)
    header_y = resolve_content_top(header_bottom, gap_in=0.20)
    header_h = Inches(0.38)

    # Normalize column widths to sum exactly to total_w
    col_widths_sum = sum(c.width for c in columns)
    scale_w = (total_w.inches / col_widths_sum) if col_widths_sum > 0 else 1.0
    scaled_widths = [Inches(c.width * scale_w) for c in columns]

    # Header Band (Single-Line Rule: Muted surface with dark bold slate text, eliminating the solid dark banner block)
    hdr_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, header_y, total_w, header_h)
    hdr_card.fill.solid()
    hdr_card.fill.fore_color.rgb = theme.get_rgb("surface_muted")
    hdr_card.line.fill.background()
    strip_shape_shadows(hdr_card)

    # Clean hairline divider under header row
    hdr_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, header_y + header_h, total_w, Pt(1.0))
    hdr_div.fill.solid()
    hdr_div.fill.fore_color.rgb = theme.get_rgb("border")
    hdr_div.line.fill.background()
    strip_shape_shadows(hdr_div)

    cur_x = start_x
    for c_idx, col in enumerate(columns):
        cw = scaled_widths[c_idx]
        is_highlighted = getattr(col, "is_highlight", False)
        if is_highlighted:
            hdr_hl = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cur_x, header_y, cw, header_h)
            hdr_hl.fill.solid()
            hdr_hl.fill.fore_color.rgb = hex_to_rgb("#1E3A8A")
            hdr_hl.line.fill.background()
            strip_shape_shadows(hdr_hl)

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
        p.font.size = Pt(9.0)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255) if is_highlighted else theme.get_rgb("primary")
        cur_x += cw

    # Rows (reserve space for optional detached addendum rows + centered connector icon)
    num_rows = len(rows)
    d_rows = list(detached_rows) if detached_rows else []
    n_detached = len(d_rows)
    connector_gap = Inches(0.46) if n_detached > 0 else Inches(0)
    row_start_y = header_y + header_h
    bottom_bound = Inches(6.68 if footnote else 6.86)
    avail_row_h = max(Inches(2.40), bottom_bound - row_start_y)
    total_data_rows = num_rows + n_detached

    if takeaway:
        is_two_row_tk = isinstance(takeaway, dict) and bool(takeaway.get("title") and takeaway.get("description"))
        tk_bottom = Inches(5.32 if is_two_row_tk else 6.08)
        if footnote:
            tk_bottom -= Inches(0.24)
        avail_table_h = max(Inches(1.80), tk_bottom - row_start_y)
        row_h = min(Inches(0.56), max(Inches(0.30), (avail_table_h - connector_gap) / total_data_rows))
    else:
        max_h = Inches(0.65) if total_data_rows <= 5 else Inches(0.50)
        row_h = min(max_h, max(Inches(0.30), (avail_row_h - connector_gap) / total_data_rows))

    status_keywords = {
        "COMPLETE", "COMPLETED", "IN PROGRESS", "ON TRACK", "RESCHEDULED", "PLANNED",
        "READY", "NOT READY", "AVAILABLE", "PARTIAL", "PARTIALLY AVAILABLE",
        "NOT AVAILABLE", "UNAVAILABLE", "REQUIRES VALIDATION",
        "CRITICAL GATE", "MILESTONE GATE", "HIGH", "MEDIUM", "LOW", "SIGNED-OFF",
        "MUTUAL", "DAILY", "WEEKLY", "AS NEEDED", "OPEN", "RESOLVED", "INCLUDE ANYWAY"
    }

    font_size_pt = 9.0 if total_data_rows > 8 else (10.0 if total_data_rows > 5 else 10.5)

    for r_idx, row in enumerate(rows):
        cur_ry = row_start_y + r_idx * row_h
        _render_table_row(
            slide=slide,
            theme=theme,
            columns=columns,
            scaled_widths=scaled_widths,
            row=row,
            start_x=start_x,
            cur_ry=cur_ry,
            total_w=total_w,
            row_h=row_h,
            font_size_pt=font_size_pt,
            status_keywords=status_keywords,
            is_alt=(r_idx % 2 != 0),
            is_detached=False,
        )

    if n_detached > 0:
        table_end_y = row_start_y + num_rows * row_h
        sym = str(detached_connector_symbol or "+").strip()
        if sym:
            badge_d = Inches(0.30)
            badge_x = start_x + (total_w - badge_d) / 2
            badge_y = table_end_y + (connector_gap - badge_d) / 2
            badge_oval = slide.shapes.add_shape(MSO_SHAPE.OVAL, badge_x, badge_y, badge_d, badge_d)
            badge_oval.shadow.inherit = False
            badge_oval.fill.solid()
            badge_oval.fill.fore_color.rgb = hex_to_rgb("#E0F2FE")
            badge_oval.line.color.rgb = theme.get_rgb("accent")
            badge_oval.line.width = Pt(1.25)
            strip_shape_shadows(badge_oval)
            tf_sym = badge_oval.text_frame
            tf_sym.word_wrap = False
            tf_sym.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_sym.margin_left = tf_sym.margin_right = tf_sym.margin_top = tf_sym.margin_bottom = 0
            p_sym = tf_sym.paragraphs[0]
            p_sym.text = sym
            p_sym.alignment = PP_ALIGN.CENTER
            p_sym.font.name = theme.font_family_header
            p_sym.font.size = Pt(14.0)
            p_sym.font.bold = True
            p_sym.font.color.rgb = theme.get_rgb("accent")

        det_start_y = table_end_y + connector_gap
        for d_idx, d_row in enumerate(d_rows):
            _render_table_row(
                slide=slide,
                theme=theme,
                columns=columns,
                scaled_widths=scaled_widths,
                row=d_row,
                start_x=start_x,
                cur_ry=det_start_y + d_idx * row_h,
                total_w=total_w,
                row_h=row_h,
                font_size_pt=font_size_pt,
                status_keywords=status_keywords,
                is_alt=False,
                is_detached=True,
            )

    if takeaway:
        is_two_row_tk = isinstance(takeaway, dict) and bool(takeaway.get("title") and takeaway.get("description"))
        if is_two_row_tk:
            takeaway_top = row_start_y + total_data_rows * row_h + connector_gap + Inches(0.14)
            takeaway_h = Inches(1.30)
        else:
            takeaway_top = Inches(6.08) if footnote else Inches(6.28)
            takeaway_h = Inches(0.54)
        add_takeaway_bar(slide, theme, takeaway, top_y=takeaway_top, left_x=start_x, width=total_w, height=takeaway_h)

    if footnote:
        foot_y = Inches(6.75)
        tb_fn = slide.shapes.add_textbox(start_x, foot_y, total_w, Inches(0.22))
        tf_fn = tb_fn.text_frame
        tf_fn.word_wrap = False
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.5)
        p_fn.font.color.rgb = theme.get_rgb("muted")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


_NAMED_ACCENT_HEX: Dict[str, str] = {
    "brickred": "#DC2626",
    "brick_red": "#DC2626",
    "snowblue": "#0284C7",
    "snow_blue": "#0284C7",
    "maroon": "#800000",
    "maroon_red": "#800000",
    "crimson": "#991B1B",
    "red": "#DC2626",
    "blue": "#0284C7",
    "amber": "#D97706",
    "green": "#16A34A",
    "teal": "#0F766E",
    "slate": "#475569",
}


def _resolve_narrative_color(
    color_spec: Optional[Union[str, RGBColor]],
    theme: Theme,
    default_key: str = "accent",
) -> RGBColor:
    """Resolve a hex string, named preset (e.g. brickred, snowblue, maroon), or theme token into RGBColor."""
    if isinstance(color_spec, RGBColor):
        return color_spec
    if isinstance(color_spec, str) and color_spec.strip():
        clean = color_spec.strip()
        low = clean.lower().replace("-", "_")
        if low in _NAMED_ACCENT_HEX:
            return hex_to_rgb(_NAMED_ACCENT_HEX[low])
        if clean.startswith("#") and len(clean) in (4, 7):
            return hex_to_rgb(clean)
        try:
            return theme.get_rgb(low)
        except Exception:
            pass
    return theme.get_rgb(default_key)


def _draw_hairline(
    slide: Any,
    left: Inches,
    top: Inches,
    width: Inches,
    color: RGBColor,
    width_pt: float = 0.75,
) -> Any:
    """Draw a flat horizontal hairline divider with zero shadow."""
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Pt(width_pt))
    line.shadow.inherit = False
    strip_shape_shadows(line)
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line


def build_narrative_row_list_slide(
    prs_or_slide: Any,
    theme: Optional[Theme] = None,
    tracker: Optional[str] = None,
    action_title: str = "Open-Canvas Narrative Breakdown",
    subtitle: Optional[str] = None,
    rows: Optional[List[Dict[str, Any]]] = None,
    sections: Optional[List[Dict[str, Any]]] = None,
    sidebar_title: Optional[str] = None,
    sidebar_note: Optional[str] = None,
    show_index: bool = False,
    flag_stripe: bool = False,
    footer_callout: Optional[str] = None,
    obligated_color: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    Open-canvas, hairline-separated qualitative row list (McKinsey / Oliver Wyman style).

    Obligated fields: action_title, and rows (or sections[].rows) with title + description/bullets.
    Optional fields: tracker, subtitle, sidebar_title/sidebar_note, index/badge, lead_in,
    accent_color (per-section or per-row, e.g. 'brickred', 'snowblue', '#800000'),
    flag_stripe (vertical color-flag bar on left edge), footer_callout, obligated_color.
    """
    if theme is None:
        theme = get_theme("default")

    if hasattr(prs_or_slide, "slides"):
        slide = add_slide_with_background(prs_or_slide, theme)
    else:
        slide = prs_or_slide

    ob_rgb = _resolve_narrative_color(obligated_color, theme, "primary") if obligated_color else None

    header_bottom = add_slide_header(
        slide,
        theme,
        tracker=tracker,
        action_title=action_title,
        subtitle=subtitle,
    )
    # If obligated_color is set, tint the obligated action title textBox to signal required element
    if ob_rgb is not None:
        for shp in slide.shapes:
            if shp.has_text_frame and shp.top < Inches(1.2) and shp.left == Inches(0.8):
                for p in shp.text_frame.paragraphs:
                    if p.text and p.text.strip() == action_title.strip():
                        for run in p.runs:
                            run.font.color.rgb = ob_rgb

    content_top_in = max(0.98, header_bottom + 0.14)
    max_bottom_in = 6.52 if footer_callout else 6.88
    left_margin_in = 0.80
    total_w_in = 11.733

    # Optional Left Sidebar (McKinsey Debate/Question Rail)
    if sidebar_title:
        rail_w_in = 2.95
        gap_in = 0.35
        tb_sb = slide.shapes.add_textbox(
            Inches(left_margin_in),
            Inches(content_top_in),
            Inches(rail_w_in),
            Inches(max_bottom_in - content_top_in),
        )
        tf_sb = tb_sb.text_frame
        tf_sb.word_wrap = True
        tf_sb.margin_left = tf_sb.margin_right = tf_sb.margin_top = tf_sb.margin_bottom = 0
        p_sb = tf_sb.paragraphs[0]
        p_sb.text = sidebar_title
        p_sb.font.name = theme.font_family_header
        p_sb.font.size = Pt(15.0)
        p_sb.font.bold = True
        p_sb.font.color.rgb = theme.get_rgb("primary")
        if sidebar_note:
            p_sn = tf_sb.add_paragraph()
            p_sn.space_before = Pt(10)
            p_sn.text = sidebar_note
            p_sn.font.name = theme.font_family
            p_sn.font.size = Pt(9.5)
            p_sn.font.color.rgb = theme.get_rgb("muted")
        list_left_in = left_margin_in + rail_w_in + gap_in
        list_w_in = total_w_in - rail_w_in - gap_in
    else:
        list_left_in = left_margin_in
        list_w_in = total_w_in

    # Normalize into sections
    norm_sections: List[Dict[str, Any]] = []
    if sections:
        for sec in sections:
            norm_sections.append({
                "title": sec.get("title"),
                "accent_color": sec.get("accent_color"),
                "flag_stripe": sec.get("flag_stripe", flag_stripe),
                "rows": list(sec.get("rows") or []),
            })
    else:
        norm_sections.append({
            "title": None,
            "accent_color": None,
            "flag_stripe": flag_stripe,
            "rows": list(rows or []),
        })

    total_rows = sum(len(s["rows"]) for s in norm_sections)
    if total_rows == 0:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    section_headers_count = sum(1 for s in norm_sections if s.get("title"))
    is_dense = total_rows >= 8
    section_hdr_h_in = 0.25 if is_dense else 0.30
    section_gap_in = (0.10 if is_dense else 0.16) if len(norm_sections) > 1 else 0.0
    avail_h_in = (
        (max_bottom_in - content_top_in)
        - (section_headers_count * section_hdr_h_in)
        - (max(0, len(norm_sections) - 1) * section_gap_in)
    )
    row_h_in = max(0.38, min(1.18, avail_h_in / max(1, total_rows)))
    is_compact = row_h_in < 0.62

    cur_y_in = content_top_in
    global_idx = 1

    for sec_i, sec in enumerate(norm_sections):
        sec_accent = _resolve_narrative_color(sec.get("accent_color"), theme, "accent")
        sec_flag = bool(sec.get("flag_stripe", flag_stripe))

        if sec.get("title"):
            tb_sh = slide.shapes.add_textbox(
                Inches(list_left_in),
                Inches(cur_y_in),
                Inches(list_w_in),
                Inches(0.24),
            )
            tf_sh = tb_sh.text_frame
            tf_sh.word_wrap = False
            tf_sh.margin_left = tf_sh.margin_right = tf_sh.margin_top = tf_sh.margin_bottom = 0
            p_sh = tf_sh.paragraphs[0]
            p_sh.text = str(sec["title"])
            p_sh.font.name = theme.font_family_header
            p_sh.font.size = Pt(11.0)
            p_sh.font.bold = True
            p_sh.font.color.rgb = sec_accent
            _draw_hairline(
                slide,
                Inches(list_left_in),
                Inches(cur_y_in + 0.25),
                Inches(list_w_in),
                sec_accent,
                width_pt=1.25,
            )
            cur_y_in += section_hdr_h_in

        sec_rows = sec["rows"]
        for r_i, row in enumerate(sec_rows):
            row_accent = _resolve_narrative_color(row.get("accent_color") or sec.get("accent_color"), theme, "accent")
            row_flag = bool(row.get("flag_stripe", sec_flag))
            row_title = str(row.get("title") or row.get("label") or "")
            lead_in = row.get("lead_in") or row.get("question")
            bullets = row.get("bullets")
            desc = row.get("description") or row.get("body") or ""
            idx_val = row.get("index") or row.get("badge") or (str(global_idx) if show_index else None)
            global_idx += 1

            # Optional vertical color-flag stripe (Image 4 maturity-inspired)
            stripe_offset_in = 0.0
            if row_flag:
                stripe_h_in = max(0.28, row_h_in - 0.12)
                st = slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE,
                    Inches(list_left_in),
                    Inches(cur_y_in + 0.06),
                    Pt(3.5),
                    Inches(stripe_h_in),
                )
                st.shadow.inherit = False
                strip_shape_shadows(st)
                st.fill.solid()
                st.fill.fore_color.rgb = row_accent
                st.line.fill.background()
                stripe_offset_in = 0.14

            # Optional circular index badge
            badge_offset_in = 0.0
            if idx_val is not None:
                badge_d_in = 0.26 if is_compact else 0.30
                badge_y_in = cur_y_in + (row_h_in - badge_d_in) / 2.0
                circ = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Inches(list_left_in + stripe_offset_in),
                    Inches(badge_y_in),
                    Inches(badge_d_in),
                    Inches(badge_d_in),
                )
                circ.shadow.inherit = False
                strip_shape_shadows(circ)
                circ.fill.solid()
                circ.fill.fore_color.rgb = row_accent
                circ.line.fill.background()
                tf_c = circ.text_frame
                tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
                p_c = tf_c.paragraphs[0]
                p_c.text = str(idx_val)
                p_c.alignment = PP_ALIGN.CENTER
                p_c.font.name = theme.font_family_header
                p_c.font.size = Pt(9.5 if is_compact else 10.5)
                p_c.font.bold = True
                p_c.font.color.rgb = RGBColor(255, 255, 255)
                badge_offset_in = badge_d_in + 0.14

            # Left topic / label column
            topic_x_in = list_left_in + stripe_offset_in + badge_offset_in
            topic_w_in = 2.45 if list_w_in > 9.0 else 1.85
            tb_topic = slide.shapes.add_textbox(
                Inches(topic_x_in),
                Inches(cur_y_in + 0.04),
                Inches(topic_w_in),
                Inches(row_h_in - 0.08),
            )
            tf_top = tb_topic.text_frame
            tf_top.word_wrap = True
            tf_top.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_top.margin_left = tf_top.margin_right = tf_top.margin_top = tf_top.margin_bottom = 0
            p_top = tf_top.paragraphs[0]
            p_top.text = row_title
            p_top.font.name = theme.font_family_header
            p_top.font.size = Pt(10.5 if is_compact else 11.5)
            p_top.font.bold = True
            p_top.font.color.rgb = (
                _resolve_narrative_color(row["title_color"], theme, "primary")
                if row.get("title_color")
                else (ob_rgb if ob_rgb is not None else theme.get_rgb("primary"))
            )

            # Right narrative / bullets column
            body_x_in = topic_x_in + topic_w_in + 0.22
            body_w_in = (list_left_in + list_w_in) - body_x_in
            tb_body = slide.shapes.add_textbox(
                Inches(body_x_in),
                Inches(cur_y_in + 0.04),
                Inches(body_w_in),
                Inches(row_h_in - 0.08),
            )
            tf_body = tb_body.text_frame
            tf_body.word_wrap = True
            tf_body.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_body.margin_left = tf_body.margin_right = tf_body.margin_top = tf_body.margin_bottom = 0

            body_rgb = (
                _resolve_narrative_color(row["body_color"], theme, "secondary")
                if row.get("body_color")
                else (ob_rgb if ob_rgb is not None else theme.get_rgb("secondary"))
            )
            body_pt = 9.5 if is_compact else 10.5
            first_para = True

            if lead_in:
                p_li = tf_body.paragraphs[0]
                first_para = False
                p_li.text = str(lead_in)
                p_li.font.name = theme.font_family_header
                p_li.font.size = Pt(body_pt + 0.5)
                p_li.font.bold = True
                p_li.font.color.rgb = row_accent

            if bullets and isinstance(bullets, list):
                for b_item in bullets:
                    p_b = tf_body.paragraphs[0] if first_para else tf_body.add_paragraph()
                    first_para = False
                    p_b.space_before = Pt(2 if is_compact else 3)
                    append_formatted_runs(
                        paragraph=p_b,
                        text=f"• {b_item}",
                        font_name=theme.font_family,
                        font_size_pt=body_pt,
                        font_color=body_rgb,
                    )
            elif desc:
                p_d = tf_body.paragraphs[0] if first_para else tf_body.add_paragraph()
                if not first_para:
                    p_d.space_before = Pt(2)
                append_formatted_runs(
                    paragraph=p_d,
                    text=str(desc),
                    font_name=theme.font_family,
                    font_size_pt=body_pt,
                    font_color=body_rgb,
                )

            cur_y_in += row_h_in

            # Hairline divider between rows (not after last row in a section)
            if r_i < len(sec_rows) - 1:
                _draw_hairline(
                    slide,
                    Inches(list_left_in),
                    Inches(cur_y_in),
                    Inches(list_w_in),
                    theme.get_rgb("border"),
                    width_pt=0.75,
                )

        if sec_i < len(norm_sections) - 1:
            cur_y_in += section_gap_in

    # Optional bottom callout bar (Oliver Wyman style)
    if footer_callout:
        _draw_hairline(
            slide,
            Inches(left_margin_in),
            Inches(6.54),
            Inches(total_w_in),
            theme.get_rgb("border"),
            width_pt=0.75,
        )
        tb_fc = slide.shapes.add_textbox(Inches(left_margin_in), Inches(6.60), Inches(total_w_in), Inches(0.28))
        tf_fc = tb_fc.text_frame
        tf_fc.word_wrap = False
        tf_fc.margin_left = tf_fc.margin_right = tf_fc.margin_top = tf_fc.margin_bottom = 0
        p_fc = tf_fc.paragraphs[0]
        append_formatted_runs(
            paragraph=p_fc,
            text=footer_callout,
            font_name=theme.font_family,
            font_size_pt=9.5,
            font_color=theme.get_rgb("secondary"),
        )

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


def build_tiered_priority_ladder_slide(
    prs_or_slide: Any,
    theme: Optional[Theme] = None,
    tracker: Optional[str] = None,
    action_title: str = "Strategic Priority Action Ladder",
    subtitle: Optional[str] = None,
    left_header: str = "Priority",
    right_header: str = "Recommendation",
    tiers: Optional[List[Dict[str, Any]]] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    BCG-style asymmetric 2-column priority ladder (Batch 1, Image 2).
    Left column renders grouped solid tier blocks spanning their child items;
    right column renders circular numbered badges (1..N) + action items separated by hairlines.
    """
    if theme is None:
        theme = get_theme("default")

    if hasattr(prs_or_slide, "slides"):
        slide = add_slide_with_background(prs_or_slide, theme)
    else:
        slide = prs_or_slide

    header_bottom = add_slide_header(
        slide,
        theme,
        tracker=tracker,
        action_title=action_title,
        subtitle=subtitle,
    )
    top_y_in = max(1.05, header_bottom + 0.16)
    left_margin_in = 0.80
    total_w_in = 11.733
    tier_w_in = 2.15
    col_gap_in = 0.24
    right_x_in = left_margin_in + tier_w_in + col_gap_in
    right_w_in = (left_margin_in + total_w_in) - right_x_in

    # Column Headers + Top Hairlines
    for h_x, h_w, h_txt in [
        (left_margin_in, tier_w_in, left_header),
        (right_x_in, right_w_in, right_header),
    ]:
        tb_h = slide.shapes.add_textbox(Inches(h_x), Inches(top_y_in), Inches(h_w), Inches(0.28))
        tf_h = tb_h.text_frame
        tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0
        p_h = tf_h.paragraphs[0]
        p_h.text = h_txt
        p_h.alignment = PP_ALIGN.CENTER
        p_h.font.name = theme.font_family_header
        p_h.font.size = Pt(12.0)
        p_h.font.bold = True
        p_h.font.color.rgb = theme.get_rgb("primary")
        draw_hairline(slide, Inches(h_x), Inches(top_y_in + 0.30), Inches(h_w), theme.get_rgb("accent"), width_pt=1.25)

    tier_list = list(tiers or [])
    total_items = sum(len(t.get("items") or []) for t in tier_list)
    if total_items == 0:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    body_top_in = top_y_in + 0.38
    max_bottom_in = 6.55 if footnote else 6.85
    avail_h_in = max_bottom_in - body_top_in
    row_h_in = avail_h_in / total_items

    cur_y_in = body_top_in
    global_idx = 1

    for t_i, tier in enumerate(tier_list):
        t_items = list(tier.get("items") or [])
        if not t_items:
            continue
        t_accent = resolve_accent_color(tier.get("accent_color"), theme, "accent")
        t_label = str(tier.get("label") or tier.get("title") or "")
        block_h_in = len(t_items) * row_h_in - (0.06 if t_i < len(tier_list) - 1 else 0.0)

        # Left grouped tier rectangle
        rect = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(left_margin_in),
            Inches(cur_y_in + 0.02),
            Inches(tier_w_in),
            Inches(max(0.32, block_h_in - 0.02)),
        )
        rect.shadow.inherit = False
        strip_shape_shadows(rect)
        rect.fill.solid()
        rect.fill.fore_color.rgb = t_accent
        rect.line.fill.background()
        tf_r = rect.text_frame
        tf_r.word_wrap = True
        tf_r.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_r.margin_left = tf_r.margin_right = Inches(0.10)
        p_r = tf_r.paragraphs[0]
        p_r.text = t_label
        p_r.alignment = PP_ALIGN.CENTER
        p_r.font.name = theme.font_family_header
        p_r.font.size = Pt(12.5)
        p_r.font.bold = True
        p_r.font.color.rgb = _get_contrast_text_color(t_accent)

        # Right numbered items
        for it_i, item in enumerate(t_items):
            item_y_in = cur_y_in + it_i * row_h_in
            if isinstance(item, dict):
                item_idx = str(item.get("index") or global_idx)
                item_text = str(item.get("text") or item.get("description") or "")
            else:
                item_idx = str(global_idx)
                item_text = str(item)
            global_idx += 1

            badge_d_in = min(0.32, max(0.24, row_h_in * 0.54))
            badge_y_in = item_y_in + (row_h_in - badge_d_in) / 2.0
            circ = slide.shapes.add_shape(
                MSO_SHAPE.OVAL,
                Inches(right_x_in + 0.04),
                Inches(badge_y_in),
                Inches(badge_d_in),
                Inches(badge_d_in),
            )
            circ.shadow.inherit = False
            strip_shape_shadows(circ)
            circ.fill.solid()
            circ.fill.fore_color.rgb = t_accent
            circ.line.fill.background()
            tf_c = circ.text_frame
            tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
            p_c = tf_c.paragraphs[0]
            p_c.text = item_idx
            p_c.alignment = PP_ALIGN.CENTER
            p_c.font.name = theme.font_family_header
            p_c.font.size = Pt(10.0)
            p_c.font.bold = True
            p_c.font.color.rgb = _get_contrast_text_color(t_accent)

            text_x_in = right_x_in + badge_d_in + 0.22
            tb_it = slide.shapes.add_textbox(
                Inches(text_x_in),
                Inches(item_y_in + 0.03),
                Inches((right_x_in + right_w_in) - text_x_in),
                Inches(row_h_in - 0.06),
            )
            tf_it = tb_it.text_frame
            tf_it.word_wrap = True
            tf_it.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_it.margin_left = tf_it.margin_right = tf_it.margin_top = tf_it.margin_bottom = 0
            p_it = tf_it.paragraphs[0]
            append_formatted_runs(
                paragraph=p_it,
                text=item_text,
                font_name=theme.font_family,
                font_size_pt=10.5 if total_items <= 7 else 9.5,
                font_color=theme.get_rgb("primary"),
            )

            if not (t_i == len(tier_list) - 1 and it_i == len(t_items) - 1):
                draw_hairline(
                    slide,
                    Inches(right_x_in),
                    Inches(item_y_in + row_h_in),
                    Inches(right_w_in),
                    theme.get_rgb("border"),
                    width_pt=0.75,
                )

        cur_y_in += len(t_items) * row_h_in

    if footnote:
        tb_fn = slide.shapes.add_textbox(Inches(left_margin_in), Inches(6.65), Inches(total_w_in), Inches(0.24))
        tf_fn = tb_fn.text_frame
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.5)
        p_fn.font.color.rgb = theme.get_rgb("muted")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


def build_bubble_matrix_slide(
    prs_or_slide: Any,
    theme: Optional[Theme] = None,
    tracker: Optional[str] = None,
    action_title: str = "Proportional Entity & Metric Matrix",
    subtitle: Optional[str] = None,
    entities: Optional[List[str]] = None,
    rows: Optional[List[Dict[str, Any]]] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    BCG-style proportional bubble matrix (Batch 2, Image 1).
    Plots data-driven area-proportional circles across entities and metrics,
    interleaved with optional qualitative delta rows.
    """
    import math

    if theme is None:
        theme = get_theme("default")

    if hasattr(prs_or_slide, "slides"):
        slide = add_slide_with_background(prs_or_slide, theme)
    else:
        slide = prs_or_slide

    header_bottom = add_slide_header(
        slide,
        theme,
        tracker=tracker,
        action_title=action_title,
        subtitle=subtitle,
    )
    top_y_in = max(1.05, header_bottom + 0.16)
    left_margin_in = 0.80
    total_w_in = 11.733
    label_col_w_in = 1.95
    ent_list = list(entities or [])
    row_list = list(rows or [])

    if not ent_list or not row_list:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    ent_w_in = (total_w_in - label_col_w_in) / len(ent_list)

    # Column entity headers
    hdr_h_in = 0.42
    for e_i, ent_name in enumerate(ent_list):
        ex_in = left_margin_in + label_col_w_in + e_i * ent_w_in
        tb_e = slide.shapes.add_textbox(Inches(ex_in), Inches(top_y_in), Inches(ent_w_in), Inches(hdr_h_in))
        tf_e = tb_e.text_frame
        tf_e.word_wrap = True
        tf_e.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_e.margin_left = tf_e.margin_right = tf_e.margin_top = tf_e.margin_bottom = 0
        p_e = tf_e.paragraphs[0]
        p_e.text = str(ent_name)
        p_e.alignment = PP_ALIGN.CENTER
        p_e.font.name = theme.font_family_header
        p_e.font.size = Pt(10.5)
        p_e.font.bold = True
        p_e.font.color.rgb = theme.get_rgb("primary")

    body_top_in = top_y_in + hdr_h_in + 0.06
    draw_hairline(slide, Inches(left_margin_in), Inches(body_top_in), Inches(total_w_in), theme.get_rgb("muted"), width_pt=1.25)

    max_bottom_in = 6.50 if footnote else 6.85
    avail_h_in = max_bottom_in - body_top_in

    # Allocate row heights (bubble rows get more vertical weight than text rows)
    weights = [1.45 if str(r.get("type", "bubble")).lower() == "bubble" else 0.85 for r in row_list]
    total_weight = sum(weights) or 1.0

    cur_y_in = body_top_in
    for r_i, row in enumerate(row_list):
        r_h_in = avail_h_in * (weights[r_i] / total_weight)
        r_type = str(row.get("type", "bubble")).lower()
        r_label = str(row.get("label") or "")
        r_vals = list(row.get("values") or [])
        r_accent = resolve_accent_color(row.get("accent_color"), theme, "accent")

        # Left row label
        tb_rl = slide.shapes.add_textbox(
            Inches(left_margin_in),
            Inches(cur_y_in + 0.04),
            Inches(label_col_w_in - 0.14),
            Inches(r_h_in - 0.08),
        )
        tf_rl = tb_rl.text_frame
        tf_rl.word_wrap = True
        tf_rl.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_rl.margin_left = tf_rl.margin_right = tf_rl.margin_top = tf_rl.margin_bottom = 0
        p_rl = tf_rl.paragraphs[0]
        p_rl.text = r_label
        p_rl.font.name = theme.font_family_header
        p_rl.font.size = Pt(10.5)
        p_rl.font.bold = True
        p_rl.font.color.rgb = theme.get_rgb("primary")

        if r_type == "bubble":
            nums = []
            for v in r_vals:
                try:
                    nums.append(float(v))
                except (TypeError, ValueError):
                    nums.append(0.0)
            max_val = max((abs(n) for n in nums), default=1.0) or 1.0
            max_d_in = min(r_h_in * 0.84, ent_w_in * 0.78, float(row.get("max_diameter_in", 1.35)))
            min_d_in = min(max_d_in * 0.45, 0.36)
            unit_suffix = str(row.get("unit", ""))

            for e_i in range(len(ent_list)):
                val_raw = r_vals[e_i] if e_i < len(r_vals) else 0
                num_val = nums[e_i] if e_i < len(nums) else 0.0
                ratio = math.sqrt(abs(num_val) / max_val) if max_val > 0 else 0.0
                d_in = max(min_d_in, max_d_in * ratio)
                cx_in = left_margin_in + label_col_w_in + (e_i + 0.5) * ent_w_in
                cy_in = cur_y_in + r_h_in / 2.0

                circ = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Inches(cx_in - d_in / 2.0),
                    Inches(cy_in - d_in / 2.0),
                    Inches(d_in),
                    Inches(d_in),
                )
                circ.shadow.inherit = False
                strip_shape_shadows(circ)
                circ.fill.solid()
                circ.fill.fore_color.rgb = r_accent
                circ.line.fill.background()

                tf_c = circ.text_frame
                tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
                p_c = tf_c.paragraphs[0]
                disp_num = int(num_val) if float(num_val).is_integer() else round(num_val, 1)
                p_c.text = f"{disp_num}{unit_suffix}" if not isinstance(val_raw, str) else val_raw
                p_c.alignment = PP_ALIGN.CENTER
                p_c.font.name = theme.font_family_header
                p_c.font.size = Pt(9.5 if d_in < 0.55 else 11.0)
                p_c.font.bold = True
                p_c.font.color.rgb = _get_contrast_text_color(r_accent)
        else:
            for e_i in range(len(ent_list)):
                txt_val = str(r_vals[e_i]) if e_i < len(r_vals) else ""
                ex_in = left_margin_in + label_col_w_in + e_i * ent_w_in
                tb_v = slide.shapes.add_textbox(
                    Inches(ex_in + 0.06),
                    Inches(cur_y_in + 0.04),
                    Inches(ent_w_in - 0.12),
                    Inches(r_h_in - 0.08),
                )
                tf_v = tb_v.text_frame
                tf_v.word_wrap = True
                tf_v.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf_v.margin_left = tf_v.margin_right = tf_v.margin_top = tf_v.margin_bottom = 0
                p_v = tf_v.paragraphs[0]
                p_v.text = txt_val
                p_v.alignment = PP_ALIGN.CENTER
                p_v.font.name = theme.font_family
                p_v.font.size = Pt(9.5)
                p_v.font.color.rgb = theme.get_rgb("secondary")

        cur_y_in += r_h_in
        if r_i < len(row_list) - 1:
            draw_hairline(slide, Inches(left_margin_in), Inches(cur_y_in), Inches(total_w_in), theme.get_rgb("muted"), width_pt=1.0)

    if footnote:
        tb_fn = slide.shapes.add_textbox(Inches(left_margin_in), Inches(6.62), Inches(total_w_in), Inches(0.24))
        tf_fn = tb_fn.text_frame
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.5)
        p_fn.font.color.rgb = theme.get_rgb("muted")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


def build_ranked_bar_scorecard_slide(
    prs_or_slide: Any,
    theme: Optional[Theme] = None,
    tracker: Optional[str] = None,
    action_title: str = "Ranked Performance & Delta Scorecard",
    subtitle: Optional[str] = None,
    panels: Optional[List[Dict[str, Any]]] = None,
    callout: Optional[str] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    Distilled BCG ranked horizontal bar scorecard (Batch 3, Image 5).
    Supports 1 or 2 side-by-side horizontal bar panels with clean trend delta glyphs (↑, ↓, ≈)
    and zero noisy gradient backdrops.
    """
    if theme is None:
        theme = get_theme("default")

    if hasattr(prs_or_slide, "slides"):
        slide = add_slide_with_background(prs_or_slide, theme)
    else:
        slide = prs_or_slide

    header_bottom = add_slide_header(
        slide,
        theme,
        tracker=tracker,
        action_title=action_title,
        subtitle=subtitle,
    )
    top_y_in = max(1.05, header_bottom + 0.16)
    left_margin_in = 0.80
    total_w_in = 11.733
    panel_list = list(panels or [])[:2]

    if not panel_list:
        add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
        return slide

    panel_gap_in = 0.55 if len(panel_list) > 1 else 0.0
    panel_w_in = (total_w_in - panel_gap_in * (len(panel_list) - 1)) / len(panel_list)
    max_bottom_in = 6.18 if callout else (6.55 if footnote else 6.85)
    has_any_notes = any(p.get("notes") or p.get("takeaways") or p.get("analysis") for p in panel_list)
    notes_h_in = 1.25 if has_any_notes else 0.0
    notes_gap_in = 0.14 if has_any_notes else 0.0

    delta_map = {
        "UP": ("▲", "#16A34A"),
        "DOWN": ("▼", "#DC2626"),
        "FLAT": ("≈", "#0284C7"),
        "N/A": ("n.a.", "#64748B"),
    }

    for p_i, panel in enumerate(panel_list):
        px_in = left_margin_in + p_i * (panel_w_in + panel_gap_in)
        p_title = str(panel.get("title") or "")
        p_unit = str(panel.get("unit") or "%")
        p_accent = resolve_accent_color(panel.get("accent_color"), theme, "accent")
        bars = list(panel.get("bars") or [])

        # Panel Title + underline
        tb_pt = slide.shapes.add_textbox(Inches(px_in), Inches(top_y_in), Inches(panel_w_in), Inches(0.30))
        tf_pt = tb_pt.text_frame
        tf_pt.margin_left = tf_pt.margin_right = tf_pt.margin_top = tf_pt.margin_bottom = 0
        p_pt = tf_pt.paragraphs[0]
        p_pt.text = p_title
        p_pt.font.name = theme.font_family_header
        p_pt.font.size = Pt(12.5)
        p_pt.font.bold = True
        p_pt.font.color.rgb = theme.get_rgb("primary")
        draw_hairline(slide, Inches(px_in), Inches(top_y_in + 0.32), Inches(panel_w_in), p_accent, width_pt=1.0)

        if not bars:
            continue

        bars_top_in = top_y_in + 0.44
        avail_h_in = max_bottom_in - bars_top_in - notes_h_in - notes_gap_in
        row_h_in = min(0.74, avail_h_in / len(bars))
        has_delta = any(b.get("delta") for b in bars)
        delta_w_in = 0.42 if has_delta else 0.0
        lbl_w_in = min(2.35, panel_w_in * 0.36)
        val_w_in = 0.55
        bar_area_w_in = panel_w_in - delta_w_in - lbl_w_in - val_w_in - 0.16
        max_v = max((float(b.get("value", 0)) for b in bars), default=100.0) or 100.0

        for b_i, b in enumerate(bars):
            by_in = bars_top_in + b_i * row_h_in
            b_label = str(b.get("label") or "")
            b_val = float(b.get("value", 0))
            b_delta = str(b.get("delta") or "").upper()
            b_color = resolve_accent_color(b.get("accent_color"), theme, "accent") if b.get("accent_color") else (
                p_accent if b_i == 0 or b.get("highlight") else theme.get_rgb("border")
            )

            # Delta glyph
            if has_delta and b_delta in delta_map:
                glyph, g_hex = delta_map[b_delta]
                tb_d = slide.shapes.add_textbox(Inches(px_in), Inches(by_in), Inches(delta_w_in), Inches(row_h_in))
                tf_d = tb_d.text_frame
                tf_d.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf_d.margin_left = tf_d.margin_right = tf_d.margin_top = tf_d.margin_bottom = 0
                p_d = tf_d.paragraphs[0]
                p_d.text = glyph
                p_d.alignment = PP_ALIGN.CENTER
                p_d.font.name = theme.font_family_header
                p_d.font.size = Pt(10.0 if glyph != "n.a." else 8.5)
                p_d.font.bold = True
                p_d.font.color.rgb = hex_to_rgb(g_hex)

            # Right-aligned category label
            lbl_x_in = px_in + delta_w_in
            tb_l = slide.shapes.add_textbox(
                Inches(lbl_x_in),
                Inches(by_in + 0.02),
                Inches(lbl_w_in - 0.10),
                Inches(row_h_in - 0.04),
            )
            tf_l = tb_l.text_frame
            tf_l.word_wrap = True
            tf_l.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0
            p_l = tf_l.paragraphs[0]
            p_l.text = b_label
            p_l.alignment = PP_ALIGN.RIGHT
            p_l.font.name = theme.font_family
            p_l.font.size = Pt(9.5)
            p_l.font.bold = bool(b_i == 0 or b.get("highlight"))
            p_l.font.color.rgb = theme.get_rgb("primary")

            # Horizontal bar
            bar_x_in = lbl_x_in + lbl_w_in
            bar_h_in = min(0.36, row_h_in * 0.58)
            bar_y_in = by_in + (row_h_in - bar_h_in) / 2.0
            bar_w_in = max(0.08, bar_area_w_in * (b_val / max_v))
            bar_shp = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(bar_x_in),
                Inches(bar_y_in),
                Inches(bar_w_in),
                Inches(bar_h_in),
            )
            bar_shp.shadow.inherit = False
            strip_shape_shadows(bar_shp)
            bar_shp.fill.solid()
            bar_shp.fill.fore_color.rgb = b_color
            bar_shp.line.fill.background()

            # Value label
            tb_v = slide.shapes.add_textbox(
                Inches(bar_x_in + bar_w_in + 0.08),
                Inches(by_in),
                Inches(val_w_in),
                Inches(row_h_in),
            )
            tf_v = tb_v.text_frame
            tf_v.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_v.margin_left = tf_v.margin_right = tf_v.margin_top = tf_v.margin_bottom = 0
            p_v = tf_v.paragraphs[0]
            disp_v = int(b_val) if float(b_val).is_integer() else round(b_val, 1)
            p_v.text = f"{disp_v}{p_unit}"
            p_v.font.name = theme.font_family_header
            p_v.font.size = Pt(10.0)
            p_v.font.bold = True
            p_v.font.color.rgb = theme.get_rgb("primary")

        raw_notes = panel.get("notes") or panel.get("takeaways") or panel.get("analysis")
        if raw_notes:
            note_items = [str(x).strip() for x in raw_notes if str(x).strip()] if isinstance(raw_notes, list) else [str(raw_notes).strip()]
            if note_items:
                notes_top_in = max_bottom_in - notes_h_in
                draw_hairline(slide, Inches(px_in), Inches(notes_top_in - 0.06), Inches(panel_w_in), theme.get_rgb("border"), width_pt=0.75)
                tb_n = slide.shapes.add_textbox(Inches(px_in), Inches(notes_top_in), Inches(panel_w_in), Inches(notes_h_in))
                tf_n = tb_n.text_frame
                tf_n.word_wrap = True
                tf_n.margin_left = tf_n.margin_right = tf_n.margin_top = tf_n.margin_bottom = 0
                is_multi = len(note_items) > 1
                for n_i, item_txt in enumerate(note_items):
                    p_n = tf_n.paragraphs[0] if n_i == 0 else tf_n.add_paragraph()
                    if n_i > 0:
                        p_n.space_before = Pt(4)
                    text_to_render = f"• {item_txt}" if is_multi else item_txt
                    append_formatted_runs(
                        paragraph=p_n,
                        text=text_to_render,
                        font_name=theme.font_family,
                        font_size_pt=10.0,
                        font_color=theme.get_rgb("secondary"),
                    )

    if callout:
        add_takeaway_bar(
            slide,
            theme,
            callout,
            top_y=Inches(6.24),
            left_x=Inches(left_margin_in),
            width=Inches(total_w_in),
            height=Inches(0.46),
        )

    if footnote:
        tb_fn = slide.shapes.add_textbox(Inches(left_margin_in), Inches(6.74), Inches(total_w_in), Inches(0.22))
        tf_fn = tb_fn.text_frame
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = footnote
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.5)
        p_fn.font.color.rgb = theme.get_rgb("muted")

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide



