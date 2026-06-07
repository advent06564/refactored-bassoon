"""Launcher Diagnostic Tool -- checks path existence and health without launching.

Usage:
    python diagnostic.py            # Check all paths and process detection
    python diagnostic.py --launch   # Also attempt actual launches (interactive)
    python diagnostic.py --obs      # Check OBS specifically
"""

import os
import sys
import subprocess

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    is_process_running,
    find_first_existing,
    ENV,
    reset_tracker,
    was_launched,
)
from launcher import (
    _GAME_LAUNCHERS,
    _GAME_LAUNCHER_EXES,
    _BROWSER_EXECUTABLES,
    _LIVE_KIT_APPS,
    _LIVE_KIT_EXES,
)


# -- Colors (ANSI) ------------------------------------------------------------

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def ok(text: str) -> str:
    return f"{GREEN}{text}{RESET}"

def fail(text: str) -> str:
    return f"{RED}{text}{RESET}"

def warn(text: str) -> str:
    return f"{YELLOW}{text}{RESET}"

def info(text: str) -> str:
    return f"{CYAN}{text}{RESET}"

def bold(text: str) -> str:
    return f"{BOLD}{text}{RESET}"

SEP = "-" * 60
EQ = "=" * 60


# -- Path Checking ------------------------------------------------------------

def check_paths(category: str, paths_dict: dict, exe_map: dict | None = None) -> None:
    """Check existence of all paths in a launcher dictionary."""
    print(f"\n{bold(SEP)}")
    print(f"  {bold(category)}")
    print(f"{bold(SEP)}")

    found_count = 0
    missing_count = 0
    running_count = 0

    for name, paths_or_path in paths_dict.items():
        # Normalize to list
        if isinstance(paths_or_path, list):
            paths = paths_or_path
        else:
            paths = [paths_or_path]

        resolved = None
        for p in paths:
            expanded = os.path.expandvars(p)
            if os.path.exists(expanded):
                resolved = expanded
                break

        if resolved:
            found_count += 1
            print(f"  {ok('[FOUND]')} {name}")
            print(f"          Path: {resolved}")

            # Check if the process is already running
            if exe_map and name in exe_map:
                exe = exe_map[name]
                if is_process_running(exe):
                    running_count += 1
                    print(f"          Status: {warn('[RUNNING]')} ({exe} is active)")
                else:
                    print(f"          Status: Not running")
        else:
            missing_count += 1
            print(f"  {fail('[MISS]')} {name}")
            if len(paths) <= 3:
                for p in paths:
                    print(f"           X {p}")
            else:
                print(f"           X {len(paths)} paths checked -- none found")

    print(f"\n  {bold('Summary:')} {ok(str(found_count))} found, "
          f"{fail(str(missing_count))} missing, "
          f"{warn(str(running_count))} already running")


