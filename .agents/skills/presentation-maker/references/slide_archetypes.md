# Slide Layout Archetypes

Presentation designs fall into structured archetypes based on their narrative function and argument topology. For layout routing logic, see [`references/mbb_storyline_and_page_logic.md`](./mbb_storyline_and_page_logic.md).

---

## Part I: Enterprise Consulting Archetypes

### 1. Split-Hero Feasibility / Strategic Inquiry (`split_hero`)
- **Structure**: 1/3 Hero Stat/Takeaway Panel (Left) + 2/3 Analytical Dimension Cards (Right).
- **Use Case**: Strategic decision gates, diagnostic root causes, or single high-impact metric anchors (e.g. `AUC-ROC >= 0.82` or `92% Freeze-All Severance`).
- **Engine Builder**: `PitchDeckBuilder` (`archetype: split_hero`).

### 2. Gap Analysis & As-Is vs To-Be (`gap_analysis` / `as_is_to_be`)
- **Structure**: 2 paired comparison columns (As-Is State vs Proposed Target Architecture) with transitional delta badges and impact summary cards.
- **Use Case**: Technology replacement justification, legacy debt elimination, operational modernization.
- **Engine Builder**: `PitchDeckBuilder` (`archetype: gap_analysis`).

### 3. BCG 3-Horizon Modernization (`bcg_3_horizon`)
- **Structure**: 3 chronological columns (`Horizon 1: 0-3m`, `Horizon 2: 3-9m`, `Horizon 3: 9-18m`) on clean white surface containers with subtle hairline borders (`0.75pt`, zero top stripes).
- **Anatomy**:
  - Top: Clean uppercase horizon eyebrow tag (`HORIZON 01 • 0-3 MONTHS`) + sleek status pill (`ACTIVE`).
  - Title & Focus: Prominent headline (`14.5pt` bold) + italicized/muted strategic focus narrative (`9.5pt`).
  - Hero Metric: Open-air floating metric (`26pt` bold) + descriptive label (`9pt`), with zero nested gray box containers.
  - Divider: Subtle hairline horizontal rule (`0.75pt`, `#E2E8F0`).
  - Initiatives: Hanging indent bullet points with bold lead-ins (`• **Lead:** Action...`).
- **Use Case**: Long-term technology roadmaps, data platform migration pacing, phased budget allocation.
- **Engine Builder**: `ConsultingDeckBuilder.add_bcg_3_horizon_slide(...)` or `PitchDeckBuilder` (`archetype: bcg_3_horizon`).

### 4. Dense Workstream Runbook (`dense_workstream_runbook`, Gear 3)
- **Structure**: 4-quadrant container discipline (Objective, Vendor Actions, Client Actions, Dependencies) anchored by a named PIC ownership matrix and micro-typography (8.5–9.5pt).
- **Use Case**: Technical kickoff alignment, CAB review, operational transition runbooks.
- **Engine Builder**: `ConsultingDeckBuilder.add_dense_workstream_runbook_slide(...)`.

### 5. Target Architecture Swimlane (`target_architecture_swimlane`, Gear 2)
- **Structure**: 3-column boundary swimlanes (Source Systems &rarr; Cloud Platform &rarr; Consumer Applications) with labeled workstream routes (`WS1`, `WS2`, `WS4`) and boundary fences.
- **Use Case**: Pre-KOM technical alignment, integration scope fencing.
- **Engine Builder**: `ConsultingDeckBuilder.add_target_architecture_swimlane_slide(...)`.

### 6. Audited Metric & Empirical Table (`table` / `matrix_table`)
- **Structure**: Modern executive table following the **Single-Line Rule**:
  - Header Row: Transparent or soft surface tint (`#F1F5F9`) with dark slate bold text (`9.0pt`), separated from data by a single `1.0pt` hairline rule (no solid colored banner block).
  - Rows: Borderless cells with subtle alternating fill (`#F8FAFC`) and `0.5pt` bottom dividers (no individual boxed row cards).
  - Takeaway Card: Clean surface card with vertical left accent bar indicator (`4pt` width) rather than an overused top accent stripe.
- **Use Case**: Query audit results, schema inventory, data severance findings, contractual SLA tables.
- **Engine Builder**: `PitchDeckBuilder` (`archetype: table`).

### 7. Linear Value Chain & Process (`chevron_process` / `process_flow`)
- **Structure**: 4–5 sequenced chevron blocks with stage badges, prerequisites, and milestone criteria.
- **Use Case**: Delivery lifecycle, Change Request procedures, release governance gates.
- **Engine Builder**: `PitchDeckBuilder` (`archetype: chevron_process`).

---

## Part II: Academic & Econometric Archetypes (Research Papers)

### 1. Research Gap & Bridge (3-Stage Flow)
- **Stage 1 (Left Card)**: Established Literature & Prior Findings.
- **Stage 2 (Middle Card / Bridge)**: The Unexplored Context / Conflict.
- **Stage 3 (Right Card / Focus)**: Core Research Question & Contribution.

### 2. Empirical Model & Methodology Specification
- **Top Block**: Mathematical / econometric equation displayed in a highlighted accent box.
- **Bottom Grid**: 3-column definition cards (Dependent, Independent, Control variables).

### 3. Empirical Results & Regression Tables
- **Left/Center (65% width)**: Structured statistical table with standard errors and significance stars (`*`, `**`, `***`).
- **Right Panel (35% width)**: Key Finding callout + Hypothesis Confirmation link.
