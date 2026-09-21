# Session Handover: Sprints 17–27 Review & Enhancement Sprint (Phases 1–5)

**Date:** 2026-09-21  
**Topic:** Sprints 17–27 Review & Enhancement Sprint Completion (Phases 1–5)  
**Branch:** `main`  
**Status:** Completed, Verified & Ledger Synchronized  
**Operating Directives:** [`AGENTS.md`](../../AGENTS.md) (Strict ZERO INTERMEDIATE UNIT TESTING)

---

## 1. Executive Summary

This transition briefing documents the comprehensive implementation and verification of the **Sprints 17–27 Review & Enhancement Sprint (Phases 1–5)**, executing the authoritative architectural blueprint established in [`docs/handovers/2026-09-21_sprints_17_27_review_and_enhancement_roadmap.md`](2026-09-21_sprints_17_27_review_and_enhancement_roadmap.md).

All five implementation phases have been delivered, statically verified, and harmonized across `enterprise-bench` engines (`src/ppt_engine`, `src/docx_engine`, `src/xlsx_engine`, `src/core`):

1. **Phase 1 — Universal Slug & PII Normalization:** Established **"Nusantara Global Logistics"** (`NGL`) as the system-wide canonical default client entity in [`src/core/slug_registry.py`](../../src/core/slug_registry.py). Implemented recursive slide shape and group shape traversal in `substitute_slugs_in_presentation`. Sanitized all master YAML presets and enforced a global optical font floor ($\ge 11.0\text{pt}$).
2. **Phase 2 — Project Closing Deck (`5.1`) Visual Enrichment:** Integrated Lucide vector icons tinted with theme accents across Agenda, Capability, Deliverable, and Checklist slides in [`src/ppt_engine/closing_deck.py`](../../src/ppt_engine/closing_deck.py). Upgraded Slide 07 from flat boxes into a formal 3-swimlane maintenance workflow. Re-architected Slide 09 to default to a clean corporate closing.
3. **Phase 3 — Weekly Progress Report (`4.2`) Typography & Language Purity:** Resolved the Slide 07 milestone row vertical alignment defect using `MSO_ANCHOR.MIDDLE` on full row height text frames. Upgraded Slide 08 risk mitigations with DrawingML bullet glyphs and hanging indents. Enforced a 100% pure English baseline across presets and builders, eliminating bilingual language contamination.
4. **Phase 4 — Project Kick-off Material (`1.1`) Defect Rectification:** Deprecated the static raster architecture screenshot on Slide 10 in [`src/ppt_engine/reference_slides.py`](../../src/ppt_engine/reference_slides.py), replacing it with a native 3-column OpenXML vector architecture featuring official SVG logos and high-visibility orange callout boxes. Resolved Slide 12 Gantt canvas bleed via dynamic milestone diamond label flipping, prevented duration bar text overflow, stripped drop shadows, and set Slide 19 to clean corporate closing defaults.
5. **Phase 5 — Automated Change Request Suite (`CR_07`):** Enhanced [`src/core/change_request.py`](../../src/core/change_request.py) with dynamic client routing to `output/NGL_Snowflake_Analytics/change_requests/CR_07/`. Integrated `_substitute_docx` and `_substitute_xlsx` for recursive post-generation document sanitization. Confirmed zero legacy logos across all CR deliverables and clean workspace templates.

---

## 2. Phase-by-Phase Technical Implementations

### Phase 1: Universal Slug & PII Normalization

- **Canonical Slug Constants & Default Registry ([`src/core/slug_registry.py`](../../src/core/slug_registry.py)):**
  - Codified canonical constants:
    - `DEFAULT_CLIENT_COMPANY_NAME = "Nusantara Global Logistics"`
    - `DEFAULT_CLIENT_SHORT_NAME = "NGL"`
    - `DEFAULT_CLIENT_ADDRESS = "Gedung Cyber 2, Lt. 18, Jl. H.R. Rasuna Said, Jakarta Selatan"`
    - `DEFAULT_PROJECT_NAME = "Enterprise Financial Intelligence & Cloud Analytics Platform"`
    - `DEFAULT_VENDOR_COMPANY_NAME = "PT Metrodata Electronics Tbk"`
    - `DEFAULT_VENDOR_SHORT_NAME = "Metrodata"`
    - `DEFAULT_VENDOR_DIVISION = "Data & AI Modernization Practice"`
  - Added `EngagementContext.default_ngl()` and updated `EngagementContext` model fields to bind to canonical constants.
  - Implemented `EngagementContext.substitute(text: str)` performing complete slug token expansion alongside regex scrubbing of legacy client variants (`PT Toyota Tsusho Indonesia`, `Toyota Tsusho Indonesia`, `Toyota Tsusho`, `TTLC`, `TTI`).

