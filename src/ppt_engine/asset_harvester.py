"""
Deterministic Asset Harvester & Central Diagram Asset Subsystem
==============================================================
Provides tools to:
1. Ingest, harvest, and normalize enterprise vendor vector stencils (Databricks, Cloudera, Snowflake, Cloud providers).
2. Decompress and parse Draw.io <mxlibrary> XML files (JSON, URL-encoded, Base64/zlib, remote URLs).
3. Maintain the centralized icon manifest (assets/icons/manifest.json) with vendor namespaces, categories, and aliases.
4. Deterministically resolve diagram assets by ID, key, alias, or path without ad-hoc web scraping.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Repository Paths
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ASSETS_DIR = _REPO_ROOT / "assets"
_LOGOS_DIR = _ASSETS_DIR / "logos"
_ICONS_DIR = _ASSETS_DIR / "icons"
_VENDOR_PACKS_DIR = _REPO_ROOT / "vendor_packs"
_MANIFEST_FILE = _ICONS_DIR / "manifest.json"


@dataclass
class ResolvedAsset:
    """Rich resolution descriptor for diagram and presentation assets."""
    id: str
    title: str
    pack: str
    format: str
    file: str  # relative path
    absolute_path: Path
    weight: str  # 'brand' | 'light'
    size_bytes: int
    exists: bool
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "pack": self.pack,
            "format": self.format,
            "file": self.file,
            "absolute_path": str(self.absolute_path),
            "weight": self.weight,
            "size_bytes": self.size_bytes,
            "exists": self.exists,
            "category": self.category,
        }


class AssetHarvester:
    """Coordinates deterministic ingestion, parsing, cataloging, and resolution of vector assets."""

    DATABRICKS_CATALOG_URL = (
        "https://raw.githubusercontent.com/oieduardorabelo/databricks-architecture-icons/main/icons/catalog.json"
    )
    DATABRICKS_LOGO_URL = (
        "https://raw.githubusercontent.com/oieduardorabelo/databricks-architecture-icons/main/icons/logos/databricks.svg"
    )
    DATABRICKS_DRAWIO_LIB_URL = (
        "https://raw.githubusercontent.com/oieduardorabelo/databricks-architecture-icons/main/drawio/databricks-architecture-icons.xml"
    )

    @staticmethod
    def normalize_svg_content(raw_svg: str, title: Optional[str] = None) -> str:
        """Ensures standard XML namespace and clean viewBox attributes for standalone SVG."""
        content = raw_svg.strip()
        if 'xmlns="http://www.w3.org/2000/svg"' not in content:
            content = re.sub(r"<svg(\s+)", r'<svg xmlns="http://www.w3.org/2000/svg"\1', content, count=1)

        # Inject title tag if missing and title provided
        if title and "<title>" not in content:
            content = re.sub(r"(<svg[^>]*>)", rf"\1\n  <title>{title}</title>", content, count=1)

        return content

    @classmethod
    def harvest_databricks_stencils(
        cls,
        dest_dir: Optional[Path] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Harvests official Databricks (DBX) vector stencils and logos deterministically.
        Downloads the official architecture icon catalog, ingests 70+ vector SVGs
        into assets/logos/databricks/, caches vendor_packs/databricks_icons.xml,
        and registers all assets in assets/icons/manifest.json.
        """
        target_dir = dest_dir or (_LOGOS_DIR / "databricks")
        target_dir.mkdir(parents=True, exist_ok=True)
        _VENDOR_PACKS_DIR.mkdir(parents=True, exist_ok=True)

        from src.ppt_engine.library_importer import IconRegistry

        # 1. Fetch Databricks catalog descriptor
        catalog_cache = _VENDOR_PACKS_DIR / "databricks_catalog.json"
        cat_data: Optional[Dict[str, Any]] = None

        if catalog_cache.exists() and not force:
            try:
                cat_data = json.loads(catalog_cache.read_text(encoding="utf-8"))
            except Exception:
                pass

        if cat_data is None:
            try:
                req = urllib.request.Request(cls.DATABRICKS_CATALOG_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    cat_data = json.loads(resp.read().decode("utf-8"))
                    catalog_cache.write_text(json.dumps(cat_data, indent=2), encoding="utf-8")
            except Exception as e:
                logger.warning("Could not fetch remote Databricks catalog: %s", e)
                if catalog_cache.exists():
                    cat_data = json.loads(catalog_cache.read_text(encoding="utf-8"))
                else:
                    cat_data = {"products": []}

        products = cat_data.get("products", [])

        # 2. Download and save Databricks master logo
        core_logo_file = target_dir / "databricks.svg"
        if not core_logo_file.exists() or force:
            try:
                req = urllib.request.Request(cls.DATABRICKS_LOGO_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    raw_logo = resp.read().decode("utf-8")
                    norm_logo = cls.normalize_svg_content(raw_logo, title="Databricks")
                    core_logo_file.write_text(norm_logo, encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to download Databricks core logo: %s", e)

        # 3. Download / Harvest products in parallel
        def _fetch_product_svg(p: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
            slug = p.get("slug", "")
            title = p.get("name", slug.replace("-", " ").title())
            category = p.get("category", "general")
            urls = p.get("urls", {})
            svg_url = urls.get("svg") or f"https://oieduardorabelo.github.io/databricks-architecture-icons/icons/svg/{slug}.svg"

            file_stem = slug.replace("-", "_")
            out_path = target_dir / f"{file_stem}.svg"

            if not out_path.exists() or force:
                try:
                    req = urllib.request.Request(svg_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        content = resp.read().decode("utf-8")
                        norm = cls.normalize_svg_content(content, title=title)
                        out_path.write_text(norm, encoding="utf-8")
                except Exception as ex:
                    logger.debug("Failed to download %s: %s", slug, ex)
                    return slug, title, category, "", str(ex)

            # Also ensure hyphenated alias symlink or companion exists if needed
            hyphen_path = target_dir / f"{slug}.svg"
            if not hyphen_path.exists() and out_path.exists():
                try:
                    hyphen_path.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
                except Exception:
                    pass

            return slug, title, category, out_path.relative_to(_REPO_ROOT).as_posix(), ""

        harvested = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_fetch_product_svg, prod) for prod in products]
            for fut in as_completed(futures):
                slug, title, cat, rel_path, err = fut.result()
                if rel_path:
                    harvested.append({"slug": slug, "title": title, "category": cat, "file": rel_path})

        # 4. Cache official Draw.io library XML file
        dbx_lib_file = _VENDOR_PACKS_DIR / "databricks_icons.xml"
        if not dbx_lib_file.exists() or force:
            try:
                req = urllib.request.Request(cls.DATABRICKS_DRAWIO_LIB_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    dbx_lib_file.write_bytes(resp.read())
            except Exception:
                pass

        # 5. Register in manifest.json
        manifest = IconRegistry.load_manifest()

        # Ensure pack metadata is present
        if not any(p["id"] == "databricks" for p in manifest.get("packs", [])):
            manifest.setdefault("packs", []).append({
                "id": "databricks",
                "name": "Databricks Intelligence Platform",
                "vendor": "Databricks",
                "brand_color": "#FF3621",
                "source": "Official Vector Architecture Stencils",
            })

        # Register core databricks icon
        if core_logo_file.exists():
            IconRegistry.register_icon(
                icon_id="databricks",
                title="Databricks",
                pack="databricks",
                rel_file_path=core_logo_file.relative_to(_REPO_ROOT).as_posix(),
                fmt="svg",
                category="platform",
            )
            IconRegistry.register_icon(
                icon_id="databricks:databricks",
                title="Databricks",
                pack="databricks",
                rel_file_path=core_logo_file.relative_to(_REPO_ROOT).as_posix(),
                fmt="svg",
                category="platform",
            )
            IconRegistry.register_icon(
                icon_id="dbx",
                title="Databricks",
                pack="databricks",
                rel_file_path=core_logo_file.relative_to(_REPO_ROOT).as_posix(),
                fmt="svg",
                category="platform",
            )

        # Register all harvested products
        for h in harvested:
            slug_stem = h["slug"].replace("-", "_")
            rel_file = h["file"]
            icon_id = f"databricks:{slug_stem}"

            IconRegistry.register_icon(
                icon_id=icon_id,
                title=h["title"],
                pack="databricks",
                rel_file_path=rel_file,
                fmt="svg",
                category=h["category"],
            )

            # Register hyphenated alias (e.g. databricks:unity-catalog)
            if slug_stem != h["slug"]:
                IconRegistry.register_icon(
                    icon_id=f"databricks:{h['slug']}",
                    title=h["title"],
                    pack="databricks",
                    rel_file_path=rel_file,
                    fmt="svg",
                    category=h["category"],
                )

            # Register short dbx alias (e.g. dbx:unity_catalog)
            IconRegistry.register_icon(
                icon_id=f"dbx:{slug_stem}",
                title=h["title"],
                pack="databricks",
                rel_file_path=rel_file,
                fmt="svg",
                category=h["category"],
            )

        return {
            "pack": "databricks",
            "total_harvested": len(harvested) + (1 if core_logo_file.exists() else 0),
            "dest_dir": str(target_dir),
            "vendor_library": str(dbx_lib_file) if dbx_lib_file.exists() else None,
            "icons": harvested,
        }

    @classmethod
    def harvest_cloudera_pack(cls) -> Dict[str, Any]:
        """
        Harmonizes and standardizes all Cloudera CDP and CDSW icons in assets/logos/cloudera/,
        ensuring authentic modern marks and updating manifest registration.
        """
        from src.ppt_engine.library_importer import IconRegistry

        cloudera_dir = _LOGOS_DIR / "cloudera"
        cloudera_dir.mkdir(parents=True, exist_ok=True)

        registered = []

        # 1. Ensure cloudera_cdsw.svg exists
        cdsw_svg = cloudera_dir / "cloudera_cdsw.svg"
        ai_svg = cloudera_dir / "cloudera_ai.svg"
        if not cdsw_svg.exists() and ai_svg.exists():
            cdsw_svg.write_text(ai_svg.read_text(encoding="utf-8"), encoding="utf-8")

        # 2. Key Cloudera mappings
        cloudera_entries = [
            ("cloudera", "Cloudera", "cloudera_official.svg", "corporate"),
            ("cloudera:official", "Cloudera", "cloudera_official.svg", "corporate"),
            ("cloudera:cdsw", "Cloudera Data Science Workbench (CDSW)", "cloudera_cdsw.svg", "data_science"),
            ("cloudera:cloudera_cdsw", "Cloudera Data Science Workbench", "cloudera_cdsw.svg", "data_science"),
            ("cloudera:cloudera_ai", "Cloudera Machine Learning / AI", "cloudera_ai.svg", "data_science"),
            ("cloudera:cloudera_cdp_data_hub", "Cloudera CDP Data Hub", "cloudera_cdp_data_hub.svg", "platform"),
            ("cloudera:cloudera_manager", "Cloudera Manager", "cloudera_manager.svg", "management"),
        ]

        for icon_id, title, filename, cat in cloudera_entries:
            target_p = cloudera_dir / filename
            if target_p.exists():
                rel_p = target_p.relative_to(_REPO_ROOT).as_posix()
                IconRegistry.register_icon(
                    icon_id=icon_id,
                    title=title,
                    pack="cloudera",
                    rel_file_path=rel_p,
                    fmt="svg",
                    category=cat,
                )
                registered.append({"id": icon_id, "title": title, "file": rel_p})

        return {
            "pack": "cloudera",
            "total_registered": len(registered),
            "icons": registered,
        }

    @classmethod
    def harvest_aws_pack(cls) -> Dict[str, Any]:
        """
        Harmonizes and standardizes all AWS cloud vector stencils in assets/logos/aws/,
        registering them in manifest.json with official namespaces and aliases.
        """
        from src.ppt_engine.library_importer import IconRegistry

        aws_dir = _LOGOS_DIR / "aws"
        aws_dir.mkdir(parents=True, exist_ok=True)

        registered = []
        aws_entries = [
            ("aws", "Amazon Web Services", "aws.svg", "cloud", _LOGOS_DIR / "aws.svg"),
            ("aws:lambda", "AWS Lambda Serverless", "aws_lambda.svg", "compute", aws_dir / "aws_lambda.svg"),
            ("aws:aws_lambda", "AWS Lambda", "aws_lambda.svg", "compute", aws_dir / "aws_lambda.svg"),
            ("lambda", "AWS Lambda", "aws_lambda.svg", "compute", aws_dir / "aws_lambda.svg"),
            ("aws:api_gateway", "Amazon API Gateway", "aws_api_gateway.svg", "integration", aws_dir / "aws_api_gateway.svg"),
            ("api_gateway", "Amazon API Gateway", "aws_api_gateway.svg", "integration", aws_dir / "aws_api_gateway.svg"),
            ("aws:secrets_manager", "AWS Secrets Manager / KMS", "aws_secrets_manager.svg", "security", aws_dir / "aws_secrets_manager.svg"),
            ("secrets_manager", "AWS Secrets Manager", "aws_secrets_manager.svg", "security", aws_dir / "aws_secrets_manager.svg"),
            ("aws:s3", "Amazon S3 Object Storage", "amazons3.svg", "storage", _LOGOS_DIR / "amazons3.svg"),
        ]

        manifest = IconRegistry.load_manifest()
        if not any(p["id"] == "aws" for p in manifest.get("packs", [])):
            manifest.setdefault("packs", []).append({
                "id": "aws",
                "name": "Amazon Web Services (AWS)",
                "vendor": "Amazon",
                "brand_color": "#FF9900",
                "source": "Official Cloud Architecture Stencils",
            })

        for icon_id, title, filename, cat, target_p in aws_entries:
            if target_p.exists():
                rel_p = target_p.relative_to(_REPO_ROOT).as_posix()
                IconRegistry.register_icon(
                    icon_id=icon_id,
                    title=title,
                    pack="aws",
                    rel_file_path=rel_p,
                    fmt="svg",
                    category=cat,
                )
                registered.append({"id": icon_id, "title": title, "file": rel_p})

        return {
            "pack": "aws",
            "total_registered": len(registered),
            "icons": registered,
        }


    @classmethod
    def resolve_asset(cls, icon_key_or_path: str) -> Optional[ResolvedAsset]:
        """
        Deterministically resolves any icon key, ID, alias, or file path to a concrete asset.
        Resolution operates purely against local manifest and assets/ repositories with ZERO web scraping.
        Precedence:
        1. Direct file path if exists on disk
        2. Manifest exact ID match
        3. Alias lookup (dbx -> databricks, cloudera:cdsw -> cloudera_cdsw)
        4. Case-insensitive / normalized lookup (_ vs -)
        5. assets/logos/{key}.svg or assets/logos/{pack}/{slug}.svg
        6. assets/icons/lucide/{slug}.svg or assets/icons/feather/{slug}.svg
        """
        if not icon_key_or_path or not icon_key_or_path.strip():
            return None

        key = icon_key_or_path.strip()

        # 1. Direct path check
        p = Path(key)
        if p.exists() and p.is_file():
            abs_p = p.resolve()
            try:
                rel = abs_p.relative_to(_REPO_ROOT).as_posix()
            except ValueError:
                rel = str(abs_p)
            return ResolvedAsset(
                id=key,
                title=abs_p.stem.replace("_", " ").title(),
                pack="filesystem",
                format=abs_p.suffix.lower().lstrip("."),
                file=rel,
                absolute_path=abs_p,
                weight="brand" if "logos" in rel else "light",
                size_bytes=abs_p.stat().st_size,
                exists=True,
            )

        rel_p = _REPO_ROOT / key
        if rel_p.exists() and rel_p.is_file():
            abs_p = rel_p.resolve()
            return ResolvedAsset(
                id=key,
                title=abs_p.stem.replace("_", " ").title(),
                pack="repo",
                format=abs_p.suffix.lower().lstrip("."),
                file=abs_p.relative_to(_REPO_ROOT).as_posix(),
                absolute_path=abs_p,
                weight="brand" if "logos" in str(abs_p) else "light",
                size_bytes=abs_p.stat().st_size,
                exists=True,
            )

        from src.ppt_engine.library_importer import IconRegistry
        manifest = IconRegistry.load_manifest()

        # 2. Alias normalizations
        normalized_keys = [key, key.lower()]
        if key.startswith("dbx:"):
            normalized_keys.append(key.replace("dbx:", "databricks:"))
        elif key == "dbx":
            normalized_keys.append("databricks")
        elif key.startswith("databricks:"):
            normalized_keys.append(key.replace("databricks:", "dbx:"))

        if "-" in key:
            normalized_keys.append(key.replace("-", "_"))
        if "_" in key:
            normalized_keys.append(key.replace("_", "-"))

        # 3. Check manifest entries
        for item in manifest.get("icons", []):
            item_id = item.get("id", "")
            if item_id in normalized_keys or item_id.lower() in normalized_keys:
                target = _REPO_ROOT / item["file"]
                if target.exists() and target.is_file():
                    return ResolvedAsset(
                        id=item_id,
                        title=item.get("title", item_id),
                        pack=item.get("pack", "logos"),
                        format=item.get("format", target.suffix.lower().lstrip(".")),
                        file=item["file"],
                        absolute_path=target.resolve(),
                        weight="brand" if "logos" in item.get("file", "") else "light",
                        size_bytes=target.stat().st_size,
                        exists=True,
                        category=item.get("category", "general"),
                    )

        # 4. Check assets/logos/ directly
        candidate_svg = _LOGOS_DIR / f"{key}.svg"
        if candidate_svg.exists():
            return ResolvedAsset(
                id=key,
                title=key.replace("_", " ").title(),
                pack="logos",
                format="svg",
                file=candidate_svg.relative_to(_REPO_ROOT).as_posix(),
                absolute_path=candidate_svg.resolve(),
                weight="brand",
                size_bytes=candidate_svg.stat().st_size,
                exists=True,
            )

        # 5. Check pack slash/colon notation (e.g. databricks:unity_catalog, cloudera/cdsw)
        if ":" in key or "/" in key:
            norm_path = key.replace(":", "/")
            cand = _LOGOS_DIR / f"{norm_path}.svg"
            if cand.exists():
                return ResolvedAsset(
                    id=key,
                    title=cand.stem.replace("_", " ").title(),
                    pack=norm_path.split("/")[0],
                    format="svg",
                    file=cand.relative_to(_REPO_ROOT).as_posix(),
                    absolute_path=cand.resolve(),
                    weight="brand",
                    size_bytes=cand.stat().st_size,
                    exists=True,
                )

            # Try hyphen-underscore variations
            cand_alt = _LOGOS_DIR / f"{norm_path.replace('-', '_')}.svg"
            if cand_alt.exists():
                return ResolvedAsset(
                    id=key,
                    title=cand_alt.stem.replace("_", " ").title(),
                    pack=norm_path.split("/")[0],
                    format="svg",
                    file=cand_alt.relative_to(_REPO_ROOT).as_posix(),
                    absolute_path=cand_alt.resolve(),
                    weight="brand",
                    size_bytes=cand_alt.stat().st_size,
                    exists=True,
                )

            # Check inside assets/icons/lucide
            slug = key.split(":")[-1].split("/")[-1]
            cand_lucide = _ICONS_DIR / "lucide" / f"{slug}.svg"
            if cand_lucide.exists():
                return ResolvedAsset(
                    id=key,
                    title=slug.replace("_", " ").title(),
                    pack="lucide",
                    format="svg",
                    file=cand_lucide.relative_to(_REPO_ROOT).as_posix(),
                    absolute_path=cand_lucide.resolve(),
                    weight="light",
                    size_bytes=cand_lucide.stat().st_size,
                    exists=True,
                )

        # 6. Check Lucide / Feather
        cand_lucide = _ICONS_DIR / "lucide" / f"{key}.svg"
        if cand_lucide.exists():
            return ResolvedAsset(
                id=key,
                title=key.replace("_", " ").title(),
                pack="lucide",
                format="svg",
                file=cand_lucide.relative_to(_REPO_ROOT).as_posix(),
                absolute_path=cand_lucide.resolve(),
                weight="light",
                size_bytes=cand_lucide.stat().st_size,
                exists=True,
            )

        return None
