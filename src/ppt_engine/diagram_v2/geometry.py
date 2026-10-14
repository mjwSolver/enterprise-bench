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


@dataclass(frozen=True)
class Box:
    """Axis-aligned bounding box with proportional and absolute port anchors."""
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
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.unit = canvas_unit.lower().strip()

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
    def resolve_port(box: Box, port_desc: Optional[str]) -> Point:
        """
        Resolves a port string into an exact (x, y) coordinate on the given box.
        Examples:
        - 'left', 'right', 'top', 'bottom'
        - 'right(0.25)', 'left(0.8)'
        - 'right_at(2.50)', 'bottom_at(9.00)'
        """
        if not port_desc:
            return box.right()

        s = port_desc.strip().lower()

        # Check for function-like syntax, e.g. right_at(2.5) or left(0.7)
        m_at = re.match(r"(left|right|top|bottom)_at\s*\(\s*([0-9.]+)\s*\)", s)
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

        m_prop = re.match(r"(left|right|top|bottom)\s*\(\s*([0-9.]+)\s*\)", s)
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

        return box.right()

    @staticmethod
    def compute_auto_route(src: Box, tgt: Box, curve: str = "orthogonal") -> List[Point]:
        """
        Computes a deterministic route between two boxes when no explicit points are provided.
        """
        dx = tgt.cx - src.cx
        dy = tgt.cy - src.cy

        is_horizontal = abs(dx) >= abs(dy)

        if is_horizontal:
            if dx > 0:
                p_start = src.right()
                p_end = tgt.left()
            else:
                p_start = src.left()
                p_end = tgt.right()
        else:
            if dy > 0:
                p_start = src.bottom()
                p_end = tgt.top()
            else:
                p_start = src.top()
                p_end = tgt.bottom()

        if curve == "straight":
            return [p_start, p_end]

        # Orthogonal mid-elbow
        if is_horizontal:
            mx = (p_start[0] + p_end[0]) / 2.0
            return [p_start, (mx, p_start[1]), (mx, p_end[1]), p_end]
        else:
            my = (p_start[1] + p_end[1]) / 2.0
            return [p_start, (p_start[0], my), (p_end[0], my), p_end]
