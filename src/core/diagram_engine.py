"""
src/core/diagram_engine.py
==========================
Core re-export shim for the Diagram Engine and Draw.io compilation subsystem.
Provides unified access across core and presentation engines.
"""

from __future__ import annotations

from src.ppt_engine.diagram_engine import (
    DiagramNode,
    DrawIONode,
    DiagramEdge,
    DiagramSubgraph,
    IngressBus,
    ParsedDiagram,
    MermaidParser,
    HierarchicalLayoutEngine,
    DrawIOConverter,
    DiagramRenderer,
    DiagramEngine,
    DrawIOProject,
    apply_node_icons,
    harmonize_icon_svg,
    mxgraph_to_ast,
    compile_mermaid,
    THEME_PRESETS,
    VENDOR_BRAND_COLORS,
)

__all__ = [
    "DiagramNode",
    "DrawIONode",
    "DiagramEdge",
    "DiagramSubgraph",
    "IngressBus",
    "ParsedDiagram",
    "MermaidParser",
    "HierarchicalLayoutEngine",
    "DrawIOConverter",
    "DiagramRenderer",
    "DiagramEngine",
    "DrawIOProject",
    "apply_node_icons",
    "harmonize_icon_svg",
    "mxgraph_to_ast",
    "compile_mermaid",
    "THEME_PRESETS",
    "VENDOR_BRAND_COLORS",
]
