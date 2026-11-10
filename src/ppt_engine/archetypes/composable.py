from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from src.ppt_engine.icon_engine import (
    get_brand_icon,
    normalize_color,
    recolor_svg,
    render_svg_to_png,
)
from src.ppt_engine.text_formatting import append_formatted_runs, set_formatted_text
from src.ppt_engine.theme_engine import Theme, hex_to_rgb, rgb_to_hex, strip_shape_shadows

from .common import (
    add_slide_with_background,
    add_slide_header,
    add_card,
    add_card_with_top_stripe,
    add_card_with_harmonized_icon,
    add_slide_footer,
    add_takeaway_bar,
    _fit_image_in_box,
)
from .grids import CardGridItem

logger = logging.getLogger(__name__)


def to_emu(val: Union[int, float, Emu]) -> Emu:
    """Guarantees strictly integral EMU length to prevent XML float serialization errors."""
    return Emu(int(round(val)))


# =============================================================================
# Layout Calculations & Geometry
# =============================================================================

def parse_split_fractions(split: Optional[Union[List[Union[int, float]], str]], num_panes: int) -> List[float]:
    """
    Parses split configuration into normalized fractions that sum to 1.0.
    
    Supports:
      - List of percentages: [35, 65] -> [0.35, 0.65]
      - List of fractions: [0.35, 0.65] -> [0.35, 0.65]
      - 3-column splits: [25, 50, 25] -> [0.25, 0.50, 0.25]
      - Colon / slash strings: "35:65", "1:2:1"
      - None / empty: defaults to equal distribution [1/N, ..., 1/N]
    """
    if num_panes <= 0:
        return []

    if split is None:
        return [1.0 / num_panes] * num_panes

    raw_vals: List[float] = []
    if isinstance(split, str):
        parts = re.split(r"[:/, \t]+", split.strip())
        for p in parts:
            if p:
                try:
                    raw_vals.append(float(p))
                except ValueError:
                    pass
    elif isinstance(split, (list, tuple)):
        for v in split:
            try:
                raw_vals.append(float(v))
            except (ValueError, TypeError):
                pass

    if len(raw_vals) != num_panes or sum(raw_vals) <= 0:
        return [1.0 / num_panes] * num_panes

    total = sum(raw_vals)
    return [v / total for v in raw_vals]


def compute_pane_bounding_boxes(
    content_left: Inches,
    content_top: Inches,
    content_width: Inches,
    content_height: Inches,
    fractions: List[float],
    gap: Inches,
) -> List[Tuple[Inches, Inches, Inches, Inches]]:
    """
    Divides available canvas area into collision-free bounding boxes (left, top, width, height)
    spaced by `gap`.
    """
    n = len(fractions)
    if n == 0:
        return []
    if n == 1:
        return [(content_left, content_top, content_width, content_height)]

    total_gap = gap * (n - 1)
    avail_width = content_width - total_gap
    if avail_width < Inches(1.0):
        avail_width = content_width  # Fallback guard against overflow

    boxes: List[Tuple[Inches, Inches, Inches, Inches]] = []
    curr_x = content_left

    for i, frac in enumerate(fractions):
        w = Emu(int(round(avail_width * frac)))
        boxes.append((curr_x, content_top, w, content_height))
        curr_x = Emu(int(round(curr_x + w + gap)))

    return boxes


# =============================================================================
# Regional Pane Widget Renderers
# =============================================================================

