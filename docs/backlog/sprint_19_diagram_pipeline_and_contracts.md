# Sprint 19 Implementation Runbook: Pipeline Integration & Contract Hardening

> **Sprint:** 19  
> **Status:** ✅ **COMPLETED** (2026-09-19T11:43:35+07:00 | Commit `7785eeb`)  
> **Target Subsystems:** `src/core/`, `src/docx_engine/`, `src/xlsx_engine/`, `src/ppt_engine/`  
> **Estimated Execution Time:** ~35 minutes  
> **Operating Guardrail:** [`AGENTS.md`](../../AGENTS.md) (Strict **ZERO INTERMEDIATE UNIT TESTING**).

---

## 1. Objective & Scope

Harden cross-engine contracts, eliminate silent data truncation hazards, centralize fragmented coordinate systems, and eliminate manual export friction by enabling on-demand Draw.io URI embedding directly inside Markdown technical specifications and PowerPoint deck manifests:

1. **On-Demand Draw.io URI Embedder:** Resolve `.drawio#PageName` and `.yaml#PageName` directly in `spec_compiler.py` and presentation asset pipelines, auto-rasterizing target pages to cached high-DPI PNGs.
2. **Centralized Unit Space Conversions:** Establish `src/core/units.py` with standard constants and conversion functions across Points, Inches, EMUs, Twips, and DrawingML Alpha.
3. **Pydantic Contract Hardening:** Replace polymorphic untyped dictionaries in S-Curves, Cloud Sizing, and Spec Frontmatter with validated Pydantic models.
4. **Resilience & Silent Failure Elimination:** Eliminate bare `except Exception: pass` blocks in `docx_purger.py` and `calculator_stamper.py`, and guard against silent warehouse truncation in `cloud_sizing.py`.

---

## 2. Implementation Tasks

### Task 1: Implement On-Demand Draw.io URI Embedder
- **Target Files:**
  - [`src/core/diagram_uri.py`](../../src/core/diagram_uri.py) *(NEW)*
  - [`src/docx_engine/spec_compiler.py`](../../src/docx_engine/spec_compiler.py)
  - [`src/ppt_engine/resource_manager.py`](../../src/ppt_engine/resource_manager.py)

#### 1. Create `src/core/diagram_uri.py`
Provide a dedicated URI parser and on-demand rasterizer with persistent file caching:
```python
"""
src/core/diagram_uri.py
On-demand URI resolver and rasterizer for multi-page Draw.io projects (.drawio)
and declarative diagram manifests (.yaml).
"""
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
        project = DrawIOProject.load(path_obj)
        target_page = int(page_ref) if page_ref.isdigit() else page_ref
        try:
            return project.export_page(target_page, output_path=cached_png, format="png", scale=scale)
        except Exception:
            return None

    elif suffix in (".yaml", ".yml"):
        import yaml
        from src.ppt_engine.diagram_engine import DrawIOProject, ParsedDiagram, HierarchicalLayoutEngine
        raw = yaml.safe_load(path_obj.read_text(encoding="utf-8"))
        pages_cfg = raw.get("pages", {}) if isinstance(raw, dict) else {}
        
        # Match page by name or index
        page_data = None
        if page_ref in pages_cfg:
            page_data = pages_cfg[page_ref]
        elif page_ref.isdigit() and int(page_ref) < len(pages_cfg):
            page_data = list(pages_cfg.values())[int(page_ref)]
        else:
            for k, v in pages_cfg.items():
                if k.lower() == page_ref.lower():
                    page_data = v
                    break

        if not page_data or "mermaid" not in page_data:
            return None

        project = DrawIOProject()
        theme_name = page_data.get("theme", raw.get("project", {}).get("theme", "modern_consulting"))
        font_size = page_data.get("font_size", 18.0)
        project.add_mermaid_page(
            name=page_ref,
            mermaid_code=page_data["mermaid"],
            theme=theme_name,
            font_size=font_size,
        )
        try:
            return project.export_page(0, output_path=cached_png, format="png", scale=scale)
        except Exception:
            return None

    return None
```

#### 2. Update `src/docx_engine/spec_compiler.py`
In `add_image(self, image_path: Union[str, Path], caption: Optional[str] = None)`:
```python
        # Check for Diagram URI syntax (e.g. .drawio#Page or .yaml#Page)
        str_path = str(image_path)
        if "#" in str_path:
            from src.core.diagram_uri import resolve_diagram_uri
            resolved = resolve_diagram_uri(str_path, base_dir=self.base_dir)
            if resolved and resolved.exists():
                path_obj = resolved
```

