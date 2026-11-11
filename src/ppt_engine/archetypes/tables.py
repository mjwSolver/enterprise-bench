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
    _interpolate_color, _add_status_pill, _add_bullet_paragraph,
)

logger = logging.getLogger(__name__)

@dataclass
class FeatureScorecardRow:
    """Represents an evaluation criterion row in a comparison matrix."""
    category: str
    criteria: str
    scores: Dict[str, str]           # platform -> "FULL", "HALF", "EMPTY", "N/A" or glyphs "●", "◐", "○"
    business_impact: str = "HIGH"

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

    # 2. Unified Header Frame
    header_bottom = add_slide_header(slide, theme, tracker=tracker, title=action_title, subtitle=subtitle)

    # 3. Canvas Table Layout Bounds (Dynamic below header + reclaims space if footnote omitted)
    table_left = Inches(0.80)
    table_top = resolve_content_top(header_bottom, gap_in=0.20)
    table_w = Inches(11.733)
    hdr_h = Inches(0.42)
    bottom_limit = Inches(6.24 if data.footnote else 6.86)
    n_rows = max(1, len(data.rows))
    row_gap = Inches(0.06)
    avail_rows_h = max(Inches(2.50), bottom_limit - table_top - hdr_h - row_gap)
    row_h = min(Inches(0.82), max(Inches(0.42), (avail_rows_h - (row_gap * max(0, n_rows - 1))) / n_rows))

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
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        p.text = text
        p.font.name = theme.font_family_header
        p.font.size = Pt(9.0)
        p.font.bold = True
        p.font.color.rgb = RGBColor(147, 197, 253) if is_rec else RGBColor(255, 255, 255)

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
        tb_cat = slide.shapes.add_textbox(table_left + Inches(0.12), cur_y + Inches(0.10), cat_w - Inches(0.18), row_h - Inches(0.20))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_c = tf_cat.paragraphs[0]
        p_c.text = row.category
        p_c.font.name = theme.font_family_header
        p_c.font.size = Pt(10.0)
        p_c.font.bold = True
        p_c.font.color.rgb = theme.get_rgb("primary")

        # Criteria cell
        tb_crit = slide.shapes.add_textbox(table_left + cat_w + Inches(0.10), cur_y + Inches(0.10), crit_w - Inches(0.20), row_h - Inches(0.20))
        tf_crit = tb_crit.text_frame
        tf_crit.word_wrap = True
        tf_crit.vertical_anchor = MSO_ANCHOR.MIDDLE
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
            if is_rec:
                col_hl = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px + Inches(0.04), cur_y + Inches(0.04), plat_w - Inches(0.08), row_h - Inches(0.08))
                col_hl.fill.solid()
                col_hl.fill.fore_color.rgb = RGBColor(241, 245, 249)
                col_hl.line.fill.background()

            tb_sc = slide.shapes.add_textbox(px, cur_y + Inches(0.08), plat_w, row_h - Inches(0.16))
            tf_sc = tb_sc.text_frame
            tf_sc.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_s = tf_sc.paragraphs[0]
            p_s.alignment = PP_ALIGN.CENTER
            p_s.text = glyph
            p_s.font.name = theme.font_family_header
            p_s.font.size = Pt(16.0 if glyph in ("●", "◐", "○") else 10.5)
            p_s.font.bold = True
            if glyph == "●":
                p_s.font.color.rgb = RGBColor(16, 185, 129) if is_rec else theme.get_rgb("primary")
            elif glyph == "◐":
                p_s.font.color.rgb = RGBColor(245, 158, 11)  # Amber
            elif glyph == "○":
                p_s.font.color.rgb = RGBColor(148, 163, 184)  # Slate-400
            else:
                p_s.font.color.rgb = theme.get_rgb("primary")

        # Impact Badge (Scaled cleanly to 10.0pt to match spacious cells)
        tb_imp = slide.shapes.add_textbox(table_left + cat_w + crit_w + len(platforms) * plat_w, cur_y + Inches(0.08), impact_w, row_h - Inches(0.16))
        tf_imp = tb_imp.text_frame
        tf_imp.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_im = tf_imp.paragraphs[0]
        p_im.alignment = PP_ALIGN.CENTER
        p_im.text = row.business_impact.upper()
        p_im.font.name = theme.font_family_header
        p_im.font.size = Pt(10.0)
        p_im.font.bold = True
        if row.business_impact.upper() in ("CRITICAL", "HIGH"):
            p_im.font.color.rgb = RGBColor(220, 38, 38)
        else:
            p_im.font.color.rgb = theme.get_rgb("accent")

        cur_y += row_h + Inches(0.06)

    # 5. Strictly Opt-In Footnote / Legend
    if data.footnote and str(data.footnote).strip():
        foot_y = cur_y + Inches(0.12)
        tb_fn = slide.shapes.add_textbox(table_left, foot_y, table_w, Inches(0.30))
        tf_fn = tb_fn.text_frame
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = str(data.footnote).strip()
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
            row_bg.shadow.inherit = False
            row_bg.fill.solid()
            row_bg.fill.fore_color.rgb = theme.get_rgb("surface_muted")
            row_bg.line.fill.background()

        row_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, cur_ry + row_h, total_w, Pt(0.5))
        row_div.shadow.inherit = False
        row_div.fill.solid()
        row_div.fill.fore_color.rgb = theme.get_rgb("border")
        row_div.line.fill.background()

    cur_cx = start_x
    dim_idx = 1 if (columns and columns[0].is_index) else 0
    for c_idx, col in enumerate(columns):
        cw = scaled_widths[c_idx]
        is_highlighted = getattr(col, "is_highlight", False)
        if is_highlighted and not is_detached:
            cell_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cur_cx, cur_ry, cw, row_h)
            cell_card.shadow.inherit = False
            cell_card.fill.solid()
            cell_card.fill.fore_color.rgb = RGBColor(238, 246, 255)
            cell_card.line.fill.background()

        cell_val = row[c_idx] if c_idx < len(row) else ""
        cell_str = str(cell_val).strip()
        is_status_col = col.is_status or (cell_str.upper() in status_keywords and len(cell_str) <= 20)

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
                override_color_key="accent" if is_detached else None,
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
    hdr_card.shadow.inherit = False
    hdr_card.fill.solid()
    hdr_card.fill.fore_color.rgb = theme.get_rgb("surface_muted")
    hdr_card.line.fill.background()

    # Clean hairline divider under header row
    hdr_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, header_y + header_h, total_w, Pt(1.0))
    hdr_div.shadow.inherit = False
    hdr_div.fill.solid()
    hdr_div.fill.fore_color.rgb = theme.get_rgb("border")
    hdr_div.line.fill.background()

    cur_x = start_x
    for c_idx, col in enumerate(columns):
        cw = scaled_widths[c_idx]
        is_highlighted = getattr(col, "is_highlight", False)
        if is_highlighted:
            hdr_hl = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cur_x, header_y, cw, header_h)
            hdr_hl.shadow.inherit = False
            hdr_hl.fill.solid()
            hdr_hl.fill.fore_color.rgb = hex_to_rgb("#1E3A8A")
            hdr_hl.line.fill.background()

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

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide

