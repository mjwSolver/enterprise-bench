"""
Diagram Engine V2 - High-Fidelity Vector SVG Compiler
=====================================================
Compiles declarative DiagramSpec instances into standalone, publication-grade
vector SVG files featuring drop shadows, brand accent stripes, container boundaries,
3D database cylinders, official tech logos, and routed directional flow connectors.
"""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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


class SVGCompiler:
    """Compiles a DiagramSpec into a standalone high-fidelity SVG string."""

    def __init__(self, spec: DiagramSpec) -> None:
        self.spec = spec
        self.norm = GeometryNormalizer(
            canvas_width=spec.canvas.width,
            canvas_height=spec.canvas.height,
            canvas_unit=spec.canvas.unit,
        )
        self._used_colors: Set[str] = set()
        self._icon_cache: Dict[str, str] = {}
        self._node_boxes: Dict[str, Box] = {}
        self._container_boxes: Dict[str, Box] = {}

    def _clean_color_id(self, hex_color: Optional[str]) -> str:
        """Converts a hex color code to a safe XML identifier (e.g. '#2563EB' -> '2563eb')."""
        if not hex_color:
            return "000000"
        cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(hex_color)).lower()
        return cleaned or "000000"

    def _resolve_icon_data_uri(self, icon_ref: Optional[str]) -> str:
        """Resolves an icon identifier or path to an embedded Base64 data URI."""
        if not icon_ref:
            return ""
        if icon_ref in self._icon_cache:
            return self._icon_cache[icon_ref]

        data_uri = ""
        resolved_path: Optional[Path] = None

        p = Path(icon_ref)
        if p.exists() and p.is_file():
            resolved_path = p
        else:
            try:
                from src.ppt_engine.library_importer import IconRegistry
                resolved_path = IconRegistry.resolve_icon(icon_ref)
            except Exception:
                pass

        if resolved_path and resolved_path.exists():
            mime = "image/svg+xml" if resolved_path.suffix.lower() == ".svg" else "image/png"
            b64_data = base64.b64encode(resolved_path.read_bytes()).decode("ascii")
            data_uri = f"data:{mime};base64,{b64_data}"

        self._icon_cache[icon_ref] = data_uri
        return data_uri

    def compile_svg(self) -> str:
        """Compiles the full high-fidelity SVG string."""
        canvas_box = self.norm.to_pixels(0, 0, self.spec.canvas.width, self.spec.canvas.height)
        cw = int(canvas_box.w)
        ch = int(canvas_box.h)

        # Collect all stroke colors from flows to generate arrowhead markers
        for f in self.spec.flows:
            self._used_colors.add(f.stroke_hex)

        parts: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}">',
            self._render_defs(),
            self._render_canvas_background(cw, ch),
        ]

        # 1. Header
        if self.spec.header.show:
            parts.append(self._render_header())

        # 2. Containers / Boundaries
        for c in self.spec.containers:
            parts.append(self._render_container(c))

        # 3. Entity Nodes & Cards
        for n in self.spec.nodes:
            parts.append(self._render_node(n))

        # 4. Badges & Warning Pills
        for b in self.spec.badges:
            parts.append(self._render_badge(b))

        # 5. Bullet Lists
        for bl in self.spec.bullet_lists:
            parts.append(self._render_bullet_list(bl))

        # 6. Routed Connectors / Flows
        for f in self.spec.flows:
            parts.append(self._render_flow(f))

        parts.append('</svg>')
        return "\n".join(parts)

    def _render_defs(self) -> str:
        lines: List[str] = [
            '  <defs>',
            '    <!-- Drop Shadows -->',
            '    <filter id="shadow" x="-10%" y="-10%" width="125%" height="130%">',
            '      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.08"/>',
            '    </filter>',
            '    <filter id="card-shadow" x="-8%" y="-8%" width="120%" height="125%">',
            '      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#0F172A" flood-opacity="0.06"/>',
            '    </filter>',
            '    <!-- Arrowhead Markers -->',
        ]

        # Common fallback colors + dynamically requested flow colors
        all_colors = {"#2563EB", "#7C3AED", "#D97706", "#10B981", "#EF4444", "#0284C7", "#94A3B8"} | self._used_colors
        for c in sorted(all_colors):
            cid = self._clean_color_id(c)
            lines.append(
                f'    <marker id="arrow-{cid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="{c}"/></marker>'
            )

        lines.append('  </defs>')
        return "\n".join(lines)

    def _render_canvas_background(self, cw: int, ch: int) -> str:
        lines: List[str] = [
            f'  <!-- Clean Canvas Background -->',
            f'  <rect width="{cw}" height="{ch}" fill="{self.spec.canvas.background}"/>',
        ]
        if self.spec.canvas.show_grid:
            lines.append(f'  <rect width="{cw}" height="{ch}" fill="#F8FAFC" opacity="0.45"/>')
            lines.append(f'  <!-- Subtle Blueprint Grid Pattern -->')
            lines.append(f'  <g stroke="{self.spec.canvas.grid_color}" stroke-width="0.75" opacity="{self.spec.canvas.grid_opacity}">')
            sp = max(10, int(self.spec.canvas.grid_spacing or 45))
            # Horizontal lines
            h_lines = " ".join([f"M 0 {y} L {cw} {y}" for y in range(sp, ch, sp)])
            lines.append(f'    <path d="{h_lines}" />')
            # Vertical lines
            v_lines = " ".join([f"M {x} 0 L {x} {ch}" for x in range(sp, cw, sp)])
            lines.append(f'    <path d="{v_lines}" />')
            lines.append('  </g>')
        return "\n".join(lines)

    def _render_header(self) -> str:
        h = self.spec.header
        canvas_unit = (self.spec.canvas.unit or "in").lower().strip()
        default_x = DeckHeaderContract.STRIPES_LEFT_IN if canvas_unit == "in" else 57.6
        default_y = DeckHeaderContract.STRIPES_TOP_IN if canvas_unit == "in" else 26.88
        hx = h.x if h.x is not None else default_x
        hy = h.y if h.y is not None else default_y
        box = self.norm.to_pixels(hx, hy, 1.0, 1.0)

        stripe_h = 52.8
        stripe_red_w = 4.32
        stripe_gap = 1.92
        stripe_blue_w = 8.64

        lines: List[str] = [
            '  <!-- ================= HEADER SECTION ================= -->',
        ]
        if h.brand_stripes:
            lines.append(f'  <!-- Brand Stripes (1 Red : 2 Blue Ratio) -->')
            lines.append(f'  <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{stripe_red_w:.1f}" height="{stripe_h:.1f}" fill="{h.red_hex}" rx="1"/>')
            lines.append(f'  <rect x="{box.x + stripe_red_w + stripe_gap:.1f}" y="{box.y:.1f}" width="{stripe_blue_w:.1f}" height="{stripe_h:.1f}" fill="{h.blue_hex}" rx="1"/>')
            tx = box.x + 24.0
        else:
            tx = box.x

        lines.extend([
            f'  <text x="{tx:.1f}" y="{box.y + 20.0:.1f}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif" font-size="22" font-weight="800" fill="#0F172A">{html.escape(h.action_title)}</text>',
            f'  <text x="{tx:.1f}" y="{box.y + 40.0:.1f}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="500" fill="#64748B">{html.escape(h.subtitle)}</text>',
        ])
        return "\n".join(lines)

    def _render_container(self, c: ContainerSpec) -> str:
        box = self.norm.to_pixels(c.x, c.y, c.w, c.h)
        self._container_boxes[c.id] = box
        dash_attr = f' stroke-dasharray="{c.dash_pattern.replace(" ", ",")}"' if c.dashed else ''

        lines: List[str] = [
            f'  <!-- Container Boundary: {html.escape(c.label)} -->',
            '  <g>',
            f'    <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{c.corner_radius:.1f}" fill="{c.fill_hex}" fill-opacity="{c.fill_opacity}" stroke="{c.border_hex}" stroke-width="{c.stroke_width}"{dash_attr}/>',
        ]

        valign = c.resolved_vertical_align()
        align = c.resolved_align()

        # Container Label
        anchor = "middle" if align == "center" else ("start" if align == "left" else "end")
        lx = box.cx if align == "center" else (box.x + 20.0 if align == "left" else box.x2 - 20.0)
        ly = box.y + 24.0 if valign == "top" else box.y2 - 16.0
        lines.append(
            f'    <text x="{lx:.1f}" y="{ly:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{c.font_size:.1f}" font-weight="700" fill="{c.font_color}" text-anchor="{anchor}" letter-spacing="0.5">{html.escape(c.label.upper())}</text>'
        )

        # Optional Top-Right Tag Badge (e.g. AWS CLOUD) - decoupled at box.y + 12.0
        if c.tag_badge:
            bw = max(98.0, len(c.tag_badge) * 8.5 + 24.0)
            bh = 24.0
            bx = box.x2 - bw - 15.0
            by = box.y + 12.0
            lines.extend([
                f'    <g transform="translate({bx:.1f}, {by:.1f})">',
                f'      <rect width="{bw:.1f}" height="{bh:.1f}" rx="5" fill="{c.tag_bg_hex}" stroke="{c.border_hex}" stroke-width="1"/>',
                f'      <text x="{bw/2.0:.1f}" y="16" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="800" fill="{c.tag_text_hex}" text-anchor="middle" letter-spacing="0.5">{html.escape(c.tag_badge.upper())}</text>',
                '    </g>',
            ])

        lines.append('  </g>')
        return "\n".join(lines)

    def _render_node(self, n: NodeSpec) -> str:
        box = self.norm.to_pixels(n.x, n.y, n.w, n.h if n.h is not None else (1.2 if self.spec.canvas.unit == "in" else 100.0))
        self._node_boxes[n.id] = box
        icon_data_uri = self._resolve_icon_data_uri(n.icon)

        lines: List[str] = [
            f'  <!-- Node Card: {html.escape(n.title)} -->',
        ]

        if n.is_cylinder or n.shape in ("cylinder", "database"):
            # 3D Seamless Cylinder
            rim_h = 15.0
            lines.extend([
                '  <g filter="url(#shadow)">',
                f'    <path d="M {box.x:.1f} {box.y + rim_h:.1f} L {box.x:.1f} {box.y2 - rim_h:.1f} A {box.w/2.0:.1f} {rim_h:.1f} 0 0 0 {box.x2:.1f} {box.y2 - rim_h:.1f} L {box.x2:.1f} {box.y + rim_h:.1f} Z" fill="{n.fill_hex}" stroke="{n.stroke_hex}" stroke-width="{n.stroke_width}"/>',
                f'    <ellipse cx="{box.cx:.1f}" cy="{box.y + rim_h:.1f}" rx="{box.w/2.0:.1f}" ry="{rim_h:.1f}" fill="#E0F2FE" stroke="{n.stroke_hex}" stroke-width="{n.stroke_width}"/>',
                f'    <path d="M {box.x:.1f} {box.y2 - rim_h:.1f} A {box.w/2.0:.1f} {rim_h:.1f} 0 0 0 {box.x2:.1f} {box.y2 - rim_h:.1f}" fill="none" stroke="{n.stroke_hex}" stroke-width="{n.stroke_width}"/>',
            ])
            # Side-slot or Centered Icon & Typography inside cylinder body
            body_cy = box.y + rim_h + (box.h - rim_h) / 2.0
            if icon_data_uri:
                lines.append(f'    <image href="{icon_data_uri}" x="{box.x + 20.0:.1f}" y="{body_cy - 16.0:.1f}" width="28" height="28"/>')
                tx = box.x + 56.0
                anchor = "start"
            else:
                tx = box.cx
                anchor = "middle"

            w_in = box.w / 90.0
            h_in = box.h / 90.0
            cyl_title_pt, cyl_font_size, cyl_sp = resolve_node_fonts(n, w_in, h_in)
            lines.append(f'    <text x="{tx:.1f}" y="{body_cy - 2.0:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{cyl_title_pt:.1f}" font-weight="800" fill="{n.title_color}" text-anchor="{anchor}">{html.escape(n.title)}</text>')
            cyl_raw_bullets = [str(b).strip() for b in (getattr(n, "bullets", None) or []) if str(b).strip()]
            cyl_subs = ([s.strip() for s in n.subtitle.split("\n") if s.strip()] if n.subtitle else []) + cyl_raw_bullets
            if cyl_subs:
                cyl_y = body_cy + 13.0
                for csl in cyl_subs:
                    csl_text = csl if (csl.startswith("•") or not cyl_raw_bullets) else f"• {csl}"
                    lines.append(f'    <text x="{tx:.1f}" y="{cyl_y:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{cyl_font_size:.1f}" font-weight="600" fill="{n.subtitle_color}" text-anchor="{anchor}">{html.escape(csl_text)}</text>')
                    cyl_y += (cyl_font_size * 1.30)
            lines.append('  </g>')
            return "\n".join(lines)

        # Regular Rectangular or Rounded Card
        filter_str = ' filter="url(#card-shadow)"' if n.shadow else ''
        rx_val = 14.0 if n.is_rounded else 0.0

        lines.extend([
            f'  <g{filter_str}>',
            f'    <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="{rx_val:.1f}" fill="{n.fill_hex}" stroke="{n.stroke_hex}" stroke-width="{n.stroke_width}"/>',
        ])

        # Optical vertical centering
        has_kicker = bool(n.kicker)
        has_svg_icon = bool(icon_data_uri)
        has_emoji = bool(n.icon_emoji) and not has_svg_icon
        w_in = box.w / 90.0
        h_in = box.h / 90.0
        t_pt, resolved_sub_pt, sp_pt = resolve_node_fonts(n, w_in, h_in)
        raw_bullets = [str(b).strip() for b in (getattr(n, "bullets", None) or []) if str(b).strip()]
        sub_lines = ([s for s in n.subtitle.split("\n") if s.strip()] if n.subtitle else []) + raw_bullets

        is_side_icon = (getattr(n, "icon_layout", "auto") == "side") and has_svg_icon
        kicker_h = 24.0 if has_kicker else 0.0
        icon_h = 0.0 if is_side_icon else (40.0 if has_svg_icon else (34.0 if has_emoji else 0.0))
        title_h = t_pt + 4.0
        sub_h = len(sub_lines) * (resolved_sub_pt * 1.20 + sp_pt * 90.0 / 72.0) if sub_lines else 0.0
        total_content_h = kicker_h + icon_h + title_h + sub_h

        # Vertical alignment
        if n.valign == "top":
            cur_y = box.y + 18.0
        elif n.valign == "bottom":
            cur_y = box.y2 - total_content_h - 18.0
        else:
            cur_y = box.y + max(8.0, (box.h - total_content_h) / 2.0)

        # Kicker Pill Badge
        if has_kicker:
            kw, kh = 90.0, 18.0
            kx = box.cx - kw / 2.0
            kicker_bg = "#EDE9FE" if n.stroke_hex in ("#8B5CF6", "#7C3AED") else ("#FEE2E2" if n.stroke_hex in ("#EF4444", "#DC2626") else "#FEF3C7")
            lines.extend([
                f'    <g transform="translate({kx:.1f}, {cur_y:.1f})">',
                f'      <rect width="{kw}" height="{kh}" rx="4" fill="{kicker_bg}"/>',
                f'      <text x="{kw/2.0:.1f}" y="13" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="800" fill="{n.stroke_hex}" text-anchor="middle" letter-spacing="0.5">{html.escape(n.kicker).upper()}</text>',
                '    </g>',
            ])
            cur_y += kicker_h

        # Tech Icon or Emoji
        if is_side_icon:
            isize = min(26.0, max(18.0, box.h - 14.0))
            iy = box.cy - isize / 2.0
            lines.append(f'    <image href="{icon_data_uri}" x="{box.x + 14.0:.1f}" y="{iy:.1f}" width="{isize:.1f}" height="{isize:.1f}"/>')
        elif has_svg_icon:
            lines.append(f'    <image href="{icon_data_uri}" x="{box.cx - 15.0:.1f}" y="{cur_y:.1f}" width="30" height="30"/>')
            cur_y += icon_h
        elif has_emoji:
            lines.append(f'    <text x="{box.cx:.1f}" y="{cur_y + 22.0:.1f}" font-size="22" text-anchor="middle">{n.icon_emoji}</text>')
            cur_y += icon_h

        # Title
        if is_side_icon:
            isize = min(26.0, max(18.0, box.h - 14.0))
            t_align = "start"
            t_x = box.x + 14.0 + isize + 10.0
        else:
            t_align = "start" if getattr(n, "align", "center") == "left" else "middle"
            t_x = (box.x + 16.0) if t_align == "start" else box.cx
        lines.append(f'    <text x="{t_x:.1f}" y="{cur_y + t_pt:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{t_pt:.1f}" font-weight="800" fill="{n.title_color}" text-anchor="{t_align}">{html.escape(n.title)}</text>')
        cur_y += title_h

        # Subtitle
        sub_font_size = resolved_sub_pt
        has_bullets = any(sl.strip().startswith("•") for sl in sub_lines) or bool(getattr(n, "bullets", None))
        if is_side_icon:
            default_sub_x = t_x
            default_sub_align = "start"
        elif getattr(n, "align", "center") == "center" and has_bullets:
            max_bw_px = max(
                (len(sl if (sl.strip().startswith("•") or not getattr(n, "bullets", None)) else f"• {sl}") * sub_font_size * 0.52 for sl in sub_lines),
                default=0.0,
            )
            default_sub_x = box.cx - max_bw_px / 2.0
            default_sub_align = "start"
        elif getattr(n, "align", "center") == "center":
            default_sub_x = box.cx
            default_sub_align = "middle"
        elif getattr(n, "align", "center") == "left" or has_bullets:
            default_sub_x = box.x + 12.0
            default_sub_align = "start"
        else:
            default_sub_x = box.cx
            default_sub_align = "middle"

        for sl in sub_lines:
            cur_y += max(12.0, sub_font_size * 1.20 + sp_pt * 90.0 / 72.0)
            sl_text = sl if (sl.strip().startswith("•") or not getattr(n, "bullets", None)) else f"• {sl}"
            lines.append(f'    <text x="{default_sub_x:.1f}" y="{cur_y:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{sub_font_size:.1f}" font-weight="600" fill="{n.subtitle_color}" text-anchor="{default_sub_align}">{html.escape(sl_text)}</text>')

        lines.append('  </g>')
        return "\n".join(lines)

    def _render_badge(self, b: BadgeSpec) -> str:
        box = self.norm.to_pixels(b.x, b.y, b.w, b.h)
        lines = [
            f'  <g filter="url(#card-shadow)">',
            f'    <rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="5" fill="{b.bg_hex}" stroke="{b.border_hex}" stroke-width="1"/>',
            f'    <text x="{box.cx:.1f}" y="{box.cy + 4.0:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{b.font_pt:.1f}" font-weight="800" fill="{b.text_hex}" text-anchor="middle">{html.escape(b.text)}</text>',
            '  </g>',
        ]
        return "\n".join(lines)

    def _render_bullet_list(self, bl: BulletListSpec) -> str:
        box = self.norm.to_pixels(bl.x, bl.y, bl.w, bl.h)
        lines = [
            '  <g>',
            f'    <text x="{box.x:.1f}" y="{box.y + 16.0:.1f}" font-family="Helvetica, Arial, sans-serif" font-size="{bl.font_size:.1f}" font-weight="700" fill="{bl.font_color}">',
        ]
        for i, item in enumerate(bl.items):
            dy_attr = f' dy="20"' if i > 0 else ''
            lines.append(f'      <tspan x="{box.x:.1f}"{dy_attr}>• {html.escape(item)}</tspan>')
        lines.extend([
            '    </text>',
            '  </g>',
        ])
        return "\n".join(lines)

    def _render_flow(self, f: FlowSpec) -> str:
        pts: List[Point] = []
        all_boxes = {**self._container_boxes, **self._node_boxes}
        if f.points:
            pts = [self.norm.point_to_pixels(p) for p in f.points if len(p) >= 2]
        elif f.source and f.target and f.source in all_boxes and f.target in all_boxes:
            src_box = all_boxes[f.source]
            tgt_box = all_boxes[f.target]
            pts = GeometryNormalizer.compute_auto_route(
                src_box,
                tgt_box,
                curve=f.curve,
                src_port=f.source_port,
                tgt_port=f.target_port,
            )

        if len(pts) < 2:
            return ""

        cid = self._clean_color_id(f.stroke_hex)
        marker_attr = f' marker-end="url(#arrow-{cid})"' if f.has_arrow else ''
        dash_attr = ' stroke-dasharray="5,3"' if f.dashed else ''

        lines: List[str] = [
            f'  <!-- Flow Connector: {html.escape(f.label or "flow")} -->',
        ]

        # Build path string
        if len(pts) == 2 and f.curve == "curved":
            # Cubic bezier curve
            p1, p2 = pts[0], pts[1]
            cx1 = p1[0] + (p2[0] - p1[0]) * 0.5
            cy1 = p1[1]
            cx2 = p1[0] + (p2[0] - p1[0]) * 0.5
            cy2 = p2[1]
            d = f"M {p1[0]:.1f} {p1[1]:.1f} C {cx1:.1f} {cy1:.1f}, {cx2:.1f} {cy2:.1f}, {p2[0]:.1f} {p2[1]:.1f}"
        else:
            # Polyline orthogonal or straight
            d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join([f"L {p[0]:.1f} {p[1]:.1f}" for p in pts[1:]])

        lines.append(
            f'  <path d="{d}" fill="none" stroke="{f.stroke_hex}" stroke-width="{f.stroke_width}"{dash_attr}{marker_attr}/>'
        )

        # Flow Label Pill
        if f.label:
            segs = list(zip(pts, pts[1:]))
            best_seg = max(segs, key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
            p1, p2 = best_seg
            is_horiz = abs(p2[1] - p1[1]) < 5.0
            is_vert = abs(p2[0] - p1[0]) < 5.0

            if f.label_at:
                lx, ly = self.norm.point_to_pixels(f.label_at)
            else:
                lx = (best_seg[0][0] + best_seg[1][0]) / 2.0
                ly = (best_seg[0][1] + best_seg[1][1]) / 2.0
                pos = f.label_position
                if pos == "auto":
                    if is_horiz:
                        pos = "above" if p2[0] > p1[0] else "below"
                    elif is_vert:
                        pos = "side"
                    else:
                        pos = "above"

                offset_px = f.label_offset * self.norm.scale_to_px_y if f.label_offset is not None else 14.0

                if pos == "above":
                    ly -= offset_px
                elif pos == "below":
                    ly += offset_px
                elif pos in ("side", "right"):
                    lx += (offset_px * 2.5)
                elif pos == "left":
                    lx -= (offset_px * 2.5)

            font_pt = f.font_pt or 9.0
            label_lines = f.label.split("\n")
            max_chars = max((len(seg) for seg in label_lines), default=0)
            text_w = max_chars * font_pt * 0.55
            lw = max(48.0, text_w + 14.0)
            lh = max(18.0, len(label_lines) * (font_pt * 1.35) + 6.0)
            border = f.label_border_hex or f.stroke_hex

            text_tspans = []
            line_height = font_pt * 1.25
            first_y = ly - ((len(label_lines) - 1) * line_height) / 2.0 + 3.5
            for idx, seg in enumerate(label_lines):
                seg_y = first_y + idx * line_height
                text_tspans.append(
                    f'<tspan x="{lx:.1f}" y="{seg_y:.1f}">{html.escape(seg)}</tspan>'
                )

            lines.extend([
                f'  <g filter="url(#card-shadow)">',
                f'    <rect x="{lx - lw/2.0:.1f}" y="{ly - lh/2.0:.1f}" width="{lw:.1f}" height="{lh:.1f}" rx="4" fill="{f.label_bg_hex}" stroke="{border}" stroke-width="1"/>',
                f'    <text font-family="Helvetica, Arial, sans-serif" font-size="{font_pt:.1f}" font-weight="700" fill="{f.label_text_hex}" text-anchor="middle">{"".join(text_tspans)}</text>',
                '  </g>',
            ])

        return "\n".join(lines)
