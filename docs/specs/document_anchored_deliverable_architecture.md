# Spec: Canonical Document-Anchored Deliverable Architecture & Archive Lineage

## 1. Problem Statement & Anti-Pattern Analysis
Previously, visualization harvesting relied on generic domain theme heuristics (`theme_slug` such as `cdsw_aws_lambda`), which created a "vacuum cleaner" anti-pattern:
- Batch execution slides, generic lakehouse flight tests, and unrelated workstream diagrams were pulled into dedicated realtime functional deliverables.
- Standalone visualizations proliferated across `output/diagrams_v2/`, `doc_output/`, and `output/bundles/` without clear lineage.
- Multi-line descriptive cards caused text-wrapping collisions in rendered SVG/raster previews when PowerPoint word-wrapping margins were narrower than headless Cairo SVG raster limits.

## 2. The 1:1 Canonical Document-to-Bundle Contract
Deliverable visual decks must be strictly anchored to a canonical client specification document (e.g. Google Doc, Jira epic, or functional specification):

1. **Strict 1:1 Scope Boundary:**
   - Visual decks (`output/bundles/LATEST_<doc_slug>.pptx`) must mirror the figures in the canonical document slide-for-slide.
   - For example, `[ME - DBX - BSIM] - Realtime Inference - Device Whitelist` maps 1:1 to `LATEST_whitelist_system_design.pptx` containing strictly the 5 approved architectural options (Current Baseline, Option A: RDS, Option B: Lakebase, Option C: Statement API, Option E: Lambda Serverless).
   - General workstream deliverables (WS4 Batch Jobs, Customer Churn, Org Charts) must reside in separate dedicated deliverable decks and never pollute specific functional specifications.

2. **Tight `LATEST_` Boundary:**
   - Capped at 5–8 canonical architecture slides representing active target states.
   - Every slide must correspond to a named section or architectural diagram in the client specification.

## 3. The Structured `ARCHIVE_` Presentation Pattern
Superseded iterations, exploratory layouts, and retired monoliths are preserved in a dedicated historical archive deck:

1. **Single Companion Archive per Deliverable:**
   - Named `output/bundles/ARCHIVE_<doc_slug>.pptx`.
   - Never leave unlinked stray PPTX files floating in working directories.

2. **Executive Chapter Divider Punctuation:**
   - Every superseded iteration must be preceded by a high-contrast Chapter Divider title slide (`build_chapter_divider_slide` or dark navy `#0F172A` archetype).
   - Chapter Divider metadata must clearly state:
     - Section tag: `ARCHIVE SECTION XX · <ITERATION_NAME>`
     - High-contrast action title and explanatory subtitle ("Why was this superseded?").
     - Semantic status pill badge (`SUPERSEDED ITERATION`, `LAYOUT EXPERIMENTS`, `RETIRED REVISION`).

## 4. SVG & Multi-Line Card Clearance Invariant
To ensure 100% visual parity across native DrawingML PowerPoint shapes, headless SVG exports, and high-DPI PNG renders:

1. **Card Width Clearance:**
   - Any container card holding $\ge 3$ lines of subtitle/descriptive text must have an explicit minimum width threshold ($w \ge 1.25''$ on standard 13.333" $\times$ 7.5" 16:9 canvas).
2. **Side-by-Side Icon & Header Positioning:**
   - Header cards with status icons (e.g. `Safe Checker` with shield icon) must enforce `icon_layout: "side"` with sufficient horizontal card width ($w \ge 2.20''$–$3.10''$) to prevent text from overflowing or leaking outside container boundaries.
3. **Semantic Status Colors:**
   - Red (`#DC2626`) strictly for defect/bottleneck/stopped states (e.g. `shield-alert_DC2626.svg`).
   - Green (`#16A34A` / `#10B981`) for allowed/target/deployed states.
