import os
import sys
import shutil
import zipfile
import datetime
from pathlib import Path

def build_bundle():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_name = f"diagram_engine_v2_bundle_{ts}"
    staging_root = f"/tmp/{bundle_name}"
    
    repo_root = Path("/Users/marcelljw/VisualStudioCode/enterprise-bench")
    
    if os.path.exists(staging_root):
        shutil.rmtree(staging_root)
    os.makedirs(staging_root, exist_ok=True)

    print(f"Staging bundle at: {staging_root}")

    # 1. Copy diagram_v2 core
    shutil.copytree(
        repo_root / "src/ppt_engine/diagram_v2",
        os.path.join(staging_root, "engine", "diagram_v2"),
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )

    # 2. Copy library_importer, asset_harvester, and icon_engine
    shutil.copy(
        repo_root / "src/ppt_engine/library_importer.py",
        os.path.join(staging_root, "engine", "library_importer.py")
    )
    shutil.copy(
        repo_root / "src/ppt_engine/asset_harvester.py",
        os.path.join(staging_root, "engine", "asset_harvester.py")
    )
    shutil.copy(
        repo_root / "src/ppt_engine/icon_engine.py",
        os.path.join(staging_root, "engine", "icon_engine.py")
    )

    # 3. Create engine/__init__.py
    with open(os.path.join(staging_root, "engine", "__init__.py"), "w", encoding="utf-8") as f:
        f.write('"""Standalone Diagram Engine V2 Package."""\n')

    # 4. Copy assets/icons and assets/logos
    os.makedirs(os.path.join(staging_root, "assets"), exist_ok=True)
    shutil.copytree(
        repo_root / "assets/icons",
        os.path.join(staging_root, "assets", "icons")
    )
    shutil.copytree(
        repo_root / "assets/logos",
        os.path.join(staging_root, "assets", "logos")
    )

    # 5. Copy sample spec and candidate test slide
    os.makedirs(os.path.join(staging_root, "specs"), exist_ok=True)
    sample_spec = Path("/Users/marcelljw/Documents/antigravity/adventurous-darwin/BSIM_Migration/specs/diagrams/proposed_aws_dynamodb_whitelist.yaml")
    if sample_spec.exists():
        shutil.copy(sample_spec, os.path.join(staging_root, "specs", "sample_dynamodb_whitelist.yaml"))

    # Copy candidate reference image directly to bundle root
    candidate_img = Path("/Users/marcelljw/Documents/antigravity/adventurous-darwin/BSIM_Migration/output/candidate_reference_slide_3.png")
    if candidate_img.exists():
        shutil.copy(candidate_img, os.path.join(staging_root, "candidate_reference_slide_3.png"))

    # Copy VERSION_LOG.md to bundle root as well for immediate visibility
    version_log_src = repo_root / "src/ppt_engine/diagram_v2/VERSION_LOG.md"
    if version_log_src.exists():
        shutil.copy(version_log_src, os.path.join(staging_root, "VERSION_LOG.md"))

    # 6. Create safe workspaces
    os.makedirs(os.path.join(staging_root, "my_specs"), exist_ok=True)
    with open(os.path.join(staging_root, "my_specs", ".gitkeep"), "w") as f:
        f.write("")

    os.makedirs(os.path.join(staging_root, "my_output"), exist_ok=True)
    with open(os.path.join(staging_root, "my_output", ".gitkeep"), "w") as f:
        f.write("")

    # 7. Patch internal imports across engine/
    for root, _, files in os.walk(os.path.join(staging_root, "engine")):
        for f in files:
            if f.endswith(".py"):
                fp = os.path.join(root, f)
                with open(fp, "r", encoding="utf-8") as fh:
                    code = fh.read()

                code = code.replace("src.ppt_engine.diagram_v2", "engine.diagram_v2")
                code = code.replace("src.ppt_engine.library_importer", "engine.library_importer")
                code = code.replace("src.ppt_engine.asset_harvester", "engine.asset_harvester")
                code = code.replace("src.ppt_engine.icon_engine", "engine.icon_engine")

                if f in ("library_importer.py", "asset_harvester.py"):
                    code = code.replace(
                        "_REPO_ROOT = Path(__file__).resolve().parent.parent.parent",
                        "_REPO_ROOT = Path(__file__).resolve().parent.parent"
                    )

                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(code)

    # 8. Create compile.py
    compile_script = '''#!/usr/bin/env python3
"""
Standalone Diagram Engine V2 CLI Runner
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine.diagram_v2 import compile_diagram

def main():
    parser = argparse.ArgumentParser(
        description="Compile declarative diagram YAML to Draw.io XML, SVG, PNG, and native PowerPoint shapes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
IMPORTANT WORKSPACE DIRECTIVE:
-----------------------------
Always save your custom YAML files in 'my_specs/' and your outputs in 'my_output/'.
Do NOT edit or save inside 'engine/' or 'assets/'!
This ensures that when a new engine zip is released, you can update without overwriting your deliverables.
"""
    )
    parser.add_argument("spec", help="Path to the YAML diagram specification file")
    parser.add_argument("-o", "--output", default="my_output", help="Output directory or file path (default: my_output)")
    parser.add_argument("-f", "--format", default="all", help="Target formats: all, pptx, svg, drawio, png (comma-separated)")
    parser.add_argument("--open", action="store_true", help="Open generated PowerPoint presentation on desktop")

    args = parser.parse_args()

    spec_p = Path(args.spec)
    if not spec_p.exists():
        print(f"\\033[91m[Error]\\033[0m Spec file not found: {args.spec}")
        sys.exit(1)

    formats = [f.strip() for f in args.format.split(",") if f.strip()]
    out_path = Path(args.output)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"\\033[94m[*] Compiling diagram topology from:\\033[0m {args.spec}")
    try:
        res = compile_diagram(spec_path_or_dict=spec_p, output_dir_or_file=str(out_path), formats=formats, open_deck=args.open)
        print(f"\\033[92m[✓] Successfully compiled:\\033[0m {res.spec.name}")
        if res.drawio_path:
            print(f"  • Draw.io XML:  {res.drawio_path}")
        if res.svg_path:
            print(f"  • Vector SVG:   {res.svg_path}")
        if res.png_path:
            print(f"  • PNG:          {res.png_path}")
        if res.pptx_path:
            print(f"  • Native PPTX:  {res.pptx_path}")
    except Exception as e:
        print(f"\\033[91m[Error compiling diagram]:\\033[0m {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    with open(os.path.join(staging_root, "compile.py"), "w", encoding="utf-8") as f:
        f.write(compile_script)
    os.chmod(os.path.join(staging_root, "compile.py"), 0o755)

    # 9. Create requirements.txt
    reqs = '''# Diagram Engine V2 Standalone Requirements
