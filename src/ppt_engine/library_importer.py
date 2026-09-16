"""
Draw.io Library Importer and Central Icon Registry Subsystem
===========================================================
Provides tools to:
1. Parse and decode Draw.io `<mxlibrary>` XML files (deflate, base64, URL-encoded, or raw JSON).
2. Extract standalone vector SVGs (and raster PNG fallbacks) for each component stencil.
3. Maintain a centralized icon catalog and manifest (`assets/icons/manifest.json`).
4. Resolve icons by key, alias, vendor, or path for both headless slide compilation and Draw.io XML export.
"""

from __future__ import annotations

import base64
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Root directory of the repository
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ASSETS_DIR = _REPO_ROOT / "assets"
_LOGOS_DIR = _ASSETS_DIR / "logos"
_ICONS_DIR = _ASSETS_DIR / "icons"
_MANIFEST_FILE = _ICONS_DIR / "manifest.json"


# ============================================================================
# 1. Draw.io <mxlibrary> Decoder & Extractor
# ============================================================================

class MxLibraryDecoder:
    """Decodes Draw.io `<mxlibrary>` packages into structured shape representations."""

    @staticmethod
    def decode_library(content_or_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parses a Draw.io library file or raw XML string.
        Handles:
        - Plain JSON inside `<mxlibrary>[...]</mxlibrary>`
        - URL-encoded JSON
        - Base64-encoded, zlib-deflated JSON payloads
        """
        raw_text: str
        p = Path(content_or_path) if isinstance(content_or_path, (str, Path)) else None
        if p and p.exists() and p.is_file():
            raw_text = p.read_text(encoding="utf-8").strip()
        else:
            raw_text = str(content_or_path).strip()

        # Extract content between <mxlibrary>...</mxlibrary> if present
        if "<mxlibrary>" in raw_text and "</mxlibrary>" in raw_text:
            start = raw_text.find("<mxlibrary>") + len("<mxlibrary>")
            end = raw_text.find("</mxlibrary>")
            payload = raw_text[start:end].strip()
        elif "<mxlibrary>" in raw_text:
            m = re.search(r"<mxlibrary>(.*?)</mxlibrary>", raw_text, re.DOTALL)
            payload = m.group(1).strip() if m else raw_text
        else:
            payload = raw_text

        # Attempt 1: Direct JSON parse
        try:
            return json.loads(payload)
        except Exception:
            pass

        # Attempt 2: URL-decoded JSON
        try:
            unquoted = urllib.parse.unquote(payload)
            if unquoted.startswith("[") and unquoted.endswith("]"):
                return json.loads(unquoted)
        except Exception:
            pass

        # Attempt 3: Base64 decode + zlib inflate (Draw.io standard compressed payload)
        try:
            b64_decoded = base64.b64decode(payload)
            try:
                # Raw deflate (wbits=-15)
                decompressed = zlib.decompress(b64_decoded, -15)
            except Exception:
                decompressed = zlib.decompress(b64_decoded)

            text = decompressed.decode("utf-8")
            unquoted = urllib.parse.unquote(text)
            return json.loads(unquoted)
        except Exception:
            pass

        raise ValueError("Failed to decode <mxlibrary> content: unsupported or corrupted encoding.")

    @staticmethod
    def extract_svg_or_image(shape_item: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """
        Extracts vector SVG text or raster Base64 data from a shape item.
        Returns: (data_string, "svg" | "png" | "unknown")
        """
        xml_content = shape_item.get("xml", "")
        if not xml_content:
            return None, "unknown"

        # Check for data:image/svg+xml;base64,... or data:image/svg+xml,...
        m_svg_b64 = re.search(r"image=data:image/svg\+xml(?:;base64)?,([A-Za-z0-9+/=]+)", xml_content)
        if m_svg_b64:
            try:
                raw_svg = base64.b64decode(m_svg_b64.group(1)).decode("utf-8")
                return raw_svg, "svg"
            except Exception:
                pass

        # Check for data:image/svg+xml,<url_encoded_svg>
        m_svg_url = re.search(r"image=data:image/svg\+xml,([^;\"'\s]+)", xml_content)
        if m_svg_url:
            try:
                raw_svg = urllib.parse.unquote(m_svg_url.group(1))
                return raw_svg, "svg"
            except Exception:
                pass

        # Check for data:image/png;base64,... or data:image/png,...
        m_png_b64 = re.search(r"image=data:image/png(?:;base64)?,([A-Za-z0-9+/=]+)", xml_content)
        if m_png_b64:
            return m_png_b64.group(1), "png"

        # Check for raw <svg>...</svg> embedded directly in XML
        if "<svg" in xml_content and "</svg>" in xml_content:
            s_idx = xml_content.find("<svg")
            e_idx = xml_content.find("</svg>") + len("</svg>")
            return xml_content[s_idx:e_idx], "svg"

        # Check for Draw.io custom <shape> stencil
        if "<shape" in xml_content and "</shape>" in xml_content:
            s_idx = xml_content.find("<shape")
            e_idx = xml_content.find("</shape>") + len("</shape>")
            stencil_xml = xml_content[s_idx:e_idx]
            svg_converted = MxLibraryDecoder._stencil_to_svg(stencil_xml, shape_item.get("w", 48), shape_item.get("h", 48))
            if svg_converted:
                return svg_converted, "svg"

        return None, "unknown"

    @staticmethod
    def _stencil_to_svg(stencil_xml: str, width: int = 48, height: int = 48) -> Optional[str]:
        """Rudimentary conversion from Draw.io <shape> vector paths to standard SVG."""
        try:
            root = ET.fromstring(stencil_xml)
            viewbox = f"0 0 {width} {height}"
            svg_lines = [
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="{width}" height="{height}">'
            ]
            # Extract foreground/background paths
            for path_elem in root.iter("path"):
                d = path_elem.attrib.get("d", "")
                if d:
                    svg_lines.append(f'  <path d="{d}" fill="currentColor"/>')
            svg_lines.append("</svg>")
            return "\n".join(svg_lines)
        except Exception:
            return None


# ============================================================================
# 2. Central Icon Registry & Catalog
# ============================================================================

class IconRegistry:
    """Manages icon discovery, normalization, and catalog indexing."""

    _manifest_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def load_manifest(cls) -> Dict[str, Any]:
        """Load manifest.json or initialize a default manifest."""
        if cls._manifest_cache is not None:
            return cls._manifest_cache

        if _MANIFEST_FILE.exists():
            try:
                cls._manifest_cache = json.loads(_MANIFEST_FILE.read_text(encoding="utf-8"))
                return cls._manifest_cache
            except Exception:
                pass

        # Build initial manifest from existing files on disk
        manifest = {
            "version": "1.0.0",
            "packs": [
                {"id": "logos", "name": "Core Enterprise Tech Logos", "vendor": "Various"},
                {"id": "lucide", "name": "Lucide UI Icons", "vendor": "Lucide"},
                {"id": "feather", "name": "Feather Icons", "vendor": "Feather"},
            ],
            "icons": [],
        }

        # Index assets/logos
        if _LOGOS_DIR.exists():
            for f in sorted(_LOGOS_DIR.rglob("*.*")):
                if f.suffix.lower() in (".svg", ".png"):
                    rel_p = f.relative_to(_REPO_ROOT).as_posix()
                    slug = f.stem
                    # If inside a subfolder, include pack prefix
                    if f.parent != _LOGOS_DIR:
                        pack_id = f.parent.name
                        icon_id = f"{pack_id}:{slug}"
                    else:
                        pack_id = "logos"
                        icon_id = slug

                    manifest["icons"].append({
                        "id": icon_id,
                        "title": slug.replace("_", " ").title(),
                        "pack": pack_id,
                        "file": rel_p,
                        "format": f.suffix.lower().lstrip("."),
                    })

        cls._manifest_cache = manifest
        return manifest

    @classmethod
    def save_manifest(cls, manifest: Dict[str, Any]) -> None:
        """Persist manifest to assets/icons/manifest.json."""
        _ICONS_DIR.mkdir(parents=True, exist_ok=True)
        _MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        cls._manifest_cache = manifest

    @classmethod
    def resolve_icon(cls, icon_key_or_path: str) -> Optional[Path]:
        """
        Resolves an icon identifier, file path, or slug to a concrete absolute Path.
        Resolution precedence:
        1. Direct file path if it exists
        2. Manifest ID exact match (e.g. 'cloudera:manager' or 'kafka')
        3. Local assets/logos/{key}.svg
        4. Local assets/logos/{key}.png
        5. Pack-qualified path assets/logos/{pack}/{key}.svg
        6. Lucide icons assets/icons/lucide/{key}.svg
        """
        if not icon_key_or_path:
            return None

        # 1. Direct path
        p = Path(icon_key_or_path)
        if p.exists() and p.is_file():
            return p.resolve()

        # Check relative to repo root
        rel = _REPO_ROOT / icon_key_or_path
        if rel.exists() and rel.is_file():
            return rel.resolve()

        key = icon_key_or_path.strip()

        # 2. Check manifest
        manifest = cls.load_manifest()
        for item in manifest.get("icons", []):
            if item["id"] == key or item["id"] == key.lower():
                target = _REPO_ROOT / item["file"]
                if target.exists() and target.is_file():
                    return target.resolve()

        # 3. Direct in assets/logos/
        candidate_svg = _LOGOS_DIR / f"{key}.svg"
        if candidate_svg.exists():
            return candidate_svg.resolve()
        candidate_png = _LOGOS_DIR / f"{key}.png"
        if candidate_png.exists():
            return candidate_png.resolve()

        # 4. Pack slash/colon notation (e.g. 'cloudera/manager' or 'lucide:database')
        if "/" in key or ":" in key:
            norm_key = key.replace(":", "/")
            cand = _LOGOS_DIR / f"{norm_key}.svg"
            if cand.exists():
                return cand.resolve()
            cand_png = _LOGOS_DIR / f"{norm_key}.png"
            if cand_png.exists():
                return cand_png.resolve()
            # Also check _ICONS_DIR (e.g. assets/icons/lucide/database.svg)
            cand_icon = _ICONS_DIR / f"{norm_key}.svg"
            if cand_icon.exists():
                return cand_icon.resolve()
            # Strip pack prefix if present (e.g. lucide:database -> database in lucide)
            slug = key.split(":")[-1].split("/")[-1]
            cand_slug_lucide = _ICONS_DIR / "lucide" / f"{slug}.svg"
            if cand_slug_lucide.exists():
                return cand_slug_lucide.resolve()

        # 5. Lucide / Feather UI icons
        cand_lucide = _ICONS_DIR / "lucide" / f"{key}.svg"
        if cand_lucide.exists():
            return cand_lucide.resolve()
        cand_feather = _ICONS_DIR / "feather" / f"{key}.svg"
        if cand_feather.exists():
            return cand_feather.resolve()

        return None

    @classmethod
    def list_icons(cls, pack: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """List registered icons filtered by pack and/or search query."""
        manifest = cls.load_manifest()
        results = []
        for icon in manifest.get("icons", []):
            if pack and icon.get("pack") != pack:
                continue
            if query:
                q = query.lower()
                if q not in icon["id"].lower() and q not in icon.get("title", "").lower():
                    continue
            results.append(icon)
        return results

    @classmethod
    def register_icon(
        cls,
        icon_id: str,
        title: str,
        pack: str,
        rel_file_path: str,
        fmt: str = "svg",
        category: str = "general",
    ) -> None:
        """Register a new or updated icon in the manifest."""
        manifest = cls.load_manifest()
        # Check if pack is registered
        if not any(p["id"] == pack for p in manifest.get("packs", [])):
            manifest.setdefault("packs", []).append({
                "id": pack,
                "name": pack.replace("_", " ").title(),
                "vendor": pack.capitalize(),
            })

        # Update or append icon
        existing = [i for i in manifest.get("icons", []) if i["id"] == icon_id]
        if existing:
            existing[0]["title"] = title
            existing[0]["file"] = rel_file_path
            existing[0]["format"] = fmt
            existing[0]["category"] = category
        else:
            manifest.setdefault("icons", []).append({
                "id": icon_id,
                "title": title,
                "pack": pack,
                "file": rel_file_path,
                "format": fmt,
                "category": category,
            })

        cls.save_manifest(manifest)


# ============================================================================
# 3. High-Level Import Pipeline
# ============================================================================

def import_drawio_library(
    library_file: Union[str, Path],
    pack_name: str,
    target_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Imports a Draw.io `.xml` library file, unpacks its shapes, extracts SVG/PNG
    assets to `assets/logos/<pack_name>/`, and registers them in the icon manifest.
    """
    lib_path = Path(library_file)
    if not lib_path.exists():
        raise FileNotFoundError(f"Draw.io library file not found: {library_file}")

    shapes = MxLibraryDecoder.decode_library(lib_path)
    if not shapes:
        return {"imported": 0, "pack": pack_name, "icons": []}

    dest_dir = target_dir or (_LOGOS_DIR / pack_name)
    dest_dir.mkdir(parents=True, exist_ok=True)

    imported_icons = []

    for item in shapes:
        title = item.get("title", "").strip() or "unnamed_shape"
        # Create a slug for the file name
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", title.lower()).strip("_")
        if not slug:
            slug = "shape"

        data, fmt = MxLibraryDecoder.extract_svg_or_image(item)
        if not data:
            continue

        if fmt == "svg":
            out_file = dest_dir / f"{slug}.svg"
            # Ensure SVG has xmlns
            if 'xmlns="http://www.w3.org/2000/svg"' not in data:
                data = data.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ')
            out_file.write_text(data, encoding="utf-8")
        elif fmt == "png":
            out_file = dest_dir / f"{slug}.png"
            out_file.write_bytes(base64.b64decode(data))
        else:
            continue

        rel_p = out_file.relative_to(_REPO_ROOT).as_posix()
        icon_id = f"{pack_name}:{slug}"

        IconRegistry.register_icon(
            icon_id=icon_id,
            title=title,
            pack=pack_name,
            rel_file_path=rel_p,
            fmt=fmt,
        )

        imported_icons.append({
            "id": icon_id,
            "title": title,
            "file": rel_p,
            "format": fmt,
        })

    return {
        "imported": len(imported_icons),
        "pack": pack_name,
        "icons": imported_icons,
    }
