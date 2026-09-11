"""
Universal PII Extraction & Sanitization Engine
==============================================
Provides end-to-end detection, mapping, and sanitization of sensitive personal
and corporate entities across Microsoft Word (.docx), PowerPoint (.pptx),
Excel (.xlsx), and extensible future document formats.
"""

from __future__ import annotations

from src.core.pii.detectors import (
    BaseDetector,
    ContractIdDetector,
    DetectorPipeline,
    DictionaryDetector,
    EmailDetector,
    GovernmentIdDetector,
    NetworkDetector,
    PhoneDetector,
    RegexDetector,
)
from src.core.pii.engine import (
    PiiEngine,
    load_mapping_json,
    save_mapping_json,
)
from src.core.pii.handlers.base import BaseFormatHandler
from src.core.pii.handlers.docx_handler import DocxHandler
from src.core.pii.handlers.pptx_handler import PptxHandler
from src.core.pii.handlers.xlsx_handler import XlsxHandler
from src.core.pii.models import (
    PiiCategory,
    PiiConfidence,
    PiiMatch,
    ReplacementMapping,
    SanitizationManifest,
    SanitizeResult,
    ScanReport,
    TextNode,
)
from src.core.pii.registry import (
    HandlerRegistry,
    default_registry,
    register_handler,
)

# Global default engine instance for quick scripting
_default_engine = PiiEngine()


def scan_file(path, pipeline=None) -> ScanReport:
    """Scan a single file for PII entities."""
    engine = PiiEngine(pipeline=pipeline) if pipeline else _default_engine
    return engine.scan_file(path)


def scan_directory(directory, recursive: bool = True, pipeline=None) -> ScanReport:
    """Scan all supported files in a directory."""
    engine = PiiEngine(pipeline=pipeline) if pipeline else _default_engine
    return engine.scan_directory(directory, recursive=recursive)


def generate_mapping(scan_report: ScanReport, strategy: str = "jinja") -> ReplacementMapping:
    """Generate a template replacement map from a scan report."""
    return _default_engine.generate_mapping(scan_report, strategy=strategy)


def sanitize_file(input_path, output_path=None, mapping=None) -> SanitizeResult:
    """Sanitize a single document file."""
    return _default_engine.sanitize_file(input_path, output_path=output_path, mapping=mapping)


def sanitize_directory(source_dir, output_dir, mapping=None, recursive: bool = True) -> SanitizationManifest:
    """Batch sanitize all documents in a directory."""
    return _default_engine.sanitize_directory(source_dir, output_dir=output_dir, mapping=mapping, recursive=recursive)


__all__ = [
    # Engine & Facade
    "PiiEngine",
    "scan_file",
    "scan_directory",
    "generate_mapping",
    "sanitize_file",
    "sanitize_directory",
    "save_mapping_json",
    "load_mapping_json",
    # Models
    "PiiCategory",
    "PiiConfidence",
    "PiiMatch",
    "TextNode",
    "ScanReport",
    "ReplacementMapping",
    "SanitizeResult",
    "SanitizationManifest",
    # Registry & Handlers
    "HandlerRegistry",
    "register_handler",
    "default_registry",
    "BaseFormatHandler",
    "DocxHandler",
    "PptxHandler",
    "XlsxHandler",
    # Detectors
    "DetectorPipeline",
    "BaseDetector",
    "RegexDetector",
    "EmailDetector",
    "PhoneDetector",
    "GovernmentIdDetector",
    "ContractIdDetector",
    "NetworkDetector",
    "DictionaryDetector",
]
