"""
Native PowerPoint Diagram Compiler
==================================
Compiles diagram specifications and architecture topologies into 100% native,
fully editable Microsoft PowerPoint (DrawingML) shapes, cards, text frames, and connectors.

Design system (Tier 19):
- **Flat aesthetic:** every emitted shape (autoshapes, freeforms, connectors, pictures,
  text boxes) receives an explicit empty ``<a:effectLst/>`` which overrides the theme
  ``<p:style><a:effectRef>`` drop shadow that python-pptx attaches by default.
- **Proportional padding engine:** card content (icon + kicker + title + subtitle) is
  measured with an Arial width model, wrapped against the inner card width, auto-shrunk
  when it would overflow, and vertically centered so top/bottom optical padding is equal.
  Padding scales with card size (``_plan_card``). Cylinders reserve the 3D rim and the
  bottom arc and use a side-slot icon layout so logos never sit on the top ellipse.
- **Orthogonal routed flows:** connectors are attached to card ports (``Box.left_at`` ...),
  routed as single editable polylines through inter-zone gutters, and audited so no
  segment runs collinear with a zone boundary or card border (``_audit_route``).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Emu, Inches, Pt

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

Point = Tuple[float, float]

# Typography width model (Arial average advance width as a fraction of the em).
_ARIAL_EM_REGULAR = 0.52
_ARIAL_EM_BOLD = 0.57
_LINE_SPACING = 1.20  # PowerPoint single-spacing line box relative to point size

# Routing clearances (inches)
_BORDER_CLEARANCE = 0.12  # min distance between a parallel flow segment and any border
_LABEL_CLEARANCE = 0.10   # min distance between a label pill and a boundary border


def _hex_to_rgb(hex_code: str) -> RGBColor:
    """Converts a '#RRGGBB' hex code to pptx RGBColor."""
    h = hex_code.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _flatten(shape) -> None:
    """
    Strips drop shadows / theme effects from a shape for a flat consulting aesthetic.
    Writes an explicit empty ``<a:effectLst/>`` into ``spPr`` which overrides the
    ``<p:style><a:effectRef idx="2">`` shadow inherited from the default theme.
    """
    try:
        shape.shadow.inherit = False
        return
    except Exception:
        pass
    try:
        sp_pr = shape._element.spPr
        if sp_pr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}effectLst") is None:
            sp_pr.append(OxmlElement("a:effectLst"))
    except Exception as e:  # pragma: no cover - defensive
        logger.debug("Could not flatten shape effects: %s", e)


def _set_connector_arrowhead(connector, arrow_type: str = "triangle", at_tail: bool = True) -> None:
    """
    Attaches an OpenXML arrowhead to a connector line.
    In OpenXML DrawingML, <a:headEnd> is the start point (x1, y1),
    while <a:tailEnd> is the termination point (x2, y2).
    To point towards the destination (x2, y2), at_tail must be True.
    """
    try:
        ln_elem = connector._element.spPr.ln
        tag = "a:tailEnd" if at_tail else "a:headEnd"
        end_elem = OxmlElement(tag)
        end_elem.set("type", arrow_type)
        end_elem.set("w", "med")
        end_elem.set("len", "med")
        ln_elem.append(end_elem)
    except Exception as e:
        logger.debug("Could not attach connector arrowhead: %s", e)


def _set_round_join(shape) -> None:
    """Applies rounded line joins so polyline elbows render as clean bends (no notches)."""
    try:
        ln_elem = shape._element.spPr.ln
        ln_elem.append(OxmlElement("a:round"))
    except Exception as e:
        logger.debug("Could not set round line join: %s", e)


def _svg_to_png_bytes(svg_path: Path, target_dpi: int = 300) -> Optional[bytes]:
    """Converts an SVG file to transparent PNG bytes using cairosvg or rsvg-convert."""
    if not svg_path.exists():
        return None

    try:
        from src.ppt_engine.diagram_engine import _setup_cairo_library
        _setup_cairo_library()
        import cairosvg
        return cairosvg.svg2png(bytestring=svg_path.read_bytes(), scale=3.0)
    except Exception:
        pass

    import subprocess
    import tempfile
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


# -----------------------------------------------------------------------------
# Typography measurement
# -----------------------------------------------------------------------------

def _text_width_in(text: str, pt: float, bold: bool = False) -> float:
    """Estimates the rendered single-line width of Arial text in inches."""
    em = _ARIAL_EM_BOLD if bold else _ARIAL_EM_REGULAR
    return len(text) * pt * em / 72.0


def _wrapped_line_count(text: str, pt: float, width_in: float, bold: bool = False) -> int:
    """Greedy word-wrap line count for text (honours explicit '\\n' breaks)."""
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
class _Para:
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


def _stack_height(paras: Sequence[_Para], width_in: float) -> float:
    return sum(p.height_in(width_in) for p in paras)


# -----------------------------------------------------------------------------
# Geometry primitives
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Box:
    """Axis-aligned rectangle (inches) with connector port helpers."""

    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    # Proportional ports (t in 0..1 along the side)
    def left(self, t: float = 0.5) -> Point:
        return (self.x, self.y + self.h * t)

    def right(self, t: float = 0.5) -> Point:
        return (self.x2, self.y + self.h * t)

    def top(self, t: float = 0.5) -> Point:
        return (self.x + self.w * t, self.y)

    def bottom(self, t: float = 0.5) -> Point:
        return (self.x + self.w * t, self.y2)

    # Absolute ports (attach at a given coordinate along the side)
    def left_at(self, y: float) -> Point:
        return (self.x, y)

    def right_at(self, y: float) -> Point:
        return (self.x2, y)

    def top_at(self, x: float) -> Point:
        return (x, self.y)

    def bottom_at(self, x: float) -> Point:
        return (x, self.y2)


@dataclass
class _CardPlan:
    """Resolved content layout for a card (all offsets relative to card origin)."""

    mode: str                 # 'stack' | 'side'
    pad_h: float
    region_top: float
    region_bottom: float
    icon_size: float
    icon_gap: float
    paras: List[_Para] = field(default_factory=list)
    text_width: float = 0.0
    content_h: float = 0.0

    @property
    def region_h(self) -> float:
        return self.region_bottom - self.region_top


class PowerPointDiagramCompiler:
    """Compiles diagram topologies into native, fully editable PowerPoint DrawingML slides."""

    def __init__(self) -> None:
        self._boundaries: List[Box] = []
        self._cards: List[Box] = []

    def create_deck(self) -> Presentation:
        """Initializes a 16:9 widescreen presentation (13.333" x 7.5")."""
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        return prs

    def _new_slide(self, prs: Presentation):
        """Adds a blank slide and resets per-slide routing obstacle registries."""
        self._boundaries = []
        self._cards = []
        return prs.slides.add_slide(prs.slide_layouts[6])

    # -------------------------------------------------------------------------
    # Primitive Builders
    # -------------------------------------------------------------------------

    def add_unified_header(
        self,
        slide,
        action_title: str,
        subtitle: str,
        tracker: Optional[str] = None,
        x: float = 0.6,
        y: float = 0.4,
    ) -> None:
        """
        Renders an authentic enterprise header with dual brand accent stripes
        (1 Red : 2 Blue ratio) and unified Title + Subtitle flow.
        """
        # Metrodata dual brand stripes
        s_red = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(0.045), Inches(0.55))
        s_red.fill.solid()
        s_red.fill.fore_color.rgb = _hex_to_rgb("#E11D48")
        s_red.line.fill.background()
        _flatten(s_red)

        s_blue = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 0.065), Inches(y), Inches(0.090), Inches(0.55))
        s_blue.fill.solid()
        s_blue.fill.fore_color.rgb = _hex_to_rgb("#0284C7")
        s_blue.line.fill.background()
        _flatten(s_blue)

        # Text Frame for Title & Subtitle (unified flow)
        tx_box = slide.shapes.add_textbox(Inches(x + 0.25), Inches(y - 0.05), Inches(11.5), Inches(0.85))
        _flatten(tx_box)
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_title = tf.paragraphs[0]
        p_title.text = action_title
        p_title.font.name = "Arial"
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = _hex_to_rgb("#0F172A")

        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.name = "Arial"
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = _hex_to_rgb("#64748B")
        p_sub.space_before = Pt(4)

    def add_container_boundary(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: float,
        label: str,
        border_hex: str = "#94A3B8",
        fill_hex: str = "#F8FAFC",
        tag_badge: Optional[str] = None,
        tag_bg_hex: str = "#FEF3C7",
        tag_text_hex: str = "#B45309",
    ) -> Box:
        """Adds a dashed zone boundary container with top/right labels."""
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = _hex_to_rgb(fill_hex)
        shape.line.color.rgb = _hex_to_rgb(border_hex)
        shape.line.width = Pt(1.5)
        shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        _flatten(shape)

        # Boundary Label
        tb = slide.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.10), Inches(w - 0.4), Inches(0.45))
        _flatten(tb)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = label.upper()
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = _hex_to_rgb(border_hex if border_hex != "#94A3B8" else "#64748B")

        # Optional Top-Right Tag Badge (e.g. "CLOUDERA CDSW")
        if tag_badge:
            badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x + w - 1.8), Inches(y + 0.12), Inches(1.6), Inches(0.28))
            badge.fill.solid()
            badge.fill.fore_color.rgb = _hex_to_rgb(tag_bg_hex)
            badge.line.color.rgb = _hex_to_rgb(tag_text_hex)
            badge.line.width = Pt(0.75)
            _flatten(badge)
            tf_b = badge.text_frame
            tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0
            p_b = tf_b.paragraphs[0]
            p_b.text = tag_badge
            p_b.alignment = PP_ALIGN.CENTER
            p_b.font.name = "Arial"
            p_b.font.size = Pt(8.5)
            p_b.font.bold = True
            p_b.font.color.rgb = _hex_to_rgb(tag_text_hex)

        box = Box(x, y, w, h)
        self._boundaries.append(box)
        return box

    # -------------------------------------------------------------------------
    # Proportional Content Padding Engine
    # -------------------------------------------------------------------------

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
        """
        Computes uniform, size-proportional padding and content metrics for a card.

        - Padding scales with the card's short side (``ss``) and width.
        - Cylinders (``MSO_SHAPE.CAN``) reserve the top ellipse (0.25·ss) and the
          bottom front arc (0.125·ss) so content lives on the body face only.
        - Fonts and icon shrink in small steps until content fits the inner region.
        """
        ss = min(w, h)
        pad_v = _clamp(0.11 * ss, 0.10, 0.20)
        pad_h = _clamp(0.07 * w, 0.08, 0.18)

        if is_cylinder:
            # Rim geometry already provides visual breathing room; use a lighter pad.
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
            paras: List[_Para] = []
            if kicker:
                paras.append(_Para(kicker.upper(), k_pt, True, stroke_hex))
            paras.append(_Para(title, t_pt, True, "#0F172A", 1.0 if kicker else 0.0))
            if subtitle:
                paras.append(_Para(subtitle, s_pt, False, "#64748B", 2.0))

            inner_w = w - 2 * pad_h
            if mode == "side" and has_icon:
                text_w = inner_w - icon - icon_gap * 1.5
                text_h = _stack_height(paras, text_w)
                content = max(icon, text_h)
            else:
                text_w = inner_w
                text_h = _stack_height(paras, text_w)
                content = (icon + icon_gap if has_icon else 0.0) + text_h

            plan.paras, plan.text_width, plan.content_h, plan.icon_size = paras, text_w, content, icon
            if content <= plan.region_h + 1e-6:
                break
            # Graceful shrink: title first, then subtitle, then icon.
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
                logger.warning("Card '%s' content (%.2f\") exceeds inner region (%.2f\").", title, content, plan.region_h)
                break
        return plan

    def measure_card_height(
        self,
        w: float,
        title: str,
        subtitle: Optional[str] = None,
        kicker: Optional[str] = None,
        has_icon: bool = False,
        is_cylinder: bool = False,
        title_pt: Optional[float] = None,
    ) -> float:
        """Returns the minimum card height that fits content with proportional padding."""
        h = 1.0
        for _ in range(6):
            plan = self._plan_card(w, 4.0, title, subtitle, kicker, "#000000", has_icon, is_cylinder, title_pt=title_pt)
            ss = min(w, h)
            pad_v = _clamp(0.11 * ss, 0.10, 0.20)
            if is_cylinder:
                overhead = 0.375 * ss + 2 * pad_v * 0.6
            else:
                overhead = 2 * pad_v
            h = round(plan.content_h + overhead + 0.02, 2)
        return h

    def _render_paras(self, tf, paras: Sequence[_Para], align) -> None:
        for i, spec in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = spec.text
            p.alignment = align
            p.font.name = "Arial"
            p.font.size = Pt(spec.pt)
            p.font.bold = spec.bold
            p.font.color.rgb = _hex_to_rgb(spec.color_hex)
            if spec.space_before_pt:
                p.space_before = Pt(spec.space_before_pt)

    def _add_icon(self, slide, x: float, y: float, size: float, icon_path: Optional[Path], icon_emoji: Optional[str]) -> None:
        if icon_path is not None:
            png_bytes = _svg_to_png_bytes(icon_path)
            if png_bytes:
                pic = slide.shapes.add_picture(io.BytesIO(png_bytes), Inches(x), Inches(y), width=Inches(size), height=Inches(size))
                _flatten(pic)
                return
        if icon_emoji:
            em_box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(size), Inches(size))
            _flatten(em_box)
            tf_em = em_box.text_frame
            tf_em.margin_left = tf_em.margin_top = tf_em.margin_right = tf_em.margin_bottom = 0
            tf_em.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_em = tf_em.paragraphs[0]
            p_em.text = icon_emoji
            p_em.alignment = PP_ALIGN.CENTER
            p_em.font.size = Pt(round(size * 72 * 0.78, 1))

    def add_card(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: Optional[float],
        title: str,
        subtitle: Optional[str] = None,
        kicker: Optional[str] = None,
        stroke_hex: str = "#3B82F6",
        fill_hex: str = "#FFFFFF",
        icon_path: Optional[Path] = None,
        icon_emoji: Optional[str] = None,
        is_rounded: bool = True,
        is_cylinder: bool = False,
        icon_layout: str = "auto",
        title_pt: Optional[float] = None,
        stroke_pt: float = 2.0,
    ) -> Box:
        """
        Adds a native editable card container with title, subtitle, and vector logo.

        Content is laid out by the proportional padding engine (``_plan_card``):
        equal top/bottom optical padding, wrap-aware text measurement, and automatic
        font/icon shrink. Pass ``h=None`` to auto-size the card height to its content.
        Cylinders default to a side-slot icon layout inside the body (never on the rim).
        """
        resolved_icon = icon_path if (icon_path is not None and icon_path.exists()) else None
        has_icon = resolved_icon is not None or bool(icon_emoji)
        if h is None:
            h = self.measure_card_height(w, title, subtitle, kicker, has_icon, is_cylinder, title_pt)

        shape_type = MSO_SHAPE.CAN if is_cylinder else (MSO_SHAPE.ROUNDED_RECTANGLE if is_rounded else MSO_SHAPE.RECTANGLE)
        card = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
        card.fill.solid()
        card.fill.fore_color.rgb = _hex_to_rgb(fill_hex)
        card.line.color.rgb = _hex_to_rgb(stroke_hex)
        card.line.width = Pt(stroke_pt)
        _flatten(card)

        plan = self._plan_card(w, h, title, subtitle, kicker, stroke_hex, has_icon, is_cylinder, icon_layout, title_pt)
        region_top = y + plan.region_top
        region_h = plan.region_h

        if plan.mode == "side" and has_icon:
            # Side slot: [icon] [left-aligned text], group centered horizontally on the body.
            natural_w = min(plan.text_width, max(p.natural_width_in() for p in plan.paras) + 0.06)
            group_w = plan.icon_size + plan.icon_gap * 1.5 + natural_w
            gx = x + plan.pad_h + max(0.0, (w - 2 * plan.pad_h - group_w) / 2.0)
            icon_y = region_top + (region_h - plan.icon_size) / 2.0
            self._add_icon(slide, gx, icon_y, plan.icon_size, resolved_icon, icon_emoji)

            tx = gx + plan.icon_size + plan.icon_gap * 1.5
            tb = slide.shapes.add_textbox(Inches(tx), Inches(region_top), Inches(natural_w), Inches(region_h))
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            self._render_paras(tf, plan.paras, PP_ALIGN.LEFT)
        elif has_icon:
            # Stack: icon above text, whole group vertically centered (equal top/bottom padding).
            start_y = region_top + max(0.0, (region_h - plan.content_h) / 2.0)
            self._add_icon(slide, x + (w - plan.icon_size) / 2.0, start_y, plan.icon_size, resolved_icon, icon_emoji)
            text_top = start_y + plan.icon_size + plan.icon_gap
            # Top-anchored, so extending the frame to the card's inner edge (stroke inset)
            # does not move glyphs; it only grants overflow headroom.
            text_h = max(0.30, (y + h - 0.04) - text_top)
            tb = slide.shapes.add_textbox(Inches(x + plan.pad_h), Inches(text_top), Inches(plan.text_width), Inches(text_h))
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.TOP
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            self._render_paras(tf, plan.paras, PP_ALIGN.CENTER)
        else:
            # Text-only: anchor middle across the padded region for exact optical centering.
            tb = slide.shapes.add_textbox(Inches(x + plan.pad_h), Inches(region_top), Inches(plan.text_width), Inches(region_h))
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            self._render_paras(tf, plan.paras, PP_ALIGN.CENTER)

        box = Box(x, y, w, h)
        self._cards.append(box)
        return box

    def add_pill_badge(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        bg_hex: str,
        text_hex: str,
        border_hex: str,
        font_pt: float = 9.0,
    ) -> Box:
        """Adds a native standalone status or warning pill badge."""
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        pill.fill.solid()
        pill.fill.fore_color.rgb = _hex_to_rgb(bg_hex)
        pill.line.color.rgb = _hex_to_rgb(border_hex)
        pill.line.width = Pt(1.0)
        _flatten(pill)

        tf = pill.text_frame
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Arial"
        p.font.size = Pt(font_pt)
        p.font.bold = True
        p.font.color.rgb = _hex_to_rgb(text_hex)
        return Box(x, y, w, h)

    def add_bullet_list(
        self,
        slide,
        x: float,
        y: float,
        w: float,
        h: float,
        items: List[str],
        font_size: float = 11.5,
    ) -> None:
        """Adds native bullet text items."""
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        _flatten(tb)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"• {item}"
            p.font.name = "Arial"
            p.font.size = Pt(font_size)
            p.font.bold = True
            p.font.color.rgb = _hex_to_rgb("#0F172A")
            if i > 0:
                p.space_before = Pt(5)

    # -------------------------------------------------------------------------
    # Flow Routing (orthogonal polylines, port-anchored, border-audited)
    # -------------------------------------------------------------------------

    def add_flow_label(
        self,
        slide,
        cx: float,
        cy: float,
        text: str,
        border_hex: str,
        bg_hex: str,
        text_hex: str,
        font_pt: float = 8.5,
    ) -> Box:
        """Adds a label pill centered on a flow segment, auto-sized to its text."""
        w = round(_text_width_in(text, font_pt, bold=True) + 0.24, 2)
        h = 0.24
        box = self.add_pill_badge(slide, cx - w / 2.0, cy - h / 2.0, w, h, text, bg_hex, text_hex, border_hex, font_pt=font_pt)
        self._audit_label(box, text)
        return box

    def _audit_route(self, points: Sequence[Point], name: str) -> None:
        """
        Warns when a flow segment runs collinear with (inlines along) a zone boundary
        border or a card border. Perpendicular crossings are allowed.
        """
        edges: List[Tuple[str, float, float, float, str]] = []  # (orient, const, lo, hi, owner)
        for b in self._boundaries:
            edges += [("h", b.y, b.x, b.x2, "boundary"), ("h", b.y2, b.x, b.x2, "boundary"),
                      ("v", b.x, b.y, b.y2, "boundary"), ("v", b.x2, b.y, b.y2, "boundary")]
        for c in self._cards:
            edges += [("h", c.y, c.x, c.x2, "card"), ("h", c.y2, c.x, c.x2, "card"),
                      ("v", c.x, c.y, c.y2, "card"), ("v", c.x2, c.y, c.y2, "card")]

        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            if abs(y1 - y2) < 1e-6:
                orient, const, lo, hi = "h", y1, min(x1, x2), max(x1, x2)
            elif abs(x1 - x2) < 1e-6:
                orient, const, lo, hi = "v", x1, min(y1, y2), max(y1, y2)
            else:
                logger.warning("Flow '%s' has a non-orthogonal segment (%.2f,%.2f)->(%.2f,%.2f).", name, x1, y1, x2, y2)
                continue
            for e_orient, e_const, e_lo, e_hi, owner in edges:
                if e_orient != orient:
                    continue
                overlap = min(hi, e_hi) - max(lo, e_lo)
                if overlap > 0.05 and abs(const - e_const) < _BORDER_CLEARANCE:
                    logger.warning(
                        "Flow '%s' segment inlines with a %s border (offset %.2f\" < %.2f\").",
                        name, owner, abs(const - e_const), _BORDER_CLEARANCE,
                    )

    def _audit_label(self, pill: Box, text: str) -> None:
        """Warns when a label pill sits on (or too close to) a boundary border."""
        c = _LABEL_CLEARANCE
        for b in self._boundaries:
            for bx in (b.x, b.x2):
                if pill.x - c < bx < pill.x2 + c and pill.y2 > b.y and pill.y < b.y2:
                    logger.warning("Label '%s' collides with a vertical boundary border at x=%.2f.", text, bx)
            for by in (b.y, b.y2):
                if pill.y - c < by < pill.y2 + c and pill.x2 > b.x and pill.x < b.x2:
                    logger.warning("Label '%s' collides with a horizontal boundary border at y=%.2f.", text, by)

    def add_routed_flow(
        self,
        slide,
        points: Sequence[Point],
        stroke_hex: str = "#2563EB",
        label: Optional[str] = None,
        label_at: Optional[Point] = None,
        label_bg_hex: str = "#EFF6FF",
        label_text_hex: str = "#1D4ED8",
        has_arrow: bool = True,
        dashed: bool = False,
        width_pt: float = 2.0,
        name: Optional[str] = None,
    ) -> None:
        """
        Draws an orthogonal flow as ONE editable shape: a straight connector for
        2-point routes, or an open freeform polyline (rounded joins) for multi-bend
        routes. The arrowhead sits on the final point (``<a:tailEnd>``).
        """
        if len(points) < 2:
            raise ValueError("A routed flow needs at least two points.")
        flow_name = name or label or "flow"
        self._audit_route(points, flow_name)

        if len(points) == 2:
            (x1, y1), (x2, y2) = points
            line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        else:
            emu_pts = [(int(Inches(px)), int(Inches(py))) for px, py in points]
            builder = slide.shapes.build_freeform(emu_pts[0][0], emu_pts[0][1], scale=1.0)
            builder.add_line_segments(emu_pts[1:], close=False)
            line = builder.convert_to_shape(Emu(0), Emu(0))
            line.fill.background()

        line.line.color.rgb = _hex_to_rgb(stroke_hex)
        line.line.width = Pt(width_pt)
        if dashed:
            line.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        if len(points) > 2:
            _set_round_join(line)
        if has_arrow:
            _set_connector_arrowhead(line, arrow_type="triangle", at_tail=True)
        _flatten(line)

        if label:
            if label_at is None:
                (ax, ay), (bx, by) = max(zip(points, points[1:]), key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
                label_at = ((ax + bx) / 2.0, (ay + by) / 2.0)
            self.add_flow_label(slide, label_at[0], label_at[1], label, stroke_hex, label_bg_hex, label_text_hex)

    def add_connector_flow(
        self,
        slide,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: Optional[str] = None,
        stroke_hex: str = "#2563EB",
        label_bg_hex: str = "#EFF6FF",
        label_text_hex: str = "#1D4ED8",
        label_x: Optional[float] = None,
        label_y: Optional[float] = None,
        is_curved: bool = False,
        has_arrow: bool = True,
        dashed: bool = False,
    ) -> None:
        """
        Adds a native PowerPoint connector line with destination arrowhead and optional label badge.
        Legacy point-to-point API: ``is_curved`` now emits a deterministic horizontal-vertical-horizontal
        orthogonal route (mid-x elbow) instead of PowerPoint's auto-elbow. ``label_x``/``label_y`` are
        interpreted as the label CENTER when provided.
        """
        if is_curved and abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
            mx = (x1 + x2) / 2.0
            pts: List[Point] = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
        else:
            pts = [(x1, y1), (x2, y2)]
        label_at = (label_x, label_y) if (label_x is not None and label_y is not None) else None
        self.add_routed_flow(
            slide, pts, stroke_hex=stroke_hex, label=label, label_at=label_at,
            label_bg_hex=label_bg_hex, label_text_hex=label_text_hex, has_arrow=has_arrow, dashed=dashed,
        )

    # -------------------------------------------------------------------------
    # High-Level Slide Compilers
    # -------------------------------------------------------------------------
    # Layout grid (both slides): Client zone x=0.60..3.50 | 1.30" gutter (center x=4.15) |
    # right-hand zones from x=4.80. Every label pill sits centered in a gutter so it never
    # straddles a dashed boundary border; every flow crosses borders perpendicularly.

    _CLIENT_ZONE = Box(0.60, 1.35, 2.90, 4.60)
    _GUTTER_X = 4.15

    def build_slide_1_cdsw_process(self, prs: Presentation) -> None:
        """Compiles Slide 1: Current Legacy CDSW Job Execution into native PowerPoint shapes."""
        slide = self._new_slide(prs)

        # 1. Header
        self.add_unified_header(
            slide,
            action_title="Current: Legacy CDSW Job Execution",
            subtitle="Monolithic Synchronous Batch Processing & Bottleneck Lifecycle Dataflow",
        )

        # 2. Zones (drawn first = bottom of z-order)
        cz = self._CLIENT_ZONE
        self.add_container_boundary(slide, cz.x, cz.y, cz.w, cz.h, label="Client Applications",
                                    border_hex="#94A3B8", fill_hex="#F8FAFC")
        self.add_container_boundary(
            slide, x=4.80, y=1.35, w=7.90, h=4.60,
            label="Backend Execution Boundary",
            border_hex="#F59E0B", fill_hex="#FFFBEB",
            tag_badge="CLOUDERA CDSW", tag_bg_hex="#FEF3C7", tag_text_hex="#B45309",
        )

        # 3. Node geometry (main flow row aligned on y=2.75 so flows 1 & 2 are straight)
        row_y = 2.75
        app1 = Box(1.35, row_y - 0.575, 1.40, 1.15)
        app2 = Box(0.80, 4.05, 1.15, 1.15)
        app3 = Box(2.15, 4.05, 1.15, 1.15)
        cdsw = Box(5.20, row_y - 0.80, 2.30, 1.60)
        task = Box(8.50, row_y - 0.475, 2.20, 0.95)
        self._cards = [app1, app2, app3, cdsw, task]

        # 4. Flows (beneath cards so line ends tuck under card borders)
        self.add_routed_flow(
            slide, [app1.right_at(row_y), cdsw.left_at(row_y)],
            stroke_hex="#2563EB", label="1. EXE Call", label_at=(self._GUTTER_X, row_y),
            label_bg_hex="#EFF6FF", label_text_hex="#1D4ED8",
        )
        self.add_routed_flow(
            slide, [cdsw.right_at(row_y), task.left_at(row_y)],
            stroke_hex="#0284C7", label="2. Run", label_at=((cdsw.x2 + task.x) / 2.0, row_y),
            label_bg_hex="#F0F9FF", label_text_hex="#0369A1",
        )
        # 3. Return: east out of the task, down the right-hand channel, west along the
        # bottom channel (0.40" above the zone floor, 0.35" below app cards).
        channel_y = 5.55
        return_x = 11.80
        self.add_routed_flow(
            slide,
            [task.right_at(row_y), (return_x, row_y), (return_x, channel_y), (self._GUTTER_X, channel_y)],
            stroke_hex="#D97706", label="3. Return", label_at=(8.00, channel_y),
            label_bg_hex="#FFFBEB", label_text_hex="#B45309", has_arrow=False,
        )
        # 4. Response: hand-off in the gutter, then up into app3's bottom port.
        self.add_routed_flow(
            slide,
            [(self._GUTTER_X, channel_y), (app3.cx, channel_y), app3.bottom()],
            stroke_hex="#2563EB", label="4. Response", label_at=(self._GUTTER_X, channel_y),
            label_bg_hex="#EFF6FF", label_text_hex="#1D4ED8",
        )

        # 5. Cards
        for box, name, sub in ((app1, "app1", "Device 1"), (app2, "app2", "Device 2"), (app3, "app3", "Device 3")):
            self.add_card(slide, box.x, box.y, box.w, box.h, title=name, subtitle=sub, icon_emoji="🖥️")

        cdsw_svg = _REPO_ROOT / "assets" / "logos" / "cloudera" / "cloudera_cdsw.svg"
        self.add_card(
            slide, cdsw.x, cdsw.y, cdsw.w, cdsw.h,
            title="CDSW JOB",
            subtitle="Cloudera Data Science\nWorkbench Job Runner",
            stroke_hex="#0284C7", fill_hex="#FFFFFF",
            icon_path=cdsw_svg if cdsw_svg.exists() else None,
        )
        self.add_card(
            slide, task.x, task.y, task.w, task.h,
            title="1 Task", title_pt=22, stroke_hex="#DC2626", fill_hex="#FFFFFF", stroke_pt=2.5,
        )

        # Warning Pills (above the task card)
        pill_y = task.y - 0.45
        self.add_pill_badge(slide, x=task.x, y=pill_y, w=1.40, h=0.28, text="⚠️ BOTTLENECK",
                            bg_hex="#FEE2E2", text_hex="#DC2626", border_hex="#FECACA")
        self.add_pill_badge(slide, x=task.x + 1.55, y=pill_y, w=1.55, h=0.28, text="⚠️ SYNCHRONOUS",
                            bg_hex="#FEF3C7", text_hex="#B45309", border_hex="#FDE68A")

        # Step Bullet List
        self.add_bullet_list(
            slide, x=task.x, y=3.55, w=2.90, h=1.55,
            items=["Input metadata", "SQL Query", "Filter & Search Dev. ADD", "Logging", "Return to sender"],
            font_size=11.5,
        )

    def build_slide_2_aws_lambda(self, prs: Presentation) -> None:
        """Compiles Slide 2: Proposed AWS Lambda Serverless Architecture into native PowerPoint shapes."""
        slide = self._new_slide(prs)

        # 1. Header
        self.add_unified_header(
            slide,
            action_title="Proposed: AWS Lambda",
            subtitle="Serverless Architecture & Execution Lifecycle Dataflow",
        )

        # 2. Zones
        cz = self._CLIENT_ZONE
        self.add_container_boundary(slide, cz.x, cz.y, cz.w, 5.25, label="Client Applications",
                                    border_hex="#94A3B8", fill_hex="#F8FAFC")
        cloud = self.add_container_boundary(slide, x=8.10, y=1.35, w=4.80, h=3.85, label="AWS Cloud",
                                            border_hex="#F59E0B", fill_hex="#FFFBEB")

        # 3. Node geometry
        req_y, resp_y = 2.50, 5.75           # request row / response row
        mid_gutter_x = (6.90 + cloud.x) / 2.0  # gutter between gateway and AWS Cloud (x=7.50)

        app1 = Box(1.35, req_y - 0.55, 1.40, 1.10)
        app2 = Box(0.80, resp_y - 0.60, 1.15, 1.20)
        app3 = Box(2.15, resp_y - 0.60, 1.15, 1.20)
        api_gw = Box(4.80, 2.10, 2.10, 2.70)
        code = Box(8.45, 1.85, 1.60, 1.30)
        secret = Box(10.60, 1.85, 2.00, 1.30)
        lam = Box(8.45, 3.65, 4.15, 1.30)
        dbx = Box(secret.cx - 0.85, 5.75, 1.70, 1.35)
        self._cards = [app1, app2, app3, api_gw, code, secret, lam, dbx]

        deliver_x = 9.00  # lambda bottom port

        # 4. Flows
        # Flow 1. Request: Client App1 -> API Gateway (straight horizontal)
        self.add_routed_flow(
            slide, [app1.right_at(req_y), api_gw.left_at(req_y)],
            stroke_hex="#2563EB", label="1. Request", label_at=(4.15, req_y),
            label_bg_hex="#EFF6FF", label_text_hex="#1D4ED8",
        )
        # Flow 2. Invoke: API Gateway -> AWS Lambda (clean straight horizontal forward flow)
        invoke_y = 3.90
        self.add_routed_flow(
            slide,
            [api_gw.right_at(invoke_y), lam.left_at(invoke_y)],
            stroke_hex="#7C3AED", label="2. Invoke", label_at=(7.50, invoke_y),
            label_bg_hex="#F5F3FF", label_text_hex="#6D28D9",
        )
        # Code deployment into Lambda
        self.add_routed_flow(
            slide, [code.bottom(), lam.top_at(code.cx)],
            stroke_hex="#10B981", name="Code deploy",
        )
        # Secrets injection into Lambda
        self.add_routed_flow(
            slide, [secret.bottom(), lam.top_at(secret.cx)],
            stroke_hex="#EF4444", label="3. Secrets", label_at=(secret.cx, (secret.y2 + lam.y) / 2.0),
            label_bg_hex="#FEF2F2", label_text_hex="#991B1B", dashed=True,
        )
        # DBX SQL Query
        self.add_routed_flow(
            slide, [lam.bottom_at(dbx.cx), dbx.top()],
            stroke_hex="#0284C7", label="4. DBX Query", label_at=(dbx.cx, (cloud.y2 + dbx.y) / 2.0),
            label_bg_hex="#F0F9FF", label_text_hex="#0369A1",
        )
        # Flow 5. Deliver: AWS Lambda -> API Gateway (clean straight horizontal return flow)
        deliver_y = 4.55
        self.add_routed_flow(
            slide,
            [lam.left_at(deliver_y), api_gw.right_at(deliver_y)],
            stroke_hex="#7C3AED", label="5. Deliver", label_at=(7.50, deliver_y),
            label_bg_hex="#F5F3FF", label_text_hex="#6D28D9",
        )
        # Flow 6. Response: API Gateway -> Client App3 (downward routed return flow)
        exit_resp_y = 4.30
        self.add_routed_flow(
            slide, [api_gw.left_at(exit_resp_y), (self._GUTTER_X, exit_resp_y), (self._GUTTER_X, resp_y), app3.right_at(resp_y)],
            stroke_hex="#2563EB", label="6. Response", label_at=(self._GUTTER_X, (exit_resp_y + resp_y) / 2.0),
            label_bg_hex="#EFF6FF", label_text_hex="#1D4ED8",
        )

        # 5. Cards
        for box, name, sub in ((app1, "app1", "Device 1"), (app2, "app2", "Device 2"), (app3, "app3", "Device 3")):
            self.add_card(slide, box.x, box.y, box.w, box.h, title=name, subtitle=sub, icon_emoji="🖥️")

        gw_svg = _REPO_ROOT / "assets" / "logos" / "aws" / "aws_api_gateway.svg"
        self.add_card(
            slide, api_gw.x, api_gw.y, api_gw.w, api_gw.h,
            title="API Gateway", subtitle="HTTP / REST Endpoints\n& Response Delivery", kicker="API Gateway",
            stroke_hex="#8B5CF6", fill_hex="#F5F3FF", icon_path=gw_svg if gw_svg.exists() else None,
        )
        self.add_card(
            slide, code.x, code.y, code.w, code.h,
            title="Code", subtitle="DEPLOYED", stroke_hex="#10B981", fill_hex="#ECFDF5",
        )
        sec_svg = _REPO_ROOT / "assets" / "logos" / "aws" / "aws_secrets_manager.svg"
        self.add_card(
            slide, secret.x, secret.y, secret.w, secret.h,
            title="Secret Management", subtitle="KMS / Secrets Manager", kicker="Security",
            stroke_hex="#EF4444", fill_hex="#FEF2F2", icon_path=sec_svg if sec_svg.exists() else None,
        )
        lambda_svg = _REPO_ROOT / "assets" / "logos" / "aws" / "aws_lambda.svg"
        self.add_card(
            slide, lam.x, lam.y, lam.w, lam.h,
            title="AWS Lambda", subtitle="(Aws Lamda)\nServerless Compute",
            stroke_hex="#D97706", fill_hex="#FFFFFF", icon_path=lambda_svg if lambda_svg.exists() else None,
        )
        dbx_svg = _REPO_ROOT / "assets" / "logos" / "databricks" / "databricks.svg"
        self.add_card(
            slide, dbx.x, dbx.y, dbx.w, dbx.h,
            title="DBX", subtitle="Databricks / DB",
            stroke_hex="#0284C7", fill_hex="#F0F9FF",
            icon_path=dbx_svg if dbx_svg.exists() else None,
            is_cylinder=True,  # side-slot icon inside the body, clear of the 3D rim
        )

    def build_slide_3_comparison(self, prs: Presentation) -> None:
        """Compiles Slide 3: Combined Before vs After Architecture Modernization Comparison."""
        slide = self._new_slide(prs)

        # 1. Unified Header
        self.add_unified_header(
            slide,
            action_title="Device Whitelisting: Architecture Evolution (Before vs. After)",
            subtitle="Comparative Modernization Analysis: Legacy CDSW Monolith vs. Proposed AWS Lambda Serverless",
        )

        # Status Badge
        self.add_pill_badge(
            slide, x=10.30, y=0.45, w=2.40, h=0.32,
            text="MODERNIZATION DELTA SPEC",
            bg_hex="#EFF6FF", text_hex="#1D4ED8", border_hex="#BFDBFE", font_pt=8.5,
        )

        # 2. Executive Delta Ribbon
        ribbon_y = 1.25
        ribbon_h = 0.45
        ribbon = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.60), Inches(ribbon_y), Inches(12.10), Inches(ribbon_h))
        ribbon.fill.solid()
        ribbon.fill.fore_color.rgb = _hex_to_rgb("#F8FAFC")
        ribbon.line.color.rgb = _hex_to_rgb("#CBD5E1")
        ribbon.line.width = Pt(1.0)
        _flatten(ribbon)

        # Ribbon text boxes (4 KPIs)
        kpis = [
            ("EXECUTION MODEL", "Sequential Batch", "Event-Driven Serverless", 0.70, 2.90),
            ("INGRESS GATEWAY", "Direct Binary EXE", "Managed HTTPS REST API", 3.75, 2.90),
            ("CREDENTIAL SECURITY", "Script Environment", "AWS Secrets Mgr & KMS", 6.80, 2.90),
            ("DATA PERSISTENCE", "Shared Cluster Store", "Databricks Lakehouse (DBX)", 9.85, 2.75),
        ]
        for label, before, after, kx, kw in kpis:
            tb = slide.shapes.add_textbox(Inches(kx), Inches(ribbon_y + 0.05), Inches(kw), Inches(0.35))
            _flatten(tb)
            tf = tb.text_frame
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.font.name = "Arial"
            p.font.size = Pt(8.5)
            r1 = p.add_run()
            r1.text = f"{label}: "
            r1.font.bold = True
            r1.font.color.rgb = _hex_to_rgb("#64748B")
            r2 = p.add_run()
            r2.text = f"{before} ➔ "
            r2.font.bold = True
            r2.font.color.rgb = _hex_to_rgb("#DC2626")
            r3 = p.add_run()
            r3.text = after
            r3.font.bold = True
            r3.font.color.rgb = _hex_to_rgb("#16A34A")

        # 3. Two Side-by-Side Architectural Summary Containers
        box_y = 1.85
        box_h = 2.65
        box_w = 5.95

        # Left: Current Legacy CDSW
        left_b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.60), Inches(box_y), Inches(box_w), Inches(box_h))
        left_b.fill.solid()
        left_b.fill.fore_color.rgb = _hex_to_rgb("#FFFDFB")
        left_b.line.color.rgb = _hex_to_rgb("#FCA5A5")
        left_b.line.width = Pt(1.5)
        _flatten(left_b)

        left_th = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.60), Inches(box_y), Inches(box_w), Inches(0.42))
        left_th.fill.solid()
        left_th.fill.fore_color.rgb = _hex_to_rgb("#FEF2F2")
        left_th.line.color.rgb = _hex_to_rgb("#FECACA")
        left_th.line.width = Pt(1.0)
        _flatten(left_th)
        tf_lth = left_th.text_frame
        tf_lth.margin_left = Inches(0.2)
        p_lth = tf_lth.paragraphs[0]
        p_lth.text = "BEFORE: Current Legacy CDSW Job Execution"
        p_lth.font.name = "Arial"
        p_lth.font.size = Pt(11)
        p_lth.font.bold = True
        p_lth.font.color.rgb = _hex_to_rgb("#991B1B")

        self.add_pill_badge(slide, x=5.05, y=box_y + 0.08, w=1.35, h=0.25, text="⚠️ BOTTLENECK", bg_hex="#FEE2E2", text_hex="#DC2626", border_hex="#FECACA", font_pt=8.0)

        left_bullets = [
            "Execution Topology: Monolithic scheduled batch runner running on shared CDSW cluster node.",
            "Ingress Trigger: Direct local executable (EXE) invocation lacking TLS, auth, or throttling.",
            "Concurrency Lock: Serialized 1-task queue forces concurrent client requests to stall and timeout.",
            "Credential Security: Plaintext database connection tokens stored directly in script filesystem.",
        ]
        self.add_bullet_list(slide, x=0.75, y=box_y + 0.50, w=box_w - 0.30, h=box_h - 0.55, items=left_bullets, font_size=9.5)

        # Right: Proposed AWS Lambda
        right_b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.75), Inches(box_y), Inches(box_w), Inches(box_h))
        right_b.fill.solid()
        right_b.fill.fore_color.rgb = _hex_to_rgb("#F0FDF4")
        right_b.line.color.rgb = _hex_to_rgb("#86EFAC")
        right_b.line.width = Pt(1.5)
        _flatten(right_b)

        right_th = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.75), Inches(box_y), Inches(box_w), Inches(0.42))
        right_th.fill.solid()
        right_th.fill.fore_color.rgb = _hex_to_rgb("#ECFDF5")
        right_th.line.color.rgb = _hex_to_rgb("#A7F3D0")
        right_th.line.width = Pt(1.0)
        _flatten(right_th)
        tf_rth = right_th.text_frame
        tf_rth.margin_left = Inches(0.2)
        p_rth = tf_rth.paragraphs[0]
        p_rth.text = "AFTER: Proposed AWS Lambda Serverless"
        p_rth.font.name = "Arial"
        p_rth.font.size = Pt(11)
        p_rth.font.bold = True
        p_rth.font.color.rgb = _hex_to_rgb("#065F46")

        self.add_pill_badge(slide, x=11.20, y=box_y + 0.08, w=1.35, h=0.25, text="✓ AUTO-SCALING", bg_hex="#DCFCE7", text_hex="#15803D", border_hex="#BBF7D0", font_pt=8.0)

        right_bullets = [
            "Execution Topology: Decoupled on-demand serverless functions scaling 0 to 1,000+ instances.",
            "Ingress Trigger: Single Unified API Gateway endpoint enforcing TLS termination & IAM auth.",
            "Concurrency Lock: Sub-second parallel execution eliminates queue starvation & thread lockouts.",
            "Credential Security: Zero-Trust AWS Secrets Manager & KMS with dynamic ephemeral token rotation.",
        ]
        self.add_bullet_list(slide, x=6.90, y=box_y + 0.50, w=box_w - 0.30, h=box_h - 0.55, items=right_bullets, font_size=9.5)

        # 4. Bottom Native PowerPoint Table (Architectural Delta Matrix)
        tbl_y = 4.65
        tbl_w = 12.10
        tbl_h = 2.30
        rows = 4
        cols = 4
        tbl_shape = slide.shapes.add_table(rows, cols, Inches(0.60), Inches(tbl_y), Inches(tbl_w), Inches(tbl_h))
        _flatten(tbl_shape)
        table = tbl_shape.table
        table.columns[0].width = Inches(2.00)
        table.columns[1].width = Inches(3.20)
        table.columns[2].width = Inches(3.40)
        table.columns[3].width = Inches(3.50)

        headers = ["ARCHITECTURAL PILLAR", "CURRENT STATE (LEGACY CDSW)", "TARGET STATE (AWS LAMBDA)", "STRATEGIC BUSINESS IMPACT"]
        for ci, h_text in enumerate(headers):
            cell = table.cell(0, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _hex_to_rgb("#F1F5F9")
            p = cell.text_frame.paragraphs[0]
            p.text = h_text
            p.font.name = "Arial"
            p.font.size = Pt(8.5)
            p.font.bold = True
            p.font.color.rgb = _hex_to_rgb("#DC2626" if ci == 1 else ("#16A34A" if ci == 2 else ("#2563EB" if ci == 3 else "#475569")))

        matrix_data = [
            ("Throughput & Latency", "Serialized 1-task queue (>30-60s batch latency)", "Concurrent micro-compute (<150ms cold, <25ms warm)", "Eliminates client timeouts; empowers instantaneous device whitelist verification"),
            ("Credential Security", "Plaintext tokens in script files; unmanaged access keys", "AWS Secrets Manager + KMS with dynamic IAM rotation", "Remediates P1 audit findings; ensures strict SOC2 & ISO 27001 compliance"),
            ("Blast Radius & SLA", "Single query crash aborts entire batch; manual CDSW restart", "Per-request micro-isolation; automated DLQ & retry policies", "Prevents cascading outages across apps; guarantees 99.99% availability SLA"),
        ]
        for ri, (col0, col1, col2, col3) in enumerate(matrix_data, start=1):
            for ci, val in enumerate((col0, col1, col2, col3)):
                cell = table.cell(ri, ci)
                cell.fill.solid()
                cell.fill.fore_color.rgb = _hex_to_rgb("#FFFFFF" if ri % 2 == 1 else "#F8FAFC")
                p = cell.text_frame.paragraphs[0]
                p.text = val
                p.font.name = "Arial"
                p.font.size = Pt(8.5)
                if ci == 0:
                    p.font.bold = True
                    p.font.color.rgb = _hex_to_rgb("#0F172A")
                elif ci == 1:
                    p.font.color.rgb = _hex_to_rgb("#991B1B")
                elif ci == 2:
                    p.font.color.rgb = _hex_to_rgb("#065F46")
                else:
                    p.font.color.rgb = _hex_to_rgb("#334155")

    def build_slide_interwoven_migration(self, prs: Presentation) -> None:
        """Compiles Slide 3: Unified Interwoven Migration Architecture with single shared client origin."""
        slide = self._new_slide(prs)
        self.add_unified_header(
            slide,
            action_title="Device Whitelisting: Interwoven Migration Topology",
            subtitle="Unified Architecture: Decommissioning Monolithic CDSW Batch (Upper Track) vs. Activating AWS Serverless (Lower Track)",
        )
        img_path = _REPO_ROOT / "TEMP" / "whitelist_system_interwoven_migration.png"
        if img_path.exists():
            pic = slide.shapes.add_picture(str(img_path), Inches(0.60), Inches(1.25), width=Inches(12.13))
            _flatten(pic)

    def build_slide_4_visual_plate(self, prs: Presentation) -> None:
        """Embeds the full high-resolution Before & After architecture visual plate."""
        slide = self._new_slide(prs)
        self.add_unified_header(
            slide,
            action_title="Architecture Evolution: High-Resolution Topology Plate",
            subtitle="Full End-to-End System Diagram: Legacy CDSW Monolith vs. Target AWS Serverless",
        )
        img_path = _REPO_ROOT / "TEMP" / "whitelist_system_before_after_comparison.png"
        if img_path.exists():
            pic = slide.shapes.add_picture(str(img_path), Inches(0.60), Inches(1.25), width=Inches(12.10))
            _flatten(pic)

    def compile_presentation(self, output_path: Union[str, Path]) -> Path:
        """Compiles the complete 5-slide editable architecture presentation."""
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        prs = self.create_deck()
        self.build_slide_1_cdsw_process(prs)
        self.build_slide_2_aws_lambda(prs)
        self.build_slide_interwoven_migration(prs)
        self.build_slide_3_comparison(prs)
        self.build_slide_4_visual_plate(prs)

        prs.save(str(out_p))
        return out_p


