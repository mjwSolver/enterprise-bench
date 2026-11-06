# AGENTS.md — Enterprise Workbench (`enterprise-bench`)

## 🚨 Critical Directives

1. **Zero Intermediate Unit Testing:** NEVER run unit tests (`pytest`, `uv run pytest`) during active development, refactoring, or bug fixing. Allowed ONLY when explicitly requested by user (e.g. *"run tests"*) or before authorized git push.
2. **Headless-First Verification:** All verifications must be 100% headless (CLI audits, linting, headless raster checks). NEVER launch desktop apps (`open -a`, `osascript`) unless user explicitly issues `"pop it"`, `"show me"`, `"open on desktop"`, or `"open in finder"`.
3. **Line-Targeted Reading & Context Hygiene:** Never read entire multi-topic ledgers or documents >100 lines into context. Use line-targeted inspection (`StartLine`/`EndLine`). Avoid repo-wide blind `grep`/`find`; resolve paths via structured manifests (`docs/INDEX.md`).
4. **Environment & Path Links:** Always execute commands via `uv run bench ...`. Always use relative markdown links (`[doc](path.md)`).
5. **Declarative YAML-First Architecture:** NEVER write or iteratively patch monolithic, imperatively hardcoded layout scripts (e.g. 500–700 line Python scripts embedding raw coordinates, shapes, and copy). Content hierarchy, badges, copy, and layout parameters must reside in a declarative YAML spec (e.g. `specs/<topic>.yaml`), executed headlessly by a decoupled, reusable compiler (`uv run bench diagram v2 compile`, static runner). All iteration and content revisions must touch *only* the YAML spec, never re-emitting compiler boilerplate ([ADR](docs/decisions/ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md)).
6. **Explicit Version Stamping on Distribution Archives:** NEVER create or distribute unversioned or timestamp-only archive files (e.g. `diagram_bundle.zip` or `diagram_engine_v2_portable_<timestamp>.zip`). All export bundles and release archives MUST explicitly stamp their semver release version in both the filename and root folder (`diagram_engine_v2_portable_v<X.Y>_<TIMESTAMP>.zip`, containing `diagram_engine_v2_bundle_v<X.Y>_<TIMESTAMP>/`), verified against `VERSION_LOG.md` and `pyproject.toml` prior to distribution ([SOP](docs/specs/diagram_engine_v2_export_sop.md)).

---

## ⚡ The 3-Lane Request Routing Triad

*(Inspired by OfficeCLI architecture, credit: Vrieza — see [ADR](docs/decisions/ADR_OFFICECLI_EVALUATION_AND_NATIVE_ROUTING.md))*

Classify incoming requests into one execution lane:
- **🔍 Lane 1: Inspection & Headless Audit:** Read-only verification, zero shape/coordinate modifications (`uv run bench ppt view`, `uv run bench doc view`, `uv run bench diagram v2 audit <spec.yaml> --strict`, `uv run bench ppt lint`, `uv run bench stage preflight`).
- **✏️ Lane 2: In-Situ Micro-Patch:** Localized text, typo, label, or image updates without altering coordinate grids or canvas bounding boxes (`uv run bench ppt patch`, `uv run bench ppt replace-image`, `gdrive mutate update <file_id> <path.pptx>`). Target presentation window must be dismissed prior to saving if previously opened.
- **📐 Lane 3: Greenfield Architecture & Staging:** Declarative YAML (`specs/diagrams/<name>.yaml`) compiled via Diagram Engine V2 (`uv run bench diagram v2 compile`). Target presentation window must be dismissed prior to re-saving if previously opened.
  - *Audit-First Invariant:* Always execute `bench diagram v2 audit <spec.yaml>` to verify clearances *before* compiling. Never iterate via blind recompilation.

---

## 📐 Presentation & Diagram Architecture Standard

