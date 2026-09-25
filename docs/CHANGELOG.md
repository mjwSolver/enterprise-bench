# Enterprise Workbench Changelog & Architectural History

This document serves as the **authoritative, chronological historical ledger** of all completed platform milestones, architectural changes, engine expansions, and subsystem implementations across `enterprise-bench`.

---

## [2026-09-26] - Milestone 28: Comprehensive System Anti-Pattern Compliance & Deep Universal PII / Real Names Purge

### Summary
Delivered enterprise-grade privacy protection, strict presentation geometry validation, robust diagram layout routing, and automated document element purging across `enterprise-bench`. Codified comprehensive regex personnel substitutions in `src/core/slug_registry.py` eliminating all real individual names in favor of canonical personas ("Agus Pramono", "Dewi Lestari", "Rudi Hermawan", "Dian Permata", "Aditya Putra", "Hendra Setiawan", "Reza Pratama", "Andi Wijaya"), and upgraded `src/core/pii/` handlers (`DocxHandler`, `PptxHandler`, `XlsxHandler`) with compiled regex pattern replacement passes across runs, paragraphs, table cells, and sheets. Hardened `src/ppt_engine/slide_validator.py` with AST checks under `CHECK_5_THEME_GEOMETRY` enforcing Cover Slide Architecture Compliance (zero footers/pagination on Slide 1) and the Geometric Alignment Rule (container cards with top stripes MUST be sharp rectangles `MSO_SHAPE.RECTANGLE`, strictly prohibiting `MSO_SHAPE.ROUNDED_RECTANGLE`). Upgraded `src/ppt_engine/diagram_engine.py` with standardized 40-48px icon sizing, minimum node height bounds, and upward/feedback edge bypass routing in `DiagramRenderer` to prevent straight lines through intervening containers. Integrated automated OpenXML element purging (`purge_docx_elements`) directly into `TemplateStamper.render` and `stamp_template` in `src/docx_engine/template_stamper.py` (`purge_elements=True` default) to automatically strip review comments, highlights, and tracked changes on deliverable stamping.

### Milestones Delivered
- **Deep Universal PII & Real Names Purge:**
  - Enhanced [`src/core/slug_registry.py`](../src/core/slug_registry.py) with comprehensive regex normalization for all historical personnel names across client and vendor roles.
  - Upgraded `substitute_slugs_in_document` and `substitute_slugs_in_workbook` with automatic context-aware regex substitution across body paragraphs, tables, headers, and footers.
  - Upgraded [`src/core/pii/handlers/`](../src/core/pii/handlers/) (`DocxHandler`, `PptxHandler`, `XlsxHandler`) to compile replacement dictionaries into case-insensitive regex patterns (`compiled_rules`), executing run-level and paragraph-level substitutions to ensure complete entity purging across styled text boundaries.
  - Sanitized manifests ([`clean_workspace/catalog_data.json`](../clean_workspace/catalog_data.json), [`clean_workspace/sanitization_manifest.json`](../clean_workspace/sanitization_manifest.json)), deck presets ([`presets/deck_configs/closing_deck.yaml`](../presets/deck_configs/closing_deck.yaml), [`presets/deck_configs/kickoff_presentation.yaml`](../presets/deck_configs/kickoff_presentation.yaml), [`presets/deck_configs/uat_briefing.yaml`](../presets/deck_configs/uat_briefing.yaml)), and specs ([`specs/tti_analytics/`](../specs/tti_analytics/)).
- **Presentation Anti-Pattern Compliance & Slide Validator Hardening:**
  - Added Cover Slide Architecture Compliance check (`CHECK_5_THEME_GEOMETRY`) in [`src/ppt_engine/slide_validator.py`](../src/ppt_engine/slide_validator.py) prohibiting footer bars and pagination shapes on Slide 1.
  - Added Geometric Alignment Rule check (`CHECK_5_THEME_GEOMETRY`) in [`src/ppt_engine/slide_validator.py`](../src/ppt_engine/slide_validator.py) flagging rounded container cards (`MSO_SHAPE.ROUNDED_RECTANGLE`) paired with top accent stripes and enforcing sharp rectangles (`MSO_SHAPE.RECTANGLE`).
- **Diagram Engine Layout & Edge Routing Hardening:**
  - Standardized vector tech logo and icon dimensions to $40\text{px} - 48\text{px}$ (`icon_sz = min(max(node.height * 0.58, 40.0), 48.0)`) and left text padding (`spacing_left = icon_sz + 20`) in [`src/ppt_engine/diagram_engine.py`](../src/ppt_engine/diagram_engine.py).
  - Enhanced `HierarchicalLayoutEngine` card geometry to enforce minimum card volume and height ($\ge 64\text{px}$ when icons/logos are present).
  - Implemented upward/feedback edge routing in `DiagramRenderer.render_svg` to bypass intermediate vertical obstacles ($X_{\text{route}} = X_{\max} + 24\text{px}$).
  - Refactored [`presets/diagrams/fsd_architecture.yaml`](../presets/diagrams/fsd_architecture.yaml) to a balanced 3-column architecture topology with official SVG logos and clean gutter routing.
- **Automated OpenXML Document Element Purging:**
  - Integrated `purge_docx_elements` into `TemplateStamper.render` and `stamp_template` in [`src/docx_engine/template_stamper.py`](../src/docx_engine/template_stamper.py) (`purge_elements=True` default), ensuring comment, highlight, and revision stripping on all stamped DOCX deliverables.
- Reference Handover: [`docs/handovers/2026-09-26_comprehensive_antipattern_compliance_and_pii_purge.md`](handovers/2026-09-26_comprehensive_antipattern_compliance_and_pii_purge.md)

---

## [2026-09-23] - Milestone 27 / Sprints 17–27 Feedback & Quality Enhancement Sprint: PII Scrubbing, Aspect QA & DrawingML Hardening

