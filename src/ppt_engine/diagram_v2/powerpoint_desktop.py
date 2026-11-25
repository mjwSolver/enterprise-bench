"""
Diagram Engine V2 - macOS Microsoft PowerPoint Desktop Lifecycle Manager
========================================================================
Encapsulates AppleScript queries and safe presentation lifecycle controls
(open-deck inspection, unsaved modification guard, graceful close, and
foreground activation) for atomic desktop hot-reload (`--target & --pop`).
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class PowerPointDirtyError(RuntimeError):
    """Raised when an open target presentation has unsaved edits in PowerPoint."""
    pass


def _hfs_to_posix_candidates(raw_path: str) -> List[str]:
    """Converts macOS HFS paths ('Macintosh HD:Users:alice:deck.pptx') into POSIX candidates."""
    clean = raw_path.strip()
    if ":" in clean and not clean.startswith("/") and "://" not in clean and "\\" not in clean:
        parts = [p for p in clean.split(":") if p]
        if len(parts) >= 2:
            return [
                "/" + "/".join(parts[1:]),
                "/Volumes/" + "/".join(parts),
            ]
    return [clean]


def _canonical_path_pair(target_path: Union[str, Path]) -> Tuple[str, str, str]:
    """Returns (resolved_posix_path, abs_posix_path, basename) for safe path matching."""
    raw_str = str(target_path)
    candidates = _hfs_to_posix_candidates(raw_str)
    chosen = next((c for c in candidates if Path(c).expanduser().exists()), candidates[0])
    p = Path(chosen).expanduser()
    try:
        resolved = str(p.resolve())
    except Exception:
        resolved = str(p)
    try:
        abs_p = os.path.abspath(str(p))
    except Exception:
        abs_p = str(p)
    return resolved, abs_p, p.name


def _has_path_separators(entry: str) -> bool:
    return ("/" in entry) or ("\\" in entry) or (":" in entry)


def _entry_matches_target(entry: str, target_resolved: str, target_abs: str, target_name: str, target_is_bare: bool) -> bool:
    """
    Matches an AppleScript presentation identifier against the target path.
    Full POSIX/HFS paths must match canonically; basename fallback is permitted ONLY
    when BOTH the open entry and the caller's target have no path separators (bare unsaved deck name).
    """
    clean = entry.strip()
    if not clean:
        return False
    if _has_path_separators(clean):
        for cand in _hfs_to_posix_candidates(clean):
            try:
                entry_resolved = str(Path(cand).expanduser().resolve())
            except Exception:
                entry_resolved = cand
            if entry_resolved == target_resolved or cand == target_abs or cand == target_resolved:
                return True
        return False
    return bool(target_is_bare and clean == target_name)


class PowerPointDesktopManager:
    """Manages macOS Microsoft PowerPoint inspection, clean close, and activation."""

    APP_NAME = "Microsoft PowerPoint"

    @staticmethod
    def is_supported_platform() -> bool:
        """Returns True on macOS where AppleScript and PowerPoint desktop automation exist."""
        return sys.platform == "darwin"

    @classmethod
    def is_powerpoint_running(cls) -> bool:
        """Checks whether Microsoft PowerPoint is currently running without launching it."""
        if not cls.is_supported_platform():
            return False
        try:
            res = subprocess.run(
                ["pgrep", "-x", cls.APP_NAME],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def list_open_presentations(cls) -> List[str]:
        """Returns canonical POSIX paths (or bare names for unsaved decks) of open PowerPoint presentations."""
        if not cls.is_powerpoint_running():
            return []
        script = (
            'tell application "Microsoft PowerPoint"\n'
            '    set outList to {}\n'
            '    repeat with p in presentations\n'
            '        set pFull to ""\n'
            '        try\n'
            '            set pFull to (full name of p) as text\n'
            '        end try\n'
            '        if pFull is "" then\n'
            '            set pFull to (name of p) as text\n'
            '        else if pFull does not start with "/" and pFull contains ":" then\n'
            '            try\n'
            '                set pFull to POSIX path of pFull\n'
            '            end try\n'
            '        end if\n'
            '        set end of outList to pFull\n'
            '    end repeat\n'
            '    set AppleScript\'s text item delimiters to "\\n"\n'
            '    return outList as text\n'
            'end tell'
        )
        try:
            res = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode != 0:
                return []
            return [line.strip() for line in res.stdout.splitlines() if line.strip()]
        except Exception as exc:
            logger.debug("Failed to list open PowerPoint presentations: %s", exc)
            return []

    @classmethod
    def is_presentation_open(cls, target_path: Union[str, Path]) -> bool:
        """Checks whether the exact target presentation path is currently open in PowerPoint."""
        target_resolved, target_abs, target_name = _canonical_path_pair(target_path)
        target_is_bare = not _has_path_separators(str(target_path))
        for entry in cls.list_open_presentations():
            if _entry_matches_target(entry, target_resolved, target_abs, target_name, target_is_bare):
                return True
        return False

    @classmethod
    def is_presentation_saved(cls, target_path: Union[str, Path]) -> Optional[bool]:
        """
        Queries PowerPoint's `saved` property for the target presentation (matched by canonical POSIX path).
        Returns True if saved, False if dirty/unsaved, or None if not open/unavailable.
        """
        if not cls.is_powerpoint_running():
            return None
        target_resolved, target_abs, target_name = _canonical_path_pair(target_path)
        target_is_bare = "true" if not _has_path_separators(str(target_path)) else "false"
        script = """
        on run argv
            set targetResolved to item 1 of argv
            set targetAbs to item 2 of argv
            set targetName to item 3 of argv
            set targetIsBare to item 4 of argv
            tell application "Microsoft PowerPoint"
                repeat with p in presentations
                    set pFull to ""
                    try
                        set pFull to (full name of p) as text
                    end try
                    if pFull is not "" and pFull does not start with "/" and pFull contains ":" then
                        try
                            set pFull to POSIX path of pFull
                        end try
                    end if
                    if pFull is targetResolved or pFull is targetAbs then
                        return saved of p
                    else if targetIsBare is "true" and (pFull is "" or (pFull does not contain "/" and pFull does not contain ":")) and (name of p) is targetName then
                        return saved of p
                    end if
                end repeat
            end tell
            return "NOT_FOUND"
        end run
        """
        try:
            res = subprocess.run(
                ["osascript", "-e", script, target_resolved, target_abs, target_name, target_is_bare],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode != 0:
                return None
            val = res.stdout.strip().lower()
            if val == "true":
                return True
            if val == "false":
                return False
            return None
        except Exception as exc:
            logger.debug("Failed to query saved state for %s: %s", target_resolved, exc)
            return None

    @classmethod
    def close_presentation_if_open(
        cls,
        target_path: Union[str, Path],
        force: bool = False,
        timeout_ms: int = 1000,
    ) -> bool:
        """
        Inspects and cleanly closes the target presentation in PowerPoint if open.

        Raises PowerPointDirtyError if the presentation has unsaved edits (`saved == false`)
        and `force` is False. Polls up to `timeout_ms` until the file lock (`~$<name>`)
        is released. Returns True if a presentation was closed, False otherwise.
        """
        target_p = Path(target_path)
        if not cls.is_supported_platform() or not cls.is_powerpoint_running():
            return False
        if not cls.is_presentation_open(target_p):
            return False

        saved = cls.is_presentation_saved(target_p)
        if saved is False and not force:
            raise PowerPointDirtyError(
                f"Target presentation '{target_p.name}' has unsaved modifications in PowerPoint. "
                "Save (Cmd+S) or discard (or pass --force) before hot-reloading."
            )

        target_resolved, target_abs, target_name = _canonical_path_pair(target_p)
        target_is_bare = "true" if not _has_path_separators(str(target_path)) else "false"
        script = """
        on run argv
            set targetResolved to item 1 of argv
            set targetAbs to item 2 of argv
            set targetName to item 3 of argv
            set targetIsBare to item 4 of argv
            tell application "Microsoft PowerPoint"
                repeat with idx from (count of presentations) to 1 by -1
                    set p to presentation idx
                    set pFull to ""
                    try
                        set pFull to (full name of p) as text
                    end try
                    if pFull is not "" and pFull does not start with "/" and pFull contains ":" then
                        try
                            set pFull to POSIX path of pFull
                        end try
                    end if
                    set matched to false
                    if pFull is targetResolved or pFull is targetAbs then
                        set matched to true
                    else if targetIsBare is "true" and (pFull is "" or (pFull does not contain "/" and pFull does not contain ":")) and (name of p) is targetName then
                        set matched to true
                    end if
                    if matched then
                        close p saving no
                    end if
                end repeat
            end tell
        end run
        """
        try:
            subprocess.run(
                ["osascript", "-e", script, target_resolved, target_abs, target_name, target_is_bare],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except Exception as exc:
            logger.debug("AppleScript close failed for %s: %s", target_resolved, exc)
            return False

        lock_file = target_p.parent / f"~${target_name}"
        deadline = time.monotonic() + (max(0, timeout_ms) / 1000.0)
        while time.monotonic() < deadline:
            if not lock_file.exists() and not cls.is_presentation_open(target_p):
                break
            time.sleep(0.05)

        return True

    @classmethod
    def activate_presentation(
        cls,
        target_path: Union[str, Path],
        slide_index: Optional[int] = None,
    ) -> bool:
        """
        Opens the presentation in Microsoft PowerPoint on macOS, brings it to
        the foreground (matching canonical path), and optionally navigates to `slide_index` (1-based).
        """
        target_p = Path(target_path).resolve()
        if not cls.is_supported_platform():
            logger.info("Desktop launch skipped: AppleScript not available on this platform")
            return False
        if not target_p.exists():
            logger.warning("Cannot activate missing presentation: %s", target_p)
            return False

        try:
            subprocess.run(
                ["open", "-a", cls.APP_NAME, str(target_p)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            logger.warning("Failed to launch %s for %s: %s", cls.APP_NAME, target_p, exc)
            return False

        target_resolved, target_abs, target_name = _canonical_path_pair(target_p)
        target_is_bare = "false"
        slide_num_str = str(slide_index) if slide_index and slide_index >= 1 else ""
        script = """
        on run argv
            set targetResolved to item 1 of argv
            set targetAbs to item 2 of argv
            set targetName to item 3 of argv
            set slideNumStr to item 4 of argv
            set targetIsBare to item 5 of argv
            tell application "Microsoft PowerPoint"
                activate
                try
                    repeat with p in presentations
                        set pFull to ""
                        try
                            set pFull to (full name of p) as text
                        end try
                        if pFull is not "" and pFull does not start with "/" and pFull contains ":" then
                            try
                                set pFull to POSIX path of pFull
                            end try
                        end if
                        if pFull is targetResolved or pFull is targetAbs then
                            set active presentation to p
                            exit repeat
                        else if targetIsBare is "true" and (pFull is "" or (pFull does not contain "/" and pFull does not contain ":")) and (name of p) is targetName then
                            set active presentation to p
                            exit repeat
                        end if
                    end repeat
                end try
                if slideNumStr is not "" then
                    try
                        set slideNum to slideNumStr as integer
                        go to slide active window view number slideNum
                    end try
                end if
            end tell
        end run
        """
        try:
            subprocess.run(
                ["osascript", "-e", script, target_resolved, target_abs, target_name, slide_num_str, target_is_bare],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return True
        except Exception as exc:
            logger.debug("AppleScript activation failed for %s: %s", target_resolved, exc)
            return False
