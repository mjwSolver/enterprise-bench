# Task Delegation Briefing: Slide 3 Corporate Equity & Shareholding Tree Archetype

> **Target Role:** PPT Engine Architect / Slide Visual Designer  
> **Repository:** `enterprise-bench`  
> **Target Subsystem:** `src/ppt_engine/consulting_archetypes.py`, `src/ppt_engine/reference_slides.py`  
> **Source Benchmark:** Slide 3 of `clean_workspace/projects/TTI_Snowflake_Analytics/01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx`  
> **Output Artifact Target:** `uv run bench ppt build-deck --config presets/deck_configs/corporate_equity_tree.yaml`  

---

## 1. Executive Summary & Objective

In modern enterprise and presales decks (M&A pitches, corporate governance overviews, vendor capabilities), organizations must visually communicate their corporate structure, subsidiaries, joint ventures, and percentage equity holdings.

The benchmark deck Slide 3 contains an 82-shape corporate structure tree showing **PT Metrodata Electronics Tbk (MTDL)** and its multi-tier holding structure. The objective of this task is to codify this into a first-class programmatic consulting archetype: **`build_equity_corporate_tree_slide(...)`**.

---

## 2. Forensic Analysis of Benchmark Slide 3

### Canvas & Coordinate Geometry
- **Slide Canvas:** 16:9 widescreen ($13.333'' \times 7.50''$).
- **Slide Header:** Action title centered or top-aligned:
  - Title: `METRODATA CORPORATE STRUCTURE` ($y=0.40''$, $w=11.5''$).
  - Subtitle / Tracker: `SUBSIDIARIES & ASSOCIATES` ($y=1.47''$).
- **Top Parent Entity (Holding Level - Row 1):**
  - Node: `PT METRODATA ELECTRONICS TBK (MTDL)`
  - Position: Centered at $x \approx 4.09''$ to $9.00''$, $y \approx 1.00''$ to $1.50''$.
  - Style: Deep navy container with ticker `(MTDL)` and Metrodata emblem badge.
- **Top Bus Connector Line:**
  - Vertical stem down from parent at $x \approx 6.77''$, dropping to horizontal trunk line at $y \approx 2.39''$ spanning $x = 2.88''$ to $9.56''$.

### Tier 1: Direct Operating Subsidiaries & Affiliates (Row 2, $y \approx 2.65''$)
4 primary column blocks with distinct ownership percentage pills anchored at the top of each container:

| Entity Name | Code | Equity % | Functional Business Domain | Color Accent |
| :--- | :--- | :--- | :--- | :--- |
| **PT Mitra Integrasi Informatika** | `MII` | `99.99%` | `ICT SOLUTIONS` | Primary Blue (`#0052CC`) |
| **PT Sinergi Transformasi Digital** | `SINERGI` | `95.00%` | `ICT SOLUTIONS` | Primary Blue (`#0052CC`) |
| **PT Soltius Indonesia** | `SI` | `99.99%` | `ICT CONSULTING` | Cyan / Indigo (`#0284C7`) |
| **PT Synnex Metrodata Indonesia** | `SMI` | `50.00%` | `ICT DISTRIBUTION` | Crimson Red / Amber (`#DC2626`) |

### Tier 2: Indirect Subsidiaries & Joint Ventures (Row 3, $y \approx 5.15''$)
Branch connectors dropping down from Tier 1 nodes into specialized secondary entities:

- **Branch A (Under MII / Direct Associates):**
  - `PT FPT Metrodata Indonesia` (`FMI`) — **60.00%** (`SECURITY SOLUTIONS`)
  - `PT CacaFly Metrodata Indonesia` (`CMI`) — **49.00%** (`DIGITAL MARKETING SOLUTIONS`)
  - `PT Packet Systems Indonesia` (`PSI`) — **20.50%** (`ICT BROADBAND & SOLUTION NETWORK`)
