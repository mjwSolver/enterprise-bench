"""
Presales Modernization Pitch Deck Builder Subsystem
===================================================
Automates and modernizes the 36-slide Presales Pitch Deck
(`Modernize_Data_Platform_Pitch_Deck_Template.pptx`) for enterprise cloud modernizations,
conforming to consulting frameworks, 60-30-10 palette distribution, and geometric rules:

  Slide 01: Master Cover (Cinematic Hero Cover / Clean Typographic Columns)
  Slide 02: Chapter Divider (Our Company Profile)
  Slide 03: Metrodata Corporate Structure (Hierarchical Equity Tree)
  Slide 04: Metrodata 8 Pillars Offering (4x2 Capability Card Matrix)
  Slide 05: Chapter Divider (Our Data & AI Portfolio)
  Slide 06: Product Portfolio (Normalized Tech Logo Grid)
  Slide 07: Modern Data Stack & Orchestration (Pipeline Ingestion Grid)
  Slide 08: Competencies & Certifications (Tiered Badge Matrix)
  Slide 09: Chapter Divider (Our Customer References)
  Slide 10: Enterprise Client References (Multi-Sector Credential Grid)
  Slide 11: Data Science & AI Portfolio (Capability Card Grid)
  Slide 12: Chapter Divider (Data Analytics Journey)
  Slide 13: Analytics Journey – Start with KPI (Split-Hero Inquiry Cards)
  Slide 14: The Iceberg Concept (Visible Interface vs Subsurface Foundation)
  Slide 15: Chapter Divider (Product Introduction & Objective)
  Slide 16: Snowflake: The AI Data Cloud (3-Tier Decoupled Architecture)
  Slide 17: Snowflake Platform Architecture (Official Architecture Blueprint)
  Slide 18: Business Applications & End-to-End Pipeline (Official Solution Flow)
  Slide 19: Chapter Divider (Existing Challenge & Proposed Solution)
  Slide 20: Existing Challenges (SAP ERP Window Mockup + Observation Cards)
  Slide 21: Gap Analysis & Solution (As-Is vs To-Be Comparative Matrix)
  Slide 22: Proposed Solution (4-Stage Value Chain Chevrons)
  Slide 23: Proposed Target Architecture (Architecture Blueprint Container)
  Slide 24: Analytics & Serving Architecture (Streamlit Window Mockup)
  Slide 25: Chapter Divider (Scope of Work)
  Slide 26: Project Delivery Lifecycle (Initiation to Handover Stepped Cards)
  Slide 27: Scope of Work Workstreams (4-Column WBS Structure)
  Slide 28: Assumptions – Sales & Gross Profit (Streamlit Browser Container)
  Slide 29: Assumptions – Opex & Margin (Streamlit Financial Container)
  Slide 30: Assumptions Summary (Strategic Scope Boundaries)
  Slide 31: Chapter Divider (Project Timeline & Organization)
  Slide 32: Project Timeline Estimate (Delivery Gantt Archetype)
  Slide 33: Project Organization Structure (Hierarchical RACI Org Tree)
  Slide 34: Chapter Divider (Change Request Procedure)
  Slide 35: Change Request Procedure (Governance Pipeline & Decision Gates)
  Slide 36: Executive Closing & Contact (Corporate Emblem & Contacts)

Strictly enforces:
  - Zero overlapping top lines on rounded cards (sharp MSO_SHAPE.RECTANGLE).
  - Unified title and subtitle frames (space_before = Pt(10)).
  - Clean typographic metadata on cover (zero boxed containers, no cover footer).
  - Synchronized bottom pagination ('02 / 36' to '36 / 36').
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from src.core.slug_registry import EngagementContext, substitute_slugs_in_presentation
from src.ppt_engine.archetypes.common import find_emojis
from src.ppt_engine.consulting_archetypes import (
    AgendaItem,
    BadgeMatrixSection,
    CardGridItem,
    ConsultingDeckBuilder,
    EquityEntityNode,
    EquityTreeData,
    FeatureMatrixData,
    GanttTask,
    GanttTimelineData,
    GanttWorkstream,
    GapDimensionData,
    HorizonColumnData,
    ProcessChevronStep,
    ScorecardMetric,
    ScorecardQuadrantData,
    SplitHeroBlock,
    StrategyPillarData,
    TableColumnDef,
    TechLogoItem,
    add_card,
    add_card_with_top_stripe,
    add_slide_footer,
    add_slide_header,
    add_slide_with_background,
    build_agenda_slide,
    build_badge_matrix_slide,
    build_bcg_3_horizon_slide,
    build_browser_mockup_slide,
    build_card_grid_slide,
    build_chapter_divider_slide,
    build_chevron_process_slide,
    build_composable_split_slide,
    build_cover_slide,
    build_crisp_dm_gate_slide,
    build_equity_corporate_tree_slide,
    build_feature_matrix_slide,
    build_gap_analysis_slide,
    build_gate_validation_slide,
    build_hero_cover_slide,
    build_iceberg_concept_slide,
    build_mckinsey_cascade_slide,
    build_medallion_tiers_slide,
    build_open_telemetry_flow_slide,
    build_split_hero_slide,
    build_table_slide,
    build_tech_logo_grid_slide,
    build_thank_you_slide,
    build_timeline_gantt_slide,
    create_presentation,
)
from src.ppt_engine.reference_slides import (
    build_change_request_procedure_slide,
    build_governance_org_structure_slide,
    build_snowflake_data_pipeline_slide,
    build_snowflake_platform_architecture_slide,
)
from src.ppt_engine.theme_engine import Theme, get_theme, hex_to_rgb, strip_shape_shadows

logger = logging.getLogger(__name__)

# Precompiled regex for footer slide pagination ("02 / 36")
PAGE_REGEX = re.compile(r"^\d{2}\s*/\s*\d{2}$")


class PitchDeckBuilder:
    """Specialized presentation generator for the 36-slide Presales Modernization Pitch Deck."""

    def __init__(
        self,
        theme: Union[str, Theme] = "metrodata",
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        if isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = theme

        self.prs: Presentation = create_presentation(self.theme)
        self.config: Dict[str, Any] = config_dict or {}
        self.metadata: Dict[str, Any] = self.config.get("metadata") or {}
        self.client_name: str = self.metadata.get("client_name", "[CLIENT_COMPANY_NAME]")
        self.vendor_name: str = self.metadata.get("vendor_name", "PT Metrodata Electronics Tbk")
        self.product: str = self.metadata.get("product", "Snowflake AI Data Cloud")
        self.date_str: str = self.metadata.get("date_str", "September 2026")
        self.notice: Optional[str] = self.metadata.get("confidentiality")

    @classmethod
    def from_yaml(
        cls,
        yaml_path: Union[str, Path],
        theme_override: Optional[str] = None,
    ) -> "PitchDeckBuilder":
        """Instantiates PitchDeckBuilder from a declarative YAML deck configuration."""
        p = Path(yaml_path)
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        theme_name = theme_override or (data.get("theme") if isinstance(data, dict) else "metrodata") or "metrodata"
        builder = cls(theme=theme_name, config_dict=data)
        return builder

    def _validate_zero_emojis(self, obj: Any, context: str = "deck") -> None:
        if isinstance(obj, str):
            found = find_emojis(obj)
            if found:
                raise ValueError(
                    f"Prohibited emoji(s) detected in {context}: {' '.join(dict.fromkeys(found))}. "
                    "Emojis are banned; use clean text or Lucide/SVG vector icons instead."
                )
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k == "icon_emoji" and v:
                    raise ValueError(
                        f"Prohibited icon_emoji '{v}' detected in {context}. "
                        "Use vector SVG logos or Lucide icons instead."
                    )
                self._validate_zero_emojis(v, context=context)
        elif isinstance(obj, (list, tuple)):
            for it in obj:
                self._validate_zero_emojis(it, context=context)

    def build_all(self, slide_limit: Optional[int] = None) -> None:
        """Iterates through all declared slides in config and compiles them into the presentation."""
        self._validate_zero_emojis(self.metadata, context="deck metadata")
        slides_cfg = self.config.get("slides") or []
        if slide_limit is not None and slide_limit > 0:
            slides_cfg = slides_cfg[:slide_limit]

        for s_idx, s_cfg in enumerate(slides_cfg, start=1):
            self._validate_zero_emojis(s_cfg, context=f"slide {s_idx}")
            archetype = s_cfg.get("archetype", "")
            self._dispatch_slide(archetype, s_cfg, s_idx, len(slides_cfg))

    def _dispatch_slide(
        self,
        archetype: str,
        cfg: Dict[str, Any],
        idx: int,
        total: int,
    ) -> None:
        """Dispatches configuration block to the matching archetype function."""
        arch = archetype.lower().strip()

        if arch in ("cover", "hero_cover", "cinematic_cover"):
            hero_img = cfg.get("hero_image_path")
            if arch in ("hero_cover", "cinematic_cover") or hero_img:
                build_hero_cover_slide(
                    self.prs,
                    self.theme,
                    title=cfg.get("title", "Data Application for Financial Analytics with Snowflake"),
                    subtitle=cfg.get("subtitle", "Modernizing Financial Data Architecture, High-Speed Ingestion & Executive Analytics"),
                    client=cfg.get("client", self.client_name),
                    vendor=cfg.get("vendor", self.vendor_name),
                    product=cfg.get("product", self.product),
                    date_str=cfg.get("date_str", self.date_str),
                    tracker=cfg.get("tracker", "ENTERPRISE PRESALES MODERNIZATION"),
                    hero_image_path=hero_img,
                    hero_height=float(cfg.get("hero_height", 3.65)),
                    scrim_alpha=float(cfg.get("scrim_alpha", 0.28)),
                )
            else:
                build_cover_slide(
                    self.prs,
                    self.theme,
                    title=cfg.get("title", "Data Application for Financial Analytics with Snowflake"),
                    subtitle=cfg.get("subtitle", "Modernizing Financial Data Architecture, High-Speed Ingestion & Executive Analytics"),
                    client=cfg.get("client", self.client_name),
                    vendor=cfg.get("vendor", self.vendor_name),
                    product=cfg.get("product", self.product),
                    date_str=cfg.get("date_str", self.date_str),
                    tracker=cfg.get("tracker", "ENTERPRISE PRESALES MODERNIZATION"),
                    client_logo_path=cfg.get("client_logo_path"),
                    product_logo_path=cfg.get("product_logo_path"),
                    vendor_logo_path=cfg.get("vendor_logo_path"),
                    client_sublabel=cfg.get("client_sublabel", "Steering Committee & Executive Sponsors"),
                    vendor_sublabel=cfg.get("vendor_sublabel", "Data & AI Modernization Practice"),
                )

        elif arch in ("agenda", "table_of_contents", "toc"):
            raw_items = cfg.get("items") or []
            items = []
            for itm in raw_items:
                if isinstance(itm, dict):
                    items.append(AgendaItem(
                        num=str(itm.get("num", f"{len(items)+1:02d}")),
                        title=itm.get("title", ""),
                        description=itm.get("description"),
                        badge=itm.get("badge"),
                        accent_key=itm.get("accent_key", "accent"),
                    ))
            build_agenda_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Agenda"),
                subtitle=cfg.get("subtitle"),
                items=items if items else None,
                columns=int(cfg.get("columns", 2)),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("chapter_divider", "section_divider"):
            build_chapter_divider_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker", "SECTION"),
                title=cfg.get("headline", cfg.get("title", "Chapter Title")),
                subtitle=cfg.get("subtitle"),
                division_tag=cfg.get("division_tagline", "PT Mitra Integrasi Informatika"),
                hero_image_path=cfg.get("hero_image_path"),
                current_idx=idx,
                total_slides=total,
            )

        elif arch in ("corporate_equity_tree", "equity_tree"):
            tree_raw = cfg.get("tree_data")
            tree_data = None
            if tree_raw and isinstance(tree_raw, dict):
                p_nodes_raw = tree_raw.get("tier1_nodes") or tree_raw.get("public_shareholders") or []
                s_nodes_raw = tree_raw.get("tier2_nodes") or tree_raw.get("subsidiaries") or []
                p_nodes = [
                    EquityEntityNode(
                        name=n.get("name", ""),
                        code=n.get("code", ""),
                        percentage=str(n.get("percentage", "")),
                        business_domain=n.get("business_domain") or n.get("domain", ""),
                        tier=int(n.get("tier", 1)),
                        parent_code=n.get("parent_code"),
                        accent_color=n.get("accent_color"),
                    )
                    for n in p_nodes_raw
                    if isinstance(n, dict)
                ]
                s_nodes = [
                    EquityEntityNode(
                        name=n.get("name", ""),
                        code=n.get("code", ""),
                        percentage=str(n.get("percentage", "")),
                        business_domain=n.get("business_domain") or n.get("domain", ""),
                        tier=int(n.get("tier", 2)),
                        parent_code=n.get("parent_code"),
                        accent_color=n.get("accent_color"),
                    )
                    for n in s_nodes_raw
                    if isinstance(n, dict)
                ]
                tree_data = EquityTreeData(
                    parent_company=tree_raw.get("parent_company") or tree_raw.get("holding_name", "PT METRODATA ELECTRONICS TBK"),
                    parent_ticker=tree_raw.get("parent_ticker") or tree_raw.get("holding_ticker", "MTDL"),
                    parent_subtitle=tree_raw.get("parent_subtitle") or tree_raw.get("holding_subtitle", "Leading ICT Solutions & Distribution Ecosystem in Indonesia"),
                    tier1_nodes=p_nodes,
                    tier2_nodes=s_nodes,
                    footnote=tree_raw.get("footnote"),
                )
            build_equity_corporate_tree_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Corporate Structure & Shareholding Hierarchy"),
                subtitle=cfg.get("subtitle"),
                tree_data=tree_data,
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("card_grid", "capability_cards", "pillars_grid"):
            raw_items = cfg.get("items") or []
            items = []
            for itm in raw_items:
                if isinstance(itm, dict):
                    items.append(CardGridItem(
                        title=itm.get("title", ""),
                        subtitle=itm.get("subtitle"),
                        icon=itm.get("icon"),
                        bullets=itm.get("bullets") or [],
                        accent_key=itm.get("accent_key", "accent"),
                        badge=itm.get("badge"),
                        metric=itm.get("metric"),
                        metric_label=itm.get("metric_label"),
                        widget=itm.get("widget"),
                        has_top_stripe=bool(itm.get("has_top_stripe", False)),
                    ))
            build_card_grid_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Capability Overview"),
                subtitle=cfg.get("subtitle"),
                items=items if items else None,
                columns=int(cfg["columns"]) if cfg.get("columns") is not None else None,
                takeaway=cfg.get("takeaway"),
                show_top_stripes=bool(cfg.get("show_top_stripes", False)),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("tech_logo_grid", "product_portfolio", "tech_grid"):
            raw_items = cfg.get("items") or []
            items = []
            for itm in raw_items:
                if isinstance(itm, dict):
                    items.append(TechLogoItem(
                        name=itm.get("name", ""),
                        category=itm.get("category", ""),
                        tier_badge=itm.get("tier_badge"),
                        logo=itm.get("logo"),
                        accent_key=itm.get("accent_key", "accent"),
                        description=itm.get("description"),
                    ))
            build_tech_logo_grid_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Technology Stack Overview"),
                subtitle=cfg.get("subtitle"),
                items=items if items else None,
                columns=int(cfg.get("columns", 4)),
                show_top_stripes=bool(cfg.get("show_top_stripes", False)),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("badge_matrix", "certifications", "partner_matrix"):
            raw_sections = cfg.get("sections") or []
            sections = []
            for s in raw_sections:
                if isinstance(s, dict):
                    sections.append(BadgeMatrixSection(
                        section_title=s.get("section_title", ""),
                        accent_key=s.get("accent_key", "accent"),
                        badge_count_label=s.get("badge_count_label"),
                        items=s.get("items") or [],
                    ))
            build_badge_matrix_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Capabilities & Credentials Matrix"),
                subtitle=cfg.get("subtitle"),
                sections=sections if sections else None,
                show_top_stripes=bool(cfg.get("show_top_stripes", False)),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("iceberg_concept", "iceberg"):
            build_iceberg_concept_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Architecture Foundation Overview"),
                subtitle=cfg.get("subtitle"),
                visible_items=cfg.get("visible_items"),
                subsurface_items=cfg.get("subsurface_items"),
                takeaways=cfg.get("takeaways"),
                takeaway_title=cfg.get("takeaway_title"),
                takeaway_subtitle=cfg.get("takeaway_subtitle"),
                show_top_stripes=bool(cfg.get("show_top_stripes", False)),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
                source=cfg.get("source"),
            )

        elif arch in ("split_hero", "kpi_framework"):
            blocks = []
            for b in (cfg.get("blocks") or []):
                if isinstance(b, dict):
                    blocks.append(SplitHeroBlock(
                        title=b.get("title", ""),
                        description=b.get("description", b.get("body", "")),
                        metric_badge=b.get("metric_badge", b.get("badge")),
                        category_tag=b.get("category_tag", b.get("tag")),
                        badge_variant=b.get("badge_variant"),
                    ))
            build_split_hero_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Executive Impact Overview"),
                subtitle=cfg.get("subtitle"),
                hero_stat=cfg.get("hero_stat", cfg.get("hero_tag", "")),
                hero_stat_label=cfg.get("hero_stat_label", cfg.get("hero_title", "")),
                hero_stat_subtext=cfg.get("hero_stat_subtext", cfg.get("hero_body")),
                hero_eyebrow=cfg.get("hero_eyebrow"),
                blocks=blocks if blocks else None,
                source=cfg.get("source"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("composable_split", "split_canvas", "composable", "multi_pane", "composite_layout"):
            build_composable_split_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", cfg.get("action_title", "")),
                subtitle=cfg.get("subtitle"),
                split=cfg.get("split"),
                panes=cfg.get("panes", cfg.get("columns", cfg.get("regions"))),
                top_kpis=cfg.get("top_kpis"),
                gap=float(cfg.get("gap", 0.35)),
                takeaway=cfg.get("takeaway"),
                source=cfg.get("source"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("snowflake_platform_architecture", "platform_architecture"):
            build_snowflake_platform_architecture_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker", "TECHNOLOGY PLATFORM BLUEPRINT | SNOWFLAKE DATA CLOUD"),
                action_title=cfg.get("title", "Fully-Managed Unified Platform Eliminates Data Silos Across Multi-Cloud Environments"),
                subtitle=cfg.get("subtitle", "Official Snowflake platform blueprint showing decoupled storage, elastic compute, and Horizon governance."),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("snowflake_data_pipeline", "solution_architecture", "data_pipeline"):
            build_snowflake_data_pipeline_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker", "SOLUTION ARCHITECTURE | END-TO-END DATA PIPELINE"),
                action_title=cfg.get("title", "Modern Data Pipeline Streamlines Continuous Ingestion into Governed Analytics Consumption"),
                subtitle=cfg.get("subtitle", "Official end-to-end data flow: transactional ERP/IoT sources into Snowflake core, virtual warehouses, and delivery channels."),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("bcg_3_horizon", "3_tier_architecture", "horizons"):
            horizons = []
            for h in (cfg.get("horizons") or []):
                if isinstance(h, dict):
                    h_tag = h.get("horizon_tag") or h.get("tag") or h.get("name") or "HORIZON"
                    h_title = h.get("title") or ""
                    h_focus = h.get("strategic_focus") or h.get("focus") or h.get("subtitle") or ""
                    h_metric = h.get("metric_highlight") or h.get("metric") or ""
                    h_label = h.get("metric_label") or h.get("subtext") or ""
                    h_inits = h.get("initiatives") or h.get("bullets") or []
                    acc_k = h.get("accent_key", "accent")
                    s_tag = h.get("status_tag") or h.get("status", "IN EXECUTION")
                    auto_bg, auto_tx = self.theme.resolve_status_badge_keys(s_tag)
                    def_bg, def_tx = auto_bg, auto_tx

                    if acc_k == "secondary" and def_bg == "badge_blue_fill":
                        def_bg, def_tx = "badge_slate_fill", "badge_slate_text"
                    elif acc_k == "muted" and def_bg == "badge_blue_fill":
                        def_bg, def_tx = "badge_muted_fill", "badge_muted_text"
                    elif acc_k == "danger":
                        def_bg, def_tx = "badge_red_fill", "badge_red_text"
                    elif acc_k == "warning":
                        def_bg, def_tx = "badge_amber_fill", "badge_amber_text"
                    elif acc_k == "success":
                        def_bg, def_tx = "badge_green_fill", "badge_green_text"

                    horizons.append(HorizonColumnData(
                        horizon_tag=h_tag,
                        title=h_title,
                        strategic_focus=h_focus,
                        metric_highlight=h_metric,
                        metric_label=h_label,
                        initiatives=h_inits,
                        accent_key=acc_k,
                        status_tag=s_tag,
                        status_bg_key=h.get("status_bg_key", def_bg),
                        status_text_key=h.get("status_text_key", def_tx),
                        icon=h.get("icon"),
                        icon_path=h.get("icon_path"),
                    ))
            build_bcg_3_horizon_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Three-Horizon Modernization Strategy"),
                subtitle=cfg.get("subtitle"),
                horizons=horizons if horizons else None,
                takeaway=cfg.get("takeaway"),
                source=cfg.get("source"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("browser_mockup", "window_mockup", "app_mockup", "app_walkthrough", "module_walkthrough"):
            build_browser_mockup_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Interface & System Preview"),
                subtitle=cfg.get("subtitle"),
                screenshot_path=cfg.get("screenshot_path") or cfg.get("screenshot") or cfg.get("image_path"),
                url=cfg.get("url", "https://finance.snowflakecomputing.com/streamlit/app"),
                telemetry_badges=cfg.get("telemetry_badges"),
                theme_mode=cfg.get("theme_mode", "light"),
                takeaways_title=cfg.get("takeaways_title"),
                takeaways=cfg.get("takeaways"),
                show_top_stripes=bool(cfg.get("show_top_stripes", False)),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
                source=cfg.get("source"),
            )

        elif arch in ("gap_analysis", "as_is_to_be"):
            dims: Optional[List[GapDimensionData]] = None
            raw_dims = cfg.get("dimensions")
            if raw_dims and isinstance(raw_dims, list):
                dims = []
                for d in raw_dims:
                    if not isinstance(d, dict):
                        continue
                    as_is_txt = d.get("as_is_state") or d.get("as_is") or ""
                    if not as_is_txt:
                        t_as = str(d.get("as_is_title") or "").strip()
                        b_as = str(d.get("as_is_body") or "").strip()
                        as_is_txt = f"{t_as}: {b_as}" if (t_as and b_as) else (t_as or b_as)
                    to_be_txt = d.get("to_be_state") or d.get("to_be") or ""
                    if not to_be_txt:
                        t_tb = str(d.get("to_be_title") or "").strip()
                        b_tb = str(d.get("to_be_body") or "").strip()
                        to_be_txt = f"{t_tb}: {b_tb}" if (t_tb and b_tb) else (t_tb or b_tb)
                    dims.append(GapDimensionData(
                        dimension=d.get("dimension", ""),
                        as_is_state=as_is_txt,
                        to_be_state=to_be_txt,
                        transition_lever=d.get("transition_lever"),
                        impact_delta=d.get("impact_delta"),
                        deficit_tag=d.get("deficit_tag"),
                    ))
            build_gap_analysis_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Current vs. Target Architecture Comparison"),
                subtitle=cfg.get("subtitle"),
                dimensions=dims,
                as_is_header=cfg.get("as_is_header", "CURRENT STATE (AS-IS)"),
                to_be_header=cfg.get("to_be_header", "TARGET ARCHITECTURE (TO-BE)"),
                left_title=cfg.get("left_title"),
                left_subtitle=cfg.get("left_subtitle"),
                left_items=cfg.get("left_items") or cfg.get("left_bullets"),
                left_eyebrow=cfg.get("left_eyebrow"),
                right_title=cfg.get("right_title"),
                right_subtitle=cfg.get("right_subtitle"),
                right_items=cfg.get("right_items") or cfg.get("right_bullets"),
                right_eyebrow=cfg.get("right_eyebrow"),
                takeaway=cfg.get("takeaway"),
                source=cfg.get("source"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("open_telemetry_flow", "pipeline_gate_matrix", "geometric_telemetry", "telemetry_pipeline_hud"):
            build_open_telemetry_flow_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Pipeline Telemetry & Quality Gates"),
                subtitle=cfg.get("subtitle"),
                pipeline_steps=cfg.get("pipeline_steps"),
                hero_metrics=cfg.get("hero_metrics"),
                mockup_config=cfg.get("mockup_config") or cfg.get("widget"),
                left_title=cfg.get("left_title", "Production Model Serving Console"),
                left_subtitle=cfg.get("left_subtitle"),
                right_title=cfg.get("right_title", "Automated Production Quality Gates"),
                right_subtitle=cfg.get("right_subtitle"),
                gate_matrix=cfg.get("gate_matrix") or cfg.get("threshold_bars") or cfg.get("chart_data"),
                footnote=cfg.get("footnote"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("gate_validation", "threshold_bars", "coverage_gate_validation", "metric_gate_review"):
            resolved_chart = cfg.get("chart_data") or cfg.get("threshold_bars")
            if not resolved_chart and cfg.get("gates"):
                raw_gates = [g for g in (cfg.get("gates") or []) if isinstance(g, dict)]
                series = []
                thresholds = []
                seen_thresh = set()
                for g in raw_gates:
                    val = float(g.get("actual", g.get("value", 0.0)))
                    st = str(g.get("status", "PASS")).upper()
                    bar_c = "#16A34A" if st == "PASS" else ("#D97706" if st in ("WARN", "WARNING") else "#DC2626")
                    series.append({
                        "label": g.get("label") or g.get("title", ""),
                        "value": val,
                        "display_value": g.get("display_value") or (f"{val * 100:.1f}%" if val <= 1.0 else f"{val}"),
                        "subtext": g.get("subtext") or g.get("variance_label", ""),
                        "status": st,
                        "bar_color": g.get("bar_color", "#0284C7" if g.get("is_hero") else bar_c),
                        "status_color": g.get("status_color", bar_c),
                    })
                    if "threshold" in g and g["threshold"] is not None:
                        t_val = float(g["threshold"])
                        if t_val not in seen_thresh:
                            seen_thresh.add(t_val)
                            thresholds.append({
                                "value": t_val,
                                "label": f">= {t_val * 100:.0f}% GATE" if t_val <= 1.0 else f">= {t_val} GATE",
                                "color": "emerald" if len(seen_thresh) == 1 else "amber",
                            })
                resolved_chart = {
                    "title": cfg.get("chart_title", "STAGE-GATE TELEMETRY VALIDATION"),
                    "series": series,
                    "thresholds": thresholds,
                }
            build_gate_validation_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Gate Validation & Empirical Threshold Review"),
                subtitle=cfg.get("subtitle"),
                kpis=cfg.get("kpis"),
                chart_data=resolved_chart,
                constraints_card=cfg.get("constraints_card") or cfg.get("constraints"),
                takeaway=cfg.get("takeaway") or cfg.get("conclusion"),
                show_top_stripes=bool(cfg.get("show_top_stripes", False)),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
                source=cfg.get("source"),
            )

        elif arch in ("crisp_dm_gate", "crisp_dm", "crisp_dm_lifecycle"):
            build_crisp_dm_gate_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "CRISP-DM Lifecycle & Data Preparation Gate"),
                subtitle=cfg.get("subtitle"),
                crisp_phases=cfg.get("crisp_phases"),
                prep_cards=cfg.get("prep_cards"),
                takeaway=cfg.get("takeaway"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("medallion_tiers", "data_tiers", "medallion_stack"):
            build_medallion_tiers_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Medallion Data Tier Eligibility"),
                subtitle=cfg.get("subtitle"),
                tiers=cfg.get("tiers"),
                takeaway=cfg.get("takeaway"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("chevron_process", "process_flow", "value_chain"):
            steps = []
            for s in (cfg.get("steps") or []):
                if isinstance(s, dict):
                    acc_key = s.get("accent_key")
                    acc_col = self.theme.get_rgb(acc_key) if acc_key else None
                    steps.append(ProcessChevronStep(
                        phase_number=str(s.get("phase_number") or s.get("num") or f"{len(steps)+1:02d}"),
                        title=s.get("title", ""),
                        duration_badge=s.get("duration_badge", s.get("subtitle")),
                        deliverables=s.get("deliverables") or [],
                        status=s.get("status"),
                        accent_color=acc_col,
                        is_current=bool(s.get("is_current", False)),
                        pin_label=s.get("pin_label"),
                        pin_color=s.get("pin_color"),
                    ))
            build_chevron_process_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Delivery Phases & Roadmap"),
                subtitle=cfg.get("subtitle"),
                steps=steps if steps else None,
                takeaway=cfg.get("takeaway"),
                pin_color=str(cfg.get("pin_color", "accent")),
                pin_label=str(cfg.get("pin_label", "[ CURRENT: WE ARE HERE ]")),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("timeline_gantt", "delivery_gantt", "gantt"):
            g_raw = cfg.get("gantt_data")
            g_data = None
            if g_raw and isinstance(g_raw, dict):
                ws_list = []
                for ws in (g_raw.get("workstreams") or []):
                    if isinstance(ws, dict):
                        t_list = []
                        for t in (ws.get("tasks") or []):
                            if isinstance(t, dict):
                                t_dict = dict(t)
                                if "start_period" not in t_dict and "start_week" in t_dict:
                                    t_dict["start_period"] = float(t_dict.pop("start_week"))
                                if "end_period" not in t_dict:
                                    if "end_week" in t_dict:
                                        t_dict["end_period"] = float(t_dict.pop("end_week"))
                                    elif "duration_weeks" in t_dict:
                                        dur = float(t_dict.pop("duration_weeks"))
                                        t_dict["end_period"] = float(t_dict.get("start_period", 1.0) + max(1.0, dur) - 1.0)
                                    else:
                                        t_dict["end_period"] = float(t_dict.get("start_period", 1.0))
                                t_dict.pop("duration_weeks", None)
                                t_dict.pop("end_week", None)
                                t_list.append(GanttTask(
                                    name=t_dict.get("name", ""),
                                    start_period=float(t_dict.get("start_period", 1.0)),
                                    end_period=float(t_dict.get("end_period", 1.0)),
                                    progress_pct=float(t_dict.get("progress_pct", 100.0)),
                                    status=t_dict.get("status", "COMPLETED"),
                                    owner=t_dict.get("owner"),
                                    is_milestone=bool(t_dict.get("is_milestone", False)),
                                ))
                            elif isinstance(t, GanttTask):
                                t_list.append(t)
                        cat = ws.get("category") or ws.get("name", "Workstream")
                        accent_c = ws.get("accent_color") or ws.get("accent_key", "primary")
                        badge_c = ws.get("badge", "WORKSTREAM")
                        ws_list.append(GanttWorkstream(
                            category=cat,
                            badge=badge_c,
                            accent_color=accent_c,
                            tasks=t_list,
                        ))
                    elif isinstance(ws, GanttWorkstream):
                        ws_list.append(ws)
                total_p = int(g_raw.get("total_periods") or g_raw.get("total_weeks", 12))
                cur_marker = float(g_raw["current_period_marker"]) if "current_period_marker" in g_raw and g_raw["current_period_marker"] is not None else 6.0
                g_data = GanttTimelineData(
                    time_scale_label=g_raw.get("time_scale_label", "WEEKS"),
                    total_periods=total_p,
                    period_labels=g_raw.get("period_labels"),
                    current_period_marker=cur_marker,
                    workstreams=ws_list,
                    footnote=g_raw.get("footnote", "*) Timeline reflects target PMO sprint velocity and scheduled governance gates."),
                )
            build_timeline_gantt_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker", "PROJECT TIMELINE & DELIVERY GANTT"),
                action_title=cfg.get("title", "16-Week Modernization Roadmap Structured Across Clear Milestone Gates"),
                subtitle=cfg.get("subtitle", "Multi-phase implementation schedule coordinating cloud staging, dbt transformations, and UAT sign-off."),
                gantt_data=g_data,
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("governance_org_structure", "org_chart", "raci"):
            build_governance_org_structure_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker", "PROJECT GOVERNANCE | ORGANIZATIONAL STRUCTURE"),
                action_title=cfg.get("title", "Joint Dual-Pillar Governance Matrix Establishes Clear Escalation & Delivery Ownership"),
                subtitle=cfg.get("subtitle", "Hierarchical project structure connects executive steering committees, PMO leads, and specialized execution pods."),
                client_name=cfg.get("client_name", self.client_name),
                vendor_name=cfg.get("vendor_name", self.vendor_name),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
                tier1_client_text=cfg.get("tier1_client_text"),
                tier1_vendor_text=cfg.get("tier1_vendor_text"),
                client_pm_title=cfg.get("client_pm_title"),
                vendor_pm_title=cfg.get("vendor_pm_title"),
                client_pm_bullets=cfg.get("client_pm_bullets"),
                vendor_pm_bullets=cfg.get("vendor_pm_bullets"),
                pods=cfg.get("pods"),
            )

        elif arch in ("change_request_procedure", "cr_procedure"):
            build_change_request_procedure_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker", "PROJECT GOVERNANCE | SCOPE & CHANGE CONTROL"),
                action_title=cfg.get("title", "Structured Change Request Procedure Governs Scope Adjustments Through Defined Decision Gates"),
                subtitle=cfg.get("subtitle", "Sequential 4-stage governance pipeline with bi-level escalation thresholds and auditable legal sign-offs."),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("table", "matrix_table", "milestones_table", "prerequisites_table", "communication_table", "risk_table", "table_matrix"):
            raw_cols = cfg.get("columns") or []
            columns = []
            for c in raw_cols:
                if isinstance(c, dict):
                    columns.append(TableColumnDef(
                        header=c.get("header", ""),
                        width=float(c.get("width", 2.0)),
                        align=str(c.get("align", "LEFT")).upper(),
                        is_status=bool(c.get("is_status", False)),
                        is_index=bool(c.get("is_index", False)),
                        is_highlight=bool(c.get("is_highlight", False)),
                    ))
            rows = cfg.get("rows") or []
            build_table_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Structured Governance Register"),
                subtitle=cfg.get("subtitle"),
                columns=columns if columns else None,
                rows=rows if rows else None,
                detached_rows=cfg.get("detached_rows") or None,
                detached_connector_symbol=str(cfg.get("detached_connector_symbol", "+")),
                footnote=cfg.get("footnote"),
                takeaway=cfg.get("takeaway") or cfg.get("callout"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("thank_you", "closing", "thank_you_closing"):
            build_thank_you_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                title=cfg.get("title", "Thank You"),
                subtitle=cfg.get("subtitle"),
                contacts=cfg.get("contacts"),
                next_steps=cfg.get("next_steps"),
                company=cfg.get("company", f"{self.vendor_name}  |  PT Mitra Integrasi Informatika"),
                office=cfg.get("office"),
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        elif arch in ("feature_matrix", "harvey_balls"):
            from src.ppt_engine.archetypes.tables import FeatureScorecardRow

            m_raw = cfg.get("matrix_data")
            m_data = None
            if m_raw and isinstance(m_raw, dict):
                f_rows = []
                for r in (m_raw.get("rows") or []):
                    if isinstance(r, dict):
                        f_rows.append(FeatureScorecardRow(
                            category=r.get("category", ""),
                            criteria=r.get("criteria", ""),
                            scores=r.get("scores") or {},
                            business_impact=r.get("business_impact") or r.get("impact"),
                        ))
                    elif hasattr(r, "category"):
                        f_rows.append(r)
                cols = m_raw.get("columns") or m_raw.get("options") or []
                if not cols and f_rows:
                    cols = list(f_rows[0].scores.keys())
                m_data = FeatureMatrixData(
                    columns=cols,
                    rows=f_rows,
                    recommendation_badge=m_raw.get("recommendation_badge") or cfg.get("recommendation_badge"),
                    recommended_column=m_raw.get("recommended_column") or cfg.get("recommended_column"),
                    footnote=m_raw.get("footnote") or cfg.get("footnote"),
                )
            build_feature_matrix_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker"),
                action_title=cfg.get("title", "Platform Comparison Matrix"),
                subtitle=cfg.get("subtitle"),
                matrix_data=m_data,
                current_idx=idx,
                total_slides=total,
                notice=self.notice,
            )

        else:
            logger.warning(f"Unknown archetype '{archetype}' at slide {idx}; falling back to chapter divider.")
            build_chapter_divider_slide(
                self.prs,
                self.theme,
                tracker=cfg.get("tracker") or f"SECTION {idx:02d}",
                title=cfg.get("title", f"Slide {idx}"),
                subtitle=cfg.get("subtitle"),
                current_idx=idx,
                total_slides=total,
            )

    def update_pagination(self) -> None:
        """
        Post-processes all slides to synchronize bottom footer pagination ('02 / 36').
        Preserves existing font styling, size, boldness, and color.
        Cover slide (Slide 1) strictly has no footer or pagination.
        """
        total_slides = len(self.prs.slides)
        for s_idx, slide in enumerate(self.prs.slides, start=1):
            if s_idx == 1:
                continue
            for shape in slide.shapes:
                if not getattr(shape, "has_text_frame", False) or not shape.has_text_frame:
                    continue
                try:
                    if getattr(shape, "top", None) is not None and shape.top < Inches(6.8):
                        continue
                except Exception:
                    pass
                for paragraph in shape.text_frame.paragraphs:
                    text_clean = paragraph.text.strip()
                    if PAGE_REGEX.match(text_clean):
                        new_page_str = f"{s_idx:02d} / {total_slides:02d}"
                        if paragraph.runs:
                            r0 = paragraph.runs[0]
                            font_name = r0.font.name
                            font_size = r0.font.size
                            font_bold = r0.font.bold
                            font_color = None
                            try:
                                if r0.font.color and getattr(r0.font.color, "type", None) == 1:
                                    font_color = r0.font.color.rgb
                            except (AttributeError, ValueError):
                                font_color = None
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

    def _strip_all_shadows(self) -> None:
        """Enforce Zero Drop Shadows across every vector shape (recursing into groups) prior to save."""
        def _walk_strip(shapes) -> None:
            for sh in shapes:
                if getattr(sh, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
                    _walk_strip(sh.shapes)
                    continue
                if getattr(sh, "shape_type", None) != MSO_SHAPE_TYPE.PICTURE:
                    strip_shape_shadows(sh)

        for slide in self.prs.slides:
            _walk_strip(slide.shapes)

    def save(
        self,
        output_path: Union[str, Path],
        engagement_context: Optional[EngagementContext] = None,
    ) -> Path:
        """Saves presentation deck to target path after synchronizing pagination, stripping shadows, and substituting slugs."""
        self.update_pagination()
        self._strip_all_shadows()
        if engagement_context is None:
            engagement_context = EngagementContext.default_ngl()
        substitute_slugs_in_presentation(self.prs, engagement_context)

        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(p))
        logger.info(f"Successfully saved pitch deck to {p}")
        return p
