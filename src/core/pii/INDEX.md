# Universal PII Extraction & Sanitization Engine: Operational Index & Developer Specification

> **Target Package:** `src.core.pii`  
> **Audience:** Future AI Agents, CLI Builders, Security Engineers, and Enterprise Deliverable Authors.  
> **Supported Formats:** Microsoft Word (`.docx`), PowerPoint (`.pptx`), Excel (`.xlsx`, `.xlsm`), and extensible to arbitrary future formats via `BaseFormatHandler`.

---

## 1. Executive System Overview

The PII Engine is a decoupled, multi-stage framework designed to discover, map, and scrub personally identifiable information (PII) and corporate secrets from binary OOXML containers and structured documents.

### Key Architectural Tenets
1. **Spatial Coordinate Awareness:** Every extracted text node records its physical location hierarchy (e.g., `Slide 2 > Shape 4`, `Sheet: Stakeholders > Cell C5`, `Section 1 > Header > Para 2`).
2. **Dual Vector Protection (Body & Metadata):** In addition to visible body text and table cells, the engine inspects and scrubs OOXML container properties (`docProps/core.xml`: `author`, `last_modified_by`, `creator`, `comments`).
3. **Format Agnostic via Registry:** Core format parsers implement `BaseFormatHandler`. Adding support for a new format (e.g. PDF, CSV, Markdown, RTF) requires only implementing 4 standard methods and decorating with `@register_handler`.
4. **Separation of Inspection vs. Mutation:** Detection does not blindly alter files; it produces a strongly typed Pydantic `ScanReport`, which can be converted into an editable `ReplacementMapping` before applying transformations.

---

## 2. The 3-Stage Operating Workflow

```text
┌────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│  STAGE 1: SCAN │ ----> │ STAGE 2: REVIEW & MAP│ ----> │  STAGE 3: SANITIZE   │
│  `scan_file()` │       │ `generate_mapping()` │       │  `sanitize_file()`   │
└────────────────┘       └──────────────────────┘       └──────────────────────┘
        │                           │                               │
        ▼                           ▼                               ▼
  `ScanReport`                `mapping.json`               Clean Binary Document
 (Locations, Types,       (Jinja or Redact Tokens,         + Audit Manifest
    Raw Values)             Human/Agent Overrides)       (`sanitization_manifest.json`)
```

### Stage 1: Scan & Audit
Inspects a file or directory tree and extracts all text nodes. The `DetectorPipeline` applies:
- High-confidence regex matchers: Emails, Phone numbers (Indonesian + international), Indonesian NIK/Tax IDs, IPv4 addresses, and enterprise contract numbers.
- Entity dictionary matchers: Enterprise client and vendor entity patterns.
- Metadata analyzer: Extracts author, creator, last modifier.

### Stage 2: Review & Mapping
Converts detected PII into an actionable mapping schema (`ReplacementMapping`):
- **Jinja Strategy (`strategy="jinja"`):** Replaces sensitive entities with reusable template tokens (e.g. `{{ client_company }}`, `{{ contact_email_1 }}`). This transforms real-world client files directly into safe, parameterized templates.
- **Redaction Strategy (`strategy="redact"`):** Replaces sensitive entities with audit tags (e.g. `[REDACTED: EMAIL]`, `[REDACTED: PHONE]`).
- **Human / Agent in the Loop:** The mapping can be saved as `mapping.json`, inspected, reviewed, or modified before applying.

### Stage 3: Sanitize & Export
Applies the verified mapping:
- Modifies paragraphs, runs, shapes, tables, notes, and cells while strictly preserving font styles, layouts, and cell formulas.
- Overwrites container metadata (`docProps/core.xml`) with neutral credits (`Enterprise Contributor`).
- Emits a cryptographic audit manifest (`sanitization_manifest.json`) recording every alteration.

---

## 3. CLI Command Blueprint for Downstream CLI Agent

This section defines the exact command specification to be implemented in `cli.py` or a dedicated `pii_cli.py` module using `typer`:

### A. Command: `bench pii scan`
Scans a file or directory and displays or exports detected PII.

```bash
# Terminal Invocation Examples:
bench pii scan --target templates/02_Initiating/1.3_Stakeholders_Register_Template.xlsx
bench pii scan --target templates/ --recursive --output-report pii_report.json
bench pii scan --target output/AcmeDigital/ --summary-only
```

- **Arguments & Options:**
  - `--target / -t` (Required, `str`): Path to input file or directory.
  - `--output-report / -o` (Optional, `str`): Path to save the JSON `ScanReport`.
  - `--recursive / -r` (Optional, `bool`, default `True`): Traverse directories recursively.
  - `--summary-only / -s` (Optional, `bool`, default `False`): Output category count table without per-match details.
- **Output:** Render a Rich table displaying Match Index, Category, Raw Value, Location, and Confidence.

### B. Command: `bench pii map`
Generates an editable `mapping.json` from a scan report or directly from a target file.

