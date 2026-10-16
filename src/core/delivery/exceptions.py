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

