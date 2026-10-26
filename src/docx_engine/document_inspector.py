"""
Word Document Inspector (L1 Inspection Engine)
==============================================
Inspects Word (.docx) files headlessly and extracts structured metadata,
heading hierarchies, table schemas, inline images, and token estimates.
Provides formatted output in Markdown, Rich tables, or raw JSON.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from docx import Document


@dataclass
class HeadingInfo:
    level: int  # 1 for Heading 1, 2 for Heading 2, etc. (0 for Title)
    style_name: str
    text: str
    paragraph_index: int


@dataclass
class TableInfo:
    table_index: int
    rows: int
    cols: int
    headers: List[str] = field(default_factory=list)
    cell_count: int = 0


@dataclass
class DocumentInfo:
    file_path: str
    total_paragraphs: int = 0
    total_headings: int = 0
    total_tables: int = 0
    total_images: int = 0
    total_words: int = 0
    estimated_tokens: int = 0
    headings: List[HeadingInfo] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)
    paragraphs_preview: List[str] = field(default_factory=list)

    def compute_totals(self) -> None:
        self.total_headings = len(self.headings)
        self.total_tables = len(self.tables)
        # Token heuristic: 1 word ~ 1.33 tokens
        self.estimated_tokens = int(math.ceil(self.total_words * 1.33))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self, full: bool = False) -> str:
        lines: List[str] = []
        filename = Path(self.file_path).name
        lines.append(f"# Document Inspection: `{filename}`")
        lines.append("")
        lines.append(f"- **Total Paragraphs**: {self.total_paragraphs}")
        lines.append(f"- **Total Headings**: {self.total_headings}")
        lines.append(f"- **Total Tables**: {self.total_tables}")
        lines.append(f"- **Total Inline Images**: {self.total_images}")
        lines.append(f"- **Total Words**: {self.total_words:,} (~{self.estimated_tokens:,} tokens)")
        lines.append("")

        if self.headings:
            lines.append("## Heading Hierarchy")
            lines.append("")
            for h in self.headings:
                indent = "  " * (max(0, h.level - 1))
                prefix = "#" * max(1, h.level) if h.level > 0 else "Title:"
                lines.append(f"{indent}- `{prefix}` {h.text}")
            lines.append("")

        if self.tables:
            lines.append("## Table Inventory")
            lines.append("")
            lines.append("| Index | Dimensions (R x C) | Cells | Header Columns Preview |")
            lines.append("| :---: | :---: | :---: | :--- |")
            for t in self.tables:
                hdr_str = ", ".join(f"`{h}`" for h in t.headers if h) if t.headers else "*(no header row)*"
                lines.append(f"| {t.table_index} | {t.rows} x {t.cols} | {t.cell_count} | {hdr_str} |")
            lines.append("")

        if full and self.paragraphs_preview:
            lines.append("## Content Sampling (First 10 Paragraphs)")
            lines.append("")
            for i, p in enumerate(self.paragraphs_preview[:10], start=1):
                lines.append(f"{i}. {p}")
            lines.append("")

        return "\n".join(lines)


class DocumentInspector:
    """Headless inspector for extracting structure and text metrics from Word documents."""

    def __init__(self, docx_path: Union[str, Path]) -> None:
        self.docx_path = Path(docx_path).resolve()
        if not self.docx_path.exists():
            raise FileNotFoundError(f"Word document not found: {self.docx_path}")
        self.doc = Document(str(self.docx_path))

    def inspect(self) -> DocumentInfo:
        headings: List[HeadingInfo] = []
        paragraphs_preview: List[str] = []
        total_words = 0

        for p_idx, p in enumerate(self.doc.paragraphs):
            text = p.text.strip()
            if not text:
                continue

            words = len(text.split())
            total_words += words

            if len(paragraphs_preview) < 15:
                paragraphs_preview.append(text[:120] + ("..." if len(text) > 120 else ""))

            style_name = p.style.name if p.style else ""
            style_lower = style_name.lower()

            if "title" in style_lower:
                headings.append(HeadingInfo(level=0, style_name=style_name, text=text, paragraph_index=p_idx))
            elif "heading 1" in style_lower:
                headings.append(HeadingInfo(level=1, style_name=style_name, text=text, paragraph_index=p_idx))
            elif "heading 2" in style_lower:
                headings.append(HeadingInfo(level=2, style_name=style_name, text=text, paragraph_index=p_idx))
            elif "heading 3" in style_lower:
                headings.append(HeadingInfo(level=3, style_name=style_name, text=text, paragraph_index=p_idx))
            elif "heading 4" in style_lower:
                headings.append(HeadingInfo(level=4, style_name=style_name, text=text, paragraph_index=p_idx))

        tables_info: List[TableInfo] = []
        for t_idx, table in enumerate(self.doc.tables, start=1):
            rows = len(table.rows)
            cols = len(table.columns) if rows > 0 else 0
            headers: List[str] = []
            if rows > 0:
                for cell in table.rows[0].cells:
                    headers.append(cell.text.strip())

            # Count words in table cells
            table_words = sum(len(c.text.split()) for r in table.rows for c in r.cells if c.text.strip())
            total_words += table_words

            tables_info.append(
                TableInfo(
                    table_index=t_idx,
                    rows=rows,
                    cols=cols,
                    headers=headers[:6],
                    cell_count=rows * cols,
                )
            )

        # Count inline images via XML drawing parts
        image_count = 0
        try:
            for rel in self.doc.part.rels.values():
                if "image" in rel.target_ref.lower():
                    image_count += 1
        except Exception:
            pass

        info = DocumentInfo(
            file_path=str(self.docx_path),
            total_paragraphs=len([p for p in self.doc.paragraphs if p.text.strip()]),
            headings=headings,
            tables=tables_info,
            total_images=image_count,
            total_words=total_words,
            paragraphs_preview=paragraphs_preview,
        )
        info.compute_totals()
        return info
