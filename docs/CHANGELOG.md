# Enterprise Workbench Changelog & Architecture Updates

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
