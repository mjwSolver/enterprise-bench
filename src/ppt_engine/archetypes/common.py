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

logger = logging.getLogger(__name__)

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

    # 1. Tracker Breadcrumb (Auto-sanitized to eliminate meta-labeling like "SLIDE 07 |")
    clean_tracker = re.sub(r"^SLIDE\s+\d+\s*\|\s*", "", tracker.strip(), flags=re.IGNORECASE)
    tb_tr = slide.shapes.add_textbox(Inches(0.8), Inches(0.36), Inches(11.733), Inches(0.22))
    tf_tr = tb_tr.text_frame
    tf_tr.word_wrap = True
    tf_tr.margin_left = tf_tr.margin_right = tf_tr.margin_top = tf_tr.margin_bottom = 0
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = clean_tracker.upper()
    p_tr.font.name = theme.font_family_header
    p_tr.font.size = Pt(thresholds.get("tracker_pt", 9.5))
    p_tr.font.bold = True
    p_tr.font.color.rgb = tracker_rgb

    # 2. Action Headline & Context Subtitle (Unified Text Frame for Consistent Spacing)
    tb_header = slide.shapes.add_textbox(Inches(0.8), Inches(0.58), Inches(11.733), Inches(0.65))
    tf_h = tb_header.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0

    p_t = tf_h.paragraphs[0]
    p_t.text = ""
    base_title_pt = thresholds.get("action_title_pt", 18.0)
    if len(resolved_title) > 60:
        base_title_pt = min(base_title_pt, 16.5)
    append_formatted_runs(
        paragraph=p_t,
        text=resolved_title,
        font_name=theme.font_family_header,
        font_size_pt=base_title_pt,
        font_color=theme.get_rgb("primary"),
        default_bold=True,
    )

    # 3. Context Subtitle (Flowed via paragraph offset to ensure consistent spacing at all times)
    if subtitle:
        p_s = tf_h.add_paragraph()
        p_s.space_before = Pt(4)
        append_formatted_runs(
            paragraph=p_s,
            text=subtitle,
            font_name=theme.font_family,
            font_size_pt=thresholds.get("subtitle_pt", 10.0),
            font_color=theme.get_rgb("secondary"),
        )


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
    source: Optional[str] = None,
) -> None:
    """Renders bottom divider line, confidentiality notice, source attribution, and slide pagination."""
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

    # Notice text (with optional source attribution prefix)
    tb_n = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(9.5), Inches(0.25))
    tf_n = tb_n.text_frame
    tf_n.margin_left = tf_n.margin_right = tf_n.margin_top = tf_n.margin_bottom = 0
    p_n = tf_n.paragraphs[0]

    if source:
        clean_src = source.strip()
        if not clean_src.lower().startswith("source:"):
            clean_src = f"Source: {clean_src}"
        p_n.text = clean_src
    else:
        p_n.text = notice or "Enterprise Strategy Group  |  Confidential & Proprietary"

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
    if p.suffix.lower() == ".svg":
        for cand in [
            p.with_suffix(".png"),
            p.parent / f"{p.stem}.png",
            p.parent.parent / "images" / "logos" / f"{p.stem}.png",
            p.parent.parent / "images" / f"{p.stem}.png",
        ]:
            if cand.is_file():
                p = cand
                break
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
    pill.line.color.rgb = theme.get_rgb(text_key)
    pill.line.width = Pt(0.5)

    tf = pill.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
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
    font_size_pt: float = 11.0,
    font_color: Optional[RGBColor] = None,
    space_before_pt: float = 7.0,
    bullet_char: str = "•",
    lead_color: Optional[RGBColor] = None,
    space_after_pt: float = 2.0,
) -> Any:
    """Appends a bullet paragraph with DrawingML hanging indent (marL/indent). Parses **bold** and Lead: text."""
    from pptx.oxml.xmlchemy import OxmlElement

    if len(tf.paragraphs) == 1 and not tf.paragraphs[0].text.strip():
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    clean_text = text.strip().replace("`", "")
    if clean_text.startswith(("•", "-", "–")):
        clean_text = clean_text.lstrip("•-–\t ").strip()
    elif clean_text.startswith("* ") or clean_text.startswith("*\t"):
        clean_text = clean_text[2:].strip()
    # Strip CSS fallback lists if present (e.g. "Calibri, Helvetica, Arial...")
    clean_font = font_name.split(",")[0].strip().strip('"\'') if font_name else "Calibri"
    if not clean_font:
        clean_font = "Calibri"
    p.space_before = Pt(space_before_pt)
    p.space_after = Pt(space_after_pt)

    # DrawingML Hanging Indent: marL="288000" (0.20 in), indent="-288000"
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", "288000")
    pPr.set("indent", "-288000")

    # In ECMA-376 PresentationML, buClrTx, buSzPct, buFont, and buChar MUST precede defRPr!
    from pptx.oxml.ns import qn
    buClrTx = OxmlElement("a:buClrTx")
    buSzPct = OxmlElement("a:buSzPct")
    buSzPct.set("val", "100000")
    buFont = OxmlElement("a:buFont")
    buFont.set("typeface", "Arial")
    buChar = OxmlElement("a:buChar")
    buChar.set("char", bullet_char)

    elems = [buClrTx, buSzPct, buFont, buChar]
    defRPr = pPr.find(qn("a:defRPr"))
    if defRPr is not None:
        idx = pPr.index(defRPr)
        for offset, el in enumerate(elems):
            pPr.insert(idx + offset, el)
    else:
        for el in elems:
            pPr.append(el)

    lead_rgb = lead_color or RGBColor(15, 23, 42)
    body_rgb = font_color or RGBColor(71, 85, 105)

    append_formatted_runs(
        paragraph=p,
        text=clean_text,
        font_name=clean_font,
        font_size_pt=font_size_pt,
        font_color=body_rgb,
        lead_color=lead_rgb,
        auto_colon_lead=True,
    )
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


