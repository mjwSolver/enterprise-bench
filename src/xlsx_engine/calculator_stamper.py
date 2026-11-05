"""
Spreadsheet Calculator & Template Stamper
========================================
Automates data injection, cell calculation, and formula-preserving modifications
for Microsoft Excel (.xlsx) templates.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import openpyxl
from openpyxl.utils.cell import coordinate_to_tuple

from src.core.config import OUTPUT_DIR, get_template_path, validate_clean_path

logger = logging.getLogger(__name__)

_COORD_REGEX = re.compile(r"^\$?[A-Za-z]+\$?[0-9]+$")


@lru_cache(maxsize=8192)
def _fast_coord_to_tuple(coord: str) -> Tuple[int, int]:
    """LRU-cached coordinate-to-tuple converter avoiding repeated regex overhead."""
    return coordinate_to_tuple(coord)


def _fast_set_cell_value(ws: openpyxl.worksheet.worksheet.Worksheet, cell_ref: str, val: Any) -> None:
    """Inject cell value using cached row/column tuples with fallback to standard setter."""
    try:
        r, c = _fast_coord_to_tuple(cell_ref)
        ws.cell(row=r, column=c, value=val)
    except Exception:
        ws[cell_ref] = val


def detect_cyclic_references(wb: openpyxl.Workbook) -> Dict[str, List[List[str]]]:
    """
    Detect circular formula dependencies within worksheets of an Excel workbook.
    Returns a dictionary mapping worksheet title to lists of cyclic cell paths.
    """
    from openpyxl.formula.tokenizer import Tokenizer

    cycles_by_sheet: Dict[str, List[List[str]]] = {}

    for ws in wb.worksheets:
        graph: Dict[str, List[str]] = {}
        for cell in ws._cells.values():
            val = cell.value
            if isinstance(val, str) and val.startswith("="):
                    src = cell.coordinate
                    graph[src] = []
                    try:
                        tok = Tokenizer(val)
                        for t in tok.items:
                            if t.subtype == "RANGE":
                                clean = t.value.replace("$", "").upper()
                                if _COORD_REGEX.match(clean):
                                    graph[src].append(clean)
                    except Exception:
                        pass

        if not graph:
            continue

        visited: Dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=visited
        cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]) -> None:
            visited[node] = 1
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited or visited[neighbor] == 0:
                    dfs(neighbor, path)
                elif visited[neighbor] == 1:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            path.pop()
            visited[node] = 2

        for node in list(graph.keys()):
            if node not in visited:
                dfs(node, [])

        if cycles:
            cycles_by_sheet[ws.title] = cycles

    return cycles_by_sheet


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

        # Pre-flight check for cyclic formula references
        cycles = detect_cyclic_references(wb)
        if cycles:
            first_sheet = next(iter(cycles))
            cycle_path = " -> ".join(cycles[first_sheet][0])
            wb.close()
            raise ValueError(f"Cyclic cell reference detected in worksheet '{first_sheet}': {cycle_path}")

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
        for key, val in data.items():
            if key == "append_rows":
                continue

            # Nested sheet mapping: {"SheetName": {"A1": 10}}
            if key in wb.sheetnames and isinstance(val, dict):
                ws = wb[key]
                for cell_ref, cell_val in val.items():
                    try:
                        _fast_set_cell_value(ws, cell_ref, cell_val)
                    except Exception as e:
                        logger.warning("Failed injecting value into %s cell %s: %s", ws.title, cell_ref, e)
                continue

            # Coordinate with sheet prefix: "Sheet1!A1"
            if "!" in key:
                sheet_part, cell_ref = key.split("!", 1)
                sheet_part = sheet_part.strip("'\"")
                if sheet_part in wb.sheetnames:
                    ws = wb[sheet_part]
                    try:
                        _fast_set_cell_value(ws, cell_ref, val)
                    except Exception as e:
                        logger.warning("Failed injecting value into %s cell %s: %s", sheet_part, cell_ref, e)
                continue

            # Direct cell coordinate on active sheet: "A1"
            if _COORD_REGEX.match(key):
                try:
                    _fast_set_cell_value(active_ws, key, val)
                except Exception as e:
                    logger.warning("Failed injecting value into active sheet cell %s: %s", key, e)
                continue

        # 3. String placeholder scan for {{ key }} substitutions
        scalar_replacements = {
            k: v for k, v in data.items()
            if isinstance(v, (str, int, float, bool))
        }
        if scalar_replacements:
            tag_pairs = [
                (f"{{{{ {var_k} }}}}", str(var_v)) for var_k, var_v in scalar_replacements.items()
            ] + [
                (f"{{{{{var_k}}}}}", str(var_v)) for var_k, var_v in scalar_replacements.items()
            ]
            for ws in wb.worksheets:
                for cell in ws._cells.values():
                    val = cell.value
                    if isinstance(val, str) and "{{" in val:
                        for tag, rep in tag_pairs:
                            if tag in val:
                                val = val.replace(tag, rep)
                        cell.value = val


def calculate_spreadsheet(
    template: Union[str, Path],
    data: Optional[Dict[str, Any]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Convenience helper to load template, inject data, and save calculated output."""
    stamper = CalculatorStamper(template)
    return stamper.calculate(data=data, output_path=output_path)
