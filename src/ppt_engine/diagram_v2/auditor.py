"""
Diagram Engine V2 - Tier 1 Geometric Collision & Clearance Linter
==================================================================
Deterministic, coordinate-level verification engine that codifies the geometric
rules and layout tolerances learned from the Milestone 33 post-mortem:

1. NODE_COLLISION: Direct bounding box overlap or insufficient gutter between entity cards.
2. CONTAINER_BADGE_OCCLUSION: Container tag badges (e.g. 'AWS CLOUD') covered by child nodes.
3. CONTAINER_LABEL_OCCLUSION: Container header label bands intruded upon by entity cards.
4. BOUNDARY_INTERSECTION: Label pills, badges, or nodes colliding with container border edges.
5. ARROW_SWALLOWED: Flow label pills smothering arrow shafts or occluding arrowheads.
6. CONNECTOR_SPAN_INSUFFICIENT: Inter-node connector spans too compact for badge text (<120-140px).
7. CEILING_COLLISION: Flow return loops or nodes routed along canvas ceiling (y < 25px).
8. PARALLEL_FLOW_CLUSTERING: Parallel or bidirectional connectors running too close (<35px).
9. SHAPE_PROPORTION_OVERSIZED: Database cylinders exceeding width threshold (>185px, e.g. 260px defect).
10. FLOW_OBSTACLE_PENETRATION: Connector route lines cutting through unrelated entity cards.
11. TEXT_OVERFLOW: Card text content exceeding available container height budget.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Sequence, Set, Tuple

from src.ppt_engine.diagram_v2.models import (
    DiagramSpec,
    ContainerSpec,
    NodeSpec,
    FlowSpec,
    BadgeSpec,
    BulletListSpec,
)
from src.ppt_engine.diagram_v2.geometry import GeometryNormalizer, Box, Point

logger = logging.getLogger(__name__)


@dataclass
class AuditIssue:
    """Represents a discrete geometric collision, clearance, or layout violation."""
    severity: Literal["CRITICAL", "WARNING", "INFO"]
    category: str
    element_id: str
    description: str
    suggested_fix: str
    coords: Optional[Tuple[float, float, float, float]] = None  # (x, y, w, h) in pixels

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "element_id": self.element_id,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "coords": self.coords,
        }

    def format_line(self) -> str:
        color = "red" if self.severity == "CRITICAL" else ("yellow" if self.severity == "WARNING" else "cyan")
        return f"[{self.severity}] ({self.category}) on '{self.element_id}': {self.description} -> Fix: {self.suggested_fix}"


def _segment_intersects_box(p1: Point, p2: Point, box: Box, margin: float = 4.0) -> bool:
    """
    Checks if a 2D line segment between p1 and p2 penetrates an axis-aligned box
    with an inward margin tolerance (ignores line endpoints touching the boundary).
    """
    bx1, by1 = box.x + margin, box.y + margin
    bx2, by2 = box.x2 - margin, box.y2 - margin
    if bx1 >= bx2 or by1 >= by2:
        return False

    x1, y1 = p1
    x2, y2 = p2

    # Check horizontal segment
    if abs(y1 - y2) < 2.0:
        y = (y1 + y2) / 2.0
        if by1 <= y <= by2:
            seg_min_x, seg_max_x = min(x1, x2), max(x1, x2)
            ox = max(0.0, min(seg_max_x, bx2) - max(seg_min_x, bx1))
            return ox > 8.0
        return False

    # Check vertical segment
    if abs(x1 - x2) < 2.0:
        x = (x1 + x2) / 2.0
        if bx1 <= x <= bx2:
            seg_min_y, seg_max_y = min(y1, y2), max(y1, y2)
            oy = max(0.0, min(seg_max_y, by2) - max(seg_min_y, by1))
            return oy > 8.0
        return False

    # Parametric Liang-Barsky test for arbitrary diagonal lines
    dx = x2 - x1
    dy = y2 - y1
    p = [-dx, dx, -dy, dy]
    q = [x1 - bx1, bx2 - x1, y1 - by1, by2 - y1]

    u1 = 0.0
    u2 = 1.0

    for i in range(4):
        if abs(p[i]) < 1e-6:
            if q[i] < 0:
                return False
        else:
            t = q[i] / p[i]
            if p[i] < 0:
                if t > u1:
                    u1 = t
            else:
                if t < u2:
                    u2 = t
            if u1 > u2:
                return False

    return (u2 - u1) > 0.05


class Tier1GeometricLinter:
    """
    Deterministic Tier 1 spatial geometry, clearance, and collision linter for DiagramSpec.
    Codifies all physical tolerances and architectural remediations from Milestone 33.
    """

    def __init__(self, spec: DiagramSpec) -> None:
        self.spec = spec
        self.norm = GeometryNormalizer(
            canvas_width=spec.canvas.width,
            canvas_height=spec.canvas.height,
            canvas_unit=spec.canvas.unit,
        )
        self.node_boxes: Dict[str, Box] = {}
        self.container_boxes: Dict[str, Box] = {}
        self.badge_boxes: Dict[str, Box] = {}

        # Resolve all elements in uniform isotropic pixel space
        for c in spec.containers:
            self.container_boxes[c.id] = self.norm.to_pixels(c.x, c.y, c.w, c.h)

        for n in spec.nodes:
            nh = n.h if n.h is not None else (1.25 if spec.canvas.unit == "in" else 100.0)
            self.node_boxes[n.id] = self.norm.to_pixels(n.x, n.y, n.w, nh)

        for i, b in enumerate(spec.badges):
            bid = b.id or f"badge_{i}"
            self.badge_boxes[bid] = self.norm.to_pixels(b.x, b.y, b.w, b.h)

        # Slide canvas bounds in uniform pixels
        self.canvas_box = Box(
            0.0,
            0.0,
            self.norm.scale_to_px_x * spec.canvas.width if spec.canvas.unit == "in" else spec.canvas.width,
            self.norm.scale_to_px_y * spec.canvas.height if spec.canvas.unit == "in" else spec.canvas.height,
        )

    def lint(self) -> List[AuditIssue]:
        """Runs the complete suite of deterministic Tier 1 geometric linting checks."""
        issues: List[AuditIssue] = []
        issues.extend(self.check_node_collisions())
        issues.extend(self.check_container_badge_occlusion())
        issues.extend(self.check_container_label_occlusion())
        issues.extend(self.check_boundary_intersections())
        issues.extend(self.check_arrow_swallowing_and_crowding())
        issues.extend(self.check_connector_span_clearance())
        issues.extend(self.check_ceiling_and_header_clearance())
        issues.extend(self.check_parallel_flow_clustering())
        issues.extend(self.check_shape_proportions_and_database_sizing())
        issues.extend(self.check_flow_obstacle_penetration())
        issues.extend(self.check_node_text_overflow())
        return issues

    # Alias for backward compatibility
    def audit(self) -> List[AuditIssue]:
        return self.lint()

    # =========================================================================
    # Rule 1: Node-on-Node Collisions & Insufficient Gutter
    # =========================================================================
    def check_node_collisions(self) -> List[AuditIssue]:
        """Detects physical intersection or insufficient gutter between entity cards."""
        issues: List[AuditIssue] = []
        items = list(self.node_boxes.items())

        for i, (id1, b1) in enumerate(items):
            for id2, b2 in items[i + 1:]:
                ox = max(0.0, min(b1.x2, b2.x2) - max(b1.x, b2.x))
                oy = max(0.0, min(b1.y2, b2.y2) - max(b1.y, b2.y))

                if ox > 1.0 and oy > 1.0:
                    issues.append(AuditIssue(
                        severity="CRITICAL",
                        category="NODE_COLLISION",
                        element_id=f"{id1}_vs_{id2}",
                        description=f"Nodes '{id1}' and '{id2}' physically overlap by {ox:.1f}px x {oy:.1f}px.",
                        suggested_fix=f"Adjust coordinates to maintain at least 18px (0.20in) separation between '{id1}' and '{id2}'.",
                        coords=(min(b1.x, b2.x), min(b1.y, b2.y), max(b1.x2, b2.x2) - min(b1.x, b2.x), max(b1.y2, b2.y2) - min(b1.y, b2.y)),
                    ))
                else:
                    # Check if nodes are in close proximity in the same row/column
                    dx = max(0.0, max(b1.x, b2.x) - min(b1.x2, b2.x2))
                    dy = max(0.0, max(b1.y, b2.y) - min(b1.y2, b2.y2))
                    if ox > 10.0 and 0.0 <= dy < 12.0:
                        issues.append(AuditIssue(
                            severity="WARNING",
                            category="INSUFFICIENT_NODE_GUTTER",
                            element_id=f"{id1}_vs_{id2}",
                            description=f"Nodes '{id1}' and '{id2}' are separated vertically by only {dy:.1f}px (gutter < 12px).",
                            suggested_fix="Increase vertical spacing between cards to at least 15px (0.16in).",
                        ))
                    elif oy > 10.0 and 0.0 <= dx < 12.0:
                        issues.append(AuditIssue(
                            severity="WARNING",
                            category="INSUFFICIENT_NODE_GUTTER",
                            element_id=f"{id1}_vs_{id2}",
                            description=f"Nodes '{id1}' and '{id2}' are separated horizontally by only {dx:.1f}px (gutter < 12px).",
                            suggested_fix="Increase horizontal spacing between cards to at least 15px (0.16in).",
                        ))

        return issues

    # =========================================================================
    # Rule 2: Container Tag Badge Occlusion
    # =========================================================================
    def check_container_badge_occlusion(self) -> List[AuditIssue]:
        """Detects when a container's tag badge is blocked or clipped by an entity card."""
        issues: List[AuditIssue] = []

        for c in self.spec.containers:
            c_box = self.container_boxes.get(c.id)
            if not c_box or not c.tag_badge:
                continue

            bw, bh = 98.0, 24.0
            bx = c_box.x2 - bw - 15.0
            by = c_box.y + 12.0 if c.vertical_align == "top" else c_box.y2 - bh - 12.0
            badge_box = Box(bx, by, bw, bh)

            for n in self.spec.nodes:
                n_box = self.node_boxes[n.id]
                ox = max(0.0, min(badge_box.x2, n_box.x2) - max(badge_box.x, n_box.x))
                oy = max(0.0, min(badge_box.y2, n_box.y2) - max(badge_box.y, n_box.y))

                if ox > 2.0 and oy > 2.0:
                    pct = ((ox * oy) / (badge_box.w * badge_box.h)) * 100.0
                    issues.append(AuditIssue(
                        severity="CRITICAL",
                        category="CONTAINER_BADGE_OCCLUSION",
                        element_id=c.id,
                        description=(
                            f"Container '{c.id}' tag badge '{c.tag_badge}' at ({bx:.1f}, {by:.1f}) is blocked by node '{n.id}' "
                            f"with {pct:.0f}% area occlusion."
                        ),
                        suggested_fix=(
                            f"Move container '{c.id}' tag_badge to the top-right (vertical_align='top') or relocate "
                            f"node '{n.id}' away from ({bx:.1f}, {by:.1f})."
                        ),
                        coords=(bx, by, bw, bh),
                    ))

        return issues

    # =========================================================================
    # Rule 3: Container Top Header Label Occlusion
    # =========================================================================
    def check_container_label_occlusion(self) -> List[AuditIssue]:
        """Detects when an entity card invades a container's top header label zone."""
        issues: List[AuditIssue] = []

        for c in self.spec.containers:
            c_box = self.container_boxes.get(c.id)
            if not c_box or not c.label:
                continue

            label_box = Box(c_box.x, c_box.y, c_box.w, 36.0)
            for n in self.spec.nodes:
                n_box = self.node_boxes[n.id]
                ox = max(0.0, min(label_box.x2, n_box.x2) - max(label_box.x, n_box.x))
                oy = max(0.0, min(label_box.y2, n_box.y2) - max(label_box.y, n_box.y))
                if ox > 10.0 and oy > 8.0:
                    issues.append(AuditIssue(
                        severity="WARNING",
                        category="CONTAINER_LABEL_OCCLUSION",
                        element_id=c.id,
                        description=f"Node '{n.id}' intrudes into container '{c.id}' top header label zone by {oy:.1f}px.",
                        suggested_fix=f"Increase container '{c.id}' top margin or lower node '{n.id}' Y position (minimum y={c_box.y + 40:.1f}px).",
                    ))

        return issues

    # =========================================================================
    # Rule 4: Container Boundary Dashed/Solid Line Intersections
    # =========================================================================
    def check_boundary_intersections(self) -> List[AuditIssue]:
        """
        Detects when standalone pills, badges, or node cards uncomfortably straddle
        or intersect container boundary edges without intentional full-span nesting.
        """
        issues: List[AuditIssue] = []
        threshold = 10.0  # pixels

        # Combine nodes and standalone badges
        elements = [(n.id, self.node_boxes[n.id], "node") for n in self.spec.nodes]
        for b_id, b_box in self.badge_boxes.items():
            elements.append((b_id, b_box, "badge"))

        for c in self.spec.containers:
            c_box = self.container_boxes[c.id]
            for elem_id, e_box, elem_type in elements:
                # If node is logically child of container and completely inside, skip
                if c_box.x + threshold < e_box.x and e_box.x2 < c_box.x2 - threshold and \
                   c_box.y + threshold < e_box.y and e_box.y2 < c_box.y2 - threshold:
                    continue

                # Check vertical left edge (x = c_box.x)
                if abs(e_box.x - c_box.x) < threshold or abs(e_box.x2 - c_box.x) < threshold:
                    if c_box.y - threshold <= e_box.cy <= c_box.y2 + threshold:
                        issues.append(AuditIssue(
                            severity="WARNING",
                            category="BOUNDARY_INTERSECTION",
                            element_id=elem_id,
                            description=f"{elem_type.title()} '{elem_id}' intersects the left boundary edge of container '{c.id}'.",
                            suggested_fix=f"Offset '{elem_id}' horizontally by at least 15px away from x={c_box.x:.1f}px.",
                        ))

                # Check vertical right edge (x = c_box.x2)
                if abs(e_box.x - c_box.x2) < threshold or abs(e_box.x2 - c_box.x2) < threshold:
                    if c_box.y - threshold <= e_box.cy <= c_box.y2 + threshold:
                        issues.append(AuditIssue(
                            severity="WARNING",
                            category="BOUNDARY_INTERSECTION",
                            element_id=elem_id,
                            description=f"{elem_type.title()} '{elem_id}' intersects the right boundary edge of container '{c.id}'.",
                            suggested_fix=f"Offset '{elem_id}' horizontally by at least 15px away from x={c_box.x2:.1f}px.",
                        ))

        return issues

    # =========================================================================
    # Rule 5: Arrow Swallowing & Arrowhead Occlusion (Milestone 33 Core Finding)
    # =========================================================================
    def check_arrow_swallowing_and_crowding(self) -> List[AuditIssue]:
        """
        Detects when a connector label pill swallows or obscures the flow line,
        leaving little to no visible arrow shaft or covering the destination arrowhead.
        """
        issues: List[AuditIssue] = []

        for f in self.spec.flows:
            if not f.label:
                continue

            pts = self._resolve_flow_points_px(f)
            if len(pts) < 2:
                continue

            segs = list(zip(pts, pts[1:]))
            seg_lengths = [math.hypot(p2[0] - p1[0], p2[1] - p1[1]) for p1, p2 in segs]
            best_idx = max(range(len(seg_lengths)), key=lambda i: seg_lengths[i])
            line_len = seg_lengths[best_idx]
            p1, p2 = segs[best_idx]

            font_size = f.font_pt or 9.0
            approx_text_w = len(f.label) * font_size * 0.55
            pill_w = max(48.0, approx_text_w + 16.0)
            pill_h = 20.0

            is_horizontal = abs(p2[1] - p1[1]) < 4.0
            is_vertical = abs(p2[0] - p1[0]) < 4.0

            # 1. Centered on line without offset
            # Compute realistic pill center based on label_at and label_position
            if f.label_at:
                pill_center = self.norm.point_to_pixels(f.label_at)
            else:
                mid_x = (p1[0] + p2[0]) / 2.0
                mid_y = (p1[1] + p2[1]) / 2.0
                off_h = 14.0
                off_v = 18.0
                if f.label_position == "above":
                    mid_y -= off_h
                elif f.label_position == "below":
                    mid_y += off_h
                elif f.label_position in ("right", "side"):
                    mid_x += off_v
                elif f.label_position == "left":
                    mid_x -= off_v
                pill_center = (mid_x, mid_y)

            pill_box = Box(pill_center[0] - pill_w / 2.0, pill_center[1] - pill_h / 2.0, pill_w, pill_h)

            # 1. Centered on line without offset
            is_centered_on_line = (
                f.label_position in ("center", None, "auto")
                and getattr(f, "label_offset", 0.0) in (None, 0.0)
                and not f.label_at
            )

            if is_horizontal and is_centered_on_line:
                visible_line = line_len - pill_w
                occlusion_ratio = pill_w / line_len if line_len > 0 else 1.0

                if visible_line < 30.0 or occlusion_ratio > 0.65:
                    issues.append(AuditIssue(
                        severity="CRITICAL",
                        category="ARROW_SWALLOWED",
                        element_id=f.id or f.label,
                        description=(
                            f"Flow '{f.id or f.label}' arrow is swallowed by centered label pill. "
                            f"Segment length is {line_len:.1f}px while pill width is {pill_w:.1f}px "
                            f"(pill occupies {occlusion_ratio*100:.0f}% of arrow shaft, leaving only {visible_line:.1f}px visible)."
                        ),
                        suggested_fix=(
                            f"Set label_position='above' or 'below' (offsetting label pill by 14px), or expand connector span "
                            f"between source and target to at least {pill_w + 60:.1f}px."
                        ),
                    ))

            elif is_vertical and is_centered_on_line:
                visible_line = line_len - pill_h
                occlusion_ratio = pill_h / line_len if line_len > 0 else 1.0

                if line_len < pill_w or visible_line < 20.0:
                    issues.append(AuditIssue(
                        severity="CRITICAL",
                        category="ARROW_SWALLOWED",
                        element_id=f.id or f.label,
                        description=(
                            f"Vertical flow '{f.id or f.label}' (length {line_len:.1f}px) is smothered by centered label pill "
                            f"'{f.label}' (width {pill_w:.1f}px, height {pill_h:.1f}px)."
                        ),
                        suggested_fix="Set label_position='side' (offsetting label horizontally) or increase vertical distance between nodes.",
                    ))

            # 2. Check if pill occludes destination arrowhead endpoint
            dest_pt = pts[-1]
            if f.has_arrow and (best_idx == len(segs) - 1):
                arrow_box = Box(dest_pt[0] - 6.0, dest_pt[1] - 6.0, 12.0, 12.0)
                ox_arr = max(0.0, min(pill_box.x2, arrow_box.x2) - max(pill_box.x, arrow_box.x))
                oy_arr = max(0.0, min(pill_box.y2, arrow_box.y2) - max(pill_box.y, arrow_box.y))
                if ox_arr > 0.0 and oy_arr > 0.0:
                    issues.append(AuditIssue(
                        severity="CRITICAL",
                        category="ARROW_HEAD_COVERED",
                        element_id=f.id or f.label,
                        description=f"Label pill '{f.label}' physically overlaps the destination arrowhead at ({dest_pt[0]:.1f}, {dest_pt[1]:.1f}).",
                        suggested_fix="Increase segment clearance or shift label along the segment away from the arrowhead.",
                    ))

            # 3. Check if pill overlaps source or target node cards
            for nid in (f.source, f.target):
                if nid and nid in self.node_boxes:
                    nbox = self.node_boxes[nid]
                    ox = max(0.0, min(pill_box.x2, nbox.x2) - max(pill_box.x, nbox.x))
                    oy = max(0.0, min(pill_box.y2, nbox.y2) - max(pill_box.y, nbox.y))
                    if ox > 4.0 and oy > 4.0:
                        issues.append(AuditIssue(
                            severity="WARNING",
                            category="FLOW_LABEL_NODE_COLLISION",
                            element_id=f.id or f.label,
                            description=f"Flow label pill '{f.label}' physically overlaps node card '{nid}' by {ox:.1f}px x {oy:.1f}px.",
                            suggested_fix=f"Expand spacing between node '{nid}' and adjacent column to at least 140px.",
                        ))

        return issues

    # =========================================================================
    # Rule 6: Insufficient Connector Span (< 120-140px clearance)
    # =========================================================================
    def check_connector_span_clearance(self) -> List[AuditIssue]:
        """
        Codifies the Milestone 33 post-mortem finding where compact inter-column
        spans (60-90px) caused connector text badges to overlap arrow stems,
        arrowheads, and node boundaries. Enforces a 140px-175px clearance standard.
        """
        issues: List[AuditIssue] = []

        for f in self.spec.flows:
            if not f.label or not f.source or not f.target:
                continue
            if f.source not in self.node_boxes or f.target not in self.node_boxes:
                continue

            b_src = self.node_boxes[f.source]
            b_tgt = self.node_boxes[f.target]

            # Horizontal span between right of source and left of target
            if b_tgt.x > b_src.x2:
                gap = b_tgt.x - b_src.x2
                if gap < 110.0:
                    font_size = f.font_pt or 9.0
                    pill_w = len(f.label) * font_size * 0.55 + 16.0
                    issues.append(AuditIssue(
                        severity="CRITICAL" if gap < 90.0 else "WARNING",
                        category="CONNECTOR_SPAN_INSUFFICIENT",
                        element_id=f.id or f.label,
                        description=(
                            f"Horizontal connector gap between '{f.source}' and '{f.target}' is only {gap:.1f}px "
                            f"(violates Milestone 33 standard: minimum 140px-175px clearance for badge '{f.label}' of width {pill_w:.1f}px)."
                        ),
                        suggested_fix=(
                            f"Expand inter-column clearance to at least 140px (1.55in) to ensure unclipped arrowheads "
                            f"and breathing room for status badge."
                        ),
                    ))

        return issues

    # =========================================================================
    # Rule 7: Canvas Ceiling Collision (Milestone 33 Return Loop Defect)
    # =========================================================================
    def check_ceiling_and_header_clearance(self) -> List[AuditIssue]:
        """
        Codifies the Milestone 33 post-mortem finding where the synchronous return
        loop was routed along the canvas ceiling (y <= 20px), colliding with zone titles.
        Enforces a minimum 25px canvas ceiling safety band and gutter placement.
        """
        issues: List[AuditIssue] = []
        min_ceiling_y = 25.0  # pixels

        # Check all flow waypoints
        for f in self.spec.flows:
            pts = self._resolve_flow_points_px(f)
            for idx, pt in enumerate(pts):
                if pt[1] < min_ceiling_y:
                    issues.append(AuditIssue(
                        severity="CRITICAL",
                        category="CEILING_COLLISION",
                        element_id=f.id or f.label or f"flow_{idx}",
                        description=(
                            f"Flow '{f.id or f.label}' waypoint #{idx+1} at ({pt[0]:.1f}, {pt[1]:.1f}) breaches the canvas ceiling "
                            f"safety band (y < {min_ceiling_y:.1f}px). Per Milestone 33 post-mortem, return loops must route "
                            f"through lower inter-track gutters (y=230-240px) rather than the ceiling."
                        ),
                        suggested_fix="Reroute flow waypoints down into the inter-track gutter (e.g. y=230px or lower).",
                    ))

        # Check node positions
        for n in self.spec.nodes:
            nbox = self.node_boxes[n.id]
            if nbox.y < min_ceiling_y:
                issues.append(AuditIssue(
                    severity="CRITICAL",
                    category="CEILING_COLLISION",
                    element_id=n.id,
                    description=f"Node '{n.id}' top edge (y={nbox.y:.1f}px) breaches canvas ceiling safety margin.",
                    suggested_fix=f"Lower node '{n.id}' Y coordinate to at least y={min_ceiling_y + 10:.1f}px.",
                ))

        # Check slide canvas header band intrusion
        if self.spec.header.show:
            header_bottom = 85.0  # px (~0.95in)
            for n in self.spec.nodes:
                nbox = self.node_boxes[n.id]
                if nbox.y < header_bottom:
                    issues.append(AuditIssue(
                        severity="WARNING",
                        category="CANVAS_HEADER_OCCLUSION",
                        element_id=n.id,
                        description=f"Node '{n.id}' at y={nbox.y:.1f}px encroaches into the slide action title header zone.",
                        suggested_fix=f"Lower node '{n.id}' to below y={header_bottom + 10:.1f}px (1.10in).",
                    ))

        return issues

    # =========================================================================
    # Rule 8: Parallel Flow Clustering & Collinear Overlap
    # =========================================================================
    def check_parallel_flow_clustering(self) -> List[AuditIssue]:
        """Detects parallel or counter-directional flows running too close together."""
        issues: List[AuditIssue] = []

        for i, f1 in enumerate(self.spec.flows):
            pts1 = self._resolve_flow_points_px(f1)
            for f2 in self.spec.flows[i + 1:]:
                pts2 = self._resolve_flow_points_px(f2)
                if len(pts1) < 2 or len(pts2) < 2:
                    continue

                for p1_a, p1_b in zip(pts1, pts1[1:]):
                    for p2_a, p2_b in zip(pts2, pts2[1:]):
                        f1_horiz = abs(p1_a[1] - p1_b[1]) < 2.0
                        f2_horiz = abs(p2_a[1] - p2_b[1]) < 2.0

                        if f1_horiz and f2_horiz:
                            x_overlap = max(0.0, min(max(p1_a[0], p1_b[0]), max(p2_a[0], p2_b[0])) - max(min(p1_a[0], p1_b[0]), min(p2_a[0], p2_b[0])))
                            if x_overlap > 30.0:
                                v_gap = abs(p1_a[1] - p2_a[1])
                                if v_gap < 32.0:
                                    issues.append(AuditIssue(
                                        severity="WARNING",
                                        category="PARALLEL_FLOW_CLUSTERING",
                                        element_id=f"{f1.id or 'flow1'}_vs_{f2.id or 'flow2'}",
                                        description=(
                                            f"Parallel flows '{f1.label or f1.id}' and '{f2.label or f2.id}' run only {v_gap:.1f}px apart "
                                            f"with {x_overlap:.1f}px collinear overlap."
                                        ),
                                        suggested_fix="Increase vertical port separation between the two flows to at least 45px (0.50in).",
                                    ))

        return issues

    # =========================================================================
    # Rule 9: Shape Proportions & Database Compression (Milestone 33 Finding)
    # =========================================================================
    def check_shape_proportions_and_database_sizing(self) -> List[AuditIssue]:
        """
        Codifies the Milestone 33 post-mortem finding where database cylinders spanned
        260px in width, crowding column 3 and pushing connectors against right-hand
        margins. Remediated by compressing cylinder geometry from 260px down to 170px.
        """
        issues: List[AuditIssue] = []

        for n in self.spec.nodes:
            nbox = self.node_boxes[n.id]

            # 1. Database cylinder compression check
            if n.is_cylinder or n.shape in ("cylinder", "database"):
                if nbox.w > 185.0:
                    issues.append(AuditIssue(
                        severity="WARNING",
                        category="SHAPE_PROPORTION_OVERSIZED",
                        element_id=n.id,
                        description=(
                            f"Database cylinder '{n.id}' width is {nbox.w:.1f}px, exceeding the recommended "
                            f"170px (1.88in) limit from Milestone 33 post-mortem. Overly wide cylinders crowd "
                            f"adjacent gutters and squeeze connector clearances."
                        ),
                        suggested_fix=f"Compress cylinder width down to 170px (1.88in) per Milestone 33 architectural standard.",
                        coords=(nbox.x, nbox.y, nbox.w, nbox.h),
                    ))

            # 2. Right canvas margin clearance
            canvas_right = self.canvas_box.w
            dist_to_right = canvas_right - nbox.x2
            if dist_to_right < 20.0:
                issues.append(AuditIssue(
                    severity="WARNING",
                    category="MARGIN_ENCROACHMENT",
                    element_id=n.id,
                    description=f"Node '{n.id}' right edge sits only {dist_to_right:.1f}px from the slide right border (minimum 25px required).",
                    suggested_fix=f"Shift node '{n.id}' left or compress width to retain at least 25px canvas margin.",
                ))

        return issues

    # =========================================================================
    # Rule 10: Flow Obstacle Penetration
    # =========================================================================
    def check_flow_obstacle_penetration(self) -> List[AuditIssue]:
        """Detects when a connector flow cuts directly through an unrelated entity card."""
        issues: List[AuditIssue] = []

        for f in self.spec.flows:
            pts = self._resolve_flow_points_px(f)
            if len(pts) < 2:
                continue

            for p1, p2 in zip(pts, pts[1:]):
                for nid, nbox in self.node_boxes.items():
                    if nid == f.source or nid == f.target:
                        continue  # Connected endpoints are expected

                    if _segment_intersects_box(p1, p2, nbox, margin=4.0):
                        issues.append(AuditIssue(
                            severity="CRITICAL",
                            category="FLOW_OBSTACLE_PENETRATION",
                            element_id=f"{f.id or f.label}_vs_{nid}",
                            description=(
                                f"Connector flow '{f.id or f.label}' segment ({p1[0]:.1f}, {p1[1]:.1f}) -> "
                                f"({p2[0]:.1f}, {p2[1]:.1f}) slices through unrelated node card '{nid}'."
                            ),
                            suggested_fix=f"Route connector through gutter channels around node '{nid}' (perimeter clearance >= 18px).",
                        ))

        return issues

    # =========================================================================
    # Rule 11: Text Overflow & Line Capacity Inside Cards
    # =========================================================================
    def check_node_text_overflow(self) -> List[AuditIssue]:
        """Estimates paragraph stack height against node card height budget."""
        issues: List[AuditIssue] = []

        for n in self.spec.nodes:
            nbox = self.node_boxes[n.id]
            title_pt = n.title_pt or 12.0
            sub_pt = 9.0

            # Estimate wrapped lines for title and subtitle
            char_w_title = title_pt * 0.55
            usable_w = max(40.0, nbox.w - 32.0)
            title_chars_per_line = max(10, int(usable_w / char_w_title))

            title_lines = max(1, (len(n.title) + title_chars_per_line - 1) // title_chars_per_line)
            title_h = title_lines * title_pt * 1.25

            sub_h = 0.0
            if n.subtitle:
                char_w_sub = sub_pt * 0.52
                sub_chars = max(12, int(usable_w / char_w_sub))
                sub_lines = max(1, (len(n.subtitle) + sub_chars - 1) // sub_chars)
                sub_h = sub_lines * sub_pt * 1.20 + 4.0

            kicker_h = 16.0 if n.kicker else 0.0
            icon_h = 28.0 if n.icon or n.icon_emoji else 0.0
            if n.icon_layout == "side":
                total_text_h = max(icon_h, kicker_h + title_h + sub_h) + 16.0
            else:
                total_text_h = icon_h + kicker_h + title_h + sub_h + 20.0

            if total_text_h > nbox.h:
                issues.append(AuditIssue(
                    severity="CRITICAL",
                    category="TEXT_OVERFLOW",
                    element_id=n.id,
                    description=(
                        f"Estimated content height ({total_text_h:.1f}px) exceeds card height ({nbox.h:.1f}px) "
                        f"on node '{n.id}'. Content risks crossing card bottom border."
                    ),
                    suggested_fix=f"Increase node '{n.id}' height to at least {total_text_h + 10:.1f}px or shorten subtitle.",
                    coords=(nbox.x, nbox.y, nbox.w, nbox.h),
                ))

        return issues

    # =========================================================================
    # Helpers
    # =========================================================================
    def _resolve_flow_points_px(self, f: FlowSpec) -> List[Point]:
        """Resolves flow waypoints in uniform pixel space."""
        if f.points:
            return [self.norm.point_to_pixels(p) for p in f.points]
        if f.source and f.target and f.source in self.node_boxes and f.target in self.node_boxes:
            b_src = self.node_boxes[f.source]
            b_tgt = self.node_boxes[f.target]
            return GeometryNormalizer.compute_auto_route(b_src, b_tgt, f.curve)
        return []


# Canonical alias preserving existing DiagramAuditor imports
DiagramAuditor = Tier1GeometricLinter
