"""
DrawingML Text Formatting & Universal Markdown Span Compiler
============================================================
Translates inline markdown formatting into native PowerPoint DrawingML text runs (<a:r>).
Supports:
- **bold** -> run.font.bold = True
- *italic* -> run.font.italic = True
- ***bold italic*** -> run.font.bold = True, run.font.italic = True
- __underline__ or <u>underline</u> -> run.font.underline = True
- **__bold underline__** / __**bold underline**__ -> bold + underline
- `code` -> monospace font family (Consolas)
- Lead-in anchors: **Lead:** Body inherits semantic primary color for lead-in
- Auto lead-in colon detection when no explicit tags exist: "Lead: Body" -> "Lead:" bold
"""

from __future__ import annotations

import re
from typing import Any, List, Optional, Tuple, Union

from pptx.dml.color import RGBColor
from pptx.text.text import _Paragraph, TextFrame
from pptx.util import Pt


# Regex tokenizer for inline styling
# Matches from longest/most specific patterns to basic spans
_INLINE_TOKEN_RE = re.compile(
    r"("
    r"\*\*\*.*?\*\*\*|"            # ***bold italic***
    r"\*\*__.*?__\*\*|"            # **__bold underline__**
    r"__\*\*.*?\*\*__|"            # __**underline bold**__
    r"\*\*.*?\*\*|"                # **bold**
    r"__.*?__|"                    # __underline__
    r"<u>.*?</u>|"                 # <u>underline</u>
    r"(?<!\w)\*[^*\n]+?\*(?!\w)|"  # *italic* (bounded by non-word/space)
    r"`[^`\n]+`"                   # `code`
    r")",
    re.DOTALL,
)


def parse_inline_markdown(text: str, auto_colon_lead: bool = False) -> List[Tuple[str, dict]]:
    """
    Parses a markdown formatted string into a sequence of (plain_text, style_dict) tuples.
    style_dict keys: 'bold' (bool), 'italic' (bool), 'underline' (bool), 'code' (bool).
    """
    if not text:
        return []

    tokens = _INLINE_TOKEN_RE.split(text)
    runs: List[Tuple[str, dict]] = []
    has_explicit_styling = False

    for token in tokens:
        if not token:
            continue

        style = {
            "bold": False,
            "italic": False,
            "underline": False,
            "code": False,
        }

        # ***bold italic***
        if token.startswith("***") and token.endswith("***") and len(token) >= 6:
            content = token[3:-3]
            style["bold"] = True
            style["italic"] = True
            has_explicit_styling = True
        # **__bold underline__**
        elif token.startswith("**__") and token.endswith("__**") and len(token) >= 8:
            content = token[4:-4]
            style["bold"] = True
            style["underline"] = True
            has_explicit_styling = True
        # __**underline bold**__
        elif token.startswith("__**") and token.endswith("**__") and len(token) >= 8:
            content = token[4:-4]
            style["bold"] = True
            style["underline"] = True
            has_explicit_styling = True
        # **bold**
        elif token.startswith("**") and token.endswith("**") and len(token) >= 4:
            content = token[2:-2]
            style["bold"] = True
            has_explicit_styling = True
        # __underline__
        elif token.startswith("__") and token.endswith("__") and len(token) >= 4:
            content = token[2:-2]
            style["underline"] = True
            has_explicit_styling = True
        # <u>underline</u>
        elif token.startswith("<u>") and token.endswith("</u>") and len(token) >= 7:
            content = token[3:-4]
            style["underline"] = True
            has_explicit_styling = True
        # *italic*
        elif token.startswith("*") and token.endswith("*") and len(token) >= 2:
            content = token[1:-1]
            style["italic"] = True
            has_explicit_styling = True
        # `code`
        elif token.startswith("`") and token.endswith("`") and len(token) >= 2:
            content = token[1:-1]
            style["code"] = True
            has_explicit_styling = True
        else:
            content = token

        if content:
            runs.append((content, style))

    # Optional fallback for unformatted bullet text with "Lead: Body" structure
    if auto_colon_lead and not has_explicit_styling and len(runs) == 1:
        single_text = runs[0][0]
        if ":" in single_text and not single_text.startswith("http"):
            lead, body = single_text.split(":", 1)
            if 0 < len(lead.strip()) <= 45:
                return [
                    (f"{lead.strip()}: ", {"bold": True, "italic": False, "underline": False, "code": False}),
                    (body.strip(), {"bold": False, "italic": False, "underline": False, "code": False}),
                ]

    return runs


def append_formatted_runs(
    paragraph: _Paragraph,
    text: str,
    font_name: str = "Calibri",
    font_size_pt: float = 11.0,
    font_color: Optional[RGBColor] = None,
    lead_color: Optional[RGBColor] = None,
    default_bold: bool = False,
    default_italic: bool = False,
    default_underline: bool = False,
    auto_colon_lead: bool = False,
) -> None:
    """
    Appends native PowerPoint DrawingML runs (<a:r>) to a paragraph,
    interpreting inline markdown styles (**bold**, *italic*, __underline__, `code`).
    """
    clean_font = font_name.split(",")[0].strip().strip('"\'') if font_name else "Calibri"
    if not clean_font:
        clean_font = "Calibri"

    body_rgb = font_color or RGBColor(71, 85, 105)       # Default slate-600
    lead_rgb = lead_color or RGBColor(15, 23, 42)        # Default slate-900 for bold lead-ins

    parsed_spans = parse_inline_markdown(text, auto_colon_lead=auto_colon_lead)
    if not parsed_spans:
        return

    for span_text, style in parsed_spans:
        run = paragraph.add_run()
        run.text = span_text

        is_bold = style["bold"] or default_bold
        is_italic = style["italic"] or default_italic
        is_underline = style["underline"] or default_underline
        is_code = style["code"]

        run.font.name = "Consolas" if is_code else clean_font
        run.font.size = Pt(font_size_pt * 0.95 if is_code else font_size_pt)
        run.font.bold = is_bold
        run.font.italic = is_italic
        run.font.underline = is_underline

        # Apply lead-in primary contrast color when text is bolded
        if is_bold and lead_color:
            run.font.color.rgb = lead_rgb
        else:
            run.font.color.rgb = body_rgb


def set_formatted_text(
    text_frame: TextFrame,
    text: str,
    font_name: str = "Calibri",
    font_size_pt: float = 11.0,
    font_color: Optional[RGBColor] = None,
    lead_color: Optional[RGBColor] = None,
    default_bold: bool = False,
    default_italic: bool = False,
    default_underline: bool = False,
    line_spacing: Optional[float] = None,
    space_after: Optional[Pt] = None,
    auto_colon_lead: bool = False,
) -> _Paragraph:
    """
    Populates a TextFrame paragraph with formatted markdown spans,
    clearing preexisting text runs.
    """
    if not text_frame.paragraphs:
        p = text_frame.add_paragraph()
    else:
        p = text_frame.paragraphs[0]
        # Clear existing text safely
        p.text = ""

    if line_spacing is not None:
        p.line_spacing = line_spacing
    if space_after is not None:
        p.space_after = space_after

    append_formatted_runs(
        paragraph=p,
        text=text,
        font_name=font_name,
        font_size_pt=font_size_pt,
        font_color=font_color,
        lead_color=lead_color,
        default_bold=default_bold,
        default_italic=default_italic,
        default_underline=default_underline,
        auto_colon_lead=auto_colon_lead,
    )
    return p
