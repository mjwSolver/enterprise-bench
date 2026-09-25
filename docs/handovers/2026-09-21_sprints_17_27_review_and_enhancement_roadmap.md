# Session Handover Blueprint: Sprints 17–27 Staged Review & Enhancement Roadmap

> **Document Type:** Live Session Review Briefing & Implementation Blueprint  
> **Date:** 2026-09-21  
> **Audience:** Subsequent Feature / Platform Implementation Subagents  
> **Author:** Review Coordinator & Enterprise Pair Programming Assistant  
> **Repository:** `enterprise-bench` | **Branch:** `main`  
> **Operating Directives:** [`AGENTS.md`](../../AGENTS.md) (Strict ZERO INTERMEDIATE UNIT TESTING)

---

## 1. Executive Purpose & Working Agreement

This document serves as the **authoritative specifications and review ledger** resulting from the live walkthrough of Sprints 17–27 (11 completed milestones). 

The primary reviewing agent is **documenting and architecting only**—no destructive refactoring or generative execution is performed during this review session. Instead, this briefing provides a following execution agent with:
1. Exact user feedback per review stage.
2. Architectural evaluations on visual enhancements (icons, images, flowcharts, alignment, font floors).
3. Concrete file targets, code paths, and configuration keys to modify.
4. Acceptance criteria and expected deliverables for the subsequent execution sprint.

---

## 2. Cross-Cutting Initiative: Universal Slug Normalization & PII Hygiene

### Problem Statement & Forensic Findings
During the Stage 1, Stage 2, and Stage 3 reviews, hardcoded legacy client identifiers (`PT Toyota Tsusho Indonesia`, `TTI`) were observed in presentation decks and configuration presets (`presets/deck_configs/closing_deck.yaml`, `kickoff_presentation.yaml`, `uat_briefing.yaml`).
- Legacy names remain embedded in production template directories (`clean_workspace/projects/TTI_Snowflake_Analytics/`).
- Hardcoded entity names violate client privacy, break deliverable portability, and force engineers to manually scour codebases when onboarding new enterprise clients.

### User Directive: Canonical Default Slug Standard
The user has formally instructed that **"Nusantara Global Logistics"** (short name / acronym: **"NGL"**) will serve as the system-wide canonical default client entity across all templates, presets, and demo outputs.
- **Strict Prohibition:** Under no circumstances should legacy client names (`Toyota`, `Tsusho`, `TTI`, `TTLC`) be hardcoded or used as fallbacks anywhere in the repository.
- If no client is specified via CLI or runtime context, all engines MUST default cleanly to `Nusantara Global Logistics`.

### Global Typography Directive: Strict Font Size Floor ($\ge 11.0\text{pt}$)
- **User Mandate:** The smallest text used across any slide or deliverable **must not be smaller than 11.0pt (and ideally 12.0pt for body copy)**.
- Micro-typography ($\le 8\text{pt}$, $7.5\text{pt}$, $7.0\text{pt}$) is strictly prohibited across all archetypes, Gantt charts, footnotes, and status indicators.

### Required Architecture for Execution Agent
1. **Canonical Registry Defaults (`src/core/slug_registry.py`):**
   - Update `EngagementContext` and `STANDARD_SLUG_MAP` to use canonical defaults:
     ```python
     DEFAULT_CLIENT_COMPANY_NAME = "Nusantara Global Logistics"
     DEFAULT_CLIENT_SHORT_NAME = "NGL"
     DEFAULT_CLIENT_ADDRESS = "Gedung Cyber 2, Lt. 18, Jl. H.R. Rasuna Said, Jakarta Selatan"
     DEFAULT_PROJECT_NAME = "Enterprise Financial Intelligence & Cloud Analytics Platform"
     DEFAULT_VENDOR_COMPANY_NAME = "PT Metrodata Electronics Tbk"
     DEFAULT_VENDOR_SHORT_NAME = "Metrodata"
     DEFAULT_VENDOR_DIVISION = "Data & AI Modernization Practice"
     ```
