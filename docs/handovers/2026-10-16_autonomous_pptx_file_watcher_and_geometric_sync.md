# Milestone 40 — Autonomous PPTX File Watcher & Reverse Geometric Synchronization

> **Date:** October 16, 2026  
> **Repository:** `enterprise-bench` | **Subsystem:** Diagram Engine V2 (`src/ppt_engine/diagram_v2/watcher.py`, `src/ppt_engine/diagram_v2/reconciler.py`, `src/cli/diagram_v2.py`)  
> **Status:** COMPLETED & VERIFIED IN ENGINE & CLI  
> **Related Specs:** [`docs/specs/pptx_file_watcher_and_geometric_reconciliation.md`](../specs/pptx_file_watcher_and_geometric_reconciliation.md) | [`docs/specs/pptx_decompiler_and_yaml_reconciliation_engine.md`](../specs/pptx_decompiler_and_yaml_reconciliation_engine.md)

---

## 1. Executive Summary

Milestone 40 delivers the **Autonomous PPTX File Watcher & Reverse Geometric Synchronization Engine**, closing the bidirectional feedback loop between PowerPoint visual editing and declarative YAML topologies. Deliverable authors can now open a PowerPoint presentation, adjust card positions, resize boundaries, edit labels, or rearrange components visually, and simply press `Cmd+S`. The background watcher daemon intercepts the save event, debounces write bursts, decompiles the DrawingML slide, extracts geometric coordinate shifts, snaps altered coordinates to clean $0.05''$ grid increments, reconciles the YAML AST, and headlessly compiles companion artifacts (`.svg`, `.png`, `.drawio`) while suppressing cyclic write loops (`--skip-pptx`).

---

## 2. Key Architectural Deliverables

### A. Reverse Geometric Extraction & Snapping Engine (`reconciler.py`)
- **Multi-Element Coordinate Diffing:** Extended `DiagramReconciler` to measure live shape bounding boxes (`left`, `top`, `width`, `height`) for containers (`container:<id>`), nodes (`node:<id>`), badges (`badge:<id>`), and bullet lists (`bullet_list:<id>`).
- **Noise Threshold Gate:** Rejects micro-movements smaller than $\pm 0.02''$ ($1.9\text{ pt}$) to eliminate incidental mouse drag noise.
- **Grid Snapping:** Automatically rounds significant shifts ($\ge 0.02''$) to clean $0.05''$ ($3.6\text{ pt}$) grid increments, preventing floating-point drift and maintaining clean git diffs.
- **Unit Conversion Engine:** Built-in `_to_inches()`, `_to_spec_units()`, and `_snap_spec_coord()` maintaining mathematical precision across both inches and pixel-based canvas coordinate systems.
- **AST Persistence:** Seamlessly updates element dictionaries (`x`, `y`, `w`, `h`) in `raw_data` and dumps formatted YAML via `dump_diagram_yaml()`.
- **Structured Change Tracking:** Added `mutated_geometry` change category and `res.mutated_geometries` property to `ReconciliationResult`.

### B. Autonomous Daemon & Lock-File Monitor (`watcher.py`)
- **PowerPoint Lock-File Filtering:** Strictly ignores transient lock files prefixed with `~$` (e.g. `~$cdsw_expanded.pptx`).
- **Sliding Debounce Window:** Implements a configurable $500\text{ ms}$ sliding debounce window to ensure compound atomic saves are completely written and handles released.
- **Zip Central Directory Integrity Verification:** Tests file readiness via non-destructive `zipfile.ZipFile.namelist()` inspection before acquiring file handles.
- **Origin Suppression (`--skip-pptx`):** Automatically compiles companion formats (`.svg`, `.png`, `.drawio`) upon save without touching the `.pptx` presentation on disk, preventing infinite ping-pong write cascades.
- **Graceful Lifecycle Management:** Thread-safe `stop()` method and clean `KeyboardInterrupt` / SIGINT handling for instant termination without leaving orphaned daemons.

### C. Unified CLI Integration (`bench diagram v2 watch & reconcile`)
- **Daemon Command (`bench diagram v2 watch`):**
  ```bash
  uv run bench diagram v2 watch specs/diagrams/cdsw_expanded.yaml
  uv run bench diagram v2 watch specs/diagrams/cdsw_expanded.yaml --debounce 0.5 --snap 0.05
  ```
- **CLI Reconcile Expansion (`bench diagram v2 reconcile`):**
  Added `--snap`, `--threshold`, and `--skip-pptx` options, plus `[cyan]GEOMETRY[/cyan]` action badges and coordinate counts in the rich reconciliation summary table.

---

## 3. Verification & Compliance Evidence

- **Headless Pipeline Verification (`scratch/test_watcher_and_geometry.py`):**
  - Compiled baseline topology from `specs/diagrams/cdsw_expanded.yaml`.
  - Reconciled clean baseline: confirmed zero geometric drift.
  - Simulated human user moving `node_step_connect` by $+0.32''$ in PowerPoint: successfully detected mutation and snapped to clean $0.05''$ increment ($4.5'' \to 4.8''$).
  - Verified `skip-pptx` invariant: companion SVG regenerated while PPTX was protected from cyclic overwrites.
  - Verified lock file filtering: `~$*.pptx` dropped by event filter.
  - Live multi-threaded test: background thread intercepted save event, debounced write burst, and reconciled AST into memory.
- **Zero Intermediate Unit Testing Compliance:** Verified 100% headlessly via direct code execution and CLI invocations without running `pytest`.
