"""
Diagram Engine V2 - Native PowerPoint (DrawingML) Slide Compiler
================================================================
Compiles declarative DiagramSpec instances into 100% native, fully editable
Microsoft PowerPoint slides featuring the flat consulting aesthetic, proportional
card padding, side-slot 3D cylinders, vector tech logos, and routed connectors.
"""

from __future__ import annotations

import io
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Emu, Inches, Pt

from src.ppt_engine.diagram_v2.models import (
    DiagramSpec,
    ContainerSpec,
    NodeSpec,
    FlowSpec,
    BadgeSpec,
    BulletListSpec,
)
from src.ppt_engine.diagram_v2.geometry import GeometryNormalizer, Box, Point

logger = logging.getLogger(__name__)

# Typography width model (Arial average advance width as a fraction of the em)
_ARIAL_EM_REGULAR = 0.52
_ARIAL_EM_BOLD = 0.57
_LINE_SPACING = 1.20


def _hex_to_rgb(hex_code: str) -> RGBColor:
    """Converts a hex code (#RRGGBB) to a python-pptx RGBColor."""
    h = hex_code.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _flatten(shape: Any) -> None:
    """
    OpenXML Sanitizer that strips default theme drop shadows and style effects.
    Guarantees flat consulting aesthetic with zero drop shadow inheritance:
    1. Sets shape.shadow.inherit = False (if attribute exists).
    2. Overrides <p:style>/<a:effectRef idx="0"> so theme drop shadows aren't inherited.
    3. Cleans any existing effectLst or outerShdw in spPr and writes an explicit empty <a:effectLst/>.
    """
    try:
        if hasattr(shape, "shadow"):
            shape.shadow.inherit = False
    except Exception:
        pass

    try:
        sp = getattr(shape, "_element", getattr(shape, "element", shape))

        # 1. Reset theme style effectRef to idx="0"
        style = sp.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
        if style is not None:
            effect_ref = style.find("{http://schemas.openxmlformats.org/drawingml/2006/main}effectRef")
            if effect_ref is not None:
                effect_ref.set("idx", "0")

        # 2. Clear out any existing effectLst / outerShdw and inject an explicit empty <a:effectLst/>
        sp_pr = getattr(sp, "spPr", None)
        if sp_pr is not None:
            for child in list(sp_pr):
                if child.tag.endswith("effectLst") or child.tag.endswith("outerShdw"):
                    sp_pr.remove(child)
            sp_pr.append(OxmlElement("a:effectLst"))
    except Exception as e:
        logger.debug("Could not flatten shape: %s", e)


def _set_connector_arrowhead(connector: Any, arrow_type: str = "triangle", at_tail: bool = True) -> None:
    """Attaches an OpenXML DrawingML arrowhead to a connector line."""
    try:
        ln_elem = connector._element.spPr.ln
        tag = "a:tailEnd" if at_tail else "a:headEnd"
        end_elem = OxmlElement(tag)
        end_elem.set("type", arrow_type)
        end_elem.set("w", "med")
        end_elem.set("len", "med")
        ln_elem.append(end_elem)
    except Exception as e:
        logger.debug("Could not attach arrowhead: %s", e)


def _set_round_join(shape: Any) -> None:
    """Applies rounded line joins so polyline elbows bend cleanly."""
    try:
        ln_elem = shape._element.spPr.ln
        ln_elem.append(OxmlElement("a:round"))
    except Exception as e:
        logger.debug("Could not set round join: %s", e)


def _svg_to_png_bytes(svg_path: Path) -> Optional[bytes]:
    """Converts an SVG file to transparent PNG bytes using cairosvg or rsvg-convert."""
    if not svg_path.exists():
        return None

    try:
        import ctypes
        import ctypes.util
        cairo_paths = [
            "/opt/homebrew/lib/libcairo.2.dylib",
            "/opt/homebrew/lib/libcairo.dylib",
            "/usr/local/lib/libcairo.2.dylib",
        ]
        orig_find = ctypes.util.find_library

        def custom_find(name: str) -> Optional[str]:
            if name in ("cairo", "cairo-2", "libcairo-2", "cairo.2", "libcairo"):
                for cp in cairo_paths:
                    if os.path.exists(cp):
                        return cp
            return orig_find(name)

        ctypes.util.find_library = custom_find
        import cairosvg
        return cairosvg.svg2png(bytestring=svg_path.read_bytes(), scale=3.0)
    except Exception:
        pass

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        res = subprocess.run(
            ["rsvg-convert", "-z", "3", str(svg_path), "-o", str(tmp_path)],
            capture_output=True,
        )
        if res.returncode == 0 and tmp_path.exists():
            data = tmp_path.read_bytes()
            tmp_path.unlink()
            return data
    except Exception:
        pass

    return None


