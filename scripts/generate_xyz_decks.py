"""
Executive Presentation Generator for Project XYZ
Generates C-level consulting decks adhering to McKinsey/BCG frameworks
using the Enterprise Bench PPT Engine.
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from src.ppt_engine.theme_engine import get_theme, hex_to_rgb
from src.ppt_engine.consulting_archetypes import (
    create_presentation,
    add_slide_with_background,
    add_slide_header,
    add_card,
    add_slide_footer,
    build_bcg_3_horizon_slide,
    build_mckinsey_cascade_slide,
    build_balanced_scorecard_slide,
    HorizonColumnData,
    StrategyPillarData,
    ScorecardQuadrantData,
    ScorecardMetric,
)

OUTPUT_DIR = Path("output/proj-xyz/presentations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DIAGRAM_DIR = Path("output/proj-xyz/diagrams")
ASSETS_DIR = Path("output/proj-xyz/assets")


def build_cover_slide(prs: Presentation, theme, title: str, subtitle: str, client: str, vendor: str, date_str: str):
    slide = add_slide_with_background(prs, theme)
    
    # Left accent band framing title block cleanly
    accent_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.8), Inches(1.8), Inches(0.12), Inches(2.5)
    )
    accent_bar.shadow.inherit = False
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = theme.get_rgb("accent")
    accent_bar.line.fill.background()

    # Category tracker
    tb_cat = slide.shapes.add_textbox(Inches(1.15), Inches(1.8), Inches(11.0), Inches(0.35))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = "ENTERPRISE TRANSFORMATION BLUEPRINT  |  PROJECT XYZ"
    p_cat.font.name = theme.font_family_header
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = theme.get_rgb("accent")

    # Main Title & Subtitle (Unified Frame for Consistent Spacing)
    tb_header = slide.shapes.add_textbox(Inches(1.15), Inches(2.25), Inches(11.0), Inches(2.3))
    tf_h = tb_header.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0

    p_title = tf_h.paragraphs[0]
    p_title.text = title
    p_title.font.name = theme.font_family_header
    p_title.font.size = Pt(28)
    p_title.font.bold = True
    p_title.font.color.rgb = theme.get_rgb("primary")

    p_sub = tf_h.add_paragraph()
    p_sub.text = subtitle
    p_sub.font.name = theme.font_family
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = theme.get_rgb("secondary")
    p_sub.space_before = Pt(12)

    # Subtle structural baseline divider (no awkward bordered block)
    divider = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.15), Inches(4.9), Inches(11.0), Inches(0.015)
    )
    divider.shadow.inherit = False
    divider.fill.solid()
    divider.fill.fore_color.rgb = theme.get_rgb("border")
    divider.line.fill.background()

    # Typographic Metadata Column 1: Client Sponsor
    tb_c1 = slide.shapes.add_textbox(Inches(1.15), Inches(5.2), Inches(5.0), Inches(1.2))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    tf_c1.margin_left = tf_c1.margin_right = tf_c1.margin_top = tf_c1.margin_bottom = 0

    p1_label = tf_c1.paragraphs[0]
    p1_label.text = "PREPARED FOR"
    p1_label.font.name = theme.font_family_header
    p1_label.font.size = Pt(8.5)
    p1_label.font.bold = True
    p1_label.font.color.rgb = theme.get_rgb("accent")

    p1_val = tf_c1.add_paragraph()
    p1_val.text = client
    p1_val.font.name = theme.font_family_header
    p1_val.font.size = Pt(13)
    p1_val.font.bold = True
    p1_val.font.color.rgb = theme.get_rgb("primary")
    p1_val.space_before = Pt(2)

    p1_sub = tf_c1.add_paragraph()
    p1_sub.text = "Enterprise Architecture & Transformation Steering Committee"
    p1_sub.font.name = theme.font_family
    p1_sub.font.size = Pt(9.5)
    p1_sub.font.color.rgb = theme.get_rgb("secondary")
    p1_sub.space_before = Pt(2)

    # Typographic Metadata Column 2: Engagement Partner & Date
    tb_c2 = slide.shapes.add_textbox(Inches(6.8), Inches(5.2), Inches(5.3), Inches(1.2))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    tf_c2.margin_left = tf_c2.margin_right = tf_c2.margin_top = tf_c2.margin_bottom = 0

    p2_label = tf_c2.paragraphs[0]
    p2_label.text = "ENGAGEMENT PARTNER"
    p2_label.font.name = theme.font_family_header
    p2_label.font.size = Pt(8.5)
    p2_label.font.bold = True
    p2_label.font.color.rgb = theme.get_rgb("accent")

    p2_val = tf_c2.add_paragraph()
    p2_val.text = vendor
    p2_val.font.name = theme.font_family_header
    p2_val.font.size = Pt(13)
    p2_val.font.bold = True
    p2_val.font.color.rgb = theme.get_rgb("primary")
    p2_val.space_before = Pt(2)

    p2_sub = tf_c2.add_paragraph()
    p2_sub.text = f"Date: {date_str}  |  Confidential & Proprietary"
    p2_sub.font.name = theme.font_family
    p2_sub.font.size = Pt(9.5)
    p2_sub.font.color.rgb = theme.get_rgb("secondary")
    p2_sub.space_before = Pt(2)

    return slide


from PIL import Image


def fit_image_within_bounds(img_path: Path, max_w: float, max_h: float) -> tuple[float, float]:
    """Calculate aspect-preserving dimensions that strictly fit inside max_w x max_h."""
    with Image.open(img_path) as img:
        w_px, h_px = img.size
    aspect = w_px / h_px
    if (max_w / max_h) > aspect:
        return max_h * aspect, max_h
    else:
        return max_w, max_w / aspect


def build_architecture_slide(prs: Presentation, theme, current_idx=4, total_slides=6):
    slide = add_slide_with_background(prs, theme)
    add_slide_header(
        slide, theme,
        tracker="TARGET SOLUTION ARCHITECTURE  |  HIGH-CONCURRENCY MESH",
        action_title="Decoupled Medallion Architecture Delivers Sub-Second Ingestion & Real-Time Decisioning",
        subtitle="Multi-AZ AWS event ingestion streaming into Snowflake Medallion lakehouse and low-latency FastAPI services."
    )

    # Left Container: Diagram Image (Width 7.2", Height 5.1")
    diagram_x = Inches(0.8)
    diagram_y = Inches(1.72)
    diagram_w = Inches(7.2)
    diagram_h = Inches(5.1)

    add_card(slide, theme, diagram_x, diagram_y, diagram_w, diagram_h, bg_color=theme.get_rgb("surface"))
    
    # Try embedding the generated diagram PNG
    img_path = DIAGRAM_DIR / "01_ingestion_streaming.png"
    if not img_path.exists():
        img_path = ASSETS_DIR / "xyz_hero_visual.jpg"

    if img_path.exists():
        pad_x = Inches(0.2)
        pad_y = Inches(0.2)
        avail_w = diagram_w - (pad_x * 2)
        avail_h = diagram_h - (pad_y * 2)
        fit_w, fit_h = fit_image_within_bounds(img_path, avail_w, avail_h)
        offset_x = diagram_x + pad_x + (avail_w - fit_w) / 2
        offset_y = diagram_y + pad_y + (avail_h - fit_h) / 2
        slide.shapes.add_picture(str(img_path), offset_x, offset_y, width=fit_w, height=fit_h)

    # Right Container: 3 Key Architecture Takeaway Cards
    right_x = Inches(8.3)
    right_w = Inches(4.23)
    card_h = Inches(1.55)
    gap_y = Inches(0.22)

    takeaways = [
        (
            "1. Event Ingress & Buffer",
            "Apache Kafka (MSK 3-AZ) handles 15,000+ msgs/sec from 450+ retail POS terminals and mobile app webhooks with zero packet loss.",
            "accent"
        ),
        (
            "2. Medallion Quality Gates",
            "dbt Core enforces 140+ schema assertions across Bronze, Silver, and Gold marts, guaranteeing clean single-source-of-truth customer data.",
            "accent_teal"
        ),
        (
            "3. Zero-Trust API Mesh",
            "FastAPI microservices cached via Amazon ElastiCache (Redis) serve executive dashboards in sub-85ms with Okta OAuth2 authentication.",
            "success"
        ),
    ]

    for idx, (head, desc, acc_key) in enumerate(takeaways):
        cy = diagram_y + idx * (card_h + gap_y)
        c = add_card(slide, theme, right_x, cy, right_w, card_h, bg_color=theme.get_rgb("surface"), force_rectangle=True)
        
        # Accent bar
        st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x, cy, Inches(0.12), card_h)
        st.shadow.inherit = False
        st.fill.solid()
        st.fill.fore_color.rgb = theme.get_rgb(acc_key)
        st.line.fill.background()

        tb = slide.shapes.add_textbox(right_x + Inches(0.25), cy + Inches(0.15), right_w - Inches(0.4), card_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p_h = tf.paragraphs[0]
        p_h.text = head
        p_h.font.name = theme.font_family_header
        p_h.font.size = Pt(11)
        p_h.font.bold = True
        p_h.font.color.rgb = theme.get_rgb("primary")

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.name = theme.font_family
        p_d.font.size = Pt(9.0)
        p_d.font.color.rgb = theme.get_rgb("secondary")
        p_d.space_before = Pt(4)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)
    return slide


def build_governance_slide(prs: Presentation, theme, current_idx=6, total_slides=6):
    slide = add_slide_with_background(prs, theme)
    add_slide_header(
        slide, theme,
        tracker="ENGAGEMENT GOVERNANCE & STAGE-GATE MILESTONES",
        action_title="Disciplined Stage-Gate Milestones Enforce Quality, Security & Contractual BAST Sign-Off",
        subtitle="Rigorous stage transitions ensure client stakeholders review deliverables prior to downstream phase commitment."
    )

    col_x = Inches(0.8)
    col_w = Inches(2.72)
    gap_x = Inches(0.28)
    col_y = Inches(1.72)
    col_h = Inches(5.1)

    stages = [
        (
            "STAGE 0 & 1",
            "Initiation & Foundation",
            "COMPLETED",
            "badge_green_fill", "badge_green_text",
            [
                "Project Charter signed",
                "PKS Master Agreement signed",
                "Stakeholder Register & RACI",
                "Baseline Schedule locked"
            ]
        ),
        (
            "STAGE 2: GATE 1",
            "Architecture Blueprint",
            "IN SIGN-OFF",
            "badge_blue_fill", "badge_blue_text",
            [
                "Functional Specification (FSD)",
                "Solution Architecture Blueprint",
                "Cloud Sizing & TCO Model",
                "BAST Milestone 1 Execution"
            ]
        ),
        (
            "STAGE 3 & 4",
            "Sprints & SIT Verification",
            "PLANNED",
            "badge_amber_fill", "badge_amber_text",
            [
                "Bi-weekly sprint releases",
                "Technical Specification (TSD)",
                "Backend & Frontend SIT scripts",
                "Zero Sev-1 / Sev-2 defects"
            ]
        ),
        (
            "STAGE 5: GATE 2",
            "Go-Live & Handover",
            "PLANNED",
            "badge_blue_fill", "badge_blue_text",
            [
                "Production Cutover Rundown",
                "Admin & User Runbooks",
                "BAST Milestone 2 Sign-off",
                "90-Day Warranty Transition"
            ]
        ),
    ]

    for idx, (st_tag, st_title, badge_txt, b_bg, b_txt, items) in enumerate(stages):
        cx = col_x + idx * (col_w + gap_x)
        add_card(slide, theme, cx, col_y, col_w, col_h, bg_color=theme.get_rgb("surface"), has_top_stripe=True)

        # Top stripe
        st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, col_y, col_w, Inches(0.08))
        st.shadow.inherit = False
        st.fill.solid()
        st.fill.fore_color.rgb = theme.get_rgb("accent")
        st.line.fill.background()

        # Text box
        tb = slide.shapes.add_textbox(cx + Inches(0.2), col_y + Inches(0.18), col_w - Inches(0.4), col_h - Inches(0.35))
        tf = tb.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = st_tag
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(9.0)
        p_tag.font.bold = True
        p_tag.font.color.rgb = theme.get_rgb("accent")

        p_t = tf.add_paragraph()
        p_t.text = st_title
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(12.0)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")
        p_t.space_before = Pt(2)

        # Status badge line
        p_badge = tf.add_paragraph()
        p_badge.text = f"STATUS: [{badge_txt}]"
        p_badge.font.name = theme.font_family_header
        p_badge.font.size = Pt(8.5)
        p_badge.font.bold = True
        p_badge.font.color.rgb = theme.get_rgb(b_txt)
        p_badge.space_before = Pt(6)
        p_badge.space_after = Pt(12)

        p_del = tf.add_paragraph()
        p_del.text = "CORE DELIVERABLES:"
        p_del.font.name = theme.font_family_header
        p_del.font.size = Pt(8.0)
        p_del.font.bold = True
        p_del.font.color.rgb = theme.get_rgb("muted")
        p_del.space_after = Pt(4)

        for item in items:
            pb = tf.add_paragraph()
            pb.text = f"✓ {item}"
            pb.font.name = theme.font_family
            pb.font.size = Pt(8.5)
            pb.font.color.rgb = theme.get_rgb("secondary")
            pb.space_before = Pt(2)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)
    return slide


def generate_executive_deck(theme_name: str = "snowblue", filename: str = "01_Project_XYZ_Executive_Strategy_Deck.pptx"):
    theme = get_theme(theme_name)
    prs = create_presentation(theme)

    # Slide 1: Cover Slide
    build_cover_slide(
        prs, theme,
        title="Project XYZ: Omni-Channel Real-Time Analytics & Customer 360 Platform",
        subtitle="Executive Architecture Blueprint, Modernization Strategy & Implementation Roadmap",
        client="Apex Global Retailers Corp.",
        vendor="Antigravity Strategic Solutions",
        date_str="September 2026"
    )

    # Slide 2: BCG 3-Horizon Strategy
    h1 = HorizonColumnData(
        horizon_tag="HORIZON 1  |  0-3 MONTHS",
        title="Streaming Ingress & Mesh Foundation",
        strategic_focus="Unify transaction feeds across 450+ stores into a zero-loss cloud landing zone.",
        metric_highlight="< 500ms",
        metric_label="Peak Ingestion Latency Target",
        initiatives=[
            "Deploy MSK Kafka 3-AZ broker cluster",
            "Establish AWS Landing Zone with encrypted S3",
            "Provision Snowflake Enterprise Virtual Warehouses",
            "Formulate FSD, TSD & BAST Gate 1 Milestone"
        ],
        status_tag="IN EXECUTION",
        status_bg_key="badge_blue_fill",
        status_text_key="badge_blue_text",
    )
    h2 = HorizonColumnData(
        horizon_tag="HORIZON 2  |  3-6 MONTHS",
        title="Customer 360 & Real-Time Marts",
        strategic_focus="Construct Silver & Gold medallion marts to drive omni-channel stock & personalized promotions.",
        metric_highlight="100%",
        metric_label="Automated Data Quality Assertions",
        initiatives=[
            "Implement dbt Core transformation pipelines",
            "Build Customer 360 unified identity graphs",
            "Deploy Redis caching tier for high concurrency",
            "Execute Backend & Frontend SIT test suites"
        ],
        status_tag="PLANNED",
        status_bg_key="badge_amber_fill",
        status_text_key="badge_amber_text",
    )
    h3 = HorizonColumnData(
        horizon_tag="HORIZON 3  |  6-12 MONTHS",
        title="Predictive AI & Autonomous Supply",
        strategic_focus="Empower store managers with edge ML inventory reordering and hyper-personalized clienteling.",
        metric_highlight="+22%",
        metric_label="Incremental Basket Size Uplift",
        initiatives=[
            "Deploy real-time recommendation inference engine",
            "Automate dynamic markdown & stock re-allocation",
            "Extend self-healing data pipeline anomaly guards",
            "Conduct full project closeout & value realization"
        ],
        status_tag="DESIGN",
        status_bg_key="badge_green_fill",
        status_text_key="badge_green_text",
    )
    build_bcg_3_horizon_slide(
        prs, theme,
        tracker="STRATEGIC ROADMAP  |  BCG 3-HORIZON FRAMEWORK",
        action_title="Phased Sequencing Unlocks Rapid Near-Term Ingestion while Scaling Customer 360 Value",
        subtitle="Three-phase transformation balances immediate data unification with long-term predictive retail intelligence.",
        horizons=[h1, h2, h3],
        current_idx=2,
        total_slides=6
    )

    # Slide 3: McKinsey MECE Strategy Cascade
    p1 = StrategyPillarData(
        pillar_number="PILLAR 01",
        title="Unified Streaming Backbone",
        target_kpi="Ingestion SLA: 99.99%",
        proof_points=[
            ("Kafka Event Hub", "Decouples point-of-sale terminals and web stores from core databases."),
            ("Zero Event Loss", "Guaranteed at-least-once delivery with write-ahead persistent logs."),
            ("Auto-Scaling Micro-Batches", "Absorbs 5x Black Friday traffic spikes without latency spikes.")
        ],
        accent_key="accent"
    )
    p2 = StrategyPillarData(
        pillar_number="PILLAR 02",
        title="Auditable Medallion Data Mesh",
        target_kpi="Data Latency: Sub-15 Mins",
        proof_points=[
            ("Bronze-Silver-Gold", "Clear segregation of raw ingestion, conformed entities, and analytical marts."),
            ("Automated Data Contracts", "dbt schema tests halt corrupt payloads before ingestion into production."),
            ("Full CDC Lineage", "Complete historical replay capability for transactional auditing.")
        ],
        accent_key="accent_teal"
    )
    p3 = StrategyPillarData(
        pillar_number="PILLAR 03",
        title="High-Concurrency Serving API",
        target_kpi="Response MTTR: < 85ms",
        proof_points=[
            ("ElastiCache Redis Caching", "Sub-10ms response times for hot customer profile queries."),
            ("FastAPI Microservices", "Containerized asynchronous endpoints with automated horizontal pod scaling."),
            ("Zero-Trust Security Mesh", "OAuth2 / JWT token validation and role-based row-level security.")
        ],
        accent_key="success"
    )
    build_mckinsey_cascade_slide(
        prs, theme,
        tracker="STRATEGIC PILLARS  |  MCKINSEY MECE ARCHITECTURE CASCADE",
        action_title="Three MECE Pillars Resolve Data Fragmentation and Elevate Customer Conversion",
        subtitle="Mutually exclusive architectural domains eliminate technical bottlenecks across ingress, storage, and egress.",
        hypothesis_statement="CORE HYPOTHESIS: Decoupling retail transaction streams from monolith ERPs into a cloud-native Medallion Lakehouse will lower operational TCO by 38% while enabling sub-second customer engagement across all digital touchpoints.",
        pillars=[p1, p2, p3],
        synthesis_conclusion="STRATEGIC MANDATE: Enforce strict API contracts at Ingestion (Pillar 1) to protect downstream Lakehouse integrity and ensure predictable serving SLAs for front-line store personnel.",
        current_idx=3,
        total_slides=6
    )

    # Slide 4: Target Solution Architecture
    build_architecture_slide(prs, theme, current_idx=4, total_slides=6)

    # Slide 5: Executive Balanced Scorecard KPI Matrix
    q1 = ScorecardQuadrantData(
        quadrant_title="1. FINANCIAL EXCELLENCE",
        tagline="TCO Reduction & Asset Efficiency",
        metrics=[
            ScorecardMetric(label="Cloud Infrastructure TCO", value="-38%", status="ON TRACK", description="Consolidation of legacy on-prem licensing"),
            ScorecardMetric(label="Inventory Holding Cost Avoidance", value="$1.8M", status="EXCEEDED", description="Accurate stock forecasting avoids stockouts"),
        ]
    )
    q2 = ScorecardQuadrantData(
        quadrant_title="2. CUSTOMER CONVERSION",
        tagline="Omni-Channel Experience & Latency",
        metrics=[
            ScorecardMetric(label="Serving API Availability", value="99.98%", status="ON TRACK", description="Target: 99.95% multi-AZ availability"),
            ScorecardMetric(label="Personalized Recommendation CTR", value="+32%", status="EXCEEDED", description="Sub-second basket cross-sell response"),
        ]
    )
    q3 = ScorecardQuadrantData(
        quadrant_title="3. OPERATIONAL AGILITY",
        tagline="Pipeline Velocity & Store Coverage",
        metrics=[
            ScorecardMetric(label="Physical Stores Connected", value="450+", status="COMPLETED", description="All tier-1 and tier-2 locations online"),
            ScorecardMetric(label="End-to-End Processing Latency", value="< 12 min", status="ON TRACK", description="From register swipe to executive BI"),
        ]
    )
    q4 = ScorecardQuadrantData(
        quadrant_title="4. GOVERNANCE & RESILIENCE",
        tagline="Zero-Trust Security & Compliance",
        metrics=[
            ScorecardMetric(label="SOC-2 / ISO-27001 Readiness", value="100%", status="COMPLIANT", description="Full role-based row-level encryption"),
            ScorecardMetric(label="Incident Recovery MTTR", value="< 15 min", status="ON TRACK", description="Automated Kafka consumer group failover"),
        ]
    )
    build_balanced_scorecard_slide(
        prs, theme,
        tracker="EXECUTIVE KPI BENCHMARKS  |  BALANCED SCORECARD",
        action_title="Balanced Scorecard Tracks Cross-Functional Alpha Across Financial & Technical Vectors",
        subtitle="Quantitative measurement guarantees that cloud investments directly manifest in customer satisfaction and EBITDA.",
        quadrants=[q1, q2, q3, q4],
        current_idx=5,
        total_slides=6
    )

    # Slide 6: Engagement Governance & Milestones
    build_governance_slide(prs, theme, current_idx=6, total_slides=6)

    out_file = OUTPUT_DIR / filename
    prs.save(str(out_file))
    print(f"Generated Executive Strategy Deck ({theme_name}): {out_file}")
    return out_file


def generate_kickoff_deck():
    theme = get_theme("brickred")
    prs = create_presentation(theme)

    # Slide 1: Cover
    build_cover_slide(
        prs, theme,
        title="Project XYZ: Engagement Kick-Off & Implementation Mobilization",
        subtitle="Stakeholder Alignment, Team Organization, Baseline Milestones & Governance Protocol",
        client="Apex Global Retailers Corp.",
        vendor="Antigravity Strategic Solutions",
        date_str="September 2026"
    )

    # Slide 2: Governance Slide
    build_governance_slide(prs, theme, current_idx=2, total_slides=3)

    # Slide 3: Scorecard Slide
    q1 = ScorecardQuadrantData(
        quadrant_title="1. SPRINT VELOCITY",
        tagline="Story Point Completion Rate",
        metrics=[
            ScorecardMetric(label="Sprint 1 Commitment", value="45 SP", status="COMMITTED", description="Core ingestion environment setup"),
            ScorecardMetric(label="Velocity Stability Target", value="95%", status="ON TRACK", description="Minimal scope deviation in sprints"),
        ]
    )
    q2 = ScorecardQuadrantData(
        quadrant_title="2. TECHNICAL READINESS",
        tagline="Environment & IAM Security",
        metrics=[
            ScorecardMetric(label="Cloud IAM Roles Provisioned", value="100%", status="COMPLETED", description="Cross-account Snowflake AWS role"),
            ScorecardMetric(label="VPC Peering Latency", value="< 2ms", status="EXCEEDED", description="Direct connect link established"),
        ]
    )
    q3 = ScorecardQuadrantData(
        quadrant_title="3. QUALITY & DEFECT DEFENSE",
        tagline="Zero-Defect Code Delivery",
        metrics=[
            ScorecardMetric(label="SIT Test Coverage", value="92%", status="TARGET", description="Backend pipelines & API unit logic"),
            ScorecardMetric(label="Critical Severity Defects", value="0", status="MAINTAINED", description="Strict zero Sev-1 / Sev-2 tolerance"),
        ]
    )
    q4 = ScorecardQuadrantData(
        quadrant_title="4. STAKEHOLDER SIGN-OFF",
        tagline="BAST Gate Sign-Off Cadence",
        metrics=[
            ScorecardMetric(label="Milestone 1 BAST Acceptance", value="Gate 1", status="SCHEDULED", description="Target sign-off: Oct 15, 2026"),
            ScorecardMetric(label="Milestone 2 BAST Acceptance", value="Gate 2", status="SCHEDULED", description="Final handover: Feb 26, 2027"),
        ]
    )
    build_balanced_scorecard_slide(
        prs, theme,
        tracker="DELIVERY GOVERNANCE BENCHMARKS",
        action_title="Mobilization Scorecard Establishes Operational Cadence for Sprint Execution",
        subtitle="Sprint commitments and milestone gating metrics reviewed bi-weekly with joint steering committee.",
        quadrants=[q1, q2, q3, q4],
        current_idx=3,
        total_slides=3
    )

    out_file = OUTPUT_DIR / "02_Project_XYZ_KickOff_Briefing.pptx"
    prs.save(str(out_file))
    print(f"Generated Kick-off Deck: {out_file}")


if __name__ == "__main__":
    generate_executive_deck("snowblue", "01_Project_XYZ_Executive_Strategy_Deck.pptx")
    generate_executive_deck("brickred", "01_Project_XYZ_Executive_Strategy_Deck_BrickRed.pptx")
    generate_kickoff_deck()
