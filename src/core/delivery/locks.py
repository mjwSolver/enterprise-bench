"""
Enterprise Deliverable Lock Manager
====================================
Headless concurrency control for document and presentation deliverables.
Prevents dual-author overwrite collisions via sidecar `.lock` metadata files
and isolated `<stem>_LOCKED_<user>.<ext>` staging copies.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set, Union

from src.core.delivery.exceptions import (
    DeliveryError,
    LockConflictError,
    LockNotFoundError,
    LockOwnershipError,
)
from src.core.delivery.models import LockPayload, LockStatus

logger = logging.getLogger(__name__)


class LockManager:
    """
    Manages stage-gate document locks using atomic sidecar files.
    
    Conventions:
      - Original file: `deliverable.pptx`
      - Lock metadata sidecar: `deliverable.pptx.lock`
      - User working copy: `deliverable_LOCKED_<user>.pptx`
    """

    def acquire_lock(
        self,
        filepath: Union[str, Path],
        user: str,
        reason: Optional[str] = None,
    ) -> LockPayload:
        """
        Acquires a collaborative lock on the specified deliverable file.
        
        Creates:
          1. `<stem>_LOCKED_<user>.<ext>` copy for safe isolated editing.
          2. `<filename>.lock` JSON sidecar recording ownership and timestamp.
          
        Raises:
          LockNotFoundError: If target original file does not exist.
          LockConflictError: If file is already locked by another user or session.
        """
        if not user or not isinstance(user, str):
            raise ValueError("Username must be a non-empty string.")
        # Path traversal guard: disallow directory traversal tokens or path separators in user
        if any(sep in user for sep in ("/", "\\", "\0")) or ".." in user:
            raise ValueError(f"Invalid username '{user}': path separators and traversal tokens are prohibited.")

        target = Path(filepath).resolve()
        if not target.exists() or not target.is_file():
            raise LockNotFoundError(f"Cannot acquire lock: target file '{target}' does not exist.")

        lock_file = target.with_name(f"{target.name}.lock")

        # Fast-path check: if lock sidecar already exists, report active holder immediately
        if lock_file.exists():
            try:
                data = json.loads(lock_file.read_text(encoding="utf-8"))
                existing = LockPayload.model_validate(data)
                owner = existing.user or "UNKNOWN"
                locked_at = existing.locked_at or "UNKNOWN"
            except Exception:
                owner = "UNKNOWN"
                locked_at = "UNKNOWN"
            raise LockConflictError(
                f"Cannot acquire lock on '{target.name}': file is already locked by '{owner}' since {locked_at}."
            )

        # Check for any existing locked working copies matching this stem
        existing_copies = list(target.parent.glob(f"{target.stem}_LOCKED_*{target.suffix}"))
        if existing_copies:
            raise LockConflictError(
                f"Cannot acquire lock on '{target.name}': locked working copy '{existing_copies[0].name}' already exists."
            )

        locked_copy = target.parent / f"{target.stem}_LOCKED_{user}{target.suffix}"
        if locked_copy.resolve().parent != target.parent.resolve():
            raise DeliveryError(f"Security violation: working copy path resolved outside target directory.")

        # Kernel-level atomic lock creation (O_CREAT | O_EXCL) to eliminate TOCTOU race conditions
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            try:
                data = json.loads(lock_file.read_text(encoding="utf-8"))
                existing = LockPayload.model_validate(data)
                owner = existing.user or "UNKNOWN"
                locked_at = existing.locked_at or "UNKNOWN"
            except Exception:
                owner = "UNKNOWN"
                locked_at = "UNKNOWN"
            raise LockConflictError(
                f"Cannot acquire lock on '{target.name}': file is already locked by '{owner}' since {locked_at}."
            )
        except OSError as exc:
            raise DeliveryError(f"Failed to create lock sidecar '{lock_file.name}': {exc}") from exc

        # File descriptor held; guarantee cleanup and zero descriptor leaks
        fd_closed = False
        try:
            try:
                shutil.copy2(target, locked_copy)
            except OSError as exc:
                if not fd_closed:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    fd_closed = True
                lock_file.unlink(missing_ok=True)
                raise DeliveryError(f"Failed to create working copy '{locked_copy.name}': {exc}") from exc

            now_utc = datetime.now(timezone.utc).isoformat()
            payload = LockPayload(
                filepath=str(target),
                user=user,
                reason=reason,
                locked_at=now_utc,
                locked_copy_path=str(locked_copy),
                lock_file=str(lock_file),
            )

            try:
                with open(fd, "w", encoding="utf-8") as f:
                    fd_closed = True
                    f.write(payload.model_dump_json(indent=2))
            except OSError as exc:
                if locked_copy.exists():
                    locked_copy.unlink(missing_ok=True)
                lock_file.unlink(missing_ok=True)
                raise DeliveryError(f"Failed to write lock sidecar '{lock_file.name}': {exc}") from exc

        except Exception:
            if not fd_closed:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if locked_copy.exists():
                locked_copy.unlink(missing_ok=True)
            if lock_file.exists():
                lock_file.unlink(missing_ok=True)
            raise

        logger.info(
            "Acquired lock on '%s' for user '%s' (working copy: '%s')",
            target.name,
            user,
            locked_copy.name,
        )
        return payload

    def release_lock(
        self,
        filepath: Union[str, Path],
        user: str,
        merge: bool = False,
        force: bool = False,
    ) -> LockPayload:
        """
        Releases an active lock on a deliverable.
        
        Args:
          filepath: Original file, `.lock` sidecar, or `_LOCKED_` working copy.
          user: Username requesting the release.
          merge: If True, copies the working copy over the original file before cleanup.
          force: If True, permits releasing locks held by other users.
          
        Raises:
          LockNotFoundError: If no active lock exists for the file.
          LockOwnershipError: If file is locked by a different user and force=False.
        """
        target, lock_file = self._resolve_target_and_lock_paths(filepath)

        if not lock_file.exists():
            raise LockNotFoundError(f"Cannot release lock: no active lock found for '{target.name}'.")

        try:
            data = json.loads(lock_file.read_text(encoding="utf-8"))
            payload = LockPayload.model_validate(data)
        except Exception as exc:
            raise DeliveryError(f"Corrupt or unreadable lock sidecar '{lock_file}': {exc}") from exc

        if payload.user != user and not force:
            raise LockOwnershipError(
                f"Cannot release lock on '{target.name}': locked by '{payload.user}', requested by '{user}'. "
                f"Pass force=True to override ownership."
            )

        # Path traversal guard: ensure locked_copy resides strictly inside target.parent
        default_locked_copy = target.parent / f"{target.stem}_LOCKED_{payload.user}{target.suffix}"
        if payload.locked_copy_path:
            candidate_copy = Path(payload.locked_copy_path).resolve()
            if candidate_copy.parent == target.parent.resolve() or candidate_copy.is_relative_to(target.parent.resolve()):
                locked_copy = candidate_copy
            else:
                logger.warning("Rejecting untrusted working copy path '%s' outside parent directory.", payload.locked_copy_path)
                locked_copy = default_locked_copy
        else:
            locked_copy = default_locked_copy

        if merge:
            if locked_copy.exists() and locked_copy.is_file():
                try:
                    shutil.copy2(locked_copy, target)
                    logger.info("Merged working copy '%s' back into '%s'", locked_copy.name, target.name)
                except OSError as exc:
                    raise DeliveryError(
                        f"Failed merging working copy '{locked_copy.name}' into '{target.name}': {exc}"
                    ) from exc
            else:
                logger.warning(
                    "Merge requested for '%s', but working copy '%s' was not found on disk.",
                    target.name,
                    locked_copy.name,
                )

        # Cleanup working copy and lock sidecar safely without race failures
        if locked_copy.exists():
            try:
                locked_copy.unlink(missing_ok=True)
                logger.info("Cleaned up working copy '%s'", locked_copy.name)
            except OSError as exc:
                logger.warning("Could not remove working copy '%s': %s", locked_copy.name, exc)

        try:
            lock_file.unlink(missing_ok=True)
            logger.info("Removed lock sidecar '%s'", lock_file.name)
        except OSError as exc:
            if lock_file.exists():
                raise DeliveryError(f"Could not remove lock sidecar '{lock_file.name}': {exc}") from exc

        return payload

    def get_status(self, filepath: Union[str, Path]) -> LockStatus:
        """
        Queries the current lock state of a file, sidecar, or working copy.
        """
        target, lock_file = self._resolve_target_and_lock_paths(filepath)

        if lock_file.exists():
            try:
                data = json.loads(lock_file.read_text(encoding="utf-8"))
                payload = LockPayload.model_validate(data)
                return LockStatus(
                    is_locked=True,
                    target_file=str(target),
                    user=payload.user,
                    reason=payload.reason,
                    locked_at=payload.locked_at,
                    lock_file_path=str(lock_file),
                    locked_copy_path=payload.locked_copy_path,
                )
            except Exception as exc:
                logger.warning("Error reading lock sidecar '%s': %s", lock_file, exc)
                return LockStatus(
                    is_locked=True,
                    target_file=str(target),
                    user="UNKNOWN",
                    reason="Corrupted lock file",
                    lock_file_path=str(lock_file),
                )

        # Inspect if an unreferenced _LOCKED_ file exists
        orphaned_copies = list(target.parent.glob(f"{target.stem}_LOCKED_*{target.suffix}"))
        if orphaned_copies:
            return LockStatus(
                is_locked=True,
                target_file=str(target),
                locked_copy_path=str(orphaned_copies[0]),
                reason="Orphaned locked working copy present without sidecar",
            )

        return LockStatus(is_locked=False, target_file=str(target))

    def list_locks(self, directory: Union[str, Path]) -> List[LockStatus]:
        """
        Recursively scans a directory tree and returns status for all locked files.
        """
        dir_path = Path(directory).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            return []

        results: List[LockStatus] = []
        seen_targets: Set[str] = set()

        # 1. Inspect all active .lock sidecars
        for lock_file in dir_path.rglob("*.lock"):
            if not lock_file.is_file():
                continue
            orig_name = lock_file.name[:-5]
            target_path = lock_file.with_name(orig_name)
            seen_targets.add(str(target_path))
            results.append(self.get_status(target_path))

        # 2. Check for any orphaned working copies without lock files
        for copy_file in dir_path.rglob("*_LOCKED_*"):
            if not copy_file.is_file() or copy_file.name.endswith(".lock"):
                continue
            stem_orig, sep, _ = copy_file.stem.rpartition("_LOCKED_")
            if sep:
                target_path = copy_file.with_name(f"{stem_orig}{copy_file.suffix}")
                if str(target_path) not in seen_targets:
                    seen_targets.add(str(target_path))
                    results.append(self.get_status(target_path))

        results.sort(key=lambda s: s.target_file)
        return results

    def _resolve_target_and_lock_paths(self, filepath: Union[str, Path]) -> tuple[Path, Path]:
        """Normalizes input path into (target_original_path, lock_sidecar_path)."""
        p = Path(filepath).resolve()
        if p.name.endswith(".lock"):
            orig_name = p.name[:-5]
            target = p.with_name(orig_name)
            lock_file = p
        elif "_LOCKED_" in p.stem:
            stem_orig, _, _ = p.stem.rpartition("_LOCKED_")
            target = p.with_name(f"{stem_orig}{p.suffix}")
            lock_file = target.with_name(f"{target.name}.lock")
        else:
            target = p
            lock_file = target.with_name(f"{target.name}.lock")
        return target, lock_file
