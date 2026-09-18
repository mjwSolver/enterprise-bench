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
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, Tuple, List, Dict, Any
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageFont

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
    shadow: bool = False,
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


def replace_slide_picture_shape(
    slide: Any,
    shape: Any,
    new_image_path: Union[str, Path],
    preserve_aspect_ratio: bool = True,
) -> bool:
    """
    Substitutes the image in a single picture shape with a new image.
    Preserves bounding box bounds and scales proportionally if preserve_aspect_ratio is True.
    """
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
        return False

    new_img_p = Path(new_image_path)
    if not new_img_p.exists():
        raise FileNotFoundError(f"Replacement image not found: {new_image_path}")

    # Embed image in slide relationships
    _, rId = slide.part.get_or_add_image_part(str(new_img_p))

    # Update blip relationship embed
    blips = shape._element.xpath(".//a:blip")
    if not blips:
        return False

    blips[0].set("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed", rId)

    if preserve_aspect_ratio:
        orig_w, orig_h = shape.width, shape.height
        orig_left, orig_top = shape.left, shape.top

        with Image.open(str(new_img_p)) as img:
            img_w, img_h = img.size

        scale = min(orig_w / img_w, orig_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        shape.left = orig_left + (orig_w - new_w) // 2
        shape.top = orig_top + (orig_h - new_h) // 2
        shape.width = new_w
        shape.height = new_h

    return True


def substitute_presentation_images(
    prs_or_path: Union[str, Path, Any],
    new_image_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    slide_index: Optional[int] = None,
    preserve_aspect_ratio: bool = True,
) -> Tuple[int, Path]:
    """
    Substitutes all (or targeted slide's) preexisting images in a PowerPoint presentation
    with a new image, saving the result to output_path.
    """
    import pptx
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    if isinstance(prs_or_path, (str, Path)):
        in_path = Path(prs_or_path)
        prs = pptx.Presentation(str(in_path))
    else:
        prs = prs_or_path
        in_path = Path("presentation.pptx")

    if slide_index is not None:
        if slide_index < 1 or slide_index > len(prs.slides):
            raise IndexError(f"Slide index {slide_index} out of bounds (1..{len(prs.slides)})")
        target_slides = [prs.slides[slide_index - 1]]
    else:
        target_slides = list(prs.slides)

    count = 0
    for slide in target_slides:
        def _walk_shapes(shapes):
            nonlocal count
            for shape in shapes:
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    if replace_slide_picture_shape(slide, shape, new_image_path, preserve_aspect_ratio):
                        count += 1
                elif shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                    _walk_shapes(shape.shapes)

        _walk_shapes(slide.shapes)

    if output_path is None:
        out_path = in_path.parent / f"{in_path.stem}_substituted{in_path.suffix}"
    else:
        out_path = Path(output_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))

    return count, out_path


# -----------------------------------------------------------------------------
# Browser Mockup & Window Chrome Container Subsystem
# -----------------------------------------------------------------------------

def _get_system_font(
    font_name: Optional[str] = None,
    size_px: int = 16,
    bold: bool = False,
    mono: bool = False,
) -> ImageFont.ImageFont:
    """Locate crisp system font on macOS/Linux/Windows with sensible fallbacks."""
    system = platform.system()
    candidates: List[str] = []

    if font_name and os.path.exists(font_name):
        candidates.append(font_name)

    if system == "Darwin":
        if mono:
            candidates.extend([
                "/System/Library/Fonts/Menlo.ttc",
                "/System/Library/Fonts/SFMono-Regular.otf",
                "/System/Library/Fonts/Supplemental/Courier New.ttf",
            ])
        elif bold:
            candidates.extend([
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/SFCompact.ttf",
                "/System/Library/Fonts/SFNS.ttf",
            ])
        else:
            candidates.extend([
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/SFCompact.ttf",
                "/System/Library/Fonts/SFNS.ttf",
            ])
    elif system == "Linux":
        if mono:
            candidates.extend([
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            ])
        elif bold:
            candidates.extend([
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            ])
        else:
            candidates.extend([
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ])
    elif system == "Windows":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        if mono:
            candidates.extend([
                os.path.join(windir, "Fonts", "consola.ttf"),
                os.path.join(windir, "Fonts", "cour.ttf"),
            ])
        elif bold:
            candidates.extend([
                os.path.join(windir, "Fonts", "arialbd.ttf"),
                os.path.join(windir, "Fonts", "segoeuib.ttf"),
            ])
        else:
            candidates.extend([
                os.path.join(windir, "Fonts", "arial.ttf"),
                os.path.join(windir, "Fonts", "segoeui.ttf"),
            ])

    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                if font_path.endswith(".ttc"):
                    return ImageFont.truetype(font_path, size_px, index=1 if bold else 0)
                return ImageFont.truetype(font_path, size_px)
            except Exception:
                continue

    try:
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def _hex_to_rgba(hex_color: Union[str, Tuple[int, ...]], alpha: int = 255) -> Tuple[int, int, int, int]:
    """Converts hex or rgb(a) color into an RGBA 4-tuple."""
    if isinstance(hex_color, (tuple, list)):
        if len(hex_color) == 4:
            return (int(hex_color[0]), int(hex_color[1]), int(hex_color[2]), int(hex_color[3]))
        return (int(hex_color[0]), int(hex_color[1]), int(hex_color[2]), alpha)
    norm = normalize_color(hex_color)
    r = int(norm[1:3], 16)
    g = int(norm[3:5], 16)
    b = int(norm[5:7], 16)
    return (r, g, b, alpha)


