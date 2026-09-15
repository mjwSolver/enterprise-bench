# AGENT HANDOVER & ARCHITECTURE BRIEFING

> **Target Repository:** `enterprise-bench`  
> **Author / Origin:** Handover from Enterprise Delivery Project (`tti-streamlit-prototype-internal-only`)  
> **Primary Goal:** Universal, multi-engine automation workbench for enterprise consulting deliverables, presentations, specifications, and contractual documents.

---

## 1. Executive Context & Vision

This repository (`enterprise-bench`) is the consolidated, centralized home for enterprise document and presentation generation. It unifies what was previously fragmented across:

1. **`PPTMaking` (`/Users/marcelljw/VisualStudioCode/PPTMaking`):**  
   A mature, generative consulting presentation engine that builds slides programmatically using `python-pptx`, custom visual archetypes, diagramming chevrons, and collision detection.
2. **`DOCXMaking` (Greenfield):**  
   A deterministic document generation engine designed to stamp out legal contracts (PKS), handover certificates (BAST), functional specs (FSD), technical specs (TSD), and meeting minutes (MoM).
3. **The Real-World Seeded Templates (`clean_workspace/projects/TTI_Snowflake_Analytics/`):**  
   **38 sanitized, real-world enterprise template archetypes** extracted directly from a major enterprise client delivery project, cataloged and stored in `clean_workspace/` as the ground-truth benchmark.

---

## 2. Core Architectural Principles

### A. The Two Opposing Paradigms (Separated by Design)
* **The Creative Engine (`src/ppt_engine`):**  
  Generative, dynamic layouting, custom consulting visual cards, process flow diagrams, and collision detection. Used when every deck requires unique visual storytelling.
* **The Compliance Engine (`src/docx_engine`):**  
  Deterministic, 100% compliant, zero-drift templating. Enterprise BAST, PKS contracts, and Weekly Status reports must look identical week over week for legal and audit compliance. Uses `docxtpl` / Jinja2 / OpenXML variable stamping.
* **The Bridge:**  
  When `docx_engine` needs an architecture diagram or process chevron for an FSD/TSD, it directly imports and invokes `src.ppt_engine.diagram_engine`, renders the asset, and embeds it into the document. Zero IPC overhead.

---

## 3. Dependency Management Philosophy (`uv`)

Dependencies are strictly tiered in `pyproject.toml` so users can install only what they need without bloat:

```text
┌─────────────────────────────────────────────────────────────┐
│              CORE NON-NEGOTIABLE DEPENDENCIES               │
│   pydantic, jinja2, rich, typer, python-dotenv, pillow      │
│                (Shared across all engines)                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
 ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
 │  Extra: [ppt] │     │ Extra: [docx] │     │ Extra: [xlsx] │
 │  python-pptx  │     │  python-docx  │     │   openpyxl    │
 │  matplotlib   │     │    docxtpl    │     │    pandas     │
 │     numpy     │     │               │     │               │
 └───────────────┘     └───────────────┘     └───────────────┘
```

### Installation Commands:
```bash
# Core only
uv sync

# If working on presentations:
uv sync --extra ppt

# If working on documents & contracts:
uv sync --extra docx

# If working on spreadsheets & calculators:
uv sync --extra xlsx

# Install the entire enterprise suite:
uv sync --all-extras
```

---

## 4. Master Directory Structure