def render_hero_kpi_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders an executive Hero KPI block in the assigned bounding box.
    Supports filled dark-card style (like split_hero left anchor) or surface card style.
    """
    bx, by, bw, bh = box
    style = str(cfg.get("card_style", "filled")).lower().strip()
    stat = str(cfg.get("stat", cfg.get("hero_stat", "99.4%"))).strip()
    stat_label = str(cfg.get("stat_label", cfg.get("label", "Primary Performance Metric"))).strip()
    stat_subtext = cfg.get("stat_subtext", cfg.get("subtext", cfg.get("description")))
    eyebrow = str(cfg.get("eyebrow", cfg.get("tracker", "KEY PERFORMANCE METRIC"))).strip().upper()
    accent_key = cfg.get("accent_key", "accent")

    is_filled = style in ("filled", "primary", "dark")
    bg_rgb = theme.get_rgb("primary") if is_filled else theme.get_rgb("surface")
    border_rgb = theme.get_rgb("primary") if is_filled else theme.get_rgb("border")

    # 1. Base Container Card
    add_card(
        slide,
        theme,
        bx,
        by,
        bw,
        bh,
        bg_color=bg_rgb,
        border_color=border_rgb,
        force_rectangle=True,
    )

    # If surface card, add top accent stripe
    if not is_filled:
        st_h = Pt(4.0)
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, by, bw, st_h)
        stripe.shadow.inherit = False
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = theme.get_rgb(accent_key)
        stripe.line.fill.background()

    pad_x = Inches(0.28)
    pad_y = Inches(0.24) if not is_filled else Inches(0.30)
    inner_w = to_emu(bw - (pad_x * 2))

    # 2. Eyebrow Tag (Full inner width, zero floating badge pills)
    tb_eye = slide.shapes.add_textbox(to_emu(bx + pad_x), to_emu(by + pad_y), inner_w, Inches(0.30))
    tf_eye = tb_eye.text_frame
    tf_eye.word_wrap = True
    tf_eye.margin_left = tf_eye.margin_right = tf_eye.margin_top = tf_eye.margin_bottom = 0
    p_eye = tf_eye.paragraphs[0]
    p_eye.text = eyebrow
    p_eye.font.name = theme.font_family_header
    p_eye.font.size = Pt(9.5)
    p_eye.font.bold = True
    p_eye.font.color.rgb = theme.get_rgb("accent") if is_filled else theme.get_rgb("muted_text")

    # 3. Huge Stat Callout
    stat_top = to_emu(by + pad_y + Inches(0.32))
    tb_stat = slide.shapes.add_textbox(to_emu(bx + pad_x), stat_top, inner_w, Inches(0.85))
    tf_stat = tb_stat.text_frame
    tf_stat.word_wrap = True
    tf_stat.margin_left = tf_stat.margin_right = tf_stat.margin_top = tf_stat.margin_bottom = 0
    p_stat = tf_stat.paragraphs[0]
    p_stat.text = stat
    p_stat.font.name = theme.font_family_header
    p_stat.font.size = Pt(36.0) if len(stat) <= 7 else Pt(30.0)
    p_stat.font.bold = True
    p_stat.font.color.rgb = RGBColor(255, 255, 255) if is_filled else theme.get_rgb("primary")

    # 4. Metric Label (Allocated 0.55" for 2-line wraps in narrow columns)
    lbl_top = to_emu(stat_top + Inches(0.82))
    tb_lbl = slide.shapes.add_textbox(to_emu(bx + pad_x), lbl_top, inner_w, Inches(0.55))
    tf_lbl = tb_lbl.text_frame
    tf_lbl.word_wrap = True
    tf_lbl.margin_left = tf_lbl.margin_right = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
    p_lbl = tf_lbl.paragraphs[0]
    p_lbl.text = stat_label
    p_lbl.font.name = theme.font_family_header
    p_lbl.font.size = Pt(12.5)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = hex_to_rgb("#F1F5F9") if is_filled else theme.get_rgb("primary")

    # 5. Native DrawingML Hairline Divider
    div_y = to_emu(lbl_top + Inches(0.60))
    h_div = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        to_emu(bx + pad_x),
        div_y,
        inner_w,
        Pt(0.75),
    )
    h_div.shadow.inherit = False
    h_div.fill.solid()
    h_div.fill.fore_color.rgb = hex_to_rgb("#334155") if is_filled else theme.get_rgb("border")
    h_div.line.fill.background()

    # 6. Subtext / Narrative Frame
    if stat_subtext:
        sub_top = to_emu(div_y + Inches(0.14))
        sub_h = to_emu(bh - (sub_top - by) - Inches(0.20))
        if sub_h > Inches(0.40):
            tb_sub = slide.shapes.add_textbox(to_emu(bx + pad_x), sub_top, inner_w, sub_h)
            tf_sub = tb_sub.text_frame
            tf_sub.word_wrap = True
            tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = ""
            append_formatted_runs(
                paragraph=p_sub,
                text=str(stat_subtext),
                font_name=theme.font_family,
                font_size_pt=10.0,
                font_color=hex_to_rgb("#CBD5E1") if is_filled else theme.get_rgb("secondary"),
                lead_color=RGBColor(255, 255, 255) if is_filled else theme.get_rgb("primary"),
            )


def render_card_list_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders a vertical list/stack of cards or divided narrative streams inside the bounding box.
    """
    bx, by, bw, bh = box
    raw_items = cfg.get("items", cfg.get("cards", cfg.get("blocks", [])))
    if not raw_items:
        return

    style = str(cfg.get("style", "cards")).lower().strip()
    is_divided = style in ("divided", "streams", "stream", "lines")

    n_items = len(raw_items)
    gap_y = Inches(0.14) if not is_divided else Inches(0)
    avail_h = bh - (gap_y * (n_items - 1)) if not is_divided else bh
    item_h = to_emu(avail_h / n_items)

    for idx, item in enumerate(raw_items):
        item_y = to_emu(by + (idx * (item_h + gap_y))) if not is_divided else to_emu(by + (idx * item_h))
        item_dict = item if isinstance(item, dict) else {"title": str(item)}

        title = str(item_dict.get("title", f"Pillar {idx+1}")).strip()
        desc = item_dict.get("description", item_dict.get("body", ""))
        bullets = item_dict.get("bullets", [])
        accent_key = item_dict.get("accent_key", "accent")

        if not is_divided:
            # Standalone card box
            add_card(
                slide,
                theme,
                bx,
                item_y,
                bw,
                item_h,
                bg_color=theme.get_rgb("surface"),
                border_color=theme.get_rgb("border"),
                force_rectangle=True,
            )
            # Left accent focus stripe
            st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, item_y, Pt(4.0), item_h)
            st.shadow.inherit = False
            st.fill.solid()
            st.fill.fore_color.rgb = theme.get_rgb(accent_key)
            st.line.fill.background()
            pad_left = Inches(0.20)
            pad_top = Inches(0.12)
        else:
            pad_left = Inches(0.04)
            pad_top = Inches(0.08)

        card_content_w = to_emu(bw - pad_left - Inches(0.16))

        # Header: Full-width Title (zero floating badge pills)
        title_h = Inches(0.48)
        tb_title = slide.shapes.add_textbox(to_emu(bx + pad_left), to_emu(item_y + pad_top), card_content_w, title_h)
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_t = tf_title.paragraphs[0]
        p_t.text = title
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(12.0)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")

        # Body: Description or Bullets
        body_y = to_emu(item_y + pad_top + title_h + Inches(0.02))
        body_h = to_emu(item_h - (body_y - item_y) - Inches(0.08))
        if body_h > Inches(0.30):
            tb_body = slide.shapes.add_textbox(to_emu(bx + pad_left), body_y, card_content_w, body_h)
            tf_body = tb_body.text_frame
            tf_body.word_wrap = True
            tf_body.margin_left = tf_body.margin_right = tf_body.margin_top = tf_body.margin_bottom = 0

            if bullets and isinstance(bullets, list):
                bullet_gap = 7.0 if body_h >= Inches(0.95) else 4.5
                for b_idx, b_text in enumerate(bullets[:2]):
                    p_b = tf_body.paragraphs[0] if b_idx == 0 else tf_body.add_paragraph()
                    p_b.space_before = Pt(bullet_gap) if b_idx > 0 else Pt(0)
                    p_b.space_after = Pt(2.0)
                    append_formatted_runs(
                        paragraph=p_b,
                        text=f"•  {b_text}",
                        font_name=theme.font_family,
                        font_size_pt=10.0,
                        font_color=theme.get_rgb("secondary"),
                        lead_color=theme.get_rgb("primary"),
                        auto_colon_lead=True,
                    )
            elif desc:
                p_d = tf_body.paragraphs[0]
                append_formatted_runs(
                    paragraph=p_d,
                    text=str(desc),
                    font_name=theme.font_family,
                    font_size_pt=10.0,
                    font_color=theme.get_rgb("secondary"),
                    lead_color=theme.get_rgb("primary"),
                    auto_colon_lead=True,
                )

        # Hairline divider between stream items (if divided mode)
        if is_divided and idx < n_items - 1:
            div = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                bx,
                item_y + item_h - Inches(0.04),
                bw,
                Pt(0.75),
            )
            div.shadow.inherit = False
            div.fill.solid()
            div.fill.fore_color.rgb = theme.get_rgb("border")
            div.line.fill.background()


