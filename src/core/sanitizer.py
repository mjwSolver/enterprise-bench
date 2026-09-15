"""
PII & Client Sanitizer Subsystem (Legacy & Compatibility Facade)
================================================================
Bridges legacy sanitization functions to the modernized, extensible
Universal PII Engine in `src.core.pii`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Re-export modern PII engine components for convenience
from src.core.pii import (
    PiiCategory,
    PiiConfidence,
    PiiEngine,
    PiiMatch,
    ReplacementMapping,
    SanitizeResult,
    ScanReport,
    generate_mapping,
    load_mapping_json,
    save_mapping_json,
    scan_directory,
    scan_file,
    sanitize_directory,
    sanitize_file,
)
from src.core.pii.detectors import DEFAULT_ORGANIZATION_RULES

# Backwards-compatible scrub rules
DEFAULT_SCRUB_RULES: List[Tuple[str, str]] = DEFAULT_ORGANIZATION_RULES


def sanitize_text(text: str, custom_rules: Optional[List[Tuple[str, str]]] = None) -> str:
    """Replace sensitive enterprise names in a string with Jinja placeholders."""
    if not text:
        return text
    rules = custom_rules or DEFAULT_SCRUB_RULES
    sanitized = text
    for pattern, replacement in rules:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    return sanitized


from src.core.docx_purger import purge_docx_elements, PurgeReport


def sanitize_docx(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    custom_rules: Optional[List[Tuple[str, str]]] = None,
    purge_elements: bool = True,
) -> Path:
    """
    Sanitize text and metadata within a Word (.docx) file.
    Uses the universal DocxHandler, followed by post-PII element purging
    (strips review comments, author highlights, and revision artifacts).
    """
    in_p = Path(input_path)
    out_p = Path(output_path) if output_path else in_p
    rules_dict = {pat: repl for pat, repl in (custom_rules or DEFAULT_SCRUB_RULES)}
    mapping = ReplacementMapping(strategy="jinja", replacements=rules_dict, strip_metadata=True)
    res = sanitize_file(in_p, out_p, mapping=mapping)

    if purge_elements:
        purge_docx_elements(out_p, out_p, purge_comments=True, purge_highlights=True, accept_revisions=True)

    return Path(res.output_path)


def sanitize_pptx(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    custom_rules: Optional[List[Tuple[str, str]]] = None,
) -> Path:
    """
    Sanitize text and metadata within a PowerPoint (.pptx) file.
    """
    in_p = Path(input_path)
    out_p = Path(output_path) if output_path else in_p
    rules_dict = {pat: repl for pat, repl in (custom_rules or DEFAULT_SCRUB_RULES)}
    mapping = ReplacementMapping(strategy="jinja", replacements=rules_dict, strip_metadata=True)
    res = sanitize_file(in_p, out_p, mapping=mapping)
    return Path(res.output_path)


def sanitize_xlsx(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    custom_rules: Optional[List[Tuple[str, str]]] = None,
) -> Path:
    """
    Sanitize cells, sheets, and metadata within an Excel (.xlsx) file.
    """
    in_p = Path(input_path)
    out_p = Path(output_path) if output_path else in_p
    rules_dict = {pat: repl for pat, repl in (custom_rules or DEFAULT_SCRUB_RULES)}
    mapping = ReplacementMapping(strategy="jinja", replacements=rules_dict, strip_metadata=True)
    res = sanitize_file(in_p, out_p, mapping=mapping)
    return Path(res.output_path)
