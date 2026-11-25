"""
Unit Tests: Desktop Hot-Reload Matching, Slide Replacement & Diagram V2 CLI
===========================================================================
All Microsoft PowerPoint AppleScript / pgrep / open calls are strictly mocked.
Zero desktop applications are launched during these tests.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches
from typer.testing import CliRunner

from src.cli import app
from src.cli.utils import close_target_presentation
from src.ppt_engine.diagram_v2.models import CanvasConfig, ContainerSpec, DiagramSpec, FlowSpec, HeaderConfig, NodeSpec
from src.ppt_engine.diagram_v2.powerpoint_desktop import (
    PowerPointDesktopManager,
    PowerPointDirtyError,
)
from src.ppt_engine.diagram_v2.pptx_compiler import PPTXCompiler, replace_slide_in_presentation

EMU_PER_INCH = 914400.0


def test_desktop_manager_canonical_path_matching_avoids_basename_collision(tmp_path: Path):
    """Two open decks with identical basenames in different directories must not collide."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    deck_a = dir_a / "deck.pptx"
    deck_b = dir_b / "deck.pptx"
    deck_a.write_bytes(b"a")
    deck_b.write_bytes(b"b")

    def fake_run(cmd, **kwargs):
        res = MagicMock()
        if cmd[0] == "pgrep":
            res.returncode = 0
            res.stdout = "1234\n"
            return res
        if cmd[0] == "osascript":
            script_arg = cmd[2]
            if "repeat with p in presentations" in script_arg and "saved of p" not in script_arg and "close p" not in script_arg:
                # list_open_presentations -> only deck_a is open
                res.returncode = 0
                res.stdout = f"{deck_a.resolve()}\n"
                return res
            if "saved of p" in script_arg:
                # Verify canonical path argv[0] is compared, not basename
                target_resolved = cmd[3]
                res.returncode = 0
                res.stdout = "false\n" if target_resolved == str(deck_a.resolve()) else "NOT_FOUND\n"
                return res
            res.returncode = 0
            res.stdout = ""
            return res
        res.returncode = 0
        return res

    with (
        patch.object(PowerPointDesktopManager, "is_supported_platform", return_value=True),
        patch("src.ppt_engine.diagram_v2.powerpoint_desktop.subprocess.run", side_effect=fake_run) as mock_run,
    ):
        assert PowerPointDesktopManager.is_presentation_open(deck_a) is True
        assert PowerPointDesktopManager.is_presentation_open(deck_b) is False
        assert PowerPointDesktopManager.is_presentation_saved(deck_a) is False
        assert PowerPointDesktopManager.is_presentation_saved(deck_b) is None

        # Sibling deck_b is NOT open -> close returns False without raising dirty error
        assert PowerPointDesktopManager.close_presentation_if_open(deck_b, force=False) is False

        # Target deck_a IS open and dirty -> raises PowerPointDirtyError unless force=True
        with pytest.raises(PowerPointDirtyError):
            PowerPointDesktopManager.close_presentation_if_open(deck_a, force=False)

        assert PowerPointDesktopManager.close_presentation_if_open(deck_a, force=True, timeout_ms=0) is True
        close_calls = [c for c in mock_run.call_args_list if c[0][0][0] == "osascript" and "close p saving no" in c[0][0][2]]
        assert close_calls
        assert "count of presentations" in close_calls[-1][0][0][2]


def test_desktop_manager_bare_unsaved_name_fallback_only_without_separators():
    """Bare unsaved presentation names without path separators still match cleanly."""
    with (
        patch.object(PowerPointDesktopManager, "is_supported_platform", return_value=True),
        patch.object(PowerPointDesktopManager, "is_powerpoint_running", return_value=True),
        patch.object(PowerPointDesktopManager, "list_open_presentations", return_value=["Presentation1"]),
    ):
        assert PowerPointDesktopManager.is_presentation_open("Presentation1") is True
        assert PowerPointDesktopManager.is_presentation_open("/tmp/other/Presentation2") is False


def test_close_target_presentation_respects_dirty_state(tmp_path: Path):
    """close_target_presentation delegates safely and returns False when dirty."""
    deck = tmp_path / "dirty.pptx"
    deck.write_bytes(b"dummy")

    with (
        patch("src.cli.utils.sys.platform", "darwin"),
        patch.object(
            PowerPointDesktopManager,
            "close_presentation_if_open",
            side_effect=PowerPointDirtyError("Unsaved edits"),
        ) as mock_close,
    ):
        assert close_target_presentation(deck) is False
        mock_close.assert_called_once_with(deck, force=False)


