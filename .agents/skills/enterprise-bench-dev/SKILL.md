---
name: enterprise-bench-dev
description: >-
  Developer guide and engineering runbook for maintaining, refactoring, and extending the Enterprise Workbench engines (`src/docx_engine`, `src/ppt_engine`, `src/xlsx_engine`, `src/core`, `cli.py`). Use when tasked with adding new templates, updating schemas, modifying OpenXML table logic, creating consulting archetypes, or adjusting CLI commands.
---

# Enterprise Workbench: Engine Developer Guide (`enterprise-bench-dev`)

> **Target Agent Role:** Core Platform Engineer / Engine Developer / Python Maintainer  
> **Mission:** Refactor, maintain, extend, and verify the multi-engine document, presentation, and spreadsheet infrastructure (`src/`) while adhering strictly to repository architecture guardrails.

---

## 1. Multi-Engine Architecture & Separation of Concerns

```
                               ┌────────────────────────────────────────────────────────┐
                               │                 Unified CLI (`bench`)                  │
                               │                      `src/cli.py`                      │
                               │  init-project | test --unit | ppt | doc | xlsx         │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
               ┌───────────────────────────────────────────┼───────────────────────────────────────────┐
               ▼                                           ▼                                           ▼
     ┌───────────────────┐                       ┌───────────────────┐                       ┌───────────────────┐
     │  `src/ppt_engine` │                       │ `src/docx_engine` │                       │ `src/xlsx_engine` │
     │ Generative Slides │                       │ Deterministic Doc │                       │ Models & S-Curves │
     │  (Consulting &    │                       │ (BAST, PKS, FSD,  │                       │ (Calculators,     │
     │ Visual Cards)     │                       │ TSD, MoM)         │                       │ RAID, Mandays)    │
     └─────────┬─────────┘                       └─────────┬─────────┘                       └─────────┬─────────┘
               │                                           │                                           │
               └───────────────────────────────────┬───────┴───────────────────────────────────────────┘
                                                   ▼
                                   ┌────────────────────────────────┐
                                   │          `src/core/`           │
                                   │ Models, Themes, Path Config &  │
                                   │     Regex PII Sanitizer        │
                                   └────────────────────────────────┘
```

### A. The Deterministic Compliance Engine (`src/docx_engine/`)
* **Philosophy**: Zero-drift. Stamped output must preserve exact enterprise legal/audit styling across iterations.
* **Core Modules**:
  - `template_stamper.py`: Powered by `docxtpl` (Jinja2). Renders context data into template documents with automated linting.
  - `table_engine.py`: Direct OpenXML XML manipulation for Microsoft Word tables:
    - Row shading (neutral slate `#F1F5F9` headers).
    - Prevents awkward page breaks across rows: `<w:cantSplit/>`.
    - Header repetition across pagination: `<w:tblHeader/>`.
  - `document_linter.py`: Pre-flight regex scanner detecting unrendered tags (e.g., `{{ ... }}` or `{% ... %}`) and dangling headers.

### B. The Generative Presentation Engine (`src/ppt_engine/`)
* **Philosophy**: Visual storytelling, layout flexibility, and collision prevention.
* **Core Modules**:
  - `consulting_archetypes.py`: Programmatic slide structures (BCG 3-Horizon, Balanced Scorecard, Metric Grids, Process Flows, De-Squared Chapter Dividers).
  - `diagram_engine.py`: Vector diagram drawing (cloud topologies, sequenced pipelines).
  - `theme_engine.py`: Corporate color palettes and font tokens loaded from `presets/themes/*.yaml`.
  - `resource_manager.py`: Asset resolution, silent pre-flight acquisition, graceful fallback handling, and automated `missing_resources.md` diagnostic ledger generation.
* **Geometry Integrity Rule (Zero Overlapping Top Lines on Rounded Containers)**:
  - Cards with top accent stripes/lines or header bars **MUST NEVER** have rounded corners at the top.
  - When an archetype features a top accent stripe, both container card and stripe **MUST be sharp rectangles (`MSO_SHAPE.RECTANGLE`)**.
  - Thin stripes must **never** use `MSO_SHAPE.ROUNDED_RECTANGLE` (which distorts into pills/capsules).
  - Enforced via `add_card_with_top_stripe(...)` or `add_card(..., has_top_stripe=True)`.
* **Chapter Divider De-Squaring & Translucent Scrim (`build_chapter_divider_slide`)**:
  - Implements asymmetric 1/3 narrative panel + 2/3 photographic plate with 45% dark scrim overlay (`#0B132B` via `<a:alpha val="45000"/>`).
  - Enforces sharp rectangular containers (`MSO_SHAPE.RECTANGLE`) across hero plate and scrim overlay.
  - Automatic graceful degradation via `ResourceManager.resolve_asset(...)` to deep primary solid containers (`#0F172A`) and typographic badges (`[ METRODATA ]`).

