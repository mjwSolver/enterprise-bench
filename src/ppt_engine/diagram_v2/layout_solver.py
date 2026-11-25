"""
Diagram Engine V2 - 2D Constraint & Flexbox Auto-Layout Solver
==============================================================
Computes collision-free bounding boxes (`x, y, w, h`) for declarative
DiagramSpec topologies when explicit coordinates are omitted or `box: auto`
is specified. Enforces >= 14pt clearance halos, container padding,
corridor spans for labeled connectors, and 0.05" grid snapping.
"""

from __future__ import annotations

import math
from collections import deque
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from src.ppt_engine.diagram_v2.models import (
        ContainerSpec,
        DiagramSpec,
        FlowSpec,
        NodeSpec,
    )

CANVAS_MARGIN_X: float = 0.45
CANVAS_MARGIN_BOTTOM: float = 0.35
CANVAS_TOP_Y: float = 1.35
DEFAULT_CANVAS_W: float = 13.333
DEFAULT_CANVAS_H: float = 7.50
PX_PER_INCH: float = 90.0
MIN_HALO_IN: float = 0.22
CONTAINER_LABEL_BAND_IN: float = 0.42
SNAP_GRID_IN: float = 0.05

_ARIAL_EM_REGULAR: float = 0.52
_ARIAL_EM_BOLD: float = 0.57


def _snap(val: float) -> float:
    """Snap coordinate or dimension to 0.05 inch grid increments."""
    return round(round(val / SNAP_GRID_IN) * SNAP_GRID_IN, 3)


def _snap_floor(val: float) -> float:
    """Snap coordinate or dimension downward to 0.05 inch grid increments."""
    return round(math.floor((val + 1e-9) / SNAP_GRID_IN) * SNAP_GRID_IN, 3)


def _snap_ceil(val: float) -> float:
    """Snap coordinate or dimension upward to 0.05 inch grid increments."""
    return round(math.ceil((val - 1e-9) / SNAP_GRID_IN) * SNAP_GRID_IN, 3)


def _fit_snap_dim(val: float, max_avail: float, floor_in: float = 0.05) -> float:
    """Snap dimension without ever exceeding `max_avail`."""
    avail = max(0.02, max_avail)
    target = min(val, avail)
    if target >= floor_in:
        snapped = _snap(target)
        if snapped > avail + 1e-6:
            snapped = _snap_floor(avail)
        return max(floor_in if avail >= floor_in else 0.02, snapped)
    return round(target, 3)


def _to_inches_spacing(val: float, pt_threshold: float = 3.0) -> float:
    """Convert spacing value: values > 3.0 are treated as points, else inches."""
    if val > pt_threshold:
        return float(val) / 72.0
    return float(val)


def _text_width_in(text: str, pt: float, bold: bool = False) -> float:
    em = _ARIAL_EM_BOLD if bold else _ARIAL_EM_REGULAR
    return len(text) * pt * em / 72.0


def _wrapped_lines(text: str, pt: float, width_in: float, bold: bool = False) -> int:
    if width_in <= 0.1:
        return max(1, len(text.split()))
    total = 0
    space_w = _text_width_in(" ", pt, bold)
    for seg in text.split("\n"):
        words = seg.split()
        if not words:
            total += 1
            continue
        lines = 1
        cur_w = 0.0
        for w in words:
            ww = _text_width_in(w, pt, bold)
            if cur_w == 0.0:
                cur_w = ww
            elif cur_w + space_w + ww <= width_in:
                cur_w += space_w + ww
            else:
                lines += 1
                cur_w = ww
        total += lines
    return max(1, total)


def estimate_node_dimensions(node: NodeSpec, default_w: float = 2.05) -> Tuple[float, float]:
    """
    Estimate natural (width_in, height_in) for a NodeSpec from its text content,
    icon layout, and shape constraints, respecting Milestone 33 cylinder limits
    and >= 11pt readability floors.
    """
    is_cyl = bool(getattr(node, "is_cylinder", False)) or getattr(node, "shape", "rounded") in ("cylinder", "database")
    title_pt = float(node.title_pt) if node.title_pt is not None else 12.0
    sub_pt = float(node.subtitle_pt) if node.subtitle_pt is not None else 9.0

    title_lines = [ln.strip() for ln in (node.title or "").split("\n") if ln.strip()]
    sub_lines = [ln.strip() for ln in (node.subtitle or "").split("\n") if ln.strip()]
    bullet_lines = [f"• {b}" for b in (node.bullets or []) if str(b).strip()]

    max_title_w = max((_text_width_in(ln, title_pt, bold=True) for ln in title_lines), default=0.8)
    max_sub_w = max((_text_width_in(ln, sub_pt, bold=False) for ln in (sub_lines + bullet_lines)), default=0.0)
    natural_text_w = max(max_title_w, max_sub_w)

    has_icon = bool(getattr(node, "icon", None))
    side_icon = has_icon and getattr(node, "icon_layout", "auto") == "side"
    extra_side_w = 0.48 if side_icon else 0.0

    if node.w is not None:
        w = float(node.w)
    else:
        raw_w = max(default_w, natural_text_w + 0.36 + extra_side_w)
        if is_cyl:
            w = max(1.55, min(1.80, raw_w))
        else:
            w = max(1.70, min(3.10, raw_w))

    if node.h is not None:
        h = float(node.h)
    else:
        inner_text_w = max(0.80, w - 0.32 - extra_side_w)
        t_lines = sum(_wrapped_lines(ln, title_pt, inner_text_w, bold=True) for ln in title_lines) if title_lines else 1
        s_lines = sum(_wrapped_lines(ln, sub_pt, inner_text_w, bold=False) for ln in (sub_lines + bullet_lines))

        title_h = t_lines * (title_pt * 1.25 / 72.0)
        sub_h = s_lines * (sub_pt * 1.22 / 72.0) + (0.06 if s_lines > 0 else 0.0)
        kicker_h = (8.0 * 1.25 / 72.0 + 0.04) if getattr(node, "kicker", None) else 0.0
        icon_h = (0.42 if (has_icon and not side_icon) else 0.0)
        cyl_rim_h = (0.38 if is_cyl else 0.0)
        pad_v = 0.28

        raw_h = pad_v + cyl_rim_h + icon_h + kicker_h + title_h + sub_h
        min_h = 1.15 if (has_icon or sub_lines or bullet_lines or is_cyl) else 0.85
        h = max(min_h, min(3.20, raw_h))

    return (_snap(w), _snap(h))


def compute_corridor_span(
    flows: List[FlowSpec],
    left_ids: Set[str],
    right_ids: Set[str],
    base_gap: float = 0.55,
) -> float:
    """
    Compute required corridor span between two groups of elements so any
    crossing flow label pill maintains >= 0.22" halo clearance on each side.
    """
    required = base_gap
    for f in flows:
        if not f.source or not f.target:
            continue
        crosses = (
            (f.source in left_ids and f.target in right_ids)
            or (f.source in right_ids and f.target in left_ids)
        )
        if crosses and f.label:
            font_pt = float(getattr(f, "font_pt", 9.0) or 9.0)
            lines = str(f.label).split("\n")
            max_w = max((_text_width_in(ln, font_pt, bold=True) for ln in lines), default=0.0)
            pill_w = max_w + 0.24
            needed = pill_w + 2.0 * MIN_HALO_IN
            if needed > required:
                required = needed
    return _snap(min(1.80, max(base_gap, required)))


def needs_auto_layout(spec: DiagramSpec) -> bool:
    """
    Returns True if any container or node omits coordinates or requests
    container/diagram-level flexbox/grid layout.
    """
    if getattr(spec, "layout", None) in ("horizontal", "vertical", "grid", "auto"):
        return True
    for c in spec.containers:
        if c.x is None or c.y is None or c.w is None or c.h is None:
            return True
        if getattr(c, "layout", None) in ("horizontal", "vertical", "grid"):
            return True
    for n in spec.nodes:
        if n.x is None or n.y is None or n.w is None or n.h is None:
            return True
    return False


def _subtract_intervals_1d(
    span: Tuple[float, float],
    reserved: List[Tuple[float, float]],
    pad: float,
    min_len: float,
) -> List[Tuple[float, float]]:
    """Subtract padded reserved 1D intervals from `span`, relaxing pad if needed to stay non-overlapping."""
    s0, s1 = span
    if not reserved:
        return [(s0, s1)] if (s1 - s0) > 1e-6 else []

    sorted_res = sorted((max(s0, r0), min(s1, r1)) for r0, r1 in reserved if r1 > s0 and r0 < s1)

    for eff_pad, eff_min in ((pad, min_len), (min(pad, 0.15), min(min_len, 0.35)), (0.02, 0.10), (0.0, 0.02)):
        free: List[Tuple[float, float]] = [(s0, s1)]
        for r0, r1 in sorted_res:
            p0, p1 = r0 - eff_pad, r1 + eff_pad
            next_free: List[Tuple[float, float]] = []
            for f0, f1 in free:
                if p1 <= f0 + 1e-6 or p0 >= f1 - 1e-6:
                    next_free.append((f0, f1))
                    continue
                if p0 > f0 + eff_min:
                    next_free.append((f0, p0))
                if p1 < f1 - eff_min:
                    next_free.append((p1, f1))
            free = [iv for iv in next_free if (iv[1] - iv[0]) >= eff_min]
        if free:
            return free
    return []


