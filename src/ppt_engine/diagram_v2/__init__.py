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
    DeckHeaderContract,
    ContainerSpec,
    NodeSpec,
    FlowSpec,
    BadgeSpec,
    BulletListSpec,
    classify_geometric_tier,
    CANONICAL_TYPOGRAPHIC_SCALE,
    resolve_node_fonts,
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
from src.ppt_engine.diagram_v2.reconciler import (
    ReconciledChange,
    ReconciliationResult,
    PPTXDiagramDecompiler,
    DiagramReconciler,
    reconcile_diagram,
    dump_diagram_yaml,
)
from src.ppt_engine.diagram_v2.watcher import (
    WatcherEvent,
    PPTXWatcher,
    watch_diagram,
)
from src.ppt_engine.diagram_v2.stray_consolidator import (
    VisualizationPod,
    ThemeCluster,
    ConsolidationReport,
    validate_bundle_headers,
    scan_stray_visualizations,
    cluster_and_rank_pods,
    consolidate_stray_visualizations,
)
from src.ppt_engine.diagram_v2.contrast import (
    contrast_ratio,
    relative_luminance,
    is_dark_hex,
    is_light_hex,
    harmonize_diagram_contrast,
    harmonize_node_contrast,
    harmonize_container_contrast,
    harmonize_flow_contrast,
    WCAG_AA_NORMAL_TEXT,
    WCAG_AA_LARGE_TEXT,
    WCAG_AAA_ENHANCED,
    MIN_BORDER_CONTRAST,
)

__all__ = [
    "DiagramSpec",
    "CanvasConfig",
    "HeaderConfig",
    "DeckHeaderContract",
    "ContainerSpec",
    "NodeSpec",
    "FlowSpec",
    "BadgeSpec",
    "BulletListSpec",
    "classify_geometric_tier",
    "CANONICAL_TYPOGRAPHIC_SCALE",
    "resolve_node_fonts",
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
    "ReconciledChange",
    "ReconciliationResult",
    "PPTXDiagramDecompiler",
    "DiagramReconciler",
    "reconcile_diagram",
    "dump_diagram_yaml",
    "WatcherEvent",
    "PPTXWatcher",
    "watch_diagram",
    "VisualizationPod",
    "ThemeCluster",
    "ConsolidationReport",
    "validate_bundle_headers",
    "scan_stray_visualizations",
    "cluster_and_rank_pods",
    "consolidate_stray_visualizations",
    "contrast_ratio",
    "relative_luminance",
    "is_dark_hex",
    "is_light_hex",
    "harmonize_diagram_contrast",
    "harmonize_node_contrast",
    "harmonize_container_contrast",
    "harmonize_flow_contrast",
    "WCAG_AA_NORMAL_TEXT",
    "WCAG_AA_LARGE_TEXT",
    "WCAG_AAA_ENHANCED",
    "MIN_BORDER_CONTRAST",
]

