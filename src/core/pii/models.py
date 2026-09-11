"""
PII Subsystem Data Models
=========================
Typed schemas representing scanned PII entities, text nodes, replacement
rules, scan reports, and audit manifests.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PiiCategory(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    CONTRACT_ID = "CONTRACT_ID"
    FINANCIAL = "FINANCIAL"
    GOVERNMENT_ID = "GOVERNMENT_ID"
    NETWORK = "NETWORK"
    METADATA = "METADATA"
    CUSTOM = "CUSTOM"


class PiiConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TextNode(BaseModel):
    """A discrete unit of text extracted from a binary or structured file."""
    location: str = Field(..., description="Human-readable coordinate (e.g., 'Slide 1 > Title', 'Sheet: Summary > Cell B4')")
    text: str = Field(..., description="Raw text content of the node")
    node_type: str = Field(..., description="Type of container (e.g., 'paragraph', 'table_cell', 'slide_shape', 'core_property')")
    context: Dict[str, Any] = Field(default_factory=dict, description="Handler-specific coordinate metadata")


class PiiMatch(BaseModel):
    """An identified PII instance found within a TextNode."""
    category: PiiCategory
    raw_value: str
    location: str
    confidence: PiiConfidence
    suggested_placeholder: str
    detector: str
    char_start: int = -1
    char_end: int = -1


class ScanReport(BaseModel):
    """Aggregated scan findings for a single file or an entire directory."""
    target_path: str
    total_files_scanned: int = 1
    total_matches: int = 0
    matches_by_category: Dict[str, int] = Field(default_factory=dict)
    matches: List[PiiMatch] = Field(default_factory=list)
    metadata_hits: Dict[str, str] = Field(default_factory=dict)


class ReplacementMapping(BaseModel):
    """Mapping instructions for scrubbing entities across files."""
    strategy: str = Field("jinja", description="'jinja' (e.g. {{ client_company }}) or 'redact' (e.g. [REDACTED: EMAIL])")
    replacements: Dict[str, str] = Field(default_factory=dict, description="Raw entity string -> replacement placeholder")
    strip_metadata: bool = Field(True, description="Whether to clear or scrub core document properties")
    metadata_overrides: Dict[str, str] = Field(
        default_factory=lambda: {
            "author": "Enterprise Contributor",
            "last_modified_by": "Enterprise Contributor",
            "creator": "Enterprise Contributor",
            "comments": "",
            "title": "",
        },
        description="Property name -> replacement value",
    )


class SanitizeResult(BaseModel):
    """Outcome of a sanitization operation on a single file."""
    source_path: str
    output_path: str
    replacements_applied: int
    metadata_scrubbed: bool
    details: List[str] = Field(default_factory=list)


class SanitizationManifest(BaseModel):
    """Audit trail documenting all changes made during a batch sanitization run."""
    timestamp: str
    files_processed: int
    total_replacements: int
    results: List[SanitizeResult] = Field(default_factory=list)
    mapping_used: ReplacementMapping
