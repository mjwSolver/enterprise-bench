# Enterprise Workbench — PII Clearing & Downstream Sharing Backlog

> **Document:** `docs/backlog/PII_CLEARING_BACKLOG.md` | **Parent Roadmap:** [`FEATURE_BACKLOG.md`](../../FEATURE_BACKLOG.md)  
> **Target Release:** Clean Downstream Mirror to `AIML-DAI/enterprise-bench`  
> **Status:** Active Clearance Register & Remediation Roadmap  

---

## 1. Executive Summary & Audit Baseline

To enable secure internal sharing of the `enterprise-bench` engine with the `AIML-DAI` organization without exposing legacy customer engagements, client credentials, or historical commit graphs, a full-workspace static audit was performed across all 698 tracked repository files.

### 📊 Audit Summary by Directory Track
- **Track 1 (`src/` & `cli.py`):** 166 findings across 21 files (mostly vendor branding and hardcoded default PIC personas in slide builders).
- **Track 2 (`docs/` & `specs/`):** 135 findings across 43 files (contains **1 critical legacy client specification suite** and historical handover notes).
- **Track 3 (`presets/`, `templates/`, `scripts/`, `tests/`):** 239 findings across 21 files (sample staff rosters, preset deck configurations, and benign test blocklists).

---

## 2. Priority Heatmap & Action Areas

The audit isolated **5 primary focus areas** where remediation effort must be concentrated before publishing:

```text
[CRITICAL]  specs/tti_analytics/                 ➔ Legacy client TSD/UAT suite (Quarantined via downstream export exclude)
[HIGH]      src/core/slug_registry.py             ➔ Hardcoded default PIC personas & vendor identity
[RESOLVED]  presets/staff_roster.json             ➔ Scrubbed to generic synthetic roles & @enterprise-bench.local
[RESOLVED]  presets/deck_configs/                 ➔ Scrubbed vendor emails and client URLs to neutral placeholders
[MEDIUM]    docs/handovers/handover_archive/      ➔ Historical sprint notes (Quarantined via downstream export exclude)
[LOW]       src/core/pii/detectors.py & tests/    ➔ Benign detection regexes & test assertions
```

---

## 3. Deep-Dive: Specific Focus Areas & Remediation Notes

### 🚨 Hotspot 1: `specs/tti_analytics/` (Legacy Client Specification Suite)
- **Files Affected:**
  - `specs/tti_analytics/tsd/00_metadata.yaml`
  - `specs/tti_analytics/tsd/01_architecture_overview.md`
  - `specs/tti_analytics/tsd/02_snowflake_ddl_and_staging.md`
  - `specs/tti_analytics/tsd/03_dbt_transformation_models.md`
  - `specs/tti_analytics/tsd/04_rbac_and_security_matrix.md`
  - `specs/tti_analytics/tsd/05_performance_tuning.md`
  - `specs/tti_analytics/sit_uat/01_uat_test_execution_matrix.md`
- **Exposure Risk:** **CRITICAL**. The folder name itself references `TTI` (Toyota Tsusho Indonesia), and the files contain actual Snowflake DDL, dbt modeling transformations, RBAC matrices, and approval sign-off names.
- **Remediation Action:**
  - **Option A (Recommended for downstream):** Completely exclude `specs/tti_analytics/` from the downstream release export.
  - **Option B (If retaining as generic archetype):** Rename to `specs/sample_analytics/`, generalize database/schema names, and scrub sign-off tables to synthetic placeholders.

---

### ⚠️ Hotspot 2: Core Engine Default PIC Personas & Vendor Strings
- **Files Affected:**
  - `src/core/slug_registry.py` (Lines 55–97)
  - `src/ppt_engine/consulting_archetypes.py` (57 occurrences)
  - `src/ppt_engine/closing_deck.py` (20 occurrences)
  - `src/ppt_engine/reference_slides.py` (17 occurrences)
  - `src/ppt_engine/weekly_progress_deck.py` (12 occurrences)
