"""
Presentation Vector Widgets Package
===================================
Provides modular, reusable DrawingML vector components:
- `threshold_bars`: Horizontal bar chart with vertical gate lines and status pills.
- `macos_window`: High-fidelity macOS desktop browser mockup with authentic chrome.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

def to_inches(val: Any) -> float:
    """Safely converts pptx Length, int (EMUs or inches), or float to float inches."""
    if hasattr(val, "inches"):
        return float(val.inches)
    if hasattr(val, "pt"):
        return float(val.pt) / 72.0
    if isinstance(val, (int, float)):
        # Any value > 500 is definitely EMUs (914400 EMUs per inch)
        if val > 500:
            return float(val) / 914400.0
        return float(val)
    return float(val)

from src.ppt_engine.widgets.threshold_bars import render_threshold_bars
from src.ppt_engine.widgets.macos_window import render_macos_window

__all__ = [
    "to_inches",
    "render_widget",
    "render_threshold_bars",
    "render_macos_window",
]


def render_widget(
    slide: Any,
    theme: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    widget_config: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Universal dispatcher for declarative presentation widgets.

    Widget schema:
      type: str ('threshold_bars', 'macos_window', 'browser_mockup')
      ... (widget-specific props)
    """
    if not isinstance(widget_config, dict):
        return None

    left_in = to_inches(left)
    top_in = to_inches(top)
    width_in = to_inches(width)
    height_in = to_inches(height)

    w_type = str(widget_config.get("type", "")).lower().strip()

    if w_type in ("threshold_bars", "gate_bars", "coverage_bars", "horizontal_bars"):
        return render_threshold_bars(slide, theme, left_in, top_in, width_in, height_in, widget_config)
    elif w_type in ("macos_window", "browser_mockup", "window_mockup", "mac_window"):
        return render_macos_window(slide, theme, left_in, top_in, width_in, height_in, widget_config)
    else:
        return None
