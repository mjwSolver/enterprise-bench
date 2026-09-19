# Enterprise Workbench Changelog & Architectural History

This document serves as the **authoritative, chronological historical ledger** of all completed platform milestones, architectural changes, engine expansions, and subsystem implementations across `enterprise-bench`.

---

## [2026-09-19] - Sprints 17–20: Security Hardening, Change Request CLI, Diagram Pipeline & Consulting Archetypes

### Summary
Delivered a 4-sprint batch execution hardening engine security and performance, operationalizing Change Request governance and project closeouts via CLI, establishing an on-demand Draw.io and declarative diagram URI pipeline, centralizing OpenXML/DrawingML coordinate conversions, and introducing executive Delivery Gantt and Harvey Balls scorecard slide archetypes.

### Milestones Delivered
- **Milestone 18 (Sprint 17: Security Hardening & Engine Optimization):**
  - **Command Injection Elimination ([`src/cli.py`](../src/cli.py)):** Replaced vulnerable `shell=True` subprocess calls in desktop PowerPoint review launchers with discrete parameter lists.
  - **Diagram DAG Ranking Optimization ([`src/ppt_engine/diagram_engine.py`](../src/ppt_engine/diagram_engine.py)):** Replaced $O(2^V)$ exponential DFS in `_assign_ranks` with Kahn's algorithm topological BFS ($O(V + E)$), preventing stack overflows and recursion errors on complex diamond topologies.
  - **Font Cache Memoization ([`src/ppt_engine/slide_exporter.py`](../src/ppt_engine/slide_exporter.py)):** Decorated `_get_system_font` with `@functools.lru_cache(maxsize=128)`, eliminating thousands of disk I/O hits per presentation export.
  - **PII Case-Insensitive Matching ([`src/core/pii/handlers/`](../src/core/pii/handlers/)):** Fixed case-sensitivity containment checks across `.docx`, `.pptx`, and `.xlsx` PII replacement handlers.
- **Milestone 19 (Sprint 18: Change Request CLI & Project Closeout):**
  - **Change Request CLI ([`src/cli.py`](../src/cli.py)):** Registered `bench cr file` command connected to `ChangeRequestProcessor`, automating 4 production master templates simultaneously (`Change_Request_Form.docx`, `Change_Log_Ledger.xlsx`, `CR_Scoping_and_Mandays.xlsx`, `BAST_Change_Request.docx`).
  - **Closeout Checklist Gate ([`src/cli.py`](../src/cli.py)):** Added `bench xlsx update-closeout` updating deliverable sign-offs in `5.2_Project_Closeout_Checklist_Template.xlsx`.
  - **Bilingual Governance Dictionaries ([`presets/locales/`](../presets/locales/)):** Expanded `en.yaml` and `id.yaml` with Change Request categories, approval statuses, and closeout sections.
- **Milestone 20 (Sprint 19: Diagram Pipeline, Units & Strict Contracts):**
  - **On-Demand Diagram URI Embedder ([`src/core/diagram_uri.py`](../src/core/diagram_uri.py)):** Built `resolve_diagram_uri` enabling `.drawio#Page` and `.yaml#Page` embedding directly within Markdown specifications and presentation asset resolution with automated disk caching.
  - **Centralized Coordinate Conversions ([`src/core/units.py`](../src/core/units.py)):** Standardized unit multipliers (`EMU`, `Twips`, `1/8 pt`, `DrawingML Alpha`) and conversion functions across OpenXML, DrawingML, python-docx, and python-pptx.
  - **Pydantic Schemas ([`src/xlsx_engine/schemas.py`](../src/xlsx_engine/schemas.py), [`src/docx_engine/schemas.py`](../src/docx_engine/schemas.py)):** Codified strict v2 schemas for S-Curve inputs, spreadsheet cell mappings, and document frontmatter metadata.
  - **Silent Failure Elimination:** Added error tracking in `docx_purger.py`, warehouse size validation ($\le 8$) in `cloud_sizing.py`, and structured logging in `calculator_stamper.py`.
