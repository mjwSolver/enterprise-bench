"""
Diagram Engine V2 - Declarative Specification Models
=====================================================
Pydantic v2 data models defining the declarative YAML schema for enterprise
diagram topologies, container boundaries, entity nodes, and routed connectors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field, field_validator



@dataclass(frozen=True)
class DeckHeaderContract:
    STRIPES_TOP_IN: float = 0.280
    STRIPES_LEFT_IN: float = 0.600
    STRIPE_RED_W_IN: float = 0.045
    STRIPE_BLUE_W_IN: float = 0.090
    STRIPES_GAP_IN: float = 0.020
    STRIPES_H_IN: float = 0.550
    STRIPES_RATIO: str = "1:2"
    STRIPE_RED_HEX: str = "#E11D48"
    STRIPE_BLUE_HEX: str = "#0284C7"
    TITLE_TOP_IN: float = 0.230
    TITLE_LEFT_WITH_STRIPES_IN: float = 0.850
    TITLE_LEFT_NO_STRIPES_IN: float = 0.600
    TITLE_W_WITH_STRIPES_IN: float = 9.800
    TITLE_W_NO_STRIPES_IN: float = 10.050
    TITLE_H_IN: float = 0.850
    TITLE_BOTTOM_IN: float = 1.080
    TITLE_BOTTOM_PX: float = 103.68
    CANONICAL_INGRESS_Y_IN: float = 1.350
    CANONICAL_INGRESS_Y_PX: float = 129.60
    MIN_HEADROOM_CLEARANCE_IN: float = 0.250
    MIN_HEADROOM_CLEARANCE_PX: float = 24.0
    HEADER_Y_TOLERANCE_IN: float = 0.010
    MAX_HEADER_DELTA_IN: float = 0.005


class CanvasConfig(BaseModel):
    """Diagram canvas geometry, measurement units, and grid background."""
    width: float = 13.333
    height: float = 7.5
    unit: Literal["in", "px", "pt"] = "in"
    background: str = "#FFFFFF"
    show_grid: bool = True
    grid_spacing: float = 60.0
    grid_color: str = "#E2E8F0"
    grid_opacity: float = 0.6


class HeaderConfig(BaseModel):
    """Action title, subtitle, and corporate brand accent stripes."""
    show: bool = True
    action_title: str = "Proposed: Enterprise Architecture"
    subtitle: str = "System Architecture & Execution Lifecycle Dataflow"
    tracker: Optional[str] = None
    brand_stripes: bool = True
    stripe_ratio: str = "1:2"  # 1 Red : 2 Blue ratio
    red_hex: str = "#E11D48"
    blue_hex: str = "#0284C7"
    x: float = 0.600
    y: float = 0.280


DIAGNOSTIC_ROLE_PALETTES: Dict[str, Dict[str, str]] = {
    # Red: Defect, bottleneck, synchronous blocking, critical debt
    "defect": {"stroke": "#DC2626", "fill": "#FEF2F2", "kicker_bg": "#FEE2E2", "text": "#991B1B"},
    "bottleneck": {"stroke": "#DC2626", "fill": "#FFFFFF", "kicker_bg": "#FEE2E2", "text": "#991B1B"},
    "p1": {"stroke": "#DC2626", "fill": "#FEF2F2", "kicker_bg": "#FEE2E2", "text": "#991B1B"},
    # Amber: Boundary, wait, sync, cloud container, compute
    "boundary": {"stroke": "#F59E0B", "fill": "#FFFBEB", "kicker_bg": "#FEF3C7", "text": "#B45309"},
    "wait": {"stroke": "#D97706", "fill": "#FFFBEB", "kicker_bg": "#FEF3C7", "text": "#B45309"},
    "sync": {"stroke": "#D97706", "fill": "#FFFBEB", "kicker_bg": "#FEF3C7", "text": "#B45309"},
    "compute": {"stroke": "#D97706", "fill": "#FFFFFF", "kicker_bg": "#FEF3C7", "text": "#92400E"},
    # Blue: Ingress, active flow, database, lakehouse
    "ingress": {"stroke": "#3B82F6", "fill": "#FFFFFF", "kicker_bg": "#EFF6FF", "text": "#1D4ED8"},
    "active": {"stroke": "#2563EB", "fill": "#EFF6FF", "kicker_bg": "#DBEAFE", "text": "#1E40AF"},
    "database": {"stroke": "#0284C7", "fill": "#F0F9FF", "kicker_bg": "#E0F2FE", "text": "#0369A1"},
    "lakehouse": {"stroke": "#0284C7", "fill": "#F0F9FF", "kicker_bg": "#E0F2FE", "text": "#0369A1"},
    # Green: Target state, deployment, reconciled, healthy
    "target": {"stroke": "#16A34A", "fill": "#ECFDF5", "kicker_bg": "#D1FAE5", "text": "#065F46"},
    "reconciled": {"stroke": "#16A34A", "fill": "#ECFDF5", "kicker_bg": "#D1FAE5", "text": "#065F46"},
    "code": {"stroke": "#10B981", "fill": "#ECFDF5", "kicker_bg": "#D1FAE5", "text": "#065F46"},
    # Purple: Gateway, orchestration, router
    "gateway": {"stroke": "#8B5CF6", "fill": "#F5F3FF", "kicker_bg": "#EDE9FE", "text": "#6D28D9"},
    "orchestration": {"stroke": "#7C3AED", "fill": "#F5F3FF", "kicker_bg": "#EDE9FE", "text": "#6D28D9"},
    # Security: KMS, Vault, Secrets
    "security": {"stroke": "#EF4444", "fill": "#FEF2F2", "kicker_bg": "#FEE2E2", "text": "#991B1B"},
    # Slate: Neutral container
    "neutral": {"stroke": "#94A3B8", "fill": "#F8FAFC", "kicker_bg": "#F1F5F9", "text": "#475569"},
}


class ContainerSpec(BaseModel):
    """Zone boundary or swimlane container enclosing entity cards."""
    id: str
    label: str
    x: float
    y: float
    w: float
    h: float
    role: Optional[str] = None
    border_hex: str = "#94A3B8"
    fill_hex: str = "#F8FAFC"
    fill_opacity: float = 0.5
    stroke_width: float = 2.0
    dashed: bool = True
    dash_pattern: str = "8 6"
    corner_radius: float = 0.0  # Sharp boundary swimlanes (MSO_SHAPE.RECTANGLE)
    tag_badge: Optional[str] = None
    tag_bg_hex: str = "#FEF3C7"
    tag_text_hex: str = "#B45309"
    font_size: float = 12.0
    font_color: str = "#64748B"
    align: Optional[str] = None
    vertical_align: Optional[str] = None
    parent_id: Optional[str] = None
    container_id: Optional[str] = None

    def resolved_vertical_align(self) -> str:
        if self.vertical_align is not None and self.vertical_align in ("top", "bottom", "middle"):
            return self.vertical_align
        return "bottom" if self.h >= 4.0 else "top"

    def resolved_align(self) -> str:
        if self.align is not None and self.align in ("left", "center", "right"):
            return self.align
        return "center" if self.w <= 2.0 else "left"

    def model_post_init(self, __context: Any) -> None:
        if self.role and self.role.lower() in DIAGNOSTIC_ROLE_PALETTES:
            palette = DIAGNOSTIC_ROLE_PALETTES[self.role.lower()]
            if self.border_hex == "#94A3B8":
                self.border_hex = palette["stroke"]
            if self.fill_hex == "#F8FAFC":
                self.fill_hex = palette["fill"]



def classify_geometric_tier(w_in: float, h_in: float) -> str:
    """
    Classify node dimensions (in inches) into 4-tier geometric scale:
    - Tier A: Primary Entity / Service Card (h >= 1.15 and w >= 1.00)
    - Tier B: Compact Card / Section Header Banner (0.50 <= h < 1.15 or h >= 1.15, w < 1.00)
    - Tier C: Sequential Process / Micro-Step Pill (h < 0.50)
    """
    if w_in > 25.0 or h_in > 25.0:
        w_in = w_in / 90.0
        h_in = h_in / 90.0
    if h_in >= 1.15 and w_in >= 1.00:
        return "Tier A"
    elif h_in >= 0.50:
        return "Tier B"
    else:
        return "Tier C"


CANONICAL_TYPOGRAPHIC_SCALE: Dict[str, Dict[str, float]] = {
    "Tier A": {"title_pt": 12.0, "subtitle_pt": 9.0, "kicker_pt": 8.0},
    "Tier B": {"title_pt": 10.5, "subtitle_pt": 8.5, "kicker_pt": 7.5},
    "Tier C": {"title_pt": 9.5, "subtitle_pt": 8.0, "kicker_pt": 0.0},
    "Tier D": {"flow_pt": 7.5, "badge_pt": 8.0},
    # Backward compatibility aliases
    "T1": {"title_pt": 12.0, "subtitle_pt": 9.0, "kicker_pt": 8.0},
    "T2": {"title_pt": 10.5, "subtitle_pt": 8.5, "kicker_pt": 7.5},
    "T3": {"title_pt": 9.5, "subtitle_pt": 8.0, "kicker_pt": 0.0},
    "T4": {"flow_pt": 7.5, "badge_pt": 8.0},
}


class NodeSpec(BaseModel):
    """Entity node, service card, database cylinder, or client application."""
    id: str
    container_id: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    bullets: Optional[List[str]] = None
    kicker: Optional[str] = None
    shape: str = "rounded"  # "rounded", "rect", "cylinder", "database", "circle", "pill"
    role: Optional[str] = None
    x: float
    y: float
    w: float
    h: Optional[float] = None  # None = auto-measure proportional height
    icon: Optional[str] = None  # Asset path, vendor slug (e.g. "aws:aws_lambda"), or SVG path
    icon_emoji: Optional[str] = None  # e.g. "🖥️"
    icon_layout: str = "auto"  # "auto", "stack", "side"
    stroke_hex: str = "#3B82F6"
    fill_hex: str = "#FFFFFF"
    stroke_width: float = 2.0
    title_color: str = "#0F172A"
    subtitle_color: str = "#64748B"
    title_pt: Optional[float] = None
    subtitle_pt: Optional[float] = None
    elastic_text: Optional[bool] = None  # None = auto-detect by geometric envelope; True = force; False = disable
    is_cylinder: bool = False
    is_rounded: bool = True
    shadow: bool = False
    valign: Literal["middle", "top", "bottom"] = "middle"
    align: Literal["center", "left", "right"] = "center"

    def resolved_title_pt(self, w_in: Optional[float] = None, h_in: Optional[float] = None) -> float:
        """Returns explicitly declared title_pt or canonical tier-based default."""
        if self.title_pt is not None:
            return float(self.title_pt)
        eff_w = w_in if w_in is not None else self.w
        eff_h = h_in if h_in is not None else (self.h if self.h is not None else 1.25)
        tier = classify_geometric_tier(eff_w, eff_h)
        return CANONICAL_TYPOGRAPHIC_SCALE[tier]["title_pt"]

    def resolved_subtitle_pt(self, w_in: Optional[float] = None, h_in: Optional[float] = None) -> float:
        """Returns explicitly declared subtitle_pt or canonical tier-based default."""
        if self.subtitle_pt is not None:
            return float(self.subtitle_pt)
        eff_w = w_in if w_in is not None else self.w
        eff_h = h_in if h_in is not None else (self.h if self.h is not None else 1.25)
        tier = classify_geometric_tier(eff_w, eff_h)
        return CANONICAL_TYPOGRAPHIC_SCALE[tier].get("subtitle_pt", 9.0)

    @field_validator("is_cylinder", mode="before")
    @classmethod
    def _validate_is_cylinder(cls, v: Any, info: Any) -> bool:
        if isinstance(v, bool):
            return v
        return False

    def model_post_init(self, __context: Any) -> None:
        if self.role and self.role.lower() in DIAGNOSTIC_ROLE_PALETTES:
            palette = DIAGNOSTIC_ROLE_PALETTES[self.role.lower()]
            if self.stroke_hex == "#3B82F6":
                self.stroke_hex = palette["stroke"]
            if self.fill_hex == "#FFFFFF":
                self.fill_hex = palette["fill"]

        if self.shape in ("cylinder", "database"):
            self.is_cylinder = True
            if self.icon_layout == "auto":
                self.icon_layout = "side"
        elif self.shape == "rect":
            self.is_rounded = False


def resolve_node_fonts(
    node: NodeSpec,
    w_in: Optional[float] = None,
    h_in: Optional[float] = None,
) -> Tuple[float, float, float]:
    """
    Resolves final rendered (title_pt, subtitle_pt, space_before_pt) for a node.
    Applies canonical tier defaults and Elastic Typography Auto-Fill when qualified.
    """
    eff_w = w_in if w_in is not None else node.w
    eff_h = h_in if h_in is not None else (node.h if node.h is not None else 1.25)
    if eff_w > 25.0 or eff_h > 25.0:
        eff_w = eff_w / 90.0
        eff_h = eff_h / 90.0

    t_pt = node.resolved_title_pt(eff_w, eff_h)
    s_pt = node.resolved_subtitle_pt(eff_w, eff_h)
    space_before_pt = 2.0

    # If elastic_text is explicitly False, retain baseline
    if node.elastic_text is False:
        return (t_pt, s_pt, space_before_pt)

    # Collect content lines
    title_lines = [seg.strip() for seg in node.title.split("\n") if seg.strip()]
    sub_lines = [seg.strip() for seg in node.subtitle.split("\n") if seg.strip()] if node.subtitle else []
    bullet_items = [str(b).strip() for b in node.bullets] if node.bullets else []
    all_bullet_lines = sub_lines + bullet_items
    total_lines = len(title_lines) + len(all_bullet_lines)

    # Check Elastic Activation Envelope
    is_forced = node.elastic_text is True
    if not is_forced:
        if node.elastic_text is None and (node.title_pt is not None or node.subtitle_pt is not None):
            return (t_pt, s_pt, space_before_pt)
        if eff_h < 1.80:
            return (t_pt, s_pt, space_before_pt)
        if getattr(node, "align", "center") not in ("left", "center") or getattr(node, "valign", "middle") not in ("top", "middle"):
            return (t_pt, s_pt, space_before_pt)
        if total_lines > 6:
            return (t_pt, s_pt, space_before_pt)

    # Geometric inner text bounds
    ss = min(eff_w, eff_h)
    pad_v = max(0.10, min(0.20, 0.11 * ss))
    pad_h = max(0.08, min(0.18, 0.07 * eff_w))
    is_cylinder = node.is_cylinder or node.shape in ("cylinder", "database")
    if is_cylinder:
        pv = pad_v * 0.6
        region_top = 0.25 * ss + pv
        region_bottom = eff_h - 0.125 * ss - pv
    else:
        region_top = pad_v
        region_bottom = eff_h - pad_v
    region_h = max(0.10, region_bottom - region_top)

    has_icon = bool(node.icon or node.icon_emoji)
    icon_sz = max(0.28, min(0.40, 0.26 * ss)) if has_icon else 0.0
    icon_gap = max(0.04, min(0.08, 0.05 * ss)) if has_icon else 0.0
    inner_w = eff_w - 2 * pad_h
    if node.icon_layout == "side" and has_icon:
        text_w = max(0.10, inner_w - icon_sz - icon_gap * 1.5)
    else:
        text_w = max(0.10, inner_w)

    def _line_width_in(text: str, pt: float, bold: bool) -> float:
        em = 0.55 if bold else 0.52
        return len(text) * pt * em / 72.0

    def _calc_content_h(cur_t_pt: float, cur_s_pt: float, cur_sp_pt: float) -> float:
        t_h = sum(max(1, math.ceil(_line_width_in(line, cur_t_pt, True) / text_w)) * cur_t_pt * 1.25 / 72.0 for line in title_lines) if title_lines else (cur_t_pt * 1.25 / 72.0)
        b_h = 0.0
        if all_bullet_lines:
            for b_line in all_bullet_lines:
                lines_cnt = max(1, math.ceil(_line_width_in(b_line, cur_s_pt, False) / text_w))
                b_h += (lines_cnt * cur_s_pt * 1.20 + cur_sp_pt) / 72.0
        kicker_h = (8.0 * 1.25 + 2.0) / 72.0 if node.kicker else 0.0
        if node.icon_layout == "side" and has_icon:
            return max(icon_sz, kicker_h + t_h + b_h)
        else:
            return (icon_sz + icon_gap if has_icon else 0.0) + kicker_h + t_h + b_h

    initial_content_h = _calc_content_h(t_pt, s_pt, space_before_pt)
    occupancy = initial_content_h / region_h

    # Check underfill threshold: initial occupancy < 0.55 (or < 0.85 if forced)
    threshold = 0.85 if is_forced else 0.55
    if occupancy >= threshold:
        return (t_pt, s_pt, space_before_pt)

    # Elastic Upward Scaling Loop
    cur_t = t_pt
    cur_s = s_pt
    cur_sp = space_before_pt

    while cur_s < 12.0:
        cand_s = cur_s + 0.5
        cand_t = min(16.5, cur_t + 0.5)
        # Zero-wrapping check
        wraps = False
        for line in title_lines:
            if _line_width_in(line, cand_t, True) > text_w:
                wraps = True
                break
        if wraps:
            break
        for line in all_bullet_lines:
            if _line_width_in(line, cand_s, False) > text_w:
                wraps = True
                break
        if wraps:
            break

        cand_sp = max(2.0, min(4.0, 2.0 + 2.0 * (cand_s - 9.0) / (12.0 - 9.0)))
        cand_content_h = _calc_content_h(cand_t, cand_s, cand_sp)
        if cand_content_h > 0.85 * region_h:
            break

        cur_s = cand_s
        cur_t = cand_t
        cur_sp = cand_sp

    return (cur_t, cur_s, cur_sp)



class FlowSpec(BaseModel):
    """Routed connector flow, inter-zone channel, or data exchange arrow."""
    id: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None
    role: Optional[str] = None
    source_port: Optional[str] = None  # "right", "left", "top", "bottom", "right_at(2.5)", or (x, y)
    target_port: Optional[str] = None  # "left", "right", "top", "bottom", "left_at(2.5)", or (x, y)
    points: List[List[float]] = Field(default_factory=list)  # explicit waypoints [[x1, y1], [x2, y2], ...]
    stroke_hex: str = "#2563EB"
    stroke_width: float = 2.5
    dashed: bool = False
    dash_pattern: Optional[str] = None
    has_arrow: bool = True
    arrow_type: str = "triangle"
    curve: str = "orthogonal"  # "straight", "orthogonal", "curved"
    label: Optional[str] = None
    label_at: Optional[List[float]] = None  # [x, y]
    label_position: Literal["center", "above", "below", "side", "left", "right", "auto"] = "auto"
    label_offset: Optional[float] = None
    label_bg_hex: str = "#EFF6FF"
    label_text_hex: str = "#1D4ED8"
    label_border_hex: Optional[str] = None
    font_pt: float = 9.0

    def model_post_init(self, __context: Any) -> None:
        if self.role and self.role.lower() in DIAGNOSTIC_ROLE_PALETTES:
            palette = DIAGNOSTIC_ROLE_PALETTES[self.role.lower()]
            if self.stroke_hex == "#2563EB":
                self.stroke_hex = palette["stroke"]
            if self.label_bg_hex == "#EFF6FF":
                self.label_bg_hex = palette["kicker_bg"]
            if self.label_text_hex == "#1D4ED8":
                self.label_text_hex = palette["text"]


class BadgeSpec(BaseModel):
    """Standalone warning pill, status indicator, or tag badge."""
    id: Optional[str] = None
    x: float
    y: float
    w: float = 1.4
    h: float = 0.28
    text: str
    bg_hex: str = "#FEF3C7"
    text_hex: str = "#B45309"
    border_hex: str = "#FDE68A"
    font_pt: float = 9.0


class BulletListSpec(BaseModel):
    """Standalone bullet list box for execution steps, milestones, or notes."""
    id: Optional[str] = None
    x: float
    y: float
    w: float = 2.9
    h: float = 1.55
    items: List[str] = Field(default_factory=list)
    font_size: float = 11.5
    font_color: str = "#0F172A"


class DiagramSpec(BaseModel):
    """Top-level declarative diagram architecture specification."""
    id: str = "diagram"
    name: str = "Architecture Diagram"
    theme: str = "metrodata"
    bundle: Optional[str] = None
    lifecycle_status: Optional[Literal["LATEST", "OUTDATED", "SCRATCH"]] = None
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    header: HeaderConfig = Field(default_factory=HeaderConfig)
    containers: List[ContainerSpec] = Field(default_factory=list)
    nodes: List[NodeSpec] = Field(default_factory=list)
    flows: List[FlowSpec] = Field(default_factory=list)
    badges: List[BadgeSpec] = Field(default_factory=list)
    bullet_lists: List[BulletListSpec] = Field(default_factory=list)