```bash
# Terminal Invocation Examples:
bench pii map --report pii_report.json --strategy jinja --output mapping.json
bench pii map --target templates/02_Initiating/ --strategy redact --output redactions.json
```

- **Arguments & Options:**
  - `--report / -r` (Optional, `str`): Path to existing `ScanReport` JSON.
  - `--target / -t` (Optional, `str`): Path to target file or directory (scans automatically if `--report` is omitted).
  - `--strategy / -s` (Optional, `str`, choice: `jinja` | `redact`, default `jinja`).
  - `--output / -o` (Required, `str`): Path to output `mapping.json`.

### C. Command: `bench pii sanitize`
Applies sanitization to a file or directory tree.

```bash
# Terminal Invocation Examples:
bench pii sanitize --input templates/02_Initiating/1.3_Stakeholders_Register_Template.xlsx --output output/clean_stakeholders.xlsx
bench pii sanitize --input templates/ --output sanitized_templates/ --mapping mapping.json
bench pii sanitize --input deck.pptx --output deck_clean.pptx --strip-metadata
```

- **Arguments & Options:**
  - `--input / -i` (Required, `str`): Path to input file or directory.
  - `--output / -o` (Required, `str`): Destination file or output directory.
  - `--mapping / -m` (Optional, `str`): Path to custom `mapping.json` (auto-generates Jinja mapping if omitted).
  - `--strip-metadata / --no-strip-metadata` (Optional, `bool`, default `True`): Cleans OOXML properties.
- **Output:** Outputs confirmation and path to generated clean documents and `sanitization_manifest.json`.

### D. Command: `bench pii metadata`
Directly inspects the embedded core properties of any Word, PowerPoint, or Excel document.

```bash
bench pii metadata --file templates/02_Initiating/1.2_Project_Charter_Template.docx
```

---

## 4. Python API Reference & Quickstart Snippets

### Quickstart 1: One-Liner File Scan & Sanitize
```python
from src.core.pii import scan_file, generate_mapping, sanitize_file

# 1. Scan
report = scan_file("templates/02_Initiating/1.3_Stakeholders_Register_Template.xlsx")
print(f"Total PII items found: {report.total_matches}")

# 2. Map (Jinja mode)
mapping = generate_mapping(report, strategy="jinja")

# 3. Sanitize
result = sanitize_file(
    input_path="templates/02_Initiating/1.3_Stakeholders_Register_Template.xlsx",
    output_path="output/Sanitized_Stakeholders.xlsx",
    mapping=mapping,
)
print(f"Sanitized document saved: {result.output_path} ({result.replacements_applied} replacements)")
```

### Quickstart 2: Batch Directory Sanitization with Manifest
```python
from src.core.pii import sanitize_directory

manifest = sanitize_directory(
    source_dir="templates/02_Initiating",
    output_dir="output/sanitized_initiating",
    recursive=True,
)
print(f"Batch processed {manifest.files_processed} files with {manifest.total_replacements} replacements.")
```

### Quickstart 3: Saving & Loading Custom Mappings
```python
from src.core.pii import scan_file, generate_mapping, save_mapping_json, load_mapping_json

# Generate and save
report = scan_file("document.docx")
mapping = generate_mapping(report, strategy="jinja")
save_mapping_json(mapping, "custom_mapping.json")

# Edit custom_mapping.json manually or via an agent, then reload:
custom_map = load_mapping_json("custom_mapping.json")
```

---

## 5. How to Add Handlers for Future Formats

Adding a new document format handler requires zero modifications to existing code. Follow this pattern:

```python
from pathlib import Path
from typing import Dict, List, Set
from src.core.pii.handlers.base import BaseFormatHandler
from src.core.pii.models import SanitizeResult, TextNode
from src.core.pii.registry import register_handler

@register_handler
class MarkdownHandler(BaseFormatHandler):
    @classmethod
    def supported_extensions(cls) -> Set[str]:
        return {".md", ".markdown"}

    def extract_text_nodes(self, path: Path) -> List[TextNode]:
        nodes = []
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    nodes.append(TextNode(
                        location=f"Line {idx + 1}",
                        text=line.strip(),
                        node_type="line",
                    ))
        return nodes

    def extract_metadata(self, path: Path) -> Dict[str, str]:
        return {}

    def apply_replacements(
        self,
        input_path: Path,
        output_path: Path,
        replacements: Dict[str, str],
        strip_metadata: bool = True,
        metadata_overrides: Dict[str, str] | None = None,
    ) -> SanitizeResult:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        count = 0
        for target, repl in replacements.items():
            if target in content:
                content = content.replace(target, repl)
                count += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return SanitizeResult(
            source_path=str(input_path),
            output_path=str(output_path),
            replacements_applied=count,
            metadata_scrubbed=strip_metadata,
        )
```
Any format registered via `@register_handler` is instantly recognized across `scan_file`, `scan_directory`, `sanitize_file`, and `sanitize_directory`.