### C. The Spreadsheet & Financial Engine (`src/xlsx_engine/`)
* **Philosophy**: Formula-preserving automated calculation and data injection.
* **Core Modules**:
  - `calculator_stamper.py`: Powered by `openpyxl`. Injects coordinates (`Sheet!A1`), key-value replacements, and table rows into templates without corrupting existing formulas or cell formats. Exposes `CalculatorStamper` and `calculate_spreadsheet`.
  - `s_curve_generator.py`: Generates earned-value cumulative progress curves (`pandas` + `matplotlib`).

### D. Shared Core Foundation (`src/core/`)
* `config.py`: Root-relative path resolution (`validate_clean_path()`, `get_template_path()`, `OUTPUT_DIR`). Enforces security boundary prohibiting direct reads from `raw_source_files/`.
* `models.py`: Strongly typed Pydantic v2 schemas (`ProjectInfo`, `BASTPayload`, `MoMPayload`, `Stakeholder`).
* `theme.py`: `BrandTheme` dataclass and hex/RGB color transformers.
* `sanitizer.py`: High-entropy regex cleaner for masking corporate identities, PII, and credentials across DOCX and XLSX.
* `docx_purger.py`: Zero-corruption OpenXML comment, highlight, tracked revision, and author profile purger. Preserves `[Content_Types].xml` and `.rels` while clearing part contents. See full runbook: [`docs/specs/openxml_purging_and_cleansing.md`](../../docs/specs/openxml_purging_and_cleansing.md).

---

## 2. 🚨 Critical Engineering Guardrail: Zero Intermediate Unit Testing

> **MANDATORY INSTRUCTION: ENFORCED VIA `AGENTS.md`**

1. **Do NOT run full unit test suites (`pytest`, `uv run pytest`)** during active development, refactoring, code drafting, or sprint cycles.
2. **Why?** In multi-agent parallel environments, running full test suites between tasks causes severe resource thrashing and duplicate execution cycles.
3. **The ONLY exceptions**:
   - The user explicitly requests running tests.
   - Pre-push verification immediately prior to a confirmed remote origin push.
4. **Fast QA Verification Gate (<1s execution)**:
   When verification is needed, use the fast in-memory unit suite via the unified CLI:
   ```bash
   uv run bench test --unit
   ```
   *(Direct pytest equivalent: `uv run pytest -m unit`)*
5. **Static Syntax Checking**:
   ```bash
   uv run python -m py_compile src/<module>/<file>.py
   ```

---

## 3. Extending the Unified CLI (`src/cli.py`)

All platform capabilities must be exposed through `uv run bench ...`. Follow this pattern to register new commands:

### A. Registering a Sub-App Router
```python
# 1. Instantiate the sub-app router
sub_app = typer.Typer(name="service", help="Service Automation Engine", no_args_is_help=True)

# 2. Register with root app
app.add_typer(sub_app, name="service")
```

### B. Defining a CLI Sub-Command
```python
@sub_app.command("action")
def perform_action(
    template: str = typer.Option(..., "--template", "-t", help="Path or name of template"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="Path to JSON payload"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Destination path"),
) -> None:
    """Execute operational engine action."""
    # 1. Parse JSON if provided
    payload = {}
    if data:
        data_p = Path(data)
        if not data_p.exists():
            rprint(f"[red]Error:[/red] Data file not found: {data}")
            raise typer.Exit(code=1)
        with open(data_p, "r", encoding="utf-8") as f:
            payload = json.load(f)

    # 2. Delegate to engine function
    try:
        result = run_engine_service(template=template, payload=payload, output=output)
        rprint(f"[green]✓ Output successfully generated:[/green] [bold]{result}[/bold]")
    except Exception as e:
        rprint(f"[red]Error during execution:[/red] {e}")
        raise typer.Exit(code=1)
```

### C. Verifying CLI Registrations
After editing `src/cli.py`:
1. Compile: `uv run python -m py_compile src/cli.py`
2. Inspect help output: `uv run bench <service> --help`
3. Fast unit test: `uv run bench test --unit`

---

## 4. Coding Standards & Integrity

- **Execution Environment**: Always execute Python commands through `uv run ...`.
- **Typing**: Use strict Python 3.10+ type hints (`dict[str, Any]`, `list[str]`, `str | None`).
- **Pathing**: Always use `pathlib.Path` resolved relative to `src.core.config.ROOT_DIR` or `clean_workspace/`. Never use hardcoded absolute machine paths.
- **Relative Links**: In documentation, always use relative markdown links (e.g., `[LIFECYCLE.md](LIFECYCLE.md)`).
- **Workspace File Writes**: When authoring or staging new workspace files, use [`scripts/write_file.py`](../../scripts/write_file.py) to avoid shell escaping pitfalls.
