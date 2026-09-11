"""
Stock Photo Fetcher, 3D Visual Assets, and Slide Image Post-Processing Pipeline.
Supports Wikimedia Commons, Unsplash, Curated 3D Assets, and Pillow Card Post-Processing.
"""

from __future__ import annotations

import os
import re
import math
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union, Tuple, List, Dict, Any
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .icon_engine import normalize_color

logger = logging.getLogger(__name__)


class ImageEngine:
    """
    Subsystem for stock photography lookup, 3D asset retrieval, image caching,
    and presentation-grade post-processing (aspect crop, rounded corners, hairline borders, drop shadows).
    """

    ASPECT_RATIOS = {
        "16:9": (16, 9),
        "4:3": (4, 3),
        "1:1": (1, 1),
        "3:2": (3, 2),
        "21:9": (21, 9),
    }

    def __init__(
        self,
        cache_dir: Union[str, Path] = "assets/images",
        unsplash_access_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.unsplash_access_key = unsplash_access_key or os.environ.get("UNSPLASH_ACCESS_KEY")
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "PPTMaking-ImageEngine/1.0 (Enterprise Slide Builder; contact@example.com)"
        })

    def search_wikimedia(
        self,
        query: str,
        limit: int = 5,
        thumb_width: int = 1280,
    ) -> List[Dict[str, Any]]:
        """
        Searches Wikimedia Commons for high-quality royalty-free images in public domain or CC.
        """
        wiki_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,  # File namespace
            "gsrlimit": limit * 2,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": thumb_width,
            "format": "json",
        }

        results = []
        try:
            resp = self.session.get(wiki_url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page in pages.items():
                    imageinfo = page.get("imageinfo", [])
                    if not imageinfo:
                        continue
                    info = imageinfo[0]
                    mime = info.get("mime", "").lower()
                    if mime not in ["image/jpeg", "image/png", "image/webp"]:
                        continue

                    # Pick thumburl if available for faster slide fitting, else original url
                    img_url = info.get("thumburl") or info.get("url")
                    title = page.get("title", "").replace("File:", "").split(".")[0].replace("_", " ")

                    ext = info.get("extmetadata", {})
                    author = ext.get("Artist", {}).get("value", "Wikimedia Commons")
                    license_name = ext.get("LicenseShortName", {}).get("value", "Public Domain / CC")

                    # Strip html tags from artist name if any
                    clean_author = re.sub(r"<[^>]+>", "", author).strip()

                    results.append({
                        "id": f"wiki_{page_id}",
                        "title": title,
                        "url": img_url,
                        "original_url": info.get("url"),
                        "width": info.get("width", 1920),
                        "height": info.get("height", 1080),
                        "source": "Wikimedia Commons",
                        "author": clean_author or "Wikimedia Contributor",
                        "license": license_name,
                    })

                    if len(results) >= limit:
                        break
        except Exception as e:
            logger.warning(f"Wikimedia search failed: {e}")

        return results

    def search_unsplash(
        self,
        query: str,
        limit: int = 5,
        orientation: str = "landscape",
    ) -> List[Dict[str, Any]]:
        """
        Searches Unsplash API if access key is available, else returns curated placeholder assets.
        """
        results = []
        if not self.unsplash_access_key:
            return results

        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {self.unsplash_access_key}"}
        params = {
            "query": query,
            "per_page": limit,
            "orientation": orientation,
        }

        try:
            resp = self.session.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    results.append({
                        "id": f"unsplash_{item.get('id')}",
                        "title": item.get("description") or item.get("alt_description") or query,
                        "url": item.get("urls", {}).get("regular"),
                        "original_url": item.get("urls", {}).get("full"),
                        "width": item.get("width", 1920),
                        "height": item.get("height", 1080),
                        "source": "Unsplash",
                        "author": item.get("user", {}).get("name", "Unsplash Photographer"),
                        "license": "Unsplash Free License",
                    })
        except Exception as e:
            logger.warning(f"Unsplash search failed: {e}")

        return results

    def search_stock(
        self,
        query: str,
        limit: int = 5,
        source: str = "all",
    ) -> List[Dict[str, Any]]:
        """
        Combined search across stock photography sources (Wikimedia Commons, Unsplash, 3D Assets).
        """
        combined = []

        if source in ["all", "unsplash"] and self.unsplash_access_key:
            combined.extend(self.search_unsplash(query, limit=limit))

        if source in ["all", "wikimedia"] and len(combined) < limit:
            wiki_items = self.search_wikimedia(query, limit=limit - len(combined))
            combined.extend(wiki_items)

        # If offline or no items returned, provide procedurally generated 3D visual fallback
        if not combined:
            combined.append(self.generate_3d_visual_metadata(query))

        return combined[:limit]

    def generate_3d_visual_metadata(self, theme: str = "technology") -> Dict[str, Any]:
        """
        Generates metadata for a local procedural 3D visual / modern gradient backdrop.
        """
        clean_name = theme.replace(" ", "_").lower()
        return {
            "id": f"procedural_3d_{clean_name}",
            "title": f"3D {theme.title()} Abstract Visual",
            "url": f"procedural://{clean_name}",
            "width": 1920,
            "height": 1080,
            "source": "Procedural 3D Visual Engine",
            "author": "PPTMaking Studio",
            "license": "MIT / Royalty Free",
        }

    def generate_procedural_3d_card(
        self,
        title: str = "Modern Abstract",
        primary_color: str = "#2563EB",
        accent_color: str = "#38BDF8",
        size: Tuple[int, int] = (1920, 1080),
        style: str = "gradient_orb",
    ) -> Image.Image:
        """
        Procedurally generates a modern 3D abstract visual / gradient mesh card using Pillow.
        Ideal for presentation backgrounds, 3D hero cards, and tech concept visuals.
        """
        w, h = size
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))  # Deep slate backdrop

        p_hex = normalize_color(primary_color)
        a_hex = normalize_color(accent_color)
        pr, pg, pb = int(p_hex[1:3], 16), int(p_hex[3:5], 16), int(p_hex[5:7], 16)
        ar, ag, ab = int(a_hex[1:3], 16), int(a_hex[3:5], 16), int(a_hex[5:7], 16)

        # Generate base gradient
        base_draw = ImageDraw.Draw(img)
        for y in range(h):
            ratio = y / h
            r = int(15 * (1 - ratio) + 30 * ratio)
            g = int(23 * (1 - ratio) + 41 * ratio)
            b = int(42 * (1 - ratio) + 59 * ratio)
            base_draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Layer 1: Primary glowing 3D Orb / Sphere
        orb_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        orb_draw = ImageDraw.Draw(orb_layer)

        cx, cy = int(w * 0.65), int(h * 0.45)
        max_rad = int(min(w, h) * 0.38)

        for radius in range(max_rad, 0, -8):
            factor = radius / max_rad
            # Color transition from primary to bright accent highlight
            curr_r = int(pr * factor + ar * (1 - factor))
            curr_g = int(pg * factor + ag * (1 - factor))
            curr_b = int(pb * factor + ab * (1 - factor))
            alpha = int(200 * (1 - factor ** 1.5))
            # Shift center upward for 3D sphere light reflection
            offset_x = cx - int((max_rad - radius) * 0.3)
            offset_y = cy - int((max_rad - radius) * 0.3)
            orb_draw.ellipse(
                [offset_x - radius, offset_y - radius, offset_x + radius, offset_y + radius],
                fill=(curr_r, curr_g, curr_b, alpha),
            )

        # Layer 2: Secondary glassmorphic accent sphere
        sec_cx, sec_cy = int(w * 0.35), int(h * 0.65)
        sec_rad = int(min(w, h) * 0.22)
        for radius in range(sec_rad, 0, -6):
            factor = radius / sec_rad
            alpha = int(150 * (1 - factor ** 1.2))
            orb_draw.ellipse(
                [sec_cx - radius, sec_cy - radius, sec_cx + radius, sec_cy + radius],
                fill=(ar, ag, ab, alpha),
            )

        # Composite and apply soft Gaussian glow
        blurred_glow = orb_layer.filter(ImageFilter.GaussianBlur(radius=30))
        img = Image.alpha_composite(img, blurred_glow)
        img = Image.alpha_composite(img, orb_layer)

        return img

    def download_image(
        self,
        url: str,
        output_path: Optional[Union[str, Path]] = None,
        use_cache: bool = True,
    ) -> Path:
        """
        Downloads an image from URL and caches it locally.
        If procedural URL is passed, generates the 3D visual.
        """
        # Handle procedural generator URL
        if url.startswith("procedural://"):
            theme_name = url.replace("procedural://", "")
            if output_path:
                out_p = Path(output_path)
            else:
                out_p = self.cache_dir / f"3d_{theme_name}.png"
            out_p.parent.mkdir(parents=True, exist_ok=True)
            card = self.generate_procedural_3d_card(title=theme_name)
            card.save(str(out_p), format="PNG")
            return out_p

        # Hash URL for unique caching
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:12]
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".webp" in url.lower():
            ext = ".webp"

        if output_path:
            out_file = Path(output_path)
        else:
            out_file = self.cache_dir / f"img_{url_hash}{ext}"

        out_file.parent.mkdir(parents=True, exist_ok=True)

        if use_cache and out_file.exists():
            return out_file

        try:
            resp = self.session.get(url, timeout=12)
            if resp.status_code == 200:
                out_file.write_bytes(resp.content)
                return out_file
        except Exception as e:
            logger.warning(f"Download failed for {url}: {e}")

        # Fallback procedural generation if download failed
        card = self.generate_procedural_3d_card(title="Stock Visual")
        card.save(str(out_file), format="PNG")
        return out_file