```text
enterprise-bench/
├── pyproject.toml              # Tiered dependency manifest
├── README.md                   # Quickstart guide
├── HANDOVER.md                 # This briefing document
├── cli.py                      # Unified CLI entrypoint (`bench doc ...`, `bench ppt ...`)
│
├── clean_workspace/            # Canonical Sanitized Workspace & Catalog
│   ├── catalog_data.json
│   ├── sanitization_manifest.json
│   └── projects/TTI_Snowflake_Analytics/ # 38 Golden Master Templates (Sanitized)
│       ├── 01_presales/        (Cloud calculators, pitch decks, POC scopes, manday estimates)
│       ├── 02_initiating/      (Kick-off deck, project charter, stakeholder register, timeline MPP)
│       ├── 03_planning/        (PMP, FSD module specs, Draw.io architecture diagrams)
│       ├── 04_executing/       (TSD, SIT/UAT scenarios, Defect tracker, User/Admin guides, Cutover)
│       ├── 05_monitoring/      (MoM minutes, Weekly status deck, Weekly progress sheet, Change logs, RAID)
│       ├── 06_closing/         (Closing presentation deck, Project closeout checklist)
│       └── 07_internal_legal_contracts/ (PKS contract, BAST Milestone 1/2/CR, Mandays & Leave logs)
│
├── src/
│   ├── core/                   # Shared foundations
│   │   ├── config.py           (Environment & workspace paths)
│   │   ├── theme.py            (Corporate color palettes, typography tokens)
│   │   ├── sanitizer.py        (PII stripping & generic variable replacer)
│   │   ├── docx_purger.py      (Zero-corruption OpenXML comment, highlight & revision purger)
│   │   └── models.py           (Pydantic schemas for Project, Milestone, Deliverable)
│   │
│   ├── ppt_engine/             # Migrated from PPTMaking/src
│   │   ├── consulting_archetypes.py
│   │   ├── diagram_engine.py
│   │   ├── theme_engine.py
│   │   ├── slide_validator.py
│   │   └── slide_exporter.py
│   │
│   ├── docx_engine/            # Deterministic document engine
│   │   ├── template_stamper.py (Jinja2 / docxtpl stamping)
│   │   ├── table_engine.py     (OpenXML cell shading, borders, widths)
│   │   └── document_linter.py  (Pagination checks, orphan heading linter)
│   │
│   └── xlsx_engine/            # Spreadsheet & financial calculators
│       ├── calculator_stamper.py
│       └── s_curve_generator.py
│
└── output/                     # Generated deliverables (gitignored)
```

---

## 5. Seeded Template Catalog (`clean_workspace/projects/TTI_Snowflake_Analytics/`)

All 38 files have been relocated and sanitized under `clean_workspace/projects/TTI_Snowflake_Analytics/` from the source client delivery project:

1. **`01_Presales/`**:
   - `Cloud_Sizing_Calculator_Template.xlsx`
   - `Modernize_Data_Platform_Pitch_Deck_Template.pptx`
   - `Account_POC_Scope_Template.docx`
   - `Timeline_and_Mandays_Estimate_Template.xlsx`
2. **`02_Initiating/`**:
   - `1.1_Kick-off_Material_Template.pptx`
   - `1.2_Project_Charter_Template.docx`
   - `1.3_Stakeholders_Register_Template.xlsx`
   - `1.4_Project_Timeline_Baseline_Template.mpp`
   - `1.4.1_Project_Timeline_Baseline_Template.xlsx`
   - `Project_Org_Structure_Template.pptx`
3. **`03_Planning/`**:
   - `2.1_Project_Management_Plan_Template.docx`
   - `2.3_Functional_Specification_Document_FSD_Template.docx`
   - `FSD_Architecture_Diagrams_Template.drawio`
4. **`04_Executing/`**:
   - `3.1_Technical_Specification_Document_TSD_Template.docx`
   - `3.3.1_SIT_Scenario_Backend_Template.docx`
   - `3.3.2_SIT_Scenario_Frontend_Template.docx`
   - `3.4_Sosialisasi_UAT_Briefing_Template.pptx`
   - `3.4_Timeline_UAT_Template.xlsx`
   - `3.4_UAT_Scenario_Template.docx`
   - `3.6_Defect_List_Template.xlsx`
   - `3.6.1_User_Guide_Template.docx`
   - `3.6.2_Admin_Guide_Template.docx`
   - `3.7_Rundown_Deployment_Template.xlsx`
5. **`05_Monitoring/`**:
   - `4.1_MoM_Minutes_of_Meeting_Template.docx`
   - `4.2_Weekly_Progress_Report_Deck_Template.pptx`
   - `4.2_Weekly_Progress_Timeline_Update_Template.xlsx`
   - `4.4_Change_Request_Form_Template.docx`
   - `4.4_Change_Log_Ledger_Template.xlsx`
   - `4.5_Risk_Register_Template.xlsx`
   - `4.6_Issue_Log_Template.xlsx`
