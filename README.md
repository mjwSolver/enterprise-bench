# Enterprise Workbench (`enterprise-bench`)

Universal, multi-engine automation workbench for enterprise consulting deliverables, presentations, specifications, and contractual documents.

---

## 🚀 Quickstart

This project is managed with [`uv`](https://docs.astral.sh/uv/) for fast, deterministic dependency resolution.

### 1. Installation Tiers

Depending on your workflow, install the core base or specific feature groups:

```bash
# Core non-negotiable tools (shared across all engines)
uv sync

# Add Presentation Engine capabilities (python-pptx, matplotlib)
uv sync --extra ppt

# Add Document & Contract Engine capabilities (python-docx, docxtpl)
uv sync --extra docx

# Add Spreadsheet & Calculator capabilities (openpyxl, pandas)
uv sync --extra xlsx

# Install the full enterprise suite (All engines)
uv sync --all-extras
```

---

## 🏛 Architecture

* **[`src/ppt_engine/`](src/ppt_engine/)**: Generative consulting presentation engine (custom visual cards, process flow chevrons, collision detection, and slide export).
* **[`src/docx_engine/`](src/docx_engine/)**: Deterministic compliance and specification engine (`docxtpl` / OpenXML stamping for BAST, PKS, FSD, TSD, MoM).
* **[`src/xlsx_engine/`](src/xlsx_engine/)**: Cloud calculators, S-curve progress tracking, and RAID log generators.
* **[`src/core/`](src/core/)**: Shared Pydantic data models, corporate brand palettes, and PII sanitization.
* **[`clean_workspace/`](clean_workspace/)**: 38 golden master enterprise templates extracted from real-world enterprise delivery.

---

## 🛠 Unified CLI (`bench`)

The repository includes a consolidated Typer CLI entrypoint:

```bash
# Display general help
uv run bench --help

# Provision a new sandboxed project workspace in output/<project_name>
uv run bench init-project AcmeDigital --client "Acme Corp" --vendor "Partner LLC"

# List available corporate brand themes
uv run bench ppt themes

# Generate an executive consulting presentation deck
uv run bench ppt generate --theme brickred --output output/AcmeDigital/presentations/strategic_deck.pptx

# Scrub sensitive client names from a Word template and inject Jinja tokens
uv run bench doc sanitize --input clean_workspace/projects/TTI_Snowflake_Analytics/07_Internal_Legal_Contracts/BAST_Milestone_1_Template.docx --output output/BAST_Sanitized.docx

# Stamp a Word template with JSON data payload
uv run bench doc stamp --template output/BAST_Sanitized.docx --data payload.json --output output/BAST_Final.docx

# Run automated QA inspection on a generated Word document
uv run bench doc lint --file output/BAST_Final.docx
```

---

## 👥 Managing Team & Client Identities

To update staff or client names manually without running CLI commands, see the step-by-step instructions in:
👉 **[docs/specs/manual_identity_guide.md](docs/specs/manual_identity_guide.md)**

---

## 🧪 Running Tests

```bash
uv run pytest
```

For detailed architecture, component boundaries, and sprint tracking, see **[HANDOVER.md](HANDOVER.md)**.
