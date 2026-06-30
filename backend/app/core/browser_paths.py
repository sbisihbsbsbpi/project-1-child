"""Cross-platform browser path detection.

This module provides automatic detection of browser installation paths
across Windows, macOS, and Linux. Supports Chrome and Brave browsers.

Features:
- Automatic OS detection
- Multiple fallback paths per platform
- User data directory detection
- Browser executable validation
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, List
from .platform_utils import PlatformDetector, OperatingSystem


class BrowserPathDetector:
    """Detect browser installation paths across platforms.

    This class provides static methods to locate Chrome and Brave browser
    executables and user data directories on Windows, macOS, and Linux.

    Examples:
        >>> chrome_path = BrowserPathDetector.get_chrome_path()
        >>> if chrome_path and chrome_path.exists():
        ...     print(f"Chrome found at: {chrome_path}")
    """

    @classmethod
    def get_chrome_path(cls) -> Optional[Path]:
        """Get Chrome executable path for current OS.

        Tries multiple common installation locations and returns the first
        valid path found. Returns None if Chrome is not found.

        Returns:
            Path to Chrome executable if found, None otherwise

        Platform-specific paths:
            - macOS: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
            - Windows: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
            - Linux: /usr/bin/google-chrome, /usr/bin/google-chrome-stable
        """
        os_type = PlatformDetector.detect_os()

        if os_type == OperatingSystem.MACOS:
            path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            return path if path.exists() else None

        elif os_type == OperatingSystem.WINDOWS:
            # Try multiple common Windows locations
            possible_paths = [
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "Application" / "chrome.exe",
            ]
            for path in possible_paths:
                if path.exists():
                    return path
            return None

        else:  # Linux
            # Try common Linux paths
            possible_paths = [
                Path("/usr/bin/google-chrome"),
                Path("/usr/bin/google-chrome-stable"),
                Path("/usr/bin/chromium"),
                Path("/usr/bin/chromium-browser"),
                Path("/snap/bin/chromium"),  # Snap package
                Path("/var/lib/flatpak/exports/bin/com.google.Chrome"),  # Flatpak
            ]
            for path in possible_paths:
                if path.exists():
                    return path
            return None

    @classmethod
    def get_brave_path(cls) -> Optional[Path]:
        """Get Brave executable path for current OS.

        Tries multiple common installation locations and returns the first
        valid path found. Returns None if Brave is not found.

        Returns:
            Path to Brave executable if found, None otherwise

        Platform-specific paths:
            - macOS: /Applications/Brave Browser.app/Contents/MacOS/Brave Browser
            - Windows: C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe
            - Linux: /usr/bin/brave, /usr/bin/brave-browser
        """
        os_type = PlatformDetector.detect_os()

        if os_type == OperatingSystem.MACOS:
            path = Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")
            return path if path.exists() else None

        elif os_type == OperatingSystem.WINDOWS:
            possible_paths = [
                Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
                Path(r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"),
                Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            ]
            for path in possible_paths:
                if path.exists():
                    return path
            return None

        else:  # Linux
            possible_paths = [
                Path("/usr/bin/brave"),
                Path("/usr/bin/brave-browser"),
                Path("/usr/bin/brave-browser-stable"),
                Path("/snap/bin/brave"),  # Snap package
                Path("/var/lib/flatpak/exports/bin/com.brave.Browser"),  # Flatpak
            ]
            for path in possible_paths:
                if path.exists():
                    return path
            return None

    @classmethod
    def get_safari_path(cls) -> Optional[Path]:
        """Get Safari executable path for macOS.

        Safari is only available on macOS. Returns None on other platforms.

        Returns:
            Path to Safari executable if found, None otherwise

        Platform-specific paths:
            - macOS: /Applications/Safari.app/Contents/MacOS/Safari
        """
        os_type = PlatformDetector.detect_os()

        if os_type == OperatingSystem.MACOS:
            # Standard Safari
            safari_path = Path("/Applications/Safari.app/Contents/MacOS/Safari")
            if safari_path.exists():
                return safari_path

            # Safari Technology Preview (for development/testing)
            stp_path = Path("/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview")
            if stp_path.exists():
                return stp_path

            return None
        else:
            # Safari not available on Windows/Linux
            return None

    @classmethod
    def get_browser_user_data_dir(cls, browser: str = "chrome") -> Path:
        """Get browser user data directory for current OS.

        Returns the default user data directory where browser profiles,
        cookies, and settings are stored.

        Args:
            browser: Browser name ("chrome" or "brave")

        Returns:
            Path to browser user data directory

        Raises:
            ValueError: If browser name is not recognized

        Examples:
            >>> chrome_data = BrowserPathDetector.get_browser_user_data_dir("chrome")
            >>> print(f"Chrome data: {chrome_data}")
        """
        os_type = PlatformDetector.detect_os()
        home = Path.home()

        browser_lower = browser.lower()

        if browser_lower == "chrome":
            if os_type == OperatingSystem.MACOS:
                return home / "Library" / "Application Support" / "Google" / "Chrome"
            elif os_type == OperatingSystem.WINDOWS:
                return home / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
            else:  # Linux
                return home / ".config" / "google-chrome"

        elif browser_lower == "brave":
            if os_type == OperatingSystem.MACOS:
                return home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser"
            elif os_type == OperatingSystem.WINDOWS:
                return home / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data"
            else:  # Linux
                return home / ".config" / "BraveSoftware" / "Brave-Browser"

        else:
            raise ValueError(f"Unknown browser: {browser}. Supported: 'chrome', 'brave'")

    @classmethod
    def find_browser(cls, preferred: str = "brave") -> Optional[tuple[Path, str]]:
        """Find any available browser, preferring the specified one.

        Searches for browsers in order of preference and returns the first
        one found. Useful when you need any Chromium-based browser.

        Args:
            preferred: Preferred browser name ("brave" or "chrome")

        Returns:
            Tuple of (browser_path, browser_name) if found, None otherwise

        Examples:
            >>> result = BrowserPathDetector.find_browser("brave")
            >>> if result:
            ...     path, name = result
            ...     print(f"Found {name} at: {path}")
        """
        # Try preferred browser first
        if preferred.lower() == "brave":
            brave_path = cls.get_brave_path()
            if brave_path:
                return (brave_path, "brave")
            # Fallback to Chrome
            chrome_path = cls.get_chrome_path()
            if chrome_path:
                return (chrome_path, "chrome")
        else:
            # Prefer Chrome
            chrome_path = cls.get_chrome_path()
            if chrome_path:
                return (chrome_path, "chrome")
            # Fallback to Brave
            brave_path = cls.get_brave_path()
            if brave_path:
                return (brave_path, "brave")

        return None

    @classmethod
    def get_all_installed_browsers(cls) -> List[tuple[str, Path]]:
        """Get list of all installed browsers.

        Scans for all supported browsers and returns those that are found.

        Returns:
            List of (browser_name, browser_path) tuples for all found browsers

        Examples:
            >>> browsers = BrowserPathDetector.get_all_installed_browsers()
            >>> for name, path in browsers:
            ...     print(f"{name}: {path}")
        """
        browsers = []

        chrome_path = cls.get_chrome_path()
        if chrome_path:
            browsers.append(("chrome", chrome_path))

        brave_path = cls.get_brave_path()
        if brave_path:
            browsers.append(("brave", brave_path))

        return browsers

    @classmethod
    def is_browser_installed(cls, browser: str) -> bool:
        """Check if a specific browser is installed.

        Args:
            browser: Browser name ("chrome" or "brave")

        Returns:
            True if browser is installed, False otherwise

        Examples:
            >>> if BrowserPathDetector.is_browser_installed("brave"):
            ...     print("Brave is installed!")
        """
        browser_lower = browser.lower()

        if browser_lower == "chrome":
            return cls.get_chrome_path() is not None
        elif browser_lower == "brave":
            return cls.get_brave_path() is not None
        else:
            raise ValueError(f"Unknown browser: {browser}")


def get_browser_launch_args(
    browser: str,
    remote_debugging_port: int = 9223,
    user_data_dir: Optional[Path] = None,
    headless: bool = False,
) -> List[str]:
    """Get platform-specific browser launch arguments.

    Constructs the command-line arguments needed to launch a browser with
    remote debugging enabled. Uses platform-appropriate path separators.

    Args:
        browser: Browser name ("chrome" or "brave")
        remote_debugging_port: CDP port number (default: 9223)
        user_data_dir: Custom user data directory (default: OS default)
        headless: Launch in headless mode (default: False)

    Returns:
        List of command-line arguments

    Examples:
        >>> args = get_browser_launch_args("brave", 9223)
        >>> print(args)
        ['--remote-debugging-port=9223', '--no-first-run', ...]
    """
    if user_data_dir is None:
        user_data_dir = BrowserPathDetector.get_browser_user_data_dir(browser)

    args = [
        f"--remote-debugging-port={remote_debugging_port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    if headless:
        args.append("--headless")

    return args
