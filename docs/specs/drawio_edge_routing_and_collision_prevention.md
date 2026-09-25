# Architecture & Design Specification: Diagram Edge Routing & Collision Prevention

> **Target Role:** Core Platform Engineer / Diagram Engine Maintainer (`enterprise-bench-dev`, `enterprise-bench-ops`)  
> **Topic:** Dynamic Port Anchoring, Intermediate Obstacle Avoidance, Gutter Channel Routing, and Parity between Draw.io XML and Headless Vector SVG  
> **Status:** Enforced Architectural Standard  
> **Target Subsystems:** [`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py) (`DrawIOConverter`, `DiagramRenderer`), [`scripts/generate_drawio_single_slide.py`](../../scripts/generate_drawio_single_slide.py)  
> **Related Documents:** [`drawio_icon_system_architecture.md`](drawio_icon_system_architecture.md), [`ingress_bus_routing_architecture.md`](ingress_bus_routing_architecture.md), [`AGENTS.md`](../../AGENTS.md)

---

## 1. Executive Summary & The Visual Defect

In multi-column columnar architecture diagrams (`flowchart LR`, where subgraphs represent sequential enterprise tiers such as *Ingress*, *Analytics & Lakehouse*, and *Control Plane*), edges can navigate three distinct spatial relationships:
1. **Forward Inter-Column Hops:** Left-to-right connections between adjacent stages ($x_{\text{tgt}} > x_{\text{src}}$).
2. **Sequential Intra-Column Hops:** Top-to-bottom connections between cards within the same container.
3. **Cross-Tier Feedback / Governance Hops:** Returning or skipping edges that cross over intermediate columns or connect non-adjacent vertical cards.

### 1.1 The "Doubled Line Without Arrowhead" Defect

When authoring complex 3-tier topologies (e.g., the Cloudera Data Platform architecture in `scripts/generate_drawio_single_slide.py`), engineers observed severe visual distortions:
* **Doubled Vertical Lines:** Two parallel vertical lines rendered only $3\text{ px}$ apart running down the gap between cards in the middle column.
* **Missing Arrowheads:** The lines entered middle cards with **zero arrowheads**, appearing as broken connectors.
* **Overlapping Trunk Lines:** Multiple edges converged on top of one another at the bottom of the column.

```
[ THE DEFECT: Naive Interpolation & Multipath Superposition ]

Tier 1: Ingress              Tier 2: Analytics             Tier 3: Control
┌──────────────────┐        ┌────────────────────────┐    ┌────────────────────┐
│ Hub              │◄───────┼───────(midpoint 892)───┼────┤                    │
│                  │        │   Data Warehouse       │    │ Catalog            │
├──────────────────┤        │         │ 895   │ 892      ├────────────────────┤
│ Flow             │◄───────┼─────────┼───────┼──────┼────┤                    │
│                  │        │   Operational Database │    │ Repl               │
├──────────────────┤        │         │ 895   │ 892      ├────────────────────┤
│ Eng              │        │   Cloudera ML          │◄───┤ Console (Hub/Flow) │
└──────────────────┘        └────────────────────────┘    └────────────────────┘
                              ▲         ▲
                      DW-->AI (895)   Console-->Hub (892)
                     Passing behind    Passing behind
                     Operational DB    Operational DB
                     (NO arrowheads   (NO arrowheads
                      at OpDB!)        at OpDB!)
```

---

## 2. Root Cause Mechanics

The visual defect was not a single bug, but the superposition of two independent routing failures in [`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py) combined with a hardcoded port mapping in the Draw.io XML generator:

### Cause A: Midpoint Cross-Column Slicing
In `DiagramRenderer.render_svg()`, horizontal orthogonal routing was calculated using naive midpoint interpolation:
$$\text{mx} = \frac{x_{\text{src}} + x_{\text{tgt}}}{2}$$

When an edge connected Tier 3 (Control Plane, $x \approx 1323$) back to Tier 1 (Ingress, $x \approx 461$), the computed midpoint was:
$$\text{mx} = \frac{1323 + 461}{2} = 892.0$$

Because Tier 2 (Cloud Analytics & Storage) was centered at $x = 895.0$, **the vertical step segment $L(892, s_y) \rightarrow L(892, t_y)$ was drawn directly through the center of Tier 2**, slicing vertically through *Data Warehouse*, *Operational Database*, and *Cloudera ML*.

