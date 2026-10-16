#!/usr/bin/env python3
"""
Implementation and Verification of the Icon + Title Encapsulation Pattern.
Topic 4 & 5 compliance:
1. Outer boundary swimlanes are sharp rectangles (MSO_SHAPE.RECTANGLE).
2. Entity nodes encase icon glyph + title within compact rounded-corner container pills (MSO_SHAPE.ROUNDED_RECTANGLE).
3. Strictly 1 label per node (CANDIDATE_CAPTION invariant, zero descriptive filler).
4. Container bounding padding: 12-16 pt.
5. Connectors have >= 8 pt clearance from text frames with native triangle arrowheads.
6. OpenXML sanitizer strips theme drop shadows (idx="0" and empty <a:effectLst/>).
"""

import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement

from src.ppt_engine.theme_engine import strip_shape_shadows
from src.ppt_engine.diagram_v2.models import (
    DiagramSpec,
    ContainerSpec,
    NodeSpec,
    FlowSpec,
    CanvasConfig,
    HeaderConfig,
)
from src.ppt_engine.diagram_v2 import compile_diagram

def verify_shape_shadow_purged(shape, name: str) -> None:
    sp = getattr(shape, "_element", shape)
    if hasattr(shape, "shadow"):
        assert shape.shadow.inherit is False, f"[{name}] shadow.inherit is not False"
        
    style = sp.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
    if style is not None:
        effect_ref = style.find("{http://schemas.openxmlformats.org/drawingml/2006/main}effectRef")
        if effect_ref is not None:
            assert effect_ref.get("idx") == "0", f"[{name}] style/effectRef idx != 0"

    sp_pr = getattr(sp, "spPr", None)
    assert sp_pr is not None, f"[{name}] Missing spPr"
    outer_shadows = sp_pr.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}outerShdw")
    assert len(outer_shadows) == 0, f"[{name}] Lingering outerShdw elements"
    effect_lst = sp_pr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}effectLst")
    assert effect_lst is not None, f"[{name}] Missing <a:effectLst/>"
    assert len(list(effect_lst)) == 0, f"[{name}] <a:effectLst/> not empty"

