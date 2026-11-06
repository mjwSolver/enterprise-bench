# Design Contract: Strategic Trade-Off (`strategic_tradeoff`)

Design contract specification raising the presentation ceiling for vendor evaluations, architecture trade-offs, buy-vs-build analyses, and scenario options.

---

## 🎯 Strategic Intent

* **Audience:** VP of Engineering, Procurement Committees, Business Sponsors.
* **Goal:** Force decisive clarity between competing options by giving dominant visual weight and positive hierarchy to the recommended path.
* **Failure State:** Symmetric cards that treat fundamentally unequal options as identical choices, forcing the reader to hunt for the recommendation.

---

## 🎛️ Parametric Dials

```yaml
density: MEDIUM
visual_variance: ASYMMETRIC
whitespace_budget: BALANCED (20-25% canvas open surface)
focal_anchor_weight: DIRECTED (Recommended option visually anchors the slide)
card_split_ratio: 40/60 or 35/65
```

---

## 📐 Layout Geometry & Topology

* **Canvas Allocation:** Asymmetric Two-Column Split:
  * **Option A / Baseline / Deprecated ($w \approx 4.5''$ - 35-40%):** Neutral Slate container, thinner border (`0.75 pt #E2E8F0`), flat white background, representing current state or rejected alternative.
  * **Option B / Recommended / Target State ($w \approx 7.2''$ - 60-65%):** Dominant container with subtle Ice-Blue wash (`#F0F9FF`), primary accent border (`1.5 pt #0284C7`), top accent stripe, and floating "RECOMMENDED" badge.
* **Inter-Card Gutters:** `0.30''` minimum clearance.

---

## 🎨 Color Strategy

* **Baseline / Rejected Column:** Neutral Slate surfaces (`#FFFFFF` on `#F8FAFC`), muted header text (`#475569`), warning flags in muted Amber (`#D97706`).
* **Recommended Column:** High-contrast crisp Ice-Blue (`#F0F9FF`) surface, Primary Accent Blue (`#0284C7`) or Target Green (`#16A34A`), crisp Slate 900 text (`#0F172A`).
* **Evaluation Matrix Rows:** Contiguous data table (`row_gap = 0.0`) with 0.75 pt hairline row dividers and alternating `#F8FAFC` zebra fills.

---

## 📝 Micro-Copy Rules

* **Action Headline:** States the decisive selection outcome (e.g. `Snowflake Managed Iceberg Outperforms Self-Hosted Trino on Maintenance Overhead and Audit Latency`).
* **Option Headers:** Clear naming of the active alternatives with immediate status descriptor (`Current Architecture (Legacy Oracle CDC)` vs `Target Solution (Snowflake Streaming Ingest)`).
* **Trade-Off Bullets:** Strictly bold lead phrases asserting the operational difference:
  * **TCO Impact:** Direct cost delta (`-$320K/yr infrastructure saving`).
  * **Operational Burden:** Engineering maintenance effort (`Zero manual partition compaction required`).

---

## 🔍 Validation Checklist

1. [ ] Recommended option has visibly larger spatial width (40/60 or 35/65 split) or dominant accent border.
2. [ ] Zero identical twin cards with identical border weights and fills.
3. [ ] Trade-off criteria directly map against each other across both options without disjointed metrics.
4. [ ] Headline asserts the definitive recommendation, not a neutral title like "Option Comparison".