- **Recursive Slide Shape & Group Shape Traversal ([`src/core/slug_registry.py`](../../src/core/slug_registry.py)):**
  - Updated `substitute_slugs_in_presentation(prs, replacement_map)`:
    - Implemented recursive `_process_shape(shape)` traversing simple shapes, tables, and nested group shapes (`shape.shapes`).
    - Traverses all paragraphs and runs within shape text frames and table cells, substituting slug tokens at run level where present (to preserve run styling) or paragraph level when tokens span across runs.

- **Master YAML Preset Sanitization ([`presets/deck_configs/`](../../presets/deck_configs/)):**
  - Normalized `closing_deck.yaml`, `kickoff_presentation.yaml`, `presales_pitch_deck.yaml`, `uat_briefing.yaml`, and `weekly_progress.yaml`.
  - Replaced hardcoded legacy client names with `[CLIENT_COMPANY_NAME]` and `[CLIENT_SHORT_NAME]`.
  - Updated confidentiality notices to standard format: `"[CLIENT_COMPANY_NAME] & [VENDOR_COMPANY_NAME]  |  Confidential"`.

- **Global Optical Font Size Floor ($\ge 11.0\text{pt}$):**
  - Eliminated micro-typography ($\le 8\text{pt}$, $7.5\text{pt}$, $7.0\text{pt}$) across all presentation builders and archetypes.
  - Standardized font floors: category tags $\ge 11.0\text{pt}$, footnotes and table cells $\ge 11.0\text{pt}$, body copy $\ge 11.0\text{pt}$ (target $12.0\text{pt}$), card headers $\ge 13.0\text{pt}$ to $14.0\text{pt}$.

---

### Phase 2: Project Closing Deck (`5.1`) Visual Enrichment

- **Lucide Icon Integration ([`src/ppt_engine/closing_deck.py`](../../src/ppt_engine/closing_deck.py)):**
  - Added vector Lucide glyphs tinted with `theme.accent` across key slide layouts:
    - **Slide 02 (Agenda):** Categorical icons paired with numbered badges (`compass`, `package-check`, `file-signature`, `shield-check`, `git-pull-request`, `bar-chart-3`).
    - **Slide 03 (Capability Review):** Integrated `add_card_with_harmonized_icon` across delivered architecture phases.
    - **Slide 04 (Deliverables Register):** Replaced plain text format tags with distinct vector format badges (`file-text` for DOCX, `presentation` for PPTX, `table` for XLSX, `code` for SQL/Python).
    - **Slide 05 (Closing Checklist & Access):** Embedded security and repository icons for Google Drive archive download and CSS customer feedback cards.

- **3-Swimlane Maintenance Support Workflow ([`src/ppt_engine/closing_deck.py`](../../src/ppt_engine/closing_deck.py)):**
  - Re-architected Slide 07 from flat sequential boxes into a formal 3-swimlane operational flowchart:
    - **Swimlane 1 (Client Organization):** Incident Logging & Initial Qualification.
    - **Swimlane 2 (Metrodata L1/L2 Managed Services):** Triage, SLA Dispatch & Root Cause Analysis.
    - **Swimlane 3 (Lead Development / Core Engineering):** Defect Remediation, Hotfix Testing & UAT Sign-off.
  - Added explicit SLA badges (P1 Critical: 2h Response / 8h Resolution; P2 Major: 4h Response / 24h Resolution; P3 Minor: Next Release).

- **Slide 09 Clean Corporate Closing:**
  - Modernized `build_closing_slide` to default to an authoritative corporate closing card featuring the Practice Brand lockup, official support alias (`enterprise.consulting@metrodata.co.id`), and corporate headquarters address, avoiding hardcoded personal staff emails by default.

---

### Phase 3: Weekly Progress Report (`4.2`) Typography & Language Purity

