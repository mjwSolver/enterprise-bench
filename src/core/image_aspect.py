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
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import lxml.etree as etree
from PIL import Image

EMU_PER_INCH = 914400

WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


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
        xml_parser = etree.XMLParser(resolve_entities=False, no_network=True)

        with zipfile.ZipFile(str(path), "r") as z:
            namelist = set(z.namelist())
            # 1. Parse word/_rels/document.xml.rels to resolve rId -> media path
            rel_map: Dict[str, str] = {}
            rels_part = "word/_rels/document.xml.rels"
            if rels_part in namelist:
                rels_root = etree.fromstring(z.read(rels_part), parser=xml_parser)
                for rel in rels_root:
                    r_id = rel.get("Id")
                    target = rel.get("Target")
                    if r_id and target and "media/" in target:
                        # Normalize path relative to word/
                        clean_target = target if target.startswith("media/") else f"media/{Path(target).name}"
                        rel_map[r_id] = f"word/{clean_target}"

            # 2. Inspect document.xml for drawing extents and blip associations
            doc_part = "word/document.xml"
            if doc_part not in namelist:
                return reports

            doc_root = etree.fromstring(z.read(doc_part), parser=xml_parser)
            drawings = doc_root.xpath(".//w:drawing", namespaces={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"})

            dim_cache: Dict[str, Optional[Tuple[int, int]]] = {}

            for draw in drawings:
                # Find blip
                blips = draw.xpath(".//a:blip", namespaces={"a": A_NS})
                if not blips:
                    continue
                r_id = blips[0].get(f"{{{R_NS}}}embed")
                if not r_id or r_id not in rel_map:
                    continue

                media_file = rel_map[r_id]
                if media_file not in namelist:
                    continue

                # Read actual image dimensions via PIL (cached per media_file)
                if media_file not in dim_cache:
                    img_data = z.read(media_file)
                    try:
                        with Image.open(io.BytesIO(img_data)) as im:
                            dim_cache[media_file] = im.size
                    except Exception:
                        dim_cache[media_file] = None

                dims = dim_cache[media_file]
                if not dims:
                    continue
                nat_w, nat_h = dims

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

                suggested_h_emu = int(round(cx * nat_h / nat_w))
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

        if not distorted_reports:
            if src_p != dst_p:
                dst_p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_p), str(dst_p))
            return 0, reports

        parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False, no_network=True)
        corrected_count = 0
        max_cx = int(max_width_in * EMU_PER_INCH)

        dst_p.parent.mkdir(parents=True, exist_ok=True)
        tmp_file: Optional[Path] = None

        try:
            with zipfile.ZipFile(str(src_p), "r") as zin:
                if "word/document.xml" not in zin.namelist():
                    if src_p != dst_p:
                        shutil.copy2(str(src_p), str(dst_p))
                    return 0, reports

                root = etree.fromstring(zin.read("word/document.xml"), parser=parser)
                seen_rel_ids: set[str] = set()

                for rep in distorted_reports:
                    if rep.rel_id in seen_rel_ids:
                        continue
                    seen_rel_ids.add(rep.rel_id)

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
                        wp_exts = draw.xpath(".//wp:extent", namespaces={"wp": WP_NS})
                        a_exts = draw.xpath(".//a:xfrm/a:ext", namespaces={"a": A_NS})
                        primary_ext = wp_exts[0] if wp_exts else (a_exts[0] if a_exts else None)
                        if primary_ext is None:
                            continue

                        cur_cx = int(primary_ext.get("cx", rep.container_width_emu))
                        if fit_width and cur_cx > max_cx:
                            cur_cx = max_cx
                        new_cy = int(round(cur_cx * rep.natural_height_px / rep.natural_width_px))

                        for ext in wp_exts:
                            ext.set("cx", str(cur_cx))
                            ext.set("cy", str(new_cy))

                        for ext in a_exts:
                            ext.set("cx", str(cur_cx))
                            ext.set("cy", str(new_cy))

                        corrected_count += 1

                modified_doc_xml = etree.tostring(root, encoding="utf-8", xml_declaration=True)

                with tempfile.NamedTemporaryFile(suffix=".docx", dir=str(dst_p.parent), delete=False) as f_out:
                    tmp_file = Path(f_out.name)
                    with zipfile.ZipFile(f_out, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                        for item in zin.infolist():
                            if item.filename == "word/document.xml":
                                zout.writestr(item, modified_doc_xml)
                            else:
                                zout.writestr(item, zin.read(item.filename))

            if tmp_file is not None:
                tmp_file.replace(dst_p)
        finally:
            if tmp_file is not None and tmp_file.exists():
                tmp_file.unlink()

        return corrected_count, self.audit_docx(dst_p)
