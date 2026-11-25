"""
Enterprise Google Drive Remote Transmission & Sync Layer
=========================================================
Differential synchronization engine pushing staged deliverables from
`.staging_manifest.json` or `DeliveryManifest` to shared Google Drive targets.
Includes mount auto-discovery, SHA-256 differential transmission, atomic writes,
remote lock collision guards, and receipt logging.
"""

from __future__ import annotations

import glob
import hashlib
import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from src.core.delivery.exceptions import (
    LockConflictError,
    PreflightGateError,
    RemoteConflictError,
    RemoteLockConflictError,
    SyncTransmissionError,
)
from src.core.delivery.locks import LockManager
from src.core.delivery.models import (
    RemotePinRecord,
    SyncItemRecord,
    SyncReceipt,
    SyncStatus,
)
from src.core.delivery import remote_guard as _remote_guard
from src.core.delivery.remote_guard import (
    RemoteDriftGuard,
    _file_revision_token,
    _write_json_atomic,
)

logger = logging.getLogger(__name__)


def _compute_sha256(file_path: Path) -> str:
    """Calculates SHA-256 hash of a file in 64KB streaming chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def discover_google_drive_mounts() -> List[Path]:
    """
    Auto-discovers locally mounted Google Drive instances on macOS / Linux.
    Returns ordered list of candidate root paths.
    """
    candidates: List[Path] = []

    # 1. macOS FileProvider / CloudStorage location
    cloud_storage = Path.home() / "Library" / "CloudStorage"
    if cloud_storage.exists() and cloud_storage.is_dir():
        for d in sorted(cloud_storage.iterdir()):
            if d.is_dir() and d.name.startswith("GoogleDrive-"):
                candidates.append(d)

    # 2. macOS /Volumes mount point (Google Drive Desktop legacy or volume mode)
    vol_gdrive = Path("/Volumes/GoogleDrive")
    if vol_gdrive.exists() and vol_gdrive.is_dir():
        candidates.append(vol_gdrive)

    # 3. Standard user home shortcuts
    home_gdrive = Path.home() / "Google Drive"
    if home_gdrive.exists() and home_gdrive.is_dir():
        candidates.append(home_gdrive)

    home_gdrive_nospace = Path.home() / "GoogleDrive"
    if home_gdrive_nospace.exists() and home_gdrive_nospace.is_dir():
        candidates.append(home_gdrive_nospace)

    return candidates


def resolve_target_drive_root(
    target_root_name: str = "Deliverables",
    drive_base: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Resolves the absolute destination folder on Google Drive.

    Precedence:
      1. Explicit `drive_base` argument
      2. Environment variable `GOOGLE_DRIVE_ROOT` or `GDRIVE_ROOT`
      3. Auto-discovered macOS / Linux Google Drive CloudStorage mounts
      4. Local fallback directory if no cloud storage mount exists
    """
    # 1. Explicit base directory
    if drive_base:
        p = Path(drive_base).resolve()
        # If the explicit path already ends with target_root_name, use it directly
        if p.name == target_root_name:
            return p
        return p / target_root_name

    # 2. Environment variables
    for env_var in ("GOOGLE_DRIVE_ROOT", "GDRIVE_ROOT"):
        if env_var in os.environ and os.environ[env_var].strip():
            p = Path(os.environ[env_var].strip()).resolve()
            if p.name == target_root_name:
                return p
            return p / target_root_name

    # 3. Auto-discovery of mounted Google Drive
    mounts = discover_google_drive_mounts()
    for m in mounts:
        # Check 'Shared drives' first
        shared_drives = m / "Shared drives"
        if shared_drives.exists() and shared_drives.is_dir():
            target_in_shared = shared_drives / target_root_name
            if target_in_shared.exists():
                return target_in_shared

        # Check 'My Drive' next
        my_drive = m / "My Drive"
        if my_drive.exists() and my_drive.is_dir():
            target_in_my_drive = my_drive / target_root_name
            return target_in_my_drive

        # If neither exists but shared_drives directory exists, target shared
        if shared_drives.exists():
            return shared_drives / target_root_name

        # If mount exists directly
        return m / target_root_name

    # 4. Fallback: check if target_root_name is an existing path or default to local directory
    p_fallback = Path(target_root_name)
    if p_fallback.is_absolute():
        return p_fallback

    logger.warning("No mounted Google Drive detected. Falling back to local destination: '%s'", target_root_name)
    return (Path.cwd() / target_root_name).resolve()


