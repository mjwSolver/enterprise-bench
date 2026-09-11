"""
Deterministic Template Stamper Subsystem
========================================
Executes Jinja2 / docxtpl variable stamping and OpenXML document generation
for corporate deliverables (BAST, PKS, FSD, TSD, MoM):
- Loads .docx master templates from templates/
- Renders variables from Pydantic models or JSON/YAML payloads
- Supports embedding dynamic diagrams rendered via src.ppt_engine.diagram_engine
- Validates rendered outputs via document linter
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches, Mm
from pydantic import BaseModel

from src.core.config import TEMPLATES_DIR, OUTPUT_DIR, get_template_path
from src.docx_engine.document_linter import lint_document, LintReport


class TemplateStamper:
    """Orchestrates deterministic template stamping for enterprise Word documents."""

    def __init__(self, template_path: Union[str, Path]) -> None:
        p = Path(template_path)
        if not p.exists():
            resolved = get_template_path(str(template_path))
            if resolved and resolved.exists():
                p = resolved
            else:
                raise FileNotFoundError(f"Template not found: {template_path}")
        self.template_path = p
        self.doc = DocxTemplate(str(p))

    def render(
        self,
        context: Union[Dict[str, Any], BaseModel],
        output_path: Union[str, Path],
        auto_lint: bool = True,
    ) -> Tuple[Path, Optional[LintReport]]:
        """
        Renders the template with the provided context dictionary or Pydantic model.
        Saves output to output_path and runs verification lint.
        """
        if isinstance(context, BaseModel):
            ctx = context.model_dump()
        else:
            ctx = dict(context)

        # Check if context requests an on-the-fly Mermaid diagram
        if "_mermaid_diagrams" in ctx and isinstance(ctx["_mermaid_diagrams"], dict):
            try:
                from src.ppt_engine.diagram_engine import compile_mermaid
                for key, mermaid_code in ctx["_mermaid_diagrams"].items():
                    res = compile_mermaid(mermaid_code)
                    if res.get("png") and Path(res["png"]).exists():
                        ctx[key] = InlineImage(self.doc, str(res["png"]), width=Inches(5.5))
            except Exception as e:
                print(f"[Warning] Diagram compilation failed for Word doc: {e}")

        # Render with Jinja2 engine
        self.doc.render(ctx)

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(out_p))

        report = None
        if auto_lint:
            report = lint_document(out_p)

        return out_p, report


def stamp_template(
    template_name_or_path: Union[str, Path],
    context: Union[Dict[str, Any], BaseModel],
    output_path: Union[str, Path],
    auto_lint: bool = True,
) -> Tuple[Path, Optional[LintReport]]:
    """Convenience helper to load, stamp, and validate a document in one call."""
    stamper = TemplateStamper(template_name_or_path)
    return stamper.render(context=context, output_path=output_path, auto_lint=auto_lint)