def test_replace_slide_4x3_scales_and_preserves_non_diagram_shapes(tmp_path: Path):
    """Replacing into a 4:3 deck fits within 10\" width and preserves user shapes unless purge_all=True."""
    target_pptx = tmp_path / "deck_4x3.pptx"
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    footer_box = slide.shapes.add_textbox(Inches(0.5), Inches(7.1), Inches(4.0), Inches(0.3))
    footer_box.name = "custom_footer"
    footer_box.text_frame.text = "Keep Me"
    old_diag = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.0), Inches(2.0), Inches(1.0))
    old_diag.name = "node:old_node"
    prs.save(str(target_pptx))

    spec = DiagramSpec(
        id="wide_16_9",
        canvas=CanvasConfig(width=13.333, height=7.5, unit="in"),
        containers=[ContainerSpec(id="c1", label="ZONE", x=0.45, y=1.35, w=12.40, h=5.50)],
        nodes=[NodeSpec(id="n1", container_id="c1", title="Scaled Card", x=1.0, y=2.0, w=3.0, h=1.5)],
    )
    replace_slide_in_presentation(spec, target_pptx, slide_index=1, purge_all=False)

    out_prs = Presentation(str(target_pptx))
    assert out_prs.slide_width / EMU_PER_INCH == pytest.approx(10.0, abs=0.01)
    assert out_prs.slide_height / EMU_PER_INCH == pytest.approx(7.5, abs=0.01)
    names = [sh.name for sh in out_prs.slides[0].shapes]
    assert "custom_footer" in names
    assert "node:old_node" not in names
    assert "node:n1" in names
    for sh in out_prs.slides[0].shapes:
        right_in = (sh.left + sh.width) / EMU_PER_INCH
        assert right_in <= 10.01, f"Shape '{sh.name}' clipped past 4:3 width: {right_in}"

    # Verify purge_all=True removes non-Diagram-V2 shapes as well
    replace_slide_in_presentation(spec, target_pptx, slide_index=1, purge_all=True)
    purged_prs = Presentation(str(target_pptx))
    purged_names = [sh.name for sh in purged_prs.slides[0].shapes]
    assert "custom_footer" not in purged_names
    assert "node:n1" in purged_names


def test_pptx_compiler_dark_mode_text_color_and_px_canvas(tmp_path: Path):
    """_plan_card honors auto-inverted dark-fill text colors and compile_presentation honors px canvas."""
    spec = DiagramSpec(
        id="dark_px",
        canvas=CanvasConfig(width=900.0, height=675.0, unit="px"),
        nodes=[
            NodeSpec(
                id="dark_card",
                title="Dark Card",
                subtitle="Auto inverted",
                fill_hex="#0F172A",
                x=90.0,
                y=180.0,
                w=270.0,
                h=135.0,
            ),
        ],
    )
    assert spec.nodes[0].title_color == "#FFFFFF"

    out_pptx = tmp_path / "dark_px.pptx"
    with patch("src.cli.utils.close_target_presentation", return_value=False):
        PPTXCompiler(spec).compile_presentation(out_pptx)

    prs = Presentation(str(out_pptx))
    assert prs.slide_width / EMU_PER_INCH == pytest.approx(10.0, abs=0.02)
    assert prs.slide_height / EMU_PER_INCH == pytest.approx(7.5, abs=0.02)

    text_shapes = [sh for sh in prs.slides[0].shapes if sh.name == "node:dark_card:text"]
    assert text_shapes
    title_rgb = str(text_shapes[0].text_frame.paragraphs[0].font.color.rgb)
    assert title_rgb == "FFFFFF"


