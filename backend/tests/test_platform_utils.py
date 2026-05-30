"""Tests for cross-platform utilities.

This module tests the platform detection and OS-specific configuration logic
to ensure it works correctly across Windows, macOS, and Linux.
"""

import pytest
from unittest.mock import patch
from pathlib import Path

# Import the modules to test
try:
    from backend.app.core.platform_utils import PlatformDetector, OperatingSystem
    from backend.app.core.platform_config import PlatformConfig
except ModuleNotFoundError:
    from app.core.platform_utils import PlatformDetector, OperatingSystem
    from app.core.platform_config import PlatformConfig


class TestPlatformDetector:
    """Test platform detection logic."""
    
    def test_detect_os_returns_valid_enum(self):
        """Platform detection should return a valid OperatingSystem enum."""
        os_type = PlatformDetector.detect_os()
        assert isinstance(os_type, OperatingSystem)
        assert os_type in [
            OperatingSystem.WINDOWS,
            OperatingSystem.MACOS,
            OperatingSystem.LINUX,
            OperatingSystem.UNKNOWN,
        ]
    
    def test_os_detection_is_cached(self):
        """Platform detection should cache results."""
        # First call
        os_type_1 = PlatformDetector.detect_os()
        # Second call should return cached value
        os_type_2 = PlatformDetector.detect_os()
        assert os_type_1 == os_type_2
        assert PlatformDetector._cached_os is not None
    
    @patch('platform.system', return_value='Windows')
    @patch('sys.platform', 'win32')
    def test_windows_detection(self, mock_system):
        """Test Windows detection."""
        PlatformDetector._cached_os = None  # Reset cache
        assert PlatformDetector.is_windows()
        assert not PlatformDetector.is_macos()
        assert not PlatformDetector.is_linux()
        assert not PlatformDetector.is_unix_like()
        assert PlatformDetector.detect_os() == OperatingSystem.WINDOWS
    
    @patch('platform.system', return_value='Darwin')
    def test_macos_detection(self, mock_system):
        """Test macOS detection."""
        PlatformDetector._cached_os = None  # Reset cache
        assert PlatformDetector.is_macos()
        assert not PlatformDetector.is_windows()
        assert not PlatformDetector.is_linux()
        assert PlatformDetector.is_unix_like()
        assert PlatformDetector.detect_os() == OperatingSystem.MACOS
    
    @patch('platform.system', return_value='Linux')
    def test_linux_detection(self, mock_system):
        """Test Linux detection."""
        PlatformDetector._cached_os = None  # Reset cache
        assert PlatformDetector.is_linux()
        assert not PlatformDetector.is_windows()
        assert not PlatformDetector.is_macos()
        assert PlatformDetector.is_unix_like()
        assert PlatformDetector.detect_os() == OperatingSystem.LINUX
    
    def test_path_separator_windows(self):
        """Test path separator on Windows."""
        with patch.object(PlatformDetector, 'is_windows', return_value=True):
            assert PlatformDetector.get_path_separator() == '\\'
    
    def test_path_separator_unix(self):
        """Test path separator on Unix-like systems."""
        with patch.object(PlatformDetector, 'is_windows', return_value=False):
            assert PlatformDetector.get_path_separator() == '/'
    
    def test_normalize_path_windows(self):
        """Test path normalization on Windows."""
        with patch.object(PlatformDetector, 'is_windows', return_value=True):
            # Should convert / to \
            result = PlatformDetector.normalize_path("folder/subfolder/file.txt")
            assert result == "folder\\subfolder\\file.txt"
    
    def test_normalize_path_unix(self):
        """Test path normalization on Unix."""
        with patch.object(PlatformDetector, 'is_windows', return_value=False):
            # Should convert \ to /
            result = PlatformDetector.normalize_path("folder\\subfolder\\file.txt")
            assert result == "folder/subfolder/file.txt"


class TestPlatformConfig:
    """Test platform-specific configurations."""
    
    def test_system_directories_windows(self):
        """Test Windows system directories."""
        with patch.object(PlatformDetector, 'detect_os', return_value=OperatingSystem.WINDOWS):
            dirs = PlatformConfig.get_system_directories()
            
            # Check Windows-specific directories
            assert "C:\\Windows" in dirs
            assert "C:\\Program Files" in dirs
            assert "C:\\Program Files (x86)" in dirs
            
            # Check common directories
            assert str(Path.home() / ".ssh") in dirs
    
    def test_system_directories_macos(self):
        """Test macOS system directories."""
        with patch.object(PlatformDetector, 'detect_os', return_value=OperatingSystem.MACOS):
            dirs = PlatformConfig.get_system_directories()
            
            # Check macOS-specific directories
            assert "/System" in dirs
            assert "/usr" in dirs
            assert "/private/etc" in dirs
            
            # Check common directories
            assert str(Path.home() / ".ssh") in dirs
    
    def test_system_directories_linux(self):
        """Test Linux system directories."""
        with patch.object(PlatformDetector, 'detect_os', return_value=OperatingSystem.LINUX):
            dirs = PlatformConfig.get_system_directories()
            
            # Check Linux-specific directories
            assert "/etc" in dirs
            assert "/var" in dirs
            assert "/usr" in dirs
            assert "/boot" in dirs
            
            # Check common directories
            assert str(Path.home() / ".ssh") in dirs
    
    def test_home_directory(self):
        """Test home directory detection."""
        home = PlatformConfig.get_home_directory()
        assert isinstance(home, Path)
        assert home.is_absolute()
        assert home.exists()
    
    def test_temp_directory(self):
        """Test temporary directory detection."""
        temp = PlatformConfig.get_temp_directory()
        assert isinstance(temp, Path)
        assert temp.is_absolute()
        # Temp directory should exist
        assert temp.exists()
    
    def test_os_name(self):
        """Test OS name retrieval."""
        os_name = PlatformConfig.get_os_name()
        assert os_name in ["Windows", "macOS", "Linux", "Unknown"]
        assert isinstance(os_name, str)


class TestPlatformIntegration:
    """Integration tests for platform detection on current OS."""
    
    def test_current_os_detected(self):
        """Test that current OS is detected correctly."""
        os_type = PlatformDetector.detect_os()
        # Should detect a known OS (not UNKNOWN)
        assert os_type != OperatingSystem.UNKNOWN
    
    def test_system_directories_not_empty(self):
        """Test that system directories are populated."""
        dirs = PlatformConfig.get_system_directories()
        # Should have at least the common directories
        assert len(dirs) > 0
    
    def test_path_separator_matches_os(self):
        """Test that path separator matches detected OS."""
        sep = PlatformDetector.get_path_separator()
        if PlatformDetector.is_windows():
            assert sep == '\\'
        else:
            assert sep == '/'
