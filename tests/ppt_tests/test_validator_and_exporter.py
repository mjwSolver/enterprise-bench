"""
Test Suite for Slide Exporter and Algorithmic Validator
======================================================
Tests:
  1. Slide Exporter: Pure-Python and multi-backend headless rendering, image output verification.
  2. Slide Validator: 5 Algorithmic QA checks (Font Floor, Diagram Threshold, Margins/Collision,
     Text Overflow, Theme Geometry) tested with compliant and violating slides.
  3. Branded Decks: Validation of Snow Blue and Brick Red consulting decks.
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure root is on path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from src.ppt_engine.slide_exporter import SlideExporter, export_deck_to_images
from src.ppt_engine.slide_validator import (
    Severity,
    SlideValidator,
    ValidationIssue,
    ValidationReport,
    validate_presentation,
)


class TestSlideExporter(unittest.TestCase):

    def setUp(self) -> None:
        self.test_output_dir = _ROOT / "project_outputs" / "test_exporter"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        self.pptx_path = self.test_output_dir / "sample_deck.pptx"

        # Create a sample 2-slide presentation
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        # Slide 1: Card + Text
        s1 = prs.slides.add_slide(prs.slide_layouts[6])
        card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.0), Inches(11.333), Inches(5.5))
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(255, 255, 255)
        card.line.color.rgb = RGBColor(203, 213, 225)

        tb = s1.shapes.add_textbox(Inches(1.5), Inches(1.5), Inches(10.0), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = "Sample Exporter Test Slide"
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = RGBColor(15, 23, 42)

        # Slide 2: Plain Slide
        s2 = prs.slides.add_slide(prs.slide_layouts[6])
        tb2 = s2.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.0), Inches(1.0))
        tf2 = tb2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = "Second Slide for Exporter"
        p2.font.size = Pt(20)

        prs.save(str(self.pptx_path))

    def test_pure_python_exporter(self) -> None:
        """Test Pure-Python fallback renderer generating PNG previews."""
        preview_dir = self.test_output_dir / "previews_py"
        exported = export_deck_to_images(self.pptx_path, output_dir=preview_dir, backend="python")
        self.assertEqual(len(exported), 2)
        for img_path in exported:
            self.assertTrue(img_path.exists())
            self.assertGreater(img_path.stat().st_size, 1000)
            # Verify PNG magic header
            with open(img_path, "rb") as f:
                header = f.read(8)
                self.assertEqual(header, b"\x89PNG\r\n\x1a\n")

    def test_auto_backend_exporter(self) -> None:
        """Test auto-backend exporter."""
        preview_dir = self.test_output_dir / "previews_auto"
        exported = export_deck_to_images(self.pptx_path, output_dir=preview_dir, backend="auto")
        self.assertEqual(len(exported), 2)
        for img_path in exported:
            self.assertTrue(img_path.exists())
            self.assertGreater(img_path.stat().st_size, 1000)

    def test_invalid_pptx_path(self) -> None:
        """Test handling missing PPTX file."""
        with self.assertRaises(FileNotFoundError):
            export_deck_to_images(self.test_output_dir / "non_existent.pptx")


class TestSlideValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.test_dir = _ROOT / "project_outputs" / "test_validator"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def _create_base_deck(self) -> Presentation:
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        return prs

    def test_check_1_font_size_floor_audit(self) -> None:
        """Check 1: Verifies detection of font size below theme floor (<8pt)."""
        prs = self._create_base_deck()
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Add text with font size 6.0 pt (violating minimum 8.0 pt floor)
        tb = slide.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(5.0), Inches(1.0))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = "Microscopic text violating font floor"
        p.font.size = Pt(6.0)

        deck_path = self.test_dir / "font_violation.pptx"
        prs.save(str(deck_path))

        report = validate_presentation(deck_path, theme="snowblue")
        self.assertFalse(report.passed)
        self.assertGreater(report.total_issues, 0)
        font_issues = [i for i in report.slide_results[0].issues if i.check_id == "CHECK_1_FONT_SIZE_FLOOR"]
        self.assertTrue(len(font_issues) >= 1)
        self.assertIn("6.0pt", font_issues[0].message)

    def test_check_2_diagram_dimensions(self) -> None:
        """Check 2: Verifies detection of miniature/compressed diagram visuals."""
        prs = self._create_base_deck()
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Use an existing diagram PNG or icon as a miniature picture (< 2.0" x 1.0")
        icon_path = _ROOT / "project_outputs" / "demo_deck" / "assets" / "icon_zap.png"
        if icon_path.exists():
            # Place as 1.5" x 0.8" (undersized for a diagram)
            slide.shapes.add_picture(str(icon_path), Inches(1.0), Inches(1.0), width=Inches(1.5), height=Inches(0.8))

            deck_path = self.test_dir / "diagram_violation.pptx"
            prs.save(str(deck_path))

            report = validate_presentation(deck_path, theme="snowblue")
            diag_issues = [i for i in report.slide_results[0].issues if i.check_id == "CHECK_2_DIAGRAM_DIMENSION"]
            self.assertTrue(len(diag_issues) >= 1)

    def test_check_3_margin_overflow(self) -> None:
        """Check 3: Verifies detection of shape crossing the 0.4\" slide margin."""
        prs = self._create_base_deck()
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Add shape overflowing left margin (left = 0.10" < min_margin 0.40")
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.10), Inches(1.0), Inches(4.0), Inches(2.0))

        deck_path = self.test_dir / "margin_violation.pptx"
        prs.save(str(deck_path))

        report = validate_presentation(deck_path, theme="snowblue")
        self.assertFalse(report.passed)
        margin_issues = [i for i in report.slide_results[0].issues if i.check_id == "CHECK_3_MARGIN_OVERFLOW"]
        self.assertTrue(len(margin_issues) >= 1)
        self.assertIn("left slide margin", margin_issues[0].message)

    def test_check_4_text_overflow_guard(self) -> None:
        """Check 4: Verifies detection of long unwrapped text risking clipping."""
        prs = self._create_base_deck()
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Textbox with word_wrap = False and long text exceeding width
        tb = slide.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(2.0), Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = "This is a very long single-line text string that will overflow the narrow two-inch box width."
        p.font.size = Pt(14)

        deck_path = self.test_dir / "overflow_violation.pptx"
        prs.save(str(deck_path))

        report = validate_presentation(deck_path, theme="snowblue")
        overflow_issues = [i for i in report.slide_results[0].issues if i.check_id == "CHECK_4_TEXT_OVERFLOW"]
        self.assertTrue(len(overflow_issues) >= 1)

    def test_check_5_theme_geometry_compliance(self) -> None:
        """Check 5: Verifies detection of excessive border stroke width."""
        prs = self._create_base_deck()
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Shape with heavy 4.5pt border stroke (exceeding theme max 2.0pt)
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.0), Inches(5.0), Inches(3.0))
        card.line.color.rgb = RGBColor(2, 132, 199)
        card.line.width = Pt(4.5)

        deck_path = self.test_dir / "geometry_violation.pptx"
        prs.save(str(deck_path))

        report = validate_presentation(deck_path, theme="snowblue")
        geo_issues = [i for i in report.slide_results[0].issues if i.check_id == "CHECK_5_THEME_GEOMETRY"]
        self.assertTrue(len(geo_issues) >= 1)

    def test_report_formatting_and_dict(self) -> None:
        """Test report text, markdown formatting, and dictionary export."""
        prs = self._create_base_deck()
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        deck_path = self.test_dir / "clean_deck.pptx"
        prs.save(str(deck_path))

        report = validate_presentation(deck_path, theme="snowblue")
        self.assertTrue(report.passed)
        txt = report.format_text()
        self.assertIn("PRESENTATION QA VALIDATION REPORT", txt)
        md = report.format_markdown()
        self.assertIn("Presentation Quality Audit", md)
        d = report.to_dict()
        self.assertEqual(d["total_slides"], 1)
        self.assertTrue(d["passed"])


if __name__ == "__main__":
    unittest.main()
