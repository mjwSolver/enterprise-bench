"""
Spreadsheet Calculator & Template Stamper
========================================
Automates data injection, cell calculation, and formula-preserving modifications
for Microsoft Excel (.xlsx) templates.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import openpyxl

from src.core.config import OUTPUT_DIR, get_template_path, validate_clean_path


class CalculatorStamper:
    """
    Handles data population and calculation injection for enterprise Excel templates.
    Preserves existing formulas, formatting, macros, and styles.
    """

    def __init__(self, template: Union[str, Path]):
        self.template_ref = template
        self.template_path = self._resolve_template(template)

    def _resolve_template(self, template: Union[str, Path]) -> Path:
        p = Path(template)
        if p.exists():
            return validate_clean_path(p)

        found = get_template_path(str(template))
        if found and found.exists():
            return found

        raise FileNotFoundError(
            f"Excel template '{template}' could not be resolved in clean_workspace/ or local paths."
        )

    def calculate(
        self,
        data: Optional[Dict[str, Any]] = None,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Inject data into the Excel template and save to output_path.

        Supported data structures:
        1. Cell coordinates:
           - {"Sheet1!B5": 100, "C5": 200}
           - {"SheetName": {"B5": 100, "C5": 200}}
        2. Placeholder replacement:
           - Cells containing `{{ var_name }}` or `{{var_name}}` replaced by data[var_name]
        3. Append rows:
           - {"append_rows": {"SheetName": [[val1, val2], ...]}} or {"append_rows": [[val1, val2], ...]}
        """
        wb = openpyxl.load_workbook(str(self.template_path), data_only=False)

        if data:
            self._apply_data(wb, data)

        if output_path is None:
            output_p = OUTPUT_DIR / f"calculated_{self.template_path.name}"
        else:
            output_p = Path(output_path)

        output_p.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(output_p))
        wb.close()

        return output_p

    def _apply_data(self, wb: openpyxl.Workbook, data: Dict[str, Any]) -> None:
        active_ws = wb.active

        # 1. Handle row append instructions if present
        if "append_rows" in data:
            append_inst = data["append_rows"]
            if isinstance(append_inst, dict):
                for s_name, rows in append_inst.items():
                    ws = wb[s_name] if s_name in wb.sheetnames else active_ws
                    for row in rows:
                        ws.append(row if isinstance(row, list) else [row])
            elif isinstance(append_inst, list):
                for row in append_inst:
                    active_ws.append(row if isinstance(row, list) else [row])

        # 2. Iterate keys and process sheets or coordinates
        coord_regex = re.compile(r"^\$?[A-Za-z]+\$?[0-9]+$")

        for key, val in data.items():
            if key == "append_rows":
                continue

            # Nested sheet mapping: {"SheetName": {"A1": 10}}
            if key in wb.sheetnames and isinstance(val, dict):
                ws = wb[key]
                for cell_ref, cell_val in val.items():
                    try:
                        ws[cell_ref] = cell_val
                    except Exception:
                        pass
                continue

            # Coordinate with sheet prefix: "Sheet1!A1"
            if "!" in key:
                sheet_part, cell_ref = key.split("!", 1)
                sheet_part = sheet_part.strip("'\"")
                if sheet_part in wb.sheetnames:
                    try:
                        wb[sheet_part][cell_ref] = val
                    except Exception:
                        pass
                continue

            # Direct cell coordinate on active sheet: "A1"
            if coord_regex.match(key):
                try:
                    active_ws[key] = val
                except Exception:
                    pass
                continue

        # 3. String placeholder scan for {{ key }} substitutions
        scalar_replacements = {
            k: v for k, v in data.items()
            if isinstance(v, (str, int, float, bool))
        }
        if scalar_replacements:
            for ws in wb.worksheets:
                for row in ws.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, str) and "{{" in cell.value:
                            for var_k, var_v in scalar_replacements.items():
                                tag1 = f"{{{{ {var_k} }}}}"
                                tag2 = f"{{{{{var_k}}}}}"
                                if tag1 in cell.value:
                                    cell.value = cell.value.replace(tag1, str(var_v))
                                if tag2 in cell.value:
                                    cell.value = cell.value.replace(tag2, str(var_v))


def calculate_spreadsheet(
    template: Union[str, Path],
    data: Optional[Dict[str, Any]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Convenience helper to load template, inject data, and save calculated output."""
    stamper = CalculatorStamper(template)
    return stamper.calculate(data=data, output_path=output_path)
