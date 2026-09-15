"""
Theme Engine Subsystem
======================
Loads, parses, validates, and manages presentation themes from YAML presets.
Provides high-level helpers for colors (RGBColor / Hex), typography scales,
geometry rules (corner radius, shadows), and diagram integration palettes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pptx.dml.color import RGBColor


# Helper: convert hex string to pptx RGBColor
def hex_to_rgb(hex_code: str) -> RGBColor:
    """Convert a hex color string (e.g. '#2563EB' or '2563EB') to pptx RGBColor."""
    clean_hex = hex_code.strip().lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join(c * 2 for c in clean_hex)
    if len(clean_hex) != 6:
        raise ValueError(f"Invalid hex color string: '{hex_code}'")
    r = int(clean_hex[0:2], 16)
    g = int(clean_hex[2:4], 16)
    b = int(clean_hex[4:6], 16)
    return RGBColor(r, g, b)


def rgb_to_hex(color: RGBColor) -> str:
    """Convert pptx RGBColor to uppercase hex string (e.g. '#2563EB')."""
    return f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"


# Color Key Aliases for maximum cross-compatibility
_PALETTE_KEY_ALIASES: Dict[str, List[str]] = {
    "background": ["canvas_bg", "bg", "canvas_background"],
    "surface": ["card_bg", "card_fill", "card"],
    "surface_muted": ["card_muted", "muted_bg", "container_fill"],
    "border": ["border_light", "card_border", "line"],
    "border_accent": ["border_highlight", "card_border_accent"],
    "primary": ["text_primary", "dark", "title_color"],
    "secondary": ["text_secondary", "text_body", "subtitle_color"],
    "muted": ["text_muted", "caption_color"],
    "accent": ["brand_primary", "brand_blue", "accent_primary", "brand_color"],
    "accent_secondary": ["brand_secondary", "brand_cyan", "brand_accent"],
    "accent_teal": ["brand_teal", "teal"],
    "success": ["brand_success", "green"],
    "warning": ["brand_warning", "amber"],
    "danger": ["error", "red", "brand_danger"],
    "badge_blue_fill": ["badge_primary_fill", "badge_blue_bg"],
    "badge_blue_text": ["badge_primary_text"],
    "badge_green_fill": ["badge_success_fill"],
    "badge_green_text": ["badge_success_text"],
    "badge_amber_fill": ["badge_warning_fill"],
    "badge_amber_text": ["badge_warning_text"],
    "badge_red_fill": ["badge_error_fill"],
    "badge_red_text": ["badge_error_text"],
}


@dataclass
class Theme:
    """
    Structured Presentation Theme.
    Encapsulates palette colors, geometry rules, typography thresholds,
    and diagram rendering styling.
    """
    name: str
    description: str = ""
    palette: Dict[str, str] = field(default_factory=dict)
    geometry: Dict[str, Any] = field(default_factory=dict)
    typography: Dict[str, Any] = field(default_factory=dict)
    diagram: Dict[str, Any] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Color Accessors
    # -------------------------------------------------------------------------
    def get_hex(self, key: str, default: str = "#000000") -> str:
        """Get uppercase hex color string for the given palette or diagram key."""
        if key in self.palette:
            return self.palette[key].upper()

        # Check aliases
        if key in _PALETTE_KEY_ALIASES:
            for alias in _PALETTE_KEY_ALIASES[key]:
                if alias in self.palette:
                    return self.palette[alias].upper()
        else:
            # Check if key is an alias for a canonical key
            for canonical, aliases in _PALETTE_KEY_ALIASES.items():
                if key in aliases and canonical in self.palette:
                    return self.palette[canonical].upper()

        # Check diagram dict
        if key in self.diagram:
            val = str(self.diagram[key])
            if val.startswith("#"):
                return val.upper()

        return default.upper()

    def get_rgb(self, key: str, default: str = "#000000") -> RGBColor:
        """Get python-pptx RGBColor object for the given palette or diagram key."""
        hex_val = self.get_hex(key, default=default)
        return hex_to_rgb(hex_val)

    # -------------------------------------------------------------------------
    # Geometry Accessors
    # -------------------------------------------------------------------------
    @property
    def corner_radius(self) -> int:
        """Corner radius in pixels/units (0 = sharp rectangular, > 0 = rounded)."""
        if "corner_radius" in self.geometry:
            return int(self.geometry["corner_radius"])
        if "corner_radius_pt" in self.geometry:
            return int(self.geometry["corner_radius_pt"])
        return 0

    @property
    def enable_shadows(self) -> bool:
        """Whether soft visual shadows are enabled for card containers."""
        return bool(self.geometry.get("enable_shadows", False))

    @property
    def card_border_width_pt(self) -> float:
        """Default card hairline border width in points."""
        return float(self.geometry.get("card_border_width_pt", self.geometry.get("border_width_pt", 1.0)))

    @property
    def accent_stripe_height_in(self) -> float:
        """Height of the top accent stripe on cards in inches."""
        return float(self.geometry.get("accent_stripe_height_in", 0.08))

    # -------------------------------------------------------------------------
    # Typography Accessors
    # -------------------------------------------------------------------------
    @property
    def font_family(self) -> str:
        """Primary body font family."""
        return str(self.typography.get("font_family", self.typography.get("font_family_body", "Helvetica, Arial, sans-serif")))

    @property
    def font_family_header(self) -> str:
        """Primary header font family."""
        return str(self.typography.get("font_family_header", self.font_family))

    @property
    def typography_thresholds(self) -> Dict[str, float]:
        """Dictionary of standard font size thresholds in points."""
        defaults = {
            "tracker_pt": float(self.typography.get("tracker_size_pt", 9.5)),
            "action_title_pt": float(self.typography.get("title_size_pt", 20.0)),
            "subtitle_pt": 11.0,
            "card_title_pt": float(self.typography.get("card_title_size_pt", 12.0)),
            "body_pt": float(self.typography.get("body_size_pt", 10.0)),
            "bullet_pt": 9.5,
            "caption_pt": float(self.typography.get("caption_size_pt", 8.5)),
            "metric_large_pt": 24.0,
            "metric_medium_pt": float(self.typography.get("metric_size_pt", 18.0)),
            "metric_small_pt": 14.0,
            "badge_pt": 8.0,
        }
        thresholds = self.typography.get("thresholds", {})
        if isinstance(thresholds, dict):
            merged = dict(defaults)
            for k, v in thresholds.items():
                try:
                    merged[k] = float(v)
                except (ValueError, TypeError):
                    pass
            return merged
        return defaults

    # -------------------------------------------------------------------------
    # Diagram Accessors
    # -------------------------------------------------------------------------
    @property
    def diagram_thresholds(self) -> Dict[str, Any]:
        """Dictionary of diagram rendering styling parameters."""
        defaults = {
            "canvas_bg": self.get_hex("background", "#F8FAFC"),
            "container_fill": self.get_hex("surface_muted", "#F1F5F9"),
            "container_stroke": self.get_hex("border", "#CBD5E1"),
            "container_font": self.get_hex("primary", "#1E293B"),
            "node_fill": self.get_hex("surface", "#FFFFFF"),
            "node_stroke": self.get_hex("accent", "#2563EB"),
            "node_stroke_width": "2",
            "node_font": self.get_hex("primary", "#1E293B"),
            "node_font_family": self.font_family,
            "node_font_size": "13",
            "accent_node_fill": self.get_hex("badge_blue_fill", "#EFF6FF"),
            "accent_node_stroke": self.get_hex("accent", "#3B82F6"),
            "accent_node_font": self.get_hex("accent", "#1E40AF"),
            "edge_stroke": self.get_hex("secondary", "#64748B"),
            "edge_stroke_width": "2",
            "edge_font": self.get_hex("secondary", "#475569"),
            "edge_font_size": "11",
            "state_node_fill": self.get_hex("primary", "#1E293B"),
        }
        if self.diagram:
            merged = dict(defaults)
            merged.update(self.diagram)
            return merged
        return defaults

    def to_dict(self) -> Dict[str, Any]:
        """Serialize theme back into dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "palette": self.palette,
            "geometry": self.geometry,
            "typography": self.typography,
            "diagram": self.diagram,
        }


