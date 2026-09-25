# Backlog: Cover Slide Hero & Deck Opening Modernization

> **Status:** Open Backlog / Architecture & Visual Design Specification  
> **Topic:** Master Cover Slide Redesign, Hero Plate Composition, Cinematic Tech Imagery, Beyond Plain Text Openings  
> **Target Subsystems:** [`src/ppt_engine/consulting_archetypes.py`](../../src/ppt_engine/consulting_archetypes.py), [`src/ppt_engine/reference_slides.py`](../../src/ppt_engine/reference_slides.py), [`assets/images/`](../../assets/images)  
> **Benchmark Reference:** Original Presales Pitch Deck Cover ([`media_1789563662926.png`](../../assets/images)) / [`Modernize_Data_Platform_Pitch_Deck_Template.pptx`](../../clean_workspace/projects/TTI_Snowflake_Analytics/01_presales/Modernize_Data_Platform_Pitch_Deck_Template.pptx)

---

## 1. Executive Context & Problem Statement

The current programmatic cover slides (`build_cover_slide(...)`) established critical baseline hygiene:
- Replaced awkward boxed metadata containers with clean typographic columns.
- Removed footer divider bars and page numbers from Slide 1.
- Added dual vertical brand accent stripes (1 Red stroke : 2 Blue strokes).

**However, the visual impact remains conservative:**
The opening slide is dominated by white negative space and plain text typography. When compared against high-impact consulting and tech vendor pitch decks (such as the original presales deck Slide 1), modern enterprise openers feature **cinematic hero photography, dynamic infrastructure motifs (interchanges, light trails, cyber grids), and asymmetric split-canvas layouts** that immediately command room attention.

```
+--------------------------------------------------------------------------------------------------+
|                                    CURRENT PROGRAMMATIC COVER                                    |
|   || Data Application for Financial Analytics with Snowflake                                     |
|   ||                                                                                             |
|   Prepared for: [CLIENT_COMPANY_NAME]                              Partner: PT Metrodata         |
|   (Clean, but visually sterile / plain text on white)                                            |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼ TARGET MODERNIZATION
+--------------------------------------------------------------------------------------------------+
|                            CINEMATIC HERO COVER ARCHITECTURE                                     |
|  [========================== FULL-WIDTH / SPLIT TOP HERO PLATE ==============================]  |
|  [ High-DPI Night Highway Interchange / Infrastructure Light Trails / Translucent Dark Scrim]  |
|  [------------------------------------------------------------------------------------------]  |
|  Category Tracker Breadcrumb                                                                     |
|  Action Title: Data Application for Financial Analytics with Snowflake                           |
|  Clean Typographic Metadata Columns               Official Vector Lockup: [Metrodata x Snowflake]|
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Visual Architecture Archetypes for Deck Openings

### Archetype A: Top-Half Cinematic Hero Plate (The Original Presales Pitch Pattern)
- **Top 50% Canvas ($x=0.0''$, $y=0.0''$, $w=13.333''$, $h=3.75''$):** Full-bleed photographic hero plate depicting modernized cloud infrastructure (e.g., Shanghai night highway interchange, illuminated data grid, or high-speed fiber light trails).
- **Dark Scrim Overlay:** OpenXML DrawingML 25–35% dark translucent scrim guaranteeing contrast.
- **Bottom 50% White Canvas ($y=3.75''$ to $7.5''$):**
  - Crisp category breadcrumb (`ENTERPRISE ANALYTICS MODERNIZATION`).
  - High-impact title in 32–36pt bold (`#0F172A`).
  - Lower typographic columns for client and engagement leads.
  - Authentic dual vector lockup: Metrodata logo on bottom left, official cyan Snowflake logo on bottom right.

### Archetype B: Asymmetric 40/60 Vertical Split Hero
- **Left 40% Narrative Spine ($w=5.333''$, $h=7.5''$, white/light surface):**
  - Brand accent vertical stripe.
  - Executive title and subtitle.
  - Client / Vendor metadata stacked cleanly.
- **Right 60% Hero Panel ($w=8.0''$, $h=7.5''$):**
  - Full-bleed photographic plate with subtle dark vignette.
  - Floating high-contrast frosted glass card with engagement scope badge.

---

## 3. Engineering Implementation Plan

1. **Asset Curation (`assets/images/hero/`):**
   - Curate 3–4 high-resolution (300+ DPI, 3840x2160) enterprise hero images:
     - `cloud_interchange_night.jpg` (infrastructure/speed).
     - `data_mesh_abstract_cyber.jpg` (enterprise data/cloud).
     - `modern_datacenter_perspective.jpg` (reliability/governance).
2. **Archetype Extension (`src/ppt_engine/consulting_archetypes.py`):**
   - Add `build_hero_cover_slide(...)` accepting `hero_image_path`, `hero_layout="top_half" | "split_vertical" | "minimal_clean"`.
   - Implement OpenXML DrawingML scrim overlay (`<a:alpha val="35000"/>`).
3. **Declarative Config Support:**
   - Allow `archetype: hero_cover` in deck YAML presets with customizable hero tags and dual-logo lockups.