# -----------------------------------------------------------------------------
# Image Post-Processing Functions (Pillow)
# -----------------------------------------------------------------------------

def crop_aspect_ratio(
    image: Image.Image,
    aspect_ratio: Union[str, Tuple[float, float], float] = "16:9",
    focus: str = "center",
) -> Image.Image:
    """
    Crops an image cleanly to the desired aspect ratio without distortion or stretching.
    Supported aspect ratios: '16:9', '4:3', '1:1', '3:2', '21:9', or tuple (width_ratio, height_ratio).
    Focus options: 'center', 'top', 'bottom', 'left', 'right'.
    """
    img = image.convert("RGBA")
    w, h = img.size

    # Calculate target ratio float
    if isinstance(aspect_ratio, str):
        if aspect_ratio in ImageEngine.ASPECT_RATIOS:
            rw, rh = ImageEngine.ASPECT_RATIOS[aspect_ratio]
            target_ratio = rw / rh
        elif ":" in aspect_ratio:
            parts = aspect_ratio.split(":")
            target_ratio = float(parts[0]) / float(parts[1])
        else:
            target_ratio = float(aspect_ratio)
    elif isinstance(aspect_ratio, (tuple, list)):
        target_ratio = float(aspect_ratio[0]) / float(aspect_ratio[1])
    else:
        target_ratio = float(aspect_ratio)

    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 1e-4:
        return img

    if current_ratio > target_ratio:
        # Image is too wide -> crop horizontal sides
        new_w = int(round(h * target_ratio))
        if focus == "left":
            left = 0
        elif focus == "right":
            left = w - new_w
        else:  # center
            left = (w - new_w) // 2
        right = left + new_w
        top = 0
        bottom = h
    else:
        # Image is too tall -> crop top/bottom
        new_h = int(round(w / target_ratio))
        if focus == "top":
            top = 0
        elif focus == "bottom":
            top = h - new_h
        else:  # center
            top = (h - new_h) // 2
        bottom = top + new_h
        left = 0
        right = w

    return img.crop((left, top, right, bottom))


