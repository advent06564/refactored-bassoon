"""Unit tests for refactored-bassoon utils.py module.

Tests the LaunchTracker singleton, path resolution, launch helpers,
and double-launch prevention scenarios.
"""

import os
import sys
import subprocess
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import utils
from utils import (
    _LaunchTracker,
    find_first_existing,
    launch_exe,
    launch_exe_from_paths,
    launch_uwp,
    launch_os_startfile,
    reset_tracker,
    was_launched,
    is_process_running,
    is_windows,
    is_macos,
    ENV,
)


# ═══════════════════════════════════════════════════════════════════════════════
# _LaunchTracker
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchTracker:
    """Unit tests for the _LaunchTracker class."""

    def test_initially_empty(self):
        tracker = _LaunchTracker()
        assert tracker.was_launched("anything") is False

    def test_mark_and_check(self):
        tracker = _LaunchTracker()
        tracker.mark_launched("Steam")
        assert tracker.was_launched("Steam") is True
        assert tracker.was_launched("Chrome") is False

    def test_mark_multiple(self):
        tracker = _LaunchTracker()
        tracker.mark_launched("A")
        tracker.mark_launched("B")
        tracker.mark_launched("C")
        assert tracker.was_launched("A")
        assert tracker.was_launched("B")
        assert tracker.was_launched("C")

    def test_clear_resets_all(self):
        tracker = _LaunchTracker()
        tracker.mark_launched("A")
        tracker.mark_launched("B")
        tracker.clear()
        assert tracker.was_launched("A") is False
        assert tracker.was_launched("B") is False

    def test_mark_idempotent(self):
        tracker = _LaunchTracker()
        tracker.mark_launched("X")
        tracker.mark_launched("X")
        tracker.mark_launched("X")
        assert tracker.was_launched("X") is True
        # Internal set should have size 1
        assert len(tracker._launched) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level tracker wrappers
# ═══════════════════════════════════════════════════════════════════════════════

class TestModuleTracker:
    """Tests for was_launched() and reset_tracker() using the singleton."""

    def setup_method(self):
        reset_tracker()

    def test_was_launched_returns_false_initially(self):
        assert was_launched("anything") is False

    def test_reset_tracker_clears_state(self):
        utils._tracker.mark_launched("Foo")
        assert was_launched("Foo") is True
        reset_tracker()
        assert was_launched("Foo") is False


# ═══════════════════════════════════════════════════════════════════════════════
# find_first_existing
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindFirstExisting:
    """Tests for path resolution utility."""

    @patch("os.path.exists", return_value=True)
    def test_returns_first_existing(self, mock_exists):
        result = find_first_existing(["/a/b", "/c/d", "/e/f"])
        assert result == "/a/b"

    @patch("os.path.exists", side_effect=[False, True, True])
    def test_skips_missing_returns_second(self, mock_exists):
        result = find_first_existing(["/a", "/b", "/c"])
        assert result == "/b"

    @patch("os.path.exists", return_value=False)
    def test_returns_none_when_none_exist(self, mock_exists):
        result = find_first_existing(["/x", "/y"])
        assert result is None

    @patch("os.path.exists", return_value=True)
    def test_expands_env_vars(self, mock_exists):
        with patch.dict(os.environ, {"MYAPP": "/opt/myapp"}):
            result = find_first_existing(["%MYAPP%/bin/app.exe"])
            assert result == "/opt/myapp/bin/app.exe"

    def test_empty_list_returns_none(self):
        assert find_first_existing([]) is None


