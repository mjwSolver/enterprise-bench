"""
Universal Multi-Backend Slide Preview Exporter
==============================================
Headless slide preview generator with multi-tier backend orchestration:
  1. macOS Native: AppleScript (`osascript`) via Keynote (`com.apple.iWork.Keynote`) or MS PowerPoint.
  2. CLI: LibreOffice / soffice headless converter if available.
  3. Pure-Python Fallback Renderer: Headless Pillow + python-pptx parser rendering crisp
     slide previews on any platform without requiring external binaries or GUI access.
"""

from __future__ import annotations

import io
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ImageColor, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN


# ============================================================================
# Helper Utilities
# ============================================================================

def _hex_or_rgb_to_tuple(color: Any, default: Tuple[int, int, int] = (255, 255, 255)) -> Tuple[int, int, int]:
    """Convert RGBColor, hex string, or tuple to (R, G, B) integer tuple."""
    if isinstance(color, RGBColor):
        return (color[0], color[1], color[2])
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return (int(color[0]), int(color[1]), int(color[2]))
    if isinstance(color, str):
        c = color.strip()
        if c.startswith("#"):
            c = c[1:]
        if len(c) == 6:
            try:
                return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
            except Exception:
                return default
    return default


def _get_system_font(font_name: Optional[str] = None, size_px: int = 16, bold: bool = False) -> ImageFont.ImageFont:
    """Locate crisp system font on macOS/Linux/Windows with sensible fallbacks."""
    system = platform.system()
    candidates: List[str] = []

    if system == "Darwin":
        if bold:
            candidates.extend([
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/SFCompact.ttf",
                "/System/Library/Fonts/SFNS.ttf",
            ])
        else:
            candidates.extend([
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/SFCompact.ttf",
                "/System/Library/Fonts/SFNS.ttf",
            ])
    elif system == "Linux":
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ])

    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                # Handle font collection indices (.ttc)
                if font_path.endswith(".ttc"):
                    return ImageFont.truetype(font_path, size_px, index=1 if bold else 0)
                return ImageFont.truetype(font_path, size_px)
            except Exception:
                continue

    try:
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


# ============================================================================
# Pure-Python Fallback Slide Renderer
# ============================================================================

