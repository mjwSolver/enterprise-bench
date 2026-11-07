from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
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
from src.ppt_engine.theme_engine import Theme, hex_to_rgb, rgb_to_hex

from .common import (
    add_slide_with_background,
    add_slide_header,
    add_card,
    add_card_with_top_stripe,
    add_card_with_harmonized_icon,
    add_slide_footer,
    add_takeaway_bar,
    _add_status_pill,
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
    badge = cfg.get("badge")
    badge_variant = cfg.get("badge_variant", "accent")
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

    # 2. Eyebrow Tag & Optional Badge Row (Strictly decoupled to prevent spatial collision)
    has_badge = bool(badge)
    pill_w = Inches(1.35) if has_badge else Inches(0)
    pill_gap = Inches(0.12) if has_badge else Inches(0)
    eye_w = to_emu(inner_w - pill_w - pill_gap) if has_badge else inner_w

    tb_eye = slide.shapes.add_textbox(to_emu(bx + pad_x), to_emu(by + pad_y), eye_w, Inches(0.30))
    tf_eye = tb_eye.text_frame
    tf_eye.word_wrap = True
    tf_eye.margin_left = tf_eye.margin_right = tf_eye.margin_top = tf_eye.margin_bottom = 0
    p_eye = tf_eye.paragraphs[0]
    p_eye.text = eyebrow
    p_eye.font.name = theme.font_family_header
    p_eye.font.size = Pt(9.5)
    p_eye.font.bold = True
    p_eye.font.color.rgb = theme.get_rgb("accent") if is_filled else theme.get_rgb("muted_text")

    if has_badge and badge:
        _add_status_pill(
            slide=slide,
            theme=theme,
            left=to_emu(bx + pad_x + eye_w + pill_gap),
            top=to_emu(by + pad_y - Inches(0.02)),
            width=pill_w,
            height=Inches(0.26),
            status=str(badge),
            font_size_pt=8.5,
            override_color_key=str(badge_variant),
        )

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
        badge = item_dict.get("badge", item_dict.get("metric_badge"))
        badge_variant = item_dict.get("badge_variant", "accent")
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

        # Header: Title + Optional Metric Badge
        has_badge = bool(badge)
        pill_w = Inches(1.60) if has_badge else Inches(0)
        pill_gap = Inches(0.15) if has_badge else Inches(0)
        title_w = to_emu(card_content_w - pill_w - pill_gap) if has_badge else card_content_w

        title_h = Inches(0.48)
        tb_title = slide.shapes.add_textbox(to_emu(bx + pad_left), to_emu(item_y + pad_top), title_w, title_h)
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_t = tf_title.paragraphs[0]
        p_t.text = title
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(12.0)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")

        if has_badge and badge:
            pill_x = to_emu(bx + pad_left + title_w + pill_gap)
            pill_y = to_emu(item_y + pad_top)
            _add_status_pill(
                slide=slide,
                theme=theme,
                left=pill_x,
                top=pill_y,
                width=pill_w,
                height=Inches(0.28),
                status=str(badge),
                font_size_pt=8.5,
                override_color_key=str(badge_variant),
            )

        # Body: Description or Bullets
        body_y = to_emu(item_y + pad_top + title_h + Inches(0.02))
        body_h = to_emu(item_h - (body_y - item_y) - Inches(0.08))
        if body_h > Inches(0.30):
            tb_body = slide.shapes.add_textbox(to_emu(bx + pad_left), body_y, card_content_w, body_h)
            tf_body = tb_body.text_frame
            tf_body.word_wrap = True
            tf_body.margin_left = tf_body.margin_right = tf_body.margin_top = tf_body.margin_bottom = 0

            if bullets and isinstance(bullets, list):
                for b_idx, b_text in enumerate(bullets[:2]):
                    p_b = tf_body.paragraphs[0] if b_idx == 0 else tf_body.add_paragraph()
                    p_b.space_before = Pt(3) if b_idx > 0 else Pt(0)
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
            for b in bullets[:2]:
                p_b = tf.add_paragraph()
                p_b.space_before = Pt(2)
                append_formatted_runs(
                    paragraph=p_b,
                    text=f"• {b}",
                    font_name=theme.font_family,
                    font_size_pt=9.0,
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
}


# =============================================================================
# Master Slide Compiler: build_composable_split_slide
# =============================================================================

def build_composable_split_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "EXECUTIVE SYNTHESIS | VALUE ARCHITECTURE",
    action_title: str = "Composable Multi-Widget Layout Solves Asymmetric Presentation Needs Without Raw DrawingML Math",
    subtitle: Optional[str] = "Canvas partitioning into relative spatial columns eliminates trial-and-error coordinate hacking.",
    split: Optional[Union[List[Union[int, float]], str]] = None,
    panes: Optional[List[Dict[str, Any]]] = None,
    gap: float = 0.35,
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: str = "Enterprise Strategy Group  |  Confidential & Proprietary",
    source: Optional[str] = None,
) -> Any:
    """
    Renders a composable multi-widget presentation slide:
      - Automatically partitions canvas into relative columns based on `split`.
      - Renders modular child widgets (hero_kpi, card_list, table, process_steps, card_grid)
        inside each calculated pane bounding box without manual coordinate calculation.
      - Automatically accounts for takeaway bar clearance and footer positioning.
    """
    slide = add_slide_with_background(prs, theme)
    add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # Content Area Geometry
    content_left = Inches(0.80)
    content_top = Inches(1.80)
    content_width = Inches(11.733)

    # Calculate content height based on takeaway presence
    if takeaway:
        # Single row takeaway: 0.54" height; 2-row: 1.30"
        is_two_row = isinstance(takeaway, dict) and bool(takeaway.get("title") and takeaway.get("description"))
        content_height = Inches(3.65) if is_two_row else Inches(4.35)
    else:
        content_height = Inches(5.05)

    if not panes:
        # Default fallback demo panes
        panes = [
            {
                "widget": "hero_kpi",
                "stat": "+99.4%",
                "stat_label": "Layout Geometry Precision",
                "stat_subtext": "Dynamic coordinate derivation preserves 100% DrawingML alignment without coordinate guessing.",
                "eyebrow": "ENGINEERING RELIABILITY",
                "badge": "MANDATED",
                "badge_variant": "success",
                "card_style": "filled",
            },
            {
                "widget": "card_list",
                "style": "cards",
                "items": [
                    {
                        "title": "Unified Canvas Splitting",
                        "description": "**Relative Proportions:** Canvas width divides into percentage-based columns with zero coordinate trial-and-error.",
                        "badge": "ZERO MATH",
                        "badge_variant": "accent",
                    },
                    {
                        "title": "Drop-in Modular Child Widgets",
                        "description": "**Multi-Widget Composition:** Mix Hero KPIs, card stacks, data tables, and step sequences effortlessly.",
                        "badge": "DROP-IN",
                        "badge_variant": "accent",
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
