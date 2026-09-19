"""
src/xlsx_engine/schemas.py
==========================
Pydantic v2 schemas for typed spreadsheet calculations and S-Curve models.
"""

from __future__ import annotations

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


class CalculatorDataPayload(BaseModel):
    """Typed payload for calculator and spreadsheet template population."""
    cell_mappings: List[CellMapping] = Field(default_factory=list)
    append_rows: Dict[str, List[List[Any]]] = Field(default_factory=dict)
    scalar_replacements: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
