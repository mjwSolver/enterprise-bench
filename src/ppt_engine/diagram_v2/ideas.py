"""
Diagram Engine V2 - Layout Ideas, Canonical Patterns & ASCII Wireframing
========================================================================
Engineering Signature: [MJW/AGY]
Provides proven enterprise consulting layout archetypes, non-blocking
ASCII wireframe rendering, and starter YAML scaffolding.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from src.ppt_engine.diagram_v2.models import DiagramSpec, ContainerSpec, NodeSpec, FlowSpec


CANONICAL_PATTERNS: Dict[str, Dict[str, Any]] = {
    "3-swimlane": {
        "id": "3-swimlane",
        "name": "3-Swimlane Modernization Flow",
        "description": "Canonical 3-column architecture (Source/Ingress -> Platform Core -> Target Lakehouse). Best for standard platform migration overviews.",
        "recommended_nodes": "6 to 9 nodes (2 to 3 per lane)",
        "ascii_wireframe": """\
┌─ Ingress (AWS / Source) ──┐  ┌─ Migration / Core ────────┐  ┌─ Target Lakehouse ────────┐
│ ┌──────────────────────┐  │  │ ┌──────────────────────┐  │  │ ┌──────────────────────┐  │
│ │ App / Client Feeds   │  │──┼─►│ Databricks Engine    │──┼─►│ Delta Lake / Catalog   │  │
│ └──────────────────────┘  │  │ └──────────────────────┘  │  │ └──────────────────────┘  │
│ ┌──────────────────────┐  │  │ ┌──────────────────────┐  │  │ ┌──────────────────────┐  │
│ │ Kafka / Event Stream │  │──┼─►│ Spark Pipelines     │──┼─►│ Serving Endpoints      │  │
│ └──────────────────────┘  │  │ └──────────────────────┘  │  │ └──────────────────────┘  │
└───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘""",
        "yaml_template": """\
id: swimlane_modernization
name: "Modernization Architecture Flow"
theme: metrodata
canvas:
  w: 13.333
  h: 7.500
header:
  action_title: "Target Platform Modernization Flow"
  subtitle: "End-to-end telemetry and batch feeds routed through managed Lakehouse pipelines"
containers:
  - id: c_ingress
    label: "Ingress (AWS / Source)"
    x: 0.80
    y: 1.50
    w: 3.60
    h: 5.20
    role: boundary
  - id: c_core
    label: "Migration & Processing Core"
    x: 4.80
    y: 1.50
    w: 3.60
    h: 5.20
    role: active
  - id: c_target
    label: "Target Lakehouse Platform"
    x: 8.80
    y: 1.50
    w: 3.70
    h: 5.20
    role: target
nodes:
  - id: n_app
    container_id: c_ingress
    title: "App Client Feeds"
    subtitle: "High-throughput REST/gRPC events"
    x: 1.10
    y: 2.20
    w: 3.00
    h: 1.20
  - id: n_stream
    container_id: c_ingress
    title: "Kafka Event Stream"
    subtitle: "Decoupled real-time ingest"
    x: 1.10
    y: 3.90
    w: 3.00
    h: 1.20
  - id: n_engine
    container_id: c_core
    title: "Databricks Engine"
    subtitle: "Distributed Lakeflow runtimes"
    x: 5.10
    y: 2.20
    w: 3.00
    h: 1.20
  - id: n_pipeline
    container_id: c_core
    title: "Spark Pipelines"
    subtitle: "Declarative Auto CDC & curation"
    x: 5.10
    y: 3.90
    w: 3.00
    h: 1.20
  - id: n_catalog
    container_id: c_target
    title: "Delta Lake & Catalog"
    subtitle: "Unified Unity Catalog governance"
    x: 9.10
    y: 2.20
    w: 3.10
    h: 1.20
  - id: n_serving
    container_id: c_target
    title: "Serving Endpoints"
    subtitle: "Real-time SQL and model APIs"
    x: 9.10
    y: 3.90
    w: 3.10
    h: 1.20
flows:
  - source: n_app
    target: n_engine
    label: "REST Ingress"
  - source: n_stream
    target: n_pipeline
    label: "Micro-batch"
  - source: n_engine
    target: n_catalog
    label: "ACID Write"
  - source: n_pipeline
    target: n_serving
    label: "Live Serving"
""",
    },
    "interwoven-hub": {
        "id": "interwoven-hub",
        "name": "Interwoven Dual-Tier Topology",
        "description": "Unified Client Ingress origin on left, branching into dual Legacy CDSW and Target Databricks tiers with vertical synchronization bridges.",
        "recommended_nodes": "7 to 10 nodes (compressed databases <= 170px)",
        "ascii_wireframe": """\