### Cause B: Vertical Obstacle Blindness
When an edge connected non-adjacent nodes in the same vertical column (e.g. `DW --> AI`, spanning row 1 to row 3):
```python
if is_vert and dy > 0:
    sx, sy = src.x + src.width / 2.0, src.y + src.height
    tx, ty = tgt.x + tgt.width / 2.0, tgt.y
    d_path = f"M {sx:.1f} {sy:.1f} L {tx:.1f} {ty:.1f}"
```
The renderer drew a single straight vertical line from row 1 down to row 3. Because *Operational Database* (row 2) was positioned directly between them with a solid fill, the card obscured the middle segment of the line. The exposed top segment (between row 1 and row 2) appeared as a vertical line entering *Operational Database* **without an arrowhead** (because its target was actually row 3).

### Cause C: The 3-Pixel Visual Overlap
In the gap between *Data Warehouse* and *Operational Database*:
* The `Console --> Hub` through-line ran vertically at $x = 892.0$.
* The `DW --> AI` through-line ran vertically at $x = 895.0$.
Because they were only $3\text{ px}$ apart, they appeared as an ugly, distorted "doubled line" with no terminating arrowheads.

### Cause D: Draw.io XML Hardcoded Ports
In `DrawIOConverter._build_edge_style()`, every edge in an `LR` flowchart was hardcoded with:
```python
style_parts.append("exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
```
This forced all edges—regardless of whether they traveled backward, downward, or upward—to exit the right face (`exitX=1`) and enter the left face (`entryX=0`). When opened in Draw.io GUI, backward and vertical edges looped erratically around cards.

---

## 3. The Three-Layer Guardrail Architecture

To permanently prevent this class of defects across all present and future diagrams, three systemic guardrails have been engineered into the core platform:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIAGRAM ENGINE GUARDRAIL ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Guardrail 1:   │       │   Guardrail 2:   │       │   Guardrail 3:   │
│   Dynamic Port   │       │Vertical Obstacle │       │ Intermediate SG  │
│  Directionality  │       │  Bypass Routing  │       │ Gutter Routing   │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ DrawIOConverter  │       │ DiagramRenderer  │       │ DiagramRenderer  │
│ Anchors based on │       │ Jogs 24pt around │       │ Shifts mx into   │
│ coordinate vector│       │ intermediate card│       │ inter-col gutter │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

### 3.1 Guardrail 1: Dynamic Port Directionality (`DrawIOConverter._build_edge_style`)

`DrawIOConverter` now inspects source and target node coordinates $(\Delta x, \Delta y)$ to determine the geometrically optimal connection faces:

```python
if src_node and tgt_node:
    dx = (tgt_node.x + tgt_node.width / 2.0) - (src_node.x + src_node.width / 2.0)
    dy = (tgt_node.y + tgt_node.height / 2.0) - (src_node.y + src_node.height / 2.0)
    is_vert = abs(dx) < max(src_node.width, tgt_node.width) * 0.45
    is_horiz = abs(dy) < max(src_node.height, tgt_node.height) * 0.45

    if is_vert:
        if dy > 0:
            style_parts.append("exitX=0.5;exitY=1;entryX=0.5;entryY=0;")  # Top-to-Bottom
        else:
            style_parts.append("exitX=0.5;exitY=0;entryX=0.5;entryY=1;")  # Bottom-to-Top
    elif is_horiz or abs(dx) >= abs(dy):
        if dx > 0:
            style_parts.append("exitX=1;exitY=0.5;entryX=0;entryY=0.5;")  # Forward (L-to-R)
        else:
            style_parts.append("exitX=0;exitY=0.5;entryX=1;entryY=0.5;")  # Backward (R-to-L)
    else:
        if dy > 0:
            style_parts.append("exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
        else:
            style_parts.append("exitX=0.5;exitY=0;entryX=0.5;entryY=1;")
```

**Result:** In Draw.io Desktop and web viewers, edges anchor cleanly to the nearest logical face, eliminating unnatural loops.

### 3.2 Guardrail 2: Vertical Obstacle Detection & Bypass (`DiagramRenderer.render_svg`)

When an edge connects two nodes vertically in the same column, `DiagramRenderer` checks the AST for any intervening node obstacles:

