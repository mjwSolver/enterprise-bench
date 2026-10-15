"""
Diagram Engine V2 - Declarative Specification Models
=====================================================
Pydantic v2 data models defining the declarative YAML schema for enterprise
diagram topologies, container boundaries, entity nodes, and routed connectors.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field, field_validator


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
    x: Optional[float] = None
    y: Optional[float] = None


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
    align: str = "center"  # "center" | "left" | "right"
    vertical_align: str = "top"  # "top" | "bottom"

    def model_post_init(self, __context: Any) -> None:
        if self.role and self.role.lower() in DIAGNOSTIC_ROLE_PALETTES:
            palette = DIAGNOSTIC_ROLE_PALETTES[self.role.lower()]
            if self.border_hex == "#94A3B8":
                self.border_hex = palette["stroke"]
            if self.fill_hex == "#F8FAFC":
                self.fill_hex = palette["fill"]


class NodeSpec(BaseModel):
    """Entity node, service card, database cylinder, or client application."""
    id: str
    container_id: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
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
    is_cylinder: bool = False
    is_rounded: bool = True
    shadow: bool = False
    valign: Literal["middle", "top", "bottom"] = "middle"

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
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    header: HeaderConfig = Field(default_factory=HeaderConfig)
    containers: List[ContainerSpec] = Field(default_factory=list)
    nodes: List[NodeSpec] = Field(default_factory=list)
    flows: List[FlowSpec] = Field(default_factory=list)
    badges: List[BadgeSpec] = Field(default_factory=list)
    bullet_lists: List[BulletListSpec] = Field(default_factory=list)
