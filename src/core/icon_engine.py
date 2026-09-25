"""
src/core/icon_engine.py
=======================
Core re-export shim for IconEngine, vector tinting, and icon resolution.
"""

from __future__ import annotations

from src.ppt_engine.icon_engine import (
    IconEngine,
    normalize_color,
    resolve_brand_color,
    recolor_svg,
    render_svg_to_png,
    get_brand_icon,
    search_icons,
    CANONICAL_ENTERPRISE_COLORS,
    FALLBACK_SVGS,
)

__all__ = [
    "IconEngine",
    "normalize_color",
    "resolve_brand_color",
    "recolor_svg",
    "render_svg_to_png",
    "get_brand_icon",
    "search_icons",
    "CANONICAL_ENTERPRISE_COLORS",
    "FALLBACK_SVGS",
]
