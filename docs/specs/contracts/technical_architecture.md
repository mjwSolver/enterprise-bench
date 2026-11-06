# Design Contract: Technical Architecture (`technical_architecture`)

Design contract specification raising the presentation ceiling for engineering architecture reviews, data pipelines, infrastructure migrations, and security topologies.

---

## 🎯 Strategic Intent

* **Audience:** Principal Engineers, Enterprise Architects, Engineering Directors.
* **Goal:** High-fidelity technical clarity, strict directional flow, boundary containment, and diagnostic status tracking.
* **Failure State:** Monolithic card grids masquerading as architecture, floating text boxes with no connectors, ambiguous ingress/egress.

---

## 🎛️ Parametric Dials

```yaml
density: HIGH
visual_variance: STRUCTURED
whitespace_budget: COMPACT (15-20% canvas open surface)
focal_anchor_weight: BALANCED (Flow directionality / Bottleneck highlight)
connector_routing: ORTHOGONAL
```

---

## 📐 Layout Geometry & Topology

* **Canvas Allocation:** Multi-Zone Swimlane or Horizontal Pipeline:
  * **Ingress / Source Band ($w \approx 2.5''$):** Data sources, ingress event buses, clients.
  * **Processing Core ($w \approx 5.8''$):** Compute, orchestration, state transformation, and storage boundaries.
  * **Egress / Serving Band ($w \approx 3.3''$):** Consumers, analytical layers, downstream APIs.
* **Connectors:**
  * Native DrawingML orthogonal elbow connectors with directional arrowheads.
  * Explicit protocol / trigger labels (`REST`, `gRPC`, `JDBC`, `EventBridge`) centered on lines in 8 pt uppercase.
* **Telemetry & SLA Quality Gates:**
  * Use `chart_style: wireline_constellation` for sub-percentage SLA/drift audits with checkpoint diamonds.
  * Use `chart_style: track_bars` for volumetric throughput or capacity saturation audits ([spec](../VISUALIZATION_CATALOG.md#12-multi-stage-telemetry--quality-gates-open_telemetry_flow)).
* **Boundaries:**
  * Clear sharp-cornered containment swimlanes with 1 pt hairline borders (`#CBD5E1`) and pale tint fills (`#F8FAFC`).

---

## 🎨 Color Strategy (Diagnostic 4-Color Standard)

* **Bottleneck / Defect Nodes:** Crimson Red (`#DC2626`) fill or border.
* **Boundary / Wait / Staging:** Warm Amber (`#D97706`).
* **Active Pipeline Flow / Core Compute:** Crisp Blue (`#0284C7`).
* **Target / Verified Production State:** Vibrant Green (`#16A34A`).
* **Surfaces:** Pure white (`#FFFFFF`) node cards with sharp rectangular geometry.

---

## 📝 Micro-Copy Rules

* **Action Headline:** Asserts the architectural transition or engineering bottleneck (e.g. `Decoupled Kafka Event Bus Replaces Point-to-Point CDC to Eliminate 4-Hour Ingestion Lags`).
* **Node Labels:** Specific technical entity names with subsystem tags (e.g. `Ingestion Bus (AWS MSK)`, not generic `Message Queue`).
* **Diagnostic Sub-badges:** Latency, throughput, or protocol metrics embedded in node metadata (`< 25ms p99`).

---

## 🔍 Validation Checklist

1. [ ] Every connector has explicit source and destination anchors with non-overlapping elbow routing.
2. [ ] Zero flat raster screenshots injected—100% native vector shapes.
3. [ ] Semantic colors adhere strictly to the 4-tier diagnostic standard (no arbitrary palette shifts).
4. [ ] Ingress flows left-to-right or top-to-bottom without circular line crossings.
