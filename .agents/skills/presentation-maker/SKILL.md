---
name: presentation-maker
description: >-
  Expert system for designing, structuring, and generating professional presentation decks (PowerPoint / .pptx) using the unified CLI (`uv run bench ppt`), python-pptx, consulting frameworks, and modern slide design systems. Use whenever creating, editing, redesigning, or automating PowerPoint presentations.
---

# Presentation Maker Skill

A comprehensive guide for generating high-impact, professional presentations using the unified Enterprise Bench CLI (`uv run bench ppt ...`), modular consulting archetypes from `src.ppt_engine`, and clean visual design standards.

---

## 🚨 Primary Protocol: Unified CLI-First Execution

> **CRITICAL RULE:** Do NOT write raw, throwaway Python scripts or manual slide assembly scripts from scratch. Always invoke presentation tasks through the unified `bench` CLI or import from `src.ppt_engine`.

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
1. Outline & Narrative Architecture  →  2. Design System & Palette  →  3. Archetype Selection  →  4. CLI / Engine Execution  →  5. Asset & Visual QA
```

### Phase 1: Narrative & Deck Architecture
- **Define Slide Roles**: Every slide must have a distinct functional purpose (e.g., Cover, Problem Framing, Regulatory Context, Research Gap, Theoretical Framework, Methodology, Empirical Results, Robustness, Implications, Q&A).
- **Takeaway Headlines**: Write action titles that express the conclusion, not just category labels (e.g., *"ESG Disclosure Significantly Enhances Financial Reporting Quality in High-Scrutiny Sectors"* instead of *"Results"*).
- **Pacing & Breathing Room**: Limit to 1 core idea per slide. Avoid dense wall-of-text paragraphs; use structured cards, columns, and visual callouts.

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

---


## 5. Reference Files
- [Python-PPTX Code Recipes](./references/python_pptx_recipes.md)
- [Design Systems & Color Schemes](./references/design_systems.md)
- [Slide Layout Archetypes](./references/slide_archetypes.md)
- [Deck Template Generator Script](./scripts/create_deck_template.py)
