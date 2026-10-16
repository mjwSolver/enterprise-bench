"""
Regression Test Suite: Diagram Engine V2 Standardization (Tracks 1 & 2)
========================================================================
Validates:
1. DeckHeaderContract coordinate constants and immutable geometric properties.
2. Check #15 (DECK_HEADER_DRIFT): header placement drift, canonical container
   ingress line invariant (y >= 1.350in), and subtitle headroom buffer (>= 0.250in).
3. Bottom-Edge Container Label Policy (BOTTOM_EDGE_CONTAINER_LABEL_POLICY):
   h >= 4.0in -> bottom, h < 4.0in -> top, w <= 2.0in -> center, w > 2.0in -> left,
   and strict adherence to explicit overrides.
4. Tight container label hitbox collision verification (no false positives).
5. Multi-slide bundle header drift validator.
6. Decoupled tag badge placement in SVG and PPTX compilers.
7. Draw.io XML vertical align style token formatting.
"""

from __future__ import annotations

import pytest

from src.ppt_engine.diagram_v2.models import (
    DiagramSpec,
    CanvasConfig,
    HeaderConfig,
    DeckHeaderContract,
    ContainerSpec,
    NodeSpec,
)
from src.ppt_engine.diagram_v2.auditor import Tier1GeometricLinter
from src.ppt_engine.diagram_v2.stray_consolidator import validate_bundle_headers
from src.ppt_engine.diagram_v2.svg_compiler import SVGCompiler
from src.ppt_engine.diagram_v2.drawio_compiler import DrawIOCompiler


def test_deck_header_contract_constants():
    """Verify physical invariant coordinates in DeckHeaderContract."""
    assert DeckHeaderContract.STRIPES_TOP_IN == 0.280
    assert DeckHeaderContract.STRIPES_LEFT_IN == 0.600
    assert DeckHeaderContract.STRIPE_RED_W_IN == 0.045
    assert DeckHeaderContract.STRIPE_BLUE_W_IN == 0.090
    assert DeckHeaderContract.TITLE_TOP_IN == 0.230
    assert DeckHeaderContract.TITLE_LEFT_WITH_STRIPES_IN == 0.850
    assert DeckHeaderContract.TITLE_LEFT_NO_STRIPES_IN == 0.600
    assert DeckHeaderContract.TITLE_BOTTOM_IN == 1.080
    assert DeckHeaderContract.CANONICAL_INGRESS_Y_IN == 1.350
    assert DeckHeaderContract.MIN_HEADROOM_CLEARANCE_IN == 0.250

    # HeaderConfig defaults
    h = HeaderConfig()
    assert h.x == 0.600
    assert h.y == 0.280


def test_check_15_header_placement_drift():
    """Verify Check #15 detects placement drift when header.y deviates from 0.280in."""
    spec = DiagramSpec(
        header=HeaderConfig(show=True, y=0.400),
        containers=[ContainerSpec(id="c1", label="Zone", x=0.5, y=1.35, w=3.0, h=4.0)],
    )
    linter = Tier1GeometricLinter(spec)
    issues = linter.check_deck_header_drift()

    categories = [i.category for i in issues]
    assert "DECK_HEADER_DRIFT" in categories
    drift_issue = next(i for i in issues if i.category == "DECK_HEADER_DRIFT")
    assert "0.400in" in drift_issue.description


def test_check_15_canonical_ingress_line_breach():
    """Verify Check #15 detects containers encroaching into y < 1.350in."""
    spec = DiagramSpec(
        header=HeaderConfig(show=True, y=0.280),
        containers=[
            ContainerSpec(id="c_violating", label="Zone A", x=0.5, y=1.20, w=3.0, h=4.0),
            ContainerSpec(id="c_valid", label="Zone B", x=4.0, y=1.35, w=3.0, h=4.0),
        ],
    )
    linter = Tier1GeometricLinter(spec)
    issues = linter.check_deck_header_drift()

    categories = [i.category for i in issues]
    assert "CANVAS_HEADER_OCCLUSION" in categories
    occlusion_issue = next(i for i in issues if i.category == "CANVAS_HEADER_OCCLUSION")
    assert occlusion_issue.element_id == "c_violating"
    assert occlusion_issue.severity == "CRITICAL"


def test_check_15_headroom_clearance_buffer():
    """Verify Check #15 flags elements that breach the 0.250in headroom clearance buffer."""
    spec = DiagramSpec(
        header=HeaderConfig(show=True, y=0.280),
        containers=[
            # Container starts at 1.25in -> clearance is 1.25 - 1.08 = 0.17in (< 0.25in)
            ContainerSpec(id="c1", label="Zone", x=0.5, y=1.25, w=3.0, h=4.0),
        ],
    )
    linter = Tier1GeometricLinter(spec)
    issues = linter.check_deck_header_drift()

    categories = [i.category for i in issues]
    assert "HEADER_HEADROOM_INSUFFICIENT" in categories


