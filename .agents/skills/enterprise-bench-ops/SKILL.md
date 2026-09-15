---
name: enterprise-bench-ops
description: >-
  Operational runbook for generating, stamping, and assembling enterprise consulting deliverables, decks, contracts, and spreadsheets using the unified CLI (`uv run bench ...`). Use when tasked with producing client artifacts, running CLI generator commands, validating stage-gate compliance, or filling document payloads.
---

# Enterprise Workbench: Operational Runbook (`enterprise-bench-ops`)

> **Target Agent Role:** Deliverable Producer / Engagement PMO / Solutions Consultant  
> **Mission:** Assemble, stamp, and validate professional client deliverables using existing benchmark templates and CLI automation tools without modifying the underlying engine codebase.

---

## 1. The Deliverable Production Decision Matrix

Whenever an operational task arrives to produce or update a project artifact:

```
                  ┌──────────────────────────────────────────────┐
                  │ 1. CHECK STAGE-GATE PREREQUISITES            │
                  │    Consult LIFECYCLE.md (Stages 0 to 6)      │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 2. IDENTIFY MASTER BENCHMARK TEMPLATE        │
                  │    Consult CATALOG.md (in clean_workspace/)  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 3. SELECT OPERATIONAL CLI GENERATION COMMAND │
                  └───────┬──────────────┬───────────────┬───────┘
                          │              │               │
                          ▼              ▼               ▼
                 [DETERMINISTIC DOCS] [CONSULTING DECKS] [SPREADSHEETS]
                 • BAST / PKS / MoM   • Pitch & Kick-off • Cloud Sizing
                 • FSD / TSD Specs    • Weekly Progress  • Mandays & Timelines
                 • SIT / UAT Scenarios• Closing Decks    • RAID & Defect Logs
                 `bench doc stamp`    `bench ppt generate``bench xlsx calculate`
                          │              │               │
                          └──────────────┼───────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ 4. RUN LINTER & QA SANITY CHECK              │
                  │    `bench doc lint --file <out.docx>`        │
                  │    `bench test --unit` (Fast verification)   │
                  └──────────────────────────────────────────────┘
```

---

## 2. Stage-Gate Compliance Rules (Enforced via `LIFECYCLE.md`)

Before generating any deliverable, verify that the project's current lifecycle stage authorizes it:

| Project Stage | Active Deliverables Allowed | Prohibited Deliverables (Out-of-Order) |
| :--- | :--- | :--- |
| **Stage 0: Presales & Sizing** | Pitch Decks, Sizing Calculators, Manday Matrices, POC Scopes, PKS Contracts | Project Charters, PMP, FSD, TSD, SIT/UAT, BAST |
| **Stage 1: Initiation & Kick-Off** | Kick-off Decks, Project Charter, Stakeholder Register, Baseline Schedules | FSD, TSD, Test Scenarios, BAST Certificates |
| **Stage 2: Assessment & Design** | PMP Master Blueprint, FSD Module Specs, Architecture Diagrams | TSD, SIT/UAT Test Scripts, Cutover Plans |
| **Gate 1 Milestone** | **BAST Milestone 1** (Formal Sign-Off on Architecture/FSD) | Cannot proceed to build without signed BAST M1 |
| **Stage 3: Sprints & Executing** | Weekly MoM, Weekly Progress Decks, RAID Registers, Change Logs | Final BAST Milestone 2 |
| **Stage 4: Verification (SIT/UAT)** | SIT Scenarios (Backend/Frontend), UAT Briefing, UAT Scenarios, Defect List | Final Closeout Checklist |
| **Stage 5: Cutover & Go-Live** | Deployment Rundown, Admin Guide, User Guide, **BAST Milestone 2** | Pre-mature Closeout |
| **Stage 6: Project Closure** | Project Closing Presentation, Closeout Checklist, CR BAST | - |

> [!WARNING]
> Never generate technical specifications (TSD) or SIT/UAT scripts in Stage 0 or Stage 1. Enterprise governance strictly prohibits drafting execution specs before commercial execution of the PKS agreement.

---

## 3. Master Deliverable Catalog Lookup (`CATALOG.md`)

Always read template baselines from [`clean_workspace/`](../../clean_workspace/) to prevent PII leakage. Key benchmark paths:

* **Legal & Handover Certificates**:
  - `clean_workspace/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/Perjanjian_Kerjasama_PKS_Template.docx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/BAST_Milestone_1_Template.docx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/BAST_Milestone_2_Final_Template.docx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/07_internal_legal_contracts/BAST_Change_Request_Template.docx`
* **Initiation & Governance**:
  - `clean_workspace/projects/TTI_Snowflake_Analytics/02_initiating/1.1_Kick-off_Material_Template.pptx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/02_initiating/1.2_Project_Charter_Template.docx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/02_initiating/1.3_Stakeholders_Register_Template.xlsx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/02_initiating/1.4.1_Project_Timeline_Baseline_Template.xlsx`