def _pack_vertical_span(
    nodes: List[NodeSpec],
    node_dims: Dict[str, Tuple[float, float]],
    inner_x: float,
    iy1: float,
    inner_w: float,
    iy2: float,
    gap_in: float,
    align: str,
) -> None:
    """Pack unpinned-y nodes into vertical interval [iy1, iy2] without overflowing iy2."""
    n_count = len(nodes)
    if n_count == 0:
        return
    span_h = max(0.10, iy2 - iy1)
    pinned_h = [n for n in nodes if n.h is not None]
    flex_h = [n for n in nodes if n.h is None]
    pinned_h_sum = sum(float(n.h) for n in pinned_h)
    flex_nat_h = sum(node_dims[n.id][1] for n in flex_h)
    total_gap = gap_in * max(0, n_count - 1)
    total_nat_h = pinned_h_sum + flex_nat_h + total_gap

    eff_gap = gap_in
    if total_nat_h > span_h and n_count > 1:
        slack_after_pinned = span_h - pinned_h_sum
        if slack_after_pinned <= eff_gap * (n_count - 1) + 0.35 * len(flex_h):
            eff_gap = max(0.04, min(gap_in, max(0.0, slack_after_pinned) / max(1, 2 * n_count)))
        else:
            eff_gap = max(MIN_HALO_IN * 0.75, min(gap_in, (span_h - pinned_h_sum - flex_nat_h * 0.65) / max(1, n_count - 1)))

    avail_flex_h = max(0.10 * len(flex_h), span_h - pinned_h_sum - eff_gap * max(0, n_count - 1))
    scale_y = min(1.0, avail_flex_h / flex_nat_h) if (flex_nat_h > avail_flex_h and flex_nat_h > 0) else 1.0

    cur_y = iy1
    if total_nat_h < span_h:
        extra_each = min(0.18, (span_h - total_nat_h) / max(1, n_count + 1))
        cur_y += extra_each

    for idx, n in enumerate(nodes):
        nat_w, nat_h = node_dims[n.id]
        is_cyl = bool(getattr(n, "is_cylinder", False)) or getattr(n, "shape", "rounded") in ("cylinder", "database")
        if n.w is not None:
            nw = float(n.w)
        elif is_cyl:
            nw = min(1.80, inner_w)
        else:
            nw = min(inner_w, max(nat_w, inner_w * 0.88))

        if n.h is not None:
            nh = float(n.h)
            if cur_y + nh > iy2 + 1e-6:
                cur_y = max(iy1, iy2 - nh)
        else:
            rem_pinned_after = sum(float(on.h) for on in nodes[idx + 1:] if on.h is not None)
            rem_flex_min = 0.15 * sum(1 for on in nodes[idx + 1:] if on.h is None)
            rem_gaps = eff_gap * max(0, n_count - 1 - idx)
            max_allowed_h = iy2 - cur_y - rem_pinned_after - rem_flex_min - rem_gaps
            min_nh = min(0.65, avail_flex_h / max(1, len(flex_h)))
            nh = max(min_nh, nat_h * scale_y)
            if cur_y + nh > iy2 - rem_pinned_after - rem_flex_min - rem_gaps + 1e-6:
                nh = max(0.10, _snap_floor(max(0.10, max_allowed_h)))
            if cur_y + nh > iy2 + 1e-6:
                rem_h = iy2 - cur_y
                if rem_h >= 0.10:
                    nh = max(0.10, _snap_floor(rem_h))
                else:
                    nh = max(0.10, _snap_floor(span_h / max(1, n_count)))
                    cur_y = max(iy1, iy2 - nh)

        if align == "left":
            nx = inner_x
        elif align == "right":
            nx = inner_x + max(0.0, inner_w - nw)
        else:
            nx = inner_x + max(0.0, (inner_w - nw) / 2.0)

        snapped_y = _snap(cur_y) if n.y is None else float(n.y)
        snapped_h = _snap(nh) if n.h is None else float(n.h)
        if n.y is None and snapped_y + snapped_h > iy2 + 1e-6:
            if n.h is None:
                rem_h = iy2 - snapped_y
                if rem_h >= 0.05:
                    snapped_h = _snap_floor(rem_h)
                elif iy2 - iy1 >= snapped_h - 1e-6:
                    snapped_y = max(iy1, _snap_floor(iy2 - snapped_h))
                else:
                    snapped_y = iy1
                    snapped_h = round(max(0.02, iy2 - iy1), 3)
            else:
                snapped_y = max(iy1, _snap_floor(iy2 - snapped_h))
                if snapped_y + snapped_h > iy2 + 1e-6:
                    snapped_h = round(max(0.02, iy2 - snapped_y), 3)

        n.x = _snap(nx) if n.x is None else n.x
        n.y = snapped_y
        n.w = _snap(nw) if n.w is None else n.w
        n.h = snapped_h
        cur_y = max(cur_y, float(n.y) + float(n.h) + eff_gap)


def _pack_horizontal_span(
    nodes: List[NodeSpec],
    node_dims: Dict[str, Tuple[float, float]],
    ix1: float,
    inner_y: float,
    ix2: float,
    inner_h: float,
    gap_in: float,
    align: str,
) -> None:
    """Pack unpinned-x nodes into horizontal interval [ix1, ix2] without overflowing ix2."""
    n_count = len(nodes)
    if n_count == 0:
        return
    span_w = max(0.20, ix2 - ix1)
    pinned_w = [n for n in nodes if n.w is not None]
    flex_w = [n for n in nodes if n.w is None]
    pinned_w_sum = sum(float(n.w) for n in pinned_w)
    flex_nat_w = sum(node_dims[n.id][0] for n in flex_w)
    total_gap = gap_in * max(0, n_count - 1)
    total_nat_w = pinned_w_sum + flex_nat_w + total_gap

    eff_gap = gap_in
    if total_nat_w > span_w and n_count > 1:
        slack_after_pinned = span_w - pinned_w_sum
        if slack_after_pinned <= eff_gap * (n_count - 1) + 0.45 * len(flex_w):
            eff_gap = max(0.04, min(gap_in, max(0.0, slack_after_pinned) / max(1, 2 * n_count)))
        else:
            eff_gap = max(MIN_HALO_IN * 0.75, min(gap_in, (span_w - pinned_w_sum - flex_nat_w * 0.65) / max(1, n_count - 1)))

    avail_flex_w = max(0.20 * len(flex_w), span_w - pinned_w_sum - eff_gap * max(0, n_count - 1))
    scale_x = min(1.0, avail_flex_w / flex_nat_w) if (flex_nat_w > avail_flex_w and flex_nat_w > 0) else 1.0

    cur_x = ix1
    if total_nat_w < span_w and align == "center":
        cur_x += (span_w - total_nat_w) / 2.0

    for idx, n in enumerate(nodes):
        nat_w, nat_h = node_dims[n.id]
        if n.w is not None:
            nw = float(n.w)
            if cur_x + nw > ix2 + 1e-6:
                cur_x = max(ix1, ix2 - nw)
        else:
            min_nw = min(0.85, avail_flex_w / max(1, len(flex_w)))
            nw = max(min_nw, nat_w * scale_x)
            rem_flex_min = sum(
                min(0.45, max(0.20, node_dims[fn.id][0] * scale_x))
                for fn in nodes[idx + 1:]
                if fn.w is None
            )
            rem_pinned_after = sum(float(pn.w) for pn in nodes[idx + 1:] if pn.w is not None)
            rem_gaps = eff_gap * max(0, n_count - 1 - idx)
            max_allowed = ix2 - cur_x - rem_flex_min - rem_pinned_after - rem_gaps
            if nw > max_allowed:
                nw = max(0.20, _snap_floor(max(0.20, max_allowed)))
            if cur_x + nw > ix2 + 1e-6:
                rem_w = ix2 - cur_x
                if rem_w >= 0.20:
                    nw = max(0.20, _snap_floor(rem_w))
                else:
                    nw = max(0.20, _snap_floor(span_w / max(1, n_count)))
                    cur_x = max(ix1, ix2 - nw)

        nh = min(inner_h, nat_h) if n.h is None else float(n.h)
        ny = inner_y + max(0.0, (inner_h - nh) / 2.0)

        snapped_x = _snap(cur_x) if n.x is None else float(n.x)
        snapped_w = _snap(nw) if n.w is None else float(n.w)
        if n.x is None and snapped_x + snapped_w > ix2 + 1e-6:
            if n.w is None:
                rem_w = ix2 - snapped_x
                if rem_w >= 0.05:
                    snapped_w = _snap_floor(rem_w)
                elif ix2 - ix1 >= snapped_w - 1e-6:
                    snapped_x = max(ix1, _snap_floor(ix2 - snapped_w))
                else:
                    snapped_x = ix1
                    snapped_w = round(max(0.02, ix2 - ix1), 3)
            else:
                snapped_x = max(ix1, _snap_floor(ix2 - snapped_w))
                if snapped_x + snapped_w > ix2 + 1e-6:
                    snapped_w = round(max(0.02, ix2 - snapped_x), 3)

        n.x = snapped_x
        n.y = _snap(ny) if n.y is None else n.y
        n.w = snapped_w
        n.h = _snap(nh) if n.h is None else n.h
        cur_x = max(cur_x, float(n.x) + float(n.w) + eff_gap)