- **Declarative Spec + Static Runner Invariant:** Content hierarchy, environment cards, badges, and copy reside in a declarative YAML specification (`specs/<topic>.yaml`), executed headlessly by a decoupled compiler. Never generate or patch monolithic layout scripts; all content revisions touch *only* the YAML spec ([case study](docs/decisions/ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md)).
- **Pluggable Design Contract Router:** Slide/diagram specs may declare `design_contract: <name>` to load specialized ceiling rules from `docs/specs/contracts/<name>.md` (e.g. `executive_csuite`, `technical_architecture`, `strategic_tradeoff`). When omitted, the Base Floor invariants below govern layout and geometry.
- **Visualization Pattern Router:** For non-rectangular elements (wireline constellations, checkpoint gates, radial dials, chrome viewports), select approved patterns and cognitive trade-offs from [VISUALIZATION_CATALOG.md](docs/specs/VISUALIZATION_CATALOG.md).
- **Sketch/Image Confirmation Gate:** When provided an image or sketch, output a structural graph contract (Containers, Nodes + semantic colors, Connectors) *before* writing code or compiling.
- **Single-Slide Ceiling:** Visualization prompts are strictly capped at **exactly 1 slide** (or single standalone diagram). No unsolicited multi-slide pitch decks or flat raster screenshots—compile to native DrawingML vector shapes.
- **Core Geometry & Visual Invariants (The Base Floor):**
  - **Locked Typographic Ramp:**
    - Slide Action Title: 20–22 pt, Bold, `#0F172A` (Slate 900).
    - Slide Subtitle / Context: 11–12 pt, Regular, `#475569` (Slate 600).
    - Card / Container Header: 13–14 pt, Bold, `#1E293B` (Slate 800).
    - Category Eyebrow / Tracker: 8.5–9.5 pt, Bold Uppercase (`tracking = 0.05em`), `#64748B` (Slate 500).
    - Body Bullet Lead-in: 10.5–11 pt, Bold `#0F172A`, followed by regular weight body.
    - KPI Hero Number: 32–36 pt, Bold, semantic color.
    - Footnote / Metadata: 8–8.5 pt, Regular, `#94A3B8` (Slate 400).
  - **Single Focal Anchor Invariant:** Every slide must possess exactly ONE visual focal point that draws executive eye-tracking within 2 seconds (1 primary accent container `#F0F9FF` with `#0284C7` border among neutral `#FFFFFF` peers, or 1 enlarged 36 pt callout). Never style all cards with identical visual weight.
  - **Decoupled KPI Micro-Formatting:** Metric callouts must strictly separate value from descriptor: Top line eyebrow (9 pt uppercase slate), Middle line naked numeric delta (`+28%`, `$4.2M`) at 32–36 pt Bold, Bottom line timeframe/descriptor (9–10 pt regular muted text) below a 0.75 pt hairline.
  - **Asymmetric Layout Routing (Anti-Uniformity):** Never default to homogeneous 3-column vertical cards unless presenting 3 truly parallel peer items. For comparisons, split canvas 40/60 or 35/65; for metrics, use left Hero Anchor column ($w \approx 3.2''$) with right body container ($w \approx 8.4''$); for sequences, use horizontal step ribbons.
  - **Full-Width Canvas Header:** Action title and subtitle flow in a **single text box** ($w \ge 11.85''$, `space_before = Pt(10)` on subtitle).
  - **Sharp Rectangles:** Sharp rectangles (`MSO_SHAPE.RECTANGLE`) for cards and top accent stripes. Zero top stripes on rounded cards.
  - **Zero Drop Shadows:** Strip OpenXML drop shadows (`<a:outerShdw>`, `<a:effectLst/>`).
  - **Zero Redundant Badging (No Badge Crutches):** Never place a status/sequence badge (e.g. `PILLAR 01`) if the card title or eyebrow already includes numbering/sequence, or if top stripes establish the semantic category.
  - **Flat Open Canvas (Zero Nested Callout Boxes):** Never nest bordered callout boxes or inner vertical stripes inside card containers (`met_card` inside `card`). Hero stats ($32\text{--}36\text{ pt}$) float directly on the open canvas above a 0.75 pt hairline divider.
  - **Contiguous Data Tables (`row_gap = 0.0`):** Table rows must sit completely flush. Zero gaps between alternating zebra fills; hairline dividers serve as the sole row boundary to eliminate double-line seam artifacts.
  - **Calibrated 3-Tier Severity (Zero "Red Wave"):** Avoid uniform red panic states and flat monotone tables. Scale severity: Neutral Slate for unmapped keys/metadata $\to$ Amber for operational warnings $\to$ Crimson Red strictly for fatal technical blockers.
  - **Max 2 Punchy Bullets (Anti-Academic Invariant):** Eliminate dense "research paper" text columns. Limit cards to 2 bullets maximum, each starting with bold lead phrases and $\ge 10.5\text{ pt}$ typography with generous vertical breathing room.
  - **Pristine Color Hygiene:** Clean ice-blue (`#F0F9FF`/`#E0F2FE`) and crisp white surfaces; strictly eliminate muddy mint-green/yellowish tinges (`#F0FDF4`).
  - **Zero Echo Chambers (The Anti-Paraphrase Invariant):** Takeaway bars must NEVER repeat or paraphrase the action headline or subtitle. The headline asserts the *Finding*; the takeaway bar strictly delivers the *Decision Lever / Capital Equation / So-What*. If no distinct forward-looking decision exists, omit the takeaway bar entirely.
  - **Zero Meta-Labeling:** Never use structural framework labels as slide copy (`DIMENSION 01`, `PHASE A`, `(Complication)`, `(Finding)`). Titles and row headers must state the active technical fact or operational reality directly.
  - **Zero Card Subtitle Echoes:** Never add a card subtitle that merely previews or summarizes the bullet points sitting directly underneath it.
  - **Centered-Block Alignment:** Container bullet lists are centered as a block (`block_cx == container.cx`) with left-aligned internal text lines.
  - **Zero Unsolicited Sub-Captions:** Never invent boilerplate captions/subtitles (e.g. "Architecture Working Group"). If not provided by user, leave empty.
