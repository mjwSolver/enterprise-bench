# Feature Specification: Default Bottom-Edge Container Label Policy (`BOTTOM_EDGE_CONTAINER_LABEL_POLICY`)

> **Repository:** `enterprise-bench` | **Subsystem:** Diagram Engine V2 (`src/ppt_engine/diagram_v2/`)  
> **Status:** Architecture Designed • Backlog Queued  
> **Target Files:** [`models.py`](../../src/ppt_engine/diagram_v2/models.py), [`pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py), [`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py), [`svg_compiler.py`](../../src/ppt_engine/diagram_v2/svg_compiler.py), [`drawio_compiler.py`](../../src/ppt_engine/diagram_v2/drawio_compiler.py)

---

## 1. Problem Statement & Empirical Defect Evidence

In architectural system topologies and multi-tier swimlane visualizations, placing container zone labels at the top boundary edge creates systemic visual collisions, structural crowding, and horizontal routing deadlocks across three primary failure modes:

1. **Top-Edge Header & Subtitle Descender Crowding:**
   When container boundaries extend across the full canvas height ($y=1.30''$ to $y=7.25''$ on a $13.333'' \times 7.50''$ 16:9 slide canvas), placing container labels at the top edge ($y = \text{box}.y + 0.08'' \approx 1.38''$) positions uppercase tracking text immediately adjacent to the action title and subtitle descenders ($y \in [0.28'', 1.25'']$). This compresses the vertical buffer between slide-level navigation and diagram-level containment to $< 0.13''$, violating visual hierarchy and canvas breathing room.

2. **Cross-Boundary Ingress & Egress Connector Collisions:**
   Architectural dataflows naturally enter full-height swimlanes near their upper third (e.g., ingress requests from users or client runtimes). In [`proposed_aws_lambda_expanded.yaml`](../../specs/diagrams/proposed_aws_lambda_expanded.yaml) and [`cdsw_expanded.yaml`](../../specs/diagrams/cdsw_expanded.yaml):
   - Ingress flow `flow_user_to_exe` (`"1. Trigger"`, $y \approx 2.40''\text{--}2.63''$) and cross-boundary API flow `flow_send_api` (`"2. REST Request"`, $y \approx 3.87''\text{--}4.07''$) traversed boundary corridors where top-aligned labels (`USER ORIGIN`, `LOCAL DEVICE`, `AWS CLOUD`) produced severe visual interference.
   - When container labels and tag badges (`tag_badge: "CLOUDERA CML"`, `tag_badge: "AWS CLOUD"`) occupied the top $0.50''$ strip of the container, ingress arrows either crossed directly over the label text or required unnatural downward jog detours.

3. **Empirical Evidence & Corridor Reclaim:**
   Empirical benchmarking during the layout refactoring of `cdsw_expanded.yaml` and `proposed_aws_lambda_expanded.yaml` demonstrated that migrating full-canvas swimlanes from top alignment to bottom-edge positioning (`vertical_align: "bottom"`, $y = \text{box}.y2 - 0.32''$):
   - **Immediately opened an unobstructed $0.55''$ horizontal corridor** ($y \in [1.30'', 1.85'']$) across the entire top edge of the architecture canvas.
   - Allowed ingress connectors (`"1. Trigger"`, `"2. REST Request"`, `"3. Invoke"`) to route cleanly across zone boundaries without collision or artificial clearance padding.
   - Maintained clean separation between slide-level title/subtitle typography and diagram component geometry.

4. **Ad-Hoc Manual Declaration Fragility:**
   Currently, [`ContainerSpec`](../../src/ppt_engine/diagram_v2/models.py) hardcodes `vertical_align: str = "top"`. Slide authors must manually supply `vertical_align: "bottom"` on every swimlane. When omitted, diagrams silently regress to cramped top-label collisions.

---

## 2. Architectural Specification & Policy Heuristics

### 2.1 Geometric Height Threshold Heuristic ($h \ge 4.0\text{in}$)

Container labels are classified dynamically by container bounding-box height:

