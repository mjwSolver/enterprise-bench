"""
src/docx_engine/schemas.py
==========================
Pydantic v2 schemas for document frontmatter and spec compiler metadata.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SpecSignoff(BaseModel):
    """Sign-off stakeholder for document governance matrix."""
    role: str
    name: str
    title: str
    status: str = "Pending"
    date: Optional[str] = None


class SpecMetadataModel(BaseModel):
    """Document frontmatter and metadata model for modular specs."""
    title: str
    document_id: str
    version: str = "1.0"
    classification: str = "CONFIDENTIAL"
    author: str = "Enterprise Bench"
    owner: str = "Enterprise Architecture"
    date: str
    signoffs: List[SpecSignoff] = Field(default_factory=list)