6. **`06_Closing/`**:
   - `5.1_Project_Closing_Deck_Template.pptx`
   - `5.2_Project_Closeout_Checklist_Template.xlsx`
7. **`07_Internal_Legal_Contracts/`**:
   - `Perjanjian_Kerjasama_PKS_Template.docx`
   - `BAST_Milestone_1_Template.docx`
   - `BAST_Milestone_2_Final_Template.docx`
   - `BAST_Change_Request_Template.docx`
   - `CR_Scoping_and_Mandays_Template.xlsx`
   - `Resource_Leave_Schedule_Template.xlsx`

---

---

## 6. Milestones & Progress Tracker

### Completed Milestones (2026-09-11)
- [x] **1. Migrate `PPTMaking` into `src/ppt_engine/`:**
  - Consolidated presentation logic into [`src/ppt_engine/`](src/ppt_engine/).
  - Migrated brand themes to [`presets/themes/`](presets/themes/) and icons to [`assets/icons/`](assets/icons/).
  - Refactored internal imports to `src.ppt_engine.*` and centralized path handling.
- [x] **2. Build `src/core/` Foundations:**
  - Implemented [`src/core/config.py`](src/core/config.py) for workspace path resolution.
  - Implemented [`src/core/models.py`](src/core/models.py) with Pydantic v2 contracts (`ProjectInfo`, `BASTPayload`, `MoMPayload`, `Stakeholder`).
  - Implemented [`src/core/theme.py`](src/core/theme.py) for unified brand tokens.
  - Implemented [`src/core/sanitizer.py`](src/core/sanitizer.py) for PII regex scrubbing.
- [x] **3. Build `src/docx_engine/` Compliance Engine:**
  - Implemented [`src/docx_engine/template_stamper.py`](src/docx_engine/template_stamper.py) with Jinja2 / `docxtpl` and on-the-fly Mermaid diagram compilation.
  - Implemented [`src/docx_engine/table_engine.py`](src/docx_engine/table_engine.py) for OpenXML table shading and row repeat protection.
  - Implemented [`src/docx_engine/document_linter.py`](src/docx_engine/document_linter.py) for automated structural and unrendered tag verification.
- [x] **4. Implement Unified CLI (`src/cli.py` / `bench`):**
  - Exposed Typer CLI with `bench init-project`, `bench ppt generate`, `bench ppt themes`, `bench doc stamp`, `bench doc sanitize`, and `bench doc lint`.
- [x] **5. Test Suite:**
  - Implemented [`tests/test_core.py`](tests/test_core.py), [`tests/test_docx_engine.py`](tests/test_docx_engine.py), and [`tests/test_ppt_engine.py`](tests/test_ppt_engine.py) (9/9 passed).
- [x] **6. Desktop Native App Preview Subsystem (`skills/local-app-preview/`):**
  - Implemented macOS `open` + AppleScript (`osascript`) workflow to launch and auto-focus Word, Excel, PowerPoint, and Preview.
  - Documented protocol in [`AGENTS.md`](AGENTS.md) and [`skills/local-app-preview/SKILL.md`](skills/local-app-preview/SKILL.md).
- [x] **7. Zero-Corruption OpenXML Purging Subsystem (`src/core/docx_purger.py`):**
  - Engineered zero-corruption comment, highlight, tracked revision, and author profile purging for `.docx`.
  - Integrated into `src/core/sanitizer.py` and exposed via `uv run bench doc purge`.
  - Audited all output deliverables and golden master templates (0 comments, 0 highlights, 0 revisions).
  - Authored comprehensive architectural runbook in [`docs/OPENXML_PURGING_AND_CLEANSING.md`](docs/OPENXML_PURGING_AND_CLEANSING.md).
