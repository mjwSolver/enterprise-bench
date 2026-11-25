"""
Enterprise Delivery Subsystem Exceptions
========================================
Typed domain exceptions for lock management, overlay stamping, and staging preflight.
"""

from __future__ import annotations


class DeliveryError(Exception):
    """Base exception for all enterprise delivery subsystem errors."""
    pass


class LockConflictError(DeliveryError):
    """Raised when an operation conflicts with an existing file lock."""
    pass


class LockNotFoundError(DeliveryError):
    """Raised when attempting to release or query a lock that does not exist."""
    pass


class LockOwnershipError(DeliveryError):
    """Raised when a user attempts to release a lock owned by another user without force."""
    pass


class PreflightGateError(DeliveryError):
    """Raised when a staging preflight validation gate fails."""
    pass


class SyncTransmissionError(DeliveryError):
    """Raised when remote transmission fails or data verification mismatches."""
    pass


class RemoteLockConflictError(DeliveryError):
    """Raised when remote destination is locked or collision guard triggers."""
    pass


class RemoteConflictError(DeliveryError):
    """Raised when remote CAS (Compare-And-Set) validation detects out-of-band drift."""

    def __init__(
        self,
        file_name: str,
        base_revision_id: Optional[str] = None,
        remote_revision_id: Optional[str] = None,
        base_hash: Optional[str] = None,
        remote_hash: Optional[str] = None,
        remote_modified_by: Optional[str] = None,
        remote_modified_time: Optional[str] = None,
        conflict_branch_path: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.file_name = file_name
        self.base_revision_id = base_revision_id
        self.remote_revision_id = remote_revision_id
        self.base_hash = base_hash
        self.remote_hash = remote_hash
        self.remote_modified_by = remote_modified_by
        self.remote_modified_time = remote_modified_time
        self.conflict_branch_path = conflict_branch_path

        if message:
            full_msg = message
        else:
            parts = [
                f"Remote conflict detected for '{file_name}' (CAS validation failed).",
                f"  Base Revision:   {base_revision_id or 'N/A'} (hash: {(base_hash or 'N/A')[:12]})",
                f"  Remote Revision: {remote_revision_id or 'N/A'} (hash: {(remote_hash or 'N/A')[:12]})",
            ]
            if remote_modified_by or remote_modified_time:
                parts.append(
                    f"  Modified By:     {remote_modified_by or 'unknown'} at {remote_modified_time or 'unknown'}"
                )
            if conflict_branch_path:
                parts.append(f"  Remote Branch:   {conflict_branch_path}")
            full_msg = "\n".join(parts)
        super().__init__(full_msg)


