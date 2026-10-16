# Feature Specification: Single-Command Atomic Desktop Hot-Reload (`--target & --pop`)

> **Repository:** `enterprise-bench` | **Subsystem:** Diagram Engine V2 (`src/ppt_engine/diagram_v2/`, `src/cli/`)  
> **Status:** Architecture Designed • Backlog Queued  
> **Target Files:** [`diagram_v2.py`](../../src/cli/diagram_v2.py), [`pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py), [`reconciler.py`](../../src/ppt_engine/diagram_v2/reconciler.py)

---

## 1. Problem Statement & Empirical Defect Evidence

During high-velocity enterprise consulting deliverable and architecture slide authoring, significant friction and wasted iterative cycles occur due to manual desktop coordination and file-system locking collisions:

1. **PowerPoint File Locking & Bad CRC-32 / Zip Corruption:**
   When Microsoft PowerPoint on macOS has a presentation open (e.g. `deck.pptx`), python-pptx / `zipfile` attempting to write directly to the target file triggers file-lock contention or partial write races. This results in corrupt ZIP archives throwing `BadZipFile: Bad CRC-32 for file 'ppt/slides/slide1.xml'` or OS-level `[Errno 16] Resource busy`, corrupting deliverables and forcing manual restoration.
2. **Multi-Turn Coordination Overhead in the Authoring Feedback Loop:**
   Authors currently endure a disjointed 5-step manual sequence:
   - Switch windows to Microsoft PowerPoint to close the active presentation.
   - Switch back to terminal to execute `uv run bench diagram v2 compile ...`.
   - Verify whether headless Tier 1 geometric audits passed.
   - Run a standalone AppleScript command or `open -a "Microsoft PowerPoint"` to inspect the recompiled slide.
   - If unsaved tweaks were left in PowerPoint or the deck remained locked, the compilation crashes mid-write.
3. **Whole-Deck Overwrite Hazard vs. In-Situ Single-Slide Replacement:**
   `PPTXCompiler.compile_presentation` unconditionally creates a new single-slide `Presentation()`. When compiling into an existing multi-slide client deliverable (e.g. updating Slide 3 of a 35-slide proposal deck), authors cannot safely target a specific slide index without destroying the remaining 34 sibling slides, layouts, notes, and master formatting.
4. **Unsolicited Desktop Window Pops vs. Headless CI/CD:**
   Ad-hoc scripts often launch desktop applications unconditionally during automated tests or audits, violating the repository's Headless-First Verification invariant. Desktop activation must be strictly opt-in and bound to an explicit single-command contract (`--pop`).

---

## 2. Architectural Design

### 2.1 Unified CLI Invocation Contract

Add `--target`, `--slide`, and `--pop` options to `compile_diagram_v2_cli` in [`src/cli/diagram_v2.py`](../../src/cli/diagram_v2.py):

```bash
uv run bench diagram v2 compile specs/diagrams/<spec>.yaml --target <output.pptx> --slide <num> --pop
```

- `--target` / `-t` (`Optional[str]`): Path to an existing or new PowerPoint presentation. If pointing to an existing file, activates in-situ slide replacement for the specified `--slide`.
- `--slide` (`int`, default: `1`): 1-based slide index targeted for in-situ replacement or compilation within the presentation.
- `--pop` (`bool`, default: `False`): Single-command atomic desktop hot-reload trigger. Executes preflight audit, graceful PowerPoint inspection/close, atomic OpenXML slide replacement, and macOS desktop activation.
- `--force` (`bool`, default: `False`): Bypass unsaved modification guard and close dirty presentations without prompting.

### 2.2 4-Phase Atomic Execution Pipeline

```
  ┌────────────────────────────────────────────────────────┐
  │  Phase 1: Headless Preflight & Geometric Audit Gate    │
  │  (Validate YAML AST + Tier 1 Collision & Clearance)    │
  └──────────────────────────┬─────────────────────────────┘
                             │ PASS
  ┌──────────────────────────▼─────────────────────────────┐
  │  Phase 2: AppleScript PowerPoint State Inspection      │
  │  (Check open decks, audit dirty flag, close cleanly)   │
  └──────────────────────────┬─────────────────────────────┘
                             │ CLEAN CLOSE
  ┌──────────────────────────▼─────────────────────────────┐
  │  Phase 3: Safe Atomic OpenXML Slide Replacement        │
  │  (Replace slide <num> shapes, temp-file, CRC-32 audit) │
  └──────────────────────────┬─────────────────────────────┘
                             │ ATOMIC RENAME
  ┌──────────────────────────▼─────────────────────────────┐
  │  Phase 4: Instant macOS Desktop Activation (--pop)     │
  │  (open -a "Microsoft PowerPoint", tell to activate)    │
  └────────────────────────────────────────────────────────┘
```

#### Phase 1: Headless Preflight & Tier 1 Geometric Audit Gate
Before initiating any macOS process interactions or file modifications:
1. Load and parse the declarative YAML specification into a `DiagramSpec` instance.
2. Execute `Tier1GeometricLinter` ([`auditor.py`](../../src/ppt_engine/diagram_v2/auditor.py)) checking for shape collisions, occlusions, text wrapping overflows, and typographic scale consistency.
3. If any `CRITICAL` issue is found (or `WARNING` under `--strict`), abort execution immediately with code `1`. The target deck remains 100% untouched and PowerPoint is never disturbed.

#### Phase 2: AppleScript PowerPoint State Inspection & Graceful Close
When `--pop` or `--target` is specified on macOS:
1. Check if the `Microsoft PowerPoint` application process is running (`pgrep -x "Microsoft PowerPoint"`).
2. Query open presentation names via AppleScript:
   ```applescript
   tell application "Microsoft PowerPoint"
       get name of every presentation
   end tell
   ```
3. If `target_path.name` matches an active presentation:
   - Query modification status:
     ```applescript
     tell application "Microsoft PowerPoint"
         get saved of presentation "<target_name>"
     end tell
     ```
   - **Dirty Presentation Guard (`saved == false`):** If the file has unsaved edits, do NOT close or overwrite unless `--force` is set. Emit an error: `Target presentation has unsaved modifications in PowerPoint. Save (Cmd+S) or discard before hot-reloading.`
   - **Clean Presentation Close (`saved == true`):** If cleanly saved, close the presentation without interactive prompts:
     ```applescript
     tell application "Microsoft PowerPoint"
         close presentation "<target_name>" saving no
     end tell
     ```
   - Poll briefly ($\le 1000\text{ms}$ in $50\text{ms}$ increments) until the file descriptor is released and lock file `~$<target_name>` is extinguished.

#### Phase 3: Safe Atomic OpenXML Slide Replacement
In [`src/ppt_engine/diagram_v2/pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py):
1. Load existing presentation: `prs = Presentation(target_path)`.
2. Verify slide index boundary: $1 \le \text{slide\_index} \le \text{len}(prs.slides)$. (If $\text{slide\_index} = \text{len} + 1$, append a blank slide).
3. Access target slide: `slide = prs.slides[slide_index - 1]`.
4. **DrawingML Shape Tree Purge:** Iteratively clear shape elements from `slide.shapes._spTree` while strictly preserving slide-level properties, backgrounds, layout relationships, and master styling.
5. **Compile Diagram Shapes:** Execute `PPTXCompiler(spec).compile_slide(slide)`.
6. **Atomic Two-Phase Write & Integrity Verification:**
   - Save to a staging sibling: `.tmp_<target_name>_<uuid>.pptx`.
   - Verify archive integrity with `zipfile.ZipFile(temp_path).testzip() is None`.
   - Atomically overwrite target via `os.replace(temp_path, target_path)`. Sibling slides $1 \dots N$ ($i \ne \text{slide\_index}$) are completely preserved.

