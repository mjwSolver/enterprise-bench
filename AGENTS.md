# AGENTS.md — Enterprise Workbench (`enterprise-bench`)

## 🚨 CRITICAL DIRECTIVE: ZERO INTERMEDIATE UNIT TESTING

> **STATUS: STRICTLY ENFORCED ACROSS ALL AGENTS & SUBAGENTS**

1. **The Rule:** Fully STOP and IGNORE running any unit tests (`pytest`, `uv run pytest`, test runners) during active development, refactoring, bug fixing, and sprint sessions. Do NOT run tests automatically or as part of verification gates.
2. **Why:** Parallel agent overhead, duplicate test executions thrashing system resources, zero-friction drafting.
3. **The ONLY Allowed Exceptions:** (a) User explicitly requests tests (e.g. *"run the tests"*); (b) Authorized pre-push gate to remote origin repository. If neither is met, **DO NOT RUN TESTS**.
4. **Verification Alternative:** Direct code inspection, syntax analysis, static typing, file existence, and targeted single-command invocations requested by the user.

---

## 🧰 MANDATORY PRE-FLIGHT: SPECIALIZED LOCAL & GLOBAL SKILLS

> **DIRECTIVE: REVIEW SPECIALIZED SKILLS BEFORE ACTING ON CREATIVE CAPACITY**

Inspect relevant skill before authoring deliverables, changing engines, or writing presentations (`.agents/skills/`):
- **Track A: Operational Workflows:** [`enterprise-bench-ops`](skills/enterprise-bench-ops/SKILL.md) — Stamping templates in `clean_workspace/` via LIFECYCLE.md/CATALOG.md, running bench CLI.
- **Track B: Engine Development:** [`enterprise-bench-dev`](skills/enterprise-bench-dev/SKILL.md) — Modifying `src/docx_engine`, `src/ppt_engine`, `src/xlsx_engine`, `src/core`, `cli.py`. Enforces Zero Intermediate Unit Testing.
- **Track C: Desktop Review:** [`local-app-preview`](skills/local-app-preview/SKILL.md) — On-demand desktop preview ONLY upon explicit user prompts (`"pop it"`, `"show me"`, `"open on desktop"`, `"open in finder"`). Zero unsolicited window pops; headless-first verification is strictly enforced.
- **Track D: Administrative & Delegation:** [`session-checkpoint`](~/.gemini/config/skills/session-checkpoint/SKILL.md) (handovers), [`setup-agents`](skills/setup-agents/SKILL.md) (skills harvest & routing).
- **Track E: Presentation Systems:** [`presentation-maker`](skills/presentation-maker/SKILL.md) (deck design, 3 Gears, archetypes), [`slide-image-prompter`](skills/slide-image-prompter/SKILL.md) (visual prompts).

---

## 🏛 Repository Conventions (`enterprise-bench`)

### 🖥 Headless-First Verification & Environment
- **Headless-First Verification:** All agent visual and spatial verifications must be 100% headless (background CLI renders, linting, headless audits). Never trigger disruptive desktop window pops (`open -a` / `osascript activate`) during autonomous workflows or verification. Desktop applications must **only** launch when the user explicitly issues `"pop it"`, `"show me"`, `"open on desktop"`, or `"open in finder"`.
- **Environment & Tooling:** Always run commands via `uv run bench ...`. Relative paths only (`[doc](path.md)`). Historical context lives in [`docs/INDEX.md`](docs/INDEX.md) and [`docs/CHANGELOG.md`](docs/CHANGELOG.md).
- **Post-PII Document Sanitization:** Strip comments, run-level highlights, and revision tags from `.docx` via `uv run bench doc purge --file <path.docx>` (see [`docs/specs/openxml_purging_and_cleansing.md`](docs/specs/openxml_purging_and_cleansing.md)).
- **Asset Resolution Guarantee:** Missing slide images/logos fall back to typographic pills or gradient scrims; logged to `missing_resources.md`. Verify via `uv run bench ppt check-resources`.

### ⚡ The 3-Lane Request Routing Triad
All incoming requests and deliverable modifications MUST be classified into one of three execution lanes:
- **🔍 Lane 1: Inspection & Headless Audit:**
  - *Scope:* Read-only verification, headless geometric audits, stage-gate compliance, and asset integrity checks.
  - *Rules:* Zero shape or coordinate modifications. Run strictly via headless CLI commands (`uv run bench diagram v2 audit`, `uv run bench stage preflight`, `uv run bench pii audit`). Window pop policy: Strictly prohibited.
