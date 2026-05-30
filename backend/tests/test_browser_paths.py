"""Tests for cross-platform browser path detection.

Tests browser path detection, user data directories, and launch arguments
across different operating systems.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.browser_paths import (
    BrowserPathDetector,
    get_browser_launch_args,
)
from app.core.platform_utils import OperatingSystem, PlatformDetector


class TestBrowserPathDetection:
    """Test browser executable path detection."""

    def test_get_chrome_path_current_os(self):
        """Chrome path detection should work on current OS."""
        # This test verifies the method runs without errors
        # Actual path existence depends on whether Chrome is installed
        chrome_path = BrowserPathDetector.get_chrome_path()

        # Should return either a Path or None
        assert chrome_path is None or isinstance(chrome_path, Path)

    def test_get_brave_path_current_os(self):
        """Brave path detection should work on current OS."""
        brave_path = BrowserPathDetector.get_brave_path()

        # Should return either a Path or None
        assert brave_path is None or isinstance(brave_path, Path)

    def test_chrome_path_macos(self):
        """Should return macOS Chrome path when on macOS."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.MACOS):
            with patch('pathlib.Path.exists', return_value=True):
                chrome_path = BrowserPathDetector.get_chrome_path()
                assert chrome_path is not None
                assert "Google Chrome.app" in str(chrome_path)
        PlatformDetector._cached_os = None

    def test_chrome_path_windows(self):
        """Should return Windows Chrome path when on Windows."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.WINDOWS):
            with patch('pathlib.Path.exists', side_effect=lambda: True):
                # Mock Path.exists() to return True for first path
                with patch.object(Path, 'exists', return_value=True):
                    chrome_path = BrowserPathDetector.get_chrome_path()
                    assert chrome_path is not None
                    assert "chrome.exe" in str(chrome_path).lower()
        PlatformDetector._cached_os = None

    def test_chrome_path_linux(self):
        """Should return Linux Chrome path when on Linux."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            with patch.object(Path, 'exists', return_value=True):
                chrome_path = BrowserPathDetector.get_chrome_path()
                assert chrome_path is not None
                assert "chrome" in str(chrome_path).lower()
        PlatformDetector._cached_os = None

    def test_brave_path_macos(self):
        """Should return macOS Brave path when on macOS."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.MACOS):
            with patch('pathlib.Path.exists', return_value=True):
                brave_path = BrowserPathDetector.get_brave_path()
                assert brave_path is not None
                assert "Brave Browser.app" in str(brave_path)
        PlatformDetector._cached_os = None

    def test_brave_path_windows(self):
        """Should return Windows Brave path when on Windows."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.WINDOWS):
            with patch.object(Path, 'exists', return_value=True):
                brave_path = BrowserPathDetector.get_brave_path()
                assert brave_path is not None
                assert "brave.exe" in str(brave_path).lower()
        PlatformDetector._cached_os = None

    def test_brave_path_linux(self):
        """Should return Linux Brave path when on Linux."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            with patch.object(Path, 'exists', return_value=True):
                brave_path = BrowserPathDetector.get_brave_path()
                assert brave_path is not None
                assert "brave" in str(brave_path).lower()
        PlatformDetector._cached_os = None

    def test_browser_not_found(self):
        """Should return None when browser is not installed."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.MACOS):
            with patch('pathlib.Path.exists', return_value=False):
                chrome_path = BrowserPathDetector.get_chrome_path()
                assert chrome_path is None

                brave_path = BrowserPathDetector.get_brave_path()
                assert brave_path is None
        PlatformDetector._cached_os = None


class TestBrowserUserDataDirectories:
    """Test browser user data directory detection."""

    def test_chrome_user_data_macos(self):
        """Should return macOS Chrome user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.MACOS):
            user_data = BrowserPathDetector.get_browser_user_data_dir("chrome")
            assert "Library/Application Support/Google/Chrome" in str(user_data)
        PlatformDetector._cached_os = None

    def test_chrome_user_data_windows(self):
        """Should return Windows Chrome user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.WINDOWS):
            user_data = BrowserPathDetector.get_browser_user_data_dir("chrome")
            assert "AppData" in str(user_data)
            assert "Google" in str(user_data)
            assert "Chrome" in str(user_data)
        PlatformDetector._cached_os = None

    def test_chrome_user_data_linux(self):
        """Should return Linux Chrome user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            user_data = BrowserPathDetector.get_browser_user_data_dir("chrome")
            assert ".config/google-chrome" in str(user_data)
        PlatformDetector._cached_os = None

    def test_brave_user_data_macos(self):
        """Should return macOS Brave user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.MACOS):
            user_data = BrowserPathDetector.get_browser_user_data_dir("brave")

            assert "BraveSoftware" in str(user_data)
        PlatformDetector._cached_os = None

    def test_brave_user_data_windows(self):
        """Should return Windows Brave user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.WINDOWS):
            user_data = BrowserPathDetector.get_browser_user_data_dir("brave")
            assert "AppData" in str(user_data)
            assert "BraveSoftware" in str(user_data)
        PlatformDetector._cached_os = None

    def test_brave_user_data_linux(self):
        """Should return Linux Brave user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            user_data = BrowserPathDetector.get_browser_user_data_dir("brave")
            assert ".config/BraveSoftware" in str(user_data)
        PlatformDetector._cached_os = None

    def test_unknown_browser_raises_error(self):
        """Should raise ValueError for unknown browser."""
        with pytest.raises(ValueError) as exc_info:
            BrowserPathDetector.get_browser_user_data_dir("firefox")

        assert "Unknown browser" in str(exc_info.value)


