"""
Core Theme & Visual Token System
=================================
Unified brand tokens, 60-30-10 palette validation, typography standards,
and conversion utilities shared across presentations, Word documents,
and spreadsheets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from src.core.config import THEMES_DIR, get_theme_path


def parse_hex(hex_code: str) -> Tuple[int, int, int]:
    """Parse hex string (#RRGGBB or RRGGBB) to (R, G, B) integer tuple."""
    clean = hex_code.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        raise ValueError(f"Invalid hex color string: '{hex_code}'")
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)


@dataclass
class EnterpriseTheme:
    """Unified brand style tokens for presentations and enterprise documents."""
    name: str
    bg_color: str = "#FFFFFF"
    surface_color: str = "#F8FAFC"
    text_primary: str = "#0F172A"
    text_secondary: str = "#475569"
    text_muted: str = "#94A3B8"
    accent_primary: str = "#2563EB"
    accent_secondary: str = "#0284C7"
    success_color: str = "#10B981"
    warning_color: str = "#F59E0B"
    danger_color: str = "#EF4444"
    border_color: str = "#E2E8F0"
    font_header: str = "Calibri"
    font_body: str = "Calibri"
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def rgb_primary(self) -> Tuple[int, int, int]:
        return parse_hex(self.accent_primary)

    @property
    def rgb_background(self) -> Tuple[int, int, int]:
        return parse_hex(self.bg_color)

    @classmethod
    def from_yaml(cls, yaml_path_or_name: Union[str, Path]) -> EnterpriseTheme:
        """Load an enterprise theme from a YAML preset file or theme name."""
        p = Path(yaml_path_or_name)
        if not p.exists():
            p = get_theme_path(str(yaml_path_or_name))
        
        if not p.exists():
            raise FileNotFoundError(f"Theme preset not found: {yaml_path_or_name}")

        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        palette = data.get("palette", {})
        typography = data.get("typography", {})

        return cls(
            name=data.get("name", p.stem),
            bg_color=palette.get("background", "#FFFFFF"),
            surface_color=palette.get("surface", "#F8FAFC"),
            text_primary=palette.get("primary", "#0F172A"),
            text_secondary=palette.get("secondary", "#475569"),
            text_muted=palette.get("muted", "#94A3B8"),
            accent_primary=palette.get("accent", "#2563EB"),
            accent_secondary=palette.get("accent_secondary", "#0284C7"),
            success_color=palette.get("success", "#10B981"),
            warning_color=palette.get("warning", "#F59E0B"),
            danger_color=palette.get("danger", "#EF4444"),
            border_color=palette.get("border", "#E2E8F0"),
            font_header=typography.get("font_header", typography.get("font_family", "Calibri")),
            font_body=typography.get("font_body", typography.get("font_family", "Calibri")),
            raw_data=data,
        )


def list_available_themes() -> List[str]:
    """Return all theme names available in presets/themes."""
    if not THEMES_DIR.exists():
        return []
    themes = []
    for f in THEMES_DIR.glob("*.yaml"):
        themes.append(f.stem)
    for f in THEMES_DIR.glob("*.yml"):
        if f.stem not in themes:
            themes.append(f.stem)
    return sorted(themes)
