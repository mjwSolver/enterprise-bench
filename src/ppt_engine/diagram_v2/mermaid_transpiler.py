"""
Diagram Engine V2 - Mermaid-to-YAML AST Transpiler
===================================================
Transpiles Mermaid flowchart syntax into audit-compliant declarative
DiagramSpec instances and clean YAML specifications using the 2D constraint
auto-layout solver.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from src.ppt_engine.archetypes.common import find_emojis
from src.ppt_engine.diagram_engine import MermaidParser, ParsedDiagram
from src.ppt_engine.diagram_v2.models import (
    CanvasConfig,
    ContainerSpec,
    DiagramSpec,
    FlowSpec,
    HeaderConfig,
    NodeSpec,
)

_EMOJI_STRIP_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def _clean_text(raw: Optional[str]) -> str:
    """Strip HTML breaks, surrounding quotes, and any Unicode emojis."""
    if not raw:
        return ""
    text = str(raw).strip()
    if len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
        text = text[1:-1].strip()
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = _EMOJI_STRIP_RE.sub("", text)
    # Remove any residual emojis detected by canonical helper
    for em in find_emojis(text):
        text = text.replace(em, "")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _infer_node_shape_and_role(
    mermaid_shape: str,
    title: str,
    subtitle: Optional[str],
    node_id: str,
) -> Tuple[str, Optional[str]]:
    """Map Mermaid node shape and semantic keywords to V2 shape + diagnostic role."""
    combined = f"{node_id} {title} {subtitle or ''}".lower()
    mshape = (mermaid_shape or "rect").lower()

    # Shape mapping
    if mshape == "cylinder":
        v2_shape = "cylinder"
    elif mshape == "circle":
        v2_shape = "circle"
    elif mshape in ("rounded", "stadium"):
        v2_shape = "rounded"
    elif mshape in ("rhombus", "hexagon"):
        v2_shape = "rounded"
    else:
        v2_shape = "rect"

    # Role inference
    role: Optional[str] = None
    if v2_shape == "cylinder" or any(
        kw in combined
        for kw in ("db", "sql", "postgres", "mysql", "dynamo", "snowflake", "delta", "s3", "lake", "warehouse", "redis", "mongo", "store")
    ):
        role = "database"
        if any(kw in combined for kw in ("db", "database", "postgres", "mysql", "dynamo", "redis", "mongo", "warehouse")):
            v2_shape = "cylinder"
    elif any(kw in combined for kw in ("legacy", "defect", "error", "dead", "dlq", "bottleneck", "fail")):
        role = "defect"
    elif any(kw in combined for kw in ("target", "prod", "reconciled", "gold", "serving", "dashboard", "success")):
        role = "target"
    elif mshape in ("rhombus", "hexagon") or any(
        kw in combined for kw in ("gateway", "router", "waf", "dns", "lb", "orchestrat", "airflow", "step", "broker")
    ):
        role = "gateway"
    elif any(kw in combined for kw in ("lambda", "spark", "kafka", "flink", "worker", "compute", "ecs", "k8s", "api", "service")):
        role = "active"

    return v2_shape, role


def transpile_mermaid_to_spec(
    mermaid_code: str,
    diagram_id: str = "mermaid_diagram",
    name: Optional[str] = None,
    theme: str = "metrodata",
) -> DiagramSpec:
    """
    Parse Mermaid flowchart syntax into a validated, auto-laid-out DiagramSpec.
    """
    if not mermaid_code or not str(mermaid_code).strip():
        raise ValueError("Mermaid input is empty; provide a valid Mermaid flowchart with at least one node.")

    parser = MermaidParser()
    parsed: ParsedDiagram = parser.parse(mermaid_code)
    if not parsed.nodes and not parsed.subgraphs:
        raise ValueError(
            "Parsed Mermaid graph contains no nodes or subgraphs; provide a valid Mermaid flowchart."
        )

    direction = (parsed.direction or "LR").upper()
    is_horizontal = direction in ("LR", "RL")
    top_layout = "horizontal" if is_horizontal else "vertical"
    child_layout = "vertical" if is_horizontal else "horizontal"

    containers: List[ContainerSpec] = []
    for sg_id, sg in parsed.subgraphs.items():
        clean_label = _clean_text(sg.title) or sg_id.replace("_", " ").upper()
        containers.append(
            ContainerSpec(
                id=sg_id,
                label=clean_label.upper(),
                layout=child_layout,
                gap=0.25,
                padding=0.22,
                border_hex="#94A3B8",
                fill_hex="#F8FAFC",
                dashed=True,
                align="center",
                vertical_align="top",
            )
        )

    nodes: List[NodeSpec] = []
    node_roles: Dict[str, Optional[str]] = {}
    for nid, dnode in parsed.nodes.items():
        cleaned = _clean_text(dnode.label or nid)
        lines = [ln for ln in cleaned.splitlines() if ln]
        title = lines[0] if lines else nid
        subtitle: Optional[str] = None
        bullets: Optional[List[str]] = None
        if len(lines) == 2:
            subtitle = lines[1]
        elif len(lines) > 2:
            subtitle = lines[1]
            bullets = lines[2:]

        v2_shape, role = _infer_node_shape_and_role(dnode.shape, title, subtitle, nid)
        node_roles[nid] = role

        nodes.append(
            NodeSpec(
                id=nid,
                container_id=dnode.subgraph_id if dnode.subgraph_id in parsed.subgraphs else None,
                title=title,
                subtitle=subtitle,
                bullets=bullets,
                shape=v2_shape,
                role=role,
            )
        )

    flows: List[FlowSpec] = []
    for idx, edge in enumerate(parsed.edges):
        clean_lbl = _clean_text(edge.label) or None
        is_dashed = edge.style_type == "dashed"
        src_role = node_roles.get(edge.source_id)
        tgt_role = node_roles.get(edge.target_id)

        flow_role: Optional[str] = None
        stroke_hex = "#0284C7"
        if tgt_role == "target":
            flow_role = "target"
            stroke_hex = "#16A34A"
        elif src_role == "defect" or tgt_role == "defect":
            flow_role = "defect"
            stroke_hex = "#DC2626"

        flows.append(
            FlowSpec(
                id=f"flow_{idx + 1}_{edge.source_id}_{edge.target_id}",
                source=edge.source_id,
                target=edge.target_id,
                role=flow_role,
                stroke_hex=stroke_hex,
                dashed=is_dashed,
                has_arrow=edge.arrow_end,
                label=clean_lbl,
            )
        )

    cleaned_name = _clean_text(name) if name else ""
    clean_title = cleaned_name or diagram_id.replace("_", " ").title()
    spec = DiagramSpec(
        id=diagram_id,
        name=clean_title,
        theme=theme,
        layout=top_layout,
        canvas=CanvasConfig(),
        header=HeaderConfig(
            show=True,
            action_title=clean_title,
            subtitle="Auto-transpiled from Mermaid flowchart topology",
            brand_stripes=True,
        ),
        containers=containers,
        nodes=nodes,
        flows=flows,
    )
    return spec


def _spec_to_clean_dict(spec: DiagramSpec) -> Dict[str, Any]:
    """Serialize DiagramSpec to a concise YAML-ready dict without None clutter."""
    raw = spec.model_dump(exclude_none=True)
    # Strip internal default-only fields from nodes/containers for readability
    for c in raw.get("containers", []):
        c.pop("allow_dense_typography", None)
        c.pop("dash_pattern", None)
        c.pop("corner_radius", None)
    for n in raw.get("nodes", []):
        n.pop("shadow", None)
        n.pop("is_cylinder", None)
        n.pop("is_rounded", None)
    return raw


def transpile_mermaid_to_yaml(
    mermaid_code: str,
    diagram_id: str = "mermaid_diagram",
    name: Optional[str] = None,
    theme: str = "metrodata",
    output_path: Optional[Union[str, Path]] = None,
) -> Tuple[DiagramSpec, str]:
    """
    Transpile Mermaid flowchart code into a DiagramSpec and clean YAML string.
    Writes the YAML file to `output_path` if provided.
    """
    spec = transpile_mermaid_to_spec(
        mermaid_code=mermaid_code,
        diagram_id=diagram_id,
        name=name,
        theme=theme,
    )
    clean_dict = _spec_to_clean_dict(spec)
    yaml_text = yaml.safe_dump(clean_dict, sort_keys=False, allow_unicode=True)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(yaml_text, encoding="utf-8")

    return spec, yaml_text