- **Milestone 21 (Sprint 20: Visual Archetypes & Deck Builders):**
  - **Delivery Gantt Timeline Archetype ([`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py)):** Implemented `build_timeline_gantt_slide` featuring calendar column axis (Weeks 1–12), workstream streams, duration bars, milestone diamonds, and a vertical "Current SPRINT" marker.
  - **Harvey Balls Feature Scorecard Archetype ([`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py)):** Implemented `build_feature_matrix_slide` supporting Harvey Balls glyphs (`● ◐ ○`) and target platform highlighting.
  - **Deck Builder Integration:** Added `add_timeline_gantt_slide` and `add_feature_matrix_slide` to `ConsultingDeckBuilder` and `ReferenceDeckBuilder`.
  - Reference Handover: [`docs/handovers/2026-09-19_sprints_17_20_platform_hardening_cr_cli_diagram_and_archetypes.md`](handovers/2026-09-19_sprints_17_20_platform_hardening_cr_cli_diagram_and_archetypes.md)

---

## [2026-09-18] - Localization & Bilingual Subsystem: Dual Catalogs (EN/ID), Hybrid Translation & Paired Reference Decks

### Summary
Delivered the Enterprise Localization and Bilingual Subsystem (`en` / `id`), enabling presentation collateral and consulting deliverables to seamlessly support canonical English and formal Indonesian enterprise governance vocabulary while preserving international cloud technology standards.

### Milestones Delivered
- **Milestone 17: Localization & Bilingual Subsystem (`en` / `id`):**
  - **Static Dictionaries (`presets/locales/`):** Authored [`presets/locales/en.yaml`](../presets/locales/en.yaml) and [`presets/locales/id.yaml`](../presets/locales/id.yaml) covering UI metadata, consulting reference slides, process pipelines, and a bidirectional PMO glossary.
  - **Core Locale Engine ([`src/core/locale_engine.py`](../src/core/locale_engine.py)):** Built zero-dependency `LocaleEngine` supporting cached loading, dot-notation key lookup, safe English fallback, dynamic placeholder interpolation, term translation, and regex-based hybrid sentence translation (`translate_hybrid`).
  - **Presentation Engine Localization ([`src/ppt_engine/reference_slides.py`](../src/ppt_engine/reference_slides.py)):** Parameterized metadata labels across cover slides (`build_cover_slide`, `build_hero_cover_slide`) and wired `locale` through reference slide builders and `ReferenceDeckBuilder`.
  - **Unified CLI Extension ([`src/cli.py`](../src/cli.py)):** Added `bench locale list`, `bench locale get`, and `bench locale translate` commands, plus `--locale / -l` override to `bench ppt build-deck`.
  - **Paired Reference Master Decks:** Built `output/presentations/Enterprise_Reference_Master_Deck_EN.pptx` and `output/presentations/Enterprise_Reference_Master_Deck_ID.pptx` from declarative YAML configurations.
  - Handover & Spec: [`docs/specs/localization_and_bilingual_subsystem.md`](specs/localization_and_bilingual_subsystem.md) and [`docs/handovers/2026-09-18_localization_and_bilingual_subsystems.md`](handovers/2026-09-18_localization_and_bilingual_subsystems.md).

---

## [2026-09-16] - Universal Deliverable Recreation: Slide Geometry, Tier 3 Financial XLSX Suite, Tier 1 Legal DOCX & PII Audit Guardrail

### Summary
Delivered high-fidelity consulting slide geometry refactoring with DirectWrite-matching headless exports, established the Tier 3 Financial XLSX suite (Snowflake cloud sizing, automated timeline-to-S-curve synchronization, and RAID/defect loggers), operationalized Tier 1 deterministic legal stamping with attendee auto-expansion, and launched an automated multi-format PII leak linter.

### Milestones Delivered
- **Milestone 12: Standalone S-Curve Progress Engine & OpenXML LineChart Injection:**
  - Engineered [`src/xlsx_engine/s_curve_generator.py`](../src/xlsx_engine/s_curve_generator.py) implementing Sigmoid, cubic smoothstep, quintic smootherstep, and linear baselines.
  - Added schedule variance ($SV$), relative $SV\%$, Schedule Performance Index ($SPI = EV/PV$), and milestone health indicators (`ON_TRACK`, `AT_RISK`, `CRITICAL_DELAY`).
  - Automated 5-card KPI header blocks and formatted data tables with OpenXML `=IF(ISBLANK(...))` formulas.
  - Automated openpyxl `LineChart` construction with Primary Navy `#1E3A8A` planned line and Emerald Green `#10B981` actual curve.
  - CLI: `bench xlsx s-curve`.
