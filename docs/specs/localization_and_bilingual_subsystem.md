# Localization & Bilingual Subsystem Architecture (`en` / `id`)

## Executive Summary & Architectural Rationale
Enterprise engagements in the Indonesian market operate under a strict bilingual dichotomy:
1. **Governance, Legal & Project Administration:** Enterprise clients, steering committees, and corporate procurement demand formal Indonesian (*Bahasa Indonesia*) terminology for project governance, sign-offs, acceptance procedures (BAST), stakeholder matrices, and escalation procedures.
2. **Technology & Cloud Architecture:** Cloud data platforms, data engineering pipelines, and security topologies demand international English standard terminology (`Snowflake AI Data Cloud`, `dbt`, `Streamlit`, `Cortex AI`, `Virtual Warehouse`, `RBAC`, `IAM / SSO`, `Iceberg`, `DDL`, etc.) to prevent ambiguity, inaccurate literal translations, or vendor misalignments.

The **Localization & Bilingual Subsystem** provides a unified, deterministic framework spanning YAML translation catalogs, a high-performance locale engine, presentation engine integration, and CLI orchestration to produce paired bilingual deliverables (`en` and `id`).

---

## Subsystem Architecture & Components

```text
┌─────────────────────────────────────────────────────────────┐
│                    Declarative Configs                      │
│   presets/deck_configs/enterprise_reference_slides.yaml     │
│   presets/deck_configs/enterprise_reference_slides_id.yaml  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Locale Catalogs (YAML)                     │
│    presets/locales/en.yaml    presets/locales/id.yaml       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Locale Engine (src/core/locale_engine.py)       │
│  - get(key) / t(key, **kwargs)   - translate_term(term)     │
│  - get_dict(key) / get_list(key) - translate_hybrid(text)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│     Presentation Engine       │ │       Unified CLI         │
│  src/ppt_engine/              │ │  src/cli.py               │
│  - consulting_archetypes.py   │ │  - bench locale list      │
│  - reference_slides.py        │ │  - bench locale get       │
│  - ReferenceDeckBuilder       │ │  - bench locale translate │
└───────────────────────────────┘ └───────────────────────────┘
```

---

## 1. Static Locale Catalogs (`presets/locales/`)

Translation catalogs are stored as structured YAML dictionaries partitioned into canonical functional sections:
- `common`: Universal UI and metadata labels (`prepared_for`, `engagement_partner`, `date_classification`, `confidential_proprietary`, `page_number`, `status_pill`).
- `reference_slides`: Slide-specific content structures:
  - `cover`: Project title, subtitle, and tracker breadcrumbs.
  - `governance_org`: Dual-pillar tiers (Executive Steering Committee, Client PMO, Vendor Engagement, Delivery Tracks).
  - `change_request`: 4-stage pipeline phases (Step 1 to 4: Identification, Impact Scoping, Decision Gate, Contract Baseline), checklists, outputs, and escalation threshold callouts.
  - `platform_arch` & `data_pipeline`: Enterprise cloud platform trackers, action titles, and subtitles.
  - `corporate_equity_tree`: Multi-tier holding shareholding labels, parent company subtitles, and equity footnotes.
- `glossary`: Bidirectional enterprise consulting dictionary supporting acronym expansion and term normalization.

---

## 2. Core Locale Engine (`src/core/locale_engine.py`)

The `LocaleEngine` class provides lightweight, zero-dependency lookup, fallback mechanics, and hybrid phrase translation:

### Key Capabilities:
- **Cached Lazy Loading:** Locales are loaded once into memory via `_load_catalog(locale)`.
- **Dot-Notation Keypath Lookup:** `engine.get("reference_slides.governance_org.title")` traverses nested dictionaries safely without key errors.
- **Canonical English Fallback:** If a key is missing in the target locale (e.g. `id`), `engine.t(key)` automatically falls back to `en.yaml`, and finally to a provided default string.
- **Dynamic Variable Interpolation:** `engine.t("common.page_number", current="01", total="05")` interpolates placeholders cleanly.
- **Hybrid Sentence Translation (`translate_hybrid`):**
  - Scans sentences for known English enterprise governance terms and substitutes formal Indonesian equivalents.
  - Preserves technical cloud terms untouched.
  - Matches terms in descending order of phrase length to ensure multi-word phrases match before individual words.
  - Automatically matches base terms when parenthetical acronyms exist (e.g., matching `"Change Request"` from `"Change Request (CR)"`).

---

## 3. Presentation Engine Integration

### A. Cover Slide Parameterization (`src/ppt_engine/consulting_archetypes.py`)
Both `build_cover_slide` and `build_hero_cover_slide` accept explicit label parameters:
- `prepared_for_label`: Defaults to `"PREPARED FOR"` (`DISIAPKAN UNTUK` in `id`).
- `engagement_partner_label`: Defaults to `"ENGAGEMENT PARTNER"` (`MITRA PELAKSANA` in `id`).
- `date_classification_label`: Defaults to `"DATE / CLASSIFICATION"` (`TANGGAL & KLASIFIKASI` in `id`).
- `confidential_label`: Defaults to `"CONFIDENTIAL"` (`RAHASIA & HAK MILIK` in `id`).

### B. Reference Slide Localization (`src/ppt_engine/reference_slides.py`)
All archetype slide builders accept a `locale: str = "en"` parameter:
- `build_governance_org_structure_slide(prs, theme, ..., locale="id")`
- `build_change_request_procedure_slide(prs, theme, ..., locale="id")`
- `build_snowflake_platform_architecture_slide(prs, theme, ..., locale="id")`
- `build_snowflake_data_pipeline_slide(prs, theme, ..., locale="id")`
- `build_equity_corporate_tree_slide(prs, theme, ..., locale="id")`

When `locale != "en"`, default English strings for trackers, action titles, subtitles, process steps, checklist items, and callout boxes automatically swap to the active locale dictionary while allowing explicit config overrides.

---

## 4. CLI Commands & Workflow

### Inspecting & Translating via CLI:
```bash
# List all active locale catalogs and key counts
uv run bench locale list

# Retrieve a localized string by key
uv run bench locale get reference_slides.governance_org.title --locale id

# Execute hybrid translation on a sentence
uv run bench locale translate "Weekly Steering Committee must review the Change Request with the PMO" --to id
```

### Generating Paired Reference Master Decks:
```bash
# Build English Canonical Master Deck:
uv run bench ppt build-deck \
  -c presets/deck_configs/enterprise_reference_slides.yaml \
  -l en \
  -o output/presentations/Enterprise_Reference_Master_Deck_EN.pptx

# Build Indonesian Enterprise Master Deck:
uv run bench ppt build-deck \
  -c presets/deck_configs/enterprise_reference_slides_id.yaml \
  -o output/presentations/Enterprise_Reference_Master_Deck_ID.pptx
```

---

## 5. Standard Preserved Technology Vocabulary
The following technical tokens must remain in English across all translations:
- **Cloud Data Platform:** `Snowflake AI Data Cloud`, `Virtual Warehouse`, `Cortex AI`, `Snowpark`, `Horizon`, `Dynamic Tables`, `Streams & Tasks`, `Iceberg`, `Time Travel`.
- **Engineering & Analytics:** `dbt Core`, `dbt Cloud`, `Streamlit`, `SQL / DDL / DML`, `Kafka`, `CDC`, `ETL / ELT`, `S-curve`.
- **Infrastructure & Security:** `AWS S3`, `IAM / SSO`, `RBAC`, `TLS 1.3`, `AES-256`, `OAuth2`, `HashiCorp Vault`, `VPN / VPC`.
