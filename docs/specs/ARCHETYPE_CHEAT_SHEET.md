# ARCHETYPE_CHEAT_SHEET.md — Declarative Slide Archetypes Catalog

This cheat sheet documents the available slide archetypes compiled by Diagram Engine V2 (`bench ppt build-deck` / `bench diagram v2 compile`).

> [!NOTE]
> All archetypes are authored exclusively in declarative YAML (`specs/<deck>.yaml`).
> Use the CLI for instant schema discovery: `uv run bench ppt archetypes --describe <archetype_name>`.

---

## 1. Grids & Layouts

### `card_grid`
Structured multi-column card grid (2, 3, or 4 columns) with optional top stripes, category badges, and metric callouts.
```yaml
- slide: 2
  archetype: card_grid
  tracker: STRATEGIC CAPABILITIES | CORE SERVICES
  title: Comprehensive Enterprise Solutions Span Infrastructure to AI
  subtitle: Eight integrated core pillars deliver complete lifecycle support.
  columns: 4
  items:
    - title: Cloud Migration
      subtitle: AWS & Azure Landing Zones
      badge: Foundation
      top_stripe: true
      bullets:
        - Lead In: Direct cause-and-effect detail.
        - Next Point: Second punchy bullet.
  takeaway: Capital equation or strategic decision lever.
```

### `split_hero`
Asymmetric layout (35/65) featuring a primary hero metric on the left and structured narrative blocks on the right.
```yaml
- slide: 3
  archetype: split_hero
  tracker: PERFORMANCE BENCHMARK | TELEMETRY
  title: Operational Telemetry Validates 28% Throughput Increase
  subtitle: Asymmetric performance profile across 12,000 production transactions.
  hero_metric: "+28%"
  hero_metric_label: HISTORICAL LIFT
  hero_descriptor: Measured over 27 continuous operating months.
  right_blocks:
    - title: Query Engine Acceleration
      description: In-memory columnar processing eliminates staging bottlenecks.
    - title: Resource Partitioning
      description: XS compute warehouses isolate exploratory analysis.
  takeaway: Resource monitors enforce auto-suspend boundaries.
```

---

## 2. Tables & Matrices

### `table_slide`
Contiguous enterprise data table with alternating rows, status badges, and takeaway bar.
```yaml
- slide: 4
  archetype: table_slide
  tracker: CLINICAL DATA ROSTER | STAGE MAPPING
  title: Four Asynchronous Fact Tables Anchor Patient Journey Analysis
  subtitle: Complete inventory of clinical facts and operational reconciliation keys.
  columns:
    - name: STAGE
      width: 1.8
    - name: FACT TABLE
      width: 3.2
    - name: VOLUME
      width: 1.8
    - name: STATUS
      width: 1.8
    - name: GOVERNANCE
      width: 3.1
  rows:
    - ["Stage 1: OPU", "FACT_MNQ.FACT_OPU", "18,420", "[GREEN] Verified", "Surgical record"]
    - ["Stage 2: Lab", "FACT_SCIENTIFIC.FACT_EMBRYO", "42,100", "[AMBER] Partial", "Straw balance"]
  takeaway: Operational reconciliation must precede model training.
```

---

## 3. Processes & Flows

### `chevron_process`
Directional stage-gate sequence with deliverables and a floating "WE ARE HERE" location badge.
```yaml
- slide: 5
  archetype: chevron_process
  tracker: IMPLEMENTATION ROADMAP | STAGE GATES
  title: Four-Stage Transition Sequence Delivers Governed Production Servicing
  subtitle: Phased delivery path from sandbox audit to production release.
  steps:
    - num: 1
      title: Discovery & Audit
      status: COMPLETED
      owner: Marcell
      deliverables:
        - "Audit: Snowflake Silver schemas"
        - "Interviews: Clinic staff"
    - num: 2
      title: Treatment Copilot
      status: IN PROGRESS
      owner: Engineering Team
      deliverables:
        - "Dashboard: 2-pane command center"
        - "Sanity: Embryo balance check"
  takeaway: Gate 2 clearance required prior to sandbox migration.
```

---

## 4. Architecture & Data Systems

### `medallion_tiers`
Three-tier data lakehouse medallion flow (Bronze, Silver, Gold) with table rosters and governance safeguards.
```yaml
- slide: 6
  archetype: medallion_tiers
  tracker: DATA ARCHITECTURE | MEDALLION STAGES
  title: Lakehouse Ingestion Model Isolates Raw Events from Feature Serving
  subtitle: Three-tier data flow enforces data quality gates before model consumption.
  tiers:
    - tier: SILVER
      tier_badge: APPROVED FOR FEATURE TRAINING
      metric: "95.8%"
      metric_label: AVERAGE JOIN COVERAGE
      tables:
        - "FACT_MNQ.FACT_OPU (18.4k rows)"
        - "FACT_SCIENTIFIC.FACT_EMBRYO (42.1k rows)"
      excluded_note: Read-only access enforced via MII_WH_XS.
    - tier: GOLD
      tier_badge: STRICTLY FORBIDDEN FOR TRAINING
      metric: "0"
      metric_label: TRAINING DEPENDENCIES
      tables:
        - "DM_JOURNEY.DM_PATIENT"
      excluded_note: Aggregations leak future clinical outcomes into past states.
  takeaway: ML features must be strictly derived from Bronze/Silver historical events.
```

### `browser_mockup`
High-DPI desktop browser frame displaying an embedded application screenshot.
```yaml
- slide: 7
  archetype: browser_mockup
  tracker: APPLICATION INTERFACE | INTERACTIVE COMMAND CENTER
  title: Streamlit in Snowflake Delivers Real-Time Clinical Journey Copilot
  subtitle: High-density command center visualizing missingness flags and straw balance.
  image_path: assets/images/mockups/magic_emr_cortex_copilot.png
  mockup_url: "https://morula.snowflakecomputing.com/streamlit/treatment-copilot"
  takeaway: Interactive filtering accelerates clinic coordinator intervention.
```
