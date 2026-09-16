# Architecture Decision Record (ADR): Custom Diagram Engine Pipeline vs. Draw.io MCP Server

> **Status:** Accepted / Canonical Architecture  
> **Date:** September 2026  
> **Topic:** Evaluation of Draw.io Model Context Protocol (MCP) Server vs. In-Engine Custom Python Pipeline  
> **Target Subsystems:** [`src/ppt_engine/diagram_engine.py`](../../src/ppt_engine/diagram_engine.py), [`src/ppt_engine/library_importer.py`](../../src/ppt_engine/library_importer.py), [`src/cli.py`](../../src/cli.py), [`assets/logos/`](../../assets/logos/)  
> **Related Documents:** [drawio_icon_system_architecture.md](drawio_icon_system_architecture.md), [../backlog/diagram_architecture.md](../backlog/diagram_architecture.md)

---

## 1. Context & Architectural Dilemma

During the evolution of `enterprise-bench`'s diagram subsystem, the following architectural question was evaluated:

> **Why build a custom Python AST, layout compiler, and SVG/XML serialization pipeline instead of using an off-the-shelf Model Context Protocol (MCP) server for Draw.io (or diagrams.net) to manipulate diagrams and port vendor icons?**

This ADR formalizes the trade-off analysis, technical constraints, and long-term rationale to prevent redundant re-evaluations in future planning cycles.

---

## 2. Core Separation: Protocol Layer vs. Engine Layer

An **MCP (Model Context Protocol) Server** operates at the **agent protocol layer**. It exposes JSON-RPC tools enabling an LLM agent to interact with an external process (e.g., query canvas coordinates, add shapes, trigger an Electron or headless Chromium export).

`enterprise-bench` is an **automated deliverable generation platform**, not merely an interactive canvas-manipulation bot. Its diagram subsystem is bound to two simultaneous, non-negotiable delivery targets:

1. **Headless Presentation Artifacts (`.pptx` / `.docx`):** High-resolution raster images ($300\text{ DPI}$, 16:9 aspect ratio, strict visual card geometry) compiled deterministically via CairoSVG and Pillow in Python without launching external graphical environments.
2. **Interactive Client Handovers (`.drawio`):** Pure source XML files delivered to enterprise client architects, PMOs, and engineering leads for ongoing governance, reviews, and post-engagement operations.

---

## 3. Detailed Trade-Off Matrix

