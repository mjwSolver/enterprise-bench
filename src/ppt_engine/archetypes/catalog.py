"""
Archetype Catalog and Registry
=============================
Canonical definitions, aliases, YAML parameter schemas, and copy-pasteable minimal
examples for all slide archetypes supported by the presentation compiler.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# =============================================================================
# Canonical Archetype Registry
# =============================================================================

ARCHETYPE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # 1. Covers & Dividers
    # -------------------------------------------------------------------------
    "cover": {
        "family": "Covers",
        "aliases": ["hero_cover", "cinematic_cover"],
        "purpose": "Executive presentation cover slide with engagement metadata, product naming, and corporate branding.",
        "keys": [
            "tracker (str): Category eyebrow tracking text",
            "title (str): Main deck title",
            "subtitle (str): Descriptive engagement narrative subtitle",
            "client (str): Client enterprise name",
            "vendor (str): Consulting vendor / delivery partner name",
            "product (str): Target platform or product technology",
            "date_str (str): Presentation delivery date",
            "hero_image_path (str, optional): Background hero image",
            "client_logo_path (str, optional): Client corporate logo",
            "vendor_logo_path (str, optional): Vendor corporate logo",
        ],
        "example_yaml": """- archetype: cover
  tracker: "EXECUTIVE ENGAGEMENT BRIEFING"
  title: "Enterprise Data Cloud Modernization"
  subtitle: "Accelerating Analytics Velocity and Automated Governance with Snowflake"
  client: "Enterprise Client Group"
  vendor: "PT Mitra Integrasi Informatika"
  product: "Snowflake AI Data Cloud"
  date_str: "November 2026"
""",
    },
    "chapter_divider": {
        "family": "Covers",
        "aliases": ["section_divider"],
        "purpose": "Bold full-canvas section separator establishing clear thematic boundaries in long presentations.",
        "keys": [
            "tracker (str): Section tracker tag (e.g. 'SECTION 02')",
            "title (str): Chapter action title",
            "subtitle (str): Transition narrative context",
            "division_tagline (str, optional): Enterprise practice or division name",
            "hero_image_path (str, optional): Optional background photography",
        ],
        "example_yaml": """- archetype: chapter_divider
  tracker: "SECTION 02"
  title: "Lakehouse Architecture & Stage-Gate Governance"
  subtitle: "Core silver feature store coverage, dynamic tables, and zero-PII masking contracts."
""",
    },
    "agenda": {
        "family": "Covers",
        "aliases": ["table_of_contents", "toc"],
        "purpose": "Multi-column executive agenda sequence establishing strategic consensus and stage-gate readiness.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "columns (int, default 2): Grid columns (1-3)",
            "items (list): Agenda items: [{num, title, description, accent_key}]",
        ],
        "example_yaml": """- archetype: agenda
  tracker: "PROJECT ALIGNMENT | EXECUTIVE AGENDA"
  title: "Executive Engagement Sequence and Review Cadence"
  subtitle: "Structured milestone agenda governing discovery, architecture, and pilot execution."
  columns: 2
  items:
    - num: "01"
      title: "Business Drivers & Value Blueprint"
      description: "Strategic objectives, core operational friction, and ROI targets."
    - num: "02"
      title: "Lakehouse Architecture & Governance"
      description: "Silver feature coverage, RBAC masking, and data contracts."
""",
    },
    "thank_you": {
        "family": "Covers",
        "aliases": ["closing", "thank_you_closing"],
        "purpose": "Engagement closing slide with primary stakeholder contacts, office coordinates, and immediate next steps.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Closing header (default 'Thank You')",
            "subtitle (str): Forward-looking partnership commitment",
            "company (str): Corporate division name",
            "office (str): Physical office address",
            "contacts (list): Contact cards: [{role, name, email}]",
            "next_steps (list): Bulleted action items for project kick-off",
        ],
        "example_yaml": """- archetype: thank_you
  tracker: "ENGAGEMENT WRAP-UP | NEXT STEPS"
  title: "Thank You"
  subtitle: "Partnering to accelerate enterprise data modernization with Snowflake AI Data Cloud."
  next_steps:
    - "Finalize Silver tier feature store schema contracts"
    - "Initiate Cortex Copilot Streamlit UI integration sprint"
  contacts:
    - role: "Lead Architect"
      name: "Enterprise Architecture Group"
      email: "consulting@mii.co.id"
