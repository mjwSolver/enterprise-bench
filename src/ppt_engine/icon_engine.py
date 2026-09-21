"""
Icon Lookup, Dynamic Brand Tinting, and SVG/PNG Rendering Subsystem.
Powered by Iconify API, resvg / cairosvg, and Pillow.
"""

from __future__ import annotations

import os
import re
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Union, Tuple, List, Dict, Any
from io import BytesIO

import requests
from PIL import Image

# Ensure dynamic libraries on macOS Homebrew paths can be located for cairosvg if needed
if sys.platform == "darwin":
    brew_paths = ["/opt/homebrew/lib", "/usr/local/lib"]
    current_dyld = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    for p in brew_paths:
        if os.path.exists(p) and p not in current_dyld:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"{p}:{current_dyld}".strip(":")

# Optional SVG rasterizers with priority: resvg-py -> cairosvg -> svglib
_HAS_RESVG = False
try:
    import resvg_py
    _HAS_RESVG = True
except ImportError:
    pass

_HAS_CAIROSVG = False
try:
    import cairosvg
    _HAS_CAIROSVG = True
except Exception:
    pass

logger = logging.getLogger(__name__)


# Standard fallback icon definitions when network is offline
FALLBACK_SVGS = {
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "user": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "trend-up": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "lock": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "settings": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>',
    "star": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "default": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
}


CANONICAL_ENTERPRISE_COLORS: Dict[str, str] = {
    "accent": "#2563EB",
    "primary": "#0F172A",
    "secondary": "#475569",
    "muted": "#94A3B8",
    "accent_primary": "#2563EB",
    "accent_secondary": "#0284C7",
    "accent_teal": "#0F766E",
    "teal": "#0F766E",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "error": "#EF4444",
    "info": "#3B82F6",
    "surface": "#F8FAFC",
    "surface_muted": "#F1F5F9",
    "background": "#FFFFFF",
    "border": "#E2E8F0",
    "brand_primary": "#2563EB",
    "brand_secondary": "#0284C7",
    "brand_teal": "#0F766E",
    "blue": "#2563EB",
    "red": "#EF4444",
    "green": "#10B981",
    "amber": "#F59E0B",
    "orange": "#F97316",
    "cyan": "#06B6D4",
    "purple": "#8B5CF6",
    "indigo": "#6366F1",
    "slate": "#64748B",
    "gray": "#6B7280",
    "grey": "#6B7280",
    "black": "#000000",
    "white": "#FFFFFF",
}


def resolve_brand_color(color: Union[str, Any], theme: Optional[Any] = None) -> str:
    """
    Resolves a color name or theme token (e.g. 'accent', 'danger', 'primary')
    to a canonical 6-digit hex string (#RRGGBB).
    If a Theme instance or dict is provided, queries the theme's palette.
    Otherwise, resolves against canonical enterprise brand defaults.
    """
    if not isinstance(color, str):
        return normalize_color(color)

    clean = color.strip()

    # If it's already hex or rgb format, let normalize_color handle it
    if clean.startswith("#") or clean.startswith("rgb") or (len(clean) in (3, 6) and re.fullmatch(r"[0-9a-fA-F]+", clean)):
        return normalize_color(clean)

    key = clean.lower()

    # 1. Resolve against provided theme
    if theme is not None:
        if hasattr(theme, "get_hex"):
            val = theme.get_hex(key, default="")
            if val and val != "#000000":
                return val
            if val == "#000000" and key in ("black", "dark"):
                return val
        elif isinstance(theme, dict):
            if key in theme:
                return normalize_color(theme[key])
            palette = theme.get("palette", {})
            if isinstance(palette, dict) and key in palette:
                return normalize_color(palette[key])

    # 2. Resolve against canonical enterprise colors
    if key in CANONICAL_ENTERPRISE_COLORS:
        return CANONICAL_ENTERPRISE_COLORS[key]

    return "#000000"


def normalize_color(
    color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int], Any],
    theme: Optional[Any] = None,
) -> str:
    """
    Normalizes any color specification into a standard uppercase 6-character HEX string (#RRGGBB).
    Supports:
      - '#2563EB', '#fff', '2563EB'
      - (37, 99, 235) or (37, 99, 235, 255)
      - 'rgb(37, 99, 235)'
      - Semantic theme tokens: 'accent', 'danger', 'warning', 'primary', etc.
    """
    if isinstance(color, (tuple, list)):
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        return f"#{r:02X}{g:02X}{b:02X}"

    if not isinstance(color, str):
        return "#000000"

    color_str = color.strip()

    # Check for rgb(...) or rgba(...)
    rgb_match = re.match(r"rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", color_str, re.IGNORECASE)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return f"#{r:02X}{g:02X}{b:02X}"

    # Check for hex
    hex_str = color_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join([c * 2 for c in hex_str])
    elif len(hex_str) == 8:  # RRGGBBAA -> take RGB
        hex_str = hex_str[:6]

    if re.fullmatch(r"[0-9a-fA-F]{6}", hex_str):
        return f"#{hex_str.upper()}"

    # Check semantic brand / theme color
    resolved = resolve_brand_color(color_str, theme=theme)
    if resolved:
        return resolved

    return "#000000"


