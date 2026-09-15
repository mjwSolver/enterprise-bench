"""
Executive Presentation Generator for Project XYZ with Enhanced Visuals.
Generates C-level consulting deck with stock photography and branded vector icons
while leaving original deck files untouched.
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from src.ppt_engine.theme_engine import get_theme
from src.ppt_engine.icon_engine import get_brand_icon
from src.ppt_engine.image_engine import frame_slide_image
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
ASSETS_IMG_DIR = Path("assets/images")
ASSETS_ICON_DIR = Path("assets/icons/lucide")


def ensure_assets():
    """Ensure all stock photos and icons are prepared."""
    ASSETS_IMG_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_ICON_DIR.mkdir(parents=True, exist_ok=True)

    # Icons
    icons = [
        ("lucide:dollar-sign", "#0284C7"),
        ("lucide:target", "#0D9488"),
        ("lucide:zap", "#F59E0B"),
        ("lucide:shield-check", "#10B981"),
        ("lucide:activity", "#0284C7"),
        ("lucide:database", "#0D9488"),
        ("lucide:server", "#6366F1"),
        ("lucide:sparkles", "#8B5CF6"),
        ("lucide:radio", "#0284C7"),
        ("lucide:lock", "#10B981"),
        ("lucide:flag", "#0284C7"),
        ("lucide:layers", "#0D9488"),
        ("lucide:cpu", "#F59E0B"),
        ("lucide:award", "#10B981"),
        ("lucide:building-2", "#475569"),
        ("lucide:calendar", "#475569"),
        ("lucide:check-circle", "#10B981"),
    ]
    for ident, color in icons:
        get_brand_icon(ident, brand_color=color, size=256)

    # Process authentic stock photo from Wikimedia Commons for Cover Slide
    stock_raw = ASSETS_IMG_DIR / "network_aisle_stock.jpg"
    hero_framed = ASSETS_IMG_DIR / "datacenter_stock_hero.png"
    if stock_raw.exists() and not hero_framed.exists():
        from PIL import Image
        im = Image.open(stock_raw)
        max_w = 1600
        if im.size[0] > max_w:
            new_h = int(im.size[1] * (max_w / im.size[0]))
            im = im.resize((max_w, new_h), Image.Resampling.LANCZOS)
            opt_path = ASSETS_IMG_DIR / "network_aisle_1600.jpg"
            im.save(opt_path, quality=92)
            source_for_framing = opt_path
        else:
            source_for_framing = stock_raw

        frame_slide_image(
            source_for_framing,
            aspect_ratio="4:3",
            corner_radius=18,
            border_width=2,
            border_color="#0284C7",
            shadow=True,
            shadow_blur=16,
            output_path=hero_framed,
        )


def build_enhanced_cover_slide(prs: Presentation, theme, title: str, subtitle: str, client: str, vendor: str, date_str: str):
    slide = add_slide_with_background(prs, theme)

    # Left accent vertical bar
    accent_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.8), Inches(1.5), Inches(0.14), Inches(4.9)
    )
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = theme.get_rgb("accent")
    accent_bar.line.fill.background()

    # Left Column: Category tracker
    tb_cat = slide.shapes.add_textbox(Inches(1.15), Inches(1.5), Inches(6.1), Inches(0.35))
    tf_cat = tb_cat.text_frame
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = "ENTERPRISE TRANSFORMATION BLUEPRINT  |  PROJECT XYZ"
    p_cat.font.name = theme.font_family_header
    p_cat.font.size = Pt(10.5)
    p_cat.font.bold = True
    p_cat.font.color.rgb = theme.get_rgb("accent")

    # Main Title (sized to fit cleanly in 3 lines without overlap)
    tb_title = slide.shapes.add_textbox(Inches(1.15), Inches(1.95), Inches(6.1), Inches(1.65))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.name = theme.font_family_header
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = theme.get_rgb("primary")

    # Subtitle
    tb_sub = slide.shapes.add_textbox(Inches(1.15), Inches(3.7), Inches(6.1), Inches(0.85))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = subtitle
    p_sub.font.name = theme.font_family
    p_sub.font.size = Pt(11.5)
    p_sub.font.color.rgb = theme.get_rgb("secondary")

    # Subtle baseline hairline separator (AGENTS.md clean typographic cover architecture)
    hairline = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.15), Inches(4.75), Inches(6.0), Inches(0.015)
    )
    hairline.fill.solid()
    hairline.fill.fore_color.rgb = theme.get_rgb("border")
    hairline.line.fill.background()

    # Typographic Multi-Column Metadata directly on slide background (Zero boxed cards)
    meta_y = Inches(4.9)
    col1_x = Inches(1.15)
    col_w = Inches(2.85)

    # Column 1: Client Metadata
    tb_m1 = slide.shapes.add_textbox(col1_x, meta_y, col_w, Inches(1.4))
    tf_m1 = tb_m1.text_frame
    tf_m1.word_wrap = True
    
    p1_lbl = tf_m1.paragraphs[0]
    p1_lbl.text = "PREPARED FOR:"
    p1_lbl.font.name = theme.font_family_header
    p1_lbl.font.size = Pt(8.0)
    p1_lbl.font.bold = True
    p1_lbl.font.color.rgb = theme.get_rgb("muted")

    p1_val = tf_m1.add_paragraph()
    p1_val.text = client
    p1_val.font.name = theme.font_family_header
    p1_val.font.size = Pt(10.0)
    p1_val.font.bold = True
    p1_val.font.color.rgb = theme.get_rgb("primary")
    p1_val.space_before = Pt(2)

    p1_sub = tf_m1.add_paragraph()
    p1_sub.text = "Enterprise Data & Architecture Division"
    p1_sub.font.name = theme.font_family
    p1_sub.font.size = Pt(8.5)
    p1_sub.font.color.rgb = theme.get_rgb("secondary")
    p1_sub.space_before = Pt(2)

    # Column 2: Engagement Partner & Version Metadata
    col2_x = Inches(4.25)
    tb_m2 = slide.shapes.add_textbox(col2_x, meta_y, col_w, Inches(1.4))
    tf_m2 = tb_m2.text_frame
    tf_m2.word_wrap = True

    p2_lbl = tf_m2.paragraphs[0]
    p2_lbl.text = "ENGAGEMENT LEAD:"
    p2_lbl.font.name = theme.font_family_header
    p2_lbl.font.size = Pt(8.0)
    p2_lbl.font.bold = True
    p2_lbl.font.color.rgb = theme.get_rgb("muted")

    p2_val = tf_m2.add_paragraph()
    p2_val.text = vendor
    p2_val.font.name = theme.font_family_header
    p2_val.font.size = Pt(10.0)
    p2_val.font.bold = True
    p2_val.font.color.rgb = theme.get_rgb("primary")
    p2_val.space_before = Pt(2)

    p2_sub = tf_m2.add_paragraph()
    p2_sub.text = f"CONFIDENTIAL • VER 1.0 • {date_str.upper()}"
    p2_sub.font.name = theme.font_family
    p2_sub.font.size = Pt(8.0)
    p2_sub.font.color.rgb = theme.get_rgb("secondary")
    p2_sub.space_before = Pt(2)

    # Right Column: Authentic Internet Stock Photography Hero Card
    stock_img_path = ASSETS_IMG_DIR / "datacenter_stock_hero.png"
    if not stock_img_path.exists():
        stock_img_path = ASSETS_IMG_DIR / "datacenter_aisle_framed.png"

    hero_x = Inches(7.5)
    hero_y = Inches(1.5)
    hero_w = Inches(5.03)
    hero_h = Inches(4.9)

    if stock_img_path.exists():
        slide.shapes.add_picture(str(stock_img_path), hero_x, hero_y, width=hero_w, height=hero_h)

        # Bottom floating telemetry caption bar over real stock photo
        cap_h = Inches(0.80)
        cap_y = hero_y + hero_h - cap_h - Inches(0.20)
        cap_x = hero_x + Inches(0.2)
        cap_w = hero_w - Inches(0.4)

        cap_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cap_x, cap_y, cap_w, cap_h)
        cap_card.fill.solid()
        cap_card.fill.fore_color.rgb = RGBColor(15, 23, 42)  # Dark slate pill
        cap_card.line.color.rgb = theme.get_rgb("accent")
        cap_card.line.width = Pt(1.0)

        cap_tb = slide.shapes.add_textbox(cap_x + Inches(0.15), cap_y + Inches(0.08), cap_w - Inches(0.3), cap_h - Inches(0.16))
        cap_tf = cap_tb.text_frame
        cap_tf.word_wrap = True
        cap_tf.margin_left = cap_tf.margin_right = cap_tf.margin_top = cap_tf.margin_bottom = 0
        p_c1 = cap_tf.paragraphs[0]
        p_c1.text = "REAL-WORLD INFRASTRUCTURE: ENTERPRISE DATA CENTER"
        p_c1.font.name = theme.font_family_header
        p_c1.font.size = Pt(8.5)
        p_c1.font.bold = True
        p_c1.font.color.rgb = RGBColor(56, 189, 248)  # Bright cyan

        p_c2 = cap_tf.add_paragraph()
        p_c2.text = "Stock Photo: Open Aisle Server Corridor (Wikimedia Commons / Public Domain)"
        p_c2.font.name = theme.font_family
        p_c2.font.size = Pt(7.5)
        p_c2.font.color.rgb = RGBColor(226, 232, 240)
        p_c2.space_before = Pt(2)

    # Note: Cover slide strictly omits footer divider bar and pagination per AGENTS.md rules
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


def build_enhanced_architecture_slide(prs: Presentation, theme, current_idx=4, total_slides=6):
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
    
    img_path = DIAGRAM_DIR / "01_ingestion_streaming.png"
    if not img_path.exists():
        img_path = ASSETS_IMG_DIR / "datacenter_stock.jpg"

    if img_path.exists():
        pad_x = Inches(0.2)
        pad_y = Inches(0.2)
        avail_w = diagram_w - (pad_x * 2)
        avail_h = diagram_h - (pad_y * 2)
        fit_w, fit_h = fit_image_within_bounds(img_path, avail_w, avail_h)
        offset_x = diagram_x + pad_x + (avail_w - fit_w) / 2
        offset_y = diagram_y + pad_y + (avail_h - fit_h) / 2
        slide.shapes.add_picture(str(img_path), offset_x, offset_y, width=fit_w, height=fit_h)

    # Right Container: 3 Key Architecture Takeaway Cards with Branded Icons
    right_x = Inches(8.3)
    right_w = Inches(4.23)
    card_h = Inches(1.55)
    gap_y = Inches(0.22)

    takeaways = [
        (
            "1. Event Ingress & Buffer",
            "Apache Kafka (MSK 3-AZ) handles 15,000+ msgs/sec from 450+ retail POS terminals and mobile app webhooks with zero packet loss.",
            "accent",
            ASSETS_ICON_DIR / "radio_0284C7.png"
        ),
        (
            "2. Medallion Quality Gates",
            "dbt Core enforces 140+ schema assertions across Bronze, Silver, and Gold marts, guaranteeing clean single-source-of-truth customer data.",
            "accent_teal",
            ASSETS_ICON_DIR / "shield-check_10B981.png"
        ),
        (
            "3. Zero-Trust API Mesh",
            "FastAPI microservices cached via Amazon ElastiCache (Redis) serve executive dashboards in sub-85ms with Okta OAuth2 authentication.",
            "success",
            ASSETS_ICON_DIR / "lock_10B981.png"
        ),
    ]

    for idx, (head, desc, acc_key, icon_p) in enumerate(takeaways):
        cy = diagram_y + idx * (card_h + gap_y)
        c = add_card(slide, theme, right_x, cy, right_w, card_h, bg_color=theme.get_rgb("surface"), force_rectangle=True)
        
        # Left accent stripe
        st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x, cy, Inches(0.12), card_h)
        st.fill.solid()
        st.fill.fore_color.rgb = theme.get_rgb(acc_key)
        st.line.fill.background()

        # Icon if available
        icon_w = Inches(0.0)
        if icon_p.exists():
            slide.shapes.add_picture(
                str(icon_p),
                right_x + Inches(0.22),
                cy + Inches(0.16),
                width=Inches(0.36),
                height=Inches(0.36)
            )
            icon_w = Inches(0.44)

        tb = slide.shapes.add_textbox(right_x + Inches(0.22) + icon_w, cy + Inches(0.12), right_w - Inches(0.35) - icon_w, card_h - Inches(0.24))
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


def build_enhanced_governance_slide(prs: Presentation, theme, current_idx=6, total_slides=6):
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
            ASSETS_ICON_DIR / "flag_0284C7.png",
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
            ASSETS_ICON_DIR / "layers_0D9488.png",
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
            ASSETS_ICON_DIR / "cpu_F59E0B.png",
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
            ASSETS_ICON_DIR / "award_10B981.png",
            [
                "Production Cutover Rundown",
                "Admin & User Runbooks",
                "BAST Milestone 2 Sign-off",
                "90-Day Warranty Transition"
            ]
        ),
    ]

    for idx, (st_tag, st_title, badge_txt, b_bg, b_txt, icon_p, items) in enumerate(stages):
        cx = col_x + idx * (col_w + gap_x)
        add_card(slide, theme, cx, col_y, col_w, col_h, bg_color=theme.get_rgb("surface"), has_top_stripe=True)

        # Top stripe
        st = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, col_y, col_w, Inches(0.08))
        st.fill.solid()
        st.fill.fore_color.rgb = theme.get_rgb("accent")
        st.line.fill.background()

        # Stage Icon
        icon_off = Inches(0.0)
        if icon_p.exists():
            slide.shapes.add_picture(str(icon_p), cx + Inches(0.2), col_y + Inches(0.18), width=Inches(0.38), height=Inches(0.38))
            icon_off = Inches(0.46)

        # Text box
        tb = slide.shapes.add_textbox(cx + Inches(0.2) + icon_off, col_y + Inches(0.16), col_w - Inches(0.35) - icon_off, Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = st_tag
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(8.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = theme.get_rgb("accent")

        p_t = tf.add_paragraph()
        p_t.text = st_title
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(11.5)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")
        p_t.space_before = Pt(2)

        # Status badge line & deliverables
        d_tb = slide.shapes.add_textbox(cx + Inches(0.2), col_y + Inches(1.15), col_w - Inches(0.4), col_h - Inches(1.3))
        d_tf = d_tb.text_frame
        d_tf.word_wrap = True

        p_badge = d_tf.paragraphs[0]
        p_badge.text = f"STATUS: [{badge_txt}]"
        p_badge.font.name = theme.font_family_header
        p_badge.font.size = Pt(8.5)
        p_badge.font.bold = True
        p_badge.font.color.rgb = theme.get_rgb(b_txt)
        p_badge.space_after = Pt(10)

        p_del = d_tf.add_paragraph()
        p_del.text = "CORE DELIVERABLES:"
        p_del.font.name = theme.font_family_header
        p_del.font.size = Pt(8.0)
        p_del.font.bold = True
        p_del.font.color.rgb = theme.get_rgb("muted")
        p_del.space_after = Pt(4)

        for item in items:
            pb = d_tf.add_paragraph()
            pb.text = f"✓ {item}"
            pb.font.name = theme.font_family
            pb.font.size = Pt(8.5)
            pb.font.color.rgb = theme.get_rgb("secondary")
            pb.space_before = Pt(2)

    add_slide_footer(slide, theme, current_idx=current_idx, total_slides=total_slides)
    return slide


def generate_enhanced_deck(theme_name: str = "snowblue", filename: str = "01_Project_XYZ_Executive_Strategy_Deck_Enhanced_Visuals.pptx"):
    ensure_assets()
    theme = get_theme(theme_name)
    prs = create_presentation(theme)

    # 1. Slide 1: Cover Slide with Stock Photo Hero Visual
    build_enhanced_cover_slide(
        prs, theme,
        title="Project XYZ: Omni-Channel Real-Time Analytics & Customer 360 Platform",
        subtitle="Executive Architecture Blueprint, Modernization Strategy & Implementation Roadmap",
        client="Apex Global Retailers Corp.",
        vendor="Antigravity Strategic Solutions",
        date_str="September 2026"
    )

    # 2. Slide 2: BCG 3-Horizon Strategy with Vector Icons
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
        icon_path=ASSETS_ICON_DIR / "activity_0284C7.png",
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
        icon_path=ASSETS_ICON_DIR / "database_0D9488.png",
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
        icon_path=ASSETS_ICON_DIR / "sparkles_8B5CF6.png",
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

    # 3. Slide 3: McKinsey MECE Strategy Cascade with Vector Icons
    p1 = StrategyPillarData(
        pillar_number="PILLAR 01",
        title="Unified Streaming Backbone",
        target_kpi="Ingestion SLA: 99.99%",
        proof_points=[
            ("Kafka Event Hub", "Decouples point-of-sale terminals and web stores from core databases."),
            ("Zero Event Loss", "Guaranteed at-least-once delivery with write-ahead persistent logs."),
            ("Auto-Scaling Micro-Batches", "Absorbs 5x Black Friday traffic spikes without latency spikes.")
        ],
        accent_key="accent",
        icon_path=ASSETS_ICON_DIR / "activity_0284C7.png",
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
        accent_key="accent_teal",
        icon_path=ASSETS_ICON_DIR / "database_0D9488.png",
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
        accent_key="success",
        icon_path=ASSETS_ICON_DIR / "server_6366F1.png",
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

    # 4. Slide 4: Target Solution Architecture with diagram & takeaway icons
    build_enhanced_architecture_slide(prs, theme, current_idx=4, total_slides=6)

    # 5. Slide 5: Executive Balanced Scorecard KPI Matrix with Quadrant Icons
    q1 = ScorecardQuadrantData(
        quadrant_title="1. FINANCIAL EXCELLENCE",
        tagline="TCO Reduction & Asset Efficiency",
        metrics=[
            ScorecardMetric(label="Cloud Infrastructure TCO", value="-38%", status="ON TRACK", description="Consolidation of legacy on-prem licensing"),
            ScorecardMetric(label="Inventory Holding Cost Avoidance", value="$1.8M", status="EXCEEDED", description="Accurate stock forecasting avoids stockouts"),
        ],
        icon_path=ASSETS_ICON_DIR / "dollar-sign_0284C7.png",
    )
    q2 = ScorecardQuadrantData(
        quadrant_title="2. CUSTOMER CONVERSION",
        tagline="Omni-Channel Experience & Latency",
        metrics=[
            ScorecardMetric(label="Serving API Availability", value="99.98%", status="ON TRACK", description="Target: 99.95% multi-AZ availability"),
            ScorecardMetric(label="Personalized Recommendation CTR", value="+32%", status="EXCEEDED", description="Sub-second basket cross-sell response"),
        ],
        icon_path=ASSETS_ICON_DIR / "target_0D9488.png",
    )
    q3 = ScorecardQuadrantData(
        quadrant_title="3. OPERATIONAL AGILITY",
        tagline="Pipeline Velocity & Store Coverage",
        metrics=[
            ScorecardMetric(label="Physical Stores Connected", value="450+", status="COMPLETED", description="All tier-1 and tier-2 locations online"),
            ScorecardMetric(label="End-to-End Processing Latency", value="< 12 min", status="ON TRACK", description="From register swipe to executive BI"),
        ],
        icon_path=ASSETS_ICON_DIR / "zap_F59E0B.png",
    )
    q4 = ScorecardQuadrantData(
        quadrant_title="4. GOVERNANCE & RESILIENCE",
        tagline="Zero-Trust Security & Compliance",
        metrics=[
            ScorecardMetric(label="SOC-2 / ISO-27001 Readiness", value="100%", status="COMPLIANT", description="Full role-based row-level encryption"),
            ScorecardMetric(label="Incident Recovery MTTR", value="< 15 min", status="ON TRACK", description="Automated Kafka consumer group failover"),
        ],
        icon_path=ASSETS_ICON_DIR / "shield-check_10B981.png",
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

    # 6. Slide 6: Engagement Governance & Milestones with Stage Gate Icons
    build_enhanced_governance_slide(prs, theme, current_idx=6, total_slides=6)

    out_file = OUTPUT_DIR / filename
    prs.save(str(out_file))
    print(f"Generated Enhanced Presentation Deck with Stock Photo & Icons: {out_file}")
    return out_file


if __name__ == "__main__":
    generate_enhanced_deck()