python-pptx>=1.0.0
pydantic>=2.0.0
pyyaml>=6.0
pillow>=10.0.0
cairosvg>=2.7.0  # Optional: only needed if exporting high-DPI raster PNGs from SVG
'''
    with open(os.path.join(staging_root, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(reqs)

    # 10. Create README.md
    readme_content = f'''# Diagram Engine V2 — Standalone Portable Distribution
**Snapshot Timestamp:** `{ts}`

---

## 🚨 CRITICAL DIRECTIVE: WHERE TO SAVE YOUR WORK

> ### ⚠️ WARNING: DO NOT SAVE YOUR WORK INSIDE `engine/` OR `assets/`!
>
> 1. **SPEC FILES:** Author all your `.yaml` diagram specifications inside **`my_specs/`**.
> 2. **GENERATED ARTIFACTS:** Point all compilations to generate outputs inside **`my_output/`**.
> 3. **ENGINE INTEGRITY:** The **`engine/`** and **`assets/`** folders are strictly **ENGINE CODE & ASSETS**.
>
> When an updated Diagram Engine zip is provided in the future, you can safely extract and overwrite `engine/` and `assets/` **without risk of losing or overwriting your diagrams or presentations.**

---

## 🚀 Quick Start

### 1. Set Up Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Compile Your First Diagram
Run the bundled sample diagram (AWS DynamoDB Whitelist Architecture):
```bash
python compile.py specs/sample_dynamodb_whitelist.yaml
```
Output files will be generated in `my_output/`:
- `my_output/proposed_aws_dynamodb_whitelist.drawio` (Editable in Draw.io)
- `my_output/proposed_aws_dynamodb_whitelist.svg` (Resolution-independent vector)
- `my_output/proposed_aws_dynamodb_whitelist.pptx` (100% native editable PowerPoint shapes)