2. **Declarative Preset Normalization (`presets/deck_configs/*.yaml`):**
   - Replace all instances of `PT Toyota Tsusho Indonesia` with `[CLIENT_COMPANY_NAME]`.
   - Replace all instances of `TTI` with `[CLIENT_SHORT_NAME]`.
   - Update `metadata.confidentiality` lines to:
     `"[CLIENT_COMPANY_NAME] & [VENDOR_COMPANY_NAME]  |  Confidential"`
3. **Automated Pre-Save Shape Traversal Middleware (`src/ppt_engine/`):**
   - In `PitchDeckBuilder.save()`, `ClosingDeckBuilder.save()`, and `WeeklyProgressDeckBuilder.save()`:
     - Implement a recursive text shape scanner traversing all slide shapes, group shapes, and table cells:
       ```python
       def _substitute_slugs(text_frame, context: EngagementContext):
           for paragraph in text_frame.paragraphs:
               for run in paragraph.runs:
                   run.text = context.substitute(run.text)
       ```
     - When CLI `--context` is omitted, hydrate with `EngagementContext.default_ngl()`.
4. **CLI Contract Binding (`src/cli.py`):**
   - Ensure `bench ppt build-deck` accepts `--context <path.json>` or CLI flags `--client "[CLIENT_NAME]"` to dynamically hydrate the deck at runtime.

---

## 3. Stage 1: Project Closing & Maintenance Transition Deck (`5.1`)

- **Artifact Reviewed:** [`output/presentations/5.1_Project_Closing_Deck_Modernized.pptx`](../../output/presentations/5.1_Project_Closing_Deck_Modernized.pptx) (9 slides)
- **Source Configuration:** [`presets/deck_configs/closing_deck.yaml`](../../presets/deck_configs/closing_deck.yaml)
- **Builder Implementation:** [`src/ppt_engine/closing_deck.py`](../../src/ppt_engine/closing_deck.py)

### User Feedback
1. **Zero Visual Elements:** The closing deck currently contains no icons, no images, and no flowcharts—it is exclusively shape cards and typography.
2. **Hardcoded Legacy Client Entity:** Client name appeared as `"PT Toyota Tsusho Indonesia"` instead of normalized slugs.

### Architectural Evaluation: Icons, Images & Flowcharts

| Component | Target Slide(s) | Feasibility | Recommendation | Architectural Implementation Pattern |
| :--- | :--- | :--- | :--- | :--- |
| **Lucide Brand Icons** | Slide 02 (Agenda 01–06)<br>Slide 03 (Capability Cards)<br>Slide 04 (Deliverables)<br>Slide 05 (Credentials)<br>Slide 06 (Service Model) | **High** | **Highly Recommended** | Use `IconEngine.get_icon_svg(name)` tinted with `theme.accent`. Replace raw format text badges (`[DOCX]`, `[PPTX]`) with file glyphs (`file-text`, `presentation`, `table`, `code`). Add category icons to agenda numbers (`compass`, `package-check`, `file-signature`, `shield-check`, `git-pull-request`, `bar-chart-3`). |
| **Enterprise Hero Images / Scrims** | Slide 01 (Cover)<br>Slide 09 (Closing) | **Medium** | **Selective / Balanced** | Retain clean typography, but add subtle abstract enterprise background or dual-panel dark scrim (`#0B132B` at 45% alpha) on right 1/3 hero plate, echoing `build_chapter_divider_slide`. Avoid embedding images inside data tables (Slides 04/05). |
| **Process Flowchart / Diagram** | Slide 07 (Support Workflow) | **High** | **Highly Recommended** | Currently Slide 07 uses 4 simple boxes with raw right arrows (`MSO_SHAPE.RIGHT_ARROW`). Upgrade to a formal swimlane process flowchart (Client vs. Vendor L1/L2 triage, Lead Dev remediation, Client sign-off) via `DiagramRenderer` or connected OpenXML vector nodes with SLA callouts. |