class PurePythonSlideRenderer:
    """
    Renders PowerPoint slides headlessly into high-resolution PNG previews
    using python-pptx and Pillow.
    Parses rectangles, rounded cards, background layers, text frames, and embedded images.
    """

    def __init__(self, dpi: int = 150) -> None:
        self.dpi = dpi

    def render_presentation(self, pptx_path: Path, output_dir: Path) -> List[Path]:
        prs = Presentation(str(pptx_path))
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered_images: List[Path] = []

        slide_w_in = prs.slide_width.inches
        slide_h_in = prs.slide_height.inches
        width_px = int(slide_w_in * self.dpi)
        height_px = int(slide_h_in * self.dpi)

        scale_x = width_px / prs.slide_width.pt
        scale_y = height_px / prs.slide_height.pt

        for idx, slide in enumerate(prs.slides, start=1):
            out_file = output_dir / f"slide_{idx:02d}.png"
            img = self.render_slide(slide, width_px, height_px, scale_x, scale_y)
            img.save(str(out_file), "PNG", dpi=(self.dpi, self.dpi))
            rendered_images.append(out_file)

        return rendered_images

    def render_slide(
        self,
        slide: Any,
        width_px: int,
        height_px: int,
        scale_x: float,
        scale_y: float,
    ) -> Image.Image:
        # Base canvas
        canvas = Image.new("RGBA", (width_px, height_px), (248, 250, 252, 255))
        draw = ImageDraw.Draw(canvas)

        # Single-pass painter's algorithm respecting natural shape z-order
        for shape in slide.shapes:
            self._render_shape_background(canvas, draw, shape, scale_x, scale_y)
            self._render_shape_picture(canvas, draw, shape, scale_x, scale_y)
            self._render_shape_table(canvas, draw, shape, scale_x, scale_y)
            self._render_shape_text(canvas, draw, shape, scale_x, scale_y)

        return canvas.convert("RGB")

    def _render_shape_background(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        shape: Any,
        scale_x: float,
        scale_y: float,
    ) -> None:
        # Recursively render group shapes
        if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                self._render_shape_background(canvas, draw, child, scale_x, scale_y)
            return

        try:
            x = shape.left.pt * scale_x
            y = shape.top.pt * scale_y
            w = shape.width.pt * scale_x
            h = shape.height.pt * scale_y
        except Exception:
            return

        # Check if shape is an AutoShape
        auto_type = None
        try:
            if hasattr(shape, "shape_type") and shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                auto_type = shape.auto_shape_type
        except Exception:
            auto_type = None

        if auto_type is None:
            return

        fill_color = None
        alpha_val = 255
        border_color = None
        border_width = 0

        # Fill extraction
        if hasattr(shape, "fill") and shape.fill.type is not None:
            try:
                if hasattr(shape.fill, "fore_color") and shape.fill.fore_color:
                    fill_color = _hex_or_rgb_to_tuple(shape.fill.fore_color.rgb)
                # Check for OpenXML DrawingML alpha
                spPr = getattr(shape._element, "spPr", None)
                if spPr is not None:
                    solid_fill = spPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
                    if solid_fill is not None:
                        srgb_clr = solid_fill.find("{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
                        if srgb_clr is not None:
                            alpha_elem = srgb_clr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}alpha")
                            if alpha_elem is not None and "val" in alpha_elem.attrib:
                                alpha_val = int(round(int(alpha_elem.attrib["val"]) / 100000.0 * 255))
            except Exception:
                fill_color = None

        # Line extraction
        if hasattr(shape, "line") and shape.line.fill.type is not None:
            try:
                if hasattr(shape.line.fill, "fore_color") and shape.line.fill.fore_color:
                    border_color = _hex_or_rgb_to_tuple(shape.line.fill.fore_color.rgb)
                if hasattr(shape.line, "width") and shape.line.width:
                    border_width = max(1, int(shape.line.width.pt * scale_x))
            except Exception:
                border_color = None

        fill_rgba = (*fill_color, alpha_val) if fill_color else None
        border_rgba = (*border_color, 255) if border_color else None

        if not fill_rgba and not border_rgba:
            return

        # If transparent alpha is present, composite via a separate layer
        if fill_rgba and fill_rgba[3] < 255:
            overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            if auto_type == MSO_SHAPE.ROUNDED_RECTANGLE:
                radius = int(min(w, h) * 0.12) if min(w, h) > 0 else 8
                radius = max(4, min(radius, 24))
                overlay_draw.rounded_rectangle(
                    [x, y, x + w, y + h],
                    radius=radius,
                    fill=fill_rgba,
                    outline=border_rgba,
                    width=border_width if border_rgba else 0,
                )
            elif auto_type == MSO_SHAPE.CHEVRON:
                notch = min(w * 0.18, h * 0.5) if (w > 0 and h > 0) else 10
                pts = [
                    (x, y),
                    (x + w - notch, y),
                    (x + w, y + h / 2),
                    (x + w - notch, y + h),
                    (x, y + h),
                    (x + notch, y + h / 2),
                ]
                overlay_draw.polygon(pts, fill=fill_rgba, outline=border_rgba)
            else:
                overlay_draw.rectangle(
                    [x, y, x + w, y + h],
                    fill=fill_rgba,
                    outline=border_rgba,
                    width=border_width if border_rgba else 0,
                )
            canvas.alpha_composite(overlay)
            return

        if auto_type == MSO_SHAPE.ROUNDED_RECTANGLE:
            radius = int(min(w, h) * 0.12) if min(w, h) > 0 else 8
            radius = max(4, min(radius, 24))

            draw.rounded_rectangle(
                [x, y, x + w, y + h],
                radius=radius,
                fill=fill_rgba,
                outline=border_rgba,
                width=border_width if border_rgba else 0,
            )

        elif auto_type == MSO_SHAPE.CHEVRON:
            notch = min(w * 0.18, h * 0.5) if (w > 0 and h > 0) else 10
            pts = [
                (x, y),
                (x + w - notch, y),
                (x + w, y + h / 2),
                (x + w - notch, y + h),
                (x, y + h),
                (x + notch, y + h / 2),
            ]
            draw.polygon(
                pts,
                fill=fill_rgba,
                outline=border_rgba,
            )

        elif auto_type == MSO_SHAPE.RECTANGLE:
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=fill_rgba,
                outline=border_rgba,
                width=border_width if border_rgba else 0,
            )
        else:
            # Fallback for other geometric shapes: render bounding rectangle so shape is never invisible
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=fill_rgba,
                outline=border_rgba,
                width=border_width if border_rgba else 0,
            )

    def _render_shape_picture(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        shape: Any,
        scale_x: float,
        scale_y: float,
    ) -> None:
        if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                self._render_shape_picture(canvas, draw, child, scale_x, scale_y)
            return

        try:
            x = shape.left.pt * scale_x
            y = shape.top.pt * scale_y
            w = shape.width.pt * scale_x
            h = shape.height.pt * scale_y
        except Exception:
            return

        is_picture = False
        try:
            if hasattr(shape, "shape_type") and shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                is_picture = True
            elif hasattr(shape, "image"):
                is_picture = True
        except Exception:
            is_picture = False

        if is_picture:
            try:
                img_bytes = shape.image.blob
                pic = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                pic_resized = pic.resize((max(1, int(w)), max(1, int(h))), Image.Resampling.LANCZOS)
                canvas.alpha_composite(pic_resized, (int(x), int(y)))
            except Exception:
                pass

    def _render_shape_table(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        shape: Any,
        scale_x: float,
        scale_y: float,
    ) -> None:
        if not getattr(shape, "has_table", False):
            return
        table = shape.table
        try:
            tbl_x = shape.left.pt * scale_x
            tbl_y = shape.top.pt * scale_y
        except Exception:
            return

        cur_y = tbl_y
        for r_idx, row in enumerate(table.rows):
            cur_x = tbl_x
            row_h = row.height.pt * scale_y if hasattr(row, "height") and row.height else 24 * scale_y
            for c_idx, cell in enumerate(row.cells):
                col_w = table.columns[c_idx].width.pt * scale_x
                cell_fill = (255, 255, 255)
                if hasattr(cell, "fill") and cell.fill.type is not None:
                    try:
                        if cell.fill.fore_color and cell.fill.fore_color.rgb:
                            cell_fill = _hex_or_rgb_to_tuple(cell.fill.fore_color.rgb)
                    except Exception:
                        pass
                draw.rectangle([cur_x, cur_y, cur_x + col_w, cur_y + row_h], fill=cell_fill, outline=(226, 232, 240), width=1)

                text = cell.text.strip()
                if text:
                    font = _get_system_font(size_px=max(8, int(10 * scale_y)), bold=(r_idx == 0))
                    text_color = (255, 255, 255) if (cell_fill[0] < 80 and cell_fill[1] < 80 and cell_fill[2] < 80) else (15, 23, 42)
                    draw.text((cur_x + 8 * scale_x, cur_y + 4 * scale_y), text, fill=text_color, font=font)
                cur_x += col_w
            cur_y += row_h

    def _render_shape_text(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        shape: Any,
        scale_x: float,
        scale_y: float,
    ) -> None:
        if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                self._render_shape_text(canvas, draw, child, scale_x, scale_y)
            return

        if not hasattr(shape, "has_text_frame") or not shape.has_text_frame:
            return

        try:
            x = shape.left.pt * scale_x
            y = shape.top.pt * scale_y
            w = shape.width.pt * scale_x
            h = shape.height.pt * scale_y
        except Exception:
            return

        tf = shape.text_frame
        is_middle = getattr(tf, "vertical_anchor", None) == MSO_ANCHOR.MIDDLE
        if is_middle and len(tf.paragraphs) == 1:
            p_first = tf.paragraphs[0]
            f_pt = p_first.font.size.pt if p_first.font.size else (p_first.runs[0].font.size.pt if p_first.runs and p_first.runs[0].font.size else 10.0)
            font_px = max(8, int(f_pt * scale_y))
            line_height = int(font_px * 1.25)
            cur_y = y + max(0, (h - line_height) / 2)
        else:
            cur_y = y + (tf.margin_top.pt * scale_y if tf.margin_top else 2)
        left_margin = (tf.margin_left.pt * scale_x if tf.margin_left else 2)
        usable_w = max(10, w - left_margin - (tf.margin_right.pt * scale_x if tf.margin_right else 2))

        for p in tf.paragraphs:
            p_text = p.text
            if not p_text.strip():
                cur_y += 8 * scale_y
                continue

            if hasattr(p, "space_before") and p.space_before:
                cur_y += p.space_before.pt * scale_y

            # Determine paragraph font properties
            font_pt = 10.0
            bold = False
            color_rgb = (15, 23, 42)

            if p.font.size:
                font_pt = p.font.size.pt
            elif p.runs and p.runs[0].font.size:
                font_pt = p.runs[0].font.size.pt

            if p.font.bold is not None:
                bold = p.font.bold
            elif p.runs and p.runs[0].font.bold is not None:
                bold = p.runs[0].font.bold

            if p.font.color and hasattr(p.font.color, "rgb") and p.font.color.rgb:
                color_rgb = _hex_or_rgb_to_tuple(p.font.color.rgb, color_rgb)
            elif p.runs and p.runs[0].font.color and hasattr(p.runs[0].font.color, "rgb") and p.runs[0].font.color.rgb:
                color_rgb = _hex_or_rgb_to_tuple(p.runs[0].font.color.rgb, color_rgb)

            font_px = max(8, int(font_pt * scale_y))
            pil_font = _get_system_font(size_px=font_px, bold=bold)

            # Check if paragraph has bullet formatting (DrawingML buChar or leading bullet glyph)
            bu_elem = p._p.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}buChar")
            has_bullet = bu_elem is not None
            bullet_char = bu_elem.get("char") if has_bullet else None

            if not has_bullet and p_text.lstrip().startswith("•"):
                has_bullet = True
                bullet_char = "•"
                p_text = p_text.lstrip("•\t ").strip()
            elif has_bullet:
                p_text = p_text.lstrip("•\t ").strip()

            bullet_indent = 0.0
            if has_bullet:
                bullet_char = bullet_char or "•"
                try:
                    b_bbox = pil_font.getbbox(f"{bullet_char} ")
                    bullet_indent = (b_bbox[2] - b_bbox[0]) * 1.5
                except Exception:
                    bullet_indent = font_px * 1.4

            # Check if paragraph has multi-run formatting (e.g. bold header + normal body)
            if len(p.runs) > 1:
                # If bulleted, draw bullet glyph at left margin
                if has_bullet:
                    draw.text((x + left_margin, cur_y), bullet_char, fill=(*color_rgb, 255), font=pil_font)
                cur_y = self._render_multi_run_paragraph(
                    draw=draw,
                    runs=p.runs,
                    x=x + left_margin + bullet_indent,
                    y=cur_y,
                    usable_w=usable_w - bullet_indent,
                    default_font_pt=font_pt,
                    scale_y=scale_y,
                    alignment=p.alignment,
                    box_w=w,
                    box_x=x,
                )
            else:
                # Single run / simple paragraph with universal hanging indent
                line_height = int(font_px * 1.25)
                if has_bullet:
                    wrapped_lines = self._wrap_text(p_text, pil_font, max(10, usable_w - bullet_indent))
                    draw.text((x + left_margin, cur_y), bullet_char, fill=(*color_rgb, 255), font=pil_font)
                    for line in wrapped_lines:
                        draw.text(
                            (x + left_margin + bullet_indent, cur_y),
                            line,
                            fill=(*color_rgb, 255),
                            font=pil_font,
                        )
                        cur_y += line_height
                else:
                    wrapped_lines = self._wrap_text(p_text, pil_font, usable_w)
                    for line in wrapped_lines:
                        text_x = x + left_margin
                        if p.alignment == PP_ALIGN.CENTER:
                            try:
                                bbox = pil_font.getbbox(line)
                                tw = bbox[2] - bbox[0]
                                text_x = x + (w - tw) / 2
                            except Exception:
                                pass
                        elif p.alignment == PP_ALIGN.RIGHT:
                            try:
                                bbox = pil_font.getbbox(line)
                                tw = bbox[2] - bbox[0]
                                text_x = x + w - left_margin - tw
                            except Exception:
                                pass

                        draw.text(
                            (text_x, cur_y),
                            line,
                            fill=(*color_rgb, 255),
                            font=pil_font,
                        )
                        cur_y += line_height

            space_after = p.space_after.pt * scale_y if p.space_after else 3 * scale_y
            cur_y += space_after

    def _render_multi_run_paragraph(
        self,
        draw: ImageDraw.ImageDraw,
        runs: List[Any],
        x: float,
        y: float,
        usable_w: float,
        default_font_pt: float,
        scale_y: float,
        alignment: Any,
        box_w: float,
        box_x: float,
    ) -> float:
        """Render a paragraph composed of multiple runs with distinct colors/weights."""
        # Deconstruct into tokens of (word, font, color)
        tokens: List[Tuple[str, ImageFont.ImageFont, Tuple[int, int, int]]] = []
        for run in runs:
            r_text = run.text
            if not r_text:
                continue
            r_pt = run.font.size.pt if run.font.size else default_font_pt
            r_bold = run.font.bold if run.font.bold is not None else False
            r_rgb = (15, 23, 42)
            if run.font.color and hasattr(run.font.color, "rgb") and run.font.color.rgb:
                r_rgb = _hex_or_rgb_to_tuple(run.font.color.rgb, r_rgb)

            r_font_px = max(8, int(r_pt * scale_y))
            r_font = _get_system_font(size_px=r_font_px, bold=r_bold)

            words = r_text.split(" ")
            for i, w in enumerate(words):
                suffix = " " if i < len(words) - 1 else ""
                tokens.append((w + suffix, r_font, r_rgb))

        cur_x = x
        cur_y = y
        line_tokens: List[Tuple[str, ImageFont.ImageFont, Tuple[int, int, int]]] = []
        line_w = 0.0
        max_h = 14.0

        for text_token, font, color in tokens:
            try:
                bbox = font.getbbox(text_token)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            except Exception:
                tw = len(text_token) * 8
                th = 14

            if line_w + tw <= usable_w or not line_tokens:
                line_tokens.append((text_token, font, color))
                line_w += tw
                max_h = max(max_h, th * 1.25)
            else:
                # Render current line
                self._draw_line_tokens(draw, line_tokens, x, cur_y)
                cur_y += max_h
                line_tokens = [(text_token, font, color)]
                line_w = tw
                max_h = th * 1.25

        if line_tokens:
            self._draw_line_tokens(draw, line_tokens, x, cur_y)
            cur_y += max_h

        return cur_y

    def _draw_line_tokens(
        self,
        draw: ImageDraw.ImageDraw,
        line_tokens: List[Tuple[str, ImageFont.ImageFont, Tuple[int, int, int]]],
        start_x: float,
        y: float,
    ) -> None:
        lx = start_x
        for text_token, font, color in line_tokens:
            draw.text((lx, y), text_token, fill=(*color, 255), font=font)
            try:
                bbox = font.getbbox(text_token)
                tw = bbox[2] - bbox[0]
            except Exception:
                tw = len(text_token) * 8
            lx += tw

    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width_px: float) -> List[str]:
        """Wrap text according to pixel width constraints with hanging indent for bullets."""
        lines: List[str] = []
        raw_lines = text.split("\n")

        for rline in raw_lines:
            is_bullet = False
            bullet_prefix = ""
            if rline.startswith("•\t") or rline.startswith("•  ") or rline.startswith("• "):
                is_bullet = True
                content_text = rline.lstrip("•\t ").strip()
                bullet_prefix = "•  "
                words = content_text.split(" ")
            else:
                words = rline.split(" ")

            if not words or (is_bullet and not words[0]):
                if is_bullet:
                    lines.append(bullet_prefix.strip())
                continue

            indent_prefix = "    " if is_bullet else ""
            cur_line = bullet_prefix if is_bullet else ""

            for word in words:
                if is_bullet and cur_line == bullet_prefix:
                    test_line = f"{cur_line}{word}"
                else:
                    test_line = f"{cur_line} {word}".strip() if cur_line else word

                try:
                    bbox = font.getbbox(test_line)
                    text_w = bbox[2] - bbox[0]
                except Exception:
                    text_w = len(test_line) * 8

                if text_w <= max_width_px or (cur_line in ("", bullet_prefix)):
                    cur_line = test_line
                else:
                    lines.append(cur_line)
                    cur_line = f"{indent_prefix}{word}" if is_bullet else word
            if cur_line:
                lines.append(cur_line)

        return lines if lines else [text]


