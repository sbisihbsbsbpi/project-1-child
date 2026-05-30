"""Tests for cross-platform path security enhancements.

This module tests the platform-aware features of PathSecurityValidator
to ensure it adapts correctly to Windows, macOS, and Linux.
"""

import pytest
from unittest.mock import patch
from pathlib import Path

# Import the modules to test
try:
    from backend.app.core.path_security import PathSecurityValidator
    from backend.app.core.platform_utils import PlatformDetector, OperatingSystem
    from backend.app.core.exceptions import PathValidationError
except ModuleNotFoundError:
    from app.core.path_security import PathSecurityValidator
    from app.core.platform_utils import PlatformDetector, OperatingSystem
    from app.core.exceptions import PathValidationError


class TestPlatformAwareBlockedPatterns:
    """Test platform-specific blocked patterns."""

    def test_common_patterns_all_platforms(self):
        """Common patterns should be blocked on all platforms."""
        patterns = PathSecurityValidator._get_blocked_patterns()

        # These should always be present
        assert ".." in patterns
        assert "~" in patterns
        assert "\x00" in patterns
        assert "%00" in patterns

    def test_windows_specific_patterns(self):
        """Windows should have additional blocked patterns."""
        with patch.object(PlatformDetector, 'is_windows', return_value=True):
            # Reset cache to ensure detect_os is called
            PlatformDetector._cached_os = None
            with patch.object(PlatformDetector, 'detect_os', return_value=OperatingSystem.WINDOWS):
                patterns = PathSecurityValidator._get_blocked_patterns()

                # Windows-specific patterns
                assert "\\\\" in patterns
                assert "C:" in patterns
                assert "D:" in patterns
            # Reset cache after test
            PlatformDetector._cached_os = None

    def test_unix_patterns_no_windows_extras(self):
        """Unix systems should not have Windows-specific patterns."""
        with patch.object(PlatformDetector, 'is_windows', return_value=False):
            with patch.object(PlatformDetector, 'detect_os', return_value=OperatingSystem.LINUX):
                patterns = PathSecurityValidator._get_blocked_patterns()

                # Should not have Windows-specific patterns
                assert "C:" not in patterns
                assert "D:" not in patterns


class TestPlatformAwareSystemDirectories:
    """Test platform-specific system directories."""

    def test_system_directories_dynamic(self):
        """System directories should be retrieved dynamically."""
        sys_dirs = PathSecurityValidator._get_system_directories()

        # Should have directories
        assert len(sys_dirs) > 0

        # Should be strings
        assert all(isinstance(d, str) for d in sys_dirs)

    def test_system_directories_windows(self):
        """Windows system directories should be protected."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_config.PlatformDetector.detect_os', return_value=OperatingSystem.WINDOWS):
            sys_dirs = PathSecurityValidator._get_system_directories()

            # Windows-specific directories
            assert "C:\\Windows" in sys_dirs
            assert "C:\\Program Files" in sys_dirs
        PlatformDetector._cached_os = None

    def test_system_directories_macos(self):
        """macOS system directories should be protected."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_config.PlatformDetector.detect_os', return_value=OperatingSystem.MACOS):
            sys_dirs = PathSecurityValidator._get_system_directories()

            # macOS-specific directories
            assert "/System" in sys_dirs
            assert "/usr" in sys_dirs
        PlatformDetector._cached_os = None

    def test_system_directories_linux(self):
        """Linux system directories should be protected."""
        PlatformDetector._cached_os = None
        with patch('app.core.platform_config.PlatformDetector.detect_os', return_value=OperatingSystem.LINUX):
            sys_dirs = PathSecurityValidator._get_system_directories()

            # Linux-specific directories
            assert "/etc" in sys_dirs
            assert "/var" in sys_dirs
            assert "/boot" in sys_dirs
        PlatformDetector._cached_os = None


class TestCrossPlatformFilenameSanitization:
    """Test cross-platform filename sanitization."""

    def test_sanitize_path_separators(self):
        """Path separators should be removed on all platforms."""
        result = PathSecurityValidator.sanitize_filename("folder/file.txt")
        assert "/" not in result

        result = PathSecurityValidator.sanitize_filename("folder\\file.txt")
        assert "\\" not in result

    def test_sanitize_null_bytes(self):
        """Null bytes should be removed."""
        result = PathSecurityValidator.sanitize_filename("file\x00.exe")
        assert "\x00" not in result
        assert result == "file.exe"

    def test_sanitize_windows_reserved_chars(self):
        """Windows reserved characters should be removed on Windows."""
        with patch.object(PlatformDetector, 'is_windows', return_value=True):
            result = PathSecurityValidator.sanitize_filename("file<>:\"|?.txt")

            # Windows reserved chars should be replaced
            assert "<" not in result
            assert ">" not in result
            assert ":" not in result
            assert "|" not in result

    def test_sanitize_windows_reserved_names(self):
        """Windows reserved names should be prefixed."""
        PlatformDetector._cached_os = None
        with patch.object(PlatformDetector, 'is_windows', return_value=True):
            with patch.object(PlatformDetector, 'detect_os', return_value=OperatingSystem.WINDOWS):
                # Test reserved device names
                result = PathSecurityValidator.sanitize_filename("CON.txt")
                assert result.startswith("_")

                result = PathSecurityValidator.sanitize_filename("PRN.log")
                assert result.startswith("_")

                result = PathSecurityValidator.sanitize_filename("AUX")
                assert result.startswith("_")
        PlatformDetector._cached_os = None

    def test_sanitize_unix_hidden_files(self):
        """Hidden files (starting with .) should be handled on Unix."""
        with patch.object(PlatformDetector, 'is_windows', return_value=False):
            result = PathSecurityValidator.sanitize_filename(".hidden")
            # On Unix, leading dot is removed
            assert not result.startswith(".")


