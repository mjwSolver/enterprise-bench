"""
Unit Tests: Remote Cloud Drift Guard, CAS Sync, Lock Sidecar CLI & Watcher
==========================================================================
Covers Milestone M2 delivery hardening:
  1. `--dry-run --cas` non-mutation (zero `_REMOTE_*` branches, zero receipt writes)
  2. Mid-batch `RemoteConflictError` / `RemoteLockConflictError` partial receipt persistence
     and no false self-conflicts on retry
  3. Subfolder-safe `pin_checkout` keys + `target_drive_path` resolution lookup
  4. Same-second remote lock sidecar UUID disambiguation, TTL validation, and active conflict guard
  5. `release_remote_lock_sidecar` format/name and ownership validation
  6. `StagingPipeline` exclusion of `_REMOTE_` conflict branch artifacts
  7. `file_id` CAS verification when remote mount file is missing locally + same-second conflict branch suffix
  8. `temp_dest` cleanup on mid-copy transmission failure
  9. `bench stage lock-remote` / `bench stage unlock-remote` / `stage sync --dry-run` CLI roundtrips
 10. `reconcile_three_way_slide` sibling slide preservation
 11. `watch_diagram()` forwarding of `remote_drift` and `receipt_path`
"""

from __future__ import annotations

import json
import shutil
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest
from pptx import Presentation
from typer.testing import CliRunner

from src.cli import app
from src.core.delivery.exceptions import (
    DeliveryError,
    LockOwnershipError,
    RemoteConflictError,
    RemoteLockConflictError,
)
from src.core.delivery.models import RemoteLockSidecar, SyncReceipt, SyncStatus
from src.core.delivery.remote_guard import RemoteDriftGuard
from src.core.delivery.staging import StagingPipeline
from src.core.delivery.sync import RemoteSyncEngine