def recolor_svg(
    svg_content: str,
    color: Union[str, Tuple[int, ...]],
    stroke_width: Optional[float] = None,
    theme: Optional[Any] = None,
) -> str:
    """
    Dynamically recolors an SVG string with the specified Brand HEX/RGB color.
    Intelligently preserves outline vs fill geometry:
    - Stroke-based icons (e.g., Lucide, Feather, Tabler) maintain fill="none" and have their stroke colored.
    - Fill-based icons (e.g., Material Design) have their fill colored.
    - Replaces 'currentColor', prior baked hex colors, RGB strings, and uncolored elements.
    """
    hex_color = normalize_color(color, theme=theme)
    svg = svg_content.strip()

    # Determine if the icon is predominantly stroke-based or fill-based
    is_stroke_based = bool(
        'stroke="currentColor"' in svg
        or 'stroke=' in svg
        or 'stroke:' in svg
        or 'fill="none"' in svg
        or 'fill:none' in svg
    )

    # 1. Replace 'currentColor' occurrences with target brand hex
    svg = re.sub(r'stroke="currentColor"', f'stroke="{hex_color}"', svg, flags=re.IGNORECASE)
    svg = re.sub(r'fill="currentColor"', f'fill="{hex_color}"', svg, flags=re.IGNORECASE)
    svg = re.sub(r'stroke:\s*currentColor', f'stroke:{hex_color}', svg, flags=re.IGNORECASE)
    svg = re.sub(r'fill:\s*currentColor', f'fill:{hex_color}', svg, flags=re.IGNORECASE)

    if is_stroke_based:
        # Stroke-based icon: ensure stroke is tinted, preserve fill="none"
        def replace_stroke_attr(match: re.Match) -> str:
            quote = match.group(1)
            val = match.group(2).strip()
            if val.lower() in ("none", "transparent"):
                return f'stroke={quote}none{quote}'
            return f'stroke={quote}{hex_color}{quote}'

        # Replace stroke="..." and stroke='...'
        svg = re.sub(r'stroke=(["\'])([^"\']+)\1', replace_stroke_attr, svg, flags=re.IGNORECASE)

        # Replace stroke in inline CSS style="..."
        def replace_stroke_style(match: re.Match) -> str:
            val = match.group(1).strip()
            if val.lower() in ("none", "transparent"):
                return "stroke: none"
            return f"stroke: {hex_color}"

        svg = re.sub(r'stroke:\s*([^;"]+)', replace_stroke_style, svg, flags=re.IGNORECASE)

        # If root svg or path doesn't have stroke, inject stroke into <svg> tag
        if 'stroke=' not in svg and 'stroke:' not in svg:
            svg = re.sub(r'(<svg\b[^>]*)(>)', rf'\1 stroke="{hex_color}"\2', svg, count=1)
    else:
        # Fill-based icon: recolor fills that are not "none" or transparent
        def replace_fill_attr(match: re.Match) -> str:
            quote = match.group(1)
            val = match.group(2).strip()
            if val.lower() in ("none", "transparent"):
                return f'fill={quote}none{quote}'
            return f'fill={quote}{hex_color}{quote}'

        if 'fill=' in svg or 'fill:' in svg:
            svg = re.sub(r'fill=(["\'])([^"\']+)\1', replace_fill_attr, svg, flags=re.IGNORECASE)

            def replace_fill_style(match: re.Match) -> str:
                val = match.group(1).strip()
                if val.lower() in ("none", "transparent"):
                    return "fill: none"
                return f"fill: {hex_color}"

            svg = re.sub(r'fill:\s*([^;"]+)', replace_fill_style, svg, flags=re.IGNORECASE)
        else:
            # If no fill specified anywhere, inject fill into root <svg>
            svg = re.sub(r'(<svg\b[^>]*)(>)', rf'\1 fill="{hex_color}"\2', svg, count=1)

    # Optional stroke-width override
    if stroke_width is not None:
        if 'stroke-width=' in svg:
            svg = re.sub(r'stroke-width=(["\'])[^"\']+\1', f'stroke-width="{stroke_width}"', svg)
        else:
            svg = re.sub(r'(<svg\b[^>]*)(>)', rf'\1 stroke-width="{stroke_width}"\2', svg, count=1)

    return svg