- **Semantic Colors:** Red (`#DC2626` bottleneck/defect), Amber (`#D97706` boundary/wait), Blue (`#0284C7` active flow), Green (`#16A34A` target state).
- **Proactive Deliverable Link:** When compiling or modifying a slide or diagram, proactively append:
  1. Clickable Markdown link (`file://` or relative path) to the deliverable.
  2. Copyable 1-line desktop open command: `open <path>`.

---

## 📚 Documentation & Subagent Delegation Protocol

- **Hub-and-Spoke Governance:** Root [`HANDOVER.md`](HANDOVER.md) and [`FEATURE_BACKLOG.md`](FEATURE_BACKLOG.md) are strictly active state pointers ($\le 80$ lines). Detailed specs belong in `docs/backlog/` or `docs/specs/`.
- **Mandatory 3-Line Subagent Handover:** Parent agents must append the completion contract to `invoke_subagent`. Subagents return ONLY:
  ```
  - Status: [SUCCESS / FAILURE]
  - Deliverable Link: [file:///path/to/target]
  - Core Change: [1-sentence summary]
  ```

---

## 🧰 Specialized Skills Routing

Inspect relevant skill in `.agents/skills/` before acting:
- **Track A (Ops):** [`enterprise-bench-ops`](skills/enterprise-bench-ops/SKILL.md) — Stamping templates, running bench CLI.
- **Track B (Engine Dev):** [`enterprise-bench-dev`](skills/enterprise-bench-dev/SKILL.md) — Modifying `src/` engines. Enforces Zero Intermediate Unit Testing.
- **Track C (Desktop Review):** [`local-app-preview`](skills/local-app-preview/SKILL.md) — On-demand desktop preview on explicit trigger.
- **Track D (Presentations):** [`presentation-maker`](skills/presentation-maker/SKILL.md) — Presentation design systems, 3 Gears, archetype layout.