def _write_minimal_manifest(
    staging_dir: Path,
    files: List[Dict[str, str]],
    target_root: str = "Deliverables",
) -> Path:
    """Writes a minimal `delivery_manifest.json` for `RemoteSyncEngine.sync`."""
    entries = []
    for entry in files:
        rel_path = entry["relative_path"]
        entries.append(
            {
                "relative_path": rel_path,
                "target_drive_path": f"{target_root}/{rel_path}",
                "file_size_bytes": (staging_dir / rel_path).stat().st_size,
                "sha256": entry.get("sha256", ""),
                "modified_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    manifest_path = staging_dir / "delivery_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "delivery_id": "DELIV-TEST-001",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_directory": str(staging_dir),
                "target_drive_root": target_root,
                "total_files": len(entries),
                "total_bytes": sum(e["file_size_bytes"] for e in entries),
                "files": entries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


def _write_minimal_diagram_spec(spec_path: Path) -> None:
    """Writes a minimal valid Diagram V2 YAML spec."""
    spec_path.write_text(
        "\n".join(
            [
                'id: "test_merge_diagram"',
                'name: "Test Merge Diagram"',
                'theme: "metrodata"',
                "canvas:",
                "  width: 13.333",
                "  height: 7.5",
                '  unit: "in"',
                '  background: "#FFFFFF"',
                "header:",
                "  show: true",
                '  action_title: "Merged Slide Title"',
                '  subtitle: "Updated via 3-way merge"',
                "containers: []",
                "nodes:",
                '  - id: "n1"',
                '    title: "Service A"',
                '    subtitle: "Reconciled"',
                "    x: 1.5",
                "    y: 2.0",
                "    w: 2.2",
                "    h: 1.2",
                "flows: []",
                "badges: []",
            ]
        ),
        encoding="utf-8",
    )


def test_dry_run_cas_does_not_write_remote_branch_or_receipt(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    remote_root = drive_base / "Deliverables"
    staging.mkdir()
    remote_root.mkdir(parents=True)

    local_file = staging / "deck.pptx"
    remote_file = remote_root / "deck.pptx"
    local_file.write_bytes(b"local-v2-content")
    remote_file.write_bytes(b"remote-v1-baseline")

    receipt_path = staging / ".sync_receipt.json"
    RemoteDriftGuard.pin_checkout(
        receipt_path=receipt_path,
        local_path=local_file,
        target_drive_path=remote_file,
        checkout_user="alice",
    )
    original_receipt_bytes = receipt_path.read_bytes()

    # Simulate out-of-band edit on remote
    time.sleep(0.02)
    remote_file.write_bytes(b"remote-v2-teammate-edit-different-size")

    manifest_path = _write_minimal_manifest(staging, [{"relative_path": "deck.pptx"}])
    engine = RemoteSyncEngine()

    with pytest.raises(RemoteConflictError) as exc_info:
        engine.sync(
            manifest_path=manifest_path,
            drive_base_dir=drive_base,
            dry_run=True,
            strict_cas=True,
            branch_on_conflict=True,
            current_user="alice",
            output_receipt_path=receipt_path,
        )

    assert exc_info.value.conflict_branch_path is None
    assert list(staging.rglob("*_REMOTE_*")) == []
    assert list(remote_root.rglob("*_REMOTE_*")) == []
    assert receipt_path.read_bytes() == original_receipt_bytes

    # Non-conflicting dry-run must also leave .sync_receipt.json untouched
    local_new = staging / "clean.txt"
    local_new.write_text("clean-payload", encoding="utf-8")
    manifest_clean = _write_minimal_manifest(staging, [{"relative_path": "clean.txt"}])
    receipt_clean = staging / ".clean_receipt.json"
    res = engine.sync(
        manifest_path=manifest_clean,
        drive_base_dir=drive_base,
        dry_run=True,
        output_receipt_path=receipt_clean,
    )
    assert res.dry_run is True
    assert res.transmitted_count == 1
    assert not receipt_clean.exists()


def test_mid_batch_remote_conflict_persists_earlier_pins(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    remote_root = drive_base / "Deliverables"
    staging.mkdir()
    remote_root.mkdir(parents=True)

    a_local = staging / "a.pptx"
    b_local = staging / "b.pptx"
    a_remote = remote_root / "a.pptx"
    b_remote = remote_root / "b.pptx"

    a_local.write_bytes(b"a-v1")
    b_local.write_bytes(b"b-v1")
    a_remote.write_bytes(b"a-v1")
    b_remote.write_bytes(b"b-v1")

    receipt_path = staging / ".sync_receipt.json"
    RemoteDriftGuard.pin_checkout(receipt_path, a_local, a_remote, checkout_user="alice")
    pin_b_initial = RemoteDriftGuard.pin_checkout(receipt_path, b_local, b_remote, checkout_user="alice")

    # Local edits both; teammate edits b_remote out-of-band
    a_local.write_bytes(b"a-v2-local")
    b_local.write_bytes(b"b-v2-local")
    time.sleep(0.02)
    b_remote.write_bytes(b"b-v2-teammate-remote-conflict")

    manifest_path = _write_minimal_manifest(
        staging,
        [{"relative_path": "a.pptx"}, {"relative_path": "b.pptx"}],
    )
    engine = RemoteSyncEngine()

    with pytest.raises(RemoteConflictError):
        engine.sync(
            manifest_path=manifest_path,
            drive_base_dir=drive_base,
            strict_cas=True,
            branch_on_conflict=True,
            current_user="alice",
            output_receipt_path=receipt_path,
        )

    assert receipt_path.exists()
    persisted = SyncReceipt.model_validate_json(receipt_path.read_text(encoding="utf-8"))
    assert "a.pptx" in persisted.remote_pins
    assert persisted.remote_pins["a.pptx"].base_md5 != pin_b_initial.base_md5
    assert persisted.transmitted_count == 1
    assert persisted.failed_count == 1
    assert len(persisted.items) == 2
    assert persisted.items[0].name == "a.pptx"
    assert persisted.items[0].status == SyncStatus.TRANSMITTED
    assert persisted.items[1].name == "b.pptx"
    assert persisted.items[1].status == SyncStatus.REMOTE_CONFLICT
    assert persisted.items[1].conflict_branch_path is not None
    assert persisted.remote_pins["b.pptx"].base_revision_id == pin_b_initial.base_revision_id

    # Clean up _REMOTE_ branch before retry, resolve b.pptx pin, and confirm retry does NOT false-conflict on a.pptx
    for branch in staging.glob("*_REMOTE_*"):
        branch.unlink()
    RemoteDriftGuard.pin_checkout(receipt_path, b_local, b_remote, checkout_user="alice")
    retry_receipt = engine.sync(
        manifest_path=manifest_path,
        drive_base_dir=drive_base,
        strict_cas=True,
        current_user="alice",
        output_receipt_path=receipt_path,
    )
    assert retry_receipt.items[0].status == SyncStatus.SKIPPED_IDENTICAL
    assert retry_receipt.items[1].status == SyncStatus.TRANSMITTED


def test_mid_batch_remote_lock_conflict_persists_earlier_pins(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    remote_root = drive_base / "Deliverables"
    staging.mkdir()
    remote_root.mkdir(parents=True)

    a_local = staging / "a.pptx"
    b_local = staging / "b.pptx"
    a_local.write_bytes(b"a-payload")
    b_local.write_bytes(b"b-payload")

    RemoteDriftGuard.acquire_remote_lock_sidecar(remote_root, "b.pptx", user="bob", ttl_seconds=600)

    manifest_path = _write_minimal_manifest(
        staging,
        [{"relative_path": "a.pptx"}, {"relative_path": "b.pptx"}],
    )
    receipt_path = staging / ".sync_receipt.json"
    engine = RemoteSyncEngine()

    with pytest.raises(RemoteLockConflictError):
        engine.sync(
            manifest_path=manifest_path,
            drive_base_dir=drive_base,
            fail_on_locks=True,
            current_user="alice",
            output_receipt_path=receipt_path,
        )

    persisted = SyncReceipt.model_validate_json(receipt_path.read_text(encoding="utf-8"))
    assert "a.pptx" in persisted.remote_pins
    assert persisted.items[-1].status == SyncStatus.LOCKED_CONFLICT


def test_pin_checkout_no_subfolder_collision_and_sync_lookup(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    remote_root = drive_base / "Deliverables"
    (staging / "sub1").mkdir(parents=True)
    (staging / "sub2").mkdir(parents=True)
    (remote_root / "sub1").mkdir(parents=True)
    (remote_root / "sub2").mkdir(parents=True)

    f1_local = staging / "sub1" / "deck.pptx"
    f2_local = staging / "sub2" / "deck.pptx"
    f1_remote = remote_root / "sub1" / "deck.pptx"
    f2_remote = remote_root / "sub2" / "deck.pptx"

    f1_local.write_bytes(b"sub1-deck-bytes")
    f2_local.write_bytes(b"sub2-deck-bytes")
    f1_remote.write_bytes(b"sub1-deck-bytes")
    f2_remote.write_bytes(b"sub2-different-remote-bytes")

    receipt_path = staging / ".sync_receipt.json"
    RemoteDriftGuard.pin_checkout(receipt_path, f1_local, f1_remote, checkout_user="alice")
    RemoteDriftGuard.pin_checkout(receipt_path, f2_local, f2_remote, checkout_user="alice")

    pins = RemoteDriftGuard.load_pins(receipt_path)
    assert "sub1/deck.pptx" in pins
    assert "sub2/deck.pptx" in pins
    assert pins["sub1/deck.pptx"].base_md5 != pins["sub2/deck.pptx"].base_md5

    # Remove sub2/deck.pptx pin; syncing sub2/deck.pptx must NOT fall back to sub1/deck.pptx
    raw_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    del raw_receipt["remote_pins"]["sub2/deck.pptx"]
    receipt_path.write_text(json.dumps(raw_receipt, indent=2), encoding="utf-8")

    manifest_sub2 = _write_minimal_manifest(staging, [{"relative_path": "sub2/deck.pptx"}])
    res = RemoteSyncEngine().sync(
        manifest_path=manifest_sub2,
        drive_base_dir=drive_base,
        strict_cas=True,
        current_user="alice",
        output_receipt_path=receipt_path,
    )
    assert res.transmitted_count == 1
    assert f2_remote.read_bytes() == b"sub2-deck-bytes"

    # Now test target_drive_path fallback when pin is stored under a non-matching dict key
    time.sleep(0.02)
    f2_remote.write_bytes(b"sub2-remote-drifted-again")
    raw_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    sub2_pin = raw_receipt["remote_pins"].pop("sub2/deck.pptx")
    raw_receipt["remote_pins"]["legacy_custom_key/deck.pptx"] = sub2_pin
    receipt_path.write_text(json.dumps(raw_receipt, indent=2), encoding="utf-8")

    with pytest.raises(RemoteConflictError):
        RemoteSyncEngine().sync(
            manifest_path=manifest_sub2,
            drive_base_dir=drive_base,
            strict_cas=True,
            branch_on_conflict=False,
            current_user="alice",
            output_receipt_path=receipt_path,
        )


def test_sync_fallback_pin_key_cleaned_up_and_drift_check_stays_clean(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    remote_root = drive_base / "Deliverables"
    (staging / "a").mkdir(parents=True)
    (staging / "b").mkdir(parents=True)
    (remote_root / "a").mkdir(parents=True)
    (remote_root / "b").mkdir(parents=True)

    a_local = staging / "a" / "deck.pptx"
    b_local = staging / "b" / "deck.pptx"
    a_remote = remote_root / "a" / "deck.pptx"
    b_remote = remote_root / "b" / "deck.pptx"

    a_local.write_bytes(b"a-v1")
    b_local.write_bytes(b"b-v1")
    a_remote.write_bytes(b"a-v1")
    b_remote.write_bytes(b"b-v1")

    receipt_path = staging / ".sync_receipt.json"
    RemoteDriftGuard.pin_checkout(receipt_path, a_local, a_remote, checkout_user="alice")
    RemoteDriftGuard.pin_checkout(receipt_path, b_local, b_remote, checkout_user="alice")

    # Rename b/deck.pptx pin to an old/alias key before updating b_local
    raw_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    b_pin = raw_receipt["remote_pins"].pop("b/deck.pptx")
    raw_receipt["remote_pins"]["legacy_alias/deck.pptx"] = b_pin
    receipt_path.write_text(json.dumps(raw_receipt, indent=2), encoding="utf-8")

    b_local.write_bytes(b"b-v2-updated")
    manifest = _write_minimal_manifest(
        staging,
        [{"relative_path": "a/deck.pptx"}, {"relative_path": "b/deck.pptx"}],
    )
    res = RemoteSyncEngine().sync(
        manifest_path=manifest,
        drive_base_dir=drive_base,
        strict_cas=True,
        current_user="alice",
        output_receipt_path=receipt_path,
    )
    assert res.transmitted_count == 1
    assert res.skipped_count == 1

    pins_after = RemoteDriftGuard.load_pins(receipt_path)
    assert "legacy_alias/deck.pptx" not in pins_after
    assert "b/deck.pptx" in pins_after
    assert "a/deck.pptx" in pins_after

    drift = RemoteDriftGuard.check_directory_drift(staging, receipt_path=receipt_path, current_user="alice")
    assert drift.has_drift is False
    assert all(it.status == "IN_SYNC" for it in drift.items)


def test_skipped_identical_and_transmitted_preserve_file_id_head_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    remote_root = drive_base / "Deliverables"
    staging.mkdir()
    remote_root.mkdir(parents=True)

    local_file = staging / "same.pptx"
    remote_file = remote_root / "same.pptx"
    payload_v1 = b"identical-deck-v1"
    local_file.write_bytes(payload_v1)
    remote_file.write_bytes(payload_v1)

    import hashlib

    md5_v1 = hashlib.md5(payload_v1).hexdigest()
    state: Dict[str, str] = {"headRevisionId": "drive-rev-42", "md5Checksum": md5_v1}
    monkeypatch.setattr(
        "src.core.delivery.remote_guard.query_gdrive_file_metadata",
        lambda fid: {
            "headRevisionId": state["headRevisionId"],
            "md5Checksum": state["md5Checksum"],
            "modifiedTime": "2026-11-24T01:00:00Z",
        },
    )

    receipt_path = staging / ".sync_receipt.json"
    RemoteDriftGuard.pin_checkout(
        receipt_path=receipt_path,
        local_path=local_file,
        target_drive_path=remote_file,
        checkout_user="alice",
        file_id="fid-same",
    )

    manifest = _write_minimal_manifest(staging, [{"relative_path": "same.pptx"}])
    engine = RemoteSyncEngine()

    # 1st CAS sync hits SKIPPED_IDENTICAL and must preserve Drive headRevisionId
    res1 = engine.sync(
        manifest_path=manifest,
        drive_base_dir=drive_base,
        strict_cas=True,
        current_user="alice",
        output_receipt_path=receipt_path,
    )
    assert res1.items[0].status == SyncStatus.SKIPPED_IDENTICAL
    pins1 = RemoteDriftGuard.load_pins(receipt_path)
    assert pins1["same.pptx"].base_revision_id == "drive-rev-42"

    # 2nd CAS sync and check_directory_drift must NOT self-conflict
    res2 = engine.sync(
        manifest_path=manifest,
        drive_base_dir=drive_base,
        strict_cas=True,
        current_user="alice",
        output_receipt_path=receipt_path,
    )
    assert res2.items[0].status == SyncStatus.SKIPPED_IDENTICAL
    drift = RemoteDriftGuard.check_directory_drift(staging, receipt_path=receipt_path, current_user="alice")
    assert drift.has_drift is False

    # Now edit locally, simulate Drive headRevisionId advancing on upload, and verify 2nd CAS sync works
    payload_v2 = b"updated-deck-v2"
    local_file.write_bytes(payload_v2)
    manifest2 = _write_minimal_manifest(staging, [{"relative_path": "same.pptx"}])

    def update_and_sync() -> SyncReceipt:
        r = engine.sync(
            manifest_path=manifest2,
            drive_base_dir=drive_base,
            strict_cas=True,
            current_user="alice",
            output_receipt_path=receipt_path,
        )
        return r

    res3 = update_and_sync()
    assert res3.items[0].status == SyncStatus.TRANSMITTED
    # Even if gdrive still returned drive-rev-42 during upload, next CAS sync must not false-conflict
    res4 = update_and_sync()
    assert res4.items[0].status == SyncStatus.SKIPPED_IDENTICAL


def test_acquire_remote_lock_sidecar_same_second_no_overwrite_and_ttl(tmp_path: Path) -> None:
    remote_dir = tmp_path / "remote"
    remote_dir.mkdir()

    with pytest.raises(ValueError):
        RemoteDriftGuard.acquire_remote_lock_sidecar(remote_dir, "a.pptx", user="alice", ttl_seconds=0)
    for bad_name in ("", "   ", ".", "..", "dir/", "dir\\", "sub/.", "sub/.."):
        with pytest.raises(ValueError):
            RemoteDriftGuard.acquire_remote_lock_sidecar(remote_dir, bad_name, user="alice", ttl_seconds=600)

    not_a_dir = tmp_path / "not_a_dir.txt"
    not_a_dir.write_text("file", encoding="utf-8")
    with pytest.raises(DeliveryError):
        RemoteDriftGuard.acquire_remote_lock_sidecar(not_a_dir, "a.pptx", user="alice", ttl_seconds=600)

    lock1 = RemoteDriftGuard.acquire_remote_lock_sidecar(remote_dir, "sub/a.pptx", user="alice", ttl_seconds=600)
    lock2 = RemoteDriftGuard.acquire_remote_lock_sidecar(remote_dir, "b.pptx", user="alice", ttl_seconds=600)
    assert lock1 != lock2
    assert lock1.exists() and lock2.exists()

    sidecar1 = RemoteLockSidecar.model_validate_json(lock1.read_text(encoding="utf-8"))
    assert sidecar1.file_name == "a.pptx"

    # Active foreign lock blocks fail_on_conflict=True
    with pytest.raises(RemoteLockConflictError):
        RemoteDriftGuard.acquire_remote_lock_sidecar(remote_dir, "a.pptx", user="bob", ttl_seconds=600)

    # Expired lock is ignored by check_remote_lock_sidecars
    expired_lock = RemoteDriftGuard.acquire_remote_lock_sidecar(
        remote_dir, "expired.pptx", user="bob", ttl_seconds=10, fail_on_conflict=False
    )
    expired_data = json.loads(expired_lock.read_text(encoding="utf-8"))
    expired_data["locked_at"] = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    expired_lock.write_text(json.dumps(expired_data), encoding="utf-8")

    assert (
        RemoteDriftGuard.check_remote_lock_sidecars(
            remote_dir, current_user="alice", target_file_name="expired.pptx"
        )
        is None
    )
    assert (
        RemoteDriftGuard.check_remote_lock_sidecars(
            remote_dir, current_user="bob", target_file_name="a.pptx"
        )
        is not None
    )


def test_release_remote_lock_sidecar_format_and_ownership(tmp_path: Path) -> None:
    remote_dir = tmp_path / "remote"
    remote_dir.mkdir()

    deliverable = remote_dir / "deck.pptx"
    deliverable.write_bytes(b"real-deliverable")

    # Never delete arbitrary non-sidecar files
    with pytest.raises(DeliveryError):
        RemoteDriftGuard.release_remote_lock_sidecar(deliverable, force=True)
    assert deliverable.exists()

    lock_p = RemoteDriftGuard.acquire_remote_lock_sidecar(remote_dir, "deck.pptx", user="alice")
    with pytest.raises(LockOwnershipError):
        RemoteDriftGuard.release_remote_lock_sidecar(lock_p, user="bob", force=False)
    assert lock_p.exists()

    assert RemoteDriftGuard.release_remote_lock_sidecar(lock_p, user="alice") is True
    assert not lock_p.exists()

    lock_p2 = RemoteDriftGuard.acquire_remote_lock_sidecar(remote_dir, "deck.pptx", user="alice")
    assert RemoteDriftGuard.release_remote_lock_sidecar(lock_p2, user="bob", force=True) is True
    assert not lock_p2.exists()

    corrupt_sidecar = remote_dir / "._LOCKED_corrupt_20261124T000000Z_abc123.json"
    corrupt_sidecar.write_text("{not-valid-json", encoding="utf-8")
    with pytest.raises(DeliveryError):
        RemoteDriftGuard.release_remote_lock_sidecar(corrupt_sidecar, force=False)
    assert RemoteDriftGuard.release_remote_lock_sidecar(corrupt_sidecar, force=True) is True


def test_staging_preflight_and_manifest_ignore_remote_conflict_branches(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()

    valid_file = staging / "summary.txt"
    valid_file.write_text("deliverable-ok", encoding="utf-8")

    # Place a 0-byte / corrupt _REMOTE_ branch artifact that would fail Gate 4 if not excluded
    conflict_branch = staging / "summary_REMOTE_20261124_000000.pptx"
    conflict_branch.write_bytes(b"")

    pipeline = StagingPipeline()
    preflight = pipeline.run_preflight(staging, fail_on_locks=True)
    assert preflight.passed is True
    assert preflight.total_files == 1

    manifest = pipeline.generate_manifest(staging, target_drive_root="Deliverables")
    assert manifest.total_files == 1
    assert manifest.files[0].relative_path == "summary.txt"


def test_verify_cas_file_id_when_local_remote_missing_and_same_second_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    staging.mkdir()
    drive_base.mkdir()

    local_file = staging / "cloud_only.pptx"
    local_file.write_bytes(b"local-copy")
    missing_remote = drive_base / "Deliverables" / "cloud_only.pptx"

    receipt_path = staging / ".sync_receipt.json"
    RemoteDriftGuard.pin_checkout(
        receipt_path=receipt_path,
        local_path=local_file,
        target_drive_path=missing_remote,
        checkout_user="alice",
        file_id="gdrive-file-id-123",
        revision_id="rev-base-1",
    )

    monkeypatch.setattr(
        "src.core.delivery.remote_guard.query_gdrive_file_metadata",
        lambda fid: {
            "headRevisionId": "rev-remote-2",
            "md5Checksum": "deadbeef1234",
            "modifiedTime": "2026-11-24T01:00:00Z",
            "lastModifyingUser": {"emailAddress": "bob@example.com"},
        },
    )

    manifest_path = _write_minimal_manifest(staging, [{"relative_path": "cloud_only.pptx"}])
    with pytest.raises(RemoteConflictError) as exc_info:
        RemoteSyncEngine().sync(
            manifest_path=manifest_path,
            drive_base_dir=drive_base,
            strict_cas=True,
            branch_on_conflict=True,
            current_user="alice",
            output_receipt_path=receipt_path,
        )
    assert exc_info.value.remote_revision_id == "rev-remote-2"

    # Also test same-second conflict branch disambiguation when remote exists locally
    monkeypatch.setattr("src.core.delivery.remote_guard.query_gdrive_file_metadata", lambda fid: None)
    missing_remote.parent.mkdir(parents=True, exist_ok=True)
    missing_remote.write_bytes(b"remote-v1")
    pin = RemoteDriftGuard.pin_checkout(receipt_path, local_file, missing_remote, checkout_user="alice")
    time.sleep(0.02)
    missing_remote.write_bytes(b"remote-v2-diverged")

    conflict_dir = tmp_path / "conflicts"
    branches: List[str] = []
    for _ in range(2):
        with pytest.raises(RemoteConflictError) as c_err:
            RemoteDriftGuard.verify_cas(pin, missing_remote, branch_on_conflict=True, conflict_dir=conflict_dir)
        assert c_err.value.conflict_branch_path is not None
        branches.append(c_err.value.conflict_branch_path)

    assert len(set(branches)) == 2
    assert all(Path(b).exists() for b in branches)


def test_sync_temp_dest_cleanup_on_copy_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    staging.mkdir()
    drive_base.mkdir()

    src_file = staging / "report.pptx"
    src_file.write_bytes(b"report-bytes")
    manifest_path = _write_minimal_manifest(staging, [{"relative_path": "report.pptx"}])

    def failing_copy(src: Path, dst: Path, *args: Any, **kwargs: Any) -> None:
        Path(dst).write_bytes(b"partial-tmp")
        raise OSError("Simulated disk full")

    monkeypatch.setattr(shutil, "copy2", failing_copy)
    receipt = RemoteSyncEngine().sync(
        manifest_path=manifest_path,
        drive_base_dir=drive_base,
        output_receipt_path=staging / ".sync_receipt.json",
    )
    assert receipt.failed_count == 1
    assert receipt.items[0].status == SyncStatus.FAILED
    remote_dir = drive_base / "Deliverables"
    assert list(remote_dir.glob("*.tmp_*")) == []


def test_cli_lock_remote_and_unlock_remote_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()
    remote_dir = tmp_path / "remote_drive"
    remote_dir.mkdir()
    target = remote_dir / "deck.pptx"
    target.write_bytes(b"deck")

    # Reject trailing-slash directory targets and non-positive TTL
    trailing_dir = tmp_path / "lock_dir"
    trailing_dir.mkdir()
    res_dir_slash = runner.invoke(
        app,
        ["stage", "lock-remote", f"{trailing_dir}/", "-u", "alice"],
    )
    assert res_dir_slash.exit_code == 1
    res_ghost_slash = runner.invoke(
        app,
        ["stage", "lock-remote", "ghost_dir/", "-u", "alice"],
    )
    assert res_ghost_slash.exit_code == 1
    res_bad_ttl = runner.invoke(
        app,
        ["stage", "lock-remote", str(target), "-u", "alice", "--ttl", "0"],
    )
    assert res_bad_ttl.exit_code == 1

    res_lock = runner.invoke(
        app,
        ["stage", "lock-remote", str(target), "-u", "alice", "--ttl", "300", "-r", "Editing slides"],
    )
    assert res_lock.exit_code == 0, res_lock.output
    sidecars = list(remote_dir.glob("._LOCKED_*.json"))
    assert len(sidecars) == 1

    # Conflict for bob without --force
    res_conflict = runner.invoke(
        app,
        ["stage", "lock-remote", "deck.pptx", "-d", str(remote_dir), "-u", "bob"],
    )
    assert res_conflict.exit_code == 1

    # Bob forces second sidecar
    res_force_lock = runner.invoke(
        app,
        ["stage", "lock-remote", "deck.pptx", "-d", str(remote_dir), "-u", "bob", "--force"],
    )
    assert res_force_lock.exit_code == 0, res_force_lock.output
    assert len(list(remote_dir.glob("._LOCKED_*.json"))) == 2

    # Explicit sidecar unlock WITHOUT --user or --force must be rejected
    alice_sidecar = next(p for p in remote_dir.glob("._LOCKED_alice_*.json"))
    res_no_auth = runner.invoke(
        app,
        ["stage", "unlock-remote", str(alice_sidecar)],
    )
    assert res_no_auth.exit_code == 1
    assert alice_sidecar.exists()

    # Charlie cannot unlock alice's sidecar
    res_wrong_user = runner.invoke(
        app,
        ["stage", "unlock-remote", str(alice_sidecar), "-u", "charlie"],
    )
    assert res_wrong_user.exit_code == 1
    assert alice_sidecar.exists()

    # --remote-dir must take precedence over a same-named decoy sidecar in CWD
    cwd_decoy_dir = tmp_path / "cwd_decoy"
    cwd_decoy_dir.mkdir()
    decoy_sidecar = cwd_decoy_dir / alice_sidecar.name
    decoy_sidecar.write_text(alice_sidecar.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.chdir(cwd_decoy_dir)
    res_unlock_alice = runner.invoke(
        app,
        ["stage", "unlock-remote", alice_sidecar.name, "-d", str(remote_dir), "-u", "alice"],
    )
    assert res_unlock_alice.exit_code == 0, res_unlock_alice.output
    assert not alice_sidecar.exists()
    assert decoy_sidecar.exists()

    # Force-unlock remaining bob sidecar by deliverable name
    res_unlock_bob = runner.invoke(
        app,
        ["stage", "unlock-remote", "deck.pptx", "-d", str(remote_dir), "--force"],
    )
    assert res_unlock_bob.exit_code == 0, res_unlock_bob.output
    assert list(remote_dir.glob("._LOCKED_*.json")) == []

    # Verify CLI dry-run output clarifies receipt is not written
    staging = tmp_path / "cli_staging"
    staging.mkdir()
    (staging / "note.txt").write_text("hello", encoding="utf-8")
    _write_minimal_manifest(staging, [{"relative_path": "note.txt"}])
    res_dry = runner.invoke(
        app,
        ["stage", "sync", str(staging), "-d", str(tmp_path / "cli_drive"), "--dry-run"],
    )
    assert res_dry.exit_code == 0, res_dry.output
    normalized_dry_out = " ".join(res_dry.output.split())
    assert "(dry-run: not written)" in normalized_dry_out
    assert not (staging / ".sync_receipt.json").exists()


def test_reconcile_three_way_slide_preserves_siblings(tmp_path: Path) -> None:
    remote_pptx = tmp_path / "remote_deck.pptx"
    merged_pptx = tmp_path / "merged_deck.pptx"
    spec_yaml = tmp_path / "diagram.yaml"
    _write_minimal_diagram_spec(spec_yaml)

    prs = Presentation()
    prs.slide_width = 12192000  # 13.333 in
    prs.slide_height = 6858000  # 7.5 in
    blank = prs.slide_layouts[6]
    s1 = prs.slides.add_slide(blank)
    tb1 = s1.shapes.add_textbox(100000, 100000, 3000000, 500000)
    tb1.text_frame.text = "Teammate Slide 1 Content"

    s2 = prs.slides.add_slide(blank)
    tb2 = s2.shapes.add_textbox(100000, 100000, 3000000, 500000)
    tb2.text_frame.text = "Old Slide 2 Placeholder"

    s3 = prs.slides.add_slide(blank)
    tb3 = s3.shapes.add_textbox(100000, 100000, 3000000, 500000)
    tb3.text_frame.text = "Teammate Slide 3 Content"
    prs.save(str(remote_pptx))

    # Out-of-bounds slide_index must fail WITHOUT writing output_path
    oob_out = tmp_path / "oob_should_not_exist.pptx"
    with pytest.raises(IndexError):
        RemoteDriftGuard.reconcile_three_way_slide(
            spec_path=spec_yaml,
            remote_pptx_path=remote_pptx,
            slide_index=5,
            output_path=oob_out,
        )
    assert not oob_out.exists()

    with pytest.raises(ValueError):
        RemoteDriftGuard.reconcile_three_way_slide(
            spec_path=spec_yaml,
            remote_pptx_path=remote_pptx,
            slide_index=0,
            output_path=oob_out,
        )
    assert not oob_out.exists()

    # Replace middle slide (slide 2 of 3) and confirm sibling slides 1 & 3 + compiled shapes
    out_path = RemoteDriftGuard.reconcile_three_way_slide(
        spec_path=spec_yaml,
        remote_pptx_path=remote_pptx,
        slide_index=2,
        output_path=merged_pptx,
    )
    assert out_path.exists()

    merged_prs = Presentation(str(out_path))
    assert len(merged_prs.slides) == 3

    def _slide_texts(slide: Any) -> List[str]:
        return [
            shp.text_frame.text
            for shp in slide.shapes
            if getattr(shp, "has_text_frame", False)
        ]

    slide1_texts = _slide_texts(merged_prs.slides[0])
    slide2_texts = _slide_texts(merged_prs.slides[1])
    slide3_texts = _slide_texts(merged_prs.slides[2])

    assert any("Teammate Slide 1 Content" in t for t in slide1_texts)
    assert any("Merged Slide Title" in t for t in slide2_texts)
    assert any("Service A" in t for t in slide2_texts)
    assert any("Teammate Slide 3 Content" in t for t in slide3_texts)


def test_watch_diagram_forwards_remote_drift_and_receipt_path(tmp_path: Path) -> None:
    import src.ppt_engine.diagram_v2.watcher as watcher_mod

    spec_yaml = tmp_path / "watch_spec.yaml"
    _write_minimal_diagram_spec(spec_yaml)
    pptx_file = tmp_path / "watch_spec.pptx"
    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6])
    prs.save(str(pptx_file))

    remote_file = tmp_path / "remote" / "watch_spec.pptx"
    remote_file.parent.mkdir(parents=True)
    remote_file.write_bytes(pptx_file.read_bytes())

    receipt_file = tmp_path / ".sync_receipt.json"
    RemoteDriftGuard.pin_checkout(
        receipt_path=receipt_file,
        local_path=pptx_file,
        target_drive_path=remote_file,
        checkout_user="alice",
    )

    ev = threading.Event()
    result_holder: Dict[str, Any] = {}

    def _run_watcher() -> None:
        result_holder["watcher"] = watcher_mod.watch_diagram(
            spec_path=spec_yaml,
            pptx_path=pptx_file,
            poll_interval=0.02,
            stop_event=ev,
            remote_drift=True,
            receipt_path=receipt_file,
            drift_poll_interval=0.05,
        )

    thread = threading.Thread(target=_run_watcher, daemon=True)
    thread.start()
    time.sleep(0.15)
    ev.set()
    thread.join(timeout=3.0)
    assert not thread.is_alive()

    watcher = result_holder["watcher"]
    assert isinstance(watcher, watcher_mod.PPTXWatcher)
    assert watcher.remote_drift is True
    assert watcher.receipt_path == receipt_file.resolve()
    assert watcher._last_drift_check > 0

    # Backwards-compatible default invocation without remote_drift/receipt_path
    ev_default = threading.Event()
    ev_default.set()
    default_watcher = watcher_mod.watch_diagram(
        spec_path=spec_yaml,
        pptx_path=pptx_file,
        poll_interval=0.02,
        stop_event=ev_default,
    )
    assert default_watcher.remote_drift is False
    assert default_watcher.receipt_path is None


def test_cli_lock_remote_nested_subpath_and_traversal_guards(tmp_path: Path) -> None:
    runner = CliRunner()
    staging = tmp_path / "staging"
    drive_base = tmp_path / "gdrive"
    remote_root = drive_base / "Deliverables"
    sub_staging = staging / "sub"
    sub_remote = remote_root / "sub"
    sub_staging.mkdir(parents=True)
    sub_remote.mkdir(parents=True)

    (sub_staging / "deck.pptx").write_bytes(b"local-sub-deck")
    (sub_remote / "deck.pptx").write_bytes(b"remote-sub-deck")

    # Lock nested subpath with -d: sidecar must land in remote_root/sub/, NOT remote_root/
    res_lock = runner.invoke(
        app,
        ["stage", "lock-remote", "sub/deck.pptx", "-d", str(remote_root), "-u", "bob"],
    )
    assert res_lock.exit_code == 0, res_lock.output
    assert list(remote_root.glob("._LOCKED_*.json")) == []
    sub_locks = list(sub_remote.glob("._LOCKED_*.json"))
    assert len(sub_locks) == 1

    # Sync Gate 2 must detect the nested lock sidecar and block Alice
    manifest = _write_minimal_manifest(staging, [{"relative_path": "sub/deck.pptx"}])
    with pytest.raises(RemoteLockConflictError):
        RemoteSyncEngine().sync(
            manifest_path=manifest,
            drive_base_dir=drive_base,
            fail_on_locks=True,
            current_user="alice",
        )

    # Unlock nested subpath with -d cleanly
    res_unlock = runner.invoke(
        app,
        ["stage", "unlock-remote", "sub/deck.pptx", "-d", str(remote_root), "-u", "bob"],
    )
    assert res_unlock.exit_code == 0, res_unlock.output
    assert list(sub_remote.glob("._LOCKED_*.json")) == []

    # Reject raw trailing /. and /.. segments across lock-remote and unlock-remote
    for bad_target in ("sub/.", "sub/..", "._LOCKED_fake_20261124T000000Z_123456.json/."):
        res_bad_lock_nod = runner.invoke(
            app,
            ["stage", "lock-remote", bad_target, "-u", "alice"],
        )
        assert res_bad_lock_nod.exit_code == 1
        res_bad_lock_d = runner.invoke(
            app,
            ["stage", "lock-remote", bad_target, "-d", str(remote_root), "-u", "alice"],
        )
        assert res_bad_lock_d.exit_code == 1
        res_bad_unlock_d = runner.invoke(
            app,
            ["stage", "unlock-remote", bad_target, "-d", str(remote_root), "-u", "alice"],
        )
        assert res_bad_unlock_d.exit_code == 1

    # Reject ../ and absolute outside path traversal when -d is provided
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_lock = RemoteDriftGuard.acquire_remote_lock_sidecar(outside_dir, "secret.pptx", user="alice")

    res_escape_unlock = runner.invoke(
        app,
        ["stage", "unlock-remote", f"../outside/{outside_lock.name}", "-d", str(remote_root), "-u", "alice"],
    )
    assert res_escape_unlock.exit_code == 1
    assert outside_lock.exists()

    res_abs_escape_unlock = runner.invoke(
        app,
        ["stage", "unlock-remote", str(outside_lock), "-d", str(remote_root), "-u", "alice"],
    )
    assert res_abs_escape_unlock.exit_code == 1
    assert outside_lock.exists()

    res_escape_lock = runner.invoke(
        app,
        ["stage", "lock-remote", "../outside/secret.pptx", "-d", str(remote_root), "-u", "alice"],
    )
    assert res_escape_lock.exit_code == 1
    assert len(list(outside_dir.glob("._LOCKED_*.json"))) == 1


def test_reconcile_three_way_slide_cleans_temp_on_copy_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec_yaml = tmp_path / "diagram.yaml"
    _write_minimal_diagram_spec(spec_yaml)
    remote_pptx = tmp_path / "remote.pptx"
    remote_pptx.write_bytes(b"placeholder")
    out_pptx = tmp_path / "out.pptx"

    def failing_copy(src: Path, dst: Path, *args: Any, **kwargs: Any) -> None:
        Path(dst).write_bytes(b"partial-merge-tmp")
        raise OSError("Simulated mid-copy I/O failure")

    monkeypatch.setattr(shutil, "copy2", failing_copy)
    with pytest.raises(OSError):
        RemoteDriftGuard.reconcile_three_way_slide(
            spec_path=spec_yaml,
            remote_pptx_path=remote_pptx,
            slide_index=1,
            output_path=out_pptx,
        )
    assert not out_pptx.exists()
    assert list(tmp_path.glob(".tmp_merge_*")) == []
