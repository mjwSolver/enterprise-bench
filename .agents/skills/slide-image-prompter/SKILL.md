---
name: slide-image-prompter
description: >-
  Generates precise, high-fidelity AI visual prompts for creating slide backgrounds, custom presentation infographics, visual motifs, and full-slide concept diagrams. Use when generating prompts for presentation visuals, slide assets, or image generation tools.
---

# Slide Image Prompter Skill

A specialized skill for authoring prompt specifications for AI image generators (such as Midjourney, DALL-E, Imagen, or internal rendering engines) to generate professional, presentation-ready slide visuals and concept art.

---

## 1. Prompt Engineering Formula for Slides

Every slide prompt must follow this structured anatomy:

```text
[Output Target & Aspect Ratio] + [Slide Narrative Role & Context] + [Precise Text Content & Hierarchy] + [Visual Composition & Style Directives] + [Negative Constraints / What to Avoid]
```

### Example Breakdown:
1. **Target**: "Create one 16:9 full-slide PowerPoint image for an executive/academic seminar deck."
2. **Slide Role**: "Slide role: Research gap and question framing."
3. **Visible Text Hierarchy**:
   - Header: `TRACKER | SECTION | 04`
   - Main Title: `Core Research Gap`
   - Key Nodes / Labels: Direct Indonesian/English text verbatim
4. **Visual Direction**:
   - Style: Modern consulting report, Swiss grid, pale cool-gray/white background (`#F8F9FA`).
   - Palette: Deep teal (`#0F766E`), slate navy (`#1E293B`), warm terracotta/amber accent (`#D97706`).
   - Elements: Hairline rules, clean geometric cards, generous whitespace, single focal path.
5. **Negative Constraints**:
   - "No generic rounded card grids, no decorative icon rows, no stock-photo people, no heavy 3D gradients, no dark full-bleed background, no misspelled words, no random filler labels."

---

## 2. Style Presets

### Preset A: Modern Consulting & Academic Seminar
- **Aesthetic**: Clean, analytical, evidence-led, minimalist.
- **Lighting & Texture**: Flat, high-contrast, matte finish, zero glossy bevels.
- **Color Codes**: Pale off-white canvas, deep slate text, dark teal primary, amber highlight.

### Preset B: Tech & Strategic Keynote
- **Aesthetic**: High contrast, crisp vectors, bold typography, directional flow.
- **Color Codes**: Charcoal/dark navy backdrop, bright cyan/indigo highlights, white headlines.

### Preset C: Financial & Quantitative Research
- **Aesthetic**: Structured table containers, metric cards, clear axis boundaries, austere geometric lines.

---

## 3. Reference Files
- [Slide Prompt Patterns & Templates](./references/prompt_patterns.md)
