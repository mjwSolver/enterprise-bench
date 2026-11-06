# Executive Presentation Visualization Catalog

A standardized reference guide for executive-ready DrawingML visualization patterns beyond plain text boxes and basic rectangle cards. Designed for automated slide compilers, agentic authoring, and presentation design systems.

---

## 1. Catalog Archetypes

### 1.1 OS & Viewport Chrome (Window Mockup)
- **Visual Pattern:** Native application frame with macOS traffic light buttons (`#FF5F56`, `#FFBD2E`, `#27C93F`), address/route bar pill, telemetry badge, and an embedded inner view or metric card.
- **Consulting Use Cases:**
  - Demonstrating software products, dashboards, portal UI workflows, and admin consoles.
  - Framing real system telemetry or clinical/enterprise portal interfaces in executive pitches without raw screenshots.
- **DrawingML Composition:**
  - Base container: Sharp rectangle with clean background fill (`#FFFFFF` or theme card fill) and hairline border (`#E2E8F0`).
  - Title bar: Header band with 3 circular traffic-light dot shapes ($0.12''$ diameter, $0.08''$ spacing).
  - URL / status bar: Centered pill shape (`ROUNDED_RECTANGLE`) with muted slate background (`#F1F5F9`) and mono-spaced or clean sans-serif route text.
  - Inner content: Nested metrics, mock table, or vector diagram.

### 1.2 Multi-Stage Telemetry & Quality Gates (`open_telemetry_flow`)

Provides dual rendering modes for tracking operational metrics, clinical SLAs, and governance thresholds.

#### Mode A: Solid Benchmark Track Rows (`chart_style: track_bars`)
- **Cognitive Purpose:** Encodes data as **2D volume/mass**. Answers: *"How much quota or capacity has been consumed?"*
- **Best Audience:** CFO, Procurement, Commercial Steering.
- **DrawingML Geometry:**
  - Background track: Slate-100 channel (`#F1F5F9`) with $0.18''$ height, $0.5\text{ pt}$ border.
  - Active fill bar: Solid semantic color rectangle (`#10B981`, `#D97706`, `#DC2626`).
  - Readout: Single-line right-aligned text box (`Pt(8.5)` bold value, `Pt(7.2)` subtext, `Pt(7.8)` status tag).

#### Mode B: Precision Wireline Constellation (`chart_style: wireline_constellation`)
- **Cognitive Purpose:** Encodes data as a **1D signal vector and trajectory**. Answers: *"Where did the signal cross the regulatory boundary?"*
- **Best Audience:** Architecture Review Boards (ARB), CISOs, Platform Engineering Leads.
- **DrawingML Geometry:**
  - Guide stem: Neutral datum line (`Inches(0.015)` height, `#E2E8F0`).
  - Active wireline: Semantic color stroke (`Inches(0.024)` height) spanning `bar_x` to terminal node coordinate.
  - Checkpoint diamonds: `MSO_SHAPE.DIAMOND` (`0.09'' \times 0.09''`, white fill with $1\text{ pt}$ colored border) marking threshold crossings.
  - Terminal orbit node: `0.20''` opaque white halo with $1.75\text{ pt}$ border and $0.075''$ solid inner core, eliminating line skewering artifacts.
  - Continuous vertical gate lines: Background hairlines (`Inches(0.015)` width) spanning all series rows with tangent caliper pill badges.

#### Mode C: Radial Telemetry Dial & Circuit Interconnect
- **Cognitive Purpose:** Functions as the **Single Focal Anchor**, establishing live hardware/runtime provenance.
- **DrawingML Geometry:**
  - Concentric dial: $0.86''$ circle with $3\text{ pt}$ track ring, $2.5\text{ pt}$ active emerald ring, centered $14.5\text{ pt}$ value.
  - Circuit trace: Vertical hairline (`0.015''` width) with a terminal junction dot (`0.05''` diameter) dropping down to anchor in the serving HUD header.

