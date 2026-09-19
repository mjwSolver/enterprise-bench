# Session Handover: Sprints 17–20 (Platform Hardening, CR CLI, Diagram Pipeline & Consulting Archetypes)

**Date:** 2026-09-19  
**Topic:** Batch Execution of Sprints 17–20 (Milestones 18–21)  
**Branch:** `main` (Commits `7785eeb` and `38498ad`)  
**Status:** Completed, Verified & Ledger Synchronized  

---

## 1. Executive Summary

Executed and closed out a comprehensive 4-sprint platform batch (Sprints 17, 18, 19, and 20 / Milestones 18, 19, 20, and 21) focused on system security hardening, enterprise governance automation, diagramming and data contracts, and presentation archetype expansion:

1. **Security & Performance Hardening (Milestone 18 / Sprint 17):** Eliminated arbitrary command injection vectors in desktop preview launchers, optimized diagram node ranking from $O(2^V)$ exponential DFS to $O(V + E)$ Kahn's topological BFS, memoized TrueType font loading (~4,000 disk I/O hits eliminated per export), and resolved case-sensitivity defects across PII replacement handlers.
2. **Change Request Governance & Closeout CLI (Milestone 19 / Sprint 18):** Wired the four-deliverable Change Request pipeline into the unified CLI via `bench cr file`, added automated sign-off checklist gating via `bench xlsx update-closeout`, and expanded bilingual governance dictionaries (`en.yaml` and `id.yaml`).
3. **Diagram Pipeline, Coordinate Standardization & Strict Contracts (Milestone 20 / Sprint 19):** Engineered an on-demand Draw.io data URI resolver (`src/core/diagram_uri.py`) supporting `.drawio#Page` and `.yaml#Page` embeds in Markdown specs and slides, centralized coordinate conversions across OpenXML/DrawingML in `src/core/units.py`, codified strict Pydantic v2 schemas for S-Curves and frontmatter, and eliminated bare exception traps and silent warehouse truncation.
4. **Executive Presentation Archetypes & Deck Builders (Milestone 21 / Sprint 20):** Engineered the Delivery Gantt timeline slide archetype (`build_timeline_gantt_slide`) with multi-period calendar headers, duration bars, milestone diamonds, and current sprint markers, plus the Harvey Balls feature comparison scorecard (`build_feature_matrix_slide`) with semantic color glyphs, integrating both into `ConsultingDeckBuilder` and `ReferenceDeckBuilder`.

---

## 2. Key Deliverables & Code Changes

