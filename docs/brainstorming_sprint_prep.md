# Sprint Preparation & Architecture Brainstorming Ledger

> **Workspace:** `BSIM_Migration` / `enterprise-bench`  
> **Date:** 2026-10-15  
> **Status:** FORMALLY SEALED & RATIFIED  
> **Purpose:** Canonical sprint reference for tomorrow's engineering sessions.  
> **Agent Navigation Instruction:** When prompted to discuss a specific topic (e.g., "let's discuss Topic 4"), use `view_file` targeted to the exact line range below. Do not read the entire document into context.

---

## ⚡ Quick Navigation & Topic Index

| Topic ID | Topic Name | Line Range | Core Focus |
| :--- | :--- | :--- | :--- |
| **Topic 1** | [Navigation & Executive Synthesis](#topic-1-navigation--executive-synthesis) | `Lines 29 - 39` | TOC, meta-rules, session boundaries |
| **Topic 2** | [Attachment-to-Visualization Trace](#topic-2-attachment-to-visualization-agent-trace) | `Lines 41 - 64` | Dissecting agent reasoning on sketch input |
| **Topic 3** | [YAML System Injection Role](#topic-3-yaml-system-injection--declarative-schemas) | `Lines 66 - 83` | Declarative `diagram_v2` vs imperative script bloat |
| **Topic 4** | [Cluster 1: Visual Design & Hierarchy](#topic-4-cluster-1-visual-design-density--branding) | `Lines 85 - 104` | Caption bloat, CANDIDATE_CAPTION, brand stripes |
| **Topic 5** | [Cluster 2: Geometry & OpenXML](#topic-5-cluster-2-vector-geometry-drawio-icons--openxml) | `Lines 106 - 127` | Drop shadows root cause, Draw.io stencils, connectors |
| **Topic 6** | [Cluster 3: Agent Cognitive Routing](#topic-6-cluster-3-agent-cognitive-routing--shortcomings) | `Lines 129 - 154` | Window pop fix, 3-lane request routing, grep thrash |
| **Topic 7** | [Cluster 4: Google Drive & PPTX Sync](#topic-7-cluster-4-google-drive--pptx-delivery-pipeline) | `Lines 156 - 170` | Local compile vs web API, conflict audit, overlay state |
| **Topic 8** | [Cluster 5: Collaboration & Governance](#topic-8-cluster-5-collaboration-github--frieza-onboarding) | `Lines 172 - 187` | `gh` CLI invitation, permissions, multi-repo boundaries |
| **Topic 9** | [Workspace Clean Manifest](#topic-9-workspace-clean-manifest--file-inventory) | `Lines 189 - 201` | `doc_output/` layout, prototype isolation |
| **Topic 10** | [Recompilation Test & CLI Tooling](#topic-10-declarative-yaml-recompilation-test--cli-tooling) | `Lines 203 - 246` | Recreating CDSW via `bench diagram v2` CLI & YAML test |
| **Ratification** | [Formal Seal & Ratification Ledger](#formal-seal--ratification-ledger) | `Lines 248 - 269` | Complete sprint closure matrix |

---

## Topic 1: Navigation & Executive Synthesis
Today’s 16 sessions exposed that our systems excelled at macro consulting deliverables (multipage Word documents, full decks) but suffered friction when tasked with sub-pixel, 4-way vector diagramming (Draw.io, SVG, PPTX, PNG). Instead of using existing declarative YAML compilers, agents repeatedly wrote one-off imperative Python scripts with hardcoded coordinates, injected flat PNG images, and fought with Google Slides API batch updates. 

This ledger locks all architectural decisions, failure post-mortems, and concrete specifications so tomorrow's sprint can execute across isolated, high-leverage tracks.

### Execution & Codification Record
* **Directive Codified in AGENTS.md:** The Line-Targeted Reading Constraint is officially codified across workspaces (`BSIM_Migration/AGENTS.md` and `enterprise-bench/AGENTS.md`). Agents are prohibited from dumping entire multi-topic ledgers (>100 lines) into context; targeted line slices via `view_file` using the Quick Navigation index are strictly required.
* **Zero Grep Thrash Invariant:** Blind recursive repository-wide grep/find search loops are strictly prohibited in favor of structured manifests (`doc_output/index.md`, `docs/INDEX.md`).
* **Topic Status:** **EXECUTED & CODIFIED**

---

## Topic 2: Attachment-to-Visualization Agent Trace

### 1. Anatomy of Session `e043544e` (Sketch-to-Diagram Breakdown)
* **The Input:** User provided an image attachment (`media_1792039391960_e7e87f2f.jpg`) with the instruction: *"my partner is going to use my laptop... he's going to give you a sketch of the visualization, make it as you would previously."*
* **What the Agent Did Internally:**
  1. *Visual Recognition:* Correctly identified that the sketch showed client laptops connecting to Databricks Jobs API via a REST trigger (`run-now`).
  2. *Context Confusion:* Found a pre-existing script `scripts/generate_databricks_jobs_architecture.py` in `TEMP/` and assumed the user's sketch was a duplicate of prior work.
  3. *Over-Scoping:* Rather than generating *only* the requested slide visualization, it generated a full 3-slide pitch presentation (cover, diagram, closing) and injected a **static PNG screenshot** of the diagram into PowerPoint instead of editable vector elements.
  4. *The Consequence:* The partner could not edit text or tweak arrows in PowerPoint. The user had to spend 15 subsequent prompts removing the extra slides, replacing PNGs with native shapes, and stripping unsolicited boilerplate captions.

### 2. Anatomy of Session `bd3a3576` (Grep Thrash Breakdown)
* **The Input:** User requested an expanded version of `Legacy CDSW Job Execution` with a new user role block on the left and an expanded `.EXE` step.
* **What the Agent Did Internally:** Spent **25 sequential tool steps** blindly running `grep` and `find` across multiple repository roots just to locate where the original diagram source code lived.
* **How to Make It 10x More Efficient for Agents:**
  * **Unified Manifest:** Maintain `doc_output/index.md` linking every output file directly to its source script or YAML spec.
  * **Sketch Ingestion Contract:** When given an image/sketch, the agent must immediately output a bulleted structural graph (Nodes, Connectors, Containers) to confirm layout *before* executing compilation.
  * **Single-Slide Scope:** Enforce that requests for "a visualization" produce exactly 1 slide, never a multi-slide deck with cover/closing boilerplate.

### 3. Implementation Status: COMPLETED & CODIFIED
* **Pre-Compilation Structural Graph Gate Codified:** Locked into `BSIM_Migration/AGENTS.md`, `enterprise-bench/AGENTS.md`, and `presentation-maker/SKILL.md` (Phase 0). Requires an immediate bulleted structural graph contract (**Containers**, **Nodes**, **Connectors**) prior to code execution or compilation when an image attachment/sketch is provided.
* **Single-Slide Scope Ceiling Codified:** Locked across `BSIM_Migration/AGENTS.md`, `enterprise-bench/AGENTS.md`, and `presentation-maker/SKILL.md` (Golden Rule 7). Visualization and diagram requests are strictly capped at exactly 1 slide; unsolicited multi-slide pitch decks (cover/closing boilerplate) are prohibited.
* **Native Vector Fidelity Enforcement:** 100% editable DrawingML vector elements compiled from declarative YAML (`diagram_v2`) are mandatory; flat PNG/raster screenshots embedded on slide canvas are strictly forbidden.

---

## Topic 3: YAML System Injection & Declarative Schemas

### 1. Does the System Have Declarative YAML?
**Yes.** The repository contains a complete declarative diagram schema in `enterprise-bench/src/ppt_engine/diagram_v2/` (`models.py`, `compiler.py`).
* It accepts concise YAML specifications defining `canvas`, `header`, `brand_stripes`, `containers`, `nodes`, and `connectors`.
* It provides a unified compiler that compiles a single YAML specification into all four target formats simultaneously: `.drawio`, `.svg`, `.png`, and native `.pptx`.

### 2. Why Was It Bypassed Today?
* **Lack of Visibility:** The agents working in `BSIM_Migration` did not inspect `src/ppt_engine/diagram_v2/samples/` (`cdsw_legacy_batch.yaml`, `proposed_aws_lambda.yaml`).
* **Imperative Habit:** Agents defaulted to writing 400-line imperative Python scripts with manual `Inches()` math and direct OpenXML manipulation (`build_final_powerpoint.py`, `generate_architecture_comparison_slide.py`).

### 3. Tomorrow's Target Architecture: The YAML Pipeline
Instead of writing imperative Python scripts for every new diagram:
1. Agent drafts a clean, human-readable YAML file in `specs/diagrams/<name>.yaml`.
2. Agent runs: `uv run bench ppt compile-diagram specs/diagrams/<name>.yaml --format all --out doc_output/<topic>/`.
3. The compiler deterministically emits Draw.io, SVG, PNG, and native editable PPTX in one execution pass.

---

## Topic 4: Cluster 1: Visual Design, Density & Branding

### 1. Caption Bloat & CANDIDATE_CAPTION Invariant
* **Rule:** Never enrich shapes with secondary subtitles unless explicitly dictated in user dialogue (`CANDIDATE_CAPTION = None`).
* **Limit:** Maximum 1 label per node. Eliminate descriptive filler (e.g. under `Database`, render only `"Database"`, never add `"Enterprise Relational Data Store"`).

### 2. Brand Accent & Header Discipline
* **Format:** Top-left dual brand stripes: Red (`#DC2626`, $w=0.045''$) and Blue (`#0284C7`, $w=0.090''$), 1:2 width ratio.
* **Title:** Single action title and subtitle inside a single text frame. Never split into multiple disconnected floating boxes.
* **Canvas:** Solid white (`#FFFFFF`), non-transparent, zero ambient background cards.

### 3. Icon & Title Encapsulation
* Permitted and encouraged: Encase icon glyph and title within compact rounded-corner container pills (`MSO_SHAPE.ROUNDED_RECTANGLE`).
* Outer boundary swimlanes remain sharp rectangles (`MSO_SHAPE.RECTANGLE`).

### 4. Proportional Visual Space
* Standardize bounding margins: $12\text{--}16\text{ pt}$ padding on container boundaries.
* Ensure connector lines have at least $8\text{ pt}$ clearance from text frames to prevent overlapping arrowheads.

---

## Topic 5: Cluster 2: Vector Geometry, Draw.io Icons & OpenXML

### 1. Drop Shadows: Why They Appeared & The XML Purge
* **Mechanism:** PowerPoint slide themes default `<a:effectRef idx="2">` on shapes, which automatically applies an outer drop shadow. In web code, LLMs default to CSS `box-shadow`.
* **The Permanent Sanitizer:** All shapes compiled via python-pptx must execute:
  ```python
  shape.shadow.inherit = False
  sp_pr = shape._element.spPr
  sp_pr.append(OxmlElement("a:effectLst")) # Empty effect list
  if shape._element.find("{...}style/{...}effectRef") is not None:
      shape._element.style.effectRef.set("idx", "0")
  ```

### 2. Draw.io vs. SVG Icon Discrepancy
* **Root Cause:** Draw.io resolves cloud and tech icons from proprietary mxGraph stencils (`databricks-architecture-icons.xml`, built-in AWS stencils). The standalone SVG generator only looked for local files in `assets/icons/` and silently dropped stencils.
* **Fix (Headless Stencil Extraction):** Run Draw.io CLI headlessly (`drawio -x -f svg --crop input.drawio -o output.svg`) to preserve 100% vector stencil fidelity in the SVG export.

### 3. 100% Native Editable PPTX Connectors
* **The Rule:** Prohibit static SVG/PNG image injection into slides.
* **Connectors:** Must use native PowerPoint DrawingML connectors (`MSO_CONNECTOR.STRAIGHT`) with explicit `<a:tailEnd type="triangle"/>` or `<a:headEnd type="triangle"/>`. Connectors must remain flexible and re-routable when users drag shapes in PowerPoint.

---

## Topic 6: Cluster 3: Agent Cognitive Routing & System Shortcomings

### 1. Eliminating Disruptive Window Pops
* **Issue:** Agents flashed PowerPoint and browser windows on the user's screen during meetings.
* **Root Cause:** `local-app-preview` skill and `AGENTS.md` instructed agents to run `osascript -e 'tell application "<App>" to activate'`.
* **Fix:** All agent visual verification must be 100% headless (using background CLI renders). Desktop apps must **only** launch when the user explicitly issues `"pop it"`, `"show me"`, `"open on desktop"`, or `"open in finder"`.

### 2. Request Routing Triad
All future incoming user requests must be classified into one of three execution lanes:
* **Lane 1 (Inspection):** Read-only verification, headless checks. Zero shape modifications.
* **Lane 2 (In-Situ Micro-Patch):** Modifying a single label, color, or typo in an existing deck without touching coordinates.
* **Lane 3 (Greenfield Architecture):** Writing or updating a declarative diagram YAML spec and compiling to all 4 formats.

### 3. Single-Slide Visualization Scope Ceiling & Sketch Ingestion Contract
* **Ceiling Invariant:** Prompts asking for "a visualization", "a diagram", or translating sketch attachments are strictly capped at exactly 1 slide. Never generate unsolicited multi-slide pitch decks (covers, executive context, closings).
* **Sketch Ingestion Contract:** Emit a bulleted structural graph breakdown (Containers, Nodes, Connectors) to confirm topological intent before running compilation.

### 4. Implementation Status: COMPLETED & VERIFIED
* **Skills Updated:**
  - `skills/local-app-preview/SKILL.md`: Inverted to strictly on-demand preview. Prohibited autonomous window popups or `osascript activate` calls during automated execution.
  - `scripts/harvest_skills.py`: Updated `local-app-preview` metadata to reflect headless-first and explicit trigger invariants.
* **AGENTS.md Contracts Synchronized:**
  - `enterprise-bench/AGENTS.md`: Codified Headless-First Verification & Environment, The 3-Lane Request Routing Triad, Single-Slide Scope Ceiling Invariant, and Sketch Ingestion Contract.
  - `BSIM_Migration/AGENTS.md`: Codified Line-Targeted Reading, The CANDIDATE_CAPTION Invariant, Headless-First Verification (`pop it` / `show me` / `open on desktop` / `open in finder`), The 3-Lane Request Routing Triad, and Single-Slide Scope Ceiling.

---

## Topic 7: Cluster 4: Google Drive & PPTX Delivery Pipeline

### 1. Approach A vs. Approach B Verdict
* Direct Google Slides API batch updates are brittle and slow for vector layouts.
* Local compilation via `python-pptx` followed by Google Drive upload is fast, reliable, and keeps files fully editable.

### 2. Google Drive Staging Architecture
* **Local Master:** All deliverables compile locally to `doc_output/<topic>/`.
* **Drive Push:** Finalized `.pptx` files sync to a shared Google Drive folder (`BSIM_Migration_Deliverables/`).
* **Conflict Prevention & Status Overlay:**
  * For slides under active agent iteration, insert a non-blocking diagnostic badge in the top right: `[🤖 Agent Working Draft]`.
  * On final approval, remove the badge and stamp `[✓ Human Approved]`.
  * If a file is being edited by a human collaborator, tag filename with `_LOCKED_<username>` to prevent overwrite collisions.

---

## Topic 8: Cluster 5: Collaboration, GitHub & Frieza Onboarding

### 1. Inviting Frieza to GitHub
* GitHub CLI (`gh`) is authenticated under `mjwSolver`.
* To invite your collaborator:
  ```bash
  gh repo collaborator add <frieza-username> --repo mjwSolver/enterprise-bench --permission push
  ```
* If `BSIM_Migration` is to be hosted as its own standalone repository:
  ```bash
  cd /Users/marcelljw/Documents/antigravity/adventurous-darwin/BSIM_Migration
  gh repo create BSIM_Migration --private --source=. --remote=origin --push
  gh repo collaborator add <frieza-username> --permission push
  ```

---

## Topic 9: Workspace Clean Manifest & File Inventory

### 1. Structured `doc_output/` Topology
All loose files from `TEMP/` and root outputs have been migrated into categorized directories:
* [`architecture_comparison/`](../doc_output/architecture_comparison/): Production architecture comparison decks.
* [`cdsw_job_execution/`](../doc_output/cdsw_job_execution/): Expanded CDSW batch bottleneck diagrams.
* [`databricks_jobs_api/`](../doc_output/databricks_jobs_api/): Databricks Jobs API orchestration slides and Draw.io models.
* [`databricks_environment_design/`](../doc_output/databricks_environment_design/): Bank Sinarmas presentation covers and topology designs.
* [`whitelist_device_system/`](../doc_output/whitelist_device_system/): Architecture evolution, Before/After models, and YAML samples.
* [`prototypes_archive/`](../doc_output/prototypes_archive/): Deprecated early prototypes (`proto1`, `proto2`, `proto3`).
* Master Manifest: Fully documented in [`doc_output/index.md`](../doc_output/index.md).

---

## Topic 10: Declarative YAML Recompilation Test & CLI Tooling

### 1. The Recompilation Test Objective
Solely evaluate and benchmark declarative YAML authoring by tasking an agent to recreate the **"CDSW Job Execution Expanded"** architecture using pure YAML rather than imperative Python scripts.
* **Target Graphic:** Compare directly against [`doc_output/cdsw_job_execution/cdsw_job_execution_expanded.png`](../doc_output/cdsw_job_execution/cdsw_job_execution_expanded.png).
* **Required Inclusions:**
  1. User element callout on the far left with role description.
  2. Expanded `.EXE` execution step with connecting dataflow.
  3. Strict adherence to zero drop shadows, brand accents (red/blue), and no caption bloat (`CANDIDATE_CAPTION = None`).

### 2. Available Workbench CLI Tooling (`bench diagram v2`)
The system already possesses a specialized diagram CLI inside `enterprise-bench`:
```bash
# 1. Emit base production template
uv run bench diagram v2 sample --name cdsw -o specs/diagrams/cdsw_expanded.yaml

# 2. Validate YAML schema & icon assets
uv run bench diagram v2 validate specs/diagrams/cdsw_expanded.yaml

# 3. Compile deterministically to Draw.io, SVG, PNG, and native editable PPTX in one pass
uv run bench diagram v2 compile specs/diagrams/cdsw_expanded.yaml -o doc_output/cdsw_job_execution/cdsw_yaml_test/ -f all

# 4. Run geometric clearance & collision linting
uv run bench diagram v2 audit specs/diagrams/cdsw_expanded.yaml
```

### 3. Verification Protocol for Tonight's Test
1. **Purity Check:** Ensure 0 lines of custom `python-pptx` or OpenXML script are written; the deliverable must be produced 100% via the YAML specification.
2. **Format Parity:** Verify that `cdsw_expanded.drawio`, `cdsw_expanded.svg`, `cdsw_expanded.png`, and `cdsw_expanded.pptx` are generated simultaneously with identical geometry.
3. **Editability Check:** Confirm all shapes in `cdsw_expanded.pptx` are native DrawingML shapes that can be selected, moved, and recolored without raster clipping.

### 4. Implementation Status: COMPLETED & VERIFIED
* **Canonical Specification:** [`specs/diagrams/cdsw_expanded.yaml`](../specs/diagrams/cdsw_expanded.yaml)
* **Replaced In-Situ Artifacts:** Compiled deterministically into [`doc_output/cdsw_job_execution/`](../doc_output/cdsw_job_execution/):
  - Draw.io XML: `cdsw_job_execution_expanded.drawio` & `current_process_cdsw_expanded.drawio`
  - Vector SVG: `cdsw_job_execution_expanded.svg` & `current_process_cdsw_expanded.svg`
  - High-DPI PNG: `cdsw_job_execution_expanded.png` & `current_process_cdsw_expanded.png`
  - Native Editable DrawingML PPTX: `cdsw_job_execution_expanded.pptx` & `current_process_cdsw_expanded.pptx`
* **Verification Outcome:**
  - **Purity:** 100% produced via declarative YAML; zero imperative Python scripts written.
  - **Geometric Clearance Audit:** Passed (`uv run bench diagram v2 audit specs/diagrams/cdsw_expanded.yaml`) with 0 critical issues and 0 warnings.
  - **Format Parity:** Identical coordinate geometry and vector styling across all 4 target formats.

---

## 🔒 Formal Seal & Ratification Ledger

This ledger is formally **SEALED & RATIFIED** as of `2026-10-16T00:18:35+07:00`. All 10 architectural topics have been executed, codified into operating directives, or verified through working implementations:

| Topic ID | Topic Name | Execution & Codification Target | Status |
| :--- | :--- | :--- | :--- |
| **Topic 1** | Navigation & Executive Synthesis | Codified in `AGENTS.md` (Line-Targeted Reading Directive & Zero Grep Thrash) | **SEALED** |
| **Topic 2** | Attachment-to-Visualization Trace | Codified in `AGENTS.md` (Structural Graph Contract & Single-Slide Scope Ceiling) | **SEALED** |
| **Topic 3** | YAML System Injection | Operationalized via `bench diagram v2` (`models.py`, `compiler.py`) | **SEALED** |
| **Topic 4** | Visual Design & Hierarchy | Codified in `AGENTS.md` (`CANDIDATE_CAPTION = None`, sharp cards, brand stripes) | **SEALED** |
| **Topic 5** | Vector Geometry & OpenXML | Implemented & verified in Milestone 35 (`strip_shape_shadows()`, headless Draw.io SVG) | **SEALED** |
| **Topic 6** | Agent Cognitive Routing | Codified in `AGENTS.md` (Headless-First Verification, 3-Lane Execution Model) | **SEALED** |
| **Topic 7** | Google Drive & PPTX Sync | Formalized in `docs/specs/delivery_and_collaboration_workflow.md` & `scripts/delivery_pipeline.py` | **SEALED** |
| **Topic 8** | Collaboration & Governance | Formalized in `docs/specs/delivery_and_collaboration_workflow.md` (Locking & Badging) | **SEALED** |
| **Topic 9** | Workspace Clean Manifest | Restructured & cataloged in `doc_output/index.md` | **SEALED** |
| **Topic 10** | Declarative Recompilation Test | Passed 100% pure declarative YAML compilation (`specs/diagrams/cdsw_expanded.yaml`) | **SEALED** |

> **Directive for Subsequent Sessions:** Do not edit closed topics in this ledger. Any future enhancements must branch as discrete specs in `docs/specs/` or milestone handovers in `docs/handovers/`.



