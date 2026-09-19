# AGENTS.md — Enterprise Workbench (`enterprise-bench`)

## 🚨 CRITICAL DIRECTIVE: ZERO INTERMEDIATE UNIT TESTING

> **STATUS: STRICTLY ENFORCED ACROSS ALL AGENTS & SUBAGENTS**

### 1. The Rule
**Fully STOP and IGNORE running any form of unit tests (`pytest`, `uv run pytest`, test runners, or test suites) during active development, refactoring, bug fixing, and sprint sessions.**

Do **NOT** run unit tests automatically or as part of verification gates.

---

### 2. Why This Rule Exists (Parallel Agent Guardrail)
* During active sprint sessions (e.g., multi-hour sprints), running tests between individual tasks creates massive overhead.
* When multiple agents or subagents work in parallel on concurrent tasks, running tests causes duplicate, redundant test runs (e.g., 3 parallel agents triggering the same test suite 3 times), thrashing system resources and slowing execution.
* Feature implementation, drafting, refactoring, and code edits must proceed with zero test friction.

---

### 3. The ONLY Allowed Exceptions
Agents may run unit tests **ONLY** under two explicit conditions:
1. **User Explicit Request:** The user explicitly types an instruction to run tests (e.g., *"run the tests"*, *"run pytest on module X"*).
2. **Pre-Push Gate to Remote Origin:** The session is preparing for an authorized `git commit` and `git push` towards a remote origin repository, where final verification before pushing is required and confirmed.

If neither condition is met, **DO NOT RUN TESTS**.

---

### 4. What To Do Instead for Verification
During development and sprint cycles:
* Rely on direct code inspection, syntax analysis, and static typing.
* Verify file existence, schema definitions, and correct function signatures.
* If testing CLI behavior, run only the specific targeted command line invocation requested by the user, never test discovery / test suites.
* Report completed changes cleanly and yield execution to the user.

---

## 🧰 MANDATORY PRE-FLIGHT: SPECIALIZED LOCAL & GLOBAL SKILLS

> **DIRECTIVE: REVIEW SPECIALIZED SKILLS BEFORE ACTING ON CREATIVE CAPACITY**

Before generating code, authoring new deliverables, designing presentations, or creating custom templates from scratch, **agents must check and activate existing specialized skills**. Primary skills index (`.agents/skills/`, symlinked via `skills/` and `.skills/`, plus global admin skills):

#### Track A: Operational Workflows (Building Deliverables with Existing Tools)
1. **`enterprise-bench-ops`** ([`skills/enterprise-bench-ops/SKILL.md`](skills/enterprise-bench-ops/SKILL.md)):
   - **Target Role:** Deliverable Producer, Engagement PMO, Solutions Consultant.
   - **When to check:** Whenever tasked with stamping contracts, drafting FSD/TSD specs, generating status decks, filling BAST milestones, or running the bench CLI.
   - **Key Protocol:** Enforces stage-gate validity via LIFECYCLE.md and requires locating the 38 production-ready master templates in clean_workspace/ via CATALOG.md before generation.

#### Track B: Platform & Engine Engineering (Extending Infrastructure)
2. **`enterprise-bench-dev`** ([`skills/enterprise-bench-dev/SKILL.md`](skills/enterprise-bench-dev/SKILL.md)):
   - **Target Role:** Core Platform Engineer, Engine Developer, Python Maintainer.
   - **When to check:** Whenever tasked with modifying src/docx_engine (OpenXML tables, Jinja2 stamping), src/ppt_engine (visual cards, collision logic), src/xlsx_engine (calculators, S-curves), src/core (schemas, PII regex), or src/cli.py.
   - **Key Protocol:** Strictly enforces the ZERO INTERMEDIATE UNIT TESTING guardrail, environment execution via uv, and architectural separation of concerns.

#### Track C: Desktop Review & Fast Turnaround (Local App Launching)
3. **`local-app-preview`** ([`skills/local-app-preview/SKILL.md`](skills/local-app-preview/SKILL.md)):
   - **Target Role:** Review Coordinator, Enterprise Consultant, Pair Programming Assistant.
   - **When to check:** Whenever tasked with opening or previewing Word (.docx), Excel (.xlsx), PowerPoint (.pptx), PDF, or diagram (.drawio, .png) deliverables on the user's local machine, or proactively suggesting desktop reviews to accelerate feedback.
   - **Key Protocol:** Uses open -a and osascript to focus application windows without blocking subshells.

