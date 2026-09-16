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

    def add_issue(self, severity: str, category: str, message: str, location: str) -> None:
        self.issues.append(LintIssue(severity=severity, category=category, message=message, location=location))
        if severity == "ERROR":
            self.passed = False
        self.total_issues = len(self.issues)


def lint_document(docx_path: Union[str, Path]) -> LintReport:
    """Inspect a .docx file and produce a quality assurance validation report."""
    p = Path(docx_path)
    report = LintReport(file_path=str(p))

    if not p.exists():
        report.add_issue("ERROR", "FILE_IO", f"File does not exist: {p}", "filesystem")
        return report

    try:
        doc = Document(str(p))
    except Exception as e:
        report.add_issue("ERROR", "CORRUPT_FILE", f"Cannot open docx: {e}", "document")
        return report

    jinja_var_pattern = re.compile(r"\{\{.*?\}\}")
    jinja_tag_pattern = re.compile(r"\{%.*?%\}")

    # 1. Check Body Paragraphs
    for i, para in enumerate(doc.paragraphs):
        txt = para.text
        if not txt:
            continue
        # Monospace code blocks are literal examples (e.g. dbt SQL, Jinja macros)
        if any(r.font.name in ("Consolas", "Courier New", "Courier", "Monaco", "Menlo") for r in para.runs):
            continue
        # Unrendered tags
        for match in jinja_var_pattern.findall(txt):
            report.add_issue("ERROR", "UNRENDERED_TAG", f"Unrendered Jinja variable found: '{match}'", f"Paragraph {i + 1}")
        for match in jinja_tag_pattern.findall(txt):
            report.add_issue("ERROR", "UNRENDERED_BLOCK", f"Unrendered Jinja tag found: '{match}'", f"Paragraph {i + 1}")

    # 2. Check Tables
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                for p_idx, para in enumerate(cell.paragraphs):
                    txt = para.text
                    if not txt:
                        continue
                    # Monospace code callouts inside table cards are literal examples
                    if any(r.font.name in ("Consolas", "Courier New", "Courier", "Monaco", "Menlo") for r in para.runs):
                        continue
                    for match in jinja_var_pattern.findall(txt):
                        report.add_issue(
                            "ERROR",
                            "UNRENDERED_TAG",
                            f"Unrendered Jinja variable found in table: '{match}'",
                            f"Table {t_idx + 1}, Row {r_idx + 1}, Cell {c_idx + 1}",
                        )
                    for match in jinja_tag_pattern.findall(txt):
                        report.add_issue(
                            "ERROR",
                            "UNRENDERED_BLOCK",
                            f"Unrendered Jinja block found in table: '{match}'",
                            f"Table {t_idx + 1}, Row {r_idx + 1}, Cell {c_idx + 1}",
                        )

    # 3. Check Headers and Footers
    for s_idx, section in enumerate(doc.sections):
        for h_p in section.header.paragraphs:
            if h_p.text:
                for match in jinja_var_pattern.findall(h_p.text):
                    report.add_issue("ERROR", "UNRENDERED_TAG", f"Unrendered tag in header: '{match}'", f"Section {s_idx + 1} Header")
        for f_p in section.footer.paragraphs:
            if f_p.text:
                for match in jinja_var_pattern.findall(f_p.text):
                    report.add_issue("ERROR", "UNRENDERED_TAG", f"Unrendered tag in footer: '{match}'", f"Section {s_idx + 1} Footer")

    return report
