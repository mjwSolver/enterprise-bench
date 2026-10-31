---
name: presentation-maker
description: >-
  Fallback legacy presentation skill. DO NOT invoke automatically. Use ONLY upon explicit manual user command or slash invocation (/presentation-maker).
---

# Presentation Maker Skill

A comprehensive guide for generating high-impact, professional presentations using the unified Enterprise Bench CLI (`uv run bench ppt ...`), modular consulting archetypes from `src.ppt_engine`, and clean visual design standards.

---

## 🚨 Primary Protocol: Unified CLI-First Execution

> **CRITICAL DIRECTIVE (DECLARATIVE YAML-FIRST):** Do NOT write raw, throwaway, monolithic Python scripts (e.g. 500–700 lines embedding coordinates, shapes, OpenXML boilerplate, and copy). All content hierarchy, badges, and layout parameters must reside in a declarative YAML spec (`specs/<topic>.yaml`), compiled headlessly by a static decoupled runner (`uv run bench diagram v2 compile` or dedicated compiler). All iterative revisions touch *only* the YAML spec ([ADR](../../docs/decisions/ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md)). Always invoke presentation tasks through the unified `bench` CLI or declarative compiler runners.

### Exact 1-Line CLI Commands

1. **Generate Consulting Presentation Deck:**
   ```bash
   uv run bench ppt generate --theme brickred --title "Enterprise Strategy Review" --client "Strategic Partner" --output output/strategy_review.pptx
   ```

2. **List Available Enterprise Themes:**
   ```bash
   uv run bench ppt themes
   ```

3. **Verify Generation & Fast Unit Sanity:**
   ```bash
   uv run bench test --unit
   ```

---

## 1. Core Workflow

```
0. Sketch/Image Ingestion Contract (Gate)  →  1. Outline & Narrative Architecture  →  2. Design System & Palette  →  3. Archetype Selection  →  4. CLI / Engine Execution  →  5. Asset & Visual QA
```

### Phase 0: Sketch & Image Ingestion Contract (Pre-Compilation Confirmation Gate)
> **MANDATORY GATE FOR IMAGE/SKETCH INPUTS:**
> When the user supplies an image attachment, whiteboard snapshot, or hand sketch:
> 1. **Do NOT Jump to Compilation:** Never immediately write code, compile slides, or assume matching legacy scripts in `TEMP/`.
> 2. **Pre-Compilation Structural Graph Output:** The agent MUST immediately output a structured, bulleted structural graph contract confirming the interpreted topology before executing compilation:
>    - **Containers & Boundaries:** Outermost canvas boundaries, swimlanes, and containment zones.
>    - **Nodes & Components:** Entities, exact labels, icon glyphs, and diagnostic semantic colors (`#DC2626` bottleneck, `#D97706` wait/boundary, `#0284C7` ingress/active, `#16A34A` target).
>    - **Connectors & Dataflows:** Directed source $\to$ target paths, trigger/protocol labels (`run-now`, REST, JDBC), and synchronous vs asynchronous channels.
> 3. **Single-Slide Scope Ceiling Invariant:**
>    - Any request for "a visualization", "a slide", "diagram this sketch", or single architecture drawing has an absolute ceiling of **exactly 1 slide** (or single standalone diagram).
>    - **Strictly Prohibited:** Generating unsolicited multi-slide pitch decks (no unprompted cover slides, context slides, or closing slides).
>    - **Zero Static Raster Injection:** Never inject flat PNG/raster screenshots of diagrams into `.pptx` slides. Diagrams must compile to 100% native editable DrawingML vector shapes and connectors via `diagram_v2`.

### Phase 1: Narrative & Deck Architecture
- **Define Slide Roles**: Every slide must have a distinct functional purpose (e.g., Cover, Problem Framing, Regulatory Context, Research Gap, Theoretical Framework, Methodology, Empirical Results, Robustness, Implications, Q&A).
- **Takeaway Headlines**: Write action titles that express the conclusion, not just category labels (e.g., *"ESG Disclosure Significantly Enhances Financial Reporting Quality in High-Scrutiny Sectors"* instead of *"Results"*).
- **Pacing & Information Density**: Match information density to audience using the 3-Gear standard. Avoid artificial truncation of contractual scope.

