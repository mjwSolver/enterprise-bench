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

## 🧰 MANDATORY PRE-FLIGHT: SPECIALIZED LOCAL SKILLS

> **DIRECTIVE: REVIEW LOCAL SKILLS BEFORE ACTING ON CREATIVE CAPACITY**

Before generating code, authoring new deliverables, designing presentations, or creating custom templates from scratch, **agents must check and activate existing specialized skills**. Future agents generally follow one of two core directions: **Operational (producing deliverables with existing tools)** or **Development (extending and maintaining the engine platform)**.

### Primary Skills Index (`.agents/skills/`, symlinked via `skills/` and `.skills/`):

#### 🚀 Track A: Operational Workflows (Building Deliverables with Existing Tools)
1. **`enterprise-bench-ops`** ([`skills/enterprise-bench-ops/SKILL.md`](skills/enterprise-bench-ops/SKILL.md)):
   - **Target Role:** Deliverable Producer, Engagement PMO, Solutions Consultant.
   - **When to check:** Whenever tasked with stamping contracts, drafting FSD/TSD specs, generating status decks, filling BAST milestones, or running the `bench` CLI.
   - **Key Protocol:** Enforces stage-gate validity via [`LIFECYCLE.md`](LIFECYCLE.md) and requires locating the 38 production-ready master templates in `clean_workspace/` via [`CATALOG.md`](CATALOG.md) before generation.

#### 🛠 Track B: Development & Engine Engineering (Extending the Platform)
2. **`enterprise-bench-dev`** ([`skills/enterprise-bench-dev/SKILL.md`](skills/enterprise-bench-dev/SKILL.md)):
   - **Target Role:** Core Platform Engineer, Engine Developer, Python Maintainer.
   - **When to check:** Whenever tasked with modifying `src/docx_engine` (OpenXML tables, Jinja2 stamping), `src/ppt_engine` (visual cards, collision logic), `src/xlsx_engine` (calculators, S-curves), `src/core` (schemas, PII regex), or `src/cli.py`.
   - **Key Protocol:** Strictly enforces the **ZERO INTERMEDIATE UNIT TESTING** guardrail, environment execution via `uv`, and architectural separation of concerns.

#### 🎨 Specialized Presentation Sub-Skills (Visual Design)
3. **`presentation-maker`** ([`skills/presentation-maker/SKILL.md`](skills/presentation-maker/SKILL.md)):
   - **When to check:** Building, styling, or automating PowerPoint decks (`python-pptx`). Provides consulting frameworks (McKinsey/BCG), executive visual card archetypes, typography rules, and collision prevention.
4. **`slide-image-prompter`** ([`skills/slide-image-prompter/SKILL.md`](skills/slide-image-prompter/SKILL.md)):
   - **When to check:** Generating high-fidelity AI visual prompts for presentation backgrounds, custom infographics, or full-slide concept diagrams.

**First Action Protocol:** Identify whether your goal is **Operational (Track A)** or **Development (Track B)** and **inspect the corresponding skill file first** before proceeding.

---

## 🏛 Repository Conventions (`enterprise-bench`)

### Environment & Tooling
* Always execute Python commands through `uv` (e.g., `uv run bench ...`, `uv sync`).
* Do not alter or break code preserving legacy implementations unless explicitly authorized.
* Maintain documentation integrity; use relative links for internal file references (e.g., `[HANDOVER.md](HANDOVER.md)`), never absolute machine paths.
* Historical context, architectural rationale, and previous handovers live in [`HANDOVER.md`](HANDOVER.md) and [`docs/`](docs/).

### Architectural Layout
* `src/ppt_engine/`: Generative consulting presentations (`python-pptx`, visual cards, collision detection).
* `src/docx_engine/`: Deterministic legal/technical documents (`docxtpl`, OpenXML, BAST, PKS, FSD).
* `src/xlsx_engine/`: Spreadsheets, calculators, S-curves, RAID logs (`openpyxl`, `pandas`).
* `src/core/`: Shared models, brand color palettes, PII sanitization.
* `clean_workspace/`: Canonical workspace containing 38 sanitized golden master templates (`projects/TTI_Snowflake_Analytics/`).

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
