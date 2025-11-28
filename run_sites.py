import sys
import json
import os
import time
import subprocess

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

if not SOCIAL_MEDIA_URLS:
    print("Warning: No social media URLs found in config.json.")
    sys.exit(0)

# --- Script Logic ---
print("\n--- Opening Social Media Management Sites on Windows Host ---")
DELAY_SECONDS = 1 # Increased delay slightly for Windows to process

for url in SOCIAL_MEDIA_URLS:
    print(f"   -> Opening: {url}")
    try:
        # Use wsl-open to open the URL in the default Windows browser
        subprocess.run(['wsl-open', url], check=True)
    except FileNotFoundError:
        print("Error: 'wsl-open' command not found. Please ensure you are running this script within a WSL environment and that 'wsl-open' is in your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error opening {url}: {e}")
    
    time.sleep(DELAY_SECONDS)

print("\n??? Script finished. All tabs should be loading in your default Windows browser.")

