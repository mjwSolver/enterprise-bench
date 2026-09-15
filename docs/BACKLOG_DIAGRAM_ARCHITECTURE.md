# Backlog & Architecture Decision: Single Monolithic `.drawio` vs. Dedicated Per-Document Files

> **Status:** Open Backlog / Architecture Trade-Off  
> **Topic:** Diagram File Organization, Searchability, and Human Collaboration UX  
> **Related Documents:** [docs/ADR_DRAWIO_PIPELINE_VS_MCP.md](ADR_DRAWIO_PIPELINE_VS_MCP.md), [docs/DRAWIO_ICON_SYSTEM_ARCHITECTURE.md](DRAWIO_ICON_SYSTEM_ARCHITECTURE.md)

---

## 1. Context & Architectural Dilemma

In enterprise engagements (e.g., Snowflake analytics, cloud migrations), a full lifecycle produces between 25 and 50 distinct visual diagrams:
- **Initiation & Presales:** High-level solution blueprint, team RACI model, executive roadmap.
- **Planning & Architecture (FSD / TSD):** Ingestion pipelines, data lakehouse layering, CDC flows, network topology, authentication sequence, CI/CD promotion gate.
- **Execution & Monitoring:** Defect triage workflow, release rundown, change management lifecycle.
- **Cutover & Go-Live:** DR failover sequence, cutover blackout timeline, operational runbook.

The fundamental design dilemma:
> **Should all 40+ diagrams live inside ONE single master `.drawio` file with 40 tabs, or should diagrams be separated into dedicated `.drawio` files partitioned by deliverable (e.g., `fsd_diagrams.drawio`, `tsd_diagrams.drawio`, `decks.drawio`)?**

---

## 2. Human Reviewer UX & In-App Searchability

If a human technical architect or client reviewer opens the file manually to make adjustments, what is the user experience?

### A. In-App GUI Search (Draw.io Desktop / Web / VS Code Extension)
1. **Find within Active Tab:** Draw.io provides a standard search bar (`Cmd+F` / `Ctrl+F`). It searches shape text, labels, and metadata **on the active page**.
2. **Cross-Tab Search Limitation:** In the Draw.io UI, there is **no native cross-tab search** that highlights search results across all 40 pages simultaneously. The user must manually click through pages or use the page picker dropdown.
3. **Tab Bar Clutter:** With 40 pages, the bottom tab bar overflows significantly. While Draw.io offers a vertical page list menu (click the page name dropdown at the bottom left), navigating 40 pages with similar enterprise titles (e.g., *Data Flow 1*, *Data Flow 2*, *Data Ingestion*) creates cognitive overhead for human editors.

### B. Agent & CLI Search (Programmatic Advantage)
Because `.drawio` files are uncompressed XML under the hood:
- Agents and CLI commands can parse and search across 40 tabs in under 5 milliseconds.
- `bench diagram list <file.drawio>` immediately outputs all tab names, indices, and node/edge counts.

---

## 3. Options Matrix

| Dimension | Option A: Single Monolithic File (`master.drawio`, 40+ Tabs) | Option B: Per-Deliverable Files (`fsd.drawio`, `tsd.drawio`, `deck.drawio`) | Option C: Hybrid by Lifecycle Stage (`stage2_design.drawio`, etc.) |
| :--- | :--- | :--- | :--- |
| **Human Review UX** | Low to Medium. Overwhelming tab bar; hard to locate 1 diagram out of 40 without prior knowledge. | **High.** Direct 1:1 mapping between deliverable and diagram file (3-6 tabs per file). | **High.** Logical staging; matches project timeline. |
| **Git Concurrency** | **High risk.** Multiple engineers/agents working on different documents touch the same XML file $\rightarrow$ merge conflicts. | **Zero risk.** Separate files for separate document owners. | Low risk. |
| **Traceability** | All visual assets centralized in one artifact. | Easy to zip/deliver specific document source packages to clients. | Balances centralization with modularity. |
| **Engine Flexibility** | Fully supported by `DrawIOProject`. | Fully supported by `DrawIOProject` (file path is arbitrary). | Fully supported by `DrawIOProject`. |

---

## 4. Slide Exporting: Transparent vs. White Background

Presentation slide builders frequently require diagram exports. Both modes are implemented in the CLI (`bench diagram export`):
- **White Background (`--white-bg`):** `--output diag.png --white-bg` renders solid pure white (`#FFFFFF`) or brand canvas color (`#F8FAFC`).
- **Transparent Background (`--transparent`):** `--output diag.png --transparent` emits a 32-bit RGBA PNG with a completely transparent alpha channel.

### Technical Limitations & Considerations for Slide Decks

