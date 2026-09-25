"""
Excel Spreadsheet (.xlsx) Format Handler
=========================================
Extracts and sanitizes text and metadata from Microsoft Excel workbooks,
inspecting cells across all worksheets, sheet titles, cell comments, and document properties.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set
from src.core.pii.handlers.base import BaseFormatHandler
from src.core.pii.models import SanitizeResult, TextNode

try:
    import openpyxl
except ImportError:
    openpyxl = None  # type: ignore


class XlsxHandler(BaseFormatHandler):
    """Handler for Microsoft Excel .xlsx spreadsheets."""

    @classmethod
    def supported_extensions(cls) -> Set[str]:
        return {".xlsx", ".xlsm"}

    def _ensure_lib(self):
        if openpyxl is None:
            raise ImportError("openpyxl is required for Excel handling. Install with 'uv sync --extra xlsx'")

    def extract_metadata(self, path: Path) -> Dict[str, str]:
        self._ensure_lib()
        wb = openpyxl.load_workbook(str(path), read_only=True)
        props = {}
        cp = wb.properties
        for attr in ["creator", "lastModifiedBy", "title", "subject", "description", "keywords"]:
            val = getattr(cp, attr, None)
            if val and str(val).strip():
                props[attr] = str(val).strip()
        wb.close()
        return props

    def extract_text_nodes(self, path: Path) -> List[TextNode]:
        self._ensure_lib()
        wb = openpyxl.load_workbook(str(path), data_only=False)
        nodes: List[TextNode] = []

        # 1. Sheet names
        for sheet_idx, sheet in enumerate(wb.worksheets):
            nodes.append(
                TextNode(
                    location=f"Sheet {sheet_idx + 1} Name",
                    text=sheet.title,
                    node_type="sheet_name",
                    context={"sheet": sheet.title},
                )
            )

            # 2. Iterate cells
            for row in sheet.iter_rows():
                for cell in row:
                    val = cell.value
                    if val is not None and isinstance(val, str):
                        t = val.strip()
                        if t:
                            nodes.append(
                                TextNode(
                                    location=f"Sheet '{sheet.title}' > Cell {cell.coordinate}",
                                    text=t,
                                    node_type="cell",
                                    context={"sheet": sheet.title, "coordinate": cell.coordinate},
                                )
                            )
                    # Cell comment if any
                    if cell.comment and cell.comment.text:
                        ct = cell.comment.text.strip()
                        if ct:
                            nodes.append(
                                TextNode(
                                    location=f"Sheet '{sheet.title}' > Cell {cell.coordinate} > Comment",
                                    text=ct,
                                    node_type="cell_comment",
                                    context={"sheet": sheet.title, "coordinate": cell.coordinate},
                                )
                            )

        # 3. Document properties
        meta = self.extract_metadata(path)
        for k, v in meta.items():
            nodes.append(
                TextNode(
                    location=f"Metadata > {k}",
                    text=v,
                    node_type="core_property",
                    context={"property": k},
                )
            )

        wb.close()
        return nodes

    def apply_replacements(
        self,
        input_path: Path,
        output_path: Path,
        replacements: Dict[str, str],
        strip_metadata: bool = True,
        metadata_overrides: Dict[str, str] | None = None,
    ) -> SanitizeResult:
        self._ensure_lib()
        # Load workbook with formatting preserved
        wb = openpyxl.load_workbook(str(input_path))
        repl_count = 0
        details: List[str] = []
        sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
        # Compile replacement rules into regex patterns (supports both regexes and literals)
        compiled_rules: List[Tuple[re.Pattern, str]] = []
        for target, replacement in sorted_replacements:
            try:
                compiled_rules.append((re.compile(target, flags=re.IGNORECASE), replacement))
            except re.error:
                compiled_rules.append((re.compile(re.escape(target), flags=re.IGNORECASE), replacement))

        for sheet in wb.worksheets:
            # Check sheet title
            orig_title = sheet.title
            new_title = orig_title
            for regex, replacement in compiled_rules:
                if regex.search(new_title):
                    safe_repl = replacement.replace("{", "").replace("}", "")
                    new_title = regex.sub(safe_repl, new_title)[:31]
            if new_title != orig_title:
                sheet.title = new_title
                repl_count += 1
                details.append(f"Renamed sheet '{orig_title}' -> '{new_title}'")

            # Check cells
            for row in sheet.iter_rows():
                for cell in row:
                    val = cell.value
                    if val is not None and isinstance(val, str):
                        orig_val = val
                        new_val = orig_val
                        for regex, replacement in compiled_rules:
                            if regex.search(new_val):
                                new_val = regex.sub(replacement, new_val)
                        if new_val != orig_val:
                            cell.value = new_val
                            repl_count += 1
                            details.append(f"Cell {sheet.title}!{cell.coordinate}: replaced content")

                    if cell.comment and cell.comment.text:
                        orig_c = cell.comment.text
                        new_c = orig_c
                        for regex, replacement in compiled_rules:
                            if regex.search(new_c):
                                new_c = regex.sub(replacement, new_c)
                        if new_c != orig_c:
                            cell.comment.text = new_c
                            repl_count += 1

        # Clean metadata
        if strip_metadata:
            overrides = metadata_overrides or {
                "creator": "Enterprise Contributor",
                "lastModifiedBy": "Enterprise Contributor",
                "title": "",
                "description": "",
                "subject": "",
            }
            for prop_name, default_val in overrides.items():
                if hasattr(wb.properties, prop_name):
                    setattr(wb.properties, prop_name, default_val)
            details.append("Scrubbed workbook properties (creator, lastModifiedBy, title)")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(output_path))
        wb.close()

        return SanitizeResult(
            source_path=str(input_path),
            output_path=str(output_path),
            replacements_applied=repl_count,
            metadata_scrubbed=strip_metadata,
            details=details,
        )