def _pack_children_into_box(
    nodes: List[NodeSpec],
    node_dims: Dict[str, Tuple[float, float]],
    inner_x: float,
    inner_y: float,
    inner_w: float,
    inner_h: float,
    layout_mode: str,
    gap_in: float,
    align: str,
    columns: Optional[int],
) -> None:
    """Place child nodes inside a finalized container interior region."""
    if not nodes:
        return

    n_count = len(nodes)
    if layout_mode == "vertical":
        pinned_y_nodes = sorted([n for n in nodes if n.y is not None], key=lambda n: float(n.y))
        auto_y_nodes = [n for n in nodes if n.y is None]
        reserved_y: List[Tuple[float, float]] = []
        inner_bottom = inner_y + inner_h
        for idx_p, pn in enumerate(pinned_y_nodes):
            nat_w, nat_h = node_dims[pn.id]
            is_cyl = bool(getattr(pn, "is_cylinder", False)) or getattr(pn, "shape", "rounded") in ("cylinder", "database")
            nw = float(pn.w) if pn.w is not None else (min(1.80, inner_w) if is_cyl else min(inner_w, max(nat_w, inner_w * 0.88)))
            py = float(pn.y)
            if pn.h is not None:
                nh = float(pn.h)
            else:
                next_py = float(pinned_y_nodes[idx_p + 1].y) if idx_p + 1 < len(pinned_y_nodes) else inner_bottom + gap_in
                max_ph = max(0.15, min(inner_bottom - py, next_py - gap_in - py))
                nh = min(nat_h, max_ph)
            if pn.x is None:
                if align == "left":
                    nx = inner_x
                elif align == "right":
                    nx = inner_x + max(0.0, inner_w - nw)
                else:
                    nx = inner_x + max(0.0, (inner_w - nw) / 2.0)
                pn.x = _snap(nx)
            pn.w = _snap(nw) if pn.w is None else pn.w
            pn.h = _snap(nh) if pn.h is None else pn.h
            reserved_y.append((py, py + float(pn.h)))

        if auto_y_nodes:
            open_y_spans = _subtract_intervals_1d((inner_y, inner_bottom), reserved_y, pad=gap_in, min_len=0.35)
            if not open_y_spans:
                open_y_spans = [(inner_y, inner_bottom)]
            if len(open_y_spans) == 1:
                _pack_vertical_span(auto_y_nodes, node_dims, inner_x, open_y_spans[0][0], inner_w, open_y_spans[0][1], gap_in, align)
            else:
                best_span = max(open_y_spans, key=lambda s: s[1] - s[0])
                total_h = sum(s[1] - s[0] for s in open_y_spans)
                if len(auto_y_nodes) == 1 or best_span[1] - best_span[0] >= 0.7 * total_h:
                    _pack_vertical_span(auto_y_nodes, node_dims, inner_x, best_span[0], inner_w, best_span[1], gap_in, align)
                else:
                    use_spans = open_y_spans[:len(auto_y_nodes)]
                    counts = [1] * len(use_spans)
                    for _ in range(len(auto_y_nodes) - len(use_spans)):
                        bi = max(range(len(use_spans)), key=lambda i: (use_spans[i][1] - use_spans[i][0]) / counts[i])
                        counts[bi] += 1
                    off = 0
                    for s_idx, cnt in enumerate(counts):
                        _pack_vertical_span(
                            auto_y_nodes[off:off + cnt],
                            node_dims,
                            inner_x,
                            use_spans[s_idx][0],
                            inner_w,
                            use_spans[s_idx][1],
                            gap_in,
                            align,
                        )
                        off += cnt

    elif layout_mode == "horizontal":
        pinned_x_nodes = sorted([n for n in nodes if n.x is not None], key=lambda n: float(n.x))
        auto_x_nodes = [n for n in nodes if n.x is None]
        reserved_x: List[Tuple[float, float]] = []
        inner_right = inner_x + inner_w
        for idx_p, pn in enumerate(pinned_x_nodes):
            nat_w, nat_h = node_dims[pn.id]
            px = float(pn.x)
            if pn.w is not None:
                nw = float(pn.w)
            else:
                next_px = float(pinned_x_nodes[idx_p + 1].x) if idx_p + 1 < len(pinned_x_nodes) else inner_right + gap_in
                max_pw = max(0.25, min(inner_right - px, next_px - gap_in - px))
                nw = min(nat_w, max_pw)
            nh = min(inner_h, nat_h) if pn.h is None else float(pn.h)
            ny = inner_y + max(0.0, (inner_h - nh) / 2.0)
            pn.y = _snap(ny) if pn.y is None else pn.y
            pn.w = _snap(nw) if pn.w is None else pn.w
            pn.h = _snap(nh) if pn.h is None else pn.h
            reserved_x.append((px, px + float(pn.w)))

        if auto_x_nodes:
            open_x_spans = _subtract_intervals_1d((inner_x, inner_right), reserved_x, pad=gap_in, min_len=0.45)
            if not open_x_spans:
                open_x_spans = [(inner_x, inner_right)]
            if len(open_x_spans) == 1:
                _pack_horizontal_span(auto_x_nodes, node_dims, open_x_spans[0][0], inner_y, open_x_spans[0][1], inner_h, gap_in, align)
            else:
                best_span = max(open_x_spans, key=lambda s: s[1] - s[0])
                total_w = sum(s[1] - s[0] for s in open_x_spans)
                if len(auto_x_nodes) == 1 or best_span[1] - best_span[0] >= 0.7 * total_w:
                    _pack_horizontal_span(auto_x_nodes, node_dims, best_span[0], inner_y, best_span[1], inner_h, gap_in, align)
                else:
                    use_spans = open_x_spans[:len(auto_x_nodes)]
                    counts = [1] * len(use_spans)
                    for _ in range(len(auto_x_nodes) - len(use_spans)):
                        bi = max(range(len(use_spans)), key=lambda i: (use_spans[i][1] - use_spans[i][0]) / counts[i])
                        counts[bi] += 1
                    off = 0
                    for s_idx, cnt in enumerate(counts):
                        _pack_horizontal_span(
                            auto_x_nodes[off:off + cnt],
                            node_dims,
                            use_spans[s_idx][0],
                            inner_y,
                            use_spans[s_idx][1],
                            inner_h,
                            gap_in,
                            align,
                        )
                        off += cnt

    else:  # grid
        cols = max(1, columns or math.ceil(math.sqrt(n_count)))
        rows = math.ceil(n_count / cols)
        if cols > 1:
            if inner_w >= 0.35 * cols + 0.05 * (cols - 1):
                eff_gx = min(gap_in, (inner_w - 0.35 * cols) / (cols - 1))
            else:
                eff_gx = min(gap_in, max(0.01, inner_w * 0.12 / (cols - 1)))
        else:
            eff_gx = 0.0
        if rows > 1:
            if inner_h >= 0.35 * rows + 0.05 * (rows - 1):
                eff_gy = min(gap_in, (inner_h - 0.35 * rows) / (rows - 1))
            else:
                eff_gy = min(gap_in, max(0.01, inner_h * 0.12 / (rows - 1)))
        else:
            eff_gy = 0.0

        raw_cell_w = max(0.02, (inner_w - eff_gx * max(0, cols - 1)) / cols)
        raw_cell_h = max(0.02, (inner_h - eff_gy * max(0, rows - 1)) / rows)
        cell_w = _snap_floor(raw_cell_w) if raw_cell_w >= 0.05 else round(raw_cell_w, 3)
        cell_h = _snap_floor(raw_cell_h) if raw_cell_h >= 0.05 else round(raw_cell_h, 3)

        inner_right = inner_x + inner_w
        inner_bottom = inner_y + inner_h
        for idx, n in enumerate(nodes):
            r = idx // cols
            col = idx % cols
            nat_w, nat_h = node_dims[n.id]
            is_cyl = bool(getattr(n, "is_cylinder", False)) or getattr(n, "shape", "rounded") in ("cylinder", "database")
            if n.w is not None:
                nw = min(float(n.w), cell_w) if n.x is None else min(float(n.w), max(0.02, inner_right - float(n.x)))
            else:
                nw = min(1.80, cell_w) if is_cyl else cell_w
            if n.h is not None:
                nh = min(float(n.h), cell_h) if n.y is None else min(float(n.h), max(0.02, inner_bottom - float(n.y)))
            else:
                nh = min(cell_h, max(min(nat_h, cell_h), cell_h * 0.85))
            cx = inner_x + col * (cell_w + eff_gx) + max(0.0, (cell_w - nw) / 2.0)
            cy = inner_y + r * (cell_h + eff_gy) + max(0.0, (cell_h - nh) / 2.0)
            snapped_x = max(inner_x, _snap(cx)) if n.x is None else float(n.x)
            snapped_y = max(inner_y, _snap(cy)) if n.y is None else float(n.y)
            snapped_w = (_snap_floor(nw) if nw >= 0.05 else round(nw, 3)) if n.w is None else nw
            snapped_h = (_snap_floor(nh) if nh >= 0.05 else round(nh, 3)) if n.h is None else nh
            if n.x is None and snapped_x + snapped_w > inner_right + 1e-6:
                rem_w = inner_right - snapped_x
                if rem_w >= 0.05:
                    snapped_w = _snap_floor(rem_w)
                else:
                    snapped_x = max(inner_x, _snap_floor(inner_right - snapped_w))
                    if snapped_x + snapped_w > inner_right + 1e-6:
                        snapped_w = round(max(0.02, inner_right - snapped_x), 3)
            if n.y is None and snapped_y + snapped_h > inner_bottom + 1e-6:
                rem_h = inner_bottom - snapped_y
                if rem_h >= 0.05:
                    snapped_h = _snap_floor(rem_h)
                else:
                    snapped_y = max(inner_y, _snap_floor(inner_bottom - snapped_h))
                    if snapped_y + snapped_h > inner_bottom + 1e-6:
                        snapped_h = round(max(0.02, inner_bottom - snapped_y), 3)
            n.x = snapped_x
            n.y = snapped_y
            n.w = snapped_w
            n.h = snapped_h