- **✏️ Lane 2: In-Situ Micro-Patch:**
  - *Scope:* Localized text corrections, single typo repairs, label updates, theme color tweaks, or targeted image substitutions in existing deliverables.
  - *Rules:* Do NOT recalculate or alter vector coordinate systems, bounding boxes, or canvas layouts. In-place surgical updates only (`uv run bench ppt replace-image`, `gslides mutate`). Drive-hosted `.pptx` decks strictly require `gdrive mutate update <id> <file.pptx>` (`gslides` throws 400 on Office files). Under parallel multi-agent sessions, resolve target slides dynamically by title/header—never hardcode numeric slide indices. Reference: [`docs/specs/google_drive_and_slides_collaboration_protocol.md`](docs/specs/google_drive_and_slides_collaboration_protocol.md).
- **📐 Lane 3: Greenfield Architecture & Declarative Staging:**
  - *Scope:* 0-to-1 net-new slides, complex system topologies, and multi-format diagram compilations.
  - *Rules:* Author declarative YAML specifications (`specs/diagrams/<name>.yaml`) and compile deterministically to all 4 formats (Draw.io XML, SVG, PNG, native editable PPTX) via Diagram Engine V2 (`uv run bench diagram v2 compile`). Zero imperative coordinate script bloat. Manage collaborative lifecycle through atomic stage locks (`bench stage checkout`/`commit`).

### 📚 Documentation Architecture & Subagent Delegation Protocol
- **4-Tier Partitioning & Dual Root State Pointers:**
  - *Milestone State Pointer:* Root [`HANDOVER.md`](HANDOVER.md) is strictly an **Active State Pointer** ($\le 80$ lines) retaining strictly the **latest 10 active handovers** (older briefs rotate to `docs/handovers/handover_archive/`). [`docs/CHANGELOG.md`](docs/CHANGELOG.md) is the canonical milestone ledger. Transition briefings live in [`docs/handovers/`].
  - *Feature Backlog Hub-and-Spoke Governance:* Root [`FEATURE_BACKLOG.md`](FEATURE_BACKLOG.md) is strictly an **Executive Feature Queue & State Pointer** ($\le 80$ lines). Agents must **NEVER** use `FEATURE_BACKLOG.md` as a technical dumping ground. Detailed specifications, audit registers, architecture blueprints, and execution checklists MUST live as dedicated standalone files in [`docs/backlog/<name>.md`](docs/backlog/) and be registered in [`docs/INDEX.md`](docs/INDEX.md). Backlog entries in root `FEATURE_BACKLOG.md` are strictly 3-to-5 line pointers (Scope, Spec Link, Status).
  - *Architectural Specs:* Permanent system runbooks, ADRs, and enduring standards live in [`docs/specs/`].
- **Line-Targeted Reading Constraint & Context Hygiene:** When inspecting architectural ledgers, sprint prep documents, or long-form specifications (`docs/brainstorming_sprint_prep.md`, `HANDOVER.md`, `FEATURE_BACKLOG.md`, `docs/specs/*`), agents MUST consult the file's index / TOC and use line-targeted reading (`view_file` with explicit `StartLine` and `EndLine` slices). Never load entire multi-topic documents (>100 lines) into context unless whole-file re-synthesis is explicitly mandated. Avoid repository-wide blind `grep` or `find` loops; navigate via structured manifests (`doc_output/index.md`, `docs/INDEX.md`) and targeted section lookups.
- **Zero In-Situ Administrative Bookkeeping:** Main agents must **NEVER** perform end-of-sprint documentation bookkeeping in an active development context.
- **Mandatory Delegation Gate:** On milestone completion, invoke subagent `Role="Adaptive Documentation Scout"` (`TypeName="self"`) to scout topology, author transition briefings, update `INDEX.md`/`CHANGELOG.md`, rotate older briefs to `docs/handovers/handover_archive/` (maintaining 10 active), trim `HANDOVER.md` ($\le 80$ lines), and audit `FEATURE_BACKLOG.md` ($\le 80$ lines). See [`docs/specs/adaptive_documentation_scout_protocol.md`](docs/specs/adaptive_documentation_scout_protocol.md).
- **Scratch & Git Hygiene:** Prior to commit/push, inspect `scratch/`. Report and obtain user greenlight before deleting. Delete prior to finalizing git operations.