def check_obs_specifically() -> None:
    """Detailed check for OBS Studio installation."""
    print(f"\n{bold(SEP)}")
    print(f"  {bold('OBS Studio -- Detailed Check')}")
    print(f"{bold(SEP)}")

    obs_path = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
    obs_dir = r"C:\Program Files\obs-studio\bin\64bit"

    print(f"  Expected path: {obs_path}")

    if os.path.exists(obs_path):
        print(f"  {ok('[OK]')} obs64.exe exists at the correct location")
        print(f"  Directory contents:")
        try:
            items = os.listdir(obs_dir)
            dlls = [f for f in items if f.endswith('.dll')]
            exes = [f for f in items if f.endswith('.exe')]
            print(f"    {len(dlls)} DLL files")
            print(f"    {len(exes)} executable files")
        except Exception as e:
            print(f"  {fail('[ERR]')} Could not list directory: {e}")
    else:
        print(f"  {fail('[MISS]')} obs64.exe not found at expected path")
        # Try alternative paths
        alt_paths = [
            r"C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe",
            os.path.join(ENV["LOCALAPPDATA"], r"obs-studio\bin\64bit\obs64.exe"),
            os.path.join(ENV["PROGFILES"], r"obs-studio\bin\64bit\obs64.exe"),
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                print(f"  {ok('[ALT]')} Found at alternative path: {alt}")
                break
        else:
            print(f"  {fail('[FAIL]')} OBS Studio not found at any known path")

    if is_process_running("obs64.exe"):
        print(f"  {warn('[RUNNING]')} OBS Studio is currently running")
    else:
        print(f"  OBS Studio is not running")


# -- Process Detection Test ---------------------------------------------------

def test_process_detection() -> None:
    """Test the process detection system."""
    print(f"\n{bold(SEP)}")
    print(f"  {bold('Process Detection System Check')}")
    print(f"{bold(SEP)}")

    print(f"  Platform: {sys.platform}")

    # Test with a process that should be running (explorer.exe on Windows)
    if os.name == "nt":
        explorer_running = is_process_running("explorer.exe")
        print(f"  explorer.exe running: {ok('Yes') if explorer_running else fail('No')} "
              f"{'(should be Yes on Windows)' if not explorer_running else ''}")

        # Test with a process that should NOT be running
        fake_running = is_process_running("thisshouldnotexist12345.exe")
        print(f"  Fake process detected: {ok('No') if not fake_running else fail('!! YES -- unexpected')}")

        svchost_running = is_process_running("svchost.exe")
        print(f"  svchost.exe running: {ok('Yes') if svchost_running else fail('No')}")
    else:
        print(f"  {warn('[SKIP]')} Process detection via tasklist only available on Windows")

    # Test the tracker system
    reset_tracker()
    assert not was_launched("TestApp"), "Tracker should be empty after reset"
    print(f"\n  Tracker reset: {ok('OK')}")
    print(f"  Tracker empty: {ok('OK')}")


# -- Launch Test --------------------------------------------------------------

def launch_test():
    """Interactive launch testing -- asks before each launch."""
    from launcher import launch_exe, launch_exe_from_paths, launch_os_startfile, launch_uwp

    print(f"\n{bold(SEP)}")
    print(f"  {bold('Interactive Launch Test')}")
    print(f"{bold(SEP)}")
    print(f"\n  {warn('WARNING: This will actually launch programs on your system.')}")
    print(f"  Each launch will be confirmed before execution.\n")

    reset_tracker()

    # -- Test OBS specifically
    obs_path = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
    if os.path.exists(obs_path):
        if is_process_running("obs64.exe"):
            print(f"  {warn('[SKIP]')} OBS is already running -- will not launch again")
        else:
            response = input(f"  Launch OBS Studio? [y/N]: ").strip().lower()
            if response == "y":
                launch_exe(obs_path, "OBS Studio", exe_name="obs64.exe")
    else:
        print(f"  {fail('[SKIP]')} OBS path not found -- cannot test")

    # -- Test a game launcher
    for name in ["Steam", "Epic Games"]:
        paths = _GAME_LAUNCHERS.get(name, [])
        exe = _GAME_LAUNCHER_EXES.get(name)
        found = find_first_existing(paths)
        if found:
            if exe and is_process_running(exe):
                print(f"  {warn('[SKIP]')} {name} is already running ({exe})")
            else:
                response = input(f"  Launch {name}? [y/N]: ").strip().lower()
                if response == "y":
                    launch_exe_from_paths(paths, name, exe_name=exe)
        else:
            print(f"  {fail('[SKIP]')} {name} not found")

    # -- Test Sticky Notes (UWP)
    response = input(f"  Launch Sticky Notes (UWP)? [y/N]: ").strip().lower()
    if response == "y":
        launch_uwp("ms-sticky-notes:", "Sticky Notes")

    print(f"\n  {bold('Launch test complete.')}")


# -- Main ---------------------------------------------------------------------

def main():
    print(bold(EQ))
    print(bold("  LAUNCHER DIAGNOSTIC TOOL"))
    print(bold(EQ))

    # Check environment
    print(f"\n  Environment paths:")
    for key in ["PROGFILES", "PROGFILES_X86", "LOCALAPPDATA", "APPDATA", "USERPROFILE"]:
        val = ENV.get(key, "N/A")
        exists = "OK" if os.path.exists(val) else "MISS"
        print(f"    {key}: {val} [{exists}]")

    # Run all checks
    check_paths("Game Launchers", _GAME_LAUNCHERS, _GAME_LAUNCHER_EXES)
    check_obs_specifically()
    check_paths("Live & Recording Kit", _LIVE_KIT_APPS, _LIVE_KIT_EXES)
    test_process_detection()

    # Browser check (simple)
    print(f"\n{bold(SEP)}")
    print(f"  {bold('Web Browsers (quick check)')}")
    print(f"{bold(SEP)}")
    import shutil
    import platform
    system = platform.system()
    for name, execs in _BROWSER_EXECUTABLES.items():
        if system == "Windows":
            exe = execs["win"]
        elif system == "Darwin":
            exe = execs["darwin"]
        else:
            exe = execs["linux"]
        found = shutil.which(exe)
        if found:
            print(f"  {ok('[FOUND]')} {name} -> {found}")
        else:
            print(f"  {fail('[MISS]')} {name} ({exe} not in PATH)")

    # Launch test
    if "--launch" in sys.argv:
        launch_test()
    elif "--obs" in sys.argv:
        check_obs_specifically()
        if os.path.exists(r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"):
            if is_process_running("obs64.exe"):
                print(f"\n  {warn('OBS is already running -- no need to launch')}")
            else:
                response = input(f"\n  Launch OBS Studio? [y/N]: ").strip().lower()
                if response == "y":
                    from launcher import launch_exe
                    launch_exe(r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
                              "OBS Studio", exe_name="obs64.exe")

    print(f"\n{bold(EQ)}")
    print(f"  Diagnostic complete.")
    print(f"{bold(EQ)}")


if __name__ == "__main__":
    main()
