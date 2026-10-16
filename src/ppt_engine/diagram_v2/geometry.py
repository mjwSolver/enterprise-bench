"""
Diagram Engine V2 - Geometry and Coordinate Normalization Subsystem
===================================================================
Provides coordinate conversion between declarative unit systems (inches vs pixels),
bounding boxes with directional port anchors, and orthogonal flow routing helpers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

Point = Tuple[float, float]

# Precompiled regex patterns for port descriptors and coordinate strings
_PORT_AT_RE = re.compile(r"^(left|right|top|bottom)_at\s*\(\s*([+-]?[0-9]*\.?[0-9]+)\s*\)$")
_PORT_PROP_RE = re.compile(r"^(left|right|top|bottom)\s*\(\s*([+-]?[0-9]*\.?[0-9]+)\s*\)$")
_PORT_COORD_RE = re.compile(r"^\(?\s*([+-]?[0-9]*\.?[0-9]+)\s*,\s*([+-]?[0-9]*\.?[0-9]+)\s*\)?$")


def line_segment_intersects_box(
    p1: Point,
    p2: Point,
    box: Box,
    margin: float = 0.0,
    min_overlap: float = 0.05,
) -> bool:
    """
    Parametric Liang-Barsky line clipping algorithm testing whether segment (p1->p2)
    intersects or cuts through an axis-aligned box with an optional inward/outward margin.

    Returns True if the segment enters the interior of the box with overlap > min_overlap.
    """
    bx1, by1 = box.x + margin, box.y + margin
    bx2, by2 = box.x2 - margin, box.y2 - margin
    if bx1 >= bx2 or by1 >= by2:
        return False

    x1, y1 = p1
    x2, y2 = p2

    # Check horizontal segment
    if abs(y1 - y2) < 1e-4:
        y = (y1 + y2) / 2.0
        if by1 <= y <= by2:
            seg_min_x, seg_max_x = min(x1, x2), max(x1, x2)
            ox = max(0.0, min(seg_max_x, bx2) - max(seg_min_x, bx1))
            return ox > 1e-4
        return False

    # Check vertical segment
    if abs(x1 - x2) < 1e-4:
        x = (x1 + x2) / 2.0
        if bx1 <= x <= bx2:
            seg_min_y, seg_max_y = min(y1, y2), max(y1, y2)
            oy = max(0.0, min(seg_max_y, by2) - max(seg_min_y, by1))
            return oy > 1e-4
        return False

    # Parametric Liang-Barsky test for arbitrary diagonal lines
    dx = x2 - x1
    dy = y2 - y1
    p = [-dx, dx, -dy, dy]
    q = [x1 - bx1, bx2 - x1, y1 - by1, by2 - y1]

    u1 = 0.0
    u2 = 1.0

    for i in range(4):
        if abs(p[i]) < 1e-9:
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

    return (u2 - u1) > min_overlap


@dataclass(frozen=True)
class Box:
    """Axis-aligned bounding box with proportional, absolute port anchors, and collision testing."""
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    # Proportional ports (t in 0..1 along side)
    def left(self, t: float = 0.5) -> Point:
        return (self.x, self.y + self.h * t)

    def right(self, t: float = 0.5) -> Point:
        return (self.x2, self.y + self.h * t)

    def top(self, t: float = 0.5) -> Point:
        return (self.x + self.w * t, self.y)

    def bottom(self, t: float = 0.5) -> Point:
        return (self.x + self.w * t, self.y2)

    # Absolute ports along given coordinate
    def left_at(self, y: float) -> Point:
        return (self.x, y)

    def right_at(self, y: float) -> Point:
        return (self.x2, y)

    def top_at(self, x: float) -> Point:
        return (x, self.y)

    def bottom_at(self, x: float) -> Point:
        return (x, self.y2)

    # Spatial containment & collision tests
    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        """Returns True if point (x, y) is inside the bounding box with optional tolerance."""
        return (self.x - margin <= x <= self.x2 + margin) and (self.y - margin <= y <= self.y2 + margin)

    def contains_point(self, pt: Point, margin: float = 0.0) -> bool:
        """Returns True if Point is inside the bounding box."""
        return self.contains(pt[0], pt[1], margin=margin)

    def intersects_box(self, other: Box, margin: float = 0.0) -> bool:
        """Determines if this bounding box overlaps another box with positive area."""
        ox = max(0.0, min(self.x2, other.x2) - max(self.x, other.x))
        oy = max(0.0, min(self.y2, other.y2) - max(self.y, other.y))
        return ox > margin and oy > margin

    def intersection_box(self, other: Box) -> Optional[Box]:
        """Returns the intersecting sub-box, or None if disjoint."""
        ix1 = max(self.x, other.x)
        iy1 = max(self.y, other.y)
        ix2 = min(self.x2, other.x2)
        iy2 = min(self.y2, other.y2)
        if ix1 < ix2 and iy1 < iy2:
            return Box(x=ix1, y=iy1, w=ix2 - ix1, h=iy2 - iy1)
        return None

    def intersects_segment(
        self,
        p1: Point,
        p2: Point,
        margin: float = 0.0,
        min_overlap: float = 0.05,
    ) -> bool:
        """Tests line segment intersection via Liang-Barsky parametric clipping."""
        return line_segment_intersects_box(p1, p2, self, margin=margin, min_overlap=min_overlap)


class GeometryNormalizer:
    """
    Normalizes coordinates between declared units (inches vs pixels)
    for target renderers (PowerPoint DrawingML in inches vs SVG/Draw.io in pixels).
    """

    DEFAULT_PPT_WIDTH = 13.333
    DEFAULT_PPT_HEIGHT = 7.5
    DEFAULT_PX_WIDTH = 1200.0
    DEFAULT_PX_HEIGHT = 675.0
    PX_PER_INCH = 90.0

    def __init__(
        self,
        canvas_width: float,
        canvas_height: float,
        canvas_unit: str = "in",
    ) -> None:
        # Guard against None, zero, or negative canvas dimensions
        self.canvas_width = max(0.001, float(canvas_width)) if canvas_width else self.DEFAULT_PPT_WIDTH
        self.canvas_height = max(0.001, float(canvas_height)) if canvas_height else self.DEFAULT_PPT_HEIGHT
        self.unit = (canvas_unit or "in").lower().strip()

        # Compute scaling factors to inches (for PPTX) and pixels (for SVG/Draw.io)
        if self.unit == "in":
            self.scale_to_in_x = 1.0
            self.scale_to_in_y = 1.0
            # Isotropic uniform 90 px/in scaling (preserves exact 16:9 aspect ratio)
            self.scale_to_px_x = self.PX_PER_INCH
            self.scale_to_px_y = self.PX_PER_INCH
        else:
            # Unit is px or pt - map pixels to inches using uniform isotropic scaling
            scale_uniform = 1.0 / self.PX_PER_INCH
            self.scale_to_in_x = scale_uniform
            self.scale_to_in_y = scale_uniform
            self.scale_to_px_x = 1.0
            self.scale_to_px_y = 1.0

    def to_inches(self, x: float, y: float, w: float, h: float) -> Box:
        """Converts coordinates to PowerPoint inches."""
        return Box(
            x=round(x * self.scale_to_in_x, 4),
            y=round(y * self.scale_to_in_y, 4),
            w=round(w * self.scale_to_in_x, 4),
            h=round(h * self.scale_to_in_y, 4),
        )

    def to_pixels(self, x: float, y: float, w: float, h: float) -> Box:
        """Converts coordinates to Draw.io / SVG pixels."""
        return Box(
            x=round(x * self.scale_to_px_x, 2),
            y=round(y * self.scale_to_px_y, 2),
            w=round(w * self.scale_to_px_x, 2),
            h=round(h * self.scale_to_px_y, 2),
        )

    def point_to_inches(self, pt: Union[Point, Sequence[float]]) -> Point:
        """Converts a single point to inches."""
        return (round(pt[0] * self.scale_to_in_x, 4), round(pt[1] * self.scale_to_in_y, 4))

    def point_to_pixels(self, pt: Union[Point, Sequence[float]]) -> Point:
        """Converts a single point to pixels."""
        return (round(pt[0] * self.scale_to_px_x, 2), round(pt[1] * self.scale_to_px_y, 2))

    @staticmethod
    def resolve_port(box: Box, port_desc: Optional[Union[str, Sequence[float]]]) -> Point:
        """
        Resolves a port string or coordinate into an exact (x, y) coordinate on the given box.
        Examples:
        - 'left', 'right', 'top', 'bottom', 'center', 'middle'
        - 'right(0.25)', 'left(0.8)'
        - 'right_at(2.50)', 'bottom_at(9.00)'
        - '(2.5, 3.5)', [2.5, 3.5]
        """
        if port_desc is None:
            return box.right()

        # Direct numeric sequence [x, y] or (x, y)
        if isinstance(port_desc, (tuple, list)) and len(port_desc) >= 2:
            return (float(port_desc[0]), float(port_desc[1]))

        s = str(port_desc).strip().lower()
        if not s:
            return box.right()

        # Coordinate string "(x, y)" or "x, y"
        m_coord = _PORT_COORD_RE.match(s)
        if m_coord:
            return (float(m_coord.group(1)), float(m_coord.group(2)))

        # Check for function-like syntax, e.g. right_at(2.5) or left(0.7)
        m_at = _PORT_AT_RE.match(s)
        if m_at:
            side, val_str = m_at.group(1), float(m_at.group(2))
            if side == "left":
                return box.left_at(val_str)
            if side == "right":
                return box.right_at(val_str)
            if side == "top":
                return box.top_at(val_str)
            if side == "bottom":
                return box.bottom_at(val_str)

        m_prop = _PORT_PROP_RE.match(s)
        if m_prop:
            side, t = m_prop.group(1), float(m_prop.group(2))
            if side == "left":
                return box.left(t)
            if side == "right":
                return box.right(t)
            if side == "top":
                return box.top(t)
            if side == "bottom":
                return box.bottom(t)

        if s == "left":
            return box.left()
        if s == "right":
            return box.right()
        if s == "top":
            return box.top()
        if s == "bottom":
            return box.bottom()
        if s in ("center", "middle"):
            return (box.cx, box.cy)

        return box.right()

    @staticmethod
    def compute_auto_route(
        src: Box,
        tgt: Box,
        curve: str = "orthogonal",
        src_port: Optional[Union[str, Sequence[float]]] = None,
        tgt_port: Optional[Union[str, Sequence[float]]] = None,
    ) -> List[Point]:
        """
        Computes a deterministic route between two boxes when no explicit points are provided.
        Respects optional source_port and target_port overrides, and prevents collinear duplicate midpoints.
        """
        if src_port is not None:
            p_start = GeometryNormalizer.resolve_port(src, src_port)
        else:
            p_start = None

        if tgt_port is not None:
            p_end = GeometryNormalizer.resolve_port(tgt, tgt_port)
        else:
            p_end = None

        dx = tgt.cx - src.cx
        dy = tgt.cy - src.cy
        is_horizontal = abs(dx) >= abs(dy)

        if p_start is None or p_end is None:
            if is_horizontal:
                if dx > 0:
                    p_start = p_start or src.right()
                    p_end = p_end or tgt.left()
                else:
                    p_start = p_start or src.left()
                    p_end = p_end or tgt.right()
            else:
                if dy > 0:
                    p_start = p_start or src.bottom()
                    p_end = p_end or tgt.top()
                else:
                    p_start = p_start or src.top()
                    p_end = p_end or tgt.bottom()

        if curve == "straight":
            return [p_start, p_end]

        # Prevent redundant collinear duplicate midpoints
        if is_horizontal and abs(p_start[1] - p_end[1]) < 1e-4:
            return [p_start, p_end]
        if not is_horizontal and abs(p_start[0] - p_end[0]) < 1e-4:
            return [p_start, p_end]

        # Orthogonal mid-elbow
        if is_horizontal:
            mx = (p_start[0] + p_end[0]) / 2.0
            return [p_start, (mx, p_start[1]), (mx, p_end[1]), p_end]
        else:
            my = (p_start[1] + p_end[1]) / 2.0
            return [p_start, (p_start[0], my), (p_end[0], my), p_end]
