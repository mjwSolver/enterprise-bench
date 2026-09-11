# Enterprise Deliverable Chronological Lifecycle & Stage-Gate Index

> **Repository Standard:** Enterprise Delivery Governance Model  
> **Source Baseline:** Extracted from verified internal schedules, PMP milestones, and executed BAST legal certificates (`TTI_Snowflake_Analytics`).  
> **Purpose:** Establishes the exact chronological sequencing of all project deliverables, detailing what files **must** exist, what files **must not** exist prematurely, and the stage-gate prerequisites governing each transition.

---

## 1. Master Chronological Flow & Stage Gates

```mermaid
flowchart TD
    S0["STAGE 0: Presales & Sizing<br><i>(Nov - Dec 2025)</i>"] -->|PKS Contract Signed| S1["STAGE 1: Initiation & Kick-Off<br><i>(15 - 16 Dec 2025)</i>"]
    S1 -->|Charter Approved| S2["STAGE 2: Assessment & Design<br><i>(19 Dec 2025 - 19 Jan 2026)</i>"]
    S2 -->|GATE 1: BAST Milestone 1 Signed (26 Jan)| S3["STAGE 3: Development Sprints<br><i>(02 Jan - 13 Feb 2026)</i>"]
    S3 -->|Code Freeze & Build Done| S4["STAGE 4: Verification & Testing (SIT/UAT)<br><i>(18 Feb - 25 Mar 2026)</i>"]
    S4 -->|UAT Accepted & Cutover Run| S5["STAGE 5: Go-Live & Deployment<br><i>(20 - 27 Mar 2026)</i>"]
    S5 -->|GATE 2: BAST Milestone 2 Signed (27 Mar)| S6["STAGE 6: Closure & Warranty<br><i>(Apr - Jun 2026)</i>"]

    subgraph Continuous Governance Across Sprints
        CG1["Weekly MoM (Minutes)"]
        CG2["Weekly Progress Deck & Gantt Update"]
        CG3["RAID Logs (Risk & Issue Registers)"]
        CG4["Change Control (CR Form, Ledger, Scoping, CR BAST)"]
    end
```

---

## 2. Stage-by-Stage Chronological Lifecycle Matrix

### Stage 0: Presales, Sizing & Contracting
- **Timeline:** Pre-project initiation (November – Early December 2025)
- **Phase Objective:** Solution discovery, architecture sizing, business case validation, and commercial contracting.

#### Files Active in Stage 0 (What SHOULD Be Here):
| File Name | Format | Role in This Stage | Key Owner / RACI |
| :--- | :--- | :--- | :--- |
| `01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx` | PPTX | Executive sales pitch establishing business pain points and proposed Snowflake modernization blueprint. | Solution Architect / Sales Lead |
| `01_presales/Cloud_Sizing_Calculator_Template.xlsx` | XLSX | Sizing model calculating credit consumption, warehouse tiers, and annual cloud infrastructure TCO. | Cloud Enterprise Architect |
| `01_presales/Timeline_and_Mandays_Estimate_Template.xlsx` | XLSX | Cost & manday estimation modeling required engineering roles, billing rates, and delivery phases. | Practice Lead / Bid Manager |
| `01_presales/Account_POC_Scope_Template.docx` | DOCX | Pre-sales technical agreement detailing trial data boundaries, success criteria, and sign-off prerequisites. | Lead Technical Consultant |
| `07_internal_legal_contracts/Perjanjian_Kerjasama_PKS_Template.docx` | DOCX | Bilateral Master Service Agreement (PKS) defining intellectual property, legal terms, and payment milestones. | Legal Counsel / Division Head |

#### Files Prohibited in Stage 0 (What SHOULD NOT Be Here Yet):
- `Project_Charter`, `PMP`, `FSD`, `TSD`, `SIT/UAT Scripts`, `BAST Handover Certificates`.
- *Audit Rationale:* No project management plans or technical specifications may be drafted before commercial execution of the PKS agreement.

---

### Stage 1: Project Initiation & Governance Baseline
- **Timeline:** 15 December 2025 – 16 December 2025
- **Phase Objective:** Formal project kickoff, governance committee chartering, baseline scheduling, and stakeholder directory registration.