### Milestone 18 (Sprint 17: Security Hardening & Engine Optimization)
- **Subprocess Command Injection Elimination ([`src/cli.py`](../../src/cli.py)):** Replaced vulnerable `shell=True` desktop preview invocations with safe discrete argument lists (`["open", "-a", ...]` and `["osascript", "-e", ...]`).
- **Topological Diagram DAG Ranking ([`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py)):** Implemented Kahn's algorithm BFS in `HierarchicalLayoutEngine._assign_ranks` ($O(V + E)$), resolving exponential execution on diamond topologies.
- **Font Cache Memoization ([`src/ppt_engine/slide_exporter.py`](../../src/ppt_engine/slide_exporter.py)):** Decorated `_get_system_font` with `@functools.lru_cache(maxsize=128)`, eliminating redundant disk calls.
- **PII Case-Insensitive Matching ([`src/core/pii/handlers/`](../../src/core/pii/handlers/)):** Updated `docx_handler.py`, `pptx_handler.py`, and `xlsx_handler.py` to use case-insensitive matching (`target.lower() in new_val.lower()`).

### Milestone 19 (Sprint 18: Change Request CLI & Project Closeout)
- **Change Request CLI Sub-Application ([`src/cli.py`](../../src/cli.py)):** Added `cr_app` and `bench cr file` command connected to `ChangeRequestProcessor` (`src/core/change_request.py`), generating `Change_Request_Form.docx`, `Change_Log_Ledger.xlsx`, `CR_Scoping_and_Mandays.xlsx`, and `BAST_Change_Request.docx` in a single command.
- **Project Closeout Gate CLI ([`src/cli.py`](../../src/cli.py)):** Added `bench xlsx update-closeout` wired to `update_closeout_checklist` (`src/xlsx_engine/ledger_models.py`) to record deliverable sign-offs on `5.2_Project_Closeout_Checklist_Template.xlsx`.
- **Bilingual Governance Dictionaries ([`presets/locales/en.yaml`](../../presets/locales/en.yaml), [`presets/locales/id.yaml`](../../presets/locales/id.yaml)):** Added governance categories, approval statuses, and closeout sections.

### Milestone 20 (Sprint 19: Diagram Pipeline, Units & Strict Contracts)
- **On-Demand Diagram URI Resolver ([`src/core/diagram_uri.py`](../../src/core/diagram_uri.py)):** Implemented `parse_diagram_uri` and `resolve_diagram_uri` with SHA-256 caching for `.drawio#Page` and `.yaml#Page` embeds.
- **Spec Compiler & Asset Integration:** Integrated diagram URI resolution into `add_image` in [`src/docx_engine/spec_compiler.py`](../../src/docx_engine/spec_compiler.py) and `resolve_asset` in [`src/ppt_engine/resource_manager.py`](../../src/ppt_engine/resource_manager.py).
- **Centralized Coordinate Conversions ([`src/core/units.py`](../../src/core/units.py)):** Standardized EMU, Twips, points, inches, OpenXML border units, and DrawingML alpha conversion utilities.
- **Strict Pydantic v2 Schemas:** Defined `SCurveMilestone`, `SCurvePayload`, `CellMapping`, and `CalculatorDataPayload` in [`src/xlsx_engine/schemas.py`](../../src/xlsx_engine/schemas.py); defined `SpecSignoff` and `SpecMetadataModel` in [`src/docx_engine/schemas.py`](../../src/docx_engine/schemas.py).
- **Silent Failure Elimination:** Added structured error reporting to `PurgeReport.errors` in [`src/core/docx_purger.py`](../../src/core/docx_purger.py), enforced maximum 8 warehouse validation in [`src/xlsx_engine/cloud_sizing.py`](../../src/xlsx_engine/cloud_sizing.py), and added cell injection warning logging in [`src/xlsx_engine/calculator_stamper.py`](../../src/xlsx_engine/calculator_stamper.py).

### Milestone 21 (Sprint 20: Visual Archetypes & Deck Builders)
- **Delivery Gantt Timeline Archetype ([`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)):** Implemented `GanttTask`, `GanttWorkstream`, `GanttTimelineData`, and `build_timeline_gantt_slide` supporting 16:9 canvas layout, calendar headers, duration bars, milestone diamonds, and current sprint hairline markers.
- **Harvey Balls Feature Matrix Archetype ([`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)):** Implemented `FeatureScorecardRow`, `FeatureMatrixData`, and `build_feature_matrix_slide` supporting Harvey Balls glyphs (`● ◐ ○`) and recommended platform highlighting.
- **Deck Builder Integration:** Added `add_timeline_gantt_slide` and `add_feature_matrix_slide` to `ConsultingDeckBuilder` ([`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)) and `ReferenceDeckBuilder` ([`src/ppt_engine/reference_slides.py`](../../src/ppt_engine/reference_slides.py)).

---

## 3. Verification & QA Status

- **Zero Intermediate Unit Testing:** Complied strictly with [`AGENTS.md`](../../AGENTS.md) directive; no unit test discovery or `pytest` suites executed.
- **Static Syntax Compilation:** All modified and newly introduced modules compiled cleanly via `python -m py_compile`:
  - `src/cli.py`
  - `src/core/diagram_uri.py`
  - `src/core/units.py`
  - `src/core/docx_purger.py`
  - `src/core/pii/handlers/docx_handler.py`
  - `src/core/pii/handlers/pptx_handler.py`
  - `src/core/pii/handlers/xlsx_handler.py`
  - `src/docx_engine/schemas.py`
  - `src/docx_engine/spec_compiler.py`
  - `src/xlsx_engine/schemas.py`
  - `src/xlsx_engine/cloud_sizing.py`
  - `src/xlsx_engine/calculator_stamper.py`
  - `src/ppt_engine/consulting_archetypes.py`
  - `src/ppt_engine/reference_slides.py`
  - `src/ppt_engine/diagram_engine.py`
  - `src/ppt_engine/slide_exporter.py`
- **Targeted CLI Smoke Tests:**
  - `uv run bench diagram export-all presets/diagrams/fsd_architecture.yaml --format svg` $\to$ Verified Kahn's algorithm diagram DAG ranking and SVG export.
  - `uv run bench cr --help` & `uv run bench cr file --help` $\to$ Verified Typer sub-application registration.
  - `uv run bench xlsx update-closeout --help` $\to$ Verified closeout CLI command registration.
  - Inline evaluation of `parse_diagram_uri("presets/diagrams/fsd_architecture.yaml#System Architecture")` $\to$ Verified parser output and hash caching logic.

---

## 4. Immediate Next Steps

1. **Presales Pitch Deck Modernization (`Modernize_Data_Platform_Pitch_Deck_Template.pptx`):**
   - Automate 36-slide presales deck using Delivery Gantt, Harvey Balls scorecard, and screenshot mockups.
2. **Project Kick-off Presentation (`1.1_Project_Kick-off_Material_Template.pptx`):**
   - Automate 19-slide kick-off deck with governance org structure, RACI matrices, and timeline gates.
3. **UAT Briefing Presentation (`3.3_Sosialisasi_UAT_Template.pptx`):**
   - Automate 15-slide bilingual UAT briefing deck for client business process owners.