### Concrete Action Items for Next Agent
1. **Update `presets/deck_configs/closing_deck.yaml`:**
   - Swap client strings for `[CLIENT_COMPANY_NAME]` and `[CLIENT_SHORT_NAME]`.
   - Add `icon` attributes to all `agenda_items`, `capability_phases`, and `service_pillars`.
2. **Refactor `src/ppt_engine/closing_deck.py`:**
   - In `build_agenda_slide`: allocate an icon slot adjacent to the number badge.
   - In `build_capability_review_slide`: integrate `add_card_with_harmonized_icon`.
   - In `build_deliverables_inventory_slide`: render vector file format glyphs alongside deliverable titles.
   - In `build_support_workflow_slide`: re-architect from flat boxes into a multi-tier horizontal workflow with step icons and clear client/vendor swimlane tags.
   - In `ClosingDeckBuilder.save`: integrate recursive slug substitution.
3. **Output Re-generation:**
   - Recompile `output/presentations/5.1_Project_Closing_Deck_Modernized.pptx`.
   - Re-export preview images to `output/presentations/previews/closing/` (slides 01–09).

---

## 4. Stage 2: Weekly Progress Report & S-Curve Synchronization (`4.2`)

- **Artifact Reviewed:** [`output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized_Chart.pptx`](../../output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized_Chart.pptx) (11 slides)
- **High-DPI Chart:** [`output/presentations/charts/s_curve_weekly.png`](../../output/presentations/charts/s_curve_weekly.png)
- **Spreadsheet Source:** [`clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Timeline_Update_Template.xlsx`](../../clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.2_Weekly_Progress_Timeline_Update_Template.xlsx)
- **Builder Implementation:** [`src/ppt_engine/weekly_progress_deck.py`](../../src/ppt_engine/weekly_progress_deck.py)

### User Feedback & Approvals
1. **Slide 04 (Overall Progress & S-Curve):** **APPROVED**. The embedded high-DPI S-Curve line chart and KPI header cards significantly elevate presentation quality.
2. **Slide 07 (Milestone Status Vertical Alignment Defect):** 
   - *User Observation:* On a horizontal plane, the rounded status indicator pill on the far right (`COMPLETED`, green) is vertically centered in the row card, but the text elements (`01`, `Kick-off Meeting`, `16 Dec 2025`) are visibly aligned to the top edge of the card rather than vertically centered.
   - *Forensic Diagnosis:* Validated 100%. In `src/ppt_engine/weekly_progress_deck.py` (lines 1213–1264), text boxes `tb0`, `tb1`, `tb2`, and `tb3` are created with `cur_ry + pad_top` and do NOT set `vertical_anchor`, defaulting in python-pptx to `MSO_ANCHOR.TOP`. Meanwhile, the status pill (`_add_status_pill`, line 183) explicitly sets `pill.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE` and centers `pill_y = cur_ry + (row_h - pill_h) / 2`.
   - *Remedy for Next Agent:*
     - Import `from pptx.enum.text import MSO_ANCHOR`.
     - In `build_milestone_status`: Set text box height to the full `row_h` (`add_textbox(x, cur_ry, col_w, row_h)`).
     - Explicitly set `tf.vertical_anchor = MSO_ANCHOR.MIDDLE` across `tf0`, `tf1`, `tf2`, and `tf3`.
     - Set `tf.margin_top = 0` and `tf.margin_bottom = 0`.
3. **Slide 08 & 09 (RAID Logs - Missing Bullets & Language Mixing):**
   - *Missing Bullets:* In Slide 08 (Risk Register), mitigation items must render with bullet glyphs (`•`) and hanging indents (`marL="288000"`, `indent="-288000"`) via `_add_bullet_paragraph`, rather than flat unstructured text blocks.
   - *Language Contamination:* Slides 08 and 09 mix English and Indonesian (e.g. English card headers and titles paired with Indonesian descriptions and mitigations pulled from `4.5_Risk_Register_Template.xlsx`).
   - *Remedy for Next Agent:*
     - Enforce a strict single-language baseline.
     - Master templates and default presets must output **100% English** first.
     - Indonesian translations must be generated through the localized catalog (`presets/locales/id.yaml` and `locale_engine.py`) as a dedicated localized build, avoiding hybrid language contamination.