---

## 🎛️ The 3 Adaptive Complexity Gears & Enterprise Density Standard

> **THE ENTERPRISE DENSITY INVARIANT:** In enterprise IT consulting, **high information density ($7.0/10$ to $9.5/10$) is a functional requirement, not a design defect.** Legibility is maintained through **hierarchical containerization, strict typographic scaling, and boundary swimlanes**, never by artificially deleting necessary technical scope. Reference: [`docs/specs/adaptive_complexity_gears_and_enterprise_density.md`](../../docs/specs/adaptive_complexity_gears_and_enterprise_density.md).

### The 3 Complexity Gears:
1. **Gear 1 (Executive / Pitch, 4.0–5.0/10):**
   - **Audience:** Board of Directors, Steering Committee kickoff, executive sponsor.
   - **Pattern:** Generous whitespace, 1 primary focal anchor, max 3 takeaway cards (e.g., 3-Horizon Modernization, Core Strategic Pillars).
2. **Gear 2 (Pre-KOM / Alignment, 6.5–7.5/10 - DEFAULT BASELINE):**
   - **Audience:** Technical Directors, Enterprise Architects, PMOs.
   - **Pattern:** 3-column boundary swimlanes (On-Premises ➔ Cloud ➔ Consumers), labeled path connectors (WS1, WS2, WS4), out-of-scope boundaries.
3. **Gear 3 (Technical Workstream Runbook, 8.5–9.5/10):**
   - **Audience:** Lead Engineers, DBAs, Security Officers, SysAdmins.
   - **Pattern:** 4-quadrant container discipline (Objective, MII Actions, Client Actions, Dependencies, Named PIC Table), 8.5–9.5pt micro-typography.

### Diagnostic Status Triad:
Deterministic semantic signaling replaces arbitrary 1-accent aesthetic caps:
- **Critical Defect / Bottleneck (`#DC2626` / `#FEE2E2`):** P1 bottleneck, single-point-of-failure, legacy debt.
- **Warning / Boundary / Sync (`#D97706` / `#FEF3C7`):** Synchronous wait, temporary VPN, freeze window, boundary fence.
- **Client Ingress / Active Flow (`#0284C7` / `#EFF6FF`):** Ingress data streams, client requests, active runtime triggers.
- **Target State / Reconciled (`#16A34A` / `#DCFCE7`):** Target cloud platform, reconciled data, approved state.
- **Neutral Container / Structural (`#CBD5E1` / `#F8FAFC`):** Standard storage, structural containers, boundary boxes.

### Casual Ingress & 1-Word Steering Triggers:
- **Default Baseline:** Unspecified or casual requests (*"make a slide on migration"*) default to **Gear 2 (Pre-KOM Alignment)**.
- **Domain-Noun Auto-Elevation:** Prompts containing enterprise nouns (VPC/CIDR, PrivateLink, CAB, PIC, BAST milestones, named counterpart teams) auto-elevate to **Gear 3 (Technical Workstream)**.
- **1-Word Steering Levers:**
  - `"pack it"` / `"full BSIM"` &rarr; Elevate to **Gear 3**.
  - `"simplify"` / `"board view"` &rarr; Drop to **Gear 1**.
  - `"swimlane it"` &rarr; Convert topology to 3-column boundary architecture.


### Phase 2: Engine Integration (When Extending Beyond CLI Defaults)
When building customized decks in Python, import directly from the engine primitives rather than writing raw `python-pptx` scripts:
```python
from src.ppt_engine.consulting_archetypes import (
    create_presentation,
    ConsultingDeckBuilder,
    HorizonColumnData,
    ScorecardQuadrantData,
    build_bcg_3_horizon_slide,
    build_balanced_scorecard_slide,
    build_chapter_divider_slide,
)
from src.ppt_engine.theme_engine import get_theme

active_theme = get_theme("brickred")
prs = create_presentation(active_theme)
# Assemble slides using archetypes...
prs.save("output/custom_deck.pptx")
```

