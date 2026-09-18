# AGENT HANDOVER & ACTIVE STATE POINTER

> **Repository:** `enterprise-bench` | **Branch:** `main`  
> **Mission:** Universal multi-engine enterprise automation workbench (DOCX, PPTX, XLSX, Draw.io).  
> **Architecture Ledger:** [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | **Index:** [`docs/INDEX.md`](docs/INDEX.md)  
> **Operating Guardrails:** [`AGENTS.md`](AGENTS.md) (Strict ZERO INTERMEDIATE UNIT TESTING).  

---

## 1. Active Platform Status & Completed Milestones

Progress: `[██████████] 100%` (Tier 1–5 Master Deliverable Automation Complete)

- **Tier 1 (Legal DOCX Stamping):** Deterministic Jinja2/docxtpl stamping, attendee auto-expansion, OpenXML styling.
- **Tier 2 (Modular Spec Compiler):** Multi-chapter Markdown to DOCX compiler with callout alerts, tables, frontmatter, and high-DPI image/diagram embeds (`src/docx_engine/spec_compiler.py`).
- **Tier 3 (Financial XLSX Models):** Snowflake sizing calculators, S-curve progress engines with OpenXML line charts, and RAID/defect loggers (`src/xlsx_engine/`).
- **Tier 4 (Consulting Presentations):** Reference slide suite, DirectWrite parity previews, BCG/McKinsey archetypes (`src/ppt_engine/`).
- **Tier 5 (Architecture Diagramming):** Multi-page Draw.io engine (`DrawIOProject`), batch exporter (`bench diagram export-all`), and declarative YAML compiler (`bench diagram build-project` via `presets/diagrams/fsd_architecture.yaml`).
- **Tier 6 (Localization & Bilingual Subsystems):** Canonical EN/ID YAML catalogs (`presets/locales/`), hybrid phrase translator (`src/core/locale_engine.py`), and paired reference master decks (`Enterprise_Reference_Master_Deck_EN.pptx`, `..._ID.pptx`).

---

## 2. Key Architecture Pointers (`docs/specs/`)

- [**Localization & Bilingual Subsystem**](docs/specs/localization_and_bilingual_subsystem.md): Dual EN/ID catalogs, hybrid phrase translation & localized decks.
- [**Master Deliverable Recreation Plan**](docs/specs/master_deliverable_recreation_plan.md): 5-tier roadmap across 38 master templates.
- [**OpenXML Document Purging**](docs/specs/openxml_purging_and_cleansing.md): Comment, highlight, and revision stripping.
- [**Draw.io Edge Routing & Collision Prevention**](docs/specs/drawio_edge_routing_and_collision_prevention.md): Dynamic ports & gutter routing.
- [**Ingress Bus Architecture**](docs/specs/ingress_bus_routing_architecture.md): Shared inter-column trunk-line routing.
- [**Change Request Subsystem**](docs/specs/change_request_subsystem.md): Commercial addendums & CR workflows.

---

## 3. Transition Briefings Archive (`docs/handovers/`)

- [`2026-09-18_localization_and_bilingual_subsystems.md`](docs/handovers/2026-09-18_localization_and_bilingual_subsystems.md): Milestone 17 (Dual catalogs, hybrid translation, paired reference decks).
- [`2026-09-16_universal_deliverable_recreation.md`](docs/handovers/2026-09-16_universal_deliverable_recreation.md): Milestones 12–16 (S-curves, XLSX suite, legal stamping, modular specs).
- [`2026-09-16_slide3_corporate_equity_tree.md`](docs/handovers/2026-09-16_slide3_corporate_equity_tree.md): Forensic data & layout spec for Slide 3 Corporate Equity Tree.
- [`2026-09-15_presentation_modernization.md`](docs/handovers/2026-09-15_presentation_modernization.md): Milestones 8–11 (Containment, 3-column diagrams).
- [`2026-09-11_cli_skills_refactoring.md`](docs/handovers/2026-09-11_cli_skills_refactoring.md): Milestones 1–7 (Core engines, CLI, OpenXML purger).

---

## 4. Immediate Next Backlog

1. **Slide 3 Corporate Equity Tree Archetype (`src/ppt_engine/reference_slides.py`):**
   - Implement `EquityTreeData` tree layout for Metrodata 4-subsidiary structure.
2. **Presentation Imagery Archetypes & Logo Lockups:**
   - Standardize template image placeholder zones (Section 5 of [`docs/backlog/slide_design_variety.md`](docs/backlog/slide_design_variety.md)).
   - Implement dual client/vendor logo lockups on cover slides and header banners.
3. **Template Variable & Slug Consolidation:**
   - Enforce [`docs/backlog/template_variable_and_slug_consolidation.md`](docs/backlog/template_variable_and_slug_consolidation.md) across remaining deliverables.