1. **Text Contrast Against Slide Surface:**
   - **Limitation:** If a diagram was authored using dark-theme presets (e.g., `executive_tech` with `#F8FAFC` light-colored text) and is exported with `--transparent` onto a standard white PowerPoint card, the text becomes unreadable.
   - **Rule:** Use `--transparent` primarily when the diagram theme matches the slide surface (e.g., dark nodes on light slides, or light nodes on dark slides). Use `--white-bg` or solid canvas if embedding as an isolated card container.
2. **Drop Shadow / Alpha Compositing:**
   - Diagram cards use subtle SVG drop shadows (`feDropShadow`). In transparent mode, shadows blend natively with the slide background color, but PowerPoint's image compression can occasionally create dark halo artifacts around semi-transparent edges if rescaled aggressively.
3. **Connector Overlaps:**
   - In transparent mode, any orthogonal connector running behind a transparent node box can show through unless the node has an explicit solid fill (`fillColor=#FFFFFF`). The engine enforces solid card fills on node vertices to prevent line bleed-through.

---

## 5. Recommended Decision for Backlog

> [!TIP]
> **Recommended Standard (Option B / C - Per-Deliverable Partitioning):**
> Instead of forcing 40 diagrams into a single massive file, adopt a **per-deliverable convention** inside `diagrams/`:
> - `output/<project>/diagrams/01_pitch_deck.drawio` (2-4 tabs)
> - `output/<project>/diagrams/02_fsd_specs.drawio` (5-8 tabs)
> - `output/<project>/diagrams/03_tsd_architecture.drawio` (6-10 tabs)
> - `output/<project>/diagrams/04_cutover_runbook.drawio` (3-5 tabs)
>
> This gives human reviewers manageable files (never more than 8 tabs per file), prevents Git merge conflicts, and maps 1:1 with deliverable handovers.

---

## 6. Backlog Item: Diagram Icon Weight, Stroke Consistency & Palette Harmonization

> **Status:** Queued Architecture Item  
> **Target Subsystem:** `src/ppt_engine/diagram_engine.py`, `assets/logos/`, `DrawIONode` AST

### A. Context & Motivation
With the integration of vector iconography and brand emblems into `.drawio` nodes (`icon` / `icon_color`), diagrams now visually communicate technology identities directly (e.g., Apache Kafka, Snowflake, dbt, AWS, HashiCorp Vault). 

However, visual asset consistency across heterogeneous icons presents two specific design challenges:
1. **Stroke Weight Mismatch (`light` outline vs. `weighted` solid):**
   - Combining ultra-thin line icons (e.g., 1px stroke Lucide wireframes) directly alongside heavy, solid filled silhouettes (e.g., solid font-awesome glyphs or dense logos) creates visual imbalance on executive slides.
2. **Color Fragmentation vs. Brand Preservation:**
   - Generic utility icons (e.g., database, lock, cloud, server) look best when harmonized to the parent container's accent color (e.g. primary brand blue `#2563EB` or slate `#475569`).
   - Official vendor logos (e.g., Snowflake cyan `#29B5E8`, AWS orange `#FF9900`, Vault green `#000000`) must preserve their authentic corporate brand colors, unless explicitly specified in monochrome/duotone mode for high-contrast slides.

---

### B. Requirements & Design Specifications

1. **Explicit Weight Classification (`weight: "light" | "weighted" | "brand"`):**
   - In `DrawIONode` and the icon asset manifest, annotate vector assets with their geometric style:
     - `light`: Outline stroke vectors (stroke width 1.5–2px, transparent fill).
     - `weighted`: Solid silhouette fills.
     - `brand`: Multi-color official corporate logos.
   - Enforce consistency: Diagrams within the same deliverable should default to a unified glyph style unless distinguishing external inputs/outputs from internal system core.

2. **Dynamic SVG Palette Injection & Stroke Replacement:**
   - Enhance SVG asset inlining in `_render_node_svg`:
     - When an outline or monochrome icon has `icon_color` specified (or defaults to the node's `stroke_color`), the engine should dynamically replace `currentColor`, `stroke="..."`, or `fill="..."` attributes with the designated theme hex before base64 encoding.
     - Provide an opt-in toggle `preserve_brand_color: bool = True` for official logos so brand trademarks are not inadvertently overridden by container theme tints.

3. **Curated Icon Asset Library (`assets/logos/` & `assets/icons/`):**
   - Establish a standard asset catalog partitioned by style:
     - `assets/icons/outline/`: Standardized Lucide/Heroicon SVGs normalized to 24×24 viewBox and 1.75px stroke.
     - `assets/icons/solid/`: Normalized weighted SVGs.
     - `assets/logos/`: Official brand SVGs (Kafka, Snowflake, dbt, AWS, Vault, etc.) with normalized square viewports.

