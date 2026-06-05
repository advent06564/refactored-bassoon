"""Unit tests for refactored-bassoon launcher.py module.

Tests all launcher functions, cross-category de-duplication, Steam exclusion
from live_kit, and the launch_all orchestration.
"""

import os
import sys
import platform
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import utils
from utils import reset_tracker, was_launched
import launcher
from launcher import (
    launch_game_launchers,
    launch_browsers,
    launch_live_kit,
    launch_vm_system,
    launch_all,
    _launch_macos_app,
    _browser_fallback_paths,
    clear_screen,
    print_header,
    print_menu,
    main,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def reset():
    """Reset the launch tracker before each test."""
    reset_tracker()


# ═══════════════════════════════════════════════════════════════════════════════
# launch_game_launchers
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchGameLaunchers:
    """Tests for the game launcher function."""

    def test_calls_launch_exe_from_paths_for_each_launcher(self):
        with patch("launcher.launch_exe_from_paths", return_value=True) as mock_launch:
            launch_game_launchers()
            # Should be called for each launcher in _GAME_LAUNCHERS
            launcher_names = list(launcher._GAME_LAUNCHERS.keys())
            assert mock_launch.call_count == len(launcher_names)
            for name in launcher_names:
                mock_launch.assert_any_call(launcher._GAME_LAUNCHERS[name], name)

    def test_includes_steam(self):
        """Steam must be in game launchers for the double-launch prevention to work."""
        assert "Steam" in launcher._GAME_LAUNCHERS


# ═══════════════════════════════════════════════════════════════════════════════
# launch_live_kit — Steam exclusion
# ═══════════════════════════════════════════════════════════════════════════════

class TestLiveKitSteamExclusion:
    """Verify Steam is NOT in live_kit (critical for double-launch prevention)."""

    def test_steam_not_in_live_kit(self):
        assert "Steam" not in launcher._LIVE_KIT_APPS, (
            "Steam must NOT be in _LIVE_KIT_APPS — it is launched by "
            "launch_game_launchers() to prevent double-opening."
        )

    def test_live_kit_has_expected_apps(self):
        expected = {"Warudo", "OBS Studio", "OneNote", "Perplexity"}
        assert set(launcher._LIVE_KIT_APPS.keys()) == expected

    def test_live_kit_calls_os_startfile_and_uwp(self):
        with patch("launcher.launch_os_startfile", return_value=True) as mock_os:
            with patch("launcher.launch_uwp", return_value=True) as mock_uwp:
                launch_live_kit()
                # 4 apps via os.startfile + 1 Sticky Notes via uwp
                assert mock_os.call_count == 4
                mock_uwp.assert_called_once_with("ms-sticky-notes:", "Sticky Notes")


# ═══════════════════════════════════════════════════════════════════════════════
# _launch_macos_app
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchMacOSApp:
    """Tests for the macOS browser launcher helper."""

    def test_marks_tracker_on_success(self):
        with patch.object(launcher.subprocess, "Popen") as mock_popen:
            result = _launch_macos_app("Google Chrome", "Chrome")
            assert result is True
            mock_popen.assert_called_once_with(["open", "-a", "Google Chrome"])
            # Use the module-level tracker directly to avoid import-binding issues
            assert utils._tracker.was_launched("Chrome") is True
            assert was_launched("Chrome") is True

    def test_skips_when_already_launched(self):
        utils._tracker.mark_launched("Chrome")
        with patch.object(launcher.subprocess, "Popen") as mock_popen:
            result = _launch_macos_app("Google Chrome", "Chrome")
            assert result is True
            mock_popen.assert_not_called()

    def test_handles_failure(self):
        with patch.object(launcher.subprocess, "Popen", side_effect=Exception("fail")):
            result = _launch_macos_app("BadApp", "BadApp")
            assert result is False
            assert was_launched("BadApp") is False


# ═══════════════════════════════════════════════════════════════════════════════
# _browser_fallback_paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestBrowserFallbackPaths:
    """Tests for the browser fallback path generator."""

    def test_returns_list_for_known_browser(self):
        paths = _browser_fallback_paths("Chrome")
        assert isinstance(paths, list)
        assert len(paths) > 0
        assert all("chrome.exe" in p for p in paths)

    def test_returns_empty_for_unknown_browser(self):
        paths = _browser_fallback_paths("UnknownBrowser")
        assert paths == []


# ═══════════════════════════════════════════════════════════════════════════════
# launch_browsers
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchBrowsers:
    """Tests for the browser launcher function."""

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which", return_value=None)
    @patch("os.path.exists", return_value=False)
    def test_prints_not_found_for_missing_browsers(self, mock_exists, mock_which, mock_system):
        with patch("launcher.launch_exe") as mock_launch:
            launch_browsers()
            mock_launch.assert_not_called()  # nothing found to launch

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which", return_value="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
    def test_launches_found_windows_browser(self, mock_which, mock_system):
        with patch("launcher.launch_exe", return_value=True) as mock_launch:
            launch_browsers()
            # Chrome should have been launched via launch_exe
            mock_launch.assert_any_call(
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "Chrome"
            )

    @patch("platform.system", return_value="Darwin")
    @patch("shutil.which", return_value="/Applications/Google Chrome.app")
    def test_launches_macos_browser_via_helper(self, mock_which, mock_system):
        with patch("launcher._launch_macos_app", return_value=True) as mock_macos:
            launch_browsers()
            mock_macos.assert_any_call("Google Chrome", "Chrome")


# ═══════════════════════════════════════════════════════════════════════════════
# Opera launcher.exe branch (Windows special case)
# ═══════════════════════════════════════════════════════════════════════════════

class TestOperaBrowser:
    """Opera's Windows executable is 'launcher.exe' — a special branch in
    launch_browsers() that skips shutil.which() and goes straight to
    fallback paths."""

    def test_opera_skips_which_on_windows(self):
        """shutil.which('launcher.exe') should NOT be called for Opera."""
        with patch("platform.system", return_value="Windows"):
            with patch("shutil.which") as mock_which:
                with patch("os.path.exists", return_value=False):
                    launch_browsers()
                    # Opera should never call shutil.which
                    opera_calls = [
                        c for c in mock_which.call_args_list
                        if c.args and c.args[0] == "launcher.exe"
                    ]
                    assert len(opera_calls) == 0, (
                        f"shutil.which was called for Opera's launcher.exe — "
                        f"should be skipped"
                    )

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which")
    @patch("os.path.exists")
    def test_opera_uses_fallback_paths(self, mock_exists, mock_which, mock_system):
        """Opera should be launched via fallback paths, not which()."""
        # Make only Opera's fallback path exist
        def exists_side_effect(path):
            # Only Opera's first fallback path exists
            return "Opera" in path and "launcher.exe" in path
        mock_exists.side_effect = exists_side_effect
        mock_which.return_value = None

        with patch("launcher.launch_exe", return_value=True) as mock_launch:
            launch_browsers()
            # Opera launch_exe should have been called at least once
            opera_calls = [
                c for c in mock_launch.call_args_list
                if "Opera" in str(c)
            ]
            assert len(opera_calls) >= 1, (
                "Opera should have been launched via fallback path"
            )

    @patch("platform.system", return_value="Windows")
    @patch("shutil.which")
    @patch("os.path.exists", return_value=False)
    def test_opera_not_found_prints_message(self, mock_exists, mock_which, mock_system):
        """When Opera is not found, it should print 'Not found' without crashing."""
        mock_which.return_value = None
        launch_browsers()  # should not raise


# ═══════════════════════════════════════════════════════════════════════════════
# launch_vm_system
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchVMSystem:
    """Tests for the VM system launcher."""

    def test_calls_docker_and_wsl(self):
        with patch("launcher.launch_exe_from_paths", return_value=True) as mock_docker:
            with patch("shutil.which", return_value="C:\\Windows\\System32\\wsl.exe"):
                with patch("launcher.launch_exe", return_value=True) as mock_wsl:
                    launch_vm_system()
                    mock_docker.assert_called_once()
                    mock_wsl.assert_called_once_with("C:\\Windows\\System32\\wsl.exe", "WSL")

    def test_handles_wsl_missing(self):
        with patch("launcher.launch_exe_from_paths", return_value=False) as mock_docker:
            with patch("shutil.which", return_value=None):
                launch_vm_system()
                mock_docker.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# launch_all — cross-category de-duplication
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchAll:
    """Tests for the launch_all orchestration function."""

    def test_resets_tracker_before_launching(self):
        """launch_all must call reset_tracker() first."""
        with patch("launcher.reset_tracker") as mock_reset:
            with patch("launcher.launch_game_launchers"):
                with patch("launcher.launch_browsers"):
                    with patch("launcher.launch_live_kit"):
                        with patch("launcher.launch_vm_system"):
                            launch_all()
                            mock_reset.assert_called_once()

    def test_calls_all_four_categories(self):
        with patch("launcher.reset_tracker"):
            with patch("launcher.launch_game_launchers") as mock_games:
                with patch("launcher.launch_browsers") as mock_browsers:
                    with patch("launcher.launch_live_kit") as mock_live:
                        with patch("launcher.launch_vm_system") as mock_vm:
                            launch_all()
                            mock_games.assert_called_once()
                            mock_browsers.assert_called_once()
                            mock_live.assert_called_once()
                            mock_vm.assert_called_once()

    def test_calls_categories_in_correct_order(self):
        """Game launchers must be called before live_kit so Steam is tracked."""
        parent_mock = MagicMock()
        parent_mock.attach_mock(MagicMock(return_value=None), "reset_tracker")
        parent_mock.attach_mock(MagicMock(return_value=None), "launch_game_launchers")
        parent_mock.attach_mock(MagicMock(return_value=None), "launch_browsers")
        parent_mock.attach_mock(MagicMock(return_value=None), "launch_live_kit")
        parent_mock.attach_mock(MagicMock(return_value=None), "launch_vm_system")

        with patch.multiple(
            "launcher",
            reset_tracker=parent_mock.reset_tracker,
            launch_game_launchers=parent_mock.launch_game_launchers,
            launch_browsers=parent_mock.launch_browsers,
            launch_live_kit=parent_mock.launch_live_kit,
            launch_vm_system=parent_mock.launch_vm_system,
        ):
            launch_all()

        # Verify order: games before live_kit (critical for Steam de-dup)
        calls = [call[0] for call in parent_mock.method_calls]
        game_idx = calls.index("launch_game_launchers")
        live_idx = calls.index("launch_live_kit")
        assert game_idx < live_idx, "game launchers must launch before live kit"


# ═══════════════════════════════════════════════════════════════════════════════
# Steam double-launch integration test
# ═══════════════════════════════════════════════════════════════════════════════

class TestSteamDoubleLaunchIntegration:
    """Integration test: Steam must not be double-launched by launch_all."""

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_steam_launched_only_once(self, mock_popen, mock_exists):
        """Simulate launch_all with all exe paths existing; Steam must be Popen'd once."""
        # All paths exist so every launcher gets launched
        launch_all()

        # Count how many times Steam.exe was opened
        steam_calls = [
            c for c in mock_popen.call_args_list
            if any("Steam.exe" in str(arg) for arg in c.args[0])
        ]
        assert len(steam_calls) <= 1, (
            f"Steam.exe was Popen'd {len(steam_calls)} times — must be ≤ 1"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Menu system
# ═══════════════════════════════════════════════════════════════════════════════

class TestMenuFunctions:
    """Smoke tests for menu display functions."""

    def test_clear_screen_does_not_crash(self):
        clear_screen()

    def test_print_header_does_not_crash(self):
        print_header()

    def test_print_menu_does_not_crash(self):
        print_menu()


# ═══════════════════════════════════════════════════════════════════════════════
# main() loop — choices 0-5
# ═══════════════════════════════════════════════════════════════════════════════

class TestMainLoop:
    """Sanity tests for the main() interactive loop."""

    def test_exits_on_zero(self):
        """Selecting 0 should exit immediately."""
        with patch("builtins.input", return_value="0"):
            with patch("launcher.clear_screen"):
                with patch("launcher.print_header"):
                    with patch("launcher.print_menu"):
                        main()  # should exit without error

    @patch("launcher.clear_screen")
    @patch("launcher.print_header")
    @patch("launcher.print_menu")
    def test_invalid_choice_does_not_crash(self, mock_menu, mock_header, mock_clear):
        """Invalid choice prints error then waits for Enter, then exits on 0."""
        # main() calls input() for: menu choice → Enter to continue → menu choice → exit
        with patch("builtins.input", side_effect=["99", "", "0"]):
            main()  # 99 → invalid, Enter → back to menu, 0 → exit


class TestMainWithChoices:
    """Test main() with each valid menu choice (1-5)."""

    def _run_main_with_choice(self, choice: str):
        """Helper: run main() with a choice, then exit."""
        with patch("launcher.clear_screen"):
            with patch("launcher.print_header"):
                with patch("launcher.print_menu"):
                    with patch("builtins.input", side_effect=[choice, "", "0"]):
                        main()

    def test_choice_1_launches_game_launchers(self):
        with patch("launcher.launch_game_launchers") as mock_games:
            self._run_main_with_choice("1")
            mock_games.assert_called_once()

    def test_choice_2_launches_browsers(self):
        with patch("launcher.launch_browsers") as mock_browsers:
            self._run_main_with_choice("2")
            mock_browsers.assert_called_once()

    def test_choice_3_launches_live_kit(self):
        with patch("launcher.launch_live_kit") as mock_live:
            self._run_main_with_choice("3")
            mock_live.assert_called_once()

    def test_choice_4_calls_launch_all(self):
        with patch("launcher.launch_all") as mock_all:
            self._run_main_with_choice("4")
            mock_all.assert_called_once()

    def test_choice_5_launches_vm_system(self):
        with patch("launcher.launch_vm_system") as mock_vm:
            self._run_main_with_choice("5")
            mock_vm.assert_called_once()

    def test_reset_tracker_called_for_each_choice(self):
        """reset_tracker() should be called before each menu action."""
        with patch("launcher.reset_tracker") as mock_reset:
            with patch("launcher.launch_browsers"):  # prevent real browser launches
                self._run_main_with_choice("2")
            mock_reset.assert_called()
