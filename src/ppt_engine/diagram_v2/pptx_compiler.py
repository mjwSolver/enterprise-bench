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
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

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
    DeckHeaderContract,
    NodeSpec,
    FlowSpec,
    BadgeSpec,
    BulletListSpec,
    classify_geometric_tier,
    CANONICAL_TYPOGRAPHIC_SCALE,
)
from src.ppt_engine.diagram_v2.geometry import GeometryNormalizer, Box, Point
from src.ppt_engine.icon_engine import recolor_svg, normalize_color, is_multicolor_vendor_logo

logger = logging.getLogger(__name__)

# In-memory cache for converted PNG bytes: (resolved_svg_path_str, target_color) -> png_bytes
_PNG_BYTES_CACHE: Dict[Tuple[str, Optional[str]], bytes] = {}

# Typography width model (Arial average advance width as a fraction of the em)
_ARIAL_EM_REGULAR = 0.52
_ARIAL_EM_BOLD = 0.57
_LINE_SPACING = 1.20


def _hex_to_rgb(hex_code: Optional[str]) -> RGBColor:
    """Converts a hex code (#RRGGBB) to a python-pptx RGBColor."""
    if not hex_code:
        return RGBColor(0, 0, 0)
    h = re.sub(r"[^0-9a-fA-F]", "", str(hex_code))
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    elif len(h) >= 6:
        h = h[:6]
    else:
        h = h.ljust(6, "0")
    try:
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception:
        return RGBColor(0, 0, 0)


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
            # Schema sequence: ln, effectLst, effectDag, scene3d, sp3d, extLst
            ext_lst = sp_pr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}extLst")
            effect_lst = OxmlElement("a:effectLst")
            if ext_lst is not None:
                sp_pr.insert(sp_pr.index(ext_lst), effect_lst)
            else:
                sp_pr.append(effect_lst)
    except Exception as e:
        logger.debug("Could not flatten shape: %s", e)


def _set_connector_arrowhead(connector: Any, arrow_type: str = "triangle", at_tail: bool = True) -> None:
    """Attaches an OpenXML DrawingML arrowhead to a connector line."""
    try:
        sp_pr = connector._element.spPr
        ln_elem = getattr(sp_pr, "ln", None)
        if ln_elem is None:
            ln_elem = sp_pr.get_or_add_ln()
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


def _svg_to_png_bytes(svg_path: Path, target_color: Optional[str] = None) -> Optional[bytes]:
    """Converts an SVG file to transparent PNG bytes using cairosvg or rsvg-convert."""
    if not svg_path.exists():
        return None

    cache_key = (str(svg_path.resolve()), target_color)
    if cache_key in _PNG_BYTES_CACHE:
        return _PNG_BYTES_CACHE[cache_key]

    try:
        svg_text = svg_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        svg_text = ""

    if not svg_text:
        return None

    if target_color:
        if not is_multicolor_vendor_logo(svg_path, svg_text):
            try:
                svg_text = recolor_svg(svg_text, target_color)
            except Exception as e:
                logger.debug("Failed to recolor SVG %s: %s", svg_path, e)

    svg_bytes = svg_text.encode("utf-8")

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
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes, scale=3.0)
        if png_bytes:
            _PNG_BYTES_CACHE[cache_key] = png_bytes
            return png_bytes
    except Exception:
        pass

    tmp_path: Optional[Path] = None
    tmp_svg: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp_s:
            tmp_s.write(svg_bytes)
            tmp_svg = Path(tmp_s.name)
        res = subprocess.run(
            ["rsvg-convert", "-z", "3", str(tmp_svg), "-o", str(tmp_path)],
            capture_output=True,
        )
        if res.returncode == 0 and tmp_path.exists():
            png_bytes = tmp_path.read_bytes()
            if png_bytes:
                _PNG_BYTES_CACHE[cache_key] = png_bytes
                return png_bytes
    except Exception:
        pass
    finally:
        if tmp_svg is not None and tmp_svg.exists():
            try:
                tmp_svg.unlink()
            except OSError:
                pass
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    return None