#### Track D: Administrative, Checkpoint & Subagent Delegation
4. **`session-checkpoint`** ([`~/.gemini/config/skills/session-checkpoint/SKILL.md`](~/.gemini/config/skills/session-checkpoint/SKILL.md)):
   - **Target Role:** Session Architect, Cognitive Phase-Shift Gatekeeper.
   - **When to check:** Wrapping up milestones, finishing intensive research/brainstorming, or when task complexity warrants clean-slate execution across files.
   - **Key Protocol:** Generates copy-paste resume prompt adhering strictly to the standard session handover schema.
5. **`setup-agents`** ([`skills/setup-agents/SKILL.md`](skills/setup-agents/SKILL.md)):
   - **Target Role:** Repository Administrator, Multi-Agent Architect, Pair Programming Coordinator.
   - **When to check:** Initializing or updating repository operating contracts, harvesting skills, setting up subagent delegation patterns, or maintaining AGENTS.md.
   - **Key Protocol:** Enforces <= 80 line budget for pre-flight indexes, cognitive separation of concerns, and universal discovery hierarchy.

#### Track E: Presentation & Visual Design Systems
6. **`presentation-maker`** ([`skills/presentation-maker/SKILL.md`](skills/presentation-maker/SKILL.md)):
   - **Target Role:** Slide Designer, Deck Automation Engineer.
   - **When to check:** Building, styling, or automating PowerPoint decks (python-pptx). Provides consulting frameworks (McKinsey/BCG), executive visual card archetypes, typography rules, and collision prevention.
   - **Key Protocol:** Enforces sharp top stripes on containers, unified title/subtitle flow, and balanced multi-column aspect ratios.
7. **`slide-image-prompter`** ([`skills/slide-image-prompter/SKILL.md`](skills/slide-image-prompter/SKILL.md)):
   - **Target Role:** Visual Prompt Engineer, Presentation Concept Designer.
   - **When to check:** Generating high-fidelity AI visual prompts for presentation backgrounds, custom infographics, or full-slide concept diagrams.
   - **Key Protocol:** Specifies aspect ratio, visual weight, negative space, and lighting conditions.

**First Action Protocol:** Identify whether your goal is **Operational (Track A)**, **Development (Track B)**, **Review & Preview (Track C)**, **Administrative (Track D)**, or **Design (Track E)** and **inspect the corresponding skill file first** before proceeding.

---

## 🏛 Repository Conventions (`enterprise-bench`)

### 🖥 Desktop Review & Native App Launching Protocol (`open` & `osascript`)
* **Accelerated Review Directive:** After generating or stamping deliverables (presentations, contracts, specs, financial models), agents should proactively offer or suggest opening the files directly in local desktop applications (Microsoft Word, Microsoft Excel, Microsoft PowerPoint, Preview, Draw.io) on the user's macOS device.
* **Launch & Focus Pattern:**
  ```bash
  # Word:
  open -a "Microsoft Word" "<file.docx>" && osascript -e 'tell application "Microsoft Word" to activate'

  # Excel:
  open -a "Microsoft Excel" "<file.xlsx>" && osascript -e 'tell application "Microsoft Excel" to activate'

  # PowerPoint:
  open -a "Microsoft PowerPoint" "<file.pptx>" && osascript -e 'tell application "Microsoft PowerPoint" to activate'

  # Diagram / Image in Preview:
  open -a "Preview" "<file.png>"
  ```
* Always wrap target file paths in quotes and confirm file existence prior to execution.

### Environment & Tooling
* Always execute Python commands through `uv` (e.g., `uv run bench ...`, `uv sync`).
* Do not alter or break code preserving legacy implementations unless explicitly authorized.
* Maintain documentation integrity; use relative links for internal file references (e.g., `[HANDOVER.md](HANDOVER.md)`), never absolute machine paths.
* Historical context, architectural rationale, and previous handovers live in [`docs/INDEX.md`](docs/INDEX.md), [`docs/CHANGELOG.md`](docs/CHANGELOG.md), and [`docs/handovers/`](docs/handovers/).

