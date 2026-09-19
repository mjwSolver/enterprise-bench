# Adaptive Documentation Scout Protocol & Subagent Runbook

> **Target Role:** Subagent / Closeout Librarian / Documentation Scout  
> **Subsystem:** Administrative Architecture & Repository Governance  
> **Applicability:** Universal across `enterprise-bench` and multi-repo environments

---

## 1. Executive Summary & Objective

The **Adaptive Documentation Scout** is a specialized subagent protocol engineered to resolve context fatigue and documentation drift. During multi-hour implementation sprints, primary execution agents expend significant context and attention on low-level syntax, typing, and complex engine logic. Requiring fatigued agents to perform manual documentation bookkeeping, changelog updates, and multi-file cross-referencing introduces human error, broken links, and incomplete records.

The Adaptive Documentation Scout protocol isolates administrative closeouts into a fresh, dedicated subagent context. Crucially, the Scout **does not rely on rigid hardcoded directory structures**, but dynamically inspects the repository's topology, identifies document categories, discovers layout drift, and reconciles documentation hubs automatically.

---

## 2. Dynamic Topology Scouting (Zero Hardcoding)

Rather than assuming fixed paths (e.g. `docs/specs/`), the Scout evaluates the workspace filesystem using standard heuristic discovery:

```
                            Repository Root
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
  Active Pointer             Central Docs Hub         Historical Ledger
   `HANDOVER.md`                 `docs/`               `CHANGELOG.md`
   (<= 80 lines)            (Index / Navigation)     (Chronological Records)
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     Transition Archives       Specifications        Backlogs & Roadmaps
      `docs/handovers/`        `docs/specs/`          `docs/backlog/`
     (Session Briefings)      (Runbooks & ADRs)      (Proposals & Sprints)
```

### Discovery Heuristics
1. **Active State Pointer:** Search root for `HANDOVER.md` or `ACTIVE_STATE.md`. Verify line budget ($\le 80$ lines).
2. **Master Navigation Index:** Search for `docs/INDEX.md`, `docs/README.md`, or root `README.md`.
3. **Chronological Ledger:** Search for `CHANGELOG.md` (root or `docs/`).
4. **Transition Briefing Archives:** Locate folder containing dated briefs (`YYYY-MM-DD_*.md`).
5. **Technical Specifications & ADRs:** Locate permanent reference directory (`specs/`, `architecture/`, `adr/`).
6. **Backlogs & Runbooks:** Locate upcoming/in-progress roadmaps (`backlog/`, `roadmap/`, `plans/`).

### Drift & Shuffle Detection
Before writing files, the Scout runs a drift check:
- Identifies any `.md` files in `docs/` that are not indexed in `docs/INDEX.md`.
- Identifies completed backlog files that need `[COMPLETED - YYYY-MM-DD]` tags or transition to `specs/`.
- Validates that archived handovers are referenced in both `docs/INDEX.md` and root `HANDOVER.md`.

---

## 3. End-of-Sprint Closeout Procedure (5-Stage Gate)

```
  ┌─────────────────┐     ┌───────────────────┐     ┌───────────────────┐
  │ 1. Git Harvest  │ ──> │ 2. Handover Brief │ ──> │ 3. Ledger Sync    │
  │  (Commit & diff)│     │  (docs/handovers/)│     │ (CHANGELOG.md)    │
  └─────────────────┘     └───────────────────┘     └───────────────────┘
                                                              │
  ┌─────────────────┐     ┌───────────────────┐               │
  │ 5. Link QA Gate │ <── │ 4. Index Reconcile│ <─────────────┘
  │ (Relative links)│     │ (INDEX & HANDOVER)│
  └─────────────────┘     └───────────────────┘
```

### Stage 1: Git Harvest & Scope Analysis
- Inspect commit history (`git log -n 5 --oneline`, `git show --stat <hash>`).
- Identify sprint deliverables, touched subsystems, and completed tasks.
- Verify status of relevant runbooks in `docs/backlog/`.

### Stage 2: Author Transition Briefing
- Create `docs/handovers/YYYY-MM-DD_<topic>.md` following the standardized schema:
  - **Frontmatter / Header:** Date, Topic, Branch, Status.
  - **Section 1: Executive Summary:** Concise overview of what was accomplished.
  - **Section 2: Key Deliverables & Code Changes:** Breakdown by subsystem / module.
  - **Section 3: Verification & QA Status:** Zero unit testing confirmation, static syntax compilation, targeted CLI runs, output artifact verification.
  - **Section 4: Immediate Next Steps:** Concrete backlog pointers for the next session.

### Stage 3: Historical Ledger Synchronization
- Inspect `docs/CHANGELOG.md`.
- Ensure delivered milestones are recorded with date, milestone number, summary, and bulleted deliverable breakdown.

### Stage 4: Master Index & Active Pointer Reconciliation
- Update `docs/INDEX.md`:
  - Add new transition briefing link under `### Session Handovers`.
  - Update any status markers on sprint backlog items.
- Update root `HANDOVER.md`:
  - Update `## 1. Active Platform Status` with new completed milestone.
  - Add the new handover link to `## 3. Transition Briefings Archive`.
  - Ensure immediate next backlog reflects current priorities.
  - **Strict Line Budget:** Enforce $\le 80$ lines total.

### Stage 5: Relative Link Integrity Gate
- Verify all markdown links are relative (e.g. `[INDEX.md](../INDEX.md)` or `[spec](lifecycle_architecture.md)`).
- Confirm every linked file exists on disk.
- Zero absolute file system paths.

---

## 4. Invocation Contract for Main Agents

Primary execution agents invoke this protocol via `invoke_subagent`:

```python
invoke_subagent(
    Subagents=[
        {
            "TypeName": "self",
            "Role": "Adaptive Documentation Scout",
            "Prompt": (
                "Execute end-of-sprint closeout for [Sprint/Milestones].\n"
                "1. Scout docs topology dynamically and harvest recent commits.\n"
                "2. Author formal transition briefing in docs/handovers/YYYY-MM-DD_<topic>.md.\n"
                "3. Reconcile docs/INDEX.md and docs/CHANGELOG.md.\n"
                "4. Reconcile root HANDOVER.md preserving the <= 80 line budget.\n"
                "5. Verify all relative links exist.\n"
                "Strict rule: ZERO INTERMEDIATE UNIT TESTING."
            ),
        }
    ],
    toolAction="Invoking subagent",
    toolSummary="Launch Documentation Scout",
)
```
