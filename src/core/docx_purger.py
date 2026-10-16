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


@dataclass
class PurgeReport:
    """Metrics from document element purging."""
    file_path: str
    comments_removed: int = 0
    highlights_removed: int = 0
    revisions_removed: int = 0
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
) -> PurgeReport:
    """
    Safely purges review comments, text highlights, and tracked changes from a .docx file.
    Leaves package relationships, [Content_Types].xml, and namespace declarations 100% untouched.
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

    try:
        with (
            zipfile.ZipFile(src_p, "r") as zin,
            zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout,
        ):
            for item in zin.infolist():
                filename = item.filename
                data = zin.read(filename)

                # 1. Clear comments XMLs while preserving root containers & namespaces
                if purge_comments and filename.endswith(_COMMENT_XML_SUFFIXES):
                    try:
                        root = etree.fromstring(data)
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
                        root = etree.fromstring(data)
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
                        root = etree.fromstring(data)
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
                        root = etree.fromstring(data)
                        xml_modified = False

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
) -> List[PurgeReport]:
    """Recursively purge comments, highlights, and revisions from all .docx files in a directory."""
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
        )
        reports.append(rep)

    return reports