def _natural_container_size(
    nodes: List[NodeSpec],
    node_dims: Dict[str, Tuple[float, float]],
    layout_mode: str,
    gap_in: float,
    pad_in: float,
    columns: Optional[int],
) -> Tuple[float, float]:
    """Compute required (w, h) for a container wrapping its child nodes."""
    if not nodes:
        return (2.40, 2.20)

    n_count = len(nodes)
    if layout_mode == "vertical":
        inner_w = max(node_dims[n.id][0] for n in nodes)
        inner_h = sum(node_dims[n.id][1] for n in nodes) + gap_in * max(0, n_count - 1)
    elif layout_mode == "horizontal":
        inner_w = sum(node_dims[n.id][0] for n in nodes) + gap_in * max(0, n_count - 1)
        inner_h = max(node_dims[n.id][1] for n in nodes)
    else:
        cols = max(1, columns or math.ceil(math.sqrt(n_count)))
        rows = math.ceil(n_count / cols)
        max_nw = max(node_dims[n.id][0] for n in nodes)
        max_nh = max(node_dims[n.id][1] for n in nodes)
        inner_w = cols * max_nw + gap_in * max(0, cols - 1)
        inner_h = rows * max_nh + gap_in * max(0, rows - 1)

    total_w = max(2.10, inner_w + 2.0 * pad_in)
    total_h = max(2.00, inner_h + 2.0 * pad_in + CONTAINER_LABEL_BAND_IN)
    return (_snap(total_w), _snap(total_h))


def _topological_layers(nodes: List[NodeSpec], flows: List[FlowSpec]) -> List[List[NodeSpec]]:
    """Assign uncontained nodes into DAG layers using Kahn's algorithm."""
    node_map = {n.id: n for n in nodes}
    node_ids = [n.id for n in nodes]
    adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}
    indeg: Dict[str, int] = {nid: 0 for nid in node_ids}

    for f in flows:
        if f.source in node_map and f.target in node_map and f.source != f.target:
            if f.target not in adj[f.source]:
                adj[f.source].append(f.target)
                indeg[f.target] += 1

    layers: List[List[NodeSpec]] = []
    remaining = set(node_ids)

    while remaining:
        ready = [nid for nid in node_ids if nid in remaining and indeg[nid] == 0]
        if not ready:
            # Break cycle deterministically using declaration order
            ready = [next(nid for nid in node_ids if nid in remaining)]
        layers.append([node_map[nid] for nid in ready])
        for nid in ready:
            remaining.remove(nid)
            for nxt in adj[nid]:
                indeg[nxt] = max(0, indeg[nxt] - 1)

    return layers


Rect = Tuple[float, float, float, float]


def _subtract_obstacles(
    usable_rect: Rect,
    obstacles: List[Rect],
    pad_x: float = 0.0,
    pad_y: float = 0.0,
    min_w: float = 1.5,
    min_h: float = 1.2,
) -> List[Rect]:
    """Compute maximal free rectangles inside `usable_rect` avoiding padded `obstacles`."""
    free: List[Rect] = [usable_rect]
    for ox1, oy1, ox2, oy2 in obstacles:
        px1, py1, px2, py2 = ox1 - pad_x, oy1 - pad_y, ox2 + pad_x, oy2 + pad_y
        next_free: List[Rect] = []
        for fx1, fy1, fx2, fy2 in free:
            if px2 <= fx1 + 1e-6 or px1 >= fx2 - 1e-6 or py2 <= fy1 + 1e-6 or py1 >= fy2 - 1e-6:
                next_free.append((fx1, fy1, fx2, fy2))
                continue
            if px1 > fx1 + min_w:
                next_free.append((fx1, fy1, px1, fy2))
            if px2 < fx2 - min_w:
                next_free.append((px2, fy1, fx2, fy2))
            if py1 > fy1 + min_h:
                next_free.append((fx1, fy1, fx2, py1))
            if py2 < fy2 - min_h:
                next_free.append((fx1, py2, fx2, fy2))

        # Prune dominated sub-rectangles
        filtered: List[Rect] = []
        for i, r1 in enumerate(next_free):
            if (r1[2] - r1[0]) < min_w or (r1[3] - r1[1]) < min_h:
                continue
            dominated = False
            for j, r2 in enumerate(next_free):
                if i != j and r2[0] <= r1[0] + 1e-6 and r2[1] <= r1[1] + 1e-6 and r2[2] >= r1[2] - 1e-6 and r2[3] >= r1[3] - 1e-6:
                    if r2 != r1 or j < i:
                        dominated = True
                        break
            if not dominated:
                filtered.append(r1)
        free = filtered
    return free


def _pick_disjoint_bands(free_rects: List[Rect], axis: str, min_w: float = 1.5, min_h: float = 1.2) -> List[Rect]:
    """Greedily pick pairwise-disjoint rectangles from `free_rects` without expanding beyond them."""
    pool = list(free_rects)
    chosen: List[Rect] = []
    while pool:
        pool.sort(key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), reverse=True)
        best = pool.pop(0)
        chosen.append(best)
        bx1, by1, bx2, by2 = best
        next_pool: List[Rect] = []
        for fx1, fy1, fx2, fy2 in pool:
            if bx2 <= fx1 + 1e-6 or bx1 >= fx2 - 1e-6 or by2 <= fy1 + 1e-6 or by1 >= fy2 - 1e-6:
                next_pool.append((fx1, fy1, fx2, fy2))
                continue
            if bx1 > fx1 + min_w:
                next_pool.append((fx1, fy1, bx1, fy2))
            if bx2 < fx2 - min_w:
                next_pool.append((bx2, fy1, fx2, fy2))
            if by1 > fy1 + min_h:
                next_pool.append((fx1, fy1, fx2, by1))
            if by2 < fy2 - min_h:
                next_pool.append((fx1, by2, fx2, fy2))
        pool = [r for r in next_pool if (r[2] - r[0]) >= min_w and (r[3] - r[1]) >= min_h]

    if axis == "vertical":
        chosen.sort(key=lambda r: (r[1], r[0]))
    else:
        chosen.sort(key=lambda r: (r[0], r[1]))
    return chosen


def _find_free_bands(
    usable_rect: Rect,
    canvas_rect: Rect,
    obstacles: List[Rect],
    axis: str,
    primary_pad: float,
    min_w: float,
    min_h: float,
) -> List[Rect]:
    """
    Find disjoint free rectangles avoiding `obstacles`, progressively tightening
    clearance padding and minimum box dimensions instead of falling back blindly
    to `usable_rect` (which would overlap obstacles).
    """
    if not obstacles:
        return [usable_rect]

    ladder = (
        (usable_rect, primary_pad, min_w, min_h),
        (usable_rect, min(primary_pad, MIN_HALO_IN), min(min_w, 0.55), min(min_h, 0.55)),
        (usable_rect, 0.05, 0.25, 0.25),
        (canvas_rect, 0.02, 0.20, 0.20),
    )
    for rect, pad, mw, mh in ladder:
        raw_free = _subtract_obstacles(rect, obstacles, pad_x=pad, pad_y=pad, min_w=mw, min_h=mh)
        bands = _pick_disjoint_bands(raw_free, axis, min_w=mw, min_h=mh)
        if bands:
            return bands
    return []


