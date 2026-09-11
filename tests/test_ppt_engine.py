"""
Unit Tests for PPT Engine
"""
from pathlib import Path
import pytest
from pptx import Presentation
from src.ppt_engine.theme_engine import get_theme, list_available_themes
from src.ppt_engine.consulting_archetypes import (
    create_presentation,
    HorizonColumnData,
    build_bcg_3_horizon_slide,
    ScorecardQuadrantData,
    ScorecardMetric,
    build_balanced_scorecard_slide,
)


def test_theme_retrieval():
    theme = get_theme("brickred")
    assert theme.name == "brickred"
    assert theme.get_hex("accent") == "#DC2626"


def test_deck_generation(tmp_path: Path):
    theme = get_theme("brickred")
    prs = create_presentation(theme)

    h1 = HorizonColumnData(
        horizon_tag="HORIZON 1",
        title="Stabilize",
        strategic_focus="Foundation",
        metric_highlight="99.9%",
        metric_label="SLA",
        initiatives=["Action 1", "Action 2"],
    )
    build_bcg_3_horizon_slide(prs=prs, theme=theme, horizons=[h1, h1, h1])

    q1 = ScorecardQuadrantData(
        quadrant_title="1. FINANCIAL",
        tagline="TCO Reduction",
        metrics=[ScorecardMetric(label="ROI", value="24%", status="ON TRACK", description="Target: 20%")],
    )
    build_balanced_scorecard_slide(prs=prs, theme=theme, quadrants=[q1, q1, q1, q1])

    out_file = tmp_path / "test_output.pptx"
    prs.save(str(out_file))
    assert out_file.exists()
    assert out_file.stat().st_size > 0
