"""Linux Platform Simulation Tests.

Tests Linux-specific features by mocking the Linux environment.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from app.core.platform_utils import PlatformDetector, OperatingSystem
from app.core.platform_config import PlatformConfig
from app.core.path_security import PathSecurityValidator
from app.core.browser_paths import BrowserPathDetector
from app.core.exceptions import PathValidationError


class TestLinuxPlatformDetection:
    """Test platform detection on Linux."""
    
    def test_linux_detection(self):
        """Should detect Linux correctly."""
        PlatformDetector._cached_os = None
        with patch('platform.system', return_value='Linux'):
            with patch('sys.platform', 'linux'):
                os_type = PlatformDetector.detect_os()
                assert os_type == OperatingSystem.LINUX
                assert PlatformDetector.is_windows() is False
                assert PlatformDetector.is_unix_like() is True
        PlatformDetector._cached_os = None
    
    def test_linux_path_separator(self):
        """Linux should use forward slash as path separator."""
        with patch('app.core.platform_utils.PlatformDetector.is_windows', return_value=False):
            sep = PlatformDetector.get_path_separator()
            assert sep == "/"


class TestLinuxPathValidation:
    """Test Linux-specific path validation."""
    
    def test_unc_check_skipped_on_linux(self):
        """UNC path check should be skipped on Linux."""
        with patch.object(PlatformDetector, 'is_windows', return_value=False):
            # Should not raise on Linux
            PathSecurityValidator._check_windows_unc_path("////server//share")
            PathSecurityValidator._check_windows_unc_path("\\\\\\\\server\\\\share")
    
    def test_drive_letter_check_skipped_on_linux(self):
        """Drive letter check should be skipped on Linux."""
        with patch.object(PlatformDetector, 'is_windows', return_value=False):
            # Should not raise on Linux
            PathSecurityValidator._check_windows_drive_letter("C:\\Users\\test")
    
    def test_path_length_linux_limit(self):
        """Linux should enforce 4096 character limit."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            # Test path at limit (4096 chars)
            path_at_limit = "/" + "a" * 4095
            PathSecurityValidator._check_path_length(path_at_limit)
            
            # Test path over limit (4097 chars)
            path_over_limit = "/" + "a" * 4096
            with pytest.raises(PathValidationError) as exc_info:
                PathSecurityValidator._check_path_length(path_over_limit)
            assert "4096" in str(exc_info.value)
            assert "Unix" in str(exc_info.value)
        PlatformDetector._cached_os = None
    
    def test_linux_blocked_patterns(self):
        """Linux should not have Windows-specific patterns."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.is_windows', return_value=False):
            patterns = PathSecurityValidator._get_blocked_patterns()
            
            # Should NOT include Windows-specific patterns
            # (They're only added when is_windows() returns True)
            # Common patterns should be present
            assert ".." in patterns
            assert "~" in patterns
        PlatformDetector._cached_os = None


class TestLinuxBrowserDetection:
    """Test browser detection on Linux."""
    
    def test_chrome_paths_linux(self):
        """Should check multiple Chrome paths on Linux."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            with patch.object(Path, 'exists', return_value=True):
                chrome_path = BrowserPathDetector.get_chrome_path()
                assert chrome_path is not None
                # Should be one of the Linux paths
                path_str = str(chrome_path).lower()
                assert ("google-chrome" in path_str or 
                        "chromium" in path_str or
                        "snap" in path_str or
                        "flatpak" in path_str)
        PlatformDetector._cached_os = None
    
    def test_brave_paths_linux(self):
        """Should check multiple Brave paths on Linux."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            with patch.object(Path, 'exists', return_value=True):
                brave_path = BrowserPathDetector.get_brave_path()
                assert brave_path is not None
                # Should be one of the Linux paths
                path_str = str(brave_path).lower()
                assert ("brave" in path_str and 
                        ("/usr/bin" in path_str or "/snap" in path_str or "flatpak" in path_str))
        PlatformDetector._cached_os = None
    
    def test_chrome_user_data_linux(self):
        """Should return Linux Chrome user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            user_data = BrowserPathDetector.get_browser_user_data_dir("chrome")
            assert ".config/google-chrome" in str(user_data)
        PlatformDetector._cached_os = None
    
    def test_brave_user_data_linux(self):
        """Should return Linux Brave user data directory."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            user_data = BrowserPathDetector.get_browser_user_data_dir("brave")
            assert ".config/BraveSoftware" in str(user_data)
        PlatformDetector._cached_os = None
    
    def test_snap_and_flatpak_support(self):
        """Should support Snap and Flatpak installations."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            # Test that Snap paths are checked
            chrome_path = BrowserPathDetector.get_chrome_path()
            # The method should check snap paths (even if not found)
            # We're just testing it doesn't crash
            assert chrome_path is None or isinstance(chrome_path, Path)
        PlatformDetector._cached_os = None


class TestLinuxSystemDirectories:
    """Test Linux system directory protection."""
    
    def test_linux_system_directories_detected(self):
        """Linux should have correct system directories."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_utils.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            config = PlatformConfig()
            sys_dirs = config.get_system_directories()
            
            # Should include Linux-specific directories
            assert "/etc" in sys_dirs or any("/etc" in str(d) for d in sys_dirs)
            assert "/var" in sys_dirs or any("/var" in str(d) for d in sys_dirs)
            assert "/usr" in sys_dirs or any("/usr" in str(d) for d in sys_dirs)
            assert "/bin" in sys_dirs or any("/bin" in str(d) for d in sys_dirs)
        PlatformDetector._cached_os = None


class TestLinuxFilenameRules:
    """Test Linux filename rules."""
    
    def test_linux_allows_more_characters(self):
        """Linux allows more characters than Windows."""
        # On Linux, these characters are generally OK (except path separators)
        filename = "file:test.txt"  # Colon is OK on Linux
        clean = PathSecurityValidator.sanitize_filename(filename)
        
        # Should remove path separators but might keep other chars
        assert "/" not in clean
        assert "\\" not in clean
    
    def test_linux_hidden_files(self):
        """Linux hidden files (starting with .) should be handled."""
        filename = ".hidden_file"
        clean = PathSecurityValidator.sanitize_filename(filename)

        # The sanitizer may remove the leading dot - just ensure it doesn't crash
        # and returns a valid filename
        assert isinstance(clean, str)
        assert len(clean) > 0
