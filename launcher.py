"""Unified Launcher — single entry point for all system launchers.

Launches game launchers, browsers, live-kit apps, and VM systems
without double-opening any program.
"""

import os
import platform
import shutil
import subprocess

import utils as _u
from utils import (
    find_first_existing,
    launch_exe,
    launch_exe_from_paths,
    launch_os_startfile,
    launch_uwp,
    reset_tracker,
    was_launched,
    ENV,
    is_windows,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Game Launchers
# ═══════════════════════════════════════════════════════════════════════════════

_GAME_LAUNCHERS: dict[str, list[str]] = {
    "Steam": [r"C:\Program Files (x86)\Steam\Steam.exe"],
    "Epic Games": [
        r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
        r"C:\Program Files\Epic Games\Launcher\Engine\Binaries\Win64\EpicGamesLauncher.exe",
        os.path.join(ENV["LOCALAPPDATA"], r"Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"),
    ],
    "GOG Galaxy": [r"C:\Program Files (x86)\GOG Galaxy\GalaxyClient.exe"],
    "Battle.net": [r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe"],
    "EA Desktop": [
        r"C:\Program Files\Electronic Arts\EA Desktop\EA Desktop\EADesktop.exe",
        r"C:\Program Files (x86)\Electronic Arts\EA Desktop\EA Desktop\EADesktop.exe",
        os.path.join(ENV["LOCALAPPDATA"], r"Electronic Arts\EA Desktop\EA Desktop\EADesktop.exe"),
    ],
    "Ubisoft Connect": [r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\UbisoftConnect.exe"],
    "Amazon Games": [os.path.join(ENV["LOCALAPPDATA"], r"Amazon Games\App\Amazon Games.exe")],
    "Xbox Game Pass": [
        os.path.join(ENV["LOCALAPPDATA"], r"Microsoft\WindowsApps\GamingApp.exe"),
        os.path.join(ENV["LOCALAPPDATA"], r"Microsoft\WindowsApps\XboxApp.exe"),
    ],
    "itch.io": [
        os.path.join(ENV["LOCALAPPDATA"], r"itch\itch.exe"),
        os.path.join(ENV["APPDATA"], r"itch\itch.exe"),
        os.path.join(ENV["LOCALAPPDATA"], r"Programs\itch\itch.exe"),
    ],
    "PlayStation PC": [
        r"C:\Program Files (x86)\PS Remote Play\RemotePlay.exe",
        r"C:\Program Files\PS Remote Play\RemotePlay.exe",
        os.path.join(ENV["LOCALAPPDATA"], r"Programs\PlayStationPlus\PlayStationPlus.exe"),
    ],
}


def launch_game_launchers() -> None:
    """Launch all installed game launchers.  Skips any already launched."""
    print("\n--- Game Launchers ---")
    found_any = False
    for name, paths in _GAME_LAUNCHERS.items():
        if launch_exe_from_paths(paths, name):
            found_any = True
    if not found_any:
        print("  No game launchers found.")


# ═══════════════════════════════════════════════════════════════════════════════
# Web Browsers
# ═══════════════════════════════════════════════════════════════════════════════

_BROWSER_EXECUTABLES: dict[str, dict[str, str]] = {
    "Chrome":  {"win": "chrome.exe",    "darwin": "Google Chrome",        "linux": "google-chrome"},
    "Firefox": {"win": "firefox.exe",   "darwin": "Firefox",              "linux": "firefox"},
    "Edge":    {"win": "msedge.exe",    "darwin": "Microsoft Edge",       "linux": "microsoft-edge"},
    "Brave":   {"win": "brave.exe",     "darwin": "Brave Browser",        "linux": "brave-browser"},
    "Opera":   {"win": "launcher.exe",  "darwin": "Opera",                "linux": "opera"},
    "Cursor":  {"win": "Cursor.exe",    "darwin": "Cursor",               "linux": "cursor"},
}


def _browser_fallback_paths(browser_name: str) -> list[str]:
    """Return fallback installation paths for a browser on Windows."""
    pf = ENV["PROGFILES"]
    pfx = ENV["PROGFILES_X86"]
    local = ENV["LOCALAPPDATA"]
    user = ENV["USERPROFILE"]

    return {
        "Chrome": [
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pfx, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
        ],
        "Firefox": [
            os.path.join(pf, "Mozilla Firefox", "firefox.exe"),
            os.path.join(pfx, "Mozilla Firefox", "firefox.exe"),
            os.path.join(local, "Mozilla Firefox", "firefox.exe"),
        ],
        "Edge": [
            os.path.join(pfx, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(local, "Microsoft", "Edge", "Application", "msedge.exe"),
        ],
        "Brave": [
            os.path.join(pf, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(pfx, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(local, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        ],
        "Opera": [
            os.path.join(user, "AppData", "Local", "Programs", "Opera", "launcher.exe"),
            os.path.join(local, "Programs", "Opera", "launcher.exe"),
            os.path.join(pf, "Opera", "launcher.exe"),
            os.path.join(pfx, "Opera", "launcher.exe"),
        ],
        "Cursor": [
            os.path.join(user, "AppData", "Local", "Programs", "cursor", "Cursor.exe"),
            os.path.join(local, "Programs", "cursor", "Cursor.exe"),
            os.path.join(local, "cursor", "Cursor.exe"),
        ],
    }.get(browser_name, [])


def _launch_macos_app(app_name: str, display_name: str) -> bool:
    """Launch a macOS application by name, respecting the launch tracker."""
    if was_launched(display_name):
        print(f"  [SKIP] Already launched: {display_name}")
        return True
    try:
        subprocess.Popen(["open", "-a", app_name])
        print(f"  [OK] Launched: {display_name}")
        _u._tracker.mark_launched(display_name)
        return True
    except Exception as e:
        print(f"  [FAIL] Error launching {display_name}: {e}")
        return False


def launch_browsers() -> None:
    """Launch all installed web browsers."""
    system = platform.system()
    print("\n--- Web Browsers ---")
    found_any = False

    for name, execs in _BROWSER_EXECUTABLES.items():
        launched = False

        if system == "Windows":
            exe = execs["win"]
        elif system == "Darwin":
            exe = execs["darwin"]
        else:
            exe = execs["linux"]

        if system == "Windows" and exe != "launcher.exe":
            found = shutil.which(exe)
            if found is not None:
                launched = launch_exe(found, name)
        elif system != "Windows":
            found = shutil.which(exe)
            if found is not None:
                if system == "Darwin":
                    launched = _launch_macos_app(exe, name)
                else:
                    launched = launch_exe(found, name)

        # Fallback paths (Windows only)
        if not launched and system == "Windows":
            for path in _browser_fallback_paths(name):
                if os.path.exists(path):
                    launched = launch_exe(path, name)
                    break

        if launched:
            found_any = True
        else:
            print(f"  - Not found: {name}")

    if not found_any:
        print("  No browsers found.")


# ═══════════════════════════════════════════════════════════════════════════════
# Live & Recording Kit
# ═══════════════════════════════════════════════════════════════════════════════

_LIVE_KIT_APPS: dict[str, str] = {
    "Warudo": r"E:\SteamLibrary\steamapps\common\Warudo\Warudo.exe",
    "OBS Studio": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "OneNote": r"C:\Program Files\Microsoft Office\root\Office16\ONENOTE.EXE",
    "Perplexity": os.path.join(ENV["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Perplexity.lnk"),
}


def launch_live_kit() -> None:
    """Launch live-streaming & recording apps.

    NOTE: Steam is intentionally NOT launched here — it is handled by
    launch_game_launchers() to prevent double-opening.
    """
    print("\n--- Live & Recording Kit ---")
    found_any = False

    for name, path in _LIVE_KIT_APPS.items():
        if launch_os_startfile(path, name):
            found_any = True

    if launch_uwp("ms-sticky-notes:", "Sticky Notes"):
        found_any = True

    if not found_any:
        print("  No live kit apps found.")


# ═══════════════════════════════════════════════════════════════════════════════
# VM System
# ═══════════════════════════════════════════════════════════════════════════════

def launch_vm_system() -> None:
    """Launch Docker Desktop and WSL."""
    print("\n--- VM System ---")

    # ── Docker Desktop ──
    docker_paths = [
        os.path.join(ENV["PROGFILES"], "Docker", "Docker", "Docker Desktop.exe"),
        os.path.join(ENV["PROGFILES_X86"], "Docker", "Docker", "Docker Desktop.exe"),
        os.path.join(ENV["LOCALAPPDATA"], "Programs", "DockerDesktop", "Docker Desktop.exe"),
        os.path.join(ENV["LOCALAPPDATA"], "DockerDesktop", "Docker Desktop.exe"),
    ]
    docker_ok = launch_exe_from_paths(docker_paths, "Docker Desktop")

    # ── WSL ──
    wsl_ok = False
    wsl_path = shutil.which("wsl.exe")
    if wsl_path:
        wsl_ok = launch_exe(wsl_path, "WSL")
    else:
        print("  [FAIL] wsl.exe not found in PATH.")

    if not docker_ok and not wsl_ok:
        print("  No VM systems found.")


# ═══════════════════════════════════════════════════════════════════════════════
# Launch All
# ═══════════════════════════════════════════════════════════════════════════════

def launch_all() -> None:
    """Launch all categories, with cross-category de-duplication."""
    reset_tracker()
    launch_game_launchers()
    launch_browsers()
    launch_live_kit()
    launch_vm_system()


# ═══════════════════════════════════════════════════════════════════════════════
# Menu System
# ═══════════════════════════════════════════════════════════════════════════════

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_header() -> None:
    print("=" * 56)
    print("          UNIFIED LAUNCHER")
    print("=" * 56)
    print("  Game Launchers | Browsers | Live Kit | VM System")
    print("=" * 56)


def print_menu() -> None:
    print()
    print("  [1] Game Launchers (Steam, Epic, GOG, Battle.net, EA, Ubisoft, Amazon, Xbox, itch, PlayStation)")
    print()
    print("  [2] Web Browsers (Chrome, Firefox, Edge, Brave, Opera, Cursor)")
    print()
    print("  [3] Live & Recording Kit (Warudo, OBS, OneNote, Sticky Notes, Perplexity)")
    print()
    print("  [4] Launch ALL")
    print()
    print("  [5] VM System (Docker Desktop, WSL)")
    print()
    print("  [0] Exit")
    print()
    print("-" * 56)


def main() -> None:
    """Interactive menu loop."""
    while True:
        clear_screen()
        print_header()
        print_menu()
        choice = input("  Enter your choice [0-5]: ").strip()
        clear_screen()
        print_header()

        reset_tracker()

        if choice == "1":
            launch_game_launchers()
        elif choice == "2":
            launch_browsers()
        elif choice == "3":
            launch_live_kit()
        elif choice == "4":
            launch_all()
        elif choice == "5":
            launch_vm_system()
        elif choice == "0":
            print("\n  Goodbye!\n")
            break
        else:
            print("\n  Invalid choice. Please enter 0-5.")

        print("\n" + "-" * 56)
        input("\n  Press Enter to return to the menu...")


if __name__ == "__main__":
    main()