- **Branch B (Under SMI Distribution Stream):**
  - `PT My Icon Technology` (`MIT`) — **99.99%** (`ICT E-COMMERCE`)
  - `PT Synnex Metrodata Technology & Services` (`SMTS`) — **99.60%** (`ICT ASSEMBLY`)

---

## 3. Visual Archetype Architectural Specification

### Geometric & Visual Rules (AGENTS.md Strict Compliance)
1. **Zero Top Overlapping Lines on Rounded Containers:**
   - Both the card body and top ownership pills **must be sharp rectangles (`MSO_SHAPE.RECTANGLE`)**.
   - Do not use `ROUNDED_RECTANGLE` for containers that connect to top bus lines.
2. **Unified Header Frame:**
   - Unified Action Title and Subtitle in a single text frame with `space_before = Pt(10)`.
3. **Card Container Layout:**
   - Fixed width per tier card ($w \approx 1.85''$ to $2.00''$, $h \approx 1.45''$ to $1.60''$).
   - Top Header Stripe / Badge: Ownership % formatted as `[ 99.99% ]` in bold 10pt with soft tinted background.
   - Body Area: Formal entity name in bold 11pt, acronym in 9.5pt.
   - Bottom Pill: Business line pill in 8pt bold uppercase (e.g., `ICT SOLUTIONS`).
4. **Vector Connector Pipelines:**
   - Draw native PowerPoint connector lines (`slide.shapes.add_connector` or orthogonal line segments) connecting parent stem to horizontal trunk lines, and dropping clean orthogonal feeds into each child card.

---

## 4. Proposed Data Model (`src/ppt_engine/consulting_archetypes.py`)

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class EquityEntityNode:
    """Represents a single corporate entity in the equity structure tree."""
    name: str                           # e.g., "PT Mitra Integrasi Informatika"
    code: str                           # e.g., "MII"
    percentage: str                     # e.g., "99.99%"
    business_domain: str                # e.g., "ICT SOLUTIONS"
    tier: int = 1                       # 1 = Direct Subsidiary, 2 = Secondary JV
    parent_code: Optional[str] = None   # Parent entity code (for orthogonal routing)
    accent_color: Optional[str] = None  # Brand accent override

@dataclass
class EquityTreeData:
    """Complete dataset for an equity holding structure."""
    parent_company: str = "PT Metrodata Electronics Tbk"
    parent_ticker: str = "MTDL"
    parent_subtitle: str = "Holding & Listed Investment Company"
    tier1_nodes: List[EquityEntityNode] = field(default_factory=list)
    tier2_nodes: List[EquityEntityNode] = field(default_factory=list)
    footnote: str = "*) Reflects legal equity shareholding percentages as of latest PMO baseline."
```

---

## 5. Required Implementation Steps

1. **Implement Function in `src/ppt_engine/consulting_archetypes.py`:**
   - `build_equity_corporate_tree_slide(prs, theme, tree_data: EquityTreeData, ...)`
   - Add helper `add_equity_corporate_tree_slide(...)` on `ConsultingDeckBuilder`.
2. **Register in `src/ppt_engine/reference_slides.py`:**
   - Support `archetype: corporate_equity_tree` in `ReferenceDeckBuilder`.
3. **Declarative Preset YAML:**
   - Author `presets/deck_configs/corporate_equity_tree.yaml`.
4. **Verification & Audit:**
   - Build deck via `uv run bench ppt build-deck --config presets/deck_configs/corporate_equity_tree.yaml --output output/reference_slides/Corporate_Equity_Tree_Deck.pptx`.
   - Validate zero PII leaks via `uv run bench pii audit --path output/reference_slides/`.
   - Confirm zero pytest executions (per AGENTS.md guardrail).

---

## 6. Verification Target Command
```bash
uv run bench ppt build-deck \
  --config presets/deck_configs/corporate_equity_tree.yaml \
  --output output/reference_slides/Corporate_Equity_Tree_Deck.pptx

uv run bench pii audit --path output/reference_slides/Corporate_Equity_Tree_Deck.pptx
```
