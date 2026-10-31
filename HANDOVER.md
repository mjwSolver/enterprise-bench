# AGENT HANDOVER & ACTIVE STATE POINTER

> **Repository:** `enterprise-bench` | **Branch:** `main`  
> **Mission:** Universal multi-engine enterprise automation workbench (DOCX, PPTX, XLSX, Draw.io).  
> **Architecture Ledger:** [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | **Index:** [`docs/INDEX.md`](docs/INDEX.md) | **Feature Backlog:** [`FEATURE_BACKLOG.md`](FEATURE_BACKLOG.md)  
> **Operating Guardrails:** [`AGENTS.md`](AGENTS.md) (Strict ZERO INTERMEDIATE UNIT TESTING).  
> **Retention Rule:** Retain strictly the **latest 10 active / legacy handovers** at all times ($\le 80$ lines). When a new active handover is written, the oldest legacy handover must be rotated into [`docs/handovers/handover_archive/`](docs/handovers/handover_archive/README.md) with its completion timestamp.

---

## 1. Active Platform Status & Completed Milestones

Progress: `[██████████] 100%` (Master Deliverables, Diagram Pipeline, Visual QA, Declarative Engine V2 & Vector Refinement Complete)
- **Engine / Agent Status:** `Agent Reviewed & Validated (Static QA Passed)`
- **User Review Status:** `PENDING USER DESKTOP REVIEW / Awaiting User Verification`
- **Deliverables Awaiting User QA:** `encapsulation_v2_test.pptx`, `openxml_sanitizer_verification.pptx`, `proposed_aws_lambda_stencil.svg`, `interwoven_migration.png` / `.drawio` / `.pptx`, `whitelist_system_interwoven_migration.png`, `open_interwoven_in_browser.html`, `architecture_evolution_cdsw_to_lambda.pptx` (Slides 1–7), and `bench diagram v2 audit/visual-qa` gates.

- **Tiers 1–6 (Core Subsystems & Foundations):** Legal DOCX stamping, Markdown spec compiler (`src/docx_engine/`), Snowflake sizing & S-curve models (`src/xlsx_engine/`), consulting deck engines (`src/ppt_engine/`), Draw.io multi-page pipelines (`bench diagram`), and bilingual EN/ID engines (`src/core/locale_engine.py`).
- **Tiers 7–16 (Modernized Presentation Suite & PII Purge — Milestones 18–28):** 36-slide pitch, 19-slide kick-off, 25-slide UAT, 11-slide weekly progress, 9-slide closing deck, Dewi Lestari persona, synthetic Gantt, OpenXML aspect ratio QA engine (`bench doc check/fix-aspect`), Cover Slide footer & sharp container validation, 40-48px icon floor, and automated OpenXML element purging.
- **Tiers 17–25 (Diagram Pipeline, Visual QA, Decompiler & Clearance Matrix — Milestones 29–37):** Deterministic asset harvester, DrawingML collision linter, flat aesthetic, single polyline routing, high-density consulting archetypes, interwoven migration topology, Tier 1/2 spatial and perceptual QA (`bench diagram v2 audit/visual-qa`), OpenXML shadow purger, bidirectional PPTX decompiler & AST reconciler, and Typed Semantic Clearance Matrix.
- **Tiers 26–30 (Diagram Standardization, Typographic Drift & Desktop Preview — Milestones 38–41, Releases 3–4: v2.0–v2.1):** Canonical 4-tier typographic scale, elastic text auto-fill, atomic O_CREAT hardening, Postel's Law keyword aliasing, dynamic multi-line label height, headless PowerPoint presentation dismissal (`close_target_presentation`), and Pydantic alias mapping.
- **Tier 31 (Declarative Architecture Guardrail & Headless Inspection/Patching — Release 5: v2.2):** Directive 5 codification and ADR retrospective (>90% per-turn token reduction); tri-signal AST linter (`bench ppt lint` & `.githooks/pre-commit`); zero-dependency L1 Presentation & Document Inspectors (`bench ppt view`, `bench doc view`); zero-dependency L2 DOM Micro-Patcher (`bench ppt patch`); 3-Lane Request Routing Triad formalization in `AGENTS.md`; and Directive 6 explicit semver release archive stamping (`diagram_engine_v2_portable_v<SEMVER>_<TIMESTAMP>.zip`).
- **Tier 32 (ASCII Wireframing, Typographic Density Guardrail & Headless Vision Verification — Release 6: v2.3):** Canonical layout patterns (`3-swimlane`, `interwoven-hub`, `data-pipeline`, `runbook-grid`) in `src/ppt_engine/diagram_v2/ideas.py`; deterministic ASCII wireframe preamble (`bench diagram v2 ideas [list|preview|scaffold]` & `bench diagram v2 compile --ascii`); Check #16 (`EXCESSIVE_NODE_DENSITY`) enforcing 11pt font floor and prescribing semantic aggregation with `allow_dense_typography: true` bypass valve down to 8pt for appendix runbooks; decoupled agent operating rules in `docs/specs/DIAGRAM_INSTRUCTIONS.md`; and cross-platform headless rasterization specification in `docs/specs/headless_rendering_setup.md`.

---

## 2. Key Architecture Pointers (`docs/specs/`)

- [**In-Flight Verification & Corridor Geometry**](docs/specs/in_flight_verification_and_corridor_geometry.md): Minimum connector corridor span invariant, Postel's Law constructor aliasing, deep PKZip central directory validation, and standardized subagent smoke pass.
- [**PPTX File Watcher & Geometric Sync**](docs/specs/pptx_file_watcher_and_geometric_reconciliation.md): Real-time background file watching, debounce window, lock file filtering & reverse geometric sync.
- [**PPTX Decompiler & YAML Reconciliation**](docs/specs/pptx_decompiler_and_yaml_reconciliation_engine.md): Topic 11 bidirectional AST diffing, shape taxonomies & 4-way regeneration.
- [**Adaptive Documentation Scout**](docs/specs/adaptive_documentation_scout_protocol.md): Subagent protocol, dynamic topology scouting & 5-stage closeout gate.
- [**Adaptive Complexity Gears**](docs/specs/adaptive_complexity_gears_and_enterprise_density.md): 3-gear density standard (Exec 4-5/10, Pre-KOM 6.5-7.5/10, Workstream 8.5-9.5/10).
- [**PowerPoint Slide Geometry**](docs/specs/powerpoint_slide_geometry.md): Sharp top stripes, cover typographic metadata, split chapter dividers, and diagram hierarchy.
- [**Localization & Bilingual Subsystem**](docs/specs/localization_and_bilingual_subsystem.md): Dual EN/ID catalogs, hybrid phrase translation & localized decks.
- [**Draw.io Edge Routing & Collision Prevention**](docs/specs/drawio_edge_routing_and_collision_prevention.md): Dynamic ports & gutter routing.
- [**OpenXML Document Purging**](docs/specs/openxml_purging_and_cleansing.md): Comment, highlight, and revision stripping.

---

## 3. Transition Briefings Archive (`docs/handovers/`)

- [`2026-10-31_ascii_wireframing_and_typographic_density_guardrails.md`](docs/handovers/2026-10-31_ascii_wireframing_and_typographic_density_guardrails.md): **Milestone Closeout / Release 6 (v2.3)** (ASCII wireframe preamble, canonical patterns catalog, Check #16 excessive node density guardrail, 11pt font floor, semantic aggregation, and headless rasterization spec).
- [`2026-10-26_declarative_guardrails_and_inspection_engine.md`](docs/handovers/2026-10-26_declarative_guardrails_and_inspection_engine.md): **Milestone Closeout / Release 5 (v2.2)** (Directive 5 declarative YAML-first architecture, mechanical AST linter & pre-commit hook, L1 headless PPT/DOCX inspection CLI, L2 in-situ micro-patcher, and 3-Lane Request Routing Triad).
- [`2026-10-24_desktop_preview_lifecycle_and_diagram_v2_resilience.md`](docs/handovers/2026-10-24_desktop_preview_lifecycle_and_diagram_v2_resilience.md): **Milestone Closeout / Release 4 (v2.1)** (PowerPoint preview window dismissal lifecycle, dynamic multi-line container label headroom calculation, peer container physical collision checks, and Pydantic alias mapping).
- [`2026-10-17_system_wide_hardening_and_in_flight_flight_test.md`](docs/handovers/2026-10-17_system_wide_hardening_and_in_flight_flight_test.md): **Milestone 41** (Multi-wave static hardening across core delivery locks, localization engine, scorecard models, and vector geometry; real-world in-flight PowerPoint stress test; dynamic elbow clearance remediation; and permanent in-flight verification & corridor geometry specification).
- [`2026-10-17_multi_subsystem_defect_remediation_and_parity.md`](docs/handovers/2026-10-17_multi_subsystem_defect_remediation_and_parity.md): **Milestone 40** (Multi-subsystem defect remediation across DOCX ECMA-376 schema ordering, XLSX timeline date progression inference, Column H formula preservation, reconciler AST paragraph partitioning, Draw.io custom shape SVG stencils, literal PII masking, strict Gate 5 DRAFT overlay enforcement, full-deck shadow stripping, and unified 90.0 DPI scaling).
- [`2026-10-16_autonomous_pptx_file_watcher_and_geometric_sync.md`](docs/handovers/2026-10-16_autonomous_pptx_file_watcher_and_geometric_sync.md): **Topic 12** (Autonomous PPTX file watcher daemon, reverse geometric coordinate diffing & $0.05''$ grid snapping across containers/nodes/badges/bullet lists, 500ms debounce, lock-file filtering, `--skip-pptx` origin suppression, and `bench diagram v2 watch` CLI).
- [`2026-10-16_typographic_scale_drift_and_elastic_autofill.md`](docs/handovers/2026-10-16_typographic_scale_drift_and_elastic_autofill.md): **Milestone 39** (Canonical 4-tier geometric typographic scale, Check #14 `TYPOGRAPHIC_SCALE_DRIFT` linter, 4-step elastic typography auto-fill expanding underfilled execution cards, Check #15 `UNDERFILLED_EXECUTION_CARD`, and cross-compiler font resolver unification).
- [`2026-10-16_diagram_v2_standardization_tracks_1_and_2.md`](docs/handovers/2026-10-16_diagram_v2_standardization_tracks_1_and_2.md): **Milestone 38** (DeckHeaderContract immutable header constants, Check #15 `DECK_HEADER_DRIFT` linter, canonical container ingress line $y \ge 1.350''$, Default Bottom-Edge Container Label Policy with $0.55''$ top corridor reclaim, dynamic obstruction bypass, and Model 2.1 Stray Harvester & Consolidator CLI).
- [`2026-10-16_typed_clearance_matrix_and_virtual_text_estimation.md`](docs/handovers/2026-10-16_typed_clearance_matrix_and_virtual_text_estimation.md): **Milestone 37** (Typed Semantic Clearance Matrix in auditor, virtual text bounding box height estimation catching text overflow before compilation, container boundary label textbox hitbox clamping from 4.40in to 1.67in, ContainerSpec/NodeSpec schema additions, and contractor layout instructions).
- [`2026-10-16_bidirectional_pptx_decompiler_and_reconciliation.md`](docs/handovers/2026-10-16_bidirectional_pptx_decompiler_and_reconciliation.md): **Milestone 36** (Bidirectional PPTX decompiler & YAML reconciliation engine, deterministic OpenXML shape naming taxonomy, lossless slide decompiler, AST diffing & pruning cascade, and `bench diagram v2 reconcile` CLI).
- [`2026-10-15_visual_vector_refinement_and_openxml_purge.md`](docs/handovers/2026-10-15_visual_vector_refinement_and_openxml_purge.md): **Milestone 35** (Visual & vector system refinement, sharp container swimlanes enclosing rounded icon+title cards, universal OpenXML drop shadow sanitizer `strip_shape_shadows()` reducing 821 defects across 874 shapes to 0, headless Draw.io vector stencil extraction CLI `export_drawio_stencil_to_svg()`, and Diagram Engine V2 spatial auditor vertical auto-offset calibration).
- *Historical handovers archived in [`docs/handovers/handover_archive/`](docs/handovers/handover_archive/README.md) (23 archived briefs).*


---

## 4. Immediate Next Backlog (Fresh Chat)

1. **Single-Command Atomic Desktop Hot-Reload:** Single-command workflow (`uv run bench diagram v2 compile --target <deck.pptx> --slide <num> --pop`) integrating Tier 1 preflight audits, AppleScript PowerPoint close/reopen, and in-place DrawingML replacement per [`docs/backlog/atomic_desktop_hot_reload.md`](docs/backlog/atomic_desktop_hot_reload.md).
2. **Consulting Presentation Generator Deep Integration:** Backport Diagram Engine V2 declarative compiler into consulting presentation builders (`src/ppt_engine/slide_builders.py`).
3. **Multi-Track Enterprise Template Harvesting:** Author declarative topologies under `specs/diagrams/` (Medallion Architecture, Active-Active DR, Streaming CDC Telemetry).
4. **Tier 2 Adversarial Visual QA Perceptual Scanner Expansion:** Add automated WCAG AA ($4.5:1$) contrast checks and multi-resolution font legibility scanners to `bench diagram v2 visual-qa`.