┌─ Client Ingress ─────────┐  ┌─ Target Modern Stack ──────────────────────────────────────┐
│ ┌──────────────────────┐ │  │ ┌──────────────────────┐     ┌───────────────────────────┐ │
│ │ Unified Apps Feeds   │─┼──┼►│ Databricks Core      │────►│ Unity Catalog Gold Tier   │ │
│ └──────────────────────┘ │  │ └──────────┬───────────┘     └───────────────────────────┘ │
└──────────────────────────┘  │            │ (Modernization Bridge)                        │
                              │            ▼                                               │
                              │ ┌──────────────────────┐     ┌───────────────────────────┐ │
                              │ │ Legacy HDFS Cluster  │────►│ Cloudera CDSW Engine      │ │
                              │ └──────────────────────┘     └───────────────────────────┘ │
                              └─ Legacy Workload Tier ─────────────────────────────────────┘""",
        "yaml_template": """\
id: interwoven_topology
name: "Interwoven Migration Topology"
theme: metrodata
canvas:
  w: 13.333
  h: 7.500
header:
  action_title: "Interwoven Dual-Tier Platform Architecture"
  subtitle: "Coexistence and phased cutover topology with live synchronization bridge"
containers:
  - id: c_client
    label: "Client Ingress"
    x: 0.80
    y: 1.50
    w: 3.20
    h: 5.20
    role: boundary
  - id: c_modern
    label: "Target Modern Stack"
    x: 4.40
    y: 1.50
    w: 8.10
    h: 2.40
    role: target
  - id: c_legacy
    label: "Legacy Workload Tier"
    x: 4.40
    y: 4.30
    w: 8.10
    h: 2.40
    role: bottleneck
nodes:
  - id: n_apps
    container_id: c_client
    title: "Client Application Origin"
    subtitle: "Shared multi-system source feeds"
    x: 1.00
    y: 2.80
    w: 2.80
    h: 1.60
  - id: n_target_core
    container_id: c_modern
    title: "Databricks Lakehouse"
    subtitle: "Serverless compute runtime"
    x: 4.80
    y: 2.00
    w: 3.20
    h: 1.40
  - id: n_gold
    container_id: c_modern
    title: "Unity Catalog Gold Tier"
    subtitle: "Governed analytics models"
    x: 8.80
    y: 2.00
    w: 3.20
    h: 1.40
  - id: n_legacy_core
    container_id: c_legacy
    title: "Legacy HDFS Storage"
    subtitle: "On-premise HDFS data lake"
    x: 4.80
    y: 4.80
    w: 3.20
    h: 1.40
  - id: n_cdsw
    container_id: c_legacy
    title: "Cloudera CDSW Engine"
    subtitle: "Legacy batch analytics jobs"
    x: 8.80
    y: 4.80
    w: 3.20
    h: 1.40
flows:
  - source: n_apps
    target: n_target_core
    label: "Modern Route"
  - source: n_apps
    target: n_legacy_core
    label: "Legacy Route"
  - source: n_target_core
    target: n_gold
    label: "Curated"
  - source: n_target_core
    target: n_legacy_core
    label: "Sync Bridge"
  - source: n_legacy_core
    target: n_cdsw
    label: "Impala / Hive"
""",
    },
    "data-pipeline": {
        "id": "data-pipeline",
        "name": "End-to-End Data Pipeline Hub",
        "description": "Chronological ingestion, transformation, and distribution pipeline with clear stage boundaries.",
        "recommended_nodes": "4 to 8 nodes",
        "ascii_wireframe": """\
┌─ 1. Ingestion ───────────┐  ┌─ 2. Transformation ───────┐  ┌─ 3. Delivery / BI ─────────┐
│ [ RDBMS / CDC Streams  ] │─►│ [ Spark Declarative Lake] │─►│ [ Lakeview Dashboards    ] │
│ [ REST API Feeds       ] │  │ [ Auto CDC Cleansing    ] │  │ [ Model Serving APIs     ] │
└──────────────────────────┘  └───────────────────────────┘  └────────────────────────────┘""",
        "yaml_template": "",  # Populated on demand
    },
    "runbook-grid": {
        "id": "runbook-grid",
        "name": "Phased Workstream Runbook Grid",
        "description": "Multi-phase implementation matrix (Assess -> Build -> Validate -> Cutover). Allows dense typography with explicit bypass.",
        "recommended_nodes": "8 to 16 nodes in 4 columns",
        "ascii_wireframe": """\
┌─ Phase 1: Assess ─────────┐ ┌─ Phase 2: Build ──────────┐ ┌─ Phase 3: Cutover ────────┐
│ • Discovery Audit (K1)   │ │ • Lakehouse Setup (W1)    │ │ • UAT Validation Gate       │
│ • Sizing & Costs (K2)     │ │ • Pipeline AST Rewrites   │ │ • Parallel Shadow Run       │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘""",
        "yaml_template": "",
    },
}


def list_idea_patterns() -> List[Dict[str, Any]]:
    """Returns metadata for all registered canonical layout patterns."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "recommended_nodes": p["recommended_nodes"],
        }
        for p in CANONICAL_PATTERNS.values()
    ]