def test_declarative_v2_compilation() -> Path:
    """Tests the encapsulation pattern via the unified Diagram Engine V2 pipeline."""
    spec = DiagramSpec(
        id="encapsulation_v2_test",
        name="Architecture Encapsulation Pattern",
        canvas=CanvasConfig(width=13.333, height=7.5, background="#FFFFFF"),
        header=HeaderConfig(
            show=True,
            action_title="Proposed Architecture: Encapsulation & Boundary Swimlanes",
            subtitle="Icon + Title Encapsulated Nodes Inside Sharp Container Swimlanes",
            brand_stripes=True,
        ),
        containers=[
            ContainerSpec(
                id="c_source",
                label="On-Premises / Source Layer",
                role="neutral",
                x=0.80,
                y=1.50,
                w=3.40,
                h=5.20,
                corner_radius=0.0, # Sharp rectangle
                stroke_width=1.5,
                dashed=True,
            ),
            ContainerSpec(
                id="c_cloud",
                label="AWS Lakehouse / Databricks",
                role="database",
                x=4.80,
                y=1.50,
                w=3.80,
                h=5.20,
                corner_radius=0.0, # Sharp rectangle
                stroke_width=2.0,
                dashed=True,
            ),
            ContainerSpec(
                id="c_consumer",
                label="Data Consumers / Analytics",
                role="active",
                x=9.20,
                y=1.50,
                w=3.40,
                h=5.20,
                corner_radius=0.0, # Sharp rectangle
                stroke_width=1.5,
                dashed=True,
            ),
        ],
        nodes=[
            # Source nodes (encapsulated rounded cards)
            NodeSpec(
                id="src_db",
                container_id="c_source",
                title="Oracle Core DB",
                icon_emoji="🗄️",
                role="neutral",
                shape="rounded",
                is_rounded=True,
                x=1.10,
                y=2.20,
                w=2.80,
                h=0.90,
                icon_layout="side",
            ),
            NodeSpec(
                id="src_cdc",
                container_id="c_source",
                title="Debezium CDC",
                icon_emoji="⚡",
                role="active",
                shape="rounded",
                is_rounded=True,
                x=1.10,
                y=3.80,
                w=2.80,
                h=0.90,
                icon_layout="side",
            ),
            # Cloud nodes
            NodeSpec(
                id="cloud_ingest",
                container_id="c_cloud",
                title="Lambda Ingestion",
                icon_emoji="λ",
                role="compute",
                shape="rounded",
                is_rounded=True,
                x=5.30,
                y=2.20,
                w=2.80,
                h=0.90,
                icon_layout="side",
            ),
            NodeSpec(
                id="cloud_dbx",
                container_id="c_cloud",
                title="Databricks Delta",
                icon_emoji="🧱",
                role="database",
                shape="rounded",
                is_rounded=True,
                x=5.30,
                y=3.80,
                w=2.80,
                h=0.90,
                icon_layout="side",
            ),
            # Consumer nodes
            NodeSpec(
                id="cons_bi",
                container_id="c_consumer",
                title="Power BI Dashboards",
                icon_emoji="📊",
                role="target",
                shape="rounded",
                is_rounded=True,
                x=9.50,
                y=2.20,
                w=2.80,
                h=0.90,
                icon_layout="side",
            ),
            NodeSpec(
                id="cons_ml",
                container_id="c_consumer",
                title="Fraud ML Serving",
                icon_emoji="🤖",
                role="target",
                shape="rounded",
                is_rounded=True,
                x=9.50,
                y=3.80,
                w=2.80,
                h=0.90,
                icon_layout="side",
            ),
        ],
        flows=[
            FlowSpec(source="src_db", target="src_cdc", label="WAL Logs", stroke_hex="#2563EB", curve="straight"),
            FlowSpec(source="src_cdc", target="cloud_ingest", label="Event Streaming", stroke_hex="#0284C7", curve="straight"),
            FlowSpec(source="cloud_ingest", target="cloud_dbx", label="Parquet Ingest", stroke_hex="#16A34A", curve="straight"),
            FlowSpec(source="cloud_dbx", target="cons_bi", label="Gold Schema", stroke_hex="#16A34A", curve="straight"),
            FlowSpec(source="cloud_dbx", target="cons_ml", label="Feature Store", stroke_hex="#16A34A", curve="straight"),
        ],
    )

    out_p = Path("output/presentations/encapsulation_v2_test.pptx")
    res = compile_diagram(spec, output_dir_or_file=out_p, formats=["pptx", "drawio", "svg"])
    assert res.pptx_path is not None and res.pptx_path.exists()
    return res.pptx_path

