"""
Timeline Aggregator & S-Curve Synchronizer
==========================================
Binds 4.2_Weekly_Progress_Timeline_Update_Template.xlsx directly to the
SCurveGenerator to extract daily planned/actual progression, compute weekly
cumulative milestones, and embed executive S-curve line charts.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import openpyxl

from src.core.config import OUTPUT_DIR, get_template_path, validate_clean_path
from src.xlsx_engine.s_curve_generator import (
    SCurveGenerator,
    SCurvePoint,
    VarianceAnalysis,
)


def _format_date(val: Any) -> str:
    """Format excel date value into ISO YYYY-MM-DD."""
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    return s[:10] if len(s) >= 10 else s


class TimelineAggregator:
    """
    Extracts and aggregates daily schedule tracking into weekly cumulative S-curves.
    """

    def __init__(self, timeline_path: Optional[Union[str, Path]] = None):
        p = timeline_path or get_template_path("4.2_Weekly_Progress_Timeline_Update_Template.xlsx")
        if not p or not Path(p).exists():
            raise FileNotFoundError(
                "4.2_Weekly_Progress_Timeline_Update_Template.xlsx template not found."
            )
        self.timeline_path = Path(p)

    def extract_s_curve(self, chunk_days: int = 7) -> VarianceAnalysis:
        """
        Parse daily planned (row 3) and actual (row 4) weights across date columns (col E onwards)
        and aggregate into weekly S-curve points.
        """
        wb = openpyxl.load_workbook(str(self.timeline_path), data_only=True)
        ws = wb.active

        daily_points: List[Dict[str, Any]] = []

        # Date header is at row 2, columns E (5) to max_column
        for c in range(5, ws.max_column + 1):
            raw_dt = ws.cell(2, c).value
            if not raw_dt:
                continue
            date_str = _format_date(raw_dt)

            raw_p = ws.cell(3, c).value
            raw_a = ws.cell(4, c).value
            raw_b = ws.cell(5, c).value

            p_val = float(raw_p) if isinstance(raw_p, (int, float)) else 0.0
            a_val = float(raw_a) if isinstance(raw_a, (int, float)) else None
            b_val = float(raw_b) if isinstance(raw_b, (int, float)) else 0.0

            daily_points.append({
                "date": date_str,
                "col": c,
                "planned": p_val,
                "actual": a_val,
                "baseline": b_val,
            })

        wb.close()

        if not daily_points:
            raise ValueError(f"No date progression points found in {self.timeline_path}")

        total_planned_weight = sum(d["planned"] for d in daily_points)
        if total_planned_weight <= 0:
            total_planned_weight = 100.0

        # Group into intervals (default 7 calendar days per week)
        periods: List[SCurvePoint] = []
        cum_p = 0.0
        cum_a = 0.0
        current_period_idx = None

        for idx in range(0, len(daily_points), chunk_days):
            chunk = daily_points[idx:idx + chunk_days]
            w_num = len(periods) + 1
            w_label = f"W{w_num:02d}"

            chunk_p = sum(d["planned"] for d in chunk)
            cum_p += chunk_p
            p_pct = round(min(1.0, cum_p / total_planned_weight), 4)

            actual_entries = [d["actual"] for d in chunk if d["actual"] is not None]
            has_actual = len(actual_entries) > 0

            if has_actual:
                current_period_idx = len(periods)
                chunk_a = sum(actual_entries)
                cum_a += chunk_a
                a_pct = round(min(1.0, cum_a / total_planned_weight), 4)
                var = round(a_pct - p_pct, 4)
                var_pct = round(var * 100, 2)

                # Health evaluation
                if var >= 0.0:
                    health = "ON TRACK"
                elif var >= -0.02:
                    health = "AT RISK"
                elif var >= -0.05:
                    health = "DELAYED"
                else:
                    health = "CRITICAL"
            else:
                a_pct = None
                var = None
                var_pct = None
                health = "PLANNED"

            start_d = chunk[0]["date"]
            end_d = chunk[-1]["date"]

            periods.append(
                SCurvePoint(
                    period=f"{w_label} ({start_d[:5]})",
                    planned_pct=p_pct,
                    actual_pct=a_pct,
                    variance=var,
                    variance_pct=var_pct,
                    health=health,
                )
            )

        # Consolidate overall variance metrics at latest active period
        curr_pt = periods[current_period_idx] if current_period_idx is not None else periods[0]
        spi = 1.0
        if curr_pt.planned_pct and curr_pt.planned_pct > 0 and curr_pt.actual_pct is not None:
            spi = round(curr_pt.actual_pct / curr_pt.planned_pct, 3)

        return VarianceAnalysis(
            current_period=curr_pt.period,
            current_period_idx=current_period_idx,
            current_planned_pct=curr_pt.planned_pct,
            current_actual_pct=curr_pt.actual_pct,
            current_variance=curr_pt.variance,
            current_variance_pct=curr_pt.variance_pct,
            overall_health=curr_pt.health,
            spi=spi,
            points=periods,
        )

    def synchronize_and_chart(
        self,
        output_path: Optional[Union[str, Path]] = None,
        chunk_days: int = 7,
    ) -> Path:
        """
        Extract cumulative curve points, load the original timeline workbook,
        and inject an executive 'S-Curve Analysis' tab with KPI cards, summary table,
        and native openpyxl LineChart.
        """
        analysis = self.extract_s_curve(chunk_days=chunk_days)

        out_path = Path(output_path) if output_path else OUTPUT_DIR / "updated_Weekly_Progress_Timeline_SCurve.xlsx"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        generator = SCurveGenerator(template=self.timeline_path)
        out_file = generator.stamp_and_chart(
            curve_data=analysis.points,
            output_path=out_path,
            sheet_name="S-Curve Analysis",
            chart_title="Data Application for Financial Analytics — Cumulative S-Curve",
            include_kpis=True,
        )
        return Path(out_file)


def synchronize_timeline_s_curve(
    timeline_path: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Tuple[Path, VarianceAnalysis]:
    """Helper to extract and chart S-curve from project timeline update spreadsheet."""
    agg = TimelineAggregator(timeline_path=timeline_path)
    analysis = agg.extract_s_curve()
    saved_path = agg.synchronize_and_chart(output_path=output_path)
    return saved_path, analysis