- **Slide 07 Milestone Status Row Vertical Alignment Defect Fix ([`src/ppt_engine/weekly_progress_deck.py`](../../src/ppt_engine/weekly_progress_deck.py)):**
  - *Diagnosis:* Text frames `tb0`, `tb1`, `tb2`, `tb3` previously defaulted to `MSO_ANCHOR.TOP` with top padding, causing text (`01`, `Kick-off Meeting`, dates) to stick to the upper border while the `COMPLETED` status pill was vertically centered.
  - *Resolution:*
    - Created text boxes with full row height: `add_textbox(x, cur_ry, col_w, row_h)`.
    - Set `tf.vertical_anchor = MSO_ANCHOR.MIDDLE` on all milestone text frames (`tf0`, `tf1`, `tf2`, `tf3`).
    - Zeroed out text frame margins: `tf.margin_top = tf.margin_bottom = 0`.
    - Harmonized typography font floor to $11.0\text{pt}$.

- **Slide 08 Risk Register Native Bullets & Hanging Indents ([`src/ppt_engine/weekly_progress_deck.py`](../../src/ppt_engine/weekly_progress_deck.py)):**
  - Replaced unstructured text paragraphs with `_add_bullet_paragraph`.
  - Added DrawingML hanging indents (`marL="288000"`, `indent="-288000"`) and bullet glyphs (`•`), ensuring multi-line mitigations wrap neatly beneath text without crowding bullet points.

- **100% Pure English Baseline ([`presets/deck_configs/weekly_progress.yaml`](../../presets/deck_configs/weekly_progress.yaml)):**
  - Replaced Indonesian phrases in master presets with pure English equivalents:
    - Root cause: *"AKAR MASALAH"* $\rightarrow$ *"ROOT CAUSE & ANALYSIS"*
    - Impact: *"ANALISIS DAMPAK"* $\rightarrow$ *"SCHEDULE & DELIVERY IMPACT"*
    - Action Plan: *"RENCANA RESOLUSI"* $\rightarrow$ *"CORRECTIVE RESOLUTION PLAN"*
    - Active risk descriptions and mitigations standardized to 100% English.
  - Enforced separation: Indonesian localization is preserved strictly through dedicated locale catalog pipelines (`presets/locales/id.yaml`), preventing hybrid language mixing.

---

### Phase 4: Project Kick-off Material (`1.1`) Defect Rectification

- **Slide 10 Native 3-Column Vector Architecture ([`src/ppt_engine/reference_slides.py`](../../src/ppt_engine/reference_slides.py)):**
  - Completely removed the static raster image embed (`snowflake_solution_architecture.png`).
  - Rebuilt `build_snowflake_data_pipeline_slide` with native OpenXML vector shapes:
    - 3 primary vertical container cards with sharp top stripes:
      1. `01. INGESTION & REPLICATION LAYER` (Kafka, Cloud Storage, REST APIs)
      2. `02. SNOWFLAKE CLOUD DATA WAREHOUSE` (Bronze Raw Vault, Silver dbt Transformations, Gold Star Schemas)
      3. `03. CONSUMPTION & GENAI SERVING` (Streamlit 8 Financial Modules, Cortex GenAI, Governed BI Direct Sync)
    - High-DPI official SVG tech logos resolved via `_resolve_logo_png`: `kafka.svg`, `snowflake.svg`, `dbt.svg`, `streamlit.svg`, `vault.svg`, `layout-dashboard.svg`, `sparkles.svg`, `shield-check.svg`.
    - Prominent bottom callout cards rendered in high-contrast orange (`#FFF7ED` fill, `#EA580C` border, `1.5pt` stroke) highlighting key architectural capabilities (Snowpipe streaming, elastic compute zero-scaling, Horizon RBAC).

- **Slide 12 Delivery Gantt Timeline Defect Rectification ([`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)):**
  - **Milestone Diamond Dynamic Label Flipping:** Fixed canvas bleed for Week 24 milestone. If `mx + diam_size + label_w > Inches(12.70)`, the label text box dynamically flips to the left of the diamond (`mx - label_w - Inches(0.06)`) with right alignment, guaranteeing $X < 13.333''$.
  - **Narrow Duration Bar Handling:** Prevented text overflow on 1–2 week bars by evaluating text width and adjusting label layout.
  - **Shadow Stripping:** Enforced `shape.shadow.inherit = False` across all timeline shapes, eliminating default drop shadows and ensuring flat vector geometry.
  - **Font Size Floor:** Upgraded timeline milestone tags, legends, and footnotes from $7.0\text{pt}$/$7.5\text{pt}$ to $\ge 11.0\text{pt}$.

- **Slide 19 Clean Corporate Closing Card ([`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)):**
  - Re-architected `build_thank_you_slide` to default to a clean corporate contact card (`contacts=None` / `show_staff_contacts=False`).
  - Renders Practice leadership branding and general inquiry alias (`enterprise.consulting@metrodata.co.id`) without exposing personal staff names unless explicitly requested.

