"""
Verification Script for Slide Design Variety Archetypes
======================================================
Tests the newly implemented consulting slide archetypes:
  - build_cover_slide (Typographic metadata, zero boxed cards, dual branding lockup)
  - build_chevron_process_slide (Stepped horizontal chevrons, progressive saturation)
  - build_split_hero_slide (1/3 high-contrast stat callout + 2/3 unbordered narrative)
  - build_gap_analysis_slide (As-Is vs. To-Be comparative layout with transition levers)
"""

from pathlib import Path
from src.ppt_engine.consulting_archetypes import ConsultingDeckBuilder
from src.ppt_engine.theme_engine import get_theme


def main() -> None:
    output_dir = Path("output/verification_archetypes")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_pptx = output_dir / "consulting_archetypes_showcase.pptx"

    print("🚀 Initializing ConsultingDeckBuilder with 'metrodata' theme...")
    builder = ConsultingDeckBuilder(theme="metrodata")

    # 1. Executive Cover Slide
    print("  Adding Slide 1: Executive Cover Slide...")
    builder.add_cover_slide(
        title="Modern Data Platform & Cloud Analytics Architecture",
        subtitle="End-to-end modernization blueprint, lakehouse foundation, and phased execution roadmap.",
        client="PT Bank Central Asia Tbk",
        vendor="PT Mitra Integrasi Informatika",
        product="Snowflake AI Data Cloud",
        date_str="September 2026",
        tracker="ENTERPRISE TRANSFORMATION BLUEPRINT  |  PROJECT XYZ",
        client_sublabel="Enterprise Architecture & Data Governance Steering Committee",
        vendor_sublabel="BAS Division  |  Cloud & AI Modernization Practice",
    )

    # 2. De-Squared Chapter Divider Slide
    print("  Adding Slide 2: De-Squared Chapter Divider Slide...")
    builder.add_chapter_divider_slide(
        tracker="PHASE 01: STRATEGIC CONTEXT & DISCOVERY",
        title="Current-State Assessment & Gap Analysis",
        subtitle="Critical capability deficits, batch ETL bottlenecks, and target modernization levers.",
    )

    # 3. Gap Analysis Slide (As-Is vs To-Be)
    print("  Adding Slide 3: Architecture Gap Analysis Slide...")
    builder.add_gap_analysis_slide(
        tracker="Architecture Gap Analysis  |  Current vs. Target State",
        action_title="Modernization Closes Critical Gaps Between Legacy Constraints and Future Target State",
        subtitle="Systematic transformation resolves batch latency, data silos, and manual governance overhead.",
    )

    # 4. Stepped Process Chevron Flow Slide
    print("  Adding Slide 4: Stepped Process Chevron Flow Slide...")
    builder.add_chevron_process_slide(
        tracker="Execution Roadmap & Phased Progression",
        action_title="Phased Execution Roadmap Delivers Accelerated Value Across Four Controlled Horizons",
        subtitle="Sequential progression transitions foundation infrastructure into production analytics.",
    )

    # 5. Split-Hero Stat Callout Slide
    print("  Adding Slide 5: Split-Hero 1/3 Stat + 2/3 Narrative Slide...")
    builder.add_split_hero_slide(
        tracker="Executive Synthesis & Quantified ROI",
        action_title="Modern Data Architecture Unlocks High-Yield Operational Transformation",
        subtitle="Centralized lakehouse foundation drives immediate cost avoidance and predictive analytics velocity.",
        hero_stat="$14.8M",
        hero_stat_label="Annualized Business Impact",
        hero_stat_subtext="Projected 3-year cumulative ROI with 4.2x payback across supply chain and analytics operations.",
    )

    # 6. BCG 3-Horizon Slide
    print("  Adding Slide 6: BCG 3-Horizon Growth Slide...")
    builder.add_bcg_3_horizon_slide(
        tracker="Portfolio Modernization  |  BCG 3-Horizon Model",
        action_title="Balanced Portfolio Allocation Fuels Core Modernization while Incubating Future Engines",
        subtitle="Phased sequencing balances near-term cash generation with disruptive 3-5 year platform bets.",
    )

    # 7. Balanced Scorecard Slide
    print("  Adding Slide 7: Balanced Scorecard Slide...")
    builder.add_balanced_scorecard_slide(
        tracker="Executive Governance & Performance  |  Balanced Scorecard",
        action_title="Target Performance Exceeds Benchmark SLAs Across All Four Operational Dimensions",
        subtitle="Comprehensive KPI matrix tracking financial returns, customer value, process speed, and resilience.",
    )

    # Save presentation to both primary and versioned paths
    builder.save(out_pptx)
    out_pptx_v2 = output_dir / "consulting_archetypes_v2.pptx"
    builder.save(out_pptx_v2)
    print(f"✓ Showcase deck generated successfully: {out_pptx} and {out_pptx_v2} ({len(builder.prs.slides)} slides)")


if __name__ == "__main__":
    main()
