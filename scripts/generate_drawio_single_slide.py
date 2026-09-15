"""
Single-Slide Draw.io Hero Presentation Generator (Unconstrained Natural Aspect Ratio)
====================================================================================
Generates a dedicated PowerPoint presentation focusing exclusively on the 18pt
Draw.io architecture visualization.
Fixes the aspect ratio distortion:
- Eliminates forced height constraint on picture shape (preserves 100% native aspect ratio).
- Removes artificial square-like card containment around the flowchart.
- Places the flowchart directly on the slide canvas with natural proportional scaling.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from src.ppt_engine.consulting_archetypes import (
    add_card,
    add_slide_footer,
    add_slide_header,
    add_slide_with_background,
    create_presentation,
)
from src.ppt_engine.diagram_engine import DrawIOProject
from src.ppt_engine.theme_engine import get_theme


def generate_single_slide_deck() -> Path:
    proj_dir = Path("output/proj-xyz")
    diag_dir = proj_dir / "diagrams"
    pres_dir = proj_dir / "presentations"
    pres_dir.mkdir(parents=True, exist_ok=True)

    # 1. Author and Export Diagram with Columnar Architecture & Integrated Tech Logos
    diag_file = diag_dir / "04_security_governance_mesh.drawio"
    mermaid_code = """flowchart LR
    subgraph Sources["Zero-Trust Ingress"]
        POS["Store POS Terminals"]
        Mobile["Mobile App Clients"]
        WAF["AWS WAF Shield"]
    end
    subgraph Mesh["Security & Streaming Mesh"]
        Kafka["MSK Kafka Cluster"]
        Vault["Tokenization Vault"]
        Snowflake["Snowflake Lakehouse"]
    end
    subgraph Governance["Continuous Compliance"]
        Audit["Immutable Audit Logs"]
        dbt["dbt Data Contracts"]
        SOC2["SOC-2 & ISO Gating"]
    end
    POS --> WAF
    Mobile --> WAF
    WAF --> Kafka
    Kafka --> Vault
    Vault --> Snowflake
    Kafka --> Audit
    Snowflake --> dbt
    dbt --> SOC2"""

    node_icons = {
        "POS": {"icon": "assets/logos/pos_store.svg", "icon_color": "#0284C7"},
        "Mobile": {"icon": "assets/logos/mobile.svg", "icon_color": "#0284C7"},
        "WAF": {"icon": "assets/logos/aws.svg"},
        "Kafka": {"icon": "assets/logos/kafka.svg"},
        "Vault": {"icon": "assets/logos/vault.svg"},
        "Snowflake": {"icon": "assets/logos/snowflake.svg"},
        "Audit": {"icon": "assets/logos/amazons3.svg"},
        "dbt": {"icon": "assets/logos/dbt.svg"},
        "SOC2": {"icon": "assets/logos/soc2_badge.svg", "icon_color": "#10B981"},
    }

    proj = DrawIOProject()
    proj.add_mermaid_page(
        "Security & Governance Mesh",
        mermaid_code,
        theme="corporate_navy",
        font_size=20.0,
        node_icons=node_icons,
    )
    proj.save(diag_file)

    out_png = diag_dir / "04_security_governance_mesh_logos.png"
    out_svg = diag_dir / "04_security_governance_mesh_logos.svg"
    proj.export_page("Security & Governance Mesh", out_png, format="png", scale=3.0, font_size=20.0, transparent=True)
    proj.export_page("Security & Governance Mesh", out_svg, format="svg", font_size=20.0, transparent=True)

    # 2. Build Single-Slide Deck (Slide 1 is the Hero Architecture Slide)
    theme = get_theme("snowblue")
    prs = create_presentation(theme)
    slide = add_slide_with_background(prs, theme)

    # Header
    add_slide_header(
        slide,
        theme,
        tracker="SECURITY & DATA GOVERNANCE MESH  |  PROJECT XYZ",
        action_title="Zero-Trust Perimeter & Continuous Auditing Enforce SOC-2 Compliance Across 450+ Stores",
        subtitle="3-Tier enterprise topology: hardware-grade mTLS ingress, tokenized PII isolation vault, and automated dbt contracts.",
    )

    # Category Tracker Tag above Flowchart
    diag_tag_tb = slide.shapes.add_textbox(Inches(0.8), Inches(1.65), Inches(11.733), Inches(0.28))
    diag_tag_tf = diag_tag_tb.text_frame
    diag_tag_tf.margin_left = diag_tag_tf.margin_right = diag_tag_tf.margin_top = diag_tag_tf.margin_bottom = 0
    p_tag = diag_tag_tf.paragraphs[0]
    p_tag.text = "TARGET ARCHITECTURE TOPOLOGY (DRAW.IO ENGINE — 3-TIER COLUMNAR MESH WITH INTEGRATED TECH LOGOS)"
    p_tag.font.name = theme.font_family_header
    p_tag.font.size = Pt(9.0)
    p_tag.font.bold = True
    p_tag.font.color.rgb = theme.get_rgb("accent")

    # 3. Flowchart Image: Placed directly on canvas with NATURAL ASPECT RATIO
    # Only 'width' is specified. python-pptx computes 'height' preserving exact pixel geometry with 0% distortion.
    flowchart_y = Inches(1.98)
    flowchart_w = Inches(11.733)
    pic = slide.shapes.add_picture(
        str(out_png),
        Inches(0.8),
        flowchart_y,
        width=flowchart_w,
    )
    pic_h = pic.height
    pic_bottom = flowchart_y + pic_h

    # 4. Bottom Row: 3 Executive KPI Summary Cards
    # Positioned comfortably below the natural bottom of the flowchart
    bottom_y = pic_bottom + Inches(0.18)
    bottom_h = Inches(6.92) - bottom_y
    card_gap = Inches(0.28)
    card_w = (flowchart_w - (2 * card_gap)) / 3

    takeaway_cards = [
        {
            "tag": "TIER 01: ZERO-TRUST INGRESS",
            "title": "Mutual TLS & WAF Shield",
            "metric": "100% mTLS",
            "accent": "accent",
            "summary": "Hardware-attested TPM chips across 450+ POS registers & Okta OAuth JWT for mobile clients.",
        },
        {
            "tag": "TIER 02: DATA PRIVACY & ISOLATION",
            "title": "Tokenized PII Vault",
            "metric": "AES-256 HSM",
            "accent": "accent_teal",
            "summary": "Pre-lakehouse tokenization vault with 24h key rotation and Snowflake row-level dynamic masking.",
        },
        {
            "tag": "TIER 03: CONTINUOUS AUDITING",
            "title": "Immutable Compliance Ledger",
            "metric": "SOC-2 Ready",
            "accent": "success",
            "summary": "Write-once S3 Glacier compliance audit logging and 140+ automated dbt schema contract test assertions.",
        },
    ]

    for idx, cdata in enumerate(takeaway_cards):
        cx = Inches(0.8) + idx * (card_w + card_gap)
        card_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, bottom_y, card_w, bottom_h)
        card_shape.fill.solid()
        card_shape.fill.fore_color.rgb = theme.get_rgb("surface")
        card_shape.line.color.rgb = theme.get_rgb("border")
        card_shape.line.width = Pt(1)

        # Top Accent Stripe (Sharp rectangle aligned with container)
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, bottom_y, card_w, Inches(0.06))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = theme.get_rgb(cdata["accent"])
        stripe.line.fill.background()

        # Content Text Box
        tb = slide.shapes.add_textbox(cx + Inches(0.16), bottom_y + Inches(0.10), card_w - Inches(0.32), bottom_h - Inches(0.16))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p_tag = tf.paragraphs[0]
        p_tag.text = cdata["tag"]
        p_tag.font.name = theme.font_family_header
        p_tag.font.size = Pt(8.0)
        p_tag.font.bold = True
        p_tag.font.color.rgb = theme.get_rgb(cdata["accent"])

        p_t = tf.add_paragraph()
        p_t.text = f"{cdata['title']}  •  [{cdata['metric']}]"
        p_t.font.name = theme.font_family_header
        p_t.font.size = Pt(9.5)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.get_rgb("primary")
        p_t.space_before = Pt(2)

        p_desc = tf.add_paragraph()
        p_desc.text = cdata["summary"]
        p_desc.font.name = theme.font_family
        p_desc.font.size = Pt(8.0)
        p_desc.font.color.rgb = theme.get_rgb("secondary")
        p_desc.space_before = Pt(2)

    # Footer (01 / 01)
    add_slide_footer(slide, theme, current_idx=1, total_slides=1)

    out_deck = pres_dir / "Project_XYZ_DrawIO_Review.pptx"
    prs.save(str(out_deck))
    print(f"Generated columnar review presentation: {out_deck}")
    print(f"  Flowchart geometry: left=0.80\", top={flowchart_y.inches:.2f}\", width={flowchart_w.inches:.2f}\", height={pic_h.inches:.2f}\"")
    print(f"  Bottom cards geometry: top={bottom_y / 914400.0:.2f}\", height={bottom_h / 914400.0:.2f}\"")
    return out_deck


if __name__ == "__main__":
    generate_single_slide_deck()
