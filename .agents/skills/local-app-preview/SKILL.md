---
name: local-app-preview
description: >-
  Launches local desktop applications (Word, Excel, PowerPoint, Preview, Draw.io) on macOS ONLY upon explicit user command ("pop it", "show me", "open on desktop", "open in finder"). Enforces headless-first verification: NEVER launch or activate desktop apps autonomously, proactively, or during automated test/audit loops.
---

# Local Desktop Application Preview & Review Skill (`local-app-preview`)

> **Target Agent Role:** Review Coordinator / Solutions Consultant / Pair Programming Assistant  
> **Mission:** Provide on-demand desktop preview of generated deliverables in native macOS applications (Microsoft Office, Preview, Draw.io) strictly when requested by the user, while enforcing headless-first verification across all automated agent workflows.

---

## 🚨 MANDATORY INVARIANT: HEADLESS-FIRST VERIFICATION

> [!CRITICAL]
> **ZERO DISRUPTIVE WINDOW POPS DURING AUTONOMOUS WORKFLOWS**
> All agent visual verification, spatial clearance audits, and artifact quality checks must be 100% headless (using background CLI tools like `uv run bench diagram v2 audit`, headless SVG/PNG exports, and code inspection).
> 
> Agents must **NEVER** proactively launch desktop applications (`open -a`) or execute window-focusing AppleScript (`osascript -e 'tell application "<App>" to activate'`) during generation, verification, or sprint execution. Disrupting the user's active screen during meetings or deep work is strictly prohibited.

---

## 1. When to Use This Skill (Explicit Triggers ONLY)

Launch desktop applications **ONLY** when the user explicitly issues an intentional desktop review trigger:

1. **Intentional Casual Shorthand:**
   - `"pop it"`
   - `"show me"`
   - `"open on desktop"`
   - `"open in finder"`
2. **Explicit Format/App Requests:**
   - *"open that doc in Word"*
   - *"show me the spreadsheet in Excel"*
   - *"launch the deck in PowerPoint"*
   - *"open the diagram in Draw.io"*

### 🚫 Strictly Prohibited Actions:
- Auto-launching applications upon file creation or milestone completion.
- Proactively invoking `open` or `osascript activate` as part of "checking" visual quality.
- Stealing window focus from user applications during background tool runs.

---

## 2. Command Reference by Deliverable Format

Execute these commands in zsh via `run_command` **only after receiving an explicit user trigger**:

### 📄 Microsoft Word (`.docx`)
```bash
# Open in Microsoft Word (explicit trigger only):
open -a "Microsoft Word" "<path_to_file.docx>"

# Bring window to front only if user explicitly asked to focus/view it:
osascript -e 'tell application "Microsoft Word" to activate'
```

### 📊 Microsoft Excel (`.xlsx`)
```bash
# Open in Microsoft Excel (explicit trigger only):
open -a "Microsoft Excel" "<path_to_file.xlsx>"

# Bring window to front only if user explicitly asked to focus/view it:
osascript -e 'tell application "Microsoft Excel" to activate'
```

### 📽 Microsoft PowerPoint (`.pptx`)
```bash
# Open in Microsoft PowerPoint (explicit trigger only):
open -a "Microsoft PowerPoint" "<path_to_file.pptx>"

# Bring window to front only if user explicitly asked to focus/view it:
osascript -e 'tell application "Microsoft PowerPoint" to activate'
```

#### 🔄 In-Situ Recompilation & Refresh Protocol (Dismiss Target Presentation)
When modifying, re-generating, or micro-patching a PowerPoint file previously opened on desktop:
1. Microsoft PowerPoint for Mac does **not** auto-reload modified files from disk; it caches the open presentation in memory.
2. Saving or recompiling while the presentation is open results in stale preview display and creates an overwrite collision risk (AutoSave or `Cmd+S` overwrites disk changes).
3. Always dismiss the target presentation window before saving new changes to disk (without quitting PowerPoint or closing other open decks):
```bash
TARGET_NAME="$(basename "<path_to_file.pptx>")"
if pgrep -x "Microsoft PowerPoint" >/dev/null 2>&1; then
  osascript -e '
  on run argv
    set targetName to item 1 of argv
    tell application "Microsoft PowerPoint"
      repeat with p in presentations
        if name of p is targetName then
          close p saving no
        end if
      end repeat
    end tell
  end run' "$TARGET_NAME"
fi
```
*(Note: `src.cli.utils.close_target_presentation` executes this check and dismissal automatically in compilation and CLI generation pipelines).*

### 📐 Diagrams (`.drawio`, `.svg`, `.png`) & Images
```bash
# Open vector diagrams or images in macOS Preview:
open -a "Preview" "<path_to_file.png>"

# Open diagrams in Draw.io (if installed) or default viewer:
open "<path_to_file.drawio>"

# Reveal in macOS Finder:
open -R "<path_to_file>"
```

---

## 3. Best Practices & Safety Guardrails

1. **Verify File Existence:**
   Always confirm the target file exists before issuing an `open` command.
2. **Path Quoting:**
   Wrap all file paths in double quotes to handle paths with spaces or symbols.
3. **Headless Verification Gate:**
   Prior to offering desktop preview or answering queries about layout correctness, always perform headless verification:
   ```bash
   uv run bench diagram v2 audit <spec.yaml> --strict
   ```
4. **Respect User Focus:**
   Never invoke AppleScript activation in unattended loops or without explicit user direction.
