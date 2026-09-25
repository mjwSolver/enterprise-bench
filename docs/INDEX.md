# Enterprise Workbench Documentation Hub

This directory contains the central documentation, architectural blueprints, subsystem specifications, historical handovers, and roadmaps for `enterprise-bench`.

---

## 🧭 Directory Taxonomy & Operating Rules

```text
docs/
├── INDEX.md               # This master navigation index
├── CHANGELOG.md           # Authoritative historical milestone ledger (Milestones 1–28+)
│
├── handovers/             # Historical sprint and session handover briefings
│   ├── 2026-09-11_cli_skills_refactoring.md
│   ├── 2026-09-15_presentation_modernization.md
│   ├── 2026-09-16_universal_deliverable_recreation.md
│   ├── 2026-09-16_slide3_corporate_equity_tree.md
│   ├── 2026-09-18_comprehensive_platform_upgrade_and_hardening_audit.md
│   ├── 2026-09-18_localization_and_bilingual_subsystems.md
│   ├── 2026-09-19_sprints_17_20_platform_hardening_cr_cli_diagram_and_archetypes.md
│   ├── 2026-09-19_visual_harmonization_and_directwrite_preview_parity.md
│   ├── 2026-09-19_presales_pitch_deck_modernization.md
│   ├── 2026-09-19_project_kickoff_presentation_modernization.md
│   ├── 2026-09-20_uat_briefing_presentation_modernization.md
│   ├── 2026-09-20_weekly_progress_report_deck_modernization.md
│   ├── 2026-09-21_project_closing_deck_modernization.md
│   ├── 2026-09-21_sprints_17_27_review_and_enhancement_roadmap.md
│   ├── 2026-09-21_sprints_17_27_completion_briefing.md
│   ├── 2026-09-23_feedback_and_quality_enhancement_sprint.md
│   └── 2026-09-26_comprehensive_antipattern_compliance_and_pii_purge.md
│
├── specs/                 # Permanent architectural references, runbooks & ADRs
│   ├── adaptive_documentation_scout_protocol.md
│   ├── adr_drawio_pipeline_vs_mcp.md
│   ├── change_request_subsystem.md
│   ├── drawio_edge_routing_and_collision_prevention.md
│   ├── drawio_icon_system_architecture.md
│   ├── ingress_bus_routing_architecture.md
│   ├── lifecycle_architecture.md
│   ├── localization_and_bilingual_subsystem.md
│   ├── manual_identity_guide.md
│   ├── master_deliverable_recreation_plan.md
│   └── openxml_purging_and_cleansing.md
│
└── backlog/               # Future sprint roadmaps, design proposals & backlogs
    ├── cover_slide_hero_and_opening_modernization.md
    ├── diagram_architecture.md
    ├── localization_and_bilingual_deck_subsystem.md
    ├── pitch_deck_screenshot_modernization.md
    ├── slide_design_variety.md
    ├── sprint_17_security_and_performance_quickwins.md
    ├── sprint_18_change_request_cli_and_closeout.md
    ├── sprint_19_diagram_pipeline_and_contracts.md
    ├── sprint_20_visual_archetypes_and_deck_builders.md
    └── template_variable_and_slug_consolidation.md
```

---

## 🏛️ Documentation Standards for Agents

1. **Active State vs. Historical Log:**
   - **Root [`HANDOVER.md`](../HANDOVER.md)** is strictly a **lean pointer** to the current active sprint state and immediate next tasks ($\le 80$ lines).
   - All historical milestone completions are logged in [`docs/CHANGELOG.md`](CHANGELOG.md).
   - End-of-sprint transition briefings are archived in [`docs/handovers/`](handovers/) with the naming pattern `YYYY-MM-DD_<topic>.md`.
2. **Subsystem Specifications:**
   - Technical documentation explaining *how a subsystem or engine functions* must live in [`docs/specs/`](specs/). Never prefix technical specifications with `HANDOVER_`.
