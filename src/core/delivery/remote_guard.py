"""
Enterprise Delivery - Remote Cloud Drift & Multi-Agent Race Condition Guard
===========================================================================
Implements Optimistic Concurrency Control (OCC) via Compare-And-Set (CAS)
revision pinning, remote lock sidecars (`._LOCKED_<user>_<ts>.json`),
out-of-band drift detection, and slide-level 3-way reconciliation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.core.delivery.exceptions import (
    DeliveryError,
    LockOwnershipError,
    RemoteConflictError,
    RemoteLockConflictError,
)
from src.core.delivery.models import (
    DriftCheckItem,
    DriftReport,
    RemoteLockSidecar,
    RemotePinRecord,
    SyncReceipt,
)

logger = logging.getLogger(__name__)


def _compute_md5(file_path: Path) -> str:
    """Calculates MD5 hex digest of a file in 64KB chunks."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _compute_sha256(file_path: Path) -> str:
    """Calculates SHA-256 hex digest of a file in 64KB chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _file_revision_token(path: Path) -> Tuple[str, str, str, str]:
    """
    Returns `(revision_id, md5, sha256, modified_iso)` for a file on disk
    or mounted Google Drive.
    """
    st = path.stat()
    md5 = _compute_md5(path)
    sha256 = _compute_sha256(path)
    mod_dt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    rev_id = f"rev-{st.st_mtime_ns}-{st.st_size}-{md5[:8]}"
    return (rev_id, md5, sha256, mod_dt)


def _write_json_atomic(target_path: Path, payload_text: str) -> None:
    """Atomically writes JSON text via temp file in the same directory + os.replace."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_p = target_path.parent / f".{target_path.name}.tmp_{uuid.uuid4().hex[:8]}"
    try:
        tmp_p.write_text(payload_text, encoding="utf-8")
        os.replace(tmp_p, target_path)
    except Exception:
        if tmp_p.exists():
            tmp_p.unlink(missing_ok=True)
        raise


