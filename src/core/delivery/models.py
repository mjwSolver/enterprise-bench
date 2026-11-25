"""
Enterprise Delivery Data Models
===============================
Pydantic v2 data contracts for deliverable locks, status overlays,
preflight validation gates, and delivery manifests.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class OverlayStatus(str, Enum):
    """Deliverable lifecycle / document classification status."""
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    FINAL = "FINAL"
    CONFIDENTIAL = "CONFIDENTIAL"


class LockPayload(BaseModel):
    """Payload persisted in `<filename>.lock` sidecar files."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    filepath: str = Field(default="", description="Absolute path to the locked target file.")
    user: str = Field(default="", description="Username or principal holding the lock.")
    reason: Optional[str] = Field(default=None, description="Optional justification for the lock.")
    locked_at: str = Field(default="", description="ISO 8601 UTC timestamp of lock acquisition.")
    locked_copy_path: Optional[str] = Field(default=None, description="Path to <stem>_LOCKED_<user>.<ext>.")
    lock_file: Optional[str] = Field(default=None, description="Path to <filename>.lock sidecar.")

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "file" in data and "filepath" not in data:
                data["filepath"] = data["file"]
            if "locked_by" in data and "user" not in data:
                data["user"] = data["locked_by"]
            if "locked_file" in data and "locked_copy_path" not in data:
                data["locked_copy_path"] = data["locked_file"]
        return data



class LockStatus(BaseModel):
    """Lock state evaluation result for a file or deliverable."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    is_locked: bool = Field(description="Whether the target file is currently locked.")
    target_file: str = Field(description="Target file path under inspection.")
    user: Optional[str] = Field(default=None, description="Username holding the lock if locked.")
    reason: Optional[str] = Field(default=None, description="Reason for lock if locked.")
    locked_at: Optional[str] = Field(default=None, description="ISO 8601 timestamp of lock.")
    lock_file_path: Optional[str] = Field(default=None, description="Path to .lock sidecar file.")
    locked_copy_path: Optional[str] = Field(default=None, description="Path to locked copy file.")


class SlideBadgeInfo(BaseModel):
    """Information regarding a status badge located on an individual slide."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    slide_number: int = Field(description="1-indexed slide number.")
    has_badge: bool = Field(default=False, description="Whether the slide contains an overlay badge.")
    status: Optional[str] = Field(default=None, description="Extracted status text.")
    text: Optional[str] = Field(default=None, description="Raw badge text.")
    shape_id: Optional[int] = Field(default=None, description="OpenXML Shape ID of the badge.")


class OverlayReport(BaseModel):
    """Result of overlay inspection, stamping, or stripping operations."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    pptx_path: str = Field(description="Path to the PowerPoint presentation.")
    status: Optional[OverlayStatus] = Field(default=None, description="Deck-level status applied or detected.")
    stamped_slides: List[int] = Field(default_factory=list, description="Slide numbers that were stamped.")
    stripped_slides: List[int] = Field(default_factory=list, description="Slide numbers from which badges were removed.")
    slide_badges: List[SlideBadgeInfo] = Field(default_factory=list, description="Badge status per slide.")
    total_slides: int = Field(default=0, description="Total slide count in presentation.")


class PreflightGateResult(BaseModel):
    """Outcome of a single preflight gate check."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    gate_name: str = Field(description="Identifier of the validation gate.")
    passed: bool = Field(description="Whether the check passed.")
    message: str = Field(description="Human-readable summary of the check result.")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic telemetry or findings.")


class PreflightReport(BaseModel):
    """Aggregated report of all staging preflight gates."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    directory: str = Field(description="Staging directory audited.")
    passed: bool = Field(description="True if all critical gates passed without blocking errors.")
    gates: List[PreflightGateResult] = Field(default_factory=list, description="List of gate execution results.")
    locked_files: List[LockStatus] = Field(default_factory=list, description="Active file locks detected.")
    total_files: int = Field(default=0, description="Total files audited in directory tree.")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warning notices.")
    errors: List[str] = Field(default_factory=list, description="Blocking gate failure errors.")


class ManifestFileEntry(BaseModel):
    """Item record in a staged delivery package manifest."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    relative_path: str = Field(description="Relative path from staging directory root.")
    target_drive_path: str = Field(description="Full destination path on target drive.")
    file_size_bytes: int = Field(description="Size of file in bytes.")
    sha256: str = Field(description="SHA-256 cryptographic digest.")
    modified_at: str = Field(description="ISO 8601 UTC timestamp of last modification.")
    mime_type: Optional[str] = Field(default=None, description="MIME content type.")
    locked: bool = Field(default=False, description="Whether the file currently has an active lock.")
    overlay_status: Optional[str] = Field(default=None, description="Detected slide overlay status if PPTX.")


