"""Unit tests for refactored-bassoon run_sites.py module.

Tests config loading, WSL detection, URL opening via WSL/controller/webbrowser
paths, browser override, and error handling.
"""

import json
import os
import sys
import platform
import subprocess
import webbrowser
import importlib
from unittest.mock import MagicMock, patch, mock_open, call

import pytest

# ── Reload helper ─────────────────────────────────────────────────────────────

def _reload_module(json_content: str | None = None, open_side_effect=None):
    """Reload run_sites with controlled config mocking.

    Returns (module, exit_mock).
    """
    if open_side_effect is not None:
        m = patch("builtins.open", side_effect=open_side_effect)
    elif json_content is not None:
        m = patch("builtins.open", mock_open(read_data=json_content))
    else:
        m = patch("builtins.open", mock_open(read_data="{}"))

    with m:
        with patch("sys.exit") as mock_exit:
            importlib.reload(run_sites)
            return mock_exit


# ── Import the module with a valid config for tests that need URLs ────────────

VALID_JSON = json.dumps({
    "default_browser": "opera",
    "social_media_urls": ["https://example.com", "https://test.com"],
})

EMPTY_JSON = json.dumps({
    "default_browser": "opera",
    "social_media_urls": [],
})

with patch("builtins.open", mock_open(read_data=VALID_JSON)):
    import run_sites


# ═══════════════════════════════════════════════════════════════════════════════
# Config loading (module-level code)
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfigLoading:
    """Tests for module-level config.json loading."""

    def test_valid_config_loads_urls_and_browser(self):
        """Valid config populates URLS and DEFAULT_BROWSER."""
        _reload_module(VALID_JSON)
        assert run_sites.URLS == ["https://example.com", "https://test.com"]
        assert run_sites.DEFAULT_BROWSER == "opera"

    def test_missing_config_exits(self):
        """FileNotFoundError → sys.exit(1)."""
        mock_exit = _reload_module(open_side_effect=FileNotFoundError("missing"))
        mock_exit.assert_called_once_with(1)

    def test_invalid_json_exits(self):
        """JSONDecodeError → sys.exit(1)."""
        mock_exit = _reload_module(json_content="{not valid json")
        mock_exit.assert_called_once_with(1)

    def test_empty_urls_exits(self):
        """Empty social_media_urls → sys.exit(0)."""
        mock_exit = _reload_module(EMPTY_JSON)
        mock_exit.assert_called_once_with(0)

    # Restore valid config for subsequent tests
    def setup_method(self):
        _reload_module(VALID_JSON)

    def teardown_method(self):
        _reload_module(VALID_JSON)


# ═══════════════════════════════════════════════════════════════════════════════
# WSL detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestWSLDetection:
    """Tests for is_wsl() platform detection."""

    @patch("platform.release", return_value="5.15.90.1-microsoft-standard-WSL2")
    def test_detects_wsl_with_microsoft(self, _mock_release):
        assert run_sites.is_wsl() is True

    @patch("platform.release", return_value="5.10.102.1-WSL2")
    def test_detects_wsl_with_wsl_keyword(self, _mock_release):
        assert run_sites.is_wsl() is True

    @patch("platform.release", return_value="WSL2-5.15")
    def test_detects_wsl_case_insensitive(self, _mock_release):
        """platform.release().lower() makes detection case-insensitive."""
        # release string contains "WSL" → lower() → "wsl" → detected
        assert run_sites.is_wsl() is True

    @patch("platform.release", return_value="10.0.22621")
    def test_returns_false_on_windows(self, _mock_release):
        assert run_sites.is_wsl() is False

    @patch("platform.release", return_value="6.5.0-18-generic")
    def test_returns_false_on_linux(self, _mock_release):
        assert run_sites.is_wsl() is False

    @patch("platform.release", return_value="22.5.0")
    def test_returns_false_on_macos(self, _mock_release):
        assert run_sites.is_wsl() is False


