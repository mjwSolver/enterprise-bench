"""
Enterprise Presentation Resource Manager
========================================
Asset resolution, silent pre-flight acquisition, graceful fallback handling,
and automated missing_resources.md diagnostic ledger generation.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any, Optional, Union
import urllib.error
import urllib.request

from src.core.config import ROOT_DIR

logger = logging.getLogger(__name__)


@dataclass
class ResourceSpec:
    """Specification of an external or local deliverable asset."""

    key: str
    target_path: Path
    canonical_url: Optional[str] = None
    fallback_url: Optional[str] = None
    fallback_type: str = "typographic"  # "typographic", "gradient", "vector"
    fallback_text: str = ""
    impacted_slides: list[str] = field(default_factory=list)
    recovery_command: Optional[str] = None

    def get_recovery_command(self, root_dir: Path) -> str:
        """Generate or return the quick recovery command (curl or extraction)."""
        if self.recovery_command:
            return self.recovery_command

        try:
            rel_path = self.target_path.relative_to(root_dir).as_posix()
        except ValueError:
            rel_path = self.target_path.as_posix()

        if self.canonical_url:
            return f'curl -sSL "{self.canonical_url}" -o {rel_path}'
        elif self.fallback_url:
            return f'curl -sSL "{self.fallback_url}" -o {rel_path}'
        return f"# Re-acquire {self.key} and place at {rel_path}"


def get_default_resources(root_dir: Path) -> list[ResourceSpec]:
    """Default enterprise presentation assets registry."""
    return [
        ResourceSpec(
            key="logo_metrodata_square",
            target_path=root_dir / "assets" / "images" / "logos" / "metrodata_square.png",
            canonical_url="https://www.snowflake.com/content/dam/snowflake-site/general/logos/partner-logos/pt-metrodata-electronics-tbk@3x.png",
            fallback_url=None,
            fallback_type="typographic",
            fallback_text="METRODATA",
            impacted_slides=["Cover", "Chapter Divider"],
            recovery_command='curl -sSL "https://www.snowflake.com/content/dam/snowflake-site/general/logos/partner-logos/pt-metrodata-electronics-tbk@3x.png" -o assets/images/logos/metrodata_square.png',
        ),
        ResourceSpec(
            key="logo_snowflake",
            target_path=root_dir / "assets" / "logos" / "snowflake.svg",
            canonical_url=None,
            fallback_url=None,
            fallback_type="vector",
            fallback_text="SNOWFLAKE",
            impacted_slides=["Cover", "Architecture", "Technology Grid"],
            recovery_command="git checkout assets/logos/snowflake.svg",
        ),
        ResourceSpec(
            key="logo_snowflake_official",
            target_path=root_dir / "assets" / "images" / "logos" / "snowflake_official.png",
            canonical_url="https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg",
            fallback_url=None,
            fallback_type="typographic",
            fallback_text="SNOWFLAKE",
            impacted_slides=["Cover", "Architecture"],
            recovery_command='curl -sSL "https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg" -o assets/logos/snowflake_official.svg',
        ),
        ResourceSpec(
            key="stock_chapter_photo",
            target_path=root_dir / "assets" / "images" / "stock" / "chapter_hero.jpg",
            canonical_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=1600&auto=format&fit=crop",
            fallback_url=None,
            fallback_type="gradient",
            fallback_text="",
            impacted_slides=["Chapter Divider"],
            recovery_command='curl -sSL "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=1600&auto=format&fit=crop" -o assets/images/stock/chapter_hero.jpg',
        ),
        ResourceSpec(
            key="hero_cloud_interchange_night",
            target_path=root_dir / "assets" / "images" / "hero" / "cloud_interchange_night.jpg",
            canonical_url=None,
            fallback_url=None,
            fallback_type="gradient",
            fallback_text="",
            impacted_slides=["Hero Cover"],
            recovery_command="python -c \"from pptx import Presentation; prs = Presentation('clean_workspace/projects/TTI_Snowflake_Analytics/01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx'); open('assets/images/hero/cloud_interchange_night.jpg', 'wb').write(prs.slides[0].shapes[0].image.blob)\"",
        ),
    ]


class ResourceManager:
    """
    Coordinates local asset resolution, automated silent downloads,
    graceful degradation, and diagnostic missing_resources.md ledgering.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = (root_dir or ROOT_DIR).resolve()
        self.missing_report_path = self.root_dir / "missing_resources.md"
        self._registry: dict[str, ResourceSpec] = {}
        self._missing_records: dict[str, ResourceSpec] = {}
        self._failed_downloads: set[str] = set()

        for spec in get_default_resources(self.root_dir):
            self.register_resource(spec)

    def register_resource(self, spec: ResourceSpec) -> None:
        """Register a resource specification."""
        if not spec.target_path.is_absolute():
            spec.target_path = (self.root_dir / spec.target_path).resolve()
        self._registry[spec.key] = spec

    def get_spec(self, key: str) -> Optional[ResourceSpec]:
        """Lookup resource specification by key."""
        return self._registry.get(key)

    def list_specs(self) -> list[ResourceSpec]:
        """List all registered resource specifications."""
        return list(self._registry.values())

    def _silent_download(self, spec: ResourceSpec, timeout: float = 3.0) -> Optional[Path]:
        """
        Attempt silent, non-blocking download of asset.
        Returns target_path if successful, None if failed or offline.
        NEVER raises an exception.
        """
        urls_to_try = [u for u in [spec.canonical_url, spec.fallback_url] if u]
        if not urls_to_try:
            return None

        for url in urls_to_try:
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
                    },
                )
                spec.target_path.parent.mkdir(parents=True, exist_ok=True)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        if content:
                            spec.target_path.write_bytes(content)
                            return spec.target_path
            except Exception as e:
                logger.debug("Download failed for %s from %s: %s", spec.key, url, e)
                continue

        return None

    def resolve_asset(
        self,
        key_or_path: Union[str, Path],
        impacted_slide: Optional[str] = None,
        timeout: float = 3.0,
    ) -> Optional[Path]:
        """
        Resolve an asset path:
        1. If key in registry and file exists on disk -> return Path.
        2. If missing on disk, attempt silent download (3.0s timeout).
        3. If download succeeds -> return Path.
        4. If offline or download fails:
           - Record missing resource for missing_resources.md.
           - Return None (triggering graceful fallback).
           - NEVER raise FileNotFoundError.
        5. If key_or_path is a path string/Path not in registry:
           - Check if it exists on disk, return Path if so, None otherwise.
        """
        key_str = str(key_or_path)

        # 1. Check if key is registered
        if key_str in self._registry:
            spec = self._registry[key_str]
            target = spec.target_path

            if target.is_file():
                return target

            # File missing locally; attempt silent download if not already failed in session
            if key_str not in self._failed_downloads:
                downloaded = self._silent_download(spec, timeout=timeout)
                if downloaded and downloaded.is_file():
                    return downloaded
                self._failed_downloads.add(key_str)

            # Download failed or offline -> record fallback event
            if impacted_slide and impacted_slide not in spec.impacted_slides:
                spec.impacted_slides.append(impacted_slide)

            self._missing_records[key_str] = spec
            self.generate_missing_report()
            return None

        # 2. Key is not registered; test as a filesystem path
        raw_p = Path(key_or_path)
        p = raw_p if raw_p.is_absolute() else (self.root_dir / raw_p)
        if p.is_file():
            return p

        # Missing unregistered path
        logger.debug("Unregistered asset path missing: %s", key_or_path)
        return None

    def check_resources(
        self,
        download: bool = True,
        timeout: float = 3.0,
    ) -> dict[str, dict[str, Any]]:
        """
        Check all registered resources:
        - If present, record present.
        - If missing and download=True, attempt silent download.
        - If any missing, update missing_resources.md.
        - If all present, clean missing_resources.md.
        Returns status dictionary keyed by resource key.
        """
        results: dict[str, dict[str, Any]] = {}
        missing_detected = False

        for key, spec in self._registry.items():
            target = spec.target_path
            was_downloaded = False

            if not target.is_file() and download:
                downloaded = self._silent_download(spec, timeout=timeout)
                if downloaded and downloaded.is_file():
                    was_downloaded = True

            is_present = target.is_file()
            results[key] = {
                "key": key,
                "present": is_present,
                "downloaded": was_downloaded,
                "path": target,
                "spec": spec,
            }

            if not is_present:
                missing_detected = True
                self._missing_records[key] = spec

        if missing_detected:
            self.generate_missing_report()
        else:
            self.clean_missing_report(remove=True)

        return results

    def generate_missing_report(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Generate or update missing_resources.md at workspace root detailing
        missing resources, impacted slides, and quick curl recovery commands.
        """
        if not self._missing_records:
            self.clean_missing_report(remove=True)
            return None

        target = output_path or self.missing_report_path
        target.parent.mkdir(parents=True, exist_ok=True)

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        lines = [
            "# Missing Deliverable Resources Report",
            f"*Generated during presentation assembly at: {now_str}*",
            "",
            "The following resources were missing. Presentation completed successfully using graceful fallbacks:",
            "",
            "| Resource Key | Expected Path | Impacted Slide | Quick Recovery Command |",
            "| :--- | :--- | :--- | :--- |",
        ]

        for key, spec in sorted(self._missing_records.items(), key=lambda x: x[0]):
            try:
                rel_path = spec.target_path.relative_to(self.root_dir).as_posix()
            except ValueError:
                rel_path = spec.target_path.as_posix()

            impacted_str = ", ".join(spec.impacted_slides) if spec.impacted_slides else "General Slide Assembly"
            cmd = spec.get_recovery_command(self.root_dir)
            lines.append(f"| `{key}` | `{rel_path}` | {impacted_str} | `{cmd}` |")

        lines.append("")
        target.write_text("\n".join(lines), encoding="utf-8")
        return target

    def clean_missing_report(self, remove: bool = True) -> None:
        """Clean or remove missing_resources.md when all assets are present."""
        self._missing_records.clear()
        if self.missing_report_path.exists():
            if remove:
                try:
                    self.missing_report_path.unlink()
                except OSError:
                    pass
            else:
                now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                self.missing_report_path.write_text(
                    f"# Missing Deliverable Resources Report\n*Updated: {now_str}*\n\nAll registered presentation resources are present and verified. Status: Clean.\n",
                    encoding="utf-8",
                )


_GLOBAL_RESOURCE_MANAGER: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get or instantiate the global singleton ResourceManager."""
    global _GLOBAL_RESOURCE_MANAGER
    if _GLOBAL_RESOURCE_MANAGER is None:
        _GLOBAL_RESOURCE_MANAGER = ResourceManager()
    return _GLOBAL_RESOURCE_MANAGER


def resolve_asset(
    key_or_path: Union[str, Path],
    impacted_slide: Optional[str] = None,
    timeout: float = 3.0,
) -> Optional[Path]:
    """Convenience function to resolve an asset using the global ResourceManager."""
    return get_resource_manager().resolve_asset(
        key_or_path, impacted_slide=impacted_slide, timeout=timeout
    )


def check_resources(download: bool = True, timeout: float = 3.0) -> dict[str, dict[str, Any]]:
    """Convenience function to check all registered resources using the global ResourceManager."""
    return get_resource_manager().check_resources(download=download, timeout=timeout)