### 📚 Documentation Architecture & Taxonomy Protocol
* **Strict Documentation Partitioning:** Agents must adhere to the 4-tier documentation taxonomy:
  - **`HANDOVER.md` (Root):** Strictly an **Active State Pointer** ($\le 80$ lines). Contains only the current sprint's active status, key pointers, and immediate next backlog. Never append historical milestone lists indefinitely.
  - **`docs/CHANGELOG.md`:** The **canonical historical milestone ledger**. When a milestone completes, record it chronologically here.
  - **`docs/handovers/`:** Archived sprint or session transition briefings (`YYYY-MM-DD_<topic>.md`).
  - **`docs/specs/`:** Permanent architectural reference runbooks, subsystem guides, and ADRs (e.g. OpenXML purging, Draw.io routing, Ingress Bus). Never prefix architectural specs with `HANDOVER_`.
  - **`docs/backlog/`:** Future sprint proposals, uncurated designs, and draft roadmaps.
* Index reference: Always check [`docs/INDEX.md`](docs/INDEX.md) for master cataloging.

### 🤖 Subagent Delegation Protocol: Cognitive Separation of Concerns
* **Zero In-Situ Administrative Bookkeeping:** Main agents engaged in active coding, feature implementation, refactoring, or bug triaging experience cognitive context fatigue. They must **NEVER** perform manual end-of-sprint documentation bookkeeping, changelog updates, or index cross-referencing in the same exhausted session.
* **Mandatory Subagent Delegation Gate:** Upon milestone completion or sprint wrap-up, primary agents MUST invoke a dedicated, fresh subagent running the `Adaptive Documentation Scout` protocol:
  ```python
  invoke_subagent(
      TypeName="self",
      Role="Adaptive Documentation Scout",
      Prompt="Execute end-of-sprint closeout for [Sprint/Milestone identifier]... Scout docs topology, author transition briefing, reconcile INDEX and CHANGELOG, update HANDOVER.md (<= 80 lines), and verify links."
  )
  ```
* **Scope of Subagent:** The subagent dynamically scouts repository doc topology without hardcoded paths, authors transition briefings in `docs/handovers/`, reconciles `docs/INDEX.md` and `docs/CHANGELOG.md`, updates the root `HANDOVER.md` pointer ($\le 80$ lines), and validates relative markdown links.

### 🧹 Git Commit & Push Hygiene: Scratch Directory & Multi-Agent Greenlight Protocol
* **Pre-Commit/Pre-Push Scratch Inspection:** Prior to staging, committing, or pushing to remote origin, agents must inspect if a runtime or temporary scratch directory (`scratch/`) exists in the workspace.
* **Multi-Agent Coordination & Greenlight Gate:** When preparing a commit and a `scratch/` directory is present, the agent must explicitly report it to the user and request a greenlight before deletion. This allows the user to verify whether concurrent or background agents are actively generating or using temporary files.
* **Sprint Cleanup:** Once the greenlight is confirmed (or sprint wrap-up is declared), delete the `scratch/` directory prior to finalizing git operations.

### Architectural Layout
* `src/ppt_engine/`: Generative consulting presentations (`python-pptx`, visual cards, collision detection, resource manager).
* `src/docx_engine/`: Deterministic legal/technical documents (`docxtpl`, OpenXML, BAST, PKS, FSD).
* `src/xlsx_engine/`: Spreadsheets, calculators, S-curves, RAID logs (`openpyxl`, `pandas`).
* `src/core/`: Shared models, brand color palettes, PII sanitization, and document element purgers (`docx_purger.py`).
* `clean_workspace/`: Canonical workspace containing 38 sanitized golden master templates (`projects/TTI_Snowflake_Analytics/`).

### 🖼️ Presentation Asset Resolution & Missing Resource Ledger Protocol
* **Graceful Degradation Guarantee:** Never allow missing external/stock images or corporate logos to throw unhandled `FileNotFoundError` during slide generation.
* **Resolution Engine (`src/ppt_engine/resource_manager.py`):**
  - All archetype image paths resolve through `ResourceManager.resolve_asset(key)`.
  - Missing assets attempt a 3-second non-blocking download before falling back to theme-compliant typographic pills (`[ METRODATA ]`), vector glyphs, or dark gradient scrims.
  - When fallbacks trigger, the engine logs diagnostic remediation steps in `missing_resources.md` at workspace root, complete with exact `curl` re-acquisition commands.
  - Verification & on-demand download CLI: `uv run bench ppt check-resources`.

### 🧹 Post-PII Document Sanitization: Comments & Highlight Purging Protocol
* **Mandatory Post-Sanitization Cleanse:** Raw enterprise deliverables often contain residual editorial comments, user highlights, and tracked changes.
* Following PII entity substitution, all `.docx` deliverables and templates must have these editorial artifacts purged:
  - **Review Comments:** Strip `word/comments*.xml` parts, relationship entries, and inline comment anchors (`<w:commentRangeStart>`, `<w:commentRangeEnd>`, `<w:commentReference>`).
  - **Text Highlighting:** Clear all run-level `<w:highlight>` elements across body, tables, and headers/footers.
  - **Tracked Revisions:** Remove `<w:del>` markup and strip revision change markers (`<w:rPrChange>`, `<w:pPrChange>`).
