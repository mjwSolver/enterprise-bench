# Backlog: Presentation Slide Design Variety & Archetype Expansion

> **Status:** Open Backlog / Design Modernization  
> **Topic:** PowerPoint Layout Variety, Eliminating Box Fatigue, Template-Driven Archetypes  
> **Target Module:** [`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py)

---

## 1. Problem Statement & Motivation

Generated presentations in the platform currently exhibit visual repetition ("box fatigue"):
- **Current Pattern:** Most content slides rely heavily on identical 3-card or 4-card structures (white rectangular containers, thin top accent lines, small icon badges, and bullet points).
- **The Need:** Enterprise presentations require structural and compositional variety to communicate complex strategic narratives (process flows, gap analyses, system architectures, executive pull-stats, and delivery timelines) without boxing every piece of information.

---

## 2. Exported Template Previews (Visual Inspection Reference)

To inspire new archetypes, full slide image exports have been generated from the production master templates using [`slide_exporter.py`](../src/ppt_engine/slide_exporter.py).

### 🚀 Fast Reference Commands (macOS Native Preview)

Open entire directories in macOS Preview:
```bash
# Presales Modernization Pitch Deck (36 slides)
open output/template_previews/pitch_deck/

# Project Kick-off Material Deck (19 slides)
open output/template_previews/kickoff/
```

### 🎯 Key Benchmark Slides to Review

| Slide File | Layout Pattern | Why It Breaks the "Box" Monotony |
| :--- | :--- | :--- |
| [`output/template_previews/pitch_deck/slide_07.png`](../output/template_previews/pitch_deck/slide_07.png) | **Horizontal Data Pipeline** | Unbordered source nodes flowing into an engine container and fanning out via arrows to consumer tools. |
| [`output/template_previews/pitch_deck/slide_08.png`](../output/template_previews/pitch_deck/slide_08.png) | **Split 1/3 Hero + 2/3 Detail** | Bold left-third accent block with large stat callouts; clean unboxed typography on the right. |
| [`output/template_previews/pitch_deck/slide_21.png`](../output/template_previews/pitch_deck/slide_21.png) | **Gap Analysis (As-Is vs. To-Be)** | Two contrasting vertical panels comparing current pain points against target capabilities with transition badges. |
| [`output/template_previews/pitch_deck/slide_26.png`](../output/template_previews/pitch_deck/slide_26.png) | **Stepped Chevron Process Flow** | Connected directional chevron flow (`Initiation ➔ Development ➔ Testing`) with progressive color saturation. |
| [`output/template_previews/pitch_deck/slide_32.png`](../output/template_previews/pitch_deck/slide_32.png) | **Gantt / Delivery Timeline** | Calendar-aligned matrix with horizontal duration bars and milestone markers. |
| [`output/template_previews/pitch_deck/slide_33.png`](../output/template_previews/pitch_deck/slide_33.png) | **Hierarchical Org & RACI Tree** | Structured governance hierarchy with orthogonal reporting connectors. |

---

## 3. Proposed Engine Archetypes to Implement

When resuming development, implement the following programmatic builders in [`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py):

1. **`build_chevron_process_slide(...)`**:
   - 3–5 interconnected horizontal chevrons/ribbons with directional points.
   - Distinct phase numbers, deliverable checklists, and progressive accent opacity.
2. **`build_split_hero_slide(...)`**:
   - Left 1/3: Deep contrast background fill (`theme.get_rgb("primary")` or `accent`), 44pt numeric highlight, sub-label.
   - Right 2/3: 3 unbordered narrative blocks separated by subtle hairline dividers (`#E2E8F0`).
3. **`build_gap_analysis_slide(...)`**:
   - Left column (Muted Slate / Red accent): Existing Challenge & Deficit.
   - Center: Transition / transformation arrow badge.
   - Right column (Brand Accent / Green tint): Target Capability & Quantified Business Value.
4. **`build_timeline_gantt_slide(...)`**:
   - Top calendar axis (e.g., Weeks 1–12 or Months 1–6).
   - Left stream labels, right duration bars with rounded caps or milestone diamonds.

