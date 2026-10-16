# In-Flight Verification Gate & Connector Corridor Geometry Standards

> **Subsystem:** Diagram Engine V2, Presentation Compilers & Delivery Gateways  
> **Status:** Enduring Architectural Specification & Standards Runbook  
> **Index Reference:** [`docs/INDEX.md`](../INDEX.md) | **Handover Ledger:** [`HANDOVER.md`](../../HANDOVER.md)

---

## 1. Executive Summary & Problem Statement

During high-velocity deliverable generation, two opposing failure modes frequently emerge:
1. **The Unit Test Tax:** Running extensive test runners (`pytest`) during active drafting introduces duplicate execution overhead, thrashing system resources and stalling generation velocity.
2. **The Static Blindspot:** Static linters and syntax checks (`python3 -m py_compile`) cannot detect runtime keyword mismatches, broken coordinate lookups, or physical geometry collisions caused by wrapped text and dynamic pill sizing.

This specification permanently establishes four architectural standards to ensure zero-defect presentation generation without intermediate unit testing overhead:
1. **The Minimum Connector Corridor Span Invariant:** Strict geometric clearance rules for labeled connector elbows and pills.
2. **Postel's Law Constructor Aliasing:** Ergonomic alias absorption across presentation dataclasses and AST models.
3. **Deep PKZip Structural Preflight Gates:** Bit-level central directory integrity validation for OpenXML deliverables.
4. **The Subagent-Delegated In-Flight Smoke Pass:** Standardized prompt contracts delegating multi-format verification to background subagents, preserving primary agent cognitive bandwidth.

---

## 2. Standard 1: Minimum Connector Corridor Span Invariant

### 2.1 The Geometric Collision Hazard
When a connector between two columns or nodes is routed orthogonally, a horizontal or vertical elbow segment carrying a text label pill must accommodate the rendered physical width of that pill:
$$\text{Pill Width } W_{\text{pill}} \approx (\text{len}(\text{label}) \times \text{pt} \times 0.55) + 16\text{px}$$

If an elbow jog turns too close to a source or destination card, centering the label pill on the segment causes its outer border to intrude into the card boundary, triggering a `FLOW_LABEL_NODE_COLLISION` warning.

### 2.2 The Minimum Span Formula
Any connector segment designated to hold a centered label pill must satisfy:
$$L_{\text{segment}} \ge W_{\text{pill}} + 2 \times \text{Clearance Halo}$$
where $\text{Clearance Halo} \ge 14.0\text{pt} \approx 18.7\text{px}$ ($0.195''$ at isotropic 96 DPI).

```
 ┌──────────────┐                                       ┌──────────────┐
 │  Node Card   │                                       │ Target Card  │
 └──────┬───────┘                                       └──────▲───────┘
        │                                                      │
        │       ┌─────────────────┐                            │
        └───────┤  2. Event Pill  ├─────────┐                  │
                └─────────────────┘         │                  │
         <────── L_segment >= W_pill + 2*Halo ──────>          │
                                            └──────────────────┘
```

### 2.3 Compiler Auto-Correction Heuristic
When compiling declarative topologies in `src/ppt_engine/diagram_v2/geometry.py`:
- If an author-specified segment length is $< W_{\text{pill}} + 2 \times \text{Halo}$, the compiler must automatically clamp the elbow outward into the inter-column corridor:
  $$x_{\text{elbow}} = x_{\text{node\_edge}} + \frac{W_{\text{pill}}}{2} + \text{Halo}$$
- Alternatively, if corridor width is restricted, the compiler must automatically migrate the label pill to the longest adjacent downstream segment or place it with `label_position: "side"`.

---

## 3. Standard 2: Postel’s Law Constructor Aliasing

### 3.1 The Robustness Principle in Presentation Systems
Presentation slide builders, CLI commands, and YAML deserializers frequently evolve independently. Strict dataclass signatures without keyword aliasing create brittle failure points (e.g. `ScorecardQuadrantData` throwing `TypeError: unexpected keyword argument 'title'` when callers pass `title` instead of `quadrant_title`).

### 3.2 Dataclass Alias Absorption Pattern
All presentation dataclasses in `src/ppt_engine/consulting_archetypes.py` must implement alias tolerance in `__post_init__`:
```python
@dataclass
class ScorecardQuadrantData:
    quadrant_title: str = ""
    tagline: str = ""
    metrics: List[ScorecardMetric] = field(default_factory=list)
    accent_key: str = "accent"
    icon: Optional[str] = None
    icon_path: Optional[Union[str, Path]] = None
    title: Optional[str] = None  # Backward-compatible alias

    def __post_init__(self) -> None:
        if self.title and not self.quadrant_title:
            self.quadrant_title = self.title
        elif not self.title and self.quadrant_title:
            self.title = self.quadrant_title
```

