# Enterprise Deliverable Architecture & Lifecycle Blueprint

> **Reference Specification:** Enterprise Delivery Governance Model  
> **Exported Standalone Artifact:** Universal Lifecycle Flow, Stage-Gate Matrix, and Document Dependency Graphs.  
> **Target Project Baseline:** `TTI_Snowflake_Analytics` & Multi-Project Workbench Engine.

---

## 1. Master Chronological Flowchart

```mermaid
flowchart TD
    subgraph PreProject["Stage 0: Presales & Sizing (Nov - Dec 2025)"]
        D0_1["Modernize Data Platform Pitch (.pptx)"]
        D0_2["Cloud Sizing Calculator (.xlsx)"]
        D0_3["Timeline & Mandays Estimate (.xlsx)"]
        D0_4["Account POC Scope (.docx)"]
        D0_5["Master Agreement PKS (.docx)"]
    end

    subgraph Stage1["Stage 1: Initiation & Governance (15 - 16 Dec 2025)"]
        D1_1["Project Kick-Off Material (.pptx)"]
        D1_2["Project Charter (.docx)"]
        D1_3["Project Org Structure (.pptx)"]
        D1_4["Stakeholders Register & RACI (.xlsx)"]
        D1_5["Timeline Baseline Gantt (.xlsx & .mpp)"]
    end

    subgraph Stage2["Stage 2: Assessment & Design (19 Dec 2025 - 19 Jan 2026)"]
        D2_1["Project Management Plan PMP (.docx)"]
        D2_2["Functional Spec FSD (.docx)"]
        D2_3["Architecture Schematics (.drawio)"]
        D2_4["Technical Spec TSD (.docx)"]
        G1{{"GATE 1 SIGN-OFF:<br>BAST Milestone 1 (.docx)<br><i>(26 Jan 2026)</i>"}}
    end

    subgraph Stage3["Stage 3: Engineering Sprints (02 Jan - 13 Feb 2026)"]
        D3_1["Snowflake Ingestion & Gold Views"]
        D3_2["Streamlit Analytics & Cortex AI Pages"]
        D3_3["Weekly Steering Decks (.pptx)"]
        D3_4["Weekly Timeline Tracker (.xlsx)"]
    end

    subgraph Stage4["Stage 4: Verification & Acceptance (18 Feb - 25 Mar 2026)"]
        D4_1["SIT Scenario Backend (.docx)"]
        D4_2["SIT Scenario Frontend (.docx)"]
        D4_3["UAT Socialization Briefing (.pptx)"]
        D4_4["UAT Timeline Tracker (.xlsx)"]
        D4_5["UAT Scenarios (.docx)"]
        D4_6["Defect Tracker & Severity Log (.xlsx)"]
    end

    subgraph Stage5["Stage 5: Cutover & Go-Live (20 - 27 Mar 2026)"]
        D5_1["Deployment Rundown & Rollback (.xlsx)"]
        D5_2["End-User Operational Guide (.docx)"]
        D5_3["System Administrator Guide (.docx)"]
        G2{{"GATE 2 SIGN-OFF:<br>BAST Milestone 2 (.docx)<br><i>(27 Mar 2026)</i>"}}
    end

    subgraph Stage6["Stage 6: Closure & Hypercare (Apr - Jun 2026)"]
        D6_1["Project Closing Presentation (.pptx)"]
        D6_2["Closeout Verification Checklist (.xlsx)"]
        D6_3["Resource Leave & Support Calendar (.xlsx)"]
    end

    subgraph ChangeManagement["Parallel Change Control Subsystem (Jan - Aug 2026)"]
        CR_1["Change Request Form (.docx)"]
        CR_2["Change Control Ledger (.xlsx)"]
        CR_3["CR Scoping & Mandays (.xlsx)"]
        CR_G{{"CR FINAL ACCEPTANCE:<br>BAST Change Request (.docx)<br><i>(20 Aug 2026)</i>"}}
    end

    PreProject -->|Commercial Signing| Stage1
    Stage1 -->|Kickoff Alignment| Stage2
    Stage2 --> G1
    G1 -->|Unlocks Development| Stage3
    Stage3 -->|Code Freeze| Stage4
    Stage4 -->|UAT Passed 100%| Stage5
    Stage5 --> G2
    G2 -->|Production Handoff| Stage6

    Stage4 -.->|Scope Expansion Intercepted| ChangeManagement
    Stage5 -.->|Post-Baseline Enhancements| ChangeManagement
```

---

## 2. Document Evolution: The FSD to TSD Bridge

```mermaid
sequenceDiagram
    autonumber
    actor Business as Business Stakeholders
    participant BA as Business Analyst / Functional Lead
    participant Architect as Lead Architect & Data Engineer
    actor Steering as Steering Committee

    Business->>BA: Explain Business Reporting Requirements (P&L, Balance Sheet, Aging)
    BA->>BA: Draft FSD (Formulas, Aggregation Rules, Wireframes, User Roles)
    BA->>Business: Review FSD Mockups & Validate Business Logic
    Business-->>BA: Business Approval of FSD
    
    rect rgb(240, 245, 255)
    note over BA,Architect: Technical Evolution Stage (FSD -> TSD)
    BA->>Architect: Hand Over Approved Functional Scope
    Architect->>Architect: Design Snowflake DDLs, ERDs, Staging Views, dbt Models
    Architect->>Architect: Define RBAC Roles, Warehouse Clusters, Data Ingestion APIs
    Architect->>Architect: Finalize TSD (Technical Realization of FSD)
    end

    Architect->>Steering: Submit TSD & FSD Architecture Blueprint
    Steering-->>Architect: Execute BAST Milestone 1 (Design Gate Sign-off)
```

---

## 3. SIT to UAT Quality Verification Gate

```mermaid
stateDiagram-v2
    [*] --> DevelopmentComplete: Code Freeze
    
    state SIT_Verification {
        [*] --> BackendSIT: Run 3.3.1 Backend SIT (ETL & Views)
        BackendSIT --> FrontendSIT: Run 3.3.2 Frontend SIT (UI & Filters)
        FrontendSIT --> DefectTriage: Log Bugs in 3.6 Defect List
        DefectTriage --> BackendSIT: Fix & Retest Defect
        DefectTriage --> SIT_Passed: 100% Critical/Major Tests Passed
    }
    
    DevelopmentComplete --> SIT_Verification
    
    state UAT_Acceptance {
        [*] --> UserBriefing: Present 3.4 UAT Socialization Briefing
        UserBriefing --> ScriptExecution: Execute 3.4 UAT Scenarios by Accounting
        ScriptExecution --> UserSignoff: Business User Sign-off per Module
    }
    
    SIT_Passed --> UAT_Acceptance: Prerequisite Gate Unlocked
    UAT_Acceptance --> CutoverReady: Unlocks 3.7 Deployment Rundown
    CutoverReady --> [*]
```
