"""
Multi-Theme Branded Presentation Deck Generator
===============================================
Generates two complete enterprise consulting presentation decks:
  1. Snow Blue Enterprise (`project_outputs/snowblue_deck/`)
     - Topic: Next-Generation Cloud Mesh & Distributed Data Ingestion Platform
     - Visuals: Cool arctic palette, sky/cyan accents, multi-region Draw.io topology
  2. Brick Red Strategic (`project_outputs/brickred_deck/`)
     - Topic: Cyber Resilience, Zero-Trust Threat Intelligence & SOC-2 Governance
     - Visuals: Warm crimson/terracotta palette, warm amber accents, cryptographic pipeline

Both decks undergo:
  - Vector Draw.io diagram compilation from Mermaid syntax.
  - Dynamic brand SVG icon retrieval and tinting.
  - Headless multi-backend slide export to high-resolution PNGs.
  - Algorithmic QA validation across all 5 quality checks.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from typing import Any, Dict, List, Optional, Tuple

import yaml
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# Local engines and modules
from src.ppt_engine.diagram_engine import DiagramEngine
from src.ppt_engine.icon_engine import IconEngine
from src.ppt_engine.image_engine import ImageEngine, frame_slide_image
from src.ppt_engine.slide_exporter import export_deck_to_images
from src.ppt_engine.slide_validator import validate_presentation


# ============================================================================
# 1. Theme Configuration Class
# ============================================================================

class ThemeConfig:
    """Encapsulates theme colors, typography, and geometry."""

    def __init__(self, theme_name: str) -> None:
        self.theme_name = theme_name
        self.yaml_path = _ROOT_DIR / "presets" / "themes" / f"{theme_name}.yaml"
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"Theme file not found: {self.yaml_path}")

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

        pal = self.data.get("palette", {})
        self.canvas_bg = self._hex_to_rgb(pal.get("canvas_bg", "#F8FAFC"))
        self.card_bg = self._hex_to_rgb(pal.get("card_bg", "#FFFFFF"))
        self.card_muted = self._hex_to_rgb(pal.get("card_muted", "#F1F5F9"))
        self.border_light = self._hex_to_rgb(pal.get("border_light", "#CBD5E1"))
        self.border_accent = self._hex_to_rgb(pal.get("border_accent", "#7DD3FC"))

        self.text_primary = self._hex_to_rgb(pal.get("text_primary", "#0F172A"))
        self.text_secondary = self._hex_to_rgb(pal.get("text_secondary", "#475569"))
        self.text_muted = self._hex_to_rgb(pal.get("text_muted", "#94A3B8"))

        self.brand_primary_hex = pal.get("brand_primary", "#0284C7")
        self.brand_primary = self._hex_to_rgb(self.brand_primary_hex)
        self.brand_secondary_hex = pal.get("brand_secondary", "#0EA5E9")
        self.brand_secondary = self._hex_to_rgb(self.brand_secondary_hex)
        self.brand_accent_hex = pal.get("brand_accent", "#38BDF8")
        self.brand_accent = self._hex_to_rgb(self.brand_accent_hex)

        self.success_hex = pal.get("success", "#10B981")
        self.success = self._hex_to_rgb(self.success_hex)
        self.warning_hex = pal.get("warning", "#F59E0B")
        self.warning = self._hex_to_rgb(self.warning_hex)

        self.badge_primary_fill = self._hex_to_rgb(pal.get("badge_primary_fill", "#EFF6FF"))
        self.badge_success_fill = self._hex_to_rgb(pal.get("badge_success_fill", "#ECFDF5"))
        self.badge_warning_fill = self._hex_to_rgb(pal.get("badge_warning_fill", "#FEF3C7"))

        diag = self.data.get("diagram", {})
        self.diagram_theme_name = diag.get("theme_name", "corporate_navy")

    def _hex_to_rgb(self, hex_str: str) -> RGBColor:
        h = hex_str.strip().lstrip("#")
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ============================================================================
# 2. Slide Layout Helpers
# ============================================================================

def create_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_slide_base(prs: Presentation, theme: ThemeConfig) -> Any:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = theme.canvas_bg
    bg.line.fill.background()
    return slide


def add_header(
    slide: Any,
    theme: ThemeConfig,
    tracker: str,
    title: str,
    subtitle: Optional[str] = None,
) -> None:
    # 1. Breadcrumb Tracker
    tb_tr = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.733), Inches(0.28))
    tf_tr = tb_tr.text_frame
    tf_tr.word_wrap = True
    tf_tr.margin_left = tf_tr.margin_right = tf_tr.margin_top = tf_tr.margin_bottom = 0
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = tracker.upper()
    p_tr.font.size = Pt(9.5)
    p_tr.font.bold = True
    p_tr.font.color.rgb = theme.brand_primary

    # 2. Action Headline & Subtitle (Unified Frame for Consistent Spacing)
    tb_header = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.95))
    tf_h = tb_header.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_right = tf_h.margin_top = tf_h.margin_bottom = 0
    p_t = tf_h.paragraphs[0]
    p_t.text = title
    p_t.font.size = Pt(20)
    p_t.font.bold = True
    p_t.font.color.rgb = theme.text_primary

    # 3. Subtitle (Flowed via paragraph offset)
    if subtitle:
        p_s = tf_h.add_paragraph()
        p_s.text = subtitle
        p_s.font.size = Pt(11)
        p_s.font.color.rgb = theme.text_secondary
        p_s.space_before = Pt(10)


def add_card_box(
    slide: Any,
    theme: ThemeConfig,
    left: Inches,
    top: Inches,
    width: Inches,
    height: Inches,
    bg_color: Optional[RGBColor] = None,
    border_color: Optional[RGBColor] = None,
    border_width: Pt = Pt(1),
    has_top_stripe: bool = False,
) -> Any:
    # GEOMETRY INTEGRITY: Overlapping top stripes require crisp 90-degree rectangle
    shape_type = MSO_SHAPE.RECTANGLE if has_top_stripe else MSO_SHAPE.ROUNDED_RECTANGLE
    card = slide.shapes.add_shape(shape_type, left, top, width, height)
    card.shadow.inherit = False
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color or theme.card_bg
    if border_color or theme.border_light:
        card.line.color.rgb = border_color or theme.border_light
        card.line.width = border_width
    else:
        card.line.fill.background()
    return card


def add_footer(slide: Any, theme: ThemeConfig, current_idx: int, total_slides: int = 3, dept: str = "Enterprise Architecture Group") -> None:
    # Divider line
    div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.90), Inches(11.733), Inches(0.015))
    div.shadow.inherit = False
    div.fill.solid()
    div.fill.fore_color.rgb = theme.border_light
    div.line.fill.background()

    # Left metadata
    f_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.96), Inches(8.0), Inches(0.25))
    tf_f = f_box.text_frame
    tf_f.word_wrap = True
    tf_f.margin_left = tf_f.margin_right = tf_f.margin_top = tf_f.margin_bottom = 0
    p_f = tf_f.paragraphs[0]
    p_f.text = f"{dept}  |  Confidential & Proprietary Strategy"
    p_f.font.size = Pt(8.5)
    p_f.font.color.rgb = theme.text_muted

    # Right page numbering
    p_box = slide.shapes.add_textbox(Inches(10.533), Inches(6.96), Inches(2.0), Inches(0.25))
    tf_p = p_box.text_frame
    tf_p.word_wrap = True
    tf_p.margin_left = tf_p.margin_right = tf_p.margin_top = tf_p.margin_bottom = 0
    p_p = tf_p.paragraphs[0]
    p_p.text = f"{current_idx:02d} / {total_slides:02d}"
    p_p.font.size = Pt(8.5)
    p_p.font.bold = True
    p_p.alignment = PP_ALIGN.RIGHT
    p_p.font.color.rgb = theme.text_muted


# ============================================================================
# 3. Slide Builders for Snow Blue & Brick Red Decks
# ============================================================================

def build_snowblue_deck(project_dir: Path, theme: ThemeConfig, assets: Dict[str, Path]) -> Path:
    prs = create_deck()

    # Slide 1: System Cloud Topology & SLA Acceleration
    s1 = add_slide_base(prs, theme)
    add_header(
        s1,
        theme,
        tracker="Cloud Architecture & Mesh Modernization  |  Executive Strategy",
        title="Decoupled Multi-Region Cloud Fabric Boosts Deployment Velocity by 4.5x",
        subtitle="Zero-downtime microservices platform unifying legacy databases with scalable event streams.",
    )
    # Row 1: KPI Cards
    kpis = [
        {"icon": assets["icon_shield"], "val": "99.999%", "lbl": "Target SLA Uptime", "sub": "Multi-region failover", "col": theme.brand_primary},
        {"icon": assets["icon_zap"], "val": "4.5x", "lbl": "Deployment Velocity", "sub": "Automated blue-green pipelines", "col": theme.success},
        {"icon": assets["icon_trend"], "val": "-64%", "lbl": "Infra TCO Reduction", "sub": "Dynamic autoscale node pools", "col": theme.brand_secondary},
    ]
    card_w = Inches(3.72)
    card_gap = Inches(0.28)
    for i, k in enumerate(kpis):
        cx = Inches(0.8) + i * (card_w + card_gap)
        add_card_box(s1, theme, cx, Inches(1.72), card_w, Inches(1.10))
        s1.shapes.add_picture(str(k["icon"]), cx + Inches(0.18), Inches(1.92), width=Inches(0.70), height=Inches(0.70))
        tb = s1.shapes.add_textbox(cx + Inches(0.98), Inches(1.85), card_w - Inches(1.05), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p1 = tf.paragraphs[0]
        p1.text = k["val"]
        p1.font.size = Pt(17)
        p1.font.bold = True
        p1.font.color.rgb = k["col"]
        p2 = tf.add_paragraph()
        p2.text = k["lbl"]
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = theme.text_primary
        p3 = tf.add_paragraph()
        p3.text = k["sub"]
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = theme.text_secondary

    # Row 2: Diagram (Left) + Framed Card (Right)
    r2_y = Inches(2.98)
    r2_h = Inches(3.78)
    diag_w = Inches(7.50)
    add_card_box(s1, theme, Inches(0.8), r2_y, diag_w, r2_h)
    tb_dh = s1.shapes.add_textbox(Inches(1.05), r2_y + Inches(0.18), diag_w - Inches(0.5), Inches(0.35))
    tf_dh = tb_dh.text_frame
    tf_dh.margin_left = tf_dh.margin_right = tf_dh.margin_top = tf_dh.margin_bottom = 0
    p_dh = tf_dh.paragraphs[0]
    p_dh.text = "TARGET SYSTEM ARCHITECTURE (DRAW.IO ENGINE)"
    p_dh.font.size = Pt(10)
    p_dh.font.bold = True
    p_dh.font.color.rgb = theme.brand_primary

    s1.shapes.add_picture(str(assets["diag_arch"]), Inches(1.0), r2_y + Inches(0.55), width=diag_w - Inches(0.4), height=r2_h - Inches(0.70))

    rx = Inches(8.55)
    rw = Inches(3.98)
    add_card_box(s1, theme, rx, r2_y, rw, r2_h)
    s1.shapes.add_picture(str(assets["framed_hero"]), rx + Inches(0.20), r2_y + Inches(0.18), width=rw - Inches(0.40), height=Inches(1.50))
    tb_st = s1.shapes.add_textbox(rx + Inches(0.25), r2_y + Inches(1.78), rw - Inches(0.50), r2_h - Inches(1.88))
    tf_st = tb_st.text_frame
    tf_st.word_wrap = True
    tf_st.margin_left = tf_st.margin_right = tf_st.margin_top = tf_st.margin_bottom = 0
    p_st = tf_st.paragraphs[0]
    p_st.text = "Strategic Migration Pillars"
    p_st.font.size = Pt(12)
    p_st.font.bold = True
    p_st.font.color.rgb = theme.text_primary
    p_st.space_after = Pt(4)

    for item_t, item_d in [
        ("Zero-Downtime Cutover", "Continuous dual-write CDC pipeline keeps legacy & cloud DBs synchronized."),
        ("Microsegmentation", "Granular service-mesh policies isolate blast radiuses across all VPCs."),
        ("Telemetry Mesh", "Distributed tracing triggers automated node failover in < 2 seconds."),
    ]:
        p = tf_st.add_paragraph()
        p.text = f"• {item_t}: "
        p.font.bold = True
        p.font.size = Pt(9.5)
        p.font.color.rgb = theme.brand_primary
        run = p.add_run()
        run.text = item_d
        run.font.bold = False
        run.font.color.rgb = theme.text_secondary
        p.space_after = Pt(3)

    add_footer(s1, theme, 1, 3, "Cloud Strategy Group")

    # Slide 2: Real-time Ingestion Pipeline
    s2 = add_slide_base(prs, theme)
    add_header(
        s2,
        theme,
        tracker="Data Platform & Cyber Resilience  |  Real-Time Streaming Engine",
        title="Sub-45ms Real-Time Ingestion Handles 1.2B Daily Distributed Events",
        subtitle="Continuous cryptographic validation, schema registry enforcement, and tiered lakehouse analytics.",
    )
    # Top horizontal diagram
    add_card_box(s2, theme, Inches(0.8), Inches(1.72), Inches(11.733), Inches(2.65))
    tb_dt = s2.shapes.add_textbox(Inches(1.05), Inches(1.87), Inches(11.2), Inches(0.35))
    tf_dt = tb_dt.text_frame
    tf_dt.margin_left = tf_dt.margin_right = tf_dt.margin_top = tf_dt.margin_bottom = 0
    p_dt = tf_dt.paragraphs[0]
    p_dt.text = "REAL-TIME STREAMING & VALIDATION PIPELINE (DRAW.IO HORIZONTAL FLOW)"
    p_dt.font.size = Pt(10)
    p_dt.font.bold = True
    p_dt.font.color.rgb = theme.brand_primary

    s2.shapes.add_picture(str(assets["diag_pipeline"]), Inches(1.0), Inches(2.20), width=Inches(11.333), height=Inches(2.05))

    # Bottom 3 metric cards
    c_data = [
        {"icon": assets["icon_lock"], "tag": "SECURITY & ATTESTATION", "metric": "100% mTLS", "title": "Zero-Trust Perimeter", "bullets": ["SPIFFE/SPIRE identity tokens", "Automated 24h cert rotation", "Zero exposed control ports"], "col": theme.brand_primary},
        {"icon": assets["icon_activity"], "tag": "STREAM PERFORMANCE", "metric": "< 45ms", "title": "Sub-Second P99 Latency", "bullets": ["Kafka partitioned clustering", "Dynamic self-throttling buffers", "Sub-10ms schema validation"], "col": theme.brand_secondary},
        {"icon": assets["icon_server"], "tag": "LAKEHOUSE SCALE", "metric": "1.2B Evts/Day", "title": "Elastic Tiered Storage", "bullets": ["Columnar Parquet cold storage", "Real-time vector index embedding", "Zero loss with 3x replica"], "col": theme.brand_accent},
    ]
    for i, cd in enumerate(c_data):
        cx = Inches(0.8) + i * (card_w + card_gap)
        add_card_box(s2, theme, cx, Inches(4.52), card_w, Inches(2.28), has_top_stripe=True)
        st = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, Inches(4.52), card_w, Inches(0.08))
        st.shadow.inherit = False
        st.fill.solid()
        st.fill.fore_color.rgb = cd["col"]
        st.line.fill.background()

        s2.shapes.add_picture(str(cd["icon"]), cx + Inches(0.18), Inches(4.70), width=Inches(0.55), height=Inches(0.55))
        cb = s2.shapes.add_textbox(cx + Inches(0.85), Inches(4.68), card_w - Inches(0.95), Inches(2.0))
        c_tf = cb.text_frame
        c_tf.word_wrap = True
        c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0
        p_top = c_tf.paragraphs[0]
        p_top.text = f"{cd['metric']}  |  {cd['tag']}"
        p_top.font.size = Pt(9)
        p_top.font.bold = True
        p_top.font.color.rgb = cd["col"]
        p_t = c_tf.add_paragraph()
        p_t.text = cd["title"]
        p_t.font.size = Pt(11.5)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.text_primary
        p_t.space_before = Pt(2)
        p_t.space_after = Pt(3)
        for b in cd["bullets"]:
            p_b = c_tf.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.size = Pt(8.8)
            p_b.font.color.rgb = theme.text_secondary
            p_b.space_after = Pt(2)

    add_footer(s2, theme, 2, 3, "Cloud Strategy Group")

    # Slide 3: Roadmap & Phased Execution
    s3 = add_slide_base(prs, theme)
    add_header(
        s3,
        theme,
        tracker="Program Execution & Governance  |  Q3 Operational Roadmap",
        title="Gated Multi-Phase Rollout Concludes Global Cloud Migration in Q3",
        subtitle="Rigorous security gates, telemetry validation, and blue-green production cutovers ensuring zero disruption.",
    )
    # State diagram card
    add_card_box(s3, theme, Inches(0.8), Inches(1.72), Inches(11.733), Inches(1.70))
    tb_mh = s3.shapes.add_textbox(Inches(1.05), Inches(1.84), Inches(11.2), Inches(0.28))
    tf_mh = tb_mh.text_frame
    tf_mh.margin_left = tf_mh.margin_right = tf_mh.margin_top = tf_mh.margin_bottom = 0
    p_mh = tf_mh.paragraphs[0]
    p_mh.text = "PHASED STATE TRANSITION & GOVERNANCE GATES (DRAW.IO ENGINE)"
    p_mh.font.size = Pt(9.5)
    p_mh.font.bold = True
    p_mh.font.color.rgb = theme.brand_primary

    s3.shapes.add_picture(str(assets["diag_state"]), Inches(1.0), Inches(2.12), width=Inches(11.333), height=Inches(1.20))

    # 3 Phase Cards
    phases = [
        {"p": "PHASE 01  |  Q1-Q2", "st": "COMPLETED", "st_bg": theme.badge_success_fill, "st_col": theme.success, "icon": assets["icon_check"], "title": "Foundation & Core Mesh", "sum": "Multi-region VPC provisioning & identity federations.", "dels": ["Terraform IaC multi-region baseline", "SPIFFE/SPIRE zero-trust auth cluster", "Automated CI/CD security scanning gates", "Dual-write database CDC live"], "col": theme.success},
        {"p": "PHASE 02  |  Q2-Q3", "st": "IN PROGRESS", "st_bg": theme.badge_primary_fill, "st_col": theme.brand_primary, "icon": assets["icon_refresh"], "title": "Microservices Migration", "sum": "Decoupling tier-1 monolithic services into K8s mesh.", "dels": ["Canary routing via Envoy API gateway", "Distributed OpenTelemetry tracing mesh", "Automated disaster recovery drills (RTO < 60s)", "Streaming pipeline certification"], "col": theme.brand_primary},
        {"p": "PHASE 03  |  Q3-Q4", "st": "UPCOMING", "st_bg": theme.badge_warning_fill, "st_col": theme.warning, "icon": assets["icon_flag"], "title": "Global GA & Cutover", "sum": "Complete legacy decommission & 100% cloud traffic.", "dels": ["Final DNS blue-green global traffic swing", "Legacy on-prem hardware deprecation", "SOC-2 Type II audit sign-off", "Enterprise 24/7 SRE NOC handover"], "col": theme.warning},
    ]
    for i, ph in enumerate(phases):
        cx = Inches(0.8) + i * (card_w + card_gap)
        add_card_box(s3, theme, cx, Inches(3.58), card_w, Inches(3.22), has_top_stripe=True)
        st = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, Inches(3.58), card_w, Inches(0.08))
        st.shadow.inherit = False
        st.fill.solid()
        st.fill.fore_color.rgb = ph["col"]
        st.line.fill.background()

        pill = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + card_w - Inches(1.35), Inches(3.76), Inches(1.15), Inches(0.28))
        pill.shadow.inherit = False
        pill.fill.solid()
        pill.fill.fore_color.rgb = ph["st_bg"]
        pill.line.color.rgb = ph["st_col"]
        pill.line.width = Pt(0.75)
        ptf = pill.text_frame
        ptf.margin_left = ptf.margin_right = ptf.margin_top = ptf.margin_bottom = 0
        pp = ptf.paragraphs[0]
        pp.text = ph["st"]
        pp.font.size = Pt(8)
        pp.font.bold = True
        pp.alignment = PP_ALIGN.CENTER
        pp.font.color.rgb = ph["st_col"]

        s3.shapes.add_picture(str(ph["icon"]), cx + Inches(0.20), Inches(3.76), width=Inches(0.48), height=Inches(0.48))
        htb = s3.shapes.add_textbox(cx + Inches(0.75), Inches(3.74), card_w - Inches(2.15), Inches(0.50))
        htf = htb.text_frame
        htf.word_wrap = True
        htf.margin_left = htf.margin_right = htf.margin_top = htf.margin_bottom = 0
        p_ph = htf.paragraphs[0]
        p_ph.text = ph["p"]
        p_ph.font.size = Pt(8.5)
        p_ph.font.bold = True
        p_ph.font.color.rgb = ph["col"]
        p_pt = htf.add_paragraph()
        p_pt.text = ph["title"]
        p_pt.font.size = Pt(11.5)
        p_pt.font.bold = True
        p_pt.font.color.rgb = theme.text_primary

        dtb = s3.shapes.add_textbox(cx + Inches(0.20), Inches(4.35), card_w - Inches(0.40), Inches(2.35))
        dtf = dtb.text_frame
        dtf.word_wrap = True
        dtf.margin_left = dtf.margin_right = dtf.margin_top = dtf.margin_bottom = 0
        psum = dtf.paragraphs[0]
        psum.text = ph["sum"]
        psum.font.size = Pt(9)
        psum.font.color.rgb = theme.text_secondary
        psum.space_after = Pt(4)

        pdh = dtf.add_paragraph()
        pdh.text = "KEY DELIVERABLES:"
        pdh.font.size = Pt(8)
        pdh.font.bold = True
        pdh.font.color.rgb = theme.text_muted
        pdh.space_after = Pt(2)

        for d in ph["dels"]:
            pd = dtf.add_paragraph()
            pd.text = f"• {d}"
            pd.font.size = Pt(8.8)
            pd.font.color.rgb = theme.text_primary
            pd.space_after = Pt(2)

    add_footer(s3, theme, 3, 3, "Cloud Strategy Group")

    out_path = project_dir / "presentation.pptx"
    prs.save(str(out_path))
    return out_path


def build_brickred_deck(project_dir: Path, theme: ThemeConfig, assets: Dict[str, Path]) -> Path:
    prs = create_deck()

    # Slide 1: Cyber Resilience & Threat Surface Reduction
    s1 = add_slide_base(prs, theme)
    add_header(
        s1,
        theme,
        tracker="Cyber Resilience & Threat Intelligence  |  Executive Strategy",
        title="Zero-Trust Cryptographic Mesh Reduces Enterprise Attack Surface by 87%",
        subtitle="Continuous identity attestation, automated anomaly quarantine, and sub-second blast radius isolation.",
    )
    # Row 1: KPI Cards
    kpis = [
        {"icon": assets["icon_shield"], "val": "87% Drop", "lbl": "Attack Surface Exposure", "sub": "Zero open management ports", "col": theme.brand_primary},
        {"icon": assets["icon_zap"], "val": "< 1.8s", "lbl": "Threat Containment MTTD", "sub": "Automated eBPF quarantine", "col": theme.brand_secondary},
        {"icon": assets["icon_trend"], "val": "100%", "lbl": "Cryptographic Attestation", "sub": "Hardware HSM enclave verification", "col": theme.brand_accent},
    ]
    card_w = Inches(3.72)
    card_gap = Inches(0.28)
    for i, k in enumerate(kpis):
        cx = Inches(0.8) + i * (card_w + card_gap)
        add_card_box(s1, theme, cx, Inches(1.72), card_w, Inches(1.10))
        s1.shapes.add_picture(str(k["icon"]), cx + Inches(0.18), Inches(1.92), width=Inches(0.70), height=Inches(0.70))
        tb = s1.shapes.add_textbox(cx + Inches(0.98), Inches(1.85), card_w - Inches(1.05), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p1 = tf.paragraphs[0]
        p1.text = k["val"]
        p1.font.size = Pt(17)
        p1.font.bold = True
        p1.font.color.rgb = k["col"]
        p2 = tf.add_paragraph()
        p2.text = k["lbl"]
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = theme.text_primary
        p3 = tf.add_paragraph()
        p3.text = k["sub"]
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = theme.text_secondary

    # Row 2: Diagram + Strategic Pillars
    r2_y = Inches(2.98)
    r2_h = Inches(3.78)
    diag_w = Inches(7.50)
    add_card_box(s1, theme, Inches(0.8), r2_y, diag_w, r2_h)
    tb_dh = s1.shapes.add_textbox(Inches(1.05), r2_y + Inches(0.18), diag_w - Inches(0.5), Inches(0.35))
    tf_dh = tb_dh.text_frame
    tf_dh.margin_left = tf_dh.margin_right = tf_dh.margin_top = tf_dh.margin_bottom = 0
    p_dh = tf_dh.paragraphs[0]
    p_dh.text = "ZERO-TRUST DEFENSE ARCHITECTURE (DRAW.IO ENGINE)"
    p_dh.font.size = Pt(10)
    p_dh.font.bold = True
    p_dh.font.color.rgb = theme.brand_primary

    s1.shapes.add_picture(str(assets["diag_arch"]), Inches(1.0), r2_y + Inches(0.55), width=diag_w - Inches(0.4), height=r2_h - Inches(0.70))

    rx = Inches(8.55)
    rw = Inches(3.98)
    add_card_box(s1, theme, rx, r2_y, rw, r2_h)
    s1.shapes.add_picture(str(assets["framed_hero"]), rx + Inches(0.20), r2_y + Inches(0.18), width=rw - Inches(0.40), height=Inches(1.50))
    tb_st = s1.shapes.add_textbox(rx + Inches(0.25), r2_y + Inches(1.78), rw - Inches(0.50), r2_h - Inches(1.88))
    tf_st = tb_st.text_frame
    tf_st.word_wrap = True
    tf_st.margin_left = tf_st.margin_right = tf_st.margin_top = tf_st.margin_bottom = 0
    p_st = tf_st.paragraphs[0]
    p_st.text = "Core Resilience Guarantees"
    p_st.font.size = Pt(12)
    p_st.font.bold = True
    p_st.font.color.rgb = theme.text_primary
    p_st.space_after = Pt(4)

    for item_t, item_d in [
        ("Continuous Validation", "SPIFFE/SPIRE short-lived tokens prevent credential replay attacks."),
        ("Micro-Quarantine", "Kernel-level eBPF firewalls isolate suspicious processes in real time."),
        ("Immutable Audit Trail", "Tamper-evident append-only ledger verifies SOC-2 compliance."),
    ]:
        p = tf_st.add_paragraph()
        p.text = f"• {item_t}: "
        p.font.bold = True
        p.font.size = Pt(9.5)
        p.font.color.rgb = theme.brand_primary
        run = p.add_run()
        run.text = item_d
        run.font.bold = False
        run.font.color.rgb = theme.text_secondary
        p.space_after = Pt(3)

    add_footer(s1, theme, 1, 3, "Cybersecurity Governance Group")

    # Slide 2: Cryptographic Ingestion & Threat Detection Flow
    s2 = add_slide_base(prs, theme)
    add_header(
        s2,
        theme,
        tracker="Threat Intelligence & Ingestion  |  Automated Policy Engine",
        title="Sub-10ms Behavioral Heuristics Stream Identifies Anomalous Payloads",
        subtitle="End-to-end mTLS encryption with hardware enclave attestation and distributed security orchestration.",
    )
    # Top horizontal diagram
    add_card_box(s2, theme, Inches(0.8), Inches(1.72), Inches(11.733), Inches(2.65))
    tb_dt = s2.shapes.add_textbox(Inches(1.05), Inches(1.87), Inches(11.2), Inches(0.35))
    tf_dt = tb_dt.text_frame
    tf_dt.margin_left = tf_dt.margin_right = tf_dt.margin_top = tf_dt.margin_bottom = 0
    p_dt = tf_dt.paragraphs[0]
    p_dt.text = "CONTINUOUS THREAT VERIFICATION PIPELINE (DRAW.IO HORIZONTAL FLOW)"
    p_dt.font.size = Pt(10)
    p_dt.font.bold = True
    p_dt.font.color.rgb = theme.brand_primary

    s2.shapes.add_picture(str(assets["diag_pipeline"]), Inches(1.0), Inches(2.20), width=Inches(11.333), height=Inches(2.05))

    # Bottom 3 metric cards
    c_data = [
        {"icon": assets["icon_lock"], "tag": "CRYPTO ATTESTATION", "metric": "FIPS 140-3", "title": "HSM Key Management", "bullets": ["Hardware security modules", "Zero plain-text in memory", "Automated enclave rotation"], "col": theme.brand_primary},
        {"icon": assets["icon_activity"], "tag": "HEURISTIC DETECTION", "metric": "< 10ms", "title": "Real-Time AI Anomaly Svc", "bullets": ["eBPF telemetry streaming", "Graph neural net classifiers", "Zero false-positive alarms"], "col": theme.brand_secondary},
        {"icon": assets["icon_server"], "tag": "AUDIT PERSISTENCE", "metric": "100% Immutable", "title": "Compliance Vault Ledger", "bullets": ["WORM compliant storage", "Cryptographic proof tree", "Real-time SOC-2 reporting"], "col": theme.brand_accent},
    ]
    for i, cd in enumerate(c_data):
        cx = Inches(0.8) + i * (card_w + card_gap)
        add_card_box(s2, theme, cx, Inches(4.52), card_w, Inches(2.28), has_top_stripe=True)
        st = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, Inches(4.52), card_w, Inches(0.08))
        st.shadow.inherit = False
        st.fill.solid()
        st.fill.fore_color.rgb = cd["col"]
        st.line.fill.background()

        s2.shapes.add_picture(str(cd["icon"]), cx + Inches(0.18), Inches(4.70), width=Inches(0.55), height=Inches(0.55))
        cb = s2.shapes.add_textbox(cx + Inches(0.85), Inches(4.68), card_w - Inches(0.95), Inches(2.0))
        c_tf = cb.text_frame
        c_tf.word_wrap = True
        c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0
        p_top = c_tf.paragraphs[0]
        p_top.text = f"{cd['metric']}  |  {cd['tag']}"
        p_top.font.size = Pt(9)
        p_top.font.bold = True
        p_top.font.color.rgb = cd["col"]
        p_t = c_tf.add_paragraph()
        p_t.text = cd["title"]
        p_t.font.size = Pt(11.5)
        p_t.font.bold = True
        p_t.font.color.rgb = theme.text_primary
        p_t.space_before = Pt(2)
        p_t.space_after = Pt(3)
        for b in cd["bullets"]:
            p_b = c_tf.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.size = Pt(8.8)
            p_b.font.color.rgb = theme.text_secondary
            p_b.space_after = Pt(2)

    add_footer(s2, theme, 2, 3, "Cybersecurity Governance Group")

    # Slide 3: SOC-2 & ISO 27001 Certification Roadmap
    s3 = add_slide_base(prs, theme)
    add_header(
        s3,
        theme,
        tracker="Compliance & Risk Governance  |  Q3 Certification Roadmap",
        title="Phased Verification Secures SOC-2 Type II & FedRAMP High Readiness",
        subtitle="Continuous compliance telemetry, third-party penetration auditing, and automated posture remediation.",
    )
    # State diagram card
    add_card_box(s3, theme, Inches(0.8), Inches(1.72), Inches(11.733), Inches(1.70))
    tb_mh = s3.shapes.add_textbox(Inches(1.05), Inches(1.84), Inches(11.2), Inches(0.28))
    tf_mh = tb_mh.text_frame
    tf_mh.margin_left = tf_mh.margin_right = tf_mh.margin_top = tf_mh.margin_bottom = 0
    p_mh = tf_mh.paragraphs[0]
    p_mh.text = "PHASED COMPLIANCE GATES & GOVERNANCE ROADMAP (DRAW.IO ENGINE)"
    p_mh.font.size = Pt(9.5)
    p_mh.font.bold = True
    p_mh.font.color.rgb = theme.brand_primary

    s3.shapes.add_picture(str(assets["diag_state"]), Inches(1.0), Inches(2.12), width=Inches(11.333), height=Inches(1.20))

    # 3 Phase Cards
    phases = [
        {"p": "PHASE 01  |  Q1-Q2", "st": "COMPLETED", "st_bg": theme.badge_success_fill, "st_col": theme.success, "icon": assets["icon_check"], "title": "Zero-Trust Perimeter", "sum": "Multi-region VPC microsegmentation & HSM cluster.", "dels": ["SPIFFE/SPIRE authentication mesh", "eBPF kernel process monitoring", "Vulnerability scanning automation", "Automated cert rotation active"], "col": theme.success},
        {"p": "PHASE 02  |  Q2-Q3", "st": "IN PROGRESS", "st_bg": theme.badge_primary_fill, "st_col": theme.brand_primary, "icon": assets["icon_refresh"], "title": "Security Orchestration", "sum": "SOAR playbook integration & red-team exercises.", "dels": ["Automated incident response playbooks", "Real-time threat graph clustering", "Red team adversarial simulation", "Zero false-positive attestation"], "col": theme.brand_primary},
        {"p": "PHASE 03  |  Q3-Q4", "st": "UPCOMING", "st_bg": theme.badge_warning_fill, "st_col": theme.warning, "icon": assets["icon_flag"], "title": "Full Audit Sign-Off", "sum": "SOC-2 Type II & FedRAMP High certification.", "dels": ["External penetration audit completion", "SOC-2 Type II report sign-off", "Executive governance board sign-off", "24/7 SOC / Incident response active"], "col": theme.warning},
    ]
    for i, ph in enumerate(phases):
        cx = Inches(0.8) + i * (card_w + card_gap)
        add_card_box(s3, theme, cx, Inches(3.58), card_w, Inches(3.22), has_top_stripe=True)
        st = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, Inches(3.58), card_w, Inches(0.08))
        st.shadow.inherit = False
        st.fill.solid()
        st.fill.fore_color.rgb = ph["col"]
        st.line.fill.background()

        pill = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + card_w - Inches(1.35), Inches(3.76), Inches(1.15), Inches(0.28))
        pill.shadow.inherit = False
        pill.fill.solid()
        pill.fill.fore_color.rgb = ph["st_bg"]
        pill.line.color.rgb = ph["st_col"]
        pill.line.width = Pt(0.75)
        ptf = pill.text_frame
        ptf.margin_left = ptf.margin_right = ptf.margin_top = ptf.margin_bottom = 0
        pp = ptf.paragraphs[0]
        pp.text = ph["st"]
        pp.font.size = Pt(8)
        pp.font.bold = True
        pp.alignment = PP_ALIGN.CENTER
        pp.font.color.rgb = ph["st_col"]

        s3.shapes.add_picture(str(ph["icon"]), cx + Inches(0.20), Inches(3.76), width=Inches(0.48), height=Inches(0.48))
        htb = s3.shapes.add_textbox(cx + Inches(0.75), Inches(3.74), card_w - Inches(2.15), Inches(0.50))
        htf = htb.text_frame
        htf.word_wrap = True
        htf.margin_left = htf.margin_right = htf.margin_top = htf.margin_bottom = 0
        p_ph = htf.paragraphs[0]
        p_ph.text = ph["p"]
        p_ph.font.size = Pt(8.5)
        p_ph.font.bold = True
        p_ph.font.color.rgb = ph["col"]
        p_pt = htf.add_paragraph()
        p_pt.text = ph["title"]
        p_pt.font.size = Pt(11.5)
        p_pt.font.bold = True
        p_pt.font.color.rgb = theme.text_primary

        dtb = s3.shapes.add_textbox(cx + Inches(0.20), Inches(4.35), card_w - Inches(0.40), Inches(2.35))
        dtf = dtb.text_frame
        dtf.word_wrap = True
        dtf.margin_left = dtf.margin_right = dtf.margin_top = dtf.margin_bottom = 0
        psum = dtf.paragraphs[0]
        psum.text = ph["sum"]
        psum.font.size = Pt(9)
        psum.font.color.rgb = theme.text_secondary
        psum.space_after = Pt(4)

        pdh = dtf.add_paragraph()
        pdh.text = "KEY DELIVERABLES:"
        pdh.font.size = Pt(8)
        pdh.font.bold = True
        pdh.font.color.rgb = theme.text_muted
        pdh.space_after = Pt(2)

        for d in ph["dels"]:
            pd = dtf.add_paragraph()
            pd.text = f"• {d}"
            pd.font.size = Pt(8.8)
            pd.font.color.rgb = theme.text_primary
            pd.space_after = Pt(2)

    add_footer(s3, theme, 3, 3, "Cybersecurity Governance Group")

    out_path = project_dir / "presentation.pptx"
    prs.save(str(out_path))
    return out_path


# ============================================================================
# 4. End-to-End Generator Pipeline
# ============================================================================

def generate_deck_suite(theme_name: str, output_dirname: str, topic_title: str) -> Tuple[Path, List[Path], Any]:
    """
    Generates a full branded consulting deck:
      1. Initializes sandbox directory in project_outputs/<output_dirname>/
      2. Compiles 3 theme-styled Draw.io diagrams
      3. Retrieves and tints theme-styled vector icons
      4. Builds 3-slide PPTX deck
      5. Headlessly exports slide previews to PNG
      6. Runs QA validator and returns report
    """
    base_dir = _ROOT_DIR
    project_dir = base_dir / "project_outputs" / output_dirname
    assets_dir = project_dir / "assets"
    diag_dir = project_dir / "diagrams"
    previews_dir = project_dir / "previews"

    project_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    diag_dir.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 78)
    print(f"🎨 Generating Branded Presentation: '{theme_name.upper()}' Theme")
    print(f"📂 Output Sandbox: {project_dir}")
    print(f"🎯 Strategy Topic: {topic_title}")
    print("=" * 78)

    theme = ThemeConfig(theme_name)
    assets_map: Dict[str, Path] = {}

    # Step 1: Compile Draw.io diagrams
    print(f"\n[1/4] Compiling Theme-Aligned Draw.io Diagrams ({theme.diagram_theme_name})...")
    diag_engine = DiagramEngine(workspace_root=base_dir)

    # Diagram 1: Topology
    mermaid_arch = """
    flowchart LR
        subgraph Ingress ["Edge & Security Perimeter"]
            DNS[Cloud DNS / Edge Anycast] --> WAF[WAF / DDoS Guard]
            WAF --> APIGW[API Gateway Ingress]
        end

        subgraph Core ["Microservices Mesh"]
            APIGW --> AuthSvc[Zero-Trust Policy Svc]
            APIGW --> ComputeSvc[Core Processing Svc]
            ComputeSvc --> StreamSvc[Telemetry Stream Svc]
        end

        subgraph Storage ["Distributed Persistence"]
            ComputeSvc --> DB[(Multi-Region Database)]
            StreamSvc --> StreamCluster[Event Stream Cluster]
            StreamSvc --> Lakehouse[(Vector Lakehouse)]
        end
    """
    r_arch = diag_engine.compile(
        mermaid_code=mermaid_arch,
        project_name=output_dirname,
        diagram_name="architecture_topology",
        theme=theme.diagram_theme_name,
        scale=3.0,
    )
    assets_map["diag_arch"] = r_arch["png"]

    # Diagram 2: Pipeline
    mermaid_pipe = """
    flowchart LR
        EdgeNodes[Edge Ingestion Hub] --> IngestQueue[Kafka Event Stream]
        IngestQueue --> PolicyEnforcer[Zero-Trust Validator]
        PolicyEnforcer --> FlinkEngine[Real-Time Analytics Engine]
        FlinkEngine --> EncryptedStorage[(Encrypted Lakehouse)]
        FlinkEngine --> RealtimeAlerts[Real-Time Exec Dashboard]
    """
    r_pipe = diag_engine.compile(
        mermaid_code=mermaid_pipe,
        project_name=output_dirname,
        diagram_name="streaming_pipeline",
        theme=theme.diagram_theme_name,
        scale=3.0,
    )
    assets_map["diag_pipeline"] = r_pipe["png"]

    # Diagram 3: State Roadmap
    mermaid_state = """
    flowchart LR
        P1[Phase 1: Foundation Baseline] --> G1{Gate 1: Security Audit}
        G1 --> P2[Phase 2: Pilot Cluster Mesh]
        P2 --> G2{Gate 2: Perf & SLA Check}
        G2 --> P3[Phase 3: Production Cutover]
        P3 --> GA([GA Full Rollout Complete])
    """
    r_state = diag_engine.compile(
        mermaid_code=mermaid_state,
        project_name=output_dirname,
        diagram_name="state_roadmap",
        theme=theme.diagram_theme_name,
        scale=3.0,
    )
    assets_map["diag_state"] = r_state["png"]
    print("  ✓ 3 Draw.io diagrams successfully generated and rasterized.")

    # Step 2: Tint Brand Icons
    print("\n[2/4] Generating & Tinting Vector Brand Icons...")
    icon_engine = IconEngine(cache_dir=assets_dir)
    icon_specs = [
        ("icon_shield", "lucide:shield-check", theme.brand_primary_hex, theme.badge_primary_fill),
        ("icon_zap", "lucide:zap", theme.success_hex, theme.badge_success_fill),
        ("icon_trend", "lucide:trending-up", theme.brand_secondary_hex, theme.badge_primary_fill),
        ("icon_lock", "lucide:lock", theme.brand_primary_hex, theme.badge_primary_fill),
        ("icon_activity", "lucide:activity", theme.brand_secondary_hex, theme.badge_primary_fill),
        ("icon_server", "lucide:server", theme.brand_accent_hex, theme.badge_primary_fill),
        ("icon_check", "lucide:check-circle", theme.success_hex, theme.badge_success_fill),
        ("icon_refresh", "lucide:refresh-cw", theme.brand_primary_hex, theme.badge_primary_fill),
        ("icon_flag", "lucide:flag", theme.warning_hex, theme.badge_warning_fill),
    ]
    for key, ident, brand_hex, bg_col in icon_specs:
        bg_h = f"#{bg_col[0]:02X}{bg_col[1]:02X}{bg_col[2]:02X}"
        ipath = icon_engine.get_icon(
            identifier=ident,
            color=brand_hex,
            size=256,
            output_path=assets_dir / f"{key}.png",
            badge_bg=bg_h,
            badge_radius=40,
        )
        assets_map[key] = ipath
    print("  ✓ 9 Tinted brand icons generated.")

    # Step 3: Procedural 3D Visual Framing
    print("\n[3/4] Generating & Framing 3D Visual Cards...")
    img_engine = ImageEngine(cache_dir=assets_dir)
    card_img = img_engine.generate_procedural_3d_card(
        title=topic_title,
        primary_color=theme.brand_primary_hex,
        accent_color=theme.brand_secondary_hex,
        size=(1600, 900),
    )
    framed_path = assets_dir / "framed_hero.png"
    frame_slide_image(
        image_input=card_img,
        aspect_ratio="16:9",
        corner_radius=20,
        border_width=1,
        border_color=theme.border_light,
        shadow=True,
        output_path=framed_path,
    )
    assets_map["framed_hero"] = framed_path
    print("  ✓ Procedural 3D hero asset framed and saved.")

    # Step 4: Construct Presentation PPTX Deck
    print("\n[4/4] Constructing Consulting Deck with python-pptx...")
    if theme_name == "snowblue":
        pptx_path = build_snowblue_deck(project_dir, theme, assets_map)
    else:
        pptx_path = build_brickred_deck(project_dir, theme, assets_map)
    print(f"  ✓ Saved PPTX deck: {pptx_path}")

    # Export Slide Previews
    print("\n📸 Exporting Slide Preview PNGs...")
    png_previews = export_deck_to_images(pptx_path, output_dir=previews_dir, backend="auto")
    print(f"  ✓ Exported {len(png_previews)} slide preview images to {previews_dir}")

    # Validate Deck
    print("\n🔍 Running Algorithmic QA Validator...")
    report = validate_presentation(pptx_path, theme=theme_name)
    report.print_summary()

    return pptx_path, png_previews, report


def main() -> None:
    print("=" * 80)
    print("🌟 MULTI-THEME BRANDED PRESENTATION GENERATOR & QA VALIDATOR 🌟")
    print("=" * 80)

    # 1. Generate Snow Blue Deck
    snow_pptx, snow_pngs, snow_rep = generate_deck_suite(
        theme_name="snowblue",
        output_dirname="snowblue_deck",
        topic_title="Cloud Mesh Architecture",
    )

    # 2. Generate Brick Red Deck
    brick_pptx, brick_pngs, brick_rep = generate_deck_suite(
        theme_name="brickred",
        output_dirname="brickred_deck",
        topic_title="Zero-Trust Cyber Resilience",
    )

    print("\n" + "=" * 80)
    print("📊 GENERATION & VALIDATION EXECUTION SUMMARY")
    print("=" * 80)
    print(f"1. Snow Blue Deck: {snow_pptx}")
    print(f"   • Previews ({len(snow_pngs)} PNGs): {[p.name for p in snow_pngs]}")
    print(f"   • QA Status: {'✅ PASSED (100%)' if snow_rep.passed else '❌ FAILED'}")

    print(f"\n2. Brick Red Deck: {brick_pptx}")
    print(f"   • Previews ({len(brick_pngs)} PNGs): {[p.name for p in brick_pngs]}")
    print(f"   • QA Status: {'✅ PASSED (100%)' if brick_rep.passed else '❌ FAILED'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
