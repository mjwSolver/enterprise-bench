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


_SUPPORTED_INLINE_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"})
_ALL_IMAGE_EXTS = _SUPPORTED_INLINE_IMAGE_EXTS | {".webp", ".svg", ".ico"}


class TemplateStamper:
    """Orchestrates deterministic template stamping for enterprise Word documents."""

    def __init__(self, template_path: Union[str, Path]) -> None:
        p = Path(template_path)
        if not p.is_file():
            resolved = get_template_path(str(template_path))
            if resolved and resolved.is_file():
                p = resolved
            else:
                raise FileNotFoundError(f"Template not found: {template_path}")
        self.template_path = p
        self.doc = DocxTemplate(str(p))
        self._rendered: bool = False

    def render(
        self,
        context: Union[Dict[str, Any], BaseModel],
        output_path: Union[str, Path],
        auto_lint: bool = True,
        purge_elements: bool = True,
    ) -> Tuple[Path, Optional[LintReport]]:
        """
        Renders the template with the provided context dictionary or Pydantic model.
        Saves output to output_path, purges editorial artifacts, and runs verification lint.
        """
        # Reload fresh DocxTemplate if this stamper instance was already rendered previously
        if self._rendered or getattr(self.doc, "is_rendered", False):
            self.doc = DocxTemplate(str(self.template_path))
            self._rendered = False

        if isinstance(context, BaseModel):
            if hasattr(context, "to_template_context"):
                ctx = dict(context.to_template_context())
            else:
                ctx = context.model_dump()
        else:
            ctx = dict(context)

        # Auto-expand indexed attendee lists/tuples (e.g. for MoM templates)
        for list_key, prefix in (("client_attendees", "client_attendee"), ("vendor_attendees", "vendor_attendee")):
            attendees = ctx.get(list_key)
            if isinstance(attendees, (list, tuple)):
                upper_bound = max(10, len(attendees))
                for i in range(1, upper_bound + 1):
                    k = f"{prefix}_{i}"
                    if k not in ctx:
                        val = attendees[i - 1] if i <= len(attendees) else ""
                        ctx[k] = "" if val is None else val

        # Check if context requests on-the-fly Mermaid diagrams
        if "_mermaid_diagrams" in ctx and isinstance(ctx["_mermaid_diagrams"], dict):
            try:
                from src.ppt_engine.diagram_engine import compile_mermaid
            except Exception as e:
                print(f"[Warning] Could not import diagram compiler for Word doc: {e}")
                compile_mermaid = None

            for key, mermaid_code in ctx["_mermaid_diagrams"].items():
                if compile_mermaid is None or not mermaid_code:
                    ctx.setdefault(key, f"[Diagram: {key}]")
                    continue
                try:
                    res = compile_mermaid(mermaid_code)
                    png_path = res.get("png") if isinstance(res, dict) else None
                    if png_path and Path(png_path).is_file():
                        ctx[key] = InlineImage(self.doc, str(png_path), width=Inches(5.5))
                    else:
                        ctx.setdefault(key, f"[Diagram: {key}]")
                except Exception as e:
                    print(f"[Warning] Diagram compilation failed for '{key}' in Word doc: {e}")
                    ctx.setdefault(key, f"[Diagram: {key}]")

        # Handle logo placeholders (e.g. client_logo, vendor_logo)
        for logo_key, fallback_label in (("client_logo", "[ CLIENT LOGO ]"), ("vendor_logo", "")):
            val = ctx.get(logo_key)
            if not val:
                if logo_key not in ctx or val is None or logo_key == "client_logo":
                    ctx[logo_key] = fallback_label
                continue

            if isinstance(val, (str, Path)):
                img_path = Path(val)
                suffix = img_path.suffix.lower()
                if img_path.is_file() and suffix in _SUPPORTED_INLINE_IMAGE_EXTS:
                    try:
                        ctx[logo_key] = InlineImage(self.doc, str(img_path), width=Inches(1.8))
                    except Exception as e:
                        print(f"[Warning] Failed to insert {logo_key} image: {e}")
                        ctx[logo_key] = fallback_label
                elif suffix in _ALL_IMAGE_EXTS or "/" in str(val) or "\\" in str(val):
                    # Missing or unsupported image path; prevent raw file path from rendering into text
                    ctx[logo_key] = fallback_label

        # Render with Jinja2 engine
        self.doc.render(ctx)
        self._rendered = True

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(out_p))

        if purge_elements:
            from src.core.docx_purger import purge_docx_elements
            purge_docx_elements(out_p, out_p, purge_comments=True, purge_highlights=True, accept_revisions=True)

        report = None
        if auto_lint:
            report = lint_document(out_p)

        return out_p, report


def stamp_template(
    template_name_or_path: Union[str, Path],
    context: Union[Dict[str, Any], BaseModel],
    output_path: Union[str, Path],
    auto_lint: bool = True,
    purge_elements: bool = True,
) -> Tuple[Path, Optional[LintReport]]:
    """Convenience helper to load, stamp, and validate a document in one call."""
    stamper = TemplateStamper(template_name_or_path)
    return stamper.render(context=context, output_path=output_path, auto_lint=auto_lint, purge_elements=purge_elements)
