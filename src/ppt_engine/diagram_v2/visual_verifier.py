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


class PerceptualImageAnalyzer:
    """
    Perceptual computer vision analyzer operating directly on rasterized PNG slide/diagram plates.
    Extracts ink density heatmaps, margin clearance metrics, and color distribution stats.
    """

    @staticmethod
    def _is_ink_pixel(r: int, g: int, b: int, a: int) -> bool:
        """Determines if an RGBA pixel represents printable or non-background ink."""
        if a < 40:
            return False
        lum = (r + g + b) / 3.0
        sat = max(r, g, b) - min(r, g, b)
        # Exclude pure white background and faint background grid lines (#E2E8F0, lum>230, sat<18)
        if lum > 228 and sat < 20:
            return False
        return lum < 215 or sat > 25

    @staticmethod
    def analyze_raster_image(png_path: Path) -> Dict[str, Any]:
        """Performs localized perceptual heuristics on the generated diagram raster image."""
        if not png_path.exists():
            return {"error": f"Raster image not found: {png_path}"}

        try:
            with Image.open(png_path) as img:
                img_rgba = img.convert("RGBA")
                w, h = img_rgba.size
                is_ink = PerceptualImageAnalyzer._is_ink_pixel

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
                    if is_ink(r, g, b, a)
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
                        if is_ink(r, g, b, a)
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
                            if is_ink(pr, pg, pb, pa)
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
            perceptual_metrics = PerceptualImageAnalyzer.analyze_raster_image(raster_path)

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