def add_takeaway_bar(
    slide: Any,
    theme: Theme,
    takeaway: Union[str, Dict[str, Any]],
    top_y: Optional[Inches] = None,
    left_x: Optional[Inches] = None,
    width: Optional[Inches] = None,
    height: Optional[Inches] = None,
    badge: Optional[str] = None,
    font_size_pt: float = 10.0,
    accent_key: str = "accent",
) -> Any:
    """Renders a standardized executive takeaway or synthesis bar at the bottom of a slide.

    Supports:
    - String format: "Key Finding: Narrative description..." (auto-bolded lead with span compiler)
    - Dict format: {"text": "...", "badge": "...", "title": "...", "description": "...", "accent_key": "..."}
    - Universal inline markdown compilation (**bold**, *italic*, `code`) across all text runs.
    - Zero drop shadows, sharp rectangle geometry, and clean left indicator accent stripe.
    """
    left_x = left_x if left_x is not None else Inches(0.80)
    width = width if width is not None else Inches(11.733)

    # Parse payload
    if isinstance(takeaway, dict):
        acc_key = takeaway.get("accent_key", accent_key)
        badge_text = takeaway.get("badge", badge)
        title_text = str(takeaway.get("title", "")).strip()
        desc_text = str(takeaway.get("description", "")).strip()
        raw_text = str(takeaway.get("text", "")).strip()
    else:
        acc_key = accent_key
        badge_text = badge
        title_text = ""
        desc_text = ""
        raw_text = str(takeaway).strip() if takeaway else ""

    is_two_row = bool(title_text and desc_text)
    if height is None:
        height = Inches(1.30) if is_two_row else Inches(0.54)
    if top_y is None:
        top_y = Inches(5.60) if is_two_row else Inches(6.28)

    acc_rgb = theme.get_rgb(acc_key)

    # 1. Base Container Card
    add_card(
        slide,
        theme,
        left_x,
        top_y,
        width,
        height,
        force_rectangle=True,
        bg_color=hex_to_rgb("#F8FAFC"),
        border_color=hex_to_rgb("#BAE6FD"),
        border_width_pt=0.75,
    )

    # 2. Vertical Focus Indicator Stripe on Left
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, top_y, Inches(0.06), height)
    stripe.shadow.inherit = False
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = acc_rgb
    stripe.line.fill.background()

    # 3. Content Text Box
    if is_two_row:
        # Two-row executive card format (Title + Description, zero floating badge pills)
        tb_y = top_y + Inches(0.10)
        tb_h = height - Inches(0.20)

        tb = slide.shapes.add_textbox(left_x + Inches(0.20), tb_y, width - Inches(0.36), tb_h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_t = tf.paragraphs[0]
        append_formatted_runs(
            paragraph=p_t,
            text=title_text,
            font_name=theme.font_family_header,
            font_size_pt=font_size_pt + 2.0,
            font_color=theme.get_rgb("primary"),
            default_bold=True,
        )

        p_d = tf.add_paragraph()
        p_d.space_before = Pt(4)
        append_formatted_runs(
            paragraph=p_d,
            text=desc_text,
            font_name=theme.font_family,
            font_size_pt=font_size_pt,
            font_color=theme.get_rgb("secondary"),
        )
    else:
        # Single-row synthesis bar format
        tb = slide.shapes.add_textbox(left_x + Inches(0.22), top_y + Inches(0.04), width - Inches(0.36), height - Inches(0.08))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]

        # Strip bracketed prefix tags from conclusion banners by default for executive clarity
        body_text = raw_text or title_text or desc_text
        body_text = re.sub(r"^(?:\[[^\]]+\]\s*)+", "", body_text).strip()
        if ":" in body_text:
            t_lead, t_body = body_text.split(":", 1)
            lead_run = p.add_run()
            lead_run.text = f"{t_lead.strip()}: "
            lead_run.font.name = theme.font_family_header
            lead_run.font.size = Pt(font_size_pt)
            lead_run.font.bold = True
            lead_run.font.color.rgb = acc_rgb

            append_formatted_runs(
                paragraph=p,
                text=t_body.strip(),
                font_name=theme.font_family,
                font_size_pt=font_size_pt,
                font_color=theme.get_rgb("primary"),
            )
        else:
            append_formatted_runs(
                paragraph=p,
                text=body_text.strip(),
                font_name=theme.font_family,
                font_size_pt=font_size_pt,
                font_color=theme.get_rgb("primary"),
            )
    return slide


