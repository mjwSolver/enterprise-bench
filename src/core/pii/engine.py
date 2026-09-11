"""
Universal PII Engine Orchestrator
==================================
Coordinates file scanning, entity detection, replacement mapping generation,
and document sanitization across all supported formats.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from src.core.pii.detectors import DetectorPipeline
from src.core.pii.models import (
    PiiCategory,
    PiiMatch,
    ReplacementMapping,
    SanitizationManifest,
    SanitizeResult,
    ScanReport,
)
from src.core.pii.registry import HandlerRegistry, default_registry


class PiiEngine:
    """High-level orchestration facade for PII scanning and redaction."""

    def __init__(
        self,
        registry: Optional[HandlerRegistry] = None,
        pipeline: Optional[DetectorPipeline] = None,
    ):
        self.registry = registry or default_registry
        self.pipeline = pipeline or DetectorPipeline()

    def scan_file(self, file_path: Union[str, Path]) -> ScanReport:
        """Scan a single document/file for PII entities and metadata."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Target file not found: {p}")

        handler = self.registry.get_handler(p)
        if not handler:
            raise ValueError(f"No handler registered for file format: {p.suffix} ({p.name})")

        # 1. Extract text nodes & core metadata
        nodes = handler.extract_text_nodes(p)
        metadata = handler.extract_metadata(p)

        # 2. Run detection pipeline
        all_matches: List[PiiMatch] = []
        matches_by_cat: Dict[str, int] = {}

        for node in nodes:
            matches = self.pipeline.scan_node(node)
            for m in matches:
                all_matches.append(m)
                matches_by_cat[m.category.value] = matches_by_cat.get(m.category.value, 0) + 1

        return ScanReport(
            target_path=str(p),
            total_files_scanned=1,
            total_matches=len(all_matches),
            matches_by_category=matches_by_cat,
            matches=all_matches,
            metadata_hits=metadata,
        )

    def scan_directory(
        self,
        directory: Union[str, Path],
        recursive: bool = True,
    ) -> ScanReport:
        """Recursively scan all supported documents in a directory."""
        dir_p = Path(directory)
        if not dir_p.is_dir():
            raise NotADirectoryError(f"Target path is not a directory: {dir_p}")

        supported = self.registry.supported_extensions()
        pattern = "**/*" if recursive else "*"
        all_matches: List[PiiMatch] = []
        matches_by_cat: Dict[str, int] = {}
        all_metadata: Dict[str, str] = {}
        files_count = 0

        for f in dir_p.glob(pattern):
            if f.is_file() and f.suffix.lower() in supported and not f.name.startswith("~$") and not f.name.startswith("."):
                files_count += 1
                try:
                    file_report = self.scan_file(f)
                    all_matches.extend(file_report.matches)
                    for cat, count in file_report.matches_by_category.items():
                        matches_by_cat[cat] = matches_by_cat.get(cat, 0) + count
                    for k, v in file_report.metadata_hits.items():
                        all_metadata[f"{f.name}:{k}"] = v
                except Exception as err:
                    # Log or skip corrupt files gracefully
                    all_metadata[f"{f.name}:error"] = str(err)

        return ScanReport(
            target_path=str(dir_p),
            total_files_scanned=files_count,
            total_matches=len(all_matches),
            matches_by_category=matches_by_cat,
            matches=all_matches,
            metadata_hits=all_metadata,
        )

    def generate_mapping(
        self,
        scan_report: ScanReport,
        strategy: str = "jinja",
    ) -> ReplacementMapping:
        """
        Synthesize a clean replacement mapping from detected PII matches.
        strategy:
          - 'jinja': uses Jinja2 template tokens (e.g. {{ client_company }})
          - 'redact': uses audit redaction masks (e.g. [REDACTED: EMAIL])
        """
        replacements: Dict[str, str] = {}
        counters: Dict[str, int] = {}

        for m in scan_report.matches:
            raw = m.raw_value.strip()
            if not raw or raw in replacements:
                continue

            if strategy == "jinja":
                # Prefer detector suggested placeholder
                base_token = m.suggested_placeholder
                if base_token.startswith("{{") and base_token.endswith("}}"):
                    token_name = base_token[2:-2].strip()
                    # If generic token, index it per unique entity
                    if token_name in ["contact_email", "contact_phone", "national_id"]:
                        counters[token_name] = counters.get(token_name, 0) + 1
                        replacements[raw] = f"{{{{ {token_name}_{counters[token_name]} }}}}"
                    else:
                        replacements[raw] = base_token
                else:
                    replacements[raw] = base_token
            else:
                # Redact strategy
                replacements[raw] = f"[REDACTED: {m.category.value}]"

        return ReplacementMapping(
            strategy=strategy,
            replacements=replacements,
            strip_metadata=True,
        )

    def sanitize_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        mapping: Optional[ReplacementMapping] = None,
    ) -> SanitizeResult:
        """Sanitize a single file using the given replacement mapping."""
        in_p = Path(input_path)
        if not in_p.exists():
            raise FileNotFoundError(f"Input file not found: {in_p}")

        handler = self.registry.get_handler(in_p)
        if not handler:
            raise ValueError(f"Unsupported format: {in_p.suffix}")

        out_p = Path(output_path) if output_path else in_p.parent / f"{in_p.stem}_sanitized{in_p.suffix}"

        if mapping is None:
            # Auto-generate on the fly if none provided
            rep = self.scan_file(in_p)
            mapping = self.generate_mapping(rep, strategy="jinja")

        return handler.apply_replacements(
            input_path=in_p,
            output_path=out_p,
            replacements=mapping.replacements,
            strip_metadata=mapping.strip_metadata,
            metadata_overrides=mapping.metadata_overrides,
        )

    def sanitize_directory(
        self,
        source_dir: Union[str, Path],
        output_dir: Union[str, Path],
        mapping: Optional[ReplacementMapping] = None,
        recursive: bool = True,
        copy_non_matching: bool = True,
    ) -> SanitizationManifest:
        """Batch sanitize an entire directory tree into an output directory."""
        import shutil
        src_p = Path(source_dir)
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        if mapping is None:
            scan_rep = self.scan_directory(src_p, recursive=recursive)
            mapping = self.generate_mapping(scan_rep, strategy="jinja")

        results: List[SanitizeResult] = []
        total_repl = 0
        supported = self.registry.supported_extensions()
        pattern = "**/*" if recursive else "*"

        for file_path in src_p.glob(pattern):
            if file_path.is_file() and not file_path.name.startswith("~$") and not file_path.name.startswith("."):
                rel_path = file_path.relative_to(src_p)
                dest_file = out_p / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                if file_path.suffix.lower() in supported:
                    try:
                        res = self.sanitize_file(file_path, dest_file, mapping)
                        results.append(res)
                        total_repl += res.replacements_applied
                    except Exception as err:
                        results.append(
                            SanitizeResult(
                                source_path=str(file_path),
                                output_path=str(dest_file),
                                replacements_applied=0,
                                metadata_scrubbed=False,
                                details=[f"Error: {err}"],
                            )
                        )
                elif copy_non_matching:
                    shutil.copy2(file_path, dest_file)

        manifest = SanitizationManifest(
            timestamp=datetime.now().isoformat(),
            files_processed=len(results),
            total_replacements=total_repl,
            results=results,
            mapping_used=mapping,
        )

        manifest_path = out_p / "sanitization_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        return manifest


# Convenience IO helpers
def save_mapping_json(mapping: ReplacementMapping, path: Union[str, Path]) -> Path:
    """Save replacement mapping to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(mapping.model_dump_json(indent=2))
    return p


def load_mapping_json(path: Union[str, Path]) -> ReplacementMapping:
    """Load replacement mapping from a JSON file."""
    p = Path(path)
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ReplacementMapping.model_validate(data)
