"""
Base Format Handler Contract
=============================
Abstract base class for all file format adapters (DOCX, PPTX, XLSX, and future formats).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Set
from src.core.pii.models import SanitizeResult, TextNode


class BaseFormatHandler(ABC):
    """Protocol that every document format handler must implement."""

    @classmethod
    @abstractmethod
    def supported_extensions(cls) -> Set[str]:
        """Return a set of lowercase extensions with dot, e.g. {'.docx'}."""
        raise NotImplementedError

    @abstractmethod
    def extract_text_nodes(self, path: Path) -> List[TextNode]:
        """
        Extract all inspectable text elements from the file along with their
        precise spatial coordinates / hierarchy.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_metadata(self, path: Path) -> Dict[str, str]:
        """
        Extract document container properties (author, creator, last_modified_by, etc.).
        """
        raise NotImplementedError

    @abstractmethod
    def apply_replacements(
        self,
        input_path: Path,
        output_path: Path,
        replacements: Dict[str, str],
        strip_metadata: bool = True,
        metadata_overrides: Dict[str, str] | None = None,
    ) -> SanitizeResult:
        """
        Apply text replacements and metadata scrubbing, writing a clean copy
        to output_path while preserving file layout and binary integrity.
        """
        raise NotImplementedError
