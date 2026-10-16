"""
Enterprise Delivery Subsystem
=============================
Headless delivery, concurrency locking, presentation overlays, and stage-gate manifests.
"""

from __future__ import annotations

from src.core.delivery.exceptions import (
    DeliveryError,
    LockConflictError,
    LockNotFoundError,
    LockOwnershipError,
    PreflightGateError,
    RemoteLockConflictError,
    SyncTransmissionError,
)
from src.core.delivery.locks import LockManager
from src.core.delivery.models import (
    DeliveryManifest,
    LockPayload,
    LockStatus,
    ManifestFileEntry,
    OverlayReport,
    OverlayStatus,
    PreflightGateResult,
    PreflightReport,
    SlideBadgeInfo,
    SyncItemRecord,
    SyncReceipt,
    SyncStatus,
)
from src.core.delivery.overlays import OverlayManager
from src.core.delivery.staging import StagingPipeline
from src.core.delivery.sync import (
    RemoteSyncEngine,
    discover_google_drive_mounts,
    resolve_target_drive_root,
)

__all__ = [
    # Managers & Pipelines
    "LockManager",
    "OverlayManager",
    "StagingPipeline",
    "RemoteSyncEngine",
    "discover_google_drive_mounts",
    "resolve_target_drive_root",
    # Status Enums
    "OverlayStatus",
    "SyncStatus",
    # Models
    "LockPayload",
    "LockStatus",
    "OverlayReport",
    "SlideBadgeInfo",
    "PreflightGateResult",
    "PreflightReport",
    "ManifestFileEntry",
    "DeliveryManifest",
    "SyncItemRecord",
    "SyncReceipt",
    # Exceptions
    "DeliveryError",
    "LockConflictError",
    "LockNotFoundError",
    "LockOwnershipError",
    "PreflightGateError",
    "RemoteLockConflictError",
    "SyncTransmissionError",
]

