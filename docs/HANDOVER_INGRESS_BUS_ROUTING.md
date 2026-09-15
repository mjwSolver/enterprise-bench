# HANDOVER: Ingress Bus & Edge Bundling Architecture for Diagram Engine

> **Target Role:** Core Platform Engineer / Engine Developer (`enterprise-bench-dev`)  
> **Topic:** Clean Orthogonal Trunk Routing & Bus Topology for Multi-Column Architecture Diagrams  
> **Status:** Ready for Immediate Implementation  
> **Target Subsystem:** `src/ppt_engine/diagram_engine.py` (`HierarchicalLayoutEngine`, `DiagramRenderer`)

---

## 1. Executive Summary & Problem Context

In our columnar diagram architecture (`flowchart LR`, where subgraphs represent sequential lifecycle stages such as *Event Ingress*, *Streaming Core*, and *Data Lakehouse*), multiple upstream nodes frequently converge into a single downstream ingress component:
* **Example:** 4 distinct source nodes (`Mobile Loyalty App`, `In-Store POS`, `E-Commerce Webhooks`, `SAP ERP CDC`) all route to `AWS API Gateway` and `Apache Kafka`.

### The Visual Defect ("Mess of Cables")
Currently, `HierarchicalLayoutEngine` and `DiagramRenderer` in [`src/ppt_engine/diagram_engine.py`](../src/ppt_engine/diagram_engine.py) calculate orthogonal Manhattan routes (`L`-shaped segments) **independently for every individual edge**:
1. Each edge generates its own vertical drop and horizontal turn within the narrow inter-column channel (~125 px width).
2. Multiple lines run parallel with awkward micro-offsets or directly overlap, creating visual clutter and confusing crossings.
3. Downstream arrows converge at the exact same connector anchor, creating a thick, tangled blob of arrowhead artifacts.

```
[ CURRENT NAIVE ROUTING: Cluttered "Mess of Cables" ]
Column 1 (Sources)           Gutter Channel             Column 2 (Streaming)
+--------------------+
| Mobile App         |───────┐
+--------------------+       │
+--------------------+       │  ┌───────────────────────>+--------------------+
| In-Store POS       |───────┼──┼───────────────────────>| AWS API Gateway    |
+--------------------+       │  │                        +--------------------+
+--------------------+       │  │
| Webhooks           |───────┼──┘
+--------------------+       │
+--------------------+       │
| SAP ERP CDC        |───────┘
+--------------------+
(4 overlapping, zig-zagging orthogonal lines fighting for space in the gutter)
```

---

## 2. Target Design Pattern: The Ingress Bus Architecture

Borrowed from hardware schematics and high-end enterprise network diagrams, the solution is a **Dedicated Inter-Column Ingress Bus (Trunk Line)**.

When $N \ge 2$ nodes from an upstream columnar subgraph target the same node (or cluster) in the adjacent downstream subgraph, the routing engine must consolidate the individual paths into a single shared vertical highway.

```
[ TARGET INGRESS BUS: Clean Enterprise Trunk Routing ]
Column 1 (Sources)           Gutter Channel             Column 2 (Streaming)
+--------------------+
| Mobile App         |───● (Tap)
+--------------------+   │
+--------------------+   │
| In-Store POS       |───● (Tap)
+--------------------+   │  Vertical Bus Trunk
+--------------------+   │  (Single clean highway)
| Webhooks           |───● (Tap)        Single Ingress Arrow
+--------------------+   │─────────────────────────────────►+--------------------+
+--------------------+   │                                  | AWS API Gateway    |
| SAP ERP CDC        |───● (Tap)                            +--------------------+
+--------------------+
```

### Key Visual Characteristics
1. **Feeder Taps:** Short horizontal stubs emerging from the right-center of each source card to the bus line ($X_{\text{tap}} = X_{\text{node}} + W_{\text{node}} \rightarrow X_{\text{bus}}$).
2. **Junction Dots (Optional / Configurable):** A subtle circular node ($r=2.5\text{px}$, matching edge stroke color) at each tap-to-bus intersection.
3. **Single Trunk Ingress:** Exactly **one** horizontal connector travels from the bus line into the target card anchor, with a single sharp arrowhead.
4. **Zero Overlaps:** Eliminates 3 redundant parallel vertical lines and 3 duplicate arrowhead collisions.

---

## 3. Technical Architecture & File Modification Points

All required logic lives inside [`src/ppt_engine/diagram_engine.py`](../src/ppt_engine/diagram_engine.py).

### A. Bus Group Detection in `HierarchicalLayoutEngine`
In `_compute_subgraph_columnar_layout()` or a new helper `_bundle_columnar_edges()`:

1. **Analyze Adjacency:** Group edges by `(source_subgraph_id, target_node_id)`.
2. **Threshold Trigger:** If `len(grouped_edges) >= 2`, mark this cluster as a candidate for `IngressBus`.
3. **Calculate Bus Geometry:**
   $$\text{bus\_x} = \text{source\_col\_right} + \frac{\text{gutter\_width}}{2}$$
   $$\text{bus\_y\_min} = \min(y_{\text{source\_taps}})$$
   $$\text{bus\_y\_max} = \max(\max(y_{\text{source\_taps}}), y_{\text{target}})$$

### B. Representation in Draw.io XML (`mxGraphModel`)
When exporting to `.drawio` XML:
* **Option 1 (Native mxGraph Trunk):** Use a hidden junction waypoint cell (`<mxCell id="bus_ingress_1" vertex="1" style="ellipse;fillColor=#64748B;strokeColor=none;" .../>`). Each source connects to the junction cell, and a single edge connects the junction cell to the target.
* **Option 2 (Custom Waypoint Routing):** Express the trunk in standard Draw.io `<mxGeometry relative="1" as="geometry"><Array as="points"><mxPoint x="..." y="..."/></Array></mxGeometry>`.

### C. Headless SVG Renderer (`DiagramRenderer.render_svg`)
When rasterizing directly via Cairo/SVG:
* Emit feeder paths:
  ```xml
  <!-- Feeder taps from source nodes to bus -->
  <path d="M {node_right} {node_center_y} L {bus_x} {node_center_y}" stroke="#64748B" stroke-width="2"/>
  <circle cx="{bus_x}" cy="{node_center_y}" r="2.5" fill="#64748B"/>
  ```
* Emit the continuous bus backbone:
  ```xml
  <!-- Shared vertical trunk -->
  <path d="M {bus_x} {bus_y_min} L {bus_x} {bus_y_max}" stroke="#64748B" stroke-width="2"/>
  ```
* Emit the single ingress arrow into the downstream card:
  ```xml
  <!-- Clean single ingress into gateway -->
  <path d="M {bus_x} {target_center_y} L {target_left} {target_center_y}" stroke="#64748B" stroke-width="2" marker-end="url(#arrow)"/>
  ```

---

## 4. Implementation Steps for the Next Agent

### Step 1: Add `IngressBus` Data Structure in `diagram_engine.py`
```python
@dataclass
class IngressBus:
    id: str
    source_node_ids: List[str]
    target_node_id: str
    bus_x: float
    y_min: float
    y_max: float
    target_y: float
    has_junction_dots: bool = True
```

### Step 2: Implement Bundling Detection in Layout Engine
* Add `_detect_and_route_buses(self, diagram: ParsedDiagram) -> Tuple[ParsedDiagram, List[IngressBus]]`.
* Filter standard independent edges so they are not rendered twice.

### Step 3: Update `DiagramRenderer` SVG Generation
* Render buses before or after standard edges.
* Support rounded corners (`rx/ry` or chamfered turns) where the horizontal taps meet the vertical bus.

### Step 4: Verification & Golden Presentation Stamping
1. Re-run `output/proj-xyz/diagrams/xyz_platform_architecture.drawio` compilation.
2. Re-export `01_ingestion_streaming.png` and `.svg`.
3. Re-generate `01_Project_XYZ_Executive_Strategy_Deck_BrickRed.pptx`.
4. Launch PowerPoint using Desktop Review Protocol:
   ```bash
   open -a "Microsoft PowerPoint" "output/proj-xyz/presentations/01_Project_XYZ_Executive_Strategy_Deck_BrickRed.pptx" && osascript -e 'tell application "Microsoft PowerPoint" to activate'
   ```

---

## 5. Strict Guardrails & Repository Rules

1. 🚨 **ZERO INTERMEDIATE UNIT TESTING:**  
   Do **NOT** run `pytest` or `uv run pytest`. Verify strictly via manual Python scripts and visual inspection of exported SVG/PNGs.
2. **Non-Breaking Fallback:**  
   If a diagram is not columnar (`flowchart TD` or arbitrary graph), preserve the existing Manhattan routing without regressions.
3. **Environment:**  
   Always run Python via `uv run python <script>`.

---

## 6. Definition of Done (Acceptance Criteria)

- [ ] `01_ingestion_streaming.svg` shows a single vertical trunk line in the gutter between Column 1 and Column 2 instead of 4 separate lines.
- [ ] Exactly 1 clean arrow enters `AWS API Gateway` (and 1 enters `Apache Kafka` if branched).
- [ ] Slide 4 of `01_Project_XYZ_Executive_Strategy_Deck_BrickRed.pptx` displays the bundled diagram with zero line tangling.
- [ ] Presentation fits cleanly inside the container card without overflowing the footer ($Y \le 6.80"$).
