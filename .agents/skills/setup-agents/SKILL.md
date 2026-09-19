---
name: setup-agents
description: Universal multi-project skill harvester and AGENTS.md administrative router. Automatically discovers local workspace skills, user global skills, and builtin skills, categorizes them into standardized functional tracks, and stamps an ultra-concise pre-flight index into the top lines of AGENTS.md. Also configures subagent delegation contracts and cognitive separation guardrails across repositories.
---

# Universal Agent Setup & Skill Routing Protocol (`setup-agents`)

> **Target Role:** Repository Administrator / Multi-Agent Architect / Pair Programming Coordinator  
> **Mission:** Establish, harvest, and maintain a high-density administrative routing contract and skills directory in `AGENTS.md` across any project workspace.

---

## 1. Core Operating Philosophy

1. **Top-of-File Situational Awareness:**
   Agents must see the critical operating guardrails and the available specialized skills within the first 80–90 lines of `AGENTS.md`. Bloated or buried skill documentation leads to missed capabilities or agents reinventing workflows from scratch.

2. **Cognitive Separation of Concerns:**
   Primary execution agents engaged in active coding, debugging, or multi-task sprints experience context fatigue. They must **never** perform manual administrative closeouts, index bookkeeping, or cross-referencing in-situ. Administrative closeouts must be delegated to dedicated, freshly initialized subagents (such as the `Adaptive Documentation Scout`).

3. **Universal Portability:**
   This skill and its discovery mechanism operate consistently across any repository, respecting both global user configurations and project-local overrides.

---

## 2. Skill Discovery Hierarchy & Precedence

When harvesting skills, the engine inspects four distinct layers in order of precedence:

| Priority | Layer | Path Pattern | Purpose |
| :---: | :--- | :--- | :--- |
| **1 (Highest)** | **Workspace Local** | `<workspace>/.agents/skills/*/SKILL.md`<br>`<workspace>/skills/*/SKILL.md`<br>`<workspace>/.skills/*/SKILL.md` | Project-specific operational, development, or domain skills checked into VCS. |
| **2** | **User Global** | `~/.gemini/config/skills/*/SKILL.md` | User-defined universal skills applicable across all local repositories. |
| **3** | **Plugin Provided** | `~/.gemini/config/plugins/**/skills/*/SKILL.md` | Installed extension plugins providing specialized workflows. |
| **4 (Lowest)** | **Antigravity Built-in** | `~/.gemini/antigravity/builtin/skills/*/SKILL.md` | System baseline skills provided by the harness platform. |

*Deduplication Rule:* If a skill with the same name exists in multiple layers, the higher-priority layer takes precedence.

---

## 3. Five-Track Functional Classification Taxonomy

Discovered skills must be grouped into standardized functional tracks to provide immediate cognitive clarity:

- **Track A: Operational Workflows (Building Deliverables)**
  - *Target:* Deliverable producers, PMO consultants, execution scripts.
  - *Examples:* `enterprise-bench-ops`, client document generators.
- **Track B: Platform & Engine Engineering (Extending Infrastructure)**
  - *Target:* Platform maintainers, engine developers, backend refactorers.
  - *Examples:* `enterprise-bench-dev`, framework engineering runbooks.
- **Track C: Review, Desktop QA & Fast Turnaround**
  - *Target:* Review coordinators, pairing assistants, native desktop verification.
  - *Examples:* `local-app-preview`.
- **Track D: Administrative, Checkpoint & Delegation**
  - *Target:* Session architects, librarian subagents, context managers.
  - *Examples:* `setup-agents`, `session-checkpoint`.
- **Track E: Creative, Visual & Content Design**
  - *Target:* Slide designers, diagram modelers, visual prompters.
  - *Examples:* `presentation-maker`, `slide-image-prompter`.

---

## 4. Ultra-Concise Summary Formatting Schema

To comply with the strict $\le 80$ lines budget for pre-flight indexes in `AGENTS.md`, each skill must be rendered into a high-density, 3-to-4 line entry:

```markdown
#### [Track Name]
N. **`[skill-name]`** ([`[relative-path-to-SKILL.md]`]):
   - **Target Role:** [Target Persona / Role]
   - **When to check:** [Trigger conditions or intent]
   - **Key Protocol:** [Core constraint or methodology]
```

*Never* copy-paste the entire body of a `SKILL.md` into `AGENTS.md`. Progressive disclosure allows the agent to read the full skill file on demand.

---

## 5. Standard Subagent Delegation Contract

When an active development cycle or sprint concludes, primary agents must trigger administrative closeouts by delegating to a subagent:

```python
invoke_subagent(
    TypeName="self",
    Role="Adaptive Documentation Scout",
    Prompt="""
    Execute end-of-sprint closeout for [Sprint/Milestone identifier].
    1. Scout the repository documentation topology dynamically.
    2. Author a formal transition briefing in the project handovers directory.
    3. Reconcile the master documentation index and changelog ledger.
    4. Update the root active state pointer (preserving <= 80 line budget).
    5. Verify relative link integrity across all updated artifacts.
    """
)
```

---

## 6. Harvester CLI Usage

The companion harvester script scans and generates the formatted markdown snippet or updates `AGENTS.md` directly:

```bash
# Dry-run / preview discovered skills:
uv run python scripts/harvest_skills.py --dry-run

# Stamp / update AGENTS.md pre-flight skills index:
uv run python scripts/harvest_skills.py --stamp
```
