# Architecture Decision Record: OfficeCLI Evaluation & The 3-Lane Request Routing Architecture

- **Status:** ACCEPTED / MANDATED
- **Date:** 2026-10-28
- **Scope:** Document & Presentation Automation (`enterprise-bench`)
- **Credits:** **Vrieza** — for proposing the evaluation of `iOfficeAI/OfficeCLI` and sparking the design of our headless agent interaction tiers.
- **Related Governance:** [`AGENTS.md`](../../AGENTS.md) (The 3-Lane Request Routing Triad), [`ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md`](ADR_DECLARATIVE_YAML_VS_IMPERATIVE_PYTHON.md)

---

## 1. Context & Motivation

During architectural reviews of AI agent workflows for enterprise documents, **Vrieza** recommended evaluating **OfficeCLI** (`iOfficeAI/OfficeCLI`), an open-source tool designed to give AI agents structured CLI access to office files.

OfficeCLI demonstrated three distinct levels of interaction:
1. **L1 (Semantic Inspection):** High-level structured read / outline extraction.
2. **L2 (DOM Micro-Edits):** Path-based element patching without full-file rewrites.
3. **L3 (Headless Rendering):** Headless export and preview.

## 2. Decision & Inspiration

Rather than taking on external C# / npm binaries or modifying our runtime dependencies, OfficeCLI inspired the formalization of our native Python architecture in [`AGENTS.md`](../../AGENTS.md): **The 3-Lane Request Routing Triad**.

- **Lane 1 (Inspired by OfficeCLI L1):** Headless inspection and read-only audits (`uv run bench ppt view`, `bench doc view`, `bench diagram v2 audit --strict`).
- **Lane 2 (Inspired by OfficeCLI L2):** In-situ micro-patching of text, badges, and images (`uv run bench ppt patch`, `bench ppt replace-image`) without layout recompilation.
- **Lane 3 (Greenfield Layout & Synthesis):** Declarative YAML specifications compiled via Diagram Engine V2 (`uv run bench diagram v2 compile`), retaining zero-dependency Python vector generation.

## 3. Practical Consequence

OfficeCLI served as the direct conceptual blueprint for splitting agent operations into discrete, lightweight lanes, preventing massive token burn and unnecessary full-file re-renders for routine edits.