def _text_width_in(text: str, pt: float, bold: bool = False) -> float:
    em = _ARIAL_EM_BOLD if bold else _ARIAL_EM_REGULAR
    return len(text) * pt * em / 72.0


def _wrapped_line_count(text: str, pt: float, width_in: float, bold: bool = False) -> int:
    total = 0
    space_w = _text_width_in(" ", pt, bold)
    for segment in text.split("\n"):
        words = segment.split()
        if not words:
            total += 1
            continue
        lines, cur = 1, 0.0
        for word in words:
            ww = _text_width_in(word, pt, bold)
            if cur == 0.0:
                cur = ww
            elif cur + space_w + ww <= width_in:
                cur += space_w + ww
            else:
                lines += 1
                cur = ww
        total += lines
    return total


@dataclass
class _ParaSpec:
    text: str
    pt: float
    bold: bool
    color_hex: str
    space_before_pt: float = 0.0

    def height_in(self, width_in: float) -> float:
        lines = _wrapped_line_count(self.text, self.pt, width_in, self.bold)
        return (lines * self.pt * _LINE_SPACING + self.space_before_pt) / 72.0

    def natural_width_in(self) -> float:
        return max(_text_width_in(seg, self.pt, self.bold) for seg in self.text.split("\n"))


@dataclass
class _CardPlan:
    mode: str
    pad_h: float
    region_top: float
    region_bottom: float
    icon_size: float
    icon_gap: float
    paras: List[_ParaSpec] = field(default_factory=list)
    text_width: float = 0.0
    content_h: float = 0.0

    @property
    def region_h(self) -> float:
        return self.region_bottom - self.region_top