$$\text{resolved\_vertical\_align} = \begin{cases} 
\text{explicit\_override} & \text{if } \text{vertical\_align is declared in YAML} \\
\text{"bottom"} & \text{if } h \ge 4.0'' \text{ (full-canvas swimlanes \& macro-zones)} \\
\text{"top"} & \text{if } h < 4.0'' \text{ (compact sub-containers \& inner cards)}
\end{cases}$$

- **Macro Swimlanes ($h \ge 4.0''$):** Full-height boundaries (`group_user` at $h=5.92''$, `group_device` at $h=5.92''$, `group_aws` at $h=4.10''$, `group_backend` at $h=5.95''$) automatically anchor their labels to the bottom edge (`y = box.y2 - 0.32''` in PPTX, `ly = box.y2 - 16.0px` in SVG).
- **Nested / Compact Sub-Containers ($h < 4.0''$):** Internal grouping boxes (e.g. `group_safe_checker` at $h=3.50''$ or localized micro-service clusters) remain top-aligned (`vertical_align: "top"`) to preserve conventional card-header semantics without colliding with macro-swimlane bottom labels.

### 2.2 Horizontal Alignment Standard (Isolated vs. Structured)

Horizontal text alignment follows topological containment semantics:

| Container Archetype | Structural Classification | Default `align` | Visual Rationale & Clearance Rule |
| :--- | :--- | :---: | :--- |
| **Isolated Origin Swimlane** | Standalone peripheral column ($w \le 2.0''$, single vertical node stack) | `center` | Centers label relative to narrow pillar (e.g., `group_user` / `USER ORIGIN` at $w=1.60''$); balances whitespace on both sides. |
| **Structured / Multi-Column Swimlane** | Multi-node system zone ($w > 2.0''$, nested sub-containers) | `left` | Anchors label to the left border ($x = \text{box}.x + 0.20''$ in PPTX, $lx = \text{box}.x + 20.0\text{px}$ in SVG); aligns with Western reading order and prevents interference with right-hand egress connectors. |
| **Egress Sink / Target Boundary** | Terminal consumer or external egress boundary | `left` (or `right` if explicit) | Anchors to bottom-left; right-edge is reserved for optional status/environment tag badges (`tag_badge`). |

### 2.3 Bottom-Edge Obstruction Bypass & Segment Clamping

When bottom-anchored entity cards, database cylinders, or low-altitude connectors occupy the bottom boundary edge, bottom labels must not overlap shapes.

1. **Obstruction Detection:**
   An obstacle is flagged if any node bounding box $[x_n, y_n, w_n, h_n]$ or horizontal flow segment intersects the bottom label footprint:
   $$\text{Zone}_{\text{bottom\_label}} = [x_{\text{label\_min}}, x_{\text{label\_max}}] \times [y2_{\text{container}} - 0.40'', y2_{\text{container}}]$$
2. **Segment Clamping & Shifting Heuristic:**
   - In [`proposed_aws_lambda_expanded.yaml`](../../specs/diagrams/proposed_aws_lambda_expanded.yaml), `node_dbx` (Databricks database cylinder, $x=10.55'', y=5.65'', w=1.80'', h=1.40''$) sits directly adjacent to the bottom edge of `group_aws` ($y2 = 5.40''$).
   - A centered label would collide with the database cylinder body or its incoming flows.
   - **Clamping Rule:** The compiler identifies visible contiguous segments along the bottom border:
     $$\text{Segment}_{\text{left}} = [x_{\text{container}}, x_{\text{obstacle\_min}}], \quad \text{Segment}_{\text{right}} = [x_{\text{obstacle\_max}}, x2_{\text{container}}]$$
     The label clamps to the widest visible border segment ($x_{\text{left\_segment}} = 9.95''$ inside `group_aws`), shifting leftward with $0.20''$ margin from the container boundary.

### 2.4 Multi-Compiler Normalization Contract

All four compilation targets and the headless geometric auditor share identical resolution semantics:

- **[`models.py`](../../src/ppt_engine/diagram_v2/models.py):**
  Add helper methods to `ContainerSpec`:
  ```python
  def resolved_vertical_align(self) -> str:
      if self.vertical_align is not None and self.vertical_align in ("top", "bottom", "middle"):
          return self.vertical_align
      return "bottom" if self.h >= 4.0 else "top"

  def resolved_align(self) -> str:
      if self.align is not None and self.align in ("left", "center", "right"):
          return self.align
      return "center" if self.w <= 2.0 else "left"
  ```