# ═══════════════════════════════════════════════════════════════════════════════
# launch_exe
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchExe:
    """Tests for the launch_exe helper."""

    def setup_method(self):
        reset_tracker()

    @patch("subprocess.Popen")
    @patch("utils.is_process_running", return_value=False)
    def test_launches_and_marks(self, mock_proc, mock_popen):
        result = launch_exe("/fake/app.exe", "TestApp")
        assert result is True
        mock_popen.assert_called_once_with(["/fake/app.exe"])
        assert was_launched("TestApp") is True

    @patch("utils.is_process_running", return_value=False)
    def test_skips_when_already_launched(self, mock_proc):
        utils._tracker.mark_launched("TestApp")
        with patch("subprocess.Popen") as mock_popen:
            result = launch_exe("/fake/app.exe", "TestApp")
            assert result is True
            mock_popen.assert_not_called()

    @patch("utils.is_process_running", return_value=False)
    def test_no_skip_when_flag_false(self, mock_proc):
        utils._tracker.mark_launched("TestApp")
        with patch("subprocess.Popen") as mock_popen:
            result = launch_exe("/fake/app.exe", "TestApp", skip_if_launched=False)
            assert result is True
            mock_popen.assert_called_once()

    @patch("subprocess.Popen", side_effect=FileNotFoundError("not found"))
    @patch("utils.is_process_running", return_value=False)
    def test_handles_launch_failure(self, mock_proc, mock_popen):
        result = launch_exe("/bad/path.exe", "BadApp")
        assert result is False
        assert was_launched("BadApp") is False  # not marked on failure

    @patch("subprocess.Popen", side_effect=PermissionError("denied"))
    @patch("utils.is_process_running", return_value=False)
    def test_handles_permission_error(self, mock_proc, mock_popen):
        result = launch_exe("/denied.exe", "DeniedApp")
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# launch_exe_from_paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchExeFromPaths:
    """Tests for the multi-path launch helper."""

    def setup_method(self):
        reset_tracker()

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen")
    @patch("utils.is_process_running", return_value=False)
    def test_finds_first_and_launches(self, mock_proc, mock_popen, mock_exists):
        result = launch_exe_from_paths(["/a/app.exe", "/b/app.exe"], "MyApp")
        assert result is True
        mock_popen.assert_called_once_with(["/a/app.exe"])
        assert was_launched("MyApp") is True

    @patch("os.path.exists", return_value=False)
    def test_returns_false_when_not_found(self, mock_exists):
        result = launch_exe_from_paths(["/missing/app.exe"], "MissingApp")
        assert result is False

    def test_skips_when_already_launched(self):
        utils._tracker.mark_launched("MyApp")
        with patch("os.path.exists") as mock_exists:
            result = launch_exe_from_paths(["/a/app.exe"], "MyApp")
            assert result is True
            mock_exists.assert_not_called()  # short-circuits

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen", side_effect=PermissionError("denied"))
    @patch("utils.is_process_running", return_value=False)
    def test_handles_permission_error(self, mock_proc, mock_popen, mock_exists):
        """PermissionError from Popen should be caught and return False."""
        result = launch_exe_from_paths(["/denied/app.exe"], "DeniedApp")
        assert result is False
        assert was_launched("DeniedApp") is False


# ═══════════════════════════════════════════════════════════════════════════════
# launch_uwp
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchUWP:
    """Tests for the UWP / protocol-handler launcher."""

    def setup_method(self):
        reset_tracker()

    @patch("subprocess.Popen")
    def test_launches_and_marks(self, mock_popen):
        result = launch_uwp("ms-settings:", "Settings")
        assert result is True
        mock_popen.assert_called_once_with(["cmd", "/c", "start", "", "ms-settings:"])
        assert was_launched("Settings") is True

    def test_skips_when_already_launched(self):
        utils._tracker.mark_launched("Settings")
        with patch("subprocess.Popen") as mock_popen:
            result = launch_uwp("ms-settings:", "Settings")
            assert result is True
            mock_popen.assert_not_called()

    def test_no_skip_when_flag_false(self):
        """With skip_if_launched=False, launch even if already tracked."""
        utils._tracker.mark_launched("Settings")
        with patch("subprocess.Popen") as mock_popen:
            result = launch_uwp("ms-settings:", "Settings", skip_if_launched=False)
            assert result is True
            mock_popen.assert_called_once()  # should launch despite tracker
            assert was_launched("Settings") is True

    @patch("subprocess.Popen", side_effect=Exception("UWP failed"))
    def test_handles_failure(self, mock_popen):
        result = launch_uwp("bad-uri:", "BadApp")
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# launch_os_startfile
# ═══════════════════════════════════════════════════════════════════════════════

