import os
import subprocess

def launch_game_launchers():
    """
    This script launches all common game launchers installed on the system.
    It checks for the existence of each launcher's executable before attempting to launch it.
    """
    launchers = {
        "Steam": r"C:\Program Files (x86)\Steam\Steam.exe",
        "Epic Games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        "GOG Galaxy": r"C:\Program Files (x86)\GOG Galaxy\GalaxyClient.exe",
        "Battle.net": r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe",
        "EA Desktop": r"C:\Program Files\Electronic Arts\EA Desktop\EA Desktop\EADesktop.exe",
        "Ubisoft Connect": r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\UbisoftConnect.exe",
        "Amazon Games": os.path.join(os.environ["LOCALAPPDATA"], r"Amazon Games\App\Amazon Games.exe")
    }

    print("Attempting to launch game launchers...")
    for name, path in launchers.items():
        if os.path.exists(path):
            try:
                subprocess.Popen([path])
                print(f"  Launched: {name}")
            except Exception as e:
                print(f"  Error launching {name}: {e}")
        else:
            print(f"  Not found: {name} (path: {path})")

if __name__ == "__main__":
    launch_game_launchers()
    print("\nAll launch commands have been sent.")
    input("Press Enter to exit.")
