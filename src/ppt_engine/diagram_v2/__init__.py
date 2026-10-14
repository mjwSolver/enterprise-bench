"""
Diagram Engine V2 - Isolated Declarative Diagram Subsystem
==========================================================
Deterministic compilation of enterprise architecture topologies from declarative
YAML specifications into Draw.io XML (.drawio), standalone vector SVG (.svg),
high-DPI PNG (.png), and 100% native PowerPoint DrawingML slides (.pptx).
Includes Tier 1 geometric collision linting and Tier 2 adversarial Visual QA.
"""

from src.ppt_engine.diagram_v2.models import (
    DiagramSpec,
    CanvasConfig,
    HeaderConfig,
    ContainerSpec,
    NodeSpec,
    FlowSpec,
    BadgeSpec,
    BulletListSpec,
)
from src.ppt_engine.diagram_v2.geometry import GeometryNormalizer, Box, Point
from src.ppt_engine.diagram_v2.drawio_compiler import DrawIOCompiler
from src.ppt_engine.diagram_v2.svg_compiler import SVGCompiler
from src.ppt_engine.diagram_v2.pptx_compiler import PPTXCompiler
from src.ppt_engine.diagram_v2.compiler import (
    compile_diagram,
    load_diagram_spec,
    validate_diagram_spec,
    EngineV2Result,
)
from src.ppt_engine.diagram_v2.auditor import (
    AuditIssue,
    Tier1GeometricLinter,
    DiagramAuditor,
)
from src.ppt_engine.diagram_v2.visual_verifier import (
    VisualFinding,
    VisualQAResult,
    PerceptualImageAnalyzer,
    AdversarialVisualQASubagent,
    Tier2VisualVerifier,
)

__all__ = [
    "DiagramSpec",
    "CanvasConfig",
    "HeaderConfig",
    "ContainerSpec",
    "NodeSpec",
    "FlowSpec",
    "BadgeSpec",
    "BulletListSpec",
    "GeometryNormalizer",
    "Box",
    "Point",
    "DrawIOCompiler",
    "SVGCompiler",
    "PPTXCompiler",
    "compile_diagram",
    "load_diagram_spec",
    "validate_diagram_spec",
    "EngineV2Result",
    "AuditIssue",
    "Tier1GeometricLinter",
    "DiagramAuditor",
    "VisualFinding",
    "VisualQAResult",
    "PerceptualImageAnalyzer",
    "AdversarialVisualQASubagent",
    "Tier2VisualVerifier",
]
