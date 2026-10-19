# Enterprise Workbench Documentation Hub

This directory contains the central documentation, architectural blueprints, subsystem specifications, historical handovers, and roadmaps for `enterprise-bench`.

---

## 🧭 Directory Taxonomy & Operating Rules

```text
docs/
├── INDEX.md               # This master navigation index
├── CHANGELOG.md           # Authoritative historical milestone ledger (Milestones 1–28+)
│
├── handovers/             # Historical sprint and session handover briefings (Latest 10 active)
│   ├── handover_archive/  # Completed briefings rotated out to preserve 10-handover limit
│   │   ├── README.md      # Archive catalog with completion timestamps
│   │   └── ...            # 20 archived briefings
│   ├── CONTRACTOR_INSTRUCTIONS.md
│   ├── 2026-10-14_cdsw_to_lambda_architecture_evolution.md
│   ├── 2026-10-14_interwoven_migration_topology_and_whitelisting.md
│   ├── 2026-10-14_tier1_collision_linting_and_tier2_adversarial_visual_qa.md
│   ├── 2026-10-15_visual_vector_refinement_and_openxml_purge.md
│   ├── 2026-10-16_bidirectional_pptx_decompiler_and_reconciliation.md
│   ├── 2026-10-16_typed_clearance_matrix_and_virtual_text_estimation.md
│   ├── 2026-10-16_diagram_v2_standardization_tracks_1_and_2.md
│   ├── 2026-10-16_typographic_scale_drift_and_elastic_autofill.md
│   ├── 2026-10-16_autonomous_pptx_file_watcher_and_geometric_sync.md
│   └── 2026-10-17_multi_subsystem_defect_remediation_and_parity.md
│
├── specs/                 # Permanent architectural references, runbooks & ADRs
│   ├── adaptive_complexity_gears_and_enterprise_density.md
│   ├── adaptive_documentation_scout_protocol.md
│   ├── adr_drawio_pipeline_vs_mcp.md
│   ├── change_request_subsystem.md
│   ├── diagram_engine_v2_export_sop.md
│   ├── document_anchored_deliverable_architecture.md
│   ├── drawio_edge_routing_and_collision_prevention.md
│   ├── drawio_icon_system_architecture.md
│   ├── ingress_bus_routing_architecture.md
│   ├── lifecycle_architecture.md
│   ├── localization_and_bilingual_subsystem.md
│   ├── manual_identity_guide.md
│   ├── master_deliverable_recreation_plan.md
│   ├── openxml_purging_and_cleansing.md
│   └── powerpoint_slide_geometry.md
│
└── backlog/               # Future sprint roadmaps, design proposals & backlogs
    ├── atomic_desktop_hot_reload.md
    ├── cover_slide_hero_and_opening_modernization.md
    ├── deck_header_contract_and_linter.md
    ├── default_container_label_policy.md
    ├── diagram_architecture.md
    ├── diagram_pipeline_and_asset_integration_roadmap.md
    ├── diagram_v2_constraint_layout_solver.md
    ├── elastic_typography_autofill.md
    ├── localization_and_bilingual_deck_subsystem.md
    ├── mermaid_to_yaml_transpiler.md
    ├── pii_clearing_backlog.md
    ├── pitch_deck_screenshot_modernization.md
    ├── remote_cloud_drift_and_race_condition_guard.md
    ├── slide_design_variety.md
    ├── sprint_17_security_and_performance_quickwins.md
    ├── sprint_18_change_request_cli_and_closeout.md
    ├── sprint_19_diagram_pipeline_and_contracts.md
    ├── sprint_20_visual_archetypes_and_deck_builders.md
    ├── template_variable_and_slug_consolidation.md
    └── typographic_scale_consistency_checker.md
```

---

## 🏛️ Documentation Standards for Agents

1. **Active State vs. Historical Log:**
   - **Root [`HANDOVER.md`](../HANDOVER.md)** is strictly a **lean pointer** to the current active sprint state and immediate next tasks ($\le 80$ lines). Retains strictly the **latest 10 active / legacy handovers**; older handovers are rotated into [`docs/handovers/handover_archive/`](handovers/handover_archive/README.md).
   - All historical milestone completions are logged in [`docs/CHANGELOG.md`](CHANGELOG.md).
   - End-of-sprint transition briefings are authored in [`docs/handovers/`](handovers/) with the naming pattern `YYYY-MM-DD_<topic>.md`.
