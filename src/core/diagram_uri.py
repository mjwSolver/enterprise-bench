"""
src/core/diagram_uri.py
=======================
On-demand URI resolver and rasterizer for multi-page Draw.io projects (.drawio)
and declarative diagram manifests (.yaml).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Tuple, Union


def parse_diagram_uri(uri: str) -> Tuple[Optional[Path], Optional[str]]:
    """
    Parse a diagram URI into (file_path, page_identifier).
    Supports:
      - 'path/to/project.drawio#Page-1' -> (Path('path/to/project.drawio'), 'Page-1')
      - 'presets/diagrams/fsd.yaml#Sales Dataflow' -> (Path('...fsd.yaml'), 'Sales Dataflow')
      - 'path/to/project.drawio#0' -> (Path('path/to/project.drawio'), '0')
    """
    if "#" not in uri:
        return None, None

    file_part, page_part = uri.split("#", 1)
    file_part = file_part.strip()
    page_part = page_part.strip()

    p = Path(file_part)
    return p, page_part


def resolve_diagram_uri(
    uri: str,
    base_dir: Optional[Union[str, Path]] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    scale: float = 3.0,
) -> Optional[Path]:
    """
    Resolve a diagram URI to an on-disk PNG file. If not cached, triggers on-demand rasterization.
    """
    path_obj, page_ref = parse_diagram_uri(uri)
    if not path_obj or not page_ref:
        return None

    # Resolve relative paths
    if not path_obj.is_absolute():
        if base_dir and (Path(base_dir) / path_obj).exists():
            path_obj = Path(base_dir) / path_obj
        elif (Path.cwd() / path_obj).exists():
            path_obj = Path.cwd() / path_obj
        elif not path_obj.exists():
            return None

    if not path_obj.exists():
        return None

    # Setup cache directory
    cdir = Path(cache_dir) if cache_dir else Path("output/.cache/diagrams")
    cdir.mkdir(parents=True, exist_ok=True)

    # Compute cache key from file mtime + page + scale
    mtime = int(path_obj.stat().st_mtime)
    uri_hash = hashlib.sha256(f"{path_obj.resolve()}:{page_ref}:{scale}:{mtime}".encode()).hexdigest()[:16]
    clean_page = "".join(c if c.isalnum() or c in "-_" else "_" for c in page_ref)
    cached_png = cdir / f"{path_obj.stem}_{clean_page}_{uri_hash}.png"

    if cached_png.exists() and cached_png.stat().st_size > 0:
        return cached_png

    # On-demand rasterization
    suffix = path_obj.suffix.lower()
    if suffix == ".drawio":
        from src.ppt_engine.diagram_engine import DrawIOProject

        try:
            project = DrawIOProject.load(path_obj)
            target_page: Union[int, str] = int(page_ref) if page_ref.isdigit() else page_ref
            return project.export_page(target_page, output_path=cached_png, format="png", scale=scale)
        except Exception:
            return None

    elif suffix in (".yaml", ".yml"):
        import yaml
        from src.ppt_engine.diagram_engine import DrawIOProject

        try:
            raw = yaml.safe_load(path_obj.read_text(encoding="utf-8"))
        except Exception:
            return None

        pages_cfg = raw.get("pages", []) if isinstance(raw, dict) else []
        default_theme = raw.get("default_theme", raw.get("project", {}).get("theme", "modern_consulting")) if isinstance(raw, dict) else "modern_consulting"
        default_font_size = float(raw.get("default_font_size", 18.0)) if isinstance(raw, dict) else 18.0

        # Match page by name or index
        page_data = None
        if isinstance(pages_cfg, list):
            if page_ref.isdigit() and int(page_ref) < len(pages_cfg):
                page_data = pages_cfg[int(page_ref)]
            else:
                for item in pages_cfg:
                    if isinstance(item, dict):
                        pname = item.get("name", "")
                        if pname == page_ref or pname.lower() == page_ref.lower():
                            page_data = item
                            break
        elif isinstance(pages_cfg, dict):
            if page_ref in pages_cfg:
                page_data = pages_cfg[page_ref]
            elif page_ref.isdigit() and int(page_ref) < len(pages_cfg):
                page_data = list(pages_cfg.values())[int(page_ref)]
            else:
                for k, v in pages_cfg.items():
                    if k.lower() == page_ref.lower():
                        page_data = v
                        break

        if not page_data or not isinstance(page_data, dict) or "mermaid" not in page_data:
            return None

        project = DrawIOProject()
        theme_name = page_data.get("theme", default_theme)
        font_size = float(page_data.get("font_size", default_font_size))
        node_icons = page_data.get("node_icons")
        custom_theme = page_data.get("custom_theme")

        try:
            project.add_mermaid_page(
                name=page_ref,
                mermaid_code=page_data["mermaid"],
                theme=theme_name,
                font_size=font_size,
                node_icons=node_icons,
                custom_theme=custom_theme,
            )
            return project.export_page(0, output_path=cached_png, format="png", scale=scale)
        except Exception:
            return None

    return None
