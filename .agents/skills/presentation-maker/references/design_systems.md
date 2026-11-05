# Design Systems & Visual Standards for Presentations

A consulting-grade presentation balances high legibility, strict alignment, and restrained aesthetics.

---

## 1. Typography Hierarchy

| Role | Font Family | Size | Weight | Color |
| :--- | :--- | :--- | :--- | :--- |
| **Category / Tracker** | Arial / Calibri / Segoe UI | 10–11 pt | Bold (UPPERCASE) | Accent Teal / Muted Gray |
| **Action Headline** | Arial / Calibri / Segoe UI | 22–26 pt | Bold | Deep Slate (`#1E293B`) |
| **Subtitle / Subhead** | Arial / Calibri / Segoe UI | 12–14 pt | Medium / Regular | Muted Slate (`#64748B`) |
| **Card Header** | Arial / Calibri / Segoe UI | 14–16 pt | Bold | Primary Slate (`#0F172A`) |
| **Body Text** | Arial / Calibri / Segoe UI | 11.5–13 pt | Regular | Neutral Dark (`#334155`) |
| **Data / Numbers** | Arial / Segoe UI | 28–44 pt | Bold | Accent Teal / Dark Slate |
| **Captions / Footnotes** | Arial / Calibri | 8.5–10 pt | Italic / Regular | Subdued (`#94A3B8`) |

---

## 2. Spacing & Grid Alignment (16:9 Standard: 13.333" x 7.5")

- **Outer Slide Margins**:
  - Left / Right: `0.80"` (20.3 mm)
  - Top: `0.50"` (12.7 mm)
  - Bottom: `0.50"` (12.7 mm)
- **Usable Content Area**: Width `11.733"`, Height `6.50"`
- **Gaps Between Cards**: `0.25"` to `0.35"`
- **Internal Card Padding**: `0.20"` to `0.30"`

---

## 3. Color Palettes

### Modern Consulting Academic (Recommended)
- Canvas Background: `#F8FAFC` (Slate 50)
- Container Surface: `#FFFFFF` (Pure White)
- Primary Typography: `#0F172A` (Slate 900)
- Secondary Elements: `#0F766E` (Teal 700)
- Accent Highlight: `#D97706` (Amber 600)
- Card Border / Dividers: `#E2E8F0` (Slate 200)

### Corporate Slate & Navy
- Canvas Background: `#F1F5F9`
- Container Surface: `#FFFFFF`
- Primary Typography: `#1E293B`
- Secondary Elements: `#2563EB` (Royal Blue)
- Accent Highlight: `#059669` (Emerald)
- Card Border / Dividers: `#CBD5E1`

---

## 4. Modern Executive Visual Hygiene & Anti-Pattern Registry

### Anti-Pattern 1: The "Top-Stripe" Header Crutch
- **Defect:** Crowning every card, column, or table container with a saturated horizontal color bar across the top edge. This turns a single-item *focus banner* (like a "RECOMMENDED" callout) into an overused, boxy corporate template from 2012.
- **Modern Upgrade:** 
  - Demote top stripes to **single-item intentional focus highlights only** (e.g., highlighting 1 column out of 3, or a single critical bottleneck).
  - Standard cards use **borderless surfaces** or **subtle hairline borders** (`0.75pt`, `#E2E8F0`) on pure white or muted surfaces (`#F8FAFC`).
  - Let whitespace and typography define the header hierarchy.

### Anti-Pattern 2: The "Box-in-a-Box" Container Cage
- **Defect:** Placing a card on the slide, and nesting smaller bordered boxes inside it (e.g., boxing a KPI number in a gray rectangle within a column card). Creates competing visual borders, clutter, and cognitive friction.
- **Modern Upgrade (Open-Air Floating Metrics):**
  - Delete nested container boxes.
  - Let metrics float freely with **dramatic typographic scale contrast**: 26–32pt bold numbers paired with 9–10pt muted sublabels.
  - Separate narrative blocks with subtle horizontal hairline dividers (`0.5–0.75pt`, `#E2E8F0`) rather than nested cards.

### Anti-Pattern 3: The Solid Header Block in Tables
- **Defect:** Painting a thick, dark primary color fill across the entire table header row with white text.
- **Modern Upgrade (The Single-Line Table Rule):**
  - Ditch solid dark header blocks.
  - Header row uses a transparent or soft-tinted surface (`#F1F5F9`) with dark slate bold text (`#0F172A`).
  - Place a **single crisp 1pt horizontal hairline rule** directly beneath the header row.
  - Table rows use borderless cells with faint alternating background tint (`#F8FAFC`) and 0.5pt row dividers. Zero vertical gridlines.

---

## 5. AI Agent Priming Directives for High-End Slide Generation

To generate executive-grade presentations, an AI agent must be primed with four operational invariants:

1. **One Slide, One Core Idea (Pyramid Principle):** Action headlines must state an analytical conclusion (`Finding + Driver + Consequence`). Never use passive category labels ("Q3 Pipeline Performance").
2. **Container Hierarchy Ceiling (Max 1 Level):** Never draw a bordered container inside another bordered card. If an element is inside a card, it floats in negative space.
3. **The 90/10 Color Discipline:** 90% neutral slate/white/charcoal tones; 10% purposeful semantic color (Red = defect, Amber = boundary, Blue = flow, Green = target). Never use color decoratively.
4. **DrawingML Hanging Indentation & Bold Lead-Ins:** All bullet items must use hanging indents with bold analytical lead-ins (e.g. `• **Root Cause:** Description...`) parsed into native bold runs, never emitting raw markdown asterisks.
