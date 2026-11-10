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
    add_slide_with_background, add_slide_header, add_card, add_card_with_top_stripe, add_slide_footer,
    _add_contained_image, _interpolate_color, _get_contrast_text_color, _add_bullet_paragraph, _fit_image_in_box,
)

logger = logging.getLogger(__name__)

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
    client_sublabel: Optional[str] = None,
    vendor_sublabel: Optional[str] = None,
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

    # 4. Subtle structural baseline divider (flush with left margin grid)
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.80),
        Inches(4.9),
        Inches(11.733),
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
    elif client and "morula" in client.lower():
        resolved_client_logo = rm.resolve_asset("logo_morula_ivf", impacted_slide="Cover")

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

    # 5a. Client Slot (Custom image if provided; omitted when no asset to avoid duplicating PREPARED FOR text)
    if resolved_client_logo:
        _add_contained_image(slide, resolved_client_logo, client_x, slot_y, client_w, slot_h)
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

    if client_sublabel:
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

    if vendor_sublabel:
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
    client_sublabel: Optional[str] = None,
    vendor_sublabel: Optional[str] = None,
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

        # Text container (Full width, zero floating badge pills)
        tb_left = card_x + num_w + Inches(0.12)
        tb_w = col_w - num_w - Inches(0.20)

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

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides, notice=notice)
    return slide


