"""
Unit Tests: Consulting Architecture Slide Builder & PitchDeckBuilder Resilience
=============================================================================
Covers:
1. build_diagram_v2_slide fitting diagram bounds cleanly above 7.05" footer divider.
2. build_diagram_v2_slide respecting dynamic header_bottom for multi-line consulting titles.
3. Missing spec_path fallback to spec_dict or diagnostic placeholder without FileNotFoundError.
4. PitchDeckBuilder.from_yaml storing self.spec_path, resolving relative/fallback paths, and
   gracefully falling back to inline nodes/containers when spec_path is absent.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from src.ppt_engine.archetypes.architecture import build_diagram_v2_slide
from src.ppt_engine.pitch_deck import PitchDeckBuilder
from src.ppt_engine.theme_engine import get_theme

EMU_PER_INCH = 914400.0


def test_build_diagram_v2_slide_template_clears_footer_divider():
    """Template extending to y=7.10\" must be fitted above the 7.05\" footer divider."""
    prs = Presentation()
    prs.slide_width = int(13.333 * EMU_PER_INCH)
    prs.slide_height = int(7.5 * EMU_PER_INCH)
    theme = get_theme("metrodata")

    slide = build_diagram_v2_slide(
        prs,
        theme,
        spec_path="specs/diagrams/template_medallion_architecture.yaml",
        tracker="ARCHITECTURE",
        action_title="Medallion Lakehouse Fits Cleanly Above Consulting Footer",
        subtitle="Verified vertical clearance against 7.05 inch footer divider",
        current_idx=2,
        total_slides=10,
        source="Platform Engineering",
    )

    diagram_shapes = [
        sh for sh in slide.shapes
        if (sh.name or "").startswith(("container:", "node:", "badge:", "bullet_list:", "flow:"))
    ]
    assert diagram_shapes, "Expected compiled Diagram V2 shapes on slide"
    max_bottom_in = max((sh.top + sh.height) / EMU_PER_INCH for sh in diagram_shapes)
    assert max_bottom_in <= 6.95, f"Diagram shape collided with footer divider (y2={max_bottom_in:.3f}\")"


def test_build_diagram_v2_slide_respects_tall_header_and_default_title():
    """Tall wrapped consulting headers push diagram top down cleanly; action_title=None uses spec header."""
    prs = Presentation()
    theme = get_theme("metrodata")

    spec_dict = {
        "id": "tall_header_fit",
        "header": {"show": True, "action_title": "Spec Default Headline"},
        "containers": [
            {"id": "c1", "label": "ZONE", "x": 0.45, "y": 1.35, "w": 12.0, "h": 5.75},
        ],
        "nodes": [
            {"id": "n1", "container_id": "c1", "title": "Service", "x": 1.0, "y": 1.85, "w": 2.4, "h": 1.2},
        ],
    }

    slide = build_diagram_v2_slide(
        prs,
        theme,
        spec_dict=spec_dict,
        tracker="DEEP DIVE",
        action_title=(
            "This Intentionally Very Long Consulting Action Headline Wraps Across Multiple Lines "
            "So Header Bottom Exceeds Canonical Ingress Line 1.35 Inches"
        ),
        subtitle="Supporting wrapped context subtitle line",
        show_diagram_header=False,
    )
    container_sh = next(sh for sh in slide.shapes if sh.name == "container:c1")
    assert container_sh.top / EMU_PER_INCH > 1.35
    assert (container_sh.top + container_sh.height) / EMU_PER_INCH <= 6.95

    # action_title=None + show_diagram_header=False uses spec.header.action_title in consulting header
    slide2 = build_diagram_v2_slide(prs, theme, spec_dict=spec_dict, action_title=None, show_diagram_header=False)
    assert not any(sh.name == "header:stripe:red" for sh in slide2.shapes)
    assert any(
        getattr(sh, "has_text_frame", False) and "Spec Default Headline" in sh.text_frame.text
        for sh in slide2.shapes
    )


def test_build_diagram_v2_slide_missing_spec_fallback_and_placeholder():
    """Missing spec_path falls back to spec_dict or diagnostic placeholder without FileNotFoundError."""
    prs = Presentation()
    theme = get_theme("metrodata")

    # 1. Fallback to spec_dict
    slide1 = build_diagram_v2_slide(
        prs,
        theme,
        spec_path="does/not/exist.yaml",
        spec_dict={
            "id": "fallback_spec",
            "nodes": [{"id": "n1", "title": "Fallback Node", "x": 1.0, "y": 2.0, "w": 2.5, "h": 1.2}],
        },
        action_title="Fallback Spec Works",
    )
    assert any(sh.name == "node:n1" for sh in slide1.shapes)

    # 2. Neither exists -> diagnostic placeholder card (no FileNotFoundError)
    slide2 = build_diagram_v2_slide(
        prs,
        theme,
        spec_path="does/not/exist_either.yaml",
        spec_dict=None,
        action_title="Missing Diagram Test",
    )
    assert any(
        getattr(sh, "has_text_frame", False) and "Missing Diagram V2 Specification" in sh.text_frame.text
        for sh in slide2.shapes
    )