### Summary
Executed an end-of-sprint feedback and quality enhancement cycle across Milestone 27 and Sprints 17–27 collateral. Scrubbed legacy PII 'Fredric Retanubun', substituting canonical client PM 'Dewi Lestari' across clean workspace templates, CR_07 change log ledger, and kickoff presets, and enhanced `src/core/slug_registry.py` with automated personnel normalization. Developed `scripts/generate_synthetic_cr_gantt.py` to replace real MS Project Gantt screenshots in Change Request CR_07 Word templates and outputs with synthetic watermarked graphics. Engineered `src/core/image_aspect.py` and CLI commands (`bench doc check-aspect`, `bench doc fix-aspect`) to dynamically audit and correct OpenXML container vs natural image aspect ratio mismatches, curing 38.7% squish down to 0% distortion in Word documents, and integrated into `src/core/change_request.py`. Overhauled Closing Deck Slide 7 maintenance workflow architecture in `src/ppt_engine/closing_deck.py`, eliminating crushed 0.27" text boxes with 3-line structured card typography and native OpenXML directional connector lines with triangle arrowheads. Resolved ECMA-376 schema ordering constraints (`<a:buFont>`, `<a:buChar>` before `<a:defRPr>`) to permanently restore missing PowerPoint bullets across `closing_deck.py`, `weekly_progress_deck.py`, and `consulting_archetypes.py`. Streamlined redundant subtitles and fixed KPI badge overflow on Closing Deck Slide 6.

### Milestones Delivered
- **PII Scrubbing & Personnel Normalization:**
  - Replaced legacy PII 'Fredric Retanubun' with canonical client PM 'Dewi Lestari' across clean workspace templates, CR_07 Change Log Ledger, and kickoff configurations ([`presets/deck_configs/kickoff_presentation.yaml`](../presets/deck_configs/kickoff_presentation.yaml)).
  - Enhanced [`src/core/slug_registry.py`](../src/core/slug_registry.py) with automated personnel regex scrubbing (`Fredric Retanubun` $\rightarrow$ `client_pm_name`, `Tadahiko Onaka` $\rightarrow$ `client_sponsor_name`) and `EngagementContext.from_client_name()`.
- **Synthetic Gantt Generator & Screenshot Replacement:**
  - Developed [`scripts/generate_synthetic_cr_gantt.py`](../scripts/generate_synthetic_cr_gantt.py) rendering 150 DPI watermarked synthetic project schedule graphics (`assets/synthetic_cr_gantt.png`).
  - Replaced real MS Project Gantt screenshots in Change Request CR_07 Word templates (`4.4_Change_Request_Form_Template.docx`, `Change_Request_Form_CR_07.docx`) and outputs with synthetic graphics.
- **Image Aspect Ratio QA Engine & Unified CLI:**
  - Built [`src/core/image_aspect.py`](../src/core/image_aspect.py) providing `ImageAspectEngine` and `ImageAspectReport` for OpenXML container vs natural image aspect ratio validation.
  - Added CLI commands `bench doc check-aspect` and `bench doc fix-aspect` in [`src/cli.py`](../src/cli.py).
  - Cured 38.7% squish down to 0% distortion in Word documents by dynamically calculating proportional extents.
  - Integrated automated aspect ratio correction into [`src/core/change_request.py`](../src/core/change_request.py) (`ChangeRequestProcessor.process_cr`).
- **Closing Deck Slide 7 Architecture (Maintenance Workflow):**
  - Eliminated crushed 0.27" floating callout boxes causing vertical letter wrapping on Slide 7 in [`src/ppt_engine/closing_deck.py`](../src/ppt_engine/closing_deck.py).
  - Replaced with 3-line structured card typography (`step_w = Inches(1.64)`, `step_h = Inches(0.72)`) with dedicated SLA and gate badges.
  - Added native OpenXML directional connector lines (`MSO_CONNECTOR.STRAIGHT`) with DrawingML triangle arrowheads (`<a:headEnd type="triangle"/>`).
