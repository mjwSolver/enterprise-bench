# AGENTS.md — Enterprise Workbench (`enterprise-bench`)

## 🚨 Critical Directives

1. **Zero Intermediate Unit Testing:** NEVER run unit tests (`pytest`, `uv run pytest`) during active development, refactoring, or bug fixing. Allowed ONLY when explicitly requested by user (e.g. *"run tests"*) or before authorized git push.
2. **Headless-First Verification:** All verifications must be 100% headless (CLI audits, linting, headless raster checks). NEVER launch desktop apps (`open -a`, `osascript`) unless user explicitly issues `"pop it"`, `"show me"`, `"open on desktop"`, or `"open in finder"`.
3. **Line-Targeted Reading & Context Hygiene:** Never read entire multi-topic ledgers or documents >100 lines into context. Use line-targeted inspection (`StartLine`/`EndLine`). Avoid repo-wide blind `grep`/`find`; resolve paths via structured manifests (`docs/INDEX.md`).
4. **Environment & Path Links:** Always execute commands via `uv run bench ...`. Always use relative markdown links (`[doc](path.md)`).
5. **Declarative YAML-First Architecture:** NEVER write or iteratively patch monolithic, imperatively hardcoded layout scripts (e.g. 500–700 line Python scripts embedding raw coordinates, shapes, and copy). Content hierarchy, badges, copy, and layout parameters must reside in a declarative YAML spec (e.g. `specs/<topic>.yaml`), executed headlessly by a decoupled, reusable compiler (`uv run bench diagram v2 compile`, static runner). All iteration and content revisions must touch *only* the YAML spec, never re-emitting compiler boilerplate ([ADR](docs/decisions/ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md)).

---

## ⚡ The 3-Lane Request Routing Triad

Classify incoming requests into one execution lane:
- **🔍 Lane 1: Inspection & Headless Audit:** Read-only verification, zero shape/coordinate modifications (`uv run bench diagram v2 audit <spec.yaml> --strict`, `uv run bench stage preflight`).
- **✏️ Lane 2: In-Situ Micro-Patch:** Localized text, typo, label, or image updates without altering coordinate grids or canvas bounding boxes (`uv run bench ppt replace-image`, `gdrive mutate update <file_id> <path.pptx>`). Target presentation window must be dismissed prior to saving if previously opened.
- **📐 Lane 3: Greenfield Architecture & Staging:** Declarative YAML (`specs/diagrams/<name>.yaml`) compiled via Diagram Engine V2 (`uv run bench diagram v2 compile`). Target presentation window must be dismissed prior to re-saving if previously opened.
  - *Audit-First Invariant:* Always execute `bench diagram v2 audit <spec.yaml>` to verify clearances *before* compiling. Never iterate via blind recompilation.

---

## 📐 Presentation & Diagram Architecture Standard

- **Declarative Spec + Static Runner Invariant:** Content hierarchy, environment cards, badges, and copy reside in a declarative YAML specification (`specs/<topic>.yaml`), executed headlessly by a decoupled compiler. Never generate or patch monolithic layout scripts; all content revisions touch *only* the YAML spec ([case study](docs/decisions/ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md)).
- **Sketch/Image Confirmation Gate:** When provided an image or sketch, output a structural graph contract (Containers, Nodes + semantic colors, Connectors) *before* writing code or compiling.
- **Single-Slide Ceiling:** Visualization prompts are strictly capped at **exactly 1 slide** (or single standalone diagram). No unsolicited multi-slide pitch decks or flat raster screenshots—compile to native DrawingML vector shapes.
- **Core Geometry & Visual Invariants:**
  - **Full-Width Canvas Header:** Action title and subtitle flow in a **single text box** ($w \ge 11.85''$, `space_before = Pt(10)` on subtitle).
  - **Sharp Rectangles:** Sharp rectangles (`MSO_SHAPE.RECTANGLE`) for cards and top accent stripes. Zero top stripes on rounded cards.
  - **Zero Drop Shadows:** Strip OpenXML drop shadows (`<a:outerShdw>`, `<a:effectLst/>`).
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
