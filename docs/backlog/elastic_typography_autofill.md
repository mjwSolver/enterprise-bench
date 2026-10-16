# Feature Specification: Elastic Typography Auto-Fill for Underfilled Execution Cards (`ELASTIC_TYPOGRAPHY_AUTOFILL`)

> **Repository:** `enterprise-bench` | **Subsystem:** Diagram Engine V2 (`src/ppt_engine/diagram_v2/`)  
> **Status:** Implemented & Verified • Milestone 39  
> **Target Files:** [`models.py`](../../src/ppt_engine/diagram_v2/models.py), [`pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py), [`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py)

---

## 1. Problem Statement & Empirical Defect Evidence

Execution callouts, code panels, and procedural checklist cards with generous vertical canvas allocations frequently render with excessive vacant whitespace because Diagram Engine V2's typographic layout engine only performs downward shrinking:

1. **One-Way Shrink-Only Bias in `PPTXCompiler._plan_card`:**
   The current card planning loop starts at static baseline defaults (`t_pt = 12.5pt` / `11.0pt`, `s_pt = 9.0pt`, `space_before = 2.0pt`) and executes an iterative 16-step downward shrink loop solely to prevent overflow. When content is brief, the compiler never expands text upward to fill available card geometry, leaving large execution cards stranded in a cavern of dead whitespace.
2. **Empirical Defect in [`specs/diagrams/cdsw_expanded.yaml`](../../specs/diagrams/cdsw_expanded.yaml):**
   The `node_task` ('Code') card in `group_backend` is allocated $w = 3.55'' \times h = 2.40''$ ($\text{region\_h} \approx 2.14''$) to anchor the data processing execution flow. It contains 5 concise single-line action bullets:
   - `• Input metadata`
   - `• SQL Query (Filter & Search)`
   - `• Filter & Search Dev. ADD`
   - `• Logging`
   - `• Return Result`
   Under standard default rendering (`s_pt = 9.0pt`), the entire text block consumes only $1.05''$ of vertical height, resulting in an occupancy ratio of $1.05 / 2.14 = 0.49$ ($>51\%$ vacant dead space). The card visually appears sparse, unanchored, and unpolished.
3. **Empirical Proof-of-Concept Remediation:**
   By elevating the title to `16.5pt`, bullets to `12.0pt`, and paragraph spacing to `4.0pt`, content height expanded to $1.82''$ ($85.0\%$ occupancy ratio). All 5 bullets retained clean single-line horizontal clearance without wrapping, transforming the card into an authoritative enterprise execution anchor.

---

## 2. Architectural Design

### 2.1 Occupancy Ratio Formulation & Activation Envelope

During card layout planning, the virtual text frame occupancy ratio is evaluated against available vertical space:

$$\text{occupancy} = \frac{H_{\text{content}}}{H_{\text{region}}}$$

Where $H_{\text{region}} = h - 2 \cdot \text{pad\_v}$ (with $\text{pad\_v} = \text{clamp}(0.11 \cdot \min(w, h), 0.10, 0.20)$).

A node card qualifies for elastic auto-fill if it meets the **Elastic Activation Envelope**:
- **Geometry:** Height $h \ge 1.80''$ ($130\text{ px}$).
- **Alignment:** `align == "left"` and `valign == "top"` (indicative of code blocks, runbooks, or checklists).
- **Concise Item Count:** Total paragraph / bullet count $N \le 6$ (avoiding over-scaling dense lists).
- **Underfill Threshold:** Initial $\text{occupancy} < 0.55$ ($>45\%$ vacant whitespace).

### 2.2 Elastic Upward Scaling Algorithm (`PPTXCompiler._plan_card`)