* **Specifications**:
  - `clean_workspace/projects/TTI_Snowflake_Analytics/03_planning/2.1_Project_Management_Plan_Template.docx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/03_planning/2.3_Functional_Specification_Document_FSD_Template.docx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/04_executing/3.1_Technical_Specification_Document_TSD_Template.docx`
* **Monitoring & Weekly Cadence**:
  - `clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.1_MoM_Minutes_of_Meeting_Template.docx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Timeline_Update_Template.xlsx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.4_Change_Log_Ledger_Template.xlsx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.5_Risk_Register_Template.xlsx`
  - `clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.6_Issue_Log_Template.xlsx`

---

## 4. CLI Operations Runbook (`bench`)

All deliverables must be generated via exact 1-line commands executed with `uv run bench ...`.

### General Project Provisioning & Verification
```bash
# Provision workspace for new engagement
uv run bench init-project "Project_Alpha" --client "Client Corp" --vendor "Consulting Partner"

# Fast sanity verification (<1s execution)
uv run bench test --unit
```

### Stage 0: Presales & Sizing
```bash
# 1. Cloud Infrastructure Sizing Calculator
uv run bench xlsx calculate --template Cloud_Sizing_Calculator_Template.xlsx --data data/sizing_input.json --output output/Cloud_Sizing_Calculated.xlsx

# 2. Presales Mandays & Pricing Estimate
uv run bench xlsx calculate --template Timeline_and_Mandays_Estimate_Template.xlsx --data data/mandays_input.json --output output/Timeline_Mandays.xlsx

# 3. Master Agreement Contract (PKS)
uv run bench doc stamp --template Perjanjian_Kerjasama_PKS_Template.docx --data data/pks_data.json --output output/PKS_Contract.docx

# 4. Presales Strategic Deck
uv run bench ppt generate --theme brickred --title "Enterprise Architecture Strategy" --output output/Presales_Pitch.pptx
```

### Stage 1: Initiation & Kick-Off
```bash
# 1. Kick-Off Meeting Deck
uv run bench ppt generate --theme brickred --title "Engagement Kick-Off" --output output/Kickoff_Deck.pptx

# 2. Project Charter
uv run bench doc stamp --template 1.2_Project_Charter_Template.docx --data data/charter.json --output output/Project_Charter.docx

# 3. Stakeholder Register & RACI
uv run bench xlsx calculate --template 1.3_Stakeholders_Register_Template.xlsx --data data/stakeholders.json --output output/Stakeholder_Register.xlsx

# 4. Project Baseline Schedule
uv run bench xlsx calculate --template 1.4.1_Project_Timeline_Baseline_Template.xlsx --data data/schedule.json --output output/Timeline_Baseline.xlsx
```

### Stage 2: Assessment & Design
```bash
# 1. Project Management Plan (PMP) Blueprint
uv run bench doc stamp --template 2.1_Project_Management_Plan_Template.docx --data data/pmp.json --output output/PMP_Blueprint.docx

# 2. Functional Specification Document (FSD)
uv run bench doc stamp --template 2.3_Functional_Specification_Document_FSD_Template.docx --data data/fsd.json --output output/FSD_Specification.docx

# 3. Gate 1 Milestone Certificate (BAST Milestone 1)
uv run bench doc stamp --template BAST_Milestone_1_Template.docx --data data/bast_m1.json --output output/BAST_Milestone_1.docx

# 4. Verify Document Formatting & Tags
uv run bench doc lint --file output/BAST_Milestone_1.docx
```

### Stage 3: Sprints & Executing
```bash
# 1. Weekly Minutes of Meeting (MoM)
uv run bench doc stamp --template 4.1_MoM_Minutes_of_Meeting_Template.docx --data data/mom.json --output output/MoM_Week04.docx

# 2. Weekly Progress Review Deck
uv run bench ppt generate --theme brickred --title "Sprint 4 Progress Review" --output output/Weekly_Status.pptx

# 3. Weekly Task Progress & Schedule Tracking
uv run bench xlsx calculate --template 4.2_Weekly_Progress_Timeline_Update_Template.xlsx --data data/progress.json --output output/Weekly_Progress.xlsx

# 4. Change Request Ledger Update
uv run bench xlsx calculate --template 4.4_Change_Log_Ledger_Template.xlsx --data data/cr_ledger.json --output output/Change_Log_Ledger.xlsx

# 5. Risk & Issue Registers (RAID)
uv run bench xlsx calculate --template 4.5_Risk_Register_Template.xlsx --data data/risks.json --output output/Risk_Register.xlsx
uv run bench xlsx calculate --template 4.6_Issue_Log_Template.xlsx --data data/issues.json --output output/Issue_Log.xlsx
```