def query_gdrive_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Optionally queries `gdrive readonly info <file_id>` if the `gdrive` CLI is
    installed and authenticated. Returns parsed JSON dict or None if unavailable.
    """
    if not file_id or not shutil.which("gdrive"):
        return None
    try:
        res = subprocess.run(
            ["gdrive", "readonly", "info", str(file_id), "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode != 0 or not res.stdout.strip():
            return None
        data = json.loads(res.stdout)
        return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.debug("gdrive readonly info failed for %s: %s", file_id, exc)
        return None


class RemoteDriftGuard:
    """
    Coordinates remote revision pinning, CAS conflict detection, remote lock
    sidecars, drift polling, and slide-level 3-way reconciliation.
    """

    @staticmethod
    def load_pins(receipt_path: Union[str, Path]) -> Dict[str, RemotePinRecord]:
        """Loads pinned remote baselines from `.sync_receipt.json`."""
        rp = Path(receipt_path)
        if not rp.exists():
            return {}
        try:
            data = json.loads(rp.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.debug("Could not parse receipt %s: %s", rp, exc)
            return {}

        pins: Dict[str, RemotePinRecord] = {}
        raw_pins = data.get("remote_pins")
        if isinstance(raw_pins, dict):
            for key, val in raw_pins.items():
                try:
                    pins[key] = RemotePinRecord.model_validate(val)
                except Exception:
                    continue

        # Fallback: extract pins from item records if remote_pins wasn't populated
        if not pins and isinstance(data.get("items"), list):
            for it in data["items"]:
                if not isinstance(it, dict):
                    continue
                target_p = it.get("target_drive_path")
                rev_id = it.get("base_revision_id")
                md5 = it.get("base_md5")
                if target_p and rev_id and md5:
                    rel_key = it.get("relative_path") or it.get("name") or target_p
                    pins[rel_key] = RemotePinRecord(
                        file_id=it.get("remote_file_id"),
                        local_path=it.get("relative_path") or it.get("name") or "",
                        target_drive_path=target_p,
                        base_revision_id=rev_id,
                        base_md5=md5,
                        base_sha256=it.get("sha256", ""),
                        base_modified_time=it.get("remote_modified_time") or data.get("timestamp", ""),
                        checkout_user=data.get("checkout_user"),
                    )
        return pins

    @staticmethod
    def pin_checkout(
        receipt_path: Union[str, Path],
        local_path: Union[str, Path],
        target_drive_path: Union[str, Path],
        checkout_user: str,
        file_id: Optional[str] = None,
        revision_id: Optional[str] = None,
    ) -> RemotePinRecord:
        """
        Records a checkout baseline pin into `.sync_receipt.json` from the remote
        file (or local file if remote does not exist yet) and optional `gdrive` metadata.
        """
        rp = Path(receipt_path)
        local_p = Path(local_path)
        remote_p = Path(target_drive_path)

        source_for_hash = remote_p if remote_p.exists() and remote_p.is_file() else local_p
        if not source_for_hash.exists():
            raise FileNotFoundError(
                f"Neither remote '{remote_p}' nor local '{local_p}' exists to pin baseline."
            )

        rev_id, md5, sha256, mod_iso = _file_revision_token(source_for_hash)
        if revision_id:
            rev_id = revision_id

        if file_id:
            gmeta = query_gdrive_file_metadata(file_id)
            if gmeta:
                rev_id = str(gmeta.get("headRevisionId") or rev_id)
                md5 = str(gmeta.get("md5Checksum") or md5)
                mod_iso = str(gmeta.get("modifiedTime") or mod_iso)

        rp_dir = rp.parent.resolve()
        local_abs = local_p.resolve()
        if local_abs.is_relative_to(rp_dir) and local_abs != rp_dir:
            pin_key = local_abs.relative_to(rp_dir).as_posix()
        elif not local_p.is_absolute():
            pin_key = local_p.as_posix()
        else:
            pin_key = str(local_abs)

        pin = RemotePinRecord(
            file_id=file_id,
            local_path=pin_key,
            target_drive_path=str(remote_p),
            base_revision_id=rev_id,
            base_md5=md5,
            base_sha256=sha256,
            base_modified_time=mod_iso,
            checkout_user=checkout_user,
        )

        # Merge into existing receipt or create a minimal SyncReceipt
        receipt_obj: SyncReceipt
        if rp.exists():
            try:
                receipt_obj = SyncReceipt.model_validate_json(rp.read_text(encoding="utf-8"))
            except Exception:
                receipt_obj = SyncReceipt(
                    sync_id=f"PIN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    source_manifest=str(rp.parent / "delivery_manifest.json"),
                    resolved_target_root=str(remote_p.parent),
                    checkout_user=checkout_user,
                )
        else:
            receipt_obj = SyncReceipt(
                sync_id=f"PIN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                source_manifest=str(rp.parent / "delivery_manifest.json"),
                resolved_target_root=str(remote_p.parent),
                checkout_user=checkout_user,
            )

        receipt_obj.checkout_user = checkout_user
        receipt_obj.remote_pins[pin_key] = pin
        _write_json_atomic(rp, receipt_obj.model_dump_json(indent=2))
        return pin

    @staticmethod
    def acquire_remote_lock_sidecar(
        remote_dir: Union[str, Path],
        file_name: str,
        user: str,
        ttl_seconds: int = 7200,
        reason: Optional[str] = None,
        fail_on_conflict: bool = True,
    ) -> Path:
        """Atomically writes a remote sidecar lock `._LOCKED_<user>_<ts>_<uid>.json`."""
        if ttl_seconds <= 0:
            raise ValueError(f"ttl_seconds must be positive (> 0), got {ttl_seconds}")
        if not user or not user.strip():
            raise ValueError("user must be a non-empty string.")
        cleaned_file_name = file_name.strip() if file_name else ""
        raw_segments = re.split(r"[/\\]", cleaned_file_name) if cleaned_file_name else []
        if (
            not cleaned_file_name
            or cleaned_file_name.endswith(("/", "\\"))
            or raw_segments[-1] in {"", ".", ".."}
        ):
            raise ValueError("file_name must be a non-empty filename.")
        norm_file_name = Path(cleaned_file_name).name
        if not norm_file_name or norm_file_name in {".", ".."}:
            raise ValueError("file_name must be a non-empty filename.")

        rdir = Path(remote_dir)
        if rdir.exists() and not rdir.is_dir():
            raise DeliveryError(f"Remote lock directory path is not a directory: '{rdir}'.")
        if fail_on_conflict:
            existing_lock = RemoteDriftGuard.check_remote_lock_sidecars(
                rdir,
                current_user=user,
                default_ttl_seconds=ttl_seconds,
                target_file_name=norm_file_name,
            )
            if existing_lock is not None:
                raise RemoteLockConflictError(
                    f"Remote file '{norm_file_name}' is already locked by '{existing_lock.locked_by}' "
                    f"(since {existing_lock.locked_at})."
                )

        rdir.mkdir(parents=True, exist_ok=True)
        safe_user = re.sub(r"[^a-zA-Z0-9_.-]", "_", user) or "agent"
        now_utc = datetime.now(timezone.utc)
        ts_str = now_utc.strftime("%Y%m%dT%H%M%SZ")
        lock_uid = uuid.uuid4().hex[:6]
        lock_path = rdir / f"._LOCKED_{safe_user}_{ts_str}_{lock_uid}.json"
        tmp_path = rdir / f".tmp_lock_{uuid.uuid4().hex[:8]}.json"

        payload = RemoteLockSidecar(
            file_name=norm_file_name,
            locked_by=user,
            locked_at=now_utc.isoformat(),
            ttl_seconds=ttl_seconds,
            reason=reason,
            lock_path=str(lock_path),
        )
        try:
            tmp_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp_path, lock_path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
        return lock_path

    @staticmethod
    def release_remote_lock_sidecar(
        lock_path: Union[str, Path],
        user: Optional[str] = None,
        force: bool = False,
    ) -> bool:
        """Validates sidecar format/ownership and removes a remote lock sidecar cleanly."""
        lp = Path(lock_path)
        if not lp.exists() or not lp.is_file():
            return False

        if not (lp.name.startswith("._LOCKED_") and lp.suffix == ".json"):
            raise DeliveryError(
                f"Refusing to delete non-sidecar file '{lp.name}' (expected '._LOCKED_*.json')."
            )

        try:
            raw = json.loads(lp.read_text(encoding="utf-8"))
            sidecar: Optional[RemoteLockSidecar] = RemoteLockSidecar.model_validate(raw)
        except Exception as exc:
            if not force:
                raise DeliveryError(f"Invalid or corrupt remote lock sidecar '{lp.name}': {exc}") from exc
            sidecar = None

        if user is not None and not force and sidecar is not None:
            if sidecar.locked_by.strip().lower() != user.strip().lower():
                raise LockOwnershipError(
                    f"Cannot release remote lock '{lp.name}': locked by '{sidecar.locked_by}', "
                    f"requested by '{user}'. Pass force=True to override."
                )

        lp.unlink()
        return True

    @staticmethod
    def check_remote_lock_sidecars(
        remote_dir: Union[str, Path],
        current_user: Optional[str] = None,
        default_ttl_seconds: int = 7200,
        target_file_name: Optional[str] = None,
    ) -> Optional[RemoteLockSidecar]:
        """
        Inspects `._LOCKED_*.json` sidecars in `remote_dir`.
        Ignores malformed files, expired locks (`age > ttl_seconds`), and locks
        owned by `current_user`. Returns the first active conflicting sidecar.
        """
        rdir = Path(remote_dir)
        if not rdir.exists() or not rdir.is_dir():
            return None

        now_utc = datetime.now(timezone.utc)
        for cand in sorted(rdir.glob("._LOCKED_*.json")):
            try:
                raw = json.loads(cand.read_text(encoding="utf-8"))
                sidecar = RemoteLockSidecar.model_validate(raw)
                sidecar.lock_path = str(cand)
            except Exception:
                continue

            if target_file_name and sidecar.file_name and Path(sidecar.file_name).name != Path(target_file_name).name:
                continue

            if current_user and sidecar.locked_by.strip().lower() == current_user.strip().lower():
                continue

            # Check TTL expiration
            try:
                locked_dt = datetime.fromisoformat(sidecar.locked_at.replace("Z", "+00:00"))
                if locked_dt.tzinfo is None:
                    locked_dt = locked_dt.replace(tzinfo=timezone.utc)
                ttl = sidecar.ttl_seconds if sidecar.ttl_seconds > 0 else default_ttl_seconds
                if (now_utc - locked_dt).total_seconds() > ttl:
                    continue
            except Exception:
                # If timestamp cannot be parsed, treat as active lock to stay safe
                pass

            return sidecar

        return None

    @staticmethod
    def verify_cas(
        pin: RemotePinRecord,
        remote_path: Union[str, Path],
        branch_on_conflict: bool = True,
        conflict_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Validates Compare-And-Set (CAS) preconditions against the live remote file.
        On divergence, optionally branches the remote copy to `<stem>_REMOTE_<ts><ext>`
        and raises `RemoteConflictError`.
        """
        rpath = Path(remote_path)
        remote_rev: Optional[str] = None
        remote_md5: Optional[str] = None
        remote_sha256: Optional[str] = None
        remote_mod_time: Optional[str] = None
        remote_mod_by: Optional[str] = None

        if pin.file_id:
            gmeta = query_gdrive_file_metadata(pin.file_id)
            if gmeta:
                remote_rev = str(gmeta.get("headRevisionId") or "") or None
                remote_md5 = str(gmeta.get("md5Checksum") or "") or None
                remote_mod_time = str(gmeta.get("modifiedTime") or "") or None
                lmu = gmeta.get("lastModifyingUser")
                if isinstance(lmu, dict):
                    remote_mod_by = lmu.get("emailAddress") or lmu.get("displayName")

        if rpath.exists() and rpath.is_file():
            disk_rev, disk_md5, disk_sha, disk_mod = _file_revision_token(rpath)
            remote_rev = remote_rev or disk_rev
            remote_md5 = remote_md5 or disk_md5
            remote_sha256 = disk_sha
            remote_mod_time = remote_mod_time or disk_mod

        if remote_rev is None and remote_md5 is None:
            return

        diverged = False
        if remote_rev and pin.base_revision_id and remote_rev != pin.base_revision_id:
            diverged = True
        if remote_md5 and pin.base_md5 and remote_md5 != pin.base_md5:
            diverged = True
        if remote_sha256 and pin.base_sha256 and remote_sha256 != pin.base_sha256:
            diverged = True

        if not diverged:
            return

        branch_path_str: Optional[str] = None
        if branch_on_conflict and rpath.exists() and rpath.is_file():
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            dest_dir = Path(conflict_dir) if conflict_dir else rpath.parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            branch_p = dest_dir / f"{rpath.stem}_REMOTE_{ts}{rpath.suffix}"
            while branch_p.exists():
                branch_p = dest_dir / f"{rpath.stem}_REMOTE_{ts}_{uuid.uuid4().hex[:6]}{rpath.suffix}"
            shutil.copy2(rpath, branch_p)
            branch_path_str = str(branch_p)

        raise RemoteConflictError(
            file_name=rpath.name,
            base_revision_id=pin.base_revision_id,
            remote_revision_id=remote_rev,
            base_hash=pin.base_md5 or pin.base_sha256,
            remote_hash=remote_md5 or remote_sha256,
            remote_modified_by=remote_mod_by,
            remote_modified_time=remote_mod_time,
            conflict_branch_path=branch_path_str,
        )

    @classmethod
    def check_directory_drift(
        cls,
        staging_dir: Union[str, Path],
        receipt_path: Optional[Union[str, Path]] = None,
        current_user: Optional[str] = None,
    ) -> DriftReport:
        """Audits every pinned deliverable in `staging_dir` for remote drift or locks."""
        sdir = Path(staging_dir).resolve()
        rp = Path(receipt_path).resolve() if receipt_path else (sdir / ".sync_receipt.json")
        pins = cls.load_pins(rp)

        items: List[DriftCheckItem] = []
        warnings: List[str] = []
        has_drift = False

        for key, pin in pins.items():
            rpath = Path(pin.target_drive_path)
            fname = rpath.name or Path(pin.local_path).name

            sidecar = cls.check_remote_lock_sidecars(
                rpath.parent,
                current_user=current_user,
                target_file_name=fname,
            )
            if sidecar is not None:
                has_drift = True
                msg = (
                    f"Remote file '{fname}' is locked by '{sidecar.locked_by}' "
                    f"(since {sidecar.locked_at})."
                )
                warnings.append(msg)
                items.append(
                    DriftCheckItem(
                        file_name=fname,
                        status="REMOTE_LOCKED",
                        target_drive_path=str(rpath),
                        base_revision_id=pin.base_revision_id,
                        remote_modified_by=sidecar.locked_by,
                        remote_modified_time=sidecar.locked_at,
                        message=msg,
                    )
                )
                continue

            if not rpath.exists():
                msg = f"Remote file '{fname}' does not exist at '{rpath}'."
                items.append(
                    DriftCheckItem(
                        file_name=fname,
                        status="REMOTE_MISSING",
                        target_drive_path=str(rpath),
                        base_revision_id=pin.base_revision_id,
                        base_hash=pin.base_md5,
                        message=msg,
                    )
                )
                continue

            try:
                cls.verify_cas(pin, rpath, branch_on_conflict=False)
                items.append(
                    DriftCheckItem(
                        file_name=fname,
                        status="IN_SYNC",
                        target_drive_path=str(rpath),
                        base_revision_id=pin.base_revision_id,
                        remote_revision_id=pin.base_revision_id,
                        base_hash=pin.base_md5,
                        remote_hash=pin.base_md5,
                        message="Remote copy matches pinned baseline.",
                    )
                )
            except RemoteConflictError as conflict:
                has_drift = True
                msg = (
                    f"Remote file '{fname}' has been modified out-of-band "
                    f"(modified at {conflict.remote_modified_time or 'unknown'}). Local copy is stale."
                )
                warnings.append(msg)
                items.append(
                    DriftCheckItem(
                        file_name=fname,
                        status="REMOTE_DRIFTED",
                        target_drive_path=str(rpath),
                        base_revision_id=conflict.base_revision_id,
                        remote_revision_id=conflict.remote_revision_id,
                        base_hash=conflict.base_hash,
                        remote_hash=conflict.remote_hash,
                        remote_modified_by=conflict.remote_modified_by,
                        remote_modified_time=conflict.remote_modified_time,
                        message=msg,
                    )
                )

        return DriftReport(
            checked_at=datetime.now(timezone.utc).isoformat(),
            directory=str(sdir),
            has_drift=has_drift,
            items=items,
            warnings=warnings,
        )

    @staticmethod
    def reconcile_three_way_slide(
        spec_path: Union[str, Path],
        remote_pptx_path: Union[str, Path],
        slide_index: int,
        output_path: Union[str, Path],
    ) -> Path:
        """
        Phase 3 Slide-Level 3-Way Merge:
        Copies `remote_pptx_path` (preserving all sibling slides edited by teammates)
        to `output_path` and atomically replaces ONLY `slide_index` with the
        compiled Diagram V2 specification.
        """
        from src.ppt_engine.diagram_v2.compiler import load_diagram_spec
        from src.ppt_engine.diagram_v2.pptx_compiler import replace_slide_in_presentation

        spec_p = Path(spec_path)
        remote_p = Path(remote_pptx_path)
        out_p = Path(output_path)

        if not spec_p.exists():
            raise FileNotFoundError(f"Diagram specification not found: {spec_p}")
        if not remote_p.exists():
            raise FileNotFoundError(f"Remote presentation not found: {remote_p}")

        ds = load_diagram_spec(spec_p)

        out_p.parent.mkdir(parents=True, exist_ok=True)
        work_p = out_p.parent / f".tmp_merge_{uuid.uuid4().hex[:8]}_{out_p.name}"
        try:
            shutil.copy2(remote_p, work_p)
            replace_slide_in_presentation(ds, work_p, slide_index=slide_index)
            os.replace(work_p, out_p)
        except Exception:
            if work_p.exists():
                work_p.unlink(missing_ok=True)
            raise
        return out_p
