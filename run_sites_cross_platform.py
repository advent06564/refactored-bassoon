import sys
import json
import os
import time
import subprocess
import platform
import webbrowser # <-- ADDED IMPORT

# --- Helper Function to Detect WSL ---
def is_wsl():
    """
    Checks if the script is running inside Windows Subsystem for Linux (WSL).
    """
    return 'microsoft' in platform.release().lower() or 'wsl' in platform.release().lower()

# --- Configuration Loading ---
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: config.json not found at {CONFIG_FILE}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {CONFIG_FILE}. Check file format.")
    sys.exit(1)

SOCIAL_MEDIA_URLS = config.get("social_media_urls", [])
DEFAULT_BROWSER = config.get("default_browser", None)

if not SOCIAL_MEDIA_URLS:
    print("Warning: No social media URLs found in config.json.")
    sys.exit(0)

# --- Script Logic ---
print("\n--- Cross-Platform Site Launcher ---")

BROWSER_NAME = DEFAULT_BROWSER
if len(sys.argv) > 1:
    BROWSER_NAME = sys.argv[1].lower()
    print(f"Browser specified in command line: {BROWSER_NAME.capitalize()}")
else:
    print(f"No browser specified. Using system default.")

IN_WSL = is_wsl()
DELAY_SECONDS = 1

if IN_WSL:
    print("WSL environment detected. Using 'wsl-open' to launch URLs on Windows host.")
else:
    print("Standard environment (Windows/macOS/Linux Desktop) detected.")

browser_controller = None
if not IN_WSL and BROWSER_NAME:
    try:
        browser_controller = webbrowser.get(BROWSER_NAME)
        print(f"Attempting to use specified browser: {BROWSER_NAME.capitalize()}")
    except webbrowser.Error:
        print(f"?????? Warning: Could not find browser '{BROWSER_NAME}'. Falling back to system default.")

for url in SOCIAL_MEDIA_URLS:
    print(f"   -> Opening: {url}")
    try:
        if IN_WSL:
            subprocess.run(['wsl-open', url], check=True)
        else:
            if browser_controller:
                browser_controller.open(url, new=2)
            else:
                webbrowser.open(url, new=2)

    except FileNotFoundError:
        print("Error: 'wsl-open' command not found. This script seems to be in a WSL environment without wsl-open.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred opening {url}: {e}")
    
    time.sleep(DELAY_SECONDS)

print("\n??? Script finished. All tabs should be loading.")