- **[`pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py):**
  ```python
  valign = c.resolved_vertical_align()
  align = c.resolved_align()
  label_y = (box.y2 - 0.32) if valign == "bottom" else (box.y + 0.08)
  label_x = self._resolve_container_label_x(c, box, estimated_text_w, align, valign)
  ```
- **[`svg_compiler.py`](../../src/ppt_engine/diagram_v2/svg_compiler.py):**
  Compute $ly = \text{box}.y2 - 16.0\text{px}$ when `valign == "bottom"` and $lx = \text{box}.x + 20.0\text{px}$ when `align == "left"`.
- **[`drawio_compiler.py`](../../src/ppt_engine/diagram_v2/drawio_compiler.py):**
  Emit `verticalAlign=bottom;spacingBottom=12;align=left;spacingLeft=18;` into the Draw.io XML style string.
- **[`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py):**
  Update Check #11 (`CONTAINER_LABEL_OCCLUSION`) to construct the collision bounding box based on `c.resolved_vertical_align()` and `c.resolved_align()`.

---

## 3. System Guardrails (Preventing Negative Side Effects)

1. **Strict Respect for Explicit Overrides:**
   The policy is an intelligent default heuristic. If a YAML author explicitly writes `vertical_align: "top"` or `align: "center"` on an $h \ge 4.0''$ container, the compiler MUST strictly respect the author's declaration without emitting linter warnings.
2. **Decoupled Tag Badge Positioning:**
   `tag_badge` elements (e.g. `"CLOUDERA CML"`, `"AWS CLOUD"`) serve as distinct status pills and must remain independently positioned. A bottom-aligned container label does not force the tag badge to the bottom; tag badges remain in the top-right corner ($x = \text{box}.x2 - w_{\text{badge}} - 0.20''$, $y = \text{box}.y + 0.12''$) unless explicitly re-anchored, maintaining balanced visual framing.
3. **Bidirectional Reconciler Determinism:**
   Reverse synchronization (`PPTXDiagramDecompiler` in [`reconciler.py`](../../src/ppt_engine/diagram_v2/reconciler.py)) must identify bottom-edge text boxes (`tb.name = f"container:{c.id}:label"`) and emit `vertical_align: "bottom"` into the reconciled YAML only if it differs from the height-derived default, avoiding unnecessary YAML churn.

---

## 4. Implementation & Normalization Checklist

- [ ] **Core Schema & Model Helper (`models.py`):**
  - Add `resolved_vertical_align()` with $h \ge 4.0''$ threshold to [`ContainerSpec`](../../src/ppt_engine/diagram_v2/models.py).
  - Add `resolved_align()` with $w \le 2.0''$ threshold to [`ContainerSpec`](../../src/ppt_engine/diagram_v2/models.py).
- [ ] **PPTX Compiler Refactor (`pptx_compiler.py`):**
  - Replace raw `c.vertical_align` access with `c.resolved_vertical_align()`.
  - Implement `_resolve_container_label_x()` with bottom-edge obstruction detection and horizontal clamping against adjacent child/foreign shapes.
- [ ] **SVG & Draw.io Compilers Alignment (`svg_compiler.py`, `drawio_compiler.py`):**
  - Update [`svg_compiler.py`](../../src/ppt_engine/diagram_v2/svg_compiler.py) to consume resolved alignment helpers.
  - Update [`drawio_compiler.py`](../../src/ppt_engine/diagram_v2/drawio_compiler.py) to emit resolved XML cell style attributes.
- [ ] **Headless Auditor Check #11 Upgrade (`auditor.py`):**
  - Update `_check_container_label_occlusions()` and `_check_container_padding()` in [`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py) to audit the dynamic bottom-edge label zone against child nodes, database cylinders, and flow crossings.
- [ ] **Declarative Spec Normalization:**
  - Verify and normalize container definitions in [`cdsw_expanded.yaml`](../../specs/diagrams/cdsw_expanded.yaml) and [`proposed_aws_lambda_expanded.yaml`](../../specs/diagrams/proposed_aws_lambda_expanded.yaml).
