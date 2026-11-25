"""
Unit Tests: Mermaid Transpiler Hardening & WCAG / Perceptual Verifier
====================================================================
Covers:
1. Empty-graph guard in transpile_mermaid_to_spec raising ValueError.
2. Emoji-only --name fallback to diagram_id title in Mermaid transpiler.
3. CLI `bench diagram v2 ingest --strict` and long inline Mermaid (>300 chars) OSError guard.
4. audit_wcag_and_legibility inspecting spec.bullet_lists, spec.header, and canvas.background fallback.
5. PerceptualImageAnalyzer._is_ink_pixel dark-background pixel handling.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.ppt_engine.diagram_v2.mermaid_transpiler import transpile_mermaid_to_spec
from src.ppt_engine.diagram_v2.models import (
    BadgeSpec,
    BulletListSpec,
    CanvasConfig,
    ContainerSpec,
    DiagramSpec,
    FlowSpec,
    HeaderConfig,
    NodeSpec,
)
from src.ppt_engine.diagram_v2.visual_verifier import (
    PerceptualImageAnalyzer,
    Tier2VisualVerifier,
    audit_wcag_and_legibility,
)


@pytest.mark.parametrize(
    "bad_mermaid",
    [
        "",
        "   \n\t  ",
        "%% comment only\n%% another comment",
        "flowchart LR",
    ],
)
def test_transpile_mermaid_empty_graph_raises_value_error(bad_mermaid: str):
    """Empty, comment-only, or node-less Mermaid inputs must raise ValueError."""
    with pytest.raises(ValueError):
        transpile_mermaid_to_spec(bad_mermaid)


def test_transpile_mermaid_emoji_only_name_falls_back_to_diagram_id():
    """Emoji-only name falls back cleanly to title-cased diagram_id."""
    spec = transpile_mermaid_to_spec(
        "flowchart LR\n  A[API] --> B[(DB)]",
        diagram_id="payment_gateway_flow",
        name="🚀🔥",
    )
    assert spec.name == "Payment Gateway Flow"
    assert spec.header.action_title == "Payment Gateway Flow"


def test_cli_ingest_strict_and_long_inline_mermaid_no_oserror(tmp_path):
    """CLI ingest handles --strict failures and >300-char inline Mermaid strings without ENAMETOOLONG."""
    runner = CliRunner()

    # Empty graph with --strict exits with code 1
    res_empty = runner.invoke(app, ["diagram", "v2", "ingest", "--mermaid", "flowchart LR", "--strict"])
    assert res_empty.exit_code == 1

    # Long inline multi-line Mermaid (>350 chars) does not trigger OSError ENAMETOOLONG
    long_lines = ["flowchart LR"] + [f"  N{i}[Service Step {i}] --> N{i+1}[Service Step {i+1}]" for i in range(1, 14)]
    long_mermaid = "\n".join(long_lines)
    assert len(long_mermaid) > 300

    out_yaml = tmp_path / "long_ingested.yaml"
    res_long = runner.invoke(
        app,
        ["diagram", "v2", "ingest", "--mermaid", long_mermaid, "--no-audit", "-o", str(out_yaml)],
    )
    assert res_long.exit_code == 0, res_long.output
    assert out_yaml.is_file()


def test_audit_wcag_inspects_bullet_lists_header_and_canvas_background_fallback():
    """audit_wcag_and_legibility catches low-contrast/tiny bullet_lists, dark-on-dark header, and None fill_hex."""
    spec = DiagramSpec(
        id="wcag_edge",
        canvas=CanvasConfig(background="#0F172A"),
        header=HeaderConfig(
            show=True,
            action_title="Invisible Dark Title on Dark Canvas",
            subtitle="Low contrast subtitle on dark canvas",
        ),
        nodes=[
            NodeSpec.model_construct(
                id="n_none_fill",
                title="Transparent Node",
                subtitle=None,
                bullets=None,
                shape="rect",
                x=1.0,
                y=1.5,
                w=2.4,
                h=1.2,
                stroke_hex="#38BDF8",
                fill_hex=None,
                title_color="#0F172A",
                subtitle_color="#64748B",
            )
        ],
        bullet_lists=[
            BulletListSpec(
                id="bl_bad",
                x=4.0,
                y=2.0,
                w=3.0,
                h=1.5,
                items=["Low contrast item"],
                font_size=7.0,
                font_color="#1E293B",
            )
        ],
        flows=[
            FlowSpec.model_construct(
                id="f1",
                points=[[1.0, 2.0], [3.0, 2.0]],
                label="Dark Pill",
                label_bg_hex=None,
                label_text_hex="#0F172A",
                label_border_hex="#38BDF8",
                font_pt=9.0,
            )
        ],
    )

    # Mutate fill_hex / label_bg_hex to None post-init to verify audit_wcag_and_legibility canvas_bg fallback
    spec.nodes[0].fill_hex = None
    spec.flows[0].label_bg_hex = None

    findings, metrics = audit_wcag_and_legibility(spec)
    regions = {f.element_or_region: f for f in findings}

    assert "header:action_title" in regions
    assert regions["header:action_title"].severity == "CRITICAL"
    assert "header:subtitle" in regions
    assert "bullet_list:bl_bad" in regions
    assert regions["bullet_list:bl_bad"].severity == "CRITICAL"
    assert "node:n_none_fill" in regions
    assert "flow:f1" in regions
    assert "Global Typography" in regions
    assert metrics["min_font_pt"] == 7.0


def test_perceptual_is_ink_pixel_dark_background():
    """Dark background pixels matching canvas bg are excluded as background rather than ceiling ink."""
    dark_bg = (15, 23, 42)  # #0F172A
    assert PerceptualImageAnalyzer._is_ink_pixel(15, 23, 42, 255, bg_rgb=dark_bg) is False
    assert PerceptualImageAnalyzer._is_ink_pixel(255, 255, 255, 255, bg_rgb=dark_bg) is True
    assert PerceptualImageAnalyzer._is_ink_pixel(255, 255, 255, 255, bg_rgb=None) is False


def test_audit_wcag_flags_zero_font_size_without_truthiness_bypass():
    """0.0pt font sizes must not be masked by `or` truthiness fallbacks in audit_wcag_and_legibility."""
    spec = DiagramSpec(
        id="zero_pt_audit",
        header=HeaderConfig(show=False),
        bullet_lists=[BulletListSpec(id="bl0", x=1.0, y=1.5, items=["Tiny"], font_size=0.0)],
    )
    findings, metrics = audit_wcag_and_legibility(spec)
    assert metrics["min_font_pt"] == 0.0
    assert any(f.element_or_region == "Global Typography" and f.severity == "CRITICAL" for f in findings)


def test_tier2_visual_verifier_dark_canvas_and_light_slate_show_grid_no_false_100pct_ink(tmp_path):
    """Empty dark (#0F172A) and light-slate (#CBD5E1) canvases with show_grid do not report 100% ink density."""
    for bg, grid in (("#0F172A", True), ("#0F172A", False), ("#CBD5E1", False)):
        spec = DiagramSpec(
            id=f"empty_{bg.lstrip('#')}_{grid}",
            canvas=CanvasConfig(background=bg, show_grid=grid),
            header=HeaderConfig(show=False),
        )
        res = Tier2VisualVerifier(spec).verify(output_dir=tmp_path, generate_subagent_briefing=False)
        densities = res.perceptual_metrics.get("cell_densities_pct", [])
        if densities:
            assert max(densities) < 10.0, f"False ink density on empty {bg} (grid={grid}): {densities}"
        assert not any(
            f.dimension == "CEILING_GUTTER_SAFETY" and f.severity == "CRITICAL"
            for f in res.tier2_findings
        ), f"False CEILING_GUTTER_SAFETY CRITICAL on empty {bg} (grid={grid})"