def test_pitch_deck_builder_from_yaml_resolves_relative_and_inline_fallback(tmp_path: Path):
    """PitchDeckBuilder.from_yaml stores self.spec_path, resolves relative paths, and falls back to inline."""
    sub_dir = tmp_path / "decks"
    sub_dir.mkdir()
    rel_diag = sub_dir / "local_arch.yaml"
    rel_diag.write_text(
        """
id: rel_diag
nodes:
  - id: rel_node
    title: Relative Node
    x: 1.0
    y: 2.0
    w: 2.4
    h: 1.2
""",
        encoding="utf-8",
    )

    deck_yaml = sub_dir / "deck.yaml"
    deck_yaml.write_text(
        """
theme: metrodata
metadata:
  client_name: Example Corp
slides:
  - archetype: diagram_v2
    title: Relative Diagram
    spec_path: local_arch.yaml
  - archetype: diagram_v2
    title: Missing Spec Inline Fallback
    spec_path: missing_external.yaml
    nodes:
      - id: inline_n1
        title: Inline Fallback Node
        x: 1.0
        y: 2.0
        w: 2.4
        h: 1.2
""",
        encoding="utf-8",
    )

    builder = PitchDeckBuilder.from_yaml(deck_yaml)
    assert builder.spec_path == deck_yaml
    builder.build_all()

    assert len(builder.prs.slides) == 2
    assert any(sh.name == "node:rel_node" for sh in builder.prs.slides[0].shapes)
    assert any(sh.name == "node:inline_n1" for sh in builder.prs.slides[1].shapes)


def test_build_diagram_v2_slide_px_wide_canvas_fits_horizontally_and_placeholder_clears_footer():
    """Wide 1600x900 px specs fit inside 13.333\" width and 3-line header placeholder clears 7.05\" footer."""
    prs = Presentation()
    prs.slide_width = int(13.333 * EMU_PER_INCH)
    prs.slide_height = int(7.5 * EMU_PER_INCH)
    theme = get_theme("metrodata")

    wide_px_spec = {
        "id": "wide_1600x900",
        "canvas": {"width": 1600.0, "height": 900.0, "unit": "px"},
        "containers": [
            {"id": "c1", "label": "LEFT", "x": 60.0, "y": 140.0, "w": 720.0, "h": 680.0},
            {"id": "c2", "label": "RIGHT", "x": 860.0, "y": 140.0, "w": 680.0, "h": 680.0},
        ],
        "nodes": [
            {"id": "n1", "container_id": "c1", "title": "Ingest", "x": 120.0, "y": 240.0, "w": 240.0, "h": 120.0},
            {"id": "n2", "container_id": "c2", "title": "Serve", "x": 1200.0, "y": 240.0, "w": 240.0, "h": 120.0},
        ],
    }
    slide1 = build_diagram_v2_slide(
        prs,
        theme,
        spec_dict=wide_px_spec,
        action_title="Wide PX Spec Scales Horizontally & Vertically",
    )
    diag_shapes = [sh for sh in slide1.shapes if (sh.name or "").startswith(("container:", "node:"))]
    assert diag_shapes
    assert max((sh.left + sh.width) / EMU_PER_INCH for sh in diag_shapes) <= 13.333
    assert max((sh.top + sh.height) / EMU_PER_INCH for sh in diag_shapes) <= 6.95

    # Missing spec placeholder with 3-line wrapped header must clear 7.05" footer divider
    slide2 = build_diagram_v2_slide(
        prs,
        theme,
        spec_path="missing/does_not_exist.yaml",
        spec_dict=None,
        tracker="DEEP DIVE",
        action_title=(
            "This Extremely Long Three-Line Wrapped Consulting Headline Pushes Header Bottom "
            "Far Below Normal Single-Line Position So Diagnostic Card Must Clamp Its Height"
        ),
        subtitle="Supporting wrapped subtitle line",
    )
    placeholder = next(
        sh for sh in slide2.shapes
        if getattr(sh, "has_text_frame", False) and "Missing Diagram V2 Specification" in sh.text_frame.text
    )
    assert (placeholder.top + placeholder.height) / EMU_PER_INCH <= 6.95


def test_pitch_deck_builder_preserves_top_level_px_canvas_and_header(tmp_path: Path):
    """Top-level inline diagram_v2 slides preserve canvas and header rather than resetting unit to inches."""
    deck_yaml = tmp_path / "px_deck.yaml"
    deck_yaml.write_text(
        """
theme: metrodata
metadata:
  client_name: Example Corp
slides:
  - archetype: diagram_v2
    title: Top-Level PX Canvas Slide
    canvas:
      width: 1200
      height: 675
      unit: px
    nodes:
      - id: px_n1
        title: Pixel Node
        x: 90
        y: 180
        w: 240
        h: 120
""",
        encoding="utf-8",
    )
    builder = PitchDeckBuilder.from_yaml(deck_yaml)
    builder.build_all()
    node_sh = next(sh for sh in builder.prs.slides[0].shapes if sh.name == "node:px_n1")
    assert node_sh.width / EMU_PER_INCH < 4.0
    assert (node_sh.left + node_sh.width) / EMU_PER_INCH <= 13.333