class DeliveryManifest(BaseModel):
    """Top-level delivery manifest describing a stage-gate deployment package."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    delivery_id: str = Field(description="Unique delivery batch identifier.")
    created_at: str = Field(description="ISO 8601 UTC timestamp of manifest generation.")
    source_directory: str = Field(description="Source directory from which manifest was built.")
    target_drive_root: str = Field(description="Target destination drive root.")
    total_files: int = Field(default=0, description="Total number of deliverables staged.")
    total_bytes: int = Field(default=0, description="Aggregated file payload size in bytes.")
    files: List[ManifestFileEntry] = Field(default_factory=list, description="Staged deliverable files.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary delivery batch metadata.")


class SyncStatus(str, Enum):
    """Transmission status for an individual deliverable during sync."""
    TRANSMITTED = "TRANSMITTED"
    SKIPPED_IDENTICAL = "SKIPPED_IDENTICAL"
    FAILED = "FAILED"
    LOCKED_CONFLICT = "LOCKED_CONFLICT"
    REMOTE_CONFLICT = "REMOTE_CONFLICT"
    DRY_RUN = "DRY_RUN"


class RemotePinRecord(BaseModel):
    """Pinned remote revision baseline captured at checkout or last sync."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    file_id: Optional[str] = Field(default=None, description="Optional Google Drive file ID.")
    local_path: str = Field(description="Local relative or absolute path.")
    target_drive_path: str = Field(description="Resolved remote path on Google Drive.")
    base_revision_id: str = Field(description="Pinned remote headRevisionId or mtime/size token.")
    base_md5: str = Field(description="Pinned remote MD5 checksum.")
    base_sha256: str = Field(default="", description="Pinned remote SHA-256 digest.")
    base_modified_time: str = Field(description="ISO 8601 UTC timestamp of pinned remote state.")
    checkout_user: Optional[str] = Field(default=None, description="Operator or agent who pinned baseline.")


class RemoteLockSidecar(BaseModel):
    """Remote collaborative lock sidecar (`._LOCKED_<user>_<ts>.json`) in Drive folder."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    file_name: str = Field(description="Target deliverable filename.")
    locked_by: str = Field(description="User or agent holding the remote lock.")
    locked_at: str = Field(description="ISO 8601 UTC lock creation timestamp.")
    ttl_seconds: int = Field(default=7200, description="Time-to-live in seconds before lock expires.")
    reason: Optional[str] = Field(default=None, description="Optional lock reason.")
    lock_path: Optional[str] = Field(default=None, description="Path to the remote lock sidecar file.")


class DriftCheckItem(BaseModel):
    """Drift evaluation status for a single pinned deliverable."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    file_name: str = Field(description="Deliverable filename.")
    status: Literal["IN_SYNC", "REMOTE_DRIFTED", "REMOTE_MISSING", "REMOTE_LOCKED"]
    target_drive_path: str = Field(description="Remote file path checked.")
    base_revision_id: Optional[str] = None
    remote_revision_id: Optional[str] = None
    base_hash: Optional[str] = None
    remote_hash: Optional[str] = None
    remote_modified_by: Optional[str] = None
    remote_modified_time: Optional[str] = None
    message: str = ""


class DriftReport(BaseModel):
    """Aggregated remote drift audit report across a staged directory."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    checked_at: str = Field(description="ISO 8601 UTC timestamp of drift check.")
    directory: str = Field(description="Local staging directory audited.")
    has_drift: bool = Field(default=False, description="True if any pinned deliverable drifted or is remotely locked.")
    items: List[DriftCheckItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SyncItemRecord(BaseModel):
    """Individual item synchronization audit log entry."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str = Field(description="Deliverable file basename.")
    category: Optional[str] = Field(default=None, description="Staging category name if categorized.")
    relative_path: str = Field(description="Source relative path.")
    target_drive_path: str = Field(description="Full target destination path on Google Drive.")
    size_bytes: int = Field(description="File size in bytes.")
    sha256: str = Field(description="Cryptographic SHA-256 digest.")
    status: SyncStatus = Field(description="Transmission outcome status.")
    error_message: Optional[str] = Field(default=None, description="Error detail if transmission failed.")
    remote_file_id: Optional[str] = Field(default=None, description="Optional Google Drive file ID.")
    base_revision_id: Optional[str] = Field(default=None, description="Pinned or updated remote revision token.")
    base_md5: Optional[str] = Field(default=None, description="Pinned or updated remote MD5 checksum.")
    remote_modified_time: Optional[str] = Field(default=None, description="Remote modified timestamp.")
    conflict_branch_path: Optional[str] = Field(default=None, description="Saved _REMOTE_ conflict branch path.")


class SyncReceipt(BaseModel):
    """Audit ledger receipt certifying transmission of staged deliverables to remote Google Drive."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    sync_id: str = Field(description="Unique synchronization execution identifier.")
    timestamp: str = Field(description="ISO 8601 UTC timestamp of sync completion.")
    source_manifest: str = Field(description="Path to manifest file used for synchronization.")
    resolved_target_root: str = Field(description="Resolved target Google Drive root directory.")
    checkout_user: Optional[str] = Field(default=None, description="Operator or agent executing sync.")
    total_files: int = Field(default=0, description="Total candidate files evaluated.")
    transmitted_count: int = Field(default=0, description="Files transmitted to Google Drive.")
    skipped_count: int = Field(default=0, description="Files skipped because remote copy is identical.")
    failed_count: int = Field(default=0, description="Files that encountered errors during transmission.")
    total_bytes_transmitted: int = Field(default=0, description="Total payload bytes transmitted.")
    dry_run: bool = Field(default=False, description="Whether execution was a dry-run simulation.")
    items: List[SyncItemRecord] = Field(default_factory=list, description="Detailed transmission records.")
    remote_pins: Dict[str, RemotePinRecord] = Field(default_factory=dict, description="Pinned remote revision baselines.")