def _text_width_in(text: str, pt: float, bold: bool = False) -> float:
    em = _ARIAL_EM_BOLD if bold else _ARIAL_EM_REGULAR
    return len(text) * pt * em / 72.0


def _wrapped_line_count(text: str, pt: float, width_in: float, bold: bool = False) -> int:
    if width_in <= 0.0:
        return max(1, len(text.split()))
    pt = max(1.0, float(pt))
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
        segments = [s for s in self.text.split("\n") if s.strip()]
        extra_space = (len(segments) - 1) * self.space_before_pt if len(segments) > 1 else 0.0
        return (lines * self.pt * _LINE_SPACING + self.space_before_pt + extra_space) / 72.0

    def natural_width_in(self) -> float:
        return max((_text_width_in(seg, self.pt, self.bold) for seg in self.text.split("\n")), default=0.0)


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
        self._container_boxes: Dict[str, Box] = {}

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
        subtitle_pt: Optional[float] = None,
        align: str = "center",
        valign: str = "middle",
        elastic_text: Optional[bool] = None,
        bullets: Optional[List[str]] = None,
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

        tier = classify_geometric_tier(w, h)
        scale_dict = CANONICAL_TYPOGRAPHIC_SCALE.get(tier, CANONICAL_TYPOGRAPHIC_SCALE["Tier B"])
        t_pt = title_pt or scale_dict["title_pt"]
        s_pt = subtitle_pt or scale_dict.get("subtitle_pt", 9.0)
        k_pt = scale_dict.get("kicker_pt", 8.0) or 8.0
        icon = _clamp(0.26 * ss, 0.28, 0.40) if has_icon else 0.0
        if mode == "side" and has_icon:
            icon = min(icon, max(0.26, (region_bottom - region_top) * 0.80))
        icon_gap = _clamp(0.05 * ss, 0.04, 0.08)

        plan = _CardPlan(mode, pad_h, region_top, region_bottom, icon, icon_gap)
        shrunk_during_loop = False
        for _ in range(16):
            paras: List[_ParaSpec] = []
            if kicker:
                paras.append(_ParaSpec(kicker.upper(), k_pt, True, stroke_hex))
            paras.append(_ParaSpec(title, t_pt, True, "#0F172A", 1.0 if kicker else 0.0))
            if subtitle:
                paras.append(_ParaSpec(subtitle, s_pt, False, "#64748B", 2.0))
            if bullets:
                for b in bullets:
                    b_str = str(b)
                    paras.append(_ParaSpec(b_str if b_str.startswith("•") else f"• {b_str}", s_pt, False, "#64748B", 2.0))

            inner_w = max(0.20, w - 2 * pad_h)
            if mode == "side" and has_icon:
                text_w = max(0.20, inner_w - icon - icon_gap * 1.5)
                text_h = sum(p.height_in(text_w) for p in paras)
                content = max(icon, text_h)
            else:
                text_w = inner_w
                text_h = sum(p.height_in(text_w) for p in paras)
                content = (icon + icon_gap if has_icon else 0.0) + text_h

            plan.paras, plan.text_width, plan.content_h, plan.icon_size = paras, text_w, content, icon
            if content <= plan.region_h + 1e-6:
                break
            shrunk_during_loop = True
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

        # Step 2, 3 & 4: Elastic Typography Auto-Fill for Underfilled Execution Cards
        if not shrunk_during_loop and elastic_text is not False:
            is_forced = elastic_text is True
            qualifies = is_forced
            if not is_forced and elastic_text is None:
                if title_pt is None and subtitle_pt is None:
                    title_lines_cnt = len([s for s in title.split("\n") if s.strip()]) if title else 1
                    sub_lines_cnt = len([s for s in subtitle.split("\n") if s.strip()]) if subtitle else 0
                    bullet_cnt = len(bullets) if bullets else 0
                    total_items = title_lines_cnt + sub_lines_cnt + bullet_cnt
                    init_occ = plan.content_h / plan.region_h if plan.region_h > 0 else 1.0
                    if h >= 1.80 and align in ("left", "center") and valign in ("top", "middle") and total_items <= 6 and init_occ < 0.55:
                        qualifies = True

            if qualifies:
                cur_t = t_pt
                cur_s = s_pt
                all_title_lines = [s for s in title.split("\n") if s.strip()] if title else []
                all_sub_lines = ([s for s in subtitle.split("\n") if s.strip()] if subtitle else []) + (bullets or [])

                while cur_s < 12.0:
                    cand_s = cur_s + 0.5
                    cand_t = min(16.5, cur_t + 0.5)

                    # Zero-wrapping check
                    wraps = False
                    for line in all_title_lines:
                        if _text_width_in(line, cand_t, bold=True) > plan.text_width:
                            wraps = True
                            break
                    if wraps:
                        break
                    for line in all_sub_lines:
                        b_line = line if (line.startswith("•") or not bullets) else f"• {line}"
                        if _text_width_in(b_line, cand_s, bold=False) > plan.text_width:
                            wraps = True
                            break
                    if wraps:
                        break

                    cand_sp = _clamp(2.0 + 2.0 * (cand_s - 9.0) / (12.0 - 9.0), 2.0, 4.0)

                    cand_paras: List[_ParaSpec] = []
                    if kicker:
                        cand_paras.append(_ParaSpec(kicker.upper(), k_pt, True, stroke_hex))
                    cand_paras.append(_ParaSpec(title, cand_t, True, "#0F172A", 1.0 if kicker else 0.0))
                    if subtitle:
                        cand_paras.append(_ParaSpec(subtitle, cand_s, False, "#64748B", cand_sp))
                    if bullets:
                        for b in bullets:
                            b_str = str(b)
                            cand_paras.append(_ParaSpec(b_str if b_str.startswith("•") else f"• {b_str}", cand_s, False, "#64748B", cand_sp))

                    if mode == "side" and has_icon:
                        cand_text_h = sum(p.height_in(plan.text_width) for p in cand_paras)
                        cand_content = max(plan.icon_size, cand_text_h)
                    else:
                        cand_text_h = sum(p.height_in(plan.text_width) for p in cand_paras)
                        cand_content = (plan.icon_size + plan.icon_gap if has_icon else 0.0) + cand_text_h

                    if cand_content > 0.85 * plan.region_h + 1e-6:
                        break

                    cur_s = cand_s
                    cur_t = cand_t
                    plan.paras = cand_paras
                    plan.content_h = cand_content

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
        icon_color: Optional[str] = None,
    ) -> None:
        if icon_path and icon_path.exists():
            png_bytes = (
                _svg_to_png_bytes(icon_path, target_color=icon_color)
                if icon_path.suffix.lower() == ".svg"
                else icon_path.read_bytes()
            )
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
                if align == PP_ALIGN.CENTER:
                    p.alignment = PP_ALIGN.CENTER
                elif line_text.strip().startswith("•") or align == PP_ALIGN.LEFT:
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
        self._node_boxes = {
            n.id: self.norm.to_inches(n.x, n.y, n.w, n.h if n.h is not None else 1.25)
            for n in self.spec.nodes
        }
        self._container_boxes = {
            c.id: self.norm.to_inches(c.x, c.y, c.w, c.h)
            for c in self.spec.containers
        }

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

        # Ensure open presentation is dismissed in PowerPoint before overwriting to prevent stale cache/race condition
        try:
            from src.cli.utils import close_target_presentation
            close_target_presentation(out_p)
        except Exception as ex:
            logger.debug("close_target_presentation failed or skipped: %s", ex)

        prs.save(str(out_p))
        return out_p

    def _compile_header(self, slide: Any) -> None:
        h = self.spec.header
        hx = h.x if h.x is not None else DeckHeaderContract.STRIPES_LEFT_IN
        hy = h.y if h.y is not None else DeckHeaderContract.STRIPES_TOP_IN
        box = self.norm.to_inches(hx, hy, 11.5, DeckHeaderContract.TITLE_H_IN)

        if h.brand_stripes:
            s_red = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(box.x),
                Inches(box.y),
                Inches(DeckHeaderContract.STRIPE_RED_W_IN),
                Inches(DeckHeaderContract.STRIPES_H_IN),
            )
            s_red.name = "header:stripe:red"
            s_red.fill.solid()
            s_red.fill.fore_color.rgb = _hex_to_rgb(h.red_hex)
            s_red.line.fill.background()
            _flatten(s_red)

            s_blue_x = box.x + DeckHeaderContract.STRIPE_RED_W_IN + DeckHeaderContract.STRIPES_GAP_IN
            s_blue = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(s_blue_x),
                Inches(box.y),
                Inches(DeckHeaderContract.STRIPE_BLUE_W_IN),
                Inches(DeckHeaderContract.STRIPES_H_IN),
            )
            s_blue.name = "header:stripe:blue"
            s_blue.fill.solid()
            s_blue.fill.fore_color.rgb = _hex_to_rgb(h.blue_hex)
            s_blue.line.fill.background()
            _flatten(s_blue)
            tx = box.x + (DeckHeaderContract.TITLE_LEFT_WITH_STRIPES_IN - DeckHeaderContract.STRIPES_LEFT_IN)
            title_w = h.w if h.w is not None else DeckHeaderContract.TITLE_W_WITH_STRIPES_IN
        else:
            tx = box.x
            title_w = h.w if h.w is not None else DeckHeaderContract.TITLE_W_NO_STRIPES_IN

        title_y = box.y - (DeckHeaderContract.STRIPES_TOP_IN - DeckHeaderContract.TITLE_TOP_IN)
        tb = slide.shapes.add_textbox(Inches(tx), Inches(title_y), Inches(title_w), Inches(DeckHeaderContract.TITLE_H_IN))
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

    def _resolve_container_label_x(
        self,
        c: ContainerSpec,
        box: Box,
        estimated_text_w: float,
        valign: str,
        align: str,
    ) -> float:
        default_x = (
            (box.x + (box.w - estimated_text_w) / 2.0)
            if align == "center"
            else (box.x + 0.2 if align == "left" else box.x2 - estimated_text_w - 0.2)
        )

        if valign != "bottom":
            return default_x

        # Obstruction detection: nodes inside container extending into bottom boundary band
        bottom_threshold = box.y2 - 0.40
        obstructing_nodes: List[Box] = []
        for n in self.spec.nodes:
            nbox = self._node_boxes.get(n.id) or self.norm.to_inches(n.x, n.y, n.w, n.h if n.h is not None else 1.25)
            is_inside = (n.container_id == c.id) or (
                nbox.cx >= box.x and nbox.cx <= box.x2 and nbox.cy >= box.y and nbox.cy <= box.y2
            )
            if is_inside and nbox.y2 > bottom_threshold:
                obstructing_nodes.append(nbox)

        if not obstructing_nodes:
            return default_x

        # Check if default label position collides with any obstructing node
        label_x1 = default_x
        label_x2 = default_x + estimated_text_w
        collides = False
        for ob in obstructing_nodes:
            if max(0.0, min(label_x2, ob.x2) - max(label_x1, ob.x)) > 0.05:
                collides = True
                break

        if not collides:
            return default_x

        # Obstruction detected: partition bottom boundary into open segments
        pad = 0.20
        min_x = box.x + pad
        max_x = box.x2 - pad
        if min_x >= max_x:
            return default_x

        intervals: List[Tuple[float, float]] = []
        for ob in obstructing_nodes:
            ix1 = max(min_x, ob.x - 0.05)
            ix2 = min(max_x, ob.x2 + 0.05)
            if ix1 < ix2:
                intervals.append((ix1, ix2))

        intervals.sort(key=lambda item: item[0])
        merged: List[Tuple[float, float]] = []
        for iv in intervals:
            if not merged or iv[0] > merged[-1][1]:
                merged.append(iv)
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], iv[1]))

        open_segments: List[Tuple[float, float]] = []
        curr = min_x
        for iv_start, iv_end in merged:
            if iv_start > curr:
                open_segments.append((curr, iv_start))
            curr = max(curr, iv_end)
        if curr < max_x:
            open_segments.append((curr, max_x))

        if not open_segments:
            return default_x

        # Pick widest open segment that fits text, or widest open segment overall
        fitting = [s for s in open_segments if (s[1] - s[0]) >= estimated_text_w]
        target_segments = fitting if fitting else open_segments
        widest_seg = max(target_segments, key=lambda s: s[1] - s[0])
        seg_w = widest_seg[1] - widest_seg[0]

        if align == "center":
            new_x = widest_seg[0] + max(0.0, (seg_w - estimated_text_w) / 2.0)
        elif align == "left":
            new_x = widest_seg[0]
        else:
            new_x = widest_seg[1] - estimated_text_w

        return max(box.x + 0.1, min(box.x2 - estimated_text_w - 0.1, new_x))

    def _compile_container(self, slide: Any, c: ContainerSpec) -> None:
        box = self._container_boxes.get(c.id) or self.norm.to_inches(c.x, c.y, c.w, c.h)
        self._container_boxes[c.id] = box
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        shape.name = f"container:{c.id}"
        shape.fill.solid()
        shape.fill.fore_color.rgb = _hex_to_rgb(c.fill_hex)
        shape.line.color.rgb = _hex_to_rgb(c.border_hex)
        shape.line.width = Pt(c.stroke_width)
        if c.dashed:
            shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        _flatten(shape)

        valign = c.resolved_vertical_align()
        align = c.resolved_align()

        # Boundary Label
        if c.label and c.label.strip():
            label_w = (box.w - 2.1) if (c.tag_badge and valign == "top") else (box.w - 0.4)
            estimated_text_w = max(0.8, min(label_w, len(c.label) * 0.08 + 0.30)) if label_w >= 0.8 else max(0.5, label_w)
            label_y = (box.y2 - 0.32) if valign == "bottom" else (box.y + 0.08)
            label_x = self._resolve_container_label_x(c, box, estimated_text_w, valign, align)
            tb = slide.shapes.add_textbox(Inches(label_x), Inches(label_y), Inches(estimated_text_w), Inches(0.26))
            tb.name = f"container:{c.id}:label"
            _flatten(tb)
            tf = tb.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.BOTTOM if valign == "bottom" else MSO_ANCHOR.TOP
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = c.label.upper()
            p.alignment = PP_ALIGN.CENTER if align == "center" else (PP_ALIGN.LEFT if align == "left" else PP_ALIGN.RIGHT)
            p.font.name = "Arial"
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = _hex_to_rgb(c.border_hex if c.border_hex != "#94A3B8" else "#64748B")

        # Top-Right Badge (always decoupled at box.y + 0.12)
        if c.tag_badge:
            bw = min(1.6, max(0.6, box.w - 0.2))
            bx = box.x2 - bw - 0.10
            badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(bx), Inches(box.y + 0.12), Inches(bw), Inches(0.28))
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
        box = self._node_boxes.get(n.id) or self.norm.to_inches(n.x, n.y, n.w, n.h if n.h is not None else 1.25)
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
                    if icon_path is None:
                        logger.warning("Diagram V2: Node '%s' specified icon '%s' which could not be resolved in IconRegistry.", n.id, n.icon)
                except Exception as ex:
                    logger.warning("Diagram V2: Exception resolving icon '%s' on node '%s': %s", n.icon, n.id, ex)

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

        resolved_icon_col = n.icon_color or (n.stroke_hex if n.stroke_hex and n.stroke_hex.upper() not in ("#000000", "#64748B", "#FFFFFF", "#0F172A", "#334155") else None)

        plan = self._plan_card(
            box.w,
            box.h,
            n.title,
            n.subtitle,
            n.kicker,
            n.stroke_hex,
            has_icon,
            is_cylinder,
            n.icon_layout,
            n.title_pt,
            n.subtitle_pt,
            align=getattr(n, "align", "center"),
            valign=getattr(n, "valign", "middle"),
            elastic_text=getattr(n, "elastic_text", None),
            bullets=getattr(n, "bullets", None),
        )
        region_top = box.y + plan.region_top
        region_h = plan.region_h

        if plan.mode == "side" and has_icon:
            natural_w = min(plan.text_width, max((p.natural_width_in() for p in plan.paras), default=0.20) + 0.06)
            group_w = plan.icon_size + plan.icon_gap * 1.5 + natural_w
            gx = box.x + plan.pad_h + max(0.0, (box.w - 2 * plan.pad_h - group_w) / 2.0)
            icon_y = region_top + (region_h - plan.icon_size) / 2.0
            self._add_icon(slide, gx, icon_y, plan.icon_size, icon_path, n.icon_emoji, shape_name=f"node:{n.id}:icon", icon_color=resolved_icon_col)

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
            self._add_icon(slide, box.x + (box.w - plan.icon_size) / 2.0, start_y, plan.icon_size, icon_path, n.icon_emoji, shape_name=f"node:{n.id}:icon", icon_color=resolved_icon_col)
            text_top = start_y + plan.icon_size + plan.icon_gap
            text_h = max(0.30, (box.y2 - 0.04) - text_top)

            bullet_paras = [p for p in plan.paras if p.text.strip().startswith("•")]
            title_paras = [p for p in plan.paras if not p.text.strip().startswith("•")]
            if getattr(n, "align", "center") == "center" and bullet_paras and title_paras:
                title_h = sum(p.height_in(plan.text_width) for p in title_paras)
                natural_bw = max(p.natural_width_in() for p in bullet_paras)
                bw = min(plan.text_width, natural_bw + 0.15)
                bullet_h = sum(p.height_in(bw) for p in bullet_paras)
                gap = 0.08

                # Centered Title
                tb_title = slide.shapes.add_textbox(Inches(box.x + plan.pad_h), Inches(text_top), Inches(plan.text_width), Inches(title_h + 0.05))
                tb_title.name = f"node:{n.id}:title"
                _flatten(tb_title)
                tf_title = tb_title.text_frame
                tf_title.word_wrap = True
                tf_title.vertical_anchor = MSO_ANCHOR.TOP
                tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
                self._render_paras(tf_title, title_paras, PP_ALIGN.CENTER)

                # Centered-Block Left-Aligned Bullets
                bx = box.cx - bw / 2.0
                by = text_top + title_h + gap
                tb_bullet = slide.shapes.add_textbox(Inches(bx), Inches(by), Inches(bw), Inches(bullet_h + 0.05))
                tb_bullet.name = f"node:{n.id}:text"
                _flatten(tb_bullet)
                tf_bullet = tb_bullet.text_frame
                tf_bullet.word_wrap = True
                tf_bullet.vertical_anchor = MSO_ANCHOR.TOP
                tf_bullet.margin_left = tf_bullet.margin_top = tf_bullet.margin_right = tf_bullet.margin_bottom = 0
                self._render_paras(tf_bullet, bullet_paras, PP_ALIGN.LEFT)
            else:
                tb = slide.shapes.add_textbox(Inches(box.x + plan.pad_h), Inches(text_top), Inches(plan.text_width), Inches(text_h))
                tb.name = f"node:{n.id}:text"
                _flatten(tb)
                tf = tb.text_frame
                tf.word_wrap = True
                tf.vertical_anchor = MSO_ANCHOR.TOP
                align_choice = PP_ALIGN.LEFT if getattr(n, "align", "center") == "left" else PP_ALIGN.CENTER
                self._render_paras(tf, plan.paras, align_choice)
        else:
            bullet_paras = [p for p in plan.paras if p.text.strip().startswith("•")]
            title_paras = [p for p in plan.paras if not p.text.strip().startswith("•")]
            if getattr(n, "align", "center") == "center" and bullet_paras:
                natural_bw = max(p.natural_width_in() for p in bullet_paras)
                bw = min(plan.text_width, natural_bw + 0.15)
                bullet_h = sum(p.height_in(bw) for p in bullet_paras)
                title_h = sum(p.height_in(plan.text_width) for p in title_paras) if title_paras else 0.0
                gap = 0.12 if title_paras else 0.0
                total_h = title_h + gap + bullet_h

                if n.valign == "top":
                    top_y = region_top
                elif n.valign == "bottom":
                    top_y = box.y2 - total_h - plan.pad_h
                else:
                    top_y = region_top + max(0.0, (region_h - total_h) / 2.0)

                # Centered Title (if present)
                if title_paras:
                    tb_title = slide.shapes.add_textbox(Inches(box.x + plan.pad_h), Inches(top_y), Inches(plan.text_width), Inches(title_h + 0.05))
                    tb_title.name = f"node:{n.id}:title"
                    _flatten(tb_title)
                    tf_title = tb_title.text_frame
                    tf_title.word_wrap = True
                    tf_title.vertical_anchor = MSO_ANCHOR.TOP
                    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
                    self._render_paras(tf_title, title_paras, PP_ALIGN.CENTER)

                # Centered-Block Left-Aligned Bullets
                bx = box.cx - bw / 2.0
                by = top_y + (title_h + gap if title_paras else 0.0)
                tb_bullet = slide.shapes.add_textbox(Inches(bx), Inches(by), Inches(bw), Inches(bullet_h + 0.05))
                tb_bullet.name = f"node:{n.id}:text"
                _flatten(tb_bullet)
                tf_bullet = tb_bullet.text_frame
                tf_bullet.word_wrap = True
                tf_bullet.vertical_anchor = MSO_ANCHOR.TOP
                tf_bullet.margin_left = tf_bullet.margin_top = tf_bullet.margin_right = tf_bullet.margin_bottom = 0
                self._render_paras(tf_bullet, bullet_paras, PP_ALIGN.LEFT)
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

    _render_node = _compile_node

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
        p.font.size = Pt(b.font_pt or 9.0)
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
            p.font.size = Pt(bl.font_size or 10.0)
            p.font.bold = True
            p.font.color.rgb = _hex_to_rgb(bl.font_color)
            if i > 0:
                p.space_before = Pt(5)

    def _compile_flow(self, slide: Any, f: FlowSpec, idx: int = 0) -> None:
        flow_id = f.id or (f"{f.source}->{f.target}" if f.source and f.target else f"flow_{idx}")
        pts: List[Point] = []
        all_boxes = {**self._container_boxes, **self._node_boxes}
        if f.points:
            pts = [self.norm.point_to_inches(p) for p in f.points if len(p) >= 2]
        elif f.source and f.target and f.source in all_boxes and f.target in all_boxes:
            src_box = all_boxes[f.source]
            tgt_box = all_boxes[f.target]
            pts = GeometryNormalizer.compute_auto_route(
                src_box,
                tgt_box,
                curve=f.curve,
                src_port=f.source_port,
                tgt_port=f.target_port,
            )

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

            flow_font_pt = f.font_pt or 9.0
            label_lines = f.label.split("\n")
            max_seg_w = max((_text_width_in(seg, flow_font_pt, bold=True) for seg in label_lines), default=0.0)
            lw = round(max_seg_w + 0.20, 2)
            lh = round(len(label_lines) * (flow_font_pt * 1.25 / 72.0) + 0.08, 2)
            pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(lx - lw / 2.0), Inches(ly - lh / 2.0), Inches(lw), Inches(lh))
            pill.name = f"flow:{flow_id}:label"
            pill.fill.solid()
            pill.fill.fore_color.rgb = _hex_to_rgb(f.label_bg_hex)
            pill.line.color.rgb = _hex_to_rgb(f.label_border_hex or f.stroke_hex)
            pill.line.width = Pt(1.0)
            _flatten(pill)

            tf = pill.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            for li, line_seg in enumerate(label_lines):
                p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
                p.text = line_seg
                p.alignment = PP_ALIGN.CENTER
                p.font.name = "Arial"
                p.font.size = Pt(flow_font_pt)
                p.font.bold = True
                p.font.color.rgb = _hex_to_rgb(f.label_text_hex)
