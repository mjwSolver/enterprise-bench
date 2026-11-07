"""
Archetypes Subsystem Package
============================
Modular consulting slide archetypes decomposed by functional family:
- common: Base canvas geometry, headers, cards, footers, typography runs, pill badges.
- covers: Cover slides, hero covers, chapter dividers, agendas, thank you slides.
- grids: Card grids, split hero blocks, badge matrices, tech logo grids.
- processes: Chevron processes, Gantt timelines, runbooks, architecture swimlanes.
- tables: Data tables, feature scorecard matrices.
- strategy: BCG 3-horizon, McKinsey cascades, balanced scorecards, gap analyses, corporate equity trees.
- architecture: Browser mockups, iceberg concepts, OpenTelemetry flows, gate validators, medallion tiers.
- deck_builder: High-level ConsultingDeckBuilder facade.
"""

from .common import *
from .covers import *
from .grids import *
from .processes import *
from .tables import *
from .strategy import *
from .architecture import *
from .deck_builder import *