class PPTXCompiler:
    """Compiles a DiagramSpec into a 16:9 widescreen PowerPoint presentation."""

    def __init__(self, spec: DiagramSpec) -> None:
        self.spec = spec
        self.norm = GeometryNormalizer(
            canvas_width=spec.canvas.width,
            canvas_height=spec.canvas.height,
            canvas_unit=spec.canvas.unit,
        )
        self._node_boxes: Dict[str, Box] = {}

    def _plan_card(
        self,
        w: float,
        h: float,
        title: str,
        subtitle: Optional[str],
        kicker: Optional[str],
        stroke_hex: str,
        has_icon: bool,
        is_cylinder: bool,
        icon_layout: str = "auto",
        title_pt: Optional[float] = None,
    ) -> _CardPlan:
        ss = min(w, h)
        pad_v = _clamp(0.11 * ss, 0.10, 0.20)
        pad_h = _clamp(0.07 * w, 0.08, 0.18)

        if is_cylinder:
            pv = pad_v * 0.6
            region_top = 0.25 * ss + pv
            region_bottom = h - 0.125 * ss - pv
        else:
            region_top = pad_v
            region_bottom = h - pad_v

        mode = icon_layout
        if mode == "auto":
            mode = "side" if (is_cylinder and has_icon) else "stack"

        t_pt = title_pt or (12.5 if h >= 1.15 else 11.0)
        s_pt = 9.0
        k_pt = 8.0
        icon = _clamp(0.26 * ss, 0.28, 0.40) if has_icon else 0.0
        if mode == "side" and has_icon:
            icon = min(icon, max(0.26, (region_bottom - region_top) * 0.80))
        icon_gap = _clamp(0.05 * ss, 0.04, 0.08)

        plan = _CardPlan(mode, pad_h, region_top, region_bottom, icon, icon_gap)
        for _ in range(16):
            paras: List[_ParaSpec] = []
            if kicker:
                paras.append(_ParaSpec(kicker.upper(), k_pt, True, stroke_hex))
            paras.append(_ParaSpec(title, t_pt, True, "#0F172A", 1.0 if kicker else 0.0))
            if subtitle:
                paras.append(_ParaSpec(subtitle, s_pt, False, "#64748B", 2.0))

            inner_w = w - 2 * pad_h
            if mode == "side" and has_icon:
                text_w = inner_w - icon - icon_gap * 1.5
                text_h = sum(p.height_in(text_w) for p in paras)
                content = max(icon, text_h)
            else:
                text_w = inner_w
                text_h = sum(p.height_in(text_w) for p in paras)
                content = (icon + icon_gap if has_icon else 0.0) + text_h

            plan.paras, plan.text_width, plan.content_h, plan.icon_size = paras, text_w, content, icon
            if content <= plan.region_h + 1e-6:
                break
            shrunk = False
            if t_pt > 9.5:
                t_pt -= 0.5
                shrunk = True
            if s_pt > 7.5:
                s_pt -= 0.25
                shrunk = True
            if has_icon and icon > 0.24:
                icon -= 0.02
                shrunk = True
            if not shrunk:
                break
        return plan

    def _add_icon(
        self,
        slide: Any,
        x: float,
        y: float,
        size: float,
        icon_path: Optional[Path],
        icon_emoji: Optional[str],
        shape_name: Optional[str] = None,
    ) -> None:
        if icon_path and icon_path.exists():
            png_bytes = _svg_to_png_bytes(icon_path) if icon_path.suffix.lower() == ".svg" else icon_path.read_bytes()
            if png_bytes:
                pic = slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(x), Inches(y), width=Inches(size), height=Inches(size))
                if shape_name:
                    pic.name = shape_name
                _flatten(pic)
                return

        if icon_emoji:
            em_box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(size), Inches(size))
            if shape_name:
                em_box.name = shape_name
            _flatten(em_box)
            tf = em_box.text_frame
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]
            p.text = icon_emoji
            p.alignment = PP_ALIGN.CENTER
            p.font.size = Pt(round(size * 72 * 0.78, 1))

    def _render_paras(self, tf: Any, paras: Sequence[_ParaSpec], align: Any) -> None:
        first_p = True
        for i, spec in enumerate(paras):
            lines = spec.text.split("\n") if "\n" in spec.text else [spec.text]
            for j, line_text in enumerate(lines):
                if first_p:
                    p = tf.paragraphs[0]
                    first_p = False
                else:
                    p = tf.add_paragraph()
                p.text = line_text
                if line_text.strip().startswith("•") or align == PP_ALIGN.LEFT:
                    p.alignment = PP_ALIGN.LEFT
                else:
                    p.alignment = align
                p.font.name = "Arial"
                p.font.size = Pt(spec.pt)
                p.font.bold = spec.bold
                p.font.color.rgb = _hex_to_rgb(spec.color_hex)
                if j == 0 and spec.space_before_pt:
                    p.space_before = Pt(spec.space_before_pt)
                elif line_text.strip().startswith("•") and not (i == 0 and j == 0):
                    p.space_before = Pt(2.5)

    def compile_slide(self, slide: Any) -> None:
        """Compiles the diagram specification elements onto an existing PowerPoint slide."""
        self._node_boxes.clear()

        # 1. Header & Brand Stripes
        if self.spec.header.show:
            self._compile_header(slide)

        # 2. Containers / Boundaries
        for c in self.spec.containers:
            self._compile_container(slide, c)

        # 3. Entity Nodes & Cards
        for n in self.spec.nodes:
            self._compile_node(slide, n)

        # 4. Badges
        for i, b in enumerate(self.spec.badges):
            self._compile_badge(slide, b, idx=i)

        # 5. Bullet Lists
        for i, bl in enumerate(self.spec.bullet_lists):
            self._compile_bullet_list(slide, bl, idx=i)

        # 6. Routed Connectors / Flows
        for i, f in enumerate(self.spec.flows):
            self._compile_flow(slide, f, idx=i)

    def compile_presentation(self, output_path: Union[str, Path]) -> Path:
        """Compiles the diagram specification into a native PowerPoint .pptx file."""
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        self.compile_slide(slide)

        prs.save(str(out_p))
        return out_p

    def _compile_header(self, slide: Any) -> None:
        h = self.spec.header
        hx = h.x if h.x is not None else 0.60
        hy = h.y if h.y is not None else 0.40
        box = self.norm.to_inches(hx, hy, 11.5, 0.85)

        if h.brand_stripes:
            s_red = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(box.x), Inches(box.y), Inches(0.045), Inches(0.55))
            s_red.name = "header:stripe:red"
            s_red.fill.solid()
            s_red.fill.fore_color.rgb = _hex_to_rgb(h.red_hex)
            s_red.line.fill.background()
            _flatten(s_red)

            s_blue = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(box.x + 0.065), Inches(box.y), Inches(0.090), Inches(0.55))
            s_blue.name = "header:stripe:blue"
            s_blue.fill.solid()
            s_blue.fill.fore_color.rgb = _hex_to_rgb(h.blue_hex)
            s_blue.line.fill.background()
            _flatten(s_blue)
            tx = box.x + 0.25
        else:
            tx = box.x
 
        header_w = min(9.8, max(6.0, box.w - tx - 2.8))
        tb = slide.shapes.add_textbox(Inches(tx), Inches(box.y - 0.05), Inches(header_w), Inches(0.85))
        tb.name = "header:title"
        _flatten(tb)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_title = tf.paragraphs[0]
        p_title.text = h.action_title
        p_title.font.name = "Arial"
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = _hex_to_rgb("#0F172A")

        p_sub = tf.add_paragraph()
        p_sub.text = h.subtitle
        p_sub.font.name = "Arial"
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = _hex_to_rgb("#64748B")
        p_sub.space_before = Pt(4)

    def _compile_container(self, slide: Any, c: ContainerSpec) -> None:
        box = self.norm.to_inches(c.x, c.y, c.w, c.h)
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        shape.name = f"container:{c.id}"
        shape.fill.solid()
        shape.fill.fore_color.rgb = _hex_to_rgb(c.fill_hex)
        shape.line.color.rgb = _hex_to_rgb(c.border_hex)
        shape.line.width = Pt(c.stroke_width)
        if c.dashed:
            shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        _flatten(shape)

        # Boundary Label
        if c.label and c.label.strip():
            label_w = (box.w - 2.1) if c.tag_badge else (box.w - 0.4)
            estimated_text_w = max(1.2, min(label_w, len(c.label) * 0.11 + 0.35)) if label_w >= 1.2 else max(0.5, label_w)
            tb = slide.shapes.add_textbox(Inches(box.x + 0.2), Inches(box.y + 0.08), Inches(estimated_text_w), Inches(0.26))
            tb.name = f"container:{c.id}:label"
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.TOP
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = c.label.upper()
            p.font.name = "Arial"
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = _hex_to_rgb(c.border_hex if c.border_hex != "#94A3B8" else "#64748B")

        # Top-Right Badge
        if c.tag_badge:
            badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(box.x2 - 1.8), Inches(box.y + 0.12), Inches(1.6), Inches(0.28))
            badge.name = f"container:{c.id}:tag_badge"
            badge.fill.solid()
            badge.fill.fore_color.rgb = _hex_to_rgb(c.tag_bg_hex)
            badge.line.color.rgb = _hex_to_rgb(c.tag_text_hex)
            badge.line.width = Pt(0.75)
            _flatten(badge)
            tf_b = badge.text_frame
            tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0
            p_b = tf_b.paragraphs[0]
            p_b.text = c.tag_badge.upper()
            p_b.alignment = PP_ALIGN.CENTER
            p_b.font.name = "Arial"
            p_b.font.size = Pt(8.5)
            p_b.font.bold = True
            p_b.font.color.rgb = _hex_to_rgb(c.tag_text_hex)

    def _compile_node(self, slide: Any, n: NodeSpec) -> None:
        box = self.norm.to_inches(n.x, n.y, n.w, n.h if n.h is not None else 1.25)
        self._node_boxes[n.id] = box

        # Resolve Icon
        icon_path: Optional[Path] = None
        if n.icon:
            p = Path(n.icon)
            if p.exists() and p.is_file():
                icon_path = p
            else:
                try:
                    from src.ppt_engine.library_importer import IconRegistry
                    icon_path = IconRegistry.resolve_icon(n.icon)
                except Exception:
                    pass

        has_icon = icon_path is not None or bool(n.icon_emoji)
        is_cylinder = n.is_cylinder or n.shape in ("cylinder", "database")
        shape_type = MSO_SHAPE.CAN if is_cylinder else (MSO_SHAPE.ROUNDED_RECTANGLE if n.is_rounded else MSO_SHAPE.RECTANGLE)

        card = slide.shapes.add_shape(shape_type, Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        card.name = f"node:{n.id}"
        card.fill.solid()
        card.fill.fore_color.rgb = _hex_to_rgb(n.fill_hex)
        card.line.color.rgb = _hex_to_rgb(n.stroke_hex)
        card.line.width = Pt(n.stroke_width)
        _flatten(card)

        plan = self._plan_card(box.w, box.h, n.title, n.subtitle, n.kicker, n.stroke_hex, has_icon, is_cylinder, n.icon_layout, n.title_pt)
        region_top = box.y + plan.region_top
        region_h = plan.region_h

        if plan.mode == "side" and has_icon:
            natural_w = min(plan.text_width, max(p.natural_width_in() for p in plan.paras) + 0.06)
            group_w = plan.icon_size + plan.icon_gap * 1.5 + natural_w
            gx = box.x + plan.pad_h + max(0.0, (box.w - 2 * plan.pad_h - group_w) / 2.0)
            icon_y = region_top + (region_h - plan.icon_size) / 2.0
            self._add_icon(slide, gx, icon_y, plan.icon_size, icon_path, n.icon_emoji, shape_name=f"node:{n.id}:icon")

            tx = gx + plan.icon_size + plan.icon_gap * 1.5
            tb = slide.shapes.add_textbox(Inches(tx), Inches(region_top), Inches(natural_w), Inches(region_h))
            tb.name = f"node:{n.id}:text"
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            self._render_paras(tf, plan.paras, PP_ALIGN.LEFT)
        elif has_icon:
            start_y = region_top + max(0.0, (region_h - plan.content_h) / 2.0)
            self._add_icon(slide, box.x + (box.w - plan.icon_size) / 2.0, start_y, plan.icon_size, icon_path, n.icon_emoji, shape_name=f"node:{n.id}:icon")
            text_top = start_y + plan.icon_size + plan.icon_gap
            text_h = max(0.30, (box.y2 - 0.04) - text_top)
            tb = slide.shapes.add_textbox(Inches(box.x + plan.pad_h), Inches(text_top), Inches(plan.text_width), Inches(text_h))
            tb.name = f"node:{n.id}:text"
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.TOP
            align_choice = PP_ALIGN.LEFT if getattr(n, "align", "center") == "left" else PP_ALIGN.CENTER
            self._render_paras(tf, plan.paras, align_choice)
        else:
            tb = slide.shapes.add_textbox(Inches(box.x + plan.pad_h), Inches(region_top), Inches(plan.text_width), Inches(region_h))
            tb.name = f"node:{n.id}:text"
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.TOP if n.valign == "top" else (MSO_ANCHOR.BOTTOM if n.valign == "bottom" else MSO_ANCHOR.MIDDLE)
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            align_choice = PP_ALIGN.LEFT if getattr(n, "align", "center") == "left" else PP_ALIGN.CENTER
            self._render_paras(tf, plan.paras, align_choice)

    def _compile_badge(self, slide: Any, b: BadgeSpec, idx: int = 0) -> None:
        badge_id = b.id or f"badge_{idx}"
        box = self.norm.to_inches(b.x, b.y, b.w, b.h)
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        pill.name = f"badge:{badge_id}"
        pill.fill.solid()
        pill.fill.fore_color.rgb = _hex_to_rgb(b.bg_hex)
        pill.line.color.rgb = _hex_to_rgb(b.border_hex)
        pill.line.width = Pt(1.0)
        _flatten(pill)

        tf = pill.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = b.text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Arial"
        p.font.size = Pt(b.font_pt)
        p.font.bold = True
        p.font.color.rgb = _hex_to_rgb(b.text_hex)

    def _compile_bullet_list(self, slide: Any, bl: BulletListSpec, idx: int = 0) -> None:
        bl_id = bl.id or f"bullet_list_{idx}"
        box = self.norm.to_inches(bl.x, bl.y, bl.w, bl.h)
        tb = slide.shapes.add_textbox(Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        tb.name = f"bullet_list:{bl_id}"
        _flatten(tb)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        for i, item in enumerate(bl.items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"• {item}"
            p.font.name = "Arial"
            p.font.size = Pt(bl.font_size)
            p.font.bold = True
            p.font.color.rgb = _hex_to_rgb(bl.font_color)
            if i > 0:
                p.space_before = Pt(5)

    def _compile_flow(self, slide: Any, f: FlowSpec, idx: int = 0) -> None:
        flow_id = f.id or (f"{f.source}->{f.target}" if f.source and f.target else f"flow_{idx}")
        pts: List[Point] = []
        if f.points:
            pts = [self.norm.point_to_inches(p) for p in f.points]
        elif f.source and f.target and f.source in self._node_boxes and f.target in self._node_boxes:
            src_box = self._node_boxes[f.source]
            tgt_box = self._node_boxes[f.target]
            pts = GeometryNormalizer.compute_auto_route(src_box, tgt_box, curve=f.curve)

        if len(pts) < 2:
            return

        if len(pts) == 2:
            (x1, y1), (x2, y2) = pts
            line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        else:
            emu_pts = [(int(Inches(px)), int(Inches(py))) for px, py in pts]
            builder = slide.shapes.build_freeform(emu_pts[0][0], emu_pts[0][1], scale=1.0)
            builder.add_line_segments(emu_pts[1:], close=False)
            line = builder.convert_to_shape(Emu(0), Emu(0))
            line.fill.background()
            _set_round_join(line)

        line.name = f"flow:{flow_id}"
        line.line.color.rgb = _hex_to_rgb(f.stroke_hex)
        line.line.width = Pt(f.stroke_width)
        if f.dashed:
            line.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        if f.has_arrow:
            _set_connector_arrowhead(line, arrow_type="triangle", at_tail=True)
        _flatten(line)

        # Label Pill
        if f.label:
            segs = list(zip(pts, pts[1:]))
            best_seg = max(segs, key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
            p1, p2 = best_seg
            is_horiz = abs(p2[1] - p1[1]) < 0.05
            is_vert = abs(p2[0] - p1[0]) < 0.05

            if f.label_at:
                lx, ly = self.norm.point_to_inches(f.label_at)
            else:
                lx = (best_seg[0][0] + best_seg[1][0]) / 2.0
                ly = (best_seg[0][1] + best_seg[1][1]) / 2.0
                pos = f.label_position
                if pos == "auto":
                    if is_horiz:
                        pos = "above" if p2[0] > p1[0] else "below"
                    elif is_vert:
                        pos = "side"
                    else:
                        pos = "above"

                offset_in = f.label_offset if f.label_offset is not None else 0.16

                if pos == "above":
                    ly -= offset_in
                elif pos == "below":
                    ly += offset_in
                elif pos in ("side", "right"):
                    lx += (offset_in * 2.5)
                elif pos == "left":
                    lx -= (offset_in * 2.5)

            lw = round(_text_width_in(f.label, f.font_pt, bold=True) + 0.20, 2)
            lh = 0.22
            pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(lx - lw / 2.0), Inches(ly - lh / 2.0), Inches(lw), Inches(lh))
            pill.name = f"flow:{flow_id}:label"
            pill.fill.solid()
            pill.fill.fore_color.rgb = _hex_to_rgb(f.label_bg_hex)
            pill.line.color.rgb = _hex_to_rgb(f.label_border_hex or f.stroke_hex)
            pill.line.width = Pt(1.0)
            _flatten(pill)

            tf = pill.text_frame
            tf.word_wrap = False
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]
            p.text = f.label
            p.alignment = PP_ALIGN.CENTER
            p.font.name = "Arial"
            p.font.size = Pt(f.font_pt)
            p.font.bold = True
            p.font.color.rgb = _hex_to_rgb(f.label_text_hex)