#### Files Active in Stage 1 (What SHOULD Be Here):
| File Name | Format | Role in This Stage | Key Owner / RACI |
| :--- | :--- | :--- | :--- |
| `02_initiating/1.1_Kick-off_Material_Template.pptx` | PPTX | Official slide deck presented during the Kick-Off Meeting (16 Dec 2025) detailing vision and ground rules. | Project Manager (Presented to Steering) |
| `02_initiating/1.2_Project_Charter_Template.docx` | DOCX | Foundational governance charter authorizing the project, defining scope boundaries, and naming sponsors. | Project Manager / Project Sponsor |
| `02_initiating/Project_Org_Structure_Template.pptx` | PPTX | Governance chart defining reporting lines, steering committee members, PMO leads, and sprint engineers. | Project Manager |
| `02_initiating/1.3_Stakeholders_Register_Template.xlsx` | XLSX | Contact directory & RACI matrix logging client department officers, consultants, and communication matrix. | Project Management Office (PMO) |
| `02_initiating/1.4.1_Project_Timeline_Baseline_Template.xlsx` | XLSX | Baseline project schedule Gantt mapping work breakdown structures across 104 planned delivery days. | Project Manager / Lead Planner |
| `02_initiating/1.4_Project_Timeline_Baseline_Template.mpp` | MPP | Native MS Project file maintaining dependency linkages, critical paths, and resource levelling. | Project Scheduler |

#### Files Prohibited in Stage 1 (What SHOULD NOT Be Here Yet):
- `FSD`, `TSD`, `SIT Scenarios`, `UAT Documents`, `Cutover Plans`, `BAST Handover Certificates`.
- *Audit Rationale:* Technical design and testing assets cannot precede formal charter approval and kickoff alignment.

---

### Stage 2: Assessment, Planning & Architecture Design
- **Timeline:** 19 December 2025 – 19 January 2026
- **Phase Objective:** Business workshops, requirement gathering, UI/report prototyping, technical architecture finalization, and Milestone 1 handover.

#### Files Active in Stage 2 (What SHOULD Be Here):
| File Name | Format | Role in This Stage | Key Owner / RACI |
| :--- | :--- | :--- | :--- |
| `03_planning/2.1_Project_Management_Plan_Template.docx` | DOCX | Master delivery plan (PMP) detailing scope baselines, quality gates, risk mitigation, and SLA controls. | Project Manager |
| `03_planning/2.3_Functional_Specification_Document_FSD_Template.docx` | DOCX | Business functional requirement defining report logic (Balance Sheet, P&L, Inventory Aging), metrics, and wireframes. | Business Analyst / Functional Consultant |
| `03_planning/FSD_Architecture_Diagrams_Template.drawio` | DRAWIO | Architecture schematics illustrating source extraction, Snowflake staging layers, and semantic models. | Solution Architect |
| `04_executing/3.1_Technical_Specification_Document_TSD_Template.docx` | DOCX | **Finalized Evolution of FSD:** Technical implementation spec translating FSD requirements into DDLs, dbt models, and RBAC. | Lead Data Engineer / Architect |
| `07_internal_legal_contracts/BAST_Milestone_1_Template.docx` | DOCX | **GATE 1 APPROVAL:** Official delivery certificate signed (26 Jan 2026) acknowledging completion of Design & Architecture. | Client Steering Committee & PM |

#### Sequential Progression Rule within Stage 2:
> [!IMPORTANT]
> **FSD vs. TSD Dependency:** `2.3_Functional_Specification_Document_FSD_Template.docx` must be reviewed and conceptually approved by business stakeholders **before** `3.1_Technical_Specification_Document_TSD_Template.docx` is finalized. The TSD is the finalized technical realization of the FSD; releasing a TSD without an approved FSD invalidates stage compliance.

#### Files Prohibited in Stage 2 (What SHOULD NOT Be Here Yet):
- `SIT Results`, `UAT Scenarios`, `Defect Lists`, `Deployment Rundowns`, `User/Admin Guides`, `BAST Milestone 2`.

---

### Stage 3: Development & Engineering Sprints
- **Timeline:** 02 January 2026 – 13 February 2026
- **Phase Objective:** Provisioning Snowflake databases, building ingestion pipelines, implementing Streamlit/Cortex UI analytics, and running unit tests.