- **Milestone 13: Weekly Progress Presentation Deck Polish & DirectWrite Typography Simulator:**
  - Refactored Slide 8 risk `[R-02]` into authentic adverse condition (*"Incomplete Source Schema & Key Discrepancies"*) preserving severity-first left-to-right hierarchy.
  - Enforced container accent color inheritance across top stripes, icon container borders, badge fills (`badge_*_fill`), and vector icon raster strokes.
  - Implemented universal hanging indents across native DrawingML (`<a:buChar char="•"/>`) and headless Pillow renderer ([`src/ppt_engine/slide_exporter.py`](../src/ppt_engine/slide_exporter.py)).
  - Re-architected Slide 3 executive summary with fixed-height title blocks (`Inches(0.58)`), centered uppercase tags, and zero baseline drift.
  - DirectWrite DPI Simulator: Stripped `* 1.33` artificial scaling bug so headless PNG previews match PowerPoint 1:1.
- **Milestone 14: Tier 3 Financial & Analytical XLSX Suite:**
  - Snowflake Infrastructure Sizing ([`src/xlsx_engine/cloud_sizing.py`](../src/xlsx_engine/cloud_sizing.py)): Parameterized virtual warehouse compute (XS–4XL), storage, Cortex AI, training, and tier totals in USD & IDR on `Cloud_Sizing_Calculator_Template.xlsx` preserving all native Excel formulas. CLI: `bench xlsx cloud-sizing`.
  - Timeline-to-S-Curve Synchronizer ([`src/xlsx_engine/timeline_aggregator.py`](../src/xlsx_engine/timeline_aggregator.py)): Aggregates 170 daily progress tracking columns in `4.2_Weekly_Progress_Timeline_Update_Template.xlsx` into weekly intervals, calculating Planned %, Actual %, Schedule Variance, and SPI, and injecting an executive `S-Curve Analysis` tab with openpyxl `LineChart`. CLI: `bench xlsx sync-s-curve`.
  - RAID, Defect & Governance Ledgers ([`src/xlsx_engine/ledger_models.py`](../src/xlsx_engine/ledger_models.py)): Safe row injectors for `3.6_Defect_List_Template.xlsx`, `1.3_Stakeholders_Register_Template.xlsx`, `4.5_Risk_Register_Template.xlsx`, and `4.6_Issue_Log_Template.xlsx` preserving `=ROWS(INDIRECT(...))` formulas. CLI: `append-defect`, `append-stakeholder`.
- **Milestone 15: Tier 1 Legal DOCX Stamping & Universal PII Guardrail:**
  - Cleansed residual legacy client entities in `Perjanjian_Kerjasama_PKS_Template.docx` and `1.2_Project_Charter_Template.docx` in `clean_workspace/`. Confirmed OpenXML AST integrity across `2.3_Functional_Specification_Document_FSD_Template.docx`.
  - Attendee Auto-Expansion ([`src/docx_engine/template_stamper.py`](../src/docx_engine/template_stamper.py)): Dynamically unpacks attendee lists into indexed scalar slots (`client_attendee_1..10`, `vendor_attendee_1..10`) during `docxtpl` rendering.
  - Universal Slug Registry & PII Linter ([`src/core/slug_registry.py`](../src/core/slug_registry.py)): Codified standard slug taxonomy (`[CLIENT_COMPANY_NAME]`, `[CONTRACT_NUMBER]`, etc.) and multi-format scanner (`.docx`, `.pptx`, `.xlsx`). CLI: `bench pii audit`. Verified 0 leaks across all outputs.
