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
            if hasattr(context, "to_template_context"):
                ctx = context.to_template_context()
            else:
                ctx = context.model_dump()
        else:
            ctx = dict(context)

        # Auto-expand indexed attendee lists (e.g. for MoM templates)
        if "client_attendees" in ctx and isinstance(ctx["client_attendees"], list):
            for i in range(1, 11):
                k = f"client_attendee_{i}"
                if k not in ctx:
                    ctx[k] = ctx["client_attendees"][i - 1] if i <= len(ctx["client_attendees"]) else ""
        if "vendor_attendees" in ctx and isinstance(ctx["vendor_attendees"], list):
            for i in range(1, 11):
                k = f"vendor_attendee_{i}"
                if k not in ctx:
                    ctx[k] = ctx["vendor_attendees"][i - 1] if i <= len(ctx["vendor_attendees"]) else ""

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

        # Handle logo placeholders (e.g. client_logo, vendor_logo)
        for logo_key in ["client_logo", "vendor_logo"]:
            if logo_key in ctx:
                val = ctx[logo_key]
                if val and isinstance(val, (str, Path)):
                    img_path = Path(val)
                    if img_path.exists() and img_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                        try:
                            ctx[logo_key] = InlineImage(self.doc, str(img_path), width=Inches(1.8))
                        except Exception as e:
                            print(f"[Warning] Failed to insert {logo_key} image: {e}")
            else:
                if logo_key == "client_logo":
                    ctx[logo_key] = "[ CLIENT LOGO ]"

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