---

### Phase 5: Automated Change Request Suite (`CR_07`)

- **Dynamic Client Routing ([`src/core/change_request.py`](../../src/core/change_request.py)):**
  - Updated `ChangeRequestProcessor.__init__` to accept `context: Optional[EngagementContext]`.
  - Configured output path resolution:
    ```python
    client_prefix = self.context.client_short_name if self.context else DEFAULT_CLIENT_SHORT_NAME
    out_p = Path("output") / f"{client_prefix}_Snowflake_Analytics" / "change_requests" / f"CR_{cr_id.zfill(2)}"
    ```
  - Standard CR generation now defaults cleanly to `output/NGL_Snowflake_Analytics/change_requests/CR_07/`.

- **Automated OpenXML & Workbook Sanitization ([`src/core/change_request.py`](../../src/core/change_request.py)):**
  - Implemented `_substitute_docx(doc, context)`: recursively scrubs legacy slug tokens and client entities across body paragraphs, tables, and nested table cells.
  - Implemented `_substitute_xlsx(wb, context)`: iterates all worksheets and cell values in openpyxl workbooks, substituting legacy tokens.
  - Bound sanitization into `process_cr()` across all four output deliverables:
    1. `Change_Request_Form_CR_07.docx`
    2. `Change_Log_Ledger_Updated_CR_07.xlsx`
    3. `CR_Scoping_and_Mandays_CR_07.xlsx`
    4. `BAST_Change_Request_Draft_CR_07.docx`

- **Verified Zero Legacy Logos:**
  - Audited `Change_Request_Form_CR_07.docx` and master template `clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.4_Change_Request_Form_Template.docx`.
  - Confirmed `<w:drawing>` and `image3.png` remain permanently removed from header XML (`word/header2.xml`).

---

## 3. Reconciled Architectural Topology & Document Ledger

| Component / Subsystem | Primary Path | Role & Changes Delivered |
| :--- | :--- | :--- |
| **Slug Registry & PII** | [`src/core/slug_registry.py`](../../src/core/slug_registry.py) | Canonical NGL defaults, regex normalizer, recursive slide shape scanner. |
| **CR Automation Suite** | [`src/core/change_request.py`](../../src/core/change_request.py) | Dynamic NGL output routing, `_substitute_docx`, `_substitute_xlsx`. |
| **Closing Deck Engine** | [`src/ppt_engine/closing_deck.py`](../../src/ppt_engine/closing_deck.py) | Lucide icons, 3-swimlane maintenance workflow, clean closing card. |
| **Weekly Deck Engine** | [`src/ppt_engine/weekly_progress_deck.py`](../../src/ppt_engine/weekly_progress_deck.py) | Slide 07 vertical centering, DrawingML hanging bullets, English baseline. |
| **Consulting Archetypes**| [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py) | Gantt diamond flip, shadow stripping, font floor $\ge 11\text{pt}$, clean closing. |
| **Pipeline Architecture**| [`src/ppt_engine/reference_slides.py`](../../src/ppt_engine/reference_slides.py) | Slide 10 native 3-column OpenXML vector architecture, SVG logos, orange callouts. |
| **Deck Configurations**  | [`presets/deck_configs/*.yaml`](../../presets/deck_configs/) | Complete YAML sanitization replacing legacy client strings with slug tokens. |

---

## 4. Verification & Static Assurance Summary

- **Static Analysis & Inspection:**
  - All modified Python source files compile cleanly with zero syntax or import errors.
  - Zero unit test suites were executed, strictly adhering to the repository guardrail in [`AGENTS.md`](../../AGENTS.md).
  - All relative links verified against the 4-tier documentation topology.

---

## 5. Immediate Next Backlog

1. **End-to-End Cross-Deliverable Orchestration:** Chaining Kick-off (`1.1`) $\rightarrow$ Specs (`FSD`/`TSD`) $\rightarrow$ S-Curves $\rightarrow$ UAT (`3.4`) $\rightarrow$ Weekly (`4.2`) $\rightarrow$ BAST $1/2$ $\rightarrow$ Closing Deck (`5.1`) under a unified `EngagementContext`.
2. **Operational Deployment Rundown & Technical Manuals:** Automate cutover checklist (`3.7_Rundown_Deployment_Template.xlsx`) and operational manuals (`3.6.1_User_Guide_Template.docx`, `3.6.2_Admin_Guide_Template.docx`).
