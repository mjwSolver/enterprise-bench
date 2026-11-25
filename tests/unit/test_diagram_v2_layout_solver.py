"""
Unit Tests: Diagram Engine V2 Layout Solver & Models Edge-Case Hardening
========================================================================
Covers:
1. Reservation of explicit container bounds when placing auto_containers (horizontal, vertical, grid).
2. Reservation of container bounds when placing uncontained auto-nodes.
3. Subtraction of pinned c.w / c.h / n.w from available space without canvas/container overflow.
4. Unit normalization for canvas.unit == "px" (and "pt") across solver and ContainerSpec alignment.
5. Safe resolve_node_fonts when node.w is None and clean handling of box="auto" / invalid box lengths.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.ppt_engine.diagram_v2.auditor import Tier1GeometricLinter
from src.ppt_engine.diagram_v2.layout_solver import solve_diagram_layout
from src.ppt_engine.diagram_v2.models import (
    CanvasConfig,
    ContainerSpec,
    DiagramSpec,
    FlowSpec,
    HeaderConfig,
    NodeSpec,
    classify_geometric_tier,
    resolve_node_fonts,
)


def _assert_no_peer_overlap(containers: list[ContainerSpec]) -> None:
    for i, c1 in enumerate(containers):
        for c2 in containers[i + 1 :]:
            ox = max(0.0, min(c1.x + c1.w, c2.x + c2.w) - max(c1.x, c2.x))
            oy = max(0.0, min(c1.y + c1.h, c2.y + c2.h) - max(c1.y, c2.y))
            assert not (ox > 0.01 and oy > 0.01), (
                f"Containers '{c1.id}' ({c1.x},{c1.y},{c1.w},{c1.h}) and "
                f"'{c2.id}' ({c2.x},{c2.y},{c2.w},{c2.h}) overlap by {ox:.3f}x{oy:.3f}"
            )


def test_mixed_explicit_and_auto_containers_horizontal_no_overlap():
    """Explicit left/middle containers must reserve bounds so auto_containers never overlap them."""
    spec = DiagramSpec(
        id="mixed_horiz",
        layout="horizontal",
        containers=[
            ContainerSpec(id="c_explicit", label="EXPLICIT", x=0.45, y=1.35, w=3.20, h=5.75),
            ContainerSpec(id="c_auto_1", label="AUTO 1"),
            ContainerSpec(id="c_auto_2", label="AUTO 2"),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="c_explicit", title="Source"),
            NodeSpec(id="n2", container_id="c_auto_1", title="Ingest"),
            NodeSpec(id="n3", container_id="c_auto_2", title="Serve"),
        ],
    )
    _assert_no_peer_overlap(spec.containers)
    for c in spec.containers:
        assert c.x >= 0.44
        assert c.x + c.w <= 13.333 - 0.44
    collisions = Tier1GeometricLinter(spec).check_peer_container_collisions()
    assert collisions == []


def test_mixed_explicit_middle_container_splits_free_bands():
    """An explicit container in the center splits free space into left and right bands."""
    spec = DiagramSpec(
        id="mixed_mid",
        layout="horizontal",
        containers=[
            ContainerSpec(id="c_mid", label="MIDDLE", x=5.20, y=1.35, w=2.80, h=5.75),
            ContainerSpec(id="c_left", label="LEFT"),
            ContainerSpec(id="c_right", label="RIGHT"),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="c_mid", title="Center"),
            NodeSpec(id="n2", container_id="c_left", title="Left"),
            NodeSpec(id="n3", container_id="c_right", title="Right"),
        ],
    )
    _assert_no_peer_overlap(spec.containers)
    assert Tier1GeometricLinter(spec).check_peer_container_collisions() == []


def test_mixed_explicit_and_auto_containers_vertical_and_grid():
    """Vertical and grid auto_containers must avoid explicit container bounding boxes."""
    for axis in ("vertical", "grid"):
        spec = DiagramSpec(
            id=f"mixed_{axis}",
            layout=axis,
            containers=[
                ContainerSpec(id="c_fixed", label="FIXED", x=0.45, y=1.35, w=12.40, h=2.00),
                ContainerSpec(id="c_auto_a", label="AUTO A"),
                ContainerSpec(id="c_auto_b", label="AUTO B"),
            ],
            nodes=[
                NodeSpec(id="n1", container_id="c_fixed", title="Top"),
                NodeSpec(id="n2", container_id="c_auto_a", title="Mid"),
                NodeSpec(id="n3", container_id="c_auto_b", title="Bot"),
            ],
        )
        _assert_no_peer_overlap(spec.containers)
        for c in spec.containers:
            assert c.y >= 1.34
            assert c.y + c.h <= 7.50 - 0.34


def test_partially_sized_pinned_width_subtracts_from_avail_w():
    """Pinned c.w (e.g. 2.0 and 8.0) must be subtracted from avail_w so flex peers do not overflow."""
    spec = DiagramSpec(
        id="pinned_w",
        layout="horizontal",
        containers=[
            ContainerSpec(id="c_small", label="SMALL", w=2.0),
            ContainerSpec(id="c_big", label="BIG", w=8.0),
            ContainerSpec(id="c_flex", label="FLEX"),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="c_small", title="A"),
            NodeSpec(id="n2", container_id="c_big", title="B"),
            NodeSpec(id="n3", container_id="c_flex", title="C"),
        ],
    )
    by_id = {c.id: c for c in spec.containers}
    assert by_id["c_small"].w == pytest.approx(2.0, abs=0.01)
    assert by_id["c_big"].w == pytest.approx(8.0, abs=0.01)
    _assert_no_peer_overlap(spec.containers)
    for c in spec.containers:
        assert c.x + c.w <= 13.333 - 0.45 + 0.01


def test_partially_sized_pinned_height_vertical_no_overflow():
    """Pinned c.h in vertical layout must be subtracted from avail_h without bottom overflow."""
    spec = DiagramSpec(
        id="pinned_h",
        layout="vertical",
        containers=[
            ContainerSpec(id="c_top", label="TOP", h=2.80),
            ContainerSpec(id="c_bot", label="BOT"),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="c_top", title="A"),
            NodeSpec(id="n2", container_id="c_bot", title="B"),
        ],
    )
    by_id = {c.id: c for c in spec.containers}
    assert by_id["c_top"].h == pytest.approx(2.80, abs=0.01)
    _assert_no_peer_overlap(spec.containers)
    for c in spec.containers:
        assert c.y + c.h <= 7.50 - 0.35 + 0.01


def test_pack_children_pinned_node_dimensions_no_container_overflow():
    """Pinned n.w in horizontal child packing and pinned n.h in vertical must not overflow container."""
    spec_h = DiagramSpec(
        id="child_pinned_h",
        containers=[
            ContainerSpec(
                id="c1",
                label="HORIZ",
                x=0.45,
                y=1.35,
                w=7.00,
                h=3.00,
                layout="horizontal",
            ),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="c1", title="Pinned", w=3.50),
            NodeSpec(id="n2", container_id="c1", title="Flex A"),
            NodeSpec(id="n3", container_id="c1", title="Flex B"),
        ],
    )
    c1 = spec_h.containers[0]
    for n in spec_h.nodes:
        assert n.x >= c1.x
        assert n.x + n.w <= c1.x + c1.w + 0.01
    assert spec_h.nodes[0].w == pytest.approx(3.50, abs=0.01)

    spec_v = DiagramSpec(
        id="child_pinned_v",
        containers=[
            ContainerSpec(
                id="c2",
                label="VERT",
                x=0.45,
                y=1.35,
                w=3.00,
                h=4.00,
                layout="vertical",
            ),
        ],
        nodes=[
            NodeSpec(id="v1", container_id="c2", title="Pinned H", h=1.20),
            NodeSpec(id="v2", container_id="c2", title="Flex 1"),
            NodeSpec(id="v3", container_id="c2", title="Flex 2"),
            NodeSpec(id="v4", container_id="c2", title="Flex 3"),
        ],
    )
    c2 = spec_v.containers[0]
    for n in spec_v.nodes:
        assert n.y + n.h <= c2.y + c2.h + 0.01


def test_uncontained_auto_nodes_avoid_containers():
    """Uncontained auto-nodes (Step 5) must reserve explicit/auto container bounding boxes."""
    spec = DiagramSpec(
        id="uncontained_reserve",
        layout="horizontal",
        containers=[
            ContainerSpec(id="c_left", label="LEFT ZONE", x=0.45, y=1.35, w=5.00, h=5.75),
        ],
        nodes=[
            NodeSpec(id="n_in", container_id="c_left", title="Inside"),
            NodeSpec(id="n_free_1", title="External A"),
            NodeSpec(id="n_free_2", title="External B"),
        ],
        flows=[FlowSpec(source="n_free_1", target="n_free_2")],
    )
    c_box = spec.containers[0]
    for n in spec.nodes:
        if n.container_id is None:
            ox = max(0.0, min(n.x + n.w, c_box.x + c_box.w) - max(n.x, c_box.x))
            oy = max(0.0, min(n.y + n.h, c_box.y + c_box.h) - max(n.y, c_box.y))
            assert not (ox > 0.01 and oy > 0.01), f"Uncontained node '{n.id}' overlaps container '{c_box.id}'"


def test_px_unit_auto_layout_and_container_alignment():
    """canvas.unit == 'px' must normalize to inches inside solver and emit pixel coordinates."""
    spec = DiagramSpec(
        id="px_diagram",
        layout="horizontal",
        canvas=CanvasConfig(width=1200.0, height=675.0, unit="px"),
        header=HeaderConfig(show=True),
        containers=[
            ContainerSpec(id="c_px_1", label="INGEST", w=360.0),
            ContainerSpec(id="c_px_2", label="SERVE"),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="c_px_1", title="API Gateway", w=220.0),
            NodeSpec(id="n2", container_id="c_px_2", title="Analytics DB", shape="cylinder"),
        ],
        flows=[FlowSpec(source="n1", target="n2", label="HTTPS")],
    )
    for c in spec.containers:
        assert c.x >= 35.0
        assert c.y >= 115.0
        assert c.w >= 180.0
        assert c.h >= 200.0
        assert c.x + c.w <= 1200.0 - 35.0
    for n in spec.nodes:
        assert n.x >= 40.0
        assert n.w >= 100.0
        assert n.h >= 50.0

    # Alignment in px must normalize >25.0 by /90.0 (360px=4in -> left, h>=360px -> bottom)
    c_px = spec.containers[0]
    assert c_px.resolved_align() == "left"
    assert c_px.resolved_vertical_align() == "bottom"

    crit = [i for i in Tier1GeometricLinter(spec).lint() if i.severity == "CRITICAL"]
    assert crit == [], f"Unexpected critical issues in px auto-layout: {crit}"


def test_resolve_node_fonts_none_width_and_box_auto():
    """resolve_node_fonts handles node.w=None without TypeError; box='auto' cleans cleanly."""
    node = NodeSpec(id="n_none_w", title="Hi", box="auto")
    assert node.box is None
    assert "box" not in node.model_dump(exclude_none=True)

    t_pt, s_pt, sp = resolve_node_fonts(node)
    assert t_pt >= 9.5
    assert s_pt >= 8.0
    assert sp >= 2.0

    c_auto = ContainerSpec(id="c_auto", label="Auto Box", box="auto")
    assert c_auto.box is None
    assert "box" not in c_auto.model_dump(exclude_none=True)

    with pytest.raises(ValidationError):
        NodeSpec(id="bad_box", title="Bad", box=[1.0, 2.0, 3.0])


def test_auto_containers_with_pinned_x_and_partial_height_no_overlap_or_overflow():
    """Pinned-x partial containers and trailing flex containers never overlap or exceed usable right edge."""
    # Case A: auto container declared before pinned-x container with h=None
    spec_a = DiagramSpec(
        id="pin_x_partial_h",
        layout="horizontal",
        containers=[
            ContainerSpec(id="c_auto_before", label="AUTO BEFORE"),
            ContainerSpec(id="c_pin_x", label="PIN X", x=0.5, y=1.35, w=4.0),
        ],
        nodes=[
            NodeSpec(id="na", container_id="c_auto_before", title="Auto"),
            NodeSpec(id="np", container_id="c_pin_x", title="Pinned"),
        ],
    )
    _assert_no_peer_overlap(spec_a.containers)
    for c in spec_a.containers:
        assert c.x + c.w <= 12.89

    # Case B: pinned-w first + pinned-x second
    spec_b = DiagramSpec(
        id="pin_w_then_pin_x",
        layout="horizontal",
        containers=[
            ContainerSpec(id="pin_w_first", label="PIN W", w=2.5),
            ContainerSpec(id="pin_x_only", label="PIN X", x=0.6),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="pin_w_first", title="W"),
            NodeSpec(id="n2", container_id="pin_x_only", title="X"),
        ],
    )
    _assert_no_peer_overlap(spec_b.containers)
    for c in spec_b.containers:
        assert c.x + c.w <= 12.89

    # Case C: pinned-x + trailing flex (rem_pinned_after == 0)
    spec_c = DiagramSpec(
        id="pin_x_trailing_flex",
        layout="horizontal",
        containers=[
            ContainerSpec(id="c1", label="C1", x=6.0),
            ContainerSpec(id="c2", label="C2"),
        ],
        nodes=[
            NodeSpec(id="n1", container_id="c1", title="One"),
            NodeSpec(id="n2", container_id="c2", title="Two"),
        ],
    )
    _assert_no_peer_overlap(spec_c.containers)
    for c in spec_c.containers:
        assert c.x >= 0.44
        assert c.x + c.w <= 12.89


def test_tight_explicit_container_and_uncontained_obstacles_no_overlap_and_grid_clamped():
    """Tight explicit obstacles never trigger blind usable_rect fallback, reserve uncontained nodes, and clamp grid."""
    # Case A: large explicit container + squeezed auto container + uncontained node
    spec_squeeze = DiagramSpec(
        id="tight_squeeze",
        layout="horizontal",
        containers=[
            ContainerSpec(id="big_exp", label="BIG", x=0.45, y=1.35, w=11.5, h=5.8),
            ContainerSpec(id="auto_squeeze", label="SQUEEZE"),
        ],
        nodes=[
            NodeSpec(id="nb", container_id="big_exp", title="Big"),
            NodeSpec(id="ns", container_id="auto_squeeze", title="Sq"),
            NodeSpec(id="un_sq", title="Uncontained"),
        ],
    )
    _assert_no_peer_overlap(spec_squeeze.containers)
    big_c = next(c for c in spec_squeeze.containers if c.id == "big_exp")
    un_sq = next(n for n in spec_squeeze.nodes if n.id == "un_sq")
    ox = max(0.0, min(un_sq.x + un_sq.w, big_c.x + big_c.w) - max(un_sq.x, big_c.x))
    oy = max(0.0, min(un_sq.y + un_sq.h, big_c.y + big_c.h) - max(un_sq.y, big_c.y))
    assert not (ox > 0.01 and oy > 0.01), "Uncontained node overlapped big_exp"

    # Case B: explicit uncontained node must be reserved by auto containers
    spec_un_obs = DiagramSpec(
        id="explicit_uncontained_obstacle",
        layout="horizontal",
        containers=[
            ContainerSpec(id="exp_left", label="LEFT", x=0.45, y=1.35, w=3.0, h=5.8),
            ContainerSpec(id="auto_1", label="AUTO 1"),
        ],
        nodes=[
            NodeSpec(id="nl", container_id="exp_left", title="Left"),
            NodeSpec(id="na", container_id="auto_1", title="Auto"),
            NodeSpec(id="un_exp", title="Pinned External", x=9.0, y=2.0, w=2.0, h=1.2),
        ],
    )
    a1 = next(c for c in spec_un_obs.containers if c.id == "auto_1")
    un_exp = next(n for n in spec_un_obs.nodes if n.id == "un_exp")
    ox2 = max(0.0, min(a1.x + a1.w, un_exp.x + un_exp.w) - max(a1.x, un_exp.x))
    oy2 = max(0.0, min(a1.y + a1.h, un_exp.y + un_exp.h) - max(a1.y, un_exp.y))
    assert not (ox2 > 0.01 and oy2 > 0.01), "auto_1 overlapped explicit uncontained node"

    # Case C: narrow grid band must clamp cell widths inside canvas right edge
    spec_grid = DiagramSpec(
        id="narrow_grid",
        layout="grid",
        containers=[
            ContainerSpec(id="exp_left", label="LEFT", x=0.45, y=1.35, w=9.5, h=5.8),
            ContainerSpec(id="g1", label="G1"),
            ContainerSpec(id="g2", label="G2"),
            ContainerSpec(id="g3", label="G3"),
            ContainerSpec(id="g4", label="G4"),
        ],
        nodes=[
            NodeSpec(id="n0", container_id="exp_left", title="Big"),
            NodeSpec(id="n1", container_id="g1", title="1"),
            NodeSpec(id="n2", container_id="g2", title="2"),
            NodeSpec(id="n3", container_id="g3", title="3"),
            NodeSpec(id="n4", container_id="g4", title="4"),
        ],
    )
    _assert_no_peer_overlap(spec_grid.containers)
    for c in spec_grid.containers:
        assert c.x + c.w <= 13.333 + 0.01
        assert c.y + c.h <= 7.50 + 0.01


def test_pack_children_pinned_and_tight_no_container_overflow():
    """Tight vertical children and pinned-x horizontal children stay strictly inside container bounds."""
    spec_v = DiagramSpec(
        id="tight_v_children",
        containers=[
            ContainerSpec(id="cv", label="VERT", x=0.45, y=1.35, w=3.5, h=3.5, layout="vertical"),
        ],
        nodes=[
            NodeSpec(id="v1", container_id="cv", title="Tall", h=2.5),
            NodeSpec(id="v2", container_id="cv", title="Small"),
        ],
    )
    cv = spec_v.containers[0]
    for n in spec_v.nodes:
        assert n.y + n.h <= cv.y + cv.h + 0.01

    spec_h = DiagramSpec(
        id="pinned_x_h_children",
        containers=[
            ContainerSpec(id="ch", label="HORIZ", x=4.5, y=1.35, w=4.0, h=3.5, layout="horizontal"),
        ],
        nodes=[
            NodeSpec(id="h1", container_id="ch", title="Right Pinned", x=7.5, w=1.0),
            NodeSpec(id="h2", container_id="ch", title="Auto Left"),
        ],
    )
    ch = spec_h.containers[0]
    h1, h2 = spec_h.nodes
    assert h2.x >= ch.x
    assert h2.x + h2.w <= ch.x + ch.w + 0.01
    ox = max(0.0, min(h1.x + h1.w, h2.x + h2.w) - max(h1.x, h2.x))
    assert ox <= 0.01


def test_mixed_unit_heuristic_per_axis_normalization():
    """Per-axis px/in normalization never divides inch defaults/banners by 90.0."""
    assert NodeSpec(id="n_px_w", title="Test PX W", w=180.0, h=None).resolved_title_pt() == 12.0
    assert resolve_node_fonts(NodeSpec(id="n_px_h", title="Test PX H", w=None, h=180.0, elastic_text=False), w_in=1.5) == (12.0, 9.0, 2.0)
    t_pt, s_pt, _ = resolve_node_fonts(NodeSpec(id="n_px_h_el", title="Test PX H", w=None, h=180.0), w_in=1.5)
    assert t_pt >= 12.0 and s_pt >= 9.0
    assert ContainerSpec(id="c_large", label="Wide 30in", w=30.0, h=3.0).resolved_align() == "left"
    assert ContainerSpec(id="c_px_small", label="PX", w=150.0, h=270.0).resolved_align() == "center"
    assert ContainerSpec(id="c_px_tall", label="PX Tall", w=150.0, h=360.0).resolved_vertical_align() == "bottom"
    assert classify_geometric_tier(180.0, 1.25) == "Tier A"
    assert classify_geometric_tier(30.0, 2.0) == "Tier A"
