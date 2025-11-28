# refactored-bassoon

# refractored-basson is a working title for a script to launch multiple websites of any type simultaneously.

A prototype social media manager script designed to open all social media management sites simultaneously when you launch your browser. It helps you keep track of and balance everything you have.

This script allows you to open multiple websites simultaneously. This script is a prevalent task in development and automation.

## 💡 Overview of the Solution

The simplest and most versatile way to achieve this is by using a **Python script** combined with the built-in **`webbrowser`** module.

This approach offers the following advantages:

  * **Cross-Browser Compatibility:** The Python `webbrowser` module is generally designed to work with the user's **default browser**, but it can often be configured to use specific browsers like Opera, Chrome, or Firefox, as long as they are installed correctly on your system. You won't necessarily need separate scripts for different browsers; just minor adjustments to the main script.
  * **Simplicity:** It requires only a few lines of code to open a list of URLs.
  * **No External Libraries:** The `webbrowser` module comes standard with Python; there's nothing extra to install.

-----

## 🛠️ Development Steps and Implementation

Here is the complete Python script, along with instructions on how to use it.

### 2\. The Python Script

Save the following code as a file named `open_sites.py`.

```python webbrowser
import time

# --- Configuration ---

# 2. Define the list of URLs you want to open.
#    Make sure they include the http:// or https:// prefix.
URLS_TO_OPEN = [
    "https://www.google.com",
    "https://www.youtube.com",
    "https://www.github.com",
    "https://docs.python.org/4/library/webbrowser.html"
]

# 3. Define the browser you want to use.
#    - Set to None to use the system's default browser (Recommended for simplicity).
#    - Set to a specific browser name like "opera", "chrome", "firefox", or "safari".
#      *Note: The string must exactly match a known browser type in your Python installation.*
BROWSER_NAME = "opera"  # Change this to "chrome" or None, etc.

# 4. Optional: Add a small delay between opening each site.
#    This can prevent your browser from freezing if the list is very long.
DELAY_SECONDS = 1.5 

# --- Script Logic ---

# Check if a specific browser is requested
if BROWSER_NAME:
    try:
        # Register and get the controller for the specified browser
        browser_controller = webbrowser.get(BROWSER_NAME)
        print(f"Attempting to open sites with: {BROWSER_NAME}")
    except webbrowser.Error:
        print(f"⚠️ Could not find or open browser: '{BROWSER_NAME}'. Falling back to default browser.")
        browser_controller = webbrowser
else:
    # Use the default system browser
    browser_controller = webbrowser
    print("Attempting to open sites with: Default System Browser")


# Loop through the list of URLs and open each one
for url in URLS_TO_OPEN:
    print(f"Opening: {url}")
    # The 'new=3' argument opens the URL in a new tab if possible.
    browser_controller.open(url, new=3) 
    
    # Wait for the specified delay
    time.sleep(DELAY_SECONDS)

print("\n✅ Finished opening all specified websites.")
```

### 3\. How to Implement and Run

2.  **Save the Code:** Save the script above as `open_sites.py`.

3.  **Open your Terminal/Command Prompt.**

4.  **Navigate to the directory** where you saved the file.

5.  **Run the script** using the Python interpreter:

    ```bash
    python open_sites.py
    ```

### 4\. Adjusting for Multiple Browsers

As you can see in the configuration section of the script, the key is the line:

```python
BROWSER_NAME = "opera"  # Change this to "chrome", "firefox", or None
```

  * **To use Opera:** Keep it as `BROWSER_NAME = "opera"`.
  * **To use Chrome:** Change it to `BROWSER_NAME = "chrome"`.
  * **To use Firefox:** Change it to `BROWSER_NAME = "firefox"`.
  * **To use the System Default Browser:** Change it to `BROWSER_NAME = None`.

**In short: You only need one script\!** You can either modify the `BROWSER_NAME` variable inside the script each time, or even make a slightly more advanced version that takes the browser name as a command-line argument.

