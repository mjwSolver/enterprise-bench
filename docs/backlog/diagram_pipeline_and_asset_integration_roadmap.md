# Architecture RFC: Unified Diagram Pipeline, Draw.io Asset Harvester & Presentation Parity

> **Status:** Draft / Active Backlog RFC  
> **Topic:** Elimination of SVG/Draw.io Code Drift, Deterministic Vendor Icon Ingestion, and Native PowerPoint vs. Draw.io Dual-Tier Workflow  
> **Target Subsystems:** [`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py), [`src/ppt_engine/library_importer.py`](../../src/ppt_engine/library_importer.py), [`src/cli.py`](../../src/cli.py), [`assets/logos/`](../../assets/logos/), [`assets/icons/`](../../assets/icons/)  
> **Related Documents:** [`docs/specs/drawio_icon_system_architecture.md`](../specs/drawio_icon_system_architecture.md), [`docs/specs/adr_drawio_pipeline_vs_mcp.md`](../specs/adr_drawio_pipeline_vs_mcp.md), [`docs/backlog/diagram_architecture.md`](diagram_architecture.md)

---

## 1. Context & Architectural Dilemma

Recent diagram generation efforts revealed three operational friction points:

1. **Rendering Drift (The Two-Brain Anti-Pattern):**  
   One-off scripts (e.g. `scripts/generate_current_cdsw_process.py`) authored raw SVG for presentation polish (drop shadows, curved bezier arcs, pill badges) while producing `.drawio` XML as a secondary afterthought. Raster previews were compiled directly from SVG via `cairosvg`/`rsvg-convert`, decoupling the visual image from the editable `.drawio` file.
2. **Icon Lottery (Unverified Web Sourcing):**  
   Missing corporate and technology logos (e.g., Cloudera CDSW, Databricks DBX) defaulted to unverified web searches, yielding outdated or incorrect marks (e.g., SimpleIcons' 2016 legacy circular orange "C" instead of modern Cloudera CDP or product-specific badges).
3. **The Editing Dichotomy:**  
   Raw SVG provides high visual fidelity but zero diagram semantics (connectors do not adhere to moving cards; non-technical stakeholders cannot edit raw SVG). Conversely, standard `.drawio` files excel at technical topology editing but lack the high-gloss aesthetic required for executive steering decks.

---

## 2. Agreed Strategic Principles

### A. Clear Role Split: Executive Slides vs. Engineering Topologies
* **Executive & PMO Deliverables (PowerPoint / Keynote):** Composed using native PowerPoint DrawingML shapes or high-fidelity vector cards with consulting aesthetics (subtle shadows, top accent stripes, metric pills).
* **Technical Architecture Deliverables (Draw.io / Confluence / FSD/TSD):** Composed using strict orthogonal routing, 90-degree elbows, magnetic connection ports, and standard container swimlanes.
* **Shared Asset Layer:** Both presentation slides and Draw.io topologies must resolve assets from the **same deterministic vector catalog**.

### B. Universal Non-Technical Editability
* End-users must be able to edit deliverables without installing vector design software (Figma/Inkscape).
* Presentations must support direct in-slide editing via Microsoft PowerPoint (`.pptx` native shapes).
* Technical architecture documents must support in-canvas editing via Draw.io Desktop, `diagrams.net`, or the VS Code Draw.io extension (`.drawio` / `.drawio.svg`).

---

## 3. Target Architecture & Improvements

```
                              [ Unified Diagram AST ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ Technical Topology ]                           [ Executive Presentation ]
                 │                                               │
                 ▼                                               ▼
       [ High-DPI .drawio.svg ]                      [ Native PPTX DrawingML Shapes ]
    (Embedded <mxfile> for IDE/Web)                    (Directly editable in PPT)
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                        [ Central Asset Harvester & Cache ]
                         - Draw.io Official Stencils (jgraph)
                         - Vendor <mxlibrary> (Databricks, Cloudera)
                         - Curated Vector CDNs (SVGL, Devicon)
```

### 1. Deterministic Draw.io Asset Harvester (No Web Search Roulette)
Instead of ad-hoc web searches, the asset subsystem will ingest icons deterministically:
* **Official Stencil Harvest:** Mirror Draw.io's open-source vector stencil repository (`jgraph/drawio/src/main/webapp/stencils/`) for official cloud libraries (AWS4, GCP, Azure, Kubernetes).
* **Vendor Pack Decompression:** Leverage existing `src/ppt_engine/library_importer.py` to decode vendor `<mxlibrary>` XML files (Databricks DBX, Cloudera CDP, Snowflake) into normalized SVGs stored in `assets/logos/<vendor>/`.
* **CLI Asset Resolver:** Introduce `uv run bench asset resolve <key>` to query the local index (`assets/icons/manifest.json`), falling back to trusted developer CDNs (SVGL API, Devicon) before logging missing assets.

### 2. Hybrid Editable `.drawio.svg` Pipeline
* Replace separate SVG and XML outputs with native `.drawio.svg`.
* Draw.io's hybrid format contains valid W3C SVG for CairoSVG/slide rendering while embedding compressed `<mxfile>` XML in its metadata.
* Files render as crisp vector images in browsers/GitHub and open as full drag-and-drop editable diagrams in Draw.io and VS Code.

### 3. Native PowerPoint Shape Compiler
* Extend `src/ppt_engine/diagram_engine.py` to compile diagram AST nodes into native grouped `python-pptx` shapes.
* Rectangles, text frames, and connectors become native PowerPoint objects, allowing consultants to tweak wording, reposition cards, and re-color elements directly in Microsoft Office.

---

## 4. Phased Execution Roadmap

### Phase 1: Icon Rectification & Asset Sourcing
* [x] Replace legacy Cloudera icon on CDSW card with authentic modern Cloudera mark or CDP Data Science badge. (Completed: authentic faceted mark in `assets/logos/cloudera/cloudera_official.svg` and CDSW product emblem in `assets/logos/cloudera/cloudera_cdsw.svg`)
* [x] Ingest Databricks (DBX) vector assets into `assets/logos/databricks/`. (Completed: 72 official vector stencils harvested, cached in `vendor_packs/databricks_icons.xml`, registered in `assets/icons/manifest.json`)
* [x] Implement `bench asset resolve <key>` CLI command. (Completed: deterministic resolver in `src/ppt_engine/asset_harvester.py`, exposed via `uv run bench asset resolve <key>`, supporting table/JSON modes with zero web scraping)

### Phase 2: Draw.io Stencil Mirror & Ingestion
* [x] Add automated script/command to ingest Draw.io's official cloud and technology stencils. (Completed: `AssetHarvester.harvest_aws_pack()`, Databricks, Cloudera, exposed via `uv run bench asset harvest`)
* [x] Register all ingested assets into `assets/icons/manifest.json`. (Completed: AWS Lambda, API Gateway, Secrets Manager, S3, Databricks 72 stencils, Cloudera services)

### Phase 3: `.drawio.svg` Compilation & Parity Gate
* [x] Update `DrawIOConverter` to emit `.drawio.svg` containing embedded `<mxfile>` metadata. (Completed: `DrawIOConverter.to_drawio_svg()` injects root `content` attribute and `<desc>` CDATA)
* [x] Verify that CairoSVG and rsvg-convert render the generated `.drawio.svg` with zero visual distortion. (Completed: Parity Gate passed for `current_process_cdsw.drawio.svg` and `proposed_aws_lambda.drawio.svg`)

### Phase 4: Native PowerPoint Shape Engine
* [x] Implement `PowerPointDiagramRenderer` to transform diagram AST into native `python-pptx` shape trees. (Completed: `PowerPointDiagramCompiler` in `src/ppt_engine/pptx_diagram_compiler.py` renders native DrawingML containers, cards, text frames, badges, and connectors)
* [x] Add CLI flag `--format pptx-shapes` to `bench diagram export`. (Completed: `uv run bench diagram export-pptx` generates 2-slide presentation `output/presentations/architecture_evolution_cdsw_to_lambda.pptx`)

---

## 5. Subagent Delegation Guidance

When tasking parallel subagents during implementation sprints:
* **Asset Engineer:** Task with downloading, normalizing, and registering authentic SVG packs via `library_importer.py`.
* **Diagram Engine Maintainer:** Task with `.drawio.svg` serialization and CairoSVG verification.
* **PPTX Builder Engineer:** Task with DrawingML shape mapping and connector layout.