#### 3. Update `src/ppt_engine/resource_manager.py`
In `ResourceManager.resolve_asset(asset_key: str)`:
```python
        if "#" in asset_key:
            from src.core.diagram_uri import resolve_diagram_uri
            resolved = resolve_diagram_uri(asset_key)
            if resolved and resolved.exists():
                return resolved
```

---

### Task 2: Centralize Unit Constants & Coordinate Conversions
- **Target File:** [`src/core/units.py`](../../src/core/units.py) *(NEW)*

Create canonical conversions across OpenXML, python-docx, python-pptx, and DrawingML:
```python
"""
src/core/units.py
Canonical unit standardization and coordinate conversions across OpenXML,
DrawingML, python-docx, and python-pptx.
"""

# Base Conversion Multipliers
EMU_PER_INCH: int = 914400
EMU_PER_PT: int = 12700
EMU_PER_CM: int = 360000
EMU_PER_MM: int = 36000

TWIPS_PER_INCH: int = 1440
TWIPS_PER_PT: int = 20

OPENXML_BORDER_SZ_PER_PT: int = 8  # 1 pt border = val="8" in w:tcBorders
DRAWINGML_ALPHA_MAX: int = 100000   # 100% alpha opacity = 100000 in a:alpha


def pt_to_emu(pt: float) -> int:
    """Convert points (pt) to English Metric Units (EMU)."""
    return int(round(pt * EMU_PER_PT))


def emu_to_pt(emu: int) -> float:
    """Convert English Metric Units (EMU) to points (pt)."""
    return emu / EMU_PER_PT


def inches_to_emu(inches: float) -> int:
    """Convert inches to English Metric Units (EMU)."""
    return int(round(inches * EMU_PER_INCH))


def emu_to_inches(emu: int) -> float:
    """Convert English Metric Units (EMU) to inches."""
    return emu / EMU_PER_INCH


def pt_to_twips(pt: float) -> int:
    """Convert points (pt) to Word processing twips (1/20 of a pt)."""
    return int(round(pt * TWIPS_PER_PT))


def twips_to_pt(twips: int) -> float:
    """Convert Word processing twips to points (pt)."""
    return twips / TWIPS_PER_PT


def alpha_percent_to_drawingml(opacity_pct: float) -> int:
    """
    Convert opacity percentage (0.0 to 100.0 or 0.0 to 1.0) to DrawingML integer alpha.
    Example: 45% -> 45000.
    """
    factor = opacity_pct / 100.0 if opacity_pct > 1.0 else opacity_pct
    return int(round(factor * DRAWINGML_ALPHA_MAX))


def pt_to_openxml_border_sz(pt: float) -> int:
    """
    Convert points (pt) to OpenXML table/cell border size (eighths of a point).
    Example: 1.0 pt -> 8, 0.5 pt -> 4.
    """
    return int(round(pt * OPENXML_BORDER_SZ_PER_PT))
```

---

### Task 3: Define Pydantic v2 Models for Untyped Payloads
- **Target Files:**
  - [`src/xlsx_engine/schemas.py`](../../src/xlsx_engine/schemas.py) *(NEW or EXPAND)*
  - [`src/docx_engine/schemas.py`](../../src/docx_engine/schemas.py) *(NEW or EXPAND)*

#### 1. `src/xlsx_engine/schemas.py`
Define models for S-Curves and Calculator inputs:
```python
from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SCurveMilestone(BaseModel):
    id: str = Field(..., description="Unique milestone identifier (e.g. M1, M2)")
    name: str = Field(..., description="Descriptive milestone title")
    weight: float = Field(..., ge=0.0, le=100.0, description="Planned percentage weight (sum to 100)")
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_completion: Optional[date] = None
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Current progress percentage")


class SCurvePayload(BaseModel):
    project_id: str
    project_name: str
    baseline_budget_idr: float = Field(default=0.0, ge=0.0)
    total_duration_weeks: int = Field(default=12, gt=0)
    milestones: List[SCurveMilestone] = Field(default_factory=list)

    @field_validator("milestones")
    @classmethod
    def validate_weights(cls, v: List[SCurveMilestone]) -> List[SCurveMilestone]:
        if not v:
            return v
        total = sum(m.weight for m in v)
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Milestone weights must sum to 100.0% (current sum: {total:.2f}%)")
        return v


class CellMapping(BaseModel):
    sheet: Optional[str] = None
    cell: str = Field(..., regex=r"^\$?[A-Za-z]+\$?[0-9]+$")
    value: Any


class CalculatorDataPayload(BaseModel):
    cell_mappings: List[CellMapping] = Field(default_factory=list)
    append_rows: Dict[str, List[List[Any]]] = Field(default_factory=dict)
    scalar_replacements: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
```