# ═══════════════════════════════════════════════════════════════════════════════
# URL opening paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestURLOpening:
    """Tests for URL opening via WSL, controller, or webbrowser paths."""

    def setup_method(self):
        _reload_module(VALID_JSON)

    # ── WSL path ──────────────────────────────────────────────────────────────

    @patch("run_sites.is_wsl", return_value=True)
    @patch("subprocess.run")
    @patch("time.sleep")
    def test_wsl_path_uses_wsl_open(self, mock_sleep, mock_run, _mock_wsl):
        run_sites.main()
        expected_calls = [
            call(["wsl-open", "https://example.com"], check=True),
            call(["wsl-open", "https://test.com"], check=True),
        ]
        assert mock_run.call_args_list == expected_calls

    @patch("run_sites.is_wsl", return_value=True)
    @patch("subprocess.run", side_effect=FileNotFoundError("wsl-open not found"))
    @patch("sys.exit")
    @patch("time.sleep")
    def test_wsl_open_not_found_exits(self, mock_sleep, mock_exit, mock_run, _mock_wsl):
        """FileNotFoundError from subprocess.run calls sys.exit(1)."""
        original_urls = run_sites.URLS
        original_argv = sys.argv
        try:
            run_sites.URLS = ["https://fail.com"]
            sys.argv = ["run_sites.py"]  # prevent pytest argv leak
            run_sites.main()
            mock_exit.assert_called_once_with(1)
        finally:
            run_sites.URLS = original_urls
            sys.argv = original_argv

    # ── Controller path ───────────────────────────────────────────────────────

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_controller_path_uses_controller_open(self, mock_sleep, _mock_wsl):
        """When a browser controller is available, it should be used."""
        mock_controller = MagicMock()
        with patch.object(webbrowser, "get", return_value=mock_controller):
            run_sites.main()
            expected_calls = [
                call("https://example.com", new=2),
                call("https://test.com", new=2),
            ]
            assert mock_controller.open.call_args_list == expected_calls

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_controller_not_found_falls_back_to_default(self, mock_sleep, _mock_wsl):
        """webbrowser.Error → falls back to webbrowser.open."""
        with patch.object(webbrowser, "get", side_effect=webbrowser.Error("not found")):
            with patch.object(webbrowser, "open") as mock_open:
                run_sites.main()
                expected_calls = [
                    call("https://example.com", new=2),
                    call("https://test.com", new=2),
                ]
                assert mock_open.call_args_list == expected_calls

    # ── Default path ──────────────────────────────────────────────────────────

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_default_path_uses_webbrowser_open(self, mock_sleep, _mock_wsl):
        """When no browser_name is given, use webbrowser.open directly."""
        # Override DEFAULT_BROWSER to None so no controller is attempted
        run_sites.DEFAULT_BROWSER = None
        try:
            with patch.object(webbrowser, "open") as mock_open:
                run_sites.main()
                expected_calls = [
                    call("https://example.com", new=2),
                    call("https://test.com", new=2),
                ]
                assert mock_open.call_args_list == expected_calls
        finally:
            run_sites.DEFAULT_BROWSER = "opera"

    # ── Error handling ────────────────────────────────────────────────────────

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_general_error_handled_continues_loop(self, mock_sleep, _mock_wsl):
        """Non-FileNotFoundError exceptions are caught; loop continues."""
        run_sites.DEFAULT_BROWSER = None
        try:
            mock_open = MagicMock(side_effect=[Exception("network error"), None])
            with patch.object(webbrowser, "open", mock_open):
                run_sites.main()
                # Both URLs were attempted
                assert mock_open.call_count == 2
        finally:
            run_sites.DEFAULT_BROWSER = "opera"

    # ── Browser override via sys.argv ─────────────────────────────────────────

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_browser_override_via_argv(self, mock_sleep, _mock_wsl):
        """sys.argv[1] overrides DEFAULT_BROWSER."""
        mock_controller = MagicMock()
        with patch.object(sys, "argv", ["run_sites.py", "chrome"]):
            with patch.object(webbrowser, "get", return_value=mock_controller) as mock_get:
                run_sites.main()
                mock_get.assert_called_once_with("chrome")
                assert mock_controller.open.call_count == 2


# ═══════════════════════════════════════════════════════════════════════════════
# main() flow — sys.argv, browser override, delay
# ═══════════════════════════════════════════════════════════════════════════════

class TestMainFlow:
    """Tests for main() orchestration and argument handling."""

    def setup_method(self):
        _reload_module(VALID_JSON)

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_no_browser_specified_uses_default(self, mock_sleep, _mock_wsl):
        """When no argv override and not WSL, uses DEFAULT_BROWSER (opera)."""
        mock_controller = MagicMock()
        with patch.object(webbrowser, "get", return_value=mock_controller) as mock_get:
            with patch.object(sys, "argv", ["run_sites.py"]):
                run_sites.main()
                mock_get.assert_called_once_with("opera")

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_wsl_takes_priority_over_controller(self, mock_sleep, _mock_wsl):
        """When WSL is detected, wsl-open is used regardless of browser arg."""
        with patch("run_sites.is_wsl", return_value=True):
            with patch("sys.exit"):
                with patch("subprocess.run") as mock_run:
                    run_sites.main()
                    # wsl-open is used, not webbrowser.get
                    assert any("wsl-open" in str(c) for c in mock_run.call_args_list)

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_delay_between_urls(self, mock_sleep, _mock_wsl):
        """time.sleep(delay) is called between each URL."""
        with patch.object(webbrowser, "open"):
            run_sites.main()
            # 2 URLs → 2 sleeps
            assert mock_sleep.call_count == 2
            mock_sleep.assert_called_with(1)  # delay = 1

    @patch("run_sites.is_wsl", return_value=False)
    @patch("time.sleep")
    def test_single_url_no_crash(self, mock_sleep, _mock_wsl):
        """One URL should work fine."""
        # Reload with single URL
        single_url_json = json.dumps({
            "default_browser": "opera",
            "social_media_urls": ["https://sole-site.com"],
        })
        _reload_module(single_url_json)
        mock_controller = MagicMock()
        with patch.object(webbrowser, "get", return_value=mock_controller):
            run_sites.main()
            mock_controller.open.assert_called_once_with("https://sole-site.com", new=2)
            assert mock_sleep.call_count == 1
