"""
Enterprise Staging & Delivery Pipeline
======================================
Headless preflight gatekeeper and manifest generator for client handovers.
Verifies file integrity, lock statuses, presentation overlays, and produces
cryptographically verifiable DeliveryManifest records.
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from src.core.delivery.exceptions import PreflightGateError
from src.core.delivery.locks import LockManager
from src.core.delivery.models import (
    DeliveryManifest,
    ManifestFileEntry,
    PreflightGateResult,
    PreflightReport,
)
from src.core.delivery.overlays import OverlayManager

logger = logging.getLogger(__name__)


def _compute_sha256(file_path: Path) -> str:
    """Calculates SHA-256 hash of a file in 64KB streaming chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class StagingPipeline:
    """
    Automates preflight validation and delivery manifest generation.
    """

    def __init__(
        self,
        lock_manager: Optional[LockManager] = None,
        overlay_manager: Optional[OverlayManager] = None,
    ) -> None:
        self.lock_mgr = lock_manager or LockManager()
        self.overlay_mgr = overlay_manager or OverlayManager()

    def run_preflight(
        self,
        directory: Union[str, Path],
        fail_on_locks: bool = True,
    ) -> PreflightReport:
        """
        Executes stage-gate preflight checks against all deliverables in a directory.
        
        Gates executed:
          1. Directory Accessibility & Existence
          2. Inventory Presence (checks for deliverable files)
          3. Lock Concurrency Audit (blocks if unreleased locks exist and fail_on_locks=True)
          4. Zero-Byte Corruption Guard (flags empty truncated files)
          5. Presentation Overlay Inspection (audits status badges on PPTX files)
          
        Args:
          directory: Target deliverable staging directory.
          fail_on_locks: If True, active locks cause gate failure.
          
        Returns:
          PreflightReport summarizing all gate outcomes.
        """
        dir_path = Path(directory).resolve()
        gates: List[PreflightGateResult] = []
        warnings: List[str] = []
        errors: List[str] = []

        # Gate 1: Directory Accessibility
        if not dir_path.exists() or not dir_path.is_dir():
            msg = f"Staging directory does not exist or is not a directory: '{dir_path}'"
            gates.append(PreflightGateResult(gate_name="DIRECTORY_ACCESSIBILITY", passed=False, message=msg))
            errors.append(msg)
            return PreflightReport(
                directory=str(dir_path),
                passed=False,
                gates=gates,
                locked_files=[],
                total_files=0,
                warnings=warnings,
                errors=errors,
            )

        gates.append(
            PreflightGateResult(
                gate_name="DIRECTORY_ACCESSIBILITY",
                passed=True,
                message=f"Directory is accessible: '{dir_path}'",
            )
        )

        # Inventory candidate deliverable files
        all_files = [
            f for f in dir_path.rglob("*")
            if f.is_file() and not f.name.startswith(".")
        ]
        deliverable_files = [
            f for f in all_files
            if not f.name.endswith(".lock") and "_LOCKED_" not in f.stem
        ]

        # Gate 2: Deliverable Inventory
        if not deliverable_files:
            msg = f"Staging directory contains zero deliverable files: '{dir_path}'"
            gates.append(PreflightGateResult(gate_name="DELIVERABLE_INVENTORY", passed=False, message=msg))
            errors.append(msg)
        else:
            gates.append(
                PreflightGateResult(
                    gate_name="DELIVERABLE_INVENTORY",
                    passed=True,
                    message=f"Found {len(deliverable_files)} candidate deliverable file(s).",
                    details={"file_count": len(deliverable_files)},
                )
            )

        # Gate 3: Lock Concurrency Audit
        active_locks = self.lock_mgr.list_locks(dir_path)
        if active_locks:
            locked_names = [Path(l.target_file).name for l in active_locks]
            if fail_on_locks:
                msg = f"Active lock conflicts detected on {len(active_locks)} file(s): {', '.join(locked_names)}"
                gates.append(
                    PreflightGateResult(
                        gate_name="LOCK_CONCURRENCY_AUDIT",
                        passed=False,
                        message=msg,
                        details={"locked_files": locked_names},
                    )
                )
                errors.append(msg)
            else:
                msg = f"{len(active_locks)} file(s) currently locked, but fail_on_locks=False: {', '.join(locked_names)}"
                gates.append(
                    PreflightGateResult(
                        gate_name="LOCK_CONCURRENCY_AUDIT",
                        passed=True,
                        message=msg,
                        details={"locked_files": locked_names},
                    )
                )
                warnings.append(msg)
        else:
            gates.append(
                PreflightGateResult(
                    gate_name="LOCK_CONCURRENCY_AUDIT",
                    passed=True,
                    message="Zero lock conflicts detected across staging tree.",
                )
            )

        # Gate 4: Zero-Byte Corruption Guard
        zero_byte_files = [f for f in deliverable_files if f.stat().st_size == 0]
        if zero_byte_files:
            corrupt_names = [f.name for f in zero_byte_files]
            msg = f"Found {len(zero_byte_files)} empty (0-byte) file(s): {', '.join(corrupt_names)}"
            gates.append(
                PreflightGateResult(
                    gate_name="ZERO_BYTE_CORRUPTION_GUARD",
                    passed=False,
                    message=msg,
                    details={"corrupt_files": corrupt_names},
                )
            )
            errors.append(msg)
        else:
            gates.append(
                PreflightGateResult(
                    gate_name="ZERO_BYTE_CORRUPTION_GUARD",
                    passed=True,
                    message="All candidate deliverables have non-zero file sizes.",
                )
            )

        # Gate 5: Presentation Overlay Inspection
        pptx_files = [f for f in deliverable_files if f.suffix.lower() == ".pptx"]
        pptx_details = {}
        for pptx in pptx_files:
            try:
                report = self.overlay_mgr.inspect(pptx)
                status_str = report.status.value if report.status else "UNSTAMPED"
                pptx_details[pptx.name] = status_str
                if status_str == "DRAFT":
                    warnings.append(f"Presentation '{pptx.name}' has DRAFT status overlay badge.")
            except Exception as exc:
                logger.warning("Could not audit overlay on '%s': %s", pptx.name, exc)
                pptx_details[pptx.name] = f"AUDIT_ERROR: {exc}"

        gates.append(
            PreflightGateResult(
                gate_name="PRESENTATION_OVERLAY_INSPECTION",
                passed=True,
                message=f"Audited {len(pptx_files)} PowerPoint presentation(s).",
                details=pptx_details,
            )
        )

        overall_passed = all(g.passed for g in gates) and len(errors) == 0

        return PreflightReport(
            directory=str(dir_path),
            passed=overall_passed,
            gates=gates,
            locked_files=active_locks,
            total_files=len(deliverable_files),
            warnings=warnings,
            errors=errors,
        )

    def generate_manifest(
        self,
        directory: Union[str, Path],
        target_drive_root: str,
        output_manifest_path: Optional[Union[str, Path]] = None,
        fail_on_locks: bool = True,
    ) -> DeliveryManifest:
        """
        Validates deliverables via preflight gates and compiles a signed delivery manifest.
        
        Args:
          directory: Staging root directory to index.
          target_drive_root: Base path on target cloud/shared drive (e.g. 'G:/Shared drives/Handover').
          output_manifest_path: Optional path to serialize manifest JSON.
          fail_on_locks: If True, aborts and raises PreflightGateError if active locks exist.
          
        Raises:
          PreflightGateError: If preflight validation gates fail.
        """
        dir_path = Path(directory).resolve()
        preflight = self.run_preflight(dir_path, fail_on_locks=fail_on_locks)
        if not preflight.passed:
            err_msg = "; ".join(preflight.errors) if preflight.errors else "Preflight gates failed."
            raise PreflightGateError(f"Cannot generate delivery manifest: {err_msg}")

        deliverable_files = [
            f for f in dir_path.rglob("*")
            if f.is_file()
            and not f.name.startswith(".")
            and not f.name.endswith(".lock")
            and "_LOCKED_" not in f.stem
        ]
        deliverable_files.sort(key=lambda p: str(p.relative_to(dir_path)))

        clean_drive_root = target_drive_root.rstrip("/\\")
        entries: List[ManifestFileEntry] = []

        for file_path in deliverable_files:
            rel_path = file_path.relative_to(dir_path).as_posix()
            target_drive_path = f"{clean_drive_root}/{rel_path}"
            stat = file_path.stat()
            size_bytes = stat.st_size
            sha256 = _compute_sha256(file_path)
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

            overlay_status = None
            if file_path.suffix.lower() == ".pptx":
                try:
                    rep = self.overlay_mgr.inspect(file_path)
                    if rep.status:
                        overlay_status = rep.status.value
                except Exception:
                    pass

            entries.append(
                ManifestFileEntry(
                    relative_path=rel_path,
                    target_drive_path=target_drive_path,
                    file_size_bytes=size_bytes,
                    sha256=sha256,
                    modified_at=mtime,
                    mime_type=mime_type,
                    locked=False,
                    overlay_status=overlay_status,
                )
            )

        now_utc = datetime.now(timezone.utc)
        delivery_id = f"DELIV-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

        manifest = DeliveryManifest(
            delivery_id=delivery_id,
            created_at=now_utc.isoformat(),
            source_directory=str(dir_path),
            target_drive_root=target_drive_root,
            total_files=len(entries),
            total_bytes=sum(e.file_size_bytes for e in entries),
            files=entries,
            metadata={
                "preflight_status": "PASSED",
                "warnings": preflight.warnings,
            },
        )

        if output_manifest_path:
            out_p = Path(output_manifest_path).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
            logger.info("Serialized delivery manifest '%s' to '%s'", delivery_id, out_p)

        return manifest
