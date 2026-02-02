import os
import subprocess
import shutil

def launch_docker_desktop():
    """Finds and launches Docker Desktop."""
    print("Starting Docker Desktop...")
    docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    if os.path.exists(docker_path):
        try:
            subprocess.Popen([docker_path])
            print("Docker Desktop launch command issued.")
        except Exception as e:
            print(f"An error occurred while starting Docker Desktop: {e}")
    else:
        print(f"Warning: Docker Desktop executable not found at '{docker_path}'")

def launch_wsl():
    """Finds and launches the Windows Subsystem for Linux (WSL)."""
    print("Starting WSL...")
    wsl_path = shutil.which("wsl.exe")

    if wsl_path:
        try:
            # Popen will open wsl.exe in a new window.
            subprocess.Popen([wsl_path])
            print("WSL launch command issued.")
        except Exception as e:
            print(f"An error occurred while starting WSL: {e}")
    else:
        print("Warning: wsl.exe not found in your system's PATH.")

if __name__ == "__main__":
    print("This script will launch Docker Desktop and WSL.\n")
    launch_docker_desktop()
    print("-" * 20)
    launch_wsl()
    print("\nAll launch commands have been sent. The applications may take a moment to open.")
    input("Press Enter to exit.")
