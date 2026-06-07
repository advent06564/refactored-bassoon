"""Shared utilities for the Unified Launcher system.

Provides:
- Launch-tracking to prevent the same program from being opened twice
- Process-level detection to skip programs already running system-wide
- Cross-platform executable resolution
- Consistent launch helpers
"""

import os
import shutil
import subprocess
import platform as _platform


# ── Launch Tracker (singleton) ────────────────────────────────────────────────

class _LaunchTracker:
    """Tracks programs that have already been launched in this session."""

    def __init__(self):
        self._launched: set[str] = set()

    def was_launched(self, name: str) -> bool:
        return name in self._launched

    def mark_launched(self, name: str) -> None:
        self._launched.add(name)

    def clear(self) -> None:
        self._launched.clear()


_tracker = _LaunchTracker()


def was_launched(name: str) -> bool:
    """Check if a program (by logical name) was already launched this session."""
    return _tracker.was_launched(name)


def reset_tracker() -> None:
    """Reset the launch tracker (e.g. between menu cycles)."""
    _tracker.clear()


# ── Path resolution ───────────────────────────────────────────────────────────

def find_first_existing(paths: list[str]) -> str | None:
    """Return the first path from the list that exists on the filesystem."""
    for path in paths:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            return expanded
    return None


# ── Launch helpers ────────────────────────────────────────────────────────────

def is_process_running(exe_name: str) -> bool:
    """Check if a process with the given executable name is running.

    Uses tasklist on Windows; returns False on non-Windows or if tasklist
    is unavailable (failing open so the user can still attempt a launch).

    Args:
        exe_name: Executable name (e.g. 'Steam.exe', 'obs64.exe').
    """
    if not is_windows():
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # tasklist returns the exe name in its output if the process is running
        return exe_name.lower() in result.stdout.lower()
    except Exception:
        # If we can't check, fail open — don't block a legitimate launch
        return False


def launch_exe(path: str, name: str, *, skip_if_launched: bool = True, exe_name: str | None = None) -> bool:
    """Launch an executable and print status.

    Args:
        path: Full path to the executable.
        name: Logical display name (also used for de-duplication).
        skip_if_launched: If True (default), skip launching if `name` was
            already launched this session OR if the process is already running.
        exe_name: Optional process name to check (e.g. 'obs64.exe').
            Derived from path basename if not provided.
    """
    if skip_if_launched and _tracker.was_launched(name):
        print(f"  [SKIP] Already launched: {name}")
        return True

    # Resolve the exe name for process-level checking
    proc_name = exe_name or os.path.basename(path)
    if skip_if_launched and is_process_running(proc_name):
        print(f"  [SKIP] Already running: {name}")
        _tracker.mark_launched(name)
        return True

    try:
        subprocess.Popen([path])
        print(f"  [OK] Launched: {name}")
        _tracker.mark_launched(name)
        return True
    except Exception as e:
        print(f"  [FAIL] Error launching {name}: {e}")
        return False


def launch_exe_from_paths(
    paths: list[str],
    name: str,
    *,
    skip_if_launched: bool = True,
    exe_name: str | None = None,
) -> bool:
    """Find the first existing path and launch it.

    Returns True if the program was found and launch was attempted.
    """
    if skip_if_launched and _tracker.was_launched(name):
        print(f"  [SKIP] Already launched: {name}")
        return True

    # Check process-level for each candidate path
    if skip_if_launched and exe_name and is_process_running(exe_name):
        print(f"  [SKIP] Already running: {name}")
        _tracker.mark_launched(name)
        return True

    found = find_first_existing(paths)
    if found:
        return launch_exe(found, name, skip_if_launched=False, exe_name=exe_name)
    else:
        print(f"  - Not found: {name}")
        return False


def launch_uwp(uri: str, name: str, *, skip_if_launched: bool = True) -> bool:
    """Launch a UWP / protocol-handler app on Windows.

    Uses cmd.exe /c start to invoke the URI handler reliably.
    """
    if skip_if_launched and _tracker.was_launched(name):
        print(f"  [SKIP] Already launched: {name}")
        return True

    try:
        # Use cmd /c start for reliable URI launching on Windows
        subprocess.Popen(["cmd", "/c", "start", "", uri])
        print(f"  [OK] Launched: {name}")
        _tracker.mark_launched(name)
        return True
    except Exception as e:
        print(f"  [FAIL] Error launching {name}: {e}")
        return False


def launch_os_startfile(path: str, name: str, *, skip_if_launched: bool = True, exe_name: str | None = None) -> bool:
    """Launch via os.startfile (Windows .lnk shortcuts, etc.)."""
    if skip_if_launched and _tracker.was_launched(name):
        print(f"  [SKIP] Already launched: {name}")
        return True

    # Check process-level if an exe_name is provided
    if skip_if_launched and exe_name and is_process_running(exe_name):
        print(f"  [SKIP] Already running: {name}")
        _tracker.mark_launched(name)
        return True

    try:
        os.startfile(path)
        print(f"  [OK] Launched: {name}")
        _tracker.mark_launched(name)
        return True
    except FileNotFoundError:
        print(f"  - Not found: {name}")
        return False
    except Exception as e:
        print(f"  [FAIL] Error launching {name}: {e}")
        return False


# ── Platform info ─────────────────────────────────────────────────────────────

def is_windows() -> bool:
    return _platform.system() == "Windows"


def is_macos() -> bool:
    return _platform.system() == "Darwin"


# ── Environment variable helpers ──────────────────────────────────────────────

def _env_paths() -> dict[str, str]:
    """Return common environment-derived path prefixes."""
    return {
        "PROGFILES": os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        "PROGFILES_X86": os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        "USERPROFILE": os.environ.get("USERPROFILE", r"C:\Users\Default"),
        "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
        "APPDATA": os.environ.get("APPDATA", ""),
    }


ENV = _env_paths()