* Executable via: `uv run bench doc purge --file <path.docx>` or batch `uv run bench doc purge --dir <directory>`.

### 📐 PowerPoint Presentation Geometry: Zero Overlapping Top Lines on Rounded Containers
* **Strict Geometric Alignment Rule:** Any container card that features a top accent line, stripe, or header bar **MUST NEVER** have rounded corners at the top.
* **Anti-Pattern Prohibited:** Never place an overlapping horizontal line or stripe shape on top of a rounded container (`MSO_SHAPE.ROUNDED_RECTANGLE`), as it causes severe visual distortion, protruding corner artifacts, and mismatched radii.
* **Enforced Pattern:**
  - When an accent line, stripe, or header bar is anchored to a container, **both the container card and the stripe MUST be sharp rectangles (`MSO_SHAPE.RECTANGLE`)**.
  - Thin accent stripes must **never** be rendered as rounded rectangles (which distort into capsules/pills).
  - Rounded shapes (`MSO_SHAPE.ROUNDED_RECTANGLE`) are reserved exclusively for standalone metric badges, status pills, or self-contained cards without top overlapping lines.
  - Implement via `add_card_with_top_stripe(...)` or `add_card(..., has_top_stripe=True)`.

### 📄 PowerPoint Cover Slide Architecture: Clean Typographic Metadata (Zero Boxed Cards)
* **Dual Vertical Brand Accent Stripes (1 Red : 2 Blue Ratio):** Frame the left edge of the cover slide title area ($x=0.80''$, $y=1.80''$) with flush, adjacent vertical stripes mirroring the Metrodata emblem: a Crimson Red stripe ($w=0.045''$) immediately adjacent to a Metrodata Blue stripe ($w=0.090''$, exactly $2\times$ thickness), reflecting the authentic 1 red stroke to 2 blue strokes brand ratio.
* **No Boxed Metadata Containers:** Never place metadata (Client, Vendor, Date, Confidentiality) inside an awkward bordered card or box container at the bottom of a cover slide.
* **Typographic Multi-Column Alignment:** Render metadata directly on the slide background in clean typographic columns (e.g., `PREPARED FOR` and `ENGAGEMENT PARTNER`) separated from the title area by an optional subtle baseline hairline.
* **No Cover Footers or Pagination:** Cover slides must **NEVER** feature slide footer divider bars, confidentiality disclaimers, or page numbers (e.g. `01 / 06`). Slide footers and pagination strictly begin on content slide 2.

### 🏷️ PowerPoint Chapter Divider Slide Architecture: De-Squared Split Layout & Translucent Scrim
* **Asymmetric 1/3 + 2/3 Composition:** Break box monotony by splitting the 16:9 widescreen canvas ($13.333'' \times 7.5''$) into an unboxed narrative panel on the left ($x=0.8''$, $y=2.0''$, $w=3.6''$, $h=4.0''$) and a full-bleed photographic hero plate on the right ($x=4.8''$ to $13.333''$, $y=0.0''$, $w=8.533''$, $h=7.5''$).
* **Unified Narrative Framing:** Flow the Category Tracker breadcrumb (10pt bold uppercase, accent color), Action Headline (30–34pt bold, primary color), and context Subtitle (11.5pt, secondary color) as sequential paragraphs within a **single unified text frame** with exact paragraph offsets (`space_before = Pt(12)` and `Pt(14)`), preventing text box collisions.
* **Translucent Dark Scrim Guarantee:** Always overlay the photographic hero panel with an OpenXML DrawingML 45% dark scrim (`#0B132B` via `<a:alpha val="45000"/>`), guaranteeing high contrast for brand marks and lockup labels regardless of underlying image luminance.
* **Brand Lockup & Graceful Fallbacks:** Center the square Metrodata mark ($x \approx 7.87''$, $y \approx 2.35''$, $w=2.4''$, $h=2.1''$) with white division tagline at $y=4.70''$. If photos or logos are missing, automatically fall back to deep primary solid rectangles (`#0F172A`) and vertically centered typographic badges (`[ METRODATA ]`), logging remediation steps in `missing_resources.md`.
* **Zero Top Stripes on Rounded Cards:** Enforce sharp rectangular geometry (`MSO_SHAPE.RECTANGLE`) across both hero and scrim plates.
* **Implement via:** `build_chapter_divider_slide(...)` or `ConsultingDeckBuilder.add_chapter_divider_slide(...)`.