Extend `_plan_card` in [`pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py) with an upward relaxation phase following the shrink loop:

- **Step 1 (Standard Overflow Shrink Loop):**
  Execute the existing downward shrink loop (stepping `t_pt` down by $-0.5\text{pt}$ and `s_pt` by $-0.25\text{pt}$). If shrinking was triggered ($content\_h > region\_h$), terminate early; elastic expansion is bypassed.
- **Step 2 (Occupancy Calculation):**
  If no shrinking occurred, calculate $\text{occupancy} = content\_h / region\_h$. If $\text{occupancy} \ge 0.55$ or the card does not meet the activation envelope, retain baseline layout.
- **Step 3 (Elastic Upward Scaling with Zero-Wrapping Invariant):**
  While $\text{occupancy} < 0.85$ and $s\_pt < \min(12.0, s\_pt\_max)$:
  - Tentatively increment $s\_pt$ by $+0.5\text{pt}$ and $t\_pt$ by $+0.5\text{pt}$ (up to $16.5\text{pt}$).
  - Calculate estimated line width for all title lines and bullet items:
    $$\text{estimated\_line\_w}(line, pt) = \text{len}(line) \cdot pt \cdot \frac{em}{72.0}$$
  - **Zero-Wrapping Gate:** If any bullet line wraps ($\text{estimated\_line\_w} > text\_w$), revert the increment and break immediately.
  - Recalculate candidate $content\_h$. If candidate $content\_h > 0.85 \cdot region\_h$, revert and break.
- **Step 4 (Proportional Paragraph Spacing Expansion):**
  Scale inter-bullet spacing (`space_before_pt`) proportionally with font growth:
  $$\text{space\_before\_pt} = \text{clamp}\left(2.0 + 2.0 \cdot \frac{s\_pt - 9.0}{12.0 - 9.0}, 2.0, 4.0\right)$$
  Verify final $content\_h \le 0.85 \cdot region\_h$.

### 2.3 Declarative Spec Control (`models.py`)

Add declarative control to `NodeSpec` in [`models.py`](../../src/ppt_engine/diagram_v2/models.py):

```python
class NodeSpec(BaseModel):
    ...
    elastic_text: Optional[bool] = None  # None = auto-detect by geometric envelope; True = force; False = disable
```

- When `elastic_text is None` (default): Auto-activates when $h \ge 1.80''$, `align == "left"`, `valign == "top"`, and bullet count $\le 6$.
- When `elastic_text is True`: Forces elastic scaling regardless of alignment, provided zero-wrapping and $85\%$ height ceiling hold.
- When `elastic_text is False`: Locks card strictly to standard baseline scale or declared overrides.

### 2.4 Tier 1 Linter Integration (`auditor.py`)

Add Check #15: `UNDERFILLED_EXECUTION_CARD` to [`Tier1GeometricLinter`](../../src/ppt_engine/diagram_v2/auditor.py):
- **15a. Underfilled Large Card Diagnostic (`INFO` / `WARNING`):**
  Flags any execution card ($h \ge 1.80''$, `align == "left"`) with $\text{occupancy} < 0.50$ when `elastic_text: false` is declared or manual undersized fonts are hardcoded, advising elastic enablement or card height reduction.
- **15b. Virtual Content Height Synchronization:**
  Update `_estimate_node_content_height()` in [`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py) to mirror elastic scaling, ensuring downstream collision and containment audits evaluate the expanded text bounding box.

---

## 3. System Guardrails (Preventing Negative Side Effects)

1. **Strict Zero-Wrapping Invariant:**
   Elastic auto-fill must **never** force a single-line bullet to wrap into multiple ragged lines. If expanding $s\_pt$ from $11.5\text{pt}$ to $12.0\text{pt}$ wraps even one word, scaling locks at $11.5\text{pt}$.
2. **Hard 85% Height Ceiling ($H_{\text{content}} \le 0.85 \cdot H_{\text{region}}$):**
   Text content never expands beyond $85\%$ of the card's inner region height, ensuring a guaranteed $15\%$ vertical margin buffer against card stroke collisions and baseline clipping.
3. **Grid Peer Harmony Exemption:**
   Cards centered horizontally (`align == "center"`) or anchored in the middle (`valign == "middle"`) are exempted from default elastic scaling. Sibling service cards in horizontal grids remain typographically uniform under [`typographic_scale_consistency_checker.md`](typographic_scale_consistency_checker.md).
4. **Reconciler Determinism (`bench diagram v2 reconcile`):**
   Elastic font calculation is a pure compiler render-time layout pass. The underlying YAML AST preserves clean declarations (`title_pt: None`, `elastic_text: true`) without polluting specs with derived runtime point sizes.

---

## 4. Implementation & Normalization Checklist

- [x] Add `elastic_text: Optional[bool] = None` field to `NodeSpec` in [`src/ppt_engine/diagram_v2/models.py`](../../src/ppt_engine/diagram_v2/models.py).
- [x] Implement 4-step elastic upward expansion in `_plan_card` in [`src/ppt_engine/diagram_v2/pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py).
- [x] Synchronize `_estimate_node_content_height` and add Check #15 (`UNDERFILLED_EXECUTION_CARD`) in [`src/ppt_engine/diagram_v2/auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py).
- [x] Align SVG and Draw.io compilers ([`svg_compiler.py`](../../src/ppt_engine/diagram_v2/svg_compiler.py), [`drawio_compiler.py`](../../src/ppt_engine/diagram_v2/drawio_compiler.py)) with the elastic upward scaling algorithm.
- [x] Remove hardcoded `title_pt: 16.5` and `subtitle_pt: 12.0` from `node_task` in [`cdsw_expanded.yaml`](../../specs/diagrams/cdsw_expanded.yaml) and verify headless compile preserves balanced 85% fill.