def build_thank_you_slide(
    prs: Presentation,
    theme: Theme,
    tracker: str = "ENGAGEMENT WRAP-UP | THANK YOU",
    title: str = "Thank You",
    subtitle: Optional[str] = "Partnering to accelerate enterprise data modernization with Snowflake AI Data Cloud.",
    contacts: Optional[List[Dict[str, str]]] = None,
    next_steps: Optional[Dict[str, Any]] = None,
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

    # 3. Content Area: Structured Split Layout if next_steps provided
    if next_steps:
        if isinstance(next_steps, list):
            formatted_items = []
            for item in next_steps:
                if isinstance(item, dict):
                    m = item.get("milestone", item.get("title", ""))
                    d = item.get("detail", item.get("description", item.get("body", "")))
                    formatted_items.append(f"**{m}:** {d}" if d else m)
                else:
                    formatted_items.append(str(item))
            next_steps = {
                "title": "IMMEDIATE GOVERNANCE & ACTION PLAN",
                "badge": "NEXT HORIZONS",
                "items": formatted_items,
                "accent_key": "accent",
            }

    if next_steps and isinstance(next_steps, dict):
        col_gap = Inches(0.25)
        if contacts:
            left_w = Inches(5.80)
            right_w = text_width - left_w - col_gap
        else:
            left_w = text_width
            right_w = Inches(0.0)
        content_y = Inches(3.70)
        content_h = Inches(2.65)

        # 3a. Left Column: Immediate Governance / Next Steps Card
        ns_title = next_steps.get("title", "IMMEDIATE GOVERNANCE & ACTION PLAN")
        ns_items = next_steps.get("items", [])
        acc_key = next_steps.get("accent_key", "accent")

        add_card_with_top_stripe(
            slide=slide,
            theme=theme,
            left=text_left,
            top=content_y,
            width=left_w,
            height=content_h,
            accent_rgb=theme.get_rgb(acc_key),
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            stripe_height_in=0.06,
        )

        ns_tb = slide.shapes.add_textbox(text_left + Inches(0.20), content_y + Inches(0.16), left_w - Inches(0.40), content_h - Inches(0.26))
        ns_tf = ns_tb.text_frame
        ns_tf.word_wrap = True
        ns_tf.margin_left = ns_tf.margin_right = ns_tf.margin_top = ns_tf.margin_bottom = 0

        p_nst = ns_tf.paragraphs[0]
        p_nst.text = ns_title
        p_nst.font.name = theme.font_family_header
        p_nst.font.size = Pt(12.0)
        p_nst.font.bold = True
        p_nst.font.color.rgb = theme.get_rgb("primary")

        for item in ns_items:
            _add_bullet_paragraph(
                ns_tf,
                item,
                theme.font_family,
                font_size_pt=9.5,
                font_color=theme.get_rgb("secondary"),
                space_before_pt=4.0,
            )

        # 3b. Right Column: Contact Cards
        right_x = text_left + left_w + col_gap
        if contacts:
            num_c = len(contacts)
            c_gap = Inches(0.12)
            c_h = (content_h - (num_c - 1) * c_gap) / num_c

            for i, c in enumerate(contacts[:3]):
                cy = content_y + i * (c_h + c_gap)
                acc_k = c.get("accent_key", "accent" if i == 0 else "accent_teal")
                add_card_with_top_stripe(
                    slide=slide,
                    theme=theme,
                    left=right_x,
                    top=cy,
                    width=right_w,
                    height=c_h,
                    accent_rgb=theme.get_rgb(acc_k),
                    bg_color=theme.get_rgb("surface"),
                    border_color=theme.get_rgb("border"),
                    stripe_height_in=0.05,
                )

                ctb = slide.shapes.add_textbox(right_x + Inches(0.18), cy + Inches(0.12), right_w - Inches(0.36), c_h - Inches(0.20))
                ctf = ctb.text_frame
                ctf.word_wrap = True
                ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0

                cp1 = ctf.paragraphs[0]
                cp1.text = c.get("name", "")
                cp1.font.name = theme.font_family_header
                cp1.font.size = Pt(12.0)
                cp1.font.bold = True
                cp1.font.color.rgb = theme.get_rgb("primary")

                cp2 = ctf.add_paragraph()
                cp2.text = c.get("role", c.get("title", ""))
                cp2.font.name = theme.font_family
                cp2.font.size = Pt(9.5)
                cp2.font.color.rgb = theme.get_rgb("accent")
                cp2.space_before = Pt(2)

                if c.get("email"):
                    cp3 = ctf.add_paragraph()
                    cp3.text = f"Email: {c['email']}"
                    cp3.font.name = theme.font_family
                    cp3.font.size = Pt(9.5)
                    cp3.font.color.rgb = theme.get_rgb("secondary")
                    cp3.space_before = Pt(2)
    elif contacts:
        num_c = len(contacts)
        card_gap = Inches(0.25)
        card_w = min(Inches(5.40), (text_width - (num_c - 1) * card_gap) / num_c)
        card_h = Inches(1.80)
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
            cp2.text = c.get("role", c.get("title", ""))
            cp2.font.name = theme.font_family
            cp2.font.size = Pt(11.0)
            cp2.font.color.rgb = theme.get_rgb("accent")
            cp2.space_before = Pt(3)

            if c.get("email"):
                cp3 = ctf.add_paragraph()
                cp3.text = f"Email: {c['email']}"
                cp3.font.name = theme.font_family
                cp3.font.size = Pt(11.0)
                cp3.font.color.rgb = theme.get_rgb("secondary")
                cp3.space_before = Pt(4)
    else:
        # Clean corporate closing card (no personal staff names)
        card_w = Inches(7.50)
        card_h = Inches(1.80)
        card_y = Inches(3.85)

        card, stripe = add_card_with_top_stripe(
            slide=slide,
            theme=theme,
            left=text_left,
            top=card_y,
            width=card_w,
            height=card_h,
            accent_rgb=theme.get_rgb("accent"),
            bg_color=theme.get_rgb("surface"),
            border_color=theme.get_rgb("border"),
            stripe_height_in=0.06,
        )

        ctb = slide.shapes.add_textbox(text_left + Inches(0.22), card_y + Inches(0.18), card_w - Inches(0.44), card_h - Inches(0.30))
        ctf = ctb.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0

        cp1 = ctf.paragraphs[0]
        cp1.text = "Data & AI Modernization Practice"
        cp1.font.name = theme.font_family_header
        cp1.font.size = Pt(14.0)
        cp1.font.bold = True
        cp1.font.color.rgb = theme.get_rgb("primary")

        cp2 = ctf.add_paragraph()
        cp2.text = "Enterprise Cloud & Analytics Advisory Core"
        cp2.font.name = theme.font_family
        cp2.font.size = Pt(11.0)
        cp2.font.color.rgb = theme.get_rgb("accent")
        cp2.space_before = Pt(3)

        cp3 = ctf.add_paragraph()
        cp3.text = "Official Support Channel: enterprise.consulting@enterprise-bench.local"
        cp3.font.name = theme.font_family
        cp3.font.size = Pt(11.0)
        cp3.font.color.rgb = theme.get_rgb("secondary")
        cp3.space_before = Pt(4)

    # 4. Corporate Address Footer Anchored at Bottom
    otb = slide.shapes.add_textbox(text_left, Inches(6.55), text_width, Inches(0.50))
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
    op2.font.size = Pt(8.5)
    op2.font.color.rgb = theme.get_rgb("muted")
    return slide

