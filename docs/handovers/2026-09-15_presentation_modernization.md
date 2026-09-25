# Handover Specification: Presentation Modernization & De-Squaring Architecture

> **Target Repository:** `enterprise-bench`  
> **Status:** Implemented & Verified (Phase A: Asset Registry & Phase B: Chapter Divider)  
> **Directives:** Enforce zero intermediate unit testing (`AGENTS.md`), use `uv run`, and preserve Git purity (`assets/images/` gitignored).

---

## 1. Architectural Vision & Context

This handover equips fresh agent contexts to modernize the PowerPoint generation engine (`src/ppt_engine/`) by addressing two core challenges:
1. **Box Fatigue / Square-ish Monotony:** Break out of repetitive 3-box/4-box card grids by introducing asymmetric split layouts (1/3 typographic anchor + 2/3 fluid photographic plates), dark gradient scrims, and unboxed hairlines.
2. **Deterministic Asset Management & Git Purity:** Protect repository history from binary bloat by keeping heavy images in `assets/images/` (gitignored), while guaranteeing zero crashes on clean clones via `assets/RESOURCE_REGISTRY.md` and an automated `missing_resources.md` diagnostic reporting system.

---

## 2. Phase A: Asset Registry & `missing_resources.md` Subsystem

### Target Module
- [`src/ppt_engine/resource_manager.py`](../../src/ppt_engine/resource_manager.py) (New core module)
- Integrated into [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py) and [`src/cli.py`](../../src/cli.py)

### Technical Specification
1. **Manifest Parsing & Resolution:**
   - Define a dataclass `ResourceSpec`:
     ```python
     @dataclass
     class ResourceSpec:
         key: str
         target_path: Path
         canonical_url: Optional[str] = None
         fallback_url: Optional[str] = None
         fallback_type: str = "typographic"  # "typographic", "gradient", "vector"
         fallback_text: str = ""
     ```
   - Default registry contains:
     * `logo_metrodata_square`: `assets/images/logos/metrodata_square.png` (Snowflake Partner CDN URL)
     * `logo_snowflake`: `assets/logos/snowflake.svg` (local vector)
     * `stock_chapter_photo`: `assets/images/stock/chapter_hero.jpg`

2. **Resolution Lifecycle (`resolve_asset(key) -> Optional[Path]`):**
   - Check if `target_path` exists on disk.
   - If missing, attempt lightweight non-blocking download via `urllib.request` (3.0s timeout).
   - If download fails or environment is offline:
     * Record failure in the active `ResourceManager` session.
     * Return `None` (triggering graceful fallback in the archetype builder).
     * Do **NOT** raise `FileNotFoundError`.

3. **`missing_resources.md` Ledger Generation:**
   - After a presentation run, if any required asset was missing and fell back, generate or update `missing_resources.md` at workspace root:
     ```markdown
     # Missing Deliverable Resources Report
     *Generated during presentation assembly at: <ISO_TIMESTAMP>*

     The following resources were missing. Presentation completed successfully using graceful fallbacks:

     | Resource Key | Expected Path | Impacted Slide | Quick Recovery Command |
     | :--- | :--- | :--- | :--- |
     | `logo_metrodata_square` | `assets/images/logos/metrodata_square.png` | Cover, Chapter Divider | `curl -sSL "https://..." -o assets/images/logos/metrodata_square.png` |
     ```
   - If all resources are present, ensure `missing_resources.md` is removed or reports clean status.

4. **CLI Integration:**
   - Add `bench ppt check-resources` to verify or download all registered assets on demand.

---

## 3. Phase B: Chapter Divider Archetype & De-Squared Layouts

### Target Module
- [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)

### Benchmark Reference
- Reference: [`output/template_previews/pitch_deck/slide_31.png`](../../output/template_previews/pitch_deck/slide_31.png) and [`slide_15.png`](../../output/template_previews/pitch_deck/slide_15.png)
- Goal: Mirror the legacy 1/3 text + 2/3 photographic plate with the square Metrodata mark, while fixing legacy contrast defects via a dark translucent scrim overlay.

### Architectural Blueprint: `build_chapter_divider_slide(...)`
```
0.0"       0.8"                      4.8"                                                 13.333"
┌──────────┬─────────────────────────┬────────────────────────────────────────────────────────┐  0.0"
│          │                         │ [ High-Res Stock Photo Plate (Right 2/3) ]             │
│          │ TRACKER BREADCRUMB      │ [ Translucent Dark Scrim Overlay (Navy/Black 45% a) ]   │
│          │ (e.g. PHASE 03 DELIVER) │                                                        │
│ (Margin) │                         │                     ┌───────────────┐                  │
│          │ Chapter Action Title    │                     │   METRODATA   │                  │
│          │ (34pt Bold Primary)     │                     │  Square Logo  │                  │
│          │                         │                     │ (592x517 px)  │                  │
│          │ Optional 2-Line Synop   │                     └───────────────┘                  │
│          │ (12pt Secondary Muted)  │               Sub-Division / Capability Tag            │
│          │                         │           "Data & AI / Snowflake Analytics"            │
└──────────┴─────────────────────────┴────────────────────────────────────────────────────────┘  7.5"
```

