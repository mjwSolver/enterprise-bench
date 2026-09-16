# Handover: Unified CLI Architecture & Skill Refactoring

> **Target Repository:** `enterprise-bench`  
> **Date:** 2026-09-11  
> **Goal:** Refactor existing agent skills (`.agents/skills/`) to use the unified CLI entrypoint (`uv run bench ...`) rather than raw Python scripts or manual code exploration.

---

## 1. Context & Architectural State

1. **Pytest Granularity Implemented:**
   - [`pyproject.toml`](pyproject.toml) and [`tests/conftest.py`](tests/conftest.py) now provide explicit markers:
     - `-m unit`: Fast in-memory tests (<1s execution) covering `src.core`, PII scrubbing, dependency isolation, and CLI routing integrity.
     - `-m integration`: Slower end-to-end rendering tests (~30s) covering PPTX slide creation, OpenXML packaging, and CairoSVG rendering.
     - `-m ppt`, `-m docx`, `-m xlsx`, `-m core`: Engine-specific markers.

2. **Core CLI Router Exists:**
   - Exposed as `bench` in [`pyproject.toml`](pyproject.toml) mapped to [`src/cli.py`](src/cli.py).
   - Currently active sub-commands:
     ```bash
     uv run bench init-project <ProjectName>
     uv run bench ppt generate --theme <theme> --output <path>
     uv run bench ppt themes
     uv run bench doc stamp --template <name> --data <json> --output <path>
     uv run bench doc sanitize --input <raw.docx> --output <clean.docx>
     uv run bench doc lint --file <out.docx>
     ```

---

## 2. Target Deliverables for Incoming Fresh Agent

### A. Extend [`src/cli.py`](src/cli.py)
1. **Spreadsheet Sub-App (`bench xlsx ...`):**
   - Add `xlsx_app = typer.Typer(name="xlsx", help="Spreadsheet & Calculator Engine")`.
   - Bind `bench xlsx calculate --template <template.xlsx> --data <data.json> --output <out.xlsx>`.
2. **Fast Test / QA Command (`bench test`):**
   - Add `bench test --unit` (runs `pytest -m unit` in <1s) to allow agents a 1-command verification gate without triggering slow integration runs.

### B. Refactor Skills in [`.agents/skills/`](.agents/skills/)
Update the runbooks so agents execute 1-line CLI commands instead of writing custom `python-pptx` or `docxtpl` scripts:
1. **[`presentation-maker`](.agents/skills/presentation-maker/SKILL.md):**
   - Direct agents to invoke `uv run bench ppt generate` or import from `src.ppt_engine` instead of writing raw scratch scripts from scratch.
2. **[`enterprise-bench-ops`](.agents/skills/enterprise-bench-ops/SKILL.md):**
   - Ensure all 7 lifecycle stages reference exact `uv run bench doc stamp`, `uv run bench ppt generate`, and `uv run bench xlsx calculate` commands with flag schemas.
3. **[`enterprise-bench-dev`](.agents/skills/enterprise-bench-dev/SKILL.md):**
   - Document how to register new sub-commands in [`src/cli.py`](src/cli.py) and enforce testing via `uv run pytest -m unit`.

---

## 3. Strict Operating Guardrails for Fresh Agent

- **Zero Intermediate Unit Testing:** Do NOT run full `uv run pytest` between minor edits. Use `uv run python -m py_compile <file>` for static syntax checks, or `uv run pytest -m unit` only when verifying unit functionality.
- **Environment Execution:** Always invoke commands via `uv run <cmd>`.
- **Relative Links:** Use relative paths in documentation and handover files (never absolute machine paths).
