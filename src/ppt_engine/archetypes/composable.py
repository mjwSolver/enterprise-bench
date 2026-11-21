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
    resolve_content_top,
    add_card,
    add_card_with_top_stripe,
    add_card_with_harmonized_icon,
    add_slide_footer,
    add_takeaway_bar,
    _fit_image_in_box,
    _get_contrast_text_color,
    _add_status_pill,
    bounded_slice,
    draw_hairline,
    resolve_accent_color,
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


def compute_vertical_pane_bounding_boxes(
    content_left: Inches,
    content_top: Inches,
    content_width: Inches,
    content_height: Inches,
    fractions: List[float],
    gap: Inches,
) -> List[Tuple[Inches, Inches, Inches, Inches]]:
    """
    Divides available canvas area vertically into collision-free row bounding boxes
    (left, top, width, height) spaced by `gap`.
    """
    n = len(fractions)
    if n == 0:
        return []
    if n == 1:
        return [(content_left, content_top, content_width, content_height)]

    total_gap = gap * (n - 1)
    avail_height = content_height - total_gap
    if avail_height < Inches(0.8):
        avail_height = content_height

    boxes: List[Tuple[Inches, Inches, Inches, Inches]] = []
    curr_y = content_top

    for frac in fractions:
        h = Emu(int(round(avail_height * frac)))
        boxes.append((content_left, curr_y, content_width, h))
        curr_y = Emu(int(round(curr_y + h + gap)))

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
    Requires explicit 'stat' and 'stat_label' (never fabricates fallback KPI numbers).
    """
    bx, by, bw, bh = box
    style = str(cfg.get("card_style", "filled")).lower().strip()
    stat_raw = cfg.get("stat", cfg.get("hero_stat"))
    label_raw = cfg.get("stat_label", cfg.get("label"))
    if not stat_raw or not label_raw:
        raise ValueError("hero_kpi widget requires explicit 'stat' and 'stat_label' values (synthetic fallbacks are prohibited).")

    stat = str(stat_raw).strip()
    stat_label = str(label_raw).strip()
    stat_subtext = cfg.get("stat_subtext", cfg.get("subtext", cfg.get("description")))
    eyebrow_raw = cfg.get("eyebrow", cfg.get("tracker"))
    eyebrow = str(eyebrow_raw).strip().upper() if eyebrow_raw and str(eyebrow_raw).strip() else ""
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

    # Optional top accent stripe on surface card (opt-in only)
    if not is_filled and cfg.get("show_top_stripe", False):
        st_h = Pt(4.0)
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, by, bw, st_h)
        stripe.shadow.inherit = False
        strip_shape_shadows(stripe)
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = theme.get_rgb(accent_key)
        stripe.line.fill.background()

    is_compact = bh <= Inches(2.90)
    pad_x = Inches(0.24 if is_compact else 0.28)
    pad_y = Inches(0.16) if is_compact else (Inches(0.24) if not is_filled else Inches(0.30))
    inner_w = to_emu(bw - (pad_x * 2))

    # 2. Opt-in Eyebrow Tag
    if eyebrow:
        eye_h = Inches(0.22 if is_compact else 0.30)
        tb_eye = slide.shapes.add_textbox(to_emu(bx + pad_x), to_emu(by + pad_y), inner_w, eye_h)
        tf_eye = tb_eye.text_frame
        tf_eye.word_wrap = True
        tf_eye.margin_left = tf_eye.margin_right = tf_eye.margin_top = tf_eye.margin_bottom = 0
        p_eye = tf_eye.paragraphs[0]
        p_eye.text = eyebrow
        p_eye.font.name = theme.font_family_header
        p_eye.font.size = Pt(9.0 if is_compact else 9.5)
        p_eye.font.bold = True
        p_eye.font.color.rgb = theme.get_rgb("accent") if is_filled else theme.get_rgb("muted_text")
        stat_top = to_emu(by + pad_y + Inches(0.24 if is_compact else 0.32))
    else:
        stat_top = to_emu(by + pad_y)
    stat_box_h = Inches(0.62 if is_compact else 0.85)
    tb_stat = slide.shapes.add_textbox(to_emu(bx + pad_x), stat_top, inner_w, stat_box_h)
    tf_stat = tb_stat.text_frame
    tf_stat.word_wrap = True
    tf_stat.margin_left = tf_stat.margin_right = tf_stat.margin_top = tf_stat.margin_bottom = 0
    p_stat = tf_stat.paragraphs[0]
    p_stat.text = stat
    p_stat.font.name = theme.font_family_header
    base_stat_pt = 32.0 if is_compact else 36.0
    p_stat.font.size = Pt(base_stat_pt) if len(stat) <= 7 else Pt(28.0 if is_compact else 30.0)
    p_stat.font.bold = True
    p_stat.font.color.rgb = RGBColor(255, 255, 255) if is_filled else theme.get_rgb("primary")

    # 4. Metric Label
    lbl_top = to_emu(stat_top + Inches(0.60 if is_compact else 0.82))
    lbl_h = Inches(0.32 if is_compact else 0.55)
    tb_lbl = slide.shapes.add_textbox(to_emu(bx + pad_x), lbl_top, inner_w, lbl_h)
    tf_lbl = tb_lbl.text_frame
    tf_lbl.word_wrap = True
    tf_lbl.margin_left = tf_lbl.margin_right = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
    p_lbl = tf_lbl.paragraphs[0]
    p_lbl.text = stat_label
    p_lbl.font.name = theme.font_family_header
    p_lbl.font.size = Pt(11.5 if is_compact else 12.5)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = hex_to_rgb("#F1F5F9") if is_filled else theme.get_rgb("primary")

    # 5. Native DrawingML Hairline Divider
    div_y = to_emu(lbl_top + Inches(0.36 if is_compact else 0.60))
    h_div = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        to_emu(bx + pad_x),
        div_y,
        inner_w,
        Pt(0.75),
    )
    h_div.shadow.inherit = False
    strip_shape_shadows(h_div)
    h_div.fill.solid()
    h_div.fill.fore_color.rgb = hex_to_rgb("#334155") if is_filled else theme.get_rgb("border")
    h_div.line.fill.background()

    # 6. Subtext / Narrative Frame
    if stat_subtext:
        sub_top = to_emu(div_y + Inches(0.10 if is_compact else 0.14))
        sub_h = to_emu(bh - (sub_top - by) - Inches(0.14 if is_compact else 0.20))
        if sub_h > Inches(0.32):
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
                font_size_pt=9.5 if is_compact else 10.0,
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
    Renders a flexible 1-6 vertical stack of cards, clean divided streams, or numbered story cards
    (large far-left index numeral + vertical hairline divider + story title & copy).
    """
    bx, by, bw, bh = box
    raw_items = cfg.get("items", cfg.get("cards", cfg.get("blocks", [])))
    if not raw_items:
        return

    header_title = cfg.get("title") or cfg.get("header_title") or cfg.get("header_bar")
    if isinstance(header_title, str) and header_title.strip():
        hdr_h = Inches(0.32)
        h_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, by, bw, hdr_h)
        h_card.shadow.inherit = False
        strip_shape_shadows(h_card)
        h_card.fill.solid()
        h_card.fill.fore_color.rgb = theme.get_rgb(cfg.get("header_bg_key", "primary"))
        h_card.line.fill.background()
        tf_h = h_card.text_frame
        tf_h.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_h.margin_left = Inches(0.14)
        p_h = tf_h.paragraphs[0]
        p_h.text = header_title.strip().upper()
        p_h.font.name = theme.font_family_header
        p_h.font.size = Pt(10.0)
        p_h.font.bold = True
        p_h.font.color.rgb = RGBColor(255, 255, 255)
        by = to_emu(by + hdr_h + Inches(0.10))
        bh = to_emu(max(Inches(1.20), bh - hdr_h - Inches(0.10)))

    style = str(cfg.get("style", "cards")).lower().strip()
    is_divided = style in ("divided", "streams", "stream", "lines")
    is_numbered = bool(
        cfg.get("numbered", cfg.get("show_numbers", False))
        or style in ("numbered", "story", "stories", "numbered_cards")
        or any(isinstance(it, dict) and (it.get("number") is not None or it.get("index") is not None) for it in raw_items)
    )
    widget_stripe_opt = cfg.get("show_stripe", cfg.get("striped"))
    base_default_stripe = bool(widget_stripe_opt) if widget_stripe_opt is not None else (style == "striped")

    items = bounded_slice(raw_items, 6, "composable_list", "items")
    n_items = len(items)
    gap_y = Inches(0.10 if n_items >= 4 else 0.14) if not is_divided else Inches(0)
    avail_h = bh - (gap_y * (n_items - 1)) if not is_divided else bh
    item_h = to_emu(avail_h / n_items)

    title_pt = 12.0 if n_items <= 3 else (10.5 if n_items <= 5 else 10.0)
    body_pt = 10.0 if n_items <= 3 else 9.0

    for idx, item in enumerate(items):
        item_y = to_emu(by + (idx * (item_h + gap_y))) if not is_divided else to_emu(by + (idx * item_h))
        item_dict = item if isinstance(item, dict) else {"title": str(item)}

        title = str(item_dict.get("title", f"Item {idx + 1}")).strip()
        desc = item_dict.get("description", item_dict.get("body", ""))
        bullets = item_dict.get("bullets", [])
        has_explicit_accent = bool(item_dict.get("accent_key"))
        accent_key = item_dict.get("accent_key", "accent")
        accent_rgb = theme.get_rgb(accent_key)
        item_default_stripe = base_default_stripe if widget_stripe_opt is not None else (base_default_stripe or has_explicit_accent)
        use_stripe = bool(item_dict.get("show_stripe", item_default_stripe))

        if not is_divided:
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
            if use_stripe:
                st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, item_y, Pt(4.0), item_h)
                st.shadow.inherit = False
                strip_shape_shadows(st)
                st.fill.solid()
                st.fill.fore_color.rgb = accent_rgb
                st.line.fill.background()
            pad_left = Inches(0.20 if use_stripe else 0.18)
            pad_top = Inches(0.08 if n_items >= 4 else 0.12)
        else:
            pad_left = Inches(0.04)
            pad_top = Inches(0.06 if n_items >= 4 else 0.08)

        # Optional Large Left Numeral Column + Hairline Vertical Divider (Story-Card Mode)
        if is_numbered:
            num_val = item_dict.get("number", item_dict.get("index", idx + 1))
            num_text = str(num_val)
            num_w = Inches(0.68 if n_items >= 4 else 0.78)
            num_x = to_emu(bx + (Inches(0.10) if not is_divided else Inches(0.02)))
            tb_num = slide.shapes.add_textbox(num_x, item_y, num_w, item_h)
            tf_num = tb_num.text_frame
            tf_num.word_wrap = False
            tf_num.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
            pn = tf_num.paragraphs[0]
            pn.text = num_text
            pn.alignment = PP_ALIGN.CENTER
            pn.font.name = theme.font_family_header
            pn.font.size = Pt(28.0 if n_items <= 3 else (22.0 if n_items <= 5 else 20.0))
            pn.font.bold = True
            pn.font.color.rgb = accent_rgb

            div_x = to_emu(num_x + num_w + Inches(0.04))
            v_pad = Inches(0.10 if n_items >= 4 else 0.16)
            v_div = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                div_x,
                to_emu(item_y + v_pad),
                Pt(0.75),
                to_emu(max(Inches(0.24), item_h - v_pad * 2)),
            )
            v_div.shadow.inherit = False
            strip_shape_shadows(v_div)
            v_div.fill.solid()
            v_div.fill.fore_color.rgb = theme.get_rgb("border")
            v_div.line.fill.background()

            text_left = to_emu(div_x + Inches(0.16))
        else:
            text_left = to_emu(bx + pad_left)

        card_content_w = to_emu((bx + bw) - text_left - Inches(0.16))

        # Header (width-aware wrapped height matching visual_qa line estimation)
        card_content_w_in = card_content_w / 914400.0
        chars_per_title_line = max(4, int(card_content_w_in * 72.0 / (title_pt * 0.55)))
        title_lines = max(1, (len(title) + chars_per_title_line - 1) // chars_per_title_line)
        min_title_h_in = (title_pt * 1.25 * title_lines + 3.0) / 72.0 + 0.02
        base_title_floor = 0.28 if n_items >= 4 else 0.30
        raw_title_h = Inches(max(base_title_floor, min_title_h_in))
        has_body = bool((bullets and isinstance(bullets, list)) or desc)
        max_title_h = max(Inches(0.26), item_h - pad_top - (Inches(0.30) if has_body else Inches(0.08)))
        title_h = to_emu(min(raw_title_h, max_title_h))

        # Dynamically vertically center sparse (title + body) blocks inside the cell,
        # falling back to min pad_top when content is dense so full cell height is available.
        chars_per_body_line = max(4, int(card_content_w_in * 72.0 / (body_pt * 0.55)))
        est_body_h_in = 0.0
        if bullets and isinstance(bullets, list):
            sliced_bullets = bounded_slice(bullets, 2, "composable_list", "item.bullets")
            total_b_lines = sum(
                max(1, (len(f"•  {str(b).replace('**', '')}") + chars_per_body_line - 1) // chars_per_body_line)
                for b in sliced_bullets
            )
            est_gap_pt = 6.0 if (item_h - pad_top - title_h) >= Inches(1.0) else 3.0
            est_body_h_in = (body_pt * 1.25 * total_b_lines + max(0, len(sliced_bullets) - 1) * est_gap_pt + len(sliced_bullets) * 1.5) / 72.0
        elif desc:
            clean_desc = str(desc).replace("**", "")
            d_lines = max(1, (len(clean_desc) + chars_per_body_line - 1) // chars_per_body_line)
            est_body_h_in = (body_pt * 1.25 * d_lines) / 72.0

        total_content_h = title_h + (Inches(0.02) + Inches(est_body_h_in) if has_body else Inches(0))
        effective_pad_top = to_emu(max(pad_top, (item_h - total_content_h) / 2))

        tb_title = slide.shapes.add_textbox(text_left, to_emu(item_y + effective_pad_top), card_content_w, title_h)
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_t = tf_title.paragraphs[0]
        p_t.text = title
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(title_pt)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")

        # Body: Description or Bullets
        body_y = to_emu(item_y + effective_pad_top + title_h + Inches(0.02))
        body_h = to_emu(item_h - (body_y - item_y) - Inches(0.06))
        if body_h > Inches(0.22):
            tb_body = slide.shapes.add_textbox(text_left, body_y, card_content_w, body_h)
            tf_body = tb_body.text_frame
            tf_body.word_wrap = True
            tf_body.margin_left = tf_body.margin_right = tf_body.margin_top = tf_body.margin_bottom = 0

            if bullets and isinstance(bullets, list):
                bullet_gap = 6.0 if body_h >= Inches(0.95) else 3.0
                for b_idx, b_text in enumerate(bounded_slice(bullets, 2, "composable_list", "item.bullets")):
                    p_b = tf_body.paragraphs[0] if b_idx == 0 else tf_body.add_paragraph()
                    p_b.space_before = Pt(bullet_gap) if b_idx > 0 else Pt(0)
                    p_b.space_after = Pt(1.5)
                    append_formatted_runs(
                        paragraph=p_b,
                        text=f"•  {b_text}",
                        font_name=theme.font_family,
                        font_size_pt=body_pt,
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
                    font_size_pt=body_pt,
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
            strip_shape_shadows(div)
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
    Supports column alignment, optional compact title, and focal row highlighting.
    """
    bx, by, bw, bh = box
    cols_cfg = cfg.get("columns")
    if cols_cfg and isinstance(cols_cfg, list):
        headers = [c.get("header", "") if isinstance(c, dict) else str(c) for c in cols_cfg]
        widths_cfg = cfg.get("column_widths") or [c.get("width", 1) if isinstance(c, dict) else 1 for c in cols_cfg]
        aligns_cfg = [str(c.get("align", "LEFT")).upper() if isinstance(c, dict) else "LEFT" for c in cols_cfg]
    else:
        headers = cfg.get("headers")
        widths_cfg = cfg.get("column_widths")
        aligns_cfg = [str(a).upper() for a in (cfg.get("column_alignments") or [])]
    rows = cfg.get("rows", [])
    if not headers or not rows:
        return

    table_title = str(cfg.get("title", "")).strip()
    if table_title:
        tb_tt = slide.shapes.add_textbox(bx, by, bw, Inches(0.26))
        tf_tt = tb_tt.text_frame
        tf_tt.word_wrap = True
        tf_tt.margin_left = tf_tt.margin_right = tf_tt.margin_top = tf_tt.margin_bottom = 0
        p_tt = tf_tt.paragraphs[0]
        p_tt.text = table_title
        p_tt.font.name = theme.font_family_header
        p_tt.font.size = Pt(11.0)
        p_tt.font.bold = True
        p_tt.font.color.rgb = theme.get_rgb("primary")
        by = to_emu(by + Inches(0.28))
        bh = to_emu(max(Inches(0.90), bh - Inches(0.28)))

    n_cols = len(headers)
    n_rows = len(rows) + 1  # include header row

    # Table shape
    shape = slide.shapes.add_table(n_rows, n_cols, bx, by, bw, bh)
    strip_shape_shadows(shape)
    table = shape.table

    # Column widths
    col_fractions = parse_split_fractions(widths_cfg, n_cols)
    for c_idx, frac in enumerate(col_fractions):
        table.columns[c_idx].width = int(bw * frac)

    def _pp_align(align_str: str) -> PP_ALIGN:
        if align_str == "RIGHT":
            return PP_ALIGN.RIGHT
        if align_str == "CENTER":
            return PP_ALIGN.CENTER
        return PP_ALIGN.LEFT

    # Header Row
    hdr_pt = float(cfg.get("header_font_size", 9.0))
    body_pt = float(cfg.get("font_size", 9.0 if len(rows) >= 6 else 9.5))
    pad_y_in = 0.05 if len(rows) >= 6 else 0.07
    for c_idx, h_text in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.fill.solid()
        cell.fill.fore_color.rgb = theme.get_rgb("primary")
        tf = cell.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.10)
        tf.margin_right = Inches(0.10)
        tf.margin_top = Inches(pad_y_in)
        tf.margin_bottom = Inches(pad_y_in)
        p = tf.paragraphs[0]
        p.text = str(h_text).upper()
        p.alignment = _pp_align(aligns_cfg[c_idx] if c_idx < len(aligns_cfg) else "LEFT")
        p.font.name = theme.font_family_header
        p.font.size = Pt(hdr_pt)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    zebra = bool(cfg.get("zebra", True))
    hl_idx_raw = cfg.get("highlight_row")
    hl_idx: Optional[int] = None
    if isinstance(hl_idx_raw, str) and hl_idx_raw.lower() == "last":
        hl_idx = len(rows) - 1
    elif isinstance(hl_idx_raw, int):
        hl_idx = hl_idx_raw if hl_idx_raw >= 0 else len(rows) + hl_idx_raw

    for r_idx, row_item in enumerate(rows, start=1):
        zero_idx = r_idx - 1
        if isinstance(row_item, dict):
            row_data = row_item.get("cells") or row_item.get("values") or []
            is_hl = bool(row_item.get("highlight") or row_item.get("is_highlight") or (hl_idx == zero_idx))
        else:
            row_data = row_item
            is_hl = hl_idx == zero_idx

        is_even = (r_idx % 2 == 0)
        if is_hl:
            row_bg = hex_to_rgb("#DBEAFE")
        else:
            row_bg = hex_to_rgb("#F8FAFC") if (zebra and is_even) else theme.get_rgb("surface")

        for c_idx in range(n_cols):
            cell = table.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            tf = cell.text_frame
            tf.word_wrap = True
            tf.margin_left = Inches(0.10)
            tf.margin_right = Inches(0.10)
            tf.margin_top = Inches(pad_y_in)
            tf.margin_bottom = Inches(pad_y_in)
            p = tf.paragraphs[0]
            p.alignment = _pp_align(aligns_cfg[c_idx] if c_idx < len(aligns_cfg) else "LEFT")
            val = str(row_data[c_idx]) if c_idx < len(row_data) else ""
            p.text = ""
            append_formatted_runs(
                paragraph=p,
                text=val,
                font_name=theme.font_family_header if is_hl else theme.font_family,
                font_size_pt=body_pt,
                font_color=theme.get_rgb("primary") if is_hl else theme.get_rgb("secondary"),
                lead_color=theme.get_rgb("primary"),
                default_bold=is_hl,
                auto_colon_lead=True,
            )


def _draw_flow_arrow(
    slide: Any,
    x_start: Emu,
    y_mid: Emu,
    x_end: Emu,
    color: RGBColor,
) -> None:
    """Draw a flat horizontal vector right-arrow connector between flow nodes."""
    gap_w = x_end - x_start
    if gap_w < Inches(0.10):
        return
    arrow_h = Inches(0.14)
    arrow = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW,
        x_start,
        to_emu(y_mid - arrow_h / 2),
        gap_w,
        arrow_h,
    )
    arrow.shadow.inherit = False
    strip_shape_shadows(arrow)
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = color
    arrow.line.fill.background()


def _render_horizontal_flow_diagram(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
    steps: List[Any],
) -> None:
    """
    Renders a horizontal connected process flow with optional owner sub-labels,
    current-step focal anchor, optional Yes/No decision branch, and bottom caption.
    """
    bx, by, bw, bh = box
    branch = cfg.get("branch") if isinstance(cfg.get("branch"), dict) else None
    caption = str(cfg.get("caption") or "").strip()

    has_owners = any(isinstance(s, dict) and str(s.get("owner") or "").strip() for s in steps)
    if branch and str(branch.get("owner") or "").strip():
        has_owners = True

    cap_h = Inches(0.28) if caption else Inches(0)
    cap_gap = Inches(0.06) if caption else Inches(0)
    owner_h = Inches(0.36) if has_owners else Inches(0)
    owner_gap = Inches(0.05) if has_owners else Inches(0)

    avail_flow_h = max(Inches(0.85), bh - cap_h - cap_gap - owner_h - owner_gap)
    flow_h = min(avail_flow_h, Inches(1.48 if branch else 1.18))
    flow_y = to_emu(by + max(Inches(0), (avail_flow_h - flow_h) / 2))

    n_linear = len(steps)
    n_cols = n_linear + (2 if branch else 0)
    conn_gap = Inches(0.46 if branch else (0.28 if n_cols >= 5 else 0.36))
    total_gaps = conn_gap * max(0, n_cols - 1)
    node_w = to_emu((bw - total_gaps) / max(1, n_cols))
    y_mid = to_emu(flow_y + flow_h / 2)
    conn_rgb = theme.get_rgb("muted")

    for s_idx, st in enumerate(steps):
        s_dict = st if isinstance(st, dict) else {"title": str(st)}
        sx = to_emu(bx + s_idx * (node_w + conn_gap))
        is_current = bool(s_dict.get("is_current") or s_dict.get("highlight"))
        accent_key = s_dict.get("accent_key", "primary" if is_current else "accent")
        accent_rgb = _resolve_widget_color(theme, accent_key)

        if is_current:
            bg_rgb = accent_rgb
            border_rgb = accent_rgb
            border_w = 1.0
            title_rgb = _get_contrast_text_color(bg_rgb)
            eye_rgb = hex_to_rgb("#BAE6FD") if bg_rgb == theme.get_rgb("primary") else title_rgb
        else:
            bg_rgb = theme.get_rgb("surface")
            border_rgb = theme.get_rgb("border")
            border_w = 1.0
            title_rgb = theme.get_rgb("primary")
            eye_rgb = accent_rgb

        add_card(
            slide,
            theme,
            sx,
            flow_y,
            node_w,
            flow_h,
            bg_color=bg_rgb,
            border_color=border_rgb,
            border_width_pt=border_w,
            force_rectangle=True,
        )

        # Thin left accent bar on non-filled steps when accent_key is explicitly set
        if not is_current and s_dict.get("accent_key"):
            l_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx, flow_y, Pt(3.5), flow_h)
            l_bar.shadow.inherit = False
            strip_shape_shadows(l_bar)
            l_bar.fill.solid()
            l_bar.fill.fore_color.rgb = accent_rgb
            l_bar.line.fill.background()

        step_num = str(s_dict.get("step_num") or s_dict.get("num") or "").strip()
        title_txt = str(s_dict.get("title") or "").strip()
        pad_x = Inches(0.10)
        inner_tb_h = min(to_emu(flow_h - Inches(0.12)), Inches(0.68 if step_num else 0.50))
        inner_tb_y = to_emu(flow_y + (flow_h - inner_tb_h) / 2)
        tb = slide.shapes.add_textbox(
            to_emu(sx + pad_x),
            inner_tb_y,
            to_emu(node_w - pad_x * 2),
            inner_tb_h,
        )
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        if step_num:
            p_num = tf.paragraphs[0]
            p_num.text = step_num.upper() if not step_num.isdigit() else f"STEP {step_num.zfill(2)}"
            p_num.alignment = PP_ALIGN.CENTER
            p_num.font.name = theme.font_family_header
            p_num.font.size = Pt(8.0)
            p_num.font.bold = True
            p_num.font.color.rgb = eye_rgb
            p_t = tf.add_paragraph()
            p_t.space_before = Pt(3)
        else:
            p_t = tf.paragraphs[0]

        p_t.text = title_txt
        p_t.alignment = PP_ALIGN.CENTER
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(10.0 if n_cols <= 5 else 9.5)
        p_t.font.bold = True
        p_t.font.color.rgb = title_rgb

        if has_owners:
            own_txt = str(s_dict.get("owner") or "").strip()
            if own_txt:
                tb_o = slide.shapes.add_textbox(
                    sx,
                    to_emu(flow_y + flow_h + owner_gap),
                    node_w,
                    owner_h,
                )
                tf_o = tb_o.text_frame
                tf_o.word_wrap = True
                tf_o.margin_left = tf_o.margin_right = tf_o.margin_top = tf_o.margin_bottom = 0
                po = tf_o.paragraphs[0]
                po.text = own_txt
                po.alignment = PP_ALIGN.CENTER
                po.font.name = theme.font_family_header if is_current else theme.font_family
                po.font.size = Pt(8.5)
                po.font.bold = is_current
                po.font.color.rgb = theme.get_rgb("primary") if is_current else theme.get_rgb("muted")

        # Connector to next step or decision gate
        if s_idx < n_linear - 1 or branch:
            _draw_flow_arrow(
                slide,
                to_emu(sx + node_w + Inches(0.02)),
                y_mid,
                to_emu(sx + node_w + conn_gap - Inches(0.02)),
                conn_rgb,
            )

    if branch:
        gate_x = to_emu(bx + n_linear * (node_w + conn_gap))
        gate_accent = _resolve_widget_color(theme, branch.get("accent_key", "warning"))
        add_card(
            slide,
            theme,
            gate_x,
            flow_y,
            node_w,
            flow_h,
            bg_color=hex_to_rgb("#FFFBEB"),
            border_color=gate_accent,
            border_width_pt=1.5,
            force_rectangle=True,
        )
        gate_tb_h = min(to_emu(flow_h - Inches(0.12)), Inches(0.68))
        gate_tb_y = to_emu(flow_y + (flow_h - gate_tb_h) / 2)
        tb_g = slide.shapes.add_textbox(
            to_emu(gate_x + Inches(0.10)),
            gate_tb_y,
            to_emu(node_w - Inches(0.20)),
            gate_tb_h,
        )
        tf_g = tb_g.text_frame
        tf_g.word_wrap = True
        tf_g.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_g.margin_left = tf_g.margin_right = tf_g.margin_top = tf_g.margin_bottom = 0
        pg_eye = tf_g.paragraphs[0]
        pg_eye.text = str(branch.get("eyebrow", "DECISION GATE")).upper()
        pg_eye.alignment = PP_ALIGN.CENTER
        pg_eye.font.name = theme.font_family_header
        pg_eye.font.size = Pt(8.0)
        pg_eye.font.bold = True
        pg_eye.font.color.rgb = gate_accent

        pg_q = tf_g.add_paragraph()
        pg_q.space_before = Pt(3)
        pg_q.text = str(branch.get("question", "Outcome?")).strip()
        pg_q.alignment = PP_ALIGN.CENTER
        pg_q.font.name = theme.font_family_header
        pg_q.font.size = Pt(10.0)
        pg_q.font.bold = True
        pg_q.font.color.rgb = theme.get_rgb("primary")

        if has_owners and str(branch.get("owner") or "").strip():
            tb_go = slide.shapes.add_textbox(gate_x, to_emu(flow_y + flow_h + owner_gap), node_w, owner_h)
            tf_go = tb_go.text_frame
            tf_go.word_wrap = True
            tf_go.margin_left = tf_go.margin_right = tf_go.margin_top = tf_go.margin_bottom = 0
            pgo = tf_go.paragraphs[0]
            pgo.text = str(branch["owner"]).strip()
            pgo.alignment = PP_ALIGN.CENTER
            pgo.font.name = theme.font_family
            pgo.font.size = Pt(8.5)
            pgo.font.color.rgb = theme.get_rgb("muted")

        # Stacked Yes / No outcome boxes
        out_x = to_emu(gate_x + node_w + conn_gap)
        out_gap_y = Inches(0.14)
        out_h = to_emu((flow_h - out_gap_y) / 2)
        yes_raw = branch.get("yes") if "yes" in branch else branch.get(True)
        no_raw = branch.get("no") if "no" in branch else branch.get(False)
        yes_cfg = yes_raw if isinstance(yes_raw, dict) else {"title": str(yes_raw or "Yes outcome")}
        no_cfg = no_raw if isinstance(no_raw, dict) else {"title": str(no_raw or "No outcome")}

        yes_y = flow_y
        no_y = to_emu(flow_y + out_h + out_gap_y)
        y_yes_mid = to_emu(yes_y + out_h / 2)
        y_no_mid = to_emu(no_y + out_h / 2)

        # Orthogonal split connector
        split_x = to_emu(gate_x + node_w + conn_gap * 0.34)
        stub_in = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, to_emu(gate_x + node_w + Inches(0.01)), to_emu(y_mid - Pt(0.75)), to_emu(split_x - (gate_x + node_w)), Pt(1.5))
        stub_in.shadow.inherit = False
        strip_shape_shadows(stub_in)
        stub_in.fill.solid()
        stub_in.fill.fore_color.rgb = conn_rgb
        stub_in.line.fill.background()

        v_stem = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, to_emu(split_x - Pt(0.75)), y_yes_mid, Pt(1.5), to_emu(y_no_mid - y_yes_mid))
        v_stem.shadow.inherit = False
        strip_shape_shadows(v_stem)
        v_stem.fill.solid()
        v_stem.fill.fore_color.rgb = conn_rgb
        v_stem.line.fill.background()

        yes_col = _resolve_widget_color(theme, yes_cfg.get("accent_key", "success"))
        no_col = _resolve_widget_color(theme, no_cfg.get("accent_key", "danger"))
        _draw_flow_arrow(slide, split_x, y_yes_mid, to_emu(out_x - Inches(0.02)), yes_col)
        _draw_flow_arrow(slide, split_x, y_no_mid, to_emu(out_x - Inches(0.02)), no_col)

        # Clean YES / NO labels placed cleanly above/below branch arrows inside gap
        lbl_w = to_emu(max(Inches(0.32), out_x - split_x - Inches(0.04)))
        tb_ly = slide.shapes.add_textbox(to_emu(split_x + Inches(0.02)), to_emu(y_yes_mid - Inches(0.24)), lbl_w, Inches(0.20))
        tf_ly = tb_ly.text_frame
        tf_ly.word_wrap = False
        tf_ly.margin_left = tf_ly.margin_right = tf_ly.margin_top = tf_ly.margin_bottom = 0
        ply = tf_ly.paragraphs[0]
        ply.text = str(yes_cfg.get("label", "YES")).upper()
        ply.font.name = theme.font_family_header
        ply.font.size = Pt(8.5)
        ply.font.bold = True
        ply.font.color.rgb = yes_col

        tb_ln = slide.shapes.add_textbox(to_emu(split_x + Inches(0.02)), to_emu(y_no_mid + Inches(0.04)), lbl_w, Inches(0.20))
        tf_ln = tb_ln.text_frame
        tf_ln.word_wrap = False
        tf_ln.margin_left = tf_ln.margin_right = tf_ln.margin_top = tf_ln.margin_bottom = 0
        pln = tf_ln.paragraphs[0]
        pln.text = str(no_cfg.get("label", "NO")).upper()
        pln.font.name = theme.font_family_header
        pln.font.size = Pt(8.5)
        pln.font.bold = True
        pln.font.color.rgb = no_col

        for oy, o_cfg, o_col, o_bg in [
            (yes_y, yes_cfg, yes_col, hex_to_rgb("#ECFDF5")),
            (no_y, no_cfg, no_col, hex_to_rgb("#FEF2F2")),
        ]:
            add_card(
                slide,
                theme,
                out_x,
                oy,
                node_w,
                out_h,
                bg_color=o_bg,
                border_color=o_col,
                border_width_pt=1.0,
                force_rectangle=True,
            )
            l_st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, out_x, oy, Pt(3.5), out_h)
            l_st.shadow.inherit = False
            strip_shape_shadows(l_st)
            l_st.fill.solid()
            l_st.fill.fore_color.rgb = o_col
            l_st.line.fill.background()

            tb_o = slide.shapes.add_textbox(to_emu(out_x + Inches(0.10)), to_emu(oy + Inches(0.04)), to_emu(node_w - Inches(0.16)), to_emu(out_h - Inches(0.08)))
            tf_out = tb_o.text_frame
            tf_out.word_wrap = True
            tf_out.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_out.margin_left = tf_out.margin_right = tf_out.margin_top = tf_out.margin_bottom = 0
            po_t = tf_out.paragraphs[0]
            po_t.text = str(o_cfg.get("title", "")).strip()
            po_t.alignment = PP_ALIGN.CENTER
            po_t.font.name = theme.font_family_header
            po_t.font.size = Pt(9.5)
            po_t.font.bold = True
            po_t.font.color.rgb = theme.get_rgb("primary")

    if caption:
        cap_y = to_emu(by + bh - cap_h)
        tb_cap = slide.shapes.add_textbox(bx, cap_y, bw, cap_h)
        tf_cap = tb_cap.text_frame
        tf_cap.word_wrap = True
        tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_top = tf_cap.margin_bottom = 0
        pc = tf_cap.paragraphs[0]
        pc.text = caption
        pc.font.name = theme.font_family
        pc.font.size = Pt(8.5)
        pc.font.color.rgb = theme.get_rgb("muted")


def render_process_steps_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders sequential process steps (vertical stack or horizontal flow) inside the bounding box.
    Horizontal mode automatically engages connected flow rendering when 'branch', 'owner',
    'caption', 'show_connectors', or style='flow' is specified.
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
        use_flow_mode = bool(
            cfg.get("branch")
            or cfg.get("show_connectors")
            or cfg.get("caption")
            or str(cfg.get("style", "")).lower() in ("flow", "diagram", "decision_flow")
            or any(isinstance(s, dict) and (s.get("owner") or s.get("is_current")) for s in steps)
        )
        if use_flow_mode:
            _render_horizontal_flow_diagram(slide, theme, box, cfg, steps)
            return

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
            strip_shape_shadows(top_st)
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
            strip_shape_shadows(left_st)
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
    Supports bullets or narrative description, optional numbered index badges,
    single-focal-anchor highlighting (is_focal/highlight), and opt-in top stripes.
    """
    bx, by, bw, bh = box
    raw_items = cfg.get("items", cfg.get("cards", []))
    if not raw_items:
        return

    columns = int(cfg.get("columns", min(3, len(raw_items)) if bh < Inches(3.6) else 2))
    cols = max(1, min(columns, len(raw_items)))
    rows = max(1, (len(raw_items) + cols - 1) // cols)

    gap_x = Inches(0.18 if cols <= 3 else 0.14)
    gap_y = Inches(0.16)
    card_w = to_emu((bw - (gap_x * (cols - 1))) / cols)
    card_h = to_emu((bh - (gap_y * (rows - 1))) / rows)
    default_top_stripes = bool(cfg.get("show_top_stripes", False))
    show_numbers = bool(cfg.get("show_numbers", cfg.get("numbered", False)))

    for idx, itm in enumerate(raw_items):
        r = idx // cols
        c = idx % cols
        cx = to_emu(bx + c * (card_w + gap_x))
        cy = to_emu(by + r * (card_h + gap_y))

        if isinstance(itm, dict):
            title = str(itm.get("title", "")).strip()
            subtitle = str(itm.get("subtitle", "")).strip()
            desc = str(itm.get("description") or itm.get("body") or "").strip()
            bullets = itm.get("bullets", [])
            accent_key = itm.get("accent_key", "accent")
            num_val = itm.get("number", itm.get("index"))
            is_focal = bool(itm.get("is_focal") or itm.get("highlight") or itm.get("is_primary"))
            use_stripe = bool(itm.get("has_top_stripe", default_top_stripes))
        else:
            title = str(getattr(itm, "title", str(itm))).strip()
            subtitle = str(getattr(itm, "subtitle", "") or "").strip()
            desc = str(getattr(itm, "description", "") or "").strip()
            bullets = getattr(itm, "bullets", [])
            accent_key = getattr(itm, "accent_key", "accent")
            num_val = getattr(itm, "number", None)
            is_focal = bool(getattr(itm, "is_focal", False))
            use_stripe = bool(getattr(itm, "has_top_stripe", default_top_stripes))

        accent_rgb = _resolve_widget_color(theme, accent_key)
        card_bg = hex_to_rgb("#F0F9FF") if is_focal else theme.get_rgb("surface")
        card_border = accent_rgb if is_focal else theme.get_rgb("border")
        border_w = 1.5 if is_focal else 1.0

        if use_stripe:
            add_card_with_top_stripe(
                slide=slide,
                theme=theme,
                left=cx,
                top=cy,
                width=card_w,
                height=card_h,
                accent_rgb=accent_rgb,
                bg_color=card_bg,
                border_color=card_border,
                border_width_pt=border_w,
                stripe_height_in=0.04,
            )
        else:
            add_card(
                slide=slide,
                theme=theme,
                left=cx,
                top=cy,
                width=card_w,
                height=card_h,
                bg_color=card_bg,
                border_color=card_border,
                border_width_pt=border_w,
                force_rectangle=True,
            )

        pad_x = Inches(0.16)
        pad_y = Inches(0.14 if rows == 1 else 0.11)
        has_num = show_numbers or (num_val is not None)
        num_str = str(num_val if num_val is not None else (idx + 1))

        if has_num:
            badge_d = Inches(0.32)
            circ = slide.shapes.add_shape(
                MSO_SHAPE.OVAL,
                to_emu(cx + pad_x),
                to_emu(cy + pad_y),
                badge_d,
                badge_d,
            )
            circ.shadow.inherit = False
            strip_shape_shadows(circ)
            circ.fill.solid()
            circ.fill.fore_color.rgb = accent_rgb if is_focal else theme.get_rgb("primary")
            circ.line.fill.background()
            tf_c = circ.text_frame
            tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0
            pc = tf_c.paragraphs[0]
            pc.text = num_str
            pc.alignment = PP_ALIGN.CENTER
            pc.font.name = theme.font_family_header
            pc.font.size = Pt(10.0)
            pc.font.bold = True
            pc.font.color.rgb = RGBColor(255, 255, 255)

            title_x = to_emu(cx + pad_x + badge_d + Inches(0.10))
            title_w = to_emu(card_w - pad_x * 2 - badge_d - Inches(0.10))
            title_h = Inches(0.46)
            tb_t = slide.shapes.add_textbox(title_x, to_emu(cy + pad_y - Inches(0.02)), title_w, title_h)
            tf_t = tb_t.text_frame
            tf_t.word_wrap = True
            tf_t.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
            p_t = tf_t.paragraphs[0]
            p_t.text = title
            p_t.font.name = theme.font_family_header
            p_t.font.size = Pt(11.5 if rows == 1 else 10.5)
            p_t.font.bold = True
            p_t.font.color.rgb = theme.get_rgb("primary")

            body_top = to_emu(cy + pad_y + title_h + Inches(0.06))
            body_h = to_emu(max(Inches(0.30), (cy + card_h - pad_y) - body_top))
            tb = slide.shapes.add_textbox(to_emu(cx + pad_x), body_top, to_emu(card_w - pad_x * 2), body_h)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            first_para = True
        else:
            tb = slide.shapes.add_textbox(to_emu(cx + pad_x), to_emu(cy + pad_y), to_emu(card_w - pad_x * 2), to_emu(card_h - pad_y * 2))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            p_t = tf.paragraphs[0]
            p_t.text = title
            p_t.font.name = theme.font_family_header
            p_t.font.size = Pt(11.5 if rows == 1 else 11.0)
            p_t.font.bold = True
            p_t.font.color.rgb = theme.get_rgb("primary")
            first_para = False

        if subtitle:
            p_sub = tf.paragraphs[0] if first_para else tf.add_paragraph()
            if not first_para:
                p_sub.space_before = Pt(3)
            first_para = False
            p_sub.text = subtitle
            p_sub.font.name = theme.font_family
            p_sub.font.size = Pt(9.0)
            p_sub.font.color.rgb = theme.get_rgb("muted")

        body_pt = 10.0 if rows == 1 else 9.0
        if bullets:
            for b_idx, b in enumerate(bounded_slice(bullets, 2, "composable_hero_card", "bullets")):
                p_b = tf.paragraphs[0] if first_para else tf.add_paragraph()
                if not first_para:
                    p_b.space_before = Pt(5.0 if b_idx > 0 else 4.0)
                first_para = False
                p_b.space_after = Pt(2.0)
                append_formatted_runs(
                    paragraph=p_b,
                    text=f"•  {b}",
                    font_name=theme.font_family,
                    font_size_pt=body_pt,
                    font_color=theme.get_rgb("secondary"),
                    lead_color=theme.get_rgb("primary"),
                    auto_colon_lead=True,
                )
        elif desc:
            p_d = tf.paragraphs[0] if first_para else tf.add_paragraph()
            if not first_para:
                p_d.space_before = Pt(6.0 if rows == 1 else 4.0)
            append_formatted_runs(
                paragraph=p_d,
                text=desc,
                font_name=theme.font_family,
                font_size_pt=body_pt,
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
    axis_pt = max(8.0, float(cfg.get("axis_font_size_pt", 9.0)))
    cat_axis = chart.category_axis
    cat_axis.has_major_gridlines = False
    cat_axis.tick_labels.font.name = theme.font_family
    cat_axis.tick_labels.font.size = Pt(axis_pt)
    cat_axis.tick_labels.font.bold = True
    cat_axis.tick_labels.font.color.rgb = theme.get_rgb("primary")
    if xl_type == XL_CHART_TYPE.BAR_CLUSTERED and cfg.get("reverse_categories", True):
        cat_axis.reverse_order = True

    # Value axis formatting
    val_axis = chart.value_axis
    val_axis.has_major_gridlines = bool(cfg.get("show_gridlines", False))
    if val_axis.has_major_gridlines:
        try:
            val_axis.major_gridlines.format.line.color.rgb = theme.get_rgb("border")
            val_axis.major_gridlines.format.line.width = Pt(0.75)
        except Exception:
            pass
    val_axis.visible = bool(cfg.get("show_value_axis", False))
    if val_axis.visible:
        val_axis.tick_labels.font.name = theme.font_family
        val_axis.tick_labels.font.size = Pt(max(8.0, axis_pt - 0.5))
        val_axis.tick_labels.font.color.rgb = theme.get_rgb("muted")
    if cfg.get("min_scale") is not None:
        val_axis.minimum_scale = float(cfg["min_scale"])
    if cfg.get("max_scale") is not None:
        val_axis.maximum_scale = float(cfg["max_scale"])
    if cfg.get("number_format"):
        val_axis.tick_labels.number_format = str(cfg["number_format"])

    # Series colors and direct data labels
    plot = chart.plots[0]
    default_gap = 105 if len(series_defs) >= 3 else 75
    plot.gap_width = int(cfg.get("gap_width", default_gap))
    show_labels = bool(cfg.get("show_data_labels", True))
    plot.has_data_labels = show_labels
    if show_labels:
        dlabels = plot.data_labels
        dlabels.position = XL_LABEL_POSITION.OUTSIDE_END
        dlabels.font.name = theme.font_family_header
        default_dl_pt = 8.5 if len(series_defs) >= 3 else 9.5
        dlabels.font.size = Pt(max(8.0, float(cfg.get("data_label_size_pt", default_dl_pt))))
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
    strip_shape_shadows(hdr)
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
                strip_shape_shadows(v_div)
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
            pm2.font.size = Pt(8.0)
            pm2.font.bold = True
            pm2.font.color.rgb = theme.get_rgb("muted_text")

        # Bottom hairline separator before code well
        h_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, to_emu(bx + Inches(0.12)), to_emu(curr_y + met_h), to_emu(bw - Inches(0.24)), Pt(0.75))
        h_div.shadow.inherit = False
        strip_shape_shadows(h_div)
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
    strip_shape_shadows(code_well)
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
            strip_shape_shadows(div)
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


def _format_exhibit_number(value: float, prefix: str = "", suffix: str = "") -> str:
    """Format a compact numeric label for stacked column exhibits."""
    abs_val = abs(value)
    if abs_val >= 100 or abs_val == int(abs_val):
        num_str = f"{abs_val:,.0f}"
    else:
        num_str = f"{abs_val:,.1f}".rstrip("0").rstrip(".")
    sign = "-" if value < 0 else ""
    return f"{sign}{prefix}{num_str}{suffix}"


def render_stacked_column_exhibit_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
) -> None:
    """
    Renders an MBB-style vector stacked column exhibit inside a clean surface card container,
    supporting direct segment labels, bold column totals, horizontal legend, optional
    top-right callout badge, and an optional right-side CAGR/YoY summary column.
    """
    bx, by, bw, bh = box
    title = str(cfg.get("title", "")).strip()
    subtitle = str(cfg.get("subtitle", "")).strip()
    footnote = str(cfg.get("footnote", "")).strip()
    callout_badge = str(cfg.get("callout_badge") or cfg.get("badge") or "").strip()

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
    bw_in = float(bw) / 914400.0
    bx_in = float(bx) / 914400.0
    by_in = float(by) / 914400.0
    bh_in = float(bh) / 914400.0

    if title:
        hdr_h = Inches(0.46) if subtitle else Inches(0.28)
        badge_reserve = Inches(1.25) if callout_badge else Inches(0.0)
        tb = slide.shapes.add_textbox(
            to_emu(bx + pad_x), to_emu(curr_y), to_emu(bw - pad_x * 2 - badge_reserve), to_emu(hdr_h)
        )
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
        if callout_badge:
            _add_status_pill(
                slide,
                theme,
                to_emu(bx + bw - pad_x - Inches(1.18)),
                to_emu(curr_y),
                Inches(1.18),
                Inches(0.24),
                callout_badge,
                font_size_pt=8.0,
                override_color_key=str(cfg.get("badge_color", "accent")),
            )
        curr_y = curr_y + hdr_h + Inches(0.06)

    categories = [str(c) for c in (cfg.get("categories") or [])]
    raw_series = list(cfg.get("series") or [])
    if not categories or not raw_series:
        return

    default_palette = ["primary", "accent", "accent_secondary", "muted", "snowblue", "amber"]
    series_defs: List[Dict[str, Any]] = []
    for s_idx, s_raw in enumerate(raw_series):
        if not isinstance(s_raw, dict):
            continue
        col_spec = s_raw.get("color") or default_palette[s_idx % len(default_palette)]
        series_defs.append({
            "name": str(s_raw.get("name") or f"Series {s_idx + 1}"),
            "values": [max(0.0, float(v)) for v in (s_raw.get("values") or [])],
            "color": resolve_accent_color(col_spec, theme, "accent"),
        })
    if not series_defs:
        return

    curr_y_in = float(curr_y) / 914400.0
    show_legend = bool(cfg.get("show_legend", len(series_defs) > 1))
    if show_legend:
        lx_in = bx_in + 0.20
        for s_def in series_defs:
            sw = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(lx_in),
                Inches(curr_y_in + 0.04),
                Inches(0.11),
                Inches(0.11),
            )
            sw.shadow.inherit = False
            strip_shape_shadows(sw)
            sw.fill.solid()
            sw.fill.fore_color.rgb = s_def["color"]
            sw.line.fill.background()

            lbl_w = min(1.55, max(0.70, len(s_def["name"]) * 0.075 + 0.22))
            if lx_in + 0.16 + lbl_w > bx_in + bw_in - 0.18:
                break
            tb_l = slide.shapes.add_textbox(
                Inches(lx_in + 0.16), Inches(curr_y_in), Inches(lbl_w), Inches(0.20)
            )
            tf_l = tb_l.text_frame
            tf_l.word_wrap = False
            tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0
            p_l = tf_l.paragraphs[0]
            p_l.text = s_def["name"]
            p_l.font.name = theme.font_family
            p_l.font.size = Pt(8.5)
            p_l.font.color.rgb = theme.get_rgb("secondary")
            lx_in += 0.16 + lbl_w + 0.14
        curr_y_in += 0.28

    foot_h_in = 0.26 if footnote else 0.12
    cagr_cfg = cfg.get("cagr_column")
    has_cagr = isinstance(cagr_cfg, dict) and bool(cagr_cfg.get("values") or cagr_cfg.get("total_value"))
    cagr_w_in = 1.05 if has_cagr else 0.0

    plot_left_in = bx_in + 0.20
    plot_w_in = max(1.20, bw_in - 0.40 - cagr_w_in)
    plot_top_in = curr_y_in + 0.24  # reserve headroom for column total labels
    plot_bottom_in = by_in + bh_in - foot_h_in - 0.34
    plot_h_in = max(0.80, plot_bottom_in - plot_top_in)

    n_cats = len(categories)
    col_totals = [
        sum(s["values"][c_i] if c_i < len(s["values"]) else 0.0 for s in series_defs)
        for c_i in range(n_cats)
    ]
    max_total = max(col_totals) if col_totals else 1.0
    if max_total <= 1e-9:
        max_total = 1.0
    scale_max = max_total * 1.15

    unit = str(cfg.get("unit") or "")
    eff_prefix = str(cfg.get("value_prefix") or (unit if unit in ("$", "€", "£") else ""))
    eff_suffix = str(cfg.get("value_suffix") or ("" if unit in ("$", "€", "£") else unit))
    show_totals = bool(cfg.get("show_totals", True))
    show_segment_labels = bool(cfg.get("show_segment_labels", True))

    draw_hairline(
        slide,
        Inches(plot_left_in),
        Inches(plot_bottom_in),
        Inches(plot_w_in),
        theme.get_rgb("border"),
        width_pt=1.0,
    )

    slot_w_in = plot_w_in / n_cats
    bar_w_in = min(0.95, slot_w_in * 0.58)
    surface_rgb = theme.get_rgb("surface")

    for c_i, cat in enumerate(categories):
        slot_x_in = plot_left_in + c_i * slot_w_in
        bar_x_in = slot_x_in + (slot_w_in - bar_w_in) / 2.0
        cum_val = 0.0

        for s_def in series_defs:
            v = s_def["values"][c_i] if c_i < len(s_def["values"]) else 0.0
            if v <= 0.0:
                continue
            seg_h_in = (v / scale_max) * plot_h_in
            seg_top_in = plot_bottom_in - ((cum_val + v) / scale_max) * plot_h_in
            cum_val += v

            seg = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(bar_x_in),
                Inches(seg_top_in),
                Inches(bar_w_in),
                Inches(max(0.03, seg_h_in)),
            )
            seg.shadow.inherit = False
            strip_shape_shadows(seg)
            seg.fill.solid()
            seg.fill.fore_color.rgb = s_def["color"]
            seg.line.color.rgb = surface_rgb
            seg.line.width = Pt(0.5)

            if show_segment_labels and seg_h_in >= 0.22:
                tf_seg = seg.text_frame
                tf_seg.word_wrap = False
                tf_seg.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf_seg.margin_left = tf_seg.margin_right = tf_seg.margin_top = tf_seg.margin_bottom = 0
                p_seg = tf_seg.paragraphs[0]
                p_seg.text = _format_exhibit_number(v, prefix=eff_prefix, suffix=eff_suffix)
                p_seg.alignment = PP_ALIGN.CENTER
                p_seg.font.name = theme.font_family_header
                p_seg.font.size = Pt(8.5)
                p_seg.font.bold = True
                p_seg.font.color.rgb = _get_contrast_text_color(s_def["color"])

        top_of_bar_in = plot_bottom_in - (col_totals[c_i] / scale_max) * plot_h_in
        if show_totals:
            tb_tot = slide.shapes.add_textbox(
                Inches(slot_x_in),
                Inches(max(curr_y_in, top_of_bar_in - 0.22)),
                Inches(slot_w_in),
                Inches(0.20),
            )
            tf_tot = tb_tot.text_frame
            tf_tot.word_wrap = False
            tf_tot.margin_left = tf_tot.margin_right = tf_tot.margin_top = tf_tot.margin_bottom = 0
            p_tot = tf_tot.paragraphs[0]
            p_tot.text = _format_exhibit_number(col_totals[c_i], prefix=eff_prefix, suffix=eff_suffix)
            p_tot.alignment = PP_ALIGN.CENTER
            p_tot.font.name = theme.font_family_header
            p_tot.font.size = Pt(9.5)
            p_tot.font.bold = True
            p_tot.font.color.rgb = theme.get_rgb("primary")

        tb_cat = slide.shapes.add_textbox(
            Inches(slot_x_in + 0.02),
            Inches(plot_bottom_in + 0.05),
            Inches(slot_w_in - 0.04),
            Inches(0.26),
        )
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = cat
        p_cat.alignment = PP_ALIGN.CENTER
        p_cat.font.name = theme.font_family_header
        p_cat.font.size = Pt(8.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = theme.get_rgb("primary")

    if has_cagr and isinstance(cagr_cfg, dict):
        cagr_x_in = plot_left_in + plot_w_in + 0.14
        cagr_box_w_in = cagr_w_in - 0.14
        # Vertical divider hairline
        v_sep = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(cagr_x_in - 0.07),
            Inches(plot_top_in - 0.16),
            Pt(0.75),
            Inches(plot_bottom_in - plot_top_in + 0.16),
        )
        v_sep.shadow.inherit = False
        strip_shape_shadows(v_sep)
        v_sep.fill.solid()
        v_sep.fill.fore_color.rgb = theme.get_rgb("border")
        v_sep.line.fill.background()

        c_hdr = str(cagr_cfg.get("header") or "CAGR").strip()
        tb_ch = slide.shapes.add_textbox(
            Inches(cagr_x_in), Inches(plot_top_in - 0.18), Inches(cagr_box_w_in), Inches(0.32)
        )
        tf_ch = tb_ch.text_frame
        tf_ch.word_wrap = True
        tf_ch.margin_left = tf_ch.margin_right = tf_ch.margin_top = tf_ch.margin_bottom = 0
        p_ch = tf_ch.paragraphs[0]
        p_ch.text = c_hdr
        p_ch.alignment = PP_ALIGN.CENTER
        p_ch.font.name = theme.font_family_header
        p_ch.font.size = Pt(8.5)
        p_ch.font.bold = True
        p_ch.font.color.rgb = theme.get_rgb("muted_text")

        cagr_vals = list(cagr_cfg.get("values") or [])
        total_val = str(cagr_cfg.get("total_value") or "").strip()
        row_items = ([(total_val, True)] if total_val else []) + [(str(v), False) for v in cagr_vals]
        row_y = plot_top_in + 0.22
        row_step = min(0.42, max(0.28, (plot_bottom_in - row_y) / max(1, len(row_items))))
        for r_txt, is_tot in row_items:
            tb_r = slide.shapes.add_textbox(
                Inches(cagr_x_in), Inches(row_y), Inches(cagr_box_w_in), Inches(0.24)
            )
            tf_r = tb_r.text_frame
            tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0
            p_r = tf_r.paragraphs[0]
            p_r.text = r_txt
            p_r.alignment = PP_ALIGN.CENTER
            p_r.font.name = theme.font_family_header
            p_r.font.size = Pt(10.0 if is_tot else 9.0)
            p_r.font.bold = True
            p_r.font.color.rgb = theme.get_rgb("accent" if is_tot else "primary")
            row_y += row_step

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


def render_stack_widget(
    slide: Any,
    theme: Theme,
    box: Tuple[Inches, Inches, Inches, Inches],
    cfg: Dict[str, Any],
    _depth: int = 0,
) -> None:
    """
    Recursively partitions a pane bounding box vertically or horizontally into child widgets.
    Supports nested layouts such as chart-left + (table-top / hero_kpi-bottom) right.
    """
    if _depth >= 4:
        logger.warning("Maximum stack nesting depth reached; skipping nested children.")
        return

    bx, by, bw, bh = box
    children = cfg.get("panes") or cfg.get("rows") or cfg.get("items") or cfg.get("children") or []
    if not isinstance(children, list) or not children:
        return

    w_name = str(cfg.get("widget", "vertical_stack")).lower().strip()
    default_dir = "horizontal" if w_name in ("horizontal_stack", "columns", "row") else "vertical"
    direction = str(cfg.get("direction", default_dir)).lower().strip()
    gap_in = float(cfg.get("gap", 0.18 if direction == "vertical" else 0.24))

    fractions = parse_split_fractions(cfg.get("split"), len(children))
    if direction == "horizontal":
        child_boxes = compute_pane_bounding_boxes(bx, by, bw, bh, fractions, Inches(gap_in))
    else:
        child_boxes = compute_vertical_pane_bounding_boxes(bx, by, bw, bh, fractions, Inches(gap_in))

    for c_idx, child_cfg in enumerate(children):
        if not isinstance(child_cfg, dict):
            continue
        c_box = child_boxes[c_idx]
        c_type = str(child_cfg.get("widget", "card_list")).lower().strip()
        if c_type in ("stack", "vertical_stack", "rows", "horizontal_stack", "columns"):
            render_stack_widget(slide, theme, c_box, child_cfg, _depth=_depth + 1)
        else:
            dispatcher = WIDGET_DISPATCHERS.get(c_type, render_card_list_widget)
            dispatcher(slide, theme, c_box, child_cfg)


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
    "process_flow": render_process_steps_widget,
    "decision_flow": render_process_steps_widget,
    "steps": render_process_steps_widget,
    "flow_steps": render_process_steps_widget,
    "card_grid": render_card_grid_widget,
    "grid": render_card_grid_widget,
    "native_chart": render_native_chart_widget,
    "bar_chart": render_native_chart_widget,
    "column_chart": render_native_chart_widget,
    "chart": render_native_chart_widget,
    "stacked_column_exhibit": render_stacked_column_exhibit_widget,
    "stacked_column": render_stacked_column_exhibit_widget,
    "stacked_bar_exhibit": render_stacked_column_exhibit_widget,
    "code_block": render_code_block_widget,
    "sql_panel": render_code_block_widget,
    "sql": render_code_block_widget,
    "image": render_image_widget,
    "png": render_image_widget,
    "stack": render_stack_widget,
    "vertical_stack": render_stack_widget,
    "rows": render_stack_widget,
    "horizontal_stack": render_stack_widget,
    "columns": render_stack_widget,
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
        strip_shape_shadows(bar)
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
    tracker: Optional[str] = None,
    action_title: str = "Composable Multi-Widget Layout Solves Asymmetric Presentation Needs Without Raw DrawingML Math",
    subtitle: Optional[str] = None,
    split: Optional[Union[List[Union[int, float]], str]] = None,
    panes: Optional[List[Dict[str, Any]]] = None,
    rows: Optional[List[Dict[str, Any]]] = None,
    direction: str = "horizontal",
    top_kpis: Optional[List[Dict[str, Any]]] = None,
    gap: Optional[float] = None,
    pane_divider: bool = False,
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    Renders a composable multi-widget presentation slide:
      - Optionally renders a horizontal Big Number `top_kpis` banner at top.
      - Automatically partitions remaining canvas horizontally (`direction='horizontal'`) or
        vertically (`direction='vertical'` or `rows=[...]`) based on `split`.
      - Renders modular child widgets (native_chart, code_block, image, hero_kpi, card_list,
        table, process_steps, card_grid, vertical_stack, etc.) inside each calculated pane.
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    # Content Area Geometry
    content_left = Inches(0.80)
    content_top = resolve_content_top(header_bottom, gap_in=0.20)
    content_width = Inches(11.733)

    if top_kpis and isinstance(top_kpis, list):
        kpi_h = Inches(0.96)
        _render_top_kpi_strip(slide, theme, top_kpis, content_left, content_top, content_width, kpi_h)
        content_top = content_top + kpi_h + Inches(0.14)

    # Calculate content height based on takeaway / footnote presence and top KPI strip offset
    foot_reserve = Inches(0.32) if footnote else Inches(0.0)
    if takeaway:
        is_two_row = isinstance(takeaway, dict) and bool(takeaway.get("title") and takeaway.get("description"))
        bottom_limit = (Inches(5.45) if is_two_row else Inches(6.15)) - foot_reserve
    else:
        bottom_limit = Inches(6.85) - foot_reserve
    content_height = to_emu(bottom_limit - content_top)

    effective_dir = str(direction or "horizontal").lower().strip()
    if rows is not None and not panes:
        panes = rows
        effective_dir = "vertical"

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

    resolved_gap = float(gap) if gap is not None else (0.22 if effective_dir == "vertical" else 0.35)

    # Calculate bounding boxes
    fractions = parse_split_fractions(split, len(panes))
    if effective_dir == "vertical":
        boxes = compute_vertical_pane_bounding_boxes(
            content_left=content_left,
            content_top=content_top,
            content_width=content_width,
            content_height=content_height,
            fractions=fractions,
            gap=Inches(resolved_gap),
        )
    else:
        boxes = compute_pane_bounding_boxes(
            content_left=content_left,
            content_top=content_top,
            content_width=content_width,
            content_height=content_height,
            fractions=fractions,
            gap=Inches(resolved_gap),
        )

    # Render each pane
    for p_idx, pane_cfg in enumerate(panes):
        box = boxes[p_idx]
        widget_type = str(pane_cfg.get("widget", "card_list")).lower().strip()
        dispatcher = WIDGET_DISPATCHERS.get(widget_type, render_card_list_widget)
        try:
            dispatcher(slide, theme, box, pane_cfg)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to render pane {p_idx} widget '{widget_type}': {e}", exc_info=True)

    # Optional hairline separator centered in the gutter between adjacent panes
    if pane_divider and len(boxes) > 1:
        border_rgb = theme.get_rgb("border")
        for i in range(len(boxes) - 1):
            b_a = boxes[i]
            b_b = boxes[i + 1]
            if effective_dir == "vertical":
                div_y = to_emu((b_a[1] + b_a[3] + b_b[1]) / 2 - Pt(0.5))
                sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, content_left, div_y, content_width, Pt(1.0))
            else:
                div_x = to_emu((b_a[0] + b_a[2] + b_b[0]) / 2 - Pt(0.5))
                sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, div_x, content_top, Pt(1.0), content_height)
            sep.shadow.inherit = False
            strip_shape_shadows(sep)
            sep.fill.solid()
            sep.fill.fore_color.rgb = border_rgb
            sep.line.fill.background()

    if footnote:
        foot_y = Inches(6.62) if not takeaway else Inches(6.02)
        tb_fn = slide.shapes.add_textbox(content_left, foot_y, content_width, Inches(0.28))
        tf_fn = tb_fn.text_frame
        tf_fn.word_wrap = True
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        p_fn = tf_fn.paragraphs[0]
        p_fn.text = str(footnote).strip()
        p_fn.font.name = theme.font_family
        p_fn.font.size = Pt(8.5)
        p_fn.font.color.rgb = theme.get_rgb("muted")

    # Takeaway Bar
    if takeaway:
        add_takeaway_bar(slide, theme, takeaway=takeaway)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