```python
if is_vert and dy > 0:
    obstacles = [
        n for n in diagram.nodes.values()
        if n.id != src.id and n.id != tgt.id
        and abs((n.x + n.width / 2.0) - (src.x + src.width / 2.0)) < max(src.width, n.width) * 0.45
        and src.y < n.y < tgt.y
    ]
    if obstacles:
        # Route around obstacles to the right of the widest card
        max_obst_r = max(n.x + n.width for n in [src, tgt] + obstacles)
        route_x = max_obst_r + 24.0
        sx, sy = src.x + src.width, src.y + src.height / 2.0
        tx, ty = tgt.x + tgt.width, tgt.y + tgt.height / 2.0
        d_path = f"M {sx:.1f} {sy:.1f} L {route_x:.1f} {sy:.1f} L {route_x:.1f} {ty:.1f} L {tx:.1f} {ty:.1f}"
    else:
        sx, sy = src.x + src.width / 2.0, src.y + src.height
        tx, ty = tgt.x + tgt.width / 2.0, tgt.y
        d_path = f"M {sx:.1f} {sy:.1f} L {tx:.1f} {ty:.1f}"
```

**Result:** If a diagram defines a skip-hop connection (e.g. Node 1 to Node 3), the line jogs outward around Node 2 rather than slicing straight through it.

### 3.3 Guardrail 3: Intermediate Subgraph Collision Avoidance (`DiagramRenderer.render_svg`)

For horizontal cross-column connections, the renderer checks whether the orthogonal step channel $mx$ falls within the boundary of any intervening subgraph:

```python
mx = (sx + tx) / 2.0

for sg in diagram.subgraphs.values():
    if (
        sg.x <= mx <= sg.x + sg.width
        and not (sg.x <= sx <= sg.x + sg.width)
        and not (sg.x <= tx <= sg.x + sg.width)
    ):
        # mx falls inside an intermediate container! Shift into the gutter
        if dx > 0:
            mx = sg.x - 18.0
        else:
            mx = sg.x + sg.width + 18.0
```

**Result:** Cross-tier or returning lines route through the clear inter-column gutter channels rather than penetrating the cards of intermediate tiers.

---

## 4. Information Architecture & Topology Best Practices

While the engine now safely routes non-standard edges, enterprise consulting diagrams must adhere to disciplined information architecture to maximize readability.

```
[ RECOMMENDED TOPOLOGY: Clean Sequential Pipelines & Symmetrical Governance ]

Tier 1: Ingress              Tier 2: Analytics             Tier 3: Control
┌──────────────────┐        ┌────────────────────────┐    ┌────────────────────┐
│ Hub              │──┐     │   Data Warehouse       │◄───┤ Data Catalog       │
├──────────────────┤  ├────►│                        │    ├────────────────────┤
│ Flow             │──┘     │         │              │    │ Replication        │
├──────────────────┤        │         ▼ (Clean Arrow)│    │ Manager            │
│ Eng              │───────►│   Operational Database │◄───┤                    │
├──────────────────┤        │         │              │    ├────────────────────┤
│                  │        │         ▼ (Clean Arrow)│    │ Management         │
│                  │        │   Cloudera ML          │◄───┤ Console            │
└──────────────────┘        └────────────────────────┘    └────────────────────┘
                             Sequential Top-to-Bottom      1-to-1 Horizontal
                             Pipeline (No Skip Jumps)      Channel Governance
```

### Rule 1: Prefer Sequential Intra-Column Pipelines
Instead of defining non-adjacent skip edges (`DW --> AI` and `OpDB --> AI`), structure the intra-container flow as a clean, sequential data pipeline:
```mermaid
DW --> OpDB
OpDB --> AI
```
This guarantees that every card in the column features a dedicated vertical entrance arrow, establishing a clear visual hierarchy.

### Rule 2: Symmetrical 1-to-1 Control Plane Governance
When modeling a Control Plane tier alongside an Analytics tier, align governance services horizontally across matching rows:
* **Row 1:** `Catalog --> DW` (Data Catalog governs Data Warehouse metadata & lineage).
* **Row 2:** `Repl --> OpDB` (Replication Manager handles Operational Database disaster recovery).
* **Row 3:** `Console --> AI` (Management Console manages Machine Learning workspaces).

---

## 5. Developer Runbook: Verifying Parity

When adding or modifying diagrams in `scripts/` or `src/ppt_engine/`:

1. **Recompile the Diagram:**
   ```bash
   uv run python scripts/generate_drawio_single_slide.py
   ```

2. **Inspect Vector SVG & PNG:**
   Verify that no two vertical paths share the exact same $X$ coordinate within a container, and confirm that all connectors terminate with `marker-end="url(#arrow)"`.

3. **Desktop Native QA (`local-app-preview`):**
   ```bash
   # Preview raster image:
   open -a "Preview" "output/proj-xyz/diagrams/04_security_governance_mesh_logos.png"

   # Open interactive Draw.io file:
   open "output/proj-xyz/diagrams/04_security_governance_mesh.drawio"
   ```