#### Files Active in Stage 3 (What SHOULD Be Here):
- Active Engineering Repositories (Python/SQL scripts, Streamlit application pages, dbt models).
- Reference Architecture: `3.1_Technical_Specification_Document_TSD_Template.docx` (used as the engineering reference).
- Continuous Sprint Governance: `4.1_MoM_Minutes_of_Meeting_Template.docx`, `4.2_Weekly_Progress_Report_Deck_Template.pptx`, `4.5_Risk_Register_Template.xlsx`, `4.6_Issue_Log_Template.xlsx`.

#### Files Prohibited in Stage 3 (What SHOULD NOT Be Here Yet):
- `3.4_UAT_Scenario_Template.docx` execution results, `3.7_Rundown_Deployment_Template.xlsx`, `BAST_Milestone_2_Final_Template.docx`.

---

### Stage 4: Verification & Acceptance Testing (SIT & UAT)
- **Timeline:** 18 February 2026 – 25 March 2026
- **Phase Objective:** Technical integration verification (SIT), business user training, user acceptance script execution (UAT), and defect resolution.

#### Files Active in Stage 4 (What SHOULD Be Here):
| File Name | Format | Role in This Stage | Key Owner / RACI |
| :--- | :--- | :--- | :--- |
| `04_executing/3.3.1_SIT_Scenario_Backend_Template.docx` | DOCX | System Integration Test scripts validating ETL data loads, transformations, and error handling. | QA Engineer / Data Engineer |
| `04_executing/3.3.2_SIT_Scenario_Frontend_Template.docx` | DOCX | SIT scripts validating UI widgets, filters, financial calculations, and data visual rendering. | QA Engineer / Frontend Dev |
| `04_executing/3.4_Sosialisasi_UAT_Briefing_Template.pptx` | PPTX | Training slide deck orienting business end users on UAT guidelines, test execution, and logging defects. | Business Analyst / PM |
| `04_executing/3.4_Timeline_UAT_Template.xlsx` | XLSX | Daily testing timetable tracking user test sessions and department sign-off checkpoints. | PMO / UAT Coordinator |
| `04_executing/3.4_UAT_Scenario_Template.docx` | DOCX | Business test cases executed by client accounting/finance teams with formal pass/fail sign-offs. | Business Users / Department Leads |
| `04_executing/3.6_Defect_List_Template.xlsx` | XLSX | Centralized bug tracker logging severity (Critical to Low), steps to reproduce, and retest verification. | QA Lead / Dev Lead |

#### Sequential Progression Rule within Stage 4:
> [!IMPORTANT]
> **SIT Precedes UAT:** `3.3.1_SIT_Scenario_Backend` and `3.3.2_SIT_Scenario_Frontend` must achieve **100% pass status on critical/major tests** before `3.4_Sosialisasi_UAT_Briefing` and `3.4_UAT_Scenario` are handed to end users. Defect list items with "Critical" severity block UAT progression.

---

### Stage 5: Production Deployment, Documentation & Go-Live
- **Timeline:** 20 March 2026 – 27 March 2026
- **Phase Objective:** Production cutover execution, knowledge transfer documentation delivery, and formal project acceptance (Milestone 2).

#### Files Active in Stage 5 (What SHOULD Be Here):
| File Name | Format | Role in This Stage | Key Owner / RACI |
| :--- | :--- | :--- | :--- |
| `04_executing/3.7_Rundown_Deployment_Template.xlsx` | XLSX | Minute-by-minute cutover checklist covering pre-flight backups, clone staging, and rollback scripts. | DevOps / Lead Data Engineer |
| `04_executing/3.6.1_User_Guide_Template.docx` | DOCX | Operational handbook instructing business users on accessing, querying, and interpreting dashboards. | Technical Writer / BA |
| `04_executing/3.6.2_Admin_Guide_Template.docx` | DOCX | Administrator manual covering user provisioning, Snowflake role maintenance, and backup schedules. | Cloud Architect / DBA |
| `07_internal_legal_contracts/BAST_Milestone_2_Final_Template.docx` | DOCX | **GATE 2 APPROVAL:** Final handover certificate signed (27 Mar 2026) acknowledging UAT acceptance & deployment. | Client Executive Sponsor & PM |

---

### Stage 6: Project Closure & Maintenance Warranty
- **Timeline:** April 2026 – June 2026
- **Phase Objective:** Final deliverable auditing, warranty support / hypercare, knowledge transfer sign-off, and contractual closeout.