#### Phase 4: Instant macOS Desktop Activation (`--pop`)
Once atomic replacement completes:
1. Re-open presentation: `subprocess.run(["open", "-a", "Microsoft PowerPoint", str(target_path)])`.
2. Bring window to the foreground via AppleScript:
   ```applescript
   tell application "Microsoft PowerPoint"
       activate
       set active presentation to presentation "<target_name>"
   end tell
   ```
3. Optionally navigate active window directly to slide `<num>`.

---

## 3. System Guardrails (Preventing Negative Side Effects)

1. **Unsaved Edits Protection (Zero Data Loss):**
   Never execute `close presentation saving no` on a dirty presentation (`saved == false`). Authors occasionally make rapid exploratory coordinate tweaks directly in PowerPoint; silently discarding these without confirmation violates client deliverable safety.
2. **Crash-Proof Atomic Staging (Zero Bad CRC-32):**
   Direct writes to `target_path` while PowerPoint or another process holds an open file handle risk truncated OpenXML streams. The two-phase staging pattern (`.tmp_*.pptx` ➔ `zipfile.testzip()` ➔ `os.replace()`) guarantees zero corrupt decks.
3. **Strict Sibling Slide & Master Layout Preservation:**
   In-situ replacement must strictly touch only shapes residing in the target slide's shape tree (`_spTree`). It must never alter presentation-level layouts, slide masters, custom themes, embedded notes, or sibling slides.
4. **Platform & Headless Graceful Degradation:**
   On Linux / CI environments or systems lacking Microsoft PowerPoint / macOS AppleScript support:
   - Atomic slide replacement continues to execute headlessly.
   - Desktop activation logic gracefully logs an info message (`[dim]Desktop launch skipped: AppleScript not available on this platform[/dim]`) rather than throwing fatal runtime exceptions.
5. **Headless-First Verification Rule Adherence:**
   In accordance with repository guidelines in `AGENTS.md`, desktop window activation is strictly gated by the explicit presence of the `--pop` flag. Autonomous linter audits, unit checks, and background batch compilations remain 100% headless.

---

## 4. Implementation & Normalization Checklist

- [ ] Add `PowerPointDesktopManager` in [`src/ppt_engine/diagram_v2/powerpoint_desktop.py`](../../src/ppt_engine/diagram_v2/powerpoint_desktop.py) encapsulating AppleScript queries (`get name of every presentation`, `saved of presentation`, `close presentation saving no`, `activate`).
- [ ] Implement `replace_slide_in_presentation(spec: DiagramSpec, target_path: Path, slide_index: int)` with atomic two-phase write and ZIP CRC-32 verification in [`src/ppt_engine/diagram_v2/pptx_compiler.py`](../../src/ppt_engine/diagram_v2/pptx_compiler.py).
- [ ] Expose `--target`, `--slide`, `--pop`, and `--force` options in `compile_diagram_v2_cli` in [`src/cli/diagram_v2.py`](../../src/cli/diagram_v2.py).
- [ ] Wire Phase 1 geometric audit gate into `compile_diagram_v2_cli` before triggering desktop or file-system mutations.
- [ ] Ensure bidirectional decompiler compatibility in [`src/ppt_engine/diagram_v2/reconciler.py`](../../src/ppt_engine/diagram_v2/reconciler.py) for presentations modified via in-situ slide replacement.
- [ ] Register new backlog specification in [`FEATURE_BACKLOG.md`](../../FEATURE_BACKLOG.md) and [`docs/INDEX.md`](../INDEX.md).
