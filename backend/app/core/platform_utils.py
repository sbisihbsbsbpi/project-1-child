"""Platform detection and OS-specific utilities.

This module provides cross-platform support by detecting the current operating
system and providing platform-specific utilities for path handling.

Supported platforms:
- Windows (Windows 10/11, Server)
- macOS (10.15+)
- Linux (Ubuntu, Debian, RHEL, etc.)
"""

from __future__ import annotations

import sys
import platform
from enum import Enum
from typing import Optional


class OperatingSystem(Enum):
    """Supported operating systems."""
    
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class PlatformDetector:
    """Detect current operating system and provide platform-specific utilities.
    
    This class uses Python's platform module to detect the OS and provides
    convenient methods for platform-specific logic. Detection results are
    cached for performance.
    
    Examples:
        >>> if PlatformDetector.is_windows():
        ...     print("Running on Windows")
        >>> os_type = PlatformDetector.detect_os()
        >>> print(f"Detected OS: {os_type.value}")
    """
    
    # Cache the detected OS to avoid repeated platform.system() calls
    _cached_os: Optional[OperatingSystem] = None
    
    @classmethod
    def detect_os(cls) -> OperatingSystem:
        """Detect the current operating system.
        
        Uses Python's platform.system() and sys.platform to reliably detect
        the OS. Results are cached for performance.
        
        Returns:
            OperatingSystem enum value indicating the current OS
            
        Examples:
            >>> os_type = PlatformDetector.detect_os()
            >>> if os_type == OperatingSystem.MACOS:
            ...     print("Running on macOS")
        """
        if cls._cached_os is not None:
            return cls._cached_os
        
        system = platform.system().lower()
        
        # Windows detection (win32, win64, cygwin)
        if system == 'windows' or sys.platform == 'win32':
            cls._cached_os = OperatingSystem.WINDOWS
        # macOS detection (Darwin is the kernel name)
        elif system == 'darwin':
            cls._cached_os = OperatingSystem.MACOS
        # Linux detection
        elif system == 'linux':
            cls._cached_os = OperatingSystem.LINUX
        # Unknown/unsupported OS
        else:
            cls._cached_os = OperatingSystem.UNKNOWN
        
        return cls._cached_os
    
    @classmethod
    def is_windows(cls) -> bool:
        """Check if running on Windows.
        
        Returns:
            True if running on Windows, False otherwise
        """
        return cls.detect_os() == OperatingSystem.WINDOWS
    
    @classmethod
    def is_macos(cls) -> bool:
        """Check if running on macOS.
        
        Returns:
            True if running on macOS, False otherwise
        """
        return cls.detect_os() == OperatingSystem.MACOS
    
    @classmethod
    def is_linux(cls) -> bool:
        """Check if running on Linux.
        
        Returns:
            True if running on Linux, False otherwise
        """
        return cls.detect_os() == OperatingSystem.LINUX
    
    @classmethod
    def is_unix_like(cls) -> bool:
        """Check if running on Unix-like OS (macOS or Linux).
        
        Returns:
            True if running on macOS or Linux, False otherwise
        """
        os_type = cls.detect_os()
        return os_type in (OperatingSystem.MACOS, OperatingSystem.LINUX)
    
    @classmethod
    def get_path_separator(cls) -> str:
        """Get the OS-specific path separator.
        
        Returns:
            '\\' for Windows, '/' for Unix-like systems
            
        Examples:
            >>> sep = PlatformDetector.get_path_separator()
            >>> path = f"folder{sep}file.txt"
        """
        return '\\' if cls.is_windows() else '/'
    
    @classmethod
    def normalize_path(cls, path_str: str) -> str:
        """Normalize path separators for current OS.
        
        Converts path separators to the appropriate format for the current OS.
        This is useful when dealing with paths from user input or configuration
        files that may use different separator conventions.
        
        Args:
            path_str: Path string with any separator style
            
        Returns:
            Path string with OS-appropriate separators
            
        Examples:
            >>> # On Windows: converts / to \\
            >>> PlatformDetector.normalize_path("folder/file.txt")
            'folder\\file.txt'
            >>> # On Unix: converts \\ to /
            >>> PlatformDetector.normalize_path("folder\\\\file.txt")
            'folder/file.txt'
        """
        if cls.is_windows():
            return path_str.replace('/', '\\')
        else:
            return path_str.replace('\\', '/')
