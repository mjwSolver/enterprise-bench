# VERSION_LOG.md — Diagram Engine V2 Release Ledger

> **NOTE:** This version log is compiled strictly for packaging and gzip/zip distribution tracking purposes across portable client workstations and sandbox environments. All distribution archives must explicitly stamp the release version in their filename (`diagram_engine_v2_portable_v<SEMVER>_<TIMESTAMP>.zip`).

---

### Release 6: v2.3 — ASCII Layout Wireframing, Typographic Density Guardrail & Headless Vision Verification
- **Release Timestamp:** `2026-10-31 20:45:00 +0700`
- **Distribution Archive:** `diagram_engine_v2_portable_v2.3_20261031_204500.zip`
- **Engineering Signature:** `[MJW/AGY]` embedded across core subsystem modules (`ideas.py`, `auditor.py`, `models.py`, `src/cli/diagram_v2.py`).
- **What's Changed vs. Release 5 (v2.2):**
  - **Canonical Layout Patterns & ASCII Wireframe Engine (`ideas.py`):**
    - Introduced canonical pattern registry (`3-swimlane`, `interwoven-hub`, `data-pipeline`, `runbook-grid`).
    - Added `render_ascii_wireframe(spec)` producing instant, human-readable terminal wireframes of containers, nodes, and flows for non-blocking conversational preambles.
    - Added unified CLI command `bench diagram v2 ideas [list|preview|scaffold]` and `--ascii` flag to `bench diagram v2 compile`.
  - **Check #16: Typographic Density & Font Floor Guardrail (`auditor.py`):**
    - Enforced hard 11pt font floor (`title_pt >= 11.0`, `subtitle_pt >= 9.5`).
    - Added Check #16 (`EXCESSIVE_NODE_DENSITY`) to `Tier1GeometricLinter`, failing when containers cram excessive nodes into narrow footprints and prescribing **Semantic Aggregation** ($\le 3\text{--}4$ cards) over font squishing.
    - Implemented `allow_dense_typography: bool = False` bypass valve in `ContainerSpec` and `DiagramSpec`, safely relaxing font floor to 8pt for Gear 3 reading/appendix decks and regulatory footnotes.
  - **Decoupled Instruction Contract (`DIAGRAM_INSTRUCTIONS.md`):**
    - Codified agent behavior rules into `docs/specs/DIAGRAM_INSTRUCTIONS.md` without polluting root monorepo `AGENTS.md` context when bundled or distributed.
  - **Headless Rasterization Specification (`docs/specs/headless_rendering_setup.md`):**
    - Documented cross-platform setup (`soffice` + `poppler`) for macOS, Linux, and Windows, formalizing the graceful fallback to Tier 1 geometric linting when headless binaries are absent.

---

### Release 5: v2.2 — Declarative Architecture Guardrails & Native Inspection/Patching Engine
- **Release Timestamp:** `2026-10-26 15:30:00 +0700`
- **Distribution Archive:** `diagram_engine_v2_portable_v2.2_20261026_160000.zip`
- **Engineering Signature:** `[MJW/AGY]` embedded across core subsystem modules (`src/cli/utils.py`, `compiler.py`, `pptx_compiler.py`, `auditor.py`, `models.py`, `linter.py`, `patcher.py`, `inspector.py`).
- **What's Changed vs. Release 4 (v2.1):**
  - **Mechanical Declarative Architecture Guardrail (`bench ppt lint` & pre-commit hook):**
    - Multi-signal AST heuristic scanner in `src/ppt_engine/linter.py` analyzing Python AST for raw imperative coordinate math, raw shape generation loops, and layout boilerplate, blocking imperative regression.
    - Automated pre-commit hook integration (`.git/hooks/pre-commit`) enforcing zero monolithic python script generation.
  - **Native In-Situ Micro-Patching Subsystem (`bench ppt patch`, `bench ppt replace-image`):**
    - Localized shape text, color, badge, and image replacements on existing PowerPoint decks without altering canvas grids or coordinates.
  - **Headless Inspection Engine (`bench ppt view`, `bench doc view`):**
    - Instant slide/document hierarchy, shape count, and text tree inspections directly in terminal.
  - **Architecture Decision Record & Efficiency Benchmark:**
    - Formally documented `ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md` proving >90% token reduction per review cycle and turnaround compression from 1–2 days down to 2.2 hours.
  - **Explicit Version Stamping Standard:**
    - Standardized all past and future distribution archives to mandate explicit semver stamping (`diagram_engine_v2_portable_v<SEMVER>_<TIMESTAMP>.zip`).

---

