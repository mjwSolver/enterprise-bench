"""
Deterministic Document Engine Package
"""
from src.docx_engine.template_stamper import (
    TemplateStamper,
    stamp_template,
)
from src.docx_engine.table_engine import (
    set_cell_background,
    set_cell_margins,
    make_row_header,
    prevent_row_split,
    style_table,
)
from src.docx_engine.document_linter import (
    LintIssue,
    LintReport,
    lint_document,
)

__all__ = [
    "TemplateStamper",
    "stamp_template",
    "set_cell_background",
    "set_cell_margins",
    "make_row_header",
    "prevent_row_split",
    "style_table",
    "LintIssue",
    "LintReport",
    "lint_document",
]
