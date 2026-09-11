"""
Test Suite for Mermaid to Draw.io Converter and Diagram Subsystem
================================================================
Tests parsing, auto-layout coordinate calculation, Draw.io mxGraph XML generation,
vector SVG rendering, high-resolution PNG rasterization, and sandbox governance.
"""

import os
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.ppt_engine.diagram_engine import (
    DiagramEngine,
    DrawIOConverter,
    HierarchicalLayoutEngine,
    MermaidParser,
    compile_mermaid,
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


class TestDiagramEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = DiagramEngine(workspace_root=WORKSPACE_ROOT)
        self.parser = MermaidParser()
        self.layout = HierarchicalLayoutEngine()

    def test_flowchart_td_parsing(self) -> None:
        """Test vertical flowchart parsing with shapes, edges, and edge labels."""
        mermaid_code = """
        graph TD
            A[Start Ingestion] -->|Raw Markdown| B(Parsing Engine)
            B --> C{Is Valid?}
            C -->|Yes| D[(Database Store)]
            C -->|No| E([Error Stadium])
            D ==> F[[Process Stage]]
            E -.-> F
        """
        diagram = self.parser.parse(mermaid_code)
        self.assertEqual(diagram.diagram_type, "flowchart")
        self.assertEqual(diagram.direction, "TD")
        self.assertEqual(len(diagram.nodes), 6)
        self.assertEqual(len(diagram.edges), 6)

        # Check shapes
        self.assertEqual(diagram.nodes["A"].shape, "rect")
        self.assertEqual(diagram.nodes["B"].shape, "rounded")
        self.assertEqual(diagram.nodes["C"].shape, "rhombus")
        self.assertEqual(diagram.nodes["D"].shape, "cylinder")
        self.assertEqual(diagram.nodes["E"].shape, "stadium")
        self.assertEqual(diagram.nodes["F"].shape, "subroutine")

        # Check edge styles and labels
        edge_0 = diagram.edges[0]
        self.assertEqual(edge_0.source_id, "A")
        self.assertEqual(edge_0.target_id, "B")
        self.assertEqual(edge_0.label, "Raw Markdown")
        self.assertEqual(edge_0.style_type, "solid")

        # Check thick and dashed edges
        thick_edges = [e for e in diagram.edges if e.style_type == "thick"]
        self.assertEqual(len(thick_edges), 1)
        dashed_edges = [e for e in diagram.edges if e.style_type == "dashed"]
        self.assertEqual(len(dashed_edges), 1)

    def test_flowchart_lr_with_subgraphs(self) -> None:
        """Test horizontal flowchart parsing with subgraphs and chained edges."""
        mermaid_code = """
        graph LR
            subgraph Ingestion_Layer [Data Ingestion]
                In1[API Gateway] --> In2[Payload Validator]
            end
            subgraph Processing_Layer [Core Processing]
                Proc1[Transformer] --> Proc2[Classifier]
            end
            In2 --> Proc1
            Proc2 --> Out1((Output Sink))
        """
        diagram = self.parser.parse(mermaid_code)
        self.assertEqual(diagram.direction, "LR")
        self.assertIn("Ingestion_Layer", diagram.subgraphs)
        self.assertIn("Processing_Layer", diagram.subgraphs)
        self.assertEqual(len(diagram.subgraphs["Ingestion_Layer"].node_ids), 2)
        self.assertEqual(diagram.nodes["Out1"].shape, "circle")

        # Test layout computation
        laid_out = self.layout.compute_layout(diagram)
        self.assertGreater(laid_out.total_width, 200)
        self.assertGreater(laid_out.total_height, 100)
        self.assertGreater(laid_out.subgraphs["Ingestion_Layer"].width, 50)

    def test_state_diagram_parsing(self) -> None:
        """Test state diagram parsing with start and end states."""
        mermaid_code = """
        stateDiagram-v2
            [*] --> Idle
            Idle --> Processing : Submit Request
            Processing --> Completed : Success
            Processing --> Failed : Error
            Completed --> [*]
            Failed --> Idle : Retry
        """
        diagram = self.parser.parse(mermaid_code)
        self.assertEqual(diagram.diagram_type, "stateDiagram")
        self.assertIn("Idle", diagram.nodes)
        self.assertIn("Processing", diagram.nodes)

        # Check start/end state nodes
        start_nodes = [n for n in diagram.nodes.values() if n.shape == "startState"]
        end_nodes = [n for n in diagram.nodes.values() if n.shape == "endState"]
        self.assertGreaterEqual(len(start_nodes), 1)
        self.assertGreaterEqual(len(end_nodes), 1)

    def test_drawio_xml_generation(self) -> None:
        """Test standard Draw.io mxGraph XML structure and valid schema."""
        mermaid_code = """
        graph TD
            Node1[Enterprise Ingestion] --> Node2[Visual Engine]
        """
        parsed = self.parser.parse(mermaid_code)
        laid_out = self.layout.compute_layout(parsed)
        converter = DrawIOConverter(theme_name="modern_consulting")
        xml_str = converter.to_xml(laid_out, page_name="TestPage")

        # Verify XML parses validly
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "mxfile")

        diagram_elem = root.find("diagram")
        self.assertIsNotNone(diagram_elem)
        self.assertEqual(diagram_elem.attrib.get("name"), "TestPage")

        model_elem = diagram_elem.find("mxGraphModel")
        self.assertIsNotNone(model_elem)

        root_elem = model_elem.find("root")
        self.assertIsNotNone(root_elem)

        # Check default cells 0 and 1
        cell_0 = root_elem.find("./mxCell[@id='0']")
        cell_1 = root_elem.find("./mxCell[@id='1']")
        self.assertIsNotNone(cell_0)
        self.assertIsNotNone(cell_1)

        # Check node cells
        node1_cell = root_elem.find("./mxCell[@id='node_Node1']")
        self.assertIsNotNone(node1_cell)
        self.assertEqual(node1_cell.attrib.get("vertex"), "1")
        self.assertIn("Enterprise Ingestion", node1_cell.attrib.get("value"))

        # Check geometry
        geo = node1_cell.find("mxGeometry")
        self.assertIsNotNone(geo)
        self.assertGreater(float(geo.attrib.get("width")), 50)
        self.assertGreater(float(geo.attrib.get("height")), 20)

    def test_end_to_end_compilation_and_sandboxing(self) -> None:
        """Test full compile pipeline outputting .drawio, .svg, and .png to project_outputs/test_run/diagrams/."""
        project_name = "test_run"
        diagram_name = "system_architecture"
        mermaid_code = """
        graph TD
            User[User Request] --> Orchestrator[Generation Orchestrator]
            Orchestrator --> DiagramSub[Mermaid to Draw.io Subsystem]
            Orchestrator --> IconSub[Icon Tinting Engine]
            DiagramSub --> Renderer[Headless SVG & PNG Renderer]
            IconSub --> PPTBuilder[python-pptx Canvas]
            Renderer --> PPTBuilder
            PPTBuilder --> Sandbox[(project_outputs/test_run/)]
        """
        output_files = self.engine.compile(
            mermaid_code=mermaid_code,
            project_name=project_name,
            diagram_name=diagram_name,
            theme="modern_consulting",
            formats=("drawio", "svg", "png"),
        )

        expected_dir = WORKSPACE_ROOT / "project_outputs" / project_name / "diagrams"
        self.assertTrue(expected_dir.exists())

        # 1. Verify .drawio file
        drawio_file = output_files.get("drawio")
        self.assertIsNotNone(drawio_file)
        self.assertTrue(drawio_file.exists())
        self.assertGreater(drawio_file.stat().st_size, 200)

        # 2. Verify .svg file
        svg_file = output_files.get("svg")
        self.assertIsNotNone(svg_file)
        self.assertTrue(svg_file.exists())
        svg_content = svg_file.read_text(encoding="utf-8")
        self.assertTrue(svg_content.startswith("<svg"))
        self.assertIn("Generation Orchestrator", svg_content)

        # 3. Verify .png file
        png_file = output_files.get("png")
        self.assertIsNotNone(png_file)
        self.assertTrue(png_file.exists())
        self.assertGreater(png_file.stat().st_size, 1000)

        # Check PNG magic bytes: \x89PNG\r\n\x1a\n
        with open(png_file, "rb") as f:
            header = f.read(8)
            self.assertEqual(header, b"\x89PNG\r\n\x1a\n")

    def test_multiple_diagram_types_in_sandbox(self) -> None:
        """Test rendering horizontal pipeline, state machine, and complex cluster diagrams."""
        project_name = "test_run"

        # 1. Horizontal Pipeline
        res_pipeline = self.engine.compile(
            mermaid_code="""
            graph LR
                A[Ingest] --> B[Validate] --> C[Transform] --> D[Export Presentation]
            """,
            project_name=project_name,
            diagram_name="horizontal_pipeline",
            theme="corporate_navy",
        )
        self.assertTrue(res_pipeline["png"].exists())

        # 2. State Machine
        res_state = self.engine.compile(
            mermaid_code="""
            stateDiagram-v2
                [*] --> Draft
                Draft --> InReview : Submit
                InReview --> Approved : Approve
                InReview --> Rejected : Reject
                Approved --> [*]
                Rejected --> Draft : Revise
            """,
            project_name=project_name,
            diagram_name="state_machine",
            theme="executive_tech",
        )
        self.assertTrue(res_state["png"].exists())

        # 3. Complex Cluster
        res_cluster = self.engine.compile(
            mermaid_code="""
            graph TD
                subgraph Client [Client Presentation]
                    UI[User Interface] --> API[REST Endpoints]
                end
                subgraph Core [Core Engine]
                    API --> Engine[Layout Compiler]
                    Engine --> DrawIO[Draw.io Subsystem]
                end
                DrawIO --> Export[(project_outputs/)]
            """,
            project_name=project_name,
            diagram_name="complex_cluster",
            theme="warm_amber",
        )
        self.assertTrue(res_cluster["png"].exists())

    def test_sandbox_security_write_barrier(self) -> None:
        """Test that directory traversal attempts are blocked by the write barrier."""
        with self.assertRaises(ValueError):
            self.engine.get_sandbox_dir("../../../etc")


if __name__ == "__main__":
    unittest.main()