2. **Subsystem Specifications:**
   - Technical documentation explaining *how a subsystem or engine functions* must live in [`docs/specs/`](specs/). Never prefix technical specifications with `HANDOVER_`.
3. **Roadmaps and Proposals:**
   - Unscheduled initiatives, exploratory slide archetypes, and feature proposals live in [`docs/backlog/`](backlog/). When implemented, their functional spec moves to `specs/` and an entry is logged in `CHANGELOG.md`.

---

## 📚 Master Index

### 1. Active Specifications & Architecture Runbooks (`docs/specs/`)
* [**`adaptive_complexity_gears_and_enterprise_density.md`**](specs/adaptive_complexity_gears_and_enterprise_density.md): 3-tier complexity gears (Exec 4-5/10, Pre-KOM 6.5-7.5/10, Workstream Runbook 8.5-9.5/10), diagnostic status triad, and casual routing contract.
* [**`adaptive_documentation_scout_protocol.md`**](specs/adaptive_documentation_scout_protocol.md): 5-stage automated closeout procedure, dynamic topology scouting, and subagent delegation runbook.
* [**`adr_drawio_pipeline_vs_mcp.md`**](specs/adr_drawio_pipeline_vs_mcp.md): Architecture Decision Record on Draw.io headless export pipeline vs MCP.
* [**`change_request_subsystem.md`**](specs/change_request_subsystem.md): Operational guide to the enterprise Change Request workflow, commercial addendums, and case studies.
* [**`drawio_edge_routing_and_collision_prevention.md`**](specs/drawio_edge_routing_and_collision_prevention.md): Dynamic port directionality, vertical obstacle bypass, and inter-column gutter routing.
* [**`drawio_icon_system_architecture.md`**](specs/drawio_icon_system_architecture.md): Vector tech iconography, Lucide glyph integration, and color tinting pipeline.
* [**`ingress_bus_routing_architecture.md`**](specs/ingress_bus_routing_architecture.md): Shared trunk-line bus architecture for clean multi-source event streaming diagrams.
* [**`lifecycle_architecture.md`**](specs/lifecycle_architecture.md): Sequence diagrams, SIT/UAT quality gates, and FSD-to-TSD document lifecycle transitions.
* [**`localization_and_bilingual_subsystem.md`**](specs/localization_and_bilingual_subsystem.md): Dual catalogs (en/id), hybrid phrase translation, and deck localization.
* [**`manual_identity_guide.md`**](specs/manual_identity_guide.md): Visual identity tokens, Metrodata brand standards, and color usage.
* [**`master_deliverable_recreation_plan.md`**](specs/master_deliverable_recreation_plan.md): Master strategy for recreating the 38 real-world enterprise consulting templates across 5 delivery tiers.
* [**`openxml_purging_and_cleansing.md`**](specs/openxml_purging_and_cleansing.md): Zero-corruption comment, highlight, tracked revision, and author profile stripping for `.docx`.
* [**`powerpoint_slide_geometry.md`**](specs/powerpoint_slide_geometry.md): Deterministic container geometry, sharp top stripes, cover typographic metadata, split chapter dividers, diagram hierarchy, and the Centered-Block Container Alignment Standard (internally left-aligned centered lists).
* [**`pptx_decompiler_and_yaml_reconciliation_engine.md`**](specs/pptx_decompiler_and_yaml_reconciliation_engine.md): Topic 11 architecture for bidirectional OpenXML shape name stamping, PPTX decompiler, AST reconciliation, and automated 4-way re-compilation.
* [**`pptx_file_watcher_and_geometric_reconciliation.md`**](specs/pptx_file_watcher_and_geometric_reconciliation.md): Autonomous PPTX file watcher daemon, reverse geometric coordinate diffing & $0.05''$ grid snapping across containers/nodes/badges/bullet lists, 500ms sliding debounce, and origin suppression.
* [**`in_flight_verification_and_corridor_geometry.md`**](specs/in_flight_verification_and_corridor_geometry.md): Minimum connector corridor span invariant ($L_{\text{segment}} \ge W_{\text{pill}} + 2 \times \text{Halo}$), Postel's Law constructor aliasing, deep PKZip central directory validation, and standardized subagent in-flight smoke pass.
* [**`google_drive_and_slides_collaboration_protocol.md`**](specs/google_drive_and_slides_collaboration_protocol.md): Multi-agent Google Drive & Slides collaboration protocol: format-aware API routing (Office `.pptx` in-place update vs. native Google Slides), anti-hardcoding dynamic title indexing, and remote OCC verification.

