# Backlog: Localization & Bilingual Deck Subsystem (`en` / `id`)

> **Status:** Open Backlog / Architecture & Strategy Specification  
> **Topic:** Multi-Language Delivery, English-to-Indonesian Translation Engine, Bilingual PMO Glossary, Local Enterprise Compliance  
> **Target Subsystems:** [`src/ppt_engine`](../src/ppt_engine), [`src/docx_engine`](../src/docx_engine), [`src/core`](../src/core), [`presets/deck_configs`](../presets/deck_configs)  
> **Applicability:** All consulting presentations, governance reference slides, legal contracts (PKS/BAST), and technical specifications.

---

## 1. Executive Summary & Problem Context

Enterprise consulting deliverables in the Indonesian corporate landscape operate under a distinct bilingual reality:
1. **Global Technology Stack in English:** Cloud, data architecture, and software blueprints natively operate in English (e.g., *Virtual Warehouses, Data Lakehouse, Zero-Copy Cloning, Cortex AI, ELT Pipelines, Role-Based Access Control*). Translating these terms into Indonesian often causes cognitive friction or ambiguity.
2. **Local Governance & Legal Mandates in Bahasa Indonesia:** Project sponsorship, steering committees, state-owned enterprise (BUMN) procurement, and private enterprise PMO teams frequently mandate formal **Bahasa Indonesia** for governance, acceptance criteria, contractual baselines, and deliverable sign-offs (supported by *UU No. 24 Tahun 2009* regarding official documentation).
3. **Current System Limitation:** All modern presentation generators (`src/ppt_engine/reference_slides.py`, `consulting_archetypes.py`) and YAML presets currently hardcode English text strings directly into Python method definitions and YAML configuration dictionaries.

```
+--------------------------------------------------------------------------------------------------+
|                                  CURRENT MONOLINGUAL REALITY                                     |
|  YAML Config: English Only  -->  Hardcoded Python Strings  -->  Pure English Presentation Slides  |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼ TARGET ARCHITECTURE
+--------------------------------------------------------------------------------------------------+
|                                BILINGUAL / LOCALIZATION ENGINE                                   |
|   Preset YAML (`locale: id`)  ──┐                                                                |
|                                 ├──>  Locale Resolver & Terminology Catalog  ──> Output Deck     |
|   Glossary (`locales/id.yaml`) ─┘     (Preserves Technical English + Indonesian Governance Flow) |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Bilingual Taxonomy: Hybrid Localization Strategy

Enterprise deliverables must avoid raw literal machine translation. The engine must enforce a **Hybrid Localization Pattern**:
- **Preserve English (Technical Terms):** Cloud components, tool names, architectural paradigms (*Snowflake Data Cloud, Streamlit, dbt, Virtual Warehouse, Iceberg Tables, REST Catalog, SSO/IAM*).
- **Translate into Formal Bahasa Indonesia (Governance & Flow):** Titles, action headlines, category trackers, procedural checklists, ownership roles, and legal sign-off terms.

### Standardized Enterprise PMO Translation Glossary

| English Source Term | Standardized Bahasa Indonesia (Baku / Konsultansi) | Context / Slide Usage |
| :--- | :--- | :--- |
| **Project Governance** | *Tata Kelola Proyek* | Category Tracker |
| **Organizational Structure** | *Struktur Organisasi & Eskalasi* | Category Tracker / Slide 2 |
| **Joint Steering Committee** | *Komite Pengarah Bersama (Steering Committee)* | Tier 1 Governance Node |
| **Project Sponsorship** | *Sponsor Eksekutif Proyek* | Executive Sponsorship |
| **Project Management Office (PMO)** | *Kantor Manajemen Proyek (PMO)* | Tier 2 Governance Node |
| **Business Process Owners (BPO)** | *Pemilik Proses Bisnis (BPO)* | Execution Pod |
| **Scope & Change Control** | *Pengendalian Ruang Lingkup & Perubahan* | Slide 3 Category Tracker |
| **Change Request (CR)** | *Permohonan Perubahan Lingkup (CR)* | CR Procedure |
| **Step 1: Identification & Request** | *Tahap 1: Identifikasi & Pengajuan* | CR Step 1 |
| **Step 2: Impact & Manday Scoping** | *Tahap 2: Penilaian Dampak & Estimasi Hari-Kerja* | CR Step 2 |
| **Step 3: Bi-Level Decision Gate** | *Tahap 3: Gerbang Keputusan Bertingkat* | CR Step 3 |
| **Step 4: Contract Baseline & Build** | *Tahap 4: Penyesuaian Kontrak & Implementasi* | CR Step 4 |
| **Submitted** | *Diajukan* | Step 1 Status Pill |
| **Evaluated** | *Dievaluasi* | Step 2 Status Pill |
| **Approved** | *Disetujui* | Step 3 Status Pill |
| **Implemented** | *Diimplementasikan* | Step 4 Status Pill |
| **Output Artifact** | *Artefak Keluaran* | Deliverable Linkage |
| **Procedural Checklist** | *Daftar Periksa Prosedural* | Action List |
| **Escalation Thresholds** | *Ambang Batas Eskalasi & Aturan Tata Kelola* | Bottom Callout Card |
| **Handover Acceptance Certificate** | *Berita Acara Serah Terima (BAST)* | Legal Contractual Deliverable |

---

## 3. Architectural Design & Implementation Blueprint

### Phase 1: Locale Dictionary Catalog (`presets/locales/`)
Create standardized YAML string catalogs:
```
presets/
  locales/
    en.yaml   # Canonical English reference dictionary
    id.yaml   # Formal Indonesian enterprise consulting dictionary