---

## 2. Visual Design System

### A. Aspect Ratio & Dimensions
- Default to **16:9 Widescreen** (enforced by `create_presentation(theme)`):
  - Width: `13.333 inches` (`12192000 EMUs`)
  - Height: `7.5 inches` (`6858000 EMUs`)

### B. Color Palettes
Choose a cohesive palette with 60-30-10 distribution (60% background/neutral, 30% primary/secondary slate, 10% high-contrast accent):

1. **Modern Consulting (`brickred`)**:
   - Background: Off-white / Cool Gray (`#F8F9FA`)
   - Primary Text: Deep Navy / Slate (`#1E293B`)
   - Secondary / Structural: Slate Blue (`#475569`)
   - Accent / Highlight: Crimson Red (`#DC2626`)
   - Surface / Card Fill: Pure White (`#FFFFFF`)
   - Border / Hairline: Subtle Slate (`#E2E8F0`)

2. **Executive Enterprise (`snowblue`)**:
   - Background: Snow Mist (`#F0F4F8`)
   - Text: Deep Charcoal (`#0F172A`)
   - Accent: Cerulean Blue (`#0284C7`)
   - Secondary: Muted Navy (`#1E3A8A`)

---

## 3. Slide Archetypes & Layouts

Refer to detailed implementation recipes in [`references/slide_archetypes.md`](./references/slide_archetypes.md):
1. **Title / Cover Slide**: Minimalist, strong typography, metadata in understated pill or baseline.
2. **Horizontal Flow / Process**: 3–4 sequenced cards with connector arrows or step badges.
3. **2-Column / 3-Column Comparison**: Distinct cards with hairline borders and top accent bands.
4. **BCG 3-Horizon Modernization**: 3 phased columns (`Horizon 1: 0-6m`, `Horizon 2: 6-18m`, `Horizon 3: 18-36m`).
5. **Balanced Scorecard KPI Matrix**: 4 quadrants (Financial, Customer, Operational, Resilience) with metric chips.
6. **Key Metrics / Stat Highlights**: Large 36–48pt numbers paired with concise 12pt descriptive labels.
7. **De-Squared Chapter Divider / Section Header**: Asymmetric split (1/3 white typographic narrative panel + 2/3 photographic plate) with 45% dark translucent scrim overlay (`#0B132B`), center-anchored square brand mark, and graceful fallbacks. Use `build_chapter_divider_slide(...)` or `ConsultingDeckBuilder.add_chapter_divider_slide(...)`.
8. **Dense Workstream Runbook (Gear 3)**: 4-quadrant container discipline (Objective, Vendor Actions, Client Actions, Dependencies, Named PIC Matrix) with 8.5–9.5pt micro-typography and tight card layouts. Use `ConsultingDeckBuilder.add_dense_workstream_runbook_slide(...)`.
9. **Target Architecture Swimlane (Gear 2)**: 3-column boundary swimlanes (Source Systems ➔ Modern Cloud Platform ➔ Consumers & Analytics) with labeled workstream route badges (WS1, WS2, WS4) and out-of-scope fences. Use `ConsultingDeckBuilder.add_target_architecture_swimlane_slide(...)`.

---

## 4. Programmatic Rules & Collision Prevention

Detailed code templates are available in [`references/python_pptx_recipes.md`](./references/python_pptx_recipes.md).

### Golden Rules for Slide Layouts:
1. **Explicit Positioning**: Never rely on default PowerPoint placeholders. Calculate explicit `left`, `top`, `width`, `height`.
2. **Text Box Margin Zeroing**: Always set internal padding when aligning text inside visual cards:
   ```python
   tf = shape.text_frame
   tf.word_wrap = True
   tf.margin_left = Inches(0.15)
   tf.margin_right = Inches(0.15)
   tf.margin_top = Inches(0.15)
   tf.margin_bottom = Inches(0.15)
   ```
