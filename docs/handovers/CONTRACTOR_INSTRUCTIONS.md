# Contractor Handoff: Diagram Engine V2 Layout & Collision Standard

> **Target Audience:** Contractors, Presentation Agents, and Deliverable Authors editing PowerPoint slides via Diagram Engine V2.  
> **Repository:** `enterprise-bench` | **Branch:** `main`  
> **Status:** Engine upgrades deployed & verified.

---

## 1. What Changed in the Engine

The engine team has deployed three core upgrades to eliminate undetected visual overlaps:

1. **Virtual Text Bounding Box Estimation (`auditor.py`):**
   - The linter no longer trusts declared YAML box heights (`h: 0.68"`). It computes the true rendered text height based on title, subtitle, bullets, kicker, icon, and padding.
   - If text overflows, the node's virtual footprint expands automatically in `node_boxes`, activating downstream collision checks (`NODE_COLLISION`, `CONTAINER_OVERFLOW`) before PPTX rendering.

2. **Typed Semantic Clearance Matrix (`auditor.py`):**
   - **Sibling <-> Sibling:** Requires at least $14\text{ pt}$ ($18\text{ px}$) clearance. Physical overlap is flagged as `CRITICAL (NODE_COLLISION)`; gutters $< 18\text{ px}$ are flagged as `WARNING (INSUFFICIENT_NODE_GUTTER)`.
   - **Child <-> Parent:** Child nodes and inner containers must fit inside the parent container's inner content box (container bounds minus $36\text{ px}$ header and $12\text{ px}$ padding). Spilling outside is flagged as `CRITICAL (CONTAINER_OVERFLOW)`; encroaching on padding is flagged as `WARNING (CONTAINER_PADDING_VIOLATION)`.
   - **Container Tag Badges:** Checked against all nested containers, foreign containers, child nodes, and standalone badges.

3. **Container Label Hitbox Clamping (`pptx_compiler.py`):**
   - Container header label textboxes are now tightly clamped to their actual text width (e.g. $1.67''$ instead of the full $4.40''$ container width), completely eliminating invisible hit-test occlusion over child cards.

---

## 2. Standard Workflow for Fixing Your Slides

When working on your diagram specs (e.g., `specs/diagrams/cdsw_expanded.yaml`):

### Step 1: Run the Tier 1 Geometric Audit
```bash
uv run bench diagram v2 audit specs/diagrams/cdsw_expanded.yaml
```
- **If `CRITICAL` issues appear:** You must adjust coordinates or expand the container/gutter.
- **If `WARNING (CONTAINER_PADDING_VIOLATION)` appears:** The slide will compile, but consider adding $0.05''\text{--}0.10''$ breathing room around your cards.

### Step 2: Compile to PowerPoint
```bash
uv run bench diagram v2 compile specs/diagrams/cdsw_expanded.yaml --format pptx
```
Your compiled slide will be emitted to `output/diagrams_v2/<spec_name>.pptx`.

### Step 3: Layout Rules to Observe
- **Never shrink fonts:** Keep titles $\ge 10\text{ pt}$, body $\ge 8.5\text{ pt}$, badges $\ge 7.0\text{ pt}$.
- **Vertical Spacing:** Maintain at least $0.20''$ ($18\text{ px}$) between stacked cards.
- **Header Clearance:** Place the top card at least $y \ge \text{Container}.y + 0.40''$ ($36\text{ px}$) to avoid colliding with the container label.