class TestAuditLoggingWithPlatformInfo:
    """Test that audit logging includes platform information."""

    def setup_method(self):
        """Clear audit events before each test."""
        PathSecurityValidator.clear_audit_events()

    def test_audit_events_include_platform(self):
        """Audit events should automatically include platform information."""
        # Trigger a security event by trying to access a blocked pattern
        with pytest.raises(PathValidationError):
            PathSecurityValidator._check_blocked_patterns("../../etc/passwd")

        # Get audit events
        events = PathSecurityValidator.get_audit_events(limit=1)
        assert len(events) > 0

        event = events[0]
        # Platform info should be automatically added
        assert "platform" in event
        assert "os_version" in event
        assert event["platform"] in ["windows", "macos", "linux", "unknown"]

    def test_audit_events_include_os_version(self):
        """Audit events should include OS version."""
        # Trigger another security event
        with pytest.raises(PathValidationError):
            PathSecurityValidator._check_null_bytes("file\x00.txt")

        events = PathSecurityValidator.get_audit_events(limit=1)
        event = events[0]

        assert "os_version" in event
        assert isinstance(event["os_version"], str)
        assert len(event["os_version"]) > 0


class TestCrossPlatformIntegration:
    """Integration tests for cross-platform path security."""

    def test_system_directory_validation_current_os(self):
        """System directory validation should work on current OS."""
        home = Path.home()

        # SSH directory should be protected
        ssh_dir = home / ".ssh"

        # Should raise error when trying to access system directory
        with pytest.raises(PathValidationError) as exc_info:
            PathSecurityValidator._check_system_directory(ssh_dir)

        assert "system directory" in str(exc_info.value).lower()

    def test_blocked_patterns_on_current_os(self):
        """Blocked patterns should work on current OS."""
        PathSecurityValidator.clear_audit_events()

        # Path traversal should be blocked
        with pytest.raises(PathValidationError) as exc_info:
            PathSecurityValidator._check_blocked_patterns("../../etc/passwd")

        assert "blocked pattern" in str(exc_info.value).lower()

    def test_filename_sanitization_current_os(self):
        """Filename sanitization should work on current OS."""
        # Should handle various dangerous characters
        dirty_filename = "../../../etc/passwd"
        clean = PathSecurityValidator.sanitize_filename(dirty_filename)

        # Should not contain path separators
        assert "/" not in clean
        assert "\\" not in clean
        assert ".." not in clean

    def test_audit_logging_includes_platform_current_os(self):
        """Audit logging should include current platform info."""
        PathSecurityValidator.clear_audit_events()

        # Trigger an event
        with pytest.raises(PathValidationError):
            PathSecurityValidator._check_blocked_patterns("~/.ssh/id_rsa")

        events = PathSecurityValidator.get_audit_events()
        assert len(events) > 0

        # Platform should match current OS
        event = events[0]
        current_os = PlatformDetector.detect_os().value
        assert event["platform"] == current_os


class TestBackwardCompatibility:
    """Test that cross-platform changes don't break existing functionality."""

    def test_extension_validation_still_works(self):
        """Extension validation should still work as before."""
        # Test valid extension
        test_path = Path("test.png")
        allowed = {".png", ".jpg"}

        # Should not raise exception
        PathSecurityValidator._check_extension(test_path, allowed)

    def test_symlink_checking_still_works(self):
        """Symlink checking should still work."""
        # This should work without errors (using current directory)
        base = Path.cwd()
        path = base / "test.txt"

        # Should not raise exception for non-symlink
        try:
            PathSecurityValidator._check_symlinks(path, base)
        except Exception as e:
            # Only PathValidationError related to symlinks is expected
            if "symlink" not in str(e).lower():
                raise

    def test_audit_summary_still_works(self):
        """Audit summary should still work with enhanced events."""
        PathSecurityValidator.clear_audit_events()

        # Add some events
        PathSecurityValidator._log_security_event(
            event_type="test_event",
            path="/test/path",
            reason="Test reason",
            severity="info"
        )

        summary = PathSecurityValidator.get_audit_summary()

        assert "total_events" in summary
        assert summary["total_events"] >= 1
        assert "by_type" in summary
        assert "by_severity" in summary
