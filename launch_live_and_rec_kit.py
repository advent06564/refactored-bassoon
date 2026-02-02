import os
import subprocess

def launch_application(path):
    """Launches an application at the given path."""
    try:
        os.startfile(path)
        print(f"Successfully launched {os.path.basename(path)}")
    except FileNotFoundError:
        print(f"Error: Application not found at {path}")
    except Exception as e:
        print(f"An error occurred while launching {os.path.basename(path)}: {e}")

if __name__ == "__main__":
    applications = {
        "Steam": r"C:\Program Files (x86)\Steam\Steam.exe",
        "Warudo": r"E:\SteamLibrary\steamapps\common\Warudo\Warudo.exe",
        "OBS Studio": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        "OneNote": r"C:\Program Files\Microsoft Office\root\Office16\ONENOTE.EXE",
        "Sticky Notes": r"%LocalAppData%\Packages\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\LocalState\plum.sqlite",
        "Perplexity": r"C:\Users\typre\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Perplexity.lnk"
    }

    for name, path in applications.items():
        print(f"Launching {name}...")
        launch_application(path)

    print("\nAll launch commands have been sent.")
