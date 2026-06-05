"""Standalone browser launcher — delegates to the unified launcher module."""
from launcher import launch_browsers

if __name__ == "__main__":
    launch_browsers()
    print("\nScript execution finished.")
    input("Press Enter to exit.")
