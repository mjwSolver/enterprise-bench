"""
Diagram Engine V2 - Tier 2 Adversarial Visual QA Subagent Verifier
===================================================================
Autonomous adversarial visual verification harness that combines local computer
vision perceptual heuristics with multimodal subagent auditing to rigorously
validate diagram plates against Milestone 33 post-mortem failure modes.

Post-Mortem Failure Modes Audited:
1. Database Cylinder Compression (w <= 170px vs 260px canvas crowding)
2. Connector Span Clearance (140px-175px clearance, zero arrow swallowing)
3. Return Loop Gutter Placement (y=230-240px gutter vs y <= 20px ceiling collision)
4. Vertical Modernization Bridges (unclipped Col 2 compute and Col 3 data bridges)
5. Boundary Edge Clearances (zero label pills straddling dashed zone margins)
6. Diagnostic Status Triad Compliance (Red/Amber/Blue/Green semantic coloring)
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Union

from PIL import Image, ImageStat

from src.ppt_engine.diagram_v2.models import DiagramSpec
from src.ppt_engine.diagram_v2.geometry import GeometryNormalizer, Box, Point
from src.ppt_engine.diagram_v2.auditor import AuditIssue, Tier1GeometricLinter
from src.ppt_engine.diagram_v2.contrast import (
    contrast_ratio,
    WCAG_AA_NORMAL_TEXT,
    WCAG_AA_LARGE_TEXT,
)

logger = logging.getLogger(__name__)


@dataclass
class VisualFinding:
    """Represents a perceptual, aesthetic, or visual hierarchy flaw detected in the rendered plate."""
    dimension: Literal[
        "GEOMETRIC_CLEARANCE",
        "ARROW_FLOW_INTEGRITY",
        "COMPONENT_PROPORTIONS",
        "CEILING_GUTTER_SAFETY",
        "VERTICAL_BRIDGES",
        "TYPOGRAPHY_LEGIBILITY",
        "DIAGNOSTIC_COLOR_HIERARCHY",
    ]
    severity: Literal["CRITICAL", "WARNING", "ADVISORY"]
    element_or_region: str
    flaw_description: str
    prescriptive_fix: str
    confidence: float = 1.0


@dataclass
class VisualQAResult:
    """Consolidated audit outcome combining Tier 1 geometric linting and Tier 2 adversarial visual QA."""
    spec_id: str
    spec_name: str
    passed: bool
    verdict: Literal["VERIFIED_PASS", "CONDITIONAL_PASS", "REVISE_REQUIRED", "FAIL"]
    score: float  # 0.0 to 100.0
    dimension_scores: Dict[str, float]
    tier1_issues: List[AuditIssue]
    tier2_findings: List[VisualFinding]
    perceptual_metrics: Dict[str, Any]
    raster_image_path: Optional[Path] = None
    subagent_prompt_path: Optional[Path] = None
    execution_time_sec: float = 0.0

    @property
    def total_critical_count(self) -> int:
        c1 = sum(1 for i in self.tier1_issues if i.severity == "CRITICAL")
        c2 = sum(1 for f in self.tier2_findings if f.severity == "CRITICAL")
        return c1 + c2

    @property
    def total_warning_count(self) -> int:
        w1 = sum(1 for i in self.tier1_issues if i.severity == "WARNING")
        w2 = sum(1 for f in self.tier2_findings if f.severity == "WARNING")
        return w1 + w2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_id": self.spec_id,
            "spec_name": self.spec_name,
            "passed": self.passed,
            "verdict": self.verdict,
            "score": round(self.score, 1),
            "dimension_scores": {k: round(v, 1) for k, v in self.dimension_scores.items()},
            "critical_count": self.total_critical_count,
            "warning_count": self.total_warning_count,
            "tier1_issues": [i.to_dict() for i in self.tier1_issues],
            "tier2_findings": [asdict(f) for f in self.tier2_findings],
            "perceptual_metrics": self.perceptual_metrics,
            "raster_image_path": str(self.raster_image_path) if self.raster_image_path else None,
            "subagent_prompt_path": str(self.subagent_prompt_path) if self.subagent_prompt_path else None,
            "execution_time_sec": round(self.execution_time_sec, 3),
        }


def audit_wcag_and_legibility(spec: DiagramSpec) -> Tuple[List[VisualFinding], Dict[str, Any]]:
    """
    Audits WCAG 2.1 AA contrast ratios (>= 4.5:1 normal text, >= 3.0:1 large/bold)
    and multi-resolution font legibility (1080p, 720p, and thumbnail pixel heights)
    across header, containers, nodes, badges, bullet lists, and labeled flows.
    """
    findings: List[VisualFinding] = []
    checks_total = 0
    checks_passed = 0
    min_cr = 21.0
    font_pts: List[float] = []
    canvas_bg = getattr(getattr(spec, "canvas", None), "background", None) or "#FFFFFF"

    primary_hex = "#0F172A"
    muted_hex = "#64748B"
    try:
        from src.ppt_engine.theme_engine import load_theme
        theme_obj = load_theme(spec.theme) if getattr(spec, "theme", None) else None
        if theme_obj is not None:
            primary_hex = theme_obj.get_hex("primary", "#0F172A")
            muted_hex = theme_obj.get_hex("muted", "#64748B")
    except Exception:
        pass

    def _check_pair(elem_id: str, label: str, fg_hex: Optional[str], bg_hex: Optional[str], pt: float, is_large: bool = False) -> None:
        nonlocal checks_total, checks_passed, min_cr
        eff_bg = bg_hex or canvas_bg
        if not fg_hex or not eff_bg:
            return
        cr = contrast_ratio(fg_hex, eff_bg)
        checks_total += 1
        min_cr = min(min_cr, cr)
        req = WCAG_AA_LARGE_TEXT if is_large else WCAG_AA_NORMAL_TEXT
        if cr >= req:
            checks_passed += 1
        elif cr < 3.0:
            findings.append(VisualFinding(
                dimension="TYPOGRAPHY_LEGIBILITY",
                severity="CRITICAL",
                element_or_region=elem_id,
                flaw_description=f"{label} contrast ratio {cr:.2f}:1 ({fg_hex} on {eff_bg}) fails minimum 3.0:1 legibility floor.",
                prescriptive_fix=f"Darken text or adjust fill to restore >= {req:.1f}:1 WCAG AA contrast.",
            ))
        else:
            findings.append(VisualFinding(
                dimension="TYPOGRAPHY_LEGIBILITY",
                severity="WARNING",
                element_or_region=elem_id,
                flaw_description=f"{label} contrast ratio {cr:.2f}:1 ({fg_hex} on {eff_bg}) is below WCAG AA {req:.1f}:1.",
                prescriptive_fix=f"Use higher-contrast slate/white ink to achieve >= {req:.1f}:1.",
            ))

    if getattr(spec, "header", None) and getattr(spec.header, "show", False):
        if getattr(spec.header, "action_title", None):
            font_pts.append(20.0)
            _check_pair("header:action_title", "Header action title", primary_hex, canvas_bg, 20.0, is_large=True)
        if getattr(spec.header, "subtitle", None):
            font_pts.append(11.0)
            _check_pair("header:subtitle", "Header subtitle", muted_hex, canvas_bg, 11.0, is_large=False)

    for c in spec.containers:
        raw_c_pt = getattr(c, "font_size", None)
        c_pt = float(raw_c_pt) if raw_c_pt is not None else 12.0
        font_pts.append(c_pt)
        _check_pair(f"container:{c.id}", "Container label", c.font_color, c.fill_hex or canvas_bg, c_pt, is_large=(c_pt >= 14.0))

    for n in spec.nodes:
        t_pt = n.resolved_title_pt()
        s_pt = n.resolved_subtitle_pt()
        font_pts.append(t_pt)
        n_bg = n.fill_hex or canvas_bg
        _check_pair(f"node:{n.id}", "Node title", n.title_color, n_bg, t_pt, is_large=(t_pt >= 14.0))
        if n.subtitle or n.bullets:
            font_pts.append(s_pt)
            _check_pair(f"node:{n.id}", "Node subtitle", n.subtitle_color, n_bg, s_pt, is_large=False)
            if not spec.allow_dense_typography and s_pt < 10.0 and s_pt >= 8.0:
                findings.append(VisualFinding(
                    dimension="TYPOGRAPHY_LEGIBILITY",
                    severity="ADVISORY",
                    element_or_region=f"node:{n.id}",
                    flaw_description=f"Node subtitle is {s_pt:.1f}pt ({s_pt * 96.0 / 72.0:.1f}px at 720p, {s_pt * 48.0 / 72.0:.1f}px thumbnail).",
                    prescriptive_fix="Raise subtitle to >= 10.0pt or enable allow_dense_typography for appendix runbooks.",
                ))

    for idx, b in enumerate(spec.badges):
        b_id = b.id or f"badge_{idx}"
        b_pt = float(b.font_pt) if b.font_pt is not None else 9.0
        font_pts.append(b_pt)
        _check_pair(f"badge:{b_id}", "Badge text", b.text_hex, b.bg_hex or canvas_bg, b_pt, is_large=False)

    for idx, bl in enumerate(getattr(spec, "bullet_lists", []) or []):
        bl_id = bl.id or f"bullet_list_{idx}"
        bl_pt = float(bl.font_size) if bl.font_size is not None else 11.5
        font_pts.append(bl_pt)
        _check_pair(f"bullet_list:{bl_id}", "Bullet list text", bl.font_color, canvas_bg, bl_pt, is_large=(bl_pt >= 14.0))

    for idx, f in enumerate(spec.flows):
        if f.label:
            f_id = f.id or f"flow_{idx}"
            f_pt = float(f.font_pt) if f.font_pt is not None else 9.0
            font_pts.append(f_pt)
            _check_pair(f"flow:{f_id}", "Flow pill text", f.label_text_hex, f.label_bg_hex or canvas_bg, f_pt, is_large=False)

    min_font_pt = min(font_pts) if font_pts else 12.0
    if min_font_pt < 8.0:
        findings.append(VisualFinding(
            dimension="TYPOGRAPHY_LEGIBILITY",
            severity="CRITICAL",
            element_or_region="Global Typography",
            flaw_description=f"Minimum font size {min_font_pt:.1f}pt ({min_font_pt * 96.0 / 72.0:.1f}px at 720p) violates 8.0pt global floor.",
            prescriptive_fix="Increase all text sizes to >= 8.0pt.",
        ))

    pass_rate = (checks_passed / checks_total * 100.0) if checks_total > 0 else 100.0
    metrics: Dict[str, Any] = {
        "wcag_checks_total": checks_total,
        "wcag_checks_passed": checks_passed,
        "wcag_aa_pass_rate_pct": round(pass_rate, 1),
        "min_contrast_ratio": round(min_cr, 2) if checks_total > 0 else 21.0,
        "min_font_pt": round(min_font_pt, 1),
        "min_font_px_720p": round(min_font_pt * 96.0 / 72.0, 1),
        "min_font_px_1080p": round(min_font_pt * 144.0 / 72.0, 1),
    }
    return findings, metrics


class PerceptualImageAnalyzer:
    """
    Perceptual computer vision analyzer operating directly on rasterized PNG slide/diagram plates.
    Extracts ink density heatmaps, margin clearance metrics, and color distribution stats.
    """

    @staticmethod
    def _parse_hex_tuple(hex_color: Optional[str]) -> Optional[Tuple[int, int, int]]:
        if not hex_color or not isinstance(hex_color, str):
            return None
        clean = hex_color.strip().lstrip("#")
        if len(clean) == 3:
            clean = "".join(c * 2 for c in clean)
        if len(clean) != 6:
            return None
        try:
            return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
        except ValueError:
            return None

    @staticmethod
    def _is_near_color_segment(
        r: int,
        g: int,
        b: int,
        c0: Tuple[int, int, int],
        c1: Tuple[int, int, int],
        tol_manhattan: int = 24,
    ) -> bool:
        dx, dy, dz = c1[0] - c0[0], c1[1] - c0[1], c1[2] - c0[2]
        denom = dx * dx + dy * dy + dz * dz
        if denom == 0:
            return abs(r - c0[0]) + abs(g - c0[1]) + abs(b - c0[2]) <= tol_manhattan
        t = ((r - c0[0]) * dx + (g - c0[1]) * dy + (b - c0[2]) * dz) / denom
        if t < -0.15 or t > 1.15:
            return False
        t_clamped = max(0.0, min(1.0, t))
        pr = c0[0] + t_clamped * dx
        pg = c0[1] + t_clamped * dy
        pb = c0[2] + t_clamped * dz
        return (abs(r - pr) + abs(g - pg) + abs(b - pb)) <= tol_manhattan

    @staticmethod
    def _is_ink_pixel(
        r: int,
        g: int,
        b: int,
        a: int,
        bg_rgb: Optional[Tuple[int, int, int]] = None,
        extra_bg_rgbs: Optional[Sequence[Tuple[int, int, int]]] = None,
        grid_segment: Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = None,
    ) -> bool:
        """Determines if an RGBA pixel represents printable or non-background ink."""
        if a < 40:
            return False
        if bg_rgb is not None:
            if abs(r - bg_rgb[0]) + abs(g - bg_rgb[1]) + abs(b - bg_rgb[2]) <= 42:
                return False
        if extra_bg_rgbs:
            for ebg in extra_bg_rgbs:
                if abs(r - ebg[0]) + abs(g - ebg[1]) + abs(b - ebg[2]) <= 32:
                    return False
        if grid_segment is not None:
            if PerceptualImageAnalyzer._is_near_color_segment(r, g, b, grid_segment[0], grid_segment[1]):
                return False
        if bg_rgb is not None and (sum(bg_rgb) / 3.0) < 128.0:
            return True
        lum = (r + g + b) / 3.0
        sat = max(r, g, b) - min(r, g, b)
        # Exclude pure white background and faint background grid lines (#E2E8F0, lum>230, sat<18)
        if lum > 228 and sat < 20:
            return False
        return lum < 215 or sat > 25

    @staticmethod
    def analyze_raster_image(
        png_path: Path,
        canvas_bg: Optional[str] = None,
        show_grid: Optional[bool] = None,
        grid_color: Optional[str] = None,
        grid_opacity: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Performs localized perceptual heuristics on the generated diagram raster image."""
        if not png_path.exists():
            return {"error": f"Raster image not found: {png_path}"}

        bg_rgb = PerceptualImageAnalyzer._parse_hex_tuple(canvas_bg)

        try:
            with Image.open(png_path) as img:
                img_rgba = img.convert("RGBA")
                w, h = img_rgba.size
                is_ink = PerceptualImageAnalyzer._is_ink_pixel

                extra_bg_rgbs: List[Tuple[int, int, int]] = []
                grid_segment: Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = None
                if bg_rgb is not None:
                    # SVGCompiler overlays #F8FAFC at opacity=0.45 when show_grid=True
                    blended_bg = (
                        int(round(0.55 * bg_rgb[0] + 0.45 * 248)),
                        int(round(0.55 * bg_rgb[1] + 0.45 * 250)),
                        int(round(0.55 * bg_rgb[2] + 0.45 * 252)),
                    )
                    use_grid = show_grid
                    if use_grid is None:
                        sample_bg = img_rgba.resize((max(1, w // 16), max(1, h // 16)), resample=Image.Resampling.NEAREST)
                        blended_hits = 0
                        raw_hits = 0
                        total_s = 0
                        for sr, sg, sb, sa in sample_bg.getdata():
                            if sa < 40:
                                continue
                            total_s += 1
                            if abs(sr - blended_bg[0]) + abs(sg - blended_bg[1]) + abs(sb - blended_bg[2]) <= 24:
                                blended_hits += 1
                            if abs(sr - bg_rgb[0]) + abs(sg - bg_rgb[1]) + abs(sb - bg_rgb[2]) <= 24:
                                raw_hits += 1
                        if total_s > 0 and blended_hits > raw_hits and blended_hits >= total_s * 0.25:
                            use_grid = True
                    if use_grid:
                        extra_bg_rgbs.append(blended_bg)
                        g_col = PerceptualImageAnalyzer._parse_hex_tuple(grid_color) or (226, 232, 240)
                        g_op = float(grid_opacity) if grid_opacity is not None else 0.6
                        line_rgb = (
                            int(round(g_op * g_col[0] + (1.0 - g_op) * blended_bg[0])),
                            int(round(g_op * g_col[1] + (1.0 - g_op) * blended_bg[1])),
                            int(round(g_op * g_col[2] + (1.0 - g_op) * blended_bg[2])),
                        )
                        grid_segment = (blended_bg, line_rgb)

                # 1. Canvas Ceiling & Margin Ink Analysis
                # Detect non-background content pixels in central/right ceiling band (x: 30%-95%, top 4.5%)
                # Excluding legitimate top-left brand stripes & slide action title
                ceiling_h = max(10, int(h * 0.045))
                c_x1 = int(w * 0.30)
                c_x2 = max(c_x1 + 1, int(w * 0.95))
                c_y2 = max(1, min(h, ceiling_h))
                ceiling_crop = img_rgba.crop((c_x1, 0, c_x2, c_y2))
                ceiling_non_bg = sum(
                    1 for r, g, b, a in ceiling_crop.getdata()
                    if is_ink(r, g, b, a, bg_rgb=bg_rgb, extra_bg_rgbs=extra_bg_rgbs, grid_segment=grid_segment)
                )

                # Outer 1.5% perimeter margin check
                margin_px = max(8, int(min(w, h) * 0.015))
                left_crop = img_rgba.crop((0, 0, min(w, margin_px), h))
                right_crop = img_rgba.crop((max(0, w - margin_px), 0, w, h))
                bottom_crop = img_rgba.crop((0, max(0, h - margin_px), w, h))

                edge_pixels = 0
                for crop in (left_crop, right_crop, bottom_crop):
                    edge_pixels += sum(
                        1 for r, g, b, a in crop.getdata()
                        if is_ink(r, g, b, a, bg_rgb=bg_rgb, extra_bg_rgbs=extra_bg_rgbs, grid_segment=grid_segment)
                    )

                # 2. Quadrant Ink Density Heatmap (3x2 grid)
                grid_rows, grid_cols = 2, 3
                cell_w = w // grid_cols
                cell_h = h // grid_rows
                cell_densities: List[float] = []

                for r in range(grid_rows):
                    for c in range(grid_cols):
                        box = (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)
                        cell_crop = img_rgba.crop(box)
                        ink_count = sum(
                            1 for pr, pg, pb, pa in cell_crop.getdata()
                            if is_ink(pr, pg, pb, pa, bg_rgb=bg_rgb, extra_bg_rgbs=extra_bg_rgbs, grid_segment=grid_segment)
                        )
                        cell_area = cell_w * cell_h
                        cell_density = (ink_count / cell_area) * 100.0 if cell_area > 0 else 0.0
                        cell_densities.append(round(cell_density, 2))

                mean_density = sum(cell_densities) / len(cell_densities) if cell_densities else 1.0
                max_density = max(cell_densities) if cell_densities else 0.0
                density_variance = sum((d - mean_density) ** 2 for d in cell_densities) / len(cell_densities) if cell_densities else 0.0
                density_max_to_mean_ratio = round(max_density / mean_density, 2) if mean_density > 0.0 else 1.0

                # 3. Diagnostic Palette Detection (Red, Amber, Blue, Green ink counts)
                red_pixels = 0
                amber_pixels = 0
                blue_pixels = 0
                green_pixels = 0

                # Sample every 4th pixel via fast nearest-neighbor downsampling
                step = 4
                sampled_w = max(1, w // step)
                sampled_h = max(1, h // step)
                sampled_img = img_rgba.resize((sampled_w, sampled_h), resample=Image.Resampling.NEAREST)
                for pr, pg, pb, pa in sampled_img.getdata():
                    if pa < 50:
                        continue
                    # Red range (#DC2626 / #E11D48)
                    if pr > 180 and pg < 60 and pb < 80:
                        red_pixels += 1
                    # Amber range (#D97706 / #F59E0B)
                    elif pr > 190 and 110 < pg < 170 and pb < 40:
                        amber_pixels += 1
                    # Blue range (#0284C7 / #2563EB)
                    elif pr < 60 and 90 < pg < 160 and pb > 180:
                        blue_pixels += 1
                    # Green range (#16A34A / #10B981)
                    elif pr < 50 and pg > 140 and pb < 100:
                        green_pixels += 1

                scale_factor = (w * h) / (sampled_w * sampled_h) if (sampled_w * sampled_h) > 0 else 1.0
                return {
                    "image_dimensions": [w, h],
                    "ceiling_non_bg_pixels": ceiling_non_bg,
                    "perimeter_edge_pixels": edge_pixels,
                    "cell_densities_pct": cell_densities,
                    "density_variance": round(density_variance, 2),
                    "density_max_to_mean_ratio": density_max_to_mean_ratio,
                    "diagnostic_ink_counts": {
                        "red": int(round(red_pixels * scale_factor)),
                        "amber": int(round(amber_pixels * scale_factor)),
                        "blue": int(round(blue_pixels * scale_factor)),
                        "green": int(round(green_pixels * scale_factor)),
                    },
                }
        except Exception as e:
            logger.debug("Perceptual analysis error: %s", e)
            return {"error": str(e)}


class AdversarialVisualQASubagent:
    """
    Orchestrates the Tier 2 Adversarial Visual QA subagent protocol.
    Constructs the adversarial inspection prompt, generates structured inspection briefings,
    and runs local heuristic evaluations against Milestone 33 post-mortem rules.
    """

    ADVERSARIAL_ROLE = "Adversarial Visual QA Auditor"

    @staticmethod
    def build_subagent_briefing(
        spec: DiagramSpec,
        image_path: Path,
        tier1_issues: List[AuditIssue],
        perceptual_metrics: Dict[str, Any],
    ) -> str:
        """
        Builds the canonical adversarial prompt briefing markdown artifact
        for delegating visual QA to a vision-capable subagent.
        """
        prompt = f"""# ADVERSARIAL VISUAL QA BRIEFING: {spec.name} ({spec.id})

> **Auditor Role:** `{AdversarialVisualQASubagent.ADVERSARIAL_ROLE}`  
> **Mission:** Aggressively inspect the generated diagram raster plate to uncover layout, geometric, perceptual, and aesthetic defects that bypass static compilers.  
> **Canonical Target Image:** `{image_path}`  

---

## 1. Operating Stance & Adversarial Directive
Assume that this diagram plate contains subtle visual defects and spacing anomalies that slipped past preliminary filters. Your job is NOT to approve superficially, but to ruthlessly interrogate the plate against the **Milestone 33 Post-Mortem Standards**:

1. **Database Cylinder Compression Standard ($w \le 170\\text{{px}}$ / $1.88''$):**
   - Check if any database cylinder (e.g. legacy HDFS, monolithic cluster DB, Databricks Delta) balloons to $260\\text{{px}}$ or overwhelms adjacent columns.
   - Cylinder shapes must exhibit balanced optical proportions with clear 3D top rim geometry and centered side-slot logos.

2. **Expanded Connector Clearances ($140\\text{{px}} - 175\\text{{px}}$):**
   - Check whether connector status badges (e.g. `1a. Legacy EXE Call`, `1b. HTTPS REST`) drown or swallow arrow shafts.
   - Verify that all arrowheads have at least $20\\text{{px}}$ ($0.22''$) of unoccluded clearance from label pills.

3. **Ceiling & Perimeter Safety ($y \\ge 25\\text{{px}}$):**
   - Verify that return loops or feedback flows are NEVER routed along the top canvas ceiling ($y \\le 20\\text{{px}}$).
   - Return flows must be cleanly routed through lower inter-track gutters ($y \\approx 230-240\\text{{px}}$).

4. **Solid Vertical Modernization Bridges:**
   - Verify that vertical inter-track flows linking upper legacy systems to lower target architectures (e.g. Col 2 compute, Col 3 storage) are straight, unbroken, and clearly visible.

5. **Diagnostic Status Triad:**
   - Verify semantic color coding: **Red (`#DC2626`)** for bottleneck/defect/P1 debt, **Amber (`#D97706`)** for boundary/wait/sync, **Blue (`#0284C7`)** for active flow/DB/lakehouse, **Green (`#16A34A`)** for target/reconciled state.

---

## 2. Pre-Flight Tier 1 Geometric Audit Ledger
The deterministic Tier 1 geometric linter reported **{len(tier1_issues)} issue(s)**:

"""
        if tier1_issues:
            for issue in tier1_issues:
                prompt += f"- **[{issue.severity}] {issue.category}** on `{issue.element_id}`: {issue.description}\n  *Suggested Fix:* {issue.suggested_fix}\n"
        else:
            prompt += "- *Zero Tier 1 geometric collisions detected.* (Proceed to visual & perceptual scrutiny).\n"

        prompt += f"""
---

## 3. Automated Perceptual Computer Vision Metrics
- **Canvas Ceiling Non-Background Pixels:** `{perceptual_metrics.get('ceiling_non_bg_pixels', 0)}` (Threshold: <= 50 px)
- **Perimeter Border Pixels:** `{perceptual_metrics.get('perimeter_edge_pixels', 0)}`
- **Quadrant Ink Densities (%):** `{perceptual_metrics.get('cell_densities_pct', [])}`
- **Density Variance:** `{perceptual_metrics.get('density_variance', 0.0)}`
- **Max-to-Mean Density Ratio:** `{perceptual_metrics.get('density_max_to_mean_ratio', 1.0)}`
- **WCAG AA Contrast Pass Rate:** `{perceptual_metrics.get('wcag_aa_pass_rate_pct', 100.0)}%` (Min CR: `{perceptual_metrics.get('min_contrast_ratio', 21.0)}:1`)
- **Multi-Resolution Font Legibility:** Min `{perceptual_metrics.get('min_font_pt', 12.0)}pt` (`{perceptual_metrics.get('min_font_px_720p', 16.0)}px` @ 720p, `{perceptual_metrics.get('min_font_px_1080p', 24.0)}px` @ 1080p)

---

## 4. Structured Output Contract
Return your evaluation in the following strict JSON schema:

```json
{{
  "verdict": "VERIFIED_PASS | CONDITIONAL_PASS | REVISE_REQUIRED | FAIL",
  "score": 85.5,
  "dimension_scores": {{
    "geometric_clearance": 90.0,
    "arrow_flow_integrity": 80.0,
    "component_proportions": 85.0,
    "ceiling_gutter_safety": 95.0,
    "vertical_bridges": 90.0,
    "typography_legibility": 85.0,
    "diagnostic_color_hierarchy": 90.0
  }},
  "findings": [
    {{
      "dimension": "ARROW_FLOW_INTEGRITY",
      "severity": "CRITICAL",
      "element_or_region": "Flow: 1a. Legacy EXE Call",
      "flaw_description": "Label pill occludes 75% of arrow stem leaving only 18px visible.",
      "prescriptive_fix": "Expand horizontal span between Col 1 and Col 2 to 145px or offset label above."
    }}
  ],
  "recommendations": [
    "Increase horizontal spacing of Column 2 by 0.35in."
  ]
}}
```
"""
        return prompt

    @staticmethod
    def evaluate_locally(
        spec: DiagramSpec,
        tier1_issues: List[AuditIssue],
        perceptual_metrics: Dict[str, Any],
        image_path: Optional[Path] = None,
    ) -> VisualQAResult:
        """
        Runs local algorithmic adversarial visual QA heuristics without requiring
        an external network API call, providing instant, deterministic Tier 2 verification.
        """
        start_time = time.time()
        findings: List[VisualFinding] = []

        # 1. Evaluate Ceiling & Margin Clearance from Perceptual Metrics
        ceiling_pixels = perceptual_metrics.get("ceiling_non_bg_pixels", 0)
        if ceiling_pixels > 80:
            findings.append(VisualFinding(
                dimension="CEILING_GUTTER_SAFETY",
                severity="CRITICAL",
                element_or_region="Canvas Ceiling (Top 3% Band)",
                flaw_description=f"Detected {ceiling_pixels} ink pixels in the top ceiling band (violates Milestone 33 return loop ceiling clearance).",
                prescriptive_fix="Reroute ceiling connectors down into the inter-track gutter (y=230px).",
            ))
        elif ceiling_pixels > 25:
            findings.append(VisualFinding(
                dimension="CEILING_GUTTER_SAFETY",
                severity="WARNING",
                element_or_region="Canvas Ceiling Margin",
                flaw_description=f"Minor ink encroachment ({ceiling_pixels} px) near top canvas border.",
                prescriptive_fix="Add 15px top margin breathing room.",
            ))

        # 2. Evaluate Density Hotspots & Visual Congestion
        density_ratio = perceptual_metrics.get("density_max_to_mean_ratio", 1.0)
        if density_ratio > 3.2:
            findings.append(VisualFinding(
                dimension="GEOMETRIC_CLEARANCE",
                severity="WARNING",
                element_or_region="Density Hotspot",
                flaw_description=f"Visual ink density variance is high (max/mean ratio {density_ratio:.1f}x), indicating an overcrowded quadrant.",
                prescriptive_fix="Distribute entity cards across horizontal canvas or expand container widths.",
            ))

        # 3. Translate Tier 1 Issues into Adversarial Findings
        for issue in tier1_issues:
            cat = issue.category
            sev = issue.severity
            finding_sev: Literal["CRITICAL", "WARNING", "ADVISORY"] = (
                "CRITICAL" if sev == "CRITICAL" else ("WARNING" if sev == "WARNING" else "ADVISORY")
            )

            if cat in ("ARROW_SWALLOWED", "ARROW_HEAD_COVERED", "FLOW_OBSTACLE_PENETRATION", "PARALLEL_FLOW_CLUSTERING"):
                findings.append(VisualFinding(
                    dimension="ARROW_FLOW_INTEGRITY",
                    severity=finding_sev,
                    element_or_region=issue.element_id,
                    flaw_description=issue.description,
                    prescriptive_fix=issue.suggested_fix,
                ))
            elif cat in ("SHAPE_PROPORTION_OVERSIZED",):
                findings.append(VisualFinding(
                    dimension="COMPONENT_PROPORTIONS",
                    severity=finding_sev,
                    element_or_region=issue.element_id,
                    flaw_description=issue.description,
                    prescriptive_fix=issue.suggested_fix,
                ))
            elif cat in (
                "CONNECTOR_SPAN_INSUFFICIENT",
                "NODE_COLLISION",
                "BADGE_NODE_COLLISION",
                "BADGE_COLLISION",
                "FLOW_LABEL_NODE_COLLISION",
                "CONTAINER_BADGE_OCCLUSION",
                "CONTAINER_LABEL_OCCLUSION",
                "CANVAS_HEADER_OCCLUSION",
                "INSUFFICIENT_NODE_GUTTER",
                "CONTAINER_OVERFLOW",
                "CONTAINER_PADDING_VIOLATION",
                "BOUNDARY_INTERSECTION",
            ):
                findings.append(VisualFinding(
                    dimension="GEOMETRIC_CLEARANCE",
                    severity=finding_sev,
                    element_or_region=issue.element_id,
                    flaw_description=issue.description,
                    prescriptive_fix=issue.suggested_fix,
                ))
            elif cat in ("CEILING_COLLISION", "MARGIN_ENCROACHMENT", "HEADER_HEADROOM_INSUFFICIENT"):
                findings.append(VisualFinding(
                    dimension="CEILING_GUTTER_SAFETY",
                    severity=finding_sev,
                    element_or_region=issue.element_id,
                    flaw_description=issue.description,
                    prescriptive_fix=issue.suggested_fix,
                ))
            elif cat in ("TEXT_OVERFLOW", "TYPOGRAPHIC_SCALE_DRIFT", "UNDERFILLED_EXECUTION_CARD", "DECK_HEADER_DRIFT"):
                findings.append(VisualFinding(
                    dimension="TYPOGRAPHY_LEGIBILITY",
                    severity=finding_sev,
                    element_or_region=issue.element_id,
                    flaw_description=issue.description,
                    prescriptive_fix=issue.suggested_fix,
                ))
            else:
                findings.append(VisualFinding(
                    dimension="GEOMETRIC_CLEARANCE",
                    severity=finding_sev,
                    element_or_region=issue.element_id,
                    flaw_description=issue.description,
                    prescriptive_fix=issue.suggested_fix,
                ))

        # 4. Check Diagnostic Color Palette Presence
        diag_counts = perceptual_metrics.get("diagnostic_ink_counts", {})
        has_status_ink = any(count > 20 for count in diag_counts.values())
        if not has_status_ink and len(spec.nodes) > 3:
            findings.append(VisualFinding(
                dimension="DIAGNOSTIC_COLOR_HIERARCHY",
                severity="ADVISORY",
                element_or_region="Palette Spectrum",
                flaw_description="Zero Diagnostic Status Triad colors detected in raster sample.",
                prescriptive_fix="Assign roles ('defect', 'wait', 'active', 'target') to convey system lifecycle state.",
            ))

        # 4b. WCAG AA Contrast & Multi-Resolution Font Legibility Scanner
        wcag_findings, wcag_metrics = audit_wcag_and_legibility(spec)
        findings.extend(wcag_findings)
        perceptual_metrics = {**perceptual_metrics, **wcag_metrics}

        # 5. Compute Composite Scores Across 7 Dimensions
        base_scores = {
            "geometric_clearance": 100.0,
            "arrow_flow_integrity": 100.0,
            "component_proportions": 100.0,
            "ceiling_gutter_safety": 100.0,
            "vertical_bridges": 100.0,
            "typography_legibility": 100.0,
            "diagnostic_color_hierarchy": 100.0,
        }

        for f in findings:
            dim_key = f.dimension.lower()
            penalty = 25.0 if f.severity == "CRITICAL" else (12.0 if f.severity == "WARNING" else 5.0)
            if dim_key in base_scores:
                base_scores[dim_key] = max(0.0, base_scores[dim_key] - penalty)

        weights = {
            "geometric_clearance": 0.20,
            "arrow_flow_integrity": 0.20,
            "component_proportions": 0.15,
            "ceiling_gutter_safety": 0.15,
            "vertical_bridges": 0.10,
            "typography_legibility": 0.10,
            "diagnostic_color_hierarchy": 0.10,
        }
        composite_score = sum(base_scores[k] * weights[k] for k in weights)

        # 6. Assign Strict Adversarial Verdict
        has_critical = any(f.severity == "CRITICAL" for f in findings) or any(i.severity == "CRITICAL" for i in tier1_issues)
        has_warning = any(f.severity == "WARNING" for f in findings) or any(i.severity == "WARNING" for i in tier1_issues)

        if has_critical or composite_score < 65.0:
            verdict = "FAIL"
            passed = False
        elif has_warning or composite_score < 85.0:
            verdict = "CONDITIONAL_PASS" if composite_score >= 80.0 else "REVISE_REQUIRED"
            passed = composite_score >= 80.0
        else:
            verdict = "VERIFIED_PASS"
            passed = True

        elapsed = time.time() - start_time
        return VisualQAResult(
            spec_id=spec.id,
            spec_name=spec.name,
            passed=passed,
            verdict=verdict,
            score=composite_score,
            dimension_scores=base_scores,
            tier1_issues=tier1_issues,
            tier2_findings=findings,
            perceptual_metrics=perceptual_metrics,
            raster_image_path=image_path,
            execution_time_sec=elapsed,
        )


class Tier2VisualVerifier:
    """
    High-level coordinator uniting Tier 1 geometric linting, 300+ DPI rasterization,
    perceptual image heuristics, and adversarial subagent briefing synthesis.
    """

    def __init__(self, spec: DiagramSpec) -> None:
        self.spec = spec
        self.linter = Tier1GeometricLinter(spec)

    def verify(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        existing_raster_path: Optional[Union[str, Path]] = None,
        generate_subagent_briefing: bool = True,
    ) -> VisualQAResult:
        """
        Executes end-to-end Tier 1 and Tier 2 adversarial visual QA.
        Returns a complete VisualQAResult structure and persists diagnostics.
        """
        safe_id = re.sub(r"[^\w\-.]", "_", self.spec.id)
        out_p = Path(output_dir) if output_dir else Path("TEMP/visual_qa") / safe_id
        out_p.mkdir(parents=True, exist_ok=True)

        # 1. Tier 1 Geometric Collision Linting
        tier1_issues = self.linter.lint()

        # 2. Acquire or Render 300+ DPI Raster PNG
        raster_path = Path(existing_raster_path) if existing_raster_path else None
        if not raster_path or not raster_path.exists():
            raster_path = self._render_spec_to_png(out_p)

        # 3. Run Perceptual Computer Vision Heuristics
        perceptual_metrics: Dict[str, Any] = {}
        if raster_path and raster_path.exists():
            canvas_cfg = getattr(self.spec, "canvas", None)
            canvas_bg = getattr(canvas_cfg, "background", None)
            perceptual_metrics = PerceptualImageAnalyzer.analyze_raster_image(
                raster_path,
                canvas_bg=canvas_bg,
                show_grid=getattr(canvas_cfg, "show_grid", None),
                grid_color=getattr(canvas_cfg, "grid_color", None),
                grid_opacity=getattr(canvas_cfg, "grid_opacity", None),
            )

        # 4. Run Local Adversarial Evaluation
        result = AdversarialVisualQASubagent.evaluate_locally(
            spec=self.spec,
            tier1_issues=tier1_issues,
            perceptual_metrics=perceptual_metrics,
            image_path=raster_path,
        )

        # 5. Persist Subagent Prompt Briefing Artifact if requested
        if generate_subagent_briefing and raster_path and raster_path.exists():
            briefing_text = AdversarialVisualQASubagent.build_subagent_briefing(
                spec=self.spec,
                image_path=raster_path,
                tier1_issues=tier1_issues,
                perceptual_metrics=perceptual_metrics,
            )
            prompt_file = out_p / f"{safe_id}_adversarial_briefing.md"
            prompt_file.write_text(briefing_text, encoding="utf-8")
            result.subagent_prompt_path = prompt_file

        # 6. Save JSON Diagnostic Ledger
        report_file = out_p / f"{safe_id}_visual_qa_report.json"
        report_file.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

        return result

    def _render_spec_to_png(self, out_dir: Path) -> Optional[Path]:
        """Renders the DiagramSpec to high-DPI companion SVG, then compiles PNG via rsvg-convert."""
        try:
            from src.ppt_engine.diagram_v2.svg_compiler import SVGCompiler
            safe_id = re.sub(r"[^\w\-.]", "_", self.spec.id)
            svg_comp = SVGCompiler(self.spec)
            svg_content = svg_comp.compile_svg()

            svg_file = out_dir / f"{safe_id}.svg"
            svg_file.write_text(svg_content, encoding="utf-8")

            png_file = out_dir / f"{safe_id}.png"
            rsvg_candidates = [
                shutil.which("rsvg-convert"),
                "/opt/homebrew/bin/rsvg-convert",
                "/usr/local/bin/rsvg-convert",
                "/usr/bin/rsvg-convert",
            ]
            rsvg_bin = next((c for c in rsvg_candidates if c and os.path.exists(c)), None)

            if rsvg_bin:
                cmd = [rsvg_bin, "-z", "3", str(svg_file), "-o", str(png_file)]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and png_file.exists():
                    return png_file

            # Fallback to cairosvg if available
            try:
                import cairosvg
                cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=str(png_file), scale=3.0)
                if png_file.exists():
                    return png_file
            except Exception:
                pass

        except Exception as e:
            logger.debug("Could not render diagram spec to PNG: %s", e)

        return None