def _place_horizontal_span_containers(
    group: List[ContainerSpec],
    sx1: float,
    by1: float,
    sx2: float,
    by2: float,
    nat_c_sizes: Dict[str, Tuple[float, float]],
    container_nodes: Dict[str, List[NodeSpec]],
    flows: List[FlowSpec],
    base_c_gap: float,
    max_auto_h: Optional[float] = None,
) -> None:
    """Place unpinned-x containers sequentially inside horizontal span [sx1, sx2]."""
    m = len(group)
    if m == 0:
        return
    span_w = max(0.5, sx2 - sx1)
    band_h = max(1.0, by2 - by1)

    c_gaps: List[float] = []
    for idx in range(m - 1):
        left_c = group[idx]
        right_c = group[idx + 1]
        l_ids = {left_c.id} | {n.id for n in container_nodes[left_c.id]}
        r_ids = {right_c.id} | {n.id for n in container_nodes[right_c.id]}
        c_gaps.append(compute_corridor_span(flows, l_ids, r_ids, base_gap=base_c_gap))

    pinned_w_sum = sum(float(c.w) for c in group if c.w is not None)
    flex_containers = [c for c in group if c.w is None]
    total_gap_w = sum(c_gaps)
    if m > 1 and pinned_w_sum + total_gap_w + 0.5 * len(flex_containers) > span_w:
        scale_g = max(0.15, (span_w - pinned_w_sum - 0.5 * len(flex_containers)) / max(0.01, total_gap_w))
        c_gaps = [max(0.10, round(g * scale_g, 2)) for g in c_gaps]
        total_gap_w = sum(c_gaps)

    avail_w = max(0.4 * m, span_w - total_gap_w)
    flex_nat_w = sum(nat_c_sizes[c.id][0] for c in flex_containers)
    flex_avail_w = max(0.4 * len(flex_containers), avail_w - pinned_w_sum)

    cur_x = sx1
    for idx, c in enumerate(group):
        actual_x = _snap(cur_x)
        actual_y = float(c.y) if c.y is not None else _snap(by1)

        if c.w is not None:
            cw = float(c.w)
            if actual_x + cw > sx2 + 1e-6 and sx2 - sx1 >= cw - 1e-6:
                actual_x = max(sx1, _snap_floor(sx2 - cw))
        else:
            nw = nat_c_sizes[c.id][0]
            raw_cw = (
                flex_avail_w * (nw / flex_nat_w)
                if flex_nat_w > 0
                else (flex_avail_w / max(1, len(flex_containers)))
            )
            cw = _snap(raw_cw)
            rem_pinned_after = sum(float(oc.w) for oc in group[idx + 1:] if oc.w is not None)
            rem_flex_after = sum(
                min(0.8, max(0.4, flex_avail_w * (nat_c_sizes[oc.id][0] / flex_nat_w) if flex_nat_w > 0 else flex_avail_w / max(1, len(flex_containers))))
                for oc in group[idx + 1:]
                if oc.w is None
            )
            rem_gaps_after = sum(c_gaps[idx:])
            max_allowed_w = sx2 - actual_x - rem_pinned_after - rem_flex_after - rem_gaps_after
            if cw > max_allowed_w:
                cw = max(0.4, _snap_floor(max(0.4, max_allowed_w)))
            if actual_x + cw > sx2 + 1e-6:
                cw = max(0.4, _snap_floor(max(0.4, sx2 - actual_x)))

        if c.h is not None:
            ch = float(c.h)
        else:
            max_ch = max(0.8, by2 - actual_y)
            target_h = min(band_h, max_ch)
            if max_auto_h is not None:
                target_h = min(target_h, max_auto_h)
            ch = _snap(target_h)
            if actual_y + ch > by2 + 1e-6:
                ch = max(0.8, _snap_floor(by2 - actual_y))

        c.x = actual_x
        c.y = actual_y
        c.w = cw
        c.h = ch
        if idx < m - 1:
            cur_x = max(cur_x, float(c.x) + float(c.w) + c_gaps[idx])


def _place_container_group_horizontal(
    group: List[ContainerSpec],
    band: Rect,
    nat_c_sizes: Dict[str, Tuple[float, float]],
    container_nodes: Dict[str, List[NodeSpec]],
    flows: List[FlowSpec],
    base_c_gap: float,
    max_auto_h: Optional[float] = None,
) -> None:
    bx1, by1, bx2, by2 = band
    band_w = max(0.5, bx2 - bx1)
    band_h = max(1.0, by2 - by1)
    m = len(group)
    if m == 0:
        return

    pinned_x_containers = sorted([c for c in group if c.x is not None], key=lambda c: float(c.x))
    auto_x_containers = [c for c in group if c.x is None]

    if not pinned_x_containers:
        _place_horizontal_span_containers(
            auto_x_containers, bx1, by1, bx2, by2, nat_c_sizes, container_nodes, flows, base_c_gap, max_auto_h=max_auto_h
        )
        return

    total_gap_w = base_c_gap * max(0, m - 1)
    avail_w = max(0.5, band_w - total_gap_w)
    pinned_w_sum = sum(float(c.w) for c in group if c.w is not None)
    flex_containers = [c for c in group if c.w is None]
    flex_nat_w = sum(nat_c_sizes[c.id][0] for c in flex_containers)
    flex_avail_w = max(0.6 * len(flex_containers), avail_w - pinned_w_sum)

    reserved_x: List[Tuple[float, float]] = []
    for idx_p, pc in enumerate(pinned_x_containers):
        actual_x = float(pc.x)
        actual_y = float(pc.y) if pc.y is not None else _snap(by1)
        if pc.w is not None:
            cw = float(pc.w)
        else:
            nw = nat_c_sizes[pc.id][0]
            raw_cw = (
                flex_avail_w * (nw / flex_nat_w)
                if flex_nat_w > 0
                else (flex_avail_w / max(1, len(flex_containers)))
            )
            cw = _snap(raw_cw)
            next_px = float(pinned_x_containers[idx_p + 1].x) if idx_p + 1 < len(pinned_x_containers) else None
            if next_px is not None and actual_x + cw + base_c_gap > next_px + 1e-6:
                cw = max(0.5, _snap_floor(next_px - base_c_gap - actual_x))
            # If pinned container starts near left edge and no space precedes it, reserve trailing auto containers
            if auto_x_containers and actual_x - bx1 < 1.2 + base_c_gap and next_px is None:
                min_auto_need = sum(float(ac.w) if ac.w is not None else 0.8 for ac in auto_x_containers) + base_c_gap * len(auto_x_containers)
                max_w_with_trail = bx2 - actual_x - min_auto_need
                if max_w_with_trail >= 0.8 and actual_x + cw > bx2 - min_auto_need + 1e-6:
                    cw = max(0.8, _snap_floor(max_w_with_trail))
            if actual_x + cw > bx2 + 1e-6:
                cw = max(0.5, _snap_floor(bx2 - actual_x))

        if pc.h is not None:
            ch = float(pc.h)
        else:
            max_ch = max(0.8, by2 - actual_y)
            target_h = min(band_h, max_ch)
            if max_auto_h is not None:
                target_h = min(target_h, max_auto_h)
            ch = _snap(target_h)
            if actual_y + ch > by2 + 1e-6:
                ch = max(0.8, _snap_floor(by2 - actual_y))

        pc.x = actual_x
        pc.y = actual_y
        pc.w = cw
        pc.h = ch
        reserved_x.append((actual_x, actual_x + cw))

    if not auto_x_containers:
        return

    open_spans = _subtract_intervals_1d((bx1, bx2), reserved_x, pad=base_c_gap, min_len=0.60)
    if not open_spans:
        open_spans = [(bx1, bx2)]

    if len(open_spans) == 1 or len(auto_x_containers) == 1:
        # Pick span wide enough for pinned widths, or largest span
        req_min = sum(float(ac.w) if ac.w is not None else 0.8 for ac in auto_x_containers)
        fitting = [sp for sp in open_spans if (sp[1] - sp[0]) >= req_min]
        best_span = max(fitting or open_spans, key=lambda s: s[1] - s[0])
        _place_horizontal_span_containers(
            auto_x_containers, best_span[0], by1, best_span[1], by2, nat_c_sizes, container_nodes, flows, base_c_gap, max_auto_h=max_auto_h
        )
    else:
        use_spans = open_spans[:len(auto_x_containers)]
        counts = [1] * len(use_spans)
        for _ in range(len(auto_x_containers) - len(use_spans)):
            bi = max(range(len(use_spans)), key=lambda i: (use_spans[i][1] - use_spans[i][0]) / counts[i])
            counts[bi] += 1
        off = 0
        for s_idx, cnt in enumerate(counts):
            _place_horizontal_span_containers(
                auto_x_containers[off:off + cnt],
                use_spans[s_idx][0],
                by1,
                use_spans[s_idx][1],
                by2,
                nat_c_sizes,
                container_nodes,
                flows,
                base_c_gap,
                max_auto_h=max_auto_h,
            )
            off += cnt


