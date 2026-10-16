"""
Diagram Engine V2 - Draw.io XML Compiler
========================================
Compiles declarative DiagramSpec instances into standard Draw.io mxGraph XML (.drawio)
with high-fidelity styles, port anchoring, embedded vector icon data URIs,
container boundaries, and routed dataflow connectors.
"""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom

from src.ppt_engine.diagram_v2.models import (
    DiagramSpec,
    ContainerSpec,
    DeckHeaderContract,
    NodeSpec,
    FlowSpec,
    BadgeSpec,
    BulletListSpec,
    resolve_node_fonts,
)
from src.ppt_engine.diagram_v2.geometry import GeometryNormalizer, Box, Point


_MIME_BY_SUFFIX: Dict[str, str] = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _escape_attr(val: Optional[str]) -> str:
    """Escapes a string for safe inclusion inside a double-quoted XML attribute."""
    if not val:
        return ""
    return html.escape(str(val), quote=True)


def _escape_multiline_html(val: Optional[str]) -> str:
    """Escapes text for Draw.io HTML cell values while converting newlines to <br/>."""
    if not val:
        return ""
    return html.escape(str(val), quote=True).replace("\n", "&lt;br/&gt;")


class DrawIOCompiler:
    """Compiles a DiagramSpec into Draw.io mxGraph XML format."""

    _GLOBAL_ICON_CACHE: Dict[str, str] = {}

    def __init__(self, spec: DiagramSpec) -> None:
        self.spec = spec
        self.norm = GeometryNormalizer(
            canvas_width=spec.canvas.width,
            canvas_height=spec.canvas.height,
            canvas_unit=spec.canvas.unit,
        )
        self._icon_cache: Dict[str, str] = self._GLOBAL_ICON_CACHE
        self._node_boxes: Dict[str, Box] = {}
        self._container_boxes: Dict[str, Box] = {}
        self._used_cell_ids: set[str] = {"0", "1"}

    def _allocate_cell_id(self, preferred_id: str) -> str:
        """Ensures every mxCell receives a unique XML ID within the diagram."""
        base_id = (preferred_id or "cell").strip() or "cell"
        candidate = base_id
        counter = 2
        while candidate in self._used_cell_ids:
            candidate = f"{base_id}_{counter}"
            counter += 1
        self._used_cell_ids.add(candidate)
        return _escape_attr(candidate)

    def _resolve_icon_data_uri(self, icon_ref: Optional[str]) -> str:
        """Resolves an icon identifier or path to an embedded Base64 data URI."""
        if not icon_ref:
            return ""
        if icon_ref in self._icon_cache:
            return self._icon_cache[icon_ref]

        data_uri = ""
        resolved_path: Optional[Path] = None

        # 1. Direct path check
        p = Path(icon_ref)
        if p.exists() and p.is_file():
            resolved_path = p
        else:
            # 2. Check via central IconRegistry or AssetHarvester if available
            try:
                from src.ppt_engine.library_importer import IconRegistry
                resolved_path = IconRegistry.resolve_icon(icon_ref)
            except Exception:
                pass

        if resolved_path and resolved_path.exists():
            mime = _MIME_BY_SUFFIX.get(resolved_path.suffix.lower(), "image/png")
            b64_data = base64.b64encode(resolved_path.read_bytes()).decode("ascii")
            data_uri = f"data:{mime};base64,{b64_data}"

        self._icon_cache[icon_ref] = data_uri
        return data_uri

    def compile_xml(self) -> str:
        """Compiles the full Draw.io XML document string."""
        self._used_cell_ids = {"0", "1"}
        canvas_box = self.norm.to_pixels(0, 0, self.spec.canvas.width, self.spec.canvas.height)
        canvas_w = int(canvas_box.w)
        canvas_h = int(canvas_box.h)

        lines: List[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<mxfile host="Electron" agent="Enterprise Bench Diagram Engine V2" version="21.0.0" type="device">',
            f'  <diagram id="{_escape_attr(self.spec.id)}" name="{_escape_attr(self.spec.name)}">',
            f'    <mxGraphModel dx="{canvas_w}" dy="{canvas_h}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{canvas_w}" pageHeight="{canvas_h}" background="{_escape_attr(self.spec.canvas.background)}" math="0" shadow="0">',
            '      <root>',
            '        <mxCell id="0"/>',
            '        <mxCell id="1" parent="0"/>',
        ]

        # 1. Header & Title
        if self.spec.header.show:
            lines.extend(self._render_header_cells())

        # 2. Container Boundaries
        for c in self.spec.containers:
            lines.extend(self._render_container_cell(c))

        # 3. Entity Nodes & Cards
        for n in self.spec.nodes:
            lines.extend(self._render_node_cell(n))

        # 4. Standalone Badges
        for b in self.spec.badges:
            lines.extend(self._render_badge_cell(b))

        # 5. Bullet Lists
        for bl in self.spec.bullet_lists:
            lines.extend(self._render_bullet_list_cell(bl))

        # 6. Routed Connectors / Flows
        for f in self.spec.flows:
            lines.extend(self._render_flow_cell(f))

        lines.extend([
            '      </root>',
            '    </mxGraphModel>',
            '  </diagram>',
            '</mxfile>',
        ])

        compact_xml = "".join(line.strip() for line in lines)
        try:
            # Reformat XML cleanly without duplicating existing whitespace text nodes
            dom = minidom.parseString(compact_xml)
            return dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        except Exception:
            return "\n".join(lines)

    def _render_header_cells(self) -> List[str]:
        h = self.spec.header
        default_x = DeckHeaderContract.STRIPES_LEFT_IN if self.spec.canvas.unit == "in" else 57.6
        default_y = DeckHeaderContract.STRIPES_TOP_IN if self.spec.canvas.unit == "in" else 26.88
        hx = h.x if h.x is not None else default_x
        hy = h.y if h.y is not None else default_y
        box = self.norm.to_pixels(hx, hy, 4.0 if self.spec.canvas.unit == "in" else 350.0, 0.6 if self.spec.canvas.unit == "in" else 55.0)

        title_html = (
            f"&lt;b style=&quot;font-size:22px; color:#0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;&quot;&gt;"
            f"{_escape_multiline_html(h.action_title)}&lt;/b&gt;&lt;br/&gt;"
            f"&lt;span style=&quot;font-size:12px; color:#64748B;&quot;&gt;{_escape_multiline_html(h.subtitle)}&lt;/span&gt;"
        )
        cell_id = self._allocate_cell_id("header_title")

        return [
            f'        <mxCell id="{cell_id}" value="{title_html}" style="text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">',
            f'          <mxGeometry x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" as="geometry"/>',
            '        </mxCell>',
        ]

    def _render_container_cell(self, c: ContainerSpec) -> List[str]:
        box = self.norm.to_pixels(c.x, c.y, c.w, c.h)
        self._container_boxes[c.id] = box
        dashed_val = 1 if c.dashed else 0
        raw_op = c.fill_opacity * 100.0 if c.fill_opacity <= 1.0 else c.fill_opacity
        opacity_val = max(0, min(100, int(round(raw_op))))

        valign = c.resolved_vertical_align()
        align = c.resolved_align()

        if valign == "bottom":
            spacing_style = "verticalAlign=bottom;spacingBottom=12;spacingTop=0;"
        elif valign == "top":
            spacing_style = "verticalAlign=top;spacingTop=14;spacingBottom=0;"
        else:
            spacing_style = f"verticalAlign={_escape_attr(valign)};spacingTop=0;spacingBottom=0;"

        style = (
            f"rounded=1;arcSize={int(c.corner_radius)};whiteSpace=wrap;html=1;"
            f"dashed={dashed_val};dashPattern={_escape_attr(c.dash_pattern)};strokeColor={_escape_attr(c.border_hex)};"
            f"strokeWidth={c.stroke_width};fillColor={_escape_attr(c.fill_hex)};fillOpacity={opacity_val};"
            f"fontFamily=Helvetica, Arial, sans-serif;fontColor={_escape_attr(c.font_color)};fontSize={int(c.font_size)};"
            f"fontStyle=1;align={_escape_attr(align)};{spacing_style}spacingRight=18;"
        )

        label_escaped = _escape_multiline_html(c.label)
        cell_id = self._allocate_cell_id(c.id)
        return [
            f'        <mxCell id="{cell_id}" value="{label_escaped}" style="{style}" vertex="1" parent="1">',
            f'          <mxGeometry x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" as="geometry"/>',
            '        </mxCell>',
        ]

    def _render_node_cell(self, n: NodeSpec) -> List[str]:
        box = self.norm.to_pixels(n.x, n.y, n.w, n.h if n.h is not None else (1.2 if self.spec.canvas.unit == "in" else 100.0))
        self._node_boxes[n.id] = box

        # Build Rich HTML Content
        content_parts: List[str] = []

        # 1. Tech Logo or Emoji
        icon_data_uri = self._resolve_icon_data_uri(n.icon)
        if icon_data_uri:
            content_parts.append(
                f'&lt;div style=&quot;margin-bottom:6px;&quot;&gt;&lt;img src=&quot;{_escape_attr(icon_data_uri)}&quot; width=&quot;28&quot; height=&quot;28&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;/div&gt;'
            )
        elif n.icon_emoji:
            content_parts.append(f'&lt;div style=&quot;font-size:22px; margin-bottom:4px;&quot;&gt;{_escape_attr(n.icon_emoji)}&lt;/div&gt;')

        # 2. Kicker Pill Badge
        if n.kicker:
            kicker_bg = "#EDE9FE" if n.stroke_hex in ("#8B5CF6", "#7C3AED") else "#FEF3C7"
            content_parts.append(
                f'&lt;div style=&quot;font-size:9.5px; font-weight:800; color:{_escape_attr(n.stroke_hex)}; text-transform:uppercase; letter-spacing:0.5px; background:{kicker_bg}; display:inline-block; padding:2px 8px; border-radius:4px; margin-bottom:4px;&quot;&gt;{_escape_multiline_html(n.kicker)}&lt;/div&gt;'
            )

        # 3. Main Title
        w_in = box.w / 90.0
        h_in = box.h / 90.0
        t_pt, s_pt, sp_pt = resolve_node_fonts(n, w_in, h_in)
        content_parts.append(
            f'&lt;div style=&quot;font-size:{t_pt:.1f}px; font-weight:800; color:{_escape_attr(n.title_color)}; line-height:1.2;&quot;&gt;{_escape_multiline_html(n.title)}&lt;/div&gt;'
        )

        # 4. Subtitle and Bullets
        sub_items = []
        if n.subtitle:
            sub_items.extend(n.subtitle.split("\n"))
        if getattr(n, "bullets", None):
            for b in n.bullets:
                b_s = str(b)
                sub_items.append(b_s if b_s.startswith("•") else f"• {b_s}")
        if sub_items:
            sub_escaped = _escape_multiline_html("\n".join(sub_items))
            content_parts.append(
                f'&lt;div style=&quot;font-size:{s_pt:.1f}px; color:{_escape_attr(n.subtitle_color)}; margin-top:{sp_pt:.1f}px; line-height:1.2;&quot;&gt;{sub_escaped}&lt;/div&gt;'
            )

        value_html = "".join(content_parts)

        # Determine Draw.io shape style
        shadow_val = 1 if n.shadow else 0
        fill_hex = _escape_attr(n.fill_hex)
        stroke_hex = _escape_attr(n.stroke_hex)
        if n.is_cylinder or n.shape in ("cylinder", "database"):
            style = (
                f"shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=14;"
                f"fillColor={fill_hex};strokeColor={stroke_hex};strokeWidth={n.stroke_width};shadow={shadow_val};"
                f"fontFamily=Helvetica, Arial, sans-serif;align=center;verticalAlign=middle;"
            )
        elif n.shape == "rect" or not n.is_rounded:
            style = (
                f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill_hex};strokeColor={stroke_hex};"
                f"strokeWidth={n.stroke_width};shadow={shadow_val};fontFamily=Helvetica, Arial, sans-serif;"
                f"align=center;verticalAlign=middle;"
            )
        else:
            style = (
                f"rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor={fill_hex};strokeColor={stroke_hex};"
                f"strokeWidth={n.stroke_width};shadow={shadow_val};fontFamily=Helvetica, Arial, sans-serif;"
                f"align=center;verticalAlign=middle;"
            )

        cell_id = self._allocate_cell_id(n.id)
        return [
            f'        <mxCell id="{cell_id}" value="{value_html}" style="{style}" vertex="1" parent="1">',
            f'          <mxGeometry x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" as="geometry"/>',
            '        </mxCell>',
        ]

    def _render_badge_cell(self, b: BadgeSpec) -> List[str]:
        box = self.norm.to_pixels(b.x, b.y, b.w, b.h)
        style = (
            f"rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor={_escape_attr(b.bg_hex)};strokeColor={_escape_attr(b.border_hex)};"
            f"strokeWidth=1;fontColor={_escape_attr(b.text_hex)};fontFamily=Helvetica, Arial, sans-serif;fontSize={int(b.font_pt)};"
            f"fontStyle=1;align=center;verticalAlign=middle;"
        )
        cell_id = self._allocate_cell_id(b.id or f"badge_{int(box.x)}_{int(box.y)}")
        return [
            f'        <mxCell id="{cell_id}" value="{_escape_multiline_html(b.text)}" style="{style}" vertex="1" parent="1">',
            f'          <mxGeometry x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" as="geometry"/>',
            '        </mxCell>',
        ]

    def _render_bullet_list_cell(self, bl: BulletListSpec) -> List[str]:
        box = self.norm.to_pixels(bl.x, bl.y, bl.w, bl.h)
        bullet_html = "".join([f"&lt;div style=&quot;margin-bottom:4px;&quot;&gt;• {_escape_multiline_html(item)}&lt;/div&gt;" for item in bl.items])
        style = (
            f"text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;"
            f"fontFamily=Helvetica, Arial, sans-serif;fontSize={int(bl.font_size)};fontColor={_escape_attr(bl.font_color)};fontStyle=1;"
        )
        cell_id = self._allocate_cell_id(bl.id or f"bl_{int(box.x)}_{int(box.y)}")
        return [
            f'        <mxCell id="{cell_id}" value="{bullet_html}" style="{style}" vertex="1" parent="1">',
            f'          <mxGeometry x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" as="geometry"/>',
            '        </mxCell>',
        ]

    def _render_flow_cell(self, f: FlowSpec) -> List[str]:
        # Pre-convert all points to pixel coordinates once
        all_boxes = {**self._container_boxes, **self._node_boxes}
        if f.points:
            pts_px = [self.norm.point_to_pixels(pt) for pt in f.points]
        elif f.source and f.target and f.source in all_boxes and f.target in all_boxes:
            src_box = all_boxes[f.source]
            tgt_box = all_boxes[f.target]
            auto_pts = GeometryNormalizer.compute_auto_route(
                src_box,
                tgt_box,
                curve=f.curve,
                src_port=f.source_port,
                tgt_port=f.target_port,
            )
            pts_px = [self.norm.point_to_pixels(pt) for pt in auto_pts]
        else:
            pts_px = []

        # Edge Style configuration
        dashed_attr = "dashed=1;dashPattern=5 3;" if f.dashed else ""
        curve_attr = "edgeStyle=straight;"
        if f.curve == "curved":
            curve_attr = "edgeStyle=curvedEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
        elif f.curve == "orthogonal" and len(pts_px) > 2:
            curve_attr = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"

        # Port attachment
        src_id = f.source or ""
        tgt_id = f.target or ""

        # Compute explicit docking ports (exitX, exitY, entryX, entryY)
        port_style = ""
        if len(pts_px) >= 2:
            p_start = pts_px[0]
            p_end = pts_px[-1]
            src_box = self._node_boxes.get(src_id) or self._container_boxes.get(src_id)
            if src_box:
                exit_x = max(0.0, min(1.0, (p_start[0] - src_box.x) / max(1.0, src_box.w)))
                exit_y = max(0.0, min(1.0, (p_start[1] - src_box.y) / max(1.0, src_box.h)))
                port_style += f"exitX={exit_x:.2f};exitY={exit_y:.2f};"
            tgt_box = self._node_boxes.get(tgt_id) or self._container_boxes.get(tgt_id)
            if tgt_box:
                entry_x = max(0.0, min(1.0, (p_end[0] - tgt_box.x) / max(1.0, tgt_box.w)))
                entry_y = max(0.0, min(1.0, (p_end[1] - tgt_box.y) / max(1.0, tgt_box.h)))
                port_style += f"entryX={entry_x:.2f};entryY={entry_y:.2f};"

        label_style = ""
        offset_xml = ""
        if f.label:
            border = _escape_attr(f.label_border_hex or f.stroke_hex)
            label_style = f"labelBackgroundColor={_escape_attr(f.label_bg_hex)};labelBorderColor={border};"

            # Determine offset
            off_x, off_y = 0, 0
            pos = f.label_position
            if pos == "auto":
                if len(pts_px) >= 2:
                    p1_px = pts_px[0]
                    p2_px = pts_px[-1]
                    is_h = abs(p2_px[1] - p1_px[1]) < 10.0
                    if is_h:
                        pos = "above" if p2_px[0] > p1_px[0] else "below"
                    else:
                        pos = "side"
                else:
                    pos = "above"

            if pos == "above":
                off_y = -12
            elif pos == "below":
                off_y = 12
            elif pos in ("side", "right"):
                off_x = 24
            elif pos == "left":
                off_x = -24

            if f.label_at and len(pts_px) >= 2:
                lx, ly = self.norm.point_to_pixels(f.label_at)
                mid_x = (pts_px[0][0] + pts_px[-1][0]) / 2.0
                mid_y = (pts_px[0][1] + pts_px[-1][1]) / 2.0
                offset_xml = f'            <mxPoint x="{lx - mid_x:.1f}" y="{ly - mid_y:.1f}" as="offset"/>'
            elif off_x != 0 or off_y != 0:
                offset_xml = f'            <mxPoint x="{off_x}" y="{off_y}" as="offset"/>'

        font_sz_str = f"{f.font_pt:.1f}" if f.font_pt % 1 else f"{int(f.font_pt)}"
        style = (
            f"{curve_attr}html=1;endArrow=block;endFill=1;strokeColor={_escape_attr(f.stroke_hex)};strokeWidth={f.stroke_width};"
            f"fontColor={_escape_attr(f.label_text_hex)};fontFamily=Helvetica, Arial, sans-serif;fontSize={font_sz_str};fontStyle=1;{label_style}{dashed_attr}{port_style}"
        )

        # Endpoint geometry fallback for unanchored edges + waypoints
        geom_children: List[str] = []
        if not src_id and len(pts_px) >= 1:
            geom_children.append(f'            <mxPoint x="{pts_px[0][0]:.1f}" y="{pts_px[0][1]:.1f}" as="sourcePoint"/>')
        if not tgt_id and len(pts_px) >= 2:
            geom_children.append(f'            <mxPoint x="{pts_px[-1][0]:.1f}" y="{pts_px[-1][1]:.1f}" as="targetPoint"/>')

        if len(pts_px) > 2:
            geom_children.append('          <Array as="points">')
            for pt in pts_px[1:-1]:
                geom_children.append(f'            <mxPoint x="{pt[0]:.1f}" y="{pt[1]:.1f}"/>')
            geom_children.append('          </Array>')
        elif len(pts_px) == 2 and f.curve == "curved":
            # Add curved intermediate point
            p1, p2 = pts_px[0], pts_px[1]
            mx = (p1[0] + p2[0]) / 2.0
            geom_children.append('          <Array as="points">')
            geom_children.append(f'            <mxPoint x="{mx:.1f}" y="{p1[1]:.1f}"/>')
            geom_children.append('          </Array>')

        label_val = _escape_multiline_html(f.label) if f.label else ""
        flow_id = self._allocate_cell_id(f.id or f"edge_{src_id}_to_{tgt_id}")

        source_attr = f' source="{_escape_attr(src_id)}"' if src_id else ''
        target_attr = f' target="{_escape_attr(tgt_id)}"' if tgt_id else ''

        res = [
            f'        <mxCell id="{flow_id}" value="{label_val}" style="{style}" edge="1" parent="1"{source_attr}{target_attr}>',
            '          <mxGeometry relative="1" as="geometry">',
        ]
        if offset_xml:
            res.append(offset_xml)
        res.extend(geom_children)
        res.append('          </mxGeometry>')
        res.append('        </mxCell>')
        return res

