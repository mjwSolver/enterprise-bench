"""
Diagram Engine V2 - Autonomous PPTX File Watcher & Reverse Geometric Synchronization Daemon
==========================================================================================
Monitors compiled presentation deliverables for human edits in Microsoft PowerPoint.
When an author saves (`Cmd+S`), the daemon intercepts the save event, debounces write
bursts, extracts structural and geometric mutations, reconciles the YAML AST, snaps
coordinates to clean 0.05" grid increments, and headlessly compiles companion formats
(SVG, PNG, Draw.io) with cyclic write loop suppression (--skip-pptx).
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from src.ppt_engine.diagram_v2.compiler import compile_diagram, load_diagram_spec
from src.ppt_engine.diagram_v2.models import DiagramSpec
from src.ppt_engine.diagram_v2.reconciler import (
    DiagramReconciler,
    ReconciliationResult,
    reconcile_diagram,
)

logger = logging.getLogger(__name__)


@dataclass
class WatcherEvent:
    """Record of a triggered filesystem reconciliation event."""
    timestamp: float
    pptx_path: Path
    spec_path: Path
    result: ReconciliationResult


class PPTXWatcher:
    """
    Autonomous filesystem watcher monitoring PowerPoint presentations for human edits.
    Implements lock-file filtering, atomic write debouncing, coordinate grid snapping,
    and cyclic write loop prevention.
    """

    def __init__(
        self,
        spec_path: Union[str, Path],
        pptx_path: Optional[Union[str, Path]] = None,
        slide_index: int = 1,
        debounce_seconds: float = 0.5,
        snap_grid: float = 0.05,
        snap_threshold: float = 0.02,
        skip_pptx: bool = True,
        formats: Sequence[str] = ("drawio", "svg", "png"),
        poll_interval: float = 0.1,
        on_reconciled: Optional[Callable[[ReconciliationResult], None]] = None,
        on_change_detected: Optional[Callable[[Path], None]] = None,
    ) -> None:
        self.spec_path = Path(spec_path).resolve()
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Diagram specification not found: {self.spec_path}")

        self.slide_index = slide_index
        self.debounce_seconds = max(0.1, float(debounce_seconds))
        self.snap_grid = max(0.001, float(snap_grid))
        self.snap_threshold = max(0.0001, float(snap_threshold))
        self.skip_pptx = skip_pptx
        self.formats = list(formats)
        self.poll_interval = max(0.02, float(poll_interval))
        self.on_reconciled = on_reconciled
        self.on_change_detected = on_change_detected

        self._spec: DiagramSpec = load_diagram_spec(self.spec_path)

        # Resolve or auto-locate PPTX path
        if pptx_path:
            self.pptx_path = Path(pptx_path).resolve()
        else:
            self.pptx_path = self._resolve_target_pptx()

        self._running = False
        self._last_mtime: float = 0.0
        self._last_size: int = 0
        self._stop_event = threading.Event()

    def _resolve_target_pptx(self) -> Path:
        """Resolves target PowerPoint presentation path, compiling initial baseline if absent."""
        candidates = [
            Path("output/diagrams_v2") / f"{self._spec.id}.pptx",
            Path("output/diagrams_v2") / f"{self.spec_path.stem}.pptx",
            self.spec_path.parent / f"{self.spec_path.stem}.pptx",
            self.spec_path.parent / f"{self._spec.id}.pptx",
        ]
        for c in candidates:
            resolved = c.resolve()
            if resolved.exists():
                return resolved

        # Auto-compile baseline presentation if not found
        logger.info("Compiled presentation not found. Compiling baseline deliverables for %s...", self.spec_path.name)
        res = compile_diagram(self.spec_path, formats=["all"])
        if res.pptx_path and res.pptx_path.exists():
            return res.pptx_path.resolve()

        return candidates[0].resolve()

    def _is_file_ready(self, path: Path) -> bool:
        """
        Verifies whether PowerPoint has finished atomic flushing and released write locks.
        Filters lock files and confirms ZIP central directory integrity.
        """
        if not path.exists():
            return False
        # Filter PowerPoint transient lock files (~$*.pptx)
        if path.name.startswith("~$") or path.suffix.lower() != ".pptx":
            return False

        try:
            # Check file size non-zero and verify ZIP structure
            if path.stat().st_size == 0:
                return False
            with zipfile.ZipFile(str(path), "r") as zf:
                # Reading namelist validates ZIP end-of-central-directory record
                names = zf.namelist()
                if "ppt/presentation.xml" not in names:
                    return False
            return True
        except (zipfile.BadZipFile, OSError, PermissionError):
            return False

    def _get_file_state(self) -> Tuple[float, int]:
        """Returns current (mtime, size) of target presentation file."""
        if not self.pptx_path.exists():
            return (0.0, 0)
        try:
            st = self.pptx_path.stat()
            return (st.st_mtime, st.st_size)
        except OSError:
            return (0.0, 0)

    def trigger_reconciliation(self) -> Optional[ReconciliationResult]:
        """Executes reverse reconciliation, AST synchronization, and companion regeneration."""
        try:
            res = reconcile_diagram(
                spec_path=self.spec_path,
                pptx_path=self.pptx_path,
                slide_index=self.slide_index,
                dry_run=False,
                no_recompile=False,
                formats=self.formats,
                skip_pptx=self.skip_pptx,
                snap_grid=self.snap_grid,
                snap_threshold=self.snap_threshold,
            )

            # Record updated mtime and size to suppress cyclic triggers
            cur_mtime, cur_size = self._get_file_state()
            self._last_mtime = cur_mtime
            self._last_size = cur_size

            if self.on_reconciled:
                self.on_reconciled(res)
            return res
        except Exception as e:
            logger.error("Reverse reconciliation failed: %s", e)
            return None

    def watch(self, stop_event: Optional[threading.Event] = None) -> None:
        """
        Main watching loop monitoring filesystem modification events.
        Debounces rapid write bursts (500ms sliding window) and triggers reconciliation.
        """
        active_stop = stop_event or self._stop_event
        self._running = True

        # Initialize baseline state
        self._last_mtime, self._last_size = self._get_file_state()
        logger.info(
            "Watching presentation: %s for spec: %s (Debounce: %.2fs, Snap: %.2f\")",
            self.pptx_path,
            self.spec_path,
            self.debounce_seconds,
            self.snap_grid,
        )

        pending_change = False
        last_change_time = 0.0

        try:
            while not active_stop.is_set() and self._running:
                cur_mtime, cur_size = self._get_file_state()

                # Detect modification on target PPTX
                if (cur_mtime != self._last_mtime or cur_size != self._last_size) and cur_mtime > 0:
                    if not pending_change:
                        pending_change = True
                        if self.on_change_detected:
                            self.on_change_detected(self.pptx_path)
                    last_change_time = time.time()
                    self._last_mtime = cur_mtime
                    self._last_size = cur_size

                # Check sliding debounce window
                if pending_change:
                    elapsed = time.time() - last_change_time
                    if elapsed >= self.debounce_seconds:
                        # Wait for presentation to become fully flushed and readable
                        if self._is_file_ready(self.pptx_path):
                            pending_change = False
                            self.trigger_reconciliation()
                        else:
                            # File still busy/locked; extend wait window slightly
                            time.sleep(0.05)

                time.sleep(self.poll_interval)
        finally:
            self._running = False

    def stop(self) -> None:
        """Signals the watcher daemon to stop monitoring."""
        self._running = False
        self._stop_event.set()


def watch_diagram(
    spec_path: Union[str, Path],
    pptx_path: Optional[Union[str, Path]] = None,
    slide_index: int = 1,
    debounce_seconds: float = 0.5,
    snap_grid: float = 0.05,
    snap_threshold: float = 0.02,
    skip_pptx: bool = True,
    formats: Sequence[str] = ("drawio", "svg", "png"),
    poll_interval: float = 0.1,
    on_reconciled: Optional[Callable[[ReconciliationResult], None]] = None,
    on_change_detected: Optional[Callable[[Path], None]] = None,
    stop_event: Optional[threading.Event] = None,
) -> PPTXWatcher:
    """Public helper function creating and running PPTXWatcher."""
    watcher = PPTXWatcher(
        spec_path=spec_path,
        pptx_path=pptx_path,
        slide_index=slide_index,
        debounce_seconds=debounce_seconds,
        snap_grid=snap_grid,
        snap_threshold=snap_threshold,
        skip_pptx=skip_pptx,
        formats=formats,
        poll_interval=poll_interval,
        on_reconciled=on_reconciled,
        on_change_detected=on_change_detected,
    )
    watcher.watch(stop_event=stop_event)
    return watcher
