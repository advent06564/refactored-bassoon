"""Standalone VM launcher — delegates to the unified launcher module."""
from launcher import launch_vm_system

if __name__ == "__main__":
    launch_vm_system()
    print("\nAll launch commands have been sent.")
    input("Press Enter to exit.")
