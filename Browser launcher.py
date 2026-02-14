import os
import subprocess
import platform
import shutil

# A list of common browsers with their executable names for different OSes.
browsers = {
    "Chrome": {"win": "chrome.exe", "darwin": "Google Chrome", "linux": "google-chrome"},
    "Firefox": {"win": "firefox.exe", "darwin": "Firefox", "linux": "firefox"},
    "Edge": {"win": "msedge.exe", "darwin": "Microsoft Edge", "linux": "microsoft-edge"},
    "Brave": {"win": "brave.exe", "darwin": "Brave Browser", "linux": "brave-browser"},
    "Opera": {"win": "launcher.exe", "darwin": "Opera", "linux": "opera"},
    "Cursor": {"win": "Cursor.exe", "darwin": "Cursor", "linux": "cursor"},
}

def open_browser(browser_name, browser_execs):
    """
    Attempts to open a browser by finding its executable in the system's PATH
    or common installation locations.
    """
    system = platform.system()
    executable = ""
    if system == "Windows":
        executable = browser_execs["win"]
        # Special case for Opera on windows
        if browser_name == "Opera":
            # Opera's launcher is usually in a path like: C:\Users\user\AppData\Local\Programs\Opera\launcher.exe
            opera_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Programs', 'Opera', executable)
            if os.path.exists(opera_path):
                try:
                    subprocess.Popen(opera_path)
                    print(f"Successfully opened {browser_name}.")
                    return
                except Exception as e:
                    print(f"An error occurred while trying to open {browser_name}: {e}")
                    return

        # Special case for Cursor on windows
        if browser_name == "Cursor":
            cursor_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Programs', 'cursor', 'Cursor.exe')
            if os.path.exists(cursor_path):
                try:
                    subprocess.Popen(cursor_path)
                    print(f"Successfully opened {browser_name}.")
                    return
                except Exception as e:
                    print(f"An error occurred while trying to open {browser_name}: {e}")
                    return
        
    elif system == "Darwin":
        executable = browser_execs["darwin"]
    else:
        executable = browser_execs["linux"]

    # Use shutil.which to find the executable in the system's PATH
    if shutil.which(executable):
        try:
            if system == "Windows":
                # The 'start' command helps to launch the browser correctly.
                subprocess.Popen(['start', executable], shell=True)
            elif system == "Darwin":
                subprocess.Popen(['open', '-a', executable])
            else:
                subprocess.Popen([executable])
            print(f"Successfully opened {browser_name}.")
        except Exception as e:
            print(f"An error occurred while trying to open {browser_name}: {e}")
    else:
        print(f"Could not find {browser_name}. Please ensure it is installed and in your system's PATH.")


def main():
    """
    Main function to iterate through the browsers and open them.
    """
    print("Attempting to open the following major web browsers:")
    for browser, executables in browsers.items():
        print(f"\n- {browser}")
        open_browser(browser, executables)
    
    print("\nScript execution finished.")
    input("Press Enter to exit.")


if __name__ == "__main__":
    main()
