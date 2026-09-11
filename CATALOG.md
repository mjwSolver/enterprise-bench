# Enterprise Bench Document & Deliverable Master Catalog

> **Workspace:** `clean_workspace/` (Production Clean & Sanitized Repository)
> **Integrity Guarantee:** All files in this catalog have been cleansed of client/vendor PII and personal identities.
> **Access Policy:** Downstream automation engines and future workshops are strictly restricted to reading from `clean_workspace/`.

---

## Project: `KRA_ESG_Research`
*Academic & Strategic Research: ESG Disclosure & Financial Reporting Quality under OJK Regulation*

### Phase: Presentations (`presentations/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `KRA_1 Sept2026.pptx` | `PPTX` | 7845.3 KB | **Academic Research Deck - Original (21 slides):** Research presentation analyzing the impact of ESG Disclosures on Financial Reporting Quality under Indonesian OJK regulation POJK No 51/2017. |
| `KRA_1_Sept2026_Modern_Consulting.pptx` | `PPTX` | 182.4 KB | **Academic Research Deck - Consulting Redesign (15 slides):** Redesigned executive presentation structuring the ESG disclosure empirical study into modern McKinsey/BCG consulting visual archetypes. |
| `generate_redesigned_deck.py` | `PY` | 63.4 KB | **Project Asset:** Internal asset supporting delivery in presentations. |
| `montage.png` | `PNG` | 1130.5 KB | **Project Asset:** Internal asset supporting delivery in presentations. |

## Project: `TTI_Snowflake_Analytics`
*Enterprise Consulting Delivery: Financial Analytics Platform on Snowflake (36 Assets across 7 Lifecycle Phases)*

### Phase: 01 Presales (`01_presales/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `Account_POC_Scope_Template.docx` | `DOCX` | 15.9 KB | **Proof of Concept (POC) Scope Document:** Pre-sales technical agreement detailing POC objectives, Snowflake architecture scope, trial data boundaries, success metrics, and sign-off prerequisites. |
| `Cloud_Sizing_Calculator_Template.xlsx` | `XLSX` | 18.0 KB | **Snowflake Infrastructure Sizing Model:** Cost and compute calculator forecasting credit consumption, storage tiers, virtual warehouse sizes (XS to XL), and annual cloud infrastructure TCO. |
| `Modernize_Data_Platform_Pitch_Deck_Template.pptx` | `PPTX` | 44702.0 KB | **Executive Presales Pitch Deck (36 slides):** Modern data platform pitch deck covering legacy DW pain points, Snowflake cloud migration roadmap, business value realization, and architectural modernization phases. |
| `Timeline_and_Mandays_Estimate_Template.xlsx` | `XLSX` | 21.1 KB | **Presales Work Breakdown & Pricing Matrix:** Effort estimation workbook detailing role-based mandays (Architect, Data Engineer, PM), billing rates, and delivery phase timelines. |

### Phase: 02 Initiating (`02_initiating/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `1.1_Kick-off_Material_Template.pptx` | `PPTX` | 6744.3 KB | **Project Kick-Off Deck (19 slides):** Initiation slide deck presenting project vision, dual governance org structure, timeline milestones, and data governance ground rules. |
| `1.2_Project_Charter_Template.docx` | `DOCX` | 148.7 KB | **Project Charter:** Official initiation governance document establishing executive sponsorship, business objectives, project constraints, milestone gates, and steering committee authority. |
| `1.3_Stakeholders_Register_Template.xlsx` | `XLSX` | 10.0 KB | **Stakeholder Directory & RACI Matrix:** Contact ledger cataloging steering committee members, client department leads, consulting team roles, and communication channels. |
| `1.4.1_Project_Timeline_Baseline_Template.xlsx` | `XLSX` | 9.0 KB | **Baseline Gantt Schedule (Spreadsheet):** Task-by-task schedule tracking work breakdown milestones from assessment to hypercare cutover. |
| `1.4_Project_Timeline_Baseline_Template.mpp` | `MPP` | 782.0 KB | **Microsoft Project Baseline File (.mpp):** Native MS Project file containing dependency linkages, critical path analysis, and resource levelling for the baseline schedule. |
| `Project_Org_Structure_Template.pptx` | `PPTX` | 420.0 KB | **Project Organization Hierarchy:** Visual chart illustrating steering committee reporting lines, PMO alignment, and technical sprint team leads. |

