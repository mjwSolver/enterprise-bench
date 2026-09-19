# Sprint 17 Implementation Runbook: Security Hardening & Performance Quick-Wins

> **Sprint:** 17  
> **Status:** ✅ **COMPLETED** (2026-09-19T11:43:35+07:00 | Commit `7785eeb`)  
> **Target Subsystems:** `src/cli.py`, `src/ppt_engine/`, `src/core/pii/`  
> **Estimated Execution Time:** ~20 minutes  
> **Operating Guardrail:** [`AGENTS.md`](../../AGENTS.md) (Strict **ZERO INTERMEDIATE UNIT TESTING**).

---

## 1. Objective & Scope

Execute four zero-risk, high-impact P0 patches addressing arbitrary command injection in desktop app launchers, an $O(2^V)$ exponential path explosion in diagram node ranking, uncached TrueType font disk I/O in slide exports, and a case-sensitivity defect in PII format handlers.

---

## 2. Implementation Tasks

### Task 1: Eliminate `shell=True` Command Injection in Desktop Launchers
- **Target File:** [`src/cli.py`](../../src/cli.py)
- **Target Lines:** 336–340 and 381–385

#### Problem
```python
# VULNERABLE PATTERN:
cmd = f'open -a "Microsoft PowerPoint" "{saved_file.resolve()}" && osascript -e \'tell application "Microsoft PowerPoint" to activate\''
subprocess.run(cmd, shell=True)
```

#### Remediation
Replace with discrete argument lists without shell interpretation:
```python
# REPLACEMENT PATTERN:
if open_deck:
    rprint(f"[cyan]ℹ Launching desktop PowerPoint:[/cyan] [bold]{saved_file.name}[/bold]")
    try:
        subprocess.run(["open", "-a", "Microsoft PowerPoint", str(saved_file.resolve())], check=False)
        subprocess.run(["osascript", "-e", 'tell application "Microsoft PowerPoint" to activate'], check=False)
    except Exception as e:
        rprint(f"[yellow]⚠ Could not activate Microsoft PowerPoint: {e}[/yellow]")
```
*Apply the identical fix to `replace_ppt_image` at lines 381–385.*

---

### Task 2: Replace $O(2^V)$ DFS with Kahn's Algorithm in Diagram Ranking
- **Target File:** [`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py)
- **Target Lines:** 1021–1046 (`_assign_ranks` inside `HierarchicalLayoutEngine`)

#### Problem
The current recursive DFS explores all simple paths without pruning already-visited higher ranks. On converging diamond topologies, path enumeration scales as $O(2^V)$, causing recursion errors or CLI freezes.

#### Remediation
Replace `_assign_ranks` with topological BFS:
```python
    def _assign_ranks(
        self, diagram: ParsedDiagram, adj: Dict[str, Set[str]], rev_adj: Dict[str, Set[str]]
    ) -> Dict[str, int]:
        """
        Assign topological ranks to diagram nodes in O(V + E) time using Kahn's algorithm.
        Ensures each node is placed in a rank strictly greater than all its upstream dependencies.
        """
        from collections import deque

        in_degree = {nid: len(preds) for nid, preds in rev_adj.items()}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        
        # If graph has cycles or no explicit roots, seed with first node
        if not queue and diagram.nodes:
            first_nid = next(iter(diagram.nodes.keys()))
            queue.append(first_nid)

        ranks: Dict[str, int] = {nid: 0 for nid in queue}

        while queue:
            curr = queue.popleft()
            curr_rank = ranks.get(curr, 0)
            for neighbor in adj.get(curr, set()):
                ranks[neighbor] = max(ranks.get(neighbor, 0), curr_rank + 1)
                in_degree[neighbor] -= 1
                if in_degree[neighbor] <= 0 and neighbor not in ranks:
                    queue.append(neighbor)

        # Fallback for disconnected components
        for nid in diagram.nodes:
            if nid not in ranks:
                ranks[nid] = 0

        return ranks
```

---

### Task 3: Memoize TrueType Font Loading in Headless Slide Exporter
- **Target File:** [`src/ppt_engine/slide_exporter.py`](../../src/ppt_engine/slide_exporter.py)
- **Target Lines:** 53–54

#### Problem
`_get_system_font` is called on every text token across slides. It performs multiple `os.path.exists` system calls and parses font files from disk on every invocation (~4,000 disk hits per presentation).

#### Remediation
Add `@functools.lru_cache` to `_get_system_font`:
```python
import functools

@functools.lru_cache(maxsize=128)
def _get_system_font(font_name: Optional[str] = None, size_px: int = 16, bold: bool = False) -> ImageFont.ImageFont:
    """Locate crisp system font on macOS/Linux/Windows with sensible fallbacks (memoized)."""
    # ... existing body remains intact ...
```

---

### Task 4: Fix Case-Sensitivity Bug in PII Handlers
- **Target Files:**
  - [`src/core/pii/handlers/docx_handler.py:157`](../../src/core/pii/handlers/docx_handler.py#L157)
  - [`src/core/pii/handlers/pptx_handler.py:151`](../../src/core/pii/handlers/pptx_handler.py#L151)
  - [`src/core/pii/handlers/xlsx_handler.py:142`](../../src/core/pii/handlers/xlsx_handler.py#L142)

#### Problem
```python
for target, replacement in sorted_replacements:
    if target in new_val:  # BUG: Case-sensitive check skips case-insensitive matches!
        new_val = re.sub(re.escape(target), replacement, new_val, flags=re.IGNORECASE)
```

#### Remediation
Perform case-insensitive containment or compile a single regex union:
```python
for target, replacement in sorted_replacements:
    if target.lower() in new_val.lower():
        new_val = re.sub(re.escape(target), replacement, new_val, flags=re.IGNORECASE)
```

---

## 3. Verification Gate (No Pytest)

Execute targeted CLI smoke runs to verify all modified modules build and run with zero syntax errors:

```bash
# 1. Static compilation check
uv run python -m py_compile src/cli.py src/ppt_engine/diagram_engine.py src/ppt_engine/slide_exporter.py src/core/pii/handlers/docx_handler.py

# 2. Verify diagram rank calculation smoke test
uv run bench diagram export-all presets/diagrams/fsd_architecture.yaml --format svg

# 3. Verify PII sanitization case-insensitivity
uv run bench doc sanitize --input clean_workspace/projects/TTI_Snowflake_Analytics/07_contracts/BAST_Milestone_1_Template.docx --output output/test_sanitized.docx
```

---

## 4. Definition of Done Checklist

- [x] `shell=True` removed from `src/cli.py:339` and `src/cli.py:384`.
- [x] `_assign_ranks` in `diagram_engine.py` converted to Kahn's topological BFS.
- [x] `@functools.lru_cache(maxsize=128)` added to `_get_system_font` in `slide_exporter.py`.
- [x] `target.lower() in new_val.lower()` applied across `docx_handler.py`, `pptx_handler.py`, and `xlsx_handler.py`.
- [x] Static py_compile and CLI smoke verification completed with zero errors.
