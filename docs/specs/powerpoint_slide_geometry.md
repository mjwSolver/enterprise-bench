# Architecture Specification: PowerPoint Slide Geometry, Visual Hierarchy & Diagram Standards

> **Target Role:** Presentation Engine Maintainer, Consulting Deck Automation Engineer (`enterprise-bench-dev`, `presentation-maker`)  
> **Status:** Approved Architectural Standard  
> **Target Subsystems:** [`src/ppt_engine/slide_builders.py`](../../src/ppt_engine/slide_builders.py), [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py), [`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py), [`src/ppt_engine/drawingml_compiler.py`](../../src/ppt_engine/drawingml_compiler.py)  
> **Related Documents:** [`docs/specs/adaptive_complexity_gears_and_enterprise_density.md`](adaptive_complexity_gears_and_enterprise_density.md), [`docs/specs/drawio_edge_routing_and_collision_prevention.md`](drawio_edge_routing_and_collision_prevention.md), [`docs/specs/openxml_purging_and_cleansing.md`](openxml_purging_and_cleansing.md)

---

## 1. Executive Summary & Scope

This specification codifies the geometry, typographic hierarchy, container framing, and collision prevention rules across all PowerPoint (`.pptx`) generation engines and diagram pipelines in `enterprise-bench`.

Applying ad-hoc shape placement or mismatched shape radii produces jarring visual defects on high-resolution displays. Enforcing these deterministic rules guarantees pixel-perfect, publication-grade executive presentations.

---

## 2. Container Geometry: Zero Overlapping Top Lines on Rounded Containers

### 2.1 The Geometric Anti-Pattern
Never place an overlapping horizontal line, accent bar, or header stripe on top of a rounded container (`MSO_SHAPE.ROUNDED_RECTANGLE`).
- A horizontal line across the top of a rounded rectangle causes severe visual distortion: protruding corner artifacts, mismatched corner radii, and gaps at the curve tangents.
- Thin accent stripes rendered as rounded rectangles distort into oval capsules or pills.

### 2.2 The Enforced Pattern
1. **Sharp Geometry for Striped Containers:** When a container card features a top accent line, stripe, or colored header bar, **both the container card and the top stripe MUST be sharp rectangles (`MSO_SHAPE.RECTANGLE`)**.
2. **Rounded Rectangle Budget:** Rounded shapes (`MSO_SHAPE.ROUNDED_RECTANGLE`) are reserved strictly for standalone metric badges, status pills, or self-contained cards without top overlapping lines.
3. **Engine Implementation:** Use `add_card_with_top_stripe(...)` or pass `has_top_stripe=True` to `add_card(...)`.

---

## 3. Cover Slide Architecture: Clean Typographic Metadata

### 3.1 Dual Vertical Brand Accent Stripes (1 Red : 2 Blue Ratio)
Frame the left edge of the cover slide title area ($x = 0.80''$, $y = 1.80''$) with flush, adjacent vertical stripes mirroring the corporate brand mark:
- **Crimson Red Stripe:** Width $w = 0.045''$ (`#DC2626`).
- **Metrodata Blue Stripe:** Width $w = 0.090''$ (`#002060`, exactly $2\times$ thickness).
- The ratio authentically reflects the 1 red stroke to 2 blue strokes mark.

### 3.2 Typographic Multi-Column Alignment (Zero Boxed Cards)
- **Prohibited:** Never place metadata (Client, Vendor, Date, Confidentiality) inside an awkward bordered card or box container at the bottom of a cover slide.
- **Enforced:** Render metadata directly on the slide canvas in clean typographic columns (e.g., `PREPARED FOR` and `ENGAGEMENT PARTNER`) separated from the title area by an optional subtle baseline hairline.

### 3.3 No Cover Footers or Pagination
Cover slides must **NEVER** feature slide footer divider bars, confidentiality disclaimers, or page numbers (e.g., `01 / 06`). Slide footers and page numbering strictly begin on content slide 2.

---

## 4. Chapter Divider Slide Architecture: De-Squared Split Layout & Translucent Scrim

### 4.1 Asymmetric 1/3 + 2/3 Canvas Composition
Break monotonous box grids by splitting the 16:9 widescreen canvas ($13.333'' \times 7.5''$) into an unboxed narrative panel and a full-bleed photographic hero plate:
- **Left Narrative Panel:** $x = 0.80''$, $y = 2.00''$, $w = 3.60''$, $h = 4.00''$.
- **Right Hero Plate:** $x = 4.80''$ to $13.333''$, $y = 0.00''$, $w = 8.533''$, $h = 7.50''$.

### 4.2 Unified Narrative Framing
Flow the Category Tracker breadcrumb (10pt bold uppercase, accent color), Action Headline (30–34pt bold, primary color), and context Subtitle (11.5pt, secondary color) as sequential paragraphs within a **single unified text frame** with exact paragraph offsets (`space_before = Pt(12)` and `Pt(14)`), preventing text box collisions.

### 4.3 Translucent Dark Scrim Guarantee
Always overlay the photographic hero panel with an OpenXML DrawingML 45% dark scrim (`#0B132B` via `<a:alpha val="45000"/>`), guaranteeing high contrast for brand marks and lockup labels regardless of underlying image luminance.

### 4.4 Brand Lockup & Graceful Degradation
- Center the square brand mark ($x \approx 7.87''$, $y \approx 2.35''$, $w = 2.4''$, $h = 2.1''$) with white division tagline at $y = 4.70''$.
- **Graceful Fallback:** If photos or logos are missing, automatically fall back to deep primary solid rectangles (`#0F172A`) and vertically centered typographic badges (`[ METRODATA ]`), logging remediation steps in `missing_resources.md`.
- **Geometry Rule:** Enforce sharp rectangular geometry (`MSO_SHAPE.RECTANGLE`) across both hero and scrim plates.
- **Implementation:** `build_chapter_divider_slide(...)` or `ConsultingDeckBuilder.add_chapter_divider_slide(...)`.

---

## 5. Header Architecture: Unified Title & Subtitle Frame

### 5.1 The Coordinate Collision Anti-Pattern
Never render Action Titles and Subtitles into separate floating text boxes with hardcoded Y coordinates. Guessing Y coordinates based on character length inevitably causes collision/crowding on 2-line wrapped titles, or oversized gaps on 1-line titles.

### 5.2 Unified Flow Architecture
1. **Single Text Box:** Place Action Title and Subtitle as sequential paragraphs within the **SAME text frame**.
2. **Paragraph Spacing Offset:** Enforce a strict paragraph offset (`space_before = Pt(10)`) on the subtitle paragraph. PowerPoint's layout engine automatically flows the subtitle exactly 10pt below the final line of the title regardless of line wrap.

---

## 6. Diagram Architecture & Visual Hierarchy Standard

### 6.1 Balanced Multi-Tier Aspect Ratio
Diagrams embedded into 16:9 presentation slides or executive documents must avoid ultra-wide single-tier horizontal chains ($>4$ nodes stretched linearly, creating $\sim 10:1$ aspect ratios that shrink to unreadable hairline ribbons).
- Enforce balanced 3-column or multi-row layouts (target aspect ratio $\sim 2.5:1$ to $3.5:1$).
- Typography scales legibly ($\ge 11\text{pt}$ to $14\text{pt}$ optical equivalent) when rendered inside slide cards.

### 6.2 Mandatory Vector Logos & Iconography
- Vertex nodes must incorporate official vector technology logos (SVG from `assets/logos/`, e.g., Kafka, Snowflake, dbt, AWS, HashiCorp Vault) or standardized icon glyphs (Lucide/Heroicons) rather than generic plain-text rectangles.
- Dedicated icon slots ($40\times 40$ px to $48\times 48$ px) with left-aligned title/body labels adjacent to the emblem and generous card volume to prevent text crowding.

### 6.3 Sub-Canvas Columnar Grouping
Topologies with multiple subgraphs must map subgraphs into distinct vertical columns or cohesive functional swimlanes with smart orthogonal routing (`_compute_subgraph_columnar_layout`).

---

## 7. Diagram Edge Architecture & Collision Prevention

### 7.1 Zero Slicing Through Containers
Never route cross-column feedback lines or multi-column hops through the geometric center of intermediate subgraphs or cards. The engine (`DiagramRenderer.render_svg`) enforces gutter-channel routing ($sg.x \pm 18\text{ pt}$) to keep intermediate columns clear.

### 7.2 Vertical Obstacle Detection & Bypass
Intra-column edges between non-adjacent nodes must never cut straight through intervening cards. When defining intra-column relationships, prefer sequential top-to-bottom pipelines (`DW --> OpDB`, `OpDB --> AI`). If skip-hops are used, the engine automatically jogs $24\text{ pt}$ around the right perimeter of intermediate obstacles.

### 7.3 Dynamic Port Directionality
Never hardcode edge ports (`exitX=1;entryX=0;`) for all connectors. `DrawIOConverter._build_edge_style` dynamically evaluates $(\Delta x, \Delta y)$ to assign exact attachment faces (top/bottom for vertical flows, left/right for forward/backward flows), guaranteeing interactive `.drawio` files match headless SVG/PNG previews with zero looping or doubled lines. Reference: [`docs/specs/drawio_edge_routing_and_collision_prevention.md`](drawio_edge_routing_and_collision_prevention.md).