def render_svg_to_png(
    svg_content: Union[str, bytes],
    output_path: Optional[Union[str, Path]] = None,
    size: Union[int, Tuple[int, int]] = 512,
    badge_bg: Optional[Union[str, Tuple[int, ...]]] = None,
    badge_radius: int = 0,
) -> Image.Image:
    """
    Renders SVG content to a crisp, high-resolution PIL RGBA Image and optionally saves to output_path.
    Uses resvg-py (fast native rust renderer) -> cairosvg -> PIL drawing fallback.
    """
    if isinstance(svg_content, bytes):
        svg_str = svg_content.decode("utf-8")
    else:
        svg_str = str(svg_content)

    width = size if isinstance(size, int) else size[0]
    height = size if isinstance(size, int) else size[1]

    img: Optional[Image.Image] = None

    # Priority 1: resvg-py (Native Rust engine, crisp vector rasterization)
    if _HAS_RESVG:
        try:
            png_bytes = resvg_py.svg_to_bytes(svg_str, width=width, height=height)
            img = Image.open(BytesIO(png_bytes)).convert("RGBA")
        except Exception as e:
            logger.debug(f"resvg_py failed: {e}")

    # Priority 2: cairosvg
    if img is None and _HAS_CAIROSVG:
        try:
            png_bytes = cairosvg.svg2png(
                bytestring=svg_str.encode("utf-8"),
                output_width=width,
                output_height=height,
            )
            img = Image.open(BytesIO(png_bytes)).convert("RGBA")
        except Exception as e:
            logger.debug(f"cairosvg failed: {e}")

    # Priority 3: Fallback basic shape render if rasterizers are unavailable
    if img is None:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        pad = int(width * 0.15)
        draw.ellipse([pad, pad, width - pad, height - pad], outline=(37, 99, 235, 255), width=int(width * 0.05))

    # Optional background badge container (e.g. rounded square or circle container)
    if badge_bg:
        bg_color_hex = normalize_color(badge_bg)
        # Parse hex to RGBA
        r = int(bg_color_hex[1:3], 16)
        g = int(bg_color_hex[3:5], 16)
        b = int(bg_color_hex[5:7], 16)
        bg_rgba = (r, g, b, 255)

        badge_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        from PIL import ImageDraw
        b_draw = ImageDraw.Draw(badge_img)
        if badge_radius > 0:
            b_draw.rounded_rectangle([0, 0, width, height], radius=badge_radius, fill=bg_rgba)
        else:
            b_draw.rectangle([0, 0, width, height], fill=bg_rgba)

        # Scale inner icon down to 60% and composite
        inner_w = int(width * 0.6)
        inner_h = int(height * 0.6)
        scaled_icon = img.resize((inner_w, inner_h), Image.Resampling.LANCZOS)
        offset = ((width - inner_w) // 2, (height - inner_h) // 2)
        badge_img.paste(scaled_icon, offset, mask=scaled_icon)
        img = badge_img

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_p), format="PNG")

    return img


