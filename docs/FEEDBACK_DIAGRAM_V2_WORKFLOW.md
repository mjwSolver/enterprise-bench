# Architectural Workflow Feedback: Declarative Diagram V2 & Workbench CLI

**Author:** Enterprise Workbench Agent  
**Context:** Bank Sinarmas (BSIM) Migration — CDSW to Model Serving Topology Refinement  
**Date:** October 16, 2026  
**Scope:** Retrospective evaluation of transitioning from imperative slide scripting to declarative YAML specification (`specs/diagrams/cdsw_expanded.yaml`) and unified CLI compilation (`uv run bench diagram v2 ...`).

---

## 1. Executive Verdict (BLUF)

The enforcement of the **declarative YAML + Workbench CLI contract** was decisively beneficial and structurally superior to imperative Python scripting. It prevented disposable coordinate hacks, guaranteed four-format deliverable parity (`.drawio`, `.svg`, `.png`, `.pptx`), and directly catalyzed permanent engine-level bug fixes in `pptx_compiler.py` and `svg_compiler.py`. 

However, developer velocity was friction-loaded in two areas: (1) manual waypoint coordinate calculations for orthogonal gutter flows, and (2) silent typographic divergences between headless SVG geometry and PowerPoint's OpenXML text wrap layout engine.

---

## 2. High-Value Wins (What Worked Exceptionally Well)

### A. Four-Format Deterministic Parity Out-of-the-Box
Running a single CLI invocation:
```bash
uv run bench diagram v2 compile specs/diagrams/cdsw_expanded.yaml -o <path>.pptx -f all
```
instantly synchronized the vector SVG, high-DPI PNG, native PowerPoint DrawingML deck, and editable Draw.io XML schema without maintaining four parallel coordinate implementations.

### B. Headless Tier 1 Geometric Auditor as an Automated Stage-Gate
The strict CLI linter (`uv run bench diagram v2 audit specs/... --strict`) immediately caught spatial clearance and collision violations headlessly. For example:
- It flagged when `badge_sync` had only $9.9\text{ px}$ of clearance against the container boundary edge (enforcing the mandatory $\ge 15\text{ px}$ rule).
- It detected collinear shaft collisions when the ingress and egress flows previously shared the exact same vertical X-coordinate ($x=8.61''$).

### C. Catalyzed Permanent Core Engine Hardening
Rather than "fudging" numbers in a throwaway script, the YAML compilation forced us to identify and fix five systemic engine defects in `enterprise-bench`:
1. **Header Width Constraint:** Constrained header text box bounds (`header_w = min(9.8, max(6.0, box.w - tx - 2.8))`) so titles never collide with top-right container badges.
2. **Container Label Sizing:** Reduced container label hitbox heights from $0.45''$ to $0.26''$ and constrained width when `tag_badge` is present, eliminating invisible bounding-box collision with child cards.
3. **Double-Offset Flow Bug:** Eliminated redundant evaluation in `pptx_compiler.py` and `svg_compiler.py` where explicitly defined `label_at` positions received a secondary hardcoded `0.16''` vertical nudge.
4. **Badge Text Wrapping:** Fixed python-pptx's default behavior by explicitly setting `tf.word_wrap = False` on badge text frames, permanently preventing single-letter line breaks (`BOTTLENEC / K` and `SYNCHRONOU / S`).
5. **Left-Alignment for Bullet Lists:** Enforced automatic left alignment for paragraph runs starting with bullets (`•`), preserving centered headers on cards while keeping bullet lists readable.

Every future slide and diagram generated across the firm immediately inherits these architectural improvements.

---

## 3. Active Friction Points & Bottlenecks

### A. Manual Waypoint Calculation for Orthogonal Channels
When routing bidirectional flows through narrow inter-zone gutters ($1.2''\text{--}1.4''$), calculating explicit multi-point arrays:
```yaml
points:
  - [7.82, 3.88]
  - [8.40, 3.88]
  - [8.40, 2.85]
  - [9.40, 2.85]
```
requires cognitive manual arithmetic to ensure:
- Segments do not intersect collinear lines.
- Label pills have sufficient horizontal and vertical clearance.
- Endpoints hit flat shape edges rather than curved corner radii.

### B. Typographic Discrepancies Between SVG & PowerPoint OpenXML
Headless SVG engines calculate font bounding boxes differently than Microsoft PowerPoint on macOS/Windows. While text fits comfortably in SVG, PowerPoint applies internal paragraph margins, font kerning, and line-wrap rules that caused trailing characters to wrap. This meant a diagram that passed headless SVG verification still showed visual wrapping defects when opened in native PowerPoint until `tf.word_wrap = False` was patched.

### C. Workspace Spec Duplication
Maintaining two separate copies of the spec (`enterprise-bench/specs/diagrams/cdsw_expanded.yaml` and `BSIM_Migration/specs/diagrams/cdsw_expanded.yaml`) created manual sync overhead.

---

## 4. Concrete Recommendations for Diagram Engine V3

1. **Declarative Gutter Routing Primitives:** Support higher-level channel routing in YAML (e.g., `routing: orthogonal`, `channel: gutter_right`, `port: left-center`) so the compiler calculates collision-free stepped waypoints automatically.
2. **Text Metrics Emulation in Linter:** Add a conservative character-width heuristic in `Tier1GeometricLinter` for badge text to warn during audit if `(len(text) * font_pt * factor) > box.w`.
3. **Workspace Path Resolution:** Allow `bench diagram v2` to resolve specs across registered sibling workspaces without manual copy operations.

---

## 5. Transition to Phase 2: The "Spotless" Slide Polish Plan

With the declarative foundation stable and the core compiler hardened, the following micro-polishing items are queued for Phase 2:
1. **Vertical Rhythm in User Origin:** Rebalance `group_user` so `node_user` and `node_user_roles` have proportional vertical distribution without bottom dead space.
2. **Color Contrast & Semantic Hierarchy:** Audit all kicker, badge, and border hex values against WCAG 2.1 AA standards.
3. **Gutter Flow Visual Elegance:** Fine-tune the arrow routing in the inter-zone gutter for maximum balance and alignment with the backend through-line.
4. **Final Stage-Gate Manifest:** Stamp approved staging locks and generate a cryptographic SHA-256 manifest for customer delivery.