def _place_vertical_span_containers(
    group: List[ContainerSpec],
    bx1: float,
    sy1: float,
    bx2: float,
    sy2: float,
    nat_c_sizes: Dict[str, Tuple[float, float]],
    base_c_gap: float,
) -> None:
    """Place unpinned-y containers sequentially inside vertical span [sy1, sy2]."""
    m = len(group)
    if m == 0:
        return
    band_w = max(0.5, bx2 - bx1)
    span_h = max(0.5, sy2 - sy1)

    total_gap_h = base_c_gap * max(0, m - 1)
    pinned_h_sum = sum(float(c.h) for c in group if c.h is not None)
    flex_containers = [c for c in group if c.h is None]
    eff_gap = base_c_gap
    if m > 1 and pinned_h_sum + total_gap_h + 0.5 * len(flex_containers) > span_h:
        eff_gap = max(0.10, min(base_c_gap, (span_h - pinned_h_sum - 0.5 * len(flex_containers)) / max(1, m - 1)))
        total_gap_h = eff_gap * (m - 1)

    avail_h = max(0.4 * m, span_h - total_gap_h)
    flex_nat_h = sum(nat_c_sizes[c.id][1] for c in flex_containers)
    flex_avail_h = max(0.4 * len(flex_containers), avail_h - pinned_h_sum)

    cur_y = sy1
    for idx, c in enumerate(group):
        actual_x = float(c.x) if c.x is not None else _snap(bx1)
        actual_y = _snap(cur_y)

        if c.w is not None:
            cw = float(c.w)
        else:
            max_cw = max(0.5, bx2 - actual_x)
            cw = _snap(min(band_w, max_cw))
            if actual_x + cw > bx2 + 1e-6:
                cw = max(0.5, _snap_floor(bx2 - actual_x))

        if c.h is not None:
            ch = float(c.h)
            if actual_y + ch > sy2 + 1e-6 and sy2 - sy1 >= ch - 1e-6:
                actual_y = max(sy1, _snap_floor(sy2 - ch))
        else:
            nh = nat_c_sizes[c.id][1]
            raw_ch = (
                flex_avail_h * (nh / flex_nat_h)
                if flex_nat_h > 0
                else (flex_avail_h / max(1, len(flex_containers)))
            )
            ch = _snap(raw_ch)
            rem_pinned_after = sum(float(oc.h) for oc in group[idx + 1:] if oc.h is not None)
            rem_flex_after = sum(
                min(0.8, max(0.4, flex_avail_h * (nat_c_sizes[oc.id][1] / flex_nat_h) if flex_nat_h > 0 else flex_avail_h / max(1, len(flex_containers))))
                for oc in group[idx + 1:]
                if oc.h is None
            )
            rem_gaps_after = eff_gap * max(0, m - 1 - idx)
            max_allowed_h = sy2 - actual_y - rem_pinned_after - rem_flex_after - rem_gaps_after
            if ch > max_allowed_h:
                ch = max(0.4, _snap_floor(max(0.4, max_allowed_h)))
            if actual_y + ch > sy2 + 1e-6:
                ch = max(0.4, _snap_floor(max(0.4, sy2 - actual_y)))

        c.x = actual_x
        c.y = actual_y
        c.w = cw
        c.h = ch
        cur_y = max(cur_y, float(c.y) + float(c.h) + eff_gap)


def _place_container_group_vertical(
    group: List[ContainerSpec],
    band: Rect,
    nat_c_sizes: Dict[str, Tuple[float, float]],
    base_c_gap: float,
) -> None:
    bx1, by1, bx2, by2 = band
    band_w = max(0.5, bx2 - bx1)
    band_h = max(0.5, by2 - by1)
    m = len(group)
    if m == 0:
        return

    pinned_y_containers = sorted([c for c in group if c.y is not None], key=lambda c: float(c.y))
    auto_y_containers = [c for c in group if c.y is None]

    if not pinned_y_containers:
        _place_vertical_span_containers(auto_y_containers, bx1, by1, bx2, by2, nat_c_sizes, base_c_gap)
        return

    total_gap_h = base_c_gap * max(0, m - 1)
    avail_h = max(0.5, band_h - total_gap_h)
    pinned_h_sum = sum(float(c.h) for c in group if c.h is not None)
    flex_containers = [c for c in group if c.h is None]
    flex_nat_h = sum(nat_c_sizes[c.id][1] for c in flex_containers)
    flex_avail_h = max(0.6 * len(flex_containers), avail_h - pinned_h_sum)

    reserved_y: List[Tuple[float, float]] = []
    for idx_p, pc in enumerate(pinned_y_containers):
        actual_x = float(pc.x) if pc.x is not None else _snap(bx1)
        actual_y = float(pc.y)
        if pc.w is not None:
            cw = float(pc.w)
        else:
            max_cw = max(0.5, bx2 - actual_x)
            cw = _snap(min(band_w, max_cw))
            if actual_x + cw > bx2 + 1e-6:
                cw = max(0.5, _snap_floor(bx2 - actual_x))

        if pc.h is not None:
            ch = float(pc.h)
        else:
            nh = nat_c_sizes[pc.id][1]
            raw_ch = (
                flex_avail_h * (nh / flex_nat_h)
                if flex_nat_h > 0
                else (flex_avail_h / max(1, len(flex_containers)))
            )
            ch = _snap(raw_ch)
            next_py = float(pinned_y_containers[idx_p + 1].y) if idx_p + 1 < len(pinned_y_containers) else None
            if next_py is not None and actual_y + ch + base_c_gap > next_py + 1e-6:
                ch = max(0.5, _snap_floor(next_py - base_c_gap - actual_y))
            if auto_y_containers and actual_y - by1 < 1.0 + base_c_gap and next_py is None:
                min_auto_need = sum(float(ac.h) if ac.h is not None else 0.8 for ac in auto_y_containers) + base_c_gap * len(auto_y_containers)
                max_h_with_trail = by2 - actual_y - min_auto_need
                if max_h_with_trail >= 0.8 and actual_y + ch > by2 - min_auto_need + 1e-6:
                    ch = max(0.8, _snap_floor(max_h_with_trail))
            if actual_y + ch > by2 + 1e-6:
                ch = max(0.5, _snap_floor(by2 - actual_y))

        pc.x = actual_x
        pc.y = actual_y
        pc.w = cw
        pc.h = ch
        reserved_y.append((actual_y, actual_y + ch))

    if not auto_y_containers:
        return

    open_spans = _subtract_intervals_1d((by1, by2), reserved_y, pad=base_c_gap, min_len=0.60)
    if not open_spans:
        open_spans = [(by1, by2)]

    if len(open_spans) == 1 or len(auto_y_containers) == 1:
        req_min = sum(float(ac.h) if ac.h is not None else 0.8 for ac in auto_y_containers)
        fitting = [sp for sp in open_spans if (sp[1] - sp[0]) >= req_min]
        best_span = max(fitting or open_spans, key=lambda s: s[1] - s[0])
        _place_vertical_span_containers(auto_y_containers, bx1, best_span[0], bx2, best_span[1], nat_c_sizes, base_c_gap)
    else:
        use_spans = open_spans[:len(auto_y_containers)]
        counts = [1] * len(use_spans)
        for _ in range(len(auto_y_containers) - len(use_spans)):
            bi = max(range(len(use_spans)), key=lambda i: (use_spans[i][1] - use_spans[i][0]) / counts[i])
            counts[bi] += 1
        off = 0
        for s_idx, cnt in enumerate(counts):
            _place_vertical_span_containers(
                auto_y_containers[off:off + cnt],
                bx1,
                use_spans[s_idx][0],
                bx2,
                use_spans[s_idx][1],
                nat_c_sizes,
                base_c_gap,
            )
            off += cnt


