"""
Spreadsheet & Financial Calculation Engine
==========================================
Spreadsheet models, financial calculators, S-curve generators, and openpyxl automation.
"""

from src.xlsx_engine.calculator_stamper import CalculatorStamper, calculate_spreadsheet
from src.xlsx_engine.cloud_sizing import (
    CloudSizingConfig,
    CloudSizingResult,
    WarehouseSpec,
    calculate_cloud_sizing,
)
from src.xlsx_engine.ledger_models import (
    CloseoutChecklistItem,
    DefectEntry,
    IssueEntry,
    RiskEntry,
    StakeholderEntry,
    append_defect_to_list,
    append_issue_to_log,
    append_risk_to_register,
    append_stakeholder_to_register,
    update_closeout_checklist,
)
from src.xlsx_engine.s_curve_generator import (
    SCurveGenerator,
    SCurvePoint,
    VarianceAnalysis,
    generate_s_curve,
)
from src.xlsx_engine.timeline_aggregator import (
    TimelineAggregator,
    synchronize_timeline_s_curve,
)

__all__ = [
    "CalculatorStamper",
    "calculate_spreadsheet",
    "SCurveGenerator",
    "generate_s_curve",
    "SCurvePoint",
    "VarianceAnalysis",
    "CloudSizingConfig",
    "CloudSizingResult",
    "WarehouseSpec",
    "calculate_cloud_sizing",
    "RiskEntry",
    "IssueEntry",
    "DefectEntry",
    "StakeholderEntry",
    "CloseoutChecklistItem",
    "append_risk_to_register",
    "append_issue_to_log",
    "append_defect_to_list",
    "append_stakeholder_to_register",
    "update_closeout_checklist",
    "TimelineAggregator",
    "synchronize_timeline_s_curve",
]

