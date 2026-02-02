import os
import glob
import winreg
import ctypes

def is_admin():
    """Checks if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def remove_startup_shortcuts():
    """Removes shortcuts from user and common startup folders."""
    startup_folders = [
        os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup"),
        os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs\Startup")
    ]

    for folder in startup_folders:
        if os.path.exists(folder):
            print(f"Cleaning startup folder: {folder}")
            files = glob.glob(os.path.join(folder, "*"))
            for f in files:
                try:
                    os.remove(f)
                    print(f"  Removed: {os.path.basename(f)}")
                except Exception as e:
                    print(f"  Error removing {os.path.basename(f)}: {e}")
        else:
            print(f"Startup folder not found: {folder}")

def clear_startup_registry_hives():
    """Clears startup program entries from the registry."""
    if not is_admin():
        print("\nWARNING: Not running as administrator.")
        print("Skipping modification of HKEY_LOCAL_MACHINE registry hives.")
        hives_to_clear = {
            "HKEY_CURRENT_USER": [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]
        }
    else:
        print("\nRunning as administrator. All targeted registry hives will be processed.")
        hives_to_clear = {
            "HKEY_CURRENT_USER": [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ],
            "HKEY_LOCAL_MACHINE": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Run"),
            ]
        }
    
    for hive_name, paths in hives_to_clear.items():
        for root, path in paths:
            print(f"\nProcessing Registry Path: {hive_name}\\{path}")
            try:
                with winreg.OpenKey(root, path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                    values_to_delete = []
                    i = 0
                    while True:
                        try:
                            value_name, _, _ = winreg.EnumValue(key, i)
                            values_to_delete.append(value_name)
                            i += 1
                        except OSError:
                            break # No more values
                    
                    if not values_to_delete:
                        print("  No startup entries found.")
                        continue

                    for value_name in values_to_delete:
                        try:
                            winreg.DeleteValue(key, value_name)
                            print(f"  Removed registry entry: {value_name}")
                        except Exception as e:
                            print(f"  Error removing registry entry '{value_name}': {e}")
            except FileNotFoundError:
                print("  Registry key not found.")
            except Exception as e:
                print(f"  An error occurred: {e}")


if __name__ == "__main__":
    print("This script will remove startup programs.\n")
    print("="*40)
    
    remove_startup_shortcuts()
    
    print("\n" + "="*40 + "\n")
    
    clear_startup_registry_hives()

    print("\n" + "="*40)
    print("Startup cleaning process finished.")
    input("Press Enter to exit.")