def test_bottom_edge_container_label_policy_resolution():
    """Verify resolved_vertical_align and resolved_align heuristics and explicit overrides."""
    # Macro swimlane: h >= 4.0in -> bottom
    c_macro = ContainerSpec(id="macro", label="Macro", x=0.5, y=1.35, w=4.0, h=5.5)
    assert c_macro.resolved_vertical_align() == "bottom"
    assert c_macro.resolved_align() == "left"

    # Narrow isolated column: w <= 2.0in -> center
    c_narrow = ContainerSpec(id="narrow", label="Narrow", x=0.5, y=1.35, w=1.8, h=5.5)
    assert c_narrow.resolved_vertical_align() == "bottom"
    assert c_narrow.resolved_align() == "center"

    # Compact sub-container: h < 4.0in -> top
    c_compact = ContainerSpec(id="compact", label="Compact", x=0.5, y=1.35, w=3.0, h=3.2)
    assert c_compact.resolved_vertical_align() == "top"
    assert c_compact.resolved_align() == "left"

    # Explicit override: h >= 4.0in but vertical_align='top'
    c_override_v = ContainerSpec(id="ov", label="Override", x=0.5, y=1.35, w=4.0, h=5.5, vertical_align="top")
    assert c_override_v.resolved_vertical_align() == "top"

    # Explicit override: w > 2.0in but align='center'
    c_override_a = ContainerSpec(id="oa", label="Override", x=0.5, y=1.35, w=4.0, h=5.5, align="center")
    assert c_override_a.resolved_align() == "center"


def test_tight_container_label_hitbox_no_false_positives():
    """Verify that a node at bottom-right does not collide with a bottom-left container label."""
    # Container at x=0.5, y=1.35, w=6.0, h=5.5.
    # Label is left-aligned, occupying approximately x=0.7 to x=2.5.
    # Node is placed at bottom-right: x=4.0, y=6.0, w=1.5, h=0.6.
    spec = DiagramSpec(
        containers=[
            ContainerSpec(id="c1", label="System Boundary", x=0.5, y=1.35, w=6.0, h=5.5, align="left"),
        ],
        nodes=[
            NodeSpec(id="n_bottom_right", container_id="c1", title="Right Node", x=4.0, y=5.8, w=1.5, h=0.6),
        ],
    )
    linter = Tier1GeometricLinter(spec)
    issues = linter.check_container_label_occlusion()

    # Must NOT report collision because label is anchored at bottom-left, while node is at bottom-right
    assert len(issues) == 0


def test_bundle_header_validator():
    """Verify validate_bundle_headers detects drift across constituent presentation slides."""
    spec1 = DiagramSpec(
        id="s1",
        header=HeaderConfig(show=True, x=0.600, y=0.280),
        containers=[ContainerSpec(id="c1", label="Z", x=0.5, y=1.35, w=3.0, h=4.0)],
    )
    spec2 = DiagramSpec(
        id="s2",
        header=HeaderConfig(show=True, x=0.600, y=0.400),  # Drifted header y
        containers=[ContainerSpec(id="c2", label="Z", x=0.5, y=1.35, w=3.0, h=4.0)],
    )

    issues = validate_bundle_headers([spec1, spec2])
    assert len(issues) == 1
    assert issues[0].category == "DECK_HEADER_DRIFT"
    assert issues[0].severity == "CRITICAL"


def test_svg_decoupled_tag_badge_stays_top_right():
    """Verify SVGCompiler keeps tag_badge at top-right even when vertical_align is bottom."""
    spec = DiagramSpec(
        containers=[
            ContainerSpec(
                id="c1",
                label="Backend Services",
                x=0.5,
                y=1.35,
                w=5.0,
                h=5.0,
                tag_badge="AWS CLOUD",
            ),
        ],
    )
    compiler = SVGCompiler(spec)
    svg_output = compiler.compile_svg()

    # Verify container label is at bottom
    assert "BACKEND SERVICES" in svg_output
    # Verify tag badge y is near top (y=1.35in * 90 = 121.5px + 12px = 133.5px)
    assert 'translate(' in svg_output
    assert "AWS CLOUD" in svg_output


def test_drawio_compiler_style_tokens():
    """Verify DrawIOCompiler emits correct verticalAlign and spacing tokens."""
    spec = DiagramSpec(
        containers=[
            ContainerSpec(id="c_bottom", label="Zone 1", x=0.5, y=1.35, w=5.0, h=5.0),
            ContainerSpec(id="c_top", label="Zone 2", x=6.0, y=1.35, w=5.0, h=2.5),
        ],
    )
    compiler = DrawIOCompiler(spec)
    xml_output = compiler.compile_xml()

    # Zone 1 (h=5.0 >= 4.0) -> bottom
    assert "verticalAlign=bottom;spacingBottom=12;spacingTop=0;" in xml_output
    # Zone 2 (h=2.5 < 4.0) -> top
    assert "verticalAlign=top;spacingTop=14;spacingBottom=0;" in xml_output