### Release 4: v2.1 — Desktop Preview Lifecycle, Spatial Clearance Hardening & Schema Resilience
- **Release Timestamp:** `2026-10-24 16:45:00 +0700`
- **Distribution Archive:** `diagram_engine_v2_portable_v2.1_20261024_170143.zip`
- **Engineering Signature:** `[MJW/AGY]` embedded across core subsystem modules (`src/cli/utils.py`, `compiler.py`, `pptx_compiler.py`, `auditor.py`, `models.py`).
- **What's Changed vs. Release 3 (v2.0 / prior releases):**
  - **PowerPoint Preview Lifecycle & Target Deck Dismissal (`src/cli/utils.py`, `pptx_compiler.py`):**
    - Added `close_target_presentation(path: Path | str) -> bool` to `src/cli/utils.py` with headless-first safety check (`pgrep -x "Microsoft PowerPoint"`), closing only the matching presentation window via targeted AppleScript without quitting PowerPoint or affecting other active slide decks.
    - Integrated automatic target presentation dismissal into `PPTXCompiler.compile_presentation` immediately prior to saving to disk, eliminating macOS in-memory PowerPoint window caches and preventing AutoSave/Cmd+S file-overwrite race conditions.
    - Documented dismissal requirements in `.agents/skills/local-app-preview/SKILL.md` (Section 2.1) and `AGENTS.md` (Lanes 2 & 3).
  - **Diagram Engine V2 Overlap & Spatial Clearance Hardening (`auditor.py`):**
    - Dynamic multi-line container label height calculation: In `check_container_label_occlusion` and `check_container_containment`, wrapped text height is now calculated dynamically based on font size and container width (`lines = max(1, math.ceil(raw_text_w / max_label_w))`, `label_h = max(36.0, lines * line_h + 12.0)`), replacing the hardcoded 36px stub.
    - Elevated `CONTAINER_LABEL_OCCLUSION` from `WARNING` to `CRITICAL` on substantial vertical overlap (`oy > 10.0`), preventing compiled collisions in headless audits.
    - Added Rule 3b-2 (`check_peer_container_collisions()`) to `auditor.py` to detect unintended physical overlaps between non-nested sibling containers, registered directly into `lint()`.
  - **Schema Resilience & Asset Diagnostics (`models.py`, `pptx_compiler.py`):**
    - Added `@model_validator(mode="before")` to `DiagramSpec` in `models.py` remapping `connectors` and `arrows` keys to `flows`, preventing silent Pydantic field dropping when LLMs write alternate keys.
    - Added `icon` and `icon_emoji` optional fields to `ContainerSpec` in `models.py`.
    - Replaced silent `except: pass` with explicit warnings in `PPTXCompiler._compile_node` when an icon slug fails resolution in `IconRegistry`.

---

### Release 3: v2.2.0 — Dynamic Contrast, Theme Tokens & Distribution Provenance
- **Release Timestamp:** `2026-10-20 08:55:00 +0700`
- **Distribution Archive:** `diagram_engine_v2_portable_v2.2_20261020_085531.zip`
- **Engineering Signature:** `[MJW/AGY]` embedded across core subsystem modules (`__init__.py`, `compiler.py`, `contrast.py`, `auditor.py`, `models.py`).
- **What's Changed vs. Release 2 (v2.1.0):**
  - **Readability & Dynamic Contrast Subsystem (`contrast.py`):** Bundles WCAG 2.1 relative luminance and contrast ratios (`calculate_contrast_ratio`, `harmonize_diagram_contrast`), auto-inverting low-contrast text and neutralizing white card washouts.
  - **Dynamic Vector Icon Tinting (`icon_engine.py`):** Added inline vector icon recoloring with multi-color vendor logo detection (`is_multicolor_vendor_logo`) to protect multi-hue brand marks (AWS, Databricks, Snowflake).
  - **Auditor & Linter Expansion (`auditor.py`):** Codified Rule 18 (Asset Resolution Verification) and Rule 19 (Automated WCAG Readability / Contrast Gate), raising the total geometric rule set to 19 rules.
  - **Theme Palette & Token Resolver (`models.py`):** Native resolution for brand themes and auto-inversion color tokens in declarative YAML specs.
  - **Packaging Provenance:** Added `VERSION_LOG.md` distribution ledger and `[MJW/AGY]` comment signatures.

---

### Release 2: v2.1.0 — Visual QA, Geometry Rules & Canonical Asset Bundling
- **Release Timestamp:** `2026-10-19 21:41:16 +0700`
- **Distribution Archive:** `diagram_engine_v2_portable_v2.1_20261019_214116.zip`
- **What's Changed vs. Release 1 (v2.0.0):**
  - **Standalone Asset Pipeline:** Fully bundled complete vector icon libraries (`assets/icons/`) and vendor logos (`assets/logos/`) with path-independent resolution.
  - **Adversarial Visual QA & Reconciler:** Integrated `visual_verifier.py`, `reconciler.py`, and `stray_consolidator.py`.
  - **Reference Deliverables & Developer Onboarding:** Added `candidate_reference_slide_3.png` in archive root and user workspace isolation (`my_specs/`, `my_output/`).
  - **17 Geometric Collision Rules:** Expanded auditor with corridor clearance, ceiling bypass, and header headroom validation.

---

### Release 1: v2.0.0 — Greenfield Declarative Compiler Core
- **Release Timestamp:** `2026-10-19 16:59:51 +0700`
- **Distribution Archive:** `diagram_engine_v2_portable_v2.0_20261019_165951.zip`
- **Initial Baseline:**
  - Greenfield core compiler supporting 4-format output (Draw.io XML, SVG, PNG, native editable PPTX DrawingML).
  - Pydantic v2 declarative schema (`DiagramSpec`, `ContainerSpec`, `NodeSpec`, `FlowSpec`).
  - Baseline coordinate normalizer (`geometry.py`) and basic Tier 1 collision auditor.
