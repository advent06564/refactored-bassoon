import webbrowser
import time
import sys
import json
import os

# --- Configuration Loading ---
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# Load configuration from config.json
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: config.json not found at {CONFIG_FILE}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {CONFIG_FILE}. Check file format.")
    sys.exit(1)

# Get URLs and default browser from config
SOCIAL_MEDIA_URLS = config.get("social_media_urls", [])
DEFAULT_BROWSER = config.get("default_browser", "opera") # Default to 'opera' if not in config

if not SOCIAL_MEDIA_URLS:
    print("Warning: No social media URLs found in config.json.")

# --- Script Logic ---

# 1. Determine the browser to use based on command line arguments.
# If no argument is provided, default to the one specified in config.json.

# Available browser types for the webbrowser module:
# "opera", "chrome", "firefox", "safari", "google-chrome", None (for default system browser)

BROWSER_NAME = DEFAULT_BROWSER # Initialize with default from config

# Check if a browser name was passed as an argument (e.g., python script.py chrome)
if len(sys.argv) > 1:                    
    BROWSER_NAME = sys.argv[1].lower()   
    print(f"Browser specified in command line: {BROWSER_NAME.capitalize()}")      
else:                                    
    print(f"No browser specified. Defaulting to: {DEFAULT_BROWSER.capitalize()}") 
                                         
                                         
# 2. Get the browser controller and handle potential errors
browser_controller = webbrowser          
                                         
if BROWSER_NAME:                         
    try:                                 
        # Get the controller for the specified browser
        browser_controller = webbrowser.get(BROWSER_NAME)                         
        print(f"Successfully configured to use: {BROWSER_NAME.capitalize()}")     
    except webbrowser.Error:
        print(f"⚠️ Warning: Could not find or use browser '{BROWSER_NAME}'. Falling back to default system browser.")      
        browser_controller = webbrowser  
                                         
                                         
# 3. Loop through the list of URLs and open each one in a new tab.                          
print("--- Opening Social Media Management Sites ---")                          
DELAY_SECONDS = 0.5 # Small delay to prevent loading issues                       
                                         
for url in SOCIAL_MEDIA_URLS:            
    print(f"   -> Opening: {url}")       
    # The 'new=2' argument tells the browser to open the URL in a new tab/window
    browser_controller.open(url, new=2)  
                                         
    # Wait briefly before opening the next one
    time.sleep(DELAY_SECONDS)            
                                         
print("✅ Script finished. All tabs should be loading in your specified browser.")
