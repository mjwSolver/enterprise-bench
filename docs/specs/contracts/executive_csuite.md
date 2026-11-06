# Design Contract: Executive C-Suite (`executive_csuite`)

Design contract specification raising the presentation ceiling for board-level briefings, investment committees, and executive steering decks.

---

## 🎯 Strategic Intent

* **Audience:** C-Level Executives, Board of Directors, Investment Committee.
* **Goal:** Instant comprehension of the core thesis, financial leverage, and forward-looking decisions within 3 seconds of scanning.
* **Failure State:** Cluttered data dump, dense bullet paragraphs, lack of single primary focal number.

---

## 🎛️ Parametric Dials

```yaml
density: LOW
visual_variance: MINIMAL
whitespace_budget: AIRY (>= 30% canvas open surface)
focal_anchor_weight: DOMINANT (Hero metric >= 36 pt)
max_bullets_per_container: 2
```

---

## 📐 Layout Geometry & Topology

* **Canvas Allocation:** Asymmetric 2-Column Split:
  * **Left Column ($w \approx 3.4''$):** Hero Metric Anchor Block. Floating numeric stat with uppercase tracking label and 0.75 pt divider.
  * **Right Column ($w \approx 8.2''$):** Strategic Narrative Container. Action takeaway, 2 bold-lead bullet findings, and capital consequence.
* **Margins & Gutters:**
  * Top margin below action title: `0.45''`
  * Inter-column gutter: `0.30''`
  * Bottom canvas clearance: `0.50''`

---

## 🎨 Color Strategy

* **Surfaces:** Clean white (`#FFFFFF`) with ice-blue accent container fill (`#F0F9FF`).
* **Focal Anchor:** Primary Brand Blue (`#0284C7`) or Emerald Green (`#16A34A` for positive ROI/margin uplift).
* **Dividers:** Hairline Slate (`#E2E8F0`, 0.75 pt).
* **Text Contrast:** Slate 900 (`#0F172A`) for headlines and metric values; Slate 600 (`#475569`) for narrative body.

---

## 📝 Micro-Copy Rules

* **Headline:** Strictly asserts the executive *Finding* (e.g. `Cloud Consolidation Recovers $4.2M in Run-Rate Runaway by Q3`).
* **Hero Callout:** Single raw numeric delta (`$4.2M` or `+34%`) with 9 pt uppercase slate category label above and time horizon below.
* **Takeaway Bar:** Formats the immediate capital or governance decision lever (e.g. `Decision Lever: Authorize Phase 2 cutover to release $1.1M tooling commitments`).

---

## 🔍 Validation Checklist

1. [ ] Exactly one hero stat block dominates the canvas.
2. [ ] Zero nested boxes or secondary borders inside the narrative column.
3. [ ] Narrative text contains $\le 2$ bullets, each starting with bold lead-ins.
4. [ ] Takeaway bar does not echo or paraphrase the top headline.
