"""Programmatic test harness for the launcher menu.

Runs the launcher with simulated menu inputs and captures all output.
Safer than tmux and works on Windows.
"""

import subprocess
import sys
import os
import time

LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))

def run_launcher_with_inputs(inputs: list[str], timeout: float = 30) -> str:
    """Run launcher.py with simulated menu inputs and return captured output.

    Args:
        inputs: List of strings to feed as stdin (e.g., ["1", "", "3", "", "0"]).
                Each "" represents pressing Enter.
        timeout: Maximum seconds to wait for the process.
    """
    input_str = "\n".join(inputs) + "\n"
    
    try:
        result = subprocess.run(
            [sys.executable, "launcher.py"],
            input=input_str,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=LAUNCHER_DIR,
        )
        return result.stdout + "\n--- STDERR ---\n" + result.stderr
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Launcher did not complete within timeout."
    except Exception as e:
        return f"[ERROR] {e}"


def main():
    print("=" * 70)
    print("  LAUNCHER MENU TEST HARNESS")
    print("=" * 70)
    
    # Test 1: Just show the menu and exit
    print("\n--- Test 1: Menu display and exit ---")
    output = run_launcher_with_inputs(["0"], timeout=10)
    print(output)
    
    # Test 2: Launch game launchers (option 1), then exit
    print("\n" + "=" * 70)
    print("--- Test 2: Game Launchers (option 1) ---")
    print("=" * 70)
    output = run_launcher_with_inputs(["1", "", "0"], timeout=30)
    print(output)
    
    # Test 3: Live & Recording Kit (option 3), then exit
    print("\n" + "=" * 70)
    print("--- Test 3: Live & Recording Kit (option 3) ---")
    print("=" * 70)
    output = run_launcher_with_inputs(["3", "", "0"], timeout=30)
    print(output)
    
    # Test 4: Launch ALL (option 4), then exit
    print("\n" + "=" * 70)
    print("--- Test 4: Launch ALL (option 4) ---")
    print("=" * 70)
    output = run_launcher_with_inputs(["4", "", "0"], timeout=45)
    print(output)


if __name__ == "__main__":
    main()