- **Exposure Risk:** **HIGH**. The core engine defaults hardcode vendor identity (`PT Metrodata Electronics Tbk`, `Metrodata`, `MII`) and Indonesian consultant names (`Hendra Setiawan`, `Dewi Lestari`, `Agus Pramono`, `Bambang Wijaya`, `Agustino`, `Budi Pratama`, `Fajar Nugraha`) into mock presentation cards and table generators.
- **Remediation Action:**
  - Decouple vendor and personal names from python source code.
  - Set default fallback values in `src/core/slug_registry.py` to neutral placeholders (e.g. `Client Company Inc.`, `Advisory Partner Ltd.`, `Lead Consultant`).
  - Slide builders should read dynamic context from `EngagementContext` rather than hardcoding vendor/person strings.

---

### ✅ Hotspot 3: Presets, Staff Rosters & Deck Configurations [REMEDIATED]
- **Files Remediated:**
  - `presets/staff_roster.json`: All 8 consultant profiles updated to generic synthetic roles (`Project Manager A`, `Solutions Architect A`, `Data Engineer 1`, etc.) and emails scrubbed to `@enterprise-bench.local`.
  - `presets/deck_configs/closing_deck.yaml`: Scrubbed vendor emails (`@metrodata.co.id`) to synthetic personas.
  - `presets/deck_configs/uat_briefing.yaml`: Scrubbed contact emails (`@mii.co.id`) to `@enterprise-bench.local`.
  - `presets/deck_configs/presales_pitch_deck.yaml`: Scrubbed contact block emails, vendor legal notices, and client hostnames (`tsusho.local` -> `enterprise-bench.local`).
- **Remediation Status:** Complete. Zero client domains or real consultant emails remain in `presets/`.

---

### ℹ️ Hotspot 4: Historical Handover Briefings (`docs/handovers/`)
- **Files Affected:**
  - `docs/handovers/handover_archive/2026-09-16_slide3_corporate_equity_tree.md`
  - `docs/handovers/handover_archive/2026-09-21_sprints_17_27_completion_briefing.md`
  - `docs/handovers/handover_archive/2026-09-23_feedback_and_quality_enhancement_sprint.md`
- **Exposure Risk:** **MEDIUM**. These archived sprint logs detail previous sanitization milestones, equity tree corporate nodes, and client project references.
- **Remediation Action:**
  - Exclude `docs/handovers/handover_archive/` from the downstream repository export. Org members only need active architectural specs (`docs/specs/`) and standard user guides.

---

### 🛡️ Hotspot 5: Benign Security Rules & Test Blocklists (No Action Needed)
- **Files Affected:**
  - `src/core/slug_registry.py` (`DEFAULT_FORBIDDEN_PATTERNS`)
  - `src/core/pii/detectors.py` (PII pattern matchers)
  - `tests/test_pii_engine.py` (Test assertions verifying detection)
- **Exposure Risk:** **NONE (INTENTIONAL CODE)**. These strings exist purely as linter rules to detect and reject forbidden entities.
- **Remediation Action:** Retain intact. Ensure comments clarify that these are detection patterns, not active data.

---

## 4. Comprehensive Inventory of Real Customer Files & Binary Assets (Review Register)

> **Scoping Status:** Work Requirements Scoped • Review & Remediation Pending  
> **Purpose:** Explicitly catalogs every binary office container (`.docx`, `.pptx`, `.xlsx`, `.mpp`, `.drawio`), image asset, and real engagement document across workspaces to map all files requiring inspection prior to clearance.

### 📁 Track A: Legacy Client Binary Intake (`raw_source_files/projects/TTI_Snowflake_Analytics/` — 38 files)
*Primary legacy customer engagement source files (Toyota Tsusho Indonesia). Must be excluded or quarantined.*

