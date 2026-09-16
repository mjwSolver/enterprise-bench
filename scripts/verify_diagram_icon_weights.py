"""
Targeted Verification Script: Diagram Icon Stroke Weight & Palette Harmonization
==============================================================================
Demonstrates and validates:
1. icon_weight == 'light': Outline stroke normalization (preventing 1px hairline disappearance)
2. icon_weight == 'brand': Authentic vendor brand color preservation:
   - Snowflake cyan (#29B5E8)
   - AWS orange (#FF9900)
   - Kafka white/black (#231F20 on light)
   - Cloudera native multi-color (#FF6A80 coral + white)
3. icon_weight == 'weighted': Solid silhouette fill & stroke harmonized to container accent palette
4. Headless & CLI export via `uv run bench diagram export`
"""

import base64
import os
import re
import subprocess
import sys
from pathlib import Path

# Ensure repo root on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ppt_engine.diagram_engine import DrawIONode, DrawIOProject


def main() -> None:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    drawio_file = output_dir / "test_diagram_weights.drawio"
    svg_output = output_dir / "test_diagram_weights.svg"
    png_output = output_dir / "test_diagram_weights.png"

    mermaid_code = """flowchart LR
    subgraph Ingress["Tier 1: Streaming Ingress"]
        KafkaNode["Apache Kafka Broker"]
    end
    subgraph Lakehouse["Tier 2: Enterprise Lakehouse"]
        SnowflakeNode["Snowflake Analytics"]
        AWSNode["AWS Cloud Storage"]
        ClouderaNode["Cloudera Data Hub"]
    end
    subgraph Governance["Tier 3: Security & Governance"]
        LightNode["Database Catalog"]
        WeightedNode["Shield Governance"]
    end
    KafkaNode --> SnowflakeNode
    KafkaNode --> AWSNode
    SnowflakeNode --> ClouderaNode
    AWSNode --> ClouderaNode
    LightNode --> SnowflakeNode
    WeightedNode --> ClouderaNode"""

    node_icons = {
        "KafkaNode": {"icon": "kafka", "icon_weight": "brand"},
        "SnowflakeNode": {"icon": "snowflake", "icon_weight": "brand"},
        "AWSNode": {"icon": "aws", "icon_weight": "brand"},
        "ClouderaNode": {"icon": "cloudera:cloudera_cdp_data_hub", "icon_weight": "brand"},
        "LightNode": {"icon": "lucide:database", "icon_weight": "light"},
        "WeightedNode": {"icon": "lucide:shield-check", "icon_weight": "weighted"},
    }

    print("[1/4] Building multi-weight Draw.io architecture project...")
    proj = DrawIOProject()
    proj.add_mermaid_page(
        name="Icon Weight Harmonization",
        mermaid_code=mermaid_code,
        theme="corporate_navy",
        font_size=18.0,
        node_icons=node_icons,
    )
    proj.save(drawio_file)
    print(f"      ✓ Saved .drawio project: {drawio_file}")

    print("\n[2/4] Verifying AST schema and icon_weight resolution...")
    for nid, props in node_icons.items():
        node = DrawIONode(id=nid, label=nid, custom_style=props)
        effective_w = node.icon_weight
        print(f"      Node {nid:15s} -> resolved icon_weight: {effective_w} (expected: {props['icon_weight']})")
        assert effective_w == props["icon_weight"], f"Weight mismatch for {nid}: {effective_w} != {props['icon_weight']}"

    # Also test inference without explicit icon_weight:
    auto_snowflake = DrawIONode(id="SF", label="Snowflake", custom_style={"icon": "snowflake"})
    auto_light = DrawIONode(id="DB", label="DB", custom_style={"icon": "lucide:database"})
    assert auto_snowflake.icon_weight == "brand", f"Auto inference failed for snowflake: {auto_snowflake.icon_weight}"
    assert auto_light.icon_weight == "light", f"Auto inference failed for lucide: {auto_light.icon_weight}"
    print("      ✓ AST schema and auto-inference successfully verified!")

    print("\n[3/4] Exporting diagram via `uv run bench diagram export` CLI...")
    cmd_svg = [
        "uv", "run", "bench", "diagram", "export",
        str(drawio_file),
        "--page", "Icon Weight Harmonization",
        "--format", "svg",
        "--output", str(svg_output),
        "--transparent",
    ]
    res_svg = subprocess.run(cmd_svg, capture_output=True, text=True, cwd=str(_ROOT))
    if res_svg.returncode != 0:
        print(f"CLI SVG export failed: {res_svg.stderr}")
        sys.exit(1)
    print(f"      ✓ CLI Exported SVG: {svg_output}")

    cmd_png = [
        "uv", "run", "bench", "diagram", "export",
        str(drawio_file),
        "--page", "Icon Weight Harmonization",
        "--format", "png",
        "--output", str(png_output),
        "--scale", "3.0",
        "--transparent",
    ]
    res_png = subprocess.run(cmd_png, capture_output=True, text=True, cwd=str(_ROOT))
    if res_png.returncode != 0:
        print(f"CLI PNG export failed: {res_png.stderr}")
        sys.exit(1)
    print(f"      ✓ CLI Exported PNG: {png_output}")

    print("\n[4/4] Inspecting rendered SVG vector and embedded data...")
    svg_text = svg_output.read_text(encoding="utf-8")
    b64_matches = re.findall(r'data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)', svg_text)
    decoded_svgs = [base64.b64decode(b).decode("utf-8", errors="ignore") for b in b64_matches]
    combined_content = svg_text + "\n" + "\n".join(decoded_svgs)

    checks = [
        ("Snowflake Cyan (#29B5E8)", "#29B5E8" in combined_content),
        ("AWS Orange (#FF9900)", "#FF9900" in combined_content),
        ("Kafka Black (#231F20)", "#231F20" in combined_content),
        ("Cloudera Native Coral (#FF6A80)", "#FF6A80" in combined_content),
        ("Stroke normalization (stroke-width >= 1.75px / 1.8px)", 'stroke-width="1.8"' in combined_content or 'stroke-width="2"' in combined_content or 'stroke-width="3"' in combined_content),
        ("Container accent palette harmonization", any(c in combined_content for c in ("#16A34A", "#3B82F6", "#2563EB", "#6366F1"))),
    ]

    print("\nVisual Palette & Stroke Verification Results:")
    all_passed = True
    for label, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {label}")

    if all_passed:
        print("\nAll diagram icon stroke weight & palette harmonization checks PASSED!")
    else:
        print("\nSome visual checks FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