#### 2. `src/docx_engine/schemas.py`
Define frontmatter metadata model:
```python
from typing import List, Optional
from pydantic import BaseModel, Field


class SpecSignoff(BaseModel):
    role: str
    name: str
    title: str
    status: str = "Pending"
    date: Optional[str] = None


class SpecMetadataModel(BaseModel):
    title: str
    document_id: str
    version: str = "1.0"
    classification: str = "CONFIDENTIAL"
    author: str = "Enterprise Bench"
    owner: str = "Enterprise Architecture"
    date: str
    signoffs: List[SpecSignoff] = Field(default_factory=list)
```

---

### Task 4: Fix Silent Failures & Bare Exception Blocks
- **Target Files:**
  - [`src/core/docx_purger.py`](../../src/core/docx_purger.py)
  - [`src/xlsx_engine/cloud_sizing.py`](../../src/xlsx_engine/cloud_sizing.py)
  - [`src/xlsx_engine/calculator_stamper.py`](../../src/xlsx_engine/calculator_stamper.py)

#### 1. Replace Bare `except: pass` in `docx_purger.py`
Replace all 4 instances of:
```python
except Exception:
    pass
```
With explicit error logging and inclusion into `PurgeReport.errors`:
```python
except Exception as err:
    report.errors.append(f"Failed processing {filename}: {err}")
```
*Ensure `PurgeReport` has `errors: List[str] = field(default_factory=list)`.*

#### 2. Guard Against Silent Warehouse Truncation in `cloud_sizing.py`
In `calculate_cloud_sizing(...)` before injecting warehouses:
```python
    if len(cfg.warehouses) > 8:
        raise ValueError(
            f"Snowflake Cloud Sizing template supports maximum 8 warehouse configurations; "
            f"received {len(cfg.warehouses)}. Please consolidate warehouse tiers."
        )
```

#### 3. Log Cell Injection Errors in `calculator_stamper.py`
Replace bare `except: pass` in `_apply_data`:
```python
except Exception as e:
    logger.warning("Failed injecting value into %s cell %s: %s", ws.title, cell_ref, e)
```

---

## 3. Verification Protocol

> **REMINDER:** Strict **ZERO INTERMEDIATE UNIT TESTING** ([`AGENTS.md`](../../AGENTS.md)).

1. **Syntax & Compilation Validation:**
   ```bash
   uv run python -m py_compile src/core/units.py
   uv run python -m py_compile src/core/diagram_uri.py
   uv run python -m py_compile src/docx_engine/schemas.py
   uv run python -m py_compile src/xlsx_engine/schemas.py
   uv run python -m py_compile src/core/docx_purger.py
   uv run python -m py_compile src/xlsx_engine/cloud_sizing.py
   uv run python -m py_compile src/xlsx_engine/calculator_stamper.py
   ```
2. **Diagram URI Test Invocations:**
   Verify `parse_diagram_uri` and caching behavior with a fast inline Python invocation:
   ```bash
   uv run python -c "from src.core.diagram_uri import parse_diagram_uri; print(parse_diagram_uri('presets/diagrams/fsd_architecture.yaml#System Architecture'))"
   ```
3. **Report Status:** Document completed tasks cleanly in `docs/CHANGELOG.md` upon completion.

---

## 4. Definition of Done Checklist

- [x] On-demand Draw.io URI embedder (`src/core/diagram_uri.py`) implemented with hashing and caching.
- [x] Diagram URI resolution wired into `spec_compiler.py` and `resource_manager.py`.
- [x] Canonical unit conversion constants and functions implemented in `src/core/units.py`.
- [x] Strict Pydantic v2 schemas added in `src/xlsx_engine/schemas.py` and `src/docx_engine/schemas.py`.
- [x] Bare `except: pass` traps eliminated in `docx_purger.py` and `calculator_stamper.py`.
- [x] Warehouse count validation guard ($\le 8$) added to `cloud_sizing.py`.
- [x] Static py_compile and inline URI resolution smoke verification passed with zero errors.

