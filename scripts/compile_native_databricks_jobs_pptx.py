#!/usr/bin/env python3
"""
Compile 100% Native, Fully Editable PowerPoint Deck for Databricks Jobs API Architecture.

Features:
- Every card is a native DrawingML shape (MSO_SHAPE.ROUNDED_RECTANGLE or MSO_SHAPE.CAN).
- Every title, badge, and subtitle is a native, selectable, live editable text box.
- Every flow connector is a native DrawingML connector line with arrowheads.
- Every flow label is a native DrawingML pill with live editable text.
- Every icon is a transparent high-resolution vector-rendered graphic sitting cleanly in its card.
- Full Solid White Canvas (#FFFFFF), flat aesthetic, zero drop shadows (enforced via explicit empty <a:effectLst/>).
- Brand Header with dual brand stripes (1:2 Red/Blue ratio) and non-verbose title.
- Zero unsolicited sub-captions, 1-slide presentation scope.
"""

import sys
import shutil
import subprocess
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement

# Directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "TEMP"
OUTPUT_DIR = PROJECT_ROOT / "output" / "presentations"
ICON_CACHE_DIR = TEMP_DIR / "icon_cache"
ASSETS_DIR = PROJECT_ROOT / "assets"

def hex_to_rgb(hex_code: str) -> RGBColor:
    h = hex_code.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def px_to_in(px: float) -> Inches:
    """Map 1280x720 SVG coordinate space directly to 13.333x7.5 inch PowerPoint widescreen slide."""
    return Inches(px / 96.0)

def strip_shadow(shape):
    """Guarantees zero drop shadows by stripping theme effects and appending empty <a:effectLst/>."""
    try:
        shape.shadow.inherit = False
    except Exception:
        pass
    try:
        sp_pr = shape._element.spPr
        effect_lst = sp_pr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}effectLst")
        if effect_lst is None:
            sp_pr.append(OxmlElement("a:effectLst"))
        else:
            effect_lst.clear()
    except Exception:
        pass
    try:
        style = shape._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
        if style is not None:
            effect_ref = style.find("{http://schemas.openxmlformats.org/drawingml/2006/main}effectRef")
            if effect_ref is not None:
                effect_ref.set("idx", "0")
    except Exception:
        pass

def set_arrowhead(connector, arrow_type: str = "triangle", at_tail: bool = True):
    """Appends DrawingML arrowhead to connector."""
    try:
        ln_elem = connector._element.spPr.ln
        tag = "a:tailEnd" if at_tail else "a:headEnd"
        end_elem = OxmlElement(tag)
        end_elem.set("type", arrow_type)
        end_elem.set("w", "med")
        end_elem.set("len", "med")
        ln_elem.append(end_elem)
    except Exception as e:
        print(f"Warning: could not set arrowhead: {e}")

def prepare_icon_png(svg_string: str, name: str) -> Path:
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    svg_file = ICON_CACHE_DIR / f"{name}.svg"
    png_file = ICON_CACHE_DIR / f"{name}.png"
    svg_file.write_text(svg_string, encoding="utf-8")
    subprocess.run(["/opt/homebrew/bin/rsvg-convert", "-z", "4", str(svg_file), "-o", str(png_file)], check=True)
    return png_file

def prepare_icon_from_asset(rel_path: str, name: str) -> Path:
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    src_svg = ASSETS_DIR / rel_path
    png_file = ICON_CACHE_DIR / f"{name}.png"
    subprocess.run(["/opt/homebrew/bin/rsvg-convert", "-z", "4", str(src_svg), "-o", str(png_file)], check=True)
    return png_file

