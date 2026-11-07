"""
Consulting Slide Archetypes Subsystem (Facade)
==============================================
Maintains 100% backward compatibility by re-exporting modular archetypes
from `src.ppt_engine.archetypes`.

Submodules:
- `archetypes.common`: Canvas geometry, headers, cards, footers, typography runs, pill badges.
- `archetypes.covers`: Cover slides, hero covers, chapter dividers, agendas, thank you slides.
- `archetypes.grids`: Card grids, split hero blocks, badge matrices, tech logo grids.
- `archetypes.processes`: Chevron processes, Gantt timelines, runbooks, architecture swimlanes.
- `archetypes.tables`: Data tables, feature scorecard matrices.
- `archetypes.strategy`: BCG 3-horizon, McKinsey cascades, balanced scorecards, gap analyses, equity trees.
- `archetypes.architecture`: Browser mockups, iceberg concepts, OpenTelemetry flows, gate validators, medallion tiers.
- `archetypes.deck_builder`: ConsultingDeckBuilder pipeline facade.
"""

from __future__ import annotations

from src.ppt_engine.archetypes import *
