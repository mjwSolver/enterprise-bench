"""
Format Handler Registry
=======================
Central registry mapping file extensions to their corresponding FormatHandler.
Supports runtime extension registration for arbitrary future formats (PDF, Markdown, JSON, etc.).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Set, Type
from src.core.pii.handlers.base import BaseFormatHandler
from src.core.pii.handlers.docx_handler import DocxHandler
from src.core.pii.handlers.pptx_handler import PptxHandler
from src.core.pii.handlers.xlsx_handler import XlsxHandler


class HandlerRegistry:
    """Registry maintaining format handlers keyed by file extension."""

    def __init__(self):
        self._handlers: Dict[str, BaseFormatHandler] = {}
        # Register core handlers by default
        self.register(DocxHandler)
        self.register(PptxHandler)
        self.register(XlsxHandler)

    def register(self, handler_cls: Type[BaseFormatHandler]) -> None:
        """Register a handler class for all its supported extensions."""
        instance = handler_cls()
        for ext in handler_cls.supported_extensions():
            normalized_ext = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            self._handlers[normalized_ext] = instance

    def get_handler(self, path: Path | str) -> Optional[BaseFormatHandler]:
        """Resolve the appropriate handler for a given file path."""
        p = Path(path)
        ext = p.suffix.lower()
        return self._handlers.get(ext)

    def is_supported(self, path: Path | str) -> bool:
        """Check whether a file extension is supported."""
        return self.get_handler(path) is not None

    def supported_extensions(self) -> Set[str]:
        """Return all registered file extensions."""
        return set(self._handlers.keys())


# Global default registry instance
default_registry = HandlerRegistry()


def register_handler(handler_cls: Type[BaseFormatHandler]) -> Type[BaseFormatHandler]:
    """Decorator to register a custom format handler into the default registry."""
    default_registry.register(handler_cls)
    return handler_cls