class RemoteSyncEngine:
    """
    Transmission engine executing differential synchronization between
    staged deliverables and Google Drive remote target roots.
    """

    def __init__(self, lock_manager: Optional[LockManager] = None) -> None:
        self.lock_mgr = lock_manager or LockManager()

    def parse_manifest(
        self,
        manifest_path: Union[str, Path],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parses manifest file into a uniform list of deliverable item dictionaries.
        Supports both hierarchical `.staging_manifest.json` and flat `DeliveryManifest`.
        """
        mpath = Path(manifest_path).resolve()
        if not mpath.exists():
            raise FileNotFoundError(f"Manifest not found at: '{mpath}'")

        try:
            with open(mpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise ValueError(f"Failed to parse manifest JSON at '{mpath}': {exc}")

        items: List[Dict[str, Any]] = []
        target_root = data.get("drive_target_root", "Deliverables")

        # Format A: Categorized manifest (doc_output/.staging_manifest.json)
        if "categories" in data and isinstance(data["categories"], dict):
            for category_name, file_records in data["categories"].items():
                for rec in file_records:
                    items.append({
                        "name": rec.get("name", Path(rec.get("local_relpath", "")).name),
                        "category": category_name,
                        "ext": rec.get("ext", Path(rec.get("name", "")).suffix.lower()),
                        "sha256": rec.get("sha256", ""),
                        "size_bytes": rec.get("size_bytes", 0),
                        "local_relpath": rec.get("local_relpath", ""),
                        "drive_relpath": rec.get("drive_relpath", f"{target_root}/{category_name}/{rec.get('name')}"),
                    })

        # Format B: Flat DeliveryManifest (delivery_manifest.json)
        elif "files" in data and isinstance(data["files"], list):
            target_root = data.get("target_drive_root", target_root)
            for rec in data["files"]:
                rel_p = rec.get("relative_path", "")
                cat = Path(rel_p).parent.as_posix() if Path(rel_p).parent.as_posix() != "." else None
                name = Path(rel_p).name
                items.append({
                    "name": name,
                    "category": cat,
                    "ext": Path(name).suffix.lower(),
                    "sha256": rec.get("sha256", ""),
                    "size_bytes": rec.get("file_size_bytes", 0),
                    "local_relpath": rel_p,
                    "drive_relpath": rec.get("target_drive_path", f"{target_root}/{rel_p}"),
                })
        else:
            raise ValueError(f"Unrecognized manifest structure in: '{mpath}'")

        return target_root, items

    def sync(
        self,
        manifest_path: Union[str, Path],
        target_drive_root: Optional[str] = None,
        drive_base_dir: Optional[Union[str, Path]] = None,
        categories: Optional[List[str]] = None,
        formats: Optional[List[str]] = None,
        dry_run: bool = False,
        fail_on_locks: bool = True,
        output_receipt_path: Optional[Union[str, Path]] = None,
        progress_callback: Optional[Callable[[int, int, str, SyncStatus], None]] = None,
        strict_cas: bool = False,
        current_user: Optional[str] = None,
        branch_on_conflict: bool = True,
        lock_ttl_seconds: int = 7200,
    ) -> SyncReceipt:
        """
        Executes differential synchronization of staged deliverables to Google Drive.

        Args:
          manifest_path: Path to `.staging_manifest.json` or `delivery_manifest.json`.
          target_drive_root: Target Google Drive folder name (e.g. 'Deliverables').
          drive_base_dir: Explicit local base mount point for Google Drive.
          categories: Optional list of category names to filter.
          formats: Optional list of file extensions to filter (e.g. ['.pptx']).
          dry_run: If True, previews operations without writing or modifying files.
          fail_on_locks: If True, aborts if active collaborative locks are detected.
          output_receipt_path: Optional path to write `.sync_receipt.json`.
          progress_callback: Optional progress hook (current, total, filename, status).

        Returns:
          SyncReceipt containing full audit trail and transmission metrics.
        """
        mpath = Path(manifest_path).resolve()
        manifest_dir = mpath.parent
        # Candidate local roots: either manifest directory or its parent (e.g. project root)
        project_root = manifest_dir.parent

        manifest_target_root, all_items = self.parse_manifest(mpath)
        target_folder_name = target_drive_root or manifest_target_root

        # Resolve destination root
        resolved_drive_root = resolve_target_drive_root(target_folder_name, drive_base=drive_base_dir)

        # Gate 1: Check active locks in manifest directory
        if fail_on_locks:
            active_locks = self.lock_mgr.list_locks(manifest_dir)
            if active_locks:
                locked_names = [Path(l.target_file).name for l in active_locks]
                raise LockConflictError(
                    f"Sync transmission blocked by active lock(s) on: {', '.join(locked_names)}"
                )

        # Apply category and format filters
        candidate_items = all_items
        if categories:
            norm_cats = [c.lower() for c in categories]
            candidate_items = [it for it in candidate_items if it.get("category") and it["category"].lower() in norm_cats]

        if formats:
            norm_fmts = [f.lower() if f.startswith(".") else f".{f.lower()}" for f in formats]
            candidate_items = [it for it in candidate_items if it.get("ext") and it["ext"].lower() in norm_fmts]

        total_files = len(candidate_items)
        transmitted_count = 0
        skipped_count = 0
        failed_count = 0
        total_bytes_transmitted = 0
        records: List[SyncItemRecord] = []

        receipt_target_p = Path(output_receipt_path) if output_receipt_path else manifest_dir / ".sync_receipt.json"
        prior_pins = RemoteDriftGuard.load_pins(receipt_target_p)
        updated_pins: Dict[str, RemotePinRecord] = dict(prior_pins)

        now_utc = datetime.now(timezone.utc)
        sync_id = f"SYNC-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

        try:
            for idx, item in enumerate(candidate_items, start=1):
                name = item["name"]
                cat = item.get("category")
                sha_expected = item.get("sha256", "")
                size_bytes = item.get("size_bytes", 0)
                local_rel = item.get("local_relpath", "")

                # Resolve local source path
                local_file: Optional[Path] = None
                for candidate_p in [
                    project_root / local_rel,
                    manifest_dir / local_rel,
                    manifest_dir / (cat or "") / name,
                    Path(local_rel),
                ]:
                    if candidate_p.exists() and candidate_p.is_file():
                        local_file = candidate_p
                        break

                if not local_file:
                    err_msg = f"Source file does not exist locally: '{local_rel}'"
                    failed_count += 1
                    rec = SyncItemRecord(
                        name=name,
                        category=cat,
                        relative_path=local_rel,
                        target_drive_path=str(resolved_drive_root / (cat or "") / name),
                        size_bytes=size_bytes,
                        sha256=sha_expected,
                        status=SyncStatus.FAILED,
                        error_message=err_msg,
                    )
                    records.append(rec)
                    if progress_callback:
                        progress_callback(idx, total_files, name, SyncStatus.FAILED)
                    continue

                if not sha_expected:
                    try:
                        sha_expected = _compute_sha256(local_file)
                    except Exception as exc:
                        logger.debug("Could not compute source sha256 for '%s': %s", local_file, exc)

                # Resolve remote destination path
                # item["drive_relpath"] typically starts with f"{target_folder_name}/..."
                drive_rel = item.get("drive_relpath", "")
                clean_drive_rel = drive_rel
                if clean_drive_rel.startswith(f"{target_folder_name}/"):
                    clean_drive_rel = clean_drive_rel[len(target_folder_name) + 1 :]
                elif cat and name:
                    clean_drive_rel = f"{cat}/{name}"
                else:
                    clean_drive_rel = name

                dest_path = resolved_drive_root / clean_drive_rel

                # Gate 2: Destination Lock Collision Check (local-style locks + remote JSON sidecars)
                dest_parent = dest_path.parent
                dest_stem = dest_path.stem
                dest_ext = dest_path.suffix
                if dest_parent.exists():
                    remote_locks = list(dest_parent.glob(f"{dest_stem}_LOCKED_*{dest_ext}"))
                    remote_lockfiles = list(dest_parent.glob(f"{dest_path.name}.lock"))
                    sidecar_lock = RemoteDriftGuard.check_remote_lock_sidecars(
                        dest_parent,
                        current_user=current_user,
                        default_ttl_seconds=lock_ttl_seconds,
                        target_file_name=dest_path.name,
                    )
                    if remote_locks or remote_lockfiles or sidecar_lock is not None:
                        if sidecar_lock is not None:
                            err_msg = (
                                f"Remote destination file '{dest_path.name}' is locked by "
                                f"'{sidecar_lock.locked_by}' (sidecar lock since {sidecar_lock.locked_at})."
                            )
                        else:
                            err_msg = f"Remote destination file is actively LOCKED by a collaborator: '{dest_path.name}'"
                        if fail_on_locks:
                            raise RemoteLockConflictError(err_msg)
                        rec = SyncItemRecord(
                            name=name,
                            category=cat,
                            relative_path=local_rel,
                            target_drive_path=str(dest_path),
                            size_bytes=size_bytes,
                            sha256=sha_expected,
                            status=SyncStatus.LOCKED_CONFLICT,
                            error_message=err_msg,
                        )
                        records.append(rec)
                        failed_count += 1
                        if progress_callback:
                            progress_callback(idx, total_files, name, SyncStatus.LOCKED_CONFLICT)
                        continue

                # Gate 3: Compare-And-Set (CAS) Remote Revision Pinning Guard
                pin_key = local_rel or name
                matched_pin_key: Optional[str] = None
                prior_pin = prior_pins.get(pin_key)
                if prior_pin is not None:
                    matched_pin_key = pin_key
                else:
                    dest_resolved = str(dest_path.resolve())
                    for cand_key, cand_pin in prior_pins.items():
                        if not cand_pin.target_drive_path:
                            continue
                        try:
                            if (
                                cand_pin.target_drive_path == str(dest_path)
                                or str(Path(cand_pin.target_drive_path).resolve()) == dest_resolved
                            ):
                                prior_pin = cand_pin
                                matched_pin_key = cand_key
                                break
                        except OSError:
                            continue
                if strict_cas and prior_pin is not None and (dest_path.exists() or prior_pin.file_id):
                    RemoteDriftGuard.verify_cas(
                        pin=prior_pin,
                        remote_path=dest_path,
                        branch_on_conflict=(branch_on_conflict and not dry_run),
                        conflict_dir=manifest_dir,
                    )

                # Differential Hash Evaluation
                is_identical = False
                if dest_path.exists() and dest_path.is_file():
                    try:
                        dest_sha = _compute_sha256(dest_path)
                        if dest_sha == sha_expected:
                            is_identical = True
                    except Exception as exc:
                        logger.warning("Could not compute remote hash for '%s': %s", dest_path, exc)

                if is_identical:
                    skipped_count += 1
                    rev_id, md5_hex, sha_hex, mod_iso = _file_revision_token(dest_path)
                    if prior_pin is not None and prior_pin.file_id:
                        gmeta = _remote_guard.query_gdrive_file_metadata(prior_pin.file_id)
                        if gmeta:
                            rev_id = str(gmeta.get("headRevisionId") or prior_pin.base_revision_id or rev_id)
                            md5_hex = str(gmeta.get("md5Checksum") or prior_pin.base_md5 or md5_hex)
                            mod_iso = str(gmeta.get("modifiedTime") or prior_pin.base_modified_time or mod_iso)
                        else:
                            rev_id = prior_pin.base_revision_id or rev_id
                            md5_hex = prior_pin.base_md5 or md5_hex
                            mod_iso = prior_pin.base_modified_time or mod_iso
                    if not dry_run:
                        if matched_pin_key and matched_pin_key != pin_key:
                            updated_pins.pop(matched_pin_key, None)
                        updated_pins[pin_key] = RemotePinRecord(
                            file_id=prior_pin.file_id if prior_pin else None,
                            local_path=pin_key,
                            target_drive_path=str(dest_path),
                            base_revision_id=rev_id,
                            base_md5=md5_hex,
                            base_sha256=sha_hex,
                            base_modified_time=mod_iso,
                            checkout_user=current_user,
                        )
                    rec = SyncItemRecord(
                        name=name,
                        category=cat,
                        relative_path=local_rel,
                        target_drive_path=str(dest_path),
                        size_bytes=size_bytes,
                        sha256=sha_expected,
                        status=SyncStatus.SKIPPED_IDENTICAL,
                        base_revision_id=rev_id,
                        base_md5=md5_hex,
                        remote_modified_time=mod_iso,
                    )
                    records.append(rec)
                    if progress_callback:
                        progress_callback(idx, total_files, name, SyncStatus.SKIPPED_IDENTICAL)
                    continue

                # Execution (Dry-Run vs Real Transmission)
                if dry_run:
                    transmitted_count += 1
                    total_bytes_transmitted += size_bytes
                    rec = SyncItemRecord(
                        name=name,
                        category=cat,
                        relative_path=local_rel,
                        target_drive_path=str(dest_path),
                        size_bytes=size_bytes,
                        sha256=sha_expected,
                        status=SyncStatus.DRY_RUN,
                    )
                    records.append(rec)
                    if progress_callback:
                        progress_callback(idx, total_files, name, SyncStatus.DRY_RUN)
                    continue

                # Atomic Transmission via Temporary Staging File
                temp_dest: Optional[Path] = None
                try:
                    dest_parent.mkdir(parents=True, exist_ok=True)
                    temp_dest = dest_parent / f".{dest_path.name}.tmp_{uuid.uuid4().hex[:6]}"

                    shutil.copy2(local_file, temp_dest)
                    written_sha = _compute_sha256(temp_dest)
                    if sha_expected and written_sha != sha_expected:
                        if temp_dest.exists():
                            temp_dest.unlink()
                        raise SyncTransmissionError(
                            f"Checksum mismatch after transmission for '{name}': expected {sha_expected}, got {written_sha}"
                        )

                    # Atomic swap into target path
                    temp_dest.replace(dest_path)

                    rev_id, md5_hex, sha_hex, mod_iso = _file_revision_token(dest_path)
                    if prior_pin is not None and prior_pin.file_id:
                        gmeta = _remote_guard.query_gdrive_file_metadata(prior_pin.file_id)
                        if gmeta:
                            rev_id = str(gmeta.get("headRevisionId") or rev_id)
                            md5_hex = str(gmeta.get("md5Checksum") or md5_hex)
                            mod_iso = str(gmeta.get("modifiedTime") or mod_iso)
                    if matched_pin_key and matched_pin_key != pin_key:
                        updated_pins.pop(matched_pin_key, None)
                    updated_pins[pin_key] = RemotePinRecord(
                        file_id=prior_pin.file_id if prior_pin else None,
                        local_path=pin_key,
                        target_drive_path=str(dest_path),
                        base_revision_id=rev_id,
                        base_md5=md5_hex,
                        base_sha256=sha_hex,
                        base_modified_time=mod_iso,
                        checkout_user=current_user,
                    )

                    transmitted_count += 1
                    total_bytes_transmitted += size_bytes
                    rec = SyncItemRecord(
                        name=name,
                        category=cat,
                        relative_path=local_rel,
                        target_drive_path=str(dest_path),
                        size_bytes=size_bytes,
                        sha256=sha_expected,
                        status=SyncStatus.TRANSMITTED,
                        base_revision_id=rev_id,
                        base_md5=md5_hex,
                        remote_modified_time=mod_iso,
                    )
                    records.append(rec)
                    if progress_callback:
                        progress_callback(idx, total_files, name, SyncStatus.TRANSMITTED)

                except Exception as exc:
                    if temp_dest is not None and temp_dest.exists():
                        try:
                            temp_dest.unlink(missing_ok=True)
                        except OSError:
                            pass
                    failed_count += 1
                    err_msg = f"Transmission failed: {exc}"
                    logger.error("Failed to sync '%s' to '%s': %s", local_file, dest_path, exc)
                    rec = SyncItemRecord(
                        name=name,
                        category=cat,
                        relative_path=local_rel,
                        target_drive_path=str(dest_path),
                        size_bytes=size_bytes,
                        sha256=sha_expected,
                        status=SyncStatus.FAILED,
                        error_message=err_msg,
                    )
                    records.append(rec)
                    if progress_callback:
                        progress_callback(idx, total_files, name, SyncStatus.FAILED)
        except (RemoteConflictError, RemoteLockConflictError) as exc:
            if not dry_run and (records or updated_pins != prior_pins):
                failed_count += 1
                if isinstance(exc, RemoteConflictError):
                    aborted_rec = SyncItemRecord(
                        name=name,
                        category=cat,
                        relative_path=local_rel,
                        target_drive_path=str(dest_path),
                        size_bytes=size_bytes,
                        sha256=sha_expected,
                        status=SyncStatus.REMOTE_CONFLICT,
                        error_message=str(exc),
                        base_revision_id=exc.base_revision_id,
                        base_md5=exc.base_hash,
                        remote_modified_time=exc.remote_modified_time,
                        conflict_branch_path=exc.conflict_branch_path,
                    )
                else:
                    aborted_rec = SyncItemRecord(
                        name=name,
                        category=cat,
                        relative_path=local_rel,
                        target_drive_path=str(dest_path),
                        size_bytes=size_bytes,
                        sha256=sha_expected,
                        status=SyncStatus.LOCKED_CONFLICT,
                        error_message=str(exc),
                    )
                records.append(aborted_rec)
                if progress_callback:
                    progress_callback(idx, total_files, name, aborted_rec.status)
                partial_receipt = SyncReceipt(
                    sync_id=sync_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    source_manifest=str(mpath),
                    resolved_target_root=str(resolved_drive_root),
                    checkout_user=current_user,
                    total_files=total_files,
                    transmitted_count=transmitted_count,
                    skipped_count=skipped_count,
                    failed_count=failed_count,
                    total_bytes_transmitted=total_bytes_transmitted,
                    dry_run=dry_run,
                    items=records,
                    remote_pins=updated_pins,
                )
                try:
                    _write_json_atomic(receipt_target_p, partial_receipt.model_dump_json(indent=2))
                    logger.info("Saved partial sync receipt after conflict to: '%s'", receipt_target_p)
                except Exception as write_exc:
                    logger.warning("Could not persist partial sync receipt to '%s': %s", receipt_target_p, write_exc)
            raise

        receipt = SyncReceipt(
            sync_id=sync_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_manifest=str(mpath),
            resolved_target_root=str(resolved_drive_root),
            checkout_user=current_user,
            total_files=total_files,
            transmitted_count=transmitted_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            total_bytes_transmitted=total_bytes_transmitted,
            dry_run=dry_run,
            items=records,
            remote_pins=updated_pins,
        )

        # Write sync receipt to file (never mutate disk during dry-run)
        if not dry_run:
            try:
                _write_json_atomic(receipt_target_p, receipt.model_dump_json(indent=2))
                logger.info("Saved sync receipt to: '%s'", receipt_target_p)
            except Exception as exc:
                logger.warning("Could not persist sync receipt to '%s': %s", receipt_target_p, exc)

        return receipt
