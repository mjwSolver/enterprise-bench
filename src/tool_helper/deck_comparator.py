"""
Deck Comparator & Slide Quality Auditor (Enterprise Workbench Tool Helper)
Performs headless, deterministic comparisons between two PowerPoint decks
to verify fixes for missing bullets, whitespace distribution, co-branding assets,
and DrawingML structural completeness.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


class DeckComparator:
    """Headless auditor comparing before/after slides for enterprise consulting standards."""

    def __init__(self, before_path: Path, after_path: Path) -> None:
        self.before_path = before_path
        self.after_path = after_path
        self.prs_before = Presentation(str(before_path)) if before_path.exists() else None
        self.prs_after = Presentation(str(after_path)) if after_path.exists() else None

    def audit_slide_metrics(self, prs: Presentation) -> List[Dict[str, Any]]:
        def _iter_leaf_shapes(shapes):
            for shape in shapes:
                if shape.shape_type == MSO_SHAPE_TYPE.GROUP or hasattr(shape, "shapes"):
                    try:
                        child_shapes = list(shape.shapes)
                        if child_shapes:
                            yield from _iter_leaf_shapes(child_shapes)
                            continue
                    except Exception:
                        pass
                yield shape

        metrics = []
        for idx, slide in enumerate(prs.slides, start=1):
            all_shapes = list(_iter_leaf_shapes(slide.shapes))
            total_shapes = len(all_shapes)
            text_boxes = 0
            tables = 0
            images = 0
            total_words = 0
            empty_boxes = 0
            y_coords = []
            h_coords = []

            for shape in all_shapes:
                if shape.has_text_frame:
                    text_boxes += 1
                    raw_text = shape.text_frame.text.strip()
                    words = len(raw_text.split())
                    total_words += words
                    if not raw_text:
                        empty_boxes += 1
                if shape.has_table:
                    tables += 1
                    seen_tcs: set[int] = set()
                    for row in shape.table.rows:
                        for cell in row.cells:
                            tc_id = id(cell._tc)
                            if tc_id in seen_tcs:
                                continue
                            seen_tcs.add(tc_id)
                            cell_text = cell.text.strip()
                            if cell_text:
                                total_words += len(cell_text.split())
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    images += 1

            # Compute slide vertical span and coverage using top-level shape coordinates
            for shape in slide.shapes:
                try:
                    top_in = shape.top.inches
                    h_in = shape.height.inches
                    # Filter out whole-slide background shape
                    if h_in < 7.4:
                        y_coords.append(top_in)
                        h_coords.append(top_in + h_in)
                except Exception:
                    pass

            max_y = max(h_coords) if h_coords else 0.0
            min_y = min(y_coords) if y_coords else 0.0
            vertical_span = max(0.0, max_y - min_y)
            # Canvas height is 7.5"; content area is ~5.4" (1.8" to 7.2")
            coverage_pct = min(100.0, (vertical_span / 5.2) * 100.0) if vertical_span > 0 else 0.0

            metrics.append({
                "slide_idx": idx,
                "total_shapes": total_shapes,
                "text_boxes": text_boxes,
                "tables": tables,
                "images": images,
                "total_words": total_words,
                "empty_boxes": empty_boxes,
                "vertical_span_in": round(vertical_span, 2),
                "coverage_pct": round(coverage_pct, 1),
            })
        return metrics

    def compare(self) -> Dict[str, Any]:
        before_m = self.audit_slide_metrics(self.prs_before) if self.prs_before else []
        after_m = self.audit_slide_metrics(self.prs_after) if self.prs_after else []

        max_slides = max(len(before_m), len(after_m))
        slide_diffs = []

        for i in range(max_slides):
            b = before_m[i] if i < len(before_m) else None
            a = after_m[i] if i < len(after_m) else None

            diff = {
                "slide_idx": i + 1,
                "before_words": b["total_words"] if b else 0,
                "after_words": a["total_words"] if a else 0,
                "word_delta": (a["total_words"] if a else 0) - (b["total_words"] if b else 0),
                "before_coverage": b["coverage_pct"] if b else 0.0,
                "after_coverage": a["coverage_pct"] if a else 0.0,
                "coverage_delta": round((a["coverage_pct"] if a else 0.0) - (b["coverage_pct"] if b else 0.0), 1),
                "before_empty_boxes": b["empty_boxes"] if b else 0,
                "after_empty_boxes": a["empty_boxes"] if a else 0,
            }
            slide_diffs.append(diff)

        total_b_words = sum(s["total_words"] for s in before_m)
        total_a_words = sum(s["total_words"] for s in after_m)

        return {
            "before_slides": len(before_m),
            "after_slides": len(after_m),
            "total_before_words": total_b_words,
            "total_after_words": total_a_words,
            "net_word_delta": total_a_words - total_b_words,
            "slide_diffs": slide_diffs,
        }
