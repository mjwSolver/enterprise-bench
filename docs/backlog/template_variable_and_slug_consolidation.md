# Backlog: Universal Template Variable & Slug Consolidation Engine

> **Status:** Backlog / Architectural Proposal  
> **Target Subsystem:** `src/core/`, `src/ppt_engine/`, `src/docx_engine/`, `src/xlsx_engine/`  
> **Priority:** High (Universal Governance & PII Hygiene)  
> **Originating Directive:** Consolidate, catalog, and enforce parameterized slugs (e.g. `[CLIENT_COMPANY_NAME]`) across all 40 master templates, presentations, contracts, and spreadsheets to prevent accidental hardcoded entity leakage.

---

## 1. Problem Statement

Across the 40 deliverable templates in `clean_workspace/` and declarative YAML slide presets:
1. Historical client names (e.g. *Toyota Tsusho Indonesia*, *PT Toyota Tsusho Logistic Center*) and legacy employee names frequently reappear in slides, contracts, and progress spreadsheets.
2. Different deliverable engines currently use divergent token schemes:
   - **DOCX:** Jinja2 syntax (`{{ client_name }}`, `{{ contract_number }}`).
   - **PPTX:** Hardcoded string defaults in python functions, varying YAML metadata keys (`client`, `client_name`, `prepared_for`).
   - **XLSX:** Hardcoded cell strings with manual regex substitution.
3. Lack of a unified variable dictionary makes it difficult to clone a project workspace for a new client without missing residual PII.

---

## 2. Universal Slug Taxonomy

All engines and declarative configurations will standardize on an authoritative slug registry:

### A. Corporate & Institutional Entity Slugs
| Authoritative Slug | Jinja2 Token (`.docx`) | Description | Example Default |
| :--- | :--- | :--- | :--- |
| `[CLIENT_COMPANY_NAME]` | `{{ client_company_name }}` | Primary client legal corporate entity | `[CLIENT_COMPANY_NAME]` |
| `[CLIENT_SHORT_NAME]` | `{{ client_short_name }}` | Abbreviated acronym or division | `[CLIENT_ACRONYM]` |
| `[CLIENT_ADDRESS]` | `{{ client_address }}` | Registered business address | `[CLIENT_LEGAL_ADDRESS]` |
| `[VENDOR_COMPANY_NAME]` | `{{ vendor_company_name }}` | Primary implementation partner | `PT Metrodata Electronics Tbk` |
| `[VENDOR_SHORT_NAME]` | `{{ vendor_short_name }}` | Abbreviated vendor name | `Metrodata` |
| `[VENDOR_DIVISION]` | `{{ vendor_division }}` | Specialized consulting practice | `Data & AI Modernization Practice` |

### B. Project Governance & Contractual Slugs
| Authoritative Slug | Jinja2 Token (`.docx`) | Description | Example Default |
| :--- | :--- | :--- | :--- |
| `[PROJECT_NAME]` | `{{ project_name }}` | Formal engagement title | `[ENTERPRISE_DATA_PROJECT]` |
| `[PROJECT_CODE]` | `{{ project_code }}` | PMO tracking identifier | `[ENG-2026-001]` |
| `[CONTRACT_NUMBER]` | `{{ contract_number }}` | Legal PKS / SOW contract number | `[PKS-METRO-2026-XXXX]` |
| `[MILESTONE_NAME]` | `{{ milestone_name }}` | Current deliverable milestone | `Milestone 1` |
| `[BAST_NUMBER]` | `{{ bast_number }}` | Official acceptance certificate ID | `[BAST-M1-2026-XXXX]` |
| `[REPORT_DATE]` | `{{ report_date }}` | Publication date | `September 2026` |
| `[REPORTING_PERIOD]` | `{{ reporting_period }}` | Progress reporting timeframe | `[START_DATE] - [END_DATE]` |

### C. RACI Governance & Personnel Slugs
| Authoritative Slug | Jinja2 Token (`.docx`) | Description |
| :--- | :--- | :--- |
| `[CLIENT_SPONSOR_NAME]` | `{{ client_sponsor_name }}` | Client Executive Sponsor (Steering Committee) |
| `[CLIENT_SPONSOR_TITLE]` | `{{ client_sponsor_title }}` | Client Sponsor Job Title |
| `[CLIENT_PM_NAME]` | `{{ client_pm_name }}` | Client Project Manager (PMO) |
| `[CLIENT_BPO_LEAD]` | `{{ client_bpo_lead }}` | Business Process Owner Lead |
| `[CLIENT_IT_LEAD]` | `{{ client_it_lead }}` | Enterprise IT & Infrastructure Lead |
| `[VENDOR_PARTNER_NAME]` | `{{ vendor_partner_name }}` | Metrodata Engagement Partner |
| `[VENDOR_PM_NAME]` | `{{ vendor_pm_name }}` | Metrodata Project Manager |
| `[LEAD_ARCHITECT_NAME]` | `{{ lead_architect_name }}` | Solution / Platform Lead Architect |

---

## 3. Architecture & Execution Blueprint

### Phase 1: Centralized Slug Catalog (`src/core/slug_registry.py`)
- Define a single immutable dictionary and Pydantic model (`EngagementContext`) holding all supported slugs with regex boundary matchers (`r"\[CLIENT_COMPANY_NAME\]"`).
- Provide bi-directional converters between YAML keys, Jinja2 tokens, and uppercase slide slugs.

### Phase 2: Dynamic Pre-Render Substitution Middleware
- **PPT Engine (`src/ppt_engine/`):**  
  Add an automatic token substitution pass in `ConsultingDeckBuilder.save()` and `ReferenceDeckBuilder.save()` that walks all text shapes and swaps declared slugs with engagement parameters.
- **DOCX Engine (`src/docx_engine/`):**  
  Ensure `template_stamper.py` validates required keys against `EngagementContext`.
- **XLSX Engine (`src/xlsx_engine/`):**  
  Apply cell-level string replacement before saving reporting spreadsheets.

### Phase 3: Automated PII Leak Linter (`bench pii audit`)
- Build a targeted CLI validator:
  ```bash
  uv run bench pii audit --path output/
  ```
  Scans all generated `.docx`, `.xlsx`, `.pptx`, and `.drawio` files for hardcoded legacy client names (*Toyota*, *Tsusho*, unapproved employee names) and reports pass/fail status before remote commit.

---

## 4. Acceptance Criteria
- [x] Reference slides updated to default to `[CLIENT_COMPANY_NAME]` across all templates.
- [ ] Central `slug_registry.py` created with comprehensive taxonomy.
- [ ] Automated regex sanitizer integrated into slide, document, and spreadsheet generators.
- [ ] Pre-commit PII audit command active in `bench` CLI.