class IconEngine:
    """
    Subsystem for searching, fetching, brand-tinting, and caching vector icons.
    """

    SUPPORTED_COLLECTIONS = [
        "lucide",
        "material-symbols",
        "mdi",
        "feather",
        "tabler",
        "ph",
        "carbon",
        "solar",
    ]

    def __init__(
        self,
        cache_dir: Union[str, Path] = "assets/icons",
        default_prefix: str = "lucide",
        session: Optional[requests.Session] = None,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_prefix = default_prefix
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "PPTMaking-IconEngine/1.0"})

    def _parse_icon_identifier(self, identifier: str) -> Tuple[str, str]:
        """
        Parses identifiers such as 'lucide:shield', 'mdi/account', or bare 'shield'.
        Returns (prefix, icon_name).
        """
        clean_id = identifier.strip().lower()
        if ":" in clean_id:
            prefix, name = clean_id.split(":", 1)
        elif "/" in clean_id:
            prefix, name = clean_id.split("/", 1)
        else:
            prefix = self.default_prefix
            name = clean_id
        return prefix.strip(), name.strip()

    def search(
        self,
        query: str,
        prefixes: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Searches Iconify API for icons matching the query.
        Returns a list of dicts with icon metadata.
        """
        if not prefixes:
            prefixes = [self.default_prefix, "material-symbols", "mdi", "feather", "tabler"]

        url = "https://api.iconify.design/search"
        params = {
            "query": query,
            "limit": limit,
            "prefixes": ",".join(prefixes),
        }

        try:
            resp = self.session.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                raw_icons = data.get("icons", [])
                results = []
                for item in raw_icons:
                    if ":" in item:
                        pfx, name = item.split(":", 1)
                    else:
                        pfx, name = self.default_prefix, item
                    results.append({
                        "id": f"{pfx}:{name}",
                        "prefix": pfx,
                        "name": name,
                        "title": f"{name.replace('-', ' ').title()} ({pfx})",
                    })
                return results[:limit]
        except Exception as e:
            logger.warning(f"Iconify search failed: {e}")

        # Fallback local matches
        query_key = query.lower().replace(" ", "-")
        fallback_results = []
        for key in FALLBACK_SVGS:
            if query_key in key or key in query_key:
                fallback_results.append({
                    "id": f"{self.default_prefix}:{key}",
                    "prefix": self.default_prefix,
                    "name": key,
                    "title": f"{key.title()} (Local Fallback)",
                })
        if not fallback_results:
            fallback_results.append({
                "id": f"{self.default_prefix}:default",
                "prefix": self.default_prefix,
                "name": "default",
                "title": "Default Indicator (Local Fallback)",
            })
        return fallback_results

    def fetch_svg(
        self,
        identifier: str,
        color: Optional[Union[str, Tuple[int, ...]]] = None,
        use_cache: bool = True,
        theme: Optional[Any] = None,
    ) -> str:
        """
        Fetches the raw SVG for an icon identifier. If color is provided, recolors it.
        Checks local disk cache in assets/icons/ before querying network.
        """
        prefix, name = self._parse_icon_identifier(identifier)
        cache_subdir = self.cache_dir / prefix
        cache_subdir.mkdir(parents=True, exist_ok=True)
        raw_cache_file = cache_subdir / f"{name}.svg"

        svg_content: Optional[str] = None

        # 1. Check local cache
        if use_cache and raw_cache_file.exists():
            try:
                svg_content = raw_cache_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.debug(f"Cache read error: {e}")

        # 2. Fetch from Iconify API
        if not svg_content:
            url = f"https://api.iconify.design/{prefix}:{name}.svg"
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200 and "<svg" in resp.text:
                    svg_content = resp.text
                    # Save raw SVG to cache
                    raw_cache_file.write_text(svg_content, encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to download icon '{identifier}': {e}")

        # 3. Fallback to built-in clean SVG if network fails
        if not svg_content:
            svg_content = FALLBACK_SVGS.get(name, FALLBACK_SVGS.get("default"))

        # 4. Apply dynamic brand recoloring if requested
        if color and svg_content:
            svg_content = recolor_svg(svg_content, color, theme=theme)

        return svg_content or FALLBACK_SVGS["default"]

    def get_icon(
        self,
        identifier: str,
        color: Optional[Union[str, Tuple[int, ...]]] = None,
        size: Union[int, Tuple[int, int]] = 512,
        output_path: Optional[Union[str, Path]] = None,
        badge_bg: Optional[Union[str, Tuple[int, ...]]] = None,
        badge_radius: int = 0,
        save_svg: bool = False,
        theme: Optional[Any] = None,
    ) -> Path:
        """
        End-to-end icon retrieval, dynamic tinting, and high-res PNG export.
        Returns the Path to the generated PNG file (or output_path).
        """
        prefix, name = self._parse_icon_identifier(identifier)
        svg = self.fetch_svg(identifier, color=color, theme=theme)

        # Default destination path if not supplied
        if output_path is None:
            color_suffix = f"_{normalize_color(color, theme=theme).lstrip('#')}" if color else ""
            out_file = self.cache_dir / prefix / f"{name}{color_suffix}.png"
        else:
            out_file = Path(output_path)

        out_file.parent.mkdir(parents=True, exist_ok=True)

        # Save SVG copy if requested
        if save_svg:
            svg_file = out_file.with_suffix(".svg")
            svg_file.write_text(svg, encoding="utf-8")

        render_svg_to_png(
            svg_content=svg,
            output_path=out_file,
            size=size,
            badge_bg=badge_bg,
            badge_radius=badge_radius,
        )

        return out_file


# Top-level functional API
_default_engine = IconEngine()

def search_icons(query: str, prefixes: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    return _default_engine.search(query=query, prefixes=prefixes, limit=limit)

def get_brand_icon(
    identifier: str,
    brand_color: Union[str, Tuple[int, ...]],
    size: int = 512,
    output_path: Optional[Union[str, Path]] = None,
    badge_bg: Optional[Union[str, Tuple[int, ...]]] = None,
    badge_radius: int = 0,
    save_svg: bool = True,
    theme: Optional[Any] = None,
) -> Path:
    return _default_engine.get_icon(
        identifier=identifier,
        color=brand_color,
        size=size,
        output_path=output_path,
        badge_bg=badge_bg,
        badge_radius=badge_radius,
        save_svg=save_svg,
        theme=theme,
    )