### 3. Compile Your Own Diagram
```bash
python compile.py my_specs/my_custom_diagram.yaml -o my_output/
```

### 4. Target Specific Formats Only
```bash
# Only compile to native PowerPoint
python compile.py my_specs/my_custom_diagram.yaml -f pptx

# Compile to PowerPoint and SVG only
python compile.py my_specs/my_custom_diagram.yaml -f pptx,svg
```

---

## 🧪 Hands-On Test: Create a New Architecture Slide

We have bundled a real reference architecture slide in the root folder: **`candidate_reference_slide_3.png`** (Proposed Databricks Lakebase Whitelist Architecture).

You can immediately test your AI coding assistant (or subagent) with a realistic workflow:

### Step 1: Open Your AI Agent Chat
In your IDE or chat interface, start a session inside this extracted folder.

### Step 2: Attach the Image
Drag & drop **`candidate_reference_slide_3.png`** into the chat window.

### Step 3: Copy & Paste This Lazy Prompt
````markdown
make a duplicate of this slide but swap out Databricks Lakebase with DynamoDB. 

Here are the notes from our discussion:
- Title should be DynamoDB Whitelist Verification
- keep the user/client side the same
- on the right side instead of lakebase it's aws dynamodb
- use api gateway for rest ingress, sub-10ms overhead
- add iam role for auth
- dynamo service key value store with single-digit ms latency
- 2 tables:
  1. device_whitelist table: PK device_id/mac, SK project_name, returns ALLOW/DENY
  2. device_audit_log table: PK mac_address, SK timestamp_iso, append-only stream, saves client ip and outcome
- hook up the arrows from api gateway to dynamodb and into both tables, then return status back to client

compile it with the engine script.
````

Your agent should author a new spec in `my_specs/` and run `python compile.py` to produce your PowerPoint slide in `my_output/` without modifying `engine/`!

---

## 📁 Folder Structure & Boundary Contract

```text
.
├── README.md                     # You are here
├── candidate_reference_slide_3.png # 🖼️ Reference slide for testing with AI
├── requirements.txt              # Minimal pip dependencies
├── compile.py                    # Single-command runner
│
├── 📂 my_specs/                  # 🟢 SAFE ZONE: Place all your custom .yaml specs here
├── 📂 my_output/                 # 🟢 SAFE ZONE: Default destination for all outputs (.pptx, .svg, .drawio)
│
├── 📂 specs/                     # Reference / sample diagram specifications
├── 📂 engine/                    # 🔴 ENGINE ZONE: Core compiler, auditor, and geometry pipeline
└── 📂 assets/                    # 🔴 ASSET ZONE: Standard vector vendor icons & logos
```
'''
    with open(os.path.join(staging_root, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 11. Create timestamped zip archive in output/releases/
    out_dir = Path("/Users/marcelljw/Documents/antigravity/adventurous-darwin/BSIM_Migration/output/releases")
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"diagram_engine_v2_portable_{ts}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(staging_root):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith(".pyc") or file == ".DS_Store":
                    continue
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, os.path.dirname(staging_root))
                zipf.write(full_p, rel_p)

    # Also mirror to enterprise-bench/output/releases/
    bench_out_dir = repo_root / "output/releases"
    bench_out_dir.mkdir(parents=True, exist_ok=True)
    bench_zip_path = bench_out_dir / f"diagram_engine_v2_portable_{ts}.zip"
    shutil.copy(zip_path, bench_zip_path)

    # Clean up staging directory
    shutil.rmtree(staging_root)

    print(f"ZIP_CREATED: {zip_path}")
    print(f"BENCH_MIRROR: {bench_zip_path}")
    print(f"SIZE_MB: {os.path.getsize(zip_path) / (1024 * 1024):.2f}")
    return zip_path

if __name__ == "__main__":
    build_bundle()