### Stage 4: Verification (SIT/UAT)
```bash
# 1. Technical Specification Document (TSD)
uv run bench doc stamp --template 3.1_Technical_Specification_Document_TSD_Template.docx --data data/tsd.json --output output/TSD_Specification.docx

# 2. UAT Timeline & Execution Schedule
uv run bench xlsx calculate --template 3.4_Timeline_UAT_Template.xlsx --data data/uat_schedule.json --output output/Timeline_UAT.xlsx

# 3. Defect Tracker & Severity Matrix
uv run bench xlsx calculate --template 3.6_Defect_List_Template.xlsx --data data/defects.json --output output/Defect_Tracker.xlsx
```

### Stage 5: Cutover & Go-Live
```bash
# 1. Production Deployment Rundown & Rollback Plan
uv run bench xlsx calculate --template 3.7_Rundown_Deployment_Template.xlsx --data data/cutover.json --output output/Deployment_Rundown.xlsx

# 2. Gate 2 Final Milestone Handover (BAST Milestone 2)
uv run bench doc stamp --template BAST_Milestone_2_Final_Template.docx --data data/bast_m2.json --output output/BAST_Milestone_2_Final.docx

# 3. Quality Assurance Linting
uv run bench doc lint --file output/BAST_Milestone_2_Final.docx
```

### Stage 6: Project Closure
```bash
# 1. Executive Closeout Deck
uv run bench ppt generate --theme brickred --title "Project Closeout & Value Realization" --output output/Project_Closeout.pptx

# 2. Project Closeout Checklist
uv run bench xlsx calculate --template 5.2_Project_Closeout_Checklist_Template.xlsx --data data/closeout.json --output output/Project_Closeout_Checklist.xlsx

# 3. Change Request Commercial Handover (BAST CR)
uv run bench doc stamp --template BAST_Change_Request_Template.docx --data data/bast_cr.json --output output/BAST_Change_Request.docx
```

### Diagrams & Architecture Visualizations (`bench diagram ...`)
Maintain multi-page master `.drawio` files for project workflows and export targeted pages to deliverables:
```bash
# 1. Inspect all diagram tabs/pages in a master .drawio file
uv run bench diagram list output/project_master.drawio

# 2. Add or update a specific diagram page tab using Mermaid syntax
uv run bench diagram add output/project_master.drawio --page "Ingestion Architecture" --mermaid "graph TD; A[API] --> B[Pipeline]"

# 3. Add or update a page from an external .mmd definition file
uv run bench diagram add output/project_master.drawio --page "Storage Cluster" --file data/storage_flow.mmd --theme corporate_navy

# 4. Export a targeted diagram page to high-DPI PNG with pure white background
uv run bench diagram export output/project_master.drawio --page "Ingestion Architecture" --output output/diagrams/ingestion.png --white-bg

# 5. Export a targeted diagram page with transparent background (ideal for PPT slides)
uv run bench diagram export output/project_master.drawio --page "Ingestion Architecture" --output output/diagrams/ingestion_transparent.png --transparent

# 6. Export a diagram page to scalable vector SVG
uv run bench diagram export output/project_master.drawio --page "Storage Cluster" --output output/diagrams/storage.svg --format svg
```

---

## 5. Security & Data Scrubbing Standards

When onboarding external raw deliverables or client files into templates:
```bash
# 1. Sanitize raw client documents before cataloging (includes automated post-PII element purge)
uv run bench doc sanitize --input raw_source_files/sample.docx --output clean_workspace/sanitized_sample.docx

# 2. Standalone Element Purge: Wipe review comments, author highlights & tracked revisions
uv run bench doc purge --file output/project_deliverable.docx

# 3. Batch Element Purge across an entire project directory
uv run bench doc purge --dir output/project_alpha/documents/
```

### Post-PII Document Cleansing Protocol (Comments & Highlights Purge)
- Raw client deliverables frequently retain hundreds of internal stakeholder comments, yellow/colored text highlights, and residual tracked revisions.
- Following standard PII entity substitution, the engine runs an automated OpenXML element purge:
  1. **Comments Purge:** Strips all `word/comments.xml`, extended comment parts, relationship bindings, and inline `<w:commentRangeStart>`, `<w:commentRangeEnd>`, and `<w:commentReference>` anchors.
  2. **Highlights Purge:** Strips all `<w:highlight>` formatting across body paragraphs, tables, headers, and footers.
  3. **Revisions Purge:** Normalizes `<w:ins>`, removes `<w:del>` markup, and strips editorial change markers (`<w:rPrChange>`, `<w:pPrChange>`).
- All stamped deliverables and newly generated files **MUST** be placed in `output/` or `project_outputs/<project_name>/`.
- **NEVER** overwrite files in `clean_workspace/` with generated client deliverables; `clean_workspace/` is strictly for clean golden master templates.
