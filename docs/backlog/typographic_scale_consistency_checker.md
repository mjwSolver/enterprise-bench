# Feature Specification: Typographic Scale & Font Size Consistency Checker (`TYPOGRAPHIC_SCALE_DRIFT`)

> **Repository:** `enterprise-bench` | **Subsystem:** Diagram Engine V2 (`src/ppt_engine/diagram_v2/`)  
> **Status:** Implemented & Verified • Milestone 39  
> **Target Files:** [`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py), [`models.py`](../../src/ppt_engine/diagram_v2/models.py), [`pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py), [`svg_compiler.py`](../../src/ppt_engine/diagram_v2/svg_compiler.py), [`drawio_compiler.py`](../../src/ppt_engine/diagram_v2/drawio_compiler.py)

---

## 1. Problem Statement & Empirical Defect Evidence

Peer architectural components with identical or near-identical bounding boxes currently render at visibly mismatched font sizes within the same visualization due to three compounding mechanisms:

1. **Isolated Per-Card Greedy Shrinking (`PPTXCompiler._plan_card`):**
   Each card executes an isolated 16-iteration shrink loop (`t_pt` stepping down by `-0.5pt` from `12.5pt` to `9.5pt`, and `s_pt` by `-0.25pt` from `9.0pt` to `7.5pt`) whenever wrapped lines + icon exceed `region_h`. Two side-by-side peer cards with identical dimensions (`w=1.40in, h=1.30in`) render at different font sizes whenever one card has a slightly longer title or a kicker badge.
2. **Ad-Hoc Manual `title_pt` Drift in Declarative YAML Specs:**
   - [`specs/diagrams/proposed_aws_lambda_expanded.yaml`](../../specs/diagrams/proposed_aws_lambda_expanded.yaml): Inside `group_aws`, identical `1.40in × 1.30in` sibling cards declare `title_pt: 11.0` (`node_code`) next to `title_pt: 9.5` (`node_secrets`), while `node_api_gw` uses `10.5`, `node_dbx` uses `11.0`, `node_lambda` uses `12.0`, and `node_user`/`node_exe` omit `title_pt`.
   - [`specs/diagrams/cdsw_expanded.yaml`](../../specs/diagrams/cdsw_expanded.yaml): `node_model_serving` omits `title_pt` (`12.5pt` in PPTX) while sibling `node_task` (`Code`) hardcodes `title_pt: 16.0`, and standalone badges span four distinct font sizes (`7.0pt`, `7.5pt`, `8.0pt`, `8.5pt`).
   - [`specs/diagrams/databricks_jobs_api.yaml`](../../specs/diagrams/databricks_jobs_api.yaml): Primary entity cards fluctuate across `14.0pt` (`App 2`/`App 3`), `15.0pt` (`Code`/`Database`), `16.0pt` (`App 1`/`Cluster`), and `17.0pt` (`DBx Jobs API`).
3. **Cross-Compiler Default Divergence (`title_pt: None`):**
   When `title_pt` is omitted, `pptx_compiler.py` defaults to `12.5pt` (if $h \ge 1.15''$) or `11.0pt`, `auditor.py` estimates height at `12.0pt`, and `svg_compiler.py` / `drawio_compiler.py` default to `15.0px`. Mixing explicit `title_pt` overrides with `None` defaults creates severe visual jumps between PPTX and SVG/Draw.io outputs.

---

## 2. Architectural Design

### 2.1 Canonical 4-Tier Geometric Typographic Scale

Nodes and annotations are classified by their normalized physical bounding-box dimensions (in inches) into four deterministic tiers:

| Tier | Structural Classification | Geometric Threshold (Inches) | Canonical `title_pt` | Canonical `subtitle_pt` | Canonical `kicker_pt` |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Tier A** | Primary Entity / Service Card | $h \ge 1.15''$ and $w \ge 1.00''$ | `12.0 pt` | `9.0 pt` | `8.0 pt` |
| **Tier B** | Compact Card / Section Header Banner | $0.50'' \le h < 1.15''$ (or $h \ge 1.15'', w < 1.00''$) | `10.5 pt` | `8.5 pt` | `7.5 pt` |
| **Tier C** | Sequential Process / Micro-Step Pill | $h < 0.50''$ | `9.5 pt` | `8.0 pt` | — |
| **Tier D** | Connector Flow Pills & Tag Badges | Flow labels & standalone/container badges | `7.5 pt` (flow) / `8.0 pt` (badge) | — | — |

### 2.2 Peer Cohort Keying & Hero Exemption Rules

