# Enterprise Workbench — Feature Backlog & Future Roadmap

> **Repository:** `enterprise-bench` | **Status:** Active Roadmap & Architecture Queue  
> **Index:** [`docs/INDEX.md`](docs/INDEX.md) | **Handover Ledger:** [`HANDOVER.md`](HANDOVER.md)

---

## 1. Active Architecture & Engineering Queue

*(All queued backlog items from Milestone 42 / Tier 33 have been implemented and are awaiting final user sign-off.)*

---

## 2. Parked & Deferred Initiatives

### 🛡️ Feature: Zero-History Repository Sanitization & Internal Distribution (`AIML-DAI`)
- **Scope:** Clean, PII-free downstream distribution of `enterprise-bench` to the `AIML-DAI` organization without exposing historical commit graphs.
- **Dedicated Strategy & Audit Register:** [`docs/backlog/PII_CLEARING_BACKLOG.md`](docs/backlog/PII_CLEARING_BACKLOG.md).
- **Status:** Section 7 Remediation Completed & Verified (`/tmp/enterprise-bench-clean` Ready for Downstream Push)

---

## 3. Recently Completed Milestones (Awaiting Sign-Off / Archived from Active Queue)

- **Single-Command Atomic Desktop Hot-Reload (`--target & --pop`)** — Implemented • Pending Sign-Off (`powerpoint_desktop.py`, `replace_slide_in_presentation`, `bench diagram v2 compile --target --slide --pop`). Spec: [`docs/backlog/atomic_desktop_hot_reload.md`](docs/backlog/atomic_desktop_hot_reload.md).
- **2D Constraint & Flexbox Auto-Layout Solver (`layout_solver.py`)** — Implemented • Pending Sign-Off (`bench diagram v2 layout`, optional `box`/`x/y/w/h`, topological layering, corridor span enforcement). Spec: [`docs/backlog/diagram_v2_constraint_layout_solver.md`](docs/backlog/diagram_v2_constraint_layout_solver.md).
- **Mermaid-to-YAML AST Transpiler (`bench diagram v2 ingest`)** — Implemented • Pending Sign-Off (`mermaid_transpiler.py` reusing `MermaidParser` + auto-layout). Spec: [`docs/backlog/mermaid_to_yaml_transpiler.md`](docs/backlog/mermaid_to_yaml_transpiler.md).
- **Consulting Presentation Generator Deep Integration (`diagram_v2` archetype)** — Implemented • Pending Sign-Off (`build_diagram_v2_slide`, `ConsultingDeckBuilder.add_diagram_v2_slide`, `PitchDeckBuilder`, `ARCHETYPE_REGISTRY`).
- **Multi-Track Enterprise Template Harvesting** — Implemented • Pending Sign-Off (`template_medallion_architecture.yaml`, `template_active_active_dr.yaml`, `template_streaming_cdc_telemetry.yaml`, all passing `--strict` audit).
- **Remote Cloud Drift & Multi-Agent Race Condition Guard** — Implemented • Pending Sign-Off (`remote_guard.py`, `RemoteConflictError`, `bench stage push --cas`, `bench stage pin`, `bench stage merge-slide`, `bench stage preflight --remote-drift`, `bench diagram v2 watch --remote-drift`). Spec: [`docs/backlog/remote_cloud_drift_and_race_condition_guard.md`](docs/backlog/remote_cloud_drift_and_race_condition_guard.md).
- **Tier 2 Adversarial Visual QA Perceptual Scanner Expansion** — Implemented • Pending Sign-Off (`audit_wcag_and_legibility` for WCAG AA contrast & multi-resolution 1080p/720p legibility in `visual_verifier.py`).
- **In-Flight System Verification & Corridor Geometry Standard (`IN_FLIGHT_VERIFICATION_AND_CORRIDOR_GEOMETRY`)** — Completed • Verified (Milestone 41). Spec: [`docs/specs/in_flight_verification_and_corridor_geometry.md`](docs/specs/in_flight_verification_and_corridor_geometry.md).
- **Autonomous PPTX File Watcher & Reverse Geometric Sync (`bench diagram v2 watch`)** — Completed • Verified (Milestone 40). Spec: [`docs/specs/pptx_file_watcher_and_geometric_reconciliation.md`](docs/specs/pptx_file_watcher_and_geometric_reconciliation.md).
- **Typographic Scale & Font Size Consistency Checker (`TYPOGRAPHIC_SCALE_DRIFT`)** — Completed • Verified (Milestone 39). Check #14. Spec: [`docs/backlog/typographic_scale_consistency_checker.md`](docs/backlog/typographic_scale_consistency_checker.md).
- **Elastic Typography Auto-Fill for Execution Cards (`ELASTIC_TYPOGRAPHY_AUTOFILL`)** — Completed • Verified (Milestone 39). Check #15. Spec: [`docs/backlog/elastic_typography_autofill.md`](docs/backlog/elastic_typography_autofill.md).
