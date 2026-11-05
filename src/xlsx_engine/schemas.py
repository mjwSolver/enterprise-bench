"""
src/xlsx_engine/schemas.py
==========================
Pydantic v2 schemas for typed spreadsheet calculations and S-Curve models.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SCurveMilestone(BaseModel):
    """Represents a discrete milestone in an S-Curve project schedule."""
    id: str = Field(..., description="Unique milestone identifier (e.g. M1, M2)")
    name: str = Field(..., description="Descriptive milestone title")
    weight: float = Field(..., ge=0.0, le=100.0, description="Planned percentage weight (sum to 100)")
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_completion: Optional[date] = None
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Current progress percentage")


class SCurvePayload(BaseModel):
    """Complete input configuration for S-Curve calculation and chart generation."""
    project_id: str
    project_name: str
    baseline_budget_idr: float = Field(default=0.0, ge=0.0)
    total_duration_weeks: int = Field(default=12, gt=0)
    milestones: List[SCurveMilestone] = Field(default_factory=list)

    @field_validator("milestones")
    @classmethod
    def validate_weights(cls, v: List[SCurveMilestone]) -> List[SCurveMilestone]:
        if not v:
            return v
        total = sum(m.weight for m in v)
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Milestone weights must sum to 100.0% (current sum: {total:.2f}%)")
        return v


class CellMapping(BaseModel):
    """Single targeted cell update specification."""
    sheet: Optional[str] = None
    cell: str = Field(..., pattern=r"^\$?[A-Za-z]+\$?[0-9]+$")
    value: Any

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any) -> Any:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            raise ValueError(f"Cell value cannot be NaN or Infinite: {v}")
        return v


class CalculatorDataPayload(BaseModel):
    """Typed payload for calculator and spreadsheet template population."""
    cell_mappings: List[CellMapping] = Field(default_factory=list)
    append_rows: Dict[str, List[List[Any]]] = Field(default_factory=dict)
    scalar_replacements: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)

    @field_validator("scalar_replacements")
    @classmethod
    def validate_scalars(cls, v: Dict[str, Union[str, int, float, bool]]) -> Dict[str, Union[str, int, float, bool]]:
        for k, val in v.items():
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                raise ValueError(f"Scalar replacement '{k}' cannot be NaN or Infinite: {val}")
        return v

    @field_validator("append_rows")
    @classmethod
    def validate_append_rows(cls, v: Dict[str, List[List[Any]]]) -> Dict[str, List[List[Any]]]:
        for s_name, rows in v.items():
            for r_idx, row in enumerate(rows):
                for c_idx, cell_val in enumerate(row):
                    if isinstance(cell_val, float) and (math.isnan(cell_val) or math.isinf(cell_val)):
                        raise ValueError(f"Appended row {r_idx} col {c_idx} in sheet '{s_name}' cannot be NaN or Infinite")
        return v

    @field_validator("cell_mappings")
    @classmethod
    def validate_cell_mappings_cycles(cls, v: List[CellMapping]) -> List[CellMapping]:
        from openpyxl.formula.tokenizer import Tokenizer
        coord_re = re.compile(r"^\$?[A-Za-z]+\$?[0-9]+$")
        graph: Dict[str, List[str]] = {}
        for m in v:
            clean_src = m.cell.replace("$", "").upper()
            if isinstance(m.value, str) and m.value.startswith("="):
                graph[clean_src] = []
                try:
                    tok = Tokenizer(m.value)
                    for t in tok.items:
                        if t.subtype == "RANGE":
                            clean_target = t.value.replace("$", "").upper()
                            if coord_re.match(clean_target):
                                graph[clean_src].append(clean_target)
                except Exception:
                    pass

        visited: Dict[str, int] = {}
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
            raise ValueError(f"Cyclic cell reference detected in cell_mappings: {' -> '.join(cycles[0])}")
        return v
