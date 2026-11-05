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

from typing import Any, Dict, List, Optional, Tuple, Union
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import RGBColor
from docx.table import Table, _Cell, _Row

from src.core.theme import parse_hex

# Pre-resolved Qualified Names (eliminates repeated string splitting & namespace lookups)
_QN_W_SHD = qn("w:shd")
_QN_W_TCMAR = qn("w:tcMar")
_QN_W_TBLHEADER = qn("w:tblHeader")
_QN_W_CANTSPLIT = qn("w:cantSplit")
_QN_W_TBLBORDERS = qn("w:tblBorders")

# Reusable insertion target sequences
_INSERT_BEFORE_SHD = ("w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign")
_INSERT_BEFORE_TCMAR = ("w:textDirection", "w:tcFitText", "w:vAlign")

# Pre-compiled static XML element templates
_CANT_SPLIT_ELEM = parse_xml(f'<w:cantSplit {nsdecls("w")}/>')
_TBL_HEADER_ELEM = parse_xml(f'<w:tblHeader {nsdecls("w")}/>')

# Element fragment caches
_SHD_CACHE: Dict[str, Any] = {}
_TCMAR_CACHE: Dict[Tuple[int, int, int, int], Any] = {}
_TBL_BORDERS_CACHE: Dict[Tuple[str, str], Any] = {}


def _get_shd_element(clean_hex: str) -> Any:
    """Retrieve or compile a cached w:shd element fragment."""
    elem = _SHD_CACHE.get(clean_hex)
    if elem is None:
        elem = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{clean_hex}"/>')
        _SHD_CACHE[clean_hex] = elem
    return elem.__copy__()


def _get_tcmar_element(top: int, bottom: int, left: int, right: int) -> Any:
    """Retrieve or compile a cached w:tcMar element fragment."""
    key = (top, bottom, left, right)
    elem = _TCMAR_CACHE.get(key)
    if elem is None:
        elem = parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            f'  <w:top w:w="{top}" w:type="dxa"/>'
            f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'  <w:left w:w="{left}" w:type="dxa"/>'
            f'  <w:right w:w="{right}" w:type="dxa"/>'
            f'</w:tcMar>'
        )
        _TCMAR_CACHE[key] = elem
    return elem.__copy__()


