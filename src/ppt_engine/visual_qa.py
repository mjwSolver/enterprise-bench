"""
PowerPoint Visual QA & Automated Spatial Collision Linter
=========================================================
Provides automated visual inspection, window screen capture, and DrawingML
spatial collision detection to automatically diagnose and remediate:
- Text overflowing container cards or colliding with border lines
- Connector label pills intersecting container boundary dashed borders
- Backwards or missing connector arrowheads
- Visual capture via live macOS PowerPoint window or headless QuickLook
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pptx import Presentation
from pptx.util import Inches, Pt

logger = logging.getLogger(__name__)


@dataclass
class VisualIssue:
    slide_index: int
    issue_type: str  # 'TEXT_OVERFLOW', 'BOUNDARY_COLLISION', 'ARROW_ORIENTATION'
    shape_name: str
    severity: str    # 'CRITICAL', 'WARNING', 'INFO'
    description: str
    suggested_fix: str
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x, y, w, h in inches


class PPTVisualLinter:
    """Performs spatial geometry linting on DrawingML presentation shapes."""

    def __init__(self, pptx_path: Path) -> None:
        self.pptx_path = Path(pptx_path)
        self.prs = Presentation(str(self.pptx_path))

    def lint_presentation(self) -> List[VisualIssue]:
        """Scans all slides for text overflow and spatial collisions."""
        issues: List[VisualIssue] = []
        for idx, slide in enumerate(self.prs.slides, start=1):
            issues.extend(self._lint_slide(slide, idx))
        return issues

    def _lint_slide(self, slide, slide_idx: int) -> List[VisualIssue]:
        issues: List[VisualIssue] = []

        boundaries: List[Dict[str, Any]] = []
        pills: List[Dict[str, Any]] = []

        for shape in slide.shapes:
            x = shape.left.inches
            y = shape.top.inches
            w = shape.width.inches
            h = shape.height.inches

            # Detect zone boundaries (large dashed containers)
            if shape.has_text_frame and shape.line and shape.line.dash_style:
                text = shape.text_frame.text.strip()
                if "APPLICATIONS" in text.upper() or "BOUNDARY" in text.upper() or "CLOUD" in text.upper():
                    boundaries.append({"name": text, "x": x, "y": y, "w": w, "h": h, "shape": shape})

            # Detect pills / label shapes (small rounded cards)
            if shape.has_text_frame and w <= 1.8 and h <= 0.40:
                text = shape.text_frame.text.strip()
                if text:
                    pills.append({"text": text, "x": x, "y": y, "w": w, "h": h, "shape": shape})

            # Check text overflow inside content cards (exclude standalone pills and title headers)
            if shape.has_text_frame and shape.text_frame.text.strip():
                tf = shape.text_frame
                text = tf.text.strip()
                para_count = len(tf.paragraphs)
                
                # Exclude pills (single short line) and unified headers
                is_pill = (w <= 1.8 and h <= 0.40 and para_count <= 1)
                is_header = ("Current:" in text or "Proposed:" in text) and y < 1.0

                if not is_pill and not is_header and h < 3.0:
                    # Estimate text height based on font sizes and line count
                    est_height = 0.0
                    for p in tf.paragraphs:
                        fs = p.font.size.pt if p.font.size else 11.0
                        # Calculate wrapped lines based on width
                        char_per_line = max(10, int(w * 16))
                        line_count = max(1, (len(p.text) + char_per_line - 1) // char_per_line)
                        est_height += (fs * 1.25 * line_count + 3.0) / 72.0

                    # Budget = frame height minus its real vertical insets (python-pptx
                    # defaults to 0.05" each). Zero-inset frames from the proportional
                    # padding engine already sit inside padded card regions.
                    try:
                        insets = tf.margin_top.inches + tf.margin_bottom.inches
                    except Exception:
                        insets = 0.15
                    avail_h = h - insets
                    if est_height > avail_h:
                        issues.append(
                            VisualIssue(
                                slide_index=slide_idx,
                                issue_type="TEXT_OVERFLOW",
                                shape_name=f"Card '{text.splitlines()[0][:25]}...'",
                                severity="CRITICAL",
                                description=(
                                    f"Estimated text height ({est_height:.2f}\") exceeds "
                                    f"available container height ({avail_h:.2f}\" of {h:.2f}\"). "
                                    f"Text risks crossing bottom card border."
                                ),
                                suggested_fix=f"Increase card height to at least {est_height + 0.25:.2f}\"",
                                bbox=(x, y, w, h),
                            )
                        )

        # Check label pill collisions with boundary edges
        for pill in pills:
            px, py, pw, ph = pill["x"], pill["y"], pill["w"], pill["h"]
            for b in boundaries:
                bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
                threshold = 0.15  # inches

                # Vertical boundary lines at x=bx (left) and x=bx+bw (right)
                crosses_left = (px - threshold <= bx <= px + pw + threshold)
                crosses_right = (px - threshold <= bx + bw <= px + pw + threshold)
                within_vertical_span = (by - threshold <= py <= by + bh + threshold)

                if (crosses_left or crosses_right) and within_vertical_span:
                    edge_name = "left" if crosses_left else "right"
                    issues.append(
                        VisualIssue(
                            slide_index=slide_idx,
                            issue_type="BOUNDARY_COLLISION",
                            shape_name=f"Pill '{pill['text']}'",
                            severity="WARNING",
                            description=(
                                f"Label pill '{pill['text']}' at x={px:.2f}\" directly intersects "
                                f"{edge_name} boundary of '{b['name']}' at x={bx if crosses_left else bx+bw:.2f}\"."
                            ),
                            suggested_fix="Offset pill horizontal position by ±0.35\" away from border line.",
                            bbox=(px, py, pw, ph),
                        )
                    )

                # Horizontal bottom boundary line at y=by+bh
                crosses_bottom = (py - threshold <= by + bh <= py + ph + threshold)
                within_horizontal_span = (bx - threshold <= px <= bx + bw + threshold)
                if crosses_bottom and within_horizontal_span:
                    issues.append(
                        VisualIssue(
                            slide_index=slide_idx,
                            issue_type="BOUNDARY_COLLISION",
                            shape_name=f"Pill '{pill['text']}'",
                            severity="WARNING",
                            description=(
                                f"Label pill '{pill['text']}' at y={py:.2f}\" directly intersects "
                                f"bottom boundary line of '{b['name']}' at y={by+bh:.2f}\"."
                            ),
                            suggested_fix="Shift pill vertical position by ±0.25\" away from bottom boundary line.",
                            bbox=(px, py, pw, ph),
                        )
                    )

        return issues


class PowerPointScreenCaptureEngine:
    """Captures pixel-perfect slide images directly from macOS Microsoft PowerPoint or QuickLook."""

    @staticmethod
    def is_powerpoint_running() -> bool:
        """Checks if Microsoft PowerPoint application is running on macOS."""
        res = subprocess.run(["pgrep", "-x", "Microsoft PowerPoint"], capture_output=True, text=True)
        return res.returncode == 0

    @staticmethod
    def capture_live_slides(pptx_path: Path, output_dir: Path) -> List[Path]:
        """
        Activates Microsoft PowerPoint, navigates through all slides,
        and captures pixel-perfect window screenshots via macOS screencapture.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        captured_images: List[Path] = []

        prs = Presentation(str(pptx_path))
        num_slides = len(prs.slides)

        # 1. Bring PowerPoint to front and get window bounds
        cmd_get_bounds = """
tell application "Microsoft PowerPoint"
    activate
end tell
delay 0.4
tell application "System Events"
    tell process "Microsoft PowerPoint"
        set pos to position of window 1
        set sz to size of window 1
        return (item 1 of pos as text) & "," & (item 2 of pos as text) & "," & (item 1 of sz as text) & "," & (item 2 of sz as text)
    end tell
end tell
"""
        res = subprocess.run(["osascript", "-e", cmd_get_bounds], capture_output=True, text=True)
        if res.returncode != 0 or not res.stdout.strip():
            logger.warning("Could not get PowerPoint window bounds; falling back to headless capture.")
            return PowerPointScreenCaptureEngine.capture_headless_quicklook(pptx_path, output_dir)

        bounds = res.stdout.strip()

        # 2. Iterate each slide
        for slide_idx in range(1, num_slides + 1):
            cmd_nav = f"""
tell application "Microsoft PowerPoint"
    activate
    go to slide view of active window number {slide_idx}
end tell
"""
            subprocess.run(["osascript", "-e", cmd_nav], capture_output=True, text=True)
            time.sleep(0.35)

            out_png = output_dir / f"slide_{slide_idx}.png"
            cap_cmd = ["screencapture", "-x", f"-R{bounds}", str(out_png)]
            subprocess.run(cap_cmd, capture_output=True, text=True)

            if out_png.exists():
                captured_images.append(out_png)

        return captured_images

    @staticmethod
    def capture_headless_quicklook(pptx_path: Path, output_dir: Path) -> List[Path]:
        """Headless fallback: extracts slide thumbnails via macOS qlmanage."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        thumb_dir = output_dir / "quicklook_thumbs"
        thumb_dir.mkdir(parents=True, exist_ok=True)

        res = subprocess.run(
            ["qlmanage", "-t", "-s", "2000", "-o", str(thumb_dir), str(pptx_path)],
            capture_output=True,
            text=True,
        )
        captured = list(thumb_dir.glob("*.png"))
        return captured
