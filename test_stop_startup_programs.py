"""Unit tests for refactored-bassoon stop_startup_programs.py module.

Tests admin detection, startup shortcut removal, and registry hive clearing.
"""

import os
import glob
import winreg
import ctypes
from unittest.mock import MagicMock, patch, call

import pytest

# Module-level code is guarded by __name__ == "__main__", safe to import
import stop_startup_programs as ssp


# ═══════════════════════════════════════════════════════════════════════════════
# is_admin
# ═══════════════════════════════════════════════════════════════════════════════

class TestIsAdmin:
    """Tests for administrative privilege detection."""

    @patch.object(ctypes.windll.shell32, "IsUserAnAdmin", return_value=1)
    def test_returns_true_when_admin(self, _mock):
        """IsUserAnAdmin returns nonzero → is_admin() is truthy."""
        assert ssp.is_admin() == True

    @patch.object(ctypes.windll.shell32, "IsUserAnAdmin", return_value=0)
    def test_returns_false_when_not_admin(self, _mock):
        """IsUserAnAdmin returns 0 → is_admin() is falsy."""
        assert ssp.is_admin() == False

    @patch.object(ctypes.windll.shell32, "IsUserAnAdmin", side_effect=AttributeError("no function"))
    def test_returns_false_on_exception(self, _mock):
        """Exceptions during privilege check should return False."""
        assert ssp.is_admin() is False


# ═══════════════════════════════════════════════════════════════════════════════
# remove_startup_shortcuts
# ═══════════════════════════════════════════════════════════════════════════════

class TestRemoveStartupShortcuts:
    """Tests for startup folder shortcut removal."""

    @patch("os.path.exists", return_value=True)
    @patch("glob.glob")
    @patch("os.remove")
    @patch.dict(os.environ, {
        "APPDATA": r"C:\Users\Test\AppData\Roaming",
        "ProgramData": r"C:\ProgramData",
    })
    def test_removes_files_from_both_folders(self, mock_remove, mock_glob, mock_exists):
        """Both startup folders exist and have files — all removed."""
        # Return different file lists per glob call (one per folder)
        mock_glob.side_effect = [
            [
                r"C:\Users\Test\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\shortcut1.lnk",
                r"C:\Users\Test\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\shortcut2.lnk",
            ],
            [
                r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\common1.lnk",
            ],
        ]
        ssp.remove_startup_shortcuts()
        assert mock_remove.call_count == 3

    @patch("os.path.exists", side_effect=[True, False])
    @patch("glob.glob")
    @patch("os.remove")
    @patch.dict(os.environ, {
        "APPDATA": r"C:\Users\Test\AppData\Roaming",
        "ProgramData": r"C:\ProgramData",
    })
    def test_removes_files_from_one_folder_only(self, mock_remove, mock_glob, mock_exists):
        """Only user startup folder exists; common folder skipped gracefully."""
        mock_glob.return_value = [r"C:\Users\Test\...\Startup\app.lnk"]
        ssp.remove_startup_shortcuts()
        mock_remove.assert_called_once()

    @patch("os.path.exists", return_value=False)
    @patch.dict(os.environ, {
        "APPDATA": r"C:\Users\Test\AppData\Roaming",
        "ProgramData": r"C:\ProgramData",
    })
    def test_handles_folder_not_found(self, mock_exists):
        """Neither startup folder exists — should print messages, not crash."""
        ssp.remove_startup_shortcuts()  # should not raise

    @patch("os.path.exists", return_value=True)
    @patch("glob.glob", return_value=[r"C:\...\Startup\readonly.lnk"])
    @patch("os.remove", side_effect=PermissionError("access denied"))
    @patch.dict(os.environ, {
        "APPDATA": r"C:\Users\Test\AppData\Roaming",
        "ProgramData": r"C:\ProgramData",
    })
    def test_handles_file_removal_permission_error(self, mock_remove, mock_glob, mock_exists):
        """PermissionError during file removal is caught, execution continues."""
        ssp.remove_startup_shortcuts()  # should not raise; error is printed

    @patch("os.path.exists", return_value=True)
    @patch("glob.glob", return_value=[r"C:\...\Startup\bad.lnk"])
    @patch("os.remove", side_effect=OSError("disk error"))
    @patch.dict(os.environ, {
        "APPDATA": r"C:\Users\Test\AppData\Roaming",
        "ProgramData": r"C:\ProgramData",
    })
    def test_handles_file_removal_os_error(self, mock_remove, mock_glob, mock_exists):
        """Generic OSError during removal is caught gracefully."""
        ssp.remove_startup_shortcuts()  # should not raise

    @patch("os.path.exists", return_value=True)
    @patch("glob.glob", return_value=[])
    @patch.dict(os.environ, {
        "APPDATA": r"C:\Users\Test\AppData\Roaming",
        "ProgramData": r"C:\ProgramData",
    })
    def test_empty_startup_folders_no_error(self, mock_glob, mock_exists):
        """Empty startup folders should not cause errors."""
        ssp.remove_startup_shortcuts()  # should not raise


# ═══════════════════════════════════════════════════════════════════════════════
# clear_startup_registry_hives
# ═══════════════════════════════════════════════════════════════════════════════

