# Enterprise Workbench — Feature Backlog & Future Roadmap

> **Repository:** `enterprise-bench` | **Status:** Active Roadmap & Architecture Queue  
> **Index:** [`docs/INDEX.md`](docs/INDEX.md) | **Handover Ledger:** [`HANDOVER.md`](HANDOVER.md)

---

## 1. Active Architecture & Engineering Queue

### ⚡ Feature: Single-Command Atomic Desktop Hot-Reload (`--target & --pop`)
- **Scope:** Single-command workflow (`uv run bench diagram v2 compile --target <deck.pptx> --slide <num> --pop`) integrating Tier 1 preflight audits, AppleScript PowerPoint inspection/close, atomic OpenXML single-slide replacement, and instant macOS desktop activation.
- **Architecture Spec:** [`docs/backlog/atomic_desktop_hot_reload.md`](docs/backlog/atomic_desktop_hot_reload.md)
- **Status:** Architecture Designed • Backlog Queued

### 📐 Feature: Consulting Presentation Generator Deep Integration
- **Scope:** Backport Diagram Engine V2 declarative compiler into consulting presentation builders (`src/ppt_engine/slide_builders.py`).
- **Target:** Eliminate imperative python-pptx coordinate drafting in favor of embedding reusable declarative YAML topology blocks directly in consulting deck templates.
- **Status:** Design Queued

### 🏛 Feature: Multi-Track Enterprise Template Harvesting
- **Scope:** Expand declarative consulting architecture topologies under `specs/diagrams/` (Medallion Architecture, Active-Active DR, Streaming CDC Telemetry).
- **Status:** Scoping Queued

### 🔍 Feature: Tier 2 Adversarial Visual QA Perceptual Scanner Expansion
- **Scope:** Expand `bench diagram v2 visual-qa` heuristic computer vision rules with automated color contrast ratio validation (WCAG AA $4.5:1$ threshold for text) and multi-resolution font legibility scanners.
- **Status:** Backlog Queued

---

## 2. Parked & Deferred Initiatives

### 🛡️ Feature: Zero-History Repository Sanitization & Internal Distribution (`AIML-DAI`)
- **Scope:** Clean, PII-free downstream distribution of `enterprise-bench` to the `AIML-DAI` organization without exposing historical commit graphs.
- **Dedicated Strategy & Audit Register:** [`docs/backlog/PII_CLEARING_BACKLOG.md`](docs/backlog/PII_CLEARING_BACKLOG.md).
- **Status:** Parked (Deferred pending clearance audit)

---

## 3. Recently Completed Milestones (Archived from Active Queue)

- **Autonomous PPTX File Watcher & Reverse Geometric Sync (`bench diagram v2 watch`)** — Completed • Verified (Milestone 40). Spec: [`docs/specs/pptx_file_watcher_and_geometric_reconciliation.md`](docs/specs/pptx_file_watcher_and_geometric_reconciliation.md).
- **Typographic Scale & Font Size Consistency Checker (`TYPOGRAPHIC_SCALE_DRIFT`)** — Completed • Verified (Milestone 39). Check #14. Spec: [`docs/backlog/typographic_scale_consistency_checker.md`](docs/backlog/typographic_scale_consistency_checker.md).
- **Elastic Typography Auto-Fill for Execution Cards (`ELASTIC_TYPOGRAPHY_AUTOFILL`)** — Completed • Verified (Milestone 39). Check #15. Spec: [`docs/backlog/elastic_typography_autofill.md`](docs/backlog/elastic_typography_autofill.md).
- **DeckHeaderContract & Multi-Slide Header Consistency Linter (`DECK_HEADER_DRIFT`)** — Completed • Verified (Milestone 38). Check #15. Spec: [`docs/backlog/deck_header_contract_and_linter.md`](docs/backlog/deck_header_contract_and_linter.md).
- **Default Bottom-Edge Container Label Policy (`BOTTOM_EDGE_CONTAINER_LABEL_POLICY`)** — Completed • Verified (Milestone 38). Spec: [`docs/backlog/default_container_label_policy.md`](docs/backlog/default_container_label_policy.md).