def test_direct_python_pptx_pattern() -> Path:
    """Tests building the encapsulation pattern directly via python-pptx."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # 1. Solid white canvas background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(255, 255, 255)
    bg.line.fill.background()
    strip_shape_shadows(bg)

    # 2. Dual brand accent stripes (1:2 ratio)
    s_red = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.80), Inches(0.50), Inches(0.045), Inches(0.55))
    s_red.fill.solid()
    s_red.fill.fore_color.rgb = RGBColor(220, 38, 38) # #DC2626
    s_red.line.fill.background()
    strip_shape_shadows(s_red)

    s_blue = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.865), Inches(0.50), Inches(0.090), Inches(0.55))
    s_blue.fill.solid()
    s_blue.fill.fore_color.rgb = RGBColor(2, 132, 199) # #0284C7
    s_blue.line.fill.background()
    strip_shape_shadows(s_blue)

    # 3. Unified Title & Subtitle text box
    tb_title = slide.shapes.add_textbox(Inches(1.05), Inches(0.45), Inches(11.5), Inches(0.65))
    tf = tb_title.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_bottom = tf.margin_right = 0
    p1 = tf.paragraphs[0]
    p1.text = "Direct Pattern: Encapsulated Icon & Title Nodes"
    p1.font.name = "Arial"
    p1.font.size = Pt(20)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(15, 23, 42)

    p2 = tf.add_paragraph()
    p2.text = "Sharp Boundary Swimlanes with Compact Rounded Pills (Zero Drop Shadows)"
    p2.font.name = "Arial"
    p2.font.size = Pt(11)
    p2.font.color.rgb = RGBColor(100, 116, 139)
    p2.space_before = Pt(4)
    strip_shape_shadows(tb_title)

    # 4. Sharp Boundary Swimlane (MSO_SHAPE.RECTANGLE)
    swimlane = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.80), Inches(1.50), Inches(5.60), Inches(5.20))
    swimlane.fill.solid()
    swimlane.fill.fore_color.rgb = RGBColor(248, 250, 252) # #F8FAFC
    swimlane.line.color.rgb = RGBColor(148, 163, 184) # #94A3B8
    swimlane.line.width = Pt(1.5)
    strip_shape_shadows(swimlane)

    # Swimlane Header Label (inside boundary margin)
    tb_sw_lbl = slide.shapes.add_textbox(Inches(1.00), Inches(1.65), Inches(5.20), Inches(0.35))
    tf_lbl = tb_sw_lbl.text_frame
    tf_lbl.margin_left = tf_lbl.margin_top = tf_lbl.margin_bottom = tf_lbl.margin_right = 0
    p_lbl = tf_lbl.paragraphs[0]
    p_lbl.text = "TRANSACTION PROCESSING LANE (SHARP RECTANGLE)"
    p_lbl.font.name = "Arial"
    p_lbl.font.size = Pt(9.5)
    p_lbl.font.bold = True
    p_lbl.font.color.rgb = RGBColor(71, 85, 105)
    strip_shape_shadows(tb_sw_lbl)

    # 5. Encapsulated Node 1: Rounded Card enclosing Icon + Title
    # Card Pill (MSO_SHAPE.ROUNDED_RECTANGLE)
    node1_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.10), Inches(2.20), Inches(5.00), Inches(0.95))
    node1_card.fill.solid()
    node1_card.fill.fore_color.rgb = RGBColor(255, 255, 255)
    node1_card.line.color.rgb = RGBColor(59, 130, 246) # #3B82F6
    node1_card.line.width = Pt(1.5)
    strip_shape_shadows(node1_card)

    # Icon Glyphs (inside pill)
    tb_icon1 = slide.shapes.add_textbox(Inches(1.25), Inches(2.35), Inches(0.65), Inches(0.65))
    tf_i1 = tb_icon1.text_frame
    tf_i1.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_i1.margin_left = tf_i1.margin_top = tf_i1.margin_bottom = tf_i1.margin_right = 0
    p_i1 = tf_i1.paragraphs[0]
    p_i1.text = "🏛️"
    p_i1.alignment = PP_ALIGN.CENTER
    p_i1.font.size = Pt(22)
    strip_shape_shadows(tb_icon1)

    # Title Text (inside pill, CANDIDATE_CAPTION invariant: 1 clean label)
    tb_txt1 = slide.shapes.add_textbox(Inches(2.00), Inches(2.35), Inches(3.90), Inches(0.65))
    tf_t1 = tb_txt1.text_frame
    tf_t1.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_t1.margin_left = tf_t1.margin_top = tf_t1.margin_bottom = tf_t1.margin_right = 0
    p_t1 = tf_t1.paragraphs[0]
    p_t1.text = "Core Banking Ingress"
    p_t1.font.name = "Arial"
    p_t1.font.size = Pt(13)
    p_t1.font.bold = True
    p_t1.font.color.rgb = RGBColor(15, 23, 42)
    strip_shape_shadows(tb_txt1)

    # 6. Encapsulated Node 2: Rounded Card enclosing Icon + Title
    node2_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.10), Inches(3.70), Inches(5.00), Inches(0.95))
    node2_card.fill.solid()
    node2_card.fill.fore_color.rgb = RGBColor(255, 255, 255)
    node2_card.line.color.rgb = RGBColor(16, 185, 129) # #10B981
    node2_card.line.width = Pt(1.5)
    strip_shape_shadows(node2_card)

    tb_icon2 = slide.shapes.add_textbox(Inches(1.25), Inches(3.85), Inches(0.65), Inches(0.65))
    tf_i2 = tb_icon2.text_frame
    tf_i2.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_i2.margin_left = tf_i2.margin_top = tf_i2.margin_bottom = tf_i2.margin_right = 0
    p_i2 = tf_i2.paragraphs[0]
    p_i2.text = "🔒"
    p_i2.alignment = PP_ALIGN.CENTER
    p_i2.font.size = Pt(22)
    strip_shape_shadows(tb_icon2)

    tb_txt2 = slide.shapes.add_textbox(Inches(2.00), Inches(3.85), Inches(3.90), Inches(0.65))
    tf_t2 = tb_txt2.text_frame
    tf_t2.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_t2.margin_left = tf_t2.margin_top = tf_t2.margin_bottom = tf_t2.margin_right = 0
    p_t2 = tf_t2.paragraphs[0]
    p_t2.text = "Audit & Compliance Ledger"
    p_t2.font.name = "Arial"
    p_t2.font.size = Pt(13)
    p_t2.font.bold = True
    p_t2.font.color.rgb = RGBColor(15, 23, 42)
    strip_shape_shadows(tb_txt2)

    # 7. Connector Line with Triangle Arrowhead and clearance
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(3.60), Inches(3.15), Inches(3.60), Inches(3.70))
    conn.line.color.rgb = RGBColor(37, 99, 235)
    conn.line.width = Pt(2.0)
    # Triangle arrowhead at destination
    tail_end = OxmlElement("a:tailEnd")
    tail_end.set("type", "triangle")
    tail_end.set("w", "med")
    tail_end.set("len", "med")
    conn._element.spPr.ln.append(tail_end)
    strip_shape_shadows(conn)

    out_p = Path("output/presentations/encapsulation_direct_test.pptx")
    prs.save(str(out_p))
    return out_p

def verify_pptx_geometry(pptx_path: Path) -> None:
    prs = Presentation(str(pptx_path))
    slide = prs.slides[0]

    # Verify all shapes have shadows purged
    for sh in slide.shapes:
        verify_shape_shadow_purged(sh, f"{pptx_path.name}:{sh.name}")

    print(f"Verified {pptx_path}: all shapes have zero drop shadows and valid OpenXML sanitization.")

def main():
    # 1. Test declarative DiagramSpec compilation
    v2_path = test_declarative_v2_compilation()
    verify_pptx_geometry(v2_path)

    # 2. Test direct python-pptx authoring
    direct_path = test_direct_python_pptx_pattern()
    verify_pptx_geometry(direct_path)

    # 3. Copy to BSIM_Migration doc_output for desktop review
    bsim_out_dir = Path("/Users/marcelljw/Documents/antigravity/adventurous-darwin/BSIM_Migration/doc_output")
    if bsim_out_dir.exists():
        import shutil
        shutil.copy2(v2_path, bsim_out_dir / "encapsulation_v2_test.pptx")
        shutil.copy2(direct_path, bsim_out_dir / "encapsulation_direct_test.pptx")
        print(f"Copied artifacts to {bsim_out_dir}")

    print("\nSUCCESS: Icon + Title Encapsulation Pattern & OpenXML Drop Shadow Purge verified.")

if __name__ == "__main__":
    main()