def apply_rounded_corners(
    image: Image.Image,
    radius: int = 24,
) -> Image.Image:
    """
    Applies smooth anti-aliased rounded corners to an image using a 4x supersampled alpha mask.
    """
    if radius <= 0:
        return image.convert("RGBA")

    img = image.convert("RGBA")
    w, h = img.size

    # 4x super-sampling for pristine edge anti-aliasing
    scale = 4
    mask_w, mask_h = w * scale, h * scale
    mask_radius = radius * scale

    mask = Image.new("L", (mask_w, mask_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [0, 0, mask_w, mask_h],
        radius=mask_radius,
        fill=255,
    )

    # Downsample mask with high-quality filter
    mask = mask.resize((w, h), Image.Resampling.LANCZOS)

    # Composite mask onto alpha channel
    r, g, b, a = img.split()
    final_alpha = ImageMath_eval_alpha(a, mask) if hasattr(Image, "ImageMath") else ImageOps.colorize(mask, (0, 0, 0), (255, 255, 255)).convert("L")
    img.putalpha(mask)

    return img


def apply_border(
    image: Image.Image,
    border_width: int = 2,
    border_color: Union[str, Tuple[int, ...]] = "#E2E8F0",
    radius: int = 24,
) -> Image.Image:
    """
    Draws a hairline or accent border around the image, accurately tracing the rounded corners.
    """
    if border_width <= 0:
        return image.convert("RGBA")

    img = image.convert("RGBA")
    w, h = img.size

    hex_color = normalize_color(border_color)
    br = int(hex_color[1:3], 16)
    bg = int(hex_color[3:5], 16)
    bb = int(hex_color[5:7], 16)
    b_rgba = (br, bg, bb, 255)

    # Super-sampled border drawing
    scale = 4
    bw = border_width * scale
    rad = radius * scale
    sw, sh = w * scale, h * scale

    border_overlay = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(border_overlay)

    # Offset rectangle by half the stroke width to keep stroke centered inside bounds
    half_bw = bw / 2.0
    rect_box = [half_bw, half_bw, sw - half_bw - 1, sh - half_bw - 1]

    if radius > 0:
        b_draw.rounded_rectangle(rect_box, radius=rad, outline=b_rgba, width=int(bw))
    else:
        b_draw.rectangle(rect_box, outline=b_rgba, width=int(bw))

    border_overlay = border_overlay.resize((w, h), Image.Resampling.LANCZOS)
    return Image.alpha_composite(img, border_overlay)


def apply_drop_shadow(
    image: Image.Image,
    offset: Tuple[int, int] = (0, 8),
    blur: int = 16,
    shadow_color: Union[str, Tuple[int, ...]] = (0, 0, 0, 50),
    padding: Optional[int] = None,
) -> Image.Image:
    """
    Adds a modern elevated drop shadow behind the image (Figma/Tailwind UI card style).
    Expands the canvas with transparent padding to accommodate blur and offset.
    """
    img = image.convert("RGBA")
    w, h = img.size

    # Calculate padding needed for blur and offset
    ox, oy = offset
    pad = padding if padding is not None else int(blur * 2 + max(abs(ox), abs(oy)) + 8)

    canvas_w = w + pad * 2
    canvas_h = h + pad * 2

    # Extract image alpha mask for shadow shape
    _, _, _, alpha_mask = img.split()

    # Shadow layer
    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    if isinstance(shadow_color, str):
        sh_hex = normalize_color(shadow_color)
        sr = int(sh_hex[1:3], 16)
        sg = int(sh_hex[3:5], 16)
        sb = int(sh_hex[5:7], 16)
        sa = 60
    elif len(shadow_color) == 4:
        sr, sg, sb, sa = shadow_color
    else:
        sr, sg, sb = shadow_color[:3]
        sa = 60

    # Paste colored silhouette with offset
    colored_silhouette = Image.new("RGBA", (w, h), (sr, sg, sb, sa))
    shadow_layer.paste(colored_silhouette, (pad + ox, pad + oy), mask=alpha_mask)

    # Blur shadow
    if blur > 0:
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur))

    # Paste original image onto shadow
    shadow_layer.paste(img, (pad, pad), mask=img)

    return shadow_layer