# ============================================================================
# Theme Engine Registry & Loader
# ============================================================================

class ThemeEngine:
    def __init__(self, themes_dir: Optional[Union[str, Path]] = None) -> None:
        if themes_dir is None:
            # Default to presets/themes relative to enterprise-bench root
            try:
                from src.core.config import THEMES_DIR
                self.themes_dir = THEMES_DIR
            except ImportError:
                repo_root = Path(__file__).resolve().parent.parent.parent
                self.themes_dir = repo_root / "presets" / "themes"
        else:
            self.themes_dir = Path(themes_dir)

        self._cache: Dict[str, Theme] = {}

    def list_available_themes(self) -> List[str]:
        """List all available theme names in presets/themes/ directory."""
        if not self.themes_dir.exists() or not self.themes_dir.is_dir():
            return ["default", "snowblue", "brickred"]
        
        themes: List[str] = []
        for file in sorted(self.themes_dir.glob("*.yaml")):
            themes.append(file.stem)
        for file in sorted(self.themes_dir.glob("*.yml")):
            if file.stem not in themes:
                themes.append(file.stem)
        
        # Ensure default themes appear if not found
        for default_name in ["default", "snowblue", "brickred"]:
            if default_name not in themes:
                themes.append(default_name)
        return themes

    def load_theme(self, name_or_path: Union[str, Path]) -> Theme:
        """
        Load a theme by preset name (e.g. 'default', 'snowblue', 'brickred')
        or from a direct file path.
        """
        path = Path(name_or_path)

        # Direct file path
        if path.exists() and path.is_file():
            theme_name = path.stem
            if theme_name in self._cache:
                return self._cache[theme_name]
            theme = self._parse_yaml_file(path)
            self._cache[theme.name] = theme
            return theme

        # Lookup by theme name in themes_dir
        theme_name = str(name_or_path).strip()
        if theme_name in self._cache:
            return self._cache[theme_name]

        target_yaml = self.themes_dir / f"{theme_name}.yaml"
        target_yml = self.themes_dir / f"{theme_name}.yml"

        if target_yaml.exists():
            theme = self._parse_yaml_file(target_yaml)
        elif target_yml.exists():
            theme = self._parse_yaml_file(target_yml)
        else:
            # Fallback builtin defaults
            theme = self._get_builtin_theme(theme_name)

        self._cache[theme.name] = theme
        return theme

    def _parse_yaml_file(self, file_path: Path) -> Theme:
        """Parse a YAML file into a Theme instance."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}

        return Theme(
            name=raw_data.get("name", file_path.stem),
            description=raw_data.get("description", ""),
            palette=raw_data.get("palette", {}),
            geometry=raw_data.get("geometry", {}),
            typography=raw_data.get("typography", {}),
            diagram=raw_data.get("diagram", {}),
        )

    def _get_builtin_theme(self, name: str) -> Theme:
        """Provide fallback builtin themes if YAML files are not present."""
        if name == "snowblue":
            return Theme(
                name="snowblue",
                description="Snow Blue: crisp frost #F0FDF4 / #F0F9FF, cobalt #0284C7, cyan accent #06B6D4, surface #FFFFFF, border #BAE6FD, corner_radius 8, soft modern borders",
                palette={
                    "background": "#F0F9FF",
                    "surface": "#FFFFFF",
                    "surface_muted": "#F0FDF4",
                    "border": "#BAE6FD",
                    "border_accent": "#38BDF8",
                    "primary": "#0F172A",
                    "secondary": "#334155",
                    "muted": "#64748B",
                    "accent": "#0284C7",
                    "accent_secondary": "#06B6D4",
                    "accent_teal": "#0D9488",
                    "success": "#10B981",
                    "warning": "#F59E0B",
                    "danger": "#EF4444",
                    "badge_blue_fill": "#E0F2FE",
                    "badge_blue_text": "#0369A1",
                    "badge_green_fill": "#ECFDF5",
                    "badge_green_text": "#047857",
                    "badge_amber_fill": "#FEF3C7",
                    "badge_amber_text": "#B45309",
                    "badge_red_fill": "#FEE2E2",
                    "badge_red_text": "#B91C1C",
                },
                geometry={"corner_radius": 8, "enable_shadows": False, "card_border_width_pt": 1.0},
            )
        elif name == "brickred":
            return Theme(
                name="brickred",
                description="Brick Red: warm terracotta / crimson #DC2626 / #991B1B, dark charcoal #0F172A, surface #FFFFFF, border #FECACA, corner_radius 0, sharp corporate square geometry",
                palette={
                    "background": "#FFFBFB",
                    "surface": "#FFFFFF",
                    "surface_muted": "#F8FAFC",
                    "border": "#FECACA",
                    "border_accent": "#F87171",
                    "primary": "#0F172A",
                    "secondary": "#334155",
                    "muted": "#64748B",
                    "accent": "#DC2626",
                    "accent_secondary": "#991B1B",
                    "accent_teal": "#0F766E",
                    "success": "#16A34A",
                    "warning": "#D97706",
                    "danger": "#991B1B",
                    "badge_blue_fill": "#EFF6FF",
                    "badge_blue_text": "#1D4ED8",
                    "badge_green_fill": "#F0FDF4",
                    "badge_green_text": "#15803D",
                    "badge_amber_fill": "#FEF3C7",
                    "badge_amber_text": "#B45309",
                    "badge_red_fill": "#FEF2F2",
                    "badge_red_text": "#991B1B",
                },
                geometry={"corner_radius": 0, "enable_shadows": False, "card_border_width_pt": 1.0},
            )
        else:
            return Theme(
                name="default",
                description="Clean Corporate: slate #1E293B, royal blue #2563EB, background #F8FAFC, surface #FFFFFF, border #E2E8F0, corner_radius 0, no shadows",
                palette={
                    "background": "#F8FAFC",
                    "surface": "#FFFFFF",
                    "surface_muted": "#F1F5F9",
                    "border": "#E2E8F0",
                    "border_accent": "#BFDBFE",
                    "primary": "#1E293B",
                    "secondary": "#475569",
                    "muted": "#94A3B8",
                    "accent": "#2563EB",
                    "accent_secondary": "#0EA5E9",
                    "accent_teal": "#0F766E",
                    "success": "#16A34A",
                    "warning": "#D97706",
                    "danger": "#DC2626",
                    "badge_blue_fill": "#EFF6FF",
                    "badge_blue_text": "#1D4ED8",
                    "badge_green_fill": "#F0FDF4",
                    "badge_green_text": "#15803D",
                    "badge_amber_fill": "#FEF3C7",
                    "badge_amber_text": "#B45309",
                    "badge_red_fill": "#FEF2F2",
                    "badge_red_text": "#B91C1C",
                },
                geometry={"corner_radius": 0, "enable_shadows": False, "card_border_width_pt": 1.0},
            )


# Global Engine Instance & Module-Level Conveniences
_DEFAULT_ENGINE = ThemeEngine()


def list_available_themes(themes_dir: Optional[Union[str, Path]] = None) -> List[str]:
    """List all available theme preset names."""
    if themes_dir:
        return ThemeEngine(themes_dir=themes_dir).list_available_themes()
    return _DEFAULT_ENGINE.list_available_themes()


def load_theme(name_or_path: Union[str, Path], themes_dir: Optional[Union[str, Path]] = None) -> Theme:
    """Load a theme by name or file path."""
    if themes_dir:
        return ThemeEngine(themes_dir=themes_dir).load_theme(name_or_path)
    return _DEFAULT_ENGINE.load_theme(name_or_path)


def get_theme(name: str = "default") -> Theme:
    """Convenience lookup for cached or preset theme."""
    return _DEFAULT_ENGINE.load_theme(name)