```

#### Example: `presets/locales/id.yaml`
```yaml
locale: id
name: "Bahasa Indonesia (Formal Enterprise)"

reference_slides:
  governance_org:
    tracker: "TATA KELOLA PROYEK | STRUKTUR ORGANISASI"
    title: "Matriks Tata Kelola Gabungan Memastikan Kejelasan Eskalasi dan Kepemilikan Pengiriman"
    subtitle: "Struktur proyek hierarkis menghubungkan komite pengarah eksekutif, pemimpin PMO, dan pod eksekusi khusus."
    tier1_header: "TINGKAT 1: KOMITE PENGARAH BERSAMA (SPONSOR PROYEK)"
    tier1_badge: "TATA KELOLA EKSEKUTIF"
    client_pmo_badge: "PMO KLIEN"
    vendor_pmo_badge: "PMO VENDOR"
    
  change_request:
    tracker: "TATA KELOLA PROYEK | PENGENDALIAN RUANG LINGKUP"
    title: "Prosedur Permohonan Perubahan Mengatur Penyesuaian Ruang Lingkup Melalui Gerbang Keputusan"
    subtitle: "Alur kerja tata kelola 4 tahap berurutan dengan ambang batas eskalasi bertingkat dan persetujuan legal."
    step_label: "TAHAP"
    statuses:
      submitted: "DIAJUKAN"
      evaluated: "DIEVALUASI"
      approved: "DISETUJUI"
      implemented: "DIIMPLEMENTASIKAN"
    checklist_label: "DAFTAR PERIKSA PROSEDURAL:"
    artifact_label: "ARTEFAK KELUARAN:"
    callout_header: "AMBANG BATAS ESKALASI PERMOHONAN PERUBAHAN & ATURAN TATA KELOLA"
```

### Phase 2: Python Locale Engine (`src/core/locale_engine.py`)
Implement a lightweight, non-breaking translation utility:
```python
class LocaleEngine:
    """Resolves localized copy strings with fallback to canonical English."""
    
    def __init__(self, locale: str = "en") -> None:
        self.locale = locale
        self._strings = self._load_catalog(locale)
        self._fallback = self._load_catalog("en")

    def t(self, keypath: str, default: Optional[str] = None) -> str:
        """Resolves dot-notated string key (e.g. 'reference_slides.change_request.statuses.approved')."""
        val = self._lookup(self._strings, keypath)
        if val is not None:
            return val
        fallback_val = self._lookup(self._fallback, keypath)
        if fallback_val is not None:
            return fallback_val
        return default or keypath
```

### Phase 3: Declarative YAML Integration
Allow any deck configuration to switch languages with a single parameter:
```yaml
deck_type: reference_slides
theme: metrodata
locale: id  # <-- Switches all slide headers, badges, and labels to formal Bahasa Indonesia
metadata:
  client_name: "[CLIENT_COMPANY_NAME]"
  vendor_name: "PT Metrodata Electronics Tbk"
```

---

## 4. Immediate Next Steps & Tracking

- [ ] **Milestone 1:** Establish `presets/locales/en.yaml` and `presets/locales/id.yaml` catalogs.
- [ ] **Milestone 2:** Implement `src/core/locale_engine.py` with dot-notation resolution and graceful fallback.
- [ ] **Milestone 3:** Wire `locale` argument into `ReferenceDeckBuilder` and `uv run bench ppt build-deck`.
- [ ] **Milestone 4:** Provide paired build targets:
  - `Enterprise_Reference_Master_Deck_EN.pptx`
  - `Enterprise_Reference_Master_Deck_ID.pptx`
