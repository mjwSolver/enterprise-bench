"""
PPTMaking Core Source Package
"""
from .diagram_engine import (
    DiagramEngine,
    DrawIOProject,
    mxgraph_to_ast,
    compile_mermaid,
    THEME_PRESETS,
)
from .theme_engine import (
    Theme,
    ThemeEngine,
    hex_to_rgb,
    rgb_to_hex,
    load_theme,
    get_theme,
    list_available_themes,
)
from .consulting_archetypes import (
    ConsultingDeckBuilder,
    HorizonColumnData,
    StrategyPillarData,
    ScorecardMetric,
    ScorecardQuadrantData,
    create_presentation,
    add_slide_with_background,
    add_slide_header,
    add_card,
    add_card_with_top_stripe,
    add_slide_footer,
    build_bcg_3_horizon_slide,
    build_mckinsey_cascade_slide,
    build_balanced_scorecard_slide,
)

__all__ = [
    "DiagramEngine",
    "DrawIOProject",
    "mxgraph_to_ast",
    "compile_mermaid",
    "THEME_PRESETS",
    "Theme",
    "ThemeEngine",
    "hex_to_rgb",
    "rgb_to_hex",
    "load_theme",
    "get_theme",
    "list_available_themes",
    "ConsultingDeckBuilder",
    "HorizonColumnData",
    "StrategyPillarData",
    "ScorecardMetric",
    "ScorecardQuadrantData",
    "create_presentation",
    "add_slide_with_background",
    "add_slide_header",
    "add_card",
    "add_card_with_top_stripe",
    "add_slide_footer",
    "build_bcg_3_horizon_slide",
    "build_mckinsey_cascade_slide",
    "build_balanced_scorecard_slide",
]