3. **Roadmaps and Proposals:**
   - Unscheduled initiatives, exploratory slide archetypes, and feature proposals live in [`docs/backlog/`](backlog/). When implemented, their functional spec moves to `specs/` and an entry is logged in `CHANGELOG.md`.

---

## 📚 Master Index

### 1. Active Specifications & Architecture Runbooks (`docs/specs/`)
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

### 2. Backlogs & Proposals (`docs/backlog/`)
* [**`cover_slide_hero_and_opening_modernization.md`**](backlog/cover_slide_hero_and_opening_modernization.md): Clean typographic metadata, dual vertical brand stripes, and hero covers.
* [**`diagram_architecture.md`**](backlog/diagram_architecture.md): Aspect ratio containment and columnar subgraph partitioning.
* [**`localization_and_bilingual_deck_subsystem.md`**](backlog/localization_and_bilingual_deck_subsystem.md): Indonesian/English dual-language string catalogs and layout adaptations.
* [**`pitch_deck_screenshot_modernization.md`**](backlog/pitch_deck_screenshot_modernization.md): High-fidelity UI mockups and screenshot frames in pitch decks.
* [**`slide_design_variety.md`**](backlog/slide_design_variety.md): Archetype expansion (case study split screens, quote cards, timeline tracks).
* [**`sprint_17_security_and_performance_quickwins.md`**](backlog/sprint_17_security_and_performance_quickwins.md) `[COMPLETED - 2026-09-19]`: Sprint 17 Runbook: P0 security hardening, ReDoS, XXE, and O(2^V) diagram path optimization.
* [**`sprint_18_change_request_cli_and_closeout.md`**](backlog/sprint_18_change_request_cli_and_closeout.md) `[COMPLETED - 2026-09-19]`: Sprint 18 Runbook: Change Request CLI (`bench cr file`), closeout checklists, and bilingual expansion.
* [**`sprint_19_diagram_pipeline_and_contracts.md`**](backlog/sprint_19_diagram_pipeline_and_contracts.md) `[COMPLETED - 2026-09-19]`: Sprint 19 Runbook: Draw.io data URI embedding, unit space conversions, and Pydantic boundaries.
* [**`sprint_20_visual_archetypes_and_deck_builders.md`**](backlog/sprint_20_visual_archetypes_and_deck_builders.md) `[COMPLETED - 2026-09-19]`: Sprint 20 Runbook: Delivery Gantt roadmap archetype and Harvey Balls feature scorecard.
* [**`template_variable_and_slug_consolidation.md`**](backlog/template_variable_and_slug_consolidation.md): Unified slug catalog and pre-commit PII audit specifications.

