"""
src/core/units.py
=================
Canonical unit standardization and coordinate conversions across OpenXML,
DrawingML, python-docx, and python-pptx.
"""

from __future__ import annotations

# Base Conversion Multipliers
EMU_PER_INCH: int = 914400
EMU_PER_PT: int = 12700
EMU_PER_CM: int = 360000
EMU_PER_MM: int = 36000

TWIPS_PER_INCH: int = 1440
TWIPS_PER_PT: int = 20

OPENXML_BORDER_SZ_PER_PT: int = 8  # 1 pt border = val="8" in w:tcBorders
DRAWINGML_ALPHA_MAX: int = 100000   # 100% alpha opacity = 100000 in a:alpha


def pt_to_emu(pt: float) -> int:
    """Convert points (pt) to English Metric Units (EMU)."""
    return int(round(pt * EMU_PER_PT))


def emu_to_pt(emu: int) -> float:
    """Convert English Metric Units (EMU) to points (pt)."""
    return emu / EMU_PER_PT


def inches_to_emu(inches: float) -> int:
    """Convert inches to English Metric Units (EMU)."""
    return int(round(inches * EMU_PER_INCH))


def emu_to_inches(emu: int) -> float:
    """Convert English Metric Units (EMU) to inches."""
    return emu / EMU_PER_INCH


def pt_to_twips(pt: float) -> int:
    """Convert points (pt) to Word processing twips (1/20 of a pt)."""
    return int(round(pt * TWIPS_PER_PT))


def twips_to_pt(twips: int) -> float:
    """Convert Word processing twips to points (pt)."""
    return twips / TWIPS_PER_PT


def alpha_percent_to_drawingml(opacity_pct: float) -> int:
    """
    Convert opacity percentage (0.0 to 100.0 or 0.0 to 1.0) to DrawingML integer alpha.
    Example: 45% -> 45000.
    """
    factor = opacity_pct / 100.0 if opacity_pct > 1.0 else opacity_pct
    return int(round(factor * DRAWINGML_ALPHA_MAX))


def pt_to_openxml_border_sz(pt: float) -> int:
    """
    Convert points (pt) to OpenXML table/cell border size (eighths of a point).
    Example: 1.0 pt -> 8, 0.5 pt -> 4.
    """
    return int(round(pt * OPENXML_BORDER_SZ_PER_PT))
