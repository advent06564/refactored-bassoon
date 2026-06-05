"""Cross-platform site / URL launcher.

Opens every URL listed in config.json in browser tabs.
Supports Windows, macOS, Linux, and WSL environments.

Usage:
    python run_sites.py              # uses browser from config.json
    python run_sites.py chrome       # override browser
    python run_sites.py firefox
"""

import json
import os
import sys
import time
import webbrowser
import platform
import subprocess


# -- Config --

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: config.json not found at {CONFIG_FILE}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {CONFIG_FILE}.")
    sys.exit(1)

URLS = config.get("social_media_urls", [])
DEFAULT_BROWSER = config.get("default_browser", None)

if not URLS:
    print("Warning: No social_media_urls found in config.json.")
    sys.exit(0)


# -- Helpers --

def is_wsl() -> bool:
    """Detect whether we are running inside Windows Subsystem for Linux."""
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


# -- Main --

def main() -> None:
    print("
--- Cross-Platform Site Launcher ---")

    browser_name = DEFAULT_BROWSER
    if len(sys.argv) > 1:
        browser_name = sys.argv[1].lower()
        print(f"Browser specified: {browser_name.capitalize()}")
    else:
        print(f"No browser override.  Default: {browser_name or 'system default'}")

    in_wsl = is_wsl()
    if in_wsl:
        print("WSL detected -- using wsl-open to launch on Windows host.")

    controller = None
    if not in_wsl and browser_name:
        try:
            controller = webbrowser.get(browser_name)
        except webbrowser.Error:
            print(f"Warning: browser '{browser_name}' not found -- using system default.")

    delay = 1

    for url in URLS:
        print(f"   -> Opening: {url}")
        try:
            if in_wsl:
                subprocess.run(["wsl-open", url], check=True)
            elif controller:
                controller.open(url, new=2)
            else:
                webbrowser.open(url, new=2)
        except FileNotFoundError:
            print("Error: 'wsl-open' not found. Are you in WSL without wsl-open installed?")
            sys.exit(1)
        except Exception as e:
            print(f"Error opening {url}: {e}")

        time.sleep(delay)

    print("
Script finished. Tabs should be loading in your browser.")


if __name__ == "__main__":
    main()
