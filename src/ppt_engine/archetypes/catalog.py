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
        "purpose": "Opt-in engagement closing slide with optional stakeholder contacts, office coordinates, and next steps; optically centers clean 'Thank You' when contact blocks are omitted.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Closing header (default 'Thank You')",
            "subtitle (str, opt-in): Closing narrative sentence",
            "company (str, opt-in): Corporate division name",
            "office (str, opt-in): Physical office address",
            "contacts (list, opt-in): Contact cards: [{role, name, email}]",
            "next_steps (list, opt-in): Bulleted action items for project kick-off",
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
        "purpose": "Auto-balanced 1-12+ capability card grid with density-scaled typography (>= 8.0 pt floor), opt-in top stripes, hero metrics, and bold lead bullets.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title stating the core finding (>= 18.0 pt)",
            "subtitle (str, opt-in): Contextual narrative subtitle",
            "columns (int, optional): Override column count (omit to auto-balance 1-12+ items across 1-4 columns)",
            "items (list): Cards: [{title, subtitle, bullets, badge, metric, metric_label, icon, accent_key, has_top_stripe}]",
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
        ],
        "example_yaml": """- archetype: split_hero
  tracker: "EXECUTIVE SYNTHESIS | ROI BLUEPRINT"
  title: "Centralized Lakehouse Unlocks $14.8M in Annualized Cost Avoidance"
  subtitle: "Automated feature engineering and model serving replace legacy manual pipelines."
  hero_stat: "$14.8M"
  hero_stat_label: "Annualized Value"
  hero_stat_subtext: "Projected 3-year cumulative ROI with 4.2x payback across clinical and ops workflows."
  blocks:
    - title: "Automated Customer Feature Pipeline"
      description: "Silver Dynamic Tables refresh features sub-hourly, eliminating 280 hours of monthly manual SQL extraction."
      category_tag: "PIPELINE VELOCITY"
    - title: "Real-Time Cortex Inference"
      description: "Serverless ML endpoints serve predictive probabilities into enterprise applications in real time."
      category_tag: "PREDICTIVE SERVING"
""",
    },
    "composable_split": {
        "family": "Grids",
        "aliases": ["split_canvas", "composable", "multi_pane", "composite_layout"],
        "purpose": "Composable multi-widget split canvas partitioning the slide into collision-free columns (`direction: horizontal`) or rows (`direction: vertical` / `rows`) hosting modular or nested `vertical_stack` widgets without raw DrawingML coordinates.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action headline expressing analytical conclusion",
            "subtitle (str, opt-in): Contextual narrative subtitle",
            "direction (str, optional): 'horizontal' (default) or 'vertical'",
            "split (list|str, optional): Column or row fractions (e.g. [35, 65], [38, 62], default equal)",
            "gap (float, optional): Gutter width/height in inches (default: 0.35 horizontal, 0.22 vertical)",
            "panes (list): Child widgets: [{widget: 'hero_kpi'|'card_list'|'table'|'process_steps'|'process_flow'|'card_grid'|'native_chart'|'stacked_column_exhibit'|'code_block'|'image'|'vertical_stack'|'horizontal_stack', ...}]; process_steps supports horizontal owner sub-labels, branch (Yes/No), and caption; vertical_stack nests rows inside a column",
            "rows (list, optional): Alias for panes that automatically sets direction: 'vertical'",
            "footnote (str, opt-in): Bottom attribution or evaluation window note",
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
  # takeaway: "Decision Lever: Approve compute retirement schedule."  # Optional — omit unless needed
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
""",
    },

    # -------------------------------------------------------------------------
    # 3. Tables & Registers
    # -------------------------------------------------------------------------
    "table": {
        "family": "Tables",
        "aliases": ["matrix_table", "milestones_table", "prerequisites_table", "communication_table", "risk_table", "table_matrix"],
        "purpose": "Flush data table with custom column widths, alignments, status badge pills, alternating zebra fills, and optional takeaway bar.",
        "keys": [
            "tracker (str): Category eyebrow tag",
            "title (str): Action title stating the register's active reality",
            "subtitle (str): Contextual narrative subtitle",
            "columns (list): Definitions: [{header, width, align ('LEFT'|'CENTER'|'RIGHT'), is_status, is_index, is_highlight}]",
            "rows (list of lists): Row cell values matching column count; status cells support str (soft auto green/amber/red/blue) or {text, color: green|amber|red|blue|slate}",
            "footnote (str, optional): Table footnote or telemetry source citation",
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
  takeaway: "Decision Lever: Authorize Week 06 sign-off gate before advancing to Gold production tables."  # Optional — omit unless slide asserts a decision gate
""",
    },
    "feature_matrix": {
        "family": "Tables",
        "aliases": ["harvey_balls"],
        "purpose": "Multi-criteria scorecard comparing architectural options, technologies, or vendors across qualitative Harvey balls.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str, opt-in): Contextual subtitle",
            "recommended_column (str, opt-in): Optional highlighted option name",
            "footnote (str, opt-in): Optional legend/methodology note",
            "matrix_data (dict): Data object: {categories: [str], options: [str], rows: [{category, criteria, scores: {opt: score}}]}",
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
""",
    },
    "narrative_row_list": {
        "family": "Tables",
        "aliases": ["open_text_list", "row_feature_list"],
        "purpose": "Open-canvas, hairline-separated qualitative row list with optional left rail, numbered/colored badges, vertical flag stripes, and per-section/per-row accent overrides.",
        "keys": [
            "title (str, OBLIGATED): Action title stating the slide's active finding",
            "rows (list of dicts, OBLIGATED if sections omitted): [{title, description|bullets, index, lead_in, accent_color, flag_stripe}]",
            "sections (list of dicts, optional): Grouped sections [{title, accent_color, flag_stripe, rows: [...]}] for mixing themes (e.g. brickred top + snowblue bottom)",
            "tracker (str, opt-in): Category eyebrow tag",
            "subtitle (str, opt-in): Contextual narrative subtitle",
            "sidebar_title (str, opt-in): Optional left-rail headline (McKinsey debate style)",
            "sidebar_note (str, opt-in): Optional left-rail muted footnote",
            "show_index (bool, opt-in): Auto-number rows 1..N with circular badges",
            "flag_stripe (bool, opt-in): Draw vertical accent flag stripe on left edge of rows",
            "footer_callout (str, opt-in): Subtle bottom hairline + callout text",
        ],
        "example_yaml": """- archetype: narrative_row_list
  title: "Five Core Capabilities Anchor Modern Retail POS Modernization"
  show_index: true
  flag_stripe: true
  sections:
    - title: "Storefront & Checkout Operations (Brick Red)"
      accent_color: "brickred"
      rows:
        - title: "Offline Queueing"
          description: "Local SQLite journal buffers card-present tokens during WAN outages."
    - title: "Cloud Inventory & Analytics (Snow Blue)"
      accent_color: "snowblue"
      rows:
        - title: "Real-Time Stock"
          description: "Sub-second CDC events sync SKU counts across all regional stores."
""",
    },
    "takeaway_columns": {
        "family": "Grids",
        "aliases": ["executive_summary_columns"],
        "purpose": "McKinsey-style open-canvas 2-4 column executive summary with circular badges, hairline rules, and bold-lead paragraphs.",
        "keys": [
            "title (str): Action title",
            "columns (list): [{title, badge, accent_color, points: [str]}]",
            "tracker (str, opt-in): Category eyebrow tag",
            "subtitle (str, opt-in): Narrative subtitle",
            "footnote (str, opt-in): Bottom source note",
        ],
        "example_yaml": """- archetype: takeaway_columns
  title: "Executive Summary: Storefront Speed, Payment Mix, and Cloud Sync"
  columns:
    - title: "Checkout Speed"
      badge: "01"
      points:
        - "**Sub-2s scans** cut peak queue times by 34% across flagship lanes."
""",
    },
    "tiered_priority_ladder": {
        "family": "Tables",
        "aliases": ["grouped_action_list"],
        "purpose": "BCG-style asymmetric 2-column action ladder pairing grouped left tier blocks with numbered circular action items.",
        "keys": [
            "title (str): Action title",
            "tiers (list): [{label, accent_color, items: [str|{index, text}]}]",
            "left_header (str, optional): Left column header (default 'Priority')",
            "right_header (str, optional): Right column header (default 'Recommendation')",
            "tracker, subtitle, footnote (opt-in)",
        ],
        "example_yaml": """- archetype: tiered_priority_ladder
  title: "Seven Sequenced Actions Modernize Store POS Operations"
  tiers:
    - label: "Foundation"
      items:
        - "Deploy local SQLite offline transaction journal on all lane terminals"
""",
    },
    "bubble_matrix": {
        "family": "Tables",
        "aliases": ["proportional_dot_matrix"],
        "purpose": "BCG proportional bubble matrix plotting data-scaled circles across entities and metrics with optional qualitative delta rows.",
        "keys": [
            "title (str): Action title",
            "entities (list of str): Column entity headers",
            "rows (list of dicts): [{label, type: 'bubble'|'text', unit, accent_color, values: [...]}]",
            "tracker, subtitle, footnote (opt-in)",
        ],
        "example_yaml": """- archetype: bubble_matrix
  title: "Checkout Latency Pressure Peaks in High-Volume Mall Formats"
  entities: ["Flagship", "Metro Mall", "Suburban", "Express"]
  rows:
    - label: "Peak Wait (sec)"
      type: "bubble"
      unit: "s"
      values: [42, 58, 24, 18]
""",
    },
    "ranked_bar_scorecard": {
        "family": "Tables",
        "aliases": ["ranked_bars"],
        "purpose": "Distilled horizontal ranked bar scorecard with clean trend delta glyphs (UP/DOWN/FLAT/N/A) and zero chart clutter.",
        "keys": [
            "title (str): Action title",
            "panels (list of dicts): [{title, unit, accent_color, bars: [{label, value, delta, highlight}]}]",
            "callout (str, opt-in): Bottom takeaway banner",
            "tracker, subtitle, footnote (opt-in)",
        ],
        "example_yaml": """- archetype: ranked_bar_scorecard
  title: "QRIS and Card-Present Contactless Drive 78% of Store Tender"
  panels:
    - title: "Tender Share (%)"
      unit: "%"
      bars:
        - label: "QRIS / E-Wallet"
          value: 44
          delta: "UP"
          highlight: true
""",
    },
    "horizon_maturity_matrix": {
        "family": "Strategy",
        "aliases": ["maturity_matrix"],
        "purpose": "2D capability x time-horizon matrix with left-edge semantic maturity color stripes and top-right maturity legend.",
        "keys": [
            "title (str): Action title",
            "horizons (list of dicts): [{title, subtitle}]",
            "capabilities (list of dicts): [{name, subtitle, cells: [{text, maturity: 'low'|'medium'|'high'}]}]",
            "maturity_legend (list, optional): [{label, color}]",
            "tracker, subtitle, footnote (opt-in)",
        ],
        "example_yaml": """- archetype: horizon_maturity_matrix
  title: "POS Capabilities Scale from Local Resilience to Autonomous Replenishment"
  horizons:
    - title: "Near term"
      subtitle: "0-6 months"
  capabilities:
    - name: "Checkout"
      cells:
        - text: "**Offline queue** protects card-present sales during WAN drops."
          maturity: "low"
""",
    },
    "comparative_forecast_columns": {
        "family": "Strategy",
        "aliases": ["tri_metric_trajectory"],
        "purpose": "3-column entity trend trajectory with native vector slope lines, analytical narrative, and bottom KPI/lead-time callouts.",
        "keys": [
            "title (str): Action title",
            "columns (list of dicts): [{title, badge, accent_color, points: [{label, value, highlight}], analysis, kpi_label, kpi_value}]",
            "tracker, subtitle, footnote (opt-in)",
        ],
        "example_yaml": """- archetype: comparative_forecast_columns
  title: "Transaction Volume Growth Demands Edge Caching by 2028"
  columns:
    - title: "Store POS"
      badge: "POS"
      points:
        - {label: "2024", value: 120}
        - {label: "2028", value: 310, highlight: true}
      analysis: "**2.6x surge** in peak-hour SKU scans."
      kpi_label: "Rollout lead time:"
      kpi_value: "3 - 6 mos"
""",
    },

    # -------------------------------------------------------------------------
    # 4. Processes & Roadmaps
    # -------------------------------------------------------------------------
    "chevron_process": {
        "family": "Processes",
        "aliases": ["process_flow", "value_chain"],
        "purpose": "Linear chevron stage-gate workflow showing end-to-end phases, optional statuses/deliverables, and opt-in customizable current-stage pin.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title asserting roadmap certainty",
            "subtitle (str, opt-in): Contextual narrative subtitle",
            "steps (list): Step definitions: [{num, title, status (optional), deliverables: [str], owner, is_current (bool, opt-in), pin_label (str), pin_color (str)}]",
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
""",
    },
    "waterfall_bridge": {
        "family": "Strategy",
        "aliases": ["waterfall", "bridge_chart", "variance_bridge"],
        "purpose": "Sequential waterfall bridge showing how a baseline metric transitions through positive and negative drivers to a target total (cost bridges, latency SLA budgets, capacity reconciliations).",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action headline expressing the net bridge conclusion",
            "subtitle (str, opt-in): Contextual narrative subtitle",
            "steps (list): Bridge steps: [{label, value, kind: 'start'|'delta'|'subtotal'|'end', display, sublabel, color}]",
            "value_prefix / value_suffix / unit (str, optional): Numeric formatting tokens (e.g. '$', 'ms', 'M')",
            "positive_is_good (bool, optional): True for revenue/savings (+ is green), False for cost/latency (- is green)",
            "show_connectors (bool, optional): Draw hairline bridge connectors between steps (default: true)",
            "right_panel (dict, optional): Compact driver summary card: {title, bullets: [...]}",
            "takeaway (str|dict, opt-in): Bottom bar ONLY for a distinct decision gate or capital lever",
            "footnote (str, opt-in): Source or methodology note",
        ],
        "example_yaml": """- archetype: waterfall_bridge
  tracker: "FINOPS | INFRASTRUCTURE COST BRIDGE"
  title: "Compute Rightsizing and Tiered Storage Cut Annual Run-Rate by $1.8M"
  subtitle: "Annualized cloud platform spend bridge from FY24 baseline to FY25 target architecture."
  value_prefix: "$"
  value_suffix: "M"
  positive_is_good: false
  steps:
    - label: "FY24 Baseline"
      value: 6.4
      kind: "start"
    - label: "Traffic Growth"
      value: 0.9
      kind: "delta"
    - label: "Spot & Rightsizing"
      value: -1.6
      kind: "delta"
    - label: "Cold Tiering"
      value: -0.7
      kind: "delta"
    - label: "Cache Offload"
      value: -0.4
      kind: "delta"
    - label: "FY25 Target"
      value: 4.6
      kind: "end"
  right_panel:
    title: "Primary Optimization Levers"
    bullets:
      - "**Compute Rightsizing:** Idle cluster autoscaling eliminates 34% peak over-provisioning."
      - "**Storage Tiering:** Lifecycle policies move >90-day logs to cold object storage."
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
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
      tables: ["RAW_TRANSACTION_LOGS", "CDC_BILLING_EVENT", "RAW_EVENT_LOG"]
      excluded_note: "Direct ML training strictly prohibited to prevent data leakage."
    - tier: "SILVER TIER (CONSOLIDATED)"
      tier_badge: "CERTIFIED"
      metric: "12 Tables"
      metric_label: "FEATURE STAGING"
      description: "Deduplicated, type-cast, and joined via validated primary keys."
      tables: ["FCT_ORDER_SUMMARY", "DIM_ACCOUNT_ATTRIBUTES", "STG_EVENT_OUTCOMES"]
      excluded_note: "Primary foundation for Cortex model feature store."
    - tier: "GOLD TIER (AGGREGATED)"
      tier_badge: "GOVERNED"
      metric: "5 Tables"
      metric_label: "BI SERVING"
      description: "Executive dashboards and regulatory financial compliance marts."
      tables: ["DM_MONTHLY_EXECUTIVE_KPI", "RPT_CLINIC_PERFORMANCE"]
      excluded_note: "Post-hoc aggregates only; not used for real-time inference."
""",
    },
    "gate_validation": {
        "family": "Architecture",
        "aliases": ["threshold_bars", "coverage_gate_validation", "metric_gate_review"],
        "purpose": "Multi-tier threshold progress bar charts comparing actual telemetry against required compliance/accuracy stage-gates.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title stating gate passage status",
            "subtitle (str, opt-in): Contextual narrative subtitle",
            "kpis (list, opt-in): 1-6 summary KPI tiles (collapses cleanly when omitted)",
            "gates (list): Metric gates: [{title, actual (float), threshold (float), status ('PASS'|'WARNING'|'CRITICAL'), category, variance_label, is_hero}]",
            "constraints_card (dict, opt-in): Right-hand observations/warnings card",
            "takeaway (str, opt-in): Bottom conclusion banner",
            "show_top_stripes (bool, default false): Opt-in accent stripes",
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
""",
    },
    "process_with_cards": {
        "family": "Processes",
        "aliases": ["flow_with_cards", "process_cards"],
        "purpose": "Top-to-bottom split pairing a horizontal connected process/decision flow (with optional Yes/No branch and owner sub-labels) on top with a structured 2-3 card explanation strip below.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title asserting workflow or operational impact",
            "subtitle (str, opt-in): Contextual subtitle",
            "steps (list): Linear horizontal nodes: [{step_num|num, title, owner, accent_key, is_current}]",
            "branch (dict, opt-in): Optional decision gate + Yes/No fork: {question, owner, accent_key, yes: {label, title, accent_key}, no: {label, title, accent_key}}",
            "caption (str, opt-in): Muted operational caveat directly below the flow diagram",
            "cards (list): Bottom cards: [{title, description|bullets, number, is_focal, accent_key}]",
            "columns (int, default 3): Number of columns in bottom card strip",
            "show_numbers (bool, default false): Render circular numbered indices on bottom cards",
            "split (list, default [38, 62]): Vertical height split between flow and card strip",
            "takeaway / footnote (opt-in)",
        ],
        "example_yaml": """- archetype: process_with_cards
  tracker: "1 BUSINESS UNDERSTANDING"
  title: "Prioritized Outreach Concentrates Daily Capacity on Highest-Risk Renewals"
  steps:
    - step_num: "01"
      title: "Active renewal queue"
      owner: "CRM Snapshot"
    - step_num: "02"
      title: "Model scores risk"
      is_current: true
      owner: "Batch Pipeline"
    - step_num: "03"
      title: "Call riskiest third"
      owner: "Account Managers"
  branch:
    question: "Account saved?"
    yes:
      label: "Yes"
      title: "Renewal locked"
    no:
      label: "No"
      title: "Escalate retention offer"
  cards:
    - title: "Capacity constraint"
      is_focal: true
      description: "**Limited outreach hours:** Team can contact only 33% of open renewals each week."
    - title: "Multi-signal scoring"
      description: "**Combined indicators:** Usage drop, support backlog, and billing cadence jointly predict churn."
    - title: "Low false-positive cost"
      description: "**Human-in-the-loop:** Score only changes call order; reps still verify account context."
""",
    },
    "cohort_funnel": {
        "family": "Architecture",
        "aliases": ["attrition_funnel", "data_funnel"],
        "purpose": "Data preparation cohort attrition funnel showing ordered horizontal exclusion bars from source records to final modeling cohort alongside unit/target definition cards and a segmented Train/Validation/Test temporal split bar.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title stating cohort scope and grain",
            "subtitle (str, opt-in): Contextual subtitle",
            "source_count (int|float|str): Starting raw record count",
            "source_label (str): Description of starting table/population",
            "exclusions_caption (str, opt-in): Counting rule caption above exclusion bars",
            "exclusions (list): Ordered exclusions: [{label, count, pct, accent_key}]",
            "final_count (int|float|str): Surviving cohort count",
            "final_label (str): Description of final modeling unit",
            "definition_cards (list): Right-hand stacked cards (1-3): [{title, description|bullets, accent_key}]",
            "split_segments (list, opt-in): Bottom split bar segments: [{label, count|value, display, accent_key|color}]",
            "split_caption (str, opt-in): Date window / holdout policy note under the split bar",
            "takeaway / footnote (opt-in)",
        ],
        "example_yaml": """- archetype: cohort_funnel
  tracker: "2 DATA UNDERSTANDING | 3 DATA PREPARATION"
  title: "Ordered Exclusions Distill 240,000 Raw Events into 48,500 Eligible Account-Days"
  source_count: 240000
  source_label: "raw subscription event records"
  exclusions_caption: "Records removed, counted under the first exclusion rule that applies"
  exclusions:
    - label: "Outside active observation window"
      count: 82400
    - label: "Same-day self-serve renewals"
      count: 54100
    - label: "Missing primary account identifier"
      count: 31200
    - label: "Duplicate account-date snapshots"
      count: 23800
  final_count: 48500
  final_label: "account-days in modeling cohort"
  definition_cards:
    - title: "Unit: account and cutoff day"
      description: "**One row per active account:** Snapshot frozen at midnight before outreach scheduling."
      accent_key: "accent"
    - title: "Target label definition"
      description: "**Non-renewal within 30 days:** Accounts with no signed renewal or billing activity; recent rows stay unknown."
      accent_key: "warning"
  split_segments:
    - label: "Train"
      count: 27160
      accent_key: "primary"
    - label: "Validation"
      count: 8730
      accent_key: "accent"
    - label: "Test"
      count: 12610
      accent_key: "warning"
  split_caption: "48,500 rows split strictly by date; test holdout evaluated once after final model freeze."
""",
    },
    "ml_benchmark": {
        "family": "Architecture",
        "aliases": ["model_benchmark", "lift_benchmark"],
        "purpose": "Composite ML evaluation slide pairing a multi-cutoff lift/capture grouped column chart (left) with a compact benchmark summary table (top-right) and focal hero lift ratio vs. pass-gate KPI card (bottom-right).",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title stating audited lift or capture result",
            "subtitle (str, opt-in): Contextual subtitle",
            "chart (dict): Left native_chart config: {title, subtitle, chart_type, categories, series: [{name, values, color}], number_format}",
            "benchmark_table (dict): Top-right table config: {columns|headers, rows, highlight_row}",
            "hero_kpi (dict): Bottom-right hero_kpi config: {eyebrow, stat, stat_label, stat_subtext, card_style}",
            "split (list, default [62, 38]): Horizontal split between chart and right stack",
            "right_split (list, default [52, 48]): Vertical split between table and hero KPI",
            "footnote / takeaway (opt-in)",
        ],
        "example_yaml": """- archetype: ml_benchmark
  tracker: "4 MODELING | 5 EVALUATION"
  title: "Model Captures 68% of At-Risk Renewals in the Top Third, 1.5x the Best Rule"
  chart:
    title: "At-Risk Renewal Capture by Call-List Size (%)"
    chart_type: "column"
    categories: ["Top 10%", "Top 20%", "Top 33%"]
    number_format: "0'%'"
    series:
      - name: "Random order"
        values: [10, 20, 33]
        color: "#CBD5E1"
      - name: "Best simple rule"
        values: [19, 30, 44]
        color: "#64748B"
      - name: "ML model"
        values: [38, 53, 68]
        color: "accent"
  benchmark_table:
    columns:
      - {header: "Method (Top 33%)", width: 52, align: "LEFT"}
      - {header: "Found", width: 24, align: "RIGHT"}
      - {header: "Hits/100", width: 24, align: "RIGHT"}
    highlight_row: "last"
    rows:
      - ["Random order", "465", "11"]
      - ["Best simple rule", "620", "15"]
      - ["ML model", "958", "23"]
  hero_kpi:
    eyebrow: "LIFT VS. BEST SIMPLE RULE"
    stat: "1.54x"
    stat_label: "Capture Advantage at Top 33%"
    stat_subtext: "90% CI: 1.48x to 1.60x | Pass Gate: >= 1.25x (PASSED)"
    card_style: "filled"
  footnote: "Out-of-time test window (N = 12,610 account-days), evaluated once after final fit."
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
            "takeaway (str|dict, opt-in): Omit by default; bottom bar ONLY for a distinct decision gate or capital lever",
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
""",
    },
    "browser_mockup": {
        "family": "Architecture",
        "aliases": ["window_mockup", "app_mockup", "app_walkthrough", "module_walkthrough"],
        "purpose": "High-DPI macOS window viewport framing live enterprise web app screenshots, dashboards, or Streamlit UIs.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title describing UI workflow",
            "subtitle (str, opt-in): Contextual narrative subtitle",
            "image_path (str): Relative path to high-resolution UI screenshot",
            "mockup_url (str, optional): Simulated browser address bar URL",
            "window_title (str, optional): Window title bar caption",
            "badge (str, optional): Status pill on top-right of frame",
            "takeaways (list, opt-in): 1-5 right-side observation cards (mockup widens cleanly when omitted)",
            "takeaways_title (str, opt-in): Optional dark header bar title above takeaways",
            "align (str, optional): Alignment for single-card takeaway ('left'|'center')",
        ],
        "example_yaml": """- archetype: browser_mockup
  tracker: "EMR COPILOT INTEGRATION | CLINICAL WORKFLOW"
  title: "Native Streamlit Copilot Embeds Directly into Existing EMR Workspace"
  subtitle: "Clinicians receive real-time predictive probabilities without leaving their consultation screen."
  image_path: "assets/images/mockups/magic_emr_cortex_copilot.png"
  mockup_url: "https://app.enterprise.internal/portal/summary"
  window_title: "Enterprise Clinical Workspace — Analytics Assistant"
  badge: "LIVE PROTOTYPE"
""",
    },
    "iceberg_concept": {
        "family": "Architecture",
        "aliases": ["iceberg"],
        "purpose": "Surface vs Subsurface visualization contrasting visible business metrics with hidden foundational architecture requirements.",
        "keys": [
            "tracker (str, opt-in): Category eyebrow tag",
            "title (str): Action title",
            "subtitle (str, opt-in): Contextual subtitle",
            "visible_items (list of str): Visible top-level items above waterline",
            "subsurface_items (list of str): Deep foundational architecture requirements below waterline",
            "takeaways (list, opt-in): Optional right-side panel items (iceberg expands full width when omitted)",
        ],
        "example_yaml": """- archetype: iceberg_concept
  tracker: "TECHNICAL FOUNDATION | ICEBERG FRAMEWORK"
  title: "Predictive Analytics Relies on a Heavy Subsurface Governance Foundation"
  subtitle: "The visible UI assistant is enabled by extensive lakehouse data modeling, masking, and CDC pipelines."
  visible_items:
    - "Streamlit Enterprise Copilot UI"
    - "Real-Time Predictive Analytics"
    - "Executive BI Dashboard Metrics"
  subsurface_items:
    - "Dynamic Table Staging & Deterministic Join Keys"
    - "Snowpipe Micro-Batch CDC Ingestion"
    - "Role-Based Access Control & Column Masking"
    - "Automated Feature Drift & Model Lineage Tracking"
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