@dataclass
class TelemetryBadge:
    """Bottom-anchored telemetry badge data container."""
    label: str
    icon: Optional[str] = None
    status: str = "neutral"

    @classmethod
    def from_raw(cls, item: Union[str, Dict[str, Any], TelemetryBadge]) -> TelemetryBadge:
        """Parses telemetry badge from string, dict, or existing instance."""
        if isinstance(item, cls):
            return item
        if isinstance(item, dict):
            return cls(
                label=item.get("label", item.get("text", "")),
                icon=item.get("icon"),
                status=item.get("status", "neutral"),
            )
        raw_str = str(item).strip()
        parts = raw_str.split(" ", 1)
        if len(parts) == 2 and any(ord(char) > 0x2000 for char in parts[0]):
            return cls(label=parts[1].strip(), icon=parts[0].strip())
        return cls(label=raw_str)


@dataclass
class BrowserMockupConfig:
    """Configuration options for high-fidelity macOS browser mockup container."""
    url: str = "https://finance.snowflakecomputing.com/streamlit/app"
    title: Optional[str] = None
    theme_mode: str = "light"  # "light" or "dark"
    header_fill: Optional[str] = None
    header_height_in: float = 0.32
    traffic_lights: bool = True
    traffic_light_diameter_in: float = 0.10
    traffic_light_colors: Tuple[str, str, str] = ("#EF4444", "#F59E0B", "#10B981")
    traffic_light_borders: Tuple[str, str, str] = ("#DC2626", "#D97706", "#059669")
    url_pill: bool = True
    url_pill_height_in: float = 0.20
    url_pill_fill: Optional[str] = None
    url_pill_border: Optional[str] = None
    secure_badge: bool = True
    target_dpi: int = 300  # Strictly enforced >= 200 DPI
    target_width_in: float = 8.0
    aspect_ratio: Optional[str] = "16:9"  # "16:9", "16:10", "4:3", None (preserve)
    corner_radius: int = 16
    hairline_border: bool = True
    border_color: Optional[str] = None
    border_width: int = 1
    shadow: bool = True
    shadow_blur: int = 24
    shadow_offset: Tuple[int, int] = (0, 10)
    shadow_color: Union[str, Tuple[int, int, int, int]] = (15, 23, 42, 45)
    telemetry_badges: Optional[List[Union[str, Dict[str, Any], TelemetryBadge]]] = None
    telemetry_footer_height_in: float = 0.32
    telemetry_fill: Optional[str] = None
    autocrop_taskbar: bool = False