def build_process_with_cards_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Sequenced Process Flow Anchors Operational Execution",
    subtitle: Optional[str] = None,
    steps: Optional[List[Dict[str, Any]]] = None,
    branch: Optional[Dict[str, Any]] = None,
    caption: Optional[str] = None,
    cards: Optional[List[Dict[str, Any]]] = None,
    columns: int = 3,
    show_numbers: bool = False,
    show_top_stripes: bool = False,
    split: Optional[Union[List[Union[int, float]], str]] = None,
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    Top-to-bottom split slide pairing a horizontal process/decision flow on top
    with a structured multi-card strip underneath.
    """
    flow_cfg: Dict[str, Any] = {
        "widget": "process_flow",
        "direction": "horizontal",
        "show_connectors": True,
        "steps": steps or [],
    }
    if branch:
        flow_cfg["branch"] = branch
    if caption:
        flow_cfg["caption"] = caption

    card_items = cards or []
    cards_cfg: Dict[str, Any] = {
        "widget": "card_grid",
        "columns": max(1, min(columns, len(card_items))) if card_items else columns,
        "show_numbers": show_numbers,
        "show_top_stripes": show_top_stripes,
        "items": card_items,
    }

    return build_composable_split_slide(
        prs=prs,
        theme=theme,
        tracker=tracker,
        action_title=action_title,
        subtitle=subtitle,
        direction="vertical",
        split=split or [38, 62],
        gap=0.22,
        rows=[flow_cfg, cards_cfg],
        takeaway=takeaway,
        footnote=footnote,
        current_idx=current_idx,
        total_slides=total_slides,
        notice=notice,
        source=source,
    )


def _format_count(val: Union[int, float, str]) -> str:
    """Format integer or numeric counts cleanly with thousand separators."""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, int) or (isinstance(val, float) and val.is_integer()):
        return f"{int(val):,}"
    return f"{val:,.1f}"


def build_cohort_funnel_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Ordered Exclusions Distill Raw Records into the Final Modeling Cohort",
    subtitle: Optional[str] = None,
    source_count: Union[int, float, str] = 100000,
    source_label: str = "Total source records",
    exclusions_caption: Optional[str] = None,
    exclusions: Optional[List[Dict[str, Any]]] = None,
    final_count: Union[int, float, str] = 20000,
    final_label: str = "Final modeling cohort",
    definition_cards: Optional[List[Dict[str, Any]]] = None,
    split_segments: Optional[List[Dict[str, Any]]] = None,
    split_caption: Optional[str] = None,
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    Renders a Cohort Attrition Funnel & Split Architecture slide:
      - Left pane (~58%): Source total -> horizontal ordered attrition bars -> final cohort anchor.
      - Right pane (~42%): Stacked unit/target definition cards.
      - Bottom full-width strip (opt-in): Temporal or stratified Train / Validation / Test split bar.
    """
    slide = add_slide_with_background(prs, theme)
    header_bottom = add_slide_header(slide, theme, tracker=tracker, action_title=action_title, subtitle=subtitle)

    content_left = Inches(0.80)
    content_top = resolve_content_top(header_bottom, gap_in=0.18)
    content_w = Inches(11.733)

    bottom_limit = Inches(6.16) if takeaway else Inches(6.86)
    if footnote and not split_segments:
        bottom_limit -= Inches(0.28)

    has_split = bool(split_segments)
    split_total_h = Inches(0.92 if split_caption else 0.56) if has_split else Inches(0)
    split_gap = Inches(0.18) if has_split else Inches(0)
    top_area_h = to_emu(max(Inches(2.80), bottom_limit - content_top - split_total_h - split_gap))

    left_w = to_emu(content_w * 0.575)
    col_gap = Inches(0.28)
    right_x = to_emu(content_left + left_w + col_gap)
    right_w = to_emu(content_w - left_w - col_gap)

    # 1. Left Funnel Card Container
    add_card(
        slide,
        theme,
        content_left,
        content_top,
        left_w,
        top_area_h,
        bg_color=theme.get_rgb("surface"),
        border_color=theme.get_rgb("border"),
        force_rectangle=True,
    )

    f_pad_x = Inches(0.22)
    f_pad_y = Inches(0.16)
    f_inner_w = to_emu(left_w - f_pad_x * 2)
    curr_y = to_emu(content_top + f_pad_y)

    # Source Header Row
    try:
        src_num = float(str(source_count).replace(",", ""))
    except ValueError:
        src_num = 0.0

    src_h = Inches(0.34)
    tb_src = slide.shapes.add_textbox(to_emu(content_left + f_pad_x), curr_y, f_inner_w, src_h)
    tf_src = tb_src.text_frame
    tf_src.word_wrap = True
    tf_src.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_src.margin_left = tf_src.margin_right = tf_src.margin_top = tf_src.margin_bottom = 0
    p_src = tf_src.paragraphs[0]
    r_num = p_src.add_run()
    r_num.text = f"{_format_count(source_count)}  "
    r_num.font.name = theme.font_family_header
    r_num.font.size = Pt(14.5)
    r_num.font.bold = True
    r_num.font.color.rgb = theme.get_rgb("primary")

    r_lbl = p_src.add_run()
    r_lbl.text = str(source_label)
    r_lbl.font.name = theme.font_family_header
    r_lbl.font.size = Pt(11.0)
    r_lbl.font.bold = True
    r_lbl.font.color.rgb = theme.get_rgb("secondary")

    curr_y = to_emu(curr_y + src_h + Inches(0.06))
    draw_hairline(slide, to_emu(content_left + f_pad_x), curr_y, f_inner_w, theme.get_rgb("border"), width_pt=0.75)
    curr_y = to_emu(curr_y + Inches(0.08))

    if exclusions_caption:
        cap_h = Inches(0.24)
        tb_ec = slide.shapes.add_textbox(to_emu(content_left + f_pad_x), curr_y, f_inner_w, cap_h)
        tf_ec = tb_ec.text_frame
        tf_ec.word_wrap = True
        tf_ec.margin_left = tf_ec.margin_right = tf_ec.margin_top = tf_ec.margin_bottom = 0
        pec = tf_ec.paragraphs[0]
        pec.text = str(exclusions_caption).strip()
        pec.font.name = theme.font_family
        pec.font.size = Pt(8.5)
        pec.font.color.rgb = theme.get_rgb("muted")
        curr_y = to_emu(curr_y + cap_h + Inches(0.04))

    # Reserve bottom final cohort result bar
    res_h = Inches(0.46)
    res_y = to_emu(content_top + top_area_h - f_pad_y - res_h)
    ex_list = bounded_slice(exclusions or [], 8, "cohort_funnel", "exclusions")

    if ex_list:
        avail_ex_h = max(Inches(1.0), res_y - curr_y - Inches(0.10))
        row_h = min(Inches(0.44), to_emu(avail_ex_h / len(ex_list)))
        lbl_w = Inches(2.60)
        val_w = Inches(1.22)
        track_x = to_emu(content_left + f_pad_x + lbl_w + Inches(0.08))
        track_w = to_emu(max(Inches(1.0), f_inner_w - lbl_w - val_w - Inches(0.18)))
        val_x = to_emu(track_x + track_w + Inches(0.08))
        bar_h = min(Inches(0.22), to_emu(row_h * 0.56))
        row_pt = 8.5 if row_h < Inches(0.36) else 9.0

        for ex in ex_list:
            ex_dict = ex if isinstance(ex, dict) else {"label": str(ex), "count": 0}
            ex_lbl = str(ex_dict.get("label") or "").strip()
            ex_cnt_raw = ex_dict.get("count", ex_dict.get("removed", 0))
            try:
                ex_cnt = float(str(ex_cnt_raw).replace(",", ""))
            except ValueError:
                ex_cnt = 0.0
            ratio = (ex_cnt / src_num) if src_num > 0 else 0.0
            pct_str = str(ex_dict.get("pct") or (f"({ratio * 100:.1f}%)" if src_num > 0 else ""))
            bar_rgb = _resolve_widget_color(theme, ex_dict.get("accent_key", "accent"))

            tb_l = slide.shapes.add_textbox(to_emu(content_left + f_pad_x), curr_y, lbl_w, row_h)
            tf_l = tb_l.text_frame
            tf_l.word_wrap = True
            tf_l.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0
            pl = tf_l.paragraphs[0]
            pl.text = ex_lbl
            pl.font.name = theme.font_family
            pl.font.size = Pt(row_pt)
            pl.font.color.rgb = theme.get_rgb("secondary")

            bar_y = to_emu(curr_y + (row_h - bar_h) / 2)
            track = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, track_x, bar_y, track_w, bar_h)
            track.shadow.inherit = False
            strip_shape_shadows(track)
            track.fill.solid()
            track.fill.fore_color.rgb = theme.get_rgb("surface_muted")
            track.line.fill.background()

            fill_w = to_emu(max(Inches(0.06), min(track_w, track_w * ratio)))
            f_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, track_x, bar_y, fill_w, bar_h)
            f_bar.shadow.inherit = False
            strip_shape_shadows(f_bar)
            f_bar.fill.solid()
            f_bar.fill.fore_color.rgb = bar_rgb
            f_bar.line.fill.background()

            tb_v = slide.shapes.add_textbox(val_x, curr_y, val_w, row_h)
            tf_v = tb_v.text_frame
            tf_v.word_wrap = True
            tf_v.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_v.margin_left = tf_v.margin_right = tf_v.margin_top = tf_v.margin_bottom = 0
            pv = tf_v.paragraphs[0]
            pv.alignment = PP_ALIGN.RIGHT
            rv1 = pv.add_run()
            rv1.text = f"-{_format_count(ex_cnt_raw)}"
            rv1.font.name = theme.font_family_header
            rv1.font.size = Pt(9.0)
            rv1.font.bold = True
            rv1.font.color.rgb = theme.get_rgb("primary")
            if pct_str:
                rv2 = pv.add_run()
                rv2.text = f" {pct_str}"
                rv2.font.name = theme.font_family
                rv2.font.size = Pt(8.0)
                rv2.font.color.rgb = theme.get_rgb("muted")

            curr_y = to_emu(curr_y + row_h)

    # Final Cohort Result Focal Bar
    res_box = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        to_emu(content_left + f_pad_x),
        res_y,
        f_inner_w,
        res_h,
    )
    res_box.shadow.inherit = False
    strip_shape_shadows(res_box)
    res_box.fill.solid()
    res_box.fill.fore_color.rgb = theme.get_rgb("primary")
    res_box.line.fill.background()

    try:
        fin_num = float(str(final_count).replace(",", ""))
        fin_pct = f"  ({(fin_num / src_num) * 100:.1f}% retained)" if src_num > 0 else ""
    except ValueError:
        fin_pct = ""

    tb_res = slide.shapes.add_textbox(to_emu(content_left + f_pad_x + Inches(0.14)), res_y, to_emu(f_inner_w - Inches(0.28)), res_h)
    tf_res = tb_res.text_frame
    tf_res.word_wrap = True
    tf_res.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_res.margin_left = tf_res.margin_right = tf_res.margin_top = tf_res.margin_bottom = 0
    pres = tf_res.paragraphs[0]
    r_fn = pres.add_run()
    r_fn.text = f"{_format_count(final_count)}  "
    r_fn.font.name = theme.font_family_header
    r_fn.font.size = Pt(13.0)
    r_fn.font.bold = True
    r_fn.font.color.rgb = RGBColor(255, 255, 255)

    r_fl = pres.add_run()
    r_fl.text = f"{final_label}{fin_pct}"
    r_fl.font.name = theme.font_family_header
    r_fl.font.size = Pt(10.0)
    r_fl.font.bold = True
    r_fl.font.color.rgb = hex_to_rgb("#BAE6FD")

    # 2. Right Definition Cards
    cards = bounded_slice(definition_cards or [], 3, "cohort_funnel", "definition_cards")
    if cards:
        c_gap = Inches(0.18)
        c_h = to_emu((top_area_h - c_gap * (len(cards) - 1)) / len(cards))
        for c_idx, c_item in enumerate(cards):
            cy = to_emu(content_top + c_idx * (c_h + c_gap))
            c_dict = c_item if isinstance(c_item, dict) else {"title": str(c_item)}
            acc_key = c_dict.get("accent_key", "warning" if c_idx == 1 else "accent")
            acc_rgb = _resolve_widget_color(theme, acc_key)

            add_card(
                slide,
                theme,
                right_x,
                cy,
                right_w,
                c_h,
                bg_color=theme.get_rgb("surface"),
                border_color=theme.get_rgb("border"),
                force_rectangle=True,
            )
            l_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x, cy, Pt(3.5), c_h)
            l_stripe.shadow.inherit = False
            strip_shape_shadows(l_stripe)
            l_stripe.fill.solid()
            l_stripe.fill.fore_color.rgb = acc_rgb
            l_stripe.line.fill.background()

            tb_c = slide.shapes.add_textbox(
                to_emu(right_x + Inches(0.20)),
                to_emu(cy + Inches(0.14)),
                to_emu(right_w - Inches(0.36)),
                to_emu(c_h - Inches(0.28)),
            )
            tf_c = tb_c.text_frame
            tf_c.word_wrap = True
            tf_c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0

            pc_t = tf_c.paragraphs[0]
            pc_t.text = str(c_dict.get("title") or "").strip()
            pc_t.font.name = theme.font_family_header
            pc_t.font.size = Pt(12.0)
            pc_t.font.bold = True
            pc_t.font.color.rgb = theme.get_rgb("primary")

            c_bullets = c_dict.get("bullets") or []
            c_desc = str(c_dict.get("description") or c_dict.get("body") or "").strip()
            if c_bullets and isinstance(c_bullets, list):
                for b_text in c_bullets[:2]:
                    pb = tf_c.add_paragraph()
                    pb.space_before = Pt(6)
                    append_formatted_runs(
                        paragraph=pb,
                        text=f"•  {b_text}",
                        font_name=theme.font_family,
                        font_size_pt=10.0,
                        font_color=theme.get_rgb("secondary"),
                        lead_color=theme.get_rgb("primary"),
                        auto_colon_lead=True,
                    )
            elif c_desc:
                pd = tf_c.add_paragraph()
                pd.space_before = Pt(6)
                append_formatted_runs(
                    paragraph=pd,
                    text=c_desc,
                    font_name=theme.font_family,
                    font_size_pt=10.0,
                    font_color=theme.get_rgb("secondary"),
                    lead_color=theme.get_rgb("primary"),
                    auto_colon_lead=True,
                )

    # 3. Bottom Temporal / Holdout Split Bar
    if has_split and split_segments:
        bar_top = to_emu(content_top + top_area_h + split_gap)
        bar_h = Inches(0.46)
        segs = list(split_segments)
        n_segs = len(segs)
        raw_vals: List[float] = []
        for s_item in segs:
            try:
                raw_vals.append(max(0.0, float(str(s_item.get("value", s_item.get("count", 1))).replace(",", ""))))
            except ValueError:
                raw_vals.append(1.0)
        tot_v = sum(raw_vals) or 1.0

        # Allocate minimum readable segment width so short splits never clip text
        min_seg_w = min(Inches(1.85), to_emu(content_w / max(1, n_segs) * 0.72))
        rem_w = max(Inches(0), content_w - min_seg_w * n_segs)
        seg_widths = [to_emu(min_seg_w + rem_w * (v / tot_v)) for v in raw_vals]
        # Snap last segment to exact right boundary
        if seg_widths:
            seg_widths[-1] = to_emu(content_w - sum(seg_widths[:-1]))

        default_seg_colors = ["primary", "accent", "warning", "slate"]
        cur_sx = content_left
        for s_idx, s_item in enumerate(segs):
            sw = seg_widths[s_idx]
            col_spec = s_item.get("color") or s_item.get("accent_key") or default_seg_colors[s_idx % len(default_seg_colors)]
            s_rgb = _resolve_widget_color(theme, col_spec)

            seg_shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cur_sx, bar_top, sw, bar_h)
            seg_shp.shadow.inherit = False
            strip_shape_shadows(seg_shp)
            seg_shp.fill.solid()
            seg_shp.fill.fore_color.rgb = s_rgb
            seg_shp.line.color.rgb = theme.get_rgb("background")
            seg_shp.line.width = Pt(1.0)

            s_lbl = str(s_item.get("label") or "").strip()
            s_disp = str(s_item.get("display") or (_format_count(s_item["count"]) if "count" in s_item else _format_count(s_item.get("value", ""))))
            txt_seg = f"{s_lbl}: {s_disp}" if (s_lbl and s_disp) else (s_lbl or s_disp)

            tb_seg = slide.shapes.add_textbox(to_emu(cur_sx + Inches(0.08)), bar_top, to_emu(sw - Inches(0.16)), bar_h)
            tf_seg = tb_seg.text_frame
            tf_seg.word_wrap = True
            tf_seg.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_seg.margin_left = tf_seg.margin_right = tf_seg.margin_top = tf_seg.margin_bottom = 0
            pseg = tf_seg.paragraphs[0]
            pseg.text = txt_seg
            pseg.alignment = PP_ALIGN.CENTER
            pseg.font.name = theme.font_family_header
            pseg.font.size = Pt(9.5)
            pseg.font.bold = True
            pseg.font.color.rgb = _get_contrast_text_color(s_rgb)

            cur_sx = to_emu(cur_sx + sw)

        if split_caption:
            tb_sc = slide.shapes.add_textbox(
                content_left,
                to_emu(bar_top + bar_h + Inches(0.06)),
                content_w,
                Inches(0.36),
            )
            tf_sc = tb_sc.text_frame
            tf_sc.word_wrap = True
            tf_sc.margin_left = tf_sc.margin_right = tf_sc.margin_top = tf_sc.margin_bottom = 0
            psc = tf_sc.paragraphs[0]
            psc.text = str(split_caption).strip()
            psc.font.name = theme.font_family
            psc.font.size = Pt(8.5)
            psc.font.color.rgb = theme.get_rgb("muted")
    elif footnote:
        tb_fn = slide.shapes.add_textbox(content_left, Inches(6.62), content_w, Inches(0.24))
        tf_fn = tb_fn.text_frame
        tf_fn.word_wrap = True
        tf_fn.margin_left = tf_fn.margin_right = tf_fn.margin_top = tf_fn.margin_bottom = 0
        pfn = tf_fn.paragraphs[0]
        pfn.text = str(footnote).strip()
        pfn.font.name = theme.font_family
        pfn.font.size = Pt(8.5)
        pfn.font.color.rgb = theme.get_rgb("muted")

    if takeaway:
        add_takeaway_bar(slide, theme, takeaway=takeaway)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice, source=source)
    return slide