class TestLaunchOsStartfile:
    """Tests for os.startfile launcher."""

    def setup_method(self):
        reset_tracker()

    @patch("utils.is_process_running", return_value=False)
    @patch("os.startfile")
    def test_launches_and_marks(self, mock_startfile, mock_proc):
        result = launch_os_startfile("C:\\shortcut.lnk", "ShortcutApp")
        assert result is True
        mock_startfile.assert_called_once_with("C:\\shortcut.lnk")
        assert was_launched("ShortcutApp") is True

    @patch("utils.is_process_running", return_value=False)
    def test_skips_when_already_launched(self, mock_proc):
        utils._tracker.mark_launched("ShortcutApp")
        with patch("os.startfile") as mock_startfile:
            result = launch_os_startfile("C:\\shortcut.lnk", "ShortcutApp")
            assert result is True
            mock_startfile.assert_not_called()

    @patch("utils.is_process_running", return_value=False)
    def test_no_skip_when_flag_false(self, mock_proc):
        """With skip_if_launched=False, launch even if already tracked."""
        utils._tracker.mark_launched("ShortcutApp")
        with patch("os.startfile") as mock_startfile:
            result = launch_os_startfile("C:\\shortcut.lnk", "ShortcutApp", skip_if_launched=False)
            assert result is True
            mock_startfile.assert_called_once()  # should launch despite tracker
            assert was_launched("ShortcutApp") is True

    @patch("os.startfile", side_effect=FileNotFoundError("missing"))
    def test_handles_file_not_found(self, mock_startfile):
        result = launch_os_startfile("C:\\missing.lnk", "MissingApp")
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# Double-launch prevention — cross-function
# ═══════════════════════════════════════════════════════════════════════════════

class TestDoubleLaunchPrevention:
    """End-to-end double-launch prevention scenarios."""

    def setup_method(self):
        reset_tracker()

    @patch("utils.is_process_running", return_value=False)
    @patch("subprocess.Popen")
    def test_same_name_blocked_across_helper_types(self, mock_popen, mock_proc):
        """launch_exe sets tracker; launch_uwp with same name should skip."""
        launch_exe("/fake/steam.exe", "Steam")
        assert was_launched("Steam")
        mock_popen.reset_mock()

        result = launch_uwp("steam://", "Steam")
        assert result is True  # returns True for skip
        mock_popen.assert_not_called()  # NOT launched again

    @patch("utils.is_process_running", return_value=False)
    @patch("subprocess.Popen")
    def test_reset_tracker_allows_relaunch(self, mock_popen, mock_proc):
        """After reset_tracker(), the same name can be launched again."""
        launch_exe("/fake/app.exe", "App")
        assert was_launched("App")
        mock_popen.reset_mock()

        reset_tracker()
        result = launch_exe("/fake/app.exe", "App")
        assert result is True
        mock_popen.assert_called_once()  # launched again after reset

    @patch("os.path.exists", return_value=True)
    @patch("utils.is_process_running", return_value=False)
    @patch("subprocess.Popen")
    def test_launch_exe_from_paths_respects_tracker(self, mock_popen, mock_proc, mock_exists):
        """launch_exe_from_paths skips when tracker has the name."""
        utils._tracker.mark_launched("Epic Games")
        result = launch_exe_from_paths(["/epic/epic.exe"], "Epic Games")
        assert result is True
        mock_exists.assert_not_called()
        mock_popen.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Platform detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlatformDetection:
    """Tests for is_windows() and is_macos()."""

    @patch("utils._platform.system", return_value="Windows")
    def test_is_windows_true(self, _mock):
        # Re-import to pick up the patched module
        import importlib
        importlib.reload(utils)
        assert utils.is_windows() is True
        assert utils.is_macos() is False

    @patch("utils._platform.system", return_value="Darwin")
    def test_is_macos_true(self, _mock):
        import importlib
        importlib.reload(utils)
        assert utils.is_macos() is True
        assert utils.is_windows() is False

    @patch("utils._platform.system", return_value="Linux")
    def test_neither_on_linux(self, _mock):
        import importlib
        importlib.reload(utils)
        assert utils.is_windows() is False
        assert utils.is_macos() is False


# ═══════════════════════════════════════════════════════════════════════════════
# is_process_running
# ═══════════════════════════════════════════════════════════════════════════════