#### Telemetry Selection Matrix
| Decision Factor | `track_bars` (Slide 1) | `wireline_constellation` (Slide 2) |
| :--- | :--- | :--- |
| **Primary Variable** | Capacity / Ingestion Volume | SLA Clearance / Boundary Transitions |
| **Focal Mechanism** | Uniform horizontal mass scan | Circular orbit halo + radial dial focal anchor |
| **Row Scalability** | Up to 8 rows comfortably | Optimal at 3–5 rows with gate diamonds |

### 1.3 Asymmetric Technical Bento Grid
- **Visual Pattern:** High-density, asymmetrical modular layout (e.g. $2 \times 1$ hero anchor card + $1 \times 1$ telemetry cards + tall vertical side rail) replacing uniform $3 \times 1$ cards.
- **Consulting Use Cases:**
  - Platform architecture summaries with uneven emphasis (1 primary core engine + 3 supporting services).
  - Executive KPI dashboards highlighting a single dominant North Star metric alongside secondary operational indicators.
- **DrawingML Composition:**
  - Heterogeneous cell coordinate calculations based on a shared $12$-column grid system.
  - Subtle hairline card borders with accent top-stripes only on the hero module.
  - Integrated metric counters ($32\text{--}36\text{ pt}$) floating above hairline dividers.

### 1.4 Isometric Architectural Planes
- **Visual Pattern:** Stacked parallel horizontal planes showing separation of concerns (e.g., Data Ingestion $\to$ Core Storage $\to$ Processing $\to$ Consumption) connected via vertical orthogonal conduits.
- **Consulting Use Cases:**
  - Cloud infrastructure migration (Legacy On-Prem vs. Hybrid vs. Target Lakehouse).
  - Security tiering (Public Edge, Application DMZ, Data Vault).
- **DrawingML Composition:**
  - Native layered planar polygons or staggered rounded-corner horizontal cards with z-index stacking.
  - Directional vertical chevron bridges or dotted OpenXML connectors indicating data transit.

### 1.5 Dual-State Horizon (The Iceberg Pattern)
- **Visual Pattern:** Distinct horizontal waterline dividing visible high-level business capabilities (above surface) from underlying architectural complexity, technical debt, or legacy dependencies (below waterline).
- **Consulting Use Cases:**
  - Justifying digital transformation investments: explaining why an apparently simple user feature requires deep data model refactoring.
  - Legacy modernization assessments (visible business apps vs. hidden monolithic mainframes).
- **DrawingML Composition:**
  - Sky/Surface region: Crisp white / light slate backdrop with positive KPI cards.
  - Waterline divider: Subtle dashed or themed horizontal rule with a "Waterline" pill badge.
  - Subsurface region: Tinted darker tone (slate or muted theme shade) hosting technical debt cards, legacy databases, and operational risk metrics.

### 1.6 Load-Bearing Capacity Stress Pillars
- **Visual Pattern:** Vertical columnar architectural blocks representing organizational pillars or cluster nodes, displaying real-time capacity fills, headrooms, and fracture/strain warning lines.
- **Consulting Use Cases:**
  - Organizational redesign & team workload saturation audits.
  - Cluster scaling limits, data warehouse compute quotas, and peak transaction headroom.
- **DrawingML Composition:**
  - Equal-width vertical column cards with internal vertical progress gauge shapes.
  - Horizontal threshold line denoting 80% saturation with alert callouts for over-capacity units.

### 1.7 Concentric Blast-Radius Rings
- **Visual Pattern:** Concentric geometric circles or rounded frames indicating increasing zones of security, blast radius, or organizational impact moving outward from the core data asset.
- **Consulting Use Cases:**
  - Zero-Trust security architectures, HIPAA/GDPR clinical data protection boundaries.
  - Failure blast radius analysis in distributed systems.
