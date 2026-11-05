"""
Deterministic Authentic Asset Fetcher & Brand Asset Ingestion Helper
===================================================================
Automates discovery, web inspection, schema parsing, and deterministic
download of authentic corporate logos and vector assets directly from
official brand domains. Prevents synthetic/mock asset hallucination.
"""

from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path
import re
from typing import Optional, Union
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree as ET

from PIL import Image

from src.core.config import ROOT_DIR

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class AssetFetcher:
    """Discovers and downloads authentic brand logos from web domains or URLs."""

    @staticmethod
    def fetch_from_url(url: str, dest_path: Union[str, Path]) -> Path:
        """
        Download an image from a direct URL with proper User-Agent.
        If SVG contains an embedded high-res base64 raster image, unpacks it to PNG.
        """
        dest = Path(dest_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        )

        with urllib.request.urlopen(req, timeout=10.0) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            raw_bytes = resp.read()

        # Handle embedded base64 PNG inside SVG
        if "svg" in content_type or url.lower().endswith(".svg") or raw_bytes.strip().startswith(b"<svg"):
            text = raw_bytes.decode("utf-8", errors="ignore")
            # Check for embedded data:image/png;base64
            match = re.search(r'data:image/(?:png|jpeg|webp);base64,([A-Za-z0-9+/=]+)', text)
            if match and dest.suffix.lower() == ".png":
                b64_data = match.group(1)
                img_data = base64.b64decode(b64_data)
                img = Image.open(io.BytesIO(img_data))
                img.save(dest, format="PNG")
                logger.info(f"Unpacked embedded base64 image from SVG to {dest} ({img.size})")
                return dest
            elif dest.suffix.lower() == ".svg":
                dest.write_bytes(raw_bytes)
                return dest
            else:
                # Target is PNG but source is raw vector SVG without embedded raster
                # Try saving as SVG first
                svg_path = dest.with_suffix(".svg")
                svg_path.write_bytes(raw_bytes)
                dest.write_bytes(raw_bytes)
                return dest

        # Verify image validity via Pillow
        try:
            img = Image.open(io.BytesIO(raw_bytes))
            if dest.suffix.lower() == ".png":
                img.save(dest, format="PNG")
            else:
                dest.write_bytes(raw_bytes)
        except Exception:
            dest.write_bytes(raw_bytes)

        logger.info(f"Successfully downloaded asset to {dest} ({len(raw_bytes):,} bytes)")
        return dest

    @classmethod
    def discover_and_fetch(
        cls,
        domain_or_url: str,
        dest_path: Optional[Union[str, Path]] = None,
        asset_name: Optional[str] = None,
        root_dir: Optional[Path] = None,
    ) -> Path:
        """
        Scrape/inspect domain homepage for official logo candidates:
        1. JSON-LD Schema.org (@type: Organization / Hospital / Corporation -> logo)
        2. OpenGraph meta (og:image)
        3. Header / Navbar img elements containing 'logo'
        Downloads the highest confidence asset and saves it locally.
        """
        root = root_dir or ROOT_DIR
        url = domain_or_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        parsed = urllib.parse.urlparse(url)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        domain_slug = parsed.netloc.replace("www.", "").split(".")[0]
        slug = asset_name or domain_slug

        final_dest = (
            Path(dest_path).resolve()
            if dest_path
            else (root / "assets" / "logos" / f"{slug}.png").resolve()
        )

        # Fetch homepage HTML
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            raise RuntimeError(f"Failed to access {url}: {e}")

        candidates: list[str] = []

        # 1. Parse JSON-LD Schema
        for match in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE):
            try:
                data = json.loads(match.group(1))
                candidates.extend(cls._extract_schema_logos(data))
            except Exception:
                continue

        # 2. Parse img tags with 'logo' in src, alt, class, or id
        img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html, re.IGNORECASE)
        for src in img_matches:
            src_lower = src.lower()
            if "logo" in src_lower and any(ext in src_lower for ext in (".svg", ".png", ".webp")):
                candidates.append(src)

        # 3. OpenGraph image fallback
        og_matches = re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for og in og_matches:
            if "logo" in og.lower():
                candidates.append(og)

        if not candidates:
            # Broader search for any logo image
            for src in img_matches:
                if any(ext in src.lower() for ext in (".svg", ".png")):
                    candidates.append(src)

        if not candidates:
            raise ValueError(f"No authentic logo elements found for {domain_or_url}")

        # Prioritize candidates: SVGs first, then high-res PNGs
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (
                0 if c.lower().endswith(".svg") else 1,
                0 if "logo" in c.lower() else 1,
                len(c),
            ),
        )

        best_url = urllib.parse.urljoin(base_origin, sorted_candidates[0])
        logger.info(f"Resolved authentic logo URL for {domain_or_url}: {best_url}")

        return cls.fetch_from_url(best_url, final_dest)

    @classmethod
    def _extract_schema_logos(cls, data: object) -> list[str]:
        """Recursively scan JSON-LD schema objects for logo URLs."""
        urls: list[str] = []
        if isinstance(data, dict):
            if "logo" in data:
                logo_val = data["logo"]
                if isinstance(logo_val, str):
                    urls.append(logo_val)
                elif isinstance(logo_val, dict) and "url" in logo_val:
                    urls.append(logo_val["url"])
            if "@graph" in data and isinstance(data["@graph"], list):
                for item in data["@graph"]:
                    urls.extend(cls._extract_schema_logos(item))
            for v in data.values():
                if isinstance(v, (dict, list)):
                    urls.extend(cls._extract_schema_logos(v))
        elif isinstance(data, list):
            for item in data:
                urls.extend(cls._extract_schema_logos(item))
        return urls
