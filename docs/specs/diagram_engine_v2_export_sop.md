# SOP: Diagram Engine V2 Standalone Export Protocol

## 1. Overview & Objective
This SOP defines the deterministic protocol for exporting the declarative **Diagram Engine V2** system from `enterprise-bench` into a 100% self-contained, portable, timestamped distribution (`diagram_engine_v2_portable_<TIMESTAMP>.zip`).

The export boundary ensures external collaborators can run the entire compilation pipeline (Draw.io XML, SVG, PNG, native PPTX) with zero dependencies on `src.core` or root bench frameworks, while guaranteeing workspace separation so future engine updates never overwrite client diagrams.

---

## 2. Directory & Workspace Boundary Standard
Any portable bundle produced under this SOP strictly enforces a 4-tier separation:

```text
diagram_engine_v2_bundle_<TIMESTAMP>/
├── compile.py              # Zero-overhead standalone runner script
├── requirements.txt        # python-pptx, pydantic, pyyaml, pillow, cairosvg
├── README.md               # Clear setup and boundary safety instructions
│
├── 📂 my_specs/            # 🟢 SAFE ZONE: User's custom YAML specs (retained on update)
├── 📂 my_output/           # 🟢 SAFE ZONE: User's compiled outputs (retained on update)
│
├── 📂 specs/               # Canonical reference and sample specifications
├── 📂 engine/              # 🔴 ENGINE ZONE: Core compiler, auditor, geometry, and reconciler
└── 📂 assets/              # 🔴 ASSET ZONE: Centralized vendor logos (AWS, Azure, etc.) & icons
```

---

## 3. Dependency Decoupling & Transitive Closure
The portable bundle extracts:
1. **Core Package:** `src/ppt_engine/diagram_v2/` $\to$ `engine/diagram_v2/`
2. **Icon & Asset Resolvers:**
   - `src/ppt_engine/library_importer.py` $\to$ `engine/library_importer.py`
   - `src/ppt_engine/asset_harvester.py` $\to$ `engine/asset_harvester.py`
3. **Vendor Icons & Manifests:**
   - `assets/icons/` $\to$ `assets/icons/`
   - `assets/logos/` $\to$ `assets/logos/`
4. **AST Import Rewrite:**
   - `src.ppt_engine.diagram_v2` $\to$ `engine.diagram_v2`
   - `src.ppt_engine.library_importer` $\to$ `engine.library_importer`
   - `src.ppt_engine.asset_harvester` $\to$ `engine.asset_harvester`
   - `_REPO_ROOT = Path(__file__).resolve().parent.parent` in resolvers.

---

## 4. Execution Standard & Trigger
Whenever the user asks to *"export the library"*, *"export the visualization engine"*, or *"create a portable bundle"*, execute the canonical builder:

```bash
# Run canonical builder script from workspace root
python3 scripts/build_diagram_bundle.py
```

### Verification Gate
Before releasing the archive:
1. Extract into an ephemeral `/tmp/` environment.
2. Compile the bundled sample spec headlessly (`specs/sample_dynamodb_whitelist.yaml`).
3. Verify that Draw.io XML, SVG, and PPTX outputs exist and return zero errors.
4. Verify destination `.zip` is ignored by `.gitignore`.
