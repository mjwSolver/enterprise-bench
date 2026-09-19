# Sprint 20 Implementation Runbook: Visual Archetypes & Deck Builders

> **Sprint:** 20  
> **Target Subsystems:** `src/ppt_engine/consulting_archetypes.py`, `src/ppt_engine/reference_slides.py`  
> **Operating Guardrail:** [`AGENTS.md`](../../AGENTS.md) (Strict **ZERO INTERMEDIATE UNIT TESTING**).

---

## 1. Objective & Scope

Eliminate repetitive rectangular "box fatigue" across consulting presentations by introducing two foundational executive slide archetypes:
1. **Delivery Gantt Timeline Archetype (`build_timeline_gantt_slide`):** Structured multi-period calendar matrix (Weeks 1–12 or Months 1–6), left stream labels with badges, horizontal duration bars with progress fills, milestone diamond markers, and vertical current sprint hairline indicator.
2. **Harvey Balls Feature Evaluation Matrix (`build_feature_matrix_slide`):** Executive scorecard with Harvey Balls glyphs (`● ◐ ○`) comparing architecture, cloud, or platform options across functional dimensions and highlighting recommended choices.
3. **Deck Builder Integrations:** Expose both archetypes via `ConsultingDeckBuilder` and `ReferenceDeckBuilder`.

---

## 2. Architectural Features

### Delivery Gantt Timeline Archetype
- **Canvas Geometry:** Widescreen 16:9 ($13.333'' \times 7.50''$).
- **Unified Header Frame:** Action title and subtitle rendered in a single unified text box with `space_before = Pt(10)` preventing collisions.
- **Sharp Rectangle Enforced:** Strictly sharp rectangular geometry (`MSO_SHAPE.RECTANGLE`) across calendar bar and task duration shapes, avoiding rounded corner distortions.
- **Milestone Diamonds:** Distinct `MSO_SHAPE.DIAMOND` markers centered along scheduled target weeks.
- **Dynamic Status Styling:** `COMPLETED` (solid primary/accent), `IN_PROGRESS` (accent fill), `PLANNED` (slate-300 fill), and `DELAYED` (crimson red).

### Harvey Balls Feature Scorecard Archetype
- **Multi-Dimensional Comparison:** Category, Criteria, Platform options, and Business Impact badge.
- **Harvey Balls Glyphs:** Centered 16pt bold glyphs with semantic color mapping:
  - Full support: `●` (Emerald Green `#10B981` on recommended platform, Primary Blue on others).
  - Partial support: `◐` (Amber `#F59E0B`).
  - Unsupported: `○` (Muted Slate `#94A3B8`).
- **Recommended Column Highlight:** Automated subtle panel tinting and accent branding on the designated target platform.

---

## 3. Definition of Done Checklist

- [x] `GanttTask`, `GanttWorkstream`, `GanttTimelineData`, and `build_timeline_gantt_slide` implemented in `src/ppt_engine/consulting_archetypes.py`.
- [x] `FeatureScorecardRow`, `FeatureMatrixData`, and `build_feature_matrix_slide` implemented in `src/ppt_engine/consulting_archetypes.py`.
- [x] Methods `add_timeline_gantt_slide` and `add_feature_matrix_slide` added to `ConsultingDeckBuilder`.
- [x] Methods `add_timeline_gantt` and `add_feature_matrix` added to `ReferenceDeckBuilder`.
- [x] Static compilation and syntax validation pass with 0 errors.
