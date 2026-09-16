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
from src.docx_engine.spec_compiler import (
    SpecCompiler,
    SpecMetadata,
    compile_markdown_to_docx,
    compile_spec_directory,
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
    "SpecCompiler",
    "SpecMetadata",
    "compile_markdown_to_docx",
    "compile_spec_directory",
]