---

## 5. Stage 3: Testing Onboarding & Initiation Collateral (`1.1` & `3.4`)

- **Artifact Reviewed:** [`output/presentations/1.1_Project_Kick-off_Material_Modernized.pptx`](../../output/presentations/1.1_Project_Kick-off_Material_Modernized.pptx) (19 slides)
- **Source Configuration:** [`presets/deck_configs/kickoff_presentation.yaml`](../../presets/deck_configs/kickoff_presentation.yaml)
- **Builder Implementation:** [`src/ppt_engine/pitch_deck.py`](../../src/ppt_engine/pitch_deck.py) / [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py)

### User Feedback & Critical Defect Register

1. **Slide Ordering / Numbering Mismatch:**
   - *Observation:* Governance Org Structure was expected on Slide 04, but Slide 04 was rendered as `"Five Strategic Objectives Guide the Financial Analytics Modernization Journey"`. Forensic check confirms Governance Org Structure is actually placed at **Slide 06** in `kickoff_presentation.yaml` (line 214).
   - *Action for Next Agent:* Reconcile slide numbers across documentation and verify whether Strategic Objectives (Slide 4) and Stakeholder Roles (Slide 5) should be moved after Governance Org Structure.
2. **Slide 10 Target Architecture Screenshot Defect:**
   - *Observation:* Slide 10 embeds an ugly, poorly formatted raster screenshot (`snowflake_solution_architecture.png`).
   - *Remedy for Next Agent:* Completely remove the static raster image embed from `build_snowflake_data_pipeline_slide`. Rebuild Slide 10 as a native vector container architecture using `DiagramRenderer` or OpenXML card shapes with official SVG logos (`kafka`, `snowflake`, `dbt`, `streamlit`) and orange highlight callout boxes to emphasize key architectural transformations.
3. **Slide 12 (Gantt Timeline) Critical Collision & Shadow Defects:**
   - *Trailing Text Canvas Bleed:* Milestone diamond for Week 24 has label `"Final Project Closure & Acceptance"` placed at `mx + diam_size + Inches(0.05)`, which pushes the right edge to $X \approx 14.7''$, bleeding completely off the $13.333''$ slide canvas.
     - *Remedy:* If `mx + label_width > Inches(12.80)`, dynamically anchor the text box to the **left** of the diamond (`mx - label_width - Inches(0.08)`) with right-aligned text.
   - *Text Overflow in Duration Bars:* Narrow duration bars (1–2 weeks) have long task titles (e.g. `"Assessment, Requirements & FSD Drafting"`, `"Streamlit 8 Financial Modules Development"`) that overflow outside their rectangle, colliding with adjacent bars.
     - *Remedy:* Compare `bar_w` against estimated text width; if text does not fit within `bar_w`, render the task label externally above/below the bar or expand row spacing.
   - *Prohibited Drop Shadows:* Gantt duration bars and containers still show drop shadows despite explicit user instructions for flat geometry.
     - *Remedy:* Enforce `shape.shadow.inherit = False` across all timeline shapes.
   - *Micro-Typography Elimination:* Replace `Pt(7.5)` task fonts and `Pt(7.0)` tag fonts with a minimum floor of $\ge 11.0\text{pt}$ (or scaled appropriately with generous row height).
4. **Slide 19 (Thank You / Closing) Staff Contacts vs. Clean Default:**
   - *Observation:* Slide 19 currently hardcodes real employee names and emails (`Agus Pramono`, `Dian Eka`, `Vicko Bhayyu`) as default contact cards in `build_thank_you_slide` (`consulting_archetypes.py:5406-5412`).
   - *Remedy for Next Agent:* Modify `build_thank_you_slide` to default to a **clean corporate closing** (Thank You title, division tagline, office address/general contact) with `contacts=None` / `show_staff_contacts=False` by default. Individual staff contacts must be strictly opt-in and parameterized.