- [x] **8. Slide Geometry Containment, Diagram 3-Column Re-Architecture & Ingress Bus Specification (2026-09-15):**
  - **Slide Geometry & Footer Guardrail:** Eliminated single-dimension unbounded image scaling in `python-pptx` that allowed squarish ($1.22:1$) diagrams to blow past container boundaries and hit $7.49"$ on $7.50"$ slides. Implemented `fit_image_within_bounds()` dual-constraint containment across `scripts/generate_xyz_decks.py` and `scripts/generate_xyz_enhanced_visual_deck.py`.
  - **Draw.io Whitespace Elimination:** Re-engineered `01_ingestion_streaming` from an asymmetrical hybrid ($>450,000\text{ px}^2$ dead whitespace in bottom-right) to a balanced 3-column architecture (`flowchart LR`, $2.77:1$ widescreen aspect ratio) with integrated vector tech logos (Kafka, Snowflake, AWS, S3, Lucide).
  - **Live Presentation Concurrency:** Established clean macOS AppleScript lock handling to close active PowerPoint presentations without saving prompts, re-generate decks, and auto-focus Slide 4.
  - **Ingress Bus Architecture Handover:** Formulated formal architectural design and specification for edge bundling / trunk-line routing in [`docs/HANDOVER_INGRESS_BUS_ROUTING.md`](docs/HANDOVER_INGRESS_BUS_ROUTING.md) to eliminate orthogonal connector clutter ("mess of cables").

---

## 7. OpenXML Sanitization & Document Cleansing Architecture

> Full technical guide: [`docs/OPENXML_PURGING_AND_CLEANSING.md`](docs/OPENXML_PURGING_AND_CLEANSING.md)

### The Two Major OpenXML Traps Solved
1. **The `[Content_Types].xml` & `.rels` Namespace Corruption Trap:**
   - Standard Python parsers (`xml.etree.ElementTree`) serialize root elements with synthetic prefixes (e.g. `<ns0:Types>`, `<ns0:Relationships>`). Microsoft Word requires these root tags to use the default namespace without prefixes; any prefix immediately corrupts the package.
   - **Solution:** **Never touch package files.** Leave `[Content_Types].xml` and `word/_rels/document.xml.rels` intact. Empty the children of `word/comments*.xml` and `word/people.xml` while preserving their root XML containers.
2. **The "Ghost Comments" vs Tracked Revisions Confusion:**
   - Word's "All Markup" view renders Tracked Changes (`<w:ins>`, `<w:del>`, `<w:rPrChange>`, `<w:pPrChange>`) in right-hand margin balloons that look identical to comments.
   - **Solution:**
     - Drop all deletions (`etree.strip_elements(root, f"{{{W_NS}}}del", with_tail=False)`).
     - Accept all insertions (`etree.strip_tags(root, f"{{{W_NS}}}ins")` keeping run text intact).
     - Strip change markers (`rPrChange`, `pPrChange`, `tblPrChange`, etc.).
     - Empty `word/people.xml` author profile cards.
     - Disable `<w:trackRevisions>` in `word/settings.xml`.

### CLI Usage:
```bash
# Purge single document
uv run bench doc purge --file path/to/document.docx

# Batch purge directory
uv run bench doc purge --dir clean_workspace/projects/TTI_Snowflake_Analytics
```

---

## 8. Immediate Next Backlog for the Next Sprint
1. **Presentation Imagery Archetypes & Company Logo Formatting:**
   - Detailed specifications captured in [`docs/BACKLOG_SLIDE_DESIGN_VARIETY.md`](docs/BACKLOG_SLIDE_DESIGN_VARIETY.md) (Section 5).
   - Standardize template-level image placeholder zones across archetypes (Hero Cover, Split-Screen Case Study 1/2 photo + 1/2 text, Side-by-Side Proof card, Team Bio Grid).
   - Implement dual client/vendor logo lockups on cover slides and header/footer banners (`client_logo_path`, `vendor_logo_path`) with transparent aspect-ratio constrained rendering.
   - Declarative data models in `consulting_archetypes.py` (`SlideImageReference`, `BrandingConfig`).
2. **Spreadsheet Engine (`src/xlsx_engine/`):**
   - Implement `calculator_stamper.py` to drive `Cloud_Sizing_Calculator_Template.xlsx` and `Timeline_and_Mandays_Estimate_Template.xlsx`.
   - Implement `s_curve_generator.py` for automated project progress curves.
3. **Batch Template Sanitization:**
   - Completed batch regex sanitization across all 38 templates, cataloged in [`clean_workspace/projects/TTI_Snowflake_Analytics/`](clean_workspace/projects/TTI_Snowflake_Analytics/).