### Phase: 03 Planning (`03_planning/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `2.1_Project_Management_Plan_Template.docx` | `DOCX` | 984.7 KB | **Project Management Plan (PMP):** Master delivery governance blueprint detailing scope management, communications cadences, quality gates, risk mitigation, and change control procedures. |
| `2.3_Functional_Specification_Document_FSD_Template.docx` | `DOCX` | 3224.6 KB | **Functional Specification Document (FSD):** Business requirement definition detailing reporting modules (Balance Sheet, P&L, Inventory Aging), business rules, input data schemas, user personas, and report layout mockups. |
| `FSD_Architecture_Diagrams_Template.drawio` | `DRAWIO` | 110.6 KB | **Architecture Diagrams (Draw.io):** Visual architecture assets illustrating source ETL ingestion flows, data warehouse staging layers, and reporting semantic models. |

### Phase: 04 Executing (`04_executing/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `3.1_Technical_Specification_Document_TSD_Template.docx` | `DOCX` | 21842.0 KB | **Technical Specification Document (TSD):** The finalized technical implementation specification formalizing FSD designs into Snowflake DDLs, dbt transformation pipelines, RBAC security roles, query performance tuning, and staging architecture. |
| `3.3.1_SIT_Scenario_Backend_Template.docx` | `DOCX` | 7624.8 KB | **System Integration Test (SIT) - Backend Test Cases:** Test scenarios validating Snowflake ingestion pipelines, data transformation logic, constraint validations, and error logging. |
| `3.3.2_SIT_Scenario_Frontend_Template.docx` | `DOCX` | 3262.0 KB | **System Integration Test (SIT) - Frontend Test Cases:** Test scenarios validating dashboard metric accuracy, interactive filter behavior, drill-down capabilities, and export functionality. |
| `3.4_Sosialisasi_UAT_Briefing_Template.pptx` | `PPTX` | 10233.3 KB | **User Acceptance Testing (UAT) Briefing Deck:** Training and orientation slides introducing business users to testing environments, test script execution, and defect reporting flows. |
| `3.4_Timeline_UAT_Template.xlsx` | `XLSX` | 6.0 KB | **UAT Execution Timeline & Tracking:** Schedule tracking daily user test sessions, business module sign-off gates, and defect turnaround windows. |
| `3.4_UAT_Scenario_Template.docx` | `DOCX` | 1956.2 KB | **UAT Scenarios & Business Sign-off Protocol:** Step-by-step test scenarios for end users to validate reporting outputs against source accounting ledgers. |
| `3.6.1_User_Guide_Template.docx` | `DOCX` | 7335.2 KB | **End-User System Guide:** Operational manual guiding business accountants and analysts on navigating the reporting portal, executing queries, and interpreting dashboard metrics. |
| `3.6.2_Admin_Guide_Template.docx` | `DOCX` | 6898.3 KB | **System Administrator Guide:** Technical administration manual covering user provisioning, Snowflake role assignments, warehouse monitoring, and backup/restore procedures. |
| `3.6_Defect_List_Template.xlsx` | `XLSX` | 70.6 KB | **Defect Tracker & Severity Ledger (5 sheets):** Bug tracking ledger with severity classifications (Critical to Low), priority matrices, and resolution audit status. |
| `3.7_Rundown_Deployment_Template.xlsx` | `XLSX` | 10.5 KB | **Production Cutover Rundown & Rollback Plan:** Minute-by-minute deployment checklist covering pre-flight backups, clone staging, cutover execution, and emergency rollback procedures. |