### 📊 Adaptive Complexity Gears & Enterprise Density Standard
In enterprise IT consulting, **high information density ($7.0/10$ to $9.5/10$) is a functional requirement, not a defect.** Legibility is maintained through container hierarchy, boundary swimlanes, and strict typographic scaling (reference: [`docs/specs/adaptive_complexity_gears_and_enterprise_density.md`](docs/specs/adaptive_complexity_gears_and_enterprise_density.md)):
- **Gear 1 (Executive / Pitch, 4.0–5.0/10):** Board/Steering kickoff. Generous whitespace, 1 focal anchor, 3 takeaway cards.
- **Gear 2 (Pre-KOM / Alignment, 6.5–7.5/10 - DEFAULT BASELINE):** Technical Directors/EAs. 3-column boundary swimlanes (On-Premises ➔ Cloud ➔ Consumers), labeled workstream paths (WS1, WS2, WS4), out-of-scope boundaries.
- **Gear 3 (Technical Workstream Runbook, 8.5–9.5/10):** Lead DBAs/Engineers. 4-quadrant container discipline (Objective, MII Actions, Client Actions, Dependencies, Named PIC Table), 8.5–9.5pt micro-typography.
- **Diagnostic Status Triad:** Red (`#DC2626`) = Defect/Bottleneck/P1 Debt; Amber (`#D97706`) = Boundary/Sync/Wait; Blue (`#0284C7`) = Ingress/Active Flow; Green (`#16A34A`) = Target/Reconciled State.
- **Casual Routing Contract:** Default to Gear 2 on casual prompts; auto-elevate to Gear 3 on enterprise domain nouns (VPC/CIDR, PrivateLink, CAB, PIC, BAST); accept 1-word steering (`"pack it"`, `"simplify"`, `"swimlane it"`).

### 📐 PowerPoint Slide Geometry & Diagram Routing Standard
Full architectural runbook: [`docs/specs/powerpoint_slide_geometry.md`](docs/specs/powerpoint_slide_geometry.md) and [`docs/specs/drawio_edge_routing_and_collision_prevention.md`](docs/specs/drawio_edge_routing_and_collision_prevention.md).
- **Pre-Compilation Structural Graph Confirmation Gate (Sketch/Image Ingestion Contract):** When provided an image attachment, hand sketch, or whiteboard photo:
  1. *Stop & Extract:* Do NOT immediately execute code, compile slides, or assume matching scripts in `TEMP/`.
  2. *Emit Structural Graph:* Immediately output a bulleted topological contract to confirm layout *before* compilation:
     - **Containers & Swimlanes:** Grouping boundaries, swimlanes, and fences.
     - **Nodes & Components:** Entities, exact labels, icon glyphs, and diagnostic semantic colors (`#DC2626` bottleneck, `#D97706` wait/boundary, `#0284C7` ingress/active, `#16A34A` target).
     - **Connectors & Dataflows:** Source $\to$ Target endpoints, trigger/protocol labels (`run-now`, REST, JDBC), and synchronous vs asynchronous channels.
- **Single-Slide Scope Ceiling Invariant:** Prompts requesting "a visualization", "a diagram", or translating a sketch/drawing are strictly capped at **exactly 1 slide** (or single standalone diagram). Never generate unsolicited multi-slide pitch decks (no unprompted cover, context, or closing slides). Generated diagrams must compile to 100% native editable DrawingML vector shapes via `diagram_v2`—never inject flat raster PNG screenshots.
- **Zero Top Stripes on Rounded Cards:** Any container card with a top accent line or header bar **MUST be a sharp rectangle (`MSO_SHAPE.RECTANGLE`)** for both card and stripe. Rounded rectangles are strictly reserved for standalone metric pills.
- **Cover Slide Typographic Metadata:** Dual vertical brand accent stripes ($w=0.045''$ Red : $w=0.090''$ Blue, 1:2 ratio). Zero boxed metadata cards (render metadata directly on canvas). No cover footers or pagination (starts on slide 2).
- **Zero Unsolicited Sub-Captions (The CANDIDATE_CAPTION Invariant):** Never extrapolate, infer, or pull boilerplate captions/subtitles (e.g. "Architecture & Migration Working Group", "Data Platform Modernization Initiative") from background repository documents into metadata cards or covers. If the user dialogue does not explicitly provide a caption, presume empty (`CANDIDATE_CAPTION = None` / `""`) and render strictly the requested label and primary value.
- **Unified Title & Subtitle Frame:** Action Title and Subtitle must flow in the **SAME text box** with `space_before = Pt(10)` on subtitle. Zero separate floating text boxes with hardcoded Y coordinates.
- **Chapter Divider Split Layout:** Asymmetric 1/3 narrative panel + 2/3 photographic hero plate with 45% dark scrim (`#0B132B`).
- **Diagram Hierarchy & Routing:** Aspect ratio $\sim 2.5:1$ to $3.5:1$, vector tech logos ($40\text{--}48\text{ px}$), gutter-channel routing ($sg.x \pm 18\text{ pt}$), vertical obstacle bypass ($24\text{ pt}$ perimeter jog), and dynamic edge port assignment.
- **Centered-Block Container Alignment Standard (The Centered-List Invariant):** Multi-line content and bullet lists inside container cards must never be pinned flush to the left container margin. The content block as a whole MUST be centered horizontally within the container (`block_cx == container.cx`), while text lines within the block are internally left-aligned (`text-align: left`) so bullet glyphs (`•`) form a clean vertical column without ragged or scattered indentation.

---

## 🔧 Tooling Fallback: [`scripts/write_file.py`](scripts/write_file.py)
```bash
python3 scripts/write_file.py path/to/file.ext <<'EOF'
... content ...
EOF
```
