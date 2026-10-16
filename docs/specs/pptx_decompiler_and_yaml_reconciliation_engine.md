# Bidirectional PPTX Decompiler & YAML Reconciliation Engine

**Subsystem:** Diagram Engine V2 (`src/ppt_engine/diagram_v2/reconciler.py`, `cli/diagram_v2.py`)  
**Context:** Milestone 36 / Topic 11 Architecture  
**Status:** Canonical Reference Specification  

---

## 1. Executive Summary & Problem Formulation

In Diagram Engine V2, diagrams and architecture topologies are authored as declarative YAML specifications (`specs/diagrams/*.yaml`) and compiled into four synchronized formats:
- Native Microsoft PowerPoint DrawingML (`.pptx`)
- Draw.io XML (`.drawio`)
- Standalone vector SVG (`.svg`)
- High-DPI raster PNG (`.png`)

When enterprise consultants or reviewers open the generated PPTX deck in Microsoft PowerPoint or Google Slides, they frequently make in-situ localized adjustments: editing typos, adjusting titles/subtitles, renaming container boundaries, changing badge descriptions, or deleting obsolete entity nodes and flows.

Previously, PowerPoint shape names were generated with arbitrary runtime counters ("Rectangle 1", "TextBox 2", "Freeform 3"), destroying reverse traceability back to the YAML AST. This forced engineers to manually transcribe slide edits back into YAML or maintain divergent fork branches.

The **Bidirectional PPTX Decompiler & YAML Reconciliation Engine** solves this by:
1. **Deterministic OpenXML Stamping:** Injecting stable, hierarchical OpenXML shape names (`<p:cNvPr name="..." id="..."/>`) during compilation in `pptx_compiler.py`.
2. **Lossless Slide Decompilation:** Recursively flattening slide shapes (including group containers) and extracting live text frames and presence states.
3. **AST Reconciliation & Pruning:** Diffing shape states against YAML AST elements, pruning deleted nodes, cascading prunings to orphan connectors, updating mutated text strings, and updating the source YAML specification on disk.
4. **Automated 4-Way Regeneration Gate:** Deterministically compiling the reconciled YAML back into `.pptx`, `.drawio`, `.svg`, and `.png` to re-establish complete 4-format parity.

---

## 2. Deterministic OpenXML Shape Naming Conventions

All DrawingML shapes stamped by `pptx_compiler.py` observe the standardized colon-delimited taxonomy:

| Element Category | OpenXML Shape Name Pattern | Description |
| :--- | :--- | :--- |
| **Header Red Stripe** | `header:stripe:red` | Corporate red accent rectangle |
| **Header Blue Stripe** | `header:stripe:blue` | Corporate blue accent rectangle |
| **Header Text Frame** | `header:title` | Action title (p0) and subtitle (p1) |
| **Container Box** | `container:{container_id}` | Outer boundary rectangle |
| **Container Label** | `container:{container_id}:label` | Top-left boundary text box |
| **Container Tag Badge**| `container:{container_id}:tag_badge` | Top-right environment pill |
| **Node Card** | `node:{node_id}` | Background card (rect, rounded, cylinder) |
| **Node Icon** | `node:{node_id}:icon` | Embedded vector/PNG picture or emoji textbox |
| **Node Text Frame** | `node:{node_id}:text` | Card text box (kicker, title, subtitle) |
| **Badge Pill** | `badge:{badge_id}` | Standalone warning or status indicator |
| **Bullet List** | `bullet_list:{bullet_list_id}` | Standalone bullet point text frame |
| **Flow Connector** | `flow:{flow_id}` | Connector line or freeform routed polyline |
| **Flow Label Pill** | `flow:{flow_id}:label` | Labeled protocol or payload pill shape |

*Note:* If an explicit `id` is omitted in YAML, deterministic fallbacks are computed:
- Flow: `f.id` or `"{source}->{target}"` or `"flow_{index}"`
- Badge: `b.id` or `"badge_{index}"`
- Bullet List: `bl.id` or `"bullet_list_{index}"`

---

## 3. Reconciliation Algorithm & Diff Rules

The reconciliation pass executes the following evaluation stages:

### A. Header Synchronization
- Inspects `header:title`. Paragraph 0 is mapped to `action_title`; paragraphs $\ge 1$ are joined into `subtitle`.
- Soft line breaks (`<a:br/>` / `\x0b`) and `\r\n` are normalized to standard `\n`.
- If text differs, updates `raw_data["header"]` in place.

### B. Container Boundary Synchronization
- Checks presence of `container:{c.id}`:
  - If missing: container is marked `PRUNED` and removed from `raw_data["containers"]`.
  - If present: compares label (`container:{c.id}:label`) and tag badge (`container:{c.id}:tag_badge`). Case-folding allowances prevent false mutations on compiler uppercasing.

### C. Node Entity Synchronization
- Checks presence of shapes matching `node:{n.id}` prefix:
  - If absent: node is marked `PRUNED`, removed from `raw_data["nodes"]`, and registered in `deleted_node_ids`.
  - If present: inspects text frame (`node:{n.id}:text`).
    - Nodes with kicker: Paragraph 0 = kicker, Paragraph 1 = title, Paragraphs $\ge 2$ = subtitle.
    - Nodes without kicker: Paragraph 0 = title, Paragraphs $\ge 1$ = subtitle.
    - Text differences are stamped as `MUTATED` and updated in `raw_data["nodes"]`.

### D. Flow & Connector Orphan Pruning
- For each flow:
  - **Endpoint Cascade:** If `f.source` or `f.target` is in `deleted_node_ids`, the flow is automatically pruned as an orphan.
  - **Shape Deletion:** If `flow:{flow_id}` is missing from the slide, the flow connector was deleted by the user and is pruned from `raw_data["flows"]`.
  - **Label Mutation:** If `flow:{flow_id}:label` text was modified, `f.label` is updated. If the label pill was deleted, `f.label` is set to `None`.

### E. Badges and Bullet Lists
- Missing shapes are pruned; altered text paragraphs update `raw_data["badges"]` and `raw_data["bullet_lists"]`.

---

## 4. CLI Router Usage (`bench diagram v2 reconcile`)

```bash
# Reconcile PPTX slide mutations against declarative YAML spec
uv run bench diagram v2 reconcile specs/diagrams/cdsw_expanded.yaml

# Reconcile passing explicit edited presentation path
uv run bench diagram v2 reconcile output/diagrams_v2/cdsw_expanded.pptx --spec specs/diagrams/cdsw_expanded.yaml

# Perform dry-run audit without touching YAML or recompiling
uv run bench diagram v2 reconcile specs/diagrams/cdsw_expanded.yaml --dry-run

# Reconcile YAML without triggering 4-way re-compilation
uv run bench diagram v2 reconcile specs/diagrams/cdsw_expanded.yaml --no-recompile
```