def _get_tbl_borders_element(clean_hex: str, sz: str) -> Any:
    """Retrieve or compile a cached w:tblBorders element fragment."""
    key = (clean_hex, sz)
    elem = _TBL_BORDERS_CACHE.get(key)
    if elem is None:
        borders_xml = (
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{clean_hex}"/>'
            f'<w:left w:val="none"/>'
            f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{clean_hex}"/>'
            f'<w:right w:val="none"/>'
            f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{clean_hex}"/>'
            f'<w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        )
        elem = parse_xml(borders_xml)
        _TBL_BORDERS_CACHE[key] = elem
    return elem.__copy__()


def set_cell_background(cell: _Cell, hex_color: Optional[str]) -> None:
    """Set background color of a table cell via OpenXML shading. If hex_color is None or empty, clears shading."""
    tcPr = cell._tc.get_or_add_tcPr()
    existing_shd = tcPr.find(_QN_W_SHD)
    if existing_shd is not None:
        tcPr.remove(existing_shd)
    if not hex_color or not isinstance(hex_color, str) or not hex_color.strip():
        return
    clean_hex = hex_color.strip().lstrip("#").upper()
    tcPr.insert_element_before(
        _get_shd_element(clean_hex),
        *_INSERT_BEFORE_SHD,
    )


def set_cell_margins(
    cell: _Cell,
    top: int = 120,
    bottom: int = 120,
    left: int = 150,
    right: int = 150,
) -> None:
    """Set inner cell padding in twips (1 pt = 20 twips, 6 pt = 120 twips)."""
    tcPr = cell._tc.get_or_add_tcPr()
    existing_mar = tcPr.find(_QN_W_TCMAR)
    if existing_mar is not None:
        tcPr.remove(existing_mar)
    tcPr.insert_element_before(_get_tcmar_element(top, bottom, left, right), *_INSERT_BEFORE_TCMAR)


def make_row_header(row: _Row) -> None:
    """Designate row as a repeating table header on page breaks."""
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(_QN_W_TBLHEADER) is None:
        trPr.append(_TBL_HEADER_ELEM.__copy__())


def prevent_row_split(row: _Row) -> None:
    """Prevent row from breaking across multiple pages."""
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(_QN_W_CANTSPLIT) is None:
        trPr.append(_CANT_SPLIT_ELEM.__copy__())


def set_table_borders(table: Table, border_color: str = "#CBD5E1", sz: str = "4") -> None:
    """Apply consistent subtle borders to a table via w:tblBorders."""
    clean_hex = border_color.strip().lstrip("#").upper()
    tblPr = table._tbl.tblPr
    existing_borders = tblPr.find(_QN_W_TBLBORDERS)
    if existing_borders is not None:
        tblPr.remove(existing_borders)
    tblPr.append(_get_tbl_borders_element(clean_hex, sz))


def style_table(
    table: Table,
    header_bg: str = "#2563EB",
    header_text_color: Optional[str] = "#FFFFFF",
    zebra_even_bg: Optional[str] = "#F8FAFC",
    zebra_odd_bg: Optional[str] = "#FFFFFF",
    border_color: str = "#CBD5E1",
) -> None:
    """Apply unified enterprise styling to a python-docx table."""
    header_rgb = RGBColor(*parse_hex(header_text_color)) if header_text_color else None

    if border_color:
        set_table_borders(table, border_color)

    clean_header = header_bg.strip().lstrip("#").upper() if header_bg else None
    clean_even = zebra_even_bg.strip().lstrip("#").upper() if zebra_even_bg else None
    clean_odd = zebra_odd_bg.strip().lstrip("#").upper() if zebra_odd_bg else None

    # Pre-obtain cloned XML templates
    tcmar_header = _get_tcmar_element(140, 140, 160, 160)
    tcmar_body = _get_tcmar_element(100, 100, 140, 140)

    # Ensure rows don't split awkwardly across page breaks
    table_rows = table.rows
    for i, row in enumerate(table_rows):
        prevent_row_split(row)
        row_cells = row.cells

        if i == 0:
            make_row_header(row)
            for cell in row_cells:
                tcPr = cell._tc.get_or_add_tcPr()
                ex_shd = tcPr.find(_QN_W_SHD)
                if ex_shd is not None:
                    tcPr.remove(ex_shd)
                if clean_header:
                    tcPr.insert_element_before(_get_shd_element(clean_header), *_INSERT_BEFORE_SHD)
                ex_mar = tcPr.find(_QN_W_TCMAR)
                if ex_mar is not None:
                    tcPr.remove(ex_mar)
                tcPr.insert_element_before(tcmar_header.__copy__(), *_INSERT_BEFORE_TCMAR)

                if header_rgb is not None:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.bold = True
                            run.font.color.rgb = header_rgb
        else:
            bg = clean_even if i % 2 == 0 else clean_odd
            shd_proto = _get_shd_element(bg) if bg else None
            for cell in row_cells:
                tcPr = cell._tc.get_or_add_tcPr()
                ex_shd = tcPr.find(_QN_W_SHD)
                if ex_shd is not None:
                    tcPr.remove(ex_shd)
                if shd_proto is not None:
                    tcPr.insert_element_before(shd_proto.__copy__(), *_INSERT_BEFORE_SHD)
                ex_mar = tcPr.find(_QN_W_TCMAR)
                if ex_mar is not None:
                    tcPr.remove(ex_mar)
                tcPr.insert_element_before(tcmar_body.__copy__(), *_INSERT_BEFORE_TCMAR)