To avoid false positives in containers that intentionally mix headers, step pills, and decision cards (e.g., `group_safe_checker`), cohorts are keyed by **`(container_scope, geometric_tier)`** rather than `container_id` alone:

1. **Cohort Key:** `(node.container_id or "__root__", classify_geometric_tier(box_in.w, box_in.h))` plus a global cross-container tier check for Tier A primary entity cards.
2. **Hero / Focal Card Exemption:** A card is exempted from peer-cohort font locking if:
   - Its bounding-box area exceeds $1.75\times$ the median area of its peer cohort, **OR**
   - It acts as an expanded code/inspection callout (`align == "left"` and `valign == "top"` with $\ge 3$ bullet lines in `subtitle` or `bullets`).

### 2.3 Check #14: `TYPOGRAPHIC_SCALE_DRIFT` in `Tier1GeometricLinter`

Add `_check_typographic_scale_consistency()` to [`Tier1GeometricLinter`](../../src/ppt_engine/diagram_v2/auditor.py) with three sub-checks:

- **14a. Declared Cohort Spread (`WARNING` / `--strict` gate):**
  Flags any peer cohort where resolved `title_pt` values across non-exempt nodes differ by $> 0.5\text{pt}$ (e.g., `node_code` at `11.0pt` vs. `node_secrets` at `9.5pt` in `group_aws`).
- **14b. Effective Post-Shrink Drift (`WARNING`):**
  Simulates `_plan_card` line-wrapping and shrink iterations for every node. If a node's effective rendered font size drops $> 0.5\text{pt}$ below its cohort peers (or below `11.0pt` for Tier A cards) due to text crowding, emits a targeted diagnostic advising the author to widen the card or shorten the title/subtitle.
- **14c. Badge & Flow Pill Sprawl (`INFO` / `WARNING`):**
  Flags diagrams where `flows[*].font_pt` uses more than 1 distinct font size or `badges[*].font_pt` uses more than 2 distinct font sizes across the canvas.

### 2.4 Unified Compiler Default Helper

Add `NodeSpec.resolved_title_pt(w_in: float, h_in: float) -> float` in [`models.py`](../../src/ppt_engine/diagram_v2/models.py) so `pptx_compiler.py`, `svg_compiler.py`, `drawio_compiler.py`, and `auditor.py` share a single source of truth when `title_pt is None`.

---

## 3. System Guardrails (Preventing Negative Side Effects)

1. **Audit Instead of Auto-Shrinking Peer Cohorts:**
   `PPTXCompiler._plan_card` must **NOT** automatically force all peer cards down to `min(peer_t_pt)`. Auto-shrinking causes a single verbose card (`"Secret Management"`) to silently degrade the legibility of every clean peer card on the slide. Instead, surface the mismatch in `bench diagram v2 audit` so the cramped box or label is fixed at the root.
2. **Preserve Bidirectional Reconciler Determinism (`Topic 11`):**
   `PPTXDiagramDecompiler` and `DiagramReconciler` ([`reconciler.py`](../../src/ppt_engine/diagram_v2/reconciler.py)) rely on deterministic coordinate and text round-tripping. Keeping typographic enforcement in the declarative spec + linter avoids silent runtime font mutations during `bench diagram v2 reconcile`.

---

## 4. Implementation & Normalization Checklist

- [x] Add `classify_geometric_tier(w_in, h_in)` and `resolved_title_pt(w_in, h_in)` to [`src/ppt_engine/diagram_v2/models.py`](../../src/ppt_engine/diagram_v2/models.py).
- [x] Unify `title_pt is None` fallback across [`pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py), [`svg_compiler.py`](../../src/ppt_engine/diagram_v2/svg_compiler.py), [`drawio_compiler.py`](../../src/ppt_engine/diagram_v2/drawio_compiler.py), and [`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py).
- [x] Implement Check #14 (`TYPOGRAPHIC_SCALE_DRIFT` — 14a Declared Cohort Spread, 14b Post-Shrink Effective Drift, 14c Badge/Flow Sprawl) in [`src/ppt_engine/diagram_v2/auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py).
- [x] Normalize drifted `title_pt` and `font_pt` declarations in [`cdsw_expanded.yaml`](../../specs/diagrams/cdsw_expanded.yaml), [`proposed_aws_lambda_expanded.yaml`](../../specs/diagrams/proposed_aws_lambda_expanded.yaml), and [`databricks_jobs_api.yaml`](../../specs/diagrams/databricks_jobs_api.yaml), and recompile all 4 target formats.
