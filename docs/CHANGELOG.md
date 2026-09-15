# Enterprise Workbench Changelog & Architecture Updates

## [2026-09-15] - Slide Geometry Containment, 3-Column Diagram Re-Architecture & Ingress Bus Specification

### Summary
Fixed PowerPoint slide overflow defects where unconstrained aspect-ratio scaling drove diagrams into the slide footer ($7.49"$ on $7.50"$ slides), eliminated $>450,000\text{ px}^2$ of dead whitespace in Draw.io diagrams by re-architecting to balanced 3-column layouts ($2.77:1$), implemented macOS live presentation concurrency automation, and authored an engineering handover specification for Ingress Bus edge bundling.

---

### Key Additions & Changes

#### 1. Presentation Geometry & Footer Collision Defense (`scripts/`)
- Diagnosed single-dimension image scaling in `python-pptx`: passing only `width` caused squarish diagrams ($1.22:1$) to expand to $5.57"$ height, overflowing the $5.10"$ container card and colliding with slide footers ($Y \ge 6.90"$).
- Implemented `fit_image_within_bounds()` dual-constraint containment calculation in [`scripts/generate_xyz_decks.py`](../scripts/generate_xyz_decks.py) and [`scripts/generate_xyz_enhanced_visual_deck.py`](../scripts/generate_xyz_enhanced_visual_deck.py).
- Guaranteed container centering and strict bottom-margin safety ($Y = 5.50"$, maintaining $1.40"$ clear headroom above the footer line).

#### 2. Diagram Architecture & Whitespace Elimination (`src/ppt_engine/diagram_engine.py`)
- Identified root cause of dead whitespace in `01_ingestion_streaming`: asymmetrical top-horizontal + left-vertical layout leaving $>450,000\text{ px}^2$ empty in the lower-right quadrant.
- Restructured `page_ingestion___streaming` in [`output/proj-xyz/diagrams/xyz_platform_architecture.drawio`](../output/proj-xyz/diagrams/xyz_platform_architecture.drawio) into a balanced 3-column columnar layout (`flowchart LR`, $2.77:1$ aspect ratio):
  - **Column 1:** Omni-Channel Event Sources (`APP`, `POS`, `WEB`, `ERP`).
  - **Column 2:** Real-Time Streaming Core (`GW`, `KAFKA`, `SPARK`).
  - **Column 3:** Cloud Landing Zone (`S3`, `SNOW_RAW`).
- Embedded official vector logos from `assets/logos/` and `assets/icons/lucide/` on all nodes.
- Re-exported vector SVG and 300-DPI PNG assets via Cairo rasterizer.

#### 3. Live Desktop Automation & Concurrency Lock Protocol
- Integrated safe PowerPoint process lock handling using AppleScript (`osascript`) to close active presentations without blocking prompts, rebuild PPTX decks, and auto-focus target slides on macOS.

#### 4. Ingress Bus & Edge Bundling Handover Specification (`docs/`)
- Authored comprehensive platform engineering specification in [`docs/HANDOVER_INGRESS_BUS_ROUTING.md`](HANDOVER_INGRESS_BUS_ROUTING.md) detailing shared inter-column trunk-line routing to eliminate orthogonal connector clutter ("mess of cables") across columnar subgraphs.

---

## [2026-09-11] - Consolidation of PPT Engine & Core Suite Launch

### Summary
Consolidated the presentation engine from `PPTMaking` into `enterprise-bench`, created the shared core infrastructure, implemented the deterministic Word document generation and linting engine, and established the unified `bench` CLI.

---

### Key Additions & Changes

#### 1. Presentation Engine (`src/ppt_engine/`)
- Consolidated generative slide layouting and consulting archetypes:
  - [`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py): BCG 3-Horizon modernization and Balanced Scorecard 2x2 matrix builders.
  - [`src/ppt_engine/diagram_engine.py`](../src/ppt_engine/diagram_engine.py): Mermaid to Draw.io vector compiler.
  - [`src/ppt_engine/theme_engine.py`](../src/ppt_engine/theme_engine.py): 60-30-10 palette validation and multi-theme YAML loader.
  - [`src/ppt_engine/slide_validator.py`](../src/ppt_engine/slide_validator.py): Bounding box overlap and geometry collision detection.
  - [`src/ppt_engine/slide_exporter.py`](../src/ppt_engine/slide_exporter.py): Multi-backend headless slide-to-PNG exporter.
  - [`src/ppt_engine/icon_engine.py`](../src/ppt_engine/icon_engine.py): Anti-emoji dynamic vector tinting.
- Migrated presets to [`presets/themes/`](../presets/themes/) (`brickred`, `snowblue`, `default`) and icon assets to [`assets/icons/`](../assets/icons/).

#### 2. Core Foundations (`src/core/`)
- [`src/core/config.py`](../src/core/config.py): Centralized directory registry and output sandboxing.
- [`src/core/models.py`](../src/core/models.py): Pydantic v2 data models for `ProjectInfo`, `BASTPayload`, `MoMPayload`, `Stakeholder`, and `Milestone`.
- [`src/core/theme.py`](../src/core/theme.py): Unified theme tokens bridging slide palettes with document styling.
- [`src/core/sanitizer.py`](../src/core/sanitizer.py): Regex PII scrubber replacing sensitive client identifiers with generic Jinja tokens.

#### 3. Deterministic Document Engine (`src/docx_engine/`)
- [`src/docx_engine/template_stamper.py`](../src/docx_engine/template_stamper.py): `docxtpl` / Jinja2 document generator with on-the-fly Mermaid diagram compilation.
- [`src/docx_engine/table_engine.py`](../src/docx_engine/table_engine.py): OpenXML table shading, row split prevention (`cantSplit`), and repeating header styling (`tblHeader`).
- [`src/docx_engine/document_linter.py`](../src/docx_engine/document_linter.py): Automated structural validator detecting unrendered tags and table anomalies.

#### 4. Unified CLI (`src/cli.py` / `bench`)
- Added Typer command groups:
  - `bench init-project <ProjectName>`: Scaffolded output directory and project manifest.
  - `bench ppt themes`: Table view of active brand palettes.
  - `bench ppt generate`: Deck builder utilizing BCG 3-Horizon and Balanced Scorecard archetypes.
  - `bench doc sanitize`: PII-scrubbing command.
  - `bench doc stamp`: Variable-stamping command.
  - `bench doc lint`: QA verification command.

#### 5. Verification Suite (`tests/`)
- [`tests/test_core.py`](../tests/test_core.py): Validates theme loading, hex parsing, PII sanitization, and Pydantic models.
- [`tests/test_docx_engine.py`](../tests/test_docx_engine.py): Tests OpenXML table styling and document linter error catching.
- [`tests/test_ppt_engine.py`](../tests/test_ppt_engine.py): Verifies presentation creation and archetype layout rendering.
- Suite status: **9 passed in 0.30s**.
