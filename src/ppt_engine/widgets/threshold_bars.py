"""
Threshold Bars Vector Widget
============================
Renders high-fidelity parametric horizontal bar charts with vertical
threshold/gate lines, status pills, and data labels into DrawingML vector shapes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from src.ppt_engine.theme_engine import strip_shape_shadows, hex_to_rgb


def _resolve_color(color_spec: Any, theme: Any, default_hex: str = "#DC2626") -> RGBColor:
    """Resolves color spec (hex, theme key, or RGBColor) into pptx RGBColor."""
    if isinstance(color_spec, RGBColor):
        return color_spec
    if not color_spec or not isinstance(color_spec, str):
        return hex_to_rgb(default_hex)
    clean = color_spec.strip()
    if clean.startswith("#"):
        return hex_to_rgb(clean)

    # 1. Semantic name map takes precedence over generic fallbacks
    named_map = {
        "emerald": "#10B981",
        "green": "#16A34A",
        "amber": "#D97706",
        "warning": "#F59E0B",
        "red": "#DC2626",
        "brickred": "#DC2626",
        "danger": "#DC2626",
        "blue": "#0284C7",
        "slate": "#64748B",
        "muted": "#94A3B8",
        "neutral": "#64748B",
        "gray": "#64748B",
    }
    clean_lower = clean.lower()
    if clean_lower in named_map:
        return hex_to_rgb(named_map[clean_lower])

    # 2. Check theme palette keys
    if hasattr(theme, "palette") and clean in theme.palette:
        try:
            return theme.get_rgb(clean)
        except Exception:
            pass

    if clean_lower == "accent":
        if hasattr(theme, "get_rgb"):
            try:
                return theme.get_rgb("accent")
            except Exception:
                pass
        return hex_to_rgb("#DC2626" if "red" in getattr(theme, "name", "").lower() else "#0284C7")

    return hex_to_rgb(default_hex)


def _to_inches(val: Any) -> float:
    if hasattr(val, "inches"):
        return float(val.inches)
    if hasattr(val, "pt"):
        return float(val.pt) / 72.0
    if isinstance(val, (int, float)):
        if val > 500:
            return float(val) / 914400.0
        return float(val)
    return float(val)


def render_threshold_bars(
    slide: Any,
    theme: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Renders the threshold bars widget into the specified slide region.

    Config schema:
      title: Optional[str]
      subtitle: Optional[str]
      series: List[Dict[str, Any]]
        - label: str (e.g. 'FACT_TRANSACTION')
        - value: float (0.0 to 1.0 or percentage)
        - display_value: Optional[str] (e.g. '99.9%')
        - subtext: Optional[str] (e.g. '(8.68M)')
        - status: Optional[str] (e.g. 'PASS', 'EXCL')
        - bar_color: Optional[str] ('blue', 'accent', '#0284C7')
        - status_color: Optional[str]
      thresholds: List[Dict[str, Any]]
        - value: float (0.0 to 1.0)
        - label: str (e.g. '>=90% GATE')
        - color: Optional[str] ('emerald', 'amber')
      footnote: Optional[str]
      show_background: Optional[bool] (default True)
    """
    left_in = _to_inches(left)
    top_in = _to_inches(top)
    w_in = _to_inches(width)
    h_in = _to_inches(height)

    # 1. Optional Container Background
    show_bg = config.get("show_background", True)
    if show_bg:
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_in), Inches(top_in), Inches(w_in), Inches(h_in))
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(255, 255, 255)
        border_c = theme.get_rgb("border") if hasattr(theme, "get_rgb") else RGBColor(186, 230, 253)
        bg.line.color.rgb = border_c
        bg.line.width = Pt(1.0)
        strip_shape_shadows(bg)

        # Optional Top Accent Stripe (opt-in)
        if config.get("show_top_stripe", False):
            stripe_color = _resolve_color(config.get("stripe_color", "accent"), theme, default_hex="#0284C7")
            stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_in), Inches(top_in), Inches(w_in), Inches(0.06))
            stripe.fill.solid()
            stripe.fill.fore_color.rgb = stripe_color
            stripe.line.fill.background()
            strip_shape_shadows(stripe)

    # 2. Header Area
    has_title = bool(config.get("title"))
    header_h = 0.62 if config.get("subtitle") else (0.42 if has_title else 0.15)
    if has_title:
        tb_hdr = slide.shapes.add_textbox(
            Inches(left_in + 0.30),
            Inches(top_in + 0.20),
            Inches(min(w_in * 0.45, 3.20)),
            Inches(header_h),
        )
        tf_hdr = tb_hdr.text_frame
        tf_hdr.word_wrap = True
        tf_hdr.margin_left = tf_hdr.margin_right = tf_hdr.margin_top = tf_hdr.margin_bottom = 0

        p1 = tf_hdr.paragraphs[0]
        p1.text = str(config.get("title", ""))
        p1.font.name = getattr(theme, "font_family_header", "Arial")
        p1.font.size = Pt(12.5)
        p1.font.bold = True
        p1.font.color.rgb = theme.get_rgb("primary") if hasattr(theme, "get_rgb") else RGBColor(15, 23, 42)

        if config.get("subtitle"):
            p2 = tf_hdr.add_paragraph()
            p2.text = str(config.get("subtitle", ""))
            p2.font.name = getattr(theme, "font_family", "Arial")
            p2.font.size = Pt(9.0)
            p2.font.color.rgb = theme.get_rgb("secondary") if hasattr(theme, "get_rgb") else RGBColor(100, 116, 139)

    # 3. Series rows layout
    series = config.get("series") or []
    thresholds = config.get("thresholds") or []
    has_foot = bool(config.get("footnote"))
    foot_h = 0.38 if has_foot else 0.05
    th_headroom = 0.52 if thresholds else 0.14

    chart_y = top_in + header_h + th_headroom
    avail_h = h_in - header_h - th_headroom - foot_h
    n_rows = max(1, len(series))
    target_total_h = min(avail_h, max(2.50, n_rows * 0.70))
    row_h = min(0.48, max(0.32, (target_total_h * 0.60) / n_rows))
    row_gap = min(0.26, max(0.10, (target_total_h - (row_h * n_rows)) / max(1, n_rows - 1)))

    # Dynamic column splits calibrated to avoid text-to-bar and text-to-edge collisions
    pad_left = 0.18
    pad_right = 0.18
    content_w = w_in - pad_left - pad_right

    max_lbl_len = max((len(str(s.get("label", ""))) for s in series), default=12)
    max_val_len = max(
        (len(f"{s.get('display_value', '')} {s.get('subtext', '')} [{s.get('status', '')}]".strip()) for s in series),
        default=16,
    )

    col_gap = 0.10
    # Proportional dynamic sizing: strictly calibrated for 1 uniform font size across all labels
    label_font_name = getattr(theme, "font_family_header", "Arial")
    label_font_size_pt = float(config.get("label_font_size", 8.5))

    req_lbl_w = (max_lbl_len * 0.076) + 0.08
    lbl_w = min(content_w * 0.40, max(1.65, req_lbl_w))

    req_val_w = max_val_len * 0.065
    val_w = min(content_w * 0.34, max(content_w * 0.24, req_val_w))

    bar_track_w = max(1.20, content_w - lbl_w - val_w - (col_gap * 2))

    bar_x = left_in + pad_left + lbl_w + col_gap
    val_x = bar_x + bar_track_w + col_gap

    for idx, s in enumerate(series):
        curr_y = chart_y + idx * (row_h + row_gap)
        lbl_text = s.get("label", f"Series {idx+1}")
        raw_val = float(s.get("value", 0.0))
        val_pct = raw_val if raw_val <= 1.0 else (raw_val / 100.0)
        disp_val = s.get("display_value", f"{val_pct*100:.1f}%")
        subtext = s.get("subtext", "")
        status_tag = s.get("status", "")

        bar_rgb = _resolve_color(s.get("bar_color", "accent"), theme, default_hex="#0284C7")
        tag_rgb = _resolve_color(s.get("status_color", ("emerald" if status_tag == "PASS" else "danger")), theme, default_hex="#10B981")

        # 1. Row Label (strictly 1 uniform font type and 1 uniform font size across all series rows)
        tb_lbl = slide.shapes.add_textbox(Inches(left_in + pad_left), Inches(curr_y), Inches(lbl_w), Inches(row_h))
        tf_lbl = tb_lbl.text_frame
        tf_lbl.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_lbl.word_wrap = False
        tf_lbl.margin_left = tf_lbl.margin_top = tf_lbl.margin_bottom = 0
        tf_lbl.margin_right = Pt(4)
        p_lbl = tf_lbl.paragraphs[0]
        p_lbl.text = lbl_text
        p_lbl.font.name = label_font_name
        p_lbl.font.size = Pt(label_font_size_pt)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = RGBColor(30, 41, 59)

        # 2. Track Background
        bar_h = row_h * 0.65
        bar_y_offset = (row_h - bar_h) / 2.0
        bg_track = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(bar_x),
            Inches(curr_y + bar_y_offset),
            Inches(bar_track_w),
            Inches(bar_h),
        )
        bg_track.fill.solid()
        bg_track.fill.fore_color.rgb = RGBColor(241, 245, 249)
        bg_track.line.fill.background()
        strip_shape_shadows(bg_track)

        # 3. Value Bar
        fill_w = max(0.01, min(bar_track_w, bar_track_w * val_pct))
        bar_fill = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(bar_x),
            Inches(curr_y + bar_y_offset),
            Inches(fill_w),
            Inches(bar_h),
        )
        bar_fill.fill.solid()
        bar_fill.fill.fore_color.rgb = bar_rgb
        bar_fill.line.fill.background()
        strip_shape_shadows(bar_fill)

        # 4. Value Text & Status
        tb_val = slide.shapes.add_textbox(Inches(val_x), Inches(curr_y), Inches(val_w), Inches(row_h))
        tf_val = tb_val.text_frame
        tf_val.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_val.word_wrap = False
        tf_val.margin_left = Pt(4)
        tf_val.margin_right = tf_val.margin_top = tf_val.margin_bottom = 0
        p_val = tf_val.paragraphs[0]
        p_val.text = f"{disp_val} "
        p_val.font.name = getattr(theme, "font_family_header", "Arial")
        p_val.font.size = Pt(9.0)
        p_val.font.bold = True
        p_val.font.color.rgb = RGBColor(15, 23, 42)

        if subtext:
            r_sub = p_val.add_run()
            r_sub.text = f"{subtext} "
            r_sub.font.size = Pt(8.0)
            r_sub.font.color.rgb = RGBColor(100, 116, 139)

        if status_tag:
            r_tag = p_val.add_run()
            r_tag.text = f"[{status_tag}]"
            r_tag.font.bold = True
            r_tag.font.size = Pt(8.2)
            r_tag.font.color.rgb = tag_rgb

    # 4. Vertical Threshold Markers
    if thresholds and len(series) > 0:
        total_rows_h = n_rows * row_h + (n_rows - 1) * row_gap
        line_top_y = chart_y
        line_h = total_rows_h

        # Sort thresholds by value ascending
        sorted_thresholds = sorted(
            thresholds,
            key=lambda t: float(t.get("value", 0.0)) if float(t.get("value", 0.0)) <= 1.0 else (float(t.get("value", 0.0)) / 100.0),
        )

        parsed_ths = []
        for th in sorted_thresholds:
            th_val = float(th.get("value", 0.0))
            th_pct = th_val if th_val <= 1.0 else (th_val / 100.0)
            th_label = th.get("label", f"{int(th_pct*100)}%")
            th_col_key = th.get("color", "emerald")
            th_rgb = _resolve_color(th_col_key, theme, default_hex="#10B981")
            th_x = bar_x + (bar_track_w * th_pct)

            pill_w = max(0.85, min(1.35, len(th_label) * 0.072))
            pill_h = 0.20
            parsed_ths.append({
                "pct": th_pct,
                "label": th_label,
                "col_key": th_col_key,
                "rgb": th_rgb,
                "x": th_x,
                "w": pill_w,
                "h": pill_h,
            })

        base_pill_y = line_top_y - 0.20 - 0.04
        tier1_pill_y = base_pill_y - 0.23

        # Compute horizontal placement and prevent pill-to-pill and line-to-pill collisions
        for i, th in enumerate(parsed_ths):
            th_x = th["x"]
            pw = th["w"]

            # If there is a next threshold close by, shift this pill left so it doesn't cross the next line
            if i + 1 < len(parsed_ths):
                next_x = parsed_ths[i + 1]["x"]
                line_gap = next_x - th_x
                if line_gap < (pw + parsed_ths[i + 1]["w"]) / 2.0 + 0.04:
                    px = th_x - pw + 0.06
                    th["pill_x"] = max(left_in + pad_left, px)
                    th["pill_y"] = base_pill_y
                    continue

            # If there is a previous threshold close by, shift this pill right so it clears the previous line
            if i > 0:
                prev_x = parsed_ths[i - 1]["x"]
                line_gap = th_x - prev_x
                if line_gap < (pw + parsed_ths[i - 1]["w"]) / 2.0 + 0.04:
                    px = th_x - 0.06
                    th["pill_x"] = min(left_in + w_in - pad_right - pw, px)
                    th["pill_y"] = base_pill_y
                    continue

            # Default: centered directly above line
            th["pill_x"] = max(left_in + pad_left, min(left_in + w_in - pad_right - pw, th_x - (pw / 2.0)))
            th["pill_y"] = base_pill_y

        # Secondary safety: if pills still touch, stagger to Tier 1
        for i in range(1, len(parsed_ths)):
            prev = parsed_ths[i - 1]
            curr = parsed_ths[i]
            if curr["pill_x"] < prev["pill_x"] + prev["w"] + 0.02:
                curr["pill_y"] = tier1_pill_y

        # Render threshold lines and pills
        for th in parsed_ths:
            th_x = th["x"]
            th_rgb = th["rgb"]
            th_col_key = th["col_key"]
            pill_x = th["pill_x"]
            pill_y = th["pill_y"]
            pill_w = th["w"]
            pill_h = th["h"]
            th_label = th["label"]

            eff_top_y = pill_y + pill_h
            eff_bottom_y = line_top_y + line_h
            eff_h = max(0.1, eff_bottom_y - eff_top_y)

            # 1. Vertical Hairline (starts exactly at bottom of pill)
            line = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(th_x),
                Inches(eff_top_y),
                Inches(0.015),
                Inches(eff_h),
            )
            line.fill.solid()
            line.fill.fore_color.rgb = th_rgb
            line.line.fill.background()
            strip_shape_shadows(line)

            # 2. Threshold Pill Badge
            pill = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(pill_x),
                Inches(pill_y),
                Inches(pill_w),
                Inches(pill_h),
            )
            pill.fill.solid()
            col_str = str(th_col_key).lower()
            if "emerald" in col_str or "green" in col_str or "success" in col_str:
                pill_bg = RGBColor(236, 253, 245)
            elif "amber" in col_str or "warning" in col_str:
                pill_bg = RGBColor(254, 243, 199)
            elif "red" in col_str or "danger" in col_str or "accent" in col_str or "brick" in col_str:
                pill_bg = RGBColor(254, 242, 242)
            else:
                pill_bg = RGBColor(241, 245, 249)
            pill.fill.fore_color.rgb = pill_bg
            pill.line.color.rgb = th_rgb
            pill.line.width = Pt(0.75)
            strip_shape_shadows(pill)

            tf_pill = pill.text_frame
            tf_pill.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf_pill.word_wrap = False
            tf_pill.margin_left = tf_pill.margin_right = tf_pill.margin_top = tf_pill.margin_bottom = 0
            p_pill = tf_pill.paragraphs[0]
            p_pill.text = th_label
            p_pill.font.name = getattr(theme, "font_family_header", "Arial")
            p_pill.font.size = Pt(8.0)
            p_pill.font.bold = True
            p_pill.font.color.rgb = th_rgb
            p_pill.alignment = PP_ALIGN.CENTER

    # 5. Optional Footnote
    if has_foot:
        tb_foot = slide.shapes.add_textbox(
            Inches(left_in + pad_left),
            Inches(top_in + h_in - foot_h - 0.04),
            Inches(w_in - pad_left - pad_right),
            Inches(foot_h),
        )
        tf_f = tb_foot.text_frame
        tf_f.margin_left = tf_f.margin_right = tf_f.margin_top = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        p_f.text = str(config["footnote"])
        p_f.font.name = getattr(theme, "font_family", "Arial")
        p_f.font.size = Pt(8.5)
        p_f.font.color.rgb = RGBColor(100, 116, 139)

    return {
        "left": left_in,
        "top": top_in,
        "width": w_in,
        "height": h_in,
    }
