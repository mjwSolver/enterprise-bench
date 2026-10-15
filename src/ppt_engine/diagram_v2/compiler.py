"""
Diagram Engine V2 - High-Level Unified Compiler Orchestrator
============================================================
Coordinates declarative YAML parsing, schema validation, geometry normalization,
and deterministic compilation into Draw.io XML (.drawio), high-fidelity SVG (.svg),
high-DPI PNG (.png), and 100% native PowerPoint slides (.pptx).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import yaml

from src.ppt_engine.diagram_v2.models import DiagramSpec
from src.ppt_engine.diagram_v2.drawio_compiler import DrawIOCompiler
from src.ppt_engine.diagram_v2.svg_compiler import SVGCompiler
from src.ppt_engine.diagram_v2.pptx_compiler import PPTXCompiler, _svg_to_png_bytes

logger = logging.getLogger(__name__)


@dataclass
class EngineV2Result:
    """Artifact collection produced by Diagram Engine V2 compilation."""
    spec: DiagramSpec
    drawio_path: Optional[Path] = None
    svg_path: Optional[Path] = None
    png_path: Optional[Path] = None
    pptx_path: Optional[Path] = None
    visual_qa_result: Optional[Any] = None

    @property
    def generated_files(self) -> List[Path]:
        return [p for p in (self.drawio_path, self.svg_path, self.png_path, self.pptx_path) if p is not None]


def load_diagram_spec(spec_path_or_dict: Union[str, Path, Dict[str, Any], DiagramSpec]) -> DiagramSpec:
    """Loads and validates a DiagramSpec from a DiagramSpec instance, YAML file, JSON string, or Python dictionary."""
    if isinstance(spec_path_or_dict, DiagramSpec):
        return spec_path_or_dict
    if isinstance(spec_path_or_dict, dict):
        return DiagramSpec.model_validate(spec_path_or_dict)

    path = Path(spec_path_or_dict)
    if not path.exists():
        raise FileNotFoundError(f"Diagram specification file not found: {path}")

    raw_text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid diagram YAML specification format in {path}: expected top-level mapping.")

    return DiagramSpec.model_validate(data)


def validate_diagram_spec(spec_path_or_dict: Union[str, Path, Dict[str, Any]]) -> Tuple[bool, List[str], Optional[DiagramSpec]]:
    """
    Validates a declarative diagram specification and verifies all node and container references.
    Returns (is_valid, list_of_diagnostics, validated_spec).
    """
    issues: List[str] = []
    spec: Optional[DiagramSpec] = None

    try:
        spec = load_diagram_spec(spec_path_or_dict)
    except Exception as e:
        return False, [f"Schema validation error: {e}"], None

    node_ids = {n.id for n in spec.nodes}
    container_ids = {c.id for c in spec.containers}

    # Verify duplicate node IDs
    if len(node_ids) < len(spec.nodes):
        seen = set()
        for n in spec.nodes:
            if n.id in seen:
                issues.append(f"Duplicate node ID detected: '{n.id}'")
            seen.add(n.id)

    # Verify flow references
    for f in spec.flows:
        if f.source and f.source not in node_ids and f.source not in container_ids:
            issues.append(f"Flow source '{f.source}' not found in registered nodes or containers.")
        if f.target and f.target not in node_ids and f.target not in container_ids:
            issues.append(f"Flow target '{f.target}' not found in registered nodes or containers.")

    # Verify container parents
    for n in spec.nodes:
        if n.container_id and n.container_id not in container_ids:
            issues.append(f"Node '{n.id}' references non-existent container '{n.container_id}'.")

    # Verify icon resolution
    for n in spec.nodes:
        if n.icon:
            p = Path(n.icon)
            if not p.exists():
                try:
                    from src.ppt_engine.library_importer import IconRegistry
                    resolved = IconRegistry.resolve_icon(n.icon)
                    if not resolved or not resolved.exists():
                        issues.append(f"Node '{n.id}' icon '{n.icon}' could not be resolved in registry or disk.")
                except Exception:
                    issues.append(f"Node '{n.id}' icon '{n.icon}' could not be resolved.")

    # Run DiagramAuditor for spatial collision, occlusion, and arrow crowding checks
    try:
        from src.ppt_engine.diagram_v2.auditor import DiagramAuditor
        auditor = DiagramAuditor(spec)
        audit_issues = auditor.audit()
        for ai in audit_issues:
            issues.append(f"[{ai.severity}] ({ai.category}) {ai.description} Suggested fix: {ai.suggested_fix}")
    except Exception as ex:
        issues.append(f"Auditor execution failure: {ex}")

    has_critical = any(
        iss.startswith("[CRITICAL]") or "Duplicate node ID" in iss or "not found" in iss or "non-existent" in iss
        for iss in issues
    )
    is_valid = not has_critical
    return is_valid, issues, spec


def compile_diagram(
    spec_path_or_dict: Union[str, Path, Dict[str, Any]],
    output_dir_or_file: Optional[Union[str, Path]] = None,
    formats: Sequence[str] = ("all",),
    open_deck: bool = False,
    run_visual_qa: bool = False,
) -> EngineV2Result:
    """
    Compiles a declarative YAML diagram specification into requested formats.
    Supported format targets: 'drawio', 'svg', 'png', 'pptx', or 'all'.
    """
    spec = load_diagram_spec(spec_path_or_dict)

    # Pre-flight spatial collision and crowding audit
    try:
        from src.ppt_engine.diagram_v2.auditor import DiagramAuditor
        auditor = DiagramAuditor(spec)
        audit_issues = auditor.audit()
        for ai in audit_issues:
            if ai.severity == "CRITICAL":
                logger.warning("Diagram Spatial Audit [%s] (%s): %s", ai.severity, ai.category, ai.description)
    except Exception as ex:
        logger.debug("Auditor exception during compile: %s", ex)

    # Normalize formats
    target_formats = set()
    for fmt in formats:
        f_lower = fmt.lower().strip()
        if f_lower == "all":
            target_formats.update({"drawio", "svg", "png", "pptx"})
        else:
            target_formats.add(f_lower)

    # Determine output paths
    slug = spec.id or "diagram"
    if output_dir_or_file:
        out_target = Path(output_dir_or_file)
        if out_target.suffix in (".drawio", ".svg", ".pptx", ".png"):
            base_dir = out_target.parent
            base_stem = out_target.stem
        else:
            base_dir = out_target
            base_stem = slug
    else:
        base_dir = Path("output/diagrams_v2")
        base_stem = slug

    base_dir.mkdir(parents=True, exist_ok=True)
    res = EngineV2Result(spec=spec)

    # 1. Compile Draw.io XML
    if "drawio" in target_formats:
        drawio_path = base_dir / f"{base_stem}.drawio"
        compiler_drawio = DrawIOCompiler(spec)
        xml_content = compiler_drawio.compile_xml()
        drawio_path.write_text(xml_content, encoding="utf-8")
        res.drawio_path = drawio_path

    # 2. Compile Vector SVG
    compiled_svg: Optional[str] = None
    if "svg" in target_formats or "png" in target_formats:
        svg_path = base_dir / f"{base_stem}.svg"
        compiler_svg = SVGCompiler(spec)
        compiled_svg = compiler_svg.compile_svg()
        if "svg" in target_formats:
            svg_path.write_text(compiled_svg, encoding="utf-8")
            res.svg_path = svg_path

    # 3. Rasterize PNG
    if "png" in target_formats:
        png_path = base_dir / f"{base_stem}.png"
        if compiled_svg:
            # Save SVG temporarily if not yet written
            svg_for_png = res.svg_path or (base_dir / f"{base_stem}.svg")
            if not svg_for_png.exists():
                svg_for_png.write_text(compiled_svg, encoding="utf-8")
            png_bytes = _svg_to_png_bytes(svg_for_png)
            if png_bytes:
                png_path.write_bytes(png_bytes)
                res.png_path = png_path
            # Cleanup temp svg if svg was not in requested formats
            if "svg" not in target_formats and svg_for_png.exists() and svg_for_png != res.svg_path:
                svg_for_png.unlink(missing_ok=True)

    # 4. Compile Native PowerPoint Slide
    if "pptx" in target_formats:
        pptx_path = base_dir / f"{base_stem}.pptx"
        compiler_pptx = PPTXCompiler(spec)
        compiler_pptx.compile_presentation(pptx_path)
        res.pptx_path = pptx_path

        if open_deck:
            import subprocess
            subprocess.run(["open", "-a", "Microsoft PowerPoint", str(pptx_path)])

    # 5. Tier 2 Adversarial Visual QA Verification (if requested)
    if run_visual_qa:
        try:
            from src.ppt_engine.diagram_v2.visual_verifier import Tier2VisualVerifier
            verifier = Tier2VisualVerifier(spec)
            vqa_res = verifier.verify(output_dir=base_dir, existing_raster_path=res.png_path)
            res.visual_qa_result = vqa_res
        except Exception as ex:
            logger.warning("Visual QA verification failed: %s", ex)

    return res