class BrowserMockupContainer:
    """
    Subsystem for framing raw enterprise UI screenshots inside a high-DPI
    macOS-style desktop browser container with traffic lights, URL pill,
    optional telemetry badges, hairline border, and ambient shadow.
    """

    def __init__(
        self,
        config: Optional[BrowserMockupConfig] = None,
        **kwargs: Any,
    ):
        if config is not None:
            self.config = config
        else:
            self.config = BrowserMockupConfig(**kwargs)

        # Enforce minimum 200 DPI target per architecture standard
        if self.config.target_dpi < 200:
            logger.info(f"Elevating target DPI from {self.config.target_dpi} to 200 (mandatory floor)")
            self.config.target_dpi = 200

    def _render_header(self, content_w: int, dpi: int) -> Image.Image:
        """Renders macOS slate header bar with traffic lights and centered URL pill."""
        is_dark = self.config.theme_mode.lower() == "dark"
        hdr_fill_hex = self.config.header_fill or ("#1E293B" if is_dark else "#F1F5F9")
        pill_fill_hex = self.config.url_pill_fill or ("#0F172A" if is_dark else "#FFFFFF")
        pill_border_hex = self.config.url_pill_border or ("#334155" if is_dark else "#CBD5E1")
        pill_text_hex = "#94A3B8" if is_dark else "#64748B"
        divider_hex = "#334155" if is_dark else "#E2E8F0"

        header_h = max(24, int(round(self.config.header_height_in * dpi)))
        header_img = Image.new("RGBA", (content_w, header_h), _hex_to_rgba(hdr_fill_hex))
        draw = ImageDraw.Draw(header_img)

        # 1. Traffic light control dots
        dot_d = max(6, int(round(self.config.traffic_light_diameter_in * dpi)))
        dot_gap = max(4, int(round(0.04 * dpi)))
        dot_x0 = max(14, int(round(0.14 * dpi)))
        dot_y0 = (header_h - dot_d) // 2

        if self.config.traffic_lights:
            for i, (fill_col, border_col) in enumerate(zip(self.config.traffic_light_colors, self.config.traffic_light_borders)):
                cx = dot_x0 + i * (dot_d + dot_gap)
                draw.ellipse(
                    [cx, dot_y0, cx + dot_d, dot_y0 + dot_d],
                    fill=_hex_to_rgba(fill_col),
                    outline=_hex_to_rgba(border_col),
                    width=1,
                )

        # 2. Centered URL / Title Pill
        if self.config.url_pill:
            pill_h = max(16, int(round(self.config.url_pill_height_in * dpi)))
            min_margin = dot_x0 + 3 * dot_d + 3 * dot_gap + int(round(0.12 * dpi))
            max_pill_w = content_w - 2 * min_margin
            pill_w = max(int(round(content_w * 0.40)), min(int(round(content_w * 0.58)), max_pill_w))
            pill_x0 = (content_w - pill_w) // 2
            pill_y0 = (header_h - pill_h) // 2
            pill_rad = pill_h // 2

            draw.rounded_rectangle(
                [pill_x0, pill_y0, pill_x0 + pill_w, pill_y0 + pill_h],
                radius=pill_rad,
                fill=_hex_to_rgba(pill_fill_hex),
                outline=_hex_to_rgba(pill_border_hex),
                width=max(1, int(round(dpi / 300.0))),
            )

            # Security lock glyph and URL string inside pill
            font_sz = max(9, int(round(pill_h * 0.42)))
            font = _get_system_font(size_px=font_sz, mono=True)

            cur_x = pill_x0 + int(round(pill_h * 0.38))
            if self.config.secure_badge:
                lock_w = max(7, int(round(font_sz * 0.65)))
                lock_h = max(9, int(round(font_sz * 0.85)))
                lock_x = cur_x
                lock_y = (header_h - lock_h) // 2
                lock_col = _hex_to_rgba("#10B981" if not is_dark else "#34D399")
                # Lock shackle
                draw.arc(
                    [lock_x + 2, lock_y, lock_x + lock_w - 2, lock_y + int(lock_h * 0.62)],
                    start=180,
                    end=0,
                    fill=lock_col,
                    width=max(1, int(round(dpi / 300.0))),
                )
                # Lock body
                draw.rounded_rectangle(
                    [lock_x, lock_y + int(lock_h * 0.44), lock_x + lock_w, lock_y + lock_h],
                    radius=2,
                    fill=lock_col,
                )
                cur_x += lock_w + int(round(0.06 * dpi))

            display_url = self.config.url or self.config.title or "https://enterprise.internal"
            max_text_w = (pill_x0 + pill_w - int(round(pill_h * 0.38))) - cur_x

            # Truncate text with ellipsis if it exceeds pill width
            bbox = font.getbbox(display_url)
            txt_w = bbox[2] - bbox[0]
            txt_h = bbox[3] - bbox[1]

            if txt_w > max_text_w:
                truncated = display_url
                while truncated and (font.getbbox(truncated + "…")[2] - font.getbbox(truncated + "…")[0]) > max_text_w:
                    truncated = truncated[:-1]
                display_url = truncated + "…"
                bbox = font.getbbox(display_url)
                txt_w = bbox[2] - bbox[0]
                txt_h = bbox[3] - bbox[1]

            text_y = pill_y0 + (pill_h - txt_h) // 2 - bbox[1]
            draw.text((cur_x, text_y), display_url, font=font, fill=_hex_to_rgba(pill_text_hex))

        # Bottom subtle divider line
        draw.line([(0, header_h - 1), (content_w, header_h - 1)], fill=_hex_to_rgba(divider_hex), width=1)
        return header_img

    def _render_footer(self, content_w: int, dpi: int) -> Optional[Image.Image]:
        """Renders bottom-anchored telemetry bar with status pills and metadata."""
        if not self.config.telemetry_badges:
            return None

        is_dark = self.config.theme_mode.lower() == "dark"
        footer_fill_hex = self.config.telemetry_fill or ("#0F172A" if is_dark else "#F8FAFC")
        pill_fill_hex = "#1E293B" if is_dark else "#FFFFFF"
        pill_border_hex = "#334155" if is_dark else "#E2E8F0"
        text_hex = "#E2E8F0" if is_dark else "#334155"
        divider_hex = "#334155" if is_dark else "#E2E8F0"

        footer_h = max(26, int(round(self.config.telemetry_footer_height_in * dpi)))
        footer_img = Image.new("RGBA", (content_w, footer_h), _hex_to_rgba(footer_fill_hex))
        draw = ImageDraw.Draw(footer_img)

        # Top hairline divider
        draw.line([(0, 0), (content_w, 0)], fill=_hex_to_rgba(divider_hex), width=1)

        badges = [TelemetryBadge.from_raw(b) for b in self.config.telemetry_badges]
        if not badges:
            return footer_img

        badge_h = max(18, int(round(footer_h * 0.62)))
        badge_y0 = (footer_h - badge_h) // 2
        badge_font_sz = max(9, int(round(badge_h * 0.44)))
        font = _get_system_font(size_px=badge_font_sz, bold=False)

        # Pre-calculate pill widths
        pill_data: List[Tuple[str, int, int]] = []
        pill_gap = int(round(0.08 * dpi))
        h_pad = int(round(badge_h * 0.45))

        for b in badges:
            text = f"{b.icon} {b.label}" if b.icon else b.label
            bbox = font.getbbox(text)
            tw = bbox[2] - bbox[0]
            pw = tw + h_pad * 2
            pill_data.append((text, pw, tw))

        total_pills_w = sum(p[1] for p in pill_data) + pill_gap * (len(pill_data) - 1)
        start_x = max(int(round(0.12 * dpi)), (content_w - total_pills_w) // 2)

        cur_x = start_x
        for text, pw, tw in pill_data:
            draw.rounded_rectangle(
                [cur_x, badge_y0, cur_x + pw, badge_y0 + badge_h],
                radius=badge_h // 2,
                fill=_hex_to_rgba(pill_fill_hex),
                outline=_hex_to_rgba(pill_border_hex),
                width=max(1, int(round(dpi / 300.0))),
            )
            bbox = font.getbbox(text)
            txt_h = bbox[3] - bbox[1]
            tx = cur_x + h_pad
            ty = badge_y0 + (badge_h - txt_h) // 2 - bbox[1]
            draw.text((tx, ty), text, font=font, fill=_hex_to_rgba(text_hex))
            cur_x += pw + pill_gap

        return footer_img

    def _process_content(self, image_input: Union[Image.Image, str, Path], content_w: int) -> Image.Image:
        """Scales and crops screenshot using high-DPI Lanczos resampling."""
        if isinstance(image_input, (str, Path)):
            img = Image.open(str(image_input)).convert("RGBA")
        else:
            img = image_input.convert("RGBA")

        # Autocrop bottom OS taskbar if enabled
        if self.config.autocrop_taskbar:
            w, h = img.size
            taskbar_crop = int(round(h * 0.045))
            if taskbar_crop > 0 and h > taskbar_crop:
                img = img.crop((0, 0, w, h - taskbar_crop))

        # Crop to target aspect ratio if specified
        ar = self.config.aspect_ratio
        if ar and str(ar).lower() not in ("none", "preserve", "original", ""):
            cropped = crop_aspect_ratio(img, aspect_ratio=ar)
        else:
            cropped = img

        # Enforce high-DPI Lanczos resampling to match target width
        orig_w, orig_h = cropped.size
        scale = content_w / float(orig_w)
        content_h = max(1, int(round(orig_h * scale)))

        return cropped.resize((content_w, content_h), Image.Resampling.LANCZOS)

    def frame(
        self,
        image_input: Union[Image.Image, str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Image.Image:
        """
        Frames the provided interface screenshot inside the window container:
        1. Resamples screenshot with high-DPI Lanczos scaling (>= 200 DPI).
        2. Renders macOS window chrome with traffic lights and centered URL pill.
        3. Renders bottom telemetry badges if configured.
        4. Smoothly composites into a single window canvas with rounded corners.
        5. Applies hairline border and ambient drop shadow.
        6. Saves to output_path if provided.
        """
        dpi = max(200, self.config.target_dpi)
        content_w = int(round(self.config.target_width_in * dpi))

        # 1. Prepare sub-components
        header_img = self._render_header(content_w=content_w, dpi=dpi)
        content_img = self._process_content(image_input=image_input, content_w=content_w)
        footer_img = self._render_footer(content_w=content_w, dpi=dpi)

        header_h = header_img.height
        content_h = content_img.height
        footer_h = footer_img.height if footer_img else 0
        total_h = header_h + content_h + footer_h

        # 2. Window composite assembly
        window = Image.new("RGBA", (content_w, total_h), (0, 0, 0, 0))
        window.paste(header_img, (0, 0))
        window.paste(content_img, (0, header_h))
        if footer_img:
            window.paste(footer_img, (0, header_h + content_h))

        # 3. Outer window rounded corners (4x supersampled mask)
        rad = max(0, int(round(self.config.corner_radius * (dpi / 300.0))))
        if rad > 0:
            window = apply_rounded_corners(window, radius=rad)

        # 4. Subtle hairline border
        if self.config.hairline_border:
            b_color = self.config.border_color or ("#CBD5E1" if self.config.theme_mode == "light" else "#334155")
            b_width = max(1, int(round(self.config.border_width * (dpi / 300.0))))
            window = apply_border(window, border_width=b_width, border_color=b_color, radius=rad)

        # 5. Ambient drop shadow
        if self.config.shadow:
            s_blur = int(round(self.config.shadow_blur * (dpi / 300.0)))
            s_ox = int(round(self.config.shadow_offset[0] * (dpi / 300.0)))
            s_oy = int(round(self.config.shadow_offset[1] * (dpi / 300.0)))
            final_img = apply_drop_shadow(
                window,
                offset=(s_ox, s_oy),
                blur=s_blur,
                shadow_color=self.config.shadow_color,
            )
        else:
            final_img = window

        # 6. Save to disk if requested
        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            final_img.save(str(out_p), format="PNG", dpi=(dpi, dpi))

        return final_img


def frame_browser_mockup(
    image_input: Union[Image.Image, str, Path],
    url: str = "https://finance.snowflakecomputing.com/streamlit/app",
    title: Optional[str] = None,
    theme_mode: str = "light",
    target_dpi: int = 300,
    target_width_in: float = 8.0,
    aspect_ratio: Optional[str] = "16:9",
    corner_radius: int = 16,
    hairline_border: bool = True,
    border_color: Optional[str] = None,
    border_width: int = 1,
    shadow: bool = True,
    shadow_blur: int = 24,
    shadow_offset: Tuple[int, int] = (0, 10),
    telemetry_badges: Optional[List[Union[str, Dict[str, Any], TelemetryBadge]]] = None,
    autocrop_taskbar: bool = False,
    output_path: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> Image.Image:
    """
    Presentation-grade convenience function for framing interface captures in a
    macOS browser container.
    """
    config = BrowserMockupConfig(
        url=url,
        title=title,
        theme_mode=theme_mode,
        target_dpi=target_dpi,
        target_width_in=target_width_in,
        aspect_ratio=aspect_ratio,
        corner_radius=corner_radius,
        hairline_border=hairline_border,
        border_color=border_color,
        border_width=border_width,
        shadow=shadow,
        shadow_blur=shadow_blur,
        shadow_offset=shadow_offset,
        telemetry_badges=telemetry_badges,
        autocrop_taskbar=autocrop_taskbar,
        **kwargs,
    )
    container = BrowserMockupContainer(config=config)
    return container.frame(image_input=image_input, output_path=output_path)


