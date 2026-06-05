"""Standalone live-kit launcher — delegates to the unified launcher module."""
from launcher import launch_live_kit

if __name__ == "__main__":
    launch_live_kit()
    print("\nAll launch commands have been sent.")
    input("Press Enter to exit.")
