"""
PowerPoint Presentation Inspector (L1 Inspection Engine)
========================================================
Inspects PowerPoint (.pptx) files headlessly and extracts structured metadata,
shape hierarchies, geometries, text contents, table structures, and token estimates.
Provides formatted output in Markdown, Rich tables, or raw JSON.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches, Pt


@dataclass
class ShapeInfo:
    shape_id: int
    name: str
    shape_type: str
    left: float
    top: float
    width: float
    height: float
    text: str = ""
    word_count: int = 0
    paragraph_count: int = 0
    paragraphs: List[str] = field(default_factory=list)
    table_data: Optional[List[List[str]]] = None
    image_info: Optional[Dict[str, Any]] = None
    children: List[ShapeInfo] = field(default_factory=list)

    @property
    def bounds_str(self) -> str:
        return f"[{self.left:.2f}\", {self.top:.2f}\", {self.width:.2f}\" x {self.height:.2f}\"]"


@dataclass
class SlideInfo:
    slide_index: int
    slide_id: int
    title: str
    shapes: List[ShapeInfo] = field(default_factory=list)
    total_words: int = 0
    total_shapes: int = 0

    def compute_totals(self) -> None:
        count = 0
        words = 0
        for s in self.shapes:
            count += 1 + len(s.children)
            words += s.word_count
            for c in s.children:
                words += c.word_count
        self.total_shapes = count
        self.total_words = words


@dataclass
class PresentationInfo:
    file_path: str
    slide_width: float
    slide_height: float
    slides: List[SlideInfo] = field(default_factory=list)
    total_slides: int = 0
    total_shapes: int = 0
    total_words: int = 0
    estimated_tokens: int = 0

    def compute_totals(self) -> None:
        self.total_slides = len(self.slides)
        self.total_shapes = sum(s.total_shapes for s in self.slides)
        self.total_words = sum(s.total_words for s in self.slides)
        # Token heuristic: 1 word ~ 1.33 tokens in standard English technical prose
        self.estimated_tokens = int(math.ceil(self.total_words * 1.33))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self, full: bool = False, slide_index: Optional[int] = None) -> str:
        lines: List[str] = []
        filename = Path(self.file_path).name
        lines.append(f"# Presentation Inspection: `{filename}`")
        lines.append("")
        lines.append(f"- **Canvas Size**: {self.slide_width:.2f}\" x {self.slide_height:.2f}\"")
        lines.append(f"- **Total Slides**: {self.total_slides}")
        lines.append(f"- **Total Shapes**: {self.total_shapes}")
        lines.append(f"- **Total Words**: {self.total_words:,} (~{self.estimated_tokens:,} tokens)")
        lines.append("")

        target_slides = self.slides
        if slide_index is not None:
            target_slides = [s for s in self.slides if s.slide_index == slide_index]

        for s in target_slides:
            lines.append(f"## Slide {s.slide_index}: {s.title or '(Untitled Slide)'}")
            lines.append(f"*Shapes: {s.total_shapes} | Words: {s.total_words}*")
            lines.append("")

            if not s.shapes:
                lines.append("*(No shapes found on slide)*\n")
                continue

            lines.append("| ID | Shape Name | Type | Bounds [x, y, w, h] | Content Preview |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")

            for sh in s.shapes:
                self._format_shape_md_row(sh, lines, full=full, depth=0)
            lines.append("")

        return "\n".join(lines)

    def _format_shape_md_row(self, sh: ShapeInfo, lines: List[str], full: bool, depth: int) -> None:
        indent = "&nbsp;&nbsp;" * depth
        name_str = f"{indent}`{sh.name}`" if not depth else f"{indent}↳ `{sh.name}`"

        if sh.table_data:
            content = f"Table ({len(sh.table_data)} rows x {len(sh.table_data[0]) if sh.table_data else 0} cols)"
            if full and sh.table_data:
                sample_rows = [", ".join(r[:3]) for r in sh.table_data[:2]]
                content += " [" + "; ".join(sample_rows) + "]"
        elif sh.image_info:
            content = f"Image ({sh.image_info.get('content_type', 'unknown')})"
        elif sh.text:
            cleaned = sh.text.replace("\n", " ").strip()
            if not full and len(cleaned) > 45:
                content = cleaned[:42] + "..."
            else:
                content = cleaned
            content = content.replace("|", "\\|")
        elif sh.children:
            content = f"Group ({len(sh.children)} child shapes)"
        else:
            content = "*(empty)*"

        lines.append(f"| {sh.shape_id} | {name_str} | `{sh.shape_type}` | `{sh.bounds_str}` | {content} |")

        for child in sh.children:
            self._format_shape_md_row(child, lines, full=full, depth=depth + 1)


class PresentationInspector:
    """Headless inspector for extracting structure and copy from PowerPoint files."""

    def __init__(self, pptx_path: Union[str, Path]) -> None:
        self.pptx_path = Path(pptx_path).resolve()
        if not self.pptx_path.exists():
            raise FileNotFoundError(f"PowerPoint file not found: {self.pptx_path}")
        self.prs = Presentation(str(self.pptx_path))

    def inspect(self) -> PresentationInfo:
        """Inspects all slides and shapes in the presentation."""
        w_in = self.prs.slide_width.inches
        h_in = self.prs.slide_height.inches

        slides_info: List[SlideInfo] = []

        for idx, slide in enumerate(self.prs.slides, start=1):
            slide_id = slide.slide_id
            slide_title = ""
            if slide.shapes.title and slide.shapes.title.has_text_frame:
                slide_title = slide.shapes.title.text_frame.text.strip().replace("\n", " ")

            shapes_info: List[ShapeInfo] = []
            for shape in slide.shapes:
                sh_info = self._inspect_shape(shape)
                if sh_info:
                    shapes_info.append(sh_info)
                    if not slide_title and sh_info.text and sh_info.top < 1.5:
                        # Fallback candidate header
                        slide_title = sh_info.text.split("\n")[0].strip()

            s_info = SlideInfo(
                slide_index=idx,
                slide_id=slide_id,
                title=slide_title,
                shapes=shapes_info,
            )
            s_info.compute_totals()
            slides_info.append(s_info)

        p_info = PresentationInfo(
            file_path=str(self.pptx_path),
            slide_width=w_in,
            slide_height=h_in,
            slides=slides_info,
        )
        p_info.compute_totals()
        return p_info

    def _inspect_shape(self, shape: Any) -> Optional[ShapeInfo]:
        try:
            sh_id = shape.shape_id
            name = shape.name
            sh_type = shape.shape_type.name if hasattr(shape.shape_type, "name") else str(shape.shape_type)
            left = shape.left.inches if hasattr(shape, "left") else 0.0
            top = shape.top.inches if hasattr(shape, "top") else 0.0
            width = shape.width.inches if hasattr(shape, "width") else 0.0
            height = shape.height.inches if hasattr(shape, "height") else 0.0
        except Exception:
            return None

        text = ""
        paragraphs: List[str] = []
        table_data: Optional[List[List[str]]] = None
        image_info: Optional[Dict[str, Any]] = None
        children: List[ShapeInfo] = []

        # 1. Text Frame
        if hasattr(shape, "has_text_frame") and shape.has_text_frame:
            tf = shape.text_frame
            text = tf.text.strip()
            paragraphs = [p.text.strip() for p in tf.paragraphs if p.text.strip()]

        # 2. Table
        if hasattr(shape, "has_table") and shape.has_table:
            sh_type = "TABLE"
            tbl = shape.table
            table_data = []
            for row in tbl.rows:
                row_cells = []
                for cell in row.cells:
                    row_cells.append(cell.text.strip())
                table_data.append(row_cells)
            # Combine table text for word count
            text = " ".join(" ".join(r) for r in table_data)

        # 3. Picture
        if hasattr(shape, "shape_type") and shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            try:
                img = shape.image
                image_info = {
                    "content_type": img.content_type,
                    "filename": getattr(img, "filename", "unknown"),
                    "byte_size": len(img.blob),
                }
            except Exception:
                image_info = {"content_type": "unknown", "filename": "unknown", "byte_size": 0}

        # 4. Group Shape
        if hasattr(shape, "shapes"):
            sh_type = "GROUP"
            for child in shape.shapes:
                c_info = self._inspect_shape(child)
                if c_info:
                    children.append(c_info)

        words = len(text.split()) if text else 0

        return ShapeInfo(
            shape_id=sh_id,
            name=name,
            shape_type=sh_type,
            left=left,
            top=top,
            width=width,
            height=height,
            text=text,
            word_count=words,
            paragraph_count=len(paragraphs),
            paragraphs=paragraphs,
            table_data=table_data,
            image_info=image_info,
            children=children,
        )