def get_pattern(pattern_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves pattern dictionary by identifier or alias."""
    pid = pattern_id.lower().strip()
    if pid in CANONICAL_PATTERNS:
        return CANONICAL_PATTERNS[pid]
    for key, p in CANONICAL_PATTERNS.items():
        if pid in key or pid in p["name"].lower():
            return p
    return None


def render_ascii_wireframe(spec: Union[DiagramSpec, Dict[str, Any]]) -> str:
    """
    Renders a crisp, human-readable ASCII layout wireframe representing
    containers, node pills, and connector flows directly from a diagram spec.
    """
    if isinstance(spec, dict):
        try:
            spec = DiagramSpec.model_validate(spec)
        except Exception:
            return _render_fallback_ascii(spec)

    lines: List[str] = []
    lines.append(f"┌─────────────────────────────────────────────────────────────────────────────┐")
    title_val = getattr(spec.header, "action_title", None) or getattr(spec, "name", "Architecture Diagram")
    title_str = str(title_val)[:73]
    lines.append(f"│ 🎯 {title_str:<72} │")
    subtitle_val = getattr(spec.header, "subtitle", None) or getattr(spec.header, "action_subtitle", None)
    if subtitle_val:
        sub_str = str(subtitle_val)[:73]
        lines.append(f"│    {sub_str:<72} │")
    lines.append(f"├─────────────────────────────────────────────────────────────────────────────┤")

    # Group nodes by container
    nodes_by_container: Dict[str, List[NodeSpec]] = {}
    orphan_nodes: List[NodeSpec] = []
    for n in spec.nodes:
        cid = getattr(n, "container_id", None)
        if cid:
            nodes_by_container.setdefault(cid, []).append(n)
        else:
            orphan_nodes.append(n)

    # Render containers
    if spec.containers:
        for c in spec.containers:
            c_nodes = nodes_by_container.get(c.id, [])
            role_badge = f"[{c.role.upper()}] " if c.role else ""
            c_label = f"Zone: {role_badge}{c.label}"[:69]
            lines.append(f"│  ┌─ {c_label:<67} ┐  │")
            
            if not c_nodes:
                lines.append(f"│  │  (Empty Container)                                                   │  │")
            else:
                for n in c_nodes:
                    clean_title = (n.title or "").replace("\n", " ").replace("\r", "").strip()[:30]
                    clean_sub = (n.subtitle or "").replace("\n", " ").replace("\r", "").strip()[:28] if n.subtitle else ""
                    sub_str = f" : {clean_sub}" if clean_sub else ""
                    pill = f"[{clean_title}{sub_str}]"[:63]
                    lines.append(f"│  │  • {pill:<65} │  │")

            lines.append(f"│  └───────────────────────────────────────────────────────────────────┘  │")
    elif orphan_nodes:
        for n in orphan_nodes:
            node_title = n.title[:35]
            sub_str = f" : {n.subtitle[:30]}" if n.subtitle else ""
            lines.append(f"│  • [{node_title}{sub_str}]                                              │")

    # Render flows summary
    if spec.flows:
        lines.append(f"├─────────────────────────────────────────────────────────────────────────────┤")
        lines.append(f"│ 🔀 Active Flows:                                                            │")
        for f in spec.flows[:6]:
            lbl = f" --({f.label})--> " if f.label else " ----> "
            flow_str = f"{f.source}{lbl}{f.target}"[:71]
            lines.append(f"│    {flow_str:<72} │")
        if len(spec.flows) > 6:
            lines.append(f"│    ... and {len(spec.flows) - 6} more flows                                               │")

    lines.append(f"└─────────────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)


def _render_fallback_ascii(raw_dict: Dict[str, Any]) -> str:
    """Fallback ASCII formatter for raw dictionaries that do not cleanly validate."""
    containers = raw_dict.get("containers", [])
    nodes = raw_dict.get("nodes", [])
    flows = raw_dict.get("flows") or raw_dict.get("connectors", [])

    lines = [
        "┌─── Rough Draft Wireframe ────────────────────────────────────────┐",
    ]
    for c in containers:
        c_label = c.get("label", c.get("id", "Zone"))[:55]
        lines.append(f"│ ┌─ Zone: {c_label:<53} ┐ │")
        cid = c.get("id")
        c_nodes = [n for n in nodes if n.get("container_id") == cid]
        for n in c_nodes:
            ntitle = n.get("title", n.get("id", "Card"))[:50]
            lines.append(f"│ │  • [{ntitle:<50}] │ │")
        lines.append(f"│ └──────────────────────────────────────────────────────────┘ │")

    if flows:
        lines.append("│ ── Active Connections ────────────────────────────────────────────── │")
        for f in flows[:4]:
            s = f.get("source", "?")
            t = f.get("target", "?")
            lbl = f.get("label", "")
            arrow = f" --({lbl})--> " if lbl else " --> "
            lines.append(f"│   {s}{arrow}{t}")

    lines.append("└────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
