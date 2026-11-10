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


def test_optional_takeaway_bars_not_forced_by_builders():
    from src.ppt_engine.consulting_archetypes import (
        build_gap_analysis_slide,
        build_crisp_dm_gate_slide,
        build_medallion_tiers_slide,
    )

    theme = get_theme("brickred")
    prs = create_presentation(theme)

    s_gap = build_gap_analysis_slide(
        prs=prs,
        theme=theme,
        left_items=["Legacy batch jobs delay reporting by 24 hours."],
        right_items=["Dynamic tables refresh continuously on change."],
        takeaway=None,
    )
    gap_texts = "\n".join(sh.text_frame.text for sh in s_gap.shapes if sh.has_text_frame)
    assert "EXECUTIVE TAKEAWAY" not in gap_texts

    s_crisp = build_crisp_dm_gate_slide(prs=prs, theme=theme)
    crisp_texts = "\n".join(sh.text_frame.text for sh in s_crisp.shapes if sh.has_text_frame)
    assert "GOVERNING INVARIANT" not in crisp_texts

    s_med = build_medallion_tiers_slide(prs=prs, theme=theme)
    med_texts = "\n".join(sh.text_frame.text for sh in s_med.shapes if sh.has_text_frame)
    assert "DATA INTEGRITY RULE" not in med_texts


def test_linter_flags_takeaway_fatigue_and_filler(tmp_path: Path):
    import yaml
    from src.ppt_engine.spec_linter import lint_presentation_spec

    saturated_spec = {
        "slides": [
            {
                "archetype": "card_grid",
                "title": "Modern Storage Architecture Cuts Cloud Storage Spend by Half",
                "subtitle": "Parquet compression removes duplicate staging snapshots across workspaces.",
                "takeaway": "EXECUTIVE TAKEAWAY: Modern storage architecture cuts cloud storage spend by half.",
                "items": [{"title": "Compression", "bullets": ["**Cuts spend:** Uses Zstd column encoding."]}],
            },
            {
                "archetype": "table",
                "title": "Automated Pipeline Checks Eliminate Schema Drift Before Release",
                "subtitle": "Pre-merge schema audits verify column contracts across staging tables.",
                "takeaway": "Decision Gate: Require schema audit pass before production deployment.",
                "columns": [{"header": "Check", "width": 4.0}, {"header": "Status", "width": 2.0}],
                "rows": [["Schema validation", "PASS"]],
            },
            {
                "archetype": "chevron_process",
                "title": "Four Delivery Stages Migrate Teams Onto Governed Tables",
                "subtitle": "Sequential rollout avoids downtime during consumer cutover.",
                "takeaway": "Rollout Note: Keep dual writes active during week one.",
                "steps": [{"num": "01", "title": "Ingest", "status": "DONE", "deliverables": ["Snowpipe"]}],
            },
        ]
    }
    bad_path = tmp_path / "saturated.yaml"
    bad_path.write_text(yaml.safe_dump(saturated_spec), encoding="utf-8")

    rep_bad = lint_presentation_spec(bad_path, strict=True)
    rule_ids = {i.rule_id for i in rep_bad.issues}
    assert "LINT008_TAKEAWAY_FATIGUE" in rule_ids
    assert "LINT008_TAKEAWAY_DISCIPLINE" in rule_ids
    assert not rep_bad.passed

    lean_spec = {
        "slides": [
            {
                "archetype": "card_grid",
                "title": "Modern Storage Architecture Cuts Cloud Storage Spend by Half",
                "subtitle": "Parquet compression removes duplicate staging snapshots across workspaces.",
                "items": [{"title": "Compression", "bullets": ["**Cuts spend:** Uses Zstd column encoding."]}],
            },
            {
                "archetype": "table",
                "title": "Automated Pipeline Checks Eliminate Schema Drift Before Release",
                "subtitle": "Pre-merge schema audits verify column contracts across staging tables.",
                "takeaway": "Decision Gate: Enforce schema check block on all production merges.",
                "columns": [{"header": "Check", "width": 4.0}, {"header": "Status", "width": 2.0}],
                "rows": [["Schema validation", "PASS"]],
            },
            {
                "archetype": "chevron_process",
                "title": "Four Delivery Stages Migrate Teams Onto Governed Tables",
                "subtitle": "Sequential rollout avoids downtime during consumer cutover.",
                "steps": [{"num": "01", "title": "Ingest", "status": "DONE", "deliverables": ["Snowpipe"]}],
            },
        ]
    }
    good_path = tmp_path / "lean.yaml"
    good_path.write_text(yaml.safe_dump(lean_spec), encoding="utf-8")

    rep_good = lint_presentation_spec(good_path, strict=True)
    assert rep_good.passed


def test_catalog_examples_treat_takeaway_as_opt_in():
    from src.ppt_engine.archetypes.catalog import ARCHETYPE_REGISTRY

    uncommented_examples = [
        name
        for name, meta in ARCHETYPE_REGISTRY.items()
        if any(line.strip().startswith("takeaway:") for line in meta.get("example_yaml", "").splitlines())
    ]
    assert len(uncommented_examples) <= 2