### Exact Geometric Coordinates:
1. **Slide Canvas:** 16:9 widescreen ($13.333'' \times 7.5''$).
2. **Left 1/3 (Typographic Narrative Panel):**
   - Background: Pure white / theme background fill.
   - Text Box: $x = 0.8''$, $y = 2.0''$, $w = 3.6''$, $h = 4.0''$.
   - Paragraph 1 (Tracker): 10pt bold uppercase, `theme.get_rgb("accent")`.
   - Paragraph 2 (Title): 32–36pt bold, `theme.get_rgb("primary")`, with `space_before = Pt(12)`.
   - Paragraph 3 (Synopsis): 11.5pt regular, `theme.get_rgb("secondary")`, with `space_before = Pt(14)`.
3. **Right 2/3 (Photographic Hero Panel):**
   - Panel Bounds: $x = 4.8''$, $y = 0.0''$, $w = 8.533''$, $h = 7.5''$.
   - If stock photo exists: Insert photo scaled to cover panel.
   - If photo missing (Fallback): Draw solid rectangle filled with deep primary color (`#0F172A` / `#1E293B`) or theme gradient.
4. **Dark Translucent Scrim Overlay (High-Contrast Guarantee):**
   - Rectangle over photo: $x = 4.8''$, $y = 0.0''$, $w = 8.533''$, $h = 7.5''$.
   - Solid fill: `#0B132B` or `#000000`.
   - Alpha transparency: $40\%\text{--}50\%$ (via OpenXML `<a:alpha val="50000"/>` or PIL scrim composite).
5. **Logo & Division Lockup:**
   - Anchor: Center of right panel ($x \approx 7.8''$, $y \approx 2.4''$, $w = 2.4''$, $h = 2.1''$).
   - Image: `assets/images/logos/metrodata_square.png`.
   - Fallback: High-contrast white typographic pill badge (`[ METRODATA ]`).
   - Subtitle Text below logo: 12pt white bold ("BAS Division  |  Data & AI Practice").

### Geometry Guardrail:
- Both left and right panel elements are sharp rectangles (`MSO_SHAPE.RECTANGLE`).
- Zero top accent stripes overlapping rounded corners.

---

## 4. Verification Protocol (Zero Test Suites)

Fresh context agents must verify without running test suites (`AGENTS.md` compliance):
1. **Verification Command:**
   ```bash
   uv run python -c "
   from src.ppt_engine.consulting_archetypes import create_presentation, build_chapter_divider_slide
   from src.ppt_engine.theme_engine import get_theme
   prs = create_presentation()
   theme = get_theme('brickred')
   build_chapter_divider_slide(prs, theme, tracker='PHASE 02: PLANNING', title='Architecture & Data Flow', subtitle='Detailed ingestion pipelines and staging schemas.')
   prs.save('output/verification_chapter_divider.pptx')
   print('Generated output/verification_chapter_divider.pptx')
   "
   ```
2. **Desktop Review:**
   ```bash
   open output/verification_chapter_divider.pptx
   ```

---

## 5. Implementation Status & Verified Deliverables

- **Core Module**: [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)
  - `build_chapter_divider_slide(...)`: Asymmetric 1/3 narrative panel + 2/3 photographic hero plate with OpenXML DrawingML 45% dark scrim overlay (`#0B132B` via `<a:alpha val="45000"/>`).
  - `ConsultingDeckBuilder.add_chapter_divider_slide(...)`: Method integration for multi-slide presentation decks.
- **Resource Integration**: Seamlessly integrated with [`src/ppt_engine/resource_manager.py`](../../src/ppt_engine/resource_manager.py) for auto-resolution and graceful fallback to solid `#0F172A` cards and typographic pill badges (`[ METRODATA ]`).
- **Exporter Enhancements**: [`src/ppt_engine/slide_exporter.py`](../../src/ppt_engine/slide_exporter.py) updated to support natural shape z-ordering and DrawingML alpha extraction in pure-Python preview exports.
- **Verified Deliverables**:
  - PPTX Output: `output/verification_chapter_divider.pptx`
  - Visual Previews: `output/verification_previews/slide_01.png` (Photo + Scrim + Logo), `slide_02.png` (Photo Fallback), `slide_03.png` (Photo & Logo Fallback).
- **Standards & Guidelines**:
  - [`AGENTS.md`](../../AGENTS.md): Enforced geometry rules, unified text frame, and 1/3 + 2/3 asymmetric composition rules.
  - [`skills/presentation-maker/SKILL.md`](../../skills/presentation-maker/SKILL.md): Added Chapter Divider archetype recipe and import references.
  - [`skills/enterprise-bench-dev/SKILL.md`](../../skills/enterprise-bench-dev/SKILL.md): Documented OpenXML alpha and de-squaring engine pattern.