- **Milestone 16: Tier 2 Modular Spec Compiler & Tier 5 Multi-Page Diagramming Engine:**
  - Modular Spec Compiler ([`src/docx_engine/spec_compiler.py`](../src/docx_engine/spec_compiler.py)): Multi-chapter Markdown compiler parsing frontmatter, H1–H4 headings, callout alerts (`> [!NOTE]`), tables, and code callouts into styled Word deliverables with corporate cover pages. Added Markdown image parser (`![Caption](path)`) embedding centered high-DPI figures with italicized captions.
  - Linter Calibration ([`src/docx_engine/document_linter.py`](../src/docx_engine/document_linter.py)): Monospace `Consolas` callouts containing dbt Jinja macros (`{{ ref(...) }}`) recognized as literal code examples rather than unrendered template errors. Compiled TSD and SIT/UAT specs passing QA with 0 errors.
  - Multi-Page Draw.io Engine ([`src/ppt_engine/diagram_engine.py`](../src/ppt_engine/diagram_engine.py)): Added `export_all_pages()` and `build_from_config()` to `DrawIOProject`. Added CLI commands `bench diagram export-all` and `bench diagram build-project`.
  - Declarative Diagram Specification ([`presets/diagrams/fsd_architecture.yaml`](../presets/diagrams/fsd_architecture.yaml)): Authored 17 reporting dataflows and entity models with vector tech logos (`snowflake`, `dbt`, `kafka`, `amazons3`, `vault`, `aws`, `pos_store`, `audit_log`, `soc2_badge`), compiled into 17-tab `.drawio` and exported to high-DPI PNGs.
- Reference Handover: [`docs/handovers/2026-09-16_universal_deliverable_recreation.md`](handovers/2026-09-16_universal_deliverable_recreation.md)

---

## [2026-09-15] - Slide Geometry Containment, 3-Column Diagram Re-Architecture & Presentation Modernization

### Summary
Fixed PowerPoint slide overflow defects where unconstrained aspect-ratio scaling drove diagrams into slide footers, eliminated $>450,000\text{ px}^2$ of dead whitespace in Draw.io diagrams by re-architecting to balanced 3-column layouts ($2.77:1$), implemented macOS live presentation concurrency automation, and engineered edge routing and presentation modernization subsystems.