### 2. Backlogs & Proposals (`docs/backlog/`)
* [**`atomic_desktop_hot_reload.md`**](backlog/atomic_desktop_hot_reload.md): Single-command atomic desktop hot-reload workflow (`bench diagram v2 compile --target <deck.pptx> --slide <num> --pop`), AppleScript PowerPoint inspection, and in-place DrawingML slide updating.
* [**`remote_cloud_drift_and_race_condition_guard.md`**](backlog/remote_cloud_drift_and_race_condition_guard.md): Remote Cloud Drift & Multi-Agent Race Condition Guard: Optimistic Concurrency Control (OCC) checkout tokens, sidecar Drive locks, and pre-push CAS verification.
* [**`cover_slide_hero_and_opening_modernization.md`**](backlog/cover_slide_hero_and_opening_modernization.md): Clean typographic metadata, dual vertical brand stripes, and hero covers.
* [**`deck_header_contract_and_linter.md`**](backlog/deck_header_contract_and_linter.md) `[COMPLETED - 2026-10-16]`: Canonical header geometry contract (`DeckHeaderContract`), $y \ge 1.350''$ container ingress line invariant, and Check #15 multi-slide header drift linter (`DECK_HEADER_DRIFT`).
* [**`default_container_label_policy.md`**](backlog/default_container_label_policy.md) `[COMPLETED - 2026-10-16]`: Full-canvas swimlane heuristic ($h \ge 4.0'' \implies \text{vertical\_align: bottom}$), cross-boundary ingress clearance ($0.55''$ top corridor), and dynamic obstacle bypass.
* [**`diagram_architecture.md`**](backlog/diagram_architecture.md): Aspect ratio containment and columnar subgraph partitioning.
* [**`diagram_pipeline_and_asset_integration_roadmap.md`**](backlog/diagram_pipeline_and_asset_integration_roadmap.md) `[COMPLETED - 2026-10-13]`: Architectural roadmap for eliminating SVG/Draw.io drift, deterministic Draw.io stencil harvesting, and native PowerPoint shape generation.
* [**`elastic_typography_autofill.md`**](backlog/elastic_typography_autofill.md) `[COMPLETED - 2026-10-16]`: Elastic typography auto-fill in `_plan_card` expanding subtitle font size up to 12.0pt with 4.0pt spacing when card occupancy is $< 55\%$ under a zero-wrapping invariant.
* [**`localization_and_bilingual_deck_subsystem.md`**](backlog/localization_and_bilingual_deck_subsystem.md): Indonesian/English dual-language string catalogs and layout adaptations.
* [**`pitch_deck_screenshot_modernization.md`**](backlog/pitch_deck_screenshot_modernization.md): High-fidelity UI mockups and screenshot frames in pitch decks.
* [**`slide_design_variety.md`**](backlog/slide_design_variety.md): Archetype expansion (case study split screens, quote cards, timeline tracks).
* [**`sprint_17_security_and_performance_quickwins.md`**](backlog/sprint_17_security_and_performance_quickwins.md) `[COMPLETED - 2026-09-19]`: Sprint 17 Runbook: P0 security hardening, ReDoS, XXE, and O(2^V) diagram path optimization.
* [**`sprint_18_change_request_cli_and_closeout.md`**](backlog/sprint_18_change_request_cli_and_closeout.md) `[COMPLETED - 2026-09-19]`: Sprint 18 Runbook: Change Request CLI (`bench cr file`), closeout checklists, and bilingual expansion.
* [**`sprint_19_diagram_pipeline_and_contracts.md`**](backlog/sprint_19_diagram_pipeline_and_contracts.md) `[COMPLETED - 2026-09-19]`: Sprint 19 Runbook: Draw.io data URI embedding, unit space conversions, and Pydantic boundaries.
* [**`sprint_20_visual_archetypes_and_deck_builders.md`**](backlog/sprint_20_visual_archetypes_and_deck_builders.md) `[COMPLETED - 2026-09-19]`: Sprint 20 Runbook: Delivery Gantt roadmap archetype and Harvey Balls feature scorecard.
* [**`template_variable_and_slug_consolidation.md`**](backlog/template_variable_and_slug_consolidation.md): Unified slug catalog and pre-commit PII audit specifications.
* [**`typographic_scale_consistency_checker.md`**](backlog/typographic_scale_consistency_checker.md) `[COMPLETED - 2026-10-16]`: Tier 1 geometric cohort font-drift linter (`TYPOGRAPHIC_SCALE_DRIFT`), post-shrink effective font simulation, and unified 4-tier compiler typography defaults.