class TestClearRegistryHives:
    """Tests for registry startup entry removal."""

    # ── Admin vs non-admin hive selection ─────────────────────────────────────

    @patch.object(ssp, "is_admin", return_value=False)
    def test_non_admin_skips_local_machine(self, _mock_admin):
        """Non-admin: only HKEY_CURRENT_USER is processed."""
        with patch.object(winreg, "OpenKey", side_effect=FileNotFoundError("key missing")):
            ssp.clear_startup_registry_hives()
            # OpenKey called only for HKCU, not HKLM
            assert winreg.OpenKey.call_count == 1
            first_root = winreg.OpenKey.call_args_list[0][0][0]
            assert first_root == winreg.HKEY_CURRENT_USER

    @patch.object(ssp, "is_admin", return_value=True)
    def test_admin_processes_all_hives(self, _mock_admin):
        """Admin: both HKCU and HKLM hives are processed."""
        with patch.object(winreg, "OpenKey", side_effect=FileNotFoundError("key missing")):
            ssp.clear_startup_registry_hives()
            # 1 HKCU + 2 HKLM = 3 calls
            assert winreg.OpenKey.call_count == 3
            roots = [c[0][0] for c in winreg.OpenKey.call_args_list]
            assert winreg.HKEY_CURRENT_USER in roots
            assert winreg.HKEY_LOCAL_MACHINE in roots

    # ── Registry key not found ────────────────────────────────────────────────

    @patch.object(ssp, "is_admin", return_value=False)
    @patch.object(winreg, "OpenKey", side_effect=FileNotFoundError("key does not exist"))
    def test_registry_key_not_found_handled(self, mock_open, _mock_admin):
        """FileNotFoundError from OpenKey is caught and handled gracefully."""
        ssp.clear_startup_registry_hives()  # should not raise

    # ── General registry errors ───────────────────────────────────────────────

    @patch.object(ssp, "is_admin", return_value=False)
    @patch.object(winreg, "OpenKey", side_effect=PermissionError("access denied"))
    def test_general_registry_error_handled(self, mock_open, _mock_admin):
        """Unexpected exceptions from OpenKey are caught."""
        ssp.clear_startup_registry_hives()  # should not raise

    # ── No startup entries ────────────────────────────────────────────────────

    @patch.object(ssp, "is_admin", return_value=False)
    @patch.object(winreg, "OpenKey")
    @patch.object(winreg, "EnumValue", side_effect=OSError)  # no more values
    @patch.object(winreg, "DeleteValue")
    def test_no_startup_entries_found(self, mock_delete, mock_enum, mock_open, _mock_admin):
        """When no values exist, skip without attempting deletions."""
        mock_open.return_value.__enter__.return_value = MagicMock()
        ssp.clear_startup_registry_hives()
        mock_delete.assert_not_called()

    # ── Removing registry values ──────────────────────────────────────────────

    @patch.object(ssp, "is_admin", return_value=False)
    @patch.object(winreg, "DeleteValue")
    @patch.object(winreg, "EnumValue")
    @patch.object(winreg, "OpenKey")
    def test_removes_registry_values(self, mock_open, mock_enum, mock_delete, _mock_admin):
        """Values are enumerated and each is deleted."""
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_enum.side_effect = [
            ("OneDrive", None, None),
            ("Spotify", None, None),
            ("Steam", None, None),
            OSError,  # end of values
        ]
        ssp.clear_startup_registry_hives()
        assert mock_delete.call_count == 3
        mock_delete.assert_any_call(mock_open.return_value.__enter__.return_value, "OneDrive")
        mock_delete.assert_any_call(mock_open.return_value.__enter__.return_value, "Spotify")
        mock_delete.assert_any_call(mock_open.return_value.__enter__.return_value, "Steam")

    # ── Error during value deletion ───────────────────────────────────────────

    @patch.object(ssp, "is_admin", return_value=False)
    @patch.object(winreg, "DeleteValue", side_effect=PermissionError("cannot delete"))
    @patch.object(winreg, "EnumValue")
    @patch.object(winreg, "OpenKey")
    def test_handles_delete_value_error(self, mock_open, mock_enum, mock_delete, _mock_admin):
        """Errors during value deletion are caught, execution continues."""
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_enum.side_effect = [
            ("LockedEntry", None, None),
            OSError,
        ]
        ssp.clear_startup_registry_hives()  # should not raise
        mock_delete.assert_called_once_with(
            mock_open.return_value.__enter__.return_value, "LockedEntry"
        )

    # ── Mixed scenario: some values delete cleanly, others fail ───────────────

    @patch.object(ssp, "is_admin", return_value=False)
    @patch.object(winreg, "DeleteValue")
    @patch.object(winreg, "EnumValue")
    @patch.object(winreg, "OpenKey")
    def test_mixed_success_and_failure(self, mock_open, mock_enum, mock_delete, _mock_admin):
        """One value deletes fine, another raises, loop continues."""
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_enum.side_effect = [
            ("GoodApp", None, None),
            ("BadApp", None, None),
            OSError,
        ]
        mock_delete.side_effect = [None, PermissionError("access denied")]
        ssp.clear_startup_registry_hives()  # should not raise
        assert mock_delete.call_count == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level __main__ guard
# ═══════════════════════════════════════════════════════════════════════════════

class TestModuleGuard:
    """The module has an if __name__ == \"__main__\" block for CLI use."""

    def test_module_import_does_not_execute_main(self):
        """Importing does not run the cleanup functions."""
        assert hasattr(ssp, "is_admin")
        assert hasattr(ssp, "remove_startup_shortcuts")
        assert hasattr(ssp, "clear_startup_registry_hives")
