# Milestone Briefing: Consulting Deck Visual Density, Semantic Redundancy Elimination & Collision Remediation

> **Date:** `2026-11-06` | **Milestone:** `Milestone 42 (Tier 33)` | **Status:** `COMPLETE`  
> **Signature:** `[MJW/AGY]` Architecture & Systems Engineering  
> **Scope:** Enterprise Workbench (`enterprise-bench`)

---

## 1. Executive Summary & Core Deliverables

Milestone 42 operationalizes McKinsey/BCG-grade signal-to-noise hygiene, 3-tier severity color calibration, automated shape collision detection, and bottom-edge canvas grounding across consulting slide archetypes.

1. **Automated Shape Collision Linting (`visual_qa.py`):**
   - Added `SHAPE_COLLISION` linter detecting bounding-box overlap $> 0.12''$ between status badge pills and adjacent text frames.
   - Dynamic text envelope height estimation prevents vertical and horizontal text collisions.
2. **Decoupled Split-Hero & Metric Card Geometry (`consulting_archetypes.py`):**
   - Decoupled title textbox ($w = 5.733''$) from status badge pill ($w = 1.80''$) with an explicit $0.20''$ air gap.
   - Placed the full-width description band ($w = 7.783''$) strictly below the pill baseline ($y = b_y + 0.64''$), eliminating text-over-pill collisions.
   - Dynamic 3-tier severity color calibration: Crimson Red (`#DC2626`) for defect blockers, Amber (`#D97706`) for resource locks/boundaries, Green (`#16A34A`) for target states.
3. **Executive Takeaway Grounding Bar (`build_bcg_3_horizon_slide`):**
   - Added full-width `EXECUTIVE ROADMAP TAKEAWAY` grounding bar at $y = 6.10''$.
   - Automatically clamps card container height to $h = 3.72''$, resolving the $1.3''$ dead space void at column bottoms when cards enforce the 2-bullet ceiling.
4. **Clean Single-Line Footer Attribution (`add_slide_footer`):**
   - Added first-class `source: Optional[str]` support. If provided, renders clean single-line `Source: <text>` on the left footer, preventing multiline text wrapping and slide-floor overflow.
5. **Anti-Redundancy & Signal-to-Noise Invariants Codified in `AGENTS.md`:**
   - **Zero Echo Chambers:** The Action Headline asserts the *Finding*; the Takeaway Bar strictly delivers the *Decision Lever / Capital Equation / So-What*.
   - **Zero Meta-Labeling:** Eliminates structural framework tags (`DIMENSION 01`, `PHASE A`, `(Complication)`); titles and headers state active facts directly.
   - **Zero Card Subtitle Echoes:** Eliminates subtitles that merely preview or summarize the bullet points beneath them.
6. **Native MBB Demonstration Deck Refinement:**
   - De-noised all 4 slides in `specs/decks/demo_mbb_transformation.yaml`, verified cleanly via headless linters and python-pptx visual QA.

---

## 2. Settled Decisions & Invariants

- **No Text Under Shapes:** In PowerPoint DrawingML, text does not wrap around overlapping vector shapes. Any badge or pill must sit in a decoupled horizontal track or separate vertical block.
- **Headline vs Takeaway Separation:** If no distinct forward-looking decision or capital equation exists, omit the takeaway bar entirely rather than repeating the headline.
- **Max 2 Punchy Bullets:** Limit cards to 2 punchy bullets maximum with bold lead phrases and $\ge 10.5\text{ pt}$ typography with generous vertical breathing room.
- **Pristine Color Hygiene:** Clean ice-blue (`#F0F9FF`/`#E0F2FE`) and crisp white surfaces; strictly eliminate muddy green/yellowish tinges (`#F0FDF4`).

---

## 3. Working Tree Delta

- **Created:**
  - `docs/handovers/2026-11-06_consulting_deck_visual_density_and_echo_elimination.md`
- **Updated:**
  - `src/ppt_engine/consulting_archetypes.py` (severity pills, decoupled text frames, takeaway grounding bar, footer source)
  - `src/ppt_engine/visual_qa.py` (`SHAPE_COLLISION` linter rule)
  - `src/ppt_engine/pitch_deck.py` (takeaway, source, badge_variant parameter plumbing)
  - `specs/decks/demo_mbb_transformation.yaml` (pruned redundancies, verified deck spec)
  - `AGENTS.md` (enshrined anti-echo, anti-meta-labeling, anti-subtitle-echo invariants)
  - `HANDOVER.md` (recorded Tier 33 / Milestone 42, rotated legacy briefing)
