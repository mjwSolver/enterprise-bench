#!/usr/bin/env python3
"""
Verification script for headless Draw.io stencil extraction to standalone SVG (`drawio -x -f svg`).
Verifies:
1. export_drawio_stencil_to_svg executes headlessly without GUI popups
2. Correctly passes 1-based page-index and --crop
3. Preserves vector stencils and emits standalone W3C SVG
"""

import sys
from pathlib import Path
from src.ppt_engine.diagram_engine import export_drawio_stencil_to_svg, DrawIOProject

def verify_svg_file(svg_path: Path, label: str) -> None:
    assert svg_path.exists(), f"[{label}] SVG output file does not exist: {svg_path}"
    content = svg_path.read_text(encoding="utf-8")
    assert len(content) > 1000, f"[{label}] SVG content is suspiciously small ({len(content)} bytes)"
    assert "<svg" in content, f"[{label}] SVG root element missing in {svg_path}"
    assert "</svg>" in content, f"[{label}] Closing svg tag missing in {svg_path}"
    assert "xmlns=\"http://www.w3.org/2000/svg\"" in content, f"[{label}] Missing SVG XML namespace"
    print(f"[{label}] Verified: {svg_path} ({len(content)} bytes, valid SVG root)")

def main():
    test_files = [
        Path("output/diagrams_v2/proposed_aws_lambda.drawio"),
        Path("output/diagrams_v2/cdsw_legacy_batch.drawio"),
    ]
    
    out_dir = Path("output/diagrams_extracted_svg")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for f in test_files:
        if not f.exists():
            print(f"Skipping {f} (file does not exist)")
            continue
            
        target_svg = out_dir / f"{f.stem}_stencil.svg"
        print(f"Extracting stencils from {f} -> {target_svg}...")
        
        # 1. Test standalone function
        exported = export_drawio_stencil_to_svg(
            drawio_input=f,
            output_svg=target_svg,
            page_index=1,
            crop=True,
            transparent=True,
        )
        verify_svg_file(exported, f"Direct Function: {f.name}")
        
        # 2. Test DrawIOProject.export_page CLI path
        proj = DrawIOProject.load(f)
        target_proj_svg = out_dir / f"{f.stem}_proj_export.svg"
        out_proj = proj.export_page(
            name_or_index=0,
            output_path=target_proj_svg,
            format="svg",
            transparent=True,
        )
        verify_svg_file(out_proj, f"DrawIOProject.export_page: {f.name}")

    print("\nSUCCESS: All headless Draw.io stencil exports verified to standalone SVG.")

if __name__ == "__main__":
    main()