5. **Asset Deduplication:** Avoid copy-pasting visual assets across different pitch and kickoff decks; each deliverable must feature tailored, distinct visuals.

---

## 6. Stage 4: Automated Change Request Governance Suite (`CR_07`)

- **Artifacts Under Review:**
  - Form: [`output/TTI_Snowflake_Analytics/change_requests/CR_07/Change_Request_Form_CR_07.docx`](../../output/TTI_Snowflake_Analytics/change_requests/CR_07/Change_Request_Form_CR_07.docx)
  - Scoping Workbook: [`output/TTI_Snowflake_Analytics/change_requests/CR_07/CR_Scoping_and_Mandays_CR_07.xlsx`](../../output/TTI_Snowflake_Analytics/change_requests/CR_07/CR_Scoping_and_Mandays_CR_07.xlsx)
  - BAST Certificate: [`output/TTI_Snowflake_Analytics/change_requests/CR_07/BAST_Change_Request_Draft_CR_07.docx`](../../output/TTI_Snowflake_Analytics/change_requests/CR_07/BAST_Change_Request_Draft_CR_07.docx)
  - Change Log Ledger: [`output/TTI_Snowflake_Analytics/change_requests/CR_07/Change_Log_Ledger_Updated_CR_07.xlsx`](../../output/TTI_Snowflake_Analytics/change_requests/CR_07/Change_Log_Ledger_Updated_CR_07.xlsx)
- **Engine Implementation:** [`src/core/change_request.py`](../../src/core/change_request.py) | CLI: `bench cr file`
- **Status:** **Active Review In Progress (Opened on User Desktop)**

### Review Focus Points & User Watchouts
1. **Single-Command Orchestration:**
   - All four documents are generated synchronously from a single CLI invocation (`bench cr file`).
2. **Data Consistency & Manday Math:**
   - Verify that scope descriptions, manday counts (e.g. 15 mandays), rates, and monetary totals calculate and stamp identically across Word and Excel.
3. **Client Slug & Directory Path Normalization:**
   - Notice that the output directory and file headers currently reflect legacy pathing (`output/TTI_Snowflake_Analytics/change_requests/CR_07/`).
   - Flag migration to `output/NGL_Snowflake_Analytics/` or `output/change_requests/CR_07/` using `[CLIENT_COMPANY_NAME]` / `[CLIENT_SHORT_NAME]`.
4. **Signatory & Approval Blocks:**
   - Check legal signatory blocks in `Change_Request_Form_CR_07.docx` and `BAST_Change_Request_Draft_CR_07.docx` for clean layout and unboxed formatting.

### User Feedback & Approvals
1. **Overall Verification:** **APPROVED**. Single-command generation (`bench cr file`), synchronized scope descriptions, and manday calculation formulas across Word and Excel verified and confirmed.
2. **Toyota Logo Defect in Header:**
   - *Observation:* `Change_Request_Form_CR_07.docx` still contained the legacy Toyota Tsusho Indonesia logo banner (`image3.png`) embedded inside the top-right header table cell (`word/header2.xml`).
   - *Action Completed:* The reviewing agent immediately purged `<w:drawing>` and stripped `image3.png` from both [`output/TTI_Snowflake_Analytics/change_requests/CR_07/Change_Request_Form_CR_07.docx`](../../output/TTI_Snowflake_Analytics/change_requests/CR_07/Change_Request_Form_CR_07.docx) and master template [`clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.4_Change_Request_Form_Template.docx`](../../clean_workspace/projects/TTI_Snowflake_Analytics/05_monitoring/4.4_Change_Request_Form_Template.docx). Integrity verified with 19 paragraphs and 7 tables.
3. **Directory Path & Client Normalization:**
   - Next agent must ensure output paths resolve via `EngagementContext` to `output/NGL_Snowflake_Analytics/change_requests/` or `output/change_requests/` rather than hardcoded `TTI_Snowflake_Analytics`.

---

## 7. Consolidated Execution Checklist for Subsequent Agent

The downstream implementation subagent tasked with executing this blueprint must follow this prioritized sprint plan:

- [ ] **Phase 1: Universal Slug & PII Normalization (`Nusantara Global Logistics`)**
  - [ ] Set `DEFAULT_CLIENT_COMPANY_NAME = "Nusantara Global Logistics"` and `DEFAULT_CLIENT_SHORT_NAME = "NGL"` in `src/core/slug_registry.py`.
  - [ ] Normalize all YAML presets (`closing_deck.yaml`, `kickoff_presentation.yaml`, `uat_briefing.yaml`, `weekly_progress.yaml`) to replace hardcoded `PT Toyota Tsusho Indonesia` / `TTI` with `[CLIENT_COMPANY_NAME]` / `[CLIENT_SHORT_NAME]`.
  - [ ] Integrate recursive text shape traversal in `PitchDeckBuilder.save()`, `ClosingDeckBuilder.save()`, and `WeeklyProgressDeckBuilder.save()` substituting declared slugs before writing to disk.
  - [ ] Enforce the global optical font size floor ($\ge 11.0\text{pt}$ minimum, $\ge 12.0\text{pt}$ body) across all deck builders.

- [ ] **Phase 2: Project Closing Deck (`5.1`) Visual Enrichment**
  - [ ] Add Lucide vector icons tinted with `theme.accent` to Slide 02 (Agenda 01–06), Slide 03 (Capabilities), Slide 04 (Format badges: `file-text`, `presentation`, `table`, `code`), and Slide 05 (Cloud archive & survey credentials).
  - [ ] Rebuild Slide 07 (Maintenance Support Workflow) from flat boxes into a formal swimlane process flowchart (Client vs. Vendor triage, Lead Dev remediation, SLA targets).
  - [ ] Recompile `output/presentations/5.1_Project_Closing_Deck_Modernized.pptx` and regenerate previews.

- [ ] **Phase 3: Weekly Progress Report (`4.2`) Typography & Language Purity**
  - [ ] Fix Slide 07 row vertical alignment defect: Set text box height to full `row_h` and set `vertical_anchor = MSO_ANCHOR.MIDDLE` on `tf0`, `tf1`, `tf2`, `tf3` in `src/ppt_engine/weekly_progress_deck.py:1213-1264`.
  - [ ] Fix Slide 08 risk register mitigations to render with `_add_bullet_paragraph` and native hanging indents (`marL="288000"`, `indent="-288000"`).
  - [ ] Eliminate English/Indonesian hybrid mixing in Slides 08 & 09; establish pure 100% English baseline.
  - [ ] Recompile `output/presentations/4.2_Weekly_Progress_Report_Deck_Modernized_Chart.pptx` and regenerate previews.

- [ ] **Phase 4: Project Kick-off Material (`1.1`) Defect Rectification**
  - [ ] Rebuild Slide 10 target architecture natively as OpenXML vector container cards with SVG tech logos and orange callouts, deprecating `snowflake_solution_architecture.png`.
  - [ ] Fix Slide 12 Gantt timeline: Flip Week 24 milestone diamond label leftwards (`mx - label_w - Inches(0.08)`) to eliminate slide canvas bleed ($X > 13.333''$).
  - [ ] Prevent duration bar text overflow on narrow bars (render externally or expand row spacing).
  - [ ] Strip drop shadows from all Gantt shapes (`shape.shadow.inherit = False`).
  - [ ] Scale Gantt task font sizes from `Pt(7.5)` to $\ge 11.0\text{pt}$.
  - [ ] Configure Slide 19 `build_thank_you_slide` to default to clean corporate closing without hardcoded staff names/emails.
  - [ ] Recompile `output/presentations/1.1_Project_Kick-off_Material_Modernized.pptx` and regenerate previews.

- [ ] **Phase 5: Automated Change Request Suite (`CR_07`)**
  - [ ] Verify `Change_Request_Form_CR_07.docx` and `4.4_Change_Request_Form_Template.docx` remain completely free of legacy logos.
  - [ ] Route CR generation destination dynamically using `EngagementContext` client slug.