- **DrawingML Composition:**
  - Concentric circles with decreasing opacity fills or graduated border weights.
  - Radial node placement along circle perimeters with connector lines into the center vault.

### 1.8 Unified Side-by-Side Schema / Code Diff
- **Visual Pattern:** Split terminal or code editor container showing Before (Red strikethrough / removal highlights) and After (Green addition highlights) with an integrated performance/efficiency bridge metric.
- **Consulting Use Cases:**
  - Query optimization (Legacy Subqueries vs. Modern Window Functions / CTEs).
  - Schema normalization, API payload modernization, refactoring business logic.
- **DrawingML Composition:**
  - Dual-column mono-spaced container box styled like an IDE editor.
  - Red-50 / Green-50 background rows with leading `+` and `-` tokens in bold mono font.
  - Central bridge badge asserting quantifiable impact (e.g., `-74% Execution Time`, `3.2x Throughput`).

---

## 2. Implementation Guidelines for Agentic Engines

1. **Avoid Monolithic Layout Code:** All widgets must be composable and parameterized by bounding box coordinates (`left`, `top`, `width`, `height`) and `theme` palettes.
2. **Handle python-pptx Length Subclassing:** Always normalize `Inches(...)` and EMU inputs using a helper (`hasattr(val, 'inches')` or `val / 914400`) before mathematical operations.
3. **Dynamic Theme Resolution:** Never hardcode hex colors inside widget renderers. Pull primary accents, border slates, and background badge tints directly from the active `Theme` instance.
4. **Collision Avoidance:** Provide built-in horizontal and vertical badge offset algorithms for adjacent milestones or close threshold markers.
5. **No Badge Crutches:** Suppress decorative container badges on cards that already feature active subtitles, top stripes, or internal widgets.

---

## 3. Python Library Archetype Inspiration Map (For DrawingML Native Rebuilds)

The goal is to study the visual grammar of popular Python visualization libraries (Plotly, Altair, Seaborn) and reconstruct them as **native, fully-editable DrawingML shapes** rather than importing uneditable rasters:

| Library Origin | Archetype Pattern | Consulting Transformation | DrawingML Vector Architecture |
| :--- | :--- | :--- | :--- |
| **Plotly Express** | **Stephen Few Bullet Graph** | Replaces circular dials/gauges with linear qualitative range bands (Poor, Satisfactory, Good), a performance bar, and a perpendicular target marker. | 3 background rectangles with calibrated grayscale fills + 1 foreground bar + 1 perpendicular hairline marker. |
| **Plotly / Waterfall** | **Bridge / Variance Ladder** | Shows EBITDA, cloud cost, or inference latency drift from starting baseline to current state via floating green/red delta bars. | Series of floating rectangles with dotted connector bridges linking adjacent column endpoints + bottom total bar. |
| **Altair / Vega-Lite** | **Cleveland Dumbbell Plot** | Replaces dense clustered bar charts by showing baseline vs. target metric pairs connected by a subtle span line. | Hairline horizontal connector segment + 2 circular pips (slate circle for Baseline, theme accent circle for Target). |
| **Altair / Waffle** | **Executive Waffle Grid** | Visualizes adoption or portfolio allocation as a clean $10 \times 10$ matrix of micro-squares or glyphs. | Nested loop creating $100$ small sharp rounded squares ($0.08'' \times 0.08''$) with boolean fill states. |
| **Seaborn** | **Annotated Risk Matrix Heatmap** | Replaces raw tables with a two-axis grid (Likelihood $\times$ Impact) where cell fills convey severity. | Uniform $N \times M$ rectangle grid with 3-tier severity fills (Slate $\to$ Amber $\to$ Red) and centered bold text. |
| **Observable / D3** | **Linear Multi-Stage Funnel** | Displays conversion, candidate drop-off, or patient IVF pipeline attrition through trapezoidal stages. | Sequential trapezoid polygons with centered drop percentages and delta callouts. |

