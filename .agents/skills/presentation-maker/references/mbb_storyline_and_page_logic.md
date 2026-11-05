# MBB Storyline Architecture, Page Logic & Layout Routing

Operational reference for management consulting presentation standards (McKinsey, BCG, Bain) implemented natively within Enterprise Workbench (`enterprise-bench`).

---

## 1. Top-Down Narrative Engineering (Pyramid Principle & SCQA)

Executive presentations fail when they force stakeholders to mentally assemble disconnected facts. Communication must follow Barbara Minto's Pyramid Principle: **Lead with the governing recommendation, then provide MECE supporting pillars.**

### The SCQA Storyline Spine
Before writing slide copy, anchor the deck's executive narrative in an explicit SCQA chain:
1. **Situation (S):** Undisputed business context and current operational reality (e.g., *"Morula IVF operates 10+ clinical centers with 38k+ FET procedures recorded in EMR"*).
2. **Complication (C):** The operational, architectural, or commercial bottleneck threatening performance (e.g., *"92% of cycles are Freeze-All; embryo straw keys are unmapped, severing longitudinal outcome tracking"*).
3. **Core Question (Q):** The critical decision gate facing executive sponsors (e.g., *"Can predictive AI be trained on raw EMR joins, or must relational keys be stabilized first?"*).
4. **Answer / Resolution (A):** The definitive analytical conclusion and tactical path forward (e.g., *"Isolate key reconciliation in Phase 1 before model training to eliminate 760x Cartesian explosion"*).

---

## 2. Page Logic & Action Headline Standards

### The One-Slide, One-Insight Rule
- Every slide must assert **exactly one governing insight**. If a slide contains two competing conclusions, split it into two slides.
- A slide is an analytical proof, not a storage locker for data points.

### The Action Headline Formula
Slide titles must NEVER be passive category tags. They must be active, complete sentences expressing the analytical takeaway.

| Anti-Pattern (Passive Category) | MBB Action Headline (Finding + Driver + Consequence) |
| :--- | :--- |
| *“Data Warehouse Performance”* | **“Nightly Batch Jobs Exceed the 6-Hour SLA Window Due to Unindexed Stage Joins, Delaying Morning Branch Operations”** |
| *“Cloud Migration Options”* | **“Decoupled Cloud Compute Lowers Annual TCO by 34% by Auto-Suspending Non-Production Warehouses Outside Working Hours”** |
| *“Security & Compliance Overview”* | **“Unmasked PII in Staging Schemas Violates UU PDP; Implementing Dynamic Column Masking Restores Compliance Prior to Audit”** |
| *“Next Steps & Roadmap”* | **“Phase 1 Workstream Focuses Exclusively on Relational Key Remediation to Unblock Phase 2 Supervised Learning”** |

### Headline Construction Rule
`Action Headline = [Analytical Conclusion] + [Direct Mechanical Driver] + [Operational Consequence / Action]`
- Max length: 2 lines ($w \ge 11.85''$).
- Subtitle: Flowed in the **same text box** (`space_before = Pt(10)`) to provide quantitative telemetry, methodology benchmarks, or explicit operational scope.

---

## 3. MECE Structural Container Discipline

Supporting content beneath the action title must be **Mutually Exclusive and Collectively Exhaustive (MECE)**:
- **Mutually Exclusive:** No overlapping scope between cards, columns, or quadrants. If Card 1 covers *Ingestion Architecture*, Card 2 cannot secretly repeat *CDC connectors*.
- **Collectively Exhaustive:** Together, the cards span the complete problem boundary (e.g., People / Process / Technology or Sourcing / Storage / Consumption).
- **Lead-in Subtitles:** Every container card must begin with a **bold summary takeaway phrase** before any bullet points. Never start a container with an unanchored bullet.
- **Data-to-Ink Maximization:** Strip all non-essential visual elements. Zero drop shadows, zero decorative gradient fills, sharp rectangles for structured cards, and minimum 20% whitespace.

---

## 4. Archetype Layout Routing Decision Matrix

Select the slide visual archetype based on the logical topology of the argument:

| Logical Argument Type | Visual Topology | Native `enterprise-bench` Archetype | Complexity Gear |
| :--- | :--- | :--- | :--- |
| **Dichotomy / Gap Analysis** | As-Is vs To-Be comparison, trade-offs, transition delta | `gap_analysis` / `as_is_to_be` | Gear 1–2 |
| **Diagnostic Feasibility Gate** | Single critical bottleneck with multidimensional impact | `split_hero` (Left hero stat + 3 analytical cards) | Gear 1–2 |
| **Phased Modernization** | Multi-year roadmap, horizon scaling, portfolio staging | `bcg_3_horizon` (`H1 0-6m`, `H2 6-18m`, `H3 18-36m`) | Gear 1–2 |
| **End-to-End System Boundary** | Data ingestion, cloud transformation, consumer integration | `snowflake_data_pipeline` / `target_architecture_swimlane` | Gear 2 (Pre-KOM) |
| **Operational Workstream Runbook**| Team assignments, PIC ownership, prerequisite handoffs | `dense_workstream_runbook` (4 quadrants + RACI table) | Gear 3 (Technical) |
| **Quantitative Empirical Proof** | Audited sample sizes, regression tables, variance analysis | `table` / `matrix_table` with takeaway badge | Gear 2–3 |
| **Multilateral Evaluation** | Capability scoring, vendor feature parity, readiness | `feature_matrix` (Harvey Balls / status badges) | Gear 2 |
| **Linear Value Chain** | Sequential lifecycle, change management, approval stages | `chevron_process` / `cr_procedure` | Gear 1–2 |

---

## 5. Pre-Flight Consulting Polish & Humanizer Gate

Before compiling or publishing any slide deck, execute this pre-flight verification:

1. **Zero AI Fluff:**
   - Strip all corporate filler words: *"In order to ensure..."*, *"It is important to remember that..."*, *"A holistic comprehensive approach..."*, *"Empowering synergies..."*.
   - Replace with terse, active engineering verbs: *Eliminates, Truncates, Isolates, Enforces, Reconciles, Enacts, Governs*.
2. **Diagnostic Semantic Color Integrity:**
   - Semantic color tokens must be deterministic:
     - Defect / Bottleneck / High Risk: `#DC2626` / `#FEE2E2`
     - Warning / Wait State / Boundary Fence: `#D97706` / `#FEF3C7`
     - Active Ingress / Client Flow: `#0284C7` / `#EFF6FF`
     - Reconciled / Approved Target State: `#16A34A` / `#DCFCE7`
     - Structural Container: `#CBD5E1` / `#F8FAFC`
   - Never use arbitrary accent rainbows or ungrounded decorative hues.
3. **Footnote & Source Attribution:**
   - Every quantitative claim or telemetry point must cite an explicit source in the lower-left footer:
     - `*) Source: Production Query History audit across 38,580 records, Oct 2026.`
4. **Clean Slide Chrome:**
   - Cover slide: Clean typographic columns for client and vendor metadata. Zero boxed card containers. Zero cover footer or page number.
   - Content slides: Sequential pagination starting from Slide 2 (`02 / NN`). Bottom-right confidentiality classification banner.
