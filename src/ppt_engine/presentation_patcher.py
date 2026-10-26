"""
PowerPoint Presentation Patcher (L2 Micro-Patch Engine)
======================================================
Enables targeted, in-situ text and image micro-patching of PowerPoint (.pptx)
presentations without requiring throwaway imperative scripts or re-compilation.
Supports finding and replacing text strings across shapes and tables, setting
specific shape copy by name/ID, and swapping images while preserving geometry.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches, Pt

logger = logging.getLogger(__name__)


@dataclass
class PatchReport:
    file_path: str
    output_path: str
    operations_count: int = 0
    impacted_slides: List[int] = field(default_factory=list)
    details: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.operations_count > 0


class PresentationPatcher:
    """Targeted DOM micro-patcher for PowerPoint presentations."""

    def __init__(self, pptx_path: Union[str, Path]) -> None:
        self.pptx_path = Path(pptx_path).resolve()
        if not self.pptx_path.exists():
            raise FileNotFoundError(f"PowerPoint file not found: {self.pptx_path}")
        self.prs = Presentation(str(self.pptx_path))
        self.operations: List[str] = []
        self.impacted_slides: set[int] = set()

    def replace_text(
        self,
        find_text: str,
        replace_text: str,
        slide_index: Optional[int] = None,
        shape_name: Optional[str] = None,
        shape_id: Optional[int] = None,
        exact_match: bool = False,
    ) -> int:
        """Find and replace text strings across shapes, tables, and groups."""
        if not find_text:
            raise ValueError("find_text cannot be empty")

        total_matches = 0
        target_slides = (
            [(slide_index, self.prs.slides[slide_index - 1])]
            if slide_index is not None
            else list(enumerate(self.prs.slides, start=1))
        )

        for s_idx, slide in target_slides:
            slide_matches = self._patch_shapes_in_container(
                shapes=slide.shapes,
                slide_index=s_idx,
                find_text=find_text,
                replace_text=replace_text,
                shape_name=shape_name,
                shape_id=shape_id,
                exact_match=exact_match,
            )
            if slide_matches > 0:
                total_matches += slide_matches
                self.impacted_slides.add(s_idx)

        desc = f"Replaced '{find_text}' -> '{replace_text}' ({total_matches} occurrence(s))"
        self.operations.append(desc)
        return total_matches

    def _patch_shapes_in_container(
        self,
        shapes: Any,
        slide_index: int,
        find_text: str,
        replace_text: str,
        shape_name: Optional[str],
        shape_id: Optional[int],
        exact_match: bool,
    ) -> int:
        matches = 0
        for shape in shapes:
            # Check filter
            if shape_id is not None and getattr(shape, "shape_id", None) != shape_id:
                continue
            if shape_name is not None:
                curr_name = getattr(shape, "name", "").strip().lower()
                if curr_name != shape_name.strip().lower():
                    continue

            # 1. Text Frame
            if hasattr(shape, "has_text_frame") and shape.has_text_frame:
                m = self._patch_text_frame(shape.text_frame, find_text, replace_text, exact_match)
                matches += m

            # 2. Table
            if hasattr(shape, "has_table") and shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        if hasattr(cell, "text_frame") and cell.text_frame:
                            m = self._patch_text_frame(cell.text_frame, find_text, replace_text, exact_match)
                            matches += m

            # 3. Group Shapes
            if hasattr(shape, "shapes"):
                m = self._patch_shapes_in_container(
                    shapes=shape.shapes,
                    slide_index=slide_index,
                    find_text=find_text,
                    replace_text=replace_text,
                    shape_name=shape_name,
                    shape_id=shape_id,
                    exact_match=exact_match,
                )
                matches += m

        return matches

    def _patch_text_frame(
        self,
        tf: Any,
        find_text: str,
        replace_text: str,
        exact_match: bool,
    ) -> int:
        count = 0
        for p in tf.paragraphs:
            # First, try run-level substitution to preserve exact run styling
            p_text = p.text
            if find_text not in p_text:
                continue

            # Check if any individual run contains the find_text
            run_matched = False
            for r in p.runs:
                if find_text in r.text:
                    if exact_match and r.text.strip() != find_text:
                        continue
                    r.text = r.text.replace(find_text, replace_text)
                    count += 1
                    run_matched = True

            # If find_text spans multiple runs in paragraph
            if not run_matched and find_text in p.text:
                if exact_match and p.text.strip() != find_text:
                    continue
                # Fallback: substitute across runs while preserving first run style
                first_run = p.runs[0] if p.runs else None
                font_name = first_run.font.name if first_run and first_run.font else None
                font_size = first_run.font.size if first_run and first_run.font else None
                font_bold = first_run.font.bold if first_run and first_run.font else None
                font_color = None
                if first_run and first_run.font and hasattr(first_run.font, "color"):
                    try:
                        font_color = first_run.font.color.rgb
                    except Exception:
                        font_color = None

                new_p_text = p.text.replace(find_text, replace_text)
                p.text = new_p_text
                count += 1

                # Reapply styling if first run exists
                if p.runs and (font_name or font_size or font_bold or font_color):
                    target_run = p.runs[0]
                    if font_name:
                        target_run.font.name = font_name
                    if font_size:
                        target_run.font.size = font_size
                    if font_bold is not None:
                        target_run.font.bold = font_bold
                    if font_color:
                        target_run.font.color.rgb = font_color

        return count

    def set_shape_text(
        self,
        target: Union[str, int],
        new_text: str,
        slide_index: Optional[int] = None,
    ) -> bool:
        """Set full text of a specific shape identified by name or shape ID."""
        target_str = str(target).strip()
        is_id = target_str.isdigit()

        target_slides = (
            [(slide_index, self.prs.slides[slide_index - 1])]
            if slide_index is not None
            else list(enumerate(self.prs.slides, start=1))
        )

        for s_idx, slide in target_slides:
            shape = self._find_shape(slide.shapes, target_str, is_id)
            if shape and hasattr(shape, "has_text_frame") and shape.has_text_frame:
                tf = shape.text_frame
                # Preserve styling attributes from first paragraph/run
                first_p = tf.paragraphs[0] if tf.paragraphs else None
                first_run = first_p.runs[0] if first_p and first_p.runs else None
                font_name = first_run.font.name if first_run and first_run.font else None
                font_size = first_run.font.size if first_run and first_run.font else None
                font_bold = first_run.font.bold if first_run and first_run.font else None
                font_color = None
                if first_run and first_run.font and hasattr(first_run.font, "color"):
                    try:
                        font_color = first_run.font.color.rgb
                    except Exception:
                        font_color = None

                tf.text = new_text

                if tf.paragraphs and tf.paragraphs[0].runs:
                    run = tf.paragraphs[0].runs[0]
                    if font_name:
                        run.font.name = font_name
                    if font_size:
                        run.font.size = font_size
                    if font_bold is not None:
                        run.font.bold = font_bold
                    if font_color:
                        run.font.color.rgb = font_color

                self.impacted_slides.add(s_idx)
                self.operations.append(f"Set shape '{target}' text on Slide {s_idx}")
                return True

        return False

    def replace_shape_image(
        self,
        target: Union[str, int],
        new_image_path: Union[str, Path],
        slide_index: Optional[int] = None,
    ) -> bool:
        """Replace the image blob of a specific picture shape."""
        new_img = Path(new_image_path).resolve()
        if not new_img.exists():
            raise FileNotFoundError(f"Replacement image not found: {new_img}")

        target_str = str(target).strip()
        is_id = target_str.isdigit()

        target_slides = (
            [(slide_index, self.prs.slides[slide_index - 1])]
            if slide_index is not None
            else list(enumerate(self.prs.slides, start=1))
        )

        with open(new_img, "rb") as f:
            new_blob = f.read()

        for s_idx, slide in target_slides:
            shape = self._find_shape(slide.shapes, target_str, is_id)
            if shape and hasattr(shape, "shape_type") and shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    # Update image part blob in-place
                    shape.image.part._blob = new_blob
                    self.impacted_slides.add(s_idx)
                    self.operations.append(f"Replaced image in shape '{target}' on Slide {s_idx}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed direct blob replacement: {e}. Falling back to shape replacement.")
                    left, top, width, height = shape.left, shape.top, shape.width, shape.height
                    sp_elem = shape._element
                    sp_elem.getparent().remove(sp_elem)
                    slide.shapes.add_picture(str(new_img), left, top, width, height)
                    self.impacted_slides.add(s_idx)
                    self.operations.append(f"Substituted picture shape '{target}' on Slide {s_idx}")
                    return True

        return False

    def _find_shape(self, shapes: Any, target_str: str, is_id: bool) -> Optional[Any]:
        for shape in shapes:
            if is_id and getattr(shape, "shape_id", None) == int(target_str):
                return shape
            curr_name = getattr(shape, "name", "").strip().lower()
            if curr_name == target_str.lower():
                return shape
            if hasattr(shape, "shapes"):
                found = self._find_shape(shape.shapes, target_str, is_id)
                if found:
                    return found
        return None

    def save(self, output_path: Optional[Union[str, Path]] = None, in_place: bool = False) -> PatchReport:
        """Save patched presentation atomically."""
        if in_place:
            dest = self.pptx_path
        elif output_path:
            dest = Path(output_path).resolve()
        else:
            dest = self.pptx_path.parent / f"{self.pptx_path.stem}_patched{self.pptx_path.suffix}"

        dest.parent.mkdir(parents=True, exist_ok=True)

        if in_place:
            # Write to temporary file first, then atomically replace
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pptx", dir=str(dest.parent))
            os.close(tmp_fd)
            try:
                self.prs.save(tmp_path)
                shutil.move(tmp_path, str(dest))
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
        else:
            self.prs.save(str(dest))

        return PatchReport(
            file_path=str(self.pptx_path),
            output_path=str(dest),
            operations_count=len(self.operations),
            impacted_slides=sorted(list(self.impacted_slides)),
            details=self.operations,
        )