def frame_slide_image(
    image_input: Union[Image.Image, str, Path],
    aspect_ratio: Union[str, Tuple[float, float]] = "16:9",
    corner_radius: int = 24,
    border_width: int = 1,
    border_color: str = "#E2E8F0",
    shadow: bool = True,
    shadow_blur: int = 14,
    shadow_offset: Tuple[int, int] = (0, 6),
    output_path: Optional[Union[str, Path]] = None,
) -> Image.Image:
    """
    Comprehensive presentation card styling pipeline:
    1. Loads / processes input image.
    2. Crops to presentation aspect ratio (e.g. 16:9, 4:3, 1:1).
    3. Applies smooth anti-aliased rounded corners.
    4. Adds hairline/brand border.
    5. Adds subtle drop shadow for depth.
    6. Saves to output_path if provided.
    """
    if isinstance(image_input, (str, Path)):
        img = Image.open(str(image_input))
    else:
        img = image_input

    # Step 1: Aspect Ratio Crop
    cropped = crop_aspect_ratio(img, aspect_ratio=aspect_ratio)

    # Step 2: Rounded Corners
    rounded = apply_rounded_corners(cropped, radius=corner_radius)

    # Step 3: Hairline / Accent Border
    bordered = apply_border(
        rounded,
        border_width=border_width,
        border_color=border_color,
        radius=corner_radius,
    )

    # Step 4: Drop Shadow
    if shadow:
        final_img = apply_drop_shadow(
            bordered,
            offset=shadow_offset,
            blur=shadow_blur,
        )
    else:
        final_img = bordered

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        final_img.save(str(out_p), format="PNG")

    return final_img


# Module-level convenience functions
_default_image_engine = ImageEngine()

def search_stock_photos(query: str, limit: int = 5, source: str = "all") -> List[Dict[str, Any]]:
    return _default_image_engine.search_stock(query=query, limit=limit, source=source)

def download_image(url: str, output_path: Optional[Union[str, Path]] = None) -> Path:
    return _default_image_engine.download_image(url=url, output_path=output_path)