def test_cli_compile_non_pptx_with_pop_skips_powerpoint_and_pptx_fallback(tmp_path: Path):
    """bench diagram v2 compile spec.yaml -f svg --pop (no --target) skips PowerPoint and PPTX creation."""
    spec_file = tmp_path / "mini.yaml"
    spec_file.write_text(
        """
id: mini_svg
name: Mini SVG Test
nodes:
  - id: n1
    title: Source
    x: 1.0
    y: 1.6
    w: 2.2
    h: 1.2
""",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    runner = CliRunner()

    with (
        patch.object(PowerPointDesktopManager, "close_presentation_if_open") as mock_close,
        patch.object(PowerPointDesktopManager, "activate_presentation") as mock_activate,
    ):
        result = runner.invoke(
            app,
            ["diagram", "v2", "compile", str(spec_file), "-o", str(out_dir), "-f", "svg", "--pop"],
        )

    assert result.exit_code == 0, result.output
    mock_close.assert_not_called()
    mock_activate.assert_not_called()
    assert (out_dir / "mini_svg.svg").is_file()
    assert not (out_dir / "mini_svg.pptx").exists()


def test_cli_layout_invalid_yaml_exits_cleanly(tmp_path: Path):
    """bench diagram v2 layout handles invalid YAML cleanly with exit code 1."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("just a scalar string", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["diagram", "v2", "layout", str(bad_yaml)])
    assert result.exit_code == 1


def test_pptx_compiler_px_unit_header_and_none_node_height(tmp_path: Path):
    """px-unit specs keep HeaderConfig inch defaults unscaled and scale None node heights in inches."""
    spec = DiagramSpec(
        id="px_hdr_and_none_h",
        canvas=CanvasConfig(width=1200.0, height=675.0, unit="px"),
        header=HeaderConfig(show=True, action_title="PX Title", subtitle="PX Sub"),
        nodes=[
            NodeSpec.model_construct(
                id="n1",
                title="Node",
                x=90.0,
                y=180.0,
                w=180.0,
                h=None,
                shape="rect",
                stroke_hex="#3B82F6",
                fill_hex="#FFFFFF",
                title_color="#0F172A",
                subtitle_color="#64748B",
                stroke_width=2.0,
                is_rounded=False,
                is_cylinder=False,
                icon_layout="auto",
                valign="middle",
                align="center",
            )
        ],
    )
    # Clear h post-init so PPTXCompiler exercises its n.h is None fallback in px mode
    spec.nodes[0].h = None
    out_pptx = tmp_path / "px_hdr.pptx"
    with patch("src.cli.utils.close_target_presentation", return_value=False):
        PPTXCompiler(spec).compile_presentation(out_pptx)

    prs = Presentation(str(out_pptx))
    shapes = {sh.name: sh for sh in prs.slides[0].shapes}
    stripe = shapes["header:stripe:red"]
    assert stripe.left / EMU_PER_INCH >= 0.40
    assert stripe.top / EMU_PER_INCH >= 0.15
    title_sh = shapes["header:title"]
    assert title_sh.top / EMU_PER_INCH >= 0.15
    node_sh = shapes["node:n1"]
    assert node_sh.height / EMU_PER_INCH == pytest.approx(1.25, abs=0.02)

    # Explicit coordinate ports scale cleanly under 4:3 target fit
    spec_43 = DiagramSpec(
        id="port_scale",
        canvas=CanvasConfig(width=13.333, height=7.5, unit="in"),
        nodes=[
            NodeSpec(id="a", title="A", x=1.0, y=2.0, w=2.0, h=1.5),
            NodeSpec(id="b", title="B", x=9.0, y=2.0, w=2.0, h=1.5),
        ],
        flows=[FlowSpec(id="f1", source="a", target="b", source_port="right_at(2.75)", target_port="left_at(2.75)")],
    )
    prs_43 = Presentation()
    prs_43.slide_width = Inches(10.0)
    prs_43.slide_height = Inches(7.5)
    slide_43 = prs_43.slides.add_slide(prs_43.slide_layouts[6])
    PPTXCompiler(spec_43, target_width_in=10.0, target_height_in=7.5).compile_slide(slide_43)
    f_sh = next(sh for sh in slide_43.shapes if sh.name == "flow:f1")
    assert f_sh.top / EMU_PER_INCH > 2.75  # centered vertically with _fit_oy > 0 and _fit_scale=0.75


def test_desktop_manager_full_path_never_matches_unsaved_bare_deck_and_normalizes_hfs():
    """Directory-qualified targets never match bare unsaved names, and HFS paths normalize to POSIX."""
    with (
        patch.object(PowerPointDesktopManager, "is_supported_platform", return_value=True),
        patch.object(PowerPointDesktopManager, "is_powerpoint_running", return_value=True),
        patch.object(PowerPointDesktopManager, "list_open_presentations", return_value=["deck.pptx"]),
    ):
        assert PowerPointDesktopManager.is_presentation_open("/tmp/a/deck.pptx") is False
        assert PowerPointDesktopManager.is_presentation_open("deck.pptx") is True
        assert PowerPointDesktopManager.close_presentation_if_open("/tmp/a/deck.pptx", force=False) is False

    # Verify AppleScript in is_presentation_saved / close_presentation_if_open passes targetIsBare="false"
    with (
        patch.object(PowerPointDesktopManager, "is_supported_platform", return_value=True),
        patch("src.ppt_engine.diagram_v2.powerpoint_desktop.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="NOT_FOUND\n")
        assert PowerPointDesktopManager.is_presentation_saved("/tmp/a/deck.pptx") is None
        osa_calls = [c for c in mock_run.call_args_list if c[0][0][0] == "osascript"]
        assert osa_calls
        assert osa_calls[-1][0][0][-1] == "false"
        assert 'targetIsBare is "true"' in osa_calls[-1][0][0][2]

    # HFS path matching
    with (
        patch.object(PowerPointDesktopManager, "is_supported_platform", return_value=True),
        patch.object(PowerPointDesktopManager, "is_powerpoint_running", return_value=True),
        patch.object(
            PowerPointDesktopManager,
            "list_open_presentations",
            return_value=["Macintosh HD:Users:alice:proj:deck.pptx"],
        ),
    ):
        assert PowerPointDesktopManager.is_presentation_open("/Users/alice/proj/deck.pptx") is True
        assert PowerPointDesktopManager.is_presentation_open("/Users/bob/proj/deck.pptx") is False