def add_databricks_jobs_api_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # 1. Canvas Background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = hex_to_rgb("#FFFFFF")
    bg.line.fill.background()
    strip_shadow(bg)

    # 2. Header Brand Stripes & Title
    red_stripe = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(50), px_to_in(34), px_to_in(5), px_to_in(34))
    red_stripe.fill.solid()
    red_stripe.fill.fore_color.rgb = hex_to_rgb("#E11D48")
    red_stripe.line.fill.background()
    strip_shadow(red_stripe)

    blue_stripe = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(58), px_to_in(34), px_to_in(9), px_to_in(34))
    blue_stripe.fill.solid()
    blue_stripe.fill.fore_color.rgb = hex_to_rgb("#0284C7")
    blue_stripe.line.fill.background()
    strip_shadow(blue_stripe)

    title_box = slide.shapes.add_textbox(px_to_in(78), px_to_in(30), px_to_in(500), px_to_in(42))
    tf = title_box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "Databricks Jobs API"
    p.font.name = "Arial"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#0F172A")
    strip_shadow(title_box)

    # 3. Zone 1: CLIENT APPLICATIONS Container
    apps_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(50), px_to_in(105), px_to_in(280), px_to_in(435))
    apps_box.fill.solid()
    apps_box.fill.fore_color.rgb = hex_to_rgb("#F8FAFC")
    apps_box.line.color.rgb = hex_to_rgb("#94A3B8")
    apps_box.line.width = Pt(1.5)
    apps_box.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    strip_shadow(apps_box)

    apps_title = slide.shapes.add_textbox(px_to_in(50), px_to_in(116), px_to_in(280), px_to_in(24))
    tf = apps_title.text_frame
    tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "CLIENT APPLICATIONS"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#64748B")
    strip_shadow(apps_title)

    # Prepare Monitor Icon
    monitor_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2" fill="#EFF6FF"/><path d="M8 21h8m-4-4v4"/></svg>"""
    monitor_png = prepare_icon_png(monitor_svg, "monitor_icon")

    # App 1 Card
    app1_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(80), px_to_in(150), px_to_in(220), px_to_in(145))
    app1_card.fill.solid()
    app1_card.fill.fore_color.rgb = hex_to_rgb("#FFFFFF")
    app1_card.line.color.rgb = hex_to_rgb("#3B82F6")
    app1_card.line.width = Pt(1.5)
    strip_shadow(app1_card)

    pic_app1 = slide.shapes.add_picture(str(monitor_png), px_to_in(165), px_to_in(170), px_to_in(50), px_to_in(50))
    strip_shadow(pic_app1)

    app1_txt = slide.shapes.add_textbox(px_to_in(80), px_to_in(236), px_to_in(220), px_to_in(35))
    tf = app1_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "App 1"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#1E3A8A")
    strip_shadow(app1_txt)

    # App 2 Card
    app2_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(70), px_to_in(325), px_to_in(115), px_to_in(165))
    app2_card.fill.solid()
    app2_card.fill.fore_color.rgb = hex_to_rgb("#FFFFFF")
    app2_card.line.color.rgb = hex_to_rgb("#3B82F6")
    app2_card.line.width = Pt(1.5)
    strip_shadow(app2_card)

    pic_app2 = slide.shapes.add_picture(str(monitor_png), px_to_in(70 + 35.5), px_to_in(325 + 24), px_to_in(44), px_to_in(44))
    strip_shadow(pic_app2)

    app2_txt = slide.shapes.add_textbox(px_to_in(70), px_to_in(420), px_to_in(115), px_to_in(35))
    tf = app2_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "App 2"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#1E3A8A")
    strip_shadow(app2_txt)

    # App 3 Card
    app3_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(195), px_to_in(325), px_to_in(115), px_to_in(165))
    app3_card.fill.solid()
    app3_card.fill.fore_color.rgb = hex_to_rgb("#FFFFFF")
    app3_card.line.color.rgb = hex_to_rgb("#3B82F6")
    app3_card.line.width = Pt(1.5)
    strip_shadow(app3_card)

    pic_app3 = slide.shapes.add_picture(str(monitor_png), px_to_in(195 + 35.5), px_to_in(325 + 24), px_to_in(44), px_to_in(44))
    strip_shadow(pic_app3)

    app3_txt = slide.shapes.add_textbox(px_to_in(195), px_to_in(420), px_to_in(115), px_to_in(35))
    tf = app3_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "App 3"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#1E3A8A")
    strip_shadow(app3_txt)

    # 4. Zone 2: DBx Jobs API Card
    dbx_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(375), px_to_in(225), px_to_in(200), px_to_in(190))
    dbx_card.fill.solid()
    dbx_card.fill.fore_color.rgb = hex_to_rgb("#FFFFFF")
    dbx_card.line.color.rgb = hex_to_rgb("#EA580C")
    dbx_card.line.width = Pt(1.75)
    strip_shadow(dbx_card)

    # DBx API Badge Pill
    dbx_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(400), px_to_in(241), px_to_in(150), px_to_in(22))
    dbx_pill.fill.solid()
    dbx_pill.fill.fore_color.rgb = hex_to_rgb("#FFEDD5")
    dbx_pill.line.fill.background()
    strip_shadow(dbx_pill)
    tf = dbx_pill.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "DATABRICKS API 2.1"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#C2410C")

    # REST API Icon (Zero black artifacts)
    rest_api_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96" fill="none">
        <path d="M47.6417 36.9986C51.4202 36.9986 54.4833 33.9355 54.4833 30.157C54.4833 26.3785 51.4202 23.3154 47.6417 23.3154C43.8632 23.3154 40.8001 26.3785 40.8001 30.157C40.8001 33.9355 43.8632 36.9986 47.6417 36.9986Z" stroke="#EA580C" stroke-width="4.5" fill="none"/>
        <path d="M68.9153 73.8431C72.6938 73.8431 75.7569 70.78 75.7569 67.0015C75.7569 63.223 72.6938 60.1599 68.9153 60.1599C65.1368 60.1599 62.0737 63.223 62.0737 67.0015C62.0737 70.78 65.1368 73.8431 68.9153 73.8431Z" stroke="#EA580C" stroke-width="4.5" fill="none"/>
        <path d="M26.3681 73.8431C30.1466 73.8431 33.2097 70.78 33.2097 67.0015C33.2097 63.223 30.1466 60.1599 26.3681 60.1599C22.5896 60.1599 19.5265 63.223 19.5265 67.0015C19.5265 70.78 22.5896 73.8431 26.3681 73.8431Z" stroke="#EA580C" stroke-width="4.5" fill="none"/>
        <path d="M60.5953 67.0016L44.1409 67.0016C44.1409 76.8192 36.1793 84.7808 26.3617 84.7808C16.5441 84.7808 8.58249 76.8192 8.58249 67.0016C8.58249 57.184 16.5441 49.2224 26.3617 49.2224" stroke="#EA580C" stroke-width="4.5" fill="none"/>
        <path d="M51.9105 37.5488L60.0321 51.6096C68.5313 46.7008 79.4049 49.6128 84.3137 58.1184C89.2225 66.6176 86.3105 77.4912 77.8049 82.4C69.3057 87.3088 58.4321 84.3968 53.5233 75.8912" stroke="#EA580C" stroke-width="4.5" fill="none"/>
        <path d="M30.5217 59.8081L38.7521 45.5553C30.2529 40.6465 27.3345 29.7729 32.2433 21.2737C37.1521 12.7745 48.0257 9.8561 56.5249 14.7649C65.0241 19.6737 67.9425 30.5473 63.0337 39.0465" stroke="#EA580C" stroke-width="4.5" fill="none"/>
    </svg>"""
    rest_api_png = prepare_icon_png(rest_api_svg, "rest_api_clean")
    pic_dbx = slide.shapes.add_picture(str(rest_api_png), px_to_in(445), px_to_in(273), px_to_in(60), px_to_in(60))
    strip_shadow(pic_dbx)

    dbx_txt = slide.shapes.add_textbox(px_to_in(375), px_to_in(350), px_to_in(200), px_to_in(35))
    tf = dbx_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "DBx Jobs API"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#7C2D12")
    strip_shadow(dbx_txt)

    # 5. Zone 3: DATABRICKS Environment Container
    dbx_env = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(640), px_to_in(105), px_to_in(595), px_to_in(435))
    dbx_env.fill.solid()
    dbx_env.fill.fore_color.rgb = hex_to_rgb("#FFFBF8")
    dbx_env.line.color.rgb = hex_to_rgb("#EA580C")
    dbx_env.line.width = Pt(1.5)
    dbx_env.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    strip_shadow(dbx_env)

    # Databricks Header Pill
    dbx_header_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(660), px_to_in(118), px_to_in(135), px_to_in(26))
    dbx_header_pill.fill.solid()
    dbx_header_pill.fill.fore_color.rgb = hex_to_rgb("#EA580C")
    dbx_header_pill.line.fill.background()
    strip_shadow(dbx_header_pill)

    dbx_logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 16 16"><path d="M13.7194 6.60746L7.25506 10.338L0.332928 6.35214L0 6.53654L0 9.43016L7.25506 13.6004L13.7194 9.88406V11.416L7.25506 15.1465L0.332928 11.1607L0 11.3451L0 11.8415L7.25506 16.0117L14.4962 11.8415V8.94789L14.1633 8.76349L7.25506 12.7351L0.776832 9.01881L0.776832 7.4869L7.25506 11.2032L14.4962 7.033V4.18193L14.1356 3.96917L7.25506 7.92661L1.10976 4.40888L7.25506 0.876967L12.3045 3.78477L12.7484 3.52945V3.17484L7.25506 0.0117187L0 4.18193L0 4.63583L7.25506 8.80605L13.7194 5.07555V6.60746Z" fill="#FFFFFF"/></svg>"""
    dbx_logo_png = prepare_icon_png(dbx_logo_svg, "dbx_logo_white")
    pic_dbx_logo = slide.shapes.add_picture(str(dbx_logo_png), px_to_in(668), px_to_in(123), px_to_in(16), px_to_in(16))
    strip_shadow(pic_dbx_logo)

    dbx_header_txt = slide.shapes.add_textbox(px_to_in(686), px_to_in(121), px_to_in(102), px_to_in(20))
    tf = dbx_header_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "DATABRICKS"
    p.font.name = "Arial"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#FFFFFF")
    strip_shadow(dbx_header_txt)

    # Cluster Card (Compute Engine)
    cluster_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(680), px_to_in(225), px_to_in(220), px_to_in(190))
    cluster_card.fill.solid()
    cluster_card.fill.fore_color.rgb = hex_to_rgb("#FFFFFF")
    cluster_card.line.color.rgb = hex_to_rgb("#FF3621")
    cluster_card.line.width = Pt(2.0)
    strip_shadow(cluster_card)

    cluster_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(720), px_to_in(245), px_to_in(140), px_to_in(22))
    cluster_pill.fill.solid()
    cluster_pill.fill.fore_color.rgb = hex_to_rgb("#FEE2E2")
    cluster_pill.line.fill.background()
    strip_shadow(cluster_pill)
    tf = cluster_pill.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "COMPUTE ENGINE"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#DC2626")

    cluster_icon_png = prepare_icon_from_asset("logos/databricks/compute_clusters.svg", "compute_clusters_icon")
    pic_cluster = slide.shapes.add_picture(str(cluster_icon_png), px_to_in(762), px_to_in(279), px_to_in(56), px_to_in(56))
    strip_shadow(pic_cluster)

    cluster_txt = slide.shapes.add_textbox(px_to_in(680), px_to_in(348), px_to_in(220), px_to_in(35))
    tf = cluster_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "Cluster"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#0F172A")
    strip_shadow(cluster_txt)

    # Code Card
    code_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(965), px_to_in(145), px_to_in(245), px_to_in(140))
    code_card.fill.solid()
    code_card.fill.fore_color.rgb = hex_to_rgb("#ECFDF5")
    code_card.line.color.rgb = hex_to_rgb("#10B981")
    code_card.line.width = Pt(1.5)
    strip_shadow(code_card)

    code_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(1027), px_to_in(159), px_to_in(120), px_to_in(20))
    code_pill.fill.solid()
    code_pill.fill.fore_color.rgb = hex_to_rgb("#D1FAE5")
    code_pill.line.fill.background()
    strip_shadow(code_pill)
    tf = code_pill.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "TASK ARTIFACT"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(8.0)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#065F46")

    notebooks_icon_png = prepare_icon_from_asset("logos/databricks/notebooks.svg", "notebooks_icon")
    pic_code = slide.shapes.add_picture(str(notebooks_icon_png), px_to_in(1070), px_to_in(183), px_to_in(35), px_to_in(35))
    strip_shadow(pic_code)

    code_txt = slide.shapes.add_textbox(px_to_in(965), px_to_in(221), px_to_in(245), px_to_in(28))
    tf = code_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "Code"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#065F46")
    strip_shadow(code_txt)

    code_sub = slide.shapes.add_textbox(px_to_in(965), px_to_in(249), px_to_in(245), px_to_in(24))
    tf = code_sub.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "Notebook, Python, Wheel Dependencies"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#047857")
    strip_shadow(code_sub)

    # Database Card (Cylinder / CAN)
    db_card = slide.shapes.add_shape(MSO_SHAPE.CAN, px_to_in(970), px_to_in(355), px_to_in(235), px_to_in(155))
    db_card.fill.solid()
    db_card.fill.fore_color.rgb = hex_to_rgb("#F0F9FF")
    db_card.line.color.rgb = hex_to_rgb("#0284C7")
    db_card.line.width = Pt(1.5)
    strip_shadow(db_card)

    db_pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(1027), px_to_in(381), px_to_in(120), px_to_in(20))
    db_pill.fill.solid()
    db_pill.fill.fore_color.rgb = hex_to_rgb("#BAE6FD")
    db_pill.line.fill.background()
    strip_shadow(db_pill)
    tf = db_pill.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "UNITY CATALOG"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(8.0)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#0369A1")

    delta_lake_png = prepare_icon_from_asset("logos/databricks/delta_lake.svg", "delta_lake_icon")
    pic_db = slide.shapes.add_picture(str(delta_lake_png), px_to_in(1070), px_to_in(405), px_to_in(35), px_to_in(35))
    strip_shadow(pic_db)

    db_txt = slide.shapes.add_textbox(px_to_in(970), px_to_in(445), px_to_in(235), px_to_in(28))
    tf = db_txt.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "Database"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#0369A1")
    strip_shadow(db_txt)

    db_sub = slide.shapes.add_textbox(px_to_in(970), px_to_in(473), px_to_in(235), px_to_in(24))
    tf = db_sub.text_frame
    tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]
    p.text = "Unity Catalog"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = hex_to_rgb("#0284C7")
    strip_shadow(db_sub)

    # 6. CONNECTORS & FLOW PILLS (100% Native DrawingML)
    def add_flow_pill(x, y, w, h, fill_hex, border_hex, text, text_hex, font_size=8.5):
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px_to_in(x), px_to_in(y), px_to_in(w), px_to_in(h))
        pill.fill.solid()
        pill.fill.fore_color.rgb = hex_to_rgb(fill_hex)
        pill.line.color.rgb = hex_to_rgb(border_hex)
        pill.line.width = Pt(1.0)
        strip_shadow(pill)
        tf = pill.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_top = tf.margin_bottom = tf.margin_left = tf.margin_right = 0
        p = tf.paragraphs[0]
        p.text = text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Arial"
        p.font.size = Pt(font_size)
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb(text_hex)
        return pill

    # 1. run-now: Apps -> DBx Jobs API
    c1 = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px_to_in(330), px_to_in(280), px_to_in(375), px_to_in(280))
    c1.line.color.rgb = hex_to_rgb("#2563EB")
    c1.line.width = Pt(2.2)
    set_arrowhead(c1, "triangle", at_tail=True)
    strip_shadow(c1)
    add_flow_pill(322, 258, 62, 19, "#EFF6FF", "#BFDBFE", "run-now", "#1D4ED8")

    # 2. returns: DBx Jobs API -> Apps
    c2 = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px_to_in(375), px_to_in(360), px_to_in(330), px_to_in(360))
    c2.line.color.rgb = hex_to_rgb("#2563EB")
    c2.line.width = Pt(2.2)
    set_arrowhead(c2, "triangle", at_tail=True)
    strip_shadow(c2)
    add_flow_pill(329, 366, 48, 19, "#EFF6FF", "#BFDBFE", "returns", "#1D4ED8")

    # 3. POST /run-now: DBx Jobs API -> Cluster
    c3 = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px_to_in(575), px_to_in(280), px_to_in(680), px_to_in(280))
    c3.line.color.rgb = hex_to_rgb("#EA580C")
    c3.line.width = Pt(2.2)
    set_arrowhead(c3, "triangle", at_tail=True)
    strip_shadow(c3)
    add_flow_pill(586, 256, 84, 20, "#FFF7ED", "#FFEDD5", "POST /run-now", "#C2410C", font_size=8.5)

    # 4. Execution Done: Cluster -> DBx Jobs API (Dashed)
    c4 = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px_to_in(680), px_to_in(360), px_to_in(575), px_to_in(360))
    c4.line.color.rgb = hex_to_rgb("#EA580C")
    c4.line.width = Pt(2.0)
    c4.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    set_arrowhead(c4, "triangle", at_tail=True)
    strip_shadow(c4)
    add_flow_pill(583, 336, 88, 20, "#FFF7ED", "#FFEDD5", "Execution Done", "#C2410C", font_size=8.5)

    # 5. Run Here: Code -> Cluster (Curved)
    c5 = slide.shapes.add_connector(MSO_CONNECTOR.CURVE, px_to_in(965), px_to_in(215), px_to_in(900), px_to_in(275))
    c5.line.color.rgb = hex_to_rgb("#10B981")
    c5.line.width = Pt(2.2)
    set_arrowhead(c5, "triangle", at_tail=True)
    strip_shadow(c5)
    add_flow_pill(898, 202, 66, 20, "#ECFDF5", "#A7F3D0", "Run Here", "#047857", font_size=8.5)

    # 6. checks: Cluster -> Database (Curved)
    c6 = slide.shapes.add_connector(MSO_CONNECTOR.CURVE, px_to_in(900), px_to_in(345), px_to_in(970), px_to_in(395))
    c6.line.color.rgb = hex_to_rgb("#0284C7")
    c6.line.width = Pt(2.2)
    set_arrowhead(c6, "triangle", at_tail=True)
    strip_shadow(c6)
    add_flow_pill(908, 350, 54, 20, "#F0F9FF", "#BAE6FD", "checks", "#0369A1", font_size=8.5)

    # 7. Record Result: Database -> Cluster (Curved Dashed)
    c7 = slide.shapes.add_connector(MSO_CONNECTOR.CURVE, px_to_in(970), px_to_in(455), px_to_in(900), px_to_in(395))
    c7.line.color.rgb = hex_to_rgb("#0284C7")
    c7.line.width = Pt(2.0)
    c7.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    set_arrowhead(c7, "triangle", at_tail=True)
    strip_shadow(c7)
    add_flow_pill(898, 435, 84, 20, "#F0F9FF", "#BAE6FD", "Record Result", "#0369A1", font_size=8.0)
    return slide

def build_native_deck(output_path: Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)
    add_databricks_jobs_api_slide(prs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    print(f"✓ Saved 100% Native, Fully Editable PowerPoint Deck to: {output_path}")

if __name__ == "__main__":
    out_file = TEMP_DIR / "databricks_jobs_api_architecture.pptx"
    build_native_deck(out_file)
    # Mirror to output/presentations/
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_file, OUTPUT_DIR / "databricks_jobs_api_architecture.pptx")
    print("Compilation complete!")
