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
    add_slide_with_background, add_slide_header, add_card, add_slide_footer,
    _interpolate_color, _add_status_pill, _add_bullet_paragraph,
)

logger = logging.getLogger(__name__)

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


class TableColumnDef:
    header: str
    width: float  # In inches
    align: str = "LEFT"  # "LEFT", "CENTER", "RIGHT"
    is_status: bool = False
    is_index: bool = False
    is_highlight: bool = False


def build_table_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "PROJECT GOVERNANCE | STAGE-GATE REGISTER",
    action_title: str = "Structured Governance Register Establishes Accountabilities and Timelines",
    subtitle: Optional[str] = "Detailed tracking matrix with designated owners, baseline targets, and delivery statuses.",
    columns: Optional[List[TableColumnDef]] = None,
    rows: Optional[List[List[Any]]] = None,
    footnote: Optional[str] = None,
    takeaway: Optional[Dict[str, Any]] = None,
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

    # Rows
    num_rows = len(rows)
    avail_row_h = Inches(4.70) if not footnote else Inches(4.45)
    row_gap = Inches(0.0)  # Continuous table rows — zero double-line gap artifact
    if takeaway:
        takeaway_h = Inches(1.45)
        avail_table_h = Inches(2.70) if footnote else Inches(2.85)
        row_h = min(Inches(0.56), max(Inches(0.32), avail_table_h / num_rows))
    else:
        max_h = Inches(0.65) if num_rows <= 5 else Inches(0.50)
        row_h = min(max_h, max(Inches(0.30), avail_row_h / num_rows))

    row_start_y = header_y + header_h

    status_keywords = {
        "COMPLETE", "COMPLETED", "IN PROGRESS", "ON TRACK", "RESCHEDULED", "PLANNED",
        "CRITICAL GATE", "MILESTONE GATE", "HIGH", "MEDIUM", "LOW", "SIGNED-OFF",
        "MUTUAL", "DAILY", "WEEKLY", "AS NEEDED", "OPEN", "RESOLVED"
    }

    font_size_pt = 9.0 if num_rows > 8 else (10.0 if num_rows > 5 else 10.5)

    for r_idx, row in enumerate(rows):
        cur_ry = row_start_y + r_idx * row_h
        is_alt = (r_idx % 2 != 0)

        # Modern Row Hygiene: Borderless rows with subtle alternating fill and hairline bottom divider
        if is_alt:
            row_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, cur_ry, total_w, row_h)
            row_bg.shadow.inherit = False
            row_bg.fill.solid()
            row_bg.fill.fore_color.rgb = theme.get_rgb("surface_muted")
            row_bg.line.fill.background()

        # Faint hairline divider under row (0.5pt)
        row_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, cur_ry + row_h, total_w, Pt(0.5))
        row_div.shadow.inherit = False
        row_div.fill.solid()
        row_div.fill.fore_color.rgb = theme.get_rgb("border")
        row_div.line.fill.background()

        cur_cx = start_x
        for c_idx, col in enumerate(columns):
            cw = scaled_widths[c_idx]
            is_highlighted = getattr(col, "is_highlight", False)
            if is_highlighted:
                cell_card = slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE,
                    cur_cx,
                    cur_ry,
                    cw,
                    row_h,
                )
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
                )
            else:
                is_idx_col = col.is_index or (c_idx == 0 and cell_str.isdigit())
                tb = slide.shapes.add_textbox(cur_cx + (Inches(0.02) if is_idx_col else Inches(0.08)), cur_ry + Inches(0.02), cw - (Inches(0.04) if is_idx_col else Inches(0.16)), row_h - Inches(0.04))
                tf = tb.text_frame
                tf.word_wrap = True
                tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf.margin_left = Pt(1) if is_idx_col else Pt(6)
                tf.margin_right = Pt(1) if is_idx_col else Pt(6)
                tf.margin_top = Pt(2)
                tf.margin_bottom = Pt(2)
                p = tf.paragraphs[0]
                p.text = cell_str
                if col.align == "CENTER":
                    p.alignment = PP_ALIGN.CENTER
                elif col.align == "RIGHT":
                    p.alignment = PP_ALIGN.RIGHT
                else:
                    p.alignment = PP_ALIGN.LEFT

                is_highlighted = getattr(col, "is_highlight", False)
                dim_idx = 1 if (columns and columns[0].is_index) else 0

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
                    p.font.color.rgb = theme.get_rgb("secondary")

            cur_cx += cw

    if takeaway and isinstance(takeaway, dict):
        takeaway_top = row_start_y + num_rows * row_h + Inches(0.14)
        takeaway_h = Inches(1.45)
        acc_key = takeaway.get("accent_key", "accent")
        acc_rgb = theme.get_rgb(acc_key)

        # Modern Executive Takeaway Card: Clean surface with left indicator accent bar
        add_card(
            slide,
            theme,
            start_x,
            takeaway_top,
            total_w,
            takeaway_h,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            border_width_pt=1.0,
            force_rectangle=True,
        )
        # Vertical focus accent stripe on left (4.5pt width)
        left_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, takeaway_top, Pt(4.5), takeaway_h)
        left_stripe.shadow.inherit = False
        left_stripe.fill.solid()
        left_stripe.fill.fore_color.rgb = acc_rgb
        left_stripe.line.fill.background()

        badge_txt = takeaway.get("badge", "STRATEGIC TAKEAWAY")
        pill_w = Inches(2.40)
        pill_h = Inches(0.26)
        _add_status_pill(
            slide=slide,
            theme=theme,
            left=start_x + Inches(0.20),
            top=takeaway_top + Inches(0.12),
            width=pill_w,
            height=pill_h,
            status=badge_txt,
            font_size_pt=8.5,
            override_color_key=acc_key,
        )

        tb_tk = slide.shapes.add_textbox(start_x + Inches(0.20), takeaway_top + Inches(0.44), total_w - Inches(0.40), takeaway_h - Inches(0.50))
        tf_tk = tb_tk.text_frame
        tf_tk.word_wrap = True
        tf_tk.margin_left = tf_tk.margin_right = tf_tk.margin_top = tf_tk.margin_bottom = 0

        p_tkt = tf_tk.paragraphs[0]
        p_tkt.text = takeaway.get("title", "")
        p_tkt.font.name = theme.font_family_header
        p_tkt.font.size = Pt(13.5)
        p_tkt.font.bold = True
        p_tkt.font.color.rgb = theme.get_rgb("primary")

        if takeaway.get("description"):
            p_tkd = tf_tk.add_paragraph()
            p_tkd.text = takeaway.get("description")
            p_tkd.font.name = theme.font_family
            p_tkd.font.size = Pt(11.5)
            p_tkd.font.color.rgb = theme.get_rgb("secondary")
            p_tkd.space_before = Pt(5)

    elif takeaway and isinstance(takeaway, str):
        take_y = Inches(6.12) if footnote else Inches(6.32)
        take_h = Inches(0.48)
        tb_take = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, start_x, take_y, total_w, take_h)
        tb_take.fill.solid()
        tb_take.fill.fore_color.rgb = RGBColor(241, 245, 249)
        tb_take.line.color.rgb = RGBColor(203, 213, 225)
        tb_take.line.width = Pt(0.75)
        strip_shape_shadows(tb_take)
        tf_take = tb_take.text_frame
        tf_take.word_wrap = True
        tf_take.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_take.margin_left = tf_take.margin_right = Inches(0.15)
        pt = tf_take.paragraphs[0]
        pt.text = str(takeaway)
        pt.font.name = theme.font_family_header
        pt.font.size = Pt(8.5)
        pt.font.bold = True
        pt.font.color.rgb = RGBColor(30, 41, 59)

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

