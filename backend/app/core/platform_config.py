"""Platform-specific paths and configurations.

This module provides OS-specific path configurations for system directories,
temporary directories, and other platform-dependent locations.

All path configurations are determined at runtime based on the detected OS,
ensuring the security system adapts to the deployment environment.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Set

from .platform_utils import PlatformDetector, OperatingSystem


class PlatformConfig:
    """OS-specific path configurations and system directories.
    
    This class provides platform-aware configurations for:
    - System directories that should be protected
    - Default application directories
    - Temporary directories
    - User-specific paths
    
    All methods use runtime OS detection to return appropriate values.
    """
    
    @classmethod
    def get_system_directories(cls) -> Set[str]:
        """Get protected system directories for the current OS.
        
        Returns a set of absolute path strings for directories that should
        never be accessible through the application (security-critical).
        
        Returns:
            Set of absolute path strings for system directories
            
        Platform-specific directories:
            - Windows: C:\\Windows, C:\\Program Files, etc.
            - macOS: /System, /Library, /usr, /bin, etc.
            - Linux: /etc, /var, /usr, /bin, /boot, etc.
            
        Examples:
            >>> sys_dirs = PlatformConfig.get_system_directories()
            >>> if "/etc" in sys_dirs:
            ...     print("Running on Unix-like system")
        """
        os_type = PlatformDetector.detect_os()
        
        # Common protected directories across all platforms
        common = {
            str(Path.home() / ".ssh"),      # SSH keys
            str(Path.home() / ".gnupg"),    # GPG keys
            str(Path.home() / ".aws"),      # AWS credentials
            str(Path.home() / ".docker"),   # Docker credentials
        }
        
        # Windows-specific system directories
        if os_type == OperatingSystem.WINDOWS:
            return common | {
                "C:\\Windows",
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                "C:\\ProgramData",
                "C:\\System Volume Information",
                "C:\\$Recycle.Bin",
                "C:\\Recovery",
                "C:\\Windows\\System32",
                str(Path.home() / "AppData" / "Roaming" / "Microsoft"),
                str(Path.home() / "AppData" / "Local" / "Microsoft"),
            }
        
        # macOS-specific system directories
        elif os_type == OperatingSystem.MACOS:
            return common | {
                "/System",
                "/Library/Application Support",
                "/Library/LaunchDaemons",
                "/Library/LaunchAgents",
                "/private/etc",
                "/private/var",
                "/usr",
                "/bin",
                "/sbin",
                "/var",
                "/etc",
                "/tmp",  # Symlink to /private/tmp
                "/cores",
            }
        
        # Linux-specific system directories
        elif os_type == OperatingSystem.LINUX:
            return common | {
                "/etc",
                "/var",
                "/usr",
                "/bin",
                "/sbin",
                "/boot",
                "/dev",
                "/proc",
                "/sys",
                "/root",
                "/lib",
                "/lib64",
                "/opt",
                "/tmp",
                "/run",
                "/mnt",
                "/media",
                "/srv",
            }
        
        # Unknown OS - return common directories only
        else:
            return common
    
    @classmethod
    def get_home_directory(cls) -> Path:
        """Get the user's home directory (cross-platform).
        
        Returns:
            Path object for the current user's home directory
            
        Examples:
            >>> home = PlatformConfig.get_home_directory()
            >>> print(f"Home: {home}")
        """
        return Path.home()
    
    @classmethod
    def get_temp_directory(cls) -> Path:
        """Get the system temporary directory (cross-platform).
        
        Uses Python's tempfile module to get the appropriate temp directory
        for the current OS.
        
        Returns:
            Path object for the system temporary directory
            
        Platform-specific locations:
            - Windows: %TEMP% or %TMP% (usually C:\\Users\\<user>\\AppData\\Local\\Temp)
            - macOS: /var/folders/... or /tmp
            - Linux: /tmp or /var/tmp
            
        Examples:
            >>> temp = PlatformConfig.get_temp_directory()
            >>> print(f"Temp: {temp}")
        """
        return Path(tempfile.gettempdir())
    
    @classmethod
    def get_os_name(cls) -> str:
        """Get a human-readable OS name.
        
        Returns:
            String name of the operating system
            
        Examples:
            >>> os_name = PlatformConfig.get_os_name()
            >>> print(f"Running on: {os_name}")
        """
        os_type = PlatformDetector.detect_os()
        
        names = {
            OperatingSystem.WINDOWS: "Windows",
            OperatingSystem.MACOS: "macOS",
            OperatingSystem.LINUX: "Linux",
            OperatingSystem.UNKNOWN: "Unknown",
        }
        
        return names.get(os_type, "Unknown")