def build_ml_benchmark_slide(
    prs: Presentation,
    theme: Theme,
    tracker: Optional[str] = None,
    action_title: str = "Candidate Model Outperforms Heuristic Baselines Across Every Operating Cutoff",
    subtitle: Optional[str] = None,
    chart: Optional[Dict[str, Any]] = None,
    benchmark_table: Optional[Dict[str, Any]] = None,
    hero_kpi: Optional[Dict[str, Any]] = None,
    split: Optional[Union[List[Union[int, float]], str]] = None,
    right_split: Optional[Union[List[Union[int, float]], str]] = None,
    takeaway: Optional[Union[str, Dict[str, Any]]] = None,
    footnote: Optional[str] = None,
    current_idx: int = 1,
    total_slides: int = 1,
    notice: Optional[str] = None,
    source: Optional[str] = None,
) -> Any:
    """
    Composite ML Evaluation Benchmark slide:
      - Left pane (~62%): Native multi-series lift/capture chart across operating cutoffs.
      - Right top pane (~54% of right height): Contiguous benchmark comparison table.
      - Right bottom pane (~46% of right height): Focal hero lift ratio vs. pass-gate KPI card.
    """
    chart_cfg = dict(chart or {})
    chart_cfg.setdefault("widget", "native_chart")
    chart_cfg.setdefault("chart_type", "column")
    chart_cfg.setdefault("show_gridlines", True)
    chart_cfg.setdefault("show_value_axis", True)

    table_cfg = dict(benchmark_table or {})
    table_cfg.setdefault("widget", "table")

    kpi_cfg = dict(hero_kpi or {})
    kpi_cfg.setdefault("widget", "hero_kpi")
    kpi_cfg.setdefault("card_style", "filled")

    right_stack = {
        "widget": "vertical_stack",
        "direction": "vertical",
        "split": right_split or [52, 48],
        "gap": 0.18,
        "panes": [table_cfg, kpi_cfg],
    }

    return build_composable_split_slide(
        prs=prs,
        theme=theme,
        tracker=tracker,
        action_title=action_title,
        subtitle=subtitle,
        split=split or [62, 38],
        gap=0.30,
        panes=[chart_cfg, right_stack],
        takeaway=takeaway,
        footnote=footnote,
        current_idx=current_idx,
        total_slides=total_slides,
        notice=notice,
        source=source,
    )