def solve_diagram_layout(spec: DiagramSpec) -> DiagramSpec:
    """
    Solve missing coordinates and container layouts in-place on `spec`,
    guaranteeing collision-free bounds and >= 14pt clearance halos.
    """
    if not needs_auto_layout(spec):
        return spec

    unit = (getattr(spec.canvas, "unit", "in") or "in").lower().strip()
    is_px_unit = unit != "in"
    if is_px_unit:
        scale_to_in = 1.0 / PX_PER_INCH
        for c in spec.containers:
            if c.x is not None:
                c.x = float(c.x) * scale_to_in
            if c.y is not None:
                c.y = float(c.y) * scale_to_in
            if c.w is not None:
                c.w = float(c.w) * scale_to_in
            if c.h is not None:
                c.h = float(c.h) * scale_to_in
        for n in spec.nodes:
            if n.x is not None:
                n.x = float(n.x) * scale_to_in
            if n.y is not None:
                n.y = float(n.y) * scale_to_in
            if n.w is not None:
                n.w = float(n.w) * scale_to_in
            if n.h is not None:
                n.h = float(n.h) * scale_to_in
        canvas_w = (float(spec.canvas.width) * scale_to_in) if spec.canvas.width else DEFAULT_CANVAS_W
        canvas_h = (float(spec.canvas.height) * scale_to_in) if spec.canvas.height else DEFAULT_CANVAS_H
    else:
        canvas_w = float(spec.canvas.width or DEFAULT_CANVAS_W)
        canvas_h = float(spec.canvas.height or DEFAULT_CANVAS_H)

    top_y = CANVAS_TOP_Y if spec.header.show else 0.45
    usable_x = CANVAS_MARGIN_X
    usable_w = max(2.0, canvas_w - 2.0 * CANVAS_MARGIN_X)
    usable_h = max(2.0, canvas_h - top_y - CANVAS_MARGIN_BOTTOM)
    usable_rect: Rect = (usable_x, top_y, usable_x + usable_w, top_y + usable_h)
    canvas_rect: Rect = (0.15, top_y, max(0.5, canvas_w - 0.15), max(top_y + 0.5, canvas_h - 0.15))

    # 1. Estimate natural dimensions for every node
    node_dims: Dict[str, Tuple[float, float]] = {}
    for n in spec.nodes:
        node_dims[n.id] = estimate_node_dimensions(n)

    # 2. Group nodes by container_id
    container_nodes: Dict[str, List[NodeSpec]] = {c.id: [] for c in spec.containers}
    uncontained_nodes: List[NodeSpec] = []
    for n in spec.nodes:
        if n.container_id and n.container_id in container_nodes:
            container_nodes[n.container_id].append(n)
        else:
            uncontained_nodes.append(n)

    explicit_uncontained_rects: List[Rect] = [
        (float(n.x), float(n.y), float(n.x) + float(n.w), float(n.y) + float(n.h))
        for n in uncontained_nodes
        if n.x is not None and n.y is not None and n.w is not None and n.h is not None
    ]
    auto_uncontained = [n for n in uncontained_nodes if n.x is None or n.y is None or n.w is None or n.h is None]

    top_axis = spec.layout if spec.layout in ("horizontal", "vertical", "grid") else "horizontal"
    default_child_layout = "vertical" if top_axis == "horizontal" else "horizontal"

    # 3. Compute natural sizes & pack explicit containers
    explicit_containers: List[ContainerSpec] = []
    auto_containers: List[ContainerSpec] = []
    nat_c_sizes: Dict[str, Tuple[float, float]] = {}

    for c in spec.containers:
        c_layout = c.layout if c.layout in ("horizontal", "vertical", "grid") else default_child_layout
        gap_in = max(MIN_HALO_IN, _to_inches_spacing(getattr(c, "gap", 0.25)))
        pad_in = max(0.18, _to_inches_spacing(getattr(c, "padding", 0.22)))
        children = container_nodes[c.id]

        if c.x is not None and c.y is not None and c.w is not None and c.h is not None:
            explicit_containers.append(c)
            # Explicit container box: pack any auto-positioned children inside it
            auto_children = [ch for ch in children if ch.x is None or ch.y is None or ch.w is None or ch.h is None]
            if auto_children or c.layout in ("horizontal", "vertical", "grid"):
                valign = c.resolved_vertical_align()
                eff_pad = min(pad_in, float(c.w) * 0.15, float(c.h) * 0.15) if (float(c.w) < 1.5 or float(c.h) < 1.5) else pad_in
                inner_x = float(c.x) + eff_pad
                inner_w = max(0.20, float(c.w) - 2.0 * eff_pad)
                if valign == "bottom":
                    inner_y = float(c.y) + eff_pad
                    inner_h = max(0.20, float(c.h) - 2.0 * eff_pad - CONTAINER_LABEL_BAND_IN)
                else:
                    inner_y = float(c.y) + CONTAINER_LABEL_BAND_IN + eff_pad * 0.5
                    inner_h = max(0.20, float(c.h) - CONTAINER_LABEL_BAND_IN - eff_pad * 1.5)
                _pack_children_into_box(
                    children, node_dims, inner_x, inner_y, inner_w, inner_h,
                    c_layout, gap_in, c.align or "center", getattr(c, "columns", None),
                )
        else:
            nat_w, nat_h = _natural_container_size(
                children, node_dims, c_layout, gap_in, pad_in, getattr(c, "columns", None)
            )
            if c.w is not None:
                nat_w = float(c.w)
            if c.h is not None:
                nat_h = float(c.h)
            nat_c_sizes[c.id] = (nat_w, nat_h)
            auto_containers.append(c)

    # 4. Position auto-containers on canvas while reserving explicit container & explicit uncontained node bounds
    if auto_containers:
        m = len(auto_containers)
        base_c_gap = max(0.45, _to_inches_spacing(getattr(spec, "container_gap", 0.55)))

        auto_parent_ids = {
            pid
            for ac in auto_containers
            for pid in (getattr(ac, "parent_id", None), getattr(ac, "container_id", None))
            if pid
        }
        explicit_obstacles: List[Rect] = [
            (float(ec.x), float(ec.y), float(ec.x) + float(ec.w), float(ec.y) + float(ec.h))
            for ec in explicit_containers
            if ec.id not in auto_parent_ids
        ] + list(explicit_uncontained_rects)

        free_bands = _find_free_bands(
            usable_rect,
            canvas_rect,
            explicit_obstacles,
            top_axis,
            primary_pad=base_c_gap,
            min_w=1.5,
            min_h=1.2,
        )
        if not free_bands:
            free_bands = [usable_rect]

        reserve_bottom_for_uncontained = (
            bool(auto_uncontained)
            and top_axis == "horizontal"
            and len(free_bands) == 1
            and (free_bands[0][2] - free_bands[0][0]) < 3.5
            and (free_bands[0][3] - free_bands[0][1]) >= 3.2
        )
        max_auto_h = (
            max(1.4, min(free_bands[0][3] - free_bands[0][1] - 1.4, max(nat_c_sizes[c.id][1] for c in auto_containers)))
            if reserve_bottom_for_uncontained
            else None
        )

        if top_axis == "horizontal":
            if len(free_bands) == 1 or m == 1:
                band = max(free_bands, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                _place_container_group_horizontal(
                    auto_containers, band, nat_c_sizes, container_nodes, spec.flows, base_c_gap, max_auto_h=max_auto_h
                )
            else:
                use_bands = free_bands[:m]
                total_bw = sum(b[2] - b[0] for b in use_bands)
                counts = [1] * len(use_bands)
                rem = m - len(use_bands)
                if rem > 0 and total_bw > 0:
                    for _ in range(rem):
                        best_bi = max(range(len(use_bands)), key=lambda i: (use_bands[i][2] - use_bands[i][0]) / counts[i])
                        counts[best_bi] += 1
                offset = 0
                for b_idx, cnt in enumerate(counts):
                    _place_container_group_horizontal(
                        auto_containers[offset:offset + cnt],
                        use_bands[b_idx],
                        nat_c_sizes,
                        container_nodes,
                        spec.flows,
                        base_c_gap,
                    )
                    offset += cnt

        elif top_axis == "vertical":
            if len(free_bands) == 1 or m == 1:
                band = max(free_bands, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                _place_container_group_vertical(auto_containers, band, nat_c_sizes, base_c_gap)
            else:
                use_bands = free_bands[:m]
                counts = [1] * len(use_bands)
                rem = m - len(use_bands)
                if rem > 0:
                    for _ in range(rem):
                        best_bi = max(range(len(use_bands)), key=lambda i: (use_bands[i][3] - use_bands[i][1]) / counts[i])
                        counts[best_bi] += 1
                offset = 0
                for b_idx, cnt in enumerate(counts):
                    _place_container_group_vertical(
                        auto_containers[offset:offset + cnt],
                        use_bands[b_idx],
                        nat_c_sizes,
                        base_c_gap,
                    )
                    offset += cnt

        else:  # grid of containers
            band = max(free_bands, key=lambda r: (r[2] - r[0]) * (r[3] - r[1])) if explicit_obstacles else usable_rect
            bx1, by1, bx2, by2 = band
            bw, bh = max(0.5, bx2 - bx1), max(0.5, by2 - by1)
            cols = max(1, math.ceil(math.sqrt(m)))
            if explicit_obstacles and bw < cols * 1.2 + base_c_gap * max(0, cols - 1) and bh >= 2.8:
                cols = max(1, min(m, int((bw + base_c_gap) // (1.1 + base_c_gap))))
            rows = math.ceil(m / cols)
            eff_gx = min(base_c_gap, max(0.10, (bw - 0.35 * cols) / max(1, cols - 1))) if cols > 1 else base_c_gap
            eff_gy = min(base_c_gap, max(0.10, (bh - 0.35 * rows) / max(1, rows - 1))) if rows > 1 else base_c_gap
            cw = max(0.30, _snap_floor((bw - eff_gx * max(0, cols - 1)) / cols))
            ch = max(0.30, _snap_floor((bh - eff_gy * max(0, rows - 1)) / rows))
            for idx, c in enumerate(auto_containers):
                r = idx // cols
                col = idx % cols
                cx = _snap(bx1 + col * (cw + eff_gx)) if c.x is None else float(c.x)
                cy = _snap(by1 + r * (ch + eff_gy)) if c.y is None else float(c.y)
                c_w = cw if c.w is None else float(c.w)
                c_h = ch if c.h is None else float(c.h)
                if c.x is None and c.w is None and cx + c_w > bx2 + 1e-6:
                    c_w = max(0.30, _snap_floor(bx2 - cx))
                if c.y is None and c.h is None and cy + c_h > by2 + 1e-6:
                    c_h = max(0.30, _snap_floor(by2 - cy))
                c.x = cx
                c.y = cy
                c.w = c_w
                c.h = c_h

        # Pack children inside each newly positioned auto-container
        for c in auto_containers:
            c_layout = c.layout if c.layout in ("horizontal", "vertical", "grid") else default_child_layout
            gap_in = max(MIN_HALO_IN, _to_inches_spacing(getattr(c, "gap", 0.25)))
            pad_in = max(0.18, _to_inches_spacing(getattr(c, "padding", 0.22)))
            eff_pad = min(pad_in, float(c.w) * 0.15, float(c.h) * 0.15) if (float(c.w) < 1.5 or float(c.h) < 1.5) else pad_in
            valign = c.resolved_vertical_align()
            inner_x = float(c.x) + eff_pad
            inner_w = max(0.20, float(c.w) - 2.0 * eff_pad)
            if valign == "bottom":
                inner_y = float(c.y) + eff_pad
                inner_h = max(0.20, float(c.h) - 2.0 * eff_pad - CONTAINER_LABEL_BAND_IN)
            else:
                inner_y = float(c.y) + CONTAINER_LABEL_BAND_IN + eff_pad * 0.5
                inner_h = max(0.20, float(c.h) - CONTAINER_LABEL_BAND_IN - eff_pad * 1.5)
            _pack_children_into_box(
                container_nodes[c.id], node_dims, inner_x, inner_y, inner_w, inner_h,
                c_layout, gap_in, c.align or "center", getattr(c, "columns", None),
            )

    # 5. Position uncontained auto-nodes via topological layering (reserving container & explicit uncontained node bounds)
    if auto_uncontained:
        un_x, un_y, un_w, un_h = usable_x, top_y, usable_w, usable_h
        c_rects: List[Rect] = [
            (float(c.x), float(c.y), float(c.x) + float(c.w), float(c.y) + float(c.h))
            for c in spec.containers
            if c.x is not None and c.y is not None and c.w is not None and c.h is not None
        ]
        node_obstacles: List[Rect] = c_rects + list(explicit_uncontained_rects)
        if node_obstacles:
            free_for_nodes = _find_free_bands(
                usable_rect,
                canvas_rect,
                node_obstacles,
                top_axis,
                primary_pad=0.35,
                min_w=1.4,
                min_h=1.0,
            )
            if free_for_nodes:
                best_r = max(free_for_nodes, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                un_x, un_y, un_w, un_h = best_r[0], best_r[1], best_r[2] - best_r[0], best_r[3] - best_r[1]

        layers = _topological_layers(auto_uncontained, spec.flows)
        num_layers = len(layers)
        un_x2 = un_x + un_w
        un_y2 = un_y + un_h
        if top_axis == "vertical":
            layer_gap = 0.55
            total_layer_h = sum(max(node_dims[n.id][1] for n in lyr) for lyr in layers) + layer_gap * max(0, num_layers - 1)
            scale_y = min(1.0, un_h / total_layer_h) if total_layer_h > un_h and total_layer_h > 0 else 1.0
            cur_y = un_y + (max(0.0, (un_h - total_layer_h) / 2.0) if scale_y == 1.0 else 0.0)
            for lyr in layers:
                lyr_h = max((float(n.h) if n.h is not None else node_dims[n.id][1] * scale_y) for n in lyr)
                node_gap = 0.35
                total_nw = sum(node_dims[n.id][0] for n in lyr) + node_gap * max(0, len(lyr) - 1)
                scale_x = min(1.0, un_w / total_nw) if total_nw > un_w and total_nw > 0 else 1.0
                cur_x = un_x + (max(0.0, (un_w - total_nw) / 2.0) if scale_x == 1.0 else 0.0)
                for n in lyr:
                    nw = float(n.w) if n.w is not None else node_dims[n.id][0] * scale_x
                    nh = float(n.h) if n.h is not None else node_dims[n.id][1] * scale_y
                    sx = _snap(cur_x) if n.x is None else float(n.x)
                    sy = _snap(cur_y) if n.y is None else float(n.y)
                    sw = _snap(nw) if n.w is None else float(n.w)
                    sh = _snap(nh) if n.h is None else float(n.h)
                    if n.x is None and n.w is None and sx + sw > un_x2 + 1e-6:
                        sw = max(0.20, _snap_floor(un_x2 - sx))
                    if n.y is None and n.h is None and sy + sh > un_y2 + 1e-6:
                        sh = max(0.20, _snap_floor(un_y2 - sy))
                    n.x, n.y, n.w, n.h = sx, sy, sw, sh
                    cur_x = max(cur_x, float(n.x) + float(n.w) + node_gap * scale_x)
                cur_y += lyr_h + layer_gap * scale_y
        else:
            l_gaps: List[float] = []
            for idx in range(num_layers - 1):
                l_ids = {n.id for n in layers[idx]}
                r_ids = {n.id for n in layers[idx + 1]}
                l_gaps.append(compute_corridor_span(spec.flows, l_ids, r_ids, base_gap=0.65))
            total_nat_w = sum(max(node_dims[n.id][0] for n in lyr) for lyr in layers) + sum(l_gaps)
            scale_x = min(1.0, un_w / total_nat_w) if total_nat_w > un_w and total_nat_w > 0 else 1.0
            cur_x = un_x + (max(0.0, (un_w - total_nat_w) / 2.0) if scale_x == 1.0 else 0.0)
            for idx, lyr in enumerate(layers):
                lyr_w = max((float(n.w) if n.w is not None else node_dims[n.id][0] * scale_x) for n in lyr)
                node_gap = 0.30
                total_nh = sum(node_dims[n.id][1] for n in lyr) + node_gap * max(0, len(lyr) - 1)
                scale_y = min(1.0, un_h / total_nh) if total_nh > un_h and total_nh > 0 else 1.0
                cur_y = un_y + (max(0.0, (un_h - total_nh) / 2.0) if scale_y == 1.0 else 0.0)
                for n in lyr:
                    nw = float(n.w) if n.w is not None else node_dims[n.id][0] * scale_x
                    nh = float(n.h) if n.h is not None else node_dims[n.id][1] * scale_y
                    sx = _snap(cur_x + max(0.0, (lyr_w - nw) / 2.0)) if n.x is None else float(n.x)
                    sy = _snap(cur_y) if n.y is None else float(n.y)
                    sw = _snap(nw) if n.w is None else float(n.w)
                    sh = _snap(nh) if n.h is None else float(n.h)
                    if n.x is None and n.w is None and sx + sw > un_x2 + 1e-6:
                        sw = max(0.20, _snap_floor(un_x2 - sx))
                    if n.y is None and n.h is None and sy + sh > un_y2 + 1e-6:
                        sh = max(0.20, _snap_floor(un_y2 - sy))
                    n.x, n.y, n.w, n.h = sx, sy, sw, sh
                    cur_y = max(cur_y, float(n.y) + float(n.h) + node_gap * scale_y)
                if idx < num_layers - 1:
                    cur_x += lyr_w + l_gaps[idx] * scale_x

    # 6. Final fallback guarantee: no None coordinates remain
    for c in spec.containers:
        if c.x is None:
            c.x = CANVAS_MARGIN_X
        if c.y is None:
            c.y = top_y
        if c.w is None:
            c.w = 3.0
        if c.h is None:
            c.h = 4.0

    for n in spec.nodes:
        nw, nh = node_dims.get(n.id, (2.0, 1.25))
        if n.x is None:
            n.x = CANVAS_MARGIN_X
        if n.y is None:
            n.y = top_y
        if n.w is None:
            n.w = nw
        if n.h is None:
            n.h = nh

    # 7. Scale solved coordinates back to declared spec units (px / pt) if non-inch
    if is_px_unit:
        for c in spec.containers:
            if c.x is not None:
                c.x = round(float(c.x) * PX_PER_INCH, 1)
            if c.y is not None:
                c.y = round(float(c.y) * PX_PER_INCH, 1)
            if c.w is not None:
                c.w = round(float(c.w) * PX_PER_INCH, 1)
            if c.h is not None:
                c.h = round(float(c.h) * PX_PER_INCH, 1)
        for n in spec.nodes:
            if n.x is not None:
                n.x = round(float(n.x) * PX_PER_INCH, 1)
            if n.y is not None:
                n.y = round(float(n.y) * PX_PER_INCH, 1)
            if n.w is not None:
                n.w = round(float(n.w) * PX_PER_INCH, 1)
            if n.h is not None:
                n.h = round(float(n.h) * PX_PER_INCH, 1)

    return spec