- **DrawingML Bullet Standardization & ECMA-376 Schema Hardening:**
  - Resolved ECMA-376 PresentationML schema constraint requiring `<a:buClrTx>`, `<a:buSzPct>`, `<a:buFont>`, `<a:buChar>` to precede `<a:defRPr>` in `<a:pPr>`.
  - Standardized `_add_bullet_paragraph` with schema insertion ordering and CSS fallback font list sanitization across [`src/ppt_engine/closing_deck.py`](../src/ppt_engine/closing_deck.py), [`src/ppt_engine/weekly_progress_deck.py`](../src/ppt_engine/weekly_progress_deck.py), and [`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py).
- **Subtitle Streamlining & Slide 6 Overflow Fix:**
  - Removed redundant subtitles across Slide 06 pillar cards and Slide 08 deliverable cards in [`src/ppt_engine/closing_deck.py`](../src/ppt_engine/closing_deck.py) and [`presets/deck_configs/closing_deck.yaml`](../presets/deck_configs/closing_deck.yaml).
  - Streamlined verbose KPI badges on Slide 6 to prevent text frame overflow and adhere to clean consulting design principles.
  - Added safe exception handling for footer page numbering in `update_pagination()`.
- Reference Handover: [`docs/handovers/2026-09-23_feedback_and_quality_enhancement_sprint.md`](handovers/2026-09-23_feedback_and_quality_enhancement_sprint.md)

---

## [2026-09-21] - Sprints 17–27 Review & Enhancement Sprint (Phases 1–5): Universal Normalization & Defect Rectification

### Summary
Executed a comprehensive 5-phase review and enhancement sprint across Sprints 17–27 collateral, resolving cross-cutting entity normalization, visual enrichment, defect rectifications, and automated change request governance. Established "Nusantara Global Logistics" (`NGL`) as the system-wide canonical default client entity across models, declarative presets, and slide pre-save shape traversal (`src/core/slug_registry.py`). Enriched Project Closing Deck (`5.1`) with Lucide vector iconography, an operational 3-swimlane maintenance workflow, and clean corporate closing geometry (`src/ppt_engine/closing_deck.py`). Perfected Weekly Progress Report (`4.2`) milestone row vertical centering via `MSO_ANCHOR.MIDDLE`, DrawingML hanging bullets in risk mitigations, and 100% English language purity (`src/ppt_engine/weekly_progress_deck.py`). Rectified Project Kick-off Material (`1.1`) defects by deprecating static screenshots on Slide 10 in favor of a native 3-column OpenXML vector architecture with SVG logos and orange callouts, flipping Gantt diamond labels leftwards to eliminate slide canvas bleed, stripping drop shadows, and eliminating hardcoded staff names on Slide 19 (`src/ppt_engine/reference_slides.py`, `src/ppt_engine/consulting_archetypes.py`). Automated Change Request (`CR_07`) dynamic output routing and recursive document/workbook sanitization (`src/core/change_request.py`).

### Milestones Delivered
- **Phase 1: Universal Slug & PII Normalization:**
  - Standardized system-wide canonical default client entity to `Nusantara Global Logistics` (short name: `NGL`) in [`src/core/slug_registry.py`](../src/core/slug_registry.py) with `EngagementContext.default_ngl()` and `EngagementContext.substitute()`.
  - Implemented recursive slide shape and group shape traversal in `substitute_slugs_in_presentation`, substituting slug tokens and regex scrubbing legacy entities across shapes, tables, and nested group shapes (`shape.shapes`).
  - Sanitized declarative YAML presets (`closing_deck.yaml`, `kickoff_presentation.yaml`, `presales_pitch_deck.yaml`, `uat_briefing.yaml`, `weekly_progress.yaml`) replacing hardcoded entities with `[CLIENT_COMPANY_NAME]` and `[CLIENT_SHORT_NAME]`.
  - Enforced a strict optical font size floor ($\ge 11.0\text{pt}$ minimum, $\ge 12.0\text{pt}$ body copy) across all presentation engines and archetypes.
- **Phase 2: Project Closing Deck (5.1) Visual Enrichment:**
  - Integrated Lucide vector icons tinted with `theme.accent` across Slide 02 Agenda badges (`compass`, `package-check`, `file-signature`, `shield-check`, `git-pull-request`, `bar-chart-3`), Slide 03 Capability cards, Slide 04 Deliverables format badges (`file-text`, `presentation`, `table`, `code`), and Slide 05 Checklist access cards in [`src/ppt_engine/closing_deck.py`](../src/ppt_engine/closing_deck.py).
  - Upgraded Slide 07 from flat sequential boxes into a formal 3-swimlane maintenance workflow (Client Organization, Metrodata L1/L2 Managed Services, Lead Development) with SLA targets.
  - Re-architected Slide 09 to default to a clean corporate closing card without hardcoded personal staff emails.
- **Phase 3: Weekly Progress Report (4.2) Typography & Language Purity:**
  - Resolved Slide 07 milestone status row vertical alignment defect in [`src/ppt_engine/weekly_progress_deck.py`](../src/ppt_engine/weekly_progress_deck.py) by allocating full `row_h` height and setting `tf.vertical_anchor = MSO_ANCHOR.MIDDLE` across text frames, harmonizing with status pills.
  - Upgraded Slide 08 Risk Register mitigations with DrawingML bullet glyphs and hanging indents (`marL="288000"`, `indent="-288000"`) via `_add_bullet_paragraph`.
  - Replaced Indonesian phrases in presets and builders with a 100% pure English baseline, isolating bilingual translation to dedicated locale catalogs.
- **Phase 4: Project Kick-off Material (1.1) Defect Rectification:**
  - Replaced static raster screenshot (`snowflake_solution_architecture.png`) on Slide 10 in [`src/ppt_engine/reference_slides.py`](../src/ppt_engine/reference_slides.py) with a native 3-column OpenXML vector container architecture with official SVG tech logos (`kafka`, `snowflake`, `dbt`, `streamlit`, `vault`) and high-contrast orange callout boxes (`#FFF7ED` fill, `#EA580C` border).
  - Fixed Slide 12 Gantt timeline in [`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py): dynamically flipped Week 24 milestone diamond label leftwards (`mx - label_w - Inches(0.06)`) when nearing the right margin, preventing slide canvas bleed ($X > 13.333''$).
  - Evaluated narrow duration bars to prevent label collisions, stripped drop shadows across all timeline shapes (`shape.shadow.inherit = False`), and scaled timeline fonts from `Pt(7.0)`/`Pt(7.5)` to $\ge 11.0\text{pt}$.
  - Re-architected Slide 19 (`build_thank_you_slide`) to default to a clean corporate contact card (`contacts=None` / `show_staff_contacts=False`).
- **Phase 5: Automated Change Request Suite (CR_07):**
  - Enhanced [`src/core/change_request.py`](../src/core/change_request.py) with dynamic client routing via `EngagementContext` to `output/NGL_Snowflake_Analytics/change_requests/CR_07/`.
  - Implemented `_substitute_docx` and `_substitute_xlsx` for recursive post-generation document and workbook sanitization across paragraphs, table cells, and worksheets.
  - Verified zero legacy logos in `Change_Request_Form_CR_07.docx` and master template `4.4_Change_Request_Form_Template.docx`.
- Reference Handover: [`docs/handovers/2026-09-21_sprints_17_27_completion_briefing.md`](handovers/2026-09-21_sprints_17_27_completion_briefing.md)

---

## [2026-09-21] - Milestone 27: Automated Project Closing Deck Modernization (9 Slides)

### Summary
Delivered the end-to-end automated generation, dynamic spreadsheet synchronization, and consulting modernization of the 9-slide Project Closing & Maintenance Transition Presentation (`5.1_Project_Closing_Deck_Modernized.pptx`), completing the full presentation suite across the TTI Snowflake Analytics engagement. Audited production deliverable `clean_workspace/projects/TTI_Snowflake_Analytics/06_closing/5.1_Project_Closing_Deck_Template.pptx` (9 slides) and companion closeout workbook `5.2_Project_Closeout_Checklist_Template.xlsx` (19 deliverables, 7 scope items, 8 closeout gates, repository download links, archive passwords, and CSS survey links), replacing the legacy Slide 5 placeholder with a high-impact executive sign-off dashboard. Engineered `ClosingDeckBuilder` in `src/ppt_engine/closing_deck.py` enforcing sharp rectangular card geometry (`MSO_SHAPE.RECTANGLE`), unified title/subtitle text flow (`space_before = Pt(10)`), clean typographic metadata on cover (zero boxed containers, no cover footer/pagination), and safe pagination thresholding (`top >= Inches(6.8)`). Built `sync_with_spreadsheets` for automated ingestion from the closeout workbook, authored the 383-line master declarative specification in `presets/deck_configs/closing_deck.yaml`, expanded `bench ppt build-deck` in `src/cli.py` with `--checklist` and closing deck aliases, exported `ClosingDeckBuilder` in `src/ppt_engine/__init__.py`, and verified presentation and 9-slide preview artifacts in `output/presentations/`.

### Milestones Delivered
- **Milestone 27: Automated Project Closing Deck Modernization:**
  - **Forensic Deliverable & Spreadsheet Audit ([`clean_workspace/.../5.1_Project_Closing_Deck_Template.pptx`](../clean_workspace/projects/TTI_Snowflake_Analytics/06_closing/5.1_Project_Closing_Deck_Template.pptx)):**
    - Audited 9-slide production master template and identified empty legacy placeholder on Slide 5 ("Please refer to and walkthrough the companion Excel document").
    - Audited companion workbook [`clean_workspace/.../5.2_Project_Closeout_Checklist_Template.xlsx`](../clean_workspace/projects/TTI_Snowflake_Analytics/06_closing/5.2_Project_Closeout_Checklist_Template.xlsx) mapping 19 deliverables across 4 categories, 7 scope workstreams, 8 verification gates, Google Drive archive link, password, and CSS survey link.
    - Transformed Slide 5 into an executive sign-off matrix paired with credential access cards.
  - **Presentation Engine Architecture ([`src/ppt_engine/closing_deck.py`](../src/ppt_engine/closing_deck.py)):**
    - Built `ClosingDeckBuilder` assembling the complete 9-slide consulting presentation suite:
      - Slide 01: Hero cover typography, authentic dual vertical brand stripes (1 Red : 2 Blue ratio), clean typographic metadata columns (`PREPARED FOR` / `ENGAGEMENT PARTNER`), zero cover footers.
      - Slide 02: 6 numbered consulting agenda cards (`01`–`06`) in a balanced $2 \times 3$ grid.
      - Slide 03: 6 capability cards detailing delivered phases with `[DONE]` and `[DELIVERED]` status pills.
      - Slide 04: Top KPI summary bar (19 / 19 Deliverables, 8 Modules, SIT & UAT, BAST 1 & 2) + 4 category columns inventorying all 19 contractual deliverables with non-wrapping format badges (`[DOCX]`, `[PPTX]`, `[XLSX]`, `[CODE]`) and status pills.
      - Slide 05: Dynamic 8-gate closeout verification matrix with theme-resolved status pills + secure Google Drive package download card (with password pill `[ Metrodata2026! ]`) and CSS survey link card.
      - Slide 06: 3-metric KPI bar (30 Mandays, 0.5 Manday unit, 100% Rollover) + 3 deep-dive pillar cards (Capacity Metering, Rollover & Terms, Supported Scope).
      - Slide 07: 4-step horizontal process lifecycle connected by native vector right arrows (`MSO_SHAPE.RIGHT_ARROW`) + designated technical leads (Andi Wijaya & Vicko Bhayyu) and official communication channels / SLA targets.
      - Slide 08: 3 large delivery cards for Monthly Usage Recaps, Developer Timesheets, and Technical / CR Documentation.
      - Slide 09: Corporate closing slide with dual vertical brand stripes, leadership contacts, and corporate office address.
    - Exported in [`src/ppt_engine/__init__.py`](../src/ppt_engine/__init__.py).
  - **Dynamic Spreadsheet Ingestion Pipeline ([`src/ppt_engine/closing_deck.py`](../src/ppt_engine/closing_deck.py)):**
    - Implemented `sync_with_spreadsheets` in `ClosingDeckBuilder` extracting 19 contractual deliverables, 7 scope workstreams, 8 checklist verification gates, deliverable download URLs, extraction passwords, and CSS survey links directly from `5.2_Project_Closeout_Checklist_Template.xlsx`.
  - **Pagination & Geometric Guardrails ([`src/ppt_engine/closing_deck.py`](../src/ppt_engine/closing_deck.py)):**
    - Enforced `MSO_SHAPE.RECTANGLE` on all container cards and top accent stripes, preventing corner protruding artifacts and distortion.
    - Structured Action Titles and Subtitles within a single unified text frame using `space_before = Pt(10)` to eliminate coordinate collisions.
    - Implemented coordinate thresholding in `update_pagination()` (`shape.top >= Inches(6.8)`), strictly preventing body metric badges ("19 / 19") from being mutated by footer page number matching.
  - **Master Declarative Deck Configuration ([`presets/deck_configs/closing_deck.yaml`](../presets/deck_configs/closing_deck.yaml)):**
    - Authored a 383-line declarative YAML specification orchestrating all 9 slides with metadata, spreadsheet bindings, and consulting narratives.
  - **Unified CLI Expansion ([`src/cli.py`](../src/cli.py)):**
    - Added `--checklist` option in `bench ppt build-deck` and registered deck aliases `closing_deck`, `project_closing`, `closing`, and `maintenance_transition`.
  - **Verification Artifacts ([`output/presentations/`](../output/presentations/)):**
    - Generated modernized presentation [`output/presentations/5.1_Project_Closing_Deck_Modernized.pptx`](../output/presentations/5.1_Project_Closing_Deck_Modernized.pptx) (9 slides, 3.2 MB).
    - Rendered 9 high-resolution PNG slide preview images in [`output/presentations/previews/closing/`](../output/presentations/previews/closing/) (`slide_01.png` through `slide_09.png`).
  - Reference Handover: [`docs/handovers/2026-09-21_project_closing_deck_modernization.md`](handovers/2026-09-21_project_closing_deck_modernization.md)

---

## [2026-09-20] - Milestone 26: Automated Weekly Progress Report Deck Modernization (11 Slides)

### Summary
Delivered the end-to-end automated generation, dynamic milestone scaling, and consulting modernization of the 11-slide Weekly Progress Report Presentation (`4.2_Weekly_Progress_Report_Deck_Modernized.pptx` and `4.2_Weekly_Progress_Report_Deck_Modernized_Chart.pptx`). Analyzed production deliverable `clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Report_Deck_Template.pptx` aligning all 11 contractual milestones and real-world RAID register data. Modernized `build_milestone_status` in `src/ppt_engine/weekly_progress_deck.py` with dynamic row height and gap calculation, fitting all 11 contractual milestones cleanly above the slide footer ($Y \le 6.82''$) without collision. Built `generate_s_curve_chart_image` rendering high-DPI (200 DPI) consulting S-curve charts directly from `TimelineAggregator` progression points, upgraded `build_overall_progress` to support a dual layout mode (phase execution progress rows or embedded S-curve chart), built `sync_with_spreadsheets` for automated ingestion from timeline, risk register, and issue log spreadsheets, updated `presets/deck_configs/weekly_progress.yaml` with the complete 11-milestone register, and enhanced `bench ppt build-deck` in `src/cli.py` with `--sync-xlsx` (`-sx`), `--chart-mode`, and spreadsheet override flags.

### Milestones Delivered
- **Milestone 26: Automated Weekly Progress Report Deck Modernization:**
  - **Forensic Deliverable Analysis ([`clean_workspace/.../4.2_Weekly_Progress_Report_Deck_Template.pptx`](../clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Report_Deck_Template.pptx)):**
    - Identified all 11 contractual milestones on Slide 7 (Kick-off, FSD, Cloud Subscription, Development, SIT, UAT, Go-live, TSD, Knowledge Transfer, 2-Months Guarantee, Project Closure) and mapped real-world RAID log schemas across `4.5_Risk_Register_Template.xlsx` and `4.6_Issue_Log_Template.xlsx`.
  - **Dynamic Milestone Scaling Engine ([`src/ppt_engine/weekly_progress_deck.py`](../src/ppt_engine/weekly_progress_deck.py)):**
    - Implemented dynamic row height and gap budgeting in `build_milestone_status`, scaling row geometry, padding, and typography ($10\text{pt}$ numbering, $9.5\text{pt}$ description, $9\text{pt}$ dates, $8\text{pt}$ status pills with $0.24''$ height) to fit all 11 milestones cleanly above the footer divider ($Y \le 6.82''$) with zero collision.
  - **Consulting S-Curve Line Chart Generator ([`src/ppt_engine/weekly_progress_deck.py`](../src/ppt_engine/weekly_progress_deck.py)):**
    - Built `generate_s_curve_chart_image` rendering high-DPI (200 DPI) consulting S-curve charts from `TimelineAggregator` cumulative progress points (Planned Baseline `#0052CC`, Actual Progress `#10B981`, Schedule Variance fill `#EF4444`) saved to `output/presentations/charts/s_curve_weekly.png`.
    - Upgraded `build_overall_progress` with dual layout architecture: either detailed delivery phase execution progress rows or high-DPI cumulative S-curve charts.
  - **Dynamic Spreadsheet Ingestion Pipeline ([`src/ppt_engine/weekly_progress_deck.py`](../src/ppt_engine/weekly_progress_deck.py)):**
    - Implemented `sync_with_spreadsheets` in `WeeklyProgressDeckBuilder`, enabling automated synchronization with `4.2_Weekly_Progress_Timeline_Update_Template.xlsx` (KPIs, SPI, phase completion percentages), `4.5_Risk_Register_Template.xlsx` (active risk cards with 3-box probability/impact meters), and `4.6_Issue_Log_Template.xlsx` (active issue resolution plans).
    - Added `EngagementContext` client slug substitution support in `WeeklyProgressDeckBuilder.save`.
  - **Master Declarative Deck Configuration ([`presets/deck_configs/weekly_progress.yaml`](../presets/deck_configs/weekly_progress.yaml)):**
    - Updated Slide 7 to all 11 contractual milestones matching real-world project target and actual dates.
    - Added `spreadsheets` configuration mapping default spreadsheet paths for automated synchronization.
  - **Unified CLI Expansion ([`src/cli.py`](../src/cli.py)):**
    - Enhanced `bench ppt build-deck` with `--sync-xlsx` (`-sx`), `--chart-mode`, `--timeline`, `--risks`, and `--issues` flags, routing through `WeeklyProgressDeckBuilder`.
  - **Verification Artifacts ([`output/presentations/`](../output/presentations/)):**
    - Generated modernized presentation [`output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized.pptx`](../output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized.pptx) (11 slides, 3.2 MB).
    - Generated chart-embedded presentation [`output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized_Chart.pptx`](../output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized_Chart.pptx) (11 slides, 3.3 MB).
    - Generated high-DPI S-Curve line chart [`output/presentations/charts/s_curve_weekly.png`](../output/presentations/charts/s_curve_weekly.png).
    - Rendered 22 slide preview images in [`output/presentations/previews/weekly/`](../output/presentations/previews/weekly/) and [`output/presentations/previews/weekly_chart/`](../output/presentations/previews/weekly_chart/).
  - Reference Handover: [`docs/handovers/2026-09-20_weekly_progress_report_deck_modernization.md`](handovers/2026-09-20_weekly_progress_report_deck_modernization.md)

---

## [2026-09-20] - Milestone 25: Automated UAT Briefing Presentation Modernization (25 Slides)

### Summary
Delivered the end-to-end automated generation and consulting modernization of the 25-slide Bilingual User Acceptance Testing (UAT) Briefing Presentation (`3.4_Sosialisasi_UAT_Briefing_Modernized.pptx`), establishing a deterministic, brand-compliant presentation pipeline for client testing onboarding. Conducted deep forensic analysis of `clean_workspace/projects/TTI_Snowflake_Analytics/04_executing/3.4_Sosialisasi_UAT_Briefing_Template.pptx` uncovering 25 full slides (correcting the preliminary 15-slide catalog estimate), codified the comprehensive 922-line master specification in `presets/deck_configs/uat_briefing.yaml`, enhanced `src/ppt_engine/consulting_archetypes.py` with independent bullet list formatting in `build_browser_mockup_slide`, calibrated precision typography advance (`font.getlength`) and soft breaks in `src/ppt_engine/slide_exporter.py`, normalized Gantt models and added `app_walkthrough` aliases in `src/ppt_engine/pitch_deck.py`, routed UAT deck types in `src/cli.py`, and verified presentation and 25-slide preview artifacts in `output/presentations/`.

### Milestones Delivered
- **Milestone 25: Automated UAT Briefing Presentation Modernization:**
  - **Forensic Template Analysis ([`clean_workspace/.../3.4_Sosialisasi_UAT_Briefing_Template.pptx`](../clean_workspace/projects/TTI_Snowflake_Analytics/04_executing/3.4_Sosialisasi_UAT_Briefing_Template.pptx)):**
    - Uncovered that the production master template comprises 25 full slides (1 cover, 1 agenda, 7 testing/governance framework slides, 1 chapter transition divider, 14 live application UI walkthrough slides, and 1 closing slide), expanding the preliminary 15-slide catalog scope into an exhaustive enterprise testing guide.
  - **Master Declarative Deck Configuration ([`presets/deck_configs/uat_briefing.yaml`](../presets/deck_configs/uat_briefing.yaml)):**
    - Codified a 922-line master specification orchestrating all 25 slides: hero cover, 2-column numbered agenda, UAT objectives, analytical scope, 6-week delivery Gantt, execution ground rules, defect triage workflows, defect severity & SLA matrix, exit criteria & sign-off gates, dark scrim chapter divider, 14 browser mockup application walkthroughs, and closing Q&A.
  - **Consulting Archetype List Formatting ([`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py)):**
    - Enhanced `build_browser_mockup_slide` observation cards to detect and iterate structured bullet lists (`list`), applying individual bullet typography, spacing, and colors to eliminate unformatted string blobs.
  - **Slide Exporter Precision Typography ([`src/ppt_engine/slide_exporter.py`](../src/ppt_engine/slide_exporter.py)):**
    - Switched text token advance measurement from bounding box (`getbbox`) to FreeType advance width (`font.getlength`), resolving whitespace under-calculation and adjacent word overlapping.
    - Added soft-break sanitization in `_wrap_text` handling vertical tabs (`\x0b`) and carriage returns (`\r`).
  - **Pitch Deck Builder Enhancements ([`src/ppt_engine/pitch_deck.py`](../src/ppt_engine/pitch_deck.py)):**
    - Implemented dictionary normalization in `timeline_gantt` deserialization (`name` $\rightarrow$ `category`, `accent_key` $\rightarrow$ `accent_color`, `total_weeks` $\rightarrow$ `total_periods`, `duration_weeks` conversion).
    - Registered archetype aliases `app_walkthrough`, `window_mockup`, `app_mockup`, and `module_walkthrough` routing to `build_browser_mockup_slide`.
    - Added parameter aliases supporting `screenshot_path`, `screenshot`, or `image_path`.
  - **CLI Deck Type Routing ([`src/cli.py`](../src/cli.py)):**
    - Added `uat_briefing`, `uat_deck`, `sosialisasi_uat`, and `uat` aliases in `bench ppt build-deck` routing directly to `PitchDeckBuilder`.
  - **Verification Artifacts ([`output/presentations/`](../output/presentations/)):**
    - Generated modernized 25-slide presentation [`output/presentations/3.4_Sosialisasi_UAT_Briefing_Modernized.pptx`](../output/presentations/3.4_Sosialisasi_UAT_Briefing_Modernized.pptx).
    - Rendered 25 high-resolution slide preview images in [`output/presentations/previews/uat/`](../output/presentations/previews/uat/) (`slide_01.png` through `slide_25.png`).
  - Reference Handover: [`docs/handovers/2026-09-20_uat_briefing_presentation_modernization.md`](handovers/2026-09-20_uat_briefing_presentation_modernization.md)

---

## [2026-09-19] - Milestone 24: Automated Project Kick-off Presentation Modernization (19 Slides)

### Summary
Delivered the end-to-end automated generation and consulting modernization of the 19-slide Project Kick-off Presentation (`1.1_Project_Kick-off_Material_Modernized.pptx`), creating a deterministic, reusable presentation pipeline for stakeholder initiation meetings. Engineered three new consulting archetypes (`AgendaItem` / `build_agenda_slide`, `TableColumnDef` / `build_table_slide` with automated status pills and alternating fills, `build_thank_you_slide` with dual brand vertical stripes and contact cards) in `src/ppt_engine/consulting_archetypes.py`, extended `build_governance_org_structure_slide` in `src/ppt_engine/reference_slides.py` with parameter overrides, enhanced `PitchDeckBuilder` in `src/ppt_engine/pitch_deck.py` with slide dispatchers and nested Gantt deserialization, added CLI deck-type aliases in `src/cli.py`, codified the 882-line master YAML in `presets/deck_configs/kickoff_presentation.yaml`, and produced presentation and 19-slide preview artifacts in `output/presentations/`.

### Milestones Delivered
- **Milestone 24: Automated Project Kick-off Presentation Modernization:**
  - **Consulting Slide Archetypes ([`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py)):**
    - `AgendaItem` & `build_agenda_slide`: Balanced multi-column executive agenda/table of contents slide with sharp rectangular card geometry (`MSO_SHAPE.RECTANGLE`), left number boxes (`01`, `02`), bold titles, and optional descriptions.
    - `TableColumnDef` & `build_table_slide`: Vector card-based consulting matrix with solid primary header band, proportional column scaling, alternating row fills (`surface` / `surface_muted`), automated status pills (`COMPLETE`, `ON TRACK`, `CRITICAL GATE`, `SIGNED-OFF`, etc.), and footnotes.
    - `build_thank_you_slide`: Corporate closing slide with Metrodata dual vertical brand stripes (1 red : 2 blue ratio), 36pt title, tracker breadcrumb, contact cards with top accent stripes, and company entity/office address footer.
  - **Reference Slide Parameter Overrides ([`src/ppt_engine/reference_slides.py`](../src/ppt_engine/reference_slides.py)):**
    - Parameterized `build_governance_org_structure_slide` with `tier1_client_text`, `tier1_vendor_text`, `client_pm_title`, `vendor_pm_title`, `client_pm_bullets`, `vendor_pm_bullets`, and custom `pods` list, enabling client-specific org tree customization while preserving locale translation fallbacks.
  - **Pitch Deck Builder Enhancements ([`src/ppt_engine/pitch_deck.py`](../src/ppt_engine/pitch_deck.py)):**
    - Implemented dispatchers for `agenda`, `table`, `thank_you`, and forwarded governance parameters.
    - Fixed nested dictionary deserialization for `timeline_gantt` slides into `GanttTimelineData`, `GanttWorkstream`, and `GanttTask` models.
    - Synchronized slide footers and pagination across slides 02–19 (`02 / 19` through `19 / 19`) while preserving clean cover typography on Slide 01.
  - **CLI Enhancements ([`src/cli.py`](../src/cli.py)):**
    - Added deck-type aliases (`kickoff_deck`, `kickoff`, `project_kickoff`, `declarative`) routing directly to `PitchDeckBuilder` in `bench ppt build-deck`.
  - **Master Declarative Deck Configuration ([`presets/deck_configs/kickoff_presentation.yaml`](../presets/deck_configs/kickoff_presentation.yaml)):**
    - Codified all 19 slides (background gap analysis, project objectives, stakeholder roles, RACI tree, workstreams, deliverables, assumptions, To-Be architecture, phased timelines, 24-week delivery Gantt, milestone register, prerequisites, communication cadences, risk register, CR procedure, Q&A, and closing).
  - **Verification Artifacts ([`output/presentations/`](../output/presentations/)):**
    - Generated modernized presentation [`output/presentations/1.1_Project_Kick-off_Material_Modernized.pptx`](../output/presentations/1.1_Project_Kick-off_Material_Modernized.pptx) (3.17 MB, 19 slides).
    - Rendered 19 high-fidelity PNG slide preview images in [`output/presentations/previews/kickoff/`](../output/presentations/previews/kickoff/) (`slide_01.png` through `slide_19.png`).
  - Reference Handover: [`docs/handovers/2026-09-19_project_kickoff_presentation_modernization.md`](handovers/2026-09-19_project_kickoff_presentation_modernization.md)

---

## [2026-09-19] - Milestone 23: Automated Presales Consulting Pitch Deck Modernization (36 Slides)

### Summary
Delivered the end-to-end automated generation and consulting modernization of the 36-slide Presales Modernization Pitch Deck (`Modernize_Data_Platform_Pitch_Deck_Modernized.pptx`), transforming legacy slide collateral into a structured, deterministic presentation pipeline. Engineered `PitchDeckBuilder` in `src/ppt_engine/pitch_deck.py`, added four new executive consulting archetypes (`TechLogoItem`, `CardGridItem`, `BadgeMatrixSection`, `build_iceberg_concept_slide`, `build_tech_logo_grid_slide`, `build_card_grid_slide`, `build_badge_matrix_slide`) in `src/ppt_engine/consulting_archetypes.py`, codified the 36-slide master declarative specification in `presets/deck_configs/presales_pitch_deck.yaml`, expanded the unified CLI with `bench ppt build-deck` (`--config`, `--slides`, `--theme`, `--context`), and generated full verification presentation and headless preview artifacts in `output/presentations/`.

### Milestones Delivered
- **Milestone 23: Automated Presales Consulting Pitch Deck Modernization:**
  - **Pitch Deck Builder Subsystem ([`src/ppt_engine/pitch_deck.py`](../src/ppt_engine/pitch_deck.py)):** Implemented `PitchDeckBuilder` to encapsulate complete deck lifecycle management: declarative YAML ingestion, archetype dispatching across 15+ slide types, post-processing footer pagination (`update_pagination` synchronizing `02 / 36` to `36 / 36` with zero pagination on Slide 1), and dynamic client slug substitution (`EngagementContext`).
  - **Consulting Slide Archetypes ([`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py)):**
    - `TechLogoItem` & `build_tech_logo_grid_slide`: Standardized multi-column partner technology grids with sharp rectangular card geometry (`MSO_SHAPE.RECTANGLE`), flush top accent stripes, status pills (`CORE PLATFORM`, `MODELING`, `STORAGE`), aspect-ratio-preserved emblem slots, and structured descriptions.
    - `CardGridItem` & `build_card_grid_slide`: Configurable $N \times M$ capability grid (Metrodata 8 Pillars, Data & AI Portfolio) with harmonized Lucide icons, top accent stripes, bulleted descriptions, and status badges.
    - `BadgeMatrixSection` & `build_badge_matrix_slide`: Tiered partner credential and certification matrix with category header bars, badge count labels (`TIER 1 STATUS`, `CERTIFIED PRACTICE`), and structured competency items.
    - `build_iceberg_concept_slide`: High-impact consulting metaphor splitting canvas into an Above the Waterline container (Visible 15% Business Interface: dashboards, Streamlit apps, GenAI) and a Below the Waterline container (Subsurface 85% Data Platform Foundation: lakehouse, CDC, dbt modeling, RBAC, DAGs, FinOps) alongside executive strategic rationale callouts.
  - **Master Declarative Deck Configuration ([`presets/deck_configs/presales_pitch_deck.yaml`](../presets/deck_configs/presales_pitch_deck.yaml)):** Authored a 900-line declarative specification mapping all 36 slides across Phase 1 (Company Profile, Portfolio & Core Snowflake) and Phase 2 (Challenges, Target Architecture, Scope & Governance) with complete headlines, subtitles, trackers, metrics, and parameters.
  - **Unified CLI Expansion ([`src/cli.py`](../src/cli.py)):** Enhanced `bench ppt build-deck` with `--config`, `--slides`, `--theme`, and `--context` options, routing `presales_pitch_deck` configurations directly through `PitchDeckBuilder`.
  - **Verification Artifacts ([`output/presentations/`](../output/presentations/)):** Generated full 36-slide deck [`output/presentations/Modernize_Data_Platform_Pitch_Deck_Modernized.pptx`](../output/presentations/Modernize_Data_Platform_Pitch_Deck_Modernized.pptx) (4.8 MB), 18-slide slice [`output/presentations/presales_pitch_deck_phase1.pptx`](../output/presentations/presales_pitch_deck_phase1.pptx) (3.6 MB), and 36 headless slide preview images in [`output/presentations/previews/`](../output/presentations/previews/).
  - Reference Handover: [`docs/handovers/2026-09-19_presales_pitch_deck_modernization.md`](handovers/2026-09-19_presales_pitch_deck_modernization.md)

---

## [2026-09-19] - Milestone 22: Presentation & Diagram Visual Harmonization and DirectWrite Preview Parity

### Summary
Delivered cross-cutting visual harmonization across presentation archetypes, diagramming engines, and slide preview generation. Expanded `IconEngine` with canonical brand color resolution and universal SVG dynamic recoloring, established `add_card_with_harmonized_icon` and synchronized brand icons across BCG, McKinsey, and Balanced Scorecard archetypes, added semantic role binding and base64 data URI safety in `DiagramEngine`, calibrated DirectWrite typography metrics (0.915 kerning factor, 1.18x line height) in `PurePythonSlideRenderer`, and extended the CLI with direct YAML diagram exports and `bench ppt export-preview`.

### Milestones Delivered
- **Milestone 22: Presentation & Diagram Visual Harmonization and DirectWrite Preview Parity:**
  - **Brand Color Resolution & Dynamic Recoloring ([`src/ppt_engine/icon_engine.py`](../src/ppt_engine/icon_engine.py)):** Codified `CANONICAL_ENTERPRISE_COLORS` and implemented `resolve_brand_color(color, theme=None)` for theme tokens (`accent`, `primary`, `secondary`, `accent_teal`, `danger`, `surface`, etc.). Upgraded `recolor_svg` to dynamically tint both stroke and fill vectors across quoted attributes and inline CSS styles.
  - **Consulting Archetype Harmonization ([`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py)):** Built `add_card_with_harmonized_icon` enforcing sharp rectangular geometry (`MSO_SHAPE.RECTANGLE`), flush top accent stripes, and dynamically tinted brand icons. Upgraded BCG 3 Horizons, McKinsey Cascade, and Balanced Scorecard archetypes with synchronized semantic icons and color palettes.
  - **Diagram Engine Semantic Roles & Base64 Data URIs ([`src/ppt_engine/diagram_engine.py`](../src/ppt_engine/diagram_engine.py)):** Implemented `apply_node_icons` to bind semantic palette roles to card strokes and icon tints. Added native base64 data URI `<image xlink:href="..."/>` rendering, fixed semicolon splitting in `mxgraph_to_ast` via `__B64SEP__`, and normalized thin outline strokes to $\ge 1.75\text{px}$.
  - **DirectWrite Typography Calibration ([`src/ppt_engine/slide_exporter.py`](../src/ppt_engine/slide_exporter.py)):** Calibrated font metric kerning with a `0.915` width factor, reduced line height multiplier to $1.18\times$, and adjusted paragraph spacing to $2.0\text{pt}$, completely eliminating artificial line wraps and vertical text bloat in Pillow preview images.
  - **Unified CLI Extensions ([`src/cli.py`](../src/cli.py)):** Enabled direct `.yaml` specification support in `bench diagram export` and `bench diagram export-all`, and introduced `bench ppt export-preview` for rapid presentation inspection.
  - Reference Handover: [`docs/handovers/2026-09-19_visual_harmonization_and_directwrite_preview_parity.md`](handovers/2026-09-19_visual_harmonization_and_directwrite_preview_parity.md)

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
  - Modular Spec Compiler ([`src/docx_engine/spec_compiler.py`](../src/docx_engine/spec_compiler.py)): Multi-chapter Markdown compiler parsing frontmatter, H1–H4 headings, callout alerts (`> [!NOTE]`), tables, and code callouts into styled Word deliverables with corporate cover pages. Added Markdown image parser (`![Caption](<path>)`) embedding centered high-DPI figures with italicized captions.
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
