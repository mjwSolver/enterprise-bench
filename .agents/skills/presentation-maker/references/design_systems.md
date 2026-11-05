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

### Anti-Pattern 4: The "Accidental RAG" on Chronological Roadmaps
- **Defect:** Assigning Red, Amber, and Green to sequential timeline or horizon phases (e.g. H1 Red, H2 Amber, H3 Green). This mistakenly borrows Red-Amber-Green (RAG) risk tokens. An executive reading the slide instinctively perceives Horizon 1 as failing/broken, Horizon 2 as at risk, and Horizon 3 as the only healthy stage.
- **Modern Upgrade (Monochromatic Temporal Depth):**
  - Roadmaps are chronological maturity phases, not health checks or defect logs.
  - Use **Monochromatic Temporal Progression**:
    - **Horizon 1 (Immediate Core / Active Execution):** Deep primary slate/navy or brand focal accent (`#0284C7`). Signals active priority.
    - **Horizon 2 (Near-Term Expansion):** Mid-tone slate (`#475569`). Medium visual weight.
    - **Horizon 3 (Long-Term Frontier):** Subdued light slate (`#94A3B8`). Lightest visual weight, communicating temporal distance.
  - Reserve Red (`#DC2626`) strictly for genuine system bottlenecks, bugs, and P1 defect chips.

### Anti-Pattern 5: The Multi-Banner Crutch & Competing Accent Stripes
- **Defect:** Crowning multiple cards with vertical or horizontal accent stripes (e.g., adding red stripes to left cards and green stripes to right cards on every single row). This destroys visual hierarchy, turning intentional accent highlights into repetitive wallpaper.
- **Modern Upgrade (The Single-Focus Takeaway Rule):**
  - Cards use clean surfaces with subtle neutral borders (`0.75pt`, `#CBD5E1` or `#BAE6FD`).
  - **There should only ever be ONE prominent banner on a slide**: specifically reserved for an **Executive Synthesis / Takeaway Bar** spanning the bottom of the canvas.

### Anti-Pattern 6: The Rigid Category Lead-In Trap vs Inverted Keyword Bolding
- **Defect:** Rigidly formatting every bullet as `**Category Label:** Long narrative sentence...` (e.g. `**Targeted Hive Offload:** Migrate top 15 critical month-end aggregation jobs directly to Snowflake virtual warehouses.`). This produces visually bloated, dictionary-style text blocks that discourage reading.
- **Modern Upgrade (Inverted Keyword Bolding):**
  - Write concise, punchy statements (10–14 words max).
  - Bold ONLY the **2–3 critical operational keywords** inside the statement (e.g. `Migrate top 15 month-end **Hive aggregation jobs** directly to Snowflake.`).
  - An executive scanning the slide catches the bold data anchors in under 2 seconds without wading through repetitive category labels.

---

## 5. Simple Geometric Shapes in Executive Slidecraft (Beyond Squares & Tables)

Top-tier strategy firms (McKinsey, BCG, Bain) deploy simple geometric shapes as structural logic models, never as decorative clip art:

| Shape | DrawingML Primitive | Core Structural Meaning | Executive Application |
| :--- | :--- | :--- | :--- |
| **Chevrons** | `MSO_SHAPE.CHEVRON` | Sequential flow & time | Horizontal timeline phase tracks (`Phase 1` $\rightarrow$ `Phase 2` $\rightarrow$ `Phase 3`), value chains. Forces natural left-to-right temporal reading. |
| **Circles / Hubs** | `MSO_SHAPE.OVAL` | Centrality & relationships | Hub-and-Spoke models (central core strategy with satellite pillars), Venn diagrams (intersections & synergies), numbered sequence badges (`①`, `②`, `③`). |
| **Hexagons** | `MSO_SHAPE.HEXAGON` | Interlocking capability mesh | Ecosystem models and organizational frameworks (e.g. McKinsey 7S). Honeycomb layout eliminates empty gaps, communicating tightly coupled modules. |
| **Pyramids / Triangles** | `MSO_SHAPE.ISOSCELES_TRIANGLE` | Hierarchy & filtering | Layered capabilities (Broad Foundation $\rightarrow$ Middle Platform $\rightarrow$ Strategic Apex), prioritization funnels. |

### Shape Usage Invariants:
1. **Form Follows Semantics:** Never add a hexagon or circle to "fill blank space". If the shape doesn't represent a category boundary, process flow, or hierarchy, delete it.
2. **Flat Vector Aesthetics:** Zero 3D bevels, zero drop shadows, hairline stroke (`0.75pt`), subtle solid fills with dark charcoal text.
3. **Internal Margin Discipline:** Non-rectangular shapes (circles, hexagons) taper at the edges. Text inside them must be tightly padded and centered so descenders never clip the tapered corners.

---

## 6. AI Agent Priming Directives for High-End Slide Generation

To generate executive-grade presentations, an AI agent must be primed with six operational invariants:

1. **One Slide, One Core Idea (Pyramid Principle):** Action headlines must state an analytical conclusion (`Finding + Driver + Consequence`). Never use passive category labels ("Q3 Pipeline Performance").
2. **Container Hierarchy Ceiling (Max 1 Level):** Never draw a bordered container inside another bordered card. If an element is inside a card, it floats in negative space.
3. **The 90/10 Color Discipline & Anti-RAG:** 90% neutral slate/white/charcoal tones; 10% purposeful semantic color (Red = defect, Amber = boundary, Blue = flow, Green = target). Never use RAG status colors across chronological steps.
4. **Inverted Keyword Bolding & Pacing:** Bold ONLY 2–3 core operational keywords per bullet. Keep bullet statements concise (10–14 words) with generous vertical whitespace (`Pt(8)` spacing between bullets).
5. **Single Focus Banner Rule:** Never repeat accent banners across multiple parallel elements. Restrict accent banners to a single Executive Synthesis Bar at the bottom of the canvas.
6. **Deterministic Preflight Linting:** Run `uv run bench ppt lint-spec <spec.yaml>` headlessly before compiling to deterministically enforce palette discipline, action titles, and typography without cluttering LLM context windows with long prompt manuals.
