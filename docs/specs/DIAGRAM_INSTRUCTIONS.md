# Diagram Engine V2 — Agent Operating Rules (`DIAGRAM_INSTRUCTIONS.md`)

> **Subsystem:** Diagram Engine V2 (Declarative YAML to DrawingML Native Vectors)  
> **Release Version:** `v2.3` | **Engineering Signature:** `[MJW/AGY]`  
> **Primary Rule:** Strictly Declarative YAML. Never write or patch monolithic imperative Python layout scripts.

---

## 1. Core Visual & Geometric Invariants

1. **Single-Slide Ceiling:** Visualization prompts are strictly capped at **exactly 1 slide** (or single standalone diagram plate). Never generate multi-slide pitch decks or flat raster screenshots—compile to native DrawingML vector shapes.
2. **Sharp Rectangles:** Sharp rectangles (`MSO_SHAPE.RECTANGLE`) for cards and top accent stripes. Zero top stripes on rounded cards.
3. **Zero Drop Shadows:** Strip OpenXML drop shadows (`<a:outerShdw>`, `<a:effectLst/>`).
4. **Full-Width Canvas Header:** Action title and subtitle flow in a **single text box** ($w \ge 11.85''$, `space_before = Pt(10)` on subtitle, canonical ingress line $y \ge 1.350''$).
5. **Semantic Status Colors:**
   - Red (`#DC2626`): Bottleneck, legacy defect, decommission candidate.
   - Amber (`#D97706`): Wait state, boundary ingestion, auth gate.
   - Blue (`#0284C7`): Active compute, data pipeline processing, live flow.
   - Green (`#16A34A`): Target state, Lakehouse catalog, verified storage.

---

## 2. Typographic Scale & The Font Floor Gate

1. **Default Font Floor ($\ge 11\text{pt}$):** Node titles must never render below $11.0\text{pt}$; subtitles/bullets must not render below $9.5\text{pt}$. Any automated scaling below this threshold is treated as a critical layout defect.
2. **The "Make It Smaller" Directive (Semantic Aggregation):**
   - When a user asks to *"make a container smaller"* or *"take up less space"*, **DO NOT geometrically shrink font sizes or squish shapes**.
   - You MUST perform **Semantic Aggregation**: collapse 5–8 granular components into $\le 3\text{--}4$ high-level logical tiers (e.g. collapse 4 database nodes into a single card: `Legacy Relational Tier (4 DBs)`).
3. **The Dense Typography Bypass Valve (`allow_dense_typography: true`):**
   - For **Gear 3 Appendix Runbooks**, reading decks, or regulatory footnote disclosures, the YAML spec may declare `allow_dense_typography: true` at the container or diagram root.
   - Under this bypass, typography down to **$8.0\text{pt}$** is permitted without triggering a `CRITICAL_AUDIT_ERROR`. Anything below $8.0\text{pt}$ is an unconditional error.

---

## 3. The Non-Blocking ASCII Preamble Protocol

When generating a new diagram or proposing a major structural layout revision:
1. **Output an ASCII Wireframe First:** Render a 5–10 line text wireframe directly in chat to show proposed container zones, node titles, and connectors.
2. **Proceed Immediately:** Do not block execution on a long interview; print the ASCII wireframe as a non-blocking preamble, then execute the declarative YAML build.
3. **Why this works:** The user gets instant visual confirmation in 2 seconds. If a component or flow is wrong, the user can easily intervene before the slide is baked.

---

## 4. Verification & Audit Commands

Always verify specifications headlessly using the Diagram Engine V2 CLI before finalizing:

```bash
# 1. Tier 1 Spatial Clearance & Typographic Density Audit
uv run bench diagram v2 audit specs/my_slide.yaml --strict

# 2. Preview ASCII layout wireframe in terminal
uv run bench diagram v2 ideas preview -s specs/my_slide.yaml

# 3. Explore or scaffold canonical patterns
uv run bench diagram v2 ideas list
uv run bench diagram v2 ideas scaffold -p 3-swimlane -o specs/my_slide.yaml

# 4. Compile to native vector PowerPoint and vector assets
uv run bench diagram v2 compile specs/my_slide.yaml
```