def render_table_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders a structured contiguous data table inside the bounding box.
    """
    bx, by, bw, bh = box
    headers = cfg.get("headers", ["Dimension", "Status", "Observation"])
    rows = cfg.get("rows", [])
    if not headers or not rows:
        return

    n_cols = len(headers)
    n_rows = len(rows) + 1  # include header row

    # Table shape
    shape = slide.shapes.add_table(n_rows, n_cols, bx, by, bw, bh)
    table = shape.table

    # Column widths
    col_fractions = parse_split_fractions(cfg.get("column_widths"), n_cols)
    for c_idx, frac in enumerate(col_fractions):
        table.columns[c_idx].width = int(bw * frac)

    # Header Row
    for c_idx, h_text in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = theme.get_rgb("primary")
        tf = cell.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.12)
        tf.margin_right = Inches(0.12)
        tf.margin_top = Inches(0.08)
        tf.margin_bottom = Inches(0.08)
        p = tf.paragraphs[0]
        p.text = str(h_text).upper()
        p.font.name = theme.font_family_header
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    zebra = bool(cfg.get("zebra", True))
    for r_idx, row_data in enumerate(rows, start=1):
        is_even = (r_idx % 2 == 0)
        row_bg = theme.get_rgb("surface_muted") if (zebra and is_even) else theme.get_rgb("surface")

        for c_idx in range(n_cols):
            cell = table.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            tf = cell.text_frame
            tf.word_wrap = True
            tf.margin_left = Inches(0.12)
            tf.margin_right = Inches(0.12)
            tf.margin_top = Inches(0.08)
            tf.margin_bottom = Inches(0.08)
            p = tf.paragraphs[0]
            val = str(row_data[c_idx]) if c_idx < len(row_data) else ""
            p.text = ""
            append_formatted_runs(
                paragraph=p,
                text=val,
                font_name=theme.font_family,
                font_size_pt=9.5,
                font_color=theme.get_rgb("secondary"),
                lead_color=theme.get_rgb("primary"),
                auto_colon_lead=True,
            )


def render_process_steps_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders sequential process steps (vertical stack or horizontal flow) inside the bounding box.
    """
    bx, by, bw, bh = box
    steps = cfg.get("steps", cfg.get("items", []))
    if not steps:
        return

    n_steps = len(steps)
    direction = str(cfg.get("direction", "auto")).lower()
    if direction == "auto":
        direction = "horizontal" if bw >= Inches(5.0) else "vertical"

    if direction == "horizontal":
        step_gap = Inches(0.12)
        avail_w = bw - (step_gap * (n_steps - 1))
        step_w = to_emu(avail_w / n_steps)
        for s_idx, st in enumerate(steps):
            s_dict = st if isinstance(st, dict) else {"title": str(st)}
            sx = to_emu(bx + (s_idx * (step_w + step_gap)))
            accent_key = s_dict.get("accent_key", "accent")

            # Step card container
            add_card(
                slide,
                theme,
                sx,
                by,
                step_w,
                bh,
                bg_color=theme.get_rgb("surface"),
                border_color=theme.get_rgb("border"),
                force_rectangle=True,
            )
            # Top accent stripe
            top_st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx, by, step_w, Pt(3.5))
            top_st.shadow.inherit = False
            top_st.fill.solid()
            top_st.fill.fore_color.rgb = theme.get_rgb(accent_key)
            top_st.line.fill.background()

            # Step number circle / badge
            num_str = str(s_dict.get("step_num", f"{s_idx+1:02d}"))
            tb_num = slide.shapes.add_textbox(to_emu(sx + Inches(0.12)), to_emu(by + Inches(0.10)), to_emu(step_w - Inches(0.24)), Inches(0.25))
            tf_num = tb_num.text_frame
            tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
            p_n = tf_num.paragraphs[0]
            p_n.text = f"STEP {num_str}"
            p_n.font.name = theme.font_family_header
            p_n.font.size = Pt(8.5)
            p_n.font.bold = True
            p_n.font.color.rgb = theme.get_rgb(accent_key)

            # Step Title
            tb_t = slide.shapes.add_textbox(to_emu(sx + Inches(0.12)), to_emu(by + Inches(0.36)), to_emu(step_w - Inches(0.24)), Inches(0.40))
            tf_t = tb_t.text_frame
            tf_t.word_wrap = True
            tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
            p_t = tf_t.paragraphs[0]
            p_t.text = str(s_dict.get("title", ""))
            p_t.font.name = theme.font_family_header
            p_t.font.size = Pt(11.0)
            p_t.font.bold = True
            p_t.font.color.rgb = theme.get_rgb("primary")

            # Step Description
            desc = s_dict.get("description", "")
            if desc:
                tb_d = slide.shapes.add_textbox(to_emu(sx + Inches(0.12)), to_emu(by + Inches(0.80)), to_emu(step_w - Inches(0.24)), to_emu(bh - Inches(0.90)))
                tf_d = tb_d.text_frame
                tf_d.word_wrap = True
                tf_d.margin_left = tf_d.margin_right = tf_d.margin_top = tf_d.margin_bottom = 0
                p_d = tf_d.paragraphs[0]
                append_formatted_runs(
                    paragraph=p_d,
                    text=str(desc),
                    font_name=theme.font_family,
                    font_size_pt=9.5,
                    font_color=theme.get_rgb("secondary"),
                    lead_color=theme.get_rgb("primary"),
                    auto_colon_lead=True,
                )
    else:
        # Vertical steps
        step_gap = Inches(0.10)
        avail_h = bh - (step_gap * (n_steps - 1))
        step_h = to_emu(avail_h / n_steps)
        for s_idx, st in enumerate(steps):
            s_dict = st if isinstance(st, dict) else {"title": str(st)}
            sy = to_emu(by + (s_idx * (step_h + step_gap)))
            accent_key = s_dict.get("accent_key", "accent")

            add_card(
                slide,
                theme,
                bx,
                sy,
                bw,
                step_h,
                bg_color=theme.get_rgb("surface"),
                border_color=theme.get_rgb("border"),
                force_rectangle=True,
            )
            # Left stripe
            left_st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, sy, Pt(3.5), step_h)
            left_st.shadow.inherit = False
            left_st.fill.solid()
            left_st.fill.fore_color.rgb = theme.get_rgb(accent_key)
            left_st.line.fill.background()

            num_str = str(s_dict.get("step_num", f"{s_idx+1:02d}"))
            title_text = str(s_dict.get("title", ""))
            desc = s_dict.get("description", "")

            tb = slide.shapes.add_textbox(to_emu(bx + Inches(0.16)), to_emu(sy + Inches(0.08)), to_emu(bw - Inches(0.28)), to_emu(step_h - Inches(0.16)))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

            p = tf.paragraphs[0]
            p.text = f"{num_str}.  {title_text}"
            p.font.name = theme.font_family_header
            p.font.size = Pt(11.0)
            p.font.bold = True
            p.font.color.rgb = theme.get_rgb("primary")

            if desc:
                p_d = tf.add_paragraph()
                p_d.space_before = Pt(2)
                append_formatted_runs(
                    paragraph=p_d,
                    text=str(desc),
                    font_name=theme.font_family,
                    font_size_pt=9.5,
                    font_color=theme.get_rgb("secondary"),
                    lead_color=theme.get_rgb("primary"),
                    auto_colon_lead=True,
                )