# ============================================================================
# Universal Slide Exporter
# ============================================================================

class SlideExporter:
    """
    Orchestrates presentation slide export with multi-backend fallback.
    Supported backends:
      - 'auto': Attempts Keynote -> PowerPoint -> soffice -> Pure Python
      - 'keynote': macOS Keynote AppleScript
      - 'powerpoint': macOS PowerPoint AppleScript
      - 'soffice': LibreOffice / soffice CLI
      - 'python' / 'pillow': Pure Python headless fallback
    """

    def __init__(self, backend: str = "auto", dpi: int = 150) -> None:
        self.backend = backend.lower()
        self.dpi = dpi
        self.python_renderer = PurePythonSlideRenderer(dpi=dpi)

    def export(self, pptx_path: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> List[Path]:
        """Export all slides from presentation to PNG images."""
        p_path = Path(pptx_path).resolve()
        if not p_path.exists():
            raise FileNotFoundError(f"Presentation file does not exist: {p_path}")

        if output_dir is None:
            out_dir = p_path.parent / "previews"
        else:
            out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # Handle specific backend choices
        if self.backend in ("python", "pillow", "pure_python"):
            return self._export_pure_python(p_path, out_dir)

        if self.backend == "keynote":
            res = self._export_keynote(p_path, out_dir)
            if res:
                return res
            print("  [SlideExporter] Keynote backend failed, falling back to pure Python...")
            return self._export_pure_python(p_path, out_dir)

        if self.backend == "powerpoint":
            res = self._export_powerpoint(p_path, out_dir)
            if res:
                return res
            print("  [SlideExporter] PowerPoint backend failed, falling back to pure Python...")
            return self._export_pure_python(p_path, out_dir)

        if self.backend == "soffice":
            res = self._export_soffice(p_path, out_dir)
            if res:
                return res
            print("  [SlideExporter] soffice backend failed, falling back to pure Python...")
            return self._export_pure_python(p_path, out_dir)

        # Auto Backend Selection: headless pure Python renderer
        # Note: We intentionally avoid auto-launching GUI desktop applications (Keynote, PowerPoint)
        # via AppleScript on macOS because doing so steals GUI window focus, triggers permission/conversion
        # dialogs, and leaves the application permanently running in the background.
        return self._export_pure_python(p_path, out_dir)

    def _export_pure_python(self, pptx_path: Path, output_dir: Path) -> List[Path]:
        return self.python_renderer.render_presentation(pptx_path, output_dir)

    def _export_keynote(self, pptx_path: Path, output_dir: Path) -> Optional[List[Path]]:
        """Exports slide images via macOS Keynote AppleScript."""
        if platform.system() != "Darwin":
            return None

        check_app = subprocess.run(
            ["osascript", "-e", 'id of app "Keynote"'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if check_app.returncode != 0:
            return None

        temp_export_dir = Path(tempfile.mkdtemp(prefix="keynote_export_"))
        script = f'''
        tell application "Keynote"
            set theDoc to open POSIX file "{pptx_path}"
            export theDoc to POSIX file "{temp_export_dir}" as slide images with properties {{image format:PNG}}
            close theDoc saving no
        end tell
        '''
        try:
            res = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=25,
            )
            if res.returncode == 0:
                raw_pngs = sorted(temp_export_dir.glob("*.png"))
                if raw_pngs:
                    final_pngs: List[Path] = []
                    for idx, raw_png in enumerate(raw_pngs, start=1):
                        dest_png = output_dir / f"slide_{idx:02d}.png"
                        shutil.copy(raw_png, dest_png)
                        final_pngs.append(dest_png)
                    shutil.rmtree(temp_export_dir, ignore_errors=True)
                    return final_pngs
        except Exception:
            pass
        finally:
            shutil.rmtree(temp_export_dir, ignore_errors=True)

        return None

    def _export_powerpoint(self, pptx_path: Path, output_dir: Path) -> Optional[List[Path]]:
        """Exports slide images via macOS PowerPoint AppleScript."""
        if platform.system() != "Darwin":
            return None

        check_app = subprocess.run(
            ["osascript", "-e", 'id of app "Microsoft PowerPoint"'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if check_app.returncode != 0:
            return None

        temp_export_dir = Path(tempfile.mkdtemp(prefix="ppt_export_"))
        script = f'''
        tell application "Microsoft PowerPoint"
            open POSIX file "{pptx_path}"
            save active presentation in POSIX file "{temp_export_dir}" as save as PNG
            close active presentation saving no
        end tell
        '''
        try:
            res = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=25,
            )
            if res.returncode == 0:
                raw_pngs = sorted(temp_export_dir.glob("**/*.png"))
                if raw_pngs:
                    final_pngs: List[Path] = []
                    for idx, raw_png in enumerate(raw_pngs, start=1):
                        dest_png = output_dir / f"slide_{idx:02d}.png"
                        shutil.copy(raw_png, dest_png)
                        final_pngs.append(dest_png)
                    shutil.rmtree(temp_export_dir, ignore_errors=True)
                    return final_pngs
        except Exception:
            pass
        finally:
            shutil.rmtree(temp_export_dir, ignore_errors=True)

        return None

    def _export_soffice(self, pptx_path: Path, output_dir: Path) -> Optional[List[Path]]:
        """Exports slide images via headless LibreOffice."""
        soffice_bin = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice_bin:
            return None

        temp_dir = Path(tempfile.mkdtemp(prefix="soffice_export_"))
        try:
            res = subprocess.run(
                [soffice_bin, "--headless", "--convert-to", "pdf", "--outdir", str(temp_dir), str(pptx_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            pdf_files = list(temp_dir.glob("*.pdf"))
            if pdf_files and shutil.which("pdftoppm"):
                pdf_file = pdf_files[0]
                prefix = temp_dir / "page"
                subprocess.run(
                    ["pdftoppm", "-png", "-r", str(self.dpi), str(pdf_file), str(prefix)],
                    check=True,
                    timeout=30,
                )
                raw_pngs = sorted(temp_dir.glob("page-*.png"))
                if raw_pngs:
                    final_pngs = []
                    for idx, p in enumerate(raw_pngs, start=1):
                        dest_png = output_dir / f"slide_{idx:02d}.png"
                        shutil.copy(p, dest_png)
                        final_pngs.append(dest_png)
                    return final_pngs
        except Exception:
            pass
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return None


def export_deck_to_images(
    pptx_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    backend: str = "auto",
    dpi: int = 150,
) -> List[Path]:
    """
    Universal presentation slide exporter.
    Renders all slides in pptx_path as crisp PNGs into output_dir.
    """
    exporter = SlideExporter(backend=backend, dpi=dpi)
    return exporter.export(pptx_path, output_dir=output_dir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pptx_input = sys.argv[1]
        out_target = sys.argv[2] if len(sys.argv) > 2 else None
        backend_choice = sys.argv[3] if len(sys.argv) > 3 else "auto"
        exported = export_deck_to_images(pptx_input, output_dir=out_target, backend=backend_choice)
        print(f"Exported {len(exported)} slide images:")
        for p in exported:
            print(f"  • {p}")
    else:
        print("Usage: python src/slide_exporter.py <presentation.pptx> [output_dir] [backend]")
