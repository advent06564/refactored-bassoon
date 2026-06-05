"""Standalone game launcher — delegates to the unified launcher module."""
from launcher import launch_game_launchers

if __name__ == "__main__":
    launch_game_launchers()
    print("\nAll launch commands have been sent.")
    input("Press Enter to exit.")
