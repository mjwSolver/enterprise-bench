---
name: local-app-preview
description: >-
  Launches and previews locally generated documents (Word .docx, Excel .xlsx, PowerPoint .pptx, PDF, Draw.io) on the user's desktop application environment using macOS CLI (`open`) and AppleScript (`osascript`). Use whenever the user asks to view/open deliverables on their device, or proactively suggest opening artifacts for rapid visual QA, stakeholder reviews, and feedback iterations.
---

# Local Desktop Application Preview & Review Skill (`local-app-preview`)

> **Target Agent Role:** Review Coordinator / Solutions Consultant / Pair Programming Assistant  
> **Mission:** Seamlessly launch and focus generated project deliverables in native desktop applications (Microsoft Office, Preview, Draw.io) on macOS using shell commands and AppleScript, accelerating user feedback and visual sign-offs.

---

## 1. When to Use This Skill

1. **Explicit User Request:**
   - *"open that doc in Word"*, *"show me the spreadsheet in Excel"*, *"launch the deck in PowerPoint"*, *"open the BAST certificate"*.
2. **Proactive Suggestion on Milestone / Delivery Completion:**
   - After generating or stamping deliverables, offer to launch them directly:
     > *"Would you like me to open `01_Project_XYZ_Executive_Strategy_Deck.pptx` in PowerPoint or the signed `01_PKS_Contract_Apex_Global.docx` in Word for your review?"*

---

## 2. Command Reference by Deliverable Format

All commands execute cleanly in zsh via `run_command`:

### 📄 Microsoft Word (`.docx`)
```bash
# Open directly in Microsoft Word and bring window to front:
open -a "Microsoft Word" "<path_to_file.docx>" && osascript -e 'tell application "Microsoft Word" to activate'

# Fallback (system default handler):
open "<path_to_file.docx>"
```

### 📊 Microsoft Excel (`.xlsx`)
```bash
# Open directly in Microsoft Excel and bring window to front:
open -a "Microsoft Excel" "<path_to_file.xlsx>" && osascript -e 'tell application "Microsoft Excel" to activate'

# Fallback (system default handler):
open "<path_to_file.xlsx>"
```

### 📽 Microsoft PowerPoint (`.pptx`)
```bash
# Open directly in Microsoft PowerPoint and bring window to front:
open -a "Microsoft PowerPoint" "<path_to_file.pptx>" && osascript -e 'tell application "Microsoft PowerPoint" to activate'

# Fallback (system default handler):
open "<path_to_file.pptx>"
```

### 📐 Diagrams (`.drawio`, `.svg`, `.png`) & Images
```bash
# Open vector diagrams or images in macOS Preview:
open -a "Preview" "<path_to_file.png>"

# Open diagrams in Draw.io (if desktop app installed) or default browser/viewer:
open "<path_to_file.drawio>"
```

---

## 3. Best Practices & Safety Guardrails

1. **Verify File Existence:**
   Always confirm the target file exists before issuing the `open` command.
2. **Path Quoting:**
   Wrap all file paths in double quotes to handle directory names with spaces or underscores properly.
3. **Non-Blocking Execution:**
   The `open` command launches applications asynchronously in macOS without blocking terminal execution.
4. **App Activation with `osascript`:**
   Chaining `osascript -e 'tell application "<AppName>" to activate'` ensures macOS immediately raises and focuses the newly opened window rather than leaving it minimized behind other applications.