### 3. Active Session Handovers (`docs/handovers/` — Latest 10)
* [**`2026-10-14_interwoven_migration_topology_and_whitelisting.md`**](handovers/2026-10-14_interwoven_migration_topology_and_whitelisting.md): Milestone 33 closeout (Unified Interwoven Migration Architecture diagram, horizontal database compression from 260px to 170px, expanded connector spans with 140-175px clearance, return loop repositioned below legacy cluster, and multi-format Draw.io/SVG/PNG/PowerPoint synchronization).
* [**`2026-10-14_tier1_collision_linting_and_tier2_adversarial_visual_qa.md`**](handovers/2026-10-14_tier1_collision_linting_and_tier2_adversarial_visual_qa.md): Milestone 34 closeout (Diagram Engine V2 Tier 1 geometric collision linter `Tier1GeometricLinter` with 11 spatial checks, Tier 2 adversarial visual QA verifier `Tier2VisualVerifier`, perceptual computer vision heuristics, 7-dimension weighted scorecard, `bench diagram v2 audit/visual-qa` CLI, and 100.0/100 reference manifest).
* [**`2026-10-15_visual_vector_refinement_and_openxml_purge.md`**](handovers/2026-10-15_visual_vector_refinement_and_openxml_purge.md): Milestone 35 closeout (Visual & vector system refinement, sharp container swimlanes enclosing rounded icon+title cards, universal OpenXML drop shadow sanitizer `strip_shape_shadows()` reducing 821 defects across 874 shapes to 0, headless Draw.io vector stencil extraction CLI `export_drawio_stencil_to_svg()`, and Diagram Engine V2 spatial auditor vertical auto-offset calibration).
* [**`2026-10-16_bidirectional_pptx_decompiler_and_reconciliation.md`**](handovers/2026-10-16_bidirectional_pptx_decompiler_and_reconciliation.md): Milestone 36 closeout (Bidirectional PPTX decompiler & YAML reconciliation engine, deterministic OpenXML shape naming taxonomy, lossless slide decompiler `PPTXDiagramDecompiler`, AST diffing & pruning cascade `DiagramReconciler`, soft-break normalization, and `bench diagram v2 reconcile` CLI with automatic 4-way re-compilation).
* [**`2026-10-16_typed_clearance_matrix_and_virtual_text_estimation.md`**](handovers/2026-10-16_typed_clearance_matrix_and_virtual_text_estimation.md): Milestone 37 closeout (Typed Semantic Clearance Matrix in `auditor.py`, virtual text bounding box height estimation catching text overflow before compilation, container boundary label textbox hitbox clamping from 4.40in to 1.67in, `ContainerSpec`/`NodeSpec` schema additions, and contractor layout instructions in `CONTRACTOR_INSTRUCTIONS.md`).
* [**`2026-10-16_diagram_v2_standardization_tracks_1_and_2.md`**](handovers/2026-10-16_diagram_v2_standardization_tracks_1_and_2.md): Milestone 38 closeout (DeckHeaderContract immutable header constants, Check #15 `DECK_HEADER_DRIFT` linter, canonical container ingress line $y \ge 1.350''$, Default Bottom-Edge Container Label Policy with $0.55''$ top corridor reclaim, dynamic obstruction bypass, and Model 2.1 Stray Visualization Harvester & Consolidator CLI).
* [**`2026-10-16_typographic_scale_drift_and_elastic_autofill.md`**](handovers/2026-10-16_typographic_scale_drift_and_elastic_autofill.md): Milestone 39 closeout (Canonical 4-tier geometric typographic scale `CANONICAL_TYPOGRAPHIC_SCALE`, Check #14 `TYPOGRAPHIC_SCALE_DRIFT` linter, 4-step elastic typography auto-fill expanding underfilled execution cards, Check #15 `UNDERFILLED_EXECUTION_CARD`, and cross-compiler font resolver unification).
* [**`2026-10-16_autonomous_pptx_file_watcher_and_geometric_sync.md`**](handovers/2026-10-16_autonomous_pptx_file_watcher_and_geometric_sync.md): Topic 12 (Autonomous PPTX file watcher daemon, reverse geometric coordinate diffing & $0.05''$ grid snapping across containers/nodes/badges/bullet lists, 500ms debounce, lock-file filtering, `--skip-pptx` origin suppression, and `bench diagram v2 watch` CLI).
* [**`2026-10-17_multi_subsystem_defect_remediation_and_parity.md`**](handovers/2026-10-17_multi_subsystem_defect_remediation_and_parity.md): Milestone 40 closeout (Multi-subsystem defect remediation across DOCX ECMA-376 schema ordering, XLSX timeline date progression inference, Column H formula preservation, reconciler AST paragraph partitioning, Draw.io custom shape SVG stencils, literal PII masking, strict Gate 5 DRAFT overlay enforcement, full-deck shadow stripping, and unified 90.0 DPI scaling).
* [**`2026-10-17_system_wide_hardening_and_in_flight_flight_test.md`**](handovers/2026-10-17_system_wide_hardening_and_in_flight_flight_test.md): Milestone 41 closeout (Multi-wave static hardening across core delivery locks, localization engine, scorecard models, and vector geometry; real-world in-flight PowerPoint stress test; dynamic elbow clearance remediation; and permanent in-flight verification & corridor geometry specification).

### 4. Archived Session Handovers (`docs/handovers/handover_archive/`)
* [**`handover_archive/README.md`**](handovers/handover_archive/README.md): Master Handover Archive Catalog with completion timestamps and retention audit.
* [**`2026-09-11_cli_skills_refactoring.md`**](handovers/handover_archive/2026-09-11_cli_skills_refactoring.md): Initial CLI routing and skill unification handover.
* [**`2026-09-15_presentation_modernization.md`**](handovers/handover_archive/2026-09-15_presentation_modernization.md): Slide containment, chapter divider archetype, and asset resolution handover.
* [**`2026-09-16_slide3_corporate_equity_tree.md`**](handovers/handover_archive/2026-09-16_slide3_corporate_equity_tree.md): Task delegation brief for the multi-tier corporate shareholding and equity tree archetype.
* [**`2026-09-16_universal_deliverable_recreation.md`**](handovers/handover_archive/2026-09-16_universal_deliverable_recreation.md): Deliverable recreation Milestones 13–15, financial XLSX suite, and PII linter.
* [**`2026-09-18_comprehensive_platform_upgrade_and_hardening_audit.md`**](handovers/handover_archive/2026-09-18_comprehensive_platform_upgrade_and_hardening_audit.md): Platform upgrade and security hardening master audit.
* [**`2026-09-18_localization_and_bilingual_subsystems.md`**](handovers/handover_archive/2026-09-18_localization_and_bilingual_subsystems.md): Dual-catalog localization, hybrid translation engine, and paired reference decks.
* [**`2026-09-19_sprints_17_20_platform_hardening_cr_cli_diagram_and_archetypes.md`**](handovers/handover_archive/2026-09-19_sprints_17_20_platform_hardening_cr_cli_diagram_and_archetypes.md): Sprints 17–20 closeout (Milestones 18–21), security fixes, CR CLI, diagram URI pipeline, and Gantt/Harvey Balls archetypes.
* [**`2026-09-19_visual_harmonization_and_directwrite_preview_parity.md`**](handovers/handover_archive/2026-09-19_visual_harmonization_and_directwrite_preview_parity.md): Milestone 22 closeout (Presentation & diagram visual harmonization, icon engine tokens, DirectWrite typography calibration, and preview CLI).
* [**`2026-09-19_presales_pitch_deck_modernization.md`**](handovers/handover_archive/2026-09-19_presales_pitch_deck_modernization.md): Milestone 23 closeout (Automated 36-slide presales consulting pitch deck modernization, PitchDeckBuilder, new archetypes, master YAML config, and preview verification).
* [**`2026-09-19_project_kickoff_presentation_modernization.md`**](handovers/handover_archive/2026-09-19_project_kickoff_presentation_modernization.md): Milestone 24 closeout (Automated 19-slide project kick-off presentation modernization, agenda/table/thank-you archetypes, governance org overrides, Gantt deserialization, and preview verification).
* [**`2026-09-20_uat_briefing_presentation_modernization.md`**](handovers/handover_archive/2026-09-20_uat_briefing_presentation_modernization.md): Milestone 25 closeout (Automated 25-slide bilingual UAT briefing presentation modernization, forensic template analysis, master YAML config, slide exporter whitespace advance calibration, Gantt normalization, and preview verification).
* [**`2026-09-20_weekly_progress_report_deck_modernization.md`**](handovers/handover_archive/2026-09-20_weekly_progress_report_deck_modernization.md): Milestone 26 closeout (Automated 11-slide weekly progress report presentation modernization, forensic template analysis, dynamic milestone row height scaling, consulting S-curve chart generator, spreadsheet ingestion pipeline, and dual-mode preview verification).
* [**`2026-09-21_project_closing_deck_modernization.md`**](handovers/handover_archive/2026-09-21_project_closing_deck_modernization.md): Milestone 27 closeout (Automated 9-slide project closing & maintenance transition deck modernization, forensic template & checklist audit, ClosingDeckBuilder, dynamic spreadsheet ingestion, and preview verification).
* [**`2026-09-21_sprints_17_27_completion_briefing.md`**](handovers/handover_archive/2026-09-21_sprints_17_27_completion_briefing.md): Sprints 17–27 closeout (Universal NGL slug & PII normalization, Closing Deck visual enrichment, Kick-off fixes, and automated Change Request suite).
* [**`2026-09-21_sprints_17_27_review_and_enhancement_roadmap.md`**](handovers/handover_archive/2026-09-21_sprints_17_27_review_and_enhancement_roadmap.md): Sprints 17–27 staged review briefing, feedback ledger, architectural evaluation, and 5-phase enhancement roadmap.
* [**`2026-09-23_feedback_and_quality_enhancement_sprint.md`**](handovers/handover_archive/2026-09-23_feedback_and_quality_enhancement_sprint.md): Milestone 27 / Sprints 17–27 Feedback & Quality Enhancement Sprint closeout (Personnel PII scrubbing to Dewi Lestari, synthetic Gantt generator, OpenXML image aspect ratio QA engine & CLI, Slide 7 maintenance workflow architecture & OpenXML connectors, DrawingML bullet schema compliance, and Slide 6 KPI overflow fix).
* [**`2026-09-26_comprehensive_antipattern_compliance_and_pii_purge.md`**](handovers/handover_archive/2026-09-26_comprehensive_antipattern_compliance_and_pii_purge.md): Milestone 28 closeout (Comprehensive system anti-pattern compliance, deep universal PII / real names purge, Cover Slide footer and striped container sharp rectangle validation in `SlideValidator`, 40-48px icon sizing and upward edge bypass routing in `DiagramEngine`, and automated OpenXML element purging in `TemplateStamper`).
* [**`2026-10-13_diagram_pipeline_and_asset_integration.md`**](handovers/handover_archive/2026-10-13_diagram_pipeline_and_asset_integration.md): Milestone 29 closeout (Diagram pipeline and asset integration Phases 1–4, deterministic asset harvester and resolver CLI, Databricks/Cloudera/AWS stencils, hybrid editable `.drawio.svg` parity, and native PowerPoint DrawingML shape compiler).
* [**`2026-10-14_visual_qa_and_drawingml_collision_remediation.md`**](handovers/handover_archive/2026-10-14_visual_qa_and_drawingml_collision_remediation.md): Milestone 30 closeout (DrawingML spatial collision linter, macOS live window screen capture, forward arrowhead orientation, card text overflow fixes, cylinder text clearance, and `bench ppt visual-qa` CLI).
* [**`2026-10-14_flat_aesthetic_padding_engine_and_flow_routing.md`**](handovers/handover_archive/2026-10-14_flat_aesthetic_padding_engine_and_flow_routing.md): Milestone 31 closeout (Flat DrawingML aesthetic standardization via `_flatten`, proportional padding engine `_plan_card`, Databricks 3D cylinder body alignment, single polyline routing, collinear boundary auditing).
* [**`2026-10-14_cdsw_to_lambda_architecture_evolution.md`**](handovers/handover_archive/2026-10-14_cdsw_to_lambda_architecture_evolution.md): Milestone 32 closeout (CDSW-to-Lambda architecture evolution presentation suite in `architecture_evolution_cdsw_to_lambda.pptx`, decoupled flow routing topology, Databricks 3D cylinder visual parity, Gear 2/3 high-density consulting archetypes, and Diagnostic Status Triad).