#### Files Active in Stage 6 (What SHOULD Be Here):
| File Name | Format | Role in This Stage | Key Owner / RACI |
| :--- | :--- | :--- | :--- |
| `06_closing/5.1_Project_Closing_Deck_Template.pptx` | PPTX | Executive presentation summarizing delivered scope, business value achieved, and maintenance contacts. | Project Manager |
| `06_closing/5.2_Project_Closeout_Checklist_Template.xlsx` | XLSX | Audit checklist verifying handover of source code, configurations, accounts, documentation, and warranty. | PMO / Quality Assurance |
| `07_internal_legal_contracts/Resource_Leave_Schedule_Template.xlsx` | XLSX | Resource planning schedule tracking support team availability and public holidays during hypercare. | Resource Manager |

---

## 3. Parallel Governance & Change Control Tracks

These files are **not bounded to a single stage**; they operate continuously across the entire delivery lifecycle:

```text
Continuous Lifecycle Tracks:
├── Project Cadence Track:
│   ├── 4.1_MoM_Minutes_of_Meeting_Template.docx          (Generated per client meeting; numbered consecutively)
│   ├── 4.2_Weekly_Progress_Report_Deck_Template.pptx     (Presented weekly at Steering status reviews)
│   └── 4.2_Weekly_Progress_Timeline_Update_Template.xlsx (Updated weekly with task completion percentages)
│
├── RAID Governance Track:
│   ├── 4.5_Risk_Register_Template.xlsx                   (Updated bi-weekly; tracks probability & mitigations)
│   └── 4.6_Issue_Log_Template.xlsx                       (Updated continuously; tracks active blockers & root causes)
│
└── Change Control Track (Initiated on scope variance):
    ├── 4.4_Change_Request_Form_Template.docx             (Submitted by client or PM upon proposed scope variance)
    ├── 4.4_Change_Log_Ledger_Template.xlsx               (Maintains numerical registry: CR-01, CR-02, etc.)
    ├── CR_Scoping_and_Mandays_Template.xlsx              (Calculates cost, billing rate, and effort for the CR)
    └── BAST_Change_Request_Template.docx                 (Formal delivery sign-off for completed CR, e.g. Aug 2026)
```

---

## 4. Stage-Gate Compliance Checklist for Agents & Humans

When evaluating a project repository workspace at any given time, use this quick checklist to determine whether the workspace is compliant:

- [ ] **If in Stage 1 (Initiating):** Ensure `Project_Charter` and `Kick-off_Material` exist. Confirm **no** `TSD` or `BAST` files exist yet.
- [ ] **If in Stage 2 (Planning):** Ensure `FSD` is drafted and approved **prior** to finalizing `TSD`. Milestone 1 sign-off (`BAST_Milestone_1`) must exist before starting Stage 3.
- [ ] **If in Stage 3 (Development):** Ensure sprint meetings have recorded `MoM` documents and RAID registers are updated. Confirm **no** UAT sign-off files exist.
- [ ] **If in Stage 4 (Testing):** Verify `SIT` test results pass 100% of critical tests before launching `3.4_UAT_Scenario`. Verify all defects are logged in `3.6_Defect_List`.
- [ ] **If in Stage 5 (Go-Live):** Verify `3.7_Rundown_Deployment` is fully rehearsed, and `User_Guide` and `Admin_Guide` are attached before signing `BAST_Milestone_2`.
- [ ] **If in Stage 6 (Closing):** Ensure `Closeout_Checklist` has all items marked "Delivered" before presenting `5.1_Project_Closing_Deck`.

---

## 5. Architectural Deep Dives & Standalone Diagrams

For extended visual diagrams and dedicated engineering subsystems:
- **[LIFECYCLE_ARCHITECTURE.md](docs/LIFECYCLE_ARCHITECTURE.md):** Standalone Mermaid sequence diagrams, SIT-to-UAT quality gates, and FSD-to-TSD evolution models.
- **[CHANGE_REQUEST_SUBSYSTEM.md](docs/CHANGE_REQUEST_SUBSYSTEM.md):** Comprehensive operational guide to the Change Request subsystem, detailing the 4 core artifacts, commercial addendums, and case studies (CR #1 through CR #6).