### 🔤 PowerPoint Header Architecture: Unified Title & Subtitle Frame (Zero Coordinate Collision)
* **No Separate Floating Text Boxes:** Never render Action Titles and Subtitles into separate shape text boxes with hardcoded Y coordinates. Guessing Y coordinates based on character length inevitably causes collision/crowding on 2-line wrapped titles, or oversized gaps on 1-line titles.
* **Unified Flow Architecture:** Place Action Title and Subtitle as sequential paragraphs within the **SAME text box**.
* **Paragraph Spacing Offset:** Enforce a strict paragraph offset (`space_before = Pt(10)`) on the subtitle paragraph. PowerPoint's text layout engine will automatically flow the subtitle exactly 10pt below the final line of the title regardless of line wrap.

### 📊 Diagram Architecture & Visual Hierarchy Standard: Large Typography & Vector Iconography
* **Balanced Multi-Tier Aspect Ratio:** Diagrams embedded into 16:9 presentation slides or executive documents must avoid ultra-wide single-tier horizontal chains ($>4$ nodes stretched linearly, creating $\sim 10:1$ aspect ratios that shrink to unreadable hairline ribbons). Enforce balanced 3-column or multi-row layouts (target aspect ratio $\sim 2.5:1$ to $3.5:1$) so typography scales legibly ($\ge 11\text{pt}$ to $14\text{pt}$ optical equivalent) when rendered inside slide cards.
* **Mandatory Vector Logos & Iconography (Zero Plain-Text Boxes):** Diagram vertices must incorporate official vector technology logos (SVG from `assets/logos/`, e.g., Kafka, Snowflake, dbt, AWS, HashiCorp Vault) or standardized icon glyphs (Lucide/Heroicons) rather than generic plain-text rectangles.
* **Node Geometry & Left-Aligned Text Flow:** Diagram cards must allocate dedicated icon slots ($40\times 40$ px to $48\times 48$ px) with left-aligned title/body labels adjacent to the emblem and generous card volume to prevent text crowding.
* **Sub-Canvas Grouping:** Topologies with multiple subgraphs must map subgraphs into distinct vertical columns or cohesive functional swimlanes with smart orthogonal routing (`_compute_subgraph_columnar_layout`).

### 📐 Diagram Edge Architecture & Collision Prevention: Dynamic Port Anchoring & Gutter Routing
* **Zero Slicing Through Containers:** Never route cross-column feedback lines or multi-column hops through the geometric center of intermediate subgraphs or cards. The engine (`DiagramRenderer.render_svg`) enforces gutter-channel routing ($sg.x \pm 18\text{ pt}$) to keep intermediate columns clear.
* **Vertical Obstacle Detection & Bypass:** Intra-column edges between non-adjacent nodes must never cut straight through intervening cards. When defining intra-column relationships, prefer sequential top-to-bottom pipelines (`DW --> OpDB`, `OpDB --> AI`). If skip-hops are used, the engine automatically jogs $24\text{ pt}$ around the right perimeter of intermediate obstacles.
* **Dynamic Draw.io XML Port Directionality:** Never hardcode edge ports (`exitX=1;entryX=0;`) for all connectors. `DrawIOConverter._build_edge_style` dynamically evaluates $(\Delta x, \Delta y)$ to assign exact attachment faces (top/bottom for vertical flows, left/right for forward/backward flows), guaranteeing that interactive `.drawio` files match headless SVG/PNG previews with zero looping or doubled lines. Reference: [`docs/specs/drawio_edge_routing_and_collision_prevention.md`](docs/specs/drawio_edge_routing_and_collision_prevention.md).

---

## 🔧 Tooling Fallback: [`scripts/write_file.py`](scripts/write_file.py)
Agents are authorized to replicate restricted harness tooling locally. For workspace file writes bypassing path restrictions and shell escaping:
```bash
# Multiline content via stdin:
python3 scripts/write_file.py path/to/file.ext <<'EOF'
... content ...
EOF

# Direct content or copy:
python3 scripts/write_file.py path/to/file.ext --content "text"
python3 scripts/write_file.py path/to/file.ext --from-file path/to/source.ext
```
