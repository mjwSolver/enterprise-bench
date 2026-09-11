"""
Table Engine Subsystem
======================
High-level OpenXML styling utilities for python-docx tables:
- Background cell shading (headers, alternate zebra rows)
- Cell padding / margins
- Header row persistence across page splits (tblHeader)
- Row split prevention (cantSplit)
- Consistent borders and alignment
"""

from __future__ import annotations

from typing import List, Optional, Union
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.table import Table, _Cell, _Row


def set_cell_background(cell: _Cell, hex_color: str) -> None:
    """Set background color of a table cell via OpenXML shading."""
    clean_hex = hex_color.strip().lstrip("#").upper()
    shd_xml = f'<w:shd {nsdecls("w")} w:fill="{clean_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shd_xml))


def set_cell_margins(
    cell: _Cell,
    top: int = 120,
    bottom: int = 120,
    left: int = 150,
    right: int = 150,
) -> None:
    """Set inner cell padding in twips (1 pt = 20 twips, 6 pt = 120 twips)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def make_row_header(row: _Row) -> None:
    """Designate row as a repeating table header on page breaks."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))


def prevent_row_split(row: _Row) -> None:
    """Prevent row from breaking across multiple pages."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))


def style_table(
    table: Table,
    header_bg: str = "#2563EB",
    header_text_color: Optional[str] = "#FFFFFF",
    zebra_even_bg: Optional[str] = "#F8FAFC",
    zebra_odd_bg: Optional[str] = "#FFFFFF",
    border_color: str = "#CBD5E1",
) -> None:
    """Apply unified enterprise styling to a python-docx table."""
    # Ensure rows don't split awkwardly across page breaks
    for i, row in enumerate(table.rows):
        prevent_row_split(row)

        if i == 0:
            make_row_header(row)
            for cell in row.cells:
                set_cell_background(cell, header_bg)
                set_cell_margins(cell, top=140, bottom=140, left=160, right=160)
                if header_text_color:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.bold = True
        else:
            bg = zebra_even_bg if i % 2 == 0 else zebra_odd_bg
            for cell in row.cells:
                if bg:
                    set_cell_background(cell, bg)
                set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