def render_card_grid_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders an N x M grid of capability cards inside the bounding box.
    """
    bx, by, bw, bh = box
    raw_items = cfg.get("items", [])
    if not raw_items:
        return

    columns = int(cfg.get("columns", 2))
    cols = max(1, min(columns, len(raw_items)))
    rows = max(1, (len(raw_items) + cols - 1) // cols)

    gap_x = Inches(0.16)
    gap_y = Inches(0.16)
    card_w = to_emu((bw - (gap_x * (cols - 1))) / cols)
    card_h = to_emu((bh - (gap_y * (rows - 1))) / rows)

    for idx, itm in enumerate(raw_items):
        r = idx // cols
        c = idx % cols
        cx = to_emu(bx + c * (card_w + gap_x))
        cy = to_emu(by + r * (card_h + gap_y))

        if isinstance(itm, dict):
            title = itm.get("title", "")
            subtitle = itm.get("subtitle", "")
            bullets = itm.get("bullets", [])
            accent_key = itm.get("accent_key", "accent")
            badge = itm.get("badge")
            icon = itm.get("icon")
        else:
            title = getattr(itm, "title", str(itm))
            subtitle = getattr(itm, "subtitle", "")
            bullets = getattr(itm, "bullets", [])
            accent_key = getattr(itm, "accent_key", "accent")
            badge = getattr(itm, "badge", None)
            icon = getattr(itm, "icon", None)

        accent_rgb = theme.get_rgb(accent_key)

        add_card_with_top_stripe(
            slide=slide,
            theme=theme,
            left=cx,
            top=cy,
            width=card_w,
            height=card_h,
            accent_rgb=accent_rgb,
            stripe_height_in=0.04,
        )

        pad_x = Inches(0.14)
        pad_y = Inches(0.10)
        tb = slide.shapes.add_textbox(cx + pad_x, cy + pad_y, card_w - (pad_x * 2), card_h - (pad_y * 2))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(11.0)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")

        if subtitle:
            p_sub = tf.add_paragraph()
            p_sub.space_before = Pt(2)
            p_sub.text = subtitle
            p_sub.font.name = theme.font_family
            p_sub.font.size = Pt(9.0)
            p_sub.font.color.rgb = theme.get_rgb("muted_text")

        if bullets:
            for b_idx, b in enumerate(bullets[:2]):
                p_b = tf.add_paragraph()
                p_b.space_before = Pt(5.0 if b_idx > 0 else 4.0)
                p_b.space_after = Pt(2.0)
                append_formatted_runs(
                    paragraph=p_b,
                    text=f"• {b}",
                    font_name=theme.font_family,
                    font_size_pt=9.0,
                    font_color=theme.get_rgb("secondary"),
                    lead_color=theme.get_rgb("primary"),
                    auto_colon_lead=True,
                )


def _resolve_widget_color(theme: Theme, color_spec: Any, default_key: str = "accent") -> RGBColor:
    """Resolves a theme key, semantic alias, or hex code to RGBColor."""
    if not color_spec:
        return theme.get_rgb(default_key)
    raw = str(color_spec).strip()
    if raw.startswith("#"):
        return hex_to_rgb(raw)
    semantic_hex = {
        "blue": "#0284C7",
        "emerald": "#10B981",
        "green": "#16A34A",
        "amber": "#D97706",
        "warning": "#D97706",
        "red": "#DC2626",
        "danger": "#DC2626",
        "slate": "#64748B",
        "muted": "#94A3B8",
    }
    if raw.lower() in semantic_hex and not (hasattr(theme, "palette") and raw in theme.palette):
        return hex_to_rgb(semantic_hex[raw.lower()])
    return theme.get_rgb(raw)


def render_native_chart_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders a native Excel-backed PowerPoint chart (BAR_CLUSTERED or COLUMN_CLUSTERED)
    inside a clean surface card container.
    """
    bx, by, bw, bh = box
    title = str(cfg.get("title", "")).strip()
    subtitle = str(cfg.get("subtitle", "")).strip()
    footnote = str(cfg.get("footnote", "")).strip()

    add_card(
        slide,
        theme,
        bx,
        by,
        bw,
        bh,
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("border"),
        force_rectangle=True,
    )

    pad_x = Inches(0.20)
    curr_y = by + Inches(0.14)

    if title:
        hdr_h = Inches(0.46) if subtitle else Inches(0.28)
        tb = slide.shapes.add_textbox(to_emu(bx + pad_x), to_emu(curr_y), to_emu(bw - pad_x * 2), to_emu(hdr_h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = theme.font_family_header
        p.font.size = Pt(12.0)
        p.font.bold = True
        p.font.color.rgb = theme.get_rgb("primary")
        if subtitle:
            p_sub = tf.add_paragraph()
            p_sub.space_before = Pt(2)
            p_sub.text = subtitle
            p_sub.font.name = theme.font_family
            p_sub.font.size = Pt(9.0)
            p_sub.font.color.rgb = theme.get_rgb("muted_text")
        curr_y = curr_y + hdr_h + Inches(0.06)

    foot_h = Inches(0.24) if footnote else Inches(0.08)
    chart_h = to_emu(by + bh - foot_h - curr_y)
    chart_w = to_emu(bw - Inches(0.24))
    chart_x = to_emu(bx + Inches(0.12))

    categories = [str(c) for c in cfg.get("categories", [])]
    if not categories:
        return

    chart_data = CategoryChartData()
    chart_data.categories = categories

    raw_series = cfg.get("series")
    if isinstance(raw_series, list) and raw_series and isinstance(raw_series[0], dict):
        series_defs = raw_series
    else:
        vals = cfg.get("values", raw_series or [])
        series_defs = [{"name": cfg.get("series_name", "Value"), "values": vals, "color": cfg.get("color", "accent")}]

    for s_def in series_defs:
        chart_data.add_series(str(s_def.get("name", "Series")), [float(v) for v in s_def.get("values", [])])

    ctype_str = str(cfg.get("chart_type", "bar")).lower().strip()
    xl_type = XL_CHART_TYPE.COLUMN_CLUSTERED if ctype_str in ("column", "col", "vertical") else XL_CHART_TYPE.BAR_CLUSTERED

    graphic_frame = slide.shapes.add_chart(xl_type, chart_x, to_emu(curr_y), chart_w, chart_h, chart_data)
    chart = graphic_frame.chart
    chart.has_title = False
    chart.has_legend = bool(cfg.get("show_legend", len(series_defs) > 1))
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False
        chart.legend.font.name = theme.font_family
        chart.legend.font.size = Pt(8.5)

    # Category axis formatting
    cat_axis = chart.category_axis
    cat_axis.has_major_gridlines = False
    cat_axis.tick_labels.font.name = theme.font_family
    cat_axis.tick_labels.font.size = Pt(9.5)
    cat_axis.tick_labels.font.bold = True
    cat_axis.tick_labels.font.color.rgb = theme.get_rgb("primary")
    if xl_type == XL_CHART_TYPE.BAR_CLUSTERED and cfg.get("reverse_categories", True):
        cat_axis.reverse_order = True

    # Value axis formatting
    val_axis = chart.value_axis
    val_axis.has_major_gridlines = bool(cfg.get("show_gridlines", False))
    val_axis.visible = bool(cfg.get("show_value_axis", False))
    if cfg.get("min_scale") is not None:
        val_axis.minimum_scale = float(cfg["min_scale"])
    if cfg.get("max_scale") is not None:
        val_axis.maximum_scale = float(cfg["max_scale"])
    if cfg.get("number_format"):
        val_axis.tick_labels.number_format = str(cfg["number_format"])

    # Series colors and direct data labels
    plot = chart.plots[0]
    plot.gap_width = int(cfg.get("gap_width", 75))
    show_labels = bool(cfg.get("show_data_labels", True))
    plot.has_data_labels = show_labels
    if show_labels:
        dlabels = plot.data_labels
        dlabels.position = XL_LABEL_POSITION.OUTSIDE_END
        dlabels.font.name = theme.font_family_header
        dlabels.font.size = Pt(9.5)
        dlabels.font.bold = True
        dlabels.font.color.rgb = theme.get_rgb("primary")
        if cfg.get("number_format"):
            dlabels.number_format = str(cfg["number_format"])

    for s_idx, s_def in enumerate(series_defs):
        if s_idx >= len(plot.series):
            break
        ser = plot.series[s_idx]
        default_col = _resolve_widget_color(theme, s_def.get("color", cfg.get("color", "accent")))
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = default_col
        ser.format.line.fill.background()

        pt_colors = s_def.get("point_colors") or cfg.get("point_colors")
        if isinstance(pt_colors, list):
            for p_idx, p_col in enumerate(pt_colors):
                if p_idx < len(ser.points) and p_col:
                    pt = ser.points[p_idx]
                    pt.format.fill.solid()
                    pt.format.fill.fore_color.rgb = _resolve_widget_color(theme, p_col)

    if footnote:
        tb_f = slide.shapes.add_textbox(
            to_emu(bx + pad_x),
            to_emu(by + bh - Inches(0.24)),
            to_emu(bw - pad_x * 2),
            Inches(0.20),
        )
        tf_f = tb_f.text_frame
        tf_f.word_wrap = True
        tf_f.margin_left = tf_f.margin_right = tf_f.margin_top = tf_f.margin_bottom = 0
        pf = tf_f.paragraphs[0]
        pf.text = footnote
        pf.font.name = theme.font_family
        pf.font.size = Pt(8.0)
        pf.font.color.rgb = theme.get_rgb("muted_text")


def render_code_block_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders a clean technical code/SQL panel with optional observed key-value output metrics below.
    """
    bx, by, bw, bh = box
    title = str(cfg.get("title", "SAMPLE SQL & VERIFIED OUTPUT")).strip()
    sql_text = str(cfg.get("sql", cfg.get("code", ""))).strip()
    results = cfg.get("results", [])
    top_metrics = cfg.get("top_metrics", [])

    # Outer container card
    add_card(
        slide,
        theme,
        bx,
        by,
        bw,
        bh,
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("border"),
        force_rectangle=True,
    )

    # Top dark header bar inside panel
    hdr_h = Inches(0.36)
    hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, by, bw, hdr_h)
    hdr.shadow.inherit = False
    hdr.fill.solid()
    hdr.fill.fore_color.rgb = theme.get_rgb("primary")
    hdr.line.fill.background()
    strip_shape_shadows(hdr)

    tb_hdr = slide.shapes.add_textbox(to_emu(bx + Inches(0.14)), to_emu(by + Inches(0.06)), to_emu(bw - Inches(0.28)), Inches(0.24))
    tf_h = tb_hdr.text_frame
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0
    ph = tf_h.paragraphs[0]
    ph.text = title.upper()
    ph.font.name = theme.font_family_header
    ph.font.size = Pt(9.0)
    ph.font.bold = True
    ph.font.color.rgb = RGBColor(255, 255, 255)

    # Optional compact horizontal KPI callouts above the code well (hairline dividers, no nested borders)
    curr_y = by + hdr_h + Inches(0.08)
    if top_metrics and isinstance(top_metrics, list):
        n_m = len(top_metrics)
        met_h = Inches(0.60)
        slot_w = to_emu((bw - Inches(0.24)) / n_m)
        for m_idx, m_item in enumerate(top_metrics):
            mx = to_emu(bx + Inches(0.12) + m_idx * slot_w)
            col_rgb = _resolve_widget_color(theme, m_item.get("color", m_item.get("accent_key", "accent")))
            if m_idx > 0:
                v_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, mx, to_emu(curr_y + Inches(0.06)), Pt(0.75), to_emu(met_h - Inches(0.14)))
                v_div.shadow.inherit = False
                v_div.fill.solid()
                v_div.fill.fore_color.rgb = theme.get_rgb("border")
                v_div.line.fill.background()
                strip_shape_shadows(v_div)

            tb_m = slide.shapes.add_textbox(to_emu(mx + Inches(0.08)), to_emu(curr_y + Inches(0.02)), to_emu(slot_w - Inches(0.16)), to_emu(met_h - Inches(0.06)))
            tf_m = tb_m.text_frame
            tf_m.word_wrap = True
            tf_m.margin_left = tf_m.margin_right = tf_m.margin_top = tf_m.margin_bottom = 0
            pm1 = tf_m.paragraphs[0]
            pm1.text = str(m_item.get("stat", ""))
            pm1.font.name = theme.font_family_header
            pm1.font.size = Pt(16.0)
            pm1.font.bold = True
            pm1.font.color.rgb = col_rgb

            pm2 = tf_m.add_paragraph()
            pm2.space_before = Pt(1)
            pm2.text = str(m_item.get("label", "")).upper()
            pm2.font.name = theme.font_family_header
            pm2.font.size = Pt(7.5)
            pm2.font.bold = True
            pm2.font.color.rgb = theme.get_rgb("muted_text")

        # Bottom hairline separator before code well
        h_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, to_emu(bx + Inches(0.12)), to_emu(curr_y + met_h), to_emu(bw - Inches(0.24)), Pt(0.75))
        h_div.shadow.inherit = False
        h_div.fill.solid()
        h_div.fill.fore_color.rgb = theme.get_rgb("border")
        h_div.line.fill.background()
        strip_shape_shadows(h_div)
        curr_y += met_h + Inches(0.08)

    # Reserve bottom section if results list is provided
    n_res = len(results) if isinstance(results, list) else 0
    res_h = Inches(0.28 + n_res * 0.28) if n_res > 0 else Inches(0.08)
    sql_top = to_emu(curr_y)
    sql_h = to_emu(by + bh - curr_y - res_h - Inches(0.08))

    # Code well background
    code_well = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        to_emu(bx + Inches(0.12)),
        sql_top,
        to_emu(bw - Inches(0.24)),
        max(Inches(0.60), sql_h),
    )
    code_well.shadow.inherit = False
    code_well.fill.solid()
    code_well.fill.fore_color.rgb = hex_to_rgb("#F8FAFC")
    code_well.line.color.rgb = theme.get_rgb("border")
    code_well.line.width = Pt(0.75)
    strip_shape_shadows(code_well)

    tb_sql = slide.shapes.add_textbox(
        to_emu(bx + Inches(0.20)),
        to_emu(sql_top + Inches(0.08)),
        to_emu(bw - Inches(0.40)),
        max(Inches(0.45), sql_h - Inches(0.16)),
    )
    tf_sql = tb_sql.text_frame
    tf_sql.word_wrap = True
    tf_sql.margin_left = tf_sql.margin_right = tf_sql.margin_top = tf_sql.margin_bottom = 0
    font_mono = str(cfg.get("code_font", "Menlo"))
    code_pt = float(cfg.get("code_size_pt", 8.0))
    code_ls = float(cfg.get("code_line_spacing", 1.05))
    lines = sql_text.splitlines() if sql_text else ["-- SQL query"]
    for l_idx, line in enumerate(lines):
        p_l = tf_sql.paragraphs[0] if l_idx == 0 else tf_sql.add_paragraph()
        p_l.text = line
        p_l.line_spacing = code_ls
        p_l.font.name = font_mono
        p_l.font.size = Pt(code_pt)
        p_l.font.color.rgb = hex_to_rgb("#1E293B")

    # Observed numbers strip at bottom
    if n_res > 0:
        res_y = to_emu(by + bh - res_h)
        res_lbl = str(cfg.get("results_title", "OBSERVED SQL NUMBERS")).upper()
        tb_rt = slide.shapes.add_textbox(to_emu(bx + Inches(0.14)), to_emu(res_y + Inches(0.02)), to_emu(bw - Inches(0.28)), Inches(0.20))
        tf_rt = tb_rt.text_frame
        tf_rt.margin_left = tf_rt.margin_right = tf_rt.margin_top = tf_rt.margin_bottom = 0
        prt = tf_rt.paragraphs[0]
        prt.text = res_lbl
        prt.font.name = theme.font_family_header
        prt.font.size = Pt(8.0)
        prt.font.bold = True
        prt.font.color.rgb = theme.get_rgb("muted_text")

        for r_idx, r_item in enumerate(results):
            row_y = to_emu(res_y + Inches(0.22 + r_idx * 0.27))
            lbl = str(r_item.get("label", "")) if isinstance(r_item, dict) else str(r_item)
            val = str(r_item.get("value", "")) if isinstance(r_item, dict) else ""

            tb_row = slide.shapes.add_textbox(to_emu(bx + Inches(0.14)), row_y, to_emu(bw - Inches(0.28)), Inches(0.24))
            tf_r = tb_row.text_frame
            tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0
            tf_r.word_wrap = True
            pr = tf_r.paragraphs[0]
            r1 = pr.add_run()
            r1.text = f"{lbl}:  "
            r1.font.name = theme.font_family
            r1.font.size = Pt(9.0)
            r1.font.color.rgb = theme.get_rgb("secondary")

            r2 = pr.add_run()
            r2.text = val
            r2.font.name = theme.font_family_header
            r2.font.size = Pt(9.5)
            r2.font.bold = True
            r2.font.color.rgb = theme.get_rgb(str(r_item.get("color", "primary"))) if isinstance(r_item, dict) else theme.get_rgb("primary")


def render_image_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders a static deterministic image (PNG/SVG rendered to PNG) fitted cleanly inside a card frame,
    optionally reserving space below the image card for a borderless floating bullet textbox.
    """
    bx, by, bw, bh = box
    img_ref = cfg.get("image_path") or cfg.get("path")
    if not img_ref:
        return
    p_img = Path(str(img_ref))
    if not p_img.exists():
        logger.warning(f"Image widget path not found: {p_img}")
        return

    show_card = bool(cfg.get("show_card", True))
    title = str(cfg.get("title", "")).strip()
    bullets = cfg.get("bullets") or cfg.get("caption_bullets") or []
    if not isinstance(bullets, list):
        bullets = []
    enclose_caption = bool(cfg.get("enclose_caption", False))

    caption_gap = Inches(0.10) if bullets else Inches(0)
    caption_h = Inches(float(cfg.get("caption_height", 0.88))) if bullets else Inches(0)
    bottom_pad = Inches(0.10) if (bullets and enclose_caption) else Inches(0)
    img_box_h = to_emu(bh - caption_gap - caption_h - bottom_pad) if bullets else bh
    card_h = bh if (enclose_caption or not bullets) else img_box_h

    if show_card:
        add_card(
            slide,
            theme,
            bx,
            by,
            bw,
            card_h,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            force_rectangle=True,
        )

    pad = Inches(0.10 if bullets else 0.12)
    curr_y = by + (Inches(0.14) if title else pad)
    if title:
        pad_x = Inches(0.20)
        tb = slide.shapes.add_textbox(to_emu(bx + pad_x), to_emu(curr_y), to_emu(bw - pad_x * 2), Inches(0.30))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = theme.font_family_header
        p.font.size = Pt(12.0)
        p.font.bold = True
        p.font.color.rgb = theme.get_rgb("primary")
        curr_y += Inches(0.32)

    avail_h = to_emu(by + img_box_h - pad - curr_y)
    avail_w = to_emu(bw - pad * 2)
    il, it, iw, ih = _fit_image_in_box(p_img, to_emu(bx + pad), to_emu(curr_y), avail_w, avail_h)
    slide.shapes.add_picture(str(p_img), il, it, width=iw, height=ih)

    if bullets:
        cap_y = to_emu(by + img_box_h + caption_gap)
        cap_pad_x = Inches(0.22) if enclose_caption else Inches(0.04)
        if enclose_caption:
            # Subtle hairline divider inside outer card separating chart from floating bullets
            div_w = to_emu(bw - cap_pad_x * 2)
            div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, to_emu(bx + cap_pad_x), to_emu(by + img_box_h + Inches(0.02)), div_w, Pt(0.75))
            div.shadow.inherit = False
            div.fill.solid()
            div.fill.fore_color.rgb = theme.get_rgb("border")
            div.line.fill.background()
        tb_cap = slide.shapes.add_textbox(to_emu(bx + cap_pad_x), cap_y, to_emu(bw - cap_pad_x * 2), to_emu(caption_h))
        tf_cap = tb_cap.text_frame
        tf_cap.word_wrap = True
        tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_top = tf_cap.margin_bottom = 0
        bullet_gap = float(cfg.get("bullet_gap_pt", 9.0))
        space_after = float(cfg.get("space_after_pt", 2.0))
        for b_idx, b_text in enumerate(bullets):
            p_b = tf_cap.paragraphs[0] if b_idx == 0 else tf_cap.add_paragraph()
            p_b.space_before = Pt(bullet_gap) if b_idx > 0 else Pt(0)
            p_b.space_after = Pt(space_after)
            append_formatted_runs(
                paragraph=p_b,
                text=f"•  {b_text}",
                font_name=theme.font_family,
                font_size_pt=float(cfg.get("caption_font_size", 9.8)),
                font_color=theme.get_rgb("secondary"),
                lead_color=theme.get_rgb("primary"),
                auto_colon_lead=True,
            )


WIDGET_DISPATCHERS = {
    "hero_kpi": render_hero_kpi_widget,
    "hero_stat": render_hero_kpi_widget,
    "kpi": render_hero_kpi_widget,
    "kpi_block": render_hero_kpi_widget,
    "card_list": render_card_list_widget,
    "cards": render_card_list_widget,
    "card_stack": render_card_list_widget,
    "narrative_streams": render_card_list_widget,
    "table": render_table_widget,
    "data_table": render_table_widget,
    "process_steps": render_process_steps_widget,
    "steps": render_process_steps_widget,
    "flow_steps": render_process_steps_widget,
    "card_grid": render_card_grid_widget,
    "grid": render_card_grid_widget,
    "native_chart": render_native_chart_widget,
    "bar_chart": render_native_chart_widget,
    "column_chart": render_native_chart_widget,
    "chart": render_native_chart_widget,
    "code_block": render_code_block_widget,
    "sql_panel": render_code_block_widget,
    "sql": render_code_block_widget,
    "image": render_image_widget,
    "png": render_image_widget,
}


# =============================================================================
# Master Slide Compiler: build_composable_split_slide
# =============================================================================

def _render_top_kpi_strip(
    slide: Any,
    theme: Theme,
    kpis: List[Dict[str, Any]],
    left: Inches,
    top: Inches,
    total_w: Inches,
    height: Inches,
) -> None:
    """Renders a clean horizontal strip of Big Number KPI cards across the top canvas."""
    n = max(1, len(kpis))
    gap_x = Inches(0.18)
    card_w = to_emu((total_w - gap_x * (n - 1)) / n)
    for idx, k_item in enumerate(kpis):
        kx = to_emu(left + idx * (card_w + gap_x))
        col_rgb = _resolve_widget_color(theme, k_item.get("color", k_item.get("accent_key", "accent")))

        add_card(
            slide,
            theme,
            kx,
            top,
            card_w,
            height,
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            force_rectangle=True,
        )
        # Thin semantic left accent rule (clean, non-boxy indicator)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, kx, top, Pt(3.5), height)
        bar.shadow.inherit = False
        bar.fill.solid()
        bar.fill.fore_color.rgb = col_rgb
        bar.line.fill.background()
        strip_shape_shadows(bar)

        tb = slide.shapes.add_textbox(to_emu(kx + Inches(0.14)), to_emu(top + Inches(0.06)), to_emu(card_w - Inches(0.22)), to_emu(height - Inches(0.12)))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = str(k_item.get("stat", ""))
        p1.font.name = theme.font_family_header
        p1.font.size = Pt(22.0)
        p1.font.bold = True
        p1.font.color.rgb = col_rgb

        p2 = tf.add_paragraph()
        p2.space_before = Pt(1)
        p2.text = str(k_item.get("label", "")).upper()
        p2.font.name = theme.font_family_header
        p2.font.size = Pt(8.5)
        p2.font.bold = True
        p2.font.color.rgb = theme.get_rgb("primary")

        if k_item.get("subtext"):
            p3 = tf.add_paragraph()
            p3.space_before = Pt(1)
            p3.text = str(k_item.get("subtext", ""))
            p3.font.name = theme.font_family
            p3.font.size = Pt(8.0)
            p3.font.color.rgb = theme.get_rgb("muted_text")


def build_composable_split_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "EXECUTIVE SYNTHESIS | VALUE ARCHITECTURE",
    action_title: str = "Composable Multi-Widget Layout Solves Asymmetric Presentation Needs Without Raw DrawingML Math",
    subtitle: Optional[str] = "Canvas partitioning into relative spatial columns eliminates trial-and-error coordinate hacking.",
    split: Optional[Union[List[Union[int, float]], str]] = None,
    panes: Optional[List[Dict[str, Any]]] = None,
    top_kpis: Optional[List[Dict[str, Any]]] = None,
    gap: float = 0.35,
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
    source: Optional[str] = None,
) -> Any:
    """
    Renders a composable multi-widget presentation slide:
      - Optionally renders a horizontal Big Number `top_kpis` banner at top.
      - Automatically partitions remaining canvas into relative columns based on `split`.
      - Renders modular child widgets (native_chart, code_block, image, hero_kpi, card_list, table, etc.)
        inside each calculated pane bounding box without manual coordinate calculation.
      - Automatically accounts for takeaway bar clearance and footer positioning.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # Content Area Geometry
    content_left = Inches(0.80)
    content_top = Inches(1.80)
    content_width = Inches(11.733)

    if top_kpis and isinstance(top_kpis, list):
        kpi_h = Inches(0.96)
        _render_top_kpi_strip(slide, theme, top_kpis, content_left, content_top, content_width, kpi_h)
        content_top = Inches(2.90)

    # Calculate content height based on takeaway presence and top KPI strip offset
    if takeaway:
        is_two_row = isinstance(takeaway, dict) and bool(takeaway.get("title") and takeaway.get("description"))
        bottom_limit = Inches(5.45) if is_two_row else Inches(6.15)
    else:
        bottom_limit = Inches(6.85)
    content_height = to_emu(bottom_limit - content_top)

    if not panes:
        # Default fallback demo panes
        panes = [
            {
                "widget": "hero_kpi",
                "stat": "+99.4%",
                "stat_label": "Layout Geometry Precision",
                "stat_subtext": "Dynamic coordinate derivation preserves 100% DrawingML alignment without coordinate guessing.",
                "eyebrow": "ENGINEERING RELIABILITY",
                "card_style": "filled",
            },
            {
                "widget": "card_list",
                "style": "cards",
                "items": [
                    {
                        "title": "Unified Canvas Splitting",
                        "description": "**Relative Proportions:** Canvas width divides into percentage-based columns with zero coordinate trial-and-error.",
                    },
                    {
                        "title": "Drop-in Modular Child Widgets",
                        "description": "**Multi-Widget Composition:** Mix Hero KPIs, card stacks, data tables, and step sequences effortlessly.",
                    },
                ],
            },
        ]

    # Calculate bounding boxes
    fractions = parse_split_fractions(split, len(panes))
    boxes = compute_pane_bounding_boxes(
        content_left=content_left,
        content_top=content_top,
        content_width=content_width,
        content_height=content_height,
        fractions=fractions,
        gap=Inches(gap),
    )

    # Render each pane
    for p_idx, pane_cfg in enumerate(panes):
        box = boxes[p_idx]
        widget_type = str(pane_cfg.get("widget", "card_list")).lower().strip()
        dispatcher = WIDGET_DISPATCHERS.get(widget_type, render_card_list_widget)
        try:
            dispatcher(slide, theme, box, pane_cfg)
        except Exception as e:
            logger.error(f"Failed to render pane {p_idx} widget '{widget_type}': {e}", exc_info=True)

    # Takeaway Bar
    if takeaway:
        add_takeaway_bar(slide, theme, takeaway=takeaway)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide
