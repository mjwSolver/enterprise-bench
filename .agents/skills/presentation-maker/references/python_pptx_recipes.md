# Python-PPTX Code Recipes

A cookbook of ready-to-use functions for constructing structured, modern presentation slides using `python-pptx`.

---

## 1. Canvas & Slide Initialization

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck(width_in=13.333, height_in=7.5):
    prs = Presentation()
    prs.slide_width = Inches(width_in)
    prs.slide_height = Inches(height_in)
    return prs

def add_blank_slide(prs, bg_color=RGBColor(248, 249, 250)):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    
    # Background fill
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = bg_color
    bg.line.fill.background()
    return slide
```

---

## 2. Header & Breadcrumb Tracker

```python
def add_header(slide, tracker_text, title_text, subtitle_text=None,
               tracker_color=RGBColor(15, 118, 110),
               title_color=RGBColor(30, 41, 59),
               subtitle_color=RGBColor(100, 116, 139)):
    # Category / Tracker breadcrumb
    tracker_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.35))
    tf_tr = tracker_box.text_frame
    tf_tr.word_wrap = True
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = tracker_text.upper()
    p_tr.font.size = Pt(10)
    p_tr.font.bold = True
    p_tr.font.color.rgb = tracker_color

    # Main Action Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.6))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = title_color

    if subtitle_text:
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.45), Inches(11.7), Inches(0.4))
        tf_s = sub_box.text_frame
        tf_s.word_wrap = True
        p_s = tf_s.paragraphs[0]
        p_s.text = subtitle_text
        p_s.font.size = Pt(12)
        p_s.font.color.rgb = subtitle_color
```

---

## 3. Container Cards & Columns

```python
def add_card(slide, left, top, width, height,
             bg_color=RGBColor(255, 255, 255),
             border_color=RGBColor(226, 232, 240),
             border_width=Pt(1),
             has_top_stripe=False):
    # Geometric Integrity: Cards with top stripes MUST NOT have rounded corners at the top
    shape_type = MSO_SHAPE.RECTANGLE if has_top_stripe else MSO_SHAPE.ROUNDED_RECTANGLE
    card = slide.shapes.add_shape(shape_type, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = border_width
    else:
        card.line.fill.background()
    return card

def add_card_with_header(slide, left, top, width, height, title, items,
                         accent_color=RGBColor(15, 118, 110),
                         card_bg=RGBColor(255, 255, 255)):
    # Background card (sharp rectangle flush with top stripe)
    add_card(slide, left, top, width, height, bg_color=card_bg, has_top_stripe=True)

    # Accent Top Stripe (clean rectangle, never rounded)
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Inches(0.08))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = accent_color
    stripe.line.fill.background()

    # Content Text Frame
    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.25), width - Inches(0.4), height - Inches(0.4))
    tf = tb.text_frame
    tf.word_wrap = True
    
    # Title
    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(14)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(30, 41, 59)
    p_title.space_after = Pt(10)

    # Bullet Items
    for item in items:
        p = tf.add_paragraph()
        p.text = f"•  {item}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = RGBColor(71, 85, 105)
        p.space_after = Pt(6)
```

---

## 4. Professional Statistical / Results Table

```python
def add_styled_table(slide, left, top, width, height, headers, data,
                     col_widths=None, highlight_rows=None):
    rows = len(data) + 1
    cols = len(headers)
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    if col_widths:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = w

    # Header Row
    for idx, h_text in enumerate(headers):
        cell = table.cell(0, idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(15, 118, 110)
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER

    # Data Rows
    for r_idx, row_values in enumerate(data, start=1):
        is_highlight = highlight_rows and (r_idx in highlight_rows)
        bg = RGBColor(241, 245, 249) if r_idx % 2 == 0 else RGBColor(255, 255, 255)
        if is_highlight:
            bg = RGBColor(254, 243, 199) # Highlight gold/amber

        for c_idx, val in enumerate(row_values):
            cell = table.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = str(val)
            p.font.size = Pt(10)
            p.font.color.rgb = RGBColor(30, 41, 59)
            if c_idx == 0:
                p.alignment = PP_ALIGN.LEFT
                p.font.bold = True
            else:
                p.alignment = PP_ALIGN.CENTER
```
