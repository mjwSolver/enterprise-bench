---
title: "User Acceptance Testing (UAT) Scenario Matrix"
subtitle: "Snowflake Financial Analytics Platform Sign-off Verification"
client: "Nusantara Global Logistics"
vendor: "PT Metrodata Electronics Tbk"
version: "1.0"
date: "July 2026"
status: "Execution Sign-off"
confidentiality: "CONFIDENTIAL & PROPRIETARY"
document_control:
  - date: "20 Jun 2026"
    version: "0.1"
    author: "QA & Test Engineering"
    description: "Initial UAT Test Case Draft"
  - date: "02 Jul 2026"
    version: "0.9"
    author: "Engagement QA Lead"
    description: "Updated with Client Review Feedback & Test Data Accounts"
  - date: "15 Jul 2026"
    version: "1.0"
    author: "Lead QA Consultant"
    description: "Final Execution Results & Stakeholder Sign-Off Baseline"
reviewers:
  - role: "Lead QA Engineer"
    name: "Andri Setiawan"
    status: "APPROVED"
    date: "15 Jul 2026"
  - role: "Client Project Manager"
    name: "Agus Suhanto"
    status: "APPROVED"
    date: "16 Jul 2026"
  - role: "Steering Committee Sponsor"
    name: "Arif Nanda Atmavidya"
    status: "APPROVED"
    date: "18 Jul 2026"
---

# 1. UAT Test Execution Framework & Criteria

## 1.1 Scope & Acceptance Objectives
User Acceptance Testing (UAT) establishes formal business validation for the **Snowflake Financial Analytics Platform**. Business users and financial controllers verify that system capabilities satisfy the approved Functional Specification Document (FSD) and business requirements.

The test scope encompasses:
1. **Authentication & Role-Based Security:** Single Sign-On (SSO) login, role switching, and dynamic data masking on sensitive fields.
2. **Financial Aggregation Accuracy:** Reconciliation between Snowflake `GOLD_FINANCE` marts and source SAP ECC accounting reports.
3. **Power BI Dashboard Visualizations:** Interactive filtering, cross-drilling, and export capabilities.
4. **Data Freshness & SLA:** Verification of daily automated dbt pipeline execution within approved morning operational windows (< 07:00 WIB).

---

## 1.2 UAT Entry & Exit Criteria

> [!NOTE]
> **Entry Criteria:** Successful completion of System Integration Testing (SIT) with 100% test execution, zero Severity-1/Severity-2 defects unresolved, and formal SIT sign-off by technical architecture leads.

> [!IMPORTANT]
> **Exit Criteria:** 100% of critical business test cases in `PASSED` status, sign-off from designated business process owners, and approved operational handover.

---

# 2. Detailed Test Scenario Execution Matrix

## 2.1 Authentication, Access Control & Data Governance

| Test ID | Module | Scenario Description | Preconditions | Test Steps | Expected Result | Status |
|:---|:---|:---|:---|:---|:---|:---|
| **UAT-SEC-01** | Authentication | Azure AD / Okta SSO Login | User assigned to NGL Azure AD group | 1. Navigate to portal URL<br>2. Click 'Login with Microsoft'<br>3. Complete MFA prompt | Seamless redirection to home dashboard with correct user profile | **PASSED** |
| **UAT-SEC-02** | Security | Role Isolation between Departments | User has 'Automotive Sales' role | 1. Access Financial Analytics mart<br>2. Filter by 'Chemical & Machinery' | Chemical & Machinery records return 0 rows or 'Access Denied' message | **PASSED** |
| **UAT-SEC-03** | Governance | Dynamic Masking on Customer Tax ID | Logged in as `ROLE_DATA_ANALYST` | 1. Query `DIM_CUSTOMER`<br>2. Inspect `TAX_IDENTIFICATION_NUMBER` | Field displays masked value: `XX.XXX.XXX.X-123.XXX` | **PASSED** |
| **UAT-SEC-04** | Security | Unmasked Access for Compliance Officer | Logged in as `ROLE_SECURITY_DBA` | 1. Query `DIM_CUSTOMER`<br>2. Inspect `TAX_IDENTIFICATION_NUMBER` | Full raw unmasked 15-digit NPWP value is visible for authorized audit | **PASSED** |

---

## 2.2 Financial Analytics, Reconciliation & Reporting

| Test ID | Module | Scenario Description | Preconditions | Test Steps | Expected Result | Status |
|:---|:---|:---|:---|:---|:---|:---|
| **UAT-FIN-01** | Reconciliation | Daily Gross Revenue vs SAP ECC FBL5N | Daily ETL completed successfully | 1. Extract net revenue from SAP FBL5N<br>2. Run Snowflake query on `FCT_SALES_AGG`<br>3. Compare totals | Revenue variance is exactly 0.00% (perfect reconciliation) | **PASSED** |
| **UAT-FIN-02** | Analytics | Multi-Currency Conversion (USD to IDR) | FX rates loaded in `DIM_FX_RATES` | 1. Select transaction in USD<br>2. Toggle currency filter to IDR<br>3. Verify applied Bank Indonesia middle rate | Accurate conversion matches official Bank Indonesia daily benchmark | **PASSED** |
| **UAT-FIN-03** | Performance | High-Volume Multi-Year Trend Query | 3 years of historical transactions (25M+ rows) | 1. Select 'All Time' date filter<br>2. Drill down into Product Category | Visual loads in under 2.5 seconds utilizing Snowflake result cache | **PASSED** |
| **UAT-FIN-04** | Export | Excel Export of Financial Report | Dashboard loaded with Q2 2026 data | 1. Click 'Export to Excel'<br>2. Verify generated spreadsheet formulas | Spreadsheet downloads cleanly with correct column headers and row counts | **PASSED** |

---

## 2.3 Exception Handling & SLA Verification

| Test ID | Module | Scenario Description | Preconditions | Test Steps | Expected Result | Status |
|:---|:---|:---|:---|:---|:---|:---|
| **UAT-OPS-01** | Operations | Daily Ingestion Pipeline Execution Window | Airflow DAG triggers at 04:00 WIB | 1. Inspect daily DAG execution log<br>2. Verify completion timestamp | Pipeline finishes by 05:45 WIB (well ahead of 07:00 WIB business SLA) | **PASSED** |
| **UAT-OPS-02** | Resilience | Auto-Recovery from Source Network Interruption | SAP network connection simulated timeout | 1. Interrupt source connection during stage extract<br>2. Observe retry mechanism | Airflow retries with exponential backoff and succeeds on attempt 2 | **PASSED** |
| **UAT-OPS-03** | Support | Defect Logging & Notification Alerting | Simulated dbt test assertion failure | 1. Inject malformed row into staging<br>2. Trigger dbt test suite | Slack / Teams alert fired to `#data-ops-alerts` with exact row count and model ID | **PASSED** |