### 3. Session Handovers (`docs/handovers/`)
* [**`2026-09-11_cli_skills_refactoring.md`**](handovers/2026-09-11_cli_skills_refactoring.md): Initial CLI routing and skill unification handover.
* [**`2026-09-15_presentation_modernization.md`**](handovers/2026-09-15_presentation_modernization.md): Slide containment, chapter divider archetype, and asset resolution handover.
* [**`2026-09-16_universal_deliverable_recreation.md`**](handovers/2026-09-16_universal_deliverable_recreation.md): Deliverable recreation Milestones 13–15, financial XLSX suite, and PII linter.
* [**`2026-09-16_slide3_corporate_equity_tree.md`**](handovers/2026-09-16_slide3_corporate_equity_tree.md): Task delegation brief for the multi-tier corporate shareholding and equity tree archetype.
* [**`2026-09-18_comprehensive_platform_upgrade_and_hardening_audit.md`**](handovers/2026-09-18_comprehensive_platform_upgrade_and_hardening_audit.md): Platform upgrade and security hardening master audit.
* [**`2026-09-18_localization_and_bilingual_subsystems.md`**](handovers/2026-09-18_localization_and_bilingual_subsystems.md): Dual-catalog localization, hybrid translation engine, and paired reference decks.
* [**`2026-09-19_sprints_17_20_platform_hardening_cr_cli_diagram_and_archetypes.md`**](handovers/2026-09-19_sprints_17_20_platform_hardening_cr_cli_diagram_and_archetypes.md): Sprints 17–20 closeout (Milestones 18–21), security fixes, CR CLI, diagram URI pipeline, and Gantt/Harvey Balls archetypes.
* [**`2026-09-19_visual_harmonization_and_directwrite_preview_parity.md`**](handovers/2026-09-19_visual_harmonization_and_directwrite_preview_parity.md): Milestone 22 closeout (Presentation & diagram visual harmonization, icon engine tokens, DirectWrite typography calibration, and preview CLI).
* [**`2026-09-19_presales_pitch_deck_modernization.md`**](handovers/2026-09-19_presales_pitch_deck_modernization.md): Milestone 23 closeout (Automated 36-slide presales consulting pitch deck modernization, PitchDeckBuilder, new archetypes, master YAML config, and preview verification).
* [**`2026-09-19_project_kickoff_presentation_modernization.md`**](handovers/2026-09-19_project_kickoff_presentation_modernization.md): Milestone 24 closeout (Automated 19-slide project kick-off presentation modernization, agenda/table/thank-you archetypes, governance org overrides, Gantt deserialization, and preview verification).
* [**`2026-09-20_uat_briefing_presentation_modernization.md`**](handovers/2026-09-20_uat_briefing_presentation_modernization.md): Milestone 25 closeout (Automated 25-slide bilingual UAT briefing presentation modernization, forensic template analysis, master YAML config, slide exporter whitespace advance calibration, Gantt normalization, and preview verification).
* [**`2026-09-20_weekly_progress_report_deck_modernization.md`**](handovers/2026-09-20_weekly_progress_report_deck_modernization.md): Milestone 26 closeout (Automated 11-slide weekly progress report presentation modernization, forensic template analysis, dynamic milestone row height scaling, consulting S-curve chart generator, spreadsheet ingestion pipeline, and dual-mode preview verification).
* [**`2026-09-21_project_closing_deck_modernization.md`**](handovers/2026-09-21_project_closing_deck_modernization.md): Milestone 27 closeout (Automated 9-slide project closing & maintenance transition deck modernization, forensic template & checklist audit, ClosingDeckBuilder, dynamic spreadsheet ingestion, and preview verification).
* [**`2026-09-21_sprints_17_27_review_and_enhancement_roadmap.md`**](handovers/2026-09-21_sprints_17_27_review_and_enhancement_roadmap.md): Sprints 17–27 review briefing, feedback ledger, architectural evaluation, and 5-phase enhancement roadmap.
* [**`2026-09-21_sprints_17_27_completion_briefing.md`**](handovers/2026-09-21_sprints_17_27_completion_briefing.md): Sprints 17–27 closeout (Universal NGL slug & PII normalization, Closing Deck visual enrichment, Weekly Progress typography & English purity, Kick-off Slide 10/12/19 defect fixes, and automated Change Request suite).
* [**`2026-09-23_feedback_and_quality_enhancement_sprint.md`**](handovers/2026-09-23_feedback_and_quality_enhancement_sprint.md): Milestone 27 / Sprints 17–27 Feedback & Quality Enhancement Sprint closeout (Personnel PII scrubbing to Dewi Lestari, synthetic Gantt generator, OpenXML image aspect ratio QA engine & CLI, Slide 7 maintenance workflow architecture & OpenXML connectors, DrawingML bullet schema compliance, and Slide 6 KPI overflow fix).
* [**`2026-09-26_comprehensive_antipattern_compliance_and_pii_purge.md`**](handovers/2026-09-26_comprehensive_antipattern_compliance_and_pii_purge.md): Milestone 28 closeout (Comprehensive system anti-pattern compliance, deep universal PII / real names purge, Cover Slide footer and striped container sharp rectangle validation in `SlideValidator`, 40-48px icon sizing and upward edge bypass routing in `DiagramEngine`, and automated OpenXML element purging in `TemplateStamper`).

