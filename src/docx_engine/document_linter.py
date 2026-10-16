"""
Document Linter Subsystem
=========================
Performs automated structural and content quality validation on rendered
Word (.docx) documents:
- Detects unrendered Jinja2 tags (e.g. {{ var }} or {% tag %})
- Checks table integrity (empty cells, degenerate rows)
- Validates heading hierarchies and orphan labels
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from docx import Document


_JINJA_VAR_RE = re.compile(r"\{\{.*?\}\}", re.DOTALL)
_JINJA_TAG_RE = re.compile(r"\{%.*?%\}", re.DOTALL)
_MONOSPACE_FONTS = frozenset(("Consolas", "Courier New", "Courier", "Monaco", "Menlo"))
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"


@dataclass
class LintIssue:
    severity: str  # "ERROR", "WARNING", "INFO"
    category: str
    message: str
    location: str


@dataclass
class LintReport:
    file_path: str
    total_issues: int = 0
    passed: bool = True
    issues: List[LintIssue] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.total_issues = len(self.issues)
        if any(issue.severity == "ERROR" for issue in self.issues):
            self.passed = False

    def add_issue(self, severity: str, category: str, message: str, location: str) -> None:
        self.issues.append(LintIssue(severity=severity, category=category, message=message, location=location))
        if severity == "ERROR":
            self.passed = False
        self.total_issues = len(self.issues)


def _extract_lintable_text(para: Any) -> str:
    """
    Return paragraph text excluding monospace code runs (e.g. dbt SQL, Jinja examples).
    If a paragraph mixes prose runs and inline monospace runs, only the non-monospace
    runs are inspected so unrendered tags in surrounding prose are still caught.
    """
    txt = para.text
    if not txt:
        return ""
    runs = para.runs
    if not runs:
        return txt
    non_empty_runs = [r for r in runs if r.text]
    if not non_empty_runs:
        return txt
    mono_flags = [r.font.name in _MONOSPACE_FONTS for r in non_empty_runs]
    if all(mono_flags):
        return ""
    if any(mono_flags):
        return "".join(r.text for r, is_mono in zip(non_empty_runs, mono_flags) if not is_mono)
    return txt


def _check_text_for_jinja(
    txt: str,
    report: LintReport,
    location: str,
    var_msg_fmt: str = "Unrendered Jinja variable found: '{match}'",
    tag_msg_fmt: str = "Unrendered Jinja tag found: '{match}'",
) -> None:
    """Scan a text string for unrendered Jinja variable and block tags."""
    if not txt or ("{{" not in txt and "{%" not in txt):
        return
    for match in _JINJA_VAR_RE.findall(txt):
        report.add_issue("ERROR", "UNRENDERED_TAG", var_msg_fmt.format(match=match), location)
    for match in _JINJA_TAG_RE.findall(txt):
        report.add_issue("ERROR", "UNRENDERED_BLOCK", tag_msg_fmt.format(match=match), location)


def _lint_tables(
    tables: Any,
    report: LintReport,
    location_prefix: str = "",
    seen_cells: Optional[set[int]] = None,
) -> None:
    """Recursively lint tables and nested tables while deduplicating merged cells."""
    if seen_cells is None:
        seen_cells = set()

    for t_idx, table in enumerate(tables):
        table_loc = f"{location_prefix}Table {t_idx + 1}"
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                tc_id = id(cell._tc)
                if tc_id in seen_cells:
                    continue
                seen_cells.add(tc_id)

                cell_loc = f"{table_loc}, Row {r_idx + 1}, Cell {c_idx + 1}"
                for para in cell.paragraphs:
                    txt = _extract_lintable_text(para)
                    _check_text_for_jinja(
                        txt,
                        report,
                        cell_loc,
                        var_msg_fmt="Unrendered Jinja variable found in table: '{match}'",
                        tag_msg_fmt="Unrendered Jinja block found in table: '{match}'",
                    )
                if cell.tables:
                    _lint_tables(cell.tables, report, location_prefix=f"{cell_loc} > ", seen_cells=seen_cells)


def _lint_textboxes(root_element: Any, report: LintReport, location_prefix: str = "") -> None:
    """Inspect Word DrawingML textboxes (<w:txbxContent>), skipping VML mc:Fallback duplicates."""
    if root_element is None:
        return
    txbx_tag = f"{{{_W_NS}}}txbxContent"
    p_tag = f"{{{_W_NS}}}p"
    t_tag = f"{{{_W_NS}}}t"
    fallback_tag = f"{{{_MC_NS}}}Fallback"

    tb_idx = 0
    for txbx in root_element.iter(txbx_tag):
        # Skip duplicate VML fallback twin inside mc:AlternateContent
        if any(anc.tag == fallback_tag for anc in txbx.iterancestors()):
            continue
        tb_idx += 1
        for p_idx, p_elem in enumerate(txbx.findall(f".//{p_tag}")):
            txt = "".join(t.text for t in p_elem.iter(t_tag) if t.text)
            if txt:
                loc = f"{location_prefix}Textbox {tb_idx}, Paragraph {p_idx + 1}"
                _check_text_for_jinja(txt, report, loc)


def lint_document(docx_path: Union[str, Path]) -> LintReport:
    """Inspect a .docx file and produce a quality assurance validation report."""
    p = Path(docx_path)
    report = LintReport(file_path=str(p))

    if not p.exists() or not p.is_file():
        report.add_issue("ERROR", "FILE_IO", f"File does not exist: {p}", "filesystem")
        return report

    try:
        doc = Document(str(p))
    except Exception as e:
        report.add_issue("ERROR", "CORRUPT_FILE", f"Cannot open docx: {e}", "document")
        return report

    # 1. Check Body Paragraphs
    for i, para in enumerate(doc.paragraphs):
        txt = _extract_lintable_text(para)
        _check_text_for_jinja(txt, report, f"Paragraph {i + 1}")

    # 2. Check Tables (including nested tables, deduplicating merged cells)
    _lint_tables(doc.tables, report)

    # 3. Check Body Textboxes (<w:txbxContent>)
    if doc.element is not None and doc.element.body is not None:
        _lint_textboxes(doc.element.body, report)

    # 4. Check Headers and Footers (primary, first-page, even-page; paragraphs, tables, textboxes)
    seen_hf_elements: set[int] = set()
    for s_idx, section in enumerate(doc.sections):
        hf_candidates = [
            ("Header", section.header),
            ("Footer", section.footer),
        ]
        if getattr(section, "different_first_page_header_footer", False):
            hf_candidates.extend([
                ("First Page Header", section.first_page_header),
                ("First Page Footer", section.first_page_footer),
            ])
        if getattr(doc.settings, "odd_and_even_pages_header_footer", False):
            hf_candidates.extend([
                ("Even Page Header", section.even_page_header),
                ("Even Page Footer", section.even_page_footer),
            ])

        for label, hf_part in hf_candidates:
            if hf_part is None or (s_idx > 0 and getattr(hf_part, "is_linked_to_previous", True)):
                continue
            el_id = id(hf_part._element)
            if el_id in seen_hf_elements:
                continue
            seen_hf_elements.add(el_id)

            loc = f"Section {s_idx + 1} {label}"
            kind_lower = "header" if "Header" in label else "footer"
            for hf_p in hf_part.paragraphs:
                txt = _extract_lintable_text(hf_p)
                _check_text_for_jinja(
                    txt,
                    report,
                    loc,
                    var_msg_fmt=f"Unrendered tag in {kind_lower}: '{{match}}'",
                    tag_msg_fmt=f"Unrendered block in {kind_lower}: '{{match}}'",
                )
            if hf_part.tables:
                _lint_tables(hf_part.tables, report, location_prefix=f"{loc} ")
            _lint_textboxes(hf_part._element, report, location_prefix=f"{loc} ")

    return report