### 3.3 Diagnostic Role Normalization
Status indicators and badge labels must never rely on brittle exact string equality. Use token containment to map statuses into standard diagnostic palettes:
- **Success / Optimal:** `ON TRACK`, `EXCEEDED`, `PASSED`, `COMPLETE`, `OPTIMAL` $\implies$ `#16A34A` / `#DCFCE7`
- **Warning / Boundary:** `MONITORED`, `AMBER`, `WARNING`, `RESCHEDULE`, `MEDIUM` $\implies$ `#D97706` / `#FEF3C7`
- **Critical / Bottleneck:** `AT RISK`, `BLOCKED`, `DELAYED`, `FAILED`, `CRITICAL` $\implies$ `#DC2626` / `#FEE2E2`
- **Active Ingress:** `IN PROGRESS`, `REVIEW`, `PENDING`, `PLANNED`, `OPEN` $\implies$ `#0284C7` / `#E0F2FE`

---

## 4. Standard 3: Deep PKZip Structural Preflight Gates

### 4.1 The OpenXML Corruption Blindspot
Office deliverables (`.pptx`, `.docx`, `.xlsx`) are zip archives containing OpenXML parts. Process interruptions or partial writes can generate 10KB–50KB files that pass basic `st_size > 0` checks but crash PowerPoint with XML/zip repair dialogs.

### 4.2 Structural Validation Gate
All delivery stage gates in `src/core/delivery/staging.py` (specifically Gate 4: `ZERO_BYTE_CORRUPTION_GUARD`) must verify zip directory integrity:
```python
import zipfile
from pathlib import Path

def verify_openxml_archive(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    if path.suffix.lower() in (".pptx", ".docx", ".xlsx", ".zip"):
        if not zipfile.is_zipfile(path):
            return False
        try:
            with zipfile.ZipFile(path, "r") as zf:
                if zf.testzip() is not None:
                    return False
        except (zipfile.BadZipFile, OSError):
            return False
    return True
```

---

## 5. Standard 4: Subagent-Delegated In-Flight Smoke Pass

### 5.1 Cognitive Separation Contract
Primary drafting agents must not be burdened with executing multi-format compilers, diffing AST reconcilers, and parsing extensive CLI terminal tables. Verification is delegated to a specialized subagent running in the background.

### 5.2 Canonical Subagent Invocation Prompt
Primary agents invoke the verification subagent using `invoke_subagent`:

```python
invoke_subagent(
    Subagents=[{
        "Role": "In-Flight Verification Scout",
        "TypeName": "self",
        "Model": "inherit",
        "Workspace": "inherit",
        "Prompt": """
You are the In-Flight Verification Scout for enterprise-bench.
Your mission is to execute the 4-Gate In-Flight Verification Smoke Pass on:
Target Spec: specs/diagrams/{spec_name}.yaml
Target Deck: output/{deck_name}.pptx

🚨 MANDATORY GUARDRAIL: ZERO INTERMEDIATE UNIT TESTING
Do NOT run pytest or test suites. Execute strictly through CLI gates.

Execution Steps:
1. Multi-Format Parity:
   uv run bench diagram v2 compile specs/diagrams/{spec_name}.yaml --format all
2. Strict Tier 1 Geometric Audit:
   uv run bench diagram v2 audit specs/diagrams/{spec_name}.yaml --strict
3. Bidirectional PPTX Reconciler:
   uv run bench diagram v2 reconcile output/diagrams_v2/{spec_name}.pptx --dry-run
4. PKZip Stage-Gate Check:
   uv run bench stage preflight output/diagrams_v2/ --strict

In-Flight Failure Protocol:
If any gate trips (e.g. FLOW_LABEL_NODE_COLLISION, constructor mismatch, corrupted zip):
- Halt immediately.
- Apply the surgical in-place fix (adjusting corridor spans, resolving alias fields, or repairing coordinates).
- Re-run the failing gate until 100% clean exit code 0.
Report back strictly with the final verification ledger and diff summary.
"""
    }]
)
```

---

## 6. Verification & Compliance Checklist

When closing a deliverable or updating engines, ensure:
- [x] All connector elbow segments satisfy $L_{\text{segment}} \ge W_{\text{pill}} + 2 \times \text{Halo}$.
- [x] All presentation dataclasses provide synonym absorption in `__post_init__`.
- [x] Gate 4 in `bench stage preflight` executes `zipfile.testzip()` validation.
- [x] In-flight flight tests run cleanly across all 4 target formats (`.drawio`, `.svg`, `.png`, `.pptx`).