| Evaluation Dimension | Draw.io MCP Server (Community / Playwright / Electron) | Custom In-Engine Pipeline (`DrawIOProject` + `diagram_engine.py`) |
| :--- | :--- | :--- |
| **Dual-Target Parity (The CairoSVG Dilemma)** | **Fails.** Native Draw.io stencils (`shape=mxgraph.aws4.*`) reside exclusively in Draw.io's proprietary client JavaScript runtime. Headless Python (`cairosvg`, `pillow`) cannot parse or render mxGraph JS shapes into presentation slides without spawning a headless browser for every single diagram. | **Succeeds.** We manage source SVGs directly. Cairo renders vector SVGs into high-DPI slide cards, while `DrawIOConverter` embeds the identical SVG as a base64 Data URI inside compound `shape=label` XML cells. |
| **Deliverable Portability & Client Handoff** | **Brittle.** Nodes referencing external web URIs or proprietary stencil extensions fail or render as blank boxes when client architects open the file offline, behind enterprise firewalls, or in unconfigured desktop editors. | **100% Self-Contained.** Base64 Data URIs (`image=data:image/svg+xml;base64,...`) are embedded directly into the `.drawio` XML. The file has zero external dependencies and renders with 100% visual fidelity in any Draw.io viewer. |
| **Runtime Footprint & CI/CD Determinism** | **Heavy & Fragile.** Requires persistent background daemons (Node.js/Chromium/Electron), WebSocket/stdio lifecycle management, and external runtime dependencies. Prone to connection drops, port conflicts, and high latency during batch jobs. | **Zero Overhead.** Pure Python AST and XML serialization running entirely within the project virtual environment via `uv run bench diagram ...`. Extremely fast (sub-10ms compilation per diagram). |
| **Vendor Icon Catalog & Extensibility** | **Constrained.** Limited to whatever shapes the specific MCP server has indexed or whatever default stencil libraries are loaded. Ingesting proprietary vendor packs (Cloudera CDP, custom bank emblems) requires hacking server bundles. | **Full Control.** Through [`library_importer.py`](../src/ppt_engine/library_importer.py), the platform can ingest raw vendor XML libraries (`<mxlibrary>`), decompress Pako/zlib payloads, normalize SVGs, and register them directly into `assets/logos/`. |
| **Consulting Layout & Typography Rules** | **Uncontrolled.** Relies on generic mxGraph auto-layout, which often produces ultra-wide single-tier ribbons ($>10:1$ aspect ratios) that shrink into unreadable hairlines when embedded into 16:9 slides. | **Strictly Enforced.** The engine enforces balanced 3-column / multi-tier layouts (target aspect ratio $2.5:1$ to $3.5:1$), optical minimum font sizes ($\ge 11\text{pt}$ to $14\text{pt}$), dedicated icon badges ($40\times 40$ px), and orthogonal bus routing. |
| **Human Ergonomics vs. Agent Micromanagement** | **High Overhead.** Moving nodes or tweaking connections via prompt-by-prompt agent interaction is tedious and high-latency compared to direct user action. | **Practical Handoff.** The platform generates the structured baseline (90% effort); humans adjust or fine-tune layout in Draw.io Desktop with standard mouse and keyboard in seconds. |

---

## 4. The Core Blockers an MCP Server Cannot Solve

Even if a Draw.io MCP server were integrated tomorrow:

1. **The Vector Extraction Bottleneck:**  
   An MCP tool might let an agent call `add_node(stencil="mxgraph.aws4.bucket")`, but it does **not** provide the raw SVG path data to Python. To embed that diagram into a PowerPoint deck using `python-pptx`, the engine would still have to screenshot the canvas via headless Chrome, losing vector crispness, transparency tuning, and layout flexibility.

2. **Batch Generation Scale:**  
   In a standard consulting engagement (e.g., FSD, TSD, Executive Decks, Cutover Runbooks), the toolchain generates between 25 and 50 diagrams across multiple lifecycle stages. Serializing dozens of interactive JSON-RPC requests to an MCP browser session introduces significant failure points compared to compiling all diagrams locally in a single `uv run bench` invocation.

---

## 5. Where an MCP Server *Does* Make Sense (Future Scope)

An MCP server is not an *alternative* to our engine—it is an *interface layer*.

If future engagement workflows require **live, interactive canvas synchronization** directly inside agent chat (e.g., an architect prompting: *"Inspect the open canvas in my editor, highlight all unencrypted ingress paths in amber, and add a disaster recovery note"*), an MCP server can be introduced as a **thin wrapper around our existing `DrawIOProject` AST and CLI commands**:

```
[ LLM Agent ] ──(MCP Tool Call)──> [ bench-mcp-wrapper ] ──> [ DrawIOProject / CLI ] ──> [ .drawio XML ]
```

In this architecture, the engine remains the single source of truth for AST parsing, layout constraints, and self-contained SVG serialization. The MCP server simply exposes those capabilities to the agent protocol layer.

---

## 6. The Verdict

Building the dedicated in-engine pipeline was the correct architectural choice:
1. It guarantees **100% visual parity** between presentation slide cards (CairoSVG) and interactive client files (Draw.io XML).
2. It produces **fully self-contained, air-gapped deliverables** with zero broken asset paths.
3. It keeps execution **deterministic, fast, and dependency-free** via `uv run bench`.
4. It eliminates the need to babysit an LLM to micromanage pixel coordinates that human architects can adjust in seconds with a mouse.

Any future MCP work should strictly serve as an optional CLI wrapper for interactive sessions, not as a replacement for the core diagram compilation engine.
