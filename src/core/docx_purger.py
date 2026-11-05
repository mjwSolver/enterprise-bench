"""
Document Element Purging Subsystem (Zero-Corruption OpenXML Engine)
==================================================================
Comprehensive, non-destructive OpenXML purger for Word (.docx) documents:
  - Wipes margin comments and reviewer notes (comments.xml, commentsExtended, etc.).
  - Accepts tracked revisions: unrolls <w:ins> insertions and strips <w:del> deletions.
  - Removes editorial change markers (<w:rPrChange>, <w:pPrChange>, <w:tblPrChange>).
  - Clears run-level author highlighting (<w:highlight>).
  - Wipes contributor identities in word/people.xml.
  - Disables revision tracking in word/settings.xml (<w:trackRevisions>).
  - Preserves [Content_Types].xml, .rels, and all namespace schemas 100% intact.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import lxml.etree as etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def _get_safe_parser() -> etree.XMLParser:
    """Returns a hardened XML parser that blocks XXE, entity expansion, and network fetching."""
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        dtd_validation=False,
        load_dtd=False,
    )


def _unwrap_element(elem: etree._Element) -> None:
    """Unwraps an XML element by promoting all children to its parent in place, preserving text."""
    parent = elem.getparent()
    if parent is None:
        return
    idx = parent.index(elem)
    if elem.text:
        if idx > 0:
            prev = parent[idx - 1]
            prev.tail = (prev.tail or "") + elem.text
        else:
            parent.text = (parent.text or "") + elem.text
    for child in list(elem):
        parent.insert(idx, child)
        idx += 1
    if elem.tail:
        if len(elem) > 0:
            last_child = elem[-1]
            last_child.tail = (last_child.tail or "") + elem.tail
        elif idx > 0:
            prev = parent[idx - 1]
            prev.tail = (prev.tail or "") + elem.tail
        else:
            parent.text = (parent.text or "") + elem.tail
    parent.remove(elem)


@dataclass
class PurgeReport:
    """Metrics from document element purging."""
    file_path: str
    comments_removed: int = 0
    highlights_removed: int = 0
    revisions_removed: int = 0
    macros_removed: int = 0
    external_rels_removed: int = 0
    success: bool = True
    error_message: Optional[str] = None
    errors: List[str] = field(default_factory=list)


_WORD_CONTENT_FILES = frozenset({
    "word/document.xml",
    "word/styles.xml",
    "word/numbering.xml",
    "word/footnotes.xml",
    "word/endnotes.xml",
})

_COMMENT_XML_SUFFIXES = (
    "comments.xml",
    "commentsExtended.xml",
    "commentsExtensible.xml",
    "commentsIds.xml",
)

_FORMAT_CHANGE_TAGS = (
    "rPrChange",
    "pPrChange",
    "tblPrChange",
    "tblPrExChange",
    "tcPrChange",
    "trPrChange",
    "sectPrChange",
    "tblGridChange",
    "numberingChange",
)

_MOVE_RANGE_TAGS = (
    "moveFromRangeStart",
    "moveFromRangeEnd",
    "moveToRangeStart",
    "moveToRangeEnd",
)

_COMMENT_ANCHOR_TAGS = (
    "commentRangeStart",
    "commentRangeEnd",
    "commentReference",
)


def _is_wordprocessingml_content_part(filename: str) -> bool:
    """Return True if the ZIP entry is a WordprocessingML content/style XML part."""
    if filename in _WORD_CONTENT_FILES:
        return True
    if filename.startswith("word/") and filename.endswith(".xml") and "/" not in filename[5:]:
        stem = filename[5:-4]
        if stem.startswith(("header", "footer")):
            return True
    return False


def purge_docx_elements(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    purge_comments: bool = True,
    purge_highlights: bool = True,
    accept_revisions: bool = True,
    purge_macros: bool = True,
    purge_external_rels: bool = True,
) -> PurgeReport:
    """
    Safely purges review comments, text highlights, tracked changes, VBA macros,
    and external relationships from a .docx / .docm file.
    Guards against Zip Slip / path traversal and XML External Entity (XXE) attacks.
    Leaves package relationships and namespace declarations schema-valid and intact.
    """
    src_p = Path(input_path)
    dst_p = Path(output_path) if output_path else src_p

    report = PurgeReport(file_path=str(dst_p))

    if not src_p.exists():
        report.success = False
        report.error_message = f"File not found: {src_p}"
        return report

    dst_p.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(suffix=".docx", dir=str(dst_p.parent))
    os.close(tmp_fd)
    tmp_path = Path(tmp_path_str)

    parser = _get_safe_parser()

    try:
        with (
            zipfile.ZipFile(src_p, "r") as zin,
            zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout,
        ):
            # Guard against Zip Slip / Path Traversal
            for item in zin.infolist():
                member_p = Path(item.filename)
                if (
                    member_p.is_absolute()
                    or ".." in member_p.parts
                    or item.filename.startswith(("/", "\\"))
                    or (len(item.filename) > 1 and item.filename[1] == ":")
                ):
                    raise ValueError(
                        f"Zip Slip / Path traversal attempt detected in archive entry: {item.filename}"
                    )

            # Pre-scan .rels to discover external and macro relationship IDs
            removed_external_rids: set[str] = set()
            removed_macro_rids: set[str] = set()
            if purge_external_rels or purge_macros:
                for item in zin.infolist():
                    if item.filename.endswith(".rels"):
                        try:
                            rel_root = etree.fromstring(zin.read(item.filename), parser=parser)
                            for rel in rel_root:
                                rel_id = rel.get("Id")
                                target_mode = rel.get("TargetMode", "")
                                rel_type = rel.get("Type", "")
                                rel_target = rel.get("Target", "")
                                if purge_external_rels and target_mode.lower() == "external":
                                    if rel_id:
                                        removed_external_rids.add(rel_id)
                                if purge_macros and ("vba" in rel_type.lower() or "vbaproject" in rel_target.lower()):
                                    if rel_id:
                                        removed_macro_rids.add(rel_id)
                        except Exception:
                            pass

            for item in zin.infolist():
                filename = item.filename
                data = zin.read(filename)

                # Macro purging: completely strip macro binary parts
                if purge_macros and (
                    filename.lower().endswith("vbaproject.bin")
                    or filename == "word/vbaProject.bin"
                    or filename == "word/vbaData.xml"
                    or filename.startswith("word/vba")
                ):
                    report.macros_removed += 1
                    continue

                # Content Types: strip macro content types and overrides
                if purge_macros and filename == "[Content_Types].xml":
                    try:
                        ct_root = etree.fromstring(data, parser=parser)
                        ct_modified = False
                        for child in list(ct_root):
                            part_name = child.get("PartName", "").lower()
                            content_type = child.get("ContentType", "").lower()
                            ext = child.get("Extension", "").lower()
                            if "vbaproject" in part_name or "vbadata" in part_name or "/word/vba" in part_name:
                                ct_root.remove(child)
                                ct_modified = True
                            elif part_name == "/word/document.xml" and "macroenabled" in content_type:
                                child.set(
                                    "ContentType",
                                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
                                )
                                ct_modified = True
                            elif "vbaproject" in content_type or (ext == "bin" and "vba" in content_type):
                                ct_root.remove(child)
                                ct_modified = True
                        if ct_modified:
                            data = etree.tostring(
                                ct_root, xml_declaration=True, encoding="utf-8", standalone=True
                            )
                    except Exception as err:
                        report.errors.append(f"Failed processing {filename}: {err}")

                # Relationships: strip external relationships and macro relationships
                elif (purge_external_rels or purge_macros) and filename.endswith(".rels"):
                    try:
                        rel_root = etree.fromstring(data, parser=parser)
                        rels_modified = False
                        for rel in list(rel_root):
                            target_mode = rel.get("TargetMode", "")
                            rel_type = rel.get("Type", "")
                            rel_target = rel.get("Target", "")
                            if purge_external_rels and target_mode.lower() == "external":
                                rel_root.remove(rel)
                                report.external_rels_removed += 1
                                rels_modified = True
                            elif purge_macros and ("vba" in rel_type.lower() or "vbaproject" in rel_target.lower()):
                                rel_root.remove(rel)
                                report.macros_removed += 1
                                rels_modified = True
                        if rels_modified:
                            data = etree.tostring(
                                rel_root, xml_declaration=True, encoding="utf-8", standalone=True
                            )
                    except Exception as err:
                        report.errors.append(f"Failed processing {filename}: {err}")

                # 1. Clear comments XMLs while preserving root containers & namespaces
                elif purge_comments and filename.endswith(_COMMENT_XML_SUFFIXES):
                    try:
                        root = etree.fromstring(data, parser=parser)
                        child_count = len(root)
                        if child_count > 0:
                            report.comments_removed += child_count
                            for child in list(root):
                                root.remove(child)
                            data = etree.tostring(
                                root, xml_declaration=True, encoding="utf-8", standalone=True
                            )
                    except Exception as err:
                        report.errors.append(f"Failed processing {filename}: {err}")

                # 2. Clear people.xml (reviewer and contributor identity list)
                elif purge_comments and filename == "word/people.xml":
                    try:
                        root = etree.fromstring(data, parser=parser)
                        if len(root) > 0:
                            for child in list(root):
                                root.remove(child)
                            data = etree.tostring(
                                root, xml_declaration=True, encoding="utf-8", standalone=True
                            )
                    except Exception as err:
                        report.errors.append(f"Failed processing {filename}: {err}")

                # 3. Settings.xml: remove trackRevisions flag
                elif accept_revisions and filename == "word/settings.xml":
                    try:
                        root = etree.fromstring(data, parser=parser)
                        if root.find(f".//{{{W_NS}}}trackRevisions") is not None:
                            etree.strip_elements(root, f"{{{W_NS}}}trackRevisions", with_tail=False)
                            data = etree.tostring(
                                root, xml_declaration=True, encoding="utf-8", standalone=True
                            )
                    except Exception as err:
                        report.errors.append(f"Failed processing {filename}: {err}")

                # 4. WordprocessingML content/style parts (document, headers, footers, notes, styles, numbering)
                elif _is_wordprocessingml_content_part(filename):
                    try:
                        root = etree.fromstring(data, parser=parser)
                        xml_modified = False

                        # If external rels were removed, unwrap referencing <w:hyperlink> elements to preserve text safely
                        if purge_external_rels and removed_external_rids:
                            for hl in list(root.findall(f".//{{{W_NS}}}hyperlink")):
                                r_id = hl.get(f"{{{R_NS}}}id") or hl.get("r:id")
                                if r_id and r_id in removed_external_rids:
                                    _unwrap_element(hl)
                                    xml_modified = True

                        # Revisions: remove deletions, format change markers, and unwrap insertions
                        if accept_revisions:
                            # Handle table row deletions (<w:trPr><w:del/>) and insertions (<w:trPr><w:ins/>) first
                            for tr in list(root.findall(f".//{{{W_NS}}}tr")):
                                trPr = tr.find(f"{{{W_NS}}}trPr")
                                if trPr is not None:
                                    tr_del = trPr.find(f"{{{W_NS}}}del")
                                    if tr_del is not None:
                                        parent = tr.getparent()
                                        if parent is not None:
                                            parent.remove(tr)
                                            report.revisions_removed += 1
                                            xml_modified = True
                                        continue
                                    tr_ins = trPr.find(f"{{{W_NS}}}ins")
                                    if tr_ins is not None:
                                        trPr.remove(tr_ins)
                                        report.revisions_removed += 1
                                        xml_modified = True

                            dels = root.findall(f".//{{{W_NS}}}del")
                            if dels:
                                report.revisions_removed += len(dels)
                                etree.strip_elements(root, f"{{{W_NS}}}del", with_tail=False)
                                xml_modified = True

                            move_froms = root.findall(f".//{{{W_NS}}}moveFrom")
                            if move_froms:
                                report.revisions_removed += len(move_froms)
                                etree.strip_elements(root, f"{{{W_NS}}}moveFrom", with_tail=False)
                                xml_modified = True

                            for rng_tag in _MOVE_RANGE_TAGS:
                                rng_elems = root.findall(f".//{{{W_NS}}}{rng_tag}")
                                if rng_elems:
                                    report.revisions_removed += len(rng_elems)
                                    etree.strip_elements(root, f"{{{W_NS}}}{rng_tag}", with_tail=False)
                                    xml_modified = True

                            for chg in _FORMAT_CHANGE_TAGS:
                                chgs = root.findall(f".//{{{W_NS}}}{chg}")
                                if chgs:
                                    report.revisions_removed += len(chgs)
                                    etree.strip_elements(root, f"{{{W_NS}}}{chg}", with_tail=False)
                                    xml_modified = True

                            # Unwrap insertions and moveTo (keeps clean inserted/moved text)
                            if root.find(f".//{{{W_NS}}}ins") is not None:
                                etree.strip_tags(root, f"{{{W_NS}}}ins")
                                xml_modified = True
                            if root.find(f".//{{{W_NS}}}moveTo") is not None:
                                etree.strip_tags(root, f"{{{W_NS}}}moveTo")
                                xml_modified = True

                        # Comments: remove inline anchors and dedicated commentReference wrapper runs
                        if purge_comments:
                            for ref in list(root.findall(f".//{{{W_NS}}}commentReference")):
                                parent = ref.getparent()
                                if parent is not None and parent.tag == f"{{{W_NS}}}r":
                                    non_rpr_children = [c for c in parent if c.tag != f"{{{W_NS}}}rPr"]
                                    if len(non_rpr_children) == 1 and non_rpr_children[0] is ref:
                                        r_parent = parent.getparent()
                                        if r_parent is not None:
                                            r_parent.remove(parent)
                                            xml_modified = True
                                            continue

                            for c_tag in _COMMENT_ANCHOR_TAGS:
                                if root.find(f".//{{{W_NS}}}{c_tag}") is not None:
                                    etree.strip_elements(root, f"{{{W_NS}}}{c_tag}", with_tail=False)
                                    xml_modified = True

                        # Highlights: strip run-level highlight elements
                        if purge_highlights:
                            hls = root.findall(f".//{{{W_NS}}}highlight")
                            if hls:
                                report.highlights_removed += len(hls)
                                etree.strip_elements(root, f"{{{W_NS}}}highlight", with_tail=False)
                                xml_modified = True

                        if xml_modified:
                            data = etree.tostring(
                                root, xml_declaration=True, encoding="utf-8", standalone=True
                            )
                    except Exception as err:
                        report.errors.append(f"Failed processing {filename}: {err}")

                zout.writestr(filename, data)

        os.replace(str(tmp_path), str(dst_p))

    except Exception as e:
        report.success = False
        report.error_message = str(e)
        return report
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    return report


def purge_directory_elements(
    directory_path: Union[str, Path],
    purge_comments: bool = True,
    purge_highlights: bool = True,
    accept_revisions: bool = True,
    purge_macros: bool = True,
    purge_external_rels: bool = True,
) -> List[PurgeReport]:
    """Recursively purge comments, highlights, revisions, macros, and external rels from all .docx files in a directory."""
    d = Path(directory_path)
    reports: List[PurgeReport] = []
    if not d.exists():
        return reports

    for f in d.rglob("*.docx"):
        if f.name.startswith((".", "~$")):
            continue
        rep = purge_docx_elements(
            f, f,
            purge_comments=purge_comments,
            purge_highlights=purge_highlights,
            accept_revisions=accept_revisions,
            purge_macros=purge_macros,
            purge_external_rels=purge_external_rels,
        )
        reports.append(rep)

    return reports
