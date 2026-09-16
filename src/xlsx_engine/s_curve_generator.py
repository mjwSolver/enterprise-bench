"""
Enterprise Project S-Curve Engine
=================================
Automates mathematical generation, variance analysis, milestone tracking,
and openpyxl LineChart injection for cumulative project progress S-curves.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import openpyxl
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.axis import ChartLines, NumericAxis
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.core.config import OUTPUT_DIR, get_template_path, validate_clean_path


# ============================================================================
# Domain Models & Dataclasses
# ============================================================================

@dataclass
class SCurvePoint:
    """Individual period data point on the project S-curve."""
    period: str
    planned_pct: float
    actual_pct: Optional[float] = None
    variance: Optional[float] = None
    variance_pct: Optional[float] = None
    health: str = "PLANNED"
    milestone: Optional[str] = None


@dataclass
class VarianceAnalysis:
    """Consolidated project variance, SPI, and milestone health metrics."""
    current_period: Optional[str] = None
    current_period_idx: Optional[int] = None
    current_planned_pct: Optional[float] = None
    current_actual_pct: Optional[float] = None
    current_variance: Optional[float] = None
    current_variance_pct: Optional[float] = None
    overall_health: str = "PLANNED"
    spi: float = 1.0
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    points: List[SCurvePoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_period": self.current_period,
            "current_period_idx": self.current_period_idx,
            "current_planned_pct": self.current_planned_pct,
            "current_actual_pct": self.current_actual_pct,
            "current_variance": self.current_variance,
            "current_variance_pct": self.current_variance_pct,
            "overall_health": self.overall_health,
            "spi": self.spi,
            "milestones": self.milestones,
        }


# ============================================================================
# Mathematical Distribution Generators
# ============================================================================

def calculate_sigmoid_curve(
    num_periods: int,
    k: float = 10.0,
    x0: float = 0.5,
) -> List[float]:
    """
    Generate normalized Sigmoid (logistic) cumulative S-curve values from 0.0 to 1.0.

    f(x) = (g(x) - g(0)) / (g(1) - g(0)), where g(x) = 1 / (1 + exp(-k * (x - x0)))
    """
    if num_periods <= 1:
        return [1.0] * num_periods

    raw: List[float] = []
    for i in range(num_periods):
        x = i / (num_periods - 1)
        val = 1.0 / (1.0 + math.exp(-k * (x - x0)))
        raw.append(val)

    g0, g1 = raw[0], raw[-1]
    span = g1 - g0 if g1 != g0 else 1.0
    return [round((v - g0) / span, 4) for v in raw]


def calculate_polynomial_curve(
    num_periods: int,
    method: str = "smoothstep",
) -> List[float]:
    """
    Generate normalized polynomial cumulative S-curve values from 0.0 to 1.0.

    - cubic smoothstep: 3*x^2 - 2*x^3
    - quintic smootherstep: 6*x^5 - 15*x^4 + 10*x^3
    """
    if num_periods <= 1:
        return [1.0] * num_periods

    curve: List[float] = []
    for i in range(num_periods):
        x = i / (num_periods - 1)
        if method == "quintic":
            val = 6.0 * (x ** 5) - 15.0 * (x ** 4) + 10.0 * (x ** 3)
        else:  # cubic smoothstep
            val = 3.0 * (x ** 2) - 2.0 * (x ** 3)
        curve.append(round(max(0.0, min(1.0, val)), 4))
    return curve


def calculate_linear_curve(num_periods: int) -> List[float]:
    """Generate linear cumulative progress as a straight baseline."""
    if num_periods <= 1:
        return [1.0] * num_periods
    return [round(i / (num_periods - 1), 4) for i in range(num_periods)]


# ============================================================================
# Core Engine: SCurveGenerator
# ============================================================================

class SCurveGenerator:
    """
    Automated S-Curve Progress Engine.

    Features:
    - Mathematical distribution modeling (Sigmoid, Polynomial Smoothstep, Linear).
    - Planned vs. Actual progress curve harmonization.
    - Variance analysis (Schedule Variance points, SV %, SPI).
    - Milestone health indicators (ON_TRACK, AT_RISK, CRITICAL_DELAY).
    - OpenXML openpyxl LineChart construction with brand theme styling.
    - Stamping into existing templates or standalone workbooks.
    """

    # Corporate styling tokens
    COLOR_PRIMARY = "1E3A8A"      # Deep Navy Blue
    COLOR_ACTUAL = "10B981"       # Emerald Green
    COLOR_BORDER = "E2E8F0"       # Light Slate Border
    COLOR_HEADER_BG = "0F172A"    # Dark Slate Header
    COLOR_CARD_BG = "F8FAFC"      # Card Background

    HEALTH_COLORS = {
        "ON_TRACK": {"fill": "DCFCE7", "text": "166534"},       # Green
        "AT_RISK": {"fill": "FEF3C7", "text": "92400E"},        # Amber
        "CRITICAL_DELAY": {"fill": "FEE2E2", "text": "991B1B"}, # Red
        "COMPLETED": {"fill": "E0E7FF", "text": "3730A3"},      # Indigo
        "PLANNED": {"fill": "F1F5F9", "text": "475569"},        # Neutral Slate
    }

    def __init__(
        self,
        template: Optional[Union[str, Path]] = None,
        project_name: str = "Enterprise Modernization Project",
    ):
        self.project_name = project_name
        self.template_ref = template
        self.template_path = self._resolve_template(template) if template else None

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

    # ------------------------------------------------------------------------
    # Data Modeling & Math
    # ------------------------------------------------------------------------

    def generate_curve_data(
        self,
        periods: Optional[List[str]] = None,
        num_periods: int = 12,
        planned_pct: Optional[List[float]] = None,
        actual_pct: Optional[List[Optional[float]]] = None,
        distribution: str = "sigmoid",
        milestones: Optional[List[Dict[str, Any]]] = None,
        current_period_idx: Optional[int] = None,
        lag_factor: float = 0.0,
    ) -> List[SCurvePoint]:
        """
        Synthesize or harmonize cumulative S-curve points.

        If planned_pct is omitted, calculates cumulative curve using chosen distribution.
        If actual_pct is omitted and current_period_idx is set, simulates actual progress.
        """
        # 1. Resolve period labels
        if periods is None:
            n = len(planned_pct) if planned_pct else num_periods
            periods = [f"W{i+1:02d}" for i in range(n)]
        else:
            num_periods = len(periods)

        # 2. Resolve planned cumulative curve
        if planned_pct is None:
            dist = distribution.lower().strip()
            if dist in ("sigmoid", "logistic"):
                planned_pct = calculate_sigmoid_curve(num_periods)
            elif dist in ("polynomial", "smoothstep", "cubic"):
                planned_pct = calculate_polynomial_curve(num_periods, method="smoothstep")
            elif dist == "quintic":
                planned_pct = calculate_polynomial_curve(num_periods, method="quintic")
            elif dist == "linear":
                planned_pct = calculate_linear_curve(num_periods)
            else:
                planned_pct = calculate_sigmoid_curve(num_periods)

        # 3. Resolve actual cumulative curve
        if actual_pct is None and current_period_idx is not None:
            actual_pct = []
            for i in range(num_periods):
                if i <= current_period_idx:
                    p = planned_pct[i]
                    # Apply lag factor (e.g. -0.05 for 5% behind)
                    act = round(max(0.0, min(1.0, p + lag_factor)), 4)
                    actual_pct.append(act)
                else:
                    actual_pct.append(None)
        elif actual_pct is None:
            # All pending/future
            actual_pct = [None] * num_periods

        # 4. Map milestones by period index or period name
        milestone_map: Dict[str, str] = {}
        if milestones:
            for m in milestones:
                m_name = m.get("name", "Milestone")
                if "period" in m:
                    milestone_map[str(m["period"])] = m_name
                elif "week" in m:
                    w_idx = int(m["week"])
                    # Support 1-based week integer or 0-based
                    if 1 <= w_idx <= len(periods):
                        milestone_map[periods[w_idx - 1]] = m_name
                    elif 0 <= w_idx < len(periods):
                        milestone_map[periods[w_idx]] = m_name

        # 5. Build SCurvePoint list with variance & health evaluation
        points: List[SCurvePoint] = []
        for i, per in enumerate(periods):
            p_val = planned_pct[i] if i < len(planned_pct) else 1.0
            a_val = actual_pct[i] if (actual_pct and i < len(actual_pct)) else None

            var_val: Optional[float] = None
            var_pct_val: Optional[float] = None
            health = "PLANNED"

            if a_val is not None:
                var_val = round(a_val - p_val, 4)
                var_pct_val = round((var_val / p_val * 100), 2) if p_val > 0 else 0.0

                if a_val >= 1.0 or (p_val >= 1.0 and a_val >= 0.99):
                    health = "COMPLETED"
                elif var_val >= -0.03:
                    health = "ON_TRACK"
                elif -0.10 <= var_val < -0.03:
                    health = "AT_RISK"
                else:
                    health = "CRITICAL_DELAY"

            points.append(
                SCurvePoint(
                    period=per,
                    planned_pct=p_val,
                    actual_pct=a_val,
                    variance=var_val,
                    variance_pct=var_pct_val,
                    health=health,
                    milestone=milestone_map.get(per),
                )
            )

        return points

    def analyze_variance(
        self,
        curve_data: List[SCurvePoint],
        milestones: Optional[List[Dict[str, Any]]] = None,
    ) -> VarianceAnalysis:
        """Analyze schedule variance, SPI, and milestone health indicators."""
        # Find latest period with actual recorded data
        completed_points = [p for p in curve_data if p.actual_pct is not None]

        if not completed_points:
            return VarianceAnalysis(
                overall_health="PLANNED",
                spi=1.0,
                points=curve_data,
            )

        latest = completed_points[-1]
        latest_idx = curve_data.index(latest)

        planned_now = latest.planned_pct
        actual_now = latest.actual_pct or 0.0
        var_points = latest.variance or 0.0
        var_pct = latest.variance_pct or 0.0

        # Schedule Performance Index (SPI = EV / PV)
        spi = round(actual_now / planned_now, 3) if planned_now > 0 else 1.0

        # Evaluate milestone statuses
        ms_eval: List[Dict[str, Any]] = []
        if milestones is None:
            milestones = [
                {"name": pt.milestone, "period": pt.period}
                for pt in curve_data if pt.milestone
            ]

        if milestones:
            for m in milestones:
                m_copy = dict(m)
                p_label = str(m.get("period", ""))
                if not p_label and "week" in m:
                    w_idx = int(m["week"])
                    if 1 <= w_idx <= len(curve_data):
                        p_label = curve_data[w_idx - 1].period
                    elif 0 <= w_idx < len(curve_data):
                        p_label = curve_data[w_idx].period
                    m_copy["period"] = p_label

                # Find matching point
                match = next((pt for pt in curve_data if pt.period == p_label), None)
                if match:
                    if match.actual_pct is not None:
                        m_copy["actual_pct"] = match.actual_pct
                        m_copy["variance"] = match.variance
                        m_copy["status"] = match.health
                    else:
                        m_copy["status"] = "PENDING"
                else:
                    m_copy["status"] = "UNSCHEDULED"
                ms_eval.append(m_copy)


        return VarianceAnalysis(
            current_period=latest.period,
            current_period_idx=latest_idx,
            current_planned_pct=planned_now,
            current_actual_pct=actual_now,
            current_variance=var_points,
            current_variance_pct=var_pct,
            overall_health=latest.health,
            spi=spi,
            milestones=ms_eval,
            points=curve_data,
        )

    # ------------------------------------------------------------------------
    # Openpyxl Table Stamping & Chart Construction
    # ------------------------------------------------------------------------

    def stamp_and_chart(
        self,
        curve_data: List[SCurvePoint],
        output_path: Optional[Union[str, Path]] = None,
        sheet_name: str = "S-Curve",
        chart_title: str = "Project Progress S-Curve (Planned vs Actual)",
        chart_anchor: str = "I6",
        include_kpis: bool = True,
    ) -> Path:
        """
        Render S-curve table, format KPI summary cards, and embed openpyxl LineChart.
        """
        # 1. Load existing template or initialize new workbook
        if self.template_path:
            wb = openpyxl.load_workbook(str(self.template_path), data_only=False)
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
            else:
                ws = wb.create_sheet(title=sheet_name)
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name

        analysis = self.analyze_variance(curve_data)

        # 2. Render KPI Summary Header if requested
        if include_kpis:
            self._render_kpi_cards(ws, analysis)

        # 3. Render S-Curve Data Table
        start_row = 6 if include_kpis else 2
        start_col = 2  # Column B
        table_meta = self._render_table(ws, curve_data, start_row=start_row, start_col=start_col)

        # 4. Construct and attach openpyxl LineChart
        self._attach_line_chart(
            ws=ws,
            table_meta=table_meta,
            chart_title=chart_title,
            anchor=chart_anchor,
        )

        # 5. Save workbook
        if output_path is None:
            prefix = self.template_path.stem if self.template_path else "project"
            output_p = OUTPUT_DIR / f"scurve_{prefix}.xlsx"
        else:
            output_p = Path(output_path)

        output_p.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(output_p))
        wb.close()

        return output_p

    def _render_kpi_cards(self, ws: openpyxl.worksheet.worksheet.Worksheet, analysis: VarianceAnalysis) -> None:
        """Render 4 executive KPI summary cards above the data table."""
        # Clean gridlines visibility
        ws.views.sheetView[0].showGridLines = True

        thin_side = Side(border_style="thin", color=self.COLOR_BORDER)
        card_border = Border(top=thin_side, left=thin_side, right=thin_side, bottom=thin_side)

        cards = [
            {
                "label": "CUT-OFF PERIOD",
                "val": analysis.current_period or "W01 (Plan)",
                "cols": (2, 3),  # B to C
                "color": "475569",
            },
            {
                "label": "PLANNED CUMULATIVE",
                "val": f"{(analysis.current_planned_pct or 0.0):.1%}",
                "cols": (4, 5),  # D to E
                "color": self.COLOR_PRIMARY,
            },
            {
                "label": "ACTUAL CUMULATIVE",
                "val": f"{(analysis.current_actual_pct or 0.0):.1%}" if analysis.current_actual_pct is not None else "N/A",
                "cols": (6, 7),  # F to G
                "color": self.COLOR_ACTUAL,
            },
            {
                "label": "SCHEDULE VARIANCE (SV)",
                "val": f"{(analysis.current_variance or 0.0):+.1%}" if analysis.current_variance is not None else "0.0%",
                "cols": (8, 9),  # H to I
                "color": "991B1B" if (analysis.current_variance or 0) < -0.05 else "166534",
            },
            {
                "label": "MILESTONE HEALTH",
                "val": analysis.overall_health.replace("_", " "),
                "cols": (10, 11),  # J to K
                "color": self.HEALTH_COLORS.get(analysis.overall_health, {}).get("text", "0F172A"),
                "fill": self.HEALTH_COLORS.get(analysis.overall_health, {}).get("fill", "F1F5F9"),
            },
        ]

        for card in cards:
            c1, c2 = card["cols"]
            ws.merge_cells(start_row=2, start_column=c1, end_row=2, end_column=c2)
            ws.merge_cells(start_row=3, start_column=c1, end_row=3, end_column=c2)

            top_cell = ws.cell(row=2, column=c1, value=card["label"])
            top_cell.font = Font(name="Calibri", size=8, bold=True, color="64748B")
            top_cell.alignment = Alignment(horizontal="center", vertical="center")

            val_cell = ws.cell(row=3, column=c1, value=card["val"])
            val_cell.font = Font(name="Calibri", size=13, bold=True, color=card["color"])
            val_cell.alignment = Alignment(horizontal="center", vertical="center")

            card_fill_hex = card.get("fill", self.COLOR_CARD_BG)
            fill_obj = PatternFill(start_color=card_fill_hex, end_color=card_fill_hex, fill_type="solid")

            for r in range(2, 4):
                for c in range(c1, c2 + 1):
                    cell = ws.cell(row=r, column=c)
                    cell.border = card_border
                    cell.fill = fill_obj

    def _render_table(
        self,
        ws: openpyxl.worksheet.worksheet.Worksheet,
        curve_data: List[SCurvePoint],
        start_row: int = 6,
        start_col: int = 2,
    ) -> Dict[str, Any]:
        """Render S-curve coordinate data with formatting, headers, and status fills."""
        headers = [
            "Period",
            "Planned Cum. %",
            "Actual Cum. %",
            "Schedule Variance",
            "Variance %",
            "Health Status",
            "Key Milestone / Deliverable",
        ]

        header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color=self.COLOR_HEADER_BG, end_color=self.COLOR_HEADER_BG, fill_type="solid")
        thin_side = Side(border_style="thin", color=self.COLOR_BORDER)
        cell_border = Border(top=thin_side, left=thin_side, right=thin_side, bottom=thin_side)

        # 1. Write headers
        for col_idx, h_text in enumerate(headers, start=start_col):
            c = ws.cell(row=start_row, column=col_idx, value=h_text)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = cell_border

        ws.row_dimensions[start_row].height = 26

        # 2. Write data rows
        curr_r = start_row + 1
        for pt in curve_data:
            ws.row_dimensions[curr_r].height = 20

            # Period (Col B)
            c_per = ws.cell(row=curr_r, column=start_col, value=pt.period)
            c_per.font = Font(name="Calibri", size=10, bold=True)
            c_per.alignment = Alignment(horizontal="center", vertical="center")
            c_per.border = cell_border

            # Planned Cum % (Col C)
            c_plan = ws.cell(row=curr_r, column=start_col + 1, value=pt.planned_pct)
            c_plan.font = Font(name="Calibri", size=10)
            c_plan.number_format = "0.0%"
            c_plan.alignment = Alignment(horizontal="right", vertical="center")
            c_plan.border = cell_border

            # Actual Cum % (Col D)
            c_act = ws.cell(row=curr_r, column=start_col + 2, value=pt.actual_pct if pt.actual_pct is not None else "")
            c_act.font = Font(name="Calibri", size=10, bold=True if pt.actual_pct is not None else False)
            if pt.actual_pct is not None:
                c_act.number_format = "0.0%"
            c_act.alignment = Alignment(horizontal="right", vertical="center")
            c_act.border = cell_border

            # Schedule Variance (Col E) - formula `=IF(ISBLANK(D{row}),"",D{row}-C{row})`
            var_formula = f'=IF(ISBLANK({get_column_letter(start_col + 2)}{curr_r}),"",{get_column_letter(start_col + 2)}{curr_r}-{get_column_letter(start_col + 1)}{curr_r})'
            c_var = ws.cell(row=curr_r, column=start_col + 3, value=var_formula)
            c_var.font = Font(name="Calibri", size=10)
            c_var.number_format = "+0.0%;-0.0%;0.0%"
            c_var.alignment = Alignment(horizontal="right", vertical="center")
            c_var.border = cell_border

            # Variance % (Col F) - formula `=IF(ISBLANK(D{row}),"",IF(C{row}>0,(D{row}-C{row})/C{row},0))`
            vp_formula = f'=IF(ISBLANK({get_column_letter(start_col + 2)}{curr_r}),"",IF({get_column_letter(start_col + 1)}{curr_r}>0,({get_column_letter(start_col + 2)}{curr_r}-{get_column_letter(start_col + 1)}{curr_r})/{get_column_letter(start_col + 1)}{curr_r},0))'
            c_vp = ws.cell(row=curr_r, column=start_col + 4, value=vp_formula)
            c_vp.font = Font(name="Calibri", size=10)
            c_vp.number_format = "+0.0%;-0.0%;0.0%"
            c_vp.alignment = Alignment(horizontal="right", vertical="center")
            c_vp.border = cell_border

            # Health Status (Col G)
            c_health = ws.cell(row=curr_r, column=start_col + 5, value=pt.health.replace("_", " "))
            h_cfg = self.HEALTH_COLORS.get(pt.health, self.HEALTH_COLORS["PLANNED"])
            c_health.font = Font(name="Calibri", size=9, bold=True, color=h_cfg["text"])
            c_health.fill = PatternFill(start_color=h_cfg["fill"], end_color=h_cfg["fill"], fill_type="solid")
            c_health.alignment = Alignment(horizontal="center", vertical="center")
            c_health.border = cell_border

            # Milestone (Col H)
            c_ms = ws.cell(row=curr_r, column=start_col + 6, value=pt.milestone or "")
            c_ms.font = Font(name="Calibri", size=9, italic=True if pt.milestone else False)
            c_ms.alignment = Alignment(horizontal="left", vertical="center")
            c_ms.border = cell_border

            curr_r += 1

        # Adjust column widths
        col_widths = {
            start_col: 10,       # Period
            start_col + 1: 15,   # Planned
            start_col + 2: 15,   # Actual
            start_col + 3: 17,   # Variance
            start_col + 4: 15,   # Variance %
            start_col + 5: 18,   # Health
            start_col + 6: 32,   # Milestone
        }
        for col_idx, width in col_widths.items():
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        return {
            "start_row": start_row,
            "end_row": curr_r - 1,
            "start_col": start_col,
            "end_col": start_col + len(headers) - 1,
            "num_rows": len(curve_data),
        }

    def _attach_line_chart(
        self,
        ws: openpyxl.worksheet.worksheet.Worksheet,
        table_meta: Dict[str, Any],
        chart_title: str,
        anchor: str = "J6",
    ) -> LineChart:
        """Construct and anchor an openpyxl LineChart visualizing Planned vs Actual curves."""
        chart = LineChart()
        chart.title = chart_title
        chart.style = 10
        chart.width = 19
        chart.height = 12

        # Axes labels & styling
        chart.y_axis.title = "Cumulative Progress (%)"
        chart.x_axis.title = "Project Timeline"
        chart.y_axis.number_format = "0%"
        chart.y_axis.scaling.min = 0.0
        chart.y_axis.scaling.max = 1.05
        chart.y_axis.majorUnit = 0.1
        chart.y_axis.majorGridlines = ChartLines()

        # Legend position at bottom
        chart.legend.legendPos = "b"

        # References to Planned and Actual columns
        # Planned is start_col + 1, Actual is start_col + 2
        start_row = table_meta["start_row"]
        end_row = table_meta["end_row"]
        start_col = table_meta["start_col"]

        data_ref = Reference(
            ws,
            min_col=start_col + 1,
            min_row=start_row,
            max_col=start_col + 2,
            max_row=end_row,
        )
        cats_ref = Reference(
            ws,
            min_col=start_col,
            min_row=start_row + 1,
            max_row=end_row,
        )

        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats_ref)

        # Style Series 1: Planned Cumulative Progress
        if len(chart.series) >= 1:
            s_plan = chart.series[0]
            s_plan.graphicalProperties.line.solidFill = self.COLOR_PRIMARY
            s_plan.graphicalProperties.line.width = 25000  # ~2pt
            s_plan.smooth = True

        # Style Series 2: Actual Cumulative Progress
        if len(chart.series) >= 2:
            s_act = chart.series[1]
            s_act.graphicalProperties.line.solidFill = self.COLOR_ACTUAL
            s_act.graphicalProperties.line.width = 32000  # ~2.5pt
            s_act.smooth = True
            # Marker configuration
            s_act.marker.symbol = "circle"
            s_act.marker.size = 6
            s_act.marker.graphicalProperties.solidFill = self.COLOR_ACTUAL
            s_act.marker.graphicalProperties.line.solidFill = self.COLOR_ACTUAL

        ws.add_chart(chart, anchor)
        return chart

    # ------------------------------------------------------------------------
    # High-Level One-Shot Generation
    # ------------------------------------------------------------------------

    def generate(
        self,
        output_path: Optional[Union[str, Path]] = None,
        periods: Optional[List[str]] = None,
        num_periods: int = 12,
        planned_pct: Optional[List[float]] = None,
        actual_pct: Optional[List[Optional[float]]] = None,
        distribution: str = "sigmoid",
        milestones: Optional[List[Dict[str, Any]]] = None,
        current_period_idx: Optional[int] = None,
        lag_factor: float = 0.0,
        sheet_name: str = "S-Curve",
        chart_title: str = "Project Progress S-Curve (Planned vs Actual)",
        chart_anchor: str = "J6",
    ) -> Path:
        """One-shot method to generate S-curve data and stamp workbook with chart."""
        points = self.generate_curve_data(
            periods=periods,
            num_periods=num_periods,
            planned_pct=planned_pct,
            actual_pct=actual_pct,
            distribution=distribution,
            milestones=milestones,
            current_period_idx=current_period_idx,
            lag_factor=lag_factor,
        )

        return self.stamp_and_chart(
            curve_data=points,
            output_path=output_path,
            sheet_name=sheet_name,
            chart_title=chart_title,
            chart_anchor=chart_anchor,
        )


# ============================================================================
# Standalone Convenience Helper
# ============================================================================

def generate_s_curve(
    template: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None,
    periods: Optional[List[str]] = None,
    num_periods: int = 12,
    planned_pct: Optional[List[float]] = None,
    actual_pct: Optional[List[Optional[float]]] = None,
    distribution: str = "sigmoid",
    milestones: Optional[List[Dict[str, Any]]] = None,
    current_period_idx: Optional[int] = None,
    lag_factor: float = 0.0,
    sheet_name: str = "S-Curve",
    chart_title: str = "Project Progress S-Curve (Planned vs Actual)",
    project_name: str = "Enterprise Modernization Project",
) -> Path:
    """Convenience functional wrapper around SCurveGenerator."""
    gen = SCurveGenerator(template=template, project_name=project_name)
    return gen.generate(
        output_path=output_path,
        periods=periods,
        num_periods=num_periods,
        planned_pct=planned_pct,
        actual_pct=actual_pct,
        distribution=distribution,
        milestones=milestones,
        current_period_idx=current_period_idx,
        lag_factor=lag_factor,
        sheet_name=sheet_name,
        chart_title=chart_title,
    )