---

## 4. Immediate Next Step

Review the exported PNGs in `output/template_previews/pitch_deck/` to prioritize which 2 archetypes should be coded first into `src/ppt_engine/consulting_archetypes.py`.

---

## 5. Backlog: Imagery, Stock Photography & Company Logo Formatting

> **Status:** Open / High Priority  
> **Topic:** Dedicated Image Bounding Boxes, Logo Lockups, and Template Reference Formatting  
> **Modules:** [`src/ppt_engine/consulting_archetypes.py`](../src/ppt_engine/consulting_archetypes.py), [`src/ppt_engine/image_engine.py`](../src/ppt_engine/image_engine.py), [`src/ppt_engine/theme_engine.py`](../src/ppt_engine/theme_engine.py)

### 📌 Problem Statement & Context
Current presentation generation relies primarily on text containers and vector icons. While initial support for stock photography and image framing exists (`frame_slide_image`), presentations lack structured, template-level conventions for:
1. **Where & How Images Should Be Placed:** Lack of defined image slots/bounding boxes across slide archetypes.
2. **Company Logos:** No automated lockups for dual client/vendor branding on cover slides and header/footer banners.
3. **Asset References:** Absence of declarative schema fields designating image intent (e.g., real-world photographic proof, process diagrams, or client badges).

### 🎯 Requirements & Proposed Architecture

#### A. Standardized Image Placeholder Zones in Archetypes
Define standardized visual bounding boxes across consulting archetypes:
- **Cover Slide Hero Visual:** Fixed 4:3 or 16:9 framed picture container (`x=7.5"`, `y=1.5"`, `w=5.0"`, `h=4.9"`) with anti-aliased rounded corners (`r=16px`), brand hairline border, subtle drop shadow, and floating telemetry pill.
- **Split-Screen Editorial Slide (1/2 Photo + 1/2 Text):** Left 5.8" photographic panel for high-impact case studies or real-world facility imagery; right 5.8" structured takeaway bullets.
- **Side-by-Side Proof Card:** Metric or architecture slides with a secondary supporting photographic proof thumbnail (`w=3.5"`, `h=2.2"`).
- **Leadership & Bio Grid:** Multi-column team cards with circular or rounded avatar placeholders (`1:1` aspect ratio, `r=50%`).

#### B. Company Logo Placement & Dual-Branding Protocol
- **Cover Slide Lockup:**
  - Support `client_logo_path` and `vendor_logo_path` in `PresentationConfig` / `build_cover_slide`.
  - Place logos in the top-right header zone (`x=10.5"`, `y=0.8"`) or within the typographic metadata block.
  - Enforce aspect-ratio preserving bounding box (`max_h=0.55"`, `max_w=2.0"`) with alpha transparency.
- **Content Slide Header/Footer Integration:**
  - Subtle client/vendor mark in slide header or footer divider (`h=0.25"`).
  - High-contrast inversion handling for dark/light themes.

#### C. Declarative Archetype Schema Extensions
Extend data models in `consulting_archetypes.py`:
```python
@dataclass
class SlideImageReference:
    source_path: Union[str, Path]
    caption_title: Optional[str] = None
    caption_source: Optional[str] = None
    aspect_ratio: str = "4:3"   # "16:9", "4:3", "1:1"
    corner_radius: int = 16
    has_border: bool = True
    has_shadow: bool = True

@dataclass
class BrandingConfig:
    client_logo: Optional[Path] = None
    vendor_logo: Optional[Path] = None
    partner_logos: List[Path] = field(default_factory=list)
```

#### D. Sourcing & Asset Distinction Protocol
- **Authentic Stock Photos:** Default to real photography from verified public domain / CC sources (Wikimedia Commons, Unsplash API) rather than AI-generated 3D renders when real-world context is required.
- **Vector Icons:** Lucide/Iconify vector glyphs for conceptual milestones and KPIs.
- **Technical Diagrams:** OpenXML / Pillow flow diagrams for architecture and data pipelines.

