from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.util import Inches, Pt

from src.ppt_engine.icon_engine import (
    get_brand_icon,
    normalize_color,
    recolor_svg,
    render_svg_to_png,
    resolve_brand_color,
)
from src.ppt_engine.text_formatting import append_formatted_runs, set_formatted_text
from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb, rgb_to_hex, strip_shape_shadows

from .common import *
from .covers import *
from .grids import *
from .processes import *
from .tables import *
from .strategy import *
from .architecture import *

logger = logging.getLogger(__name__)

class ConsultingDeckBuilder:
    """High-level builder for assembling full multi-slide consulting decks."""

    def __init__(self, theme: Union[str, Theme] = "default") -> None:
        if isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = theme
        self.prs = create_presentation(self.theme)

    def add_cover_slide(
        self,
        title: str = "Enterprise Modernization Blueprint",
        subtitle: Optional[str] = "Strategic cloud transformation, data lakehouse architecture, and operational runbook.",
        client: str = "Enterprise Client",
        vendor: str = "Metrodata Consulting",
        product: Optional[str] = "Snowflake AI Data Cloud",
        date_str: Optional[str] = None,
        tracker: str = "STRATEGIC ENGAGEMENT DELIVERABLE",
        client_logo_path: Optional[Union[str, Path]] = None,
        vendor_logo_path: Optional[Union[str, Path]] = None,
        product_logo_path: Optional[Union[str, Path]] = None,
        client_sublabel: str = "Steering Committee & Executive Sponsors",
        vendor_sublabel: str = "Data & AI Modernization Practice",
    ) -> Any:
        return build_cover_slide(
            prs=self.prs,
            theme=self.theme,
            title=title,
            subtitle=subtitle,
            client=client,
            vendor=vendor,
            product=product,
            date_str=date_str,
            tracker=tracker,
            client_logo_path=client_logo_path,
            vendor_logo_path=vendor_logo_path,
            product_logo_path=product_logo_path,
            client_sublabel=client_sublabel,
            vendor_sublabel=vendor_sublabel,
        )

    def add_hero_cover_slide(
        self,
        title: str = "Enterprise Modernization Blueprint",
        subtitle: Optional[str] = "Strategic cloud transformation, data lakehouse architecture, and operational runbook.",
        client: str = "[CLIENT_COMPANY_NAME]",
        vendor: str = "PT Metrodata Electronics Tbk",
        product: Optional[str] = "Snowflake AI Data Cloud",
        date_str: Optional[str] = "September 2026",
        tracker: str = "ENTERPRISE TRANSFORMATION BLUEPRINT  |  PROJECT ENGAGEMENT",
        hero_image_path: Optional[Union[str, Path]] = None,
        hero_height: float = 3.65,
        scrim_alpha: float = 0.28,
        client_logo_path: Optional[Union[str, Path]] = None,
        vendor_logo_path: Optional[Union[str, Path]] = None,
        product_logo_path: Optional[Union[str, Path]] = None,
        client_sublabel: str = "Steering Committee & Executive Sponsors",
        vendor_sublabel: str = "Data & AI Modernization Practice",
    ) -> Any:
        return build_hero_cover_slide(
            prs=self.prs,
            theme=self.theme,
            title=title,
            subtitle=subtitle,
            client=client,
            vendor=vendor,
            product=product,
            date_str=date_str,
            tracker=tracker,
            hero_image_path=hero_image_path,
            hero_height=hero_height,
            scrim_alpha=scrim_alpha,
            client_logo_path=client_logo_path,
            vendor_logo_path=vendor_logo_path,
            product_logo_path=product_logo_path,
            client_sublabel=client_sublabel,
            vendor_sublabel=vendor_sublabel,
        )

    def add_bcg_3_horizon_slide(
        self,
        tracker: str = "Growth Strategy & Modernization  |  BCG 3-Horizon Framework",
        action_title: str = "Balanced Portfolio Allocation Fuels Core Modernization while Incubating Future Engines",
        subtitle: Optional[str] = "Phased sequencing balances near-term cash generation with disruptive 3-5 year platform bets.",
        horizons: Optional[List[HorizonColumnData]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_bcg_3_horizon_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            horizons=horizons,
            current_idx=idx,
            total_slides=idx,
        )

    def add_mckinsey_cascade_slide(
        self,
        tracker: str = "Corporate Transformation & Strategy Cascade  |  McKinsey MECE Model",
        action_title: str = "Structured Hypothesis Cascade Unlocks $42M in Sustainable Operational Alpha",
        subtitle: Optional[str] = "Three mutually exclusive strategic pillars resolve core platform constraints and optimize cost-to-serve.",
        hypothesis_statement: Optional[str] = None,
        pillars: Optional[List[StrategyPillarData]] = None,
        synthesis_conclusion: Optional[str] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        kwargs: Dict[str, Any] = {
            "prs": self.prs,
            "theme": self.theme,
            "tracker": tracker,
            "action_title": action_title,
            "subtitle": subtitle,
            "pillars": pillars,
            "current_idx": idx,
            "total_slides": idx,
        }
        if hypothesis_statement:
            kwargs["hypothesis_statement"] = hypothesis_statement
        if synthesis_conclusion:
            kwargs["synthesis_conclusion"] = synthesis_conclusion

        return build_mckinsey_cascade_slide(**kwargs)

    def add_balanced_scorecard_slide(
        self,
        tracker: str = "Executive Governance & Performance  |  Balanced Scorecard",
        action_title: str = "Target Performance Exceeds Benchmark SLAs Across All Four Operational Dimensions",
        subtitle: Optional[str] = "Comprehensive KPI matrix tracking financial returns, customer value, process speed, and organizational resilience.",
        quadrants: Optional[List[ScorecardQuadrantData]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_balanced_scorecard_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            quadrants=quadrants,
            current_idx=idx,
            total_slides=idx,
        )

    def add_chapter_divider_slide(
        self,
        tracker: str = "PHASE 02: ARCHITECTURE & PLANNING",
        title: str = "Modern Cloud Data Platform Architecture",
        subtitle: Optional[str] = "End-to-end data pipelines, staging lakehouse, and analytics delivery.",
        hero_image_path: Optional[Union[str, Path]] = None,
        logo_path: Optional[Union[str, Path]] = None,
        division_tag: Optional[str] = "BAS Division  |  Data & AI Practice",
        tagline: Optional[str] = None,
        scrim_alpha: float = 0.45,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_chapter_divider_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            title=title,
            subtitle=subtitle,
            hero_image_path=hero_image_path,
            logo_path=logo_path,
            division_tag=division_tag,
            tagline=tagline,
            scrim_alpha=scrim_alpha,
            current_idx=idx,
            total_slides=idx,
            show_footer=False,
        )

    def add_chevron_process_slide(
        self,
        tracker: str = "Execution Roadmap & Delivery Phases",
        action_title: str = "Phased Execution Roadmap Delivers Accelerated Value Across Four Controlled Horizons",
        subtitle: Optional[str] = "Sequential progression transitions foundation infrastructure into production analytics.",
        steps: Optional[List[ProcessChevronStep]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_chevron_process_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            steps=steps,
            current_idx=idx,
            total_slides=idx,
        )

    def add_split_hero_slide(
        self,
        tracker: str = "Executive Synthesis & Core Impact",
        action_title: str = "Modern Data Architecture Unlocks High-Yield Operational Transformation",
        subtitle: Optional[str] = "Centralized lakehouse foundation drives immediate cost avoidance and predictive analytics velocity.",
        hero_stat: str = "$14.8M",
        hero_stat_label: str = "Annualized Business Value",
        hero_stat_subtext: Optional[str] = "Projected 3-year cumulative ROI with 4.2x payback across supply chain and analytics operations.",
        blocks: Optional[List[SplitHeroBlock]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_split_hero_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            hero_stat=hero_stat,
            hero_stat_label=hero_stat_label,
            hero_stat_subtext=hero_stat_subtext,
            blocks=blocks,
            current_idx=idx,
            total_slides=idx,
        )

    def add_gap_analysis_slide(
        self,
        tracker: str = "Architecture Gap Analysis  |  Current vs. Target State",
        action_title: str = "Modernization Closes Critical Gaps Between Legacy Constraints and Future Target State",
        subtitle: Optional[str] = "Systematic transformation resolves batch latency, data silos, and manual governance overhead.",
        dimensions: Optional[List[GapDimensionData]] = None,
        as_is_header: str = "CURRENT STATE (AS-IS)",
        to_be_header: str = "TARGET ARCHITECTURE (TO-BE)",
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_gap_analysis_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            dimensions=dimensions,
            as_is_header=as_is_header,
            to_be_header=to_be_header,
            current_idx=idx,
            total_slides=idx,
        )

    def add_equity_corporate_tree_slide(
        self,
        tracker: str = "CORPORATE GOVERNANCE | EQUITY STRUCTURE",
        action_title: str = "Metrodata Group Operates Multi-Tier Operating Subsidiaries and Specialized JVs",
        subtitle: Optional[str] = "PT Metrodata Electronics Tbk (MTDL) maintains controlling equity across core ICT distribution, solutions, and digital consulting entities.",
        tree_data: Optional[EquityTreeData] = None,
        footnote: Optional[str] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        if tree_data and footnote:
            tree_data.footnote = footnote
        return build_equity_corporate_tree_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            tree_data=tree_data,
            current_idx=idx,
            total_slides=idx,
        )

    def add_browser_mockup_slide(
        self,
        tracker: str = "System Architecture & Interface Validation",
        action_title: str = "Modernized Analytics Platform Eliminates ERP Latency and Siloed Data Exports",
        subtitle: Optional[str] = "High-fidelity interface preview running directly on Snowflake Cortex AI and Streamlit serving tiers.",
        screenshot_path: Optional[Union[str, Path]] = None,
        url: str = "https://finance.snowflakecomputing.com/streamlit/app",
        telemetry_badges: Optional[List[str]] = None,
        theme_mode: str = "light",
        aspect_ratio: Optional[str] = "16:9",
        target_dpi: int = 300,
        takeaways_title: str = "KEY OBSERVATIONS & DRIVERS",
        takeaways: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_browser_mockup_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            screenshot_path=screenshot_path,
            url=url,
            telemetry_badges=telemetry_badges,
            theme_mode=theme_mode,
            aspect_ratio=aspect_ratio,
            target_dpi=target_dpi,
            takeaways_title=takeaways_title,
            takeaways=takeaways,
            current_idx=idx,
            total_slides=idx,
        )

    def add_timeline_gantt_slide(
        self,
        tracker: str = "DELIVERY ROADMAP | PROJECT EXECUTION",
        action_title: str = "Phased Execution Plan Ensures Iterative Milestone Realization Across 12 Weeks",
        subtitle: Optional[str] = "Integrated schedule coordinating foundational lakehouse infrastructure, dbt transformations, and Streamlit delivery.",
        gantt_data: Optional[GanttTimelineData] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_timeline_gantt_slide(
            prs_or_slide=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            gantt_data=gantt_data,
            current_idx=idx,
            total_slides=idx,
        )

    def add_feature_matrix_slide(
        self,
        tracker: str = "ARCHITECTURE EVALUATION | PLATFORM BENCHMARK",
        action_title: str = "Snowflake AI Data Cloud Demonstrates Superior Capabilities Across Core Evaluation Criteria",
        subtitle: Optional[str] = "Multi-dimensional comparative assessment evaluating compute elasticity, data governance, and native AI integration.",
        matrix_data: Optional[FeatureMatrixData] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_feature_matrix_slide(
            prs_or_slide=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            matrix_data=matrix_data,
            current_idx=idx,
            total_slides=idx,
        )

    def add_tech_logo_grid_slide(
        self,
        tracker: str = "TECHNOLOGY PORTFOLIO | ENTERPRISE ECOSYSTEM",
        action_title: str = "Curated Best-of-Breed Technology Stack Delivers Governed High-Performance Analytics",
        subtitle: Optional[str] = "Standardized technology matrix spanning ingestion, lakehouse storage, transformation, and semantic delivery.",
        items: Optional[List[TechLogoItem]] = None,
        columns: int = 4,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_tech_logo_grid_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            items=items,
            columns=columns,
            current_idx=idx,
            total_slides=idx,
        )

    def add_card_grid_slide(
        self,
        tracker: str = "STRATEGIC CAPABILITIES | CORE SERVICE OFFERINGS",
        action_title: str = "Comprehensive Enterprise Solutions Span Modern Infrastructure to Autonomous Intelligence",
        subtitle: Optional[str] = "Eight integrated core pillars deliver complete lifecycle support from strategic advisory to operational execution.",
        items: Optional[List[CardGridItem]] = None,
        columns: int = 4,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_card_grid_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            items=items,
            columns=columns,
            current_idx=idx,
            total_slides=idx,
        )

    def add_badge_matrix_slide(
        self,
        tracker: str = "COMPETENCY & CREDENTIALS | PARTNERSHIP TIERS",
        action_title: str = "Certified Industry Expertise Assures Technical Excellence and Rapid Delivery",
        subtitle: Optional[str] = "Tiered competency matrix validates advanced specialization across hyperscalers, lakehouse platforms, and governance frameworks.",
        sections: Optional[List[BadgeMatrixSection]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_badge_matrix_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            sections=sections,
            current_idx=idx,
            total_slides=idx,
        )

    def add_iceberg_concept_slide(
        self,
        tracker: str = "STRATEGIC RATIONALE | ARCHITECTURE FOUNDATION",
        action_title: str = "Modern Data Platform Architecture Solves the Critical Subsurface Foundation Gap",
        subtitle: Optional[str] = "While executives interact with surface dashboards, 85% of analytical resilience depends on robust foundation engineering.",
        visible_items: Optional[List[Dict[str, str]]] = None,
        subsurface_items: Optional[List[Dict[str, str]]] = None,
        takeaways: Optional[List[str]] = None,
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_iceberg_concept_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            visible_items=visible_items,
            subsurface_items=subsurface_items,
            takeaways=takeaways,
            current_idx=idx,
            total_slides=idx,
        )

    def add_dense_workstream_runbook_slide(
        self,
        tracker: str = "WORKSTREAM RUNBOOK  |  WS1: AWS LANDING ZONE FOUNDATION",
        action_title: str = "AWS Landing Zone Foundation Establishes Multi-Account Isolation and Transit Mesh",
        subtitle: Optional[str] = "Contractual engineering execution runbook defining technical deliverables, counterpart PICs, and cross-stream dependencies.",
        runbook_data: Optional[DenseWorkstreamRunbookData] = None,
        notice: str = "Enterprise Architecture & Modernization Practice  |  Confidential & Contractual",
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_dense_workstream_runbook_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            runbook_data=runbook_data,
            current_idx=idx,
            total_slides=idx,
            notice=notice,
        )

    def add_target_architecture_swimlane_slide(
        self,
        tracker: str = "TARGET ARCHITECTURE  |  3-COLUMN BOUNDARY SWIMLANES",
        action_title: str = "Target Lakehouse Architecture Establishes Unified Medallion Ingestion and Semantic Serving",
        subtitle: Optional[str] = "Three-column boundary architecture isolating on-premises feeds, managed cloud lakehouse core, and consumer analytics.",
        swimlane_data: Optional[TargetArchitectureSwimlaneData] = None,
        notice: str = "Enterprise Architecture & Modernization Practice  |  Confidential & Contractual",
    ) -> Any:
        idx = len(self.prs.slides) + 1
        return build_target_architecture_swimlane_slide(
            prs=self.prs,
            theme=self.theme,
            tracker=tracker,
            action_title=action_title,
            subtitle=subtitle,
            swimlane_data=swimlane_data,
            current_idx=idx,
            total_slides=idx,
            notice=notice,
        )

    def update_pagination(self) -> None:
        """
        Post-processes all slides to ensure bottom footer pagination (e.g. '02 / 07')
        accurately reflects the total slide count across the entire deck.
        Preserves existing font styling, size, boldness, and color.
        """
        import re
        total_slides = len(self.prs.slides)
        for s_idx, slide in enumerate(self.prs.slides, start=1):
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text_clean = paragraph.text.strip()
                        if re.match(r"^\d{2}\s*/\s*\d{2}$", text_clean):
                            new_page_str = f"{s_idx:02d} / {total_slides:02d}"
                            if paragraph.runs:
                                r0 = paragraph.runs[0]
                                font_name = r0.font.name
                                font_size = r0.font.size
                                font_bold = r0.font.bold
                                font_color = r0.font.color.rgb if (r0.font.color and r0.font.color.type == 1) else None
                                paragraph.text = new_page_str
                                if paragraph.runs:
                                    nr = paragraph.runs[0]
                                    nr.font.name = font_name
                                    nr.font.size = font_size
                                    nr.font.bold = font_bold
                                    if font_color:
                                        nr.font.color.rgb = font_color
                            else:
                                paragraph.text = new_page_str

    def save(
        self,
        output_path: Union[str, Path],
        engagement_context: Optional[Any] = None,
    ) -> Path:
        """Save presentation deck to the specified path after synchronizing pagination and substituting slugs."""
        self.update_pagination()
        if engagement_context is not None:
            from src.core.slug_registry import substitute_slugs_in_presentation
            substitute_slugs_in_presentation(self.prs, engagement_context)

        # Enforce flat vector aesthetic by stripping OpenXML drop shadows across all slide shapes
        for slide in self.prs.slides:
            for sh in slide.shapes:
                strip_shape_shadows(sh)

        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(p))
        return p


