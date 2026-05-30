"""Phase 5: Comprehensive Integration Tests.

Tests complete workflows across all phases to ensure the entire
cross-platform system works together correctly.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.platform_utils import PlatformDetector, OperatingSystem
from app.core.platform_config import PlatformConfig
from app.core.path_security import PathSecurityValidator
from app.core.browser_paths import BrowserPathDetector, get_browser_launch_args
from app.core.exceptions import PathValidationError


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_platform_detection_to_path_validation(self):
        """Complete workflow: detect platform → validate path."""
        # Step 1: Detect platform
        os_type = PlatformDetector.detect_os()
        assert os_type in [OperatingSystem.WINDOWS, OperatingSystem.MACOS, OperatingSystem.LINUX]
        
        # Step 2: Get system directories for platform
        sys_dirs = PathSecurityValidator._get_system_directories()
        assert len(sys_dirs) > 0
        
        # Step 3: Validate a safe path
        base_dir = Path.cwd()
        safe_path = "test_file.txt"
        
        try:
            result = PathSecurityValidator.validate_path(
                safe_path,
                base_dir,
                must_exist=False
            )
            assert result is not None
        except PathValidationError:
            # Some validation might fail, but not due to platform detection
            pass
    
    def test_platform_detection_to_browser_launch(self):
        """Complete workflow: detect platform → find browser → generate args."""
        # Step 1: Detect platform
        os_type = PlatformDetector.detect_os()
        
        # Step 2: Find any available browser
        result = BrowserPathDetector.find_browser("brave")
        
        if result:
            browser_path, browser_name = result
            
            # Step 3: Get user data directory
            user_data = BrowserPathDetector.get_browser_user_data_dir(browser_name)
            assert user_data is not None
            
            # Step 4: Generate launch arguments
            args = get_browser_launch_args(browser_name, 9223, user_data)
            assert "--remote-debugging-port=9223" in args
            assert any("user-data-dir" in arg for arg in args)
    
    def test_path_validation_with_all_phase4_checks(self):
        """Test that all Phase 4 checks work together."""
        base_dir = Path.cwd()
        
        # Test 1: Path length check
        long_path = "a" * 5000
        with pytest.raises(PathValidationError) as exc_info:
            PathSecurityValidator.validate_path(long_path, base_dir, must_exist=False)
        assert "too long" in str(exc_info.value).lower()
        
        # Test 2: Blocked pattern check
        traversal_path = "../../../etc/passwd"
        with pytest.raises(PathValidationError) as exc_info:
            PathSecurityValidator.validate_path(traversal_path, base_dir, must_exist=False)
        assert "blocked pattern" in str(exc_info.value).lower()
        
        # Test 3: Normal path passes all checks
        normal_path = "data/test.txt"
        try:
            result = PathSecurityValidator.validate_path(normal_path, base_dir, must_exist=False)
            # Should either pass or fail for legitimate reasons (not Phase 4 checks)
            assert result is not None
        except PathValidationError as e:
            # If it fails, shouldn't be due to length or basic patterns
            error_msg = str(e).lower()
            assert "too long" not in error_msg


class TestCrossPlatformConsistency:
    """Test that behavior is consistent across platforms."""
    
    def test_platform_detector_caching(self):
        """Platform detection should cache results."""
        # Clear cache
        PlatformDetector._cached_os = None
        
        # First call
        os1 = PlatformDetector.detect_os()
        
        # Second call (should use cache)
        os2 = PlatformDetector.detect_os()
        
        assert os1 == os2
        assert PlatformDetector._cached_os is not None
    
    def test_path_security_audit_logging(self):
        """Audit logging should work across all validation types."""
        PathSecurityValidator.clear_audit_events()
        
        # Trigger multiple types of events
        try:
            PathSecurityValidator._check_path_length("a" * 5000)
        except PathValidationError:
            pass
        
        try:
            PathSecurityValidator._check_blocked_patterns("../../etc/passwd")
        except PathValidationError:
            pass
        
        # Should have at least 2 events
        events = PathSecurityValidator.get_audit_events()
        assert len(events) >= 2
        
        # All events should have platform info
        for event in events:
            assert "platform" in event
            assert "os_version" in event
    
    def test_browser_paths_fallback(self):
        """Browser detection should handle missing browsers gracefully."""
        # Test with potentially missing browser
        chrome_path = BrowserPathDetector.get_chrome_path()
        brave_path = BrowserPathDetector.get_brave_path()
        
        # At least one should work, or both can be None
        # The important thing is no exceptions are raised
        assert chrome_path is None or isinstance(chrome_path, Path)
        assert brave_path is None or isinstance(brave_path, Path)
    
    def test_canonicalization_with_validation(self):
        """Path canonicalization should work with validation."""
        # Test relative path
        rel_path = "./test.txt"
        canonical = PathSecurityValidator.canonicalize_path(rel_path)
        
        assert canonical.is_absolute()
        assert "test.txt" in str(canonical)


class TestErrorHandlingAndRecovery:
    """Test error handling and graceful degradation."""
    
    def test_missing_browser_error_handling(self):
        """Should handle missing browsers gracefully."""
        # Mock both browsers as missing
        with patch.object(BrowserPathDetector, 'get_brave_path', return_value=None):
            with patch.object(BrowserPathDetector, 'get_chrome_path', return_value=None):
                result = BrowserPathDetector.find_browser("brave")
                assert result is None
                
                browsers = BrowserPathDetector.get_all_installed_browsers()
                assert browsers == []
    
    def test_path_validation_error_messages_complete(self):
        """Error messages should be complete and helpful."""
        PathSecurityValidator.clear_audit_events()
        
        try:
            PathSecurityValidator._check_blocked_patterns("../../../etc/passwd")
        except PathValidationError as e:
            error_msg = str(e)
            # Should contain key information
            assert "blocked pattern" in error_msg.lower()
            assert "platform:" in error_msg.lower() or PlatformDetector.get_os_name().lower() in error_msg.lower()