""",
    },

    # -------------------------------------------------------------------------
    # 2. Grids & Capabilities
    # -------------------------------------------------------------------------
    "card_grid": {
        "family": "Grids",
        "aliases": ["capability_cards", "pillars_grid"],
        "purpose": "Structured 1-4 column capability card grid with top stripes, status pills, hero metrics, and bold lead bullets.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title stating the core finding",
            "subtitle (str): Contextual narrative subtitle",
            "columns (int, default 4): Number of card columns (1-4)",
            "items (list): Cards: [{title, subtitle, bullets, badge, metric, metric_label, icon, accent_key}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: card_grid
  tracker: "STRATEGIC CAPABILITIES | CORE OFFERINGS"
  title: "Modern Data Platform Unlocks 4 Operational Levers"
  subtitle: "Integrated pillars deliver complete lifecycle support from ingestion to predictive analytics."
  columns: 2
  items:
    - title: "High-Speed Ingestion"
      subtitle: "Snowpipe Streaming & CDC"
      bullets:
        - "**Sub-second latency:** Continuous micro-batch ingestion."
        - "**Zero staging footprint:** Direct write to Bronze Delta."
      accent_key: "accent"
      metric: "< 1.2s"
      metric_label: "P99 INGESTION"
    - title: "Feature Store"
      subtitle: "Silver Dynamic Tables"
      bullets:
        - "**Standardized lineage:** Fully deterministic feature keys."
        - "**Cross-stage joins:** Validated cycle IDs eliminate cartesian."
      accent_key: "primary"
      metric: "99.6%"
      metric_label: "FEATURE INTEGRITY"
  takeaway: "Capital Lever: Consolidate staging layers to reclaim compute credits."
""",
    },
    "split_hero": {
        "family": "Grids",
        "aliases": ["kpi_framework"],
        "purpose": "Asymmetric 35/65 hero split pairing an oversized left ROI/telemetry anchor with right-side narrative cards.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title stating the primary business discovery",
            "subtitle (str): Contextual narrative subtitle",
            "hero_stat (str): Big naked 32-36pt metric (e.g. '$14.8M', '99.6%')",
            "hero_stat_label (str): Metric label (e.g. 'Annualized Value')",
            "hero_stat_subtext (str): 1-2 sentence metric audit context",
            "blocks (list): Narrative blocks: [{title, description, category_tag}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: split_hero
  tracker: "EXECUTIVE SYNTHESIS | ROI BLUEPRINT"
  title: "Centralized Lakehouse Unlocks $14.8M in Annualized Cost Avoidance"
  subtitle: "Automated feature engineering and model serving replace legacy manual pipelines."
  hero_stat: "$14.8M"
  hero_stat_label: "Annualized Value"
  hero_stat_subtext: "Projected 3-year cumulative ROI with 4.2x payback across clinical and ops workflows."
  blocks:
    - title: "Automated Patient Feature Pipeline"
      description: "Silver Dynamic Tables refresh features sub-hourly, eliminating 280 hours of monthly manual SQL extraction."
      category_tag: "PIPELINE VELOCITY"
    - title: "Real-Time Cortex Inference"
      description: "Serverless ML endpoints serve predictive probabilities into EMR before consultation starts."
      category_tag: "PREDICTIVE SERVING"
  takeaway: "Decision Lever: Prioritize Silver staging deployment to lock in FY27 savings."
""",
    },
    "composable_split": {
        "family": "Grids",
        "aliases": ["split_canvas", "composable", "multi_pane", "composite_layout"],
        "purpose": "Composable multi-widget split canvas partitioning the slide into collision-free relative columns hosting modular widgets (hero KPI, card list, card grid, table, process steps) without raw DrawingML coordinates.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action headline expressing analytical conclusion",
            "subtitle (str): Contextual narrative subtitle",
            "split (list|str, optional): Column widths/fractions (e.g. [35, 65], [25, 50, 25], default equal)",
            "gap (float, optional): Gutter width between columns in inches (default: 0.35)",
            "panes (list): Child widgets: [{widget: 'hero_kpi'|'card_list'|'table'|'process_steps'|'card_grid', ...}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: composable_split
  tracker: "EXECUTIVE SYNTHESIS | VALUE ARCHITECTURE"
  title: "Composable Split Architecture Enables Arbitrary Multi-Widget Layouts Without DrawingML Drift"
  subtitle: "Canvas width divides dynamically into relative fractional columns hosting modular widgets."
  split: [35, 65]
  gap: 0.35
  panes:
    - widget: hero_kpi
      stat: "+$4.2M"
      stat_label: "24-Month Net Savings"
      stat_subtext: "Payback model reflects 3.4x ROI across compute retirement and engineering capacity recapture."
      eyebrow: "EXECUTIVE VALUE THESIS"
      card_style: "filled"
    - widget: card_list
      style: "cards"
      items:
        - title: "Infrastructure Rationalization & Compute Deprecation"
          description: "**Retiring Monolithic Compute:** Decommissioning on-prem clusters eliminates fixed refresh cycles."
        - title: "Toolchain Consolidation & Engineering Capacity"
          description: "**Eliminating Point Solutions:** Unifying storage and governance avoids redundant software tools."
  takeaway:
    action: "ARCHITECTURAL EFFICIENCY"
    text: "Decoupling regional partitioning from widget rendering solves custom diagram composition in 1 turn."
""",
    },
    "tech_logo_grid": {
        "family": "Grids",
        "aliases": ["product_portfolio", "tech_grid"],
        "purpose": "Structured partner ecosystem grid displaying technology logos, specialization tiers, and domain pillars.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "items (list): Technologies: [{name, category, logo, accent_key}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: tech_logo_grid
  tracker: "ECOSYSTEM ARCHITECTURE | PLATFORM STACK"
  title: "Enterprise Modernization Leverages Best-of-Breed Cloud Stack"
  subtitle: "Integrated hyperscaler and lakehouse technologies power the analytics foundation."
  items:
    - name: "Snowflake"
      category: "Data Cloud & Cortex GenAI"
    - name: "dbt Core"
      category: "Semantic Transformation"
  takeaway: "Architecture Policy: Native lakehouse services replace fragile self-managed clusters."
""",
    },
    "badge_matrix": {
        "family": "Grids",
        "aliases": ["certifications", "partner_matrix"],
        "purpose": "Tiered partner competency matrix validating certifications, credentials, and compliance standards.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "sections (list): Grouped badge categories: [{title, badges: [str]}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: badge_matrix
  tracker: "COMPETENCY & CREDENTIALS | PARTNERSHIP TIERS"
  title: "Certified Expertise Assures Technical Excellence and Rapid Delivery"
  subtitle: "Tiered specialization across hyperscalers, lakehouse platforms, and governance."
  sections:
    - title: "Cloud Data Architecture"
      badges: ["Snowflake SnowPro Core", "SnowPro Advanced Architect", "AWS Data Analytics"]
    - title: "Security & Governance"
      badges: ["SOC 2 Type II", "ISO 27001", "HIPAA Data Compliance"]
  takeaway: "Assurance: 100% certified engineering squads eliminate delivery execution risk."
""",
    },

    # -------------------------------------------------------------------------
    # 3. Tables & Registers
    # -------------------------------------------------------------------------
    "table": {
        "family": "Tables",
        "aliases": ["matrix_table", "milestones_table", "prerequisites_table", "communication_table", "risk_table", "table_matrix"],
        "purpose": "Flush data table with custom column widths, alignments, status badge pills, alternating zebra fills, and takeaway bar.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title stating the register's active reality",
            "subtitle (str): Contextual narrative subtitle",
            "columns (list): Definitions: [{header, width, align ('LEFT'|'CENTER'|'RIGHT'), is_status, is_index, is_highlight}]",
            "rows (list of lists): Row cell values matching column count",
            "footnote (str, optional): Table footnote or telemetry source citation",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: table
  tracker: "PROGRAM GOVERNANCE | MILESTONE REGISTER"
  title: "Structured Delivery Gates Establish Clear Accountability"
  subtitle: "Execution roadmap with designated owners, SLA targets, and stage-gate readiness."
  columns:
    - header: "#"
      width: 0.6
      align: "CENTER"
      is_index: true
    - header: "Milestone Deliverable"
      width: 4.2
      align: "LEFT"
    - header: "Lead Owner"
      width: 2.2
      align: "LEFT"
    - header: "Target Window"
      width: 2.0
      align: "CENTER"
    - header: "Status"
      width: 2.7
      align: "CENTER"
      is_status: true
  rows:
    - ["1", "Silver Tier Dynamic Tables Deployed", "Data Engineering Lead", "Week 02", "COMPLETED"]
    - ["2", "EMR Cortex Copilot Streamlit Mockup", "Frontend ML Specialist", "Week 04", "ON TRACK"]
    - ["3", "Zero-PII Dynamic Masking Audit", "SecOps Compliance Officer", "Week 06", "CRITICAL GATE"]
  takeaway: "Decision Lever: Authorize Week 06 sign-off gate before advancing to Gold production tables."
""",
    },
    "feature_matrix": {
        "family": "Tables",
        "aliases": ["harvey_balls"],
        "purpose": "Multi-criteria scorecard comparing architectural options, technologies, or vendors across qualitative Harvey balls.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "matrix_data (dict): Data object: {categories: [str], options: [str], rows: [{category, criteria, scores: {opt: score}}]}",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: feature_matrix
  tracker: "PLATFORM EVALUATION | COMPARATIVE SCORECARD"
  title: "Snowflake Cortex Delivers Highest Governance and Lowest Operational Overhead"
  subtitle: "Comparative assessment against legacy custom clusters and third-party SaaS point solutions."
  matrix_data:
    categories: ["Data Architecture", "Model Serving", "Security"]
    options: ["Snowflake Cortex", "Legacy DIY Clusters", "Third-Party SaaS"]
    rows:
      - category: "Data Architecture"
        criteria: "Zero-ETL Lakehouse Integration"
        scores: {"Snowflake Cortex": "FULL", "Legacy DIY Clusters": "NONE", "Third-Party SaaS": "PARTIAL"}
      - category: "Security"
        criteria: "In-VPC Role-Based Masking"
        scores: {"Snowflake Cortex": "FULL", "Legacy DIY Clusters": "PARTIAL", "Third-Party SaaS": "NONE"}
  takeaway: "Platform Verdict: In-warehouse model serving eliminates egress data leakage risks."
""",
    },

    # -------------------------------------------------------------------------
    # 4. Processes & Roadmaps
    # -------------------------------------------------------------------------
    "chevron_process": {
        "family": "Processes",
        "aliases": ["process_flow", "value_chain"],
        "purpose": "Linear chevron stage-gate workflow showing end-to-end phases, milestone deliverables, and active 'WE ARE HERE' status.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title asserting roadmap certainty",
            "subtitle (str): Contextual narrative subtitle",
            "steps (list): Step definitions: [{num, title, status ('COMPLETED'|'IN PROGRESS'|'PLANNED'), deliverables: [str], owner}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: chevron_process
  tracker: "EXECUTION ROADMAP | STAGE GATES"
  title: "Five-Phase Modernization Journey Ensures Safe Cutover"
  subtitle: "Sequential progression from baseline data ingestion to enterprise model serving."
  steps:
    - num: "01"
      title: "Discovery & Ingestion"
      status: "COMPLETED"
      deliverables: ["Source audits", "CDC Snowpipe"]
      owner: "Data Eng"
    - num: "02"
      title: "Feature Staging"
      status: "IN PROGRESS"
      deliverables: ["Dynamic Tables", "Cross-stage joins"]
      owner: "ML Ops"
    - num: "03"
      title: "Cortex Copilot"
      status: "PLANNED"
      deliverables: ["Streamlit UI", "Prompt gates"]
      owner: "App Dev"
    - num: "04"
      title: "Security & RBAC"
      status: "PLANNED"
      deliverables: ["Row masking", "Audit logs"]
      owner: "SecOps"
  takeaway: "Execution Focus: Phase 02 Dynamic Table validation unlocks production inference."
""",
    },
    "timeline_gantt": {
        "family": "Processes",
        "aliases": ["delivery_gantt", "gantt"],
        "purpose": "Multi-workstream delivery Gantt timeline plotting work packages across months or quarters with milestone markers.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title asserting schedule confidence",
            "subtitle (str): Contextual narrative subtitle",
            "timeline_data (dict): Object: {months: [str], workstreams: [{name, color_key, tasks: [{name, start_month, duration_months, is_milestone}]}]}",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: timeline_gantt
  tracker: "PROGRAM SCHEDULE | DELIVERY GANTT"
  title: "12-Week Delivery Timeline Mitigates Production Disruption"
  subtitle: "Structured workstreams with phased validation milestones and production cutover windows."
  timeline_data:
    months: ["Month 01", "Month 02", "Month 03"]
    workstreams:
      - name: "Data Engineering"
        color_key: "accent"
        tasks:
          - name: "Snowpipe CDC Deployment"
            start_month: 1.0
            duration_months: 1.0
          - name: "Dynamic Table Staging"
            start_month: 1.8
            duration_months: 1.2
      - name: "MLOps & Cortex"
        color_key: "primary"
        tasks:
          - name: "Model Endpoint Staging"
            start_month: 2.2
            duration_months: 0.8
            is_milestone: true
  takeaway: "Schedule Risk: Dynamic table sign-off by Week 06 is critical path for model cutover."
""",
    },
    "change_request_procedure": {
        "family": "Processes",
        "aliases": ["cr_procedure"],
        "purpose": "Standardized 4-step Change Control procedure defining SLA response times, approval gates, and escalation thresholds.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "steps (list): Steps: [{step_num, title, description, sla, gate_action}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: change_request_procedure
  tracker: "GOVERNANCE & COMPLIANCE | CHANGE CONTROL"
  title: "Formal Change Control Procedure Guards Production Baseline"
  subtitle: "Transparent review lifecycle with designated evaluation SLAs and sign-off thresholds."
  steps:
    - step_num: "01"
      title: "Request Logging"
      description: "Submit RFC ticket with architectural rationale and blast radius."
      sla: "24 Hours"
      gate_action: "PMO Validation"
    - step_num: "02"
      title: "Technical Review"
      description: "Architecture review board audits compute impact and security posture."
      sla: "48 Hours"
      gate_action: "Lead Sign-off"
  takeaway: "Policy: Any schema alteration altering Silver feature definitions requires formal CR approval."
""",
    },

    # -------------------------------------------------------------------------
    # 5. Strategic Frameworks
    # -------------------------------------------------------------------------
    "bcg_3_horizon": {
        "family": "Strategy",
        "aliases": ["3_tier_architecture", "horizons"],
        "purpose": "BCG 3-Horizon Growth / Modernization Framework categorizing initiatives across H1 (Core), H2 (Emerging), and H3 (Transformational).",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title asserting strategic trajectory",
            "subtitle (str): Contextual narrative subtitle",
            "horizons (list): Horizon columns: [{name, timeframe, focus, metric, metric_label, bullets: [str]}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: bcg_3_horizon
  tracker: "STRATEGIC TRANSFORMATION | THREE HORIZONS"
  title: "Modernization Roadmap Delivers Immediate Stability and Long-Term Intelligence"
  subtitle: "Phased capability evolution balancing immediate cost avoidance with predictive transformation."
  horizons:
    - name: "Horizon 1: Foundation"
      timeframe: "Months 1-3"
      focus: "Lakehouse Core & Staging"
      metric: "99.9%"
      metric_label: "PIPELINE RELIABILITY"
      bullets:
        - "**Automated Ingestion:** Replace manual extracts with Snowpipe."
        - "**Dynamic Feature Tables:** Deterministic cross-stage joins."
    - name: "Horizon 2: Cortex Intelligence"
      timeframe: "Months 4-6"
      focus: "Predictive Analytics"
      metric: "+42%"
      metric_label: "CLINICAL ADOPTION"
      bullets:
        - "**EMR Copilot:** Surface inference probabilities in clinical UI."
        - "**Model Monitoring:** Automated feature drift detection."
    - name: "Horizon 3: Autonomous Lakehouse"
      timeframe: "Months 7-12"
      focus: "Closed-Loop Automation"
      metric: "4.2x"
      metric_label: "CUMULATIVE ROI"
      bullets:
        - "**Closed-loop feedback:** Automated retraining triggers."
        - "**Multi-tenant governance:** Zero-trust cross-clinic data sharing."
  takeaway: "Strategic Imperative: Horizon 1 foundation is mandatory before Horizon 2 Cortex rollout."
""",
    },
    "gap_analysis": {
        "family": "Strategy",
        "aliases": ["as_is_to_be"],
        "purpose": "3-column comparative matrix contrasting Current State ('As-Is') vs Target State ('To-Be') with concrete Remediation Action Plans.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "dimensions (list): Dimensions: [{dimension, as_is, to_be, action_plan, status}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: gap_analysis
  tracker: "GAP ANALYSIS | AS-IS VS TO-BE"
  title: "Architecture Remediation Closes Three Critical Operating Bottlenecks"
  subtitle: "Targeted modernization bridges clinical workflow latency, manual reporting, and data drift."
  dimensions:
    - dimension: "Data Ingestion"
      as_is: "Manual daily CSV batch dumps; 24-hour reporting lag."
      to_be: "Sub-second CDC Snowpipe streaming directly to lakehouse."
      action_plan: "Deploy Snowflake managed Kafka connector in Week 02."
      status: "IN PROGRESS"
    - dimension: "Feature Lineage"
      as_is: "Ad-hoc SQL scripts scattered across local notebooks."
      to_be: "Centralized Silver Dynamic Tables with automated lineage."
      action_plan: "Migrate 12 feature scripts to versioned dbt project."
      status: "PLANNED"
  takeaway: "Priority: Resolving ingestion latency eliminates 85% of downstream data reconciliation overhead."
""",
    },
    "corporate_equity_tree": {
        "family": "Strategy",
        "aliases": ["equity_tree"],
        "purpose": "Hierarchical corporate ownership structure tree displaying holding entities, shareholders, equity stakes, and subsidiaries.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "tree_data (dict): Tree object: {root_title, tier1_nodes: [{name, code, percentage}], tier2_nodes: [{name, code, percentage}]}",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: corporate_equity_tree
  tracker: "CORPORATE GOVERNANCE | EQUITY STRUCTURE"
  title: "Parent Holding Structure Governs Operating Subsidiaries"
  subtitle: "Direct equity stakes validate consolidated financial reporting boundaries."
  tree_data:
    root_title: "Holding Corporation"
    tier1_nodes:
      - name: "Founding Partners"
        code: "FOUNDERS"
        percentage: "55.0%"
      - name: "Public Shareholders"
        code: "IDX:TICKER"
        percentage: "45.0%"
    tier2_nodes:
      - name: "Clinical Operating Unit"
        code: "CLINIC_OPS"
        percentage: "100.0%"
  takeaway: "Governance Anchor: 100% clinical subsidiary ownership assures streamlined decision authority."
""",
    },

    # -------------------------------------------------------------------------
    # 6. Technical Architecture & Telemetry
    # -------------------------------------------------------------------------
    "medallion_tiers": {
        "family": "Architecture",
        "aliases": ["data_tiers", "medallion_stack"],
        "purpose": "3-tier lakehouse data architecture (Bronze, Silver, Gold) specifying allowed feature coverage, excluded tables, and governance safeguards.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title asserting schema boundary rules",
            "subtitle (str): Contextual narrative subtitle",
            "tiers (list): Tier definitions: [{tier, tier_badge, metric, metric_label, description, tables: [str], excluded_note}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: medallion_tiers
  tracker: "MEDALLION DATA TIERS | ELIGIBILITY ROSTER"
  title: "Silver Tables Provide Clean Feature Coverage; Bronze Requires Approval"
  subtitle: "Strict tier governance prevents raw dirty data from contaminating predictive models."
  tiers:
    - tier: "BRONZE TIER (RAW INGESTION)"
      tier_badge: "RESTRICTED"
      metric: "48 Tables"
      metric_label: "RAW INGESTION"
      description: "Direct append-only CDC feeds from legacy MySQL and Postgres systems."
      tables: ["RAW_PATIENT_LOGS", "CDC_BILLING_EVENT", "RAW_APPOINTMENT_LOG"]
      excluded_note: "Direct ML training strictly prohibited to prevent data leakage."
    - tier: "SILVER TIER (CONSOLIDATED)"
      tier_badge: "CERTIFIED"
      metric: "12 Tables"
      metric_label: "FEATURE STAGING"
      description: "Deduplicated, type-cast, and joined via validated CYCLE_ID keys."
      tables: ["FCT_CYCLE_SUMMARY", "DIM_PATIENT_ATTRIBUTES", "STG_CLINICAL_OUTCOMES"]
      excluded_note: "Primary foundation for Cortex model feature store."
    - tier: "GOLD TIER (AGGREGATED)"
      tier_badge: "GOVERNED"
      metric: "5 Tables"
      metric_label: "BI SERVING"
      description: "Executive dashboards and regulatory financial compliance marts."
      tables: ["DM_MONTHLY_EXECUTIVE_KPI", "RPT_CLINIC_PERFORMANCE"]
      excluded_note: "Post-hoc aggregates only; not used for real-time inference."
  takeaway: "Governance Invariant: Never train predictive ML models on Gold aggregation tables."
""",
    },
    "gate_validation": {
        "family": "Architecture",
        "aliases": ["threshold_bars", "coverage_gate_validation", "metric_gate_review"],
        "purpose": "Multi-tier threshold progress bar charts comparing actual telemetry against required compliance/accuracy stage-gates.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title stating gate passage status",
            "subtitle (str): Contextual narrative subtitle",
            "gates (list): Metric gates: [{title, actual (float), threshold (float), status ('PASS'|'WARNING'|'CRITICAL'), category, variance_label, is_hero}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: gate_validation
  tracker: "STAGE-GATE VALIDATION | ACCURACY THRESHOLDS"
  title: "Model Accuracy Exceeds 92% Gate; Latency Remains Within 100ms SLA"
  subtitle: "Rigorous empirical telemetry audit verifies production cutover readiness."
  gates:
    - title: "Cycle Outcome Prediction AUC-ROC"
      actual: 0.942
      threshold: 0.900
      status: "PASS"
      category: "MODEL ACCURACY"
      variance_label: "+4.2% Above Gate"
      is_hero: true
    - title: "Inference Latency P95"
      actual: 0.720
      threshold: 0.850
      status: "PASS"
      category: "OPERATIONAL SLA"
      variance_label: "15% Headroom"
  takeaway: "Go/No-Go Decision: All gating criteria met; approve canary deployment to Clinic 01."
""",
    },
    "open_telemetry_flow": {
        "family": "Architecture",
        "aliases": ["pipeline_gate_matrix", "geometric_telemetry", "telemetry_pipeline_hud"],
        "purpose": "End-to-end data/telemetry pipeline flow diagram with ingestion gates, processing nodes, and operational health badges.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "flow_nodes (list): Nodes: [{name, type, status, metrics}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: open_telemetry_flow
  tracker: "OBSERVABILITY & TELEMETRY | DATA PIPELINE"
  title: "End-to-End Pipeline Telemetry Assures Sub-Second Data Health"
  subtitle: "OpenTelemetry tracing captures micro-batch latency from source CDC to feature serving."
  flow_nodes:
    - name: "Postgres CDC Source"
      type: "INGEST"
      status: "HEALTHY"
    - name: "Snowpipe Streaming"
      type: "QUEUE"
      status: "HEALTHY"
    - name: "Dynamic Table Staging"
      type: "TRANSFORM"
      status: "HEALTHY"
  takeaway: "Telemetry SLA: P99 end-to-end pipeline latency audited at 820ms."
""",
    },
    "crisp_dm_gate": {
        "family": "Architecture",
        "aliases": ["crisp_dm", "crisp_dm_lifecycle"],
        "purpose": "Industry-standard CRISP-DM 6-phase machine learning readiness gate validator with stage checklist criteria.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "phases (list): Phases: [{name, status, checklist: [str]}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: crisp_dm_gate
  tracker: "ML LIFECYCLE GOVERNANCE | CRISP-DM AUDIT"
  title: "CRISP-DM Phase 04 Modeling Complete; Advancing to Clinical Evaluation"
  subtitle: "Methodical lifecycle governance validates clinical feature readiness before production cutover."
  phases:
    - name: "Business Understanding"
      status: "PASSED"
      checklist: ["Clinical KPI alignment", "ROI baseline signed off"]
    - name: "Data Understanding"
      status: "PASSED"
      checklist: ["Schema audit complete", "Cross-stage join keys verified"]
    - name: "Evaluation & Deployment"
      status: "IN PROGRESS"
      checklist: ["Clinician blind test", "Shadow mode latency audit"]
  takeaway: "Quality Gate: Shadow deployment must maintain 99.5% uptime for 14 continuous days."
""",
    },
    "browser_mockup": {
        "family": "Architecture",
        "aliases": ["window_mockup", "app_mockup", "app_walkthrough", "module_walkthrough"],
        "purpose": "High-DPI macOS window viewport framing live enterprise web app screenshots, dashboards, or Streamlit UIs.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title describing UI workflow",
            "subtitle (str): Contextual narrative subtitle",
            "image_path (str): Relative path to high-resolution UI screenshot",
            "mockup_url (str, optional): Simulated browser address bar URL",
            "window_title (str, optional): Window title bar caption",
            "badge (str, optional): Status pill on top-right of frame",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: browser_mockup
  tracker: "EMR COPILOT INTEGRATION | CLINICAL WORKFLOW"
  title: "Native Streamlit Copilot Embeds Directly into Existing EMR Workspace"
  subtitle: "Clinicians receive real-time predictive probabilities without leaving their consultation screen."
  image_path: "assets/images/mockups/magic_emr_cortex_copilot.png"
  mockup_url: "https://emr.morulaivf.co.id/portal/patient/cycle-summary"
  window_title: "EMR Clinical Workspace — Cortex Intelligence Assistant"
  badge: "LIVE PROTOTYPE"
  takeaway: "UX Paradigm: Zero-context-switching design increases daily clinician adoption by 74%."
""",
    },
    "iceberg_concept": {
        "family": "Architecture",
        "aliases": ["iceberg"],
        "purpose": "Surface vs Subsurface visualization contrasting visible business metrics with hidden foundational architecture requirements.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str): Contextual subtitle",
            "visible_items (list of str): Visible top-level items above waterline",
            "subsurface_items (list of str): Deep foundational architecture requirements below waterline",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: iceberg_concept
  tracker: "TECHNICAL FOUNDATION | ICEBERG FRAMEWORK"
  title: "Predictive Analytics Relies on a Heavy Subsurface Governance Foundation"
  subtitle: "The visible UI assistant is enabled by extensive lakehouse data modeling, masking, and CDC pipelines."
  visible_items:
    - "Streamlit EMR Copilot UI"
    - "Real-Time Patient Outcome Predictions"
    - "Executive BI Dashboard Metrics"
  subsurface_items:
    - "Dynamic Table Staging & Deterministic Join Keys"
    - "Snowpipe Micro-Batch CDC Ingestion"
    - "Role-Based Access Control & Column Masking"
    - "Automated Feature Drift & Model Lineage Tracking"
  takeaway: "Investment Reality: 80% of project effort is dedicated to the subsurface data foundation."
""",
    },

    # -------------------------------------------------------------------------
    # 7. Governance & Organization
    # -------------------------------------------------------------------------
    "governance_org_structure": {
        "family": "Governance",
        "aliases": ["org_chart", "raci"],
        "purpose": "Program governance organization chart showing Steering Committee, Working Groups, PMO, and delivery teams with RACI accountabilities.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title asserting governance rigor",
            "subtitle (str): Contextual narrative subtitle",
            "leadership (list): Executive tier: [{role, name, responsibility}]",
            "working_groups (list): Squads: [{name, lead, members: [str]}]",
            "takeaway (str|dict, optional): Bottom executive decision lever bar",
        ],
        "example_yaml": """- archetype: governance_org_structure
  tracker: "PROGRAM GOVERNANCE | OPERATING MODEL"
  title: "Multi-Tiered Governance Structure Assures Strategic Alignment"
  subtitle: "Clear escalation paths and accountability boundaries across executive and technical squads."
  leadership:
    - role: "Executive Sponsor"
      name: "Chief Technology Officer"
      responsibility: "Strategic prioritization and capital allocation."
    - role: "Program Director"
      name: "Lead Enterprise Architect"
      responsibility: "Cross-workstream delivery and risk mitigation."
  working_groups:
    - name: "Data Engineering Squad"
      lead: "Principal Data Engineer"
      members: ["CDC Pipelines", "Dynamic Tables", "Data Quality"]
    - name: "Clinical ML Squad"
      lead: "Lead ML Scientist"
      members: ["Cortex Serving", "Model Validation", "Clinician Feedback"]
  takeaway: "Accountability: Weekly Steering Committee cadence eliminates cross-squad blockers."
""",
    },
}


def get_archetype_info(name: str) -> Optional[Dict[str, Any]]:
    """Resolve an archetype entry by canonical name or accepted alias."""
    query = name.lower().strip()
    if query in ARCHETYPE_REGISTRY:
        info = dict(ARCHETYPE_REGISTRY[query])
        info["canonical_name"] = query
        return info

    for canonical, data in ARCHETYPE_REGISTRY.items():
        if query in [a.lower() for a in data.get("aliases", [])]:
            info = dict(data)
            info["canonical_name"] = canonical
            return info

    return None