class TestBrowserFindAndDetection:
    """Test browser finding and detection utilities."""

    def test_find_browser_prefers_brave(self):
        """Should prefer Brave when it's available."""
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=Path("/usr/bin/brave")):
            with patch.object(BrowserPathDetector, 'get_chrome_path', return_value=Path("/usr/bin/chrome")):
                result = BrowserPathDetector.find_browser("brave")
                assert result is not None
                path, name = result
                assert name == "brave"
                assert "brave" in str(path).lower()

    def test_find_browser_fallback_to_chrome(self):
        """Should fallback to Chrome when Brave is not available."""
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=None):
            with patch.object(BrowserPathDetector, 'get_chrome_path', return_value=Path("/usr/bin/chrome")):
                result = BrowserPathDetector.find_browser("brave")
                assert result is not None
                path, name = result
                assert name == "chrome"

    def test_find_browser_none_when_no_browsers(self):
        """Should return None when no browsers are available."""
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=None):
            with patch.object(BrowserPathDetector, 'get_chrome_path', return_value=None):
                result = BrowserPathDetector.find_browser("brave")
                assert result is None

    def test_get_all_installed_browsers(self):
        """Should return list of all installed browsers."""
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=Path("/usr/bin/brave")):
            with patch.object(BrowserPathDetector, 'get_chrome_path', return_value=Path("/usr/bin/chrome")):
                browsers = BrowserPathDetector.get_all_installed_browsers()
                assert len(browsers) == 2

                names = [name for name, _ in browsers]
                assert "chrome" in names
                assert "brave" in names

    def test_get_all_installed_browsers_empty(self):
        """Should return empty list when no browsers installed."""
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=None):
            with patch.object(BrowserPathDetector, 'get_chrome_path', return_value=None):
                browsers = BrowserPathDetector.get_all_installed_browsers()
                assert browsers == []

    def test_is_browser_installed_true(self):
        """Should return True when browser is installed."""
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=Path("/usr/bin/brave")):
            assert BrowserPathDetector.is_browser_installed("brave") is True

    def test_is_browser_installed_false(self):
        """Should return False when browser is not installed."""
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=None):
            assert BrowserPathDetector.is_browser_installed("brave") is False

    def test_is_browser_installed_unknown_raises(self):
        """Should raise ValueError for unknown browser."""
        with pytest.raises(ValueError):
            BrowserPathDetector.is_browser_installed("firefox")


class TestBrowserLaunchArgs:
    """Test browser launch argument generation."""

    def test_get_browser_launch_args_default(self):
        """Should generate default launch args."""
        args = get_browser_launch_args("brave", 9223)

        assert "--remote-debugging-port=9223" in args
        assert "--no-first-run" in args
        assert "--no-default-browser-check" in args
        assert any("user-data-dir" in arg for arg in args)

    def test_get_browser_launch_args_custom_user_data(self):
        """Should use custom user data directory."""
        custom_dir = Path("/custom/data/dir")
        args = get_browser_launch_args("brave", 9223, custom_dir)

        assert f"--user-data-dir={custom_dir}" in args

    def test_get_browser_launch_args_headless(self):
        """Should include headless flag when requested."""
        args = get_browser_launch_args("brave", 9223, headless=True)

        assert "--headless" in args

    def test_get_browser_launch_args_no_headless(self):
        """Should not include headless flag by default."""
        args = get_browser_launch_args("brave", 9223, headless=False)

        assert "--headless" not in args

    def test_get_browser_launch_args_custom_port(self):
        """Should use custom CDP port."""
        args = get_browser_launch_args("brave", 9999)

        assert "--remote-debugging-port=9999" in args