| Phase / Workstream | Relative File Path | Format | Nature of File & Real Exposure Risk | Review Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Presales** | `raw_source_files/projects/TTI_Snowflake_Analytics/01_presales/Account_POC_Scope_Template.docx` | `.docx` | POC scope agreement with real customer requirements | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/01_presales/Cloud_Sizing_Calculator_Template.xlsx` | `.xlsx` | Infrastructure sizing models with real warehouse compute metrics | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx` | `.pptx` | 36-slide presales proposal containing corporate logos and team bios | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/01_presales/Timeline_and_Mandays_Estimate_Template.xlsx` | `.xlsx` | Commercial pricing workbook with billable mandays and rates | Quarantined / Exclude |
| **Initiating** | `raw_source_files/projects/TTI_Snowflake_Analytics/02_initiating/1.1_Kick-off_Material_Template.pptx` | `.pptx` | 19-slide kick-off presentation with client/partner organization charts | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/02_initiating/1.2_Project_Charter_Template.docx` | `.docx` | Signed project charter, objective statements, and governance roles | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/02_initiating/1.3_Stakeholders_Register_Template.xlsx` | `.xlsx` | Real client employee registry (emails, phone numbers, department titles) | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/02_initiating/1.4.1_Project_Timeline_Baseline_Template.xlsx` | `.xlsx` | Project timeline and deliverable milestone schedules | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/02_initiating/1.4_Project_Timeline_Baseline_Template.mpp` | `.mpp` | Microsoft Project native schedule binary | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/02_initiating/Project_Org_Structure_Template.pptx` | `.pptx` | Joint project governance organogram with named personnel | Quarantined / Exclude |
| **Planning** | `raw_source_files/projects/TTI_Snowflake_Analytics/03_planning/2.1_Project_Management_Plan_Template.docx` | `.docx` | Detailed project management execution plan and escalations | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/03_planning/2.3_Functional_Specification_Document_FSD_Template.docx` | `.docx` | Functional specifications describing real client business entities | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/03_planning/FSD_Architecture_Diagrams_Template.drawio` | `.drawio` | Multi-page Draw.io architectural models with network topology | Quarantined / Exclude |
| **Executing** | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.1_Technical_Specification_Document_TSD_Template.docx` | `.docx` | Full technical specification with production Snowflake schema names | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.3.1_SIT_Scenario_Backend_Template.docx` | `.docx` | System integration test cases for data ingestion pipelines | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.3.2_SIT_Scenario_Frontend_Template.docx` | `.docx` | System integration test cases for BI dashboards | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.4_Sosialisasi_UAT_Briefing_Template.pptx` | `.pptx` | 25-slide user acceptance briefing deck with business workflows | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.4_Timeline_UAT_Template.xlsx` | `.xlsx` | UAT test execution calendar and user availability matrix | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.4_UAT_Scenario_Template.docx` | `.docx` | Business user acceptance testing scenarios and approval forms | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.6.1_User_Guide_Template.docx` | `.docx` | End-user manual with application screenshots and logins | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.6.2_Admin_Guide_Template.docx` | `.docx` | System administrator operations and security manual | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.6_Defect_List_Template.xlsx` | `.xlsx` | SIT/UAT defect tracking log with tester names | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/04_executing/3.7_Rundown_Deployment_Template.xlsx` | `.xlsx` | Production cutover rundown with timed engineer actions | Quarantined / Exclude |
| **Monitoring** | `raw_source_files/projects/TTI_Snowflake_Analytics/05_monitoring/4.1_MoM_Minutes_of_Meeting_Template.docx` | `.docx` | Minutes of kickoff meeting with attendee sign-in roster | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Report_Deck_Template.pptx` | `.pptx` | Weekly progress slide deck template | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Timeline_Update_Template.xlsx` | `.xlsx` | Weekly progress timeline and EVM S-curve data | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/05_monitoring/4.4_Change_Log_Ledger_Template.xlsx` | `.xlsx` | Scope change request register and approval dates | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/05_monitoring/4.4_Change_Request_Form_Template.docx` | `.docx` | Official change request template with sign-off blocks | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/05_monitoring/4.5_Risk_Register_Template.xlsx` | `.xlsx` | Project risk register and risk owner assignments | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/05_monitoring/4.6_Issue_Log_Template.xlsx` | `.xlsx` | Production issue and blocker resolution log | Quarantined / Exclude |
| **Closing** | `raw_source_files/projects/TTI_Snowflake_Analytics/06_closing/5.1_Project_Closing_Deck_Template.pptx` | `.pptx` | 9-slide formal engagement closure and warranty deck | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/06_closing/5.2_Project_Closeout_Checklist_Template.xlsx` | `.xlsx` | Closeout acceptance criteria and handover checklist | Quarantined / Exclude |
| **Contracts** | `raw_source_files/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/BAST_Change_Request_Template.docx` | `.docx` | Legal handover certificate (BAST) for change requests | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/BAST_Milestone_1_Template.docx` | `.docx` | Milestone 1 legal acceptance certificate with signatory names | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/BAST_Milestone_2_Final_Template.docx` | `.docx` | Final acceptance legal certificate with signatory names | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/CR_Scoping_and_Mandays_Template.xlsx` | `.xlsx` | Change request commercial scoping and mandays calculator | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/Perjanjian_Kerjasama_PKS_Template.docx` | `.docx` | Master Services Agreement (PKS) legal contract with corporate entities | Quarantined / Exclude |
| | `raw_source_files/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/Resource_Leave_Schedule_Template.xlsx` | `.xlsx` | Named consultant leave calendar and resource planning | Quarantined / Exclude |

---

### 📁 Track B: Academic & ESG Case Study Source Files (`raw_source_files/projects/KRA_ESG_Research/` & `work_archive/`)
*Real academic research decks and presentation redesign assets.*

| Location | Relative File Path | Format | Nature of File & Real Exposure Risk | Review Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `raw_source_files/` | `raw_source_files/projects/KRA_ESG_Research/presentations/KRA_1 Sept2026.pptx` | `.pptx` | Real academic research deck (Faculty of Economics & Business, Unair) | Quarantined / Exclude |
| `raw_source_files/` | `raw_source_files/projects/KRA_ESG_Research/presentations/KRA_1_Sept2026_Modern_Consulting.pptx` | `.pptx` | Redesigned consulting deck variant | Quarantined / Exclude |
| `raw_source_files/` | `raw_source_files/projects/KRA_ESG_Research/presentations/generate_redesigned_deck.py` | `.py` | Generation script for academic redesign deck | Quarantined / Exclude |
| `raw_source_files/` | `raw_source_files/projects/KRA_ESG_Research/presentations/montage.png` | `.png` | Visual raster montage of academic presentation slides | Quarantined / Exclude |
| `work_archive/` | `work_archive/KRA_1 Sept2026.pptx` | `.pptx` | Working copy of academic research deck | Exclude from mirror |
| `work_archive/` | `work_archive/KRA_1_Sept2026_Modern_Consulting.pptx` | `.pptx` | Working copy of modernized presentation | Exclude from mirror |
| `work_archive/` | `work_archive/KRA_1_Sept2026_modern_consulting/assets/unair_logo.png` | `.png` | Real university emblem asset (Universitas Airlangga) | Exclude from mirror |
| `work_archive/` | `work_archive/KRA_1 Sept2026/slide-[1..21].png` | `.png` | 21 raster slide screenshots containing research text/charts | Exclude from mirror |
| `work_archive/` | `work_archive/rendered_slides/rendered_slides.[001..015].png` | `.png` | 15 rendered review slides of academic presentation | Exclude from mirror |
| `work_archive/` | `work_archive/extracted_assets/slide_13_shape_*.png`, `slide_15_shape_*.png` | `.png` | Extracted raster figure graphics | Exclude from mirror |

---

### 📁 Track C: Bank Sinarmas Live Client Intake (`BSIM_Migration/doc_files/` & root)
*Live migration workbooks, timelines, and Jira backlog extracts from active engagement.*

| Location | Relative File Path | Format | Nature of File & Real Exposure Risk | Review Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `BSIM_Migration/` | `doc_files/BSIM - Proposed Timeline V02.xlsx` | `.xlsx` | Live Bank Sinarmas project timeline and cutover schedule | Customer Live / Keep in Workspace Only |
| `BSIM_Migration/` | `doc_files/BSIM_Cloudera_Data_Platform_Modernization_Proposed_Timeline.xlsx` | `.xlsx` | Cloudera CDP to Databricks migration master timeline | Customer Live / Keep in Workspace Only |
| `BSIM_Migration/` | `doc_files/BSIM_Presentation.pptx` | `.pptx` | Original Bank Sinarmas modernization presentation deck | Customer Live / Keep in Workspace Only |
| `BSIM_Migration/` | `BSIM JIRA Cleaned.csv` | `.csv` | Jira extract with 54+ Workstream 4 workload tasks and statuses | Customer Live / Keep in Workspace Only |

---

### 📁 Track D: Cleaned Intake Mirror Workspace (`clean_workspace/`)
*Mirrored project directories containing staged PII-substituted templates and verification manifests.*

| Subdirectory | Relative Path | Format | Scope & Contents | Review Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `clean_workspace/` | `clean_workspace/catalog_data.json` | `.json` | Metadata catalog mapping project deliverables | Review for residual entity names |
| `clean_workspace/` | `clean_workspace/sanitization_manifest.json` | `.json` | Cryptographic audit log of performed PII token replacements | Review / Safe to retain or exclude |
| `clean_workspace/` | `clean_workspace/projects/TTI_Snowflake_Analytics/` | Multiple | 38 mirrored documents with `sanitization_manifest.json` & `team.json` | Review PII token effectiveness |
| `clean_workspace/` | `clean_workspace/projects/KRA_ESG_Research/` | Multiple | 4 mirrored files with `sanitization_manifest.json` & `team.json` | Review / Exclude from mirror |

---

### 📁 Track E: Generated Client Deliverables & Modernized Presentations (`output/` & `doc_output/`)
*Compiled artifacts, client project outputs, and modernized slide decks.*

| Output Group | Relative Path / Subdirectory | Formats | Notable Deliverables & Scope | Review Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Client Outputs** | `output/TTI_Snowflake_Analytics/change_requests/CR_07/` | `.docx`, `.xlsx` | BAST Draft, CR Scoping, Change Log, Change Request Form (4 files) | Exclude from mirror |
| | `output/NGL_Snowflake_Analytics/change_requests/CR_07/` | `.docx`, `.xlsx` | Sanitized demonstration CR suite (4 files) | Review synthetic compliance |
| | `output/proj-xyz/` | `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.png` | 33 mock project files across `documents/`, `presentations/`, `spreadsheets/` | Review mock consistency |
| | `output/AcmeDigital/` | Multiple | Synthetic test deliverables | Safe (synthetic) |
| **Modernized Decks** | `output/presentations/1.1_Project_Kick-off_Material_Modernized.pptx` | `.pptx` | 19-slide kick-off presentation with canonical synthetic personas | Inspect Slide 6 team roster |
| | `output/presentations/3.4_Sosialisasi_UAT_Briefing_Modernized.pptx` | `.pptx` | 25-slide UAT briefing deck | Inspect test scenario text |
| | `output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized.pptx` | `.pptx` | 11-slide weekly report with middle-anchored milestones | Inspect status text |
| | `output/presentations/5.1_Project_Closing_Deck_Modernized.pptx` | `.pptx` | 9-slide closing deck with maintenance workflow & contact cards | Inspect contact personas |
| | `output/presentations/Modernize_Data_Platform_Pitch_Deck_Modernized.pptx` | `.pptx` | 36-slide executive presales deck | Inspect case study logos |
| | `output/presentations/architecture_evolution_cdsw_to_lambda.pptx` | `.pptx` | Master 8-slide architecture deck (Bank Sinarmas context) | Keep in project workspace |
| | `output/presentations/cdsw_whitelist_system_design_expanded_visualization.pptx` | `.pptx` | 2-slide safe-checker & Lambda serverless deck | Keep in project workspace |
| **Root Stamped Docs** | `output/PKS_stamped.docx`, `Charter_stamped.docx`, `TSD_Snowflake_Analytics.docx` | `.docx` | Stamped legal and technical specifications (6 files) | Verify synthetic placeholders |
| | `output/BAST_M1_stamped.docx`, `MoM_stamped.docx`, `UAT_Scenario_Matrix.docx` | `.docx` | Stamped acceptance and testing forms | Verify synthetic placeholders |
| | `output/calculated_Cloud_Sizing_Calculator_Template.xlsx` | `.xlsx` | Sizing calculation model output | Verify synthetic placeholders |
| | `output/ngl_*.xlsx` & `output/stamped_*.docx` | Multiple | Stamped NGL demonstration files | Verify synthetic placeholders |

---

### 📁 Track F: Plaintext Technical Specifications & Hardcoded Schemas (`specs/tti_analytics/` & `presets/`)
*Structured plaintext files containing real client database architectures, dbt transformations, and staff configurations.*

| File / Component | Relative Path | Format | Findings & Real Content Risk | Review Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Metadata Spec** | `specs/tti_analytics/tsd/00_metadata.yaml` | `.yaml` | Client metadata, engagement acronyms (`TTI`), version tags | Exclude or re-synthesize |
| **Architecture Spec** | `specs/tti_analytics/tsd/01_architecture_overview.md` | `.md` | Architectural text detailing real client source databases | Exclude or re-synthesize |
| **Snowflake DDL** | `specs/tti_analytics/tsd/02_snowflake_ddl_and_staging.md` | `.md` | Real client table definitions, column types, and stage names | Exclude or re-synthesize |
| **dbt Models** | `specs/tti_analytics/tsd/03_dbt_transformation_models.md` | `.md` | Real business transformation SQL models and metric logic | Exclude or re-synthesize |
| **RBAC Matrix** | `specs/tti_analytics/tsd/04_rbac_and_security_matrix.md` | `.md` | Real security roles, functional roles, and permission hierarchies | Exclude or re-synthesize |
| **Tuning Spec** | `specs/tti_analytics/tsd/05_performance_tuning.md` | `.md` | Clustering keys, warehouse sizing, and execution targets | Exclude or re-synthesize |
| **UAT Matrix** | `specs/tti_analytics/sit_uat/01_uat_test_execution_matrix.md` | `.md` | Real test case descriptions, expected results, sign-offs | Exclude or re-synthesize |
| **Staff Roster** | `presets/staff_roster.json` | `.json` | Generic synthetic roles & `@enterprise-bench.local` domains | ✅ Remediated |
| **Deck Configs** | `presets/deck_configs/*.yaml` | `.yaml` | Neutralized vendor emails and client URLs | ✅ Remediated |

---

## 5. Downstream Export & Release Gate

When ready to publish to `AIML-DAI/enterprise-bench`, run the verified automated clean-slate export script:

```bash
# 1. Execute automated export script with post-export verification gate
# Dry-run preview:
./scripts/export_downstream_mirror.sh /tmp/enterprise-bench-clean true

# Live export & gate execution:
./scripts/export_downstream_mirror.sh /tmp/enterprise-bench-clean false

# 2. Or execute via rsync directly:
rsync -av --stats \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='output' \
  --exclude='doc_output' \
  --exclude='clean_workspace' \
  --exclude='raw_source_files' \
  --exclude='work_archive' \
  --exclude='specs/tti_analytics' \
  --exclude='docs/handovers/handover_archive' \
  --exclude='scratch' \
  --exclude='*.local.json' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='.pytest_cache' \
  --exclude='.ruff_cache' \
  /Users/marcelljw/VisualStudioCode/enterprise-bench/ \
  /tmp/enterprise-bench-clean/

# 3. Post-export static verification gate (enforced in script)
grep -rnEI "toyota|tsusho|\btti\b|ttlc" /tmp/enterprise-bench-clean/specs/

# 3. Initialize fresh 1-commit downstream repository
cd /tmp/enterprise-bench-clean
git init -b main
git add .
git commit -m "feat(core): initial release of enterprise workbench platform v1.0"
git remote add origin https://github.com/AIML-DAI/enterprise-bench.git
git push -u origin main
```

