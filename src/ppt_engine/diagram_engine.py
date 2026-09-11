"""
Mermaid to Draw.io Converter & Diagram Compilation Subsystem
============================================================
Translates Mermaid syntax (flowcharts, process graphs, state diagrams)
into standard Draw.io mxGraph XML (.drawio) with intelligent auto-layout,
preset brand palettes, and headless vector SVG / high-DPI PNG compilation.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import html
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from xml.dom import minidom

# Auto-configure dynamic cairo library for macOS / Linux headless rasterization
def _setup_cairo_library() -> None:
    cairo_paths = [
        "/opt/homebrew/lib/libcairo.2.dylib",
        "/opt/homebrew/lib/libcairo.dylib",
        "/usr/local/lib/libcairo.2.dylib",
        "/usr/local/lib/libcairo.dylib",
        "/usr/lib/libcairo.so.2",
        "/usr/lib/x86_64-linux-gnu/libcairo.so.2",
        "/usr/lib/aarch64-linux-gnu/libcairo.so.2",
    ]
    orig_find = ctypes.util.find_library

    def custom_find(name: str) -> Optional[str]:
        if name in ("cairo", "cairo-2", "libcairo-2", "cairo.2", "libcairo"):
            for cp in cairo_paths:
                if os.path.exists(cp):
                    return cp
        return orig_find(name)

    ctypes.util.find_library = custom_find


_setup_cairo_library()


# ============================================================================
# 1. AST Data Structures for Diagram Modeling
# ============================================================================

@dataclass
class DiagramNode:
    id: str
    label: str
    shape: str = "rect"  # rect, rounded, stadium, subroutine, cylinder, circle, rhombus, hexagon, parallelogram, signal, startState, endState
    subgraph_id: Optional[str] = None
    style_classes: List[str] = field(default_factory=list)
    custom_style: Dict[str, str] = field(default_factory=dict)
    # Calculated layout geometry
    x: float = 0.0
    y: float = 0.0
    width: float = 160.0
    height: float = 60.0
    rank: int = 0
    order: int = 0


@dataclass
class DiagramEdge:
    source_id: str
    target_id: str
    label: Optional[str] = None
    style_type: str = "solid"  # solid, dashed, thick, line
    arrow_start: bool = False
    arrow_end: bool = True
    custom_style: Dict[str, str] = field(default_factory=dict)


@dataclass
class DiagramSubgraph:
    id: str
    title: str
    parent_subgraph_id: Optional[str] = None
    node_ids: List[str] = field(default_factory=list)
    # Calculated bounding box
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


@dataclass
class ParsedDiagram:
    diagram_type: str  # flowchart, stateDiagram
    direction: str  # TD, TB, LR, BT, RL
    nodes: Dict[str, DiagramNode] = field(default_factory=dict)
    edges: List[DiagramEdge] = field(default_factory=list)
    subgraphs: Dict[str, DiagramSubgraph] = field(default_factory=dict)
    classes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # Global diagram bounds
    total_width: float = 0.0
    total_height: float = 0.0


# ============================================================================
# 2. Theme Presets and Brand Palette Definitions
# ============================================================================

THEME_PRESETS: Dict[str, Dict[str, Any]] = {
    "modern_consulting": {
        "canvas_bg": "#F8FAFC",
        "container_fill": "#F1F5F9",
        "container_stroke": "#CBD5E1",
        "container_font": "#0F172A",
        "node_fill": "#FFFFFF",
        "node_stroke": "#0F766E",
        "node_stroke_width": "2",
        "node_font": "#0F172A",
        "node_font_family": "Helvetica, Arial, sans-serif",
        "node_font_size": "13",
        "accent_node_fill": "#F0FDF4",
        "accent_node_stroke": "#16A34A",
        "accent_node_font": "#14532D",
        "edge_stroke": "#64748B",
        "edge_stroke_width": "2",
        "edge_font": "#475569",
        "edge_font_size": "11",
        "state_node_fill": "#0F172A",
    },
    "corporate_navy": {
        "canvas_bg": "#F8FAFC",
        "container_fill": "#F1F5F9",
        "container_stroke": "#CBD5E1",
        "container_font": "#1E293B",
        "node_fill": "#FFFFFF",
        "node_stroke": "#2563EB",
        "node_stroke_width": "2",
        "node_font": "#1E293B",
        "node_font_family": "Helvetica, Arial, sans-serif",
        "node_font_size": "13",
        "accent_node_fill": "#EFF6FF",
        "accent_node_stroke": "#3B82F6",
        "accent_node_font": "#1E40AF",
        "edge_stroke": "#64748B",
        "edge_stroke_width": "2",
        "edge_font": "#475569",
        "edge_font_size": "11",
        "state_node_fill": "#1E293B",
    },
    "executive_tech": {
        "canvas_bg": "#0F172A",
        "container_fill": "#1E293B",
        "container_stroke": "#334155",
        "container_font": "#F8FAFC",
        "node_fill": "#1E293B",
        "node_stroke": "#06B6D4",
        "node_stroke_width": "2",
        "node_font": "#F8FAFC",
        "node_font_family": "Helvetica, Arial, sans-serif",
        "node_font_size": "13",
        "accent_node_fill": "#312E81",
        "accent_node_stroke": "#6366F1",
        "accent_node_font": "#EEF2FF",
        "edge_stroke": "#94A3B8",
        "edge_stroke_width": "2",
        "edge_font": "#CBD5E1",
        "edge_font_size": "11",
        "state_node_fill": "#38BDF8",
    },
    "warm_amber": {
        "canvas_bg": "#FFFAF0",
        "container_fill": "#FEF3C7",
        "container_stroke": "#FDE68A",
        "container_font": "#78350F",
        "node_fill": "#FFFFFF",
        "node_stroke": "#D97706",
        "node_stroke_width": "2",
        "node_font": "#78350F",
        "node_font_family": "Helvetica, Arial, sans-serif",
        "node_font_size": "13",
        "accent_node_fill": "#FFFBEB",
        "accent_node_stroke": "#B45309",
        "accent_node_font": "#78350F",
        "edge_stroke": "#92400E",
        "edge_stroke_width": "2",
        "edge_font": "#78350F",
        "edge_font_size": "11",
        "state_node_fill": "#D97706",
    },
}


# ============================================================================
# 3. Mermaid Parser
# ============================================================================

class MermaidParser:
    """Parses Mermaid diagram text into an AST structure."""

    NODE_REGEX = re.compile(
        r"""^(?P<id>[a-zA-Z0-9_.-]+)(?:
            \(\[\s*(?P<stadium>.*?)\s*\]\)
          | \[\[\s*(?P<subroutine>.*?)\s*\]\]
          | \[\(\s*(?P<cylinder>.*?)\s*\)\]
          | \(\(\s*(?P<circle>.*?)\s*\)\)
          | \{\{\s*(?P<hexagon>.*?)\s*\}\}
          | \{\s*(?P<rhombus>.*?)\s*\}
          | \[/\s*(?P<parallelogram>.*?)\s*/\]
          | \[\\\s*(?P<parallelogram_alt>.*?)\s*\\\]
          | >\s*(?P<signal>.*?)\s*\]
          | \(\s*(?P<rounded>.*?)\s*\)
          | \[\s*(?P<rect>.*?)\s*\]
        )?$""",
        re.VERBOSE | re.DOTALL,
    )

    LINE_SPLIT_REGEX = re.compile(
        r"""(\s*(?:<--+>|<==+>|--+>|==+>|-\.+->|-\.+>>|--+|==+|-\.+-|<--+|<==+)(?:\|[^|]+\|)?\s*"""
        r"""|\s*(?:--|==|-\.)\s*(?:\"(?:[^\"\\]|\\.)+\"|[^>\-=\.]+?)\s*(?:-->|==>|\.->|--|==|-\.)\s*)"""
    )

    def __init__(self) -> None:
        self.parsed = ParsedDiagram(diagram_type="flowchart", direction="TD")
        self._current_subgraph_stack: List[str] = []
        self._state_node_counter = 0

    def parse(self, text: str) -> ParsedDiagram:
        """Parse Mermaid flowchart or state diagram."""
        self.parsed = ParsedDiagram(diagram_type="flowchart", direction="TD")
        self._current_subgraph_stack = []
        self._state_node_counter = 0

        clean_text = self._strip_mermaid_boilerplate(text)
        normalized_text = self._normalize_statements(clean_text)
        lines = [ln.strip() for ln in normalized_text.splitlines() if ln.strip()]

        for line in lines:
            if line.startswith("%%"):
                continue

            if self._parse_header(line):
                continue

            if self._parse_subgraph_statement(line):
                continue

            if self._parse_style_or_class(line):
                continue

            if self.parsed.diagram_type == "stateDiagram":
                if self._parse_state_line(line):
                    continue

            if self._parse_flowchart_line(line):
                continue

            self._parse_standalone_node(line)

        return self.parsed

    def _strip_mermaid_boilerplate(self, text: str) -> str:
        text = re.sub(r"^```mermaid\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r"^```\s*$", "", text, flags=re.MULTILINE)
        return text

    def _normalize_statements(self, text: str) -> str:
        """Normalizes semicolon statement delimiters to newlines while preserving quoted text."""
        result: List[str] = []
        in_quote = False
        quote_char: Optional[str] = None
        for char in text:
            if char in ('"', "'") and (quote_char is None or quote_char == char):
                in_quote = not in_quote
                quote_char = char if in_quote else None
            elif char == ";" and not in_quote:
                result.append("\n")
                continue
            result.append(char)
        return "".join(result)


    def _parse_header(self, line: str) -> bool:
        flowchart_match = re.match(r"^(?:graph|flowchart)\s+(TD|TB|LR|BT|RL)\b", line, re.IGNORECASE)
        if flowchart_match:
            self.parsed.diagram_type = "flowchart"
            self.parsed.direction = flowchart_match.group(1).upper()
            return True

        if re.match(r"^stateDiagram(?:-v2)?\b", line, re.IGNORECASE):
            self.parsed.diagram_type = "stateDiagram"
            self.parsed.direction = "TD"
            return True

        return False

    def _parse_subgraph_statement(self, line: str) -> bool:
        if line.lower() == "end":
            if self._current_subgraph_stack:
                self._current_subgraph_stack.pop()
            return True

        subgraph_match = re.match(r"^subgraph\s+([a-zA-Z0-9_.-]+)(?:\s*\[(.*?)\]|\s*\"(.*?)\")?", line, re.IGNORECASE)
        if subgraph_match:
            sg_id = subgraph_match.group(1)
            title = subgraph_match.group(2) or subgraph_match.group(3) or sg_id
            parent = self._current_subgraph_stack[-1] if self._current_subgraph_stack else None
            self.parsed.subgraphs[sg_id] = DiagramSubgraph(id=sg_id, title=self._clean_label(title), parent_subgraph_id=parent)
            self._current_subgraph_stack.append(sg_id)
            return True

        anon_subgraph_match = re.match(r"^subgraph\s+\"(.*?)\"", line, re.IGNORECASE)
        if anon_subgraph_match:
            title = anon_subgraph_match.group(1)
            sg_id = f"subgraph_{len(self.parsed.subgraphs) + 1}"
            parent = self._current_subgraph_stack[-1] if self._current_subgraph_stack else None
            self.parsed.subgraphs[sg_id] = DiagramSubgraph(id=sg_id, title=self._clean_label(title), parent_subgraph_id=parent)
            self._current_subgraph_stack.append(sg_id)
            return True

        return False

    def _parse_style_or_class(self, line: str) -> bool:
        class_def_match = re.match(r"^classDef\s+([a-zA-Z0-9_.-]+)\s+(.+)$", line)
        if class_def_match:
            c_name = class_def_match.group(1)
            raw_props = class_def_match.group(2).split(",")
            props: Dict[str, str] = {}
            for p in raw_props:
                if ":" in p:
                    k, v = p.split(":", 1)
                    props[k.strip()] = v.strip()
            self.parsed.classes[c_name] = props
            return True

        class_assign_match = re.match(r"^class\s+([a-zA-Z0-9_.,-]+)\s+([a-zA-Z0-9_.-]+)$", line)
        if class_assign_match:
            node_ids = class_assign_match.group(1).split(",")
            c_name = class_assign_match.group(2)
            for nid in node_ids:
                nid = nid.strip()
                if nid in self.parsed.nodes:
                    self.parsed.nodes[nid].style_classes.append(c_name)
            return True

        style_match = re.match(r"^style\s+([a-zA-Z0-9_.-]+)\s+(.+)$", line)
        if style_match:
            nid = style_match.group(1)
            raw_props = style_match.group(2).split(",")
            props = {}
            for p in raw_props:
                if ":" in p:
                    k, v = p.split(":", 1)
                    props[k.strip()] = v.strip()
            if nid in self.parsed.nodes:
                self.parsed.nodes[nid].custom_style.update(props)
            return True

        return False

    def _parse_state_line(self, line: str) -> bool:
        state_decl = re.match(r"^state\s+\"(.*?)\"\s+as\s+([a-zA-Z0-9_.-]+)$", line)
        if state_decl:
            label = state_decl.group(1)
            sid = state_decl.group(2)
            self._ensure_node(sid, label, "rounded")
            return True

        state_desc = re.match(r"^([a-zA-Z0-9_.-]+)\s*:\s*(.+)$", line)
        if state_desc:
            sid = state_desc.group(1)
            label = state_desc.group(2)
            self._ensure_node(sid, label, "rounded")
            return True

        transition_match = re.match(r"^(\[\*\]|[a-zA-Z0-9_.-]+)\s*-->\s*(\[\*\]|[a-zA-Z0-9_.-]+)(?:\s*:\s*(.+))?$", line)
        if transition_match:
            src_raw = transition_match.group(1)
            tgt_raw = transition_match.group(2)
            lbl = transition_match.group(3)

            src_id = self._resolve_state_node(src_raw, is_start=True)
            tgt_id = self._resolve_state_node(tgt_raw, is_start=False)

            self.parsed.edges.append(
                DiagramEdge(
                    source_id=src_id,
                    target_id=tgt_id,
                    label=self._clean_label(lbl) if lbl else None,
                    style_type="solid",
                    arrow_end=True,
                )
            )
            return True

        return False

    def _resolve_state_node(self, node_str: str, is_start: bool) -> str:
        if node_str == "[*]":
            self._state_node_counter += 1
            node_id = f"__state_{'start' if is_start else 'end'}_{self._state_node_counter}"
            shape = "startState" if is_start else "endState"
            node = DiagramNode(id=node_id, label="", shape=shape)
            node.width = 30
            node.height = 30
            self.parsed.nodes[node_id] = node
            return node_id
        else:
            if node_str not in self.parsed.nodes:
                self.parsed.nodes[node_str] = DiagramNode(id=node_str, label=node_str, shape="rounded")
            return node_str

    def _parse_flowchart_line(self, line: str) -> bool:
        parts = self.LINE_SPLIT_REGEX.split(line.strip())
        parts = [p for p in parts if p.strip()]

        if len(parts) < 3:
            return False

        # Parts should alternate: [node, connector, node, connector, node, ...]
        # Parse first node
        src_node = self._parse_and_register_node(parts[0])

        idx = 1
        while idx < len(parts) - 1:
            conn_token = parts[idx]
            tgt_token = parts[idx + 1]

            tgt_node = self._parse_and_register_node(tgt_token)
            style_type, arrow_start, arrow_end, label = self._parse_connector_details(conn_token)

            self.parsed.edges.append(
                DiagramEdge(
                    source_id=src_node.id,
                    target_id=tgt_node.id,
                    label=label,
                    style_type=style_type,
                    arrow_start=arrow_start,
                    arrow_end=arrow_end,
                )
            )

            src_node = tgt_node
            idx += 2

        return True

    def _parse_connector_details(self, conn_token: str) -> Tuple[str, bool, bool, Optional[str]]:
        conn_token = conn_token.strip()
        label = None

        # Check for pipe label |...|
        pipe_match = re.search(r"\|([^|]+)\|", conn_token)
        if pipe_match:
            label = self._clean_label(pipe_match.group(1))
            conn_token = conn_token.replace(pipe_match.group(0), "")

        # Check for inline label -- "label" --> or -- label -->
        inline_match = re.search(r"(?:--|==|-\.)\s*(?:\"([^\"]+)\"|([^>\-=\.]+?))\s*(?:-->|==>|\.->|--|==|-\.)", conn_token)
        if inline_match:
            raw_lbl = inline_match.group(1) or inline_match.group(2)
            if raw_lbl:
                label = self._clean_label(raw_lbl)

        arrow_start = "<" in conn_token
        arrow_end = ">" in conn_token
        if not arrow_start and not arrow_end:
            # If plain line --- or === or -.-
            arrow_end = False

        if "=" in conn_token:
            style_type = "thick"
        elif "." in conn_token:
            style_type = "dashed"
        else:
            style_type = "solid"

        return style_type, arrow_start, arrow_end, label

    def _parse_standalone_node(self, line: str) -> None:
        self._parse_and_register_node(line)

    def _parse_and_register_node(self, token: str) -> DiagramNode:
        token = token.strip()
        m = self.NODE_REGEX.match(token)
        if m:
            nid = m.group("id")
            shape = "rect"
            label = nid
            for k, v in m.groupdict().items():
                if k != "id" and v is not None:
                    shape = k
                    label = self._clean_label(v)
                    break
            return self._ensure_node(nid, label, shape)

        # Fallback for plain alphanumeric ID
        nid = re.sub(r"[^\w\.-]", "", token)
        if not nid:
            nid = token
        return self._ensure_node(nid, nid, "rect")

    def _ensure_node(self, nid: str, label: str, shape: str) -> DiagramNode:
        current_sg = self._current_subgraph_stack[-1] if self._current_subgraph_stack else None
        if nid not in self.parsed.nodes:
            node = DiagramNode(id=nid, label=label, shape=shape, subgraph_id=current_sg)
            self.parsed.nodes[nid] = node
            if current_sg and current_sg in self.parsed.subgraphs:
                if nid not in self.parsed.subgraphs[current_sg].node_ids:
                    self.parsed.subgraphs[current_sg].node_ids.append(nid)
        else:
            node = self.parsed.nodes[nid]
            if label and label != nid:
                node.label = label
            if shape != "rect":
                node.shape = shape
            if current_sg and not node.subgraph_id:
                node.subgraph_id = current_sg
                if current_sg in self.parsed.subgraphs and nid not in self.parsed.subgraphs[current_sg].node_ids:
                    self.parsed.subgraphs[current_sg].node_ids.append(nid)
        return node

    def _clean_label(self, lbl: str) -> str:
        if not lbl:
            return ""
        lbl = lbl.strip()
        if (lbl.startswith('"') and lbl.endswith('"')) or (lbl.startswith("'") and lbl.endswith("'")):
            lbl = lbl[1:-1]
        lbl = re.sub(r"<br\s*/?>", "\n", lbl, flags=re.IGNORECASE)
        lbl = lbl.replace(r"\n", "\n")
        return lbl.strip()


# ============================================================================
# 4. Hierarchical Auto-Layout Engine
# ============================================================================

class HierarchicalLayoutEngine:
    """
    Computes 2D grid/hierarchical coordinates (x, y, width, height)
    for nodes, edges, and enclosing subgraphs according to layout direction.
    """

    def __init__(
        self,
        rank_spacing: float = 80.0,
        node_spacing: float = 40.0,
        subgraph_padding: float = 30.0,
        subgraph_header: float = 35.0,
    ) -> None:
        self.rank_spacing = rank_spacing
        self.node_spacing = node_spacing
        self.subgraph_padding = subgraph_padding
        self.subgraph_header = subgraph_header

    def compute_layout(self, diagram: ParsedDiagram) -> ParsedDiagram:
        """Assign coordinates to all nodes and subgraphs."""
        if not diagram.nodes:
            return diagram

        self._calculate_node_sizes(diagram)
        adj, rev_adj = self._build_adjacency(diagram)
        ranks = self._assign_ranks(diagram, adj, rev_adj)

        rank_groups: Dict[int, List[str]] = {}
        for nid, r in ranks.items():
            rank_groups.setdefault(r, []).append(nid)

        sorted_rank_nums = sorted(rank_groups.keys())
        is_horizontal = diagram.direction in ("LR", "RL")
        is_reversed = diagram.direction in ("BT", "RL")

        if is_reversed:
            sorted_rank_nums = list(reversed(sorted_rank_nums))

        current_primary = 40.0

        for r_num in sorted_rank_nums:
            nodes_in_rank = rank_groups[r_num]
            nodes_in_rank.sort(key=lambda nid: (diagram.nodes[nid].subgraph_id or "", nid))

            if not is_horizontal:
                max_rank_thickness = max(diagram.nodes[nid].height for nid in nodes_in_rank)
            else:
                max_rank_thickness = max(diagram.nodes[nid].width for nid in nodes_in_rank)

            current_cross = 40.0
            for nid in nodes_in_rank:
                node = diagram.nodes[nid]
                if not is_horizontal:
                    node.x = current_cross
                    node.y = current_primary
                    current_cross += node.width + self.node_spacing
                else:
                    node.x = current_primary
                    node.y = current_cross
                    current_cross += node.height + self.node_spacing

            current_primary += max_rank_thickness + self.rank_spacing

        # Calculate Subgraph Bounding Boxes
        for sg_id, sg in diagram.subgraphs.items():
            sg_nodes = [diagram.nodes[nid] for nid in sg.node_ids if nid in diagram.nodes]
            if sg_nodes:
                min_x = min(n.x for n in sg_nodes) - self.subgraph_padding
                min_y = min(n.y for n in sg_nodes) - self.subgraph_padding - self.subgraph_header
                max_x = max(n.x + n.width for n in sg_nodes) + self.subgraph_padding
                max_y = max(n.y + n.height for n in sg_nodes) + self.subgraph_padding
                sg.x = max(10.0, min_x)
                sg.y = max(10.0, min_y)
                sg.width = max_x - sg.x
                sg.height = max_y - sg.y

        # Normalize coordinates
        all_x = [n.x for n in diagram.nodes.values()] + [sg.x for sg in diagram.subgraphs.values() if sg.width > 0]
        all_y = [n.y for n in diagram.nodes.values()] + [sg.y for sg in diagram.subgraphs.values() if sg.height > 0]
        min_canvas_x = min(all_x) if all_x else 0.0
        min_canvas_y = min(all_y) if all_y else 0.0

        offset_x = 40.0 - min_canvas_x
        offset_y = 40.0 - min_canvas_y

        for node in diagram.nodes.values():
            node.x += offset_x
            node.y += offset_y

        for sg in diagram.subgraphs.values():
            if sg.width > 0:
                sg.x += offset_x
                sg.y += offset_y

        max_bound_x = max((n.x + n.width for n in diagram.nodes.values()), default=100.0)
        max_bound_y = max((n.y + n.height for n in diagram.nodes.values()), default=100.0)
        for sg in diagram.subgraphs.values():
            if sg.width > 0:
                max_bound_x = max(max_bound_x, sg.x + sg.width)
                max_bound_y = max(max_bound_y, sg.y + sg.height)

        diagram.total_width = max_bound_x + 40.0
        diagram.total_height = max_bound_y + 40.0

        return diagram

    def _calculate_node_sizes(self, diagram: ParsedDiagram) -> None:
        for node in diagram.nodes.values():
            if node.shape in ("startState", "endState"):
                node.width = 32.0
                node.height = 32.0
                continue
            if node.shape == "circle":
                size = max(60.0, len(node.label) * 7.5 + 24.0)
                node.width = size
                node.height = size
                continue
            if node.shape == "rhombus":
                size = max(80.0, len(node.label) * 8.0 + 35.0)
                node.width = size * 1.2
                node.height = size
                continue

            lines = node.label.split("\n")
            max_line_len = max((len(l) for l in lines), default=1)
            line_count = len(lines)

            calc_width = max(140.0, max_line_len * 8.5 + 36.0)
            calc_height = max(52.0, line_count * 20.0 + 26.0)

            node.width = round(calc_width, 1)
            node.height = round(calc_height, 1)

    def _build_adjacency(self, diagram: ParsedDiagram) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
        adj: Dict[str, Set[str]] = {nid: set() for nid in diagram.nodes}
        rev_adj: Dict[str, Set[str]] = {nid: set() for nid in diagram.nodes}
        for e in diagram.edges:
            if e.source_id in adj and e.target_id in adj:
                adj[e.source_id].add(e.target_id)
                rev_adj[e.target_id].add(e.source_id)
        return adj, rev_adj

    def _assign_ranks(
        self, diagram: ParsedDiagram, adj: Dict[str, Set[str]], rev_adj: Dict[str, Set[str]]
    ) -> Dict[str, int]:
        ranks: Dict[str, int] = {}
        visited: Set[str] = set()

        roots = [nid for nid, in_edges in rev_adj.items() if not in_edges]
        if not roots:
            roots = list(diagram.nodes.keys())[:1]

        def dfs(curr: str, current_rank: int, path: Set[str]) -> None:
            ranks[curr] = max(ranks.get(curr, 0), current_rank)
            visited.add(curr)
            for neighbor in adj.get(curr, set()):
                if neighbor not in path:
                    dfs(neighbor, current_rank + 1, path | {neighbor})

        for r in roots:
            dfs(r, 0, {r})

        for nid in diagram.nodes:
            if nid not in ranks:
                dfs(nid, 0, {nid})

        return ranks


# ============================================================================
# 5. Draw.io mxGraph XML Converter
# ============================================================================

class DrawIOConverter:
    """Converts ParsedDiagram AST into standard Draw.io mxGraph XML."""

    SHAPE_STYLE_MAP = {
        "rect": "rounded=0;whiteSpace=wrap;html=1;",
        "rounded": "rounded=1;whiteSpace=wrap;html=1;arcSize=14;",
        "stadium": "rounded=1;whiteSpace=wrap;html=1;arcSize=50;",
        "subroutine": "shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;",
        "cylinder": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;",
        "circle": "ellipse;whiteSpace=wrap;html=1;aspect=fixed;",
        "rhombus": "rhombus;whiteSpace=wrap;html=1;",
        "hexagon": "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;",
        "parallelogram": "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;",
        "parallelogram_alt": "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;",
        "signal": "shape=signal;whiteSpace=wrap;html=1;",
        "startState": "ellipse;fillColor={state_fill};strokeColor=none;",
        "endState": "shape=endState;fillColor={state_fill};strokeColor={state_fill};",
    }

    def __init__(self, theme_name: str = "modern_consulting", custom_theme: Optional[Dict[str, Any]] = None) -> None:
        self.theme = dict(THEME_PRESETS.get(theme_name, THEME_PRESETS["modern_consulting"]))
        if custom_theme:
            self.theme.update(custom_theme)

    def to_xml(self, diagram: ParsedDiagram, page_name: str = "Page-1") -> str:
        """Generate standard Draw.io mxGraph XML string."""
        mxfile = ET.Element(
            "mxfile",
            attrib={
                "host": "Electron",
                "modified": "2026-09-03T00:00:00.000Z",
                "agent": "PPTMaking Diagram Engine",
                "version": "21.0.0",
                "type": "device",
            },
        )
        diagram_elem = ET.SubElement(mxfile, "diagram", attrib={"id": "diagram_1", "name": page_name})

        pw = max(1169, int(diagram.total_width + 100))
        ph = max(827, int(diagram.total_height + 100))

        graph_model = ET.SubElement(
            diagram_elem,
            "mxGraphModel",
            attrib={
                "dx": "1200",
                "dy": "800",
                "grid": "1",
                "gridSize": "10",
                "guides": "1",
                "tooltips": "1",
                "connect": "1",
                "arrows": "1",
                "fold": "1",
                "page": "1",
                "pageScale": "1",
                "pageWidth": str(pw),
                "pageHeight": str(ph),
                "math": "0",
                "shadow": "0",
            },
        )

        root = ET.SubElement(graph_model, "root")
        ET.SubElement(root, "mxCell", attrib={"id": "0"})
        ET.SubElement(root, "mxCell", attrib={"id": "1", "parent": "0"})

        # 1. Render Subgraphs
        for sg_id, sg in diagram.subgraphs.items():
            if sg.width <= 0 or sg.height <= 0:
                continue
            sg_style = (
                f"swimlane;whiteSpace=wrap;html=1;startSize=28;rounded=1;arcSize=8;"
                f"fillColor={self.theme['container_fill']};strokeColor={self.theme['container_stroke']};"
                f"strokeWidth=1.5;fontColor={self.theme['container_font']};"
                f"fontFamily={self.theme['node_font_family']};fontSize=12;fontStyle=1;"
            )
            sg_cell = ET.SubElement(
                root,
                "mxCell",
                attrib={
                    "id": f"subgraph_{sg_id}",
                    "value": html.escape(sg.title),
                    "style": sg_style,
                    "vertex": "1",
                    "parent": "1",
                },
            )
            ET.SubElement(
                sg_cell,
                "mxGeometry",
                attrib={
                    "x": str(int(sg.x)),
                    "y": str(int(sg.y)),
                    "width": str(int(sg.width)),
                    "height": str(int(sg.height)),
                    "as": "geometry",
                },
            )

        # 2. Render Nodes
        for nid, node in diagram.nodes.items():
            style_str = self._build_node_style(node)
            cell_val = html.escape(node.label).replace("\n", "<br>")
            cell = ET.SubElement(
                root,
                "mxCell",
                attrib={
                    "id": f"node_{nid}",
                    "value": cell_val,
                    "style": style_str,
                    "vertex": "1",
                    "parent": "1",
                },
            )
            ET.SubElement(
                cell,
                "mxGeometry",
                attrib={
                    "x": str(int(node.x)),
                    "y": str(int(node.y)),
                    "width": str(int(node.width)),
                    "height": str(int(node.height)),
                    "as": "geometry",
                },
            )

        # 3. Render Edges
        edge_counter = 0
        for edge in diagram.edges:
            edge_counter += 1
            src_cell_id = f"node_{edge.source_id}"
            tgt_cell_id = f"node_{edge.target_id}"
            edge_style = self._build_edge_style(edge, diagram.direction)
            edge_val = html.escape(edge.label or "").replace("\n", "<br>")

            e_cell = ET.SubElement(
                root,
                "mxCell",
                attrib={
                    "id": f"edge_{edge_counter}",
                    "value": edge_val,
                    "style": edge_style,
                    "edge": "1",
                    "parent": "1",
                    "source": src_cell_id,
                    "target": tgt_cell_id,
                },
            )
            ET.SubElement(e_cell, "mxGeometry", attrib={"relative": "1", "as": "geometry"})

        raw_xml = ET.tostring(mxfile, encoding="utf-8")
        parsed_xml = minidom.parseString(raw_xml)
        return parsed_xml.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    def _build_node_style(self, node: DiagramNode) -> str:
        shape_template = self.SHAPE_STYLE_MAP.get(node.shape, self.SHAPE_STYLE_MAP["rect"])
        if "{state_fill}" in shape_template:
            return shape_template.format(state_fill=self.theme["state_node_fill"])

        is_accent = "accent" in node.style_classes or "highlight" in node.style_classes
        fill = self.theme["accent_node_fill"] if is_accent else self.theme["node_fill"]
        stroke = self.theme["accent_node_stroke"] if is_accent else self.theme["node_stroke"]
        font_col = self.theme["accent_node_font"] if is_accent else self.theme["node_font"]

        fill = node.custom_style.get("fill", fill)
        stroke = node.custom_style.get("stroke", stroke)
        font_col = node.custom_style.get("color", font_col)

        style_parts = [
            shape_template,
            f"fillColor={fill};",
            f"strokeColor={stroke};",
            f"strokeWidth={self.theme['node_stroke_width']};",
            f"fontColor={font_col};",
            f"fontFamily={self.theme['node_font_family']};",
            f"fontSize={self.theme['node_font_size']};",
            "fontStyle=0;",
            "shadow=0;",
        ]
        return "".join(style_parts)

    def _build_edge_style(self, edge: DiagramEdge, direction: str) -> str:
        style_parts = [
            "edgeStyle=orthogonalEdgeStyle;",
            "rounded=1;",
            "orthogonalLoop=1;",
            "jettySize=auto;",
            "html=1;",
            f"strokeColor={self.theme['edge_stroke']};",
            f"strokeWidth={self.theme['edge_stroke_width']};",
            f"fontColor={self.theme['edge_font']};",
            f"fontFamily={self.theme['node_font_family']};",
            f"fontSize={self.theme['edge_font_size']};",
        ]

        if edge.style_type == "dashed":
            style_parts.append("dashed=1;")
        elif edge.style_type == "thick":
            style_parts.append("strokeWidth=3;")

        if not edge.arrow_end:
            style_parts.append("endArrow=none;")
        if edge.arrow_start:
            style_parts.append("startArrow=classic;")

        if direction in ("LR", "RL"):
            style_parts.append("exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
        else:
            style_parts.append("exitX=0.5;exitY=1;entryX=0.5;entryY=0;")

        return "".join(style_parts)


# ============================================================================
# 6. High-Fidelity Headless Vector SVG & Raster Renderer
# ============================================================================

class DiagramRenderer:
    """
    Renders diagram AST and Draw.io XML to vector SVG and high-resolution PNG.
    Uses native drawio CLI if installed, or built-in SVG vector compiler + Cairo/Pillow.
    """

    def __init__(self, theme_name: str = "modern_consulting", custom_theme: Optional[Dict[str, Any]] = None) -> None:
        self.theme = dict(THEME_PRESETS.get(theme_name, THEME_PRESETS["modern_consulting"]))
        if custom_theme:
            self.theme.update(custom_theme)

    def render_svg(
        self,
        diagram: ParsedDiagram,
        transparent: bool = False,
        canvas_bg: Optional[str] = None,
    ) -> str:
        """Generate a clean, scalable SVG vector document."""
        w = max(400.0, diagram.total_width)
        h = max(300.0, diagram.total_height)
        bg_fill = canvas_bg or self.theme.get("canvas_bg", "#FFFFFF")

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" width="{w:.1f}" height="{h:.1f}">',
            "  <defs>",
            '    <filter id="card-shadow" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">',
            '      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0F172A" flood-opacity="0.06"/>',
            "    </filter>",
            '    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            f'      <path d="M 0 1 L 10 5 L 0 9 z" fill="{self.theme["edge_stroke"]}"/>',
            "    </marker>",
            '    <marker id="arrow-start" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            f'      <path d="M 10 1 L 0 5 L 10 9 z" fill="{self.theme["edge_stroke"]}"/>',
            "    </marker>",
            "  </defs>",
        ]
        if not transparent:
            svg_lines.append(f'  <rect width="{w:.1f}" height="{h:.1f}" fill="{bg_fill}"/>')

        # 1. Subgraphs / Containers
        for sg in diagram.subgraphs.values():
            if sg.width <= 0 or sg.height <= 0:
                continue
            svg_lines.append(
                f'  <rect x="{sg.x:.1f}" y="{sg.y:.1f}" width="{sg.width:.1f}" height="{sg.height:.1f}" rx="8" '
                f'fill="{self.theme["container_fill"]}" stroke="{self.theme["container_stroke"]}" stroke-width="1.5"/>'
            )
            svg_lines.append(
                f'  <text x="{sg.x + 16:.1f}" y="{sg.y + 22:.1f}" font-family="{self.theme["node_font_family"]}" '
                f'font-size="12" font-weight="bold" fill="{self.theme["container_font"]}">{html.escape(sg.title)}</text>'
            )

        # 2. Edges
        for edge in diagram.edges:
            if edge.source_id not in diagram.nodes or edge.target_id not in diagram.nodes:
                continue
            src = diagram.nodes[edge.source_id]
            tgt = diagram.nodes[edge.target_id]

            if diagram.direction in ("LR", "RL"):
                sx, sy = src.x + src.width, src.y + src.height / 2.0
                tx, ty = tgt.x, tgt.y + tgt.height / 2.0
                mx = (sx + tx) / 2.0
                d_path = f"M {sx:.1f} {sy:.1f} L {mx:.1f} {sy:.1f} L {mx:.1f} {ty:.1f} L {tx:.1f} {ty:.1f}"
                label_x = mx
                label_y = (sy + ty) / 2.0 - 6.0
            else:
                sx, sy = src.x + src.width / 2.0, src.y + src.height
                tx, ty = tgt.x + tgt.width / 2.0, tgt.y
                my = (sy + ty) / 2.0
                d_path = f"M {sx:.1f} {sy:.1f} L {sx:.1f} {my:.1f} L {tx:.1f} {my:.1f} L {tx:.1f} {ty:.1f}"
                label_x = (sx + tx) / 2.0 + 8.0
                label_y = my - 6.0

            dash_attr = ' stroke-dasharray="5,4"' if edge.style_type == "dashed" else ""
            width_attr = ' stroke-width="3"' if edge.style_type == "thick" else f' stroke-width="{self.theme["edge_stroke_width"]}"'
            end_marker = ' marker-end="url(#arrow)"' if edge.arrow_end else ""
            start_marker = ' marker-start="url(#arrow-start)"' if edge.arrow_start else ""

            svg_lines.append(
                f'  <path d="{d_path}" fill="none" stroke="{self.theme["edge_stroke"]}"{width_attr}{dash_attr}{start_marker}{end_marker}/>'
            )

            if edge.label:
                svg_lines.append(
                    f'  <text x="{label_x:.1f}" y="{label_y:.1f}" font-family="{self.theme["node_font_family"]}" '
                    f'font-size="{self.theme["edge_font_size"]}" fill="{self.theme["edge_font"]}" text-anchor="middle">{html.escape(edge.label)}</text>'
                )

        # 3. Nodes
        for node in diagram.nodes.values():
            svg_lines.extend(self._render_node_svg(node))

        svg_lines.append("</svg>")
        return "\n".join(svg_lines)

    def _render_node_svg(self, node: DiagramNode) -> List[str]:
        lines: List[str] = []
        is_accent = "accent" in node.style_classes or "highlight" in node.style_classes
        fill = self.theme["accent_node_fill"] if is_accent else self.theme["node_fill"]
        stroke = self.theme["accent_node_stroke"] if is_accent else self.theme["node_stroke"]
        font_col = self.theme["accent_node_font"] if is_accent else self.theme["node_font"]

        fill = node.custom_style.get("fill", fill)
        stroke = node.custom_style.get("stroke", stroke)
        font_col = node.custom_style.get("color", font_col)

        sw = self.theme["node_stroke_width"]

        if node.shape in ("startState", "endState"):
            r = node.width / 2.0
            cx, cy = node.x + r, node.y + r
            lines.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{self.theme["state_node_fill"]}"/>')
            if node.shape == "endState":
                lines.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 4.0:.1f}" fill="{self.theme["canvas_bg"]}"/>')
                lines.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 7.0:.1f}" fill="{self.theme["state_node_fill"]}"/>')
            return lines

        if node.shape == "circle":
            r = node.width / 2.0
            cx, cy = node.x + r, node.y + r
            lines.append(
                f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#card-shadow)"/>'
            )
        elif node.shape == "rhombus":
            cx, cy = node.x + node.width / 2.0, node.y + node.height / 2.0
            pts = f"{cx:.1f},{node.y:.1f} {node.x + node.width:.1f},{cy:.1f} {cx:.1f},{node.y + node.height:.1f} {node.x:.1f},{cy:.1f}"
            lines.append(
                f'  <polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#card-shadow)"/>'
            )
        elif node.shape == "cylinder":
            lines.append(
                f'  <rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" rx="12" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#card-shadow)"/>'
            )
        elif node.shape == "stadium":
            rx = node.height / 2.0
            lines.append(
                f'  <rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" rx="{rx:.1f}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#card-shadow)"/>'
            )
        elif node.shape == "subroutine":
            lines.append(
                f'  <rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" rx="4" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#card-shadow)"/>'
            )
            lines.append(f'  <line x1="{node.x + 10:.1f}" y1="{node.y:.1f}" x2="{node.x + 10:.1f}" y2="{node.y + node.height:.1f}" stroke="{stroke}" stroke-width="1.5"/>')
            lines.append(f'  <line x1="{node.x + node.width - 10:.1f}" y1="{node.y:.1f}" x2="{node.x + node.width - 10:.1f}" y2="{node.y + node.height:.1f}" stroke="{stroke}" stroke-width="1.5"/>')
        else:
            rx = "8" if node.shape == "rounded" else "3"
            lines.append(
                f'  <rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" rx="{rx}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#card-shadow)"/>'
            )

        text_lines = node.label.split("\n")
        total_text_h = len(text_lines) * 16.0
        start_y = node.y + (node.height - total_text_h) / 2.0 + 13.0
        cx = node.x + node.width / 2.0

        for i, tline in enumerate(text_lines):
            cur_y = start_y + i * 16.0
            lines.append(
                f'  <text x="{cx:.1f}" y="{cur_y:.1f}" font-family="{self.theme["node_font_family"]}" '
                f'font-size="{self.theme["node_font_size"]}" fill="{font_col}" text-anchor="middle" font-weight="500">{html.escape(tline)}</text>'
            )

        return lines

    def export_png(self, svg_content: str, output_png_path: Path, scale: float = 3.0) -> bool:
        """Rasterize SVG to high-resolution 300+ DPI PNG via resvg-py / CairoSVG."""
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import resvg_py
            png_bytes = resvg_py.svg_to_bytes(svg_content, zoom=scale)
            output_png_path.write_bytes(png_bytes)
            return True
        except Exception:
            pass

        try:
            import cairosvg
            cairosvg.svg2png(
                bytestring=svg_content.encode("utf-8"),
                write_to=str(output_png_path),
                scale=scale,
            )
            return True
        except Exception as e:
            print(f"[DiagramRenderer] Rasterization warning: {e}")
            return False


# ============================================================================
# 7. Sandboxed Engine Facade
# ============================================================================

class DiagramEngine:
    """
    Main orchestration class for compiling Mermaid diagrams into Draw.io mxGraph XML
    and rendered PNG / SVG vector assets with strict sandbox governance.
    """

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = workspace_root or Path.cwd()
        self.parser = MermaidParser()
        self.layout = HierarchicalLayoutEngine()

    def get_sandbox_dir(self, project_name: str) -> Path:
        """Resolve and enforce sandbox directory inside project_outputs/<project_name>/diagrams/."""
        sandbox = (self.workspace_root / "project_outputs" / project_name / "diagrams").resolve()
        allowed_root = (self.workspace_root / "project_outputs").resolve()
        if not str(sandbox).startswith(str(allowed_root)):
            raise ValueError(f"Security write barrier: path {sandbox} outside allowed output directory.")
        sandbox.mkdir(parents=True, exist_ok=True)
        return sandbox

    def compile(
        self,
        mermaid_code: str,
        project_name: str = "default_project",
        diagram_name: str = "diagram",
        theme: str = "modern_consulting",
        formats: Tuple[str, ...] = ("drawio", "svg", "png"),
        scale: float = 3.0,
    ) -> Dict[str, Path]:
        """
        Full compilation pipeline:
        1. Parse Mermaid syntax into AST.
        2. Compute hierarchical layout.
        3. Convert to Draw.io XML (.drawio).
        4. Render SVG and high-resolution PNG.
        5. Save all assets sandboxed to project_outputs/<project_name>/diagrams/.
        """
        sandbox = self.get_sandbox_dir(project_name)
        result_paths: Dict[str, Path] = {}

        parsed = self.parser.parse(mermaid_code)
        laid_out = self.layout.compute_layout(parsed)

        converter = DrawIOConverter(theme_name=theme)
        drawio_xml = converter.to_xml(laid_out, page_name=diagram_name)

        if "drawio" in formats:
            drawio_path = sandbox / f"{diagram_name}.drawio"
            drawio_path.write_text(drawio_xml, encoding="utf-8")
            result_paths["drawio"] = drawio_path

        renderer = DiagramRenderer(theme_name=theme)
        svg_content = renderer.render_svg(laid_out)

        if "svg" in formats:
            svg_path = sandbox / f"{diagram_name}.svg"
            svg_path.write_text(svg_content, encoding="utf-8")
            result_paths["svg"] = svg_path

        if "png" in formats:
            png_path = sandbox / f"{diagram_name}.png"
            cli_success = self._try_drawio_cli_export(result_paths.get("drawio"), png_path, scale)
            if not cli_success:
                renderer.export_png(svg_content, png_path, scale=scale)
            result_paths["png"] = png_path

        return result_paths

    def _try_drawio_cli_export(self, drawio_path: Optional[Path], output_png: Path, scale: float) -> bool:
        """Attempts to invoke drawio desktop CLI if installed."""
        if not drawio_path or not drawio_path.exists():
            return False

        cli_candidates = [
            "drawio",
            "draw.io",
            "/Applications/draw.io.app/Contents/MacOS/draw.io",
        ]
        for cmd in cli_candidates:
            if shutil.which(cmd) or os.path.exists(cmd):
                try:
                    res = subprocess.run(
                        [cmd, "--export", "--format", "png", "--scale", str(scale), "--output", str(output_png), str(drawio_path)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10,
                    )
                    if res.returncode == 0 and output_png.exists():
                        return True
                except Exception:
                    pass
        return False


def compile_mermaid(
    mermaid_code: str,
    project_name: str = "default_project",
    diagram_name: str = "diagram",
    theme: str = "modern_consulting",
    formats: Tuple[str, ...] = ("drawio", "svg", "png"),
) -> Dict[str, Path]:
    """Convenience functional interface for diagram compilation."""
    engine = DiagramEngine()
    return engine.compile(
        mermaid_code=mermaid_code,
        project_name=project_name,
        diagram_name=diagram_name,
        theme=theme,
        formats=formats,
    )


# ============================================================================
# 8. Multi-Page Draw.io Project Manager & Bidirectional AST Bridge
# ============================================================================

def mxgraph_to_ast(diagram_elem: ET.Element) -> ParsedDiagram:
    """
    Reconstructs a ParsedDiagram AST from an mxGraphModel or <diagram> XML element.
    Extracts vertices, geometry (x, y, width, height), labels, subgraphs/swimlanes, and edges.
    """
    graph_model = diagram_elem.find(".//mxGraphModel")
    if graph_model is None:
        if diagram_elem.tag == "mxGraphModel":
            graph_model = diagram_elem
        else:
            return ParsedDiagram(diagram_type="flowchart", direction="TD")

    root = graph_model.find("root")
    if root is None:
        return ParsedDiagram(diagram_type="flowchart", direction="TD")

    parsed = ParsedDiagram(diagram_type="flowchart", direction="TD")
    max_x, max_y = 0.0, 0.0

    for cell in root.findall("mxCell"):
        cid = cell.attrib.get("id", "")
        if cid in ("0", "1"):
            continue

        is_vertex = cell.attrib.get("vertex") == "1"
        is_edge = cell.attrib.get("edge") == "1"
        style = cell.attrib.get("style", "")
        raw_val = cell.attrib.get("value", "")
        clean_label = html.unescape(raw_val).replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")

        geom = cell.find("mxGeometry")
        x = float(geom.attrib.get("x", 0)) if geom is not None and "x" in geom.attrib else 0.0
        y = float(geom.attrib.get("y", 0)) if geom is not None and "y" in geom.attrib else 0.0
        w = float(geom.attrib.get("width", 140)) if geom is not None and "width" in geom.attrib else 140.0
        h = float(geom.attrib.get("height", 50)) if geom is not None and "height" in geom.attrib else 50.0

        if is_vertex:
            if "swimlane" in style:
                sg_id = cid.replace("subgraph_", "")
                parsed.subgraphs[sg_id] = DiagramSubgraph(
                    id=sg_id,
                    title=clean_label,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                )
            else:
                nid = cid.replace("node_", "")
                shape = "rect"
                if "ellipse" in style or "aspect=fixed" in style:
                    shape = "circle"
                elif "rhombus" in style:
                    shape = "rhombus"
                elif "cylinder" in style:
                    shape = "cylinder"
                elif "rounded=1" in style:
                    if "arcSize=50" in style:
                        shape = "stadium"
                    else:
                        shape = "rounded"
                elif "shape=process" in style:
                    shape = "subroutine"

                custom_style: Dict[str, str] = {}
                for part in style.split(";"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        if k.strip() in ("fillColor", "strokeColor", "fontColor"):
                            custom_style[k.strip()] = v.strip()

                parsed.nodes[nid] = DiagramNode(
                    id=nid,
                    label=clean_label,
                    shape=shape,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    custom_style=custom_style,
                )
                max_x = max(max_x, x + w)
                max_y = max(max_y, y + h)

        elif is_edge:
            src_raw = cell.attrib.get("source", "")
            tgt_raw = cell.attrib.get("target", "")
            src_id = src_raw.replace("node_", "")
            tgt_id = tgt_raw.replace("node_", "")
            style_type = "dashed" if "dashed=1" in style else ("thick" if "strokeWidth=3" in style else "solid")
            arrow_start = "startArrow=" in style and "startArrow=none" not in style
            arrow_end = "endArrow=none" not in style
            parsed.edges.append(
                DiagramEdge(
                    source_id=src_id,
                    target_id=tgt_id,
                    label=clean_label if clean_label else None,
                    style_type=style_type,
                    arrow_start=arrow_start,
                    arrow_end=arrow_end,
                )
            )

    # Assign nodes to subgraphs based on coordinates
    for sg_id, sg in parsed.subgraphs.items():
        max_x = max(max_x, sg.x + sg.width)
        max_y = max(max_y, sg.y + sg.height)
        for nid, node in parsed.nodes.items():
            if (
                sg.x <= node.x
                and (node.x + node.width) <= (sg.x + sg.width + 10)
                and sg.y <= node.y
                and (node.y + node.height) <= (sg.y + sg.height + 10)
            ):
                node.subgraph_id = sg_id
                if nid not in sg.node_ids:
                    sg.node_ids.append(nid)

    parsed.total_width = max(max_x + 40.0, 400.0)
    parsed.total_height = max(max_y + 40.0, 300.0)
    return parsed


class DrawIOProject:
    """
    Manages multi-page Draw.io (.drawio) XML documents.
    Supports reading, adding, updating, deleting, listing, and exporting
    individual diagram pages/tabs in a single unified master file.
    """

    def __init__(self, file_path: Optional[Union[str, Path]] = None) -> None:
        self.file_path = Path(file_path) if file_path else None
        self.root = ET.Element(
            "mxfile",
            attrib={
                "host": "Electron",
                "modified": "2026-09-11T00:00:00.000Z",
                "agent": "Enterprise Bench Diagram Engine",
                "version": "21.0.0",
                "type": "device",
            },
        )
        if self.file_path and self.file_path.exists():
            self._load_from_disk(self.file_path)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "DrawIOProject":
        """Load an existing .drawio file or initialize a new one at file_path."""
        return cls(file_path=file_path)

    @classmethod
    def from_xml(cls, xml_content: str) -> "DrawIOProject":
        """Initialize DrawIOProject directly from XML string."""
        proj = cls()
        proj.root = ET.fromstring(xml_content.strip())
        return proj

    def _load_from_disk(self, path: Path) -> None:
        raw = path.read_text(encoding="utf-8")
        self.root = ET.fromstring(raw.strip())

    def list_pages(self) -> List[Dict[str, Any]]:
        """Return a list of metadata for all diagram pages in the file."""
        pages: List[Dict[str, Any]] = []
        for idx, diag in enumerate(self.root.findall("diagram")):
            pid = diag.attrib.get("id", f"diagram_{idx + 1}")
            pname = diag.attrib.get("name", f"Page-{idx + 1}")
            cells = diag.findall(".//mxCell")
            node_count = sum(
                1
                for c in cells
                if c.attrib.get("vertex") == "1" and "swimlane" not in c.attrib.get("style", "")
            )
            edge_count = sum(1 for c in cells if c.attrib.get("edge") == "1")
            container_count = sum(1 for c in cells if "swimlane" in c.attrib.get("style", ""))
            pages.append(
                {
                    "index": idx,
                    "id": pid,
                    "name": pname,
                    "node_count": node_count,
                    "edge_count": edge_count,
                    "container_count": container_count,
                }
            )
        return pages

    def get_page(self, name_or_index: Union[str, int]) -> Optional[ET.Element]:
        """Find a <diagram> element by its name (case-insensitive) or index."""
        diagrams = self.root.findall("diagram")
        if isinstance(name_or_index, int):
            if 0 <= name_or_index < len(diagrams):
                return diagrams[name_or_index]
            return None

        target = str(name_or_index).strip().lower()
        if target.isdigit():
            idx = int(target)
            if 0 <= idx < len(diagrams):
                return diagrams[idx]

        for diag in diagrams:
            if diag.attrib.get("name", "").strip().lower() == target:
                return diag
            if diag.attrib.get("id", "").strip().lower() == target:
                return diag
        return None

    def add_or_update_page(
        self,
        name: str,
        diagram: ParsedDiagram,
        page_id: Optional[str] = None,
        theme: str = "modern_consulting",
    ) -> str:
        """
        Converts a ParsedDiagram AST to mxGraphModel and inserts or replaces the named page.
        Returns the page_id.
        """
        converter = DrawIOConverter(theme_name=theme)
        temp_xml = converter.to_xml(diagram, page_name=name)
        temp_root = ET.fromstring(temp_xml.strip())
        temp_diag = temp_root.find("diagram")
        if temp_diag is None:
            raise ValueError("Failed to generate diagram page from AST")

        existing = self.get_page(name)
        assigned_id = page_id or (
            existing.attrib.get("id")
            if existing is not None
            else f"page_{re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()}"
        )
        temp_diag.attrib["id"] = assigned_id
        temp_diag.attrib["name"] = name

        if existing is not None:
            idx = list(self.root).index(existing)
            self.root.remove(existing)
            self.root.insert(idx, temp_diag)
        else:
            self.root.append(temp_diag)

        return assigned_id

    def add_mermaid_page(
        self,
        name: str,
        mermaid_code: str,
        page_id: Optional[str] = None,
        theme: str = "modern_consulting",
    ) -> str:
        """Parses Mermaid code, calculates layout, and adds/updates the page."""
        parser = MermaidParser()
        layout = HierarchicalLayoutEngine()
        parsed = parser.parse(mermaid_code)
        laid_out = layout.compute_layout(parsed)
        return self.add_or_update_page(name=name, diagram=laid_out, page_id=page_id, theme=theme)

    def delete_page(self, name_or_index: Union[str, int]) -> bool:
        """Deletes a diagram page by name or index. Returns True if removed."""
        page = self.get_page(name_or_index)
        if page is not None:
            self.root.remove(page)
            return True
        return False

    def to_xml(self) -> str:
        """Serializes the entire multi-page document to formatted XML."""
        raw = ET.tostring(self.root, encoding="utf-8")
        parsed = minidom.parseString(raw)
        return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    def save(self, file_path: Optional[Union[str, Path]] = None) -> Path:
        """Saves the multi-page XML document to disk."""
        target_path = Path(file_path) if file_path else self.file_path
        if not target_path:
            raise ValueError("No file path specified for saving DrawIOProject")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(self.to_xml(), encoding="utf-8")
        self.file_path = target_path
        return target_path

    def export_page(
        self,
        name_or_index: Union[str, int],
        output_path: Union[str, Path],
        format: str = "png",
        scale: float = 3.0,
        theme: str = "modern_consulting",
        transparent: bool = False,
        canvas_bg: Optional[str] = None,
    ) -> Path:
        """
        Exports a single page tab to PNG or SVG.
        Uses native drawio CLI if installed (--page-index), or falls back to
        built-in mxgraph_to_ast -> DiagramRenderer.
        """
        page = self.get_page(name_or_index)
        if page is None:
            raise ValueError(f"Diagram page '{name_or_index}' not found in project")

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fmt = format.lower()

        diagrams = self.root.findall("diagram")
        page_idx = diagrams.index(page)

        # 1. Try native draw.io CLI if file exists on disk
        if self.file_path and self.file_path.exists():
            cli_success = self._try_cli_export(
                self.file_path, page_idx, out_p, fmt, scale, transparent=transparent
            )
            if cli_success:
                return out_p

        # 2. Built-in headless renderer fallback
        ast = mxgraph_to_ast(page)
        renderer = DiagramRenderer(theme_name=theme)
        svg_str = renderer.render_svg(ast, transparent=transparent, canvas_bg=canvas_bg)

        if fmt == "svg":
            out_p.write_text(svg_str, encoding="utf-8")
            return out_p
        elif fmt == "png":
            renderer.export_png(svg_str, out_p, scale=scale)
            return out_p
        else:
            raise ValueError(f"Unsupported export format: {format}. Use 'png' or 'svg'.")

    def _try_cli_export(
        self,
        drawio_path: Path,
        page_index: int,
        output_path: Path,
        fmt: str,
        scale: float,
        transparent: bool = False,
    ) -> bool:
        cli_candidates = [
            "drawio",
            "draw.io",
            "/Applications/draw.io.app/Contents/MacOS/draw.io",
        ]
        for cmd in cli_candidates:
            if shutil.which(cmd) or os.path.exists(cmd):
                try:
                    args = [
                        cmd,
                        "--export",
                        "--format",
                        fmt,
                        "--page-index",
                        str(page_index),
                        "--scale",
                        str(scale),
                        "--output",
                        str(output_path),
                    ]
                    if transparent:
                        args.append("--transparent")
                    args.append(str(drawio_path))

                    res = subprocess.run(
                        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12
                    )
                    if res.returncode == 0 and output_path.exists():
                        return True
                except Exception:
                    pass
        return False


