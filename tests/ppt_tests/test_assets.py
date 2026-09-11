"""
Test Suite for PPT Asset Engine (Icon Search, Brand Tinting, Stock Photos, and Slide Image Framing).
Verifies that generated assets are created, post-processed, and saved into project_outputs/test_run/.
"""

import os
import sys
import shutil
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image

from src.ppt_engine.icon_engine import (
    IconEngine,
    search_icons,
    get_brand_icon,
    recolor_svg,
    render_svg_to_png,
    normalize_color,
)
from src.ppt_engine.image_engine import (
    ImageEngine,
    search_stock_photos,
    download_image,
    crop_aspect_ratio,
    apply_rounded_corners,
    apply_border,
    apply_drop_shadow,
    frame_slide_image,
)

OUTPUT_DIR = Path("project_outputs/test_run")


class TestAssetEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create output directories for test run
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "icons").mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "images").mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "cards").mkdir(parents=True, exist_ok=True)

    def test_01_color_normalization(self):
        """Test color normalization across hex, rgb tuples, and rgba."""
        self.assertEqual(normalize_color("#2563eb"), "#2563EB")
        self.assertEqual(normalize_color("2563EB"), "#2563EB")
        self.assertEqual(normalize_color("#fff"), "#FFFFFF")
        self.assertEqual(normalize_color((37, 99, 235)), "#2563EB")
        self.assertEqual(normalize_color("rgb(37, 99, 235)"), "#2563EB")

    def test_02_icon_search(self):
        """Test icon search across Lucide, Material Design, and Feather."""
        results = search_icons("shield", limit=5)
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        first = results[0]
        self.assertIn("id", first)
        self.assertIn("prefix", first)
        self.assertIn("name", first)
        print(f"[PASSED] Icon search for 'shield' found {len(results)} items: {[r['id'] for r in results]}")

    def test_03_svg_recolor(self):
        """Test dynamic SVG brand tinting for stroke and fill icons."""
        # Stroke-based icon (Lucide)
        lucide_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
        tinted_stroke = recolor_svg(lucide_svg, color="#2563EB")
        self.assertIn('stroke="#2563EB"', tinted_stroke)
        self.assertIn('fill="none"', tinted_stroke)

        # Fill-based icon (Material)
        mdi_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>'
        tinted_fill = recolor_svg(mdi_svg, color=(16, 185, 129))  # Emerald #10B981
        self.assertIn('fill="#10B981"', tinted_fill)
        print("[PASSED] SVG dynamic recoloring for stroke & fill models verified.")

    def test_04_icon_download_and_rendering(self):
        """Test fetching, recoloring, and rendering icons to SVG & high-res PNG."""
        engine = IconEngine(cache_dir="assets/icons")

        test_icons = [
            ("lucide:shield-check", "#2563EB", OUTPUT_DIR / "icons" / "icon_shield_blue.png"),
            ("lucide:trending-up", "#10B981", OUTPUT_DIR / "icons" / "icon_trend_green.png"),
            ("feather:activity", "#EF4444", OUTPUT_DIR / "icons" / "icon_activity_red.png"),
            ("material-symbols:diamond", "#8B5CF6", OUTPUT_DIR / "icons" / "icon_diamond_purple.png"),
        ]

        for icon_id, color, out_path in test_icons:
            res_path = engine.get_icon(
                identifier=icon_id,
                color=color,
                size=512,
                output_path=out_path,
                save_svg=True,
            )
            self.assertTrue(res_path.exists(), f"PNG file {res_path} was not created")
            self.assertGreater(res_path.stat().st_size, 0)

            # Check matching SVG
            svg_path = out_path.with_suffix(".svg")
            self.assertTrue(svg_path.exists(), f"SVG file {svg_path} was not created")

            # Check image integrity
            with Image.open(res_path) as img:
                self.assertEqual(img.size, (512, 512))
                self.assertEqual(img.mode, "RGBA")

            print(f"[PASSED] Rendered icon {icon_id} with color {color} -> {res_path.name}")

    def test_05_icon_badge_container(self):
        """Test rendering an icon inside a rounded badge container."""
        badge_path = OUTPUT_DIR / "icons" / "icon_badge_card.png"
        res = get_brand_icon(
            identifier="lucide:zap",
            brand_color="#FFFFFF",
            size=256,
            badge_bg="#3B82F6",
            badge_radius=40,
            output_path=badge_path,
        )
        self.assertTrue(res.exists())
        with Image.open(res) as img:
            self.assertEqual(img.size, (256, 256))
        print(f"[PASSED] Rendered badge icon container -> {res.name}")

    def test_06_stock_photo_search_and_download(self):
        """Test searching and downloading stock photos / visuals."""
        engine = ImageEngine(cache_dir="assets/images")
        results = engine.search_stock("technology network", limit=2)
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)

        first_asset = results[0]
        self.assertIn("url", first_asset)
        out_image_path = OUTPUT_DIR / "images" / "stock_technology.png"

        saved_path = engine.download_image(first_asset["url"], output_path=out_image_path)
        self.assertTrue(saved_path.exists())
        self.assertGreater(saved_path.stat().st_size, 0)
        print(f"[PASSED] Stock asset search & download verified -> {saved_path.name} from {first_asset['source']}")

    def test_07_procedural_3d_visual_generation(self):
        """Test procedural 3D abstract visual generator for slides."""
        engine = ImageEngine(cache_dir="assets/images")
        img_3d = engine.generate_procedural_3d_card(
            title="Enterprise Cloud Architecture",
            primary_color="#2563EB",
            accent_color="#38BDF8",
            size=(1920, 1080),
        )
        out_3d_path = OUTPUT_DIR / "images" / "procedural_3d_cloud.png"
        img_3d.save(str(out_3d_path), format="PNG")
        self.assertTrue(out_3d_path.exists())
        self.assertEqual(img_3d.size, (1920, 1080))
        print(f"[PASSED] Procedural 3D visual generated -> {out_3d_path.name}")

    def test_08_slide_image_framing_pipeline(self):
        """Test image cropping (16:9, 4:3, 1:1), rounded corners, hairline border, and drop shadow."""
        src_image_path = OUTPUT_DIR / "images" / "procedural_3d_cloud.png"
        self.assertTrue(src_image_path.exists())

        test_frames = [
            ("16:9", 28, 2, "#38BDF8", True, OUTPUT_DIR / "cards" / "card_16_9_shadow.png"),
            ("4:3", 20, 1, "#E2E8F0", True, OUTPUT_DIR / "cards" / "card_4_3_shadow.png"),
            ("1:1", 32, 2, "#2563EB", True, OUTPUT_DIR / "cards" / "card_1_1_square.png"),
            ("16:9", 0, 0, "#000000", False, OUTPUT_DIR / "cards" / "card_16_9_flat.png"),
        ]

        for ratio, radius, b_width, b_color, shadow, out_path in test_frames:
            framed = frame_slide_image(
                image_input=src_image_path,
                aspect_ratio=ratio,
                corner_radius=radius,
                border_width=b_width,
                border_color=b_color,
                shadow=shadow,
                output_path=out_path,
            )
            self.assertTrue(out_path.exists())
            self.assertGreater(out_path.stat().st_size, 0)
            self.assertEqual(framed.mode, "RGBA")
            print(f"[PASSED] Framed slide card (aspect={ratio}, r={radius}, shadow={shadow}) -> {out_path.name}")


if __name__ == "__main__":
    unittest.main()