### Milestones Delivered
- **Milestone 8: Slide Geometry Containment & 3-Column Diagram Re-Architecture:**
  - Implemented `fit_image_within_bounds()` dual-constraint containment in `scripts/generate_xyz_decks.py` and `scripts/generate_xyz_enhanced_visual_deck.py` preventing squarish ($1.22:1$) diagrams from colliding with slide footers ($Y \ge 6.90"$).
  - Restructured `page_ingestion___streaming` in `xyz_platform_architecture.drawio` into a balanced 3-column columnar layout (`flowchart LR`, $2.77:1$ aspect ratio) with vector tech logos.
  - Integrated macOS safe PowerPoint lock handling via AppleScript (`osascript`) to reload presentations without blocking prompts.
  - Handover & Spec: [`docs/specs/ingress_bus_routing_architecture.md`](specs/ingress_bus_routing_architecture.md).
- **Milestone 9: Diagram Edge Routing & Collision Prevention Subsystem:**
  - Dynamic Port Anchoring: Evaluated $(\Delta x, \Delta y)$ in `DrawIOConverter._build_edge_style` to assign directional exit/entry ports, eliminating hardcoded `exitX=1` loops.
  - Vertical Obstacle Detection & Bypass: Added intermediate card detection in `DiagramRenderer.render_svg` to jog $24\text{ pt}$ around intermediate obstacles.
  - Inter-Column Gutter Routing: Shifted vertical step channels into inter-column gutters ($sg.x \pm 18\text{ pt}$) to prevent slicing through container centers.
  - Architectural Spec: [`docs/specs/drawio_edge_routing_and_collision_prevention.md`](specs/drawio_edge_routing_and_collision_prevention.md).
- **Milestone 10: Presentation Asset Resolution & Missing Resource Reporting Subsystem:**
  - Deterministic Asset Resolution ([`src/ppt_engine/resource_manager.py`](../src/ppt_engine/resource_manager.py)): Local asset verification, silent 3-second non-blocking download attempts, and zero-crash graceful fallbacks.
  - Diagnostic Ledger Generation (`missing_resources.md`): Automated workspace root report detailing missing resource keys and exact `curl` recovery commands.
  - CLI: `uv run bench ppt check-resources`.
- **Milestone 11: Modern De-Squared Chapter Divider Slide Archetype:**
  - Built `build_chapter_divider_slide(...)` and `ConsultingDeckBuilder.add_chapter_divider_slide(...)` in [`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py) with asymmetric 1/3 narrative panel and 2/3 hero photographic plate.
  - Unified header text frame with exact `space_before` offsets (zero coordinate collision).
  - OpenXML DrawingML 45% dark scrim overlay (`#0B132B` via `<a:alpha val="45000"/>`).
  - Single-pass painter's algorithm respecting natural shape z-ordering in [`src/ppt_engine/slide_exporter.py`](../src/ppt_engine/slide_exporter.py).
- Reference Handover: [`docs/handovers/2026-09-15_presentation_modernization.md`](handovers/2026-09-15_presentation_modernization.md)

---

## [2026-09-11] - Core Engine Consolidation, Document Purging & CLI Launch

### Summary
Consolidated the presentation engine from `PPTMaking` into `enterprise-bench`, created shared core infrastructure, implemented deterministic Word document generation and linting, engineered zero-corruption OpenXML purging, added local desktop app previewing, and established the unified `bench` CLI.

### Milestones Delivered
- **Milestone 1: Migrate `PPTMaking` into `src/ppt_engine/`:**
  - Consolidated generative slide layouting, consulting archetypes (BCG 3-Horizon, Balanced Scorecard 2x2 matrix), Mermaid-to-Draw.io compiler, and 60-30-10 palette validation into [`src/ppt_engine/`](../src/ppt_engine/).
  - Migrated themes to `presets/themes/` and icon assets to `assets/icons/`.
- **Milestone 2: Build `src/core/` Shared Foundations:**
  - Implemented centralized directory registry ([`src/core/config.py`](../src/core/config.py)), Pydantic v2 data models ([`src/core/models.py`](../src/core/models.py)), unified brand theme tokens ([`src/core/theme.py`](../src/core/theme.py)), and PII regex scrubber ([`src/core/sanitizer.py`](../src/core/sanitizer.py)).
- **Milestone 3: Build `src/docx_engine/` Deterministic Document Engine:**
  - Implemented `docxtpl` / Jinja2 template stamper with on-the-fly Mermaid diagram compilation ([`src/docx_engine/template_stamper.py`](../src/docx_engine/template_stamper.py)).
  - Implemented OpenXML table styling with repeating headers and row-split protection ([`src/docx_engine/table_engine.py`](../src/docx_engine/table_engine.py)).
  - Implemented automated structural document linter ([`src/docx_engine/document_linter.py`](../src/docx_engine/document_linter.py)).
- **Milestone 4: Implement Unified CLI (`src/cli.py` / `bench`):**
  - Exposed Typer command groups: `bench init-project`, `bench ppt themes`, `bench ppt generate`, `bench doc sanitize`, `bench doc stamp`, `bench doc lint`.
- **Milestone 5: Initial Core Verification Suite (`tests/`):**
  - Unit test coverage across theme loading, hex parsing, PII sanitization, and Pydantic models (9 passed in 0.30s).
- **Milestone 6: Desktop Native App Preview Subsystem (`skills/local-app-preview/`):**
  - Implemented macOS `open` + AppleScript (`osascript`) workflow to launch and auto-focus Word, Excel, PowerPoint, and Preview.
  - Codified desktop preview protocols in `AGENTS.md` and `skills/local-app-preview/SKILL.md`.
- **Milestone 7: Zero-Corruption OpenXML Purging Subsystem (`src/core/docx_purger.py`):**
  - Engineered zero-corruption comment, highlight, tracked revision, and author profile purging for `.docx`.
  - Integrated into `src/core/sanitizer.py` and exposed via `uv run bench doc purge`.
  - Authored comprehensive architectural runbook: [`docs/specs/openxml_purging_and_cleansing.md`](specs/openxml_purging_and_cleansing.md).
- Reference Handover: [`docs/handovers/2026-09-11_cli_skills_refactoring.md`](handovers/2026-09-11_cli_skills_refactoring.md)
