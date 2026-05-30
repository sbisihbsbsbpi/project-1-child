"""Path security utilities for preventing path traversal attacks.

This module provides centralized path validation and sanitization to prevent:
- Path traversal attacks (../../etc/passwd)
- Directory escape attempts
- Symlink-based attacks
- System directory access
- Null byte injection
- Double extension bypasses
- Arbitrary file creation

All file system operations should use this module for path validation.

Cross-Platform Support:
- Automatic OS detection (Windows, macOS, Linux)
- Platform-specific system directory protection
- OS-aware path pattern blocking
- Dynamic configuration based on detected platform
"""

from __future__ import annotations

import os
import re
import logging
import platform
from pathlib import Path
from typing import Optional, List, Set, Dict, Any
from datetime import datetime
from app.core.exceptions import PathValidationError
from app.core.platform_utils import PlatformDetector, OperatingSystem
from app.core.platform_config import PlatformConfig

# Get logger for security audit events
logger = logging.getLogger(__name__)


class PathSecurityValidator:
    """Centralized path validation and security checks.

    This class provides static methods for validating file paths to prevent
    various security attacks. All path operations in the application should
    use these validators.
    """

    # Allowed base directories for file operations
    ALLOWED_BASES = {
        "screenshots": Path("screenshots").resolve(),
        "browser_sessions": Path("browser_sessions").resolve(),
        "logs": Path("logs").resolve(),
        "config": Path.cwd(),  # Project root for config files
    }

    # Blocked path patterns (common to all platforms)
    BLOCKED_PATTERNS_COMMON = [
        "..",      # Parent directory traversal
        "~",       # Home expansion (after initial expansion)
        "//",      # Double slash
        "\x00",    # Null byte injection
        "%00",     # URL-encoded null byte
        "...",     # Triple dot
        "/..",     # Root parent
        "/.",      # Root current
    ]

    # Platform-specific blocked patterns (added dynamically)
    BLOCKED_PATTERNS_WINDOWS = [
        "\\\\",    # Double backslash
        "C:",      # Drive letter manipulation (C:, D:, etc.)
        "D:",
        "E:",
        "\\\\?\\", # Windows extended path prefix
        "//",      # UNC path prefix
    ]

    # Path length limits per platform
    MAX_PATH_LENGTH_WINDOWS = 260  # Traditional MAX_PATH (can be 32,767 with extended paths)
    MAX_PATH_LENGTH_UNIX = 4096    # Typical Unix/Linux PATH_MAX

    @classmethod
    def _get_platform_context(cls) -> str:
        """Get current platform context for error messages.

        Returns:
            Platform name string (e.g., "Windows", "macOS", "Linux")
        """
        os_type = PlatformDetector.detect_os()
        return os_type.value.capitalize()

    @classmethod
    def _get_blocked_patterns(cls) -> List[str]:
        """Get blocked patterns for the current platform.

        Returns:
            List of path patterns to block
        """
        patterns = cls.BLOCKED_PATTERNS_COMMON.copy()

        # Add Windows-specific patterns
        if PlatformDetector.is_windows():
            patterns.extend(cls.BLOCKED_PATTERNS_WINDOWS)

        return patterns

    @classmethod
    def _get_system_directories(cls) -> Set[str]:
        """Get protected system directories for the current platform.

        Uses PlatformConfig to dynamically determine system directories
        based on the detected operating system.

        Returns:
            Set of system directory paths that should be protected
        """
        return PlatformConfig.get_system_directories()

    # Allowed file extensions for screenshots
    SCREENSHOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".gif", ".bmp"}

    # Allowed file extensions for configs
    CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini"}

    # Blocked file extensions (executables and scripts)
    BLOCKED_EXTENSIONS = {
        ".exe", ".bat", ".cmd", ".com", ".pif", ".scr",  # Windows executables
        ".sh", ".bash", ".zsh", ".fish", ".csh",  # Unix shells
        ".py", ".pyc", ".pyo", ".pyw",  # Python (except in specific contexts)
        ".js", ".jsx", ".ts", ".tsx",  # JavaScript/TypeScript
        ".php", ".asp", ".aspx", ".jsp",  # Server-side scripts
        ".pl", ".rb", ".lua",  # Other scripts
        ".app", ".dmg", ".pkg",  # macOS executables
        ".deb", ".rpm",  # Linux packages
        ".msi", ".dll", ".so", ".dylib",  # Libraries
    }

    # ✅ PHASE 4: Extension policies per directory
    EXTENSION_POLICIES = {
        "screenshots": {
            "allowed": {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".gif", ".bmp"},
            "description": "Screenshot and image files",
        },
        "browser_sessions": {
            "allowed": {".json"},
            "description": "Browser session data (JSON only)",
        },
        "logs": {
            "allowed": {".log", ".txt"},
            "description": "Log files",
        },
        "config": {
            "allowed": {".json", ".yaml", ".yml", ".toml", ".ini"},
            "description": "Configuration files",
        },
    }

    # ✅ PHASE 4: Security audit tracking
    _audit_events: List[Dict[str, Any]] = []
    _max_audit_events = 1000  # Keep last 1000 events in memory

    @classmethod
    def validate_path(
        cls,
        path: str | Path,
        base_dir: str | Path,
        must_exist: bool = False,
        allow_symlinks: bool = False,
        allowed_extensions: Optional[Set[str]] = None,
        check_writable: bool = False,
    ) -> Path:
        """Validate and sanitize a file path.

        This is the main validation method that should be used for all path
        operations. It performs comprehensive security checks.

        Args:
            path: Path to validate (can be relative or absolute)
            base_dir: Base directory that path must be within
            must_exist: Whether the path must already exist
            allow_symlinks: Whether to allow symbolic links
            allowed_extensions: Set of allowed file extensions (with dots)
            check_writable: Whether to verify path is writable

        Returns:
            Validated and resolved Path object

        Raises:
            PathValidationError: If path fails any security check

        Examples:
            >>> PathSecurityValidator.validate_path(
            ...     path="my_screenshot.png",
            ...     base_dir="screenshots",
            ...     must_exist=True,
            ...     allowed_extensions={".png", ".jpg"}
            ... )
            PosixPath('/path/to/screenshots/my_screenshot.png')
        """
        # Convert to Path objects
        if isinstance(path, str):
            path_obj = Path(path)
        else:
            path_obj = path

        if isinstance(base_dir, str):
            # Handle named base directories
            if base_dir in cls.ALLOWED_BASES:
                base_dir_obj = cls.ALLOWED_BASES[base_dir]
            else:
                base_dir_obj = Path(base_dir).resolve()
        else:
            base_dir_obj = base_dir.resolve()

        # Step 1: Check path length (Phase 4)
        cls._check_path_length(str(path_obj))

        # Step 2: Check for Windows UNC paths (Phase 4)
        cls._check_windows_unc_path(str(path_obj))

        # Step 3: Check for Windows drive letter manipulation (Phase 4)
        cls._check_windows_drive_letter(str(path_obj))

        # Step 4: Check for blocked patterns
        cls._check_blocked_patterns(str(path_obj))

        # Step 5: Check for null bytes
        cls._check_null_bytes(str(path_obj))

        # Step 6: Check for symlinks BEFORE resolving (to detect them properly)
        # ✅ PHASE 6: Enhanced symlink detection
        if not allow_symlinks:
            # Check if the path itself is a symlink
            if path_obj.is_symlink():
                raise PathValidationError(
                    path=str(path_obj),
                    reason="Symbolic links are not allowed"
                )

            # Check if any parent component is a symlink
            current = path_obj.resolve() if path_obj.exists() else path_obj.parent
            while current != base_dir_obj and current != current.parent:
                if current.is_symlink():
                    raise PathValidationError(
                        path=str(path_obj),
                        reason=f"Path contains symlink component: {current}"
                    )
                current = current.parent

        # Step 4: Resolve to absolute path (follows symlinks if allowed)
        try:
            resolved_path = path_obj.resolve(strict=must_exist)
        except (OSError, RuntimeError) as e:
            raise PathValidationError(
                path=str(path_obj),
                reason=f"Failed to resolve path: {str(e)}"
            )

        # Step 5: Check if path is within base directory
        try:
            resolved_path.relative_to(base_dir_obj)
        except ValueError:
            # ✅ PHASE 4: Log security event for path traversal attempt
            cls._log_security_event(
                event_type="path_traversal",
                path=str(resolved_path),
                reason=f"Path outside allowed directory: {base_dir_obj}",
                severity="error",
                base_dir=str(base_dir_obj)
            )
            raise PathValidationError(
                path=str(resolved_path),
                reason=f"Path outside allowed directory: {base_dir_obj}"
            )

        # Step 6: Additional symlink check after resolution (escaping symlinks)
        # Even if symlinks are allowed, they must not escape the base directory
        if allow_symlinks:
            cls._check_symlinks(resolved_path, base_dir_obj)

        # Step 7: Check for system directories
        cls._check_system_directory(resolved_path)

        # Step 8: Validate file extension if specified
        if allowed_extensions:
            cls._check_extension(resolved_path, allowed_extensions)

        # Step 9: Check if path exists (if required)
        if must_exist and not resolved_path.exists():
            raise PathValidationError(
                path=str(resolved_path),
                reason="Path does not exist"
            )

        # Step 10: Check if writable (if required)
        if check_writable:
            cls._check_writable(resolved_path)

        return resolved_path

    @classmethod
    def _check_blocked_patterns(cls, path_str: str) -> None:
        """Check for blocked path patterns (platform-aware).

        Args:
            path_str: Path string to check

        Raises:
            PathValidationError: If blocked pattern found
        """
        path_lower = path_str.lower()

        # Get platform-specific blocked patterns
        blocked_patterns = cls._get_blocked_patterns()

        for pattern in blocked_patterns:
            if pattern in path_str or pattern in path_lower:
                # ✅ PHASE 4: Log security event with platform info
                platform_ctx = cls._get_platform_context()
                cls._log_security_event(
                    event_type="blocked_pattern",
                    path=path_str,
                    reason=f"Blocked pattern detected: {pattern}",
                    severity="warning",
                    pattern=pattern,
                    platform=PlatformDetector.detect_os().value
                )
                raise PathValidationError(
                    path=path_str,
                    reason=f"Blocked pattern detected: {pattern} (Platform: {platform_ctx})"
                )

    @classmethod
    def _check_null_bytes(cls, path_str: str) -> None:
        """Check for null byte injection attempts.

        Args:
            path_str: Path string to check

        Raises:
            PathValidationError: If null bytes found
        """
        if "\x00" in path_str or "%00" in path_str:
            # ✅ PHASE 4: Log security event
            cls._log_security_event(
                event_type="null_byte_injection",
                path=path_str,
                reason="Null byte injection detected",
                severity="error"
            )
            raise PathValidationError(
                path=path_str,
                reason="Null byte injection detected"
            )

    @classmethod
    def _check_symlinks(cls, path: Path, base_dir: Path) -> None:
        """Check if path or any parent involves symlinks that escape base directory.

        Args:
            path: Path to check
            base_dir: Base directory path must stay within

        Raises:
            PathValidationError: If symlink attack detected
        """
        # Check each component in the path
        current = path.resolve()

        # Walk up the path checking for symlinks
        while True:
            if current.is_symlink():
                # Resolve the symlink
                target = current.readlink()

                # Check if symlink target is absolute (potentially dangerous)
                if target.is_absolute():
                    # Verify target is still within base directory
                    try:
                        target.resolve().relative_to(base_dir)
                    except ValueError:
                        raise PathValidationError(
                            path=str(path),
                            reason=f"Symlink escapes base directory: {current} -> {target}"
                        )

            # Stop when we reach the base directory
            if current == base_dir or current.parent == current:
                break

            current = current.parent

    @classmethod
    def _check_system_directory(cls, path: Path) -> None:
        """Check if path is within a system directory (platform-aware).

        Args:
            path: Path to check

        Raises:
            PathValidationError: If path is in system directory
        """
        path_str = str(path.resolve())

        # Get platform-specific system directories
        system_directories = cls._get_system_directories()

        for sys_dir in system_directories:
            if path_str.startswith(sys_dir):
                # ✅ PHASE 4: Log security event for system directory access with platform info
                cls._log_security_event(
                    event_type="system_directory_access",
                    path=path_str,
                    reason=f"Access to system directory denied: {sys_dir}",
                    severity="error",
                    system_dir=sys_dir,
                    platform=PlatformDetector.detect_os().value,
                    os_version=platform.platform()
                )
                raise PathValidationError(
                    path=path_str,
                    reason=f"Access to system directory denied: {sys_dir}"
                )

    @classmethod
    def _check_extension(cls, path: Path, allowed_extensions: Set[str]) -> None:
        """Validate file extension.

        Args:
            path: Path to check
            allowed_extensions: Set of allowed extensions (with dots)

        Raises:
            PathValidationError: If extension not allowed
        """
        # Get all suffixes (handles double extensions like .tar.gz)
        suffixes = path.suffixes

        if not suffixes:
            raise PathValidationError(
                path=str(path),
                reason="File has no extension"
            )

        # Check last extension (primary)
        primary_ext = suffixes[-1].lower()

        # Check if primary extension is blocked
        if primary_ext in cls.BLOCKED_EXTENSIONS:
            raise PathValidationError(
                path=str(path),
                reason=f"Blocked file extension: {primary_ext}"
            )

        # Check if primary extension is allowed
        if primary_ext not in allowed_extensions:
            raise PathValidationError(
                path=str(path),
                reason=f"Extension not allowed: {primary_ext} (allowed: {allowed_extensions})"
            )

        # Check for double extension attacks (e.g., .pdf.exe)
        if len(suffixes) > 1:
            for ext in suffixes[:-1]:  # Check all extensions except the last
                if ext.lower() in cls.BLOCKED_EXTENSIONS:
                    raise PathValidationError(
                        path=str(path),
                        reason=f"Double extension attack detected: {'.'.join(suffixes)}"
                    )

    @classmethod
    def _check_writable(cls, path: Path) -> None:
        """Check if path is writable.

        Args:
            path: Path to check

        Raises:
            PathValidationError: If path is not writable
        """
        # If path exists, check if it's writable
        if path.exists():
            if not os.access(path, os.W_OK):
                raise PathValidationError(
                    path=str(path),
                    reason="Path is not writable"
                )
        else:
            # Check if parent directory is writable
            parent = path.parent
            if parent.exists() and not os.access(parent, os.W_OK):
                raise PathValidationError(
                    path=str(path),
                    reason=f"Parent directory is not writable: {parent}"
                )

    @classmethod
    def _check_windows_unc_path(cls, path_str: str) -> None:
        """Check for Windows UNC (network) paths.

        UNC paths like \\\\server\\share are blocked for security unless
        explicitly allowed. These can be used to access network resources
        and potentially exfiltrate data.

        Args:
            path_str: Path string to check

        Raises:
            PathValidationError: If UNC path detected on Windows
        """
        if not PlatformDetector.is_windows():
            return

        # Check for UNC path patterns
        if path_str.startswith("\\\\") or path_str.startswith("//"):
            # Additional check: ensure it's not a double slash in the middle
            if path_str.startswith("\\\\\\\\") or path_str.startswith("////"):
                cls._log_security_event(
                    event_type="unc_path_blocked",
                    path=path_str,
                    reason="Windows UNC network path detected",
                    severity="warning"
                )
                raise PathValidationError(
                    path=path_str,
                    reason="UNC network paths are not allowed for security reasons"
                )

    @classmethod
    def _check_windows_drive_letter(cls, path_str: str) -> None:
        """Check for absolute Windows drive letter paths.

        Blocks absolute paths with drive letters (C:, D:, etc.) to prevent
        access outside the application's intended scope. Relative paths within
        the application directory are allowed.

        Args:
            path_str: Path string to check

        Raises:
            PathValidationError: If absolute drive path detected
        """
        if not PlatformDetector.is_windows():
            return

        # Check for drive letter pattern (e.g., C:, D:, E:)
        # But allow if it's part of the current working directory
        import re
        drive_pattern = re.compile(r'^[A-Za-z]:[\\/]')

        if drive_pattern.match(path_str):
            # Check if it's trying to access a different drive than CWD
            cwd_drive = Path.cwd().drive
            path_drive = Path(path_str).drive

            if path_drive and cwd_drive and path_drive.upper() != cwd_drive.upper():
                cls._log_security_event(
                    event_type="drive_letter_blocked",
                    path=path_str,
                    reason=f"Attempt to access different drive: {path_drive} (CWD: {cwd_drive})",
                    severity="warning"
                )
                raise PathValidationError(
                    path=path_str,
                    reason=f"Access to drive {path_drive} is not allowed (current: {cwd_drive})"
                )

    @classmethod
    def _check_path_length(cls, path_str: str) -> None:
        """Check if path length exceeds platform-specific limits.

        Windows: Traditional MAX_PATH is 260 characters (can be extended)
        Unix/Linux: Typically 4096 characters (PATH_MAX)

        Args:
            path_str: Path string to check

        Raises:
            PathValidationError: If path exceeds platform limit
        """
        os_type = PlatformDetector.detect_os()

        if os_type == OperatingSystem.WINDOWS:
            max_length = cls.MAX_PATH_LENGTH_WINDOWS
            # Windows can use extended paths with \\\\?\\ prefix for up to 32,767 chars
            # but we enforce the traditional limit for security
            if len(path_str) > max_length:
                cls._log_security_event(
                    event_type="path_too_long",
                    path=path_str[:100] + "..." if len(path_str) > 100 else path_str,
                    reason=f"Path length {len(path_str)} exceeds Windows MAX_PATH ({max_length})",
                    severity="warning"
                )
                raise PathValidationError(
                    path=path_str,
                    reason=f"Path too long: {len(path_str)} chars (max: {max_length} on Windows)"
                )
        else:
            # Unix/Linux/macOS
            max_length = cls.MAX_PATH_LENGTH_UNIX
            if len(path_str) > max_length:
                cls._log_security_event(
                    event_type="path_too_long",
                    path=path_str[:100] + "..." if len(path_str) > 100 else path_str,
                    reason=f"Path length {len(path_str)} exceeds Unix PATH_MAX ({max_length})",
                    severity="warning"
                )
                raise PathValidationError(
                    path=path_str,
                    reason=f"Path too long: {len(path_str)} chars (max: {max_length} on Unix)"
                )

    @classmethod
    def canonicalize_path(cls, path: str | Path) -> Path:
        """Canonicalize path to its absolute, normalized form.

        This method resolves symlinks, removes redundant separators,
        and converts to absolute paths in a platform-aware manner.

        Args:
            path: Path to canonicalize

        Returns:
            Canonicalized Path object

        Examples:
            >>> PathSecurityValidator.canonicalize_path("./foo/../bar")
            PosixPath('/absolute/path/to/bar')
        """
        path_obj = Path(path) if isinstance(path, str) else path

        try:
            # Resolve to absolute path and resolve symlinks
            canonical = path_obj.resolve()

            # Platform-specific normalization
            if PlatformDetector.is_windows():
                # Normalize Windows path separators
                canonical_str = str(canonical).replace('/', '\\')
                canonical = Path(canonical_str)

            return canonical
        except (OSError, RuntimeError) as e:
            # If path doesn't exist or has issues, at least normalize it
            cls._log_security_event(
                event_type="canonicalization_warning",
                path=str(path),
                reason=f"Could not fully canonicalize path: {e}",
                severity="info"
            )
            return path_obj.absolute()

    @classmethod
    def sanitize_filename(cls, filename: str, max_length: int = 255) -> str:
        """Sanitize a filename by removing dangerous characters (cross-platform).

        Removes path separators and platform-specific reserved characters.

        Args:
            filename: Filename to sanitize
            max_length: Maximum allowed filename length

        Returns:
            Sanitized filename

        Example:
            >>> PathSecurityValidator.sanitize_filename("../../../etc/passwd")
            'etcpasswd'
            >>> PathSecurityValidator.sanitize_filename("file<>:\"|?.txt")
            'file.txt'
        """
        # Remove any path components (both / and \)
        filename = os.path.basename(filename)
        filename = filename.replace('/', '_').replace('\\', '_')

        # Remove null bytes
        filename = filename.replace('\x00', '').replace('\r', '').replace('\n', '')

        # Windows-specific: Remove reserved characters
        if PlatformDetector.is_windows():
            # Windows reserved characters: < > : " | ? *
            for char in ['<', '>', ':', '"', '|', '?', '*']:
                filename = filename.replace(char, '_')

            # Windows reserved names (case-insensitive)
            reserved_names = {
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            }
            name_upper = filename.upper()
            if name_upper in reserved_names or name_upper.split('.')[0] in reserved_names:
                filename = '_' + filename

        # Remove or replace dangerous characters
        # Keep alphanumeric, dots, dashes, underscores, spaces
        safe_filename = re.sub(r'[^a-zA-Z0-9._\- ]', '', filename)

        # Prevent hidden files (starting with dot) on Unix
        if not PlatformDetector.is_windows() and safe_filename.startswith('.'):
            safe_filename = safe_filename[1:]

        # Ensure we still have a filename
        if not safe_filename or safe_filename.isspace():
            safe_filename = "file"

        # Truncate if too long
        if len(safe_filename) > max_length:
            # Try to preserve extension
            parts = safe_filename.rsplit('.', 1)
            if len(parts) == 2:
                name, ext = parts
                max_name_length = max_length - len(ext) - 1
                safe_filename = name[:max_name_length] + '.' + ext
            else:
                safe_filename = safe_filename[:max_length]

        return safe_filename

    @classmethod
    def validate_directory_creation(
        cls,
        path: str | Path,
        allowed_parent: Path,
        max_depth: int = 10,
    ) -> Path:
        """Validate a directory path for creation.

        Args:
            path: Directory path to validate
            allowed_parent: Parent directory it must be within
            max_depth: Maximum directory depth from parent

        Returns:
            Validated Path object

        Raises:
            PathValidationError: If validation fails
        """
        # Convert and expand user path
        if isinstance(path, str):
            path_obj = Path(path).expanduser()
        else:
            path_obj = path

        # Resolve to absolute path
        resolved_path = path_obj.resolve()

        # Check if within allowed parent
        try:
            relative = resolved_path.relative_to(allowed_parent.resolve())
        except ValueError:
            raise PathValidationError(
                path=str(resolved_path),
                reason=f"Directory must be within {allowed_parent}"
            )

        # Check depth
        depth = len(relative.parts)
        if depth > max_depth:
            raise PathValidationError(
                path=str(resolved_path),
                reason=f"Directory depth {depth} exceeds maximum {max_depth}"
            )

        # Check for system directories
        cls._check_system_directory(resolved_path)

        return resolved_path

    @classmethod
    def is_system_directory(cls, path: Path) -> bool:
        """Check if path is a system directory.

        Args:
            path: Path to check

        Returns:
            True if path is a system directory, False otherwise
        """
        path_str = str(path.resolve())


    # ========================================
    # 🔒 PHASE 4: AUDIT LOGGING
    # ========================================

    @classmethod
    def _log_security_event(
        cls,
        event_type: str,
        path: str,
        reason: str,
        severity: str = "warning",
        **extra_context
    ) -> None:
        """Log a security event for audit purposes.

        Args:
            event_type: Type of security event (e.g., "path_validation_failure")
            path: Path that triggered the event
            reason: Reason for the security event
            severity: Event severity (debug, info, warning, error)
            **extra_context: Additional context to log
        """
        # Automatically include platform information if not already provided
        if 'platform' not in extra_context:
            extra_context['platform'] = PlatformDetector.detect_os().value
        if 'os_version' not in extra_context:
            extra_context['os_version'] = platform.platform()

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "path": path,
            "reason": reason,
            "severity": severity,
            **extra_context
        }

        # Add to in-memory audit trail (bounded)
        cls._audit_events.append(event)
        if len(cls._audit_events) > cls._max_audit_events:
            cls._audit_events.pop(0)  # Remove oldest event

        # Log to standard logging with platform context
        log_message = f"🚨 Security Event [{extra_context['platform']}]: {event_type} - {reason} (path: {path})"

        if severity == "error":
            logger.error(log_message, extra=event)
        elif severity == "warning":
            logger.warning(log_message, extra=event)
        elif severity == "info":
            logger.info(log_message, extra=event)
        else:
            logger.debug(log_message, extra=event)

    @classmethod
    def get_audit_events(
        cls,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent security audit events.

        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return

        Returns:
            List of audit events (most recent first)
        """
        events = cls._audit_events[-limit:]  # Get most recent

        if event_type:
            events = [e for e in events if e["event_type"] == event_type]

        return list(reversed(events))  # Most recent first

    @classmethod
    def clear_audit_events(cls) -> int:
        """Clear audit event history.

        Returns:
            Number of events cleared
        """
        count = len(cls._audit_events)
        cls._audit_events.clear()
        return count

    @classmethod
    def get_audit_summary(cls) -> Dict[str, Any]:
        """Get summary statistics of audit events.

        Returns:
            Dictionary with audit statistics
        """
        if not cls._audit_events:
            return {
                "total_events": 0,
                "by_type": {},
                "by_severity": {},
                "oldest_event": None,
                "newest_event": None,
            }

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}

        for event in cls._audit_events:
            event_type = event.get("event_type", "unknown")
            severity = event.get("severity", "unknown")

            by_type[event_type] = by_type.get(event_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total_events": len(cls._audit_events),
            "by_type": by_type,
            "by_severity": by_severity,
            "oldest_event": cls._audit_events[0]["timestamp"],
            "newest_event": cls._audit_events[-1]["timestamp"],
        }

    @classmethod
    def get_safe_path(cls, base_dir: Path, filename: str) -> Path:
        """Get a safe path by combining base directory and sanitized filename.

        This is a convenience method for common use cases.

        Args:
            base_dir: Base directory
            filename: Filename to sanitize and combine

        Returns:
            Safe Path object

        Example:
            >>> PathSecurityValidator.get_safe_path(
            ...     Path("screenshots"),
            ...     "../../../etc/passwd"
            ... )
            PosixPath('screenshots/etcpasswd')
        """
        safe_filename = cls.sanitize_filename(filename)
        return base_dir / safe_filename


# Convenience functions for common use cases

def validate_screenshot_path(path: str | Path, must_exist: bool = True) -> Path:
    """Validate a screenshot file path.

    Args:
        path: Screenshot path to validate
        must_exist: Whether file must exist

    Returns:
        Validated Path object
    """
    return PathSecurityValidator.validate_path(
        path=path,
        base_dir="screenshots",
        must_exist=must_exist,
        allow_symlinks=False,
        allowed_extensions=PathSecurityValidator.SCREENSHOT_EXTENSIONS,
    )


def validate_config_path(path: str | Path, must_exist: bool = True) -> Path:
    """Validate a configuration file path.

    Args:
        path: Config path to validate
        must_exist: Whether file must exist

    Returns:
        Validated Path object
    """
    return PathSecurityValidator.validate_path(
        path=path,
        base_dir="config",
        must_exist=must_exist,
        allow_symlinks=False,
        allowed_extensions=PathSecurityValidator.CONFIG_EXTENSIONS,
    )


def validate_browser_session_path(path: str | Path, must_exist: bool = False) -> Path:
    """Validate a browser session file path.

    Args:
        path: Browser session path to validate
        must_exist: Whether file must exist

    Returns:
        Validated Path object
    """
    return PathSecurityValidator.validate_path(
        path=path,
        base_dir="browser_sessions",
        must_exist=must_exist,
        allow_symlinks=False,
        allowed_extensions={".json"},
    )

