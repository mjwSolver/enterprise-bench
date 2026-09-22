"""
Document & Image Aspect Ratio Quality Assurance Subsystem
=========================================================
Scans, audits, and corrects geometric distortion and aspect ratio compression for
embedded images across OpenXML documents (.docx).

Prevents vertical or horizontal squishing when legacy or synthetic screenshots
are injected into pre-existing OpenXML container frames.
"""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import lxml.etree as etree
from PIL import Image

EMU_PER_INCH = 914400

WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


@dataclass
class ImageAspectReport:
    """Diagnostic report for an embedded image frame in a document."""
    rel_id: str
    target_part: str
    media_path: str
    container_width_emu: int
    container_height_emu: int
    container_width_in: float
    container_height_in: float
    container_aspect_ratio: float
    natural_width_px: int
    natural_height_px: int
    natural_aspect_ratio: float
    distortion_pct: float
    is_distorted: bool
    suggested_height_in: float
    suggested_height_emu: int


class ImageAspectEngine:
    """Audits and automatically corrects aspect ratio distortion in OpenXML DOCX packages."""

    def __init__(self, tolerance_pct: float = 3.0):
        self.tolerance_pct = tolerance_pct

    def audit_docx(self, docx_path: Union[str, Path]) -> List[ImageAspectReport]:
        """Audits all embedded drawings in a .docx file for aspect ratio squish or distortion."""
        path = Path(docx_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        reports: List[ImageAspectReport] = []

        with zipfile.ZipFile(str(path), "r") as z:
            # 1. Parse word/_rels/document.xml.rels to resolve rId -> media path
            rel_map: Dict[str, str] = {}
            rels_part = "word/_rels/document.xml.rels"
            if rels_part in z.namelist():
                rels_root = etree.fromstring(z.read(rels_part))
                for rel in rels_root:
                    r_id = rel.get("Id")
                    target = rel.get("Target")
                    if r_id and target and "media/" in target:
                        # Normalize path relative to word/
                        clean_target = target if target.startswith("media/") else f"media/{Path(target).name}"
                        rel_map[r_id] = f"word/{clean_target}"

            # 2. Inspect document.xml for drawing extents and blip associations
            doc_part = "word/document.xml"
            if doc_part not in z.namelist():
                return reports

            doc_root = etree.fromstring(z.read(doc_part))
            drawings = doc_root.xpath(".//w:drawing", namespaces={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"})

            for draw in drawings:
                # Find blip
                blips = draw.xpath(".//a:blip", namespaces={"a": A_NS})
                if not blips:
                    continue
                r_id = blips[0].get(f"{{{R_NS}}}embed")
                if not r_id or r_id not in rel_map:
                    continue

                media_file = rel_map[r_id]
                if media_file not in z.namelist():
                    continue

                # Read actual image dimensions via PIL
                img_data = z.read(media_file)
                try:
                    with Image.open(io.BytesIO(img_data)) as im:
                        nat_w, nat_h = im.size
                except Exception:
                    continue

                if nat_w <= 0 or nat_h <= 0:
                    continue

                natural_ratio = nat_w / nat_h

                # Find container extent (wp:extent or a:ext)
                extents = draw.xpath(".//wp:extent", namespaces={"wp": WP_NS})
                if not extents:
                    extents = draw.xpath(".//a:xfrm/a:ext", namespaces={"a": A_NS})
                if not extents:
                    continue

                ext = extents[0]
                cx_str = ext.get("cx")
                cy_str = ext.get("cy")
                if not cx_str or not cy_str:
                    continue

                cx = int(cx_str)
                cy = int(cy_str)
                if cx <= 0 or cy <= 0:
                    continue

                cont_w_in = cx / EMU_PER_INCH
                cont_h_in = cy / EMU_PER_INCH
                cont_ratio = cont_w_in / cont_h_in

                # Distortion percentage
                distortion = abs(cont_ratio - natural_ratio) / natural_ratio * 100.0
                is_distorted = distortion > self.tolerance_pct

                suggested_h_emu = int(cx / natural_ratio)
                suggested_h_in = suggested_h_emu / EMU_PER_INCH

                reports.append(
                    ImageAspectReport(
                        rel_id=r_id,
                        target_part=doc_part,
                        media_path=media_file,
                        container_width_emu=cx,
                        container_height_emu=cy,
                        container_width_in=cont_w_in,
                        container_height_in=cont_h_in,
                        container_aspect_ratio=round(cont_ratio, 3),
                        natural_width_px=nat_w,
                        natural_height_px=nat_h,
                        natural_aspect_ratio=round(natural_ratio, 3),
                        distortion_pct=round(distortion, 1),
                        is_distorted=is_distorted,
                        suggested_height_in=round(suggested_h_in, 3),
                        suggested_height_emu=suggested_h_emu,
                    )
                )

        return reports

    def fix_docx(
        self,
        docx_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        fit_width: bool = True,
        max_width_in: float = 6.5,
    ) -> Tuple[int, List[ImageAspectReport]]:
        """
        Corrects distorted image extents in word/document.xml to match the natural
        aspect ratio of underlying image media parts.
        """
        src_p = Path(docx_path)
        dst_p = Path(output_path) if output_path else src_p

        reports = self.audit_docx(src_p)
        distorted_reports = [r for r in reports if r.is_distorted]

        if not distorted_reports and src_p == dst_p:
            return 0, reports

        # Create temporary working directory for in-place surgery
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            with zipfile.ZipFile(str(src_p), "r") as zin:
                zin.extractall(tmp_path)

            doc_xml_path = tmp_path / "word" / "document.xml"
            if not doc_xml_path.exists():
                return 0, reports

            parser = etree.XMLParser(remove_blank_text=False)
            tree = etree.parse(str(doc_xml_path), parser)
            root = tree.getroot()

            corrected_count = 0

            for rep in distorted_reports:
                # Find all drawings referencing this rId
                drawings = root.xpath(
                    f".//w:drawing[.//a:blip[@r:embed='{rep.rel_id}']]",
                    namespaces={
                        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
                        "a": A_NS,
                        "r": R_NS,
                    },
                )

                for draw in drawings:
                    # Update wp:extent
                    for ext in draw.xpath(".//wp:extent", namespaces={"wp": WP_NS}):
                        cur_cx = int(ext.get("cx", rep.container_width_emu))
                        # Enforce max width if requested
                        if fit_width and cur_cx > int(max_width_in * EMU_PER_INCH):
                            cur_cx = int(max_width_in * EMU_PER_INCH)
                            ext.set("cx", str(cur_cx))
                        new_cy = int(cur_cx / rep.natural_aspect_ratio)
                        ext.set("cy", str(new_cy))

                    # Update a:xfrm/a:ext
                    for ext in draw.xpath(".//a:xfrm/a:ext", namespaces={"a": A_NS}):
                        cur_cx = int(ext.get("cx", rep.container_width_emu))
                        if fit_width and cur_cx > int(max_width_in * EMU_PER_INCH):
                            cur_cx = int(max_width_in * EMU_PER_INCH)
                            ext.set("cx", str(cur_cx))
                        new_cy = int(cur_cx / rep.natural_aspect_ratio)
                        ext.set("cy", str(new_cy))

                    corrected_count += 1

            # Save modified document.xml
            tree.write(str(doc_xml_path), encoding="utf-8", xml_declaration=True)

            # Re-pack zip cleanly
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            temp_out = tmp_path / "output.docx"
            with zipfile.ZipFile(str(temp_out), "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for file_path in tmp_path.rglob("*"):
                    if file_path.is_file() and file_path != temp_out:
                        arcname = file_path.relative_to(tmp_path)
                        zout.write(str(file_path), str(arcname))

            shutil.copy2(str(temp_out), str(dst_p))

        return corrected_count, self.audit_docx(dst_p)
