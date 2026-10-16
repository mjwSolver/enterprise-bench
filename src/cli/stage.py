"""
Delivery Staging & Collaborative Lock CLI Router (`bench stage ...`)
===================================================================
Preflight gatekeeping, multi-user file lock coordination, presentation
status overlay badges, and cryptographic SHA-256 delivery manifests.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint
from rich.table import Table

from src.core.delivery import (
    DeliveryError,
    DeliveryManifest,
    LockConflictError,
    LockManager,
    LockNotFoundError,
    LockOwnershipError,
    OverlayManager,
    OverlayStatus,
    PreflightGateError,
    RemoteLockConflictError,
    RemoteSyncEngine,
    StagingPipeline,
    SyncStatus,
    SyncTransmissionError,
    discover_google_drive_mounts,
    resolve_target_drive_root,
)
from src.cli.utils import console


stage_app = typer.Typer(
    name="stage",
    help="Delivery Staging, Collaborative Locks, and Preflight Gates",
    no_args_is_help=True,
)


@stage_app.command("checkout")
def stage_checkout(
    file: str = typer.Argument(..., help="Path to deliverable file to lock and check out"),
    user: str = typer.Option(..., "--user", "-u", help="Username / agent ID checking out the file"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Reason for checkout or active workstream"),
) -> None:
    """Acquires a collaborative lock and stamps DRAFT overlay badge atomically on presentations."""
    target_path = Path(file)
    lock_mgr = LockManager()
    overlay_mgr = OverlayManager()

    try:
        payload = lock_mgr.acquire_lock(target_path, user=user, reason=reason)
        rprint(f"[green]✓ Lock acquired successfully:[/green] [bold]{target_path.name}[/bold]")
        rprint(f"  Owner:        [bold cyan]{payload.user}[/bold cyan]")
        rprint(f"  Locked At:    [dim]{payload.locked_at}[/dim]")
        rprint(f"  Working Copy: [bold green]{payload.locked_copy_path}[/bold green]")
        rprint(f"  Sidecar:      [dim]{payload.lock_file}[/dim]")

        # If presentation, stamp DRAFT overlay badge onto the working copy
        copy_p = Path(payload.locked_copy_path)
        if copy_p.suffix.lower() == ".pptx" and copy_p.exists():
            overlay_mgr.stamp(copy_p, status=OverlayStatus.DRAFT)
            rprint(f"  Status Badge: [yellow]Stamped [DRAFT] on working copy slides[/yellow]")

    except (LockConflictError, LockNotFoundError, DeliveryError) as exc:
        rprint(f"[bold red]Lock Error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@stage_app.command("commit")
def stage_commit(
    file: str = typer.Argument(..., help="Path to deliverable file, working copy, or lock sidecar"),
    user: str = typer.Option(..., "--user", "-u", help="Username releasing the lock"),
    approved: bool = typer.Option(False, "--approved", "-a", help="Stamp APPROVED badge on presentation before release (otherwise strips draft badge)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force release even if locked by another user"),
) -> None:
    """Validates integrity, updates badge to approved (or strips), and releases lock."""
    lock_mgr = LockManager()
    overlay_mgr = OverlayManager()
    target, lock_file = lock_mgr._resolve_target_and_lock_paths(file)

    try:
        # Determine working copy path from lock sidecar
        locked_copy = target.parent / f"{target.stem}_LOCKED_{user}{target.suffix}"
        if locked_copy.exists() and locked_copy.suffix.lower() == ".pptx":
            if approved:
                overlay_mgr.stamp(locked_copy, status=OverlayStatus.APPROVED)
                rprint(f"[cyan]ℹ Stamped [APPROVED] overlay badge on working copy before merge.[/cyan]")
            else:
                overlay_mgr.strip(locked_copy)
                rprint(f"[cyan]ℹ Stripped working overlay badges from working copy before merge.[/cyan]")

        payload = lock_mgr.release_lock(file, user=user, merge=True, force=force)
        rprint(f"[green]✓ Lock released and working copy merged:[/green] [bold]{target.name}[/bold]")
        rprint(f"  Released by:  [bold cyan]{user}[/bold cyan]")
        rprint(f"  Master State: [bold green]{target}[/bold green]")

    except (LockNotFoundError, LockOwnershipError, DeliveryError) as exc:
        rprint(f"[bold red]Release Error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@stage_app.command("status")
def stage_status(
    directory: str = typer.Argument("output", help="Directory or file path to check lock statuses"),
) -> None:
    """Shows active collaborative locks and file states in a Rich table."""
    lock_mgr = LockManager()
    target = Path(directory)

    if not target.exists():
        rprint(f"[red]Error:[/red] Path not found: {directory}")
        raise typer.Exit(code=1)

    if target.is_file():
        status = lock_mgr.get_status(target)
        table = Table(title=f"File Lock Status: {target.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="bold")
        table.add_row("Is Locked", "[red]YES[/red]" if status.is_locked else "[green]NO[/green]")
        table.add_row("Target File", status.target_file)
        table.add_row("Locked By", status.user or "None")
        table.add_row("Locked At", status.locked_at or "None")
        table.add_row("Reason", status.reason or "None")
        table.add_row("Working Copy", status.locked_copy_path or "None")
        console.print(table)
        return

    locks = lock_mgr.list_locks(target)
    if not locks:
        rprint(f"[green]✓ Zero active locks in:[/green] [bold]{directory}[/bold] (all deliverables unlocked)")
        return

    table = Table(title=f"Active Collaborative Locks ({len(locks)} files locked)")
    table.add_column("Target File", style="bold")
    table.add_column("Locked By", style="cyan")
    table.add_column("Locked At", style="dim")
    table.add_column("Reason", style="magenta")
    table.add_column("Working Copy", style="green")

    for lk in locks:
        target_name = Path(lk.target_file).name
        copy_name = Path(lk.locked_copy_path).name if lk.locked_copy_path else "None"
        table.add_row(
            target_name,
            lk.user or "UNKNOWN",
            lk.locked_at or "N/A",
            lk.reason or "Active editing",
            copy_name,
        )

    console.print(table)


@stage_app.command("preflight")
def stage_preflight(
    directory: str = typer.Argument("output", help="Directory containing staged deliverables"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Fail with exit code 1 if any gate fails or active locks exist"),
) -> None:
    """Headless preflight verification (Gate 1 locks, Gate 2 badges, Gate 3 checksums & corruption)."""
    dir_path = Path(directory)
    pipeline = StagingPipeline()

    rprint(f"[cyan]ℹ Running stage-gate preflight checks on:[/cyan] [bold]{directory}[/bold]")
    report = pipeline.run_preflight(dir_path, fail_on_locks=strict)

    table = Table(title=f"Preflight Gate Verification: {dir_path.name}")
    table.add_column("Gate Name", style="bold cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details / Message", style="white")

    for g in report.gates:
        status_styled = "[green]✓ PASS[/green]" if g.passed else "[red]✗ FAIL[/red]"
        table.add_row(g.gate_name, status_styled, g.message)

    console.print(table)

    if report.warnings:
        rprint(f"\n[yellow]Warnings ({len(report.warnings)}):[/yellow]")
        for w in report.warnings:
            rprint(f"  • [yellow]{w}[/yellow]")

    if report.errors:
        rprint(f"\n[red]Errors ({len(report.errors)}):[/red]")
        for e in report.errors:
            rprint(f"  • [red]{e}[/red]")

    if not report.passed:
        rprint(f"\n[red]✗ Preflight verification FAILED for:[/red] [bold]{directory}[/bold]")
        if strict:
            raise typer.Exit(code=1)
    else:
        rprint(f"\n[green]✓ All preflight gates PASSED ({report.total_files} deliverables ready).[/green]")


@stage_app.command("manifest")
def stage_manifest(
    directory: str = typer.Argument("output", help="Directory containing staged deliverables"),
    target_root: str = typer.Option("BSIM_Migration_Deliverables", "--target-root", "-t", help="Target shared Google Drive root folder name or path"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional path to output JSON manifest (defaults to <directory>/delivery_manifest.json)"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Fail if active locks or corrupted files are present"),
) -> None:
    """Builds cryptographically signed SHA-256 staging manifest for delivery handover."""
    dir_path = Path(directory)
    out_manifest = Path(output) if output else dir_path / "delivery_manifest.json"
    pipeline = StagingPipeline()

    rprint(f"[cyan]ℹ Generating staging delivery manifest for:[/cyan] [bold]{directory}[/bold]")
    try:
        manifest = pipeline.generate_manifest(
            directory=dir_path,
            target_drive_root=target_root,
            output_manifest_path=out_manifest,
            fail_on_locks=strict,
        )

        rprint(f"[green]✓ Delivery manifest compiled successfully:[/green] [bold]{manifest.delivery_id}[/bold]")
        rprint(f"  Source:       {manifest.source_directory}")
        rprint(f"  Target Root:  {manifest.target_drive_root}")
        rprint(f"  Total Files:  {manifest.total_files} files ({manifest.total_bytes:,} bytes)")
        rprint(f"  Manifest:     [bold green]{out_manifest}[/bold green]")

        table = Table(title=f"Manifest Inventory ({manifest.total_files} files)")
        table.add_column("Relative Path", style="bold")
        table.add_column("Size", justify="right")
        table.add_column("SHA-256", style="dim")
        table.add_column("Overlay Badge", style="magenta")

        for entry in manifest.files:
            size_str = f"{entry.file_size_bytes:,} B"
            badge_str = entry.overlay_status or "[dim]None[/dim]"
            table.add_row(
                entry.relative_path,
                size_str,
                f"{entry.sha256[:12]}...",
                badge_str,
            )

        console.print(table)

    except PreflightGateError as exc:
        rprint(f"[bold red]Manifest Generation Error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@stage_app.command("strip-badges")
def stage_strip_badges(
    file: str = typer.Argument(..., help="Path to PowerPoint .pptx file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional destination path (defaults to in-place)"),
) -> None:
    """Purges status overlay badges from presentation slides."""
    p_in = Path(file)
    if not p_in.exists():
        rprint(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    overlay_mgr = OverlayManager()
    try:
        report = overlay_mgr.strip(p_in, output_path=output)
        target_name = output or str(p_in)
        rprint(f"[green]✓ Purged overlay badges from {len(report.stripped_slides)} slide(s) in:[/green] [bold]{target_name}[/bold]")
    except Exception as exc:
        rprint(f"[bold red]Error stripping badges:[/bold red] {exc}")
        raise typer.Exit(code=1)


def _render_inline_meter(current: int, total: int, width: int = 16) -> str:
    """Renders standard inline progress meter e.g. [████████░░░░░░░░] 50%."""
    if total <= 0:
        return f"[{'░' * width}] 0%"
    fraction = min(max(current / total, 0.0), 1.0)
    filled = int(round(fraction * width))
    bar = "█" * filled + "░" * (width - filled)
    percent = int(fraction * 100)
    return f"[{bar}] {percent}%"


@stage_app.command("sync")
def stage_sync(
    directory: str = typer.Argument("doc_output", help="Directory containing staged deliverables and manifest"),
    manifest: Optional[str] = typer.Option(None, "--manifest", "-m", help="Explicit path to .staging_manifest.json or delivery_manifest.json"),
    target_root: Optional[str] = typer.Option(None, "--target-root", "-t", help="Shared Google Drive folder name or path"),
    drive_dir: Optional[str] = typer.Option(None, "--drive-dir", "-d", help="Explicit base directory for mounted Google Drive"),
    category: Optional[List[str]] = typer.Option(None, "--category", "-c", help="Filter specific category/categories to synchronize"),
    format: Optional[List[str]] = typer.Option(None, "--format", "-f", help="Filter specific formats (e.g. pptx, svg, drawio, png)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate synchronization without writing or modifying files"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Fail if active collaborative locks or lock collisions exist"),
    receipt: Optional[str] = typer.Option(None, "--receipt", "-r", help="Path to write .sync_receipt.json (defaults to <directory>/.sync_receipt.json)"),
) -> None:
    """Transmits staged deliverables from manifest to shared Google Drive target root."""
    dir_path = Path(directory)
    
    # Locate manifest
    manifest_p: Optional[Path] = None
    if manifest:
        manifest_p = Path(manifest).resolve()
    else:
        for candidate in [
            dir_path / ".staging_manifest.json",
            dir_path / "delivery_manifest.json",
            Path(".staging_manifest.json"),
            Path("delivery_manifest.json"),
        ]:
            if candidate.exists():
                manifest_p = candidate.resolve()
                break

    if not manifest_p or not manifest_p.exists():
        rprint(f"[bold red]Error:[/bold red] No delivery manifest found in '{directory}'. Run [bold cyan]bench stage manifest[/bold cyan] first.")
        raise typer.Exit(code=1)

    rprint(f"[cyan]ℹ Loading staging manifest from:[/cyan] [bold]{manifest_p}[/bold]")
    engine = RemoteSyncEngine()

    try:
        def on_progress(cur: int, tot: int, fname: str, status: SyncStatus) -> None:
            meter = _render_inline_meter(cur, tot)
            status_style = {
                SyncStatus.TRANSMITTED: "[green]TRANSMITTED[/green]",
                SyncStatus.SKIPPED_IDENTICAL: "[dim cyan]UP-TO-DATE[/dim cyan]",
                SyncStatus.DRY_RUN: "[yellow]DRY-RUN[/yellow]",
                SyncStatus.LOCKED_CONFLICT: "[red]LOCKED[/red]",
                SyncStatus.FAILED: "[red]FAILED[/red]",
            }.get(status, f"[dim]{status.value}[/dim]")
            rprint(f"  {meter} ({cur}/{tot}) {status_style} {fname}")

        mode_banner = "[yellow][DRY RUN MODE][/yellow] " if dry_run else ""
        rprint(f"{mode_banner}[bold]Starting differential transmission to Google Drive target root...[/bold]")

        res = engine.sync(
            manifest_path=manifest_p,
            target_drive_root=target_root,
            drive_base_dir=drive_dir,
            categories=category,
            formats=format,
            dry_run=dry_run,
            fail_on_locks=strict,
            output_receipt_path=receipt,
            progress_callback=on_progress,
        )

        rprint("\n" + "=" * 70)
        status_word = "Simulated" if dry_run else "Completed"
        rprint(f"[bold green]✓ Google Drive Transmission {status_word}:[/bold green] [bold]{res.sync_id}[/bold]")
        rprint(f"  Target Root:      [bold cyan]{res.resolved_target_root}[/bold cyan]")
        rprint(f"  Total Evaluated:  {res.total_files} file(s)")
        rprint(f"  Transmitted:      [bold green]{res.transmitted_count}[/bold green] file(s) ({res.total_bytes_transmitted:,} bytes)")
        rprint(f"  Skipped (Identical): [dim cyan]{res.skipped_count}[/dim cyan] file(s)")
        if res.failed_count > 0:
            rprint(f"  Failed:           [bold red]{res.failed_count}[/bold red] file(s)")
        out_receipt = receipt or str(manifest_p.parent / ".sync_receipt.json")
        rprint(f"  Receipt Ledger:   [bold green]{out_receipt}[/bold green]")
        rprint("=" * 70)

        # Summary Table of Transmitted / Modified Items
        active_items = [it for it in res.items if it.status != SyncStatus.SKIPPED_IDENTICAL]
        if active_items:
            table = Table(title=f"Transmission Activity ({len(active_items)} items)")
            table.add_column("Deliverable", style="bold")
            table.add_column("Category", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Size", justify="right")
            table.add_column("SHA-256", style="dim")
            table.add_column("Target Destination", style="dim")

            for it in active_items:
                status_color = "[green]TRANSMITTED[/green]" if it.status == SyncStatus.TRANSMITTED else f"[yellow]{it.status.value}[/yellow]"
                table.add_row(
                    it.name,
                    it.category or "root",
                    status_color,
                    f"{it.size_bytes:,} B",
                    f"{it.sha256[:10]}...",
                    Path(it.target_drive_path).name,
                )
            console.print(table)
        else:
            rprint("[cyan]ℹ All staged files are identical to remote copies; zero bytes transmitted.[/cyan]")

        if res.failed_count > 0 and strict:
            raise typer.Exit(code=1)

    except (LockConflictError, RemoteLockConflictError, PreflightGateError, SyncTransmissionError) as exc:
        rprint(f"\n[bold red]Sync Transmission Error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@stage_app.command("push")
def stage_push(
    directory: str = typer.Argument("doc_output", help="Directory containing staged deliverables and manifest"),
    manifest: Optional[str] = typer.Option(None, "--manifest", "-m", help="Explicit path to .staging_manifest.json or delivery_manifest.json"),
    target_root: Optional[str] = typer.Option(None, "--target-root", "-t", help="Shared Google Drive folder name or path"),
    drive_dir: Optional[str] = typer.Option(None, "--drive-dir", "-d", help="Explicit base directory for mounted Google Drive"),
    category: Optional[List[str]] = typer.Option(None, "--category", "-c", help="Filter specific category/categories to synchronize"),
    format: Optional[List[str]] = typer.Option(None, "--format", "-f", help="Filter specific formats (e.g. pptx, svg, drawio, png)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate synchronization without writing or modifying files"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Fail if active collaborative locks or lock collisions exist"),
    receipt: Optional[str] = typer.Option(None, "--receipt", "-r", help="Path to write .sync_receipt.json (defaults to <directory>/.sync_receipt.json)"),
) -> None:
    """Push staged deliverables to shared Google Drive target root (alias for bench stage sync)."""
    stage_sync(
        directory=directory,
        manifest=manifest,
        target_root=target_root,
        drive_dir=drive_dir,
        category=category,
        format=format,
        dry_run=dry_run,
        strict=strict,
        receipt=receipt,
    )

