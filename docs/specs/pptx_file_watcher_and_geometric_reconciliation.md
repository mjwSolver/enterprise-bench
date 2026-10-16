# Autonomous PPTX File Watcher & Reverse Geometric Synchronization

**Subsystem:** Diagram Engine V2 (`src/ppt_engine/diagram_v2/watcher.py`, `src/ppt_engine/diagram_v2/reconciler.py`)  
**Context:** Feature Backlog / Topic 12 Architecture  
**Status:** Canonical Engineering Specification & Architecture Runbook  
**Related Specs:** [`docs/specs/pptx_decompiler_and_yaml_reconciliation_engine.md`](pptx_decompiler_and_yaml_reconciliation_engine.md) | [`FEATURE_BACKLOG.md`](../../FEATURE_BACKLOG.md)

---

## 1. Executive Summary & Design Vision

In enterprise consulting workflows, consultants and deliverable authors make rapid, intuitive micro-adjustments directly within PowerPoint (e.g. dragging card boundaries, nudging heights, tweaking paddings, or updating labels).

Previously, these manual visual adjustments were at risk of being lost: because declarative YAML (`specs/diagrams/*.yaml`) acts as the deterministic source of truth, any subsequent CLI compilation (`uv run bench diagram v2 compile ...`) would overwrite the `.pptx` presentation with the declared YAML coordinates, wiping out in-situ human tweaks.

The **Autonomous PPTX File Watcher & Reverse Geometric Synchronization Engine** creates a frictionless bidirectional feedback loop:
1. An engineer or designer launches the watcher daemon in the background:
   ```bash
   uv run bench diagram v2 watch specs/diagrams/cdsw_expanded.yaml
   ```
2. The user edits shapes, text, or coordinates in PowerPoint and presses `Cmd+S`.
3. The daemon intercepts the save event, extracts structural and geometric changes (`left`, `top`, `width`, `height`), updates the source YAML specification on disk, and headlessly compiles companion formats (SVG, PNG, Draw.io) in real time.

---

## 2. System Architecture & Event State Machine

```
┌────────────────────────────────────────────────────────┐
│             Microsoft PowerPoint (macOS)               │
│          User modifies shape & hits Cmd+S              │
└──────────────────────────┬─────────────────────────────┘
                           │ Writes to disk
                           ▼
┌────────────────────────────────────────────────────────┐
│             Filesystem Event Monitor                   │
│  - Filters out temporary lock files ('~$*.pptx')       │
│  - Debounces rapid write events (500ms silence window) │
└──────────────────────────┬─────────────────────────────┘
                           │ Triggers on file close
                           ▼
┌────────────────────────────────────────────────────────┐
│         PPTXDiagramDecompiler (Geometric Extension)    │
│  - Extracts deterministic OpenXML names ('node:...', ) │
│  - Measures shape bounding boxes: (left, top, w, h)   │
│  - Compares against DiagramSpec AST in memory          │
│  - Detects threshold deltas: |Δ| >= 0.05" (4.8 pt)     │
│  - Snaps mutated coordinates to 0.05" grid increments  │
└──────────────────────────┬─────────────────────────────┘
                           │ Emits ReconciledChange records
                           ▼
┌────────────────────────────────────────────────────────┐
│                  DiagramReconciler                     │
│  - Updates YAML AST dictionary in memory               │
│  - Dumps beautifully formatted YAML to disk            │
└──────────────────────────┬─────────────────────────────┘
                           │ Triggers multi-target compilation
                           ▼
┌────────────────────────────────────────────────────────┐
│          Engine V2 Multi-Format Compiler               │
│  - Compiles Vector SVG (`.svg`)                        │
│  - Compiles High-DPI PNG (`.png`) via rsvg-convert     │
│  - Compiles Draw.io XML (`.drawio`)                    │
│  - SKIPS PPTX compilation (--skip-pptx) to prevent     │
│    cyclic write-trigger loops                          │
└────────────────────────────────────────────────────────┘
```

---

## 3. Core Technical Invariants & Edge Cases

### A. PowerPoint Lock-File Filtering (`~$`)
When saving changes, PowerPoint creates transient lock files prefixed with `~$` (e.g., `~$cdsw_job_execution_expanded.pptx`). The event filter must strictly drop all events matching:
```python
if path.name.startswith("~$") or path.suffix.lower() != ".pptx":
    return
```

### B. Write Event Debouncing
PowerPoint performs compound atomic writes (writing to a temp file, renaming, updating metadata). A sliding debounce window of $500\text{ ms}$ must elapse without new write events before acquiring the file handle to ensure the presentation is fully flushed and unlocked.

### C. Floating-Point Snapping & Git Hygiene
Manual mouse drags in GUI applications create erratic floating-point values (e.g., $h = 1.882194''$). To maintain clean git diffs:
- **Threshold Gate:** Coordinate shifts smaller than $\pm 0.02''$ ($1.9\text{ pt}$) are ignored as incidental drag noise.
- **Snapping Grid:** Significant shifts ($\ge 0.05''$) are snapped to $0.05''$ ($3.6\text{ pt}$) increments:
  $$\text{snapped\_coord} = \text{round}\left(\frac{\text{val}}{0.05}\right) \times 0.05$$

### D. Ping-Pong Loop Prevention (`--skip-pptx`)
If the reconciliation engine compiles a new `.pptx` on disk, the filesystem watcher would detect its own write and re-trigger reverse reconciliation infinitely. The watcher solves this via **origin suppression**:
- When reconciliation is triggered by a PPTX save, compilation runs with `--skip-pptx`.
- Companion formats (`.svg`, `.png`, `.drawio`) update instantly without touching the `.pptx` file.

---

## 4. CLI Contract & Interface

```bash
# Watch a specific diagram spec and its associated PPTX deliverable
uv run bench diagram v2 watch specs/diagrams/cdsw_expanded.yaml

# Watch with custom debounce and presentation target
uv run bench diagram v2 watch specs/diagrams/cdsw_expanded.yaml \
  --pptx doc_output/cdsw_job_execution/cdsw_job_execution_expanded.pptx \
  --debounce 0.5 \
  --snap 0.05
```