3. **Card Container Shapes & Geometric Integrity**:
   - 🚨 **ANTI-PATTERN TO PREVENT**: Never place an overlapping horizontal line, accent stripe, or header bar across a container that has rounded corners at the top.
   - **Enforcement Rule**: Any container card that features a top accent line, stripe, or header bar **MUST BE A CRISP RECTANGLE (`MSO_SHAPE.RECTANGLE`)**. Both the card and the stripe must use `MSO_SHAPE.RECTANGLE` with identical width for flush 90-degree edge-to-edge alignment.
   - Thin horizontal accent stripes must **NEVER** use `MSO_SHAPE.ROUNDED_RECTANGLE` (which distorts into an awkward capsule/pill).
   - Rounded corners (`MSO_SHAPE.ROUNDED_RECTANGLE`) are reserved exclusively for standalone self-contained metric callouts (without top lines) and floating status badges/pills.
4. **Cover Slide Elegance & Clean Metadata**:
   - 🚨 **ANTI-PATTERN TO PREVENT**: Never place metadata (Client, Vendor, Date, Confidentiality) inside an awkward bordered card or box container at the bottom of a cover slide.
   - **Enforcement Rule**: Metadata must be rendered as clean typographic columns (e.g., `PREPARED FOR` and `ENGAGEMENT PARTNER`) separated from the title area by an optional subtle hairline divider.
   - **Zero Cover Footers**: Cover slides must **NEVER** feature slide footer divider bars or page numbers (e.g. `01 / 06`). Slide footers and pagination strictly begin on content slide 2.
5. **Consistent Typography Tokens**:
   - Header Tracker / Category: 10–11pt bold, uppercase
   - Main Slide Action Title: 22–26pt bold
   - Card Titles / Subheaders: 13–15pt bold
   - Body Text: 11–12pt regular
   - Captions / Footnotes: 9–10pt muted
6. **Unified Title & Subtitle Frame (Zero Coordinate Guessing)**:
   - 🚨 **ANTI-PATTERN TO PREVENT**: Never place Action Title and Subtitle in separate textboxes with hardcoded Y positions. When titles wrap to 2 lines, the subtitle collides or crowds the headline.
   - **Enforcement Rule**: Place Action Title and Subtitle as sequential paragraphs within the **SAME text frame**. Use `p_subtitle.space_before = Pt(10)` to enforce an exact 10pt offset regardless of how many lines the title spans.
7. **Single-Slide Scope Ceiling & Native Vector Fidelity**:
   - 🚨 **ANTI-PATTERN TO PREVENT**: Never generate multi-slide pitch decks (cover, diagram, closing) or insert raster PNG screenshots when asked to produce a visualization from a sketch/diagram.
   - **Enforcement Rule**: Requests for single visualizations or diagrams are strictly capped at **exactly 1 slide**. All shapes and connectors must be 100% native DrawingML vector elements compiled from declarative YAML (`bench diagram v2`), ensuring full user editability.
8. **Declarative Spec + Static Runner Pattern (Zero Imperative Layout Scripting)**:
   - 🚨 **ANTI-PATTERN TO PREVENT**: Never write or repeatedly patch monolithic, imperatively hardcoded layout scripts (e.g. 500–700 line Python scripts embedding raw coordinates, shapes, OpenXML manipulation, and slide copy). Monolithic scripts burn 15k–25k tokens per revision cycle, risk corrupting OpenXML placeholders, and force full file rewrites for minor copy edits.
   - **Enforcement Rule**: Content hierarchy, badges, titles, card copy, step lists, and layout parameters must reside in a declarative YAML spec (e.g. `specs/<topic>.yaml`). Slide generation is performed headlessly by a decoupled, reusable compiler/runner (`bench diagram v2 compile`, static compiler runner). All iteration and content revisions MUST touch *only* the declarative YAML spec, never re-emitting compiler boilerplate. See full case study: [`ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md`](../../docs/decisions/ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md).

---


## 5. Reference Files
- [Python-PPTX Code Recipes](./references/python_pptx_recipes.md)
- [Design Systems & Color Schemes](./references/design_systems.md)
- [Slide Layout Archetypes](./references/slide_archetypes.md)
- [Deck Template Generator Script](./scripts/create_deck_template.py)
