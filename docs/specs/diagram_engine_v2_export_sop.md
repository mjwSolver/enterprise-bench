# SOP: Diagram Engine V2 Standalone Export Protocol

## 1. Overview & Objective
This SOP defines the deterministic protocol for exporting the declarative **Diagram Engine V2** system from `enterprise-bench` into a 100% self-contained, portable, version-stamped distribution (`diagram_engine_v2_portable_v<SEMVER>_<TIMESTAMP>.zip`).

The export boundary ensures external collaborators can run the entire compilation pipeline (Draw.io XML, SVG, PNG, native PPTX) with zero dependencies on `src.core` or root bench frameworks, while guaranteeing workspace separation so future engine updates never overwrite client diagrams.

> **CRITICAL DIRECTIVE ON ARCHIVE NAMING:**
> Never produce, distribute, or email unversioned or timestamp-only zip files (e.g., `diagram_bundle.zip` or `diagram_engine_v2_portable_20261024_170143.zip`). All archives MUST explicitly stamp their semver release version directly in the filename (`diagram_engine_v2_portable_v2.2_20261026_160000.zip`) and inner staging root (`diagram_engine_v2_bundle_v2.2_20261026_160000/`) so recipients and collaborators immediately know if they possess the right or wrong version.

---

## 2. Directory & Workspace Boundary Standard
Any portable bundle produced under this SOP strictly enforces a 4-tier separation:

```text
diagram_engine_v2_bundle_v<SEMVER>_<TIMESTAMP>/
├── compile.py                          # Zero-overhead standalone runner script
├── requirements.txt                    # python-pptx, pydantic, pyyaml, pillow, cairosvg
├── README.md                           # Clear setup, boundary safety & quick-test prompt
├── VERSION_LOG.md                      # Release ledger with delta tracking vs. prior zips
├── candidate_reference_slide_3.png     # Visual reference benchmark for testing prompts
│
├── 📂 my_specs/                        # 🟢 SAFE ZONE: User's custom YAML specs (retained on update)
├── 📂 my_output/                       # 🟢 SAFE ZONE: User's compiled outputs (retained on update)
│
├── 📂 specs/                           # Canonical reference and sample specifications
├── 📂 engine/                          # 🔴 ENGINE ZONE: Core compiler, auditor, geometry, reconciler
│   ├── 📂 diagram_v2/                  # Core V2 modules, contrast engine, and VERSION_LOG.md
│   ├── library_importer.py             # Vector icon catalog and index importer
│   ├── asset_harvester.py              # Vendor asset discovery helper
│   └── icon_engine.py                  # Dynamic icon tinting & multi-color logo guard
└── 📂 assets/                          # 🔴 ASSET ZONE: Centralized vendor logos (AWS, Azure, etc.) & icons
```

---

## 3. Mandatory Distributable Checklist & Invariants
Whenever packaging a new zip distributable, the builder MUST guarantee:
1. **Provenance Comment Signatures (`[MJW/AGY]`):**
   - Verified present in header docstrings of key engine modules (`__init__.py`, `compiler.py`, `contrast.py`, `auditor.py`, `models.py`).
2. **Version Log Ledger (`VERSION_LOG.md`):**
   - Located both at `engine/diagram_v2/VERSION_LOG.md` and mirrored at the root of the archive (`VERSION_LOG.md`).
   - Must explicitly note that it is compiled strictly for packaging and gzip/zip distribution tracking.
   - Must contain the exact release timestamp (`YYYY-MM-DD HH:MM:SS +0700`) and a delta breakdown vs. previous releases.
3. **Reference Visual Asset & Prompt:**
   - Bundled `candidate_reference_slide_3.png` in archive root.
   - Root `README.md` containing the lazy test seed prompt for immediate zero-friction onboarding.
4. **Dependency Decoupling & Transitive Closure:**
   - `src/ppt_engine/diagram_v2/` $\to$ `engine/diagram_v2/`
   - `src/ppt_engine/library_importer.py` $\to$ `engine/library_importer.py`
   - `src/ppt_engine/asset_harvester.py` $\to$ `engine/asset_harvester.py`
   - `src/ppt_engine/icon_engine.py` $\to$ `engine/icon_engine.py`
   - `assets/icons/` $\to$ `assets/icons/`
   - `assets/logos/` $\to$ `assets/logos/`
5. **AST / String Import Rewrites:**
   - `src.ppt_engine.diagram_v2` $\to$ `engine.diagram_v2`
   - `src.ppt_engine.library_importer` $\to$ `engine.library_importer`
   - `src.ppt_engine.asset_harvester` $\to$ `engine.asset_harvester`
   - `src.ppt_engine.icon_engine` $\to$ `engine.icon_engine`
   - `_REPO_ROOT = Path(__file__).resolve().parent.parent` in resolvers.

---

## 4. Execution Standard & Trigger
Whenever the user asks to *"export the library"*, *"export the visualization engine"*, or *"create a portable bundle"*, execute the canonical builder:

```bash
# Run canonical builder script (auto-detects version from pyproject.toml / VERSION_LOG.md)
python3 scripts/build_diagram_bundle.py

# Or specify an explicit target version stamp
python3 scripts/build_diagram_bundle.py --version v2.2
```

### Verification Gate
Before releasing the archive:
1. Verify the generated zip is explicitly stamped: `diagram_engine_v2_portable_v<SEMVER>_<TIMESTAMP>.zip`.
2. Extract into an ephemeral `/tmp/` environment.
3. Compile the bundled sample spec headlessly (`specs/sample_dynamodb_whitelist.yaml`).
4. Verify that Draw.io XML, SVG, and PPTX outputs exist and return zero errors.
5. Verify destination `.zip` is ignored by `.gitignore` in `output/releases/`.