### Phase: 05 Monitoring (`05_monitoring/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `4.1_MoM_Minutes_of_Meeting_Template.docx` | `DOCX` | 58.8 KB | **Minutes of Meeting (MoM) Template:** Formal record of project meetings documenting attendance, agenda discussions, design agreements, and numbered action items with owners. |
| `4.2_Weekly_Progress_Report_Deck_Template.pptx` | `PPTX` | 7371.3 KB | **Weekly Executive Progress Deck (11 slides):** Weekly status deck presenting percentage completions, milestone trackers, sprint achievements, and active RAID items. |
| `4.2_Weekly_Progress_Timeline_Update_Template.xlsx` | `XLSX` | 29.2 KB | **Weekly Task Progress Tracker:** Working tracking spreadsheet updating task-level percent completions and schedule variance. |
| `4.4_Change_Log_Ledger_Template.xlsx` | `XLSX` | 9.6 KB | **Change Control Ledger:** Master register tracking all submitted Change Requests, review statuses, cost impacts, and approval dates. |
| `4.4_Change_Request_Form_Template.docx` | `DOCX` | 176.4 KB | **Change Request (CR) Form:** Formal document specifying proposed scope/schedule changes, business rationale, technical impact assessment, manday effort, and steering sign-off. |
| `4.5_Risk_Register_Template.xlsx` | `XLSX` | 10.1 KB | **Risk Register (RAID):** Risk log tracking probability, impact scoring, mitigation strategies, and assigned risk owners. |
| `4.6_Issue_Log_Template.xlsx` | `XLSX` | 8.9 KB | **Issue Log (RAID):** Issue register tracking active blockers, root causes, severity ratings, corrective action plans, and resolution target dates. |

### Phase: 06 Closing (`06_closing/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `5.1_Project_Closing_Deck_Template.pptx` | `PPTX` | 5560.7 KB | **Project Closing & Handover Presentation (9 slides):** Formal completion deck summarizing contract deliverables, transition to hypercare/maintenance, and contact directory. |
| `5.2_Project_Closeout_Checklist_Template.xlsx` | `XLSX` | 9.0 KB | **Project Closeout Checklist:** Verification checklist verifying delivery of source code, documentation, credentials handover, and warranty sign-offs. |

### Phase: 07 Internal Legal Contracts (`07_internal_legal_contracts/`)

| File Name | Format | Size | Internal Content & Functional Purpose (Verified from In-File Inspection) |
| :--- | :--- | :--- | :--- |
| `BAST_Change_Request_Template.docx` | `DOCX` | 48.9 KB | **BAST Handover Certificate - Change Request:** Legal delivery certificate acknowledging formal client acceptance and sign-off for completed Change Request work. |
| `BAST_Milestone_1_Template.docx` | `DOCX` | 48.7 KB | **BAST Handover Certificate - Milestone 1:** Legal delivery certificate for Milestone 1 (Assessment, Architecture Design, and FSD/TSD sign-off). |
| `BAST_Milestone_2_Final_Template.docx` | `DOCX` | 48.8 KB | **BAST Handover Certificate - Milestone 2 (Final):** Legal delivery certificate for Milestone 2 (Development, SIT/UAT Acceptance, and Production Deployment). |
| `CR_Scoping_and_Mandays_Template.xlsx` | `XLSX` | 255.4 KB | **Change Request Effort & Manday Scoping:** Detailed spreadsheet breaking down manday requirements for specific scope additions (e.g. Inventory Aging UI extension). |
| `Perjanjian_Kerjasama_PKS_Template.docx` | `DOCX` | 743.5 KB | **Master Service Agreement (PKS):** Full bilateral legal contract defining service deliverables, intellectual property terms, payment schedules, warranties, and liability clauses. |
| `Resource_Leave_Schedule_Template.xlsx` | `XLSX` | 7.9 KB | **Consulting Team Availability & Holiday Schedule:** Team calendar tracking resource leaves and public holidays across delivery sprint cycles. |