class TestIsProcessRunning:
    """Tests for system-wide process detection."""

    @patch("utils.is_windows", return_value=True)
    @patch("subprocess.run")
    def test_detects_running_process(self, mock_run, mock_win):
        """Returns True when tasklist output contains the exe name."""
        mock_run.return_value = MagicMock(stdout="obs64.exe                       1234 Console  1     123,456 K")
        assert is_process_running("obs64.exe") is True

    @patch("utils.is_windows", return_value=True)
    @patch("subprocess.run")
    def test_detects_not_running(self, mock_run, mock_win):
        """Returns False when tasklist output does not contain the exe name."""
        mock_run.return_value = MagicMock(stdout="INFO: No tasks are running which match the specified criteria.")
        assert is_process_running("obs64.exe") is False

    @patch("utils.is_windows", return_value=True)
    @patch("subprocess.run")
    def test_case_insensitive_match(self, mock_run, mock_win):
        """Process name matching should be case-insensitive."""
        mock_run.return_value = MagicMock(stdout="Steam.exe                       5678 Console  1     234,567 K")
        assert is_process_running("steam.exe") is True

    @patch("utils.is_windows", return_value=False)
    def test_non_windows_returns_false(self, mock_win):
        """On non-Windows, always return False (fail open)."""
        assert is_process_running("anything.exe") is False

    @patch("utils.is_windows", return_value=True)
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired("tasklist", 5))
    def test_timeout_returns_false(self, mock_run, mock_win):
        """Timeout → return False (fail open — don't block launch)."""
        assert is_process_running("slow.exe") is False

    @patch("utils.is_windows", return_value=True)
    @patch("subprocess.run", side_effect=FileNotFoundError("tasklist not found"))
    def test_tasklist_missing_returns_false(self, mock_run, mock_win):
        """tasklist not found → return False (fail open)."""
        assert is_process_running("anything.exe") is False


# ═══════════════════════════════════════════════════════════════════════════════
# Process-level skip in launch_exe
# ═══════════════════════════════════════════════════════════════════════════════

class TestProcessLevelSkip:
    """Tests for system-wide process checking in launch helpers."""

    def setup_method(self):
        reset_tracker()

    @patch("utils.is_process_running", return_value=True)
    @patch("subprocess.Popen")
    def test_launch_exe_skips_when_process_running(self, mock_popen, mock_proc):
        """When process is already running system-wide, skip the launch."""
        result = launch_exe("/fake/obs64.exe", "OBS Studio", exe_name="obs64.exe")
        assert result is True  # Returns True for skip
        mock_popen.assert_not_called()
        assert was_launched("OBS Studio") is True  # Still marked as launched

    @patch("utils.is_process_running", return_value=False)
    @patch("subprocess.Popen")
    def test_launch_exe_proceeds_when_process_not_running(self, mock_popen, mock_proc):
        """When process is not running, proceed with launch."""
        result = launch_exe("/fake/obs64.exe", "OBS Studio", exe_name="obs64.exe")
        assert result is True
        mock_popen.assert_called_once_with(["/fake/obs64.exe"])

    @patch("utils.is_process_running", return_value=True)
    def test_launch_exe_from_paths_skips_when_process_running(self, mock_proc):
        """launch_exe_from_paths skips when process is running (with exe_name)."""
        with patch("os.path.exists") as mock_exists:
            result = launch_exe_from_paths(["/fake/steam.exe"], "Steam", exe_name="Steam.exe")
            assert result is True
            mock_exists.assert_not_called()  # Short-circuits before checking paths
            assert was_launched("Steam") is True

    @patch("utils.is_process_running", return_value=True)
    @patch("os.startfile")
    def test_launch_os_startfile_skips_when_process_running(self, mock_start, mock_proc):
        """launch_os_startfile skips when process is running (with exe_name)."""
        result = launch_os_startfile("C:\\obs.lnk", "OBS Studio", exe_name="obs64.exe")
        assert result is True
        mock_start.assert_not_called()
        assert was_launched("OBS Studio") is True

    @patch("utils.is_process_running", return_value=False)
    @patch("subprocess.Popen")
    def test_tracker_skip_takes_priority_over_process_check(self, mock_popen, mock_proc):
        """Tracker skip happens first — process check is not even called."""
        utils._tracker.mark_launched("Steam")
        result = launch_exe("/fake/steam.exe", "Steam", exe_name="Steam.exe")
        assert result is True
        mock_popen.assert_not_called()
        # is_process_running was never called because tracker skip took priority
        mock_proc.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# ENV dict
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnvDict:
    """Tests for the ENV dictionary structure."""

    def test_has_all_keys(self):
        for key in ("PROGFILES", "PROGFILES_X86", "USERPROFILE", "LOCALAPPDATA", "APPDATA"):
            assert key in ENV, f"ENV missing key: {key}"

    def test_values_are_strings(self):
        for key, value in ENV.items():
            assert isinstance(value, str), f"ENV['{key}'] is not a string: {type(value)}"
