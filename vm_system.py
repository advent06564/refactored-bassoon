import subprocess
import threading
import os
import platform

def start_docker():
    """Starts Docker Desktop."""
    print("Attempting to start Docker Desktop...")
    try:
        if platform.system() == "Windows":
            docker_path = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Docker", "Docker", "Docker Desktop.exe")
            if os.path.exists(docker_path):
                subprocess.Popen([docker_path])
                print("Docker Desktop launch command issued.")
            else:
                print(f"Error: Docker Desktop executable not found at '{docker_path}'.")
        elif platform.system() == "Darwin": # macOS
            docker_path = "/Applications/Docker.app"
            if os.path.exists(docker_path):
                subprocess.Popen(["open", docker_path])
                print("Docker Desktop launch command issued.")
            else:
                print(f"Error: Docker application not found at '{docker_path}'.")
        else: # Linux
            subprocess.Popen(["systemctl", "--user", "start", "docker-desktop"])
            print("Docker Desktop launch command issued.")

    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error starting Docker Desktop: {e}")

def start_wsl():
    """Starts the Windows Subsystem for Linux terminal."""
    print("Attempting to start WSL...")
    if platform.system() == "Windows":
        try:
            # Starts WSL in a new terminal window
            subprocess.Popen(["cmd.exe", "/c", "start", "wsl.exe"])
            print("WSL launch command issued.")
        except (OSError, subprocess.SubprocessError) as e:
            print(f"Error starting WSL: {e}")
    else:
        print("WSL is only available on Windows.")

if __name__ == "__main__":
    print("Launching virtualization systems...")

    # Create threads for concurrent execution
    threads = []
    if platform.system() == "Windows":
        threads.append(threading.Thread(target=start_wsl))
    
    docker_thread = threading.Thread(target=start_docker)
    threads.append(docker_thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All launch commands have been sent. The applications may take a moment to open.")
