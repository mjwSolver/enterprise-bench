"""
macOS Desktop Window & Browser Mockup Vector Widget
===================================================
Renders high-DPI raster macOS desktop browser windows using `frame_browser_mockup`
from the image engine, inserting a pixel-perfect framed picture into PPTX.
Avoids fragile imperative DrawingML vector shapes in favor of crisp anti-aliased PNGs.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image
from pptx.util import Inches

from src.ppt_engine.image_engine import frame_browser_mockup, ImageEngine


def _to_inches(val: Any) -> float:
    """Robustly converts Inches, Length, or float into float inches."""
    if hasattr(val, "inches"):
        return float(val.inches)
    if hasattr(val, "pt"):
        return float(val.pt) / 72.0
    if isinstance(val, (int, float)):
        if val > 500:
            return float(val) / 914400.0
        return float(val)
    return float(val)


def _resolve_mockup_image(image_path: Optional[Union[str, Path]], theme: Any) -> Union[Path, Image.Image]:
    """Finds existing screenshot image or generates procedural fallback."""
    if image_path:
        p = Path(image_path)
        if p.exists():
            return p
        # Check standard relative search paths
        search_dirs = [
            Path.cwd(),
            Path.cwd() / "assets" / "images" / "mockups",
            Path("/Users/marcelljw/VisualStudioCode/Snowflake/mii-snowflake-morulaivf-ai-usecases/assets/images/mockups"),
            Path("/Users/marcelljw/VisualStudioCode/enterprise-bench/assets/images/mockups"),
        ]
        for s_dir in search_dirs:
            candidate = s_dir / p.name
            if candidate.exists():
                return candidate

    # Standard candidate search
    fallback_candidates = [
        Path("/Users/marcelljw/VisualStudioCode/Snowflake/mii-snowflake-morulaivf-ai-usecases/assets/images/mockups/streamlit_treatment_copilot.png"),
        Path("/Users/marcelljw/VisualStudioCode/enterprise-bench/assets/images/mockups/streamlit_treatment_copilot.png"),
        Path("/Users/marcelljw/VisualStudioCode/Snowflake/mii-snowflake-morulaivf-ai-usecases/assets/images/mockups/magic_emr_cortex_copilot.png"),
        Path("/Users/marcelljw/VisualStudioCode/enterprise-bench/assets/images/mockups/magic_emr_cortex_copilot.png"),
    ]
    for c in fallback_candidates:
        if c.exists():
            return c

    # Fallback to procedural card
    engine = ImageEngine()
    primary = theme.get_hex("primary", default="#0284C7") if hasattr(theme, "get_hex") else "#0284C7"
    accent = theme.get_hex("accent", default="#38BDF8") if hasattr(theme, "get_hex") else "#38BDF8"
    return engine.generate_procedural_3d_card(
        title="Snowflake Cortex ML Platform",
        primary_color=primary,
        accent_color=accent,
    )


def render_macos_window(
    slide: Any,
    theme: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Renders an authentic macOS desktop browser window mockup as a high-DPI raster picture.

    Config schema:
      url: Optional[str] (e.g. 'https://morulaivf.snowflakecomputing.com/streamlit/uc2-copilot')
      title: Optional[str] (Window header title)
      theme_mode: Optional[str] ('light' or 'dark', default 'light')
      screenshot_path / image_path: Optional[str] (Path to interface capture PNG/JPG)
      telemetry_badges: Optional[List[str]] (opt-in badges, e.g. ['Snowflake Streamlit', 'PII De-Identified'])
      aspect_ratio: Optional[str] (e.g. '16:9', '16:10', '4:3', 'preserve')
      shadow: Optional[bool] (default True)
      dpi: Optional[int] (default 300)
    """
    left_in = _to_inches(left)
    top_in = _to_inches(top)
    w_in = _to_inches(width)
    h_in = _to_inches(height)

    url = str(config.get("url", "https://morulaivf.snowflakecomputing.com/streamlit/uc2-copilot"))
    title = config.get("title")
    theme_mode = str(config.get("theme_mode", "light")).lower()
    raw_img_path = config.get("screenshot_path") or config.get("image_path") or config.get("screenshot")
    src_img = _resolve_mockup_image(raw_img_path, theme)

    telemetry_badges = config.get("telemetry_badges")
    aspect_ratio = config.get("aspect_ratio", "16:9")
    target_dpi = int(config.get("dpi", config.get("target_dpi", 300)))
    shadow = bool(config.get("shadow", True))

    # Deterministic caching output path
    save_dir = Path("output/mockups")
    save_dir.mkdir(parents=True, exist_ok=True)
    img_sig = str(src_img) if isinstance(src_img, (str, Path)) else "procedural"
    h_str = hashlib.md5(f"{url}_{w_in:.2f}_{theme_mode}_{img_sig}_{telemetry_badges}".encode("utf-8")).hexdigest()[:10]
    out_png_path = save_dir / f"browser_mockup_{h_str}_{theme_mode}.png"

    # Generate framed mockup PNG via ImageEngine
    frame_browser_mockup(
        image_input=src_img,
        url=url,
        title=title,
        theme_mode=theme_mode,
        target_dpi=target_dpi,
        target_width_in=w_in,
        aspect_ratio=aspect_ratio,
        telemetry_badges=telemetry_badges,
        shadow=shadow,
        output_path=out_png_path,
    )

    # Insert framed picture into PowerPoint canvas
    pic = slide.shapes.add_picture(
        str(out_png_path),
        Inches(left_in),
        Inches(top_in),
        width=Inches(w_in),
    )

    # If rendered picture height exceeds allocated card height, rescale to fit
    actual_h_in = _to_inches(pic.height)
    if actual_h_in > h_in and h_in > 0.5:
        scale_factor = (h_in - 0.05) / actual_h_in
        pic.width = Inches(w_in * scale_factor)
        pic.height = Inches(actual_h_in * scale_factor)
        # Center horizontally within the allocated slot
        new_w_in = _to_inches(pic.width)
        pic.left = Inches(left_in + (w_in - new_w_in) / 2.0)

    return {
        "left": left_in,
        "top": top_in,
        "width": w_in,
        "height": h_in,
        "image_path": str(out_png_path),
    }
