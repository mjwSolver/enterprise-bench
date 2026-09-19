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

    tmp_fd, tmp_path_str = tempfile.mkstemp(suffix=".docx")
    os.close(tmp_fd)
    tmp_path = Path(tmp_path_str)

    try:
        items_data = {}
        with zipfile.ZipFile(src_p, "r") as zin:
            for item in zin.infolist():
                items_data[item.filename] = zin.read(item.filename)

        for filename, data in list(items_data.items()):
            # 1. Clear comments XMLs while preserving root containers & namespaces
            if purge_comments and any(
                filename.endswith(cp)
                for cp in ["comments.xml", "commentsExtended.xml", "commentsExtensible.xml", "commentsIds.xml"]
            ):
                try:
                    root = etree.fromstring(data)
                    child_count = len(root)
                    report.comments_removed += child_count
                    for child in list(root):
                        root.remove(child)
                    items_data[filename] = etree.tostring(root, xml_declaration=True, encoding="utf-8", standalone=True)
                except Exception as err:
                    report.errors.append(f"Failed processing {filename}: {err}")

            # 2. Clear people.xml (reviewer and contributor identity list)
            elif purge_comments and filename == "word/people.xml":
                try:
                    root = etree.fromstring(data)
                    for child in list(root):
                        root.remove(child)
                    items_data[filename] = etree.tostring(root, xml_declaration=True, encoding="utf-8", standalone=True)
                except Exception as err:
                    report.errors.append(f"Failed processing {filename}: {err}")

            # 3. Settings.xml: remove trackRevisions flag
            elif accept_revisions and filename == "word/settings.xml":
                try:
                    root = etree.fromstring(data)
                    etree.strip_elements(root, f"{{{W_NS}}}trackRevisions", with_tail=False)
                    items_data[filename] = etree.tostring(root, xml_declaration=True, encoding="utf-8", standalone=True)
                except Exception as err:
                    report.errors.append(f"Failed processing {filename}: {err}")

            # 4. Document XMLs: headers, footers, and main body
            elif (
                filename.startswith("word/")
                and filename.endswith(".xml")
                and not filename.startswith("word/_rels/")
            ):
                try:
                    root = etree.fromstring(data)

                    # Revisions: remove deletions, format change markers, and unwrap insertions
                    if accept_revisions:
                        dels = root.findall(f".//{{{W_NS}}}del")
                        report.revisions_removed += len(dels)
                        etree.strip_elements(root, f"{{{W_NS}}}del", with_tail=False)

                        for chg in ["rPrChange", "pPrChange", "tblPrChange", "tcPrChange", "sectPrChange", "tblGridChange"]:
                            chgs = root.findall(f".//{{{W_NS}}}{chg}")
                            report.revisions_removed += len(chgs)
                            etree.strip_elements(root, f"{{{W_NS}}}{chg}", with_tail=False)

                        # Unwrap insertions (keeps clean inserted text)
                        etree.strip_tags(root, f"{{{W_NS}}}ins")

                    # Comments: remove inline anchors
                    if purge_comments:
                        etree.strip_elements(root, f"{{{W_NS}}}commentRangeStart", with_tail=False)
                        etree.strip_elements(root, f"{{{W_NS}}}commentRangeEnd", with_tail=False)
                        etree.strip_elements(root, f"{{{W_NS}}}commentReference", with_tail=False)

                    # Highlights: strip run-level highlight elements
                    if purge_highlights:
                        hls = root.findall(f".//{{{W_NS}}}highlight")
                        report.highlights_removed += len(hls)
                        etree.strip_elements(root, f"{{{W_NS}}}highlight", with_tail=False)

                    items_data[filename] = etree.tostring(root, xml_declaration=True, encoding="utf-8", standalone=True)
                except Exception as err:
                    report.errors.append(f"Failed processing {filename}: {err}")

        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for filename, data in items_data.items():
                zout.writestr(filename, data)

        dst_p.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_path), str(dst_p))

    except Exception as e:
        report.success = False
        report.error_message = str(e)
        if tmp_path.exists():
            tmp_path.unlink()
        return report

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
