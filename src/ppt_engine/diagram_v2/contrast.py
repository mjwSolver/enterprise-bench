"""
Diagram Engine V2 - Readability & Contrast Subsystem
=====================================================
Enforces WCAG 2.1 relative luminance and contrast ratios across declarative
diagram specifications. Eliminates faded/washed-out text on white/light
backgrounds, prevents borderless layout bleed on white canvas, and ensures
crisp typographic hierarchy on dark container fills.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union


# =============================================================================
# WCAG 2.1 Luminance & Contrast Thresholds
# =============================================================================
WCAG_AA_NORMAL_TEXT: float = 4.5
WCAG_AA_LARGE_TEXT: float = 3.0
WCAG_AAA_ENHANCED: float = 7.0
MIN_BORDER_CONTRAST: float = 1.25

# High-Contrast Fallback Palettes
HIGH_CONTRAST_TITLE_LIGHT: str = "#0F172A"       # Slate 900 (High-contrast on white/light)
HIGH_CONTRAST_SUBTITLE_LIGHT: str = "#334155"    # Slate 700 (High-contrast on white/light)
HIGH_CONTRAST_MUTED_LIGHT: str = "#475569"       # Slate 600
HIGH_CONTRAST_TITLE_DARK: str = "#FFFFFF"        # Pure white on dark
HIGH_CONTRAST_SUBTITLE_DARK: str = "#E2E8F0"     # Slate 200 on dark
HIGH_CONTRAST_HAIRLINE_BORDER: str = "#CBD5E1"   # Slate 300 (Visible hairline on white canvas)


# =============================================================================
# Mathematical Helpers: Hex Parsing & WCAG Relative Luminance
# =============================================================================

def parse_hex_rgb(hex_code: Optional[str]) -> Optional[Tuple[float, float, float]]:
    """
    Parses a hex color string into normalized (R, G, B) floating-point components [0.0 .. 1.0].
    Handles None, 3-digit shorthand (#FFF), and 6-digit standard hex (#FFFFFF).
    Returns None if hex_code is invalid or empty.
    """
    if not hex_code or not isinstance(hex_code, str):
        return None
    clean = hex_code.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        return None
    try:
        r = int(clean[0:2], 16) / 255.0
        g = int(clean[2:4], 16) / 255.0
        b = int(clean[4:6], 16) / 255.0
        return (r, g, b)
    except (ValueError, TypeError):
        return None


def srgb_to_linear(c_srgb: float) -> float:
    """Converts an sRGB color component to linear luminance per WCAG 2.1 specs."""
    if c_srgb <= 0.04045:
        return c_srgb / 12.92
    return ((c_srgb + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_code: Optional[str], default_lum: float = 1.0) -> float:
    """
    Calculates the exact WCAG 2.1 relative luminance (L) of a color [0.0 .. 1.0].
    Defaults to 1.0 (pure white) if hex_code is missing or invalid.
    """
    rgb = parse_hex_rgb(hex_code)
    if rgb is None:
        return default_lum
    r_lin = srgb_to_linear(rgb[0])
    g_lin = srgb_to_linear(rgb[1])
    b_lin = srgb_to_linear(rgb[2])
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(hex1: Optional[str], hex2: Optional[str]) -> float:
    """
    Calculates the WCAG 2.1 contrast ratio between two hex colors:
    CR = (L1 + 0.05) / (L2 + 0.05) where L1 is lighter and L2 is darker.
    Returns float in range [1.0 .. 21.0].
    """
    l1 = relative_luminance(hex1, default_lum=1.0)
    l2 = relative_luminance(hex2, default_lum=1.0)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_dark_hex(hex_code: Optional[str]) -> bool:
    """
    Determine if a hex color is perceptually dark using standard Rec. 601 luma
    lum < 0.45.
    """
    rgb = parse_hex_rgb(hex_code)
    if rgb is None:
        return False
    # Fast perceptual luma
    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return lum < 0.45


def is_light_hex(hex_code: Optional[str]) -> bool:
    """Determine if a hex color is perceptually light (relative luminance >= 0.45)."""
    return not is_dark_hex(hex_code)


# =============================================================================
# Automated Contrast & Readability Harmonization Engine
# =============================================================================

def harmonize_node_contrast(node: Any, canvas_bg: str = "#FFFFFF") -> None:
    """
    Harmonizes an individual NodeSpec against its fill background and the canvas:
    1. Faded Text Elimination: On light backgrounds, title and subtitle text failing
       WCAG AA (CR < 4.5:1) are clamped to high-contrast enterprise slates.
    2. Borderless Layout Protection: On white/light backgrounds, cards whose stroke
       blends invisibly into canvas (CR < 1.25:1) are given crisp hairline borders.
    3. Dark Background Inversion: On dark fills, text and monochrome icons are auto-inverted.
    """
    node_fill = getattr(node, "fill_hex", None) or "#FFFFFF"
    canvas_lum = relative_luminance(canvas_bg, default_lum=1.0)

    if is_dark_hex(node_fill):
        # ---------------------------------------------------------------------
        # Dark Background Mode: Invert text to high-contrast whites
        # ---------------------------------------------------------------------
        if contrast_ratio(getattr(node, "title_color", None), node_fill) < WCAG_AA_NORMAL_TEXT:
            node.title_color = HIGH_CONTRAST_TITLE_DARK

        if contrast_ratio(getattr(node, "subtitle_color", None), node_fill) < WCAG_AA_LARGE_TEXT:
            node.subtitle_color = HIGH_CONTRAST_SUBTITLE_DARK

        # Auto-invert monochrome icon if unassigned or dark
        cur_icon_col = getattr(node, "icon_color", None)
        cur_stroke = getattr(node, "stroke_hex", None)
        if not cur_icon_col and (not cur_stroke or is_dark_hex(cur_stroke)):
            node.icon_color = HIGH_CONTRAST_TITLE_DARK

    else:
        # ---------------------------------------------------------------------
        # Light / White Background Mode: Eliminate faded text & washed layout
        # ---------------------------------------------------------------------
        # 1. Title Readability: Must meet WCAG AA (>= 4.5:1)
        cur_title_col = getattr(node, "title_color", None) or "#0F172A"
        if contrast_ratio(cur_title_col, node_fill) < WCAG_AA_NORMAL_TEXT:
            node.title_color = HIGH_CONTRAST_TITLE_LIGHT

        # 2. Subtitle / Bullets Readability: Must meet at least 3.5:1 on light fills
        cur_sub_col = getattr(node, "subtitle_color", None) or "#64748B"
        if contrast_ratio(cur_sub_col, node_fill) < 3.5:
            node.subtitle_color = HIGH_CONTRAST_SUBTITLE_LIGHT

        # 3. Layout Boundary Protection (The Faded Layout Invariant):
        # If card is on a white canvas and card fill is white/near-white,
        # ensure border does not bleed invisibly into canvas.
        fill_lum = relative_luminance(node_fill, default_lum=1.0)
        if fill_lum > 0.85 and canvas_lum > 0.85:
            cur_stroke = getattr(node, "stroke_hex", None) or "#CBD5E1"
            border_cr = contrast_ratio(cur_stroke, canvas_bg)
            if border_cr < MIN_BORDER_CONTRAST:
                node.stroke_hex = HIGH_CONTRAST_HAIRLINE_BORDER
                if getattr(node, "stroke_width", 1.0) < 1.0:
                    node.stroke_width = 1.0


def harmonize_container_contrast(container: Any, canvas_bg: str = "#FFFFFF") -> None:
    """
    Harmonizes a ContainerSpec against its fill and canvas background:
    1. Label contrast: ensures container label is legible against container fill.
    2. Tag badge contrast: ensures badge text is high-contrast against badge background.
    3. Boundary contrast: ensures container boundary is distinct from canvas.
    """
    c_fill = getattr(container, "fill_hex", None) or "#F8FAFC"
    if is_dark_hex(c_fill):
        if contrast_ratio(getattr(container, "font_color", None), c_fill) < WCAG_AA_NORMAL_TEXT:
            container.font_color = "#F8FAFC"
    else:
        cur_font = getattr(container, "font_color", None) or "#64748B"
        if contrast_ratio(cur_font, c_fill) < 3.5:
            container.font_color = HIGH_CONTRAST_SUBTITLE_LIGHT

    # Tag badge contrast check
    tag_bg = getattr(container, "tag_bg_hex", None)
    tag_text = getattr(container, "tag_text_hex", None)
    if tag_bg and tag_text:
        if contrast_ratio(tag_text, tag_bg) < WCAG_AA_NORMAL_TEXT:
            # Auto-clamp based on tag background hue
            if is_dark_hex(tag_bg):
                container.tag_text_hex = "#FFFFFF"
            else:
                container.tag_text_hex = "#78350F" if "#FE" in tag_bg.upper() or "#F5" in tag_bg.upper() else "#0F172A"

    # Container boundary definition
    c_border = getattr(container, "border_hex", None)
    if c_border and contrast_ratio(c_border, canvas_bg) < MIN_BORDER_CONTRAST:
        container.border_hex = "#94A3B8"


def harmonize_flow_contrast(flow: Any) -> None:
    """Ensures flow label text meets WCAG AA contrast against its label pill background."""
    bg = getattr(flow, "label_bg_hex", None)
    txt = getattr(flow, "label_text_hex", None)
    if bg and txt:
        if contrast_ratio(txt, bg) < WCAG_AA_NORMAL_TEXT:
            if is_dark_hex(bg):
                flow.label_text_hex = "#FFFFFF"
            else:
                flow.label_text_hex = "#0F172A"


def harmonize_diagram_contrast(spec: Any) -> Any:
    """
    Applies the full Readability & Contrast Subsystem pass across all entities
    in a DiagramSpec AST.
    """
    canvas_bg = "#FFFFFF"
    if hasattr(spec, "canvas") and hasattr(spec.canvas, "background"):
        canvas_bg = spec.canvas.background or "#FFFFFF"

    # 1. Containers
    if hasattr(spec, "containers"):
        for c in spec.containers:
            harmonize_container_contrast(c, canvas_bg=canvas_bg)

    # 2. Nodes
    if hasattr(spec, "nodes"):
        for n in spec.nodes:
            harmonize_node_contrast(n, canvas_bg=canvas_bg)

    # 3. Flows
    if hasattr(spec, "flows"):
        for f in spec.flows:
            harmonize_flow_contrast(f)

    return spec
