"""
Screenshot Service using Playwright
Handles browser automation and screenshot capture

✅ 2025 STEALTH ENHANCEMENTS:
- Patchright for CDP leak patching (BEST - patches at source level)
- Rebrowser patches for CDP detection bypass (fallback)
- Camoufox support for maximum stealth (optional)
- playwright-stealth as additional layer
"""

# ✅ Try to import Patchright first (BEST - patches CDP leaks at source)
STEALTH_MODE = None
try:
    from patchright.async_api import async_playwright, Browser, Page, BrowserContext

    STEALTH_MODE = "patchright"
    print("🎯 Using Patchright - CDP leaks patched at source level!")
    print("   ✅ Runtime.enable bypassed")
    print("   ✅ Console.enable disabled")
    print("   ✅ Command flags optimized")
except ImportError:
    # Try rebrowser-playwright as fallback
    try:
        from rebrowser_playwright.async_api import async_playwright, Browser, Page, BrowserContext

        STEALTH_MODE = "rebrowser"
        print("🚀 Using Rebrowser patches for enhanced stealth!")
        print("   💡 Consider upgrading to Patchright: pip install patchright")
    except ImportError:
        # Final fallback to standard playwright
        from playwright.async_api import async_playwright, Browser, Page, BrowserContext

        STEALTH_MODE = "standard"
        print("⚠️  Using standard Playwright")
        print("   💡 For better stealth, install Patchright: pip install patchright")

# Try to import Camoufox for advanced mode
try:
    # Disable SSL verification for browserforge data file downloads (macOS fix)
    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context

    from camoufox.async_api import AsyncCamoufox

    CAMOUFOX_AVAILABLE = True
    print("🦊 Camoufox available for maximum stealth mode!")
except (ImportError, FileNotFoundError, Exception) as e:
    CAMOUFOX_AVAILABLE = False
    AsyncCamoufox = None
    if isinstance(e, FileNotFoundError):
        print("⚠️  Camoufox installed but has dependency issues (browserforge data files missing)")
        print("   Skipping Camoufox - Rebrowser provides excellent stealth already!")

from playwright_stealth import stealth_async
import os
import asyncio
import random
import hashlib
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
import imagehash
import json
from collections import OrderedDict  # ✅ FIXED: LRU cache for hash storage
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Tuple, Dict, Optional
from config import settings  # ✅ PHASE 3: Use centralized configuration
from logging_config import setup_logging  # ✅ Structured logging with correlation IDs

# ✅ Create logger for this module via central logging configuration so that
# the correlation ID filter is always attached before any logs are emitted.
logger = setup_logging(__name__)

# ========================================
# 🎯 9 STEALTH SOLUTIONS - USER AGENTS
# ========================================
# Solution #2: Randomize User-Agent Strings
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# ========================================
# 🎯 9 STEALTH SOLUTIONS - VIEWPORTS
# ========================================
# Solution #6: Adjust Viewport Size and Device Emulation
VIEWPORTS = [
    # Desktop viewports
    {"width": 1920, "height": 1080, "device_type": "desktop"},  # Full HD
    {"width": 1366, "height": 768, "device_type": "desktop"},  # Laptop
    {"width": 1536, "height": 864, "device_type": "desktop"},  # HD+
    {"width": 1440, "height": 900, "device_type": "desktop"},  # MacBook
    {"width": 2560, "height": 1440, "device_type": "desktop"},  # 2K
    # Mobile viewports
    {"width": 375, "height": 667, "device_type": "mobile"},  # iPhone 8
    {"width": 414, "height": 896, "device_type": "mobile"},  # iPhone 11
    {"width": 390, "height": 844, "device_type": "mobile"},  # iPhone 12/13
    {"width": 412, "height": 915, "device_type": "mobile"},  # Pixel 5
    # Tablet viewports
    {"width": 768, "height": 1024, "device_type": "tablet"},  # iPad
    {"width": 820, "height": 1180, "device_type": "tablet"},  # iPad Air
]


class TabRegistry:
    """
    Manages browser tabs for Real Browser Mode with:
    - Disconnect detection
    - Memory leak prevention
    - Automatic cleanup
    """

    def __init__(self, max_size=100, cleanup_interval=300):
        """
        Initialize tab registry.

        Args:
            max_size: Maximum number of tabs to track (prevents memory leaks)
            cleanup_interval: Seconds between periodic cleanups (default: 5 minutes)
        """
        self.tabs = {}  # {url: {"page": Page, "status": str, "created_at": float}}
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = 0  # Will be set on first cleanup
        self.time = time

    async def register_tab(self, url: str, page: Page):
        """Register a new tab"""
        # Enforce size limit
        if len(self.tabs) >= self.max_size:
            logger.warning(f"⚠️  Tab registry at max size ({self.max_size}), cleaning up...")
            await self.cleanup_successful_tabs()

        self.tabs[url] = {
            "page": page,
            "status": "pending",
            "created_at": self.time.time()
        }
        logger.debug(f"📋 Registered tab: {url}")

    async def mark_success(self, url: str):
        """Mark tab as successfully captured"""
        if url in self.tabs:
            self.tabs[url]["status"] = "success"
            logger.debug(f"✅ Marked success: {url}")

    async def mark_failure(self, url: str):
        """Mark tab as failed"""
        if url in self.tabs:
            self.tabs[url]["status"] = "failed"
            logger.debug(f"❌ Marked failure: {url}")

    async def is_tab_alive(self, url: str) -> bool:
        """Check if tab is still accessible (multi-layered detection)"""
        if url not in self.tabs:
            return False

        page = self.tabs[url]["page"]

        # Layer 1: Check if page is closed
        try:
            if page.is_closed():
                return False
        except Exception:
            return False

        # Layer 2: Try to access page URL (detects disconnected browser)
        try:
            _ = page.url
            return True
        except Exception:
            return False

    async def cleanup_successful_tabs(self):
        """Close tabs that successfully captured screenshots"""
        import logging
        logger = logging.getLogger(__name__)

        closed_count = 0
        kept_count = 0
        stale_count = 0

        for url, info in list(self.tabs.items()):
            # Check if tab is still alive
            if not await self.is_tab_alive(url):
                del self.tabs[url]
                stale_count += 1
                logger.info(f"🧹 Removed stale tab: {url}")
                continue

            # Close successful tabs
            if info["status"] == "success":
                try:
                    # ⏱️ Wait before closing (user requested)
                    await asyncio.sleep(self.TAB_CLOSE_DELAY_SEC)
                    await info["page"].close()
                    del self.tabs[url]
                    closed_count += 1
                    logger.info(f"✅ Closed successful tab: {url}")
                except Exception as e:
                    logger.warning(f"⚠️  Error closing tab for {url}: {e}")
                    del self.tabs[url]  # Remove from registry anyway
            else:
                kept_count += 1
                logger.warning(f"⚠️  Keeping tab open for debugging: {url} (Status: {info['status']})")

        if closed_count > 0 or kept_count > 0 or stale_count > 0:
            logger.info(
                f"📊 Cleanup complete: {closed_count} closed, {kept_count} kept for debugging, {stale_count} stale removed")

    async def cleanup_stale_tabs(self):
        """Remove dead tab references (browser disconnected/crashed)"""
        stale_urls = []

        for url in list(self.tabs.keys()):
            if not await self.is_tab_alive(url):
                stale_urls.append(url)

        for url in stale_urls:
            del self.tabs[url]

        if len(stale_urls) > 0:
            logger.info(f"🧹 Removed {len(stale_urls)} stale tab references (browser disconnected)")

    async def periodic_cleanup(self):
        """Run periodic cleanup if interval elapsed"""
        current_time = self.time.time()

        # Initialize last_cleanup on first call
        if self.last_cleanup == 0:
            self.last_cleanup = current_time
            return

        if current_time - self.last_cleanup > self.cleanup_interval:
            logger.info("🧹 Running periodic cleanup...")
            await self.cleanup_stale_tabs()
            self.last_cleanup = current_time

    async def clear_all(self):
        """Close all tabs and clear registry.

        Returns the number of tabs successfully closed.
        """
        closed_count = 0

        for url, info in list(self.tabs.items()):
            try:
                if not info["page"].is_closed():
                    # ⏱️ Wait before closing
                    await asyncio.sleep(self.TAB_CLOSE_DELAY_SEC)
                    await info["page"].close()
                    closed_count += 1
            except Exception:
                # Best-effort cleanup; ignore per-tab failures
                pass

        self.tabs.clear()
        if closed_count > 0:
            logger.info(f"🧹 Cleared all tabs ({closed_count} closed)")
        return closed_count

    def get_stats(self):
        """Get registry statistics"""
        total = len(self.tabs)
        success = sum(1 for info in self.tabs.values() if info["status"] == "success")
        failed = sum(1 for info in self.tabs.values() if info["status"] == "failed")
        pending = sum(1 for info in self.tabs.values() if info["status"] == "pending")

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "pending": pending
        }


class ScreenshotService:
    # ========================================
    # 🎯 PERFORMANCE OPTIMIZATION CONSTANTS
    # ========================================
    # Timing constants
    CDP_RELOAD_WAIT_SECONDS = 15
    CDP_HEIGHT_STABILIZE_ATTEMPTS = 30
    CDP_STABILIZE_DELAY_SECONDS = 0.5
    CDP_STABLE_COUNT_THRESHOLD = 4
    CDP_LAZY_LOAD_MAX_MS = 3000
    CDP_LAZY_LOAD_CHECK_INTERVAL_MS = 500
    CDP_LAZY_LOAD_STABLE_CHECKS = 2

    # Quality constants
    DUPLICATE_SIMILARITY_THRESHOLD = 0.95

    # Scroll constants
    DEFAULT_SCROLL_DELAY_MS = 1000
    DEFAULT_OVERLAP_PERCENT = 20
    DEFAULT_MAX_SEGMENTS = 50

    # ⚡ OPTIMIZATION: Browser reuse settings
    ENABLE_BROWSER_REUSE = True  # Feature flag - set to False to disable optimization
    MAX_PAGES_PER_CONTEXT = 10  # Close and recreate context after this many pages

    # ⚡ OPTIMIZATION: Batch processing settings
    ENABLE_BATCH_PROCESSING = True  # Feature flag - set to False to disable batch processing
    DEFAULT_BATCH_SIZE = 999999  # Process ALL URLs in parallel (no limit)
    SAME_DOMAIN_BATCH_SIZE = 999999  # Process ALL URLs in parallel (same domain - no limit)

    # ✅ FIXED: Hash cache memory management
    MAX_HASH_CACHE_SIZE = 10000  # Maximum number of hashes to keep in memory (prevents unbounded growth)

    # ✅ FIXED: Timing constants (sleep durations in seconds)
    TAB_CLOSE_DELAY_SEC = 1.0  # Wait before closing tabs
    RETRY_DELAY_SEC = 1.0  # Wait between retry attempts
    LAZY_CONTENT_WAIT_SEC = 3.0  # Wait for lazy-loaded content
    DROPDOWN_SETTLE_DELAY_SEC = 2.0  # Wait after expanding dropdowns
    MODAL_APPEAR_DELAY_SEC = 2.0  # Wait for modals/dialogs to appear
    INITIAL_CONTENT_WAIT_SEC = 2.0  # Wait for initial page content
    CLOUDFLARE_CHALLENGE_WAIT_SEC = 8.0  # Wait for Cloudflare challenge
    REACT_RENDER_WAIT_SEC = 5.0  # Wait for React/SPA to render
    FINAL_CONTENT_WAIT_SEC = 2.0  # Final wait for lazy content
    SCROLL_SETTLE_DELAY_SEC = 0.5  # Wait for scroll to settle
    SCROLL_SHORT_DELAY_SEC = 0.1  # Short wait for scroll completion
    SCROLL_VERIFY_DELAY_SEC = 0.15  # Wait to verify scroll position
    SCROLL_MICRO_DELAY_SEC = 0.3  # Micro delay for scroll operations
    ELEMENT_CLICK_DELAY_SEC = 1.0  # Wait after clicking elements
    DROPDOWN_RENDER_DELAY_SEC = 2.0  # Wait for dropdowns to render
    NESTED_CONTENT_DELAY_SEC = 0.5  # Wait for nested content animations
    RETRY_DETECTION_DELAY_SEC = 3.0  # Wait before retrying detection
    FINAL_SETTLE_DELAY_SEC = 1.0  # Final wait for content to settle
    NESTED_SCROLL_DELAY_SEC = 1.0  # Wait after scrolling nested elements
    TABLE_RENDER_DELAY_SEC = 2.0  # Wait for table rows to render
    BACK_NAVIGATION_DELAY_SEC = 1.0  # Wait after back navigation
    AUTH_FULL_LOAD_WAIT_SEC = 60.0  # Wait for full auth data load
    BROWSER_POLL_INTERVAL_SEC = 1.0  # Interval for polling browser state
    PAGE_READY_DELAY_SEC = 1.0  # Wait for page to be ready
    RELOAD_CHECK_INTERVAL_SEC = 1.0  # Interval between reload checks
    SPA_FULL_RENDER_WAIT_SEC = 10.0  # Extended wait for complex SPAs
    TEKION_CONTENT_WAIT_SEC = 3.0  # Wait for Tekion-specific content
    CONTENT_TRIGGER_DELAY_SEC = 2.0  # Wait after triggering content load
    DEALER_DATA_WAIT_SEC = 5.0  # Wait for dealer-specific data

    # ✅ FIXED: Timeout constants (in milliseconds)
    DOMAIN_NAVIGATION_TIMEOUT_MS = 10000  # 10 seconds for domain navigation
    PAGE_NAVIGATION_TIMEOUT_MS = 30000  # 30 seconds for page navigation
    NETWORK_IDLE_TIMEOUT_MS = 15000  # 15 seconds for network idle
    NETWORK_IDLE_SHORT_TIMEOUT_MS = 10000  # 10 seconds for short network idle
    HUMAN_BEHAVIOR_TIMEOUT_SEC = 30.0  # 30 seconds for human behavior simulation
    PAGE_LOAD_TIMEOUT_MS = 5000  # 5 seconds for page load state
    SCREENSHOT_TIMEOUT_MS = 30000  # 30 seconds for screenshot capture
    SELECTOR_WAIT_TIMEOUT_MS = 10000  # 10 seconds for selector wait
    BACK_NAVIGATION_TIMEOUT_MS = 5000  # 5 seconds for back navigation
    TABLE_SELECTOR_TIMEOUT_MS = 5000  # 5 seconds for table selector
    AUTH_NAVIGATION_TIMEOUT_MS = 60000  # 60 seconds for auth navigation

    # ✅ FIXED: Retry and attempt constants
    MAX_CDP_CONNECTION_RETRIES = 3  # Maximum retries for CDP connection
    MAX_SCROLL_RETRIES = 3  # Maximum retries for scroll operations
    MAX_STORAGE_STATE_RETRIES = 3  # Maximum retries for saving storage state

    def __init__(self):
        self.browser: Browser = None
        self.playwright = None
        self.camoufox_browser = None  # ✅ Separate Camoufox browser instance
        self.cdp_browser = None  # 🔗 CDP-connected browser instance
        self.cdp_active_page = None  # 🔗 Active tab from CDP connection
        # Use an absolute screenshots directory so downstream services (like
        # the Document Service microservice) can reliably find files
        # regardless of their own working directory.
        self.output_dir = Path("screenshots").resolve()
        self.output_dir.mkdir(exist_ok=True)
        # ✅ FIXED: Use OrderedDict for LRU cache with bounded size (prevents memory leak)
        self._hash_cache: OrderedDict[str, str] = OrderedDict()
        self._hash_cache_file = self.output_dir / ".hash_cache.json"  # ⚡ OPTIMIZATION: Persistent cache file
        self._load_hash_cache()  # ⚡ OPTIMIZATION: Load cache from disk on startup

        # Session storage for cookies (improves stealth)
        self.session_dir = Path("browser_sessions")
        self.session_dir.mkdir(exist_ok=True)

        # Track current browser mode to detect switches
        self.current_mode_is_real_browser = None
        self.current_browser_mode = None  # ✅ Track browser mode (playwright/camoufox/cdp)
        self.is_persistent_context = False  # ✅ Track if using persistent context

        # ⚡ OPTIMIZATION: Browser context reuse tracking
        self.context_page_count = 0  # Track how many pages opened in current context
        self.stealth_injected = False  # Track if stealth scripts already injected

        # ✅ FIXED: Track background tasks to prevent garbage collection (Bug #11)
        self._background_tasks: set = set()  # Track asyncio tasks to prevent premature GC

        # ========================================
        # 🎯 9 STEALTH SOLUTIONS - Session State
        # ========================================
        # Solution #5: Manage Cookies and Session Data
        self.cookies_file = Path("browser_sessions/cookies.json")
        self.cookies_file.parent.mkdir(exist_ok=True)

        # ========================================
        # 🎯 URL-SPECIFIC CLICK CONFIGURATIONS
        # ========================================
        # ✅ NEW: Load URL-specific click action configurations
        self.url_click_config = self._load_url_click_config()
        if self.url_click_config and self.url_click_config.get("url_patterns"):
            enabled_count = sum(1 for p in self.url_click_config["url_patterns"] if p.get("enabled", True))
            logger.info(f"📋 Loaded {enabled_count} URL-specific click configurations")

        # ========================================
        # 🎯 TAB MANAGEMENT FOR REAL BROWSER MODE
        # ========================================
        # ✅ NEW: Tab registry for automatic cleanup
        self.tab_registry = TabRegistry(max_size=100, cleanup_interval=300)
        logger.info("📋 Tab registry initialized (max: 100 tabs, cleanup: 5 min)")

        # ========================================
        # 🌐 NETWORK TAB - API INTERCEPTION STORAGE
        # ========================================
        # ✅ NEW: Store intercepted API responses for Network tab
        self.intercepted_apis = []  # List of all intercepted API calls
        self.max_intercepted_apis = 1000  # Limit to prevent memory issues

    # ========================================
    # 🔧 HELPER METHODS
    # ========================================

    def _send_websocket_message_background(self, message: dict) -> None:
        """
        Send WebSocket message in background without blocking.

        ✅ FIXED (Bug #11): Properly tracks background tasks to prevent garbage collection.
        Tasks are automatically removed from tracking set when complete.

        Args:
            message: Message dict to send via WebSocket
        """
        async def _send_safe():
            """Inner coroutine that handles the actual sending with error handling."""
            try:
                from main import manager
                await manager.send_message(message)
            except Exception as e:
                # Log but don't raise - this is fire-and-forget
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"WebSocket message send failed (non-critical): {e}")

        # Create task and track it
        task = asyncio.create_task(_send_safe())
        self._background_tasks.add(task)

        # Remove from set when done (prevents memory leak)
        task.add_done_callback(self._background_tasks.discard)

    # ========================================
    # ⚡ OPTIMIZATION: Hash Cache Persistence
    # ========================================

    def _load_hash_cache(self) -> None:
        """
        Load hash cache from disk (80% faster duplicate detection)

        ✅ FIXED: Implements LRU eviction to prevent unbounded memory growth.
        Only keeps the most recent MAX_HASH_CACHE_SIZE entries.
        """
        try:
            if self._hash_cache_file.exists():
                with open(self._hash_cache_file, 'r') as f:
                    cache_data = json.load(f)

                # ✅ FIXED: Load into OrderedDict and limit size
                # Keep only the most recent entries if cache exceeds max size
                if len(cache_data) > self.MAX_HASH_CACHE_SIZE:
                    # Keep only the last MAX_HASH_CACHE_SIZE entries
                    items = list(cache_data.items())[-self.MAX_HASH_CACHE_SIZE:]
                    self._hash_cache = OrderedDict(items)
                    logger.debug(f"   ⚡ Loaded {len(self._hash_cache)} cached hashes (trimmed from {len(cache_data)})")
                else:
                    self._hash_cache = OrderedDict(cache_data)
                    logger.debug(f"   ⚡ Loaded {len(self._hash_cache)} cached hashes from disk")
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to load hash cache: {e}")
            self._hash_cache = OrderedDict()  # Graceful fallback

    def _save_hash_cache(self) -> None:
        """
        Save hash cache to disk for future use

        ✅ FIXED: Only saves up to MAX_HASH_CACHE_SIZE most recent entries
        to prevent disk bloat.
        """
        try:
            # ✅ FIXED: Convert OrderedDict to regular dict for JSON serialization
            # OrderedDict maintains insertion order, which is preserved in Python 3.7+
            with open(self._hash_cache_file, 'w') as f:
                json.dump(dict(self._hash_cache), f, indent=2)
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to save hash cache: {e}")
            # Non-critical - continue without saving

    # ========================================
    # 🎯 URL-SPECIFIC CLICK CONFIGURATIONS
    # ========================================

    def _load_url_click_config(self) -> dict:
        """
        Load URL-specific click action configurations from JSON file.

        Returns:
            dict: Configuration dictionary with url_patterns list
        """
        config_file = Path("url_click_config.json")

        # Default empty configuration
        default_config = {
            "version": "1.0",
            "description": "URL-specific click action configurations",
            "url_patterns": []
        }

        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config
            else:
                logger.debug("   ℹ️  No url_click_config.json found - using manual click_elements only")
                return default_config
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to load url_click_config.json: {e}")
            return default_config

    def _find_url_config(self, url: str) -> dict | None:
        """
        Find matching URL configuration for the given URL.

        Args:
            url: The URL to match against configured patterns

        Returns:
            dict: Matching configuration pattern or None if no match found
        """
        if not self.url_click_config or not self.url_click_config.get("url_patterns"):
            return None

        for pattern in self.url_click_config.get("url_patterns", []):
            # Skip disabled configurations
            if not pattern.get("enabled", True):
                continue

            match_type = pattern.get("match_type", "exact")
            url_pattern = pattern.get("url_pattern", "")

            # Match based on type
            if match_type == "exact":
                if url == url_pattern:
                    return pattern
            elif match_type == "contains":
                if url_pattern in url:
                    return pattern
            elif match_type == "startswith":
                if url.startswith(url_pattern):
                    return pattern
            elif match_type == "regex":
                import re
                try:
                    if re.match(url_pattern, url):
                        return pattern
                except re.error:
                    logger.warning(f"   ⚠️  Invalid regex pattern: {url_pattern}")
                    continue

        return None

    # ========================================
    # 🎯 9 STEALTH SOLUTIONS - Helper Methods
    # ========================================

    def _get_random_user_agent(self) -> str:
        """
        Solution #2: Randomize User-Agent Strings
        Returns a random user agent from the pool
        """
        return random.choice(USER_AGENTS)

    def _get_random_viewport(self) -> dict:
        """
        Solution #6: Adjust Viewport Size and Device Emulation
        Returns a random viewport configuration
        """
        return random.choice(VIEWPORTS)

    def _convert_network_events_to_curl(self, network_events: list) -> list:
        """
        Convert network events to cURL commands
        Returns list of cURL command strings
        """
        curl_commands = []

        # Filter for request events only
        requests = [e for e in network_events if e.get('event') == 'request' and e.get('type') in ['xhr', 'fetch']]

        for req in requests:
            url = req.get('url', '')
            method = req.get('method', 'GET')
            headers = req.get('headers', {})
            post_data = req.get('post_data', '')

            # Build cURL command
            curl = f"curl -X {method}"

            # Add headers
            for key, value in headers.items():
                # Skip certain headers that shouldn't be in cURL
                if key.lower() not in ['host', 'content-length', 'connection', 'accept-encoding']:
                    curl += f" -H '{key}: {value}'"

            # Add data if POST/PUT/PATCH
            if post_data and method in ['POST', 'PUT', 'PATCH']:
                # Escape single quotes in data
                escaped_data = post_data.replace("'", "'\\''")
                curl += f" -d '{escaped_data}'"

            # Add URL
            curl += f" '{url}'"

            curl_commands.append(curl)

        return curl_commands

    def _create_network_event_handlers(self):
        """
        Create network event handlers for capturing network activity
        Returns a dict with handlers and event list
        """
        network_events = []
        api_responses = []  # ✅ NEW: Store full API responses for Network tab
        start_time = asyncio.get_event_loop().time()

        def log_request(request):
            if request.resource_type in ['xhr', 'fetch', 'document', 'websocket']:
                elapsed = asyncio.get_event_loop().time() - start_time

                # Try to get request body/post data
                post_data = None
                try:
                    post_data = request.post_data
                except Exception:  # ✅ FIXED: Specific exception instead of bare except
                    pass  # POST data not available for all request types

                network_events.append({
                    'event': 'request',
                    'type': request.resource_type,
                    'method': request.method,
                    'url': request.url,
                    'timestamp': elapsed,
                    'headers': dict(request.headers),
                    'post_data': post_data
                })

        async def log_response(response):
            if response.request.resource_type in ['xhr', 'fetch']:  # ✅ Focus on API calls
                elapsed = asyncio.get_event_loop().time() - start_time

                # ✅ NEW: Capture response body for Network tab
                response_body = None
                response_json = None
                try:
                    # ✅ FIX: Use body() instead of text() - more reliable with CDP
                    # body() returns bytes, which we decode to string
                    body_bytes = await response.body()
                    response_body = body_bytes.decode('utf-8', errors='ignore')

                    # Try to parse as JSON
                    try:
                        import json
                        response_json = json.loads(response_body)
                    except Exception:  # ✅ FIXED: Specific exception instead of bare except
                        pass  # Not JSON, keep as text
                except Exception as e:
                    # ✅ IMPROVEMENT: Only log if it's not a common CDP timing issue
                    error_msg = str(e)
                    if "No data found" not in error_msg and "No resource with given identifier" not in error_msg:
                        logger.warning(f"   ⚠️ Could not capture response body: {e}")

                # Store basic event
                network_events.append({
                    'event': 'response',
                    'type': response.request.resource_type,
                    'status': response.status,
                    'statusText': response.status_text,
                    'url': response.url,
                    'timestamp': elapsed,
                    'headers': dict(response.headers) if response.request.resource_type == 'document' else {}
                })

                # ✅ NEW: Store full API response for Network tab
                if response_json is not None:  # Only store if we got JSON
                    api_responses.append({
                        'id': f"api_{len(api_responses)}_{int(elapsed * 1000)}",
                        'method': response.request.method,
                        'url': response.url,
                        'status': response.status,
                        'statusText': response.status_text,
                        'timestamp': elapsed,
                        'request_headers': dict(response.request.headers),
                        'response_headers': dict(response.headers),
                        'request_body': response.request.post_data,
                        'response_body': response_body,
                        'response_json': response_json,
                        'captured_at': asyncio.get_event_loop().time()
                    })

        def log_request_failed(request):
            elapsed = asyncio.get_event_loop().time() - start_time
            network_events.append({
                'event': 'failed',
                'type': request.resource_type,
                'method': request.method,
                'url': request.url,
                'timestamp': elapsed,
                'failure': request.failure
            })

        def log_request_finished(request):
            if request.resource_type in ['xhr', 'fetch', 'document']:
                elapsed = asyncio.get_event_loop().time() - start_time
                network_events.append({
                    'event': 'finished',
                    'type': request.resource_type,
                    'url': request.url,
                    'timestamp': elapsed
                })

        return {
            'log_request': log_request,
            'log_response': log_response,
            'log_request_failed': log_request_failed,
            'log_request_finished': log_request_finished,
            'network_events': network_events,
            'api_responses': api_responses,  # ✅ NEW: Full API responses for Network tab
            'start_time': start_time
        }

    async def _save_cookies(self, context: BrowserContext):
        """
        Solution #5: Manage Cookies and Session Data
        Save cookies for future sessions
        """
        try:
            cookies = await context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.debug(f"   💾 Saved {len(cookies)} cookies to {self.cookies_file}")
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to save cookies: {e}")

    async def _load_cookies(self, context: BrowserContext):
        """
        Solution #5: Manage Cookies and Session Data
        Load cookies from previous sessions
        """
        try:
            if self.cookies_file.exists():
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                logger.info(f"   🍪 Loaded {len(cookies)} cookies from {self.cookies_file}")
                return True
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to load cookies: {e}")
        return False

    async def _add_random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """
        Solution #9: Implement Delays and Randomization in Actions
        Add random delay to simulate human behavior
        """
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def _simulate_realistic_mouse_movement(self, page: Page):
        """
        Solution #4: Simulate Realistic Mouse Movements and Keyboard Inputs
        Simulate human-like mouse movements with smooth transitions
        """
        try:
            # Get viewport size
            viewport = page.viewport_size
            if not viewport:
                viewport = {"width": 1366, "height": 768}

            # Random starting position
            start_x = random.randint(50, viewport["width"] - 50)
            start_y = random.randint(50, viewport["height"] - 50)

            # Move to starting position
            await page.mouse.move(start_x, start_y)

            # Perform 2-4 random movements
            num_movements = random.randint(2, 4)
            for _ in range(num_movements):
                # Random target position
                target_x = random.randint(50, viewport["width"] - 50)
                target_y = random.randint(50, viewport["height"] - 50)

                # Smooth movement with random steps
                steps = random.randint(10, 25)
                await page.mouse.move(target_x, target_y, steps=steps)

                # Random delay between movements
                await self._add_random_delay(0.1, 0.5)

            logger.debug("   🖱️  Simulated realistic mouse movements")
        except Exception as e:
            logger.warning(f"   ⚠️  Mouse simulation failed: {e}")

    async def _simulate_realistic_scrolling(self, page: Page):
        """
        Solution #4: Simulate Realistic Mouse Movements and Keyboard Inputs
        Simulate human-like scrolling behavior
        """
        try:
            # Random number of scroll actions
            num_scrolls = random.randint(2, 5)

            for _ in range(num_scrolls):
                # Random scroll amount (200-800px)
                scroll_amount = random.randint(200, 800)

                # Scroll down
                await page.evaluate(f'window.scrollBy(0, {scroll_amount})')

                # Random delay between scrolls (simulate reading)
                await self._add_random_delay(0.3, 1.0)

            # Scroll back to top
            await page.evaluate('window.scrollTo(0, 0)')
            await self._add_random_delay(0.2, 0.5)

            logger.debug("   📜 Simulated realistic scrolling")
        except Exception as e:
            logger.warning(f"   ⚠️  Scroll simulation failed: {e}")

    async def _disable_navigator_webdriver(self, page: Page):
        """
        Solution #1: Disable the navigator.webdriver Flag
        This is the most obvious automation indicator
        """
        await page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
        """)
        logger.debug("   🔒 navigator.webdriver disabled")

    async def _detect_browser_mode(self, page: Page) -> dict:
        """
        🆕 IMPROVEMENT: Detect browser mode and potential bot detection signals

        Returns:
            Dictionary with browser mode information
        """
        mode_info = await page.evaluate("""() => {
            // Detect headless mode
            const isHeadless = (
                navigator.webdriver === true ||
                /HeadlessChrome/.test(navigator.userAgent) ||
                navigator.plugins.length === 0 ||
                !navigator.languages ||
                navigator.languages.length === 0
            );

            // Detect automation
            const hasAutomationSignals = (
                window.navigator.webdriver === true ||
                window.document.__selenium_unwrapped ||
                window.document.__webdriver_evaluate ||
                window.document.__driver_evaluate ||
                window.navigator.webdriver !== undefined
            );

            // Check for common headless indicators
            const headlessIndicators = {
                webdriver: navigator.webdriver,
                plugins: navigator.plugins.length,
                languages: navigator.languages ? navigator.languages.length : 0,
                userAgent: navigator.userAgent.includes('HeadlessChrome'),
                chrome: !!window.chrome,
                permissions: !!navigator.permissions,
                connection: !!navigator.connection
            };

            return {
                isHeadless: isHeadless,
                hasAutomationSignals: hasAutomationSignals,
                indicators: headlessIndicators,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight
                },
                screen: {
                    width: window.screen.width,
                    height: window.screen.height,
                    availWidth: window.screen.availWidth,
                    availHeight: window.screen.availHeight,
                    colorDepth: window.screen.colorDepth,
                    pixelDepth: window.screen.pixelDepth
                },
                devicePixelRatio: window.devicePixelRatio
            };
        }""")

        return mode_info

    async def _get_browser(self, use_real_browser: bool = False, browser_engine: str = "playwright",
                           use_stealth: bool = False, headless: bool = False):
        """
        Get or create browser instance

        ✅ 2025 STEALTH MODES (Priority Order):
        1. Patchright: Patches CDP leaks at source (Runtime.enable, Console.enable)
        2. Rebrowser: CDP patches (fallback if Patchright not installed)
        3. Standard Playwright: Basic mode (fallback)

        Additional Options:
        - Camoufox: Firefox-based maximum stealth (optional)
        - Persistent Context: Real Chrome with persistent profile (best for HTTP/2 fingerprinting)

        Args:
            use_real_browser: Use CDP to connect to existing Chrome (ignored if True, uses CDP instead)
            browser_engine: "playwright" or "camoufox"
            use_stealth: Enable stealth mode with persistent context
            headless: Run browser in headless mode (invisible) - only applies to Standard Mode
        """
        # Determine browser mode
        use_camoufox = (browser_engine == "camoufox")
        new_mode = 'camoufox' if use_camoufox else 'playwright'

        # Close browser if switching modes
        if self.current_browser_mode is not None and self.current_browser_mode != new_mode:
            await self.close()

        # ✅ CAMOUFOX MODE: Maximum stealth with Firefox
        if use_camoufox and CAMOUFOX_AVAILABLE:
            # Check if existing browser is still alive
            browser_needs_restart = False
            if self.camoufox_browser is not None:
                try:
                    # Try to get pages to check if browser is still alive
                    pages = self.camoufox_browser.pages
                    if not pages or len(pages) == 0:
                        # Browser exists but has no pages - might be closed
                        logger.warning("   ⚠️  Camoufox browser has no pages, checking if alive...")
                        # Try to create a page to verify it's alive
                        try:
                            test_page = await self.camoufox_browser.new_page()
                            await test_page.close()
                        except Exception:
                            logger.error("   ❌ Camoufox browser is closed, will restart...")
                            browser_needs_restart = True
                            self.camoufox_browser = None
                except Exception as e:
                    logger.error(f"   ❌ Camoufox browser is closed or invalid: {str(e)}")
                    browser_needs_restart = True
                    self.camoufox_browser = None

            # Camoufox is available, use it
            if self.camoufox_browser is None:
                logger.info("🦊 Launching Camoufox browser (maximum stealth mode)...")

                # ✅ ADVANCED: Configure screen, window, and navigator properties for maximum stealth
                # Camoufox can fully spoof all properties at C++ source level (undetectable)

                # Common screen resolutions with realistic distribution
                screen_configs = [
                    {'width': 1920, 'height': 1080, 'dpr': 1.0, 'name': 'Full HD'},  # 22% market share
                    {'width': 1920, 'height': 1080, 'dpr': 1.0, 'name': 'Full HD'},  # Duplicate for higher probability
                    {'width': 1366, 'height': 768, 'dpr': 1.0, 'name': 'Laptop HD'},  # 15% market share
                    {'width': 2560, 'height': 1440, 'dpr': 1.0, 'name': '2K/QHD'},  # 8% market share
                    {'width': 1920, 'height': 1080, 'dpr': 2.0, 'name': 'Retina FHD'},  # MacBook Pro
                    {'width': 1536, 'height': 864, 'dpr': 1.0, 'name': 'Laptop HD+'},  # 4% market share
                ]
                screen_config = random.choice(screen_configs)
                screen_width = screen_config['width']
                screen_height = screen_config['height']
                device_pixel_ratio = screen_config['dpr']

                # Calculate window dimensions (outer = inner + browser chrome)
                # Windows: +16px scrollbar width, +85px chrome height (title bar + toolbar)
                # macOS: +0px scrollbar (overlay), +50px chrome height (menu bar)
                # We'll use Windows defaults as most common
                inner_width = screen_width
                inner_height = screen_height
                outer_width = inner_width + 16  # Scrollbar width
                outer_height = inner_height + 85  # Title bar + toolbar + status bar

                # Available screen area (subtract taskbar)
                # Windows taskbar: typically 40-60px
                avail_height = screen_height - random.randint(40, 60)

                camoufox_config = {
                    # ========================================
                    # SCREEN PROPERTIES (Priority 1: CRITICAL)
                    # ========================================
                    'screen.width': screen_width,
                    'screen.height': screen_height,
                    'screen.availWidth': screen_width,  # Usually matches width
                    'screen.availHeight': avail_height,  # Screen height - taskbar
                    'screen.colorDepth': 24,  # True Color (16.7M colors) - most common
                    'screen.pixelDepth': 24,  # Must match colorDepth (synonymous)

                    # ========================================
                    # WINDOW PROPERTIES (Priority 1: CRITICAL)
                    # ========================================
                    'window.innerWidth': inner_width,  # Viewport width
                    'window.innerHeight': inner_height,  # Viewport height
                    'window.outerWidth': outer_width,  # Browser window width (inner + scrollbar)
                    'window.outerHeight': outer_height,  # Browser window height (inner + chrome)
                    'window.devicePixelRatio': device_pixel_ratio,  # Physical pixels per CSS pixel

                    # Window position (Priority 2: MEDIUM)
                    # Randomize to avoid "always maximized" pattern
                    'window.screenX': random.choice([0, 0, 0, random.randint(10, 100)]),  # 75% maximized
                    'window.screenY': random.choice([0, 0, 0, random.randint(10, 100)]),  # 75% maximized

                    # Browsing history (Priority 2: MEDIUM)
                    # Randomize to simulate realistic browsing session
                    'window.history.length': random.randint(1, 10),  # 1 = direct, 10 = browsing session

                    # ========================================
                    # CANVAS ANTI-FINGERPRINTING (Priority 2: MEDIUM)
                    # ========================================
                    # Camoufox uses patched Skia rendering engine (NOT JavaScript noise injection)
                    # This modifies anti-aliasing at C++ level to mimic real hardware differences
                    # Much more sophisticated than traditional noise-based approaches
                    'canvas:aaOffset': random.randint(1, 3),  # Offset pixel transparency (1-3 is subtle)
                    'canvas:aaCapOffset': True,  # Clamp alpha to 0-255 (prevent wrap-around)

                    # ========================================
                    # GEOLOCATION & TIMEZONE (Priority 2: MEDIUM)
                    # ========================================
                    # Match Playwright's configuration for consistency
                    # Location prompts will be auto-accepted when geolocation is set
                    'geolocation:latitude': 40.7128,  # New York City latitude
                    'geolocation:longitude': -74.0060,  # New York City longitude
                    # geolocation:accuracy auto-calculated from decimal precision
                    'timezone': 'America/New_York',  # TZ timezone (affects Date() and Intl API)

                    # ========================================
                    # LOCALE/INTL (Priority 2: MEDIUM)
                    # ========================================
                    # Spoof Intl API and system language/region
                    'locale:language': 'en',  # Language code (ISO 639-1)
                    'locale:region': 'US',  # Region code (ISO 3166-1 alpha-2)
                    # locale:script auto-set to "Latn" (Latin script)
                    # locale:all auto-set to "en-US, en"

                    # ========================================
                    # HTTP HEADERS (Priority 2: MEDIUM)
                    # ========================================
                    # Override network headers sent with every HTTP request
                    # Match Playwright's configuration for consistency
                    'headers.Accept-Language': 'en-US,en;q=0.9',  # Match locale (en-US)
                    'headers.Accept-Encoding': 'gzip, deflate, br',  # Standard Firefox encoding
                    # headers.User-Agent auto-set by Camoufox based on OS and browser version

                    # ========================================
                    # AUDIOCONTEXT (Priority 2: MEDIUM)
                    # ========================================
                    # Spoof AudioContext properties to prevent audio fingerprinting
                    # Using common values for standard desktop audio hardware
                    'AudioContext:sampleRate': random.choice([44100, 48000]),  # 44.1 kHz (CD) or 48 kHz (most common)
                    'AudioContext:outputLatency': round(random.uniform(0.01, 0.02), 3),  # 10-20ms (typical range)
                    'AudioContext:maxChannelCount': 2,  # Stereo (standard for desktop)
                    # mediaDevices NOT configured (disabled by default, screenshot tool doesn't need camera/mic)

                    # ========================================
                    # MISCELLANEOUS (Priority 1: CRITICAL)
                    # ========================================
                    # PDF Viewer MUST be enabled to avoid headless detection
                    # Camoufox warning: "many websites will flag a lack of pdfViewer as a headless browser"
                    'pdfViewerEnabled': True,  # ✅ CRITICAL - All modern browsers have PDF viewer
                    # battery properties NOT configured (low impact, already spoofed by Playwright)

                    # ========================================
                    # NAVIGATOR PROPERTIES
                    # ========================================
                    'navigator.hardwareConcurrency': random.randint(4, 16),  # Randomize CPU cores
                    'navigator.maxTouchPoints': 0,  # Desktop = 0, mobile = 5-10
                    'navigator.doNotTrack': random.choice(['1', 'unspecified']),  # Randomize DNT (must be string)
                    'navigator.globalPrivacyControl': random.choice([True, False]),  # Randomize GPC

                    # ========================================
                    # CURSOR MOVEMENT (C++ implementation)
                    # ========================================
                    # Algorithm from rifosnake's HumanCursor, rewritten in C++ for performance
                    'humanize:maxTime': 2.5 if use_stealth else 1.5,  # Max time for cursor movement
                    'humanize:minTime': 0.5 if use_stealth else 0.3,  # Min time for cursor movement
                    # showcursor defaults to True (not visible to page, safe to use)
                }

                logger.info(f"   🖥️  Screen: {screen_width}x{screen_height} ({screen_config['name']}), "
                      f"DPR={device_pixel_ratio}, colorDepth={camoufox_config['screen.colorDepth']}")
                logger.info(f"   🪟 Window: inner={inner_width}x{inner_height}, outer={outer_width}x{outer_height}, "
                      f"pos=({camoufox_config['window.screenX']}, {camoufox_config['window.screenY']})")
                logger.info(f"   🎨 Canvas: aaOffset={camoufox_config['canvas:aaOffset']}, "
                      f"aaCapOffset={camoufox_config['canvas:aaCapOffset']} (Skia-level anti-aliasing)")
                logger.info(f"   🌍 Location: {camoufox_config['locale:language']}-{camoufox_config['locale:region']}, "
                      f"timezone={camoufox_config['timezone']}, "
                      f"geo=({camoufox_config['geolocation:latitude']}, {camoufox_config['geolocation:longitude']})")
                logger.info(f"   📡 Headers: Accept-Language={camoufox_config['headers.Accept-Language']}, "
                      f"Accept-Encoding={camoufox_config['headers.Accept-Encoding']}")
                logger.info(f"   🎵 Audio: sampleRate={camoufox_config['AudioContext:sampleRate']}Hz, "
                      f"latency={camoufox_config['AudioContext:outputLatency']:.3f}s, "
                      f"channels={camoufox_config['AudioContext:maxChannelCount']}")
                logger.info(f"   🎭 Navigator: {camoufox_config['navigator.hardwareConcurrency']} cores, "
                      f"DNT={camoufox_config['navigator.doNotTrack']}, "
                      f"GPC={camoufox_config['navigator.globalPrivacyControl']}, "
                      f"pdfViewer={camoufox_config['pdfViewerEnabled']}")
                logger.debug(
                    f"   🖱️  Cursor: {camoufox_config['humanize:minTime']:.1f}s - {camoufox_config['humanize:maxTime']:.1f}s "
                    f"({'stealth' if use_stealth else 'normal'} mode)")
                logger.debug(f"   📜 History: {camoufox_config['window.history.length']} entries")
                logger.debug(f"   🔒 WebRTC: BLOCKED (prevents IP leaks)")

                # ✅ PERSISTENT CONTEXT MODE: Use persistent profile for auth state
                # This maintains ALL browser state (cookies, localStorage, sessionStorage, IndexedDB, etc.)
                # Perfect for login-protected pages that need consistent sessions
                persistent_profile_dir = Path(self.output_dir).parent / "browser_sessions" / "camoufox_profile"
                persistent_profile_dir.mkdir(parents=True, exist_ok=True)

                logger.info(f"   🔐 Using persistent Camoufox profile: {persistent_profile_dir}")
                logger.info(f"   💡 This maintains ALL auth state (cookies, localStorage, sessionStorage, etc.)")

                # Camoufox automatically applies all stealth patches + custom config
                self.camoufox_browser = await AsyncCamoufox(
                    headless=headless,  # ✅ NEW: Use headless parameter instead of use_real_browser
                    humanize=True,  # ✅ Enable human-like cursor movement
                    block_webrtc=True,  # ✅ Block WebRTC to prevent IP leaks
                    config=camoufox_config,  # ✅ Custom navigator + cursor properties
                    persistent_context=True,  # ✅ Enable persistent context
                    user_data_dir=str(persistent_profile_dir),  # ✅ Store profile data
                    # OS auto-selected from ["windows", "macos", "linux"]
                    # Fingerprint auto-generated with realistic values
                    # navigator.webdriver always set to false
                    # navigator.language/languages auto-set from locale
                ).__aenter__()
                self.current_browser_mode = 'camoufox'
                logger.info("✅ Camoufox browser ready with custom fingerprint and persistent profile!")
            return self.camoufox_browser
        elif use_camoufox and not CAMOUFOX_AVAILABLE:
            # User requested Camoufox but it's not available
            logger.warning("⚠️  Camoufox not installed. Install with: pip install camoufox")
            logger.debug("   Falling back to standard Playwright mode...")
            # Continue to standard Playwright mode below

        # ✅ STANDARD MODE: Patchright, Rebrowser, or Playwright (auto-selected at import)
        if self.browser is not None and self.current_mode_is_real_browser != use_real_browser:
            await self.close()

        if self.browser is None:
            if self.playwright is None:
                self.playwright = await async_playwright().start()

            launch_args = ['--no-sandbox', '--disable-setuid-sandbox']

            if not use_real_browser:
                # MAXIMUM stealth mode args
                # These make Chrome look EXACTLY like a real browser
                # 🆕 IMPROVEMENT: Enhanced headless mode detection evasion
                launch_args.extend([
                    # Core stealth
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                ])

                # ✅ FIX: Only add --headless=new when headless mode is enabled
                if headless:
                    launch_args.extend([
                        '--headless=new',  # Use new Chrome headless mode (more realistic)

                        # Window & display
                        '--window-size=1920,1080',  # Set window size
                        '--start-maximized',  # Start maximized
                        '--force-device-scale-factor=1',  # Standard display

                        # 🆕 IMPROVEMENT: Additional headless detection evasion
                        '--disable-features=IsolateOrigins,site-per-process',  # Reduce isolation overhead
                        '--disable-site-isolation-trials',  # Disable site isolation
                        '--disable-web-security',  # Allow cross-origin (use with caution)
                        '--disable-features=VizDisplayCompositor',  # Reduce GPU overhead in headless

                        # Disable automation indicators
                        '--disable-infobars',  # Disable infobars
                        '--disable-notifications',  # Disable notifications
                        '--disable-popup-blocking',  # Allow popups
                        '--disable-save-password-bubble',  # No password save prompts

                        # Performance & networking
                        '--disable-dev-shm-usage',  # Overcome limited resource problems
                        '--enable-features=NetworkService,NetworkServiceInProcess',  # Enable HTTP/2
                        '--disable-features=IsolateOrigins,site-per-process',  # Reduce isolation

                        # ✅ PHASE 2: TLS Fingerprint Improvements (2024-2025)
                        '--disable-site-isolation-trials',  # Disable site isolation trials
                        '--disable-features=IsolateOrigins',  # Further reduce isolation for TLS
                        '--enable-features=NetworkServiceInProcess',  # Keep network in-process

                        # GPU & rendering (make it look like real Chrome)
                        '--disable-gpu',  # Disable GPU hardware acceleration
                        '--disable-software-rasterizer',  # Disable software rasterizer
                        '--disable-extensions',  # Disable extensions

                        # Additional stealth
                        '--disable-default-apps',  # Disable default apps
                        '--no-first-run',  # Skip first run wizards
                        '--no-default-browser-check',  # Skip default browser check
                        '--disable-hang-monitor',  # Disable hang monitor
                        '--disable-prompt-on-repost',  # Disable repost prompts
                        '--disable-background-networking',  # Disable background networking
                        '--disable-sync',  # Disable sync
                        '--metrics-recording-only',  # Disable reporting
                        '--disable-background-timer-throttling',  # Disable throttling
                        '--disable-backgrounding-occluded-windows',  # Disable backgrounding
                        '--disable-breakpad',  # Disable crash reporter
                        '--disable-component-extensions-with-background-pages',  # Disable background extensions
                        '--disable-features=TranslateUI',  # Disable translate
                        '--disable-ipc-flooding-protection',  # Disable IPC flooding protection
                        '--enable-automation',  # Ironically, this makes it MORE stealthy with our overrides
                        '--password-store=basic',  # Use basic password store
                        '--use-mock-keychain',  # Use mock keychain
                    ])

            # ✅ PERSISTENT CONTEXT MODE: Maximum stealth for real browser
            # Uses persistent profile to keep consistent TLS/HTTP2 behavior
            # This is the BEST approach for bypassing HTTP/2 fingerprinting
            if use_stealth and use_real_browser:
                persistent_profile_dir = Path(self.output_dir).parent / "browser_profile"
                persistent_profile_dir.mkdir(exist_ok=True)

                logger.info(f"   🔐 Using persistent browser profile: {persistent_profile_dir}")
                logger.info(f"   💡 This keeps consistent TLS/HTTP2 fingerprint across sessions")

                # ========================================
                # 🎯 9 STEALTH SOLUTIONS - Applied Here
                # ========================================
                # Solution #2: Random User-Agent
                random_user_agent = self._get_random_user_agent()
                # Solution #6: Random Viewport
                random_viewport = self._get_random_viewport()

                logger.info(f"   🎭 Using random User-Agent: {random_user_agent[:50]}...")
                logger.debug(
                    f"   📐 Using random viewport: {random_viewport['width']}x{random_viewport['height']} ({random_viewport['device_type']})")

                # Launch persistent context (browser IS the context)
                self.browser = await self.playwright.chromium.launch_persistent_context(
                    str(persistent_profile_dir),
                    headless=headless,  # ✅ NEW: Use headless parameter (headful mode reduces TLS/HTTP2 mismatches)
                    channel="chrome",  # Use real Chrome build (not Chromium)
                    args=launch_args,
                    slow_mo=50,  # Human-like speed
                    viewport={'width': random_viewport['width'], 'height': random_viewport['height']},
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                    color_scheme='light',
                    device_scale_factor=1,
                    user_agent=random_user_agent,
                )

                # For persistent context, browser IS the context
                self.is_persistent_context = True

            else:
                # Standard launch (non-persistent)
                self.browser = await self.playwright.chromium.launch(
                    headless=headless,  # ✅ NEW: Use headless parameter instead of use_real_browser
                    args=launch_args,
                    channel="chrome" if not headless else None,  # ✅ NEW: Use real Chrome for headful mode
                    slow_mo=50 if not headless else None,  # ✅ NEW: Human-like speed for headful mode
                )

                self.is_persistent_context = False

            # Remember current mode
            self.current_mode_is_real_browser = use_real_browser
            self.current_browser_mode = 'playwright'

            # ⚡ OPTIMIZATION: Reset context tracking for new browser
            self.context_page_count = 0
            self.stealth_injected = False

        # ⚡ OPTIMIZATION: Check if we need to refresh context (prevent memory leaks)
        if self.ENABLE_BROWSER_REUSE and self.context_page_count >= self.MAX_PAGES_PER_CONTEXT:
            logger.debug(f"   ♻️  Context refresh: {self.context_page_count} pages opened, recreating context...")
            await self.close()
            # Recursively call to create fresh browser
            return await self._get_browser(use_real_browser, browser_engine, use_stealth, headless)

        return self.browser

    async def _connect_to_chrome_cdp(self, cdp_url: str = "http://localhost:9223", max_retries: int = None):
        """
        🔗 Connect to an existing Chrome browser via CDP (Chrome DevTools Protocol)

        This allows us to control your already-running Chrome browser instead of launching a new one.

        Args:
            cdp_url: CDP endpoint URL (default: http://localhost:9223)
                    Chrome must be launched with --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223
            max_retries: Maximum number of connection attempts (default: 3)

        Returns:
            Browser instance connected via CDP
        """
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        # Use default if not specified
        if max_retries is None:
            max_retries = self.MAX_CDP_CONNECTION_RETRIES

        # Try to connect with retries
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.debug(f"🔄 Retry attempt {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(self.RETRY_DELAY_SEC)  # Wait between retries

                logger.info(f"🔗 Connecting to Chrome via CDP at {cdp_url}...")
                self.cdp_browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
                self.current_browser_mode = 'cdp'

                # ✅ NEW: Add disconnect handler to cleanup tab registry
                def handle_disconnect():
                    logger.error("❌ Browser disconnected!")
                    logger.info("🧹 Cleaning up tab registry...")
                    self.tab_registry.tabs.clear()
                    logger.info("✅ Tab registry cleared")

                self.cdp_browser.on("disconnected", handle_disconnect)

                logger.info("✅ Connected to Chrome via CDP!")
                return self.cdp_browser

            except Exception as e:
                error_msg = str(e)

                # If this is not the last attempt, continue to retry
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️  Connection attempt {attempt + 1} failed: {error_msg}")
                    continue

                # Last attempt failed, show detailed error
                logger.error(f"❌ Failed to connect to Chrome via CDP after {max_retries} attempts: {error_msg}")
                logger.debug("\n" + "=" * 60)
                logger.info("💡 HOW TO FIX:")
                logger.debug("=" * 60)

                if "ECONNREFUSED" in error_msg or "connect" in error_msg.lower():
                    logger.debug("\n1. Chrome is not running with remote debugging enabled.")
                    logger.debug("\n2. Run this command to launch Chrome:")
                    logger.debug("   cd project-1-child")
                    logger.debug("   ./launch-chrome-debug.sh")
                    logger.debug("\n3. Or manually launch Chrome with:")
                    logger.debug(
                        "   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223")
                    logger.debug("\n4. Make sure Chrome opens and has at least one tab")
                    logger.debug("\n5. Verify Chrome is running:")
                    logger.debug("   ./check-chrome-debug.sh")
                    logger.debug("\n6. Then try capturing screenshots again")
                else:
                    logger.debug(f"\nUnexpected error: {error_msg}")
                    logger.debug("\nTry restarting Chrome with remote debugging enabled.")

                logger.debug("=" * 60 + "\n")
                raise RuntimeError(
                    f"Cannot connect to Chrome. Please launch Chrome with remote debugging enabled. Run: ./launch-chrome-debug.sh")

    async def _get_active_tab(self):
        """
        🎯 Get the currently active tab from CDP-connected browser

        Returns:
            Page object representing the active tab
        """
        if self.cdp_browser is None:
            raise RuntimeError("Not connected to Chrome via CDP. Call _connect_to_chrome_cdp() first.")

        # Get all contexts (windows)
        contexts = self.cdp_browser.contexts
        if not contexts:
            raise RuntimeError("No browser contexts found. Make sure Chrome has at least one window open.")

        # Get the first context (main window)
        context = contexts[0]

        # Get all pages (tabs) in the context
        pages = context.pages
        if not pages:
            raise RuntimeError("No tabs found in Chrome. Make sure Chrome has at least one tab open.")

        # The last page in the list is typically the active one
        # But we'll use the first page for consistency
        active_page = pages[0] if pages else None

        if active_page is None:
            raise RuntimeError("Could not find active tab.")

        logger.info(f"🎯 Using active tab: {active_page.url}")
        self.cdp_active_page = active_page
        return active_page

    async def _create_new_tab_next_to_active(self):
        """
        🆕 Create a new tab next to the active tab in CDP-connected browser

        This prevents navigating away from the screenshot tool tab.
        Instead, opens a new tab for capturing screenshots.

        Returns:
            Page object representing the newly created tab
        """
        if self.cdp_browser is None:
            raise RuntimeError("Not connected to Chrome via CDP. Call _connect_to_chrome_cdp() first.")

        # Get all contexts (windows)
        contexts = self.cdp_browser.contexts
        if not contexts:
            raise RuntimeError("No browser contexts found. Make sure Chrome has at least one window open.")

        # Get the first context (main window)
        context = contexts[0]

        # Create a new tab in the same context with timeout
        logger.debug("🆕 Creating new tab for screenshot capture...")
        try:
            # ✅ FIX: Add 10-second timeout to prevent hanging indefinitely
            new_page = await asyncio.wait_for(context.new_page(), timeout=10.0)
            logger.info(f"✅ New tab created (will load URL here)")
            return new_page
        except asyncio.TimeoutError:
            # If new_page() hangs, try alternative approach: use existing blank tab
            logger.warning("   ⚠️  new_page() timed out, trying alternative approach...")

            # Get all existing pages
            pages = context.pages

            # Look for a blank/new tab (about:blank or chrome://newtab)
            for page in pages:
                url = page.url
                if url in ['about:blank', 'chrome://newtab/', '', 'chrome://newtab']:
                    logger.info(f"   ✅ Found existing blank tab, reusing it")
                    return page

            # If no blank tab found, just use the last page
            if pages:
                logger.warning(f"   ⚠️  No blank tab found, using last tab: {pages[-1].url}")
                return pages[-1]

            # If all else fails, raise the error
            raise RuntimeError("Failed to create or find a usable tab for screenshot capture")

    @asynccontextmanager
    async def _browser_context(
            self,
            viewport_width: int,
            viewport_height: int,
            user_agent: str = None,
            extra_headers: dict = None,
            storage_state: str = None,
            use_stealth: bool = False
    ) -> AsyncGenerator[tuple[BrowserContext, Page], None]:
        """
        ✅ PHASE 2: Context manager for browser context and page.
        Ensures proper cleanup even if exceptions occur.

        Usage:
            async with self._browser_context(...) as (context, page):
                # Use context and page
                # Automatically closed when exiting block
        """
        context = None
        page = None
        try:
            browser = await self._get_browser(use_real_browser=False, use_stealth=use_stealth, headless=True)

            # ✅ For persistent context, browser IS the context
            if self.is_persistent_context:
                context = browser  # Browser is already a BrowserContext
            else:
                # Standard context creation
                context = await browser.new_context(
                    viewport={'width': viewport_width, 'height': viewport_height},
                    user_agent=user_agent,
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers=extra_headers or {},
                    permissions=['geolocation'] if use_stealth else [],
                    geolocation={'latitude': 40.7128, 'longitude': -74.0060} if use_stealth else None,
                    color_scheme='light' if use_stealth else None,
                    device_scale_factor=1,
                    has_touch=False,
                    is_mobile=False,
                    storage_state=storage_state,
                )

            # Add navigator.webdriver override for stealth mode
            if use_stealth:
                await context.add_init_script("""
                    // Override navigator.webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // Override chrome property
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };

                    // Override permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                """)

            page = await context.new_page()

            yield context, page

        finally:
            # ✅ PHASE 2: Guaranteed cleanup
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"⚠️  Error closing page: {e}")

            # ✅ Don't close persistent context (it's the browser itself)
            if context and not self.is_persistent_context:
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"⚠️  Error closing context: {e}")

    def _get_stealth_config(
            self,
            viewport_width: int,
            viewport_height: int,
            use_stealth: bool
    ) -> Tuple[int, int, Optional[str], Dict[str, str]]:
        """
        ✅ PHASE 3: Extract duplicate stealth configuration logic.

        Returns:
            Tuple of (viewport_width, viewport_height, user_agent, extra_headers)
        """
        if not use_stealth:
            return viewport_width, viewport_height, None, {}

        # Randomize viewport to avoid fingerprinting
        viewport_width = random.randint(
            max(800, viewport_width - settings.stealth_viewport_randomization),
            viewport_width
        )
        viewport_height = random.randint(
            max(600, viewport_height - settings.stealth_viewport_randomization),
            viewport_height
        )

        # Rotate through realistic user agents
        user_agent = random.choice(settings.stealth_user_agents)

        # Enhanced HTTP headers to mimic real browser
        extra_headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }

        return viewport_width, viewport_height, user_agent, extra_headers

    async def _simulate_human_behavior(self, page: Page, use_stealth: bool = False):
        """
        ✅ 9 STEALTH SOLUTIONS - Complete Human Behavior Simulation

        Implements:
        - Solution #4: Realistic Mouse Movements and Keyboard Inputs
        - Solution #9: Random Delays and Randomization in Actions

        Based on recommendations from Cloudflare bypass guide and research:
        - Random mouse movements with steps (not instant jumps)
        - Random delays between actions
        - Realistic scrolling patterns
        - Think time before interactions
        """
        if not use_stealth:
            return

        try:
            logger.info("   🎭 Starting comprehensive human behavior simulation...")

            # ========================================
            # Solution #9: Initial page load delay
            # ========================================
            await self._add_random_delay(1.0, 2.5)

            # ========================================
            # Solution #4: Realistic mouse movements
            # ========================================
            await self._simulate_realistic_mouse_movement(page)

            # ========================================
            # Solution #9: Think time
            # ========================================
            await self._add_random_delay(0.5, 1.5)

            # ========================================
            # Solution #4: Realistic scrolling
            # ========================================
            await self._simulate_realistic_scrolling(page)

            # ========================================
            # Solution #9: Final delay before capture
            # ========================================
            await self._add_random_delay(0.3, 0.8)

            logger.info("   ✅ Human behavior simulation complete")

        except Exception as e:
            # Don't fail the whole capture if human simulation fails
            logger.warning(f"   ⚠️  Human behavior simulation failed: {e}")

    def _load_auth_state(
            self,
            cookies: str = "",
            local_storage: str = ""
    ) -> Optional[str]:
        """
        ✅ PHASE 3: Extract duplicate auth state loading logic.
        🍪 ENHANCED: Also checks for cookie extractor's storage state

        Priority:
        1. Manual cookies/localStorage (if provided)
        2. Saved auth state from manual login (auth_state.json)
        3. Cookie extractor's storage state (playwright_storage_state.json)

        Returns:
            Path to storage_state file if available, None otherwise
        """
        # Priority 1: Manual cookies/localStorage take precedence
        if cookies or local_storage:
            return None  # Will be handled by manual injection

        # Priority 2: Check if saved auth state exists (from manual login)
        if settings.auth_state_file.exists():
            logger.info(f"🔐 Loading saved auth state from {settings.auth_state_file}")

            # Verify what's in the auth state file
            try:
                with open(settings.auth_state_file, 'r') as f:
                    state_data = json.load(f)
                    cookie_count = len(state_data.get('cookies', []))
                    ls_count = sum(len(origin.get('localStorage', [])) for origin in state_data.get('origins', []))
                    logger.info(f"   📊 Auth state contains: {cookie_count} cookies, {ls_count} localStorage items")

                    # Show key cookie names for verification
                    cookie_names = [c['name'] for c in state_data.get('cookies', [])]
                    auth_cookies = [name for name in cookie_names if any(
                        keyword in name.lower() for keyword in ['token', 'session', 'auth', 'sid', 'jsession'])]
                    if auth_cookies:
                        logger.info(f"   🔑 Auth cookies found: {', '.join(auth_cookies[:5])}")  # Show first 5

                    # Show key localStorage items for verification
                    for origin in state_data.get('origins', []):
                        ls_items = origin.get('localStorage', [])
                        ls_names = [item['name'] for item in ls_items]
                        auth_ls = [name for name in ls_names if
                                   any(keyword in name.lower() for keyword in ['token', 'auth', 'user', 'session'])]
                        if auth_ls:
                            logger.info(f"   💾 localStorage auth items: {', '.join(auth_ls[:5])}")  # Show first 5
                            break
            except Exception as e:
                logger.warning(f"   ⚠️  Could not verify auth state contents: {str(e)}")

            return str(settings.auth_state_file)

        # Priority 3: Check for cookie extractor's storage state
        cookie_extractor_storage = Path("browser_sessions/playwright_storage_state.json")
        if cookie_extractor_storage.exists():
            logger.info(f"🍪 Loading cookies from cookie extractor: {cookie_extractor_storage}")

            # Verify what's in the storage state
            try:
                with open(cookie_extractor_storage, 'r') as f:
                    state_data = json.load(f)
                    cookie_count = len(state_data.get('cookies', []))
                    extracted_at = state_data.get('metadata', {}).get('extracted_at', 'Unknown')
                    logger.info(f"   📊 Contains: {cookie_count} cookies")
                    logger.debug(f"   📅 Extracted at: {extracted_at}")

                    # Show domains
                    domains = list(set(c.get('domain', '') for c in state_data.get('cookies', [])))
                    if domains:
                        logger.info(f"   🌐 Domains: {', '.join(domains[:5])}")  # Show first 5
            except Exception as e:
                logger.warning(f"   ⚠️  Could not verify cookie extractor storage: {str(e)}")

            return str(cookie_extractor_storage)

        return None

    async def _setup_cross_domain_cookies(
            self,
            context: BrowserContext,
            storage_state_path: str
    ):
        """
        🔧 CROSS-DOMAIN COOKIE SUPPORT
        
        When auth state contains cookies for multiple domains (e.g., preprodapp.tekioncloud.com
        and employee.tekion.com for SSO), we need to visit each domain to set cookies.
        
        This is necessary because browsers don't send cookies across different domains.
        """
        import json
        from pathlib import Path

        try:
            # Load auth state to get all cookies
            with open(storage_state_path, 'r') as f:
                state_data = json.load(f)

            cookies = state_data.get('cookies', [])

            # Group cookies by domain
            cookies_by_domain = {}
            for cookie in cookies:
                domain = cookie.get('domain', '')
                if domain not in cookies_by_domain:
                    cookies_by_domain[domain] = []
                cookies_by_domain[domain].append(cookie)

            logger.info(f"   🔧 Cross-domain cookie setup: {len(cookies_by_domain)} domains")

            # Visit each domain to set cookies
            for domain, domain_cookies in cookies_by_domain.items():
                # Skip if no cookies for this domain
                if not domain_cookies:
                    continue

                # Construct URL for this domain
                # Use https:// for all domains
                domain_url = f"https://{domain.lstrip('.')}"

                logger.debug(f"   �� Setting {len(domain_cookies)} cookies for {domain}")

                # Create a temporary page to visit the domain
                temp_page = await context.new_page()

                try:
                    # Navigate to the domain (with short timeout)
                    await temp_page.goto(domain_url, wait_until='domcontentloaded', timeout=self.DOMAIN_NAVIGATION_TIMEOUT_MS)

                    # Cookies should now be set by Playwright from storage_state
                    # Verify they're actually there
                    actual_cookies = await context.cookies(domain_url)

                    # Show which auth cookies are active
                    auth_cookies = [c for c in actual_cookies if any(keyword in c['name'].lower()
                                                                     for keyword in
                                                                     ['token', 'session', 'auth', 'sid', 'jsession'])]

                    if auth_cookies:
                        logger.info(
                            f"      ✅ {len(auth_cookies)} auth cookies active: {', '.join([c['name'] for c in auth_cookies[:3]])}")
                    else:
                        logger.warning(f"      ⚠️  No auth cookies found for {domain}")

                except Exception as e:
                    logger.warning(f"      ⚠️  Could not visit {domain_url}: {str(e)[:100]}")
                finally:
                    # Close the temporary page
                    await temp_page.close()

            logger.info(f"   ✅ Cross-domain cookie setup complete")

        except Exception as e:
            logger.warning(f"   ⚠️  Cross-domain cookie setup failed: {str(e)}")

    async def _debug_cookies_before_navigation(
            self,
            context: BrowserContext,
            url: str
    ):
        """
        🔍 DEBUG: Show which cookies will be sent to the target URL
        """
        try:
            # Get cookies that will be sent to this URL
            cookies = await context.cookies(url)

            logger.debug(f"   🔍 Cookies that will be sent to {url}:")
            logger.info(f"      📊 Total: {len(cookies)}")

            # Show auth-related cookies
            auth_cookies = [c for c in cookies if any(keyword in c['name'].lower()
                                                      for keyword in ['token', 'session', 'auth', 'sid', 'jsession'])]

            if auth_cookies:
                logger.debug(f"      🔑 Auth cookies: {', '.join([c['name'] for c in auth_cookies])}")

                # Show cookie details
                import time
                for cookie in auth_cookies[:3]:  # Show first 3
                    domain = cookie.get('domain', 'N/A')
                    expires = cookie.get('expires', -1)

                    if expires == -1:
                        expiry = "Session"
                    elif expires < time.time():
                        expiry = "❌ EXPIRED"
                    else:
                        expiry = "✅ Valid"

                    logger.debug(f"         • {cookie['name']}: domain={domain}, {expiry}")
            else:
                logger.warning(f"      ⚠️  WARNING: No auth cookies will be sent!")
                logger.info(f"      💡 This may cause authentication to fail!")

        except Exception as e:
            logger.warning(f"   ⚠️  Cookie debug failed: {str(e)}")

    async def _setup_cross_domain_cookies(
            self,
            context: BrowserContext,
            storage_state_path: str
    ):
        """
        🔧 CROSS-DOMAIN COOKIE SUPPORT
        
        When auth state contains cookies for multiple domains (e.g., preprodapp.tekioncloud.com
        and employee.tekion.com for SSO), we need to visit each domain to set cookies.
        
        This is necessary because browsers don't send cookies across different domains.
        """
        import json
        from pathlib import Path

        try:
            # Load auth state to get all cookies
            with open(storage_state_path, 'r') as f:
                state_data = json.load(f)

            cookies = state_data.get('cookies', [])

            # Group cookies by domain
            cookies_by_domain = {}
            for cookie in cookies:
                domain = cookie.get('domain', '')
                if domain not in cookies_by_domain:
                    cookies_by_domain[domain] = []
                cookies_by_domain[domain].append(cookie)

            logger.info(f"   🔧 Cross-domain cookie setup: {len(cookies_by_domain)} domains")

            # Visit each domain to set cookies
            for domain, domain_cookies in cookies_by_domain.items():
                # Skip if no cookies for this domain
                if not domain_cookies:
                    continue

                # Construct URL for this domain
                # Use https:// for all domains
                domain_url = f"https://{domain.lstrip('.')}"

                logger.debug(f"   �� Setting {len(domain_cookies)} cookies for {domain}")

                # Create a temporary page to visit the domain
                temp_page = await context.new_page()

                try:
                    # Navigate to the domain (with short timeout)
                    await temp_page.goto(domain_url, wait_until='domcontentloaded', timeout=10000)

                    # Cookies should now be set by Playwright from storage_state
                    # Verify they're actually there
                    actual_cookies = await context.cookies(domain_url)

                    # Show which auth cookies are active
                    auth_cookies = [c for c in actual_cookies if any(keyword in c['name'].lower()
                                                                     for keyword in
                                                                     ['token', 'session', 'auth', 'sid', 'jsession'])]

                    if auth_cookies:
                        logger.info(
                            f"      ✅ {len(auth_cookies)} auth cookies active: {', '.join([c['name'] for c in auth_cookies[:3]])}")
                    else:
                        logger.warning(f"      ⚠️  No auth cookies found for {domain}")

                except Exception as e:
                    logger.warning(f"      ⚠️  Could not visit {domain_url}: {str(e)[:100]}")
                finally:
                    # Close the temporary page
                    await temp_page.close()

            logger.info(f"   ✅ Cross-domain cookie setup complete")

        except Exception as e:
            logger.warning(f"   ⚠️  Cross-domain cookie setup failed: {str(e)}")

    async def _debug_cookies_before_navigation(
            self,
            context: BrowserContext,
            url: str
    ):
        """
        🔍 DEBUG: Show which cookies will be sent to the target URL
        """
        try:
            # Get cookies that will be sent to this URL
            cookies = await context.cookies(url)

            logger.debug(f"   🔍 Cookies that will be sent to {url}:")
            logger.info(f"      📊 Total: {len(cookies)}")

            # Show auth-related cookies
            auth_cookies = [c for c in cookies if any(keyword in c['name'].lower()
                                                      for keyword in ['token', 'session', 'auth', 'sid', 'jsession'])]

            if auth_cookies:
                logger.debug(f"      🔑 Auth cookies: {', '.join([c['name'] for c in auth_cookies])}")

                # Show cookie details
                import time
                for cookie in auth_cookies[:3]:  # Show first 3
                    domain = cookie.get('domain', 'N/A')
                    expires = cookie.get('expires', -1)

                    if expires == -1:
                        expiry = "Session"
                    elif expires < time.time():
                        expiry = "❌ EXPIRED"
                    else:
                        expiry = "✅ Valid"

                    logger.debug(f"         • {cookie['name']}: domain={domain}, {expiry}")
            else:
                logger.warning(f"      ⚠️  WARNING: No auth cookies will be sent!")
                logger.info(f"      💡 This may cause authentication to fail!")

        except Exception as e:
            logger.warning(f"   ⚠️  Cookie debug failed: {str(e)}")

    async def _apply_cookies_and_storage(
            self,
            context: BrowserContext,
            cookies: str = "",
            local_storage: str = ""
    ):
        """
        ✅ PHASE 3: Extract duplicate cookies and localStorage loading logic.
        """
        # Load cookies if provided
        if cookies and cookies.strip():
            try:
                cookies_list = json.loads(cookies)
                if isinstance(cookies_list, list) and len(cookies_list) > 0:
                    logger.info(f"🍪 Loading {len(cookies_list)} cookies...")
                    for cookie in cookies_list:
                        logger.debug(f"  - {cookie.get('name', 'unknown')}: domain={cookie.get('domain', 'N/A')}")
                    await context.add_cookies(cookies_list)
                    logger.info(f"✅ Cookies loaded successfully!")
                else:
                    logger.warning(f"⚠️ Cookies JSON is empty or not an array")
            except Exception as e:
                logger.error(f"❌ Failed to load cookies: {e}")
                import traceback
                traceback.print_exc()

        # Inject localStorage if provided
        if local_storage and local_storage.strip():
            try:
                ls_data = json.loads(local_storage)
                if isinstance(ls_data, dict) and len(ls_data) > 0:
                    logger.debug(f"💾 Loading {len(ls_data)} localStorage items...")
                    # Show first few keys (truncate if too many)
                    keys = list(ls_data.keys())[:5]
                    for key in keys:
                        logger.debug(f"  - {key}")
                    if len(ls_data) > 5:
                        logger.debug(f"  ... and {len(ls_data) - 5} more items")

                    # ✅ FIX: Use official Playwright pattern for localStorage injection
                    # This passes ls_data as a parameter (not string interpolation)
                    # and runs at the earliest possible moment before app JavaScript
                    # Source: https://playwright.dev/docs/auth#session-storage
                    await context.add_init_script("""
                        (storage) => {
                            // Only inject for the correct domain to prevent leaks
                            if (window.location.hostname === 'preprodapp.tekioncloud.com' ||
                                window.location.hostname.includes('tekion')) {
                                for (const [key, value] of Object.entries(storage)) {
                                    window.localStorage.setItem(key, value);
                                }
                            }
                        }
                    """, ls_data)
                    logger.info(f"✅ localStorage loaded successfully (enhanced injection)!")
                else:
                    logger.warning(f"⚠️ localStorage JSON is empty or not an object")
            except Exception as e:
                logger.error(f"❌ Failed to load localStorage: {e}")
                import traceback
                traceback.print_exc()

    # ========================================
    # 🥷 STEALTH MODE ENHANCEMENTS (2024-2025)
    # ========================================

    async def _apply_canvas_webgl_randomization(self, page: Page):
        """
        ✅ PHASE 1: Canvas & WebGL Fingerprint Randomization

        Injects noise into canvas and WebGL rendering to prevent fingerprinting.
        This is the #1 detection method used by anti-bots in 2024-2025.

        Sources: ScrapingAnt Oct 2024, Reddit r/webscraping Dec 2024
        """
        await page.add_init_script("""
            // ========================================
            // Canvas Fingerprint Randomization
            // ========================================
            (function() {
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                const originalToBlob = HTMLCanvasElement.prototype.toBlob;
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

                // Add random noise to canvas data
                const addNoise = (imageData) => {
                    const data = imageData.data;
                    const noise = Math.random() * 10 - 5; // Random noise between -5 and 5

                    // Add noise to random pixels (10% of pixels)
                    for (let i = 0; i < data.length; i += 40) {
                        data[i] = Math.min(255, Math.max(0, data[i] + noise));
                    }
                    return imageData;
                };

                // Override toDataURL
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    const context = this.getContext('2d');
                    if (context) {
                        try {
                            const imageData = context.getImageData(0, 0, this.width, this.height);
                            addNoise(imageData);
                            context.putImageData(imageData, 0, 0);
                        } catch (e) {
                            // Ignore errors (e.g., tainted canvas)
                        }
                    }
                    return originalToDataURL.apply(this, arguments);
                };

                // Override toBlob
                HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {
                    const context = this.getContext('2d');
                    if (context) {
                        try {
                            const imageData = context.getImageData(0, 0, this.width, this.height);
                            addNoise(imageData);
                            context.putImageData(imageData, 0, 0);
                        } catch (e) {
                            // Ignore errors
                        }
                    }
                    return originalToBlob.apply(this, arguments);
                };

                // Override getImageData
                CanvasRenderingContext2D.prototype.getImageData = function() {
                    const imageData = originalGetImageData.apply(this, arguments);
                    return addNoise(imageData);
                };
            })();

            // ========================================
            // WebGL Fingerprint Randomization
            // ========================================
            (function() {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                const getParameterWebGL2 = WebGL2RenderingContext.prototype.getParameter;

                // Randomize WebGL parameters
                const randomizeParameter = function(parameter) {
                    // UNMASKED_VENDOR_WEBGL
                    if (parameter === 37445) {
                        const vendors = ['Intel Inc.', 'Google Inc.', 'NVIDIA Corporation', 'AMD'];
                        return vendors[Math.floor(Math.random() * vendors.length)];
                    }

                    // UNMASKED_RENDERER_WEBGL
                    if (parameter === 37446) {
                        const renderers = [
                            'Intel Iris OpenGL Engine',
                            'ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.1)',
                            'ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)',
                            'AMD Radeon Pro 5500M OpenGL Engine'
                        ];
                        return renderers[Math.floor(Math.random() * renderers.length)];
                    }

                    return getParameter.apply(this, arguments);
                };

                // Override for WebGL 1.0
                WebGLRenderingContext.prototype.getParameter = randomizeParameter;

                // Override for WebGL 2.0
                WebGL2RenderingContext.prototype.getParameter = randomizeParameter;

                // Randomize WebGL extensions
                const getSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
                WebGLRenderingContext.prototype.getSupportedExtensions = function() {
                    const extensions = getSupportedExtensions.apply(this, arguments);
                    // Randomly remove 1-2 extensions to vary fingerprint
                    if (extensions && extensions.length > 5) {
                        const toRemove = Math.floor(Math.random() * 2) + 1;
                        for (let i = 0; i < toRemove; i++) {
                            const idx = Math.floor(Math.random() * extensions.length);
                            extensions.splice(idx, 1);
                        }
                    }
                    return extensions;
                };
            })();
        """)
        logger.debug("   🎨 Canvas & WebGL fingerprint randomization applied")

    async def _apply_cdp_detection_bypass(self, page: Page):
        """
        ✅ PHASE 1: CDP (Chrome DevTools Protocol) Detection Bypass

        Hides traces of Chrome DevTools Protocol to prevent detection.
        Advanced anti-bots detect CDP usage to identify automation tools.

        Sources: GitHub dgtlmoon Feb 2024, ScrapingAnt Sep 2024
        """
        await page.add_init_script("""
            // ========================================
            // CDP Detection Bypass
            // ========================================
            (function() {
                // Remove CDP runtime variables
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;

                // Override navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });

                // Override chrome runtime
                if (window.chrome) {
                    Object.defineProperty(window.chrome, 'runtime', {
                        get: () => undefined,
                        configurable: true
                    });
                }

                // Hide automation flags
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: ""},
                            description: "",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ],
                    configurable: true
                });

                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({state: Notification.permission}) :
                        originalQuery(parameters)
                );
            })();
        """)
        logger.debug("   🔒 CDP detection bypass applied")

    async def _apply_audio_context_randomization(self, page: Page):
        """
        ✅ PHASE 1: Audio Context Fingerprint Randomization

        Randomizes audio API fingerprints by adding noise to oscillator frequencies.
        Some websites use audio context for fingerprinting.

        Sources: Medium Aug 2024, ArXiv Feb 2025
        """
        await page.add_init_script("""
            // ========================================
            // Audio Context Randomization
            // ========================================
            (function() {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (!AudioContext) return;

                const originalCreateOscillator = AudioContext.prototype.createOscillator;
                const originalCreateDynamicsCompressor = AudioContext.prototype.createDynamicsCompressor;

                // Randomize oscillator
                AudioContext.prototype.createOscillator = function() {
                    const oscillator = originalCreateOscillator.apply(this, arguments);
                    const originalStart = oscillator.start;

                    oscillator.start = function() {
                        // Add random frequency offset (-10 to +10 Hz)
                        const offset = Math.random() * 20 - 10;
                        oscillator.frequency.value += offset;
                        return originalStart.apply(this, arguments);
                    };

                    return oscillator;
                };

                // Randomize dynamics compressor
                AudioContext.prototype.createDynamicsCompressor = function() {
                    const compressor = originalCreateDynamicsCompressor.apply(this, arguments);

                    // Add slight randomization to compressor parameters
                    if (compressor.threshold) {
                        compressor.threshold.value += Math.random() * 2 - 1;
                    }
                    if (compressor.knee) {
                        compressor.knee.value += Math.random() * 2 - 1;
                    }
                    if (compressor.ratio) {
                        compressor.ratio.value += Math.random() * 0.5 - 0.25;
                    }

                    return compressor;
                };
            })();
        """)
        logger.debug("   🔊 Audio context randomization applied")

    async def _apply_behavioral_randomization(self, page: Page):
        """
        ✅ PHASE 2: Behavioral Randomization

        Simulates human-like behavior with mouse movements, scrolling, and timing delays.
        Modern anti-bots analyze behavioral patterns to detect automation.

        Sources: AgentQL Nov 2024, ScrapingAnt Sep 2024
        """
        try:
            # Random mouse movements (2-5 movements)
            num_movements = random.randint(2, 5)
            for _ in range(num_movements):
                x = random.randint(100, 1200)
                y = random.randint(100, 800)
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.05, 0.15))

            # Random scroll with smooth behavior
            scroll_amount = random.randint(100, 500)
            await page.evaluate(f"""
                window.scrollTo({{
                    top: {scroll_amount},
                    behavior: 'smooth'
                }});
            """)
            await asyncio.sleep(random.uniform(0.3, 0.8))

            # Occasionally click somewhere random (30% chance)
            if random.random() > 0.7:
                x = random.randint(200, 1000)
                y = random.randint(200, 700)
                try:
                    await page.mouse.click(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                except Exception:  # ✅ FIXED: Specific exception instead of bare except
                    pass  # Ignore click errors (element may not be clickable)

            # Random typing simulation (20% chance)
            if random.random() > 0.8:
                await page.keyboard.press('Tab')
                await asyncio.sleep(random.uniform(0.1, 0.2))

            logger.debug("   🤖 Human-like behavior simulation applied")
        except Exception as e:
            # Don't fail if behavioral randomization fails
            logger.warning(f"   ⚠️  Behavioral randomization warning: {e}")

    async def _apply_all_stealth_enhancements(self, page: Page, use_behavioral: bool = True):
        """
        Apply all stealth enhancements in the correct order.

        Args:
            page: Playwright page object
            use_behavioral: Whether to apply behavioral randomization (default: True)
        """
        # Phase 1: Fingerprint randomization (always apply)
        await self._apply_canvas_webgl_randomization(page)
        await self._apply_cdp_detection_bypass(page)
        await self._apply_audio_context_randomization(page)

        # Phase 2: Behavioral randomization (optional, after page load)
        if use_behavioral:
            await self._apply_behavioral_randomization(page)

    async def capture(
            self,
            url: str,
            viewport_width: int = 1920,
            viewport_height: int = 1080,
            full_page: bool = True,
            timeout: int = 30000,
            screenshot_timeout: int = 30000,  # ✅ NEW: Screenshot-specific timeout
            use_stealth: bool = False,
            use_real_browser: bool = False,
            headless: bool = False,  # ✅ FIX: Default to headful (visible browser) - Real Browser Mode is always visible
            browser_engine: str = "playwright",  # "playwright" or "camoufox"
            base_url: str = "",
            words_to_remove: str = "",
            cookies: str = "",
            local_storage: str = "",
            track_network: bool = False,  # ✅ NEW: Network event tracking
            auto_expand_dropdowns: bool = False,  # ✅ NEW: Auto expand collapsed sections
            click_elements: list = None,  # ✅ NEW: Click elements before screenshot
            non_scrollable_urls: str = ""  # ✅ NEW: Non-scrollable URL patterns (JSON string)
    ) -> str:
        """
        Capture screenshot of a URL

        Args:
            url: URL to capture
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            full_page: Capture full page or just viewport
            timeout: Page load timeout in milliseconds
            use_stealth: Enable stealth mode (anti-bot detection)
            use_real_browser: Use active tab from existing Chrome browser (CDP mode)
            headless: Run browser in headless mode (invisible) - only applies to Standard Mode
            browser_engine: Browser engine to use ("playwright" or "camoufox")

        Returns:
            Path to saved screenshot
        """
        # 🔗 ACTIVE TAB MODE: Connect to existing Chrome browser via CDP
        if use_real_browser:
            from datetime import datetime  # ✅ FIX: Local import to avoid scoping issues
            logger.info("🔗 Active Tab Mode: Using your existing Chrome browser")
            new_tab = None
            try:
                # Connect to Chrome via CDP if not already connected
                if self.cdp_browser is None:
                    await self._connect_to_chrome_cdp()

                # Create a new tab next to the active tab (don't navigate the current tab)
                new_tab = await self._create_new_tab_next_to_active()

                # ✅ NEW: Register tab in registry
                await self.tab_registry.register_tab(url, new_tab)

                # Navigate to the URL in the new tab
                logger.info(f"🌐 Loading {url} in new tab...")
                try:
                    # Try networkidle first (best for fully loaded pages)
                    await new_tab.goto(url, wait_until='networkidle', timeout=timeout)
                    logger.info("   ✅ Page loaded in new tab (network idle)")
                except Exception as e:
                    # If networkidle times out, fall back to load event
                    logger.warning(f"   ⚠️  Network idle timeout, using load event instead...")
                    await new_tab.goto(url, wait_until='load', timeout=timeout)
                    logger.info("   ✅ Page loaded in new tab (load event)")

                # Wait for page to be fully loaded and any lazy content
                logger.debug("   ⏳ Waiting for lazy-loaded content...")
                await asyncio.sleep(self.LAZY_CONTENT_WAIT_SEC)

                # ✅ NEW: Auto-expand dropdowns if enabled (global setting)
                if auto_expand_dropdowns:
                    await self._expand_all_dropdowns(new_tab)
                    # ⏱️ CRITICAL: Wait for page to settle after expansion
                    logger.debug("   ⏱️  Waiting for page to settle after dropdown expansion...")
                    await asyncio.sleep(self.DROPDOWN_SETTLE_DELAY_SEC)
                    logger.info("   ✅ Page settled, ready to capture...")

                # ✅ NEW: Click elements - check URL config first, then manual parameter
                url_config = self._find_url_config(url)
                per_url_auto_expand = bool(url_config.get("auto_expand_dropdowns")) if url_config else False

                if url_config:
                    # Use saved URL-specific configuration
                    logger.info(f"📋 Found saved configuration: '{url_config.get('name', 'Unnamed')}'")
                    actions = url_config.get("actions", [])

                    for i, action in enumerate(actions, 1):
                        if action.get("type") == "click":
                            text = action.get("text", "")
                            wait_ms = action.get("wait_after_ms", 2000)
                            description = action.get("description", "")

                            logger.debug(f"   🖱️  Action {i}/{len(actions)}: Click '{text}'")
                            if description:
                                logger.debug(f"      ℹ️  {description}")

                            await self._click_elements_by_text(new_tab, [text])
                            await asyncio.sleep(wait_ms / 1000)

                    logger.info("   ✅ All configured actions completed")

                    # 🔽 URL-specific dropdown expansion after configured actions
                    if per_url_auto_expand:
                        logger.info("   🔽 URL config requested dropdown auto-expansion after actions")
                        await self._expand_all_dropdowns(new_tab)
                        logger.debug("   ⏱️  Waiting for page to settle after URL-specific dropdown expansion...")
                        await asyncio.sleep(self.DROPDOWN_SETTLE_DELAY_SEC)
                        logger.info("   ✅ URL-specific dropdown expansion complete")

                elif click_elements:
                    # Use manual click_elements parameter (backward compatibility)
                    logger.debug(f"🖱️  Using manual click elements: {click_elements}")
                    await self._click_elements_by_text(new_tab, click_elements)
                    logger.debug("   ⏱️  Waiting for modals/dialogs to appear...")
                    await asyncio.sleep(self.MODAL_APPEAR_DELAY_SEC)
                    logger.info("   ✅ Ready to capture...")

                # Take screenshot
                # ✅ IMPORTANT: In fullpage mode, Playwright auto-detects new height after expansion
                timestamp = int(datetime.now().timestamp() * 1000)
                filename = f"screenshot_{timestamp}.png"
                filepath = self.output_dir / filename

                await new_tab.screenshot(path=str(filepath), full_page=full_page, timeout=screenshot_timeout)
                logger.info(f"✅ Screenshot saved: {filepath}")

                # ✅ IMPROVED: Better error handling for tab closing
                logger.info(f"📸 Capture complete for {url}, closing tab...")
                await self.tab_registry.mark_success(url)
                logger.info("⏱️  Waiting before closing tab...")
                await asyncio.sleep(self.TAB_CLOSE_DELAY_SEC)

                try:
                    # Check if tab is still open before attempting to close
                    if not new_tab.is_closed():
                        await new_tab.close()
                        logger.info(f"✅ Tab closed successfully: {url}")
                    else:
                        logger.info(f"ℹ️  Tab was already closed: {url}")
                except Exception as close_error:
                    logger.warning(f"⚠️  Error closing tab for {url}: {close_error}")
                    logger.warning(f"   Tab state: is_closed={new_tab.is_closed() if hasattr(new_tab, 'is_closed') else 'unknown'}")
                finally:
                    # Always remove from registry, even if close failed
                    self.tab_registry.tabs.pop(url, None)
                    logger.info(f"🧹 Removed {url} from tab registry")

                return str(filepath)

            except Exception as e:
                # ✅ NEW: Mark as failure (keep tab open for debugging)
                if url in self.tab_registry.tabs:
                    await self.tab_registry.mark_failure(url)
                    logger.warning(f"⚠️  Tab left open for debugging: {url}")

                logger.error(f"❌ Active Tab Mode failed: {e}")
                logger.debug("\n💡 Make sure Chrome is running with remote debugging enabled:")
                logger.debug(
                    "   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223")
                raise

        # ✅ STANDARD MODE: Launch new browser or use existing
        # Get browser (will auto-switch modes if needed)
        # ✅ 2025: Support Camoufox for maximum stealth
        browser = await self._get_browser(use_real_browser=False, browser_engine=browser_engine,
                                          use_stealth=use_stealth, headless=headless)

        # ✅ PHASE 3: Use helper method for stealth configuration
        viewport_width, viewport_height, user_agent, extra_headers = self._get_stealth_config(
            viewport_width, viewport_height, use_stealth and not use_real_browser
        )

        # ✅ PHASE 3: Use helper method for auth state loading
        storage_state = self._load_auth_state(cookies, local_storage)

        # ✅ FIX: Check if browser is actually a persistent context (Camoufox or persistent Playwright)
        # Persistent contexts ARE the context, not a browser that creates contexts
        is_persistent_context = (browser_engine == "camoufox" and CAMOUFOX_AVAILABLE) or \
                                (hasattr(browser, 'pages') and not hasattr(browser, 'new_context'))

        if is_persistent_context:
            # Browser IS the context (persistent context mode)
            context = browser
            logger.info("   🔐 Using persistent context (browser IS the context)")
        else:
            # Standard browser mode - create a new context
            context = await browser.new_context(
                viewport={'width': viewport_width, 'height': viewport_height},
                user_agent=user_agent,
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers=extra_headers,
                # Additional stealth settings
                permissions=['geolocation'] if use_stealth else [],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060} if use_stealth else None,  # New York
                color_scheme='light' if use_stealth else None,
                device_scale_factor=1,
                has_touch=False,  # Desktop browser
                is_mobile=False,  # Not mobile
                storage_state=storage_state,  # Load saved auth state if available
            )

        # Note: Manual stealth JavaScript removed - now using playwright-stealth library
        # The library handles all stealth techniques automatically and more comprehensively

        # ✅ PHASE 3: Use helper method for cookies and localStorage
        # Only apply if NOT using persistent context (persistent context already has auth state)
        if not is_persistent_context:
            await self._apply_cookies_and_storage(context, cookies, local_storage)

        page = await context.new_page()

        # Apply stealth mode using playwright-stealth library + 2024-2025 enhancements
        if use_stealth and not use_real_browser:
            logger.debug("   🥷 Applying playwright-stealth library...")
            await stealth_async(page)
            logger.info("   ✅ Stealth mode activated!")

            # ========================================
            # 🎯 9 STEALTH SOLUTIONS - Applied Here
            # ========================================
            logger.info("   🚀 Applying 9 stealth solutions (2025)...")

            # Solution #1: Disable navigator.webdriver (CRITICAL)
            await self._disable_navigator_webdriver(page)

            # Solution #5: Load cookies from previous sessions
            # ✅ FIX: Only load cookies.json if we didn't already load auth state
            if not storage_state:
                await self._load_cookies(context)

            # Apply 2024-2025 stealth enhancements (Phase 1 & 2)
            await self._apply_canvas_webgl_randomization(page)
            await self._apply_cdp_detection_bypass(page)
            await self._apply_audio_context_randomization(page)
            logger.info("   ✅ All 9 stealth solutions applied!")

        # Verify cookies and localStorage are actually loaded (runtime verification)
        if storage_state:
            try:
                # Check cookies
                loaded_cookies = await context.cookies()
                logger.info(f"   ✅ Runtime verification: {len(loaded_cookies)} cookies loaded in browser context")

                # Show key auth cookies
                auth_cookie_names = [c['name'] for c in loaded_cookies if any(
                    keyword in c['name'].lower() for keyword in ['token', 'session', 'auth', 'sid', 'jsession'])]
                if auth_cookie_names:
                    logger.info(f"   🔑 Active auth cookies: {', '.join(auth_cookie_names[:5])}")
                else:
                    logger.warning(f"   ⚠️  WARNING: No auth cookies found in browser context!")

                # Check localStorage (need to navigate first, so we'll check after goto)
            except Exception as e:
                logger.warning(f"   ⚠️  Could not verify runtime cookies: {str(e)}")

            # Additional JavaScript injections for enhanced stealth
            await page.add_init_script("""
                // Override the permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Add realistic battery API
                Object.defineProperty(navigator, 'getBattery', {
                    value: () => Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 0.95,
                        addEventListener: () => {},
                        removeEventListener: () => {},
                        dispatchEvent: () => true,
                    })
                });

                // Mock connection API
                Object.defineProperty(navigator, 'connection', {
                    value: {
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false,
                    },
                    writable: false
                });

                // Add realistic screen properties
                Object.defineProperty(screen, 'availWidth', {
                    get: () => window.screen.width
                });
                Object.defineProperty(screen, 'availHeight', {
                    get: () => window.screen.height - 40
                });
            """)

        try:
            # 🔧 CROSS-DOMAIN COOKIE SETUP: If auth state was loaded, set up cookies for all domains
            if storage_state:
                await self._setup_cross_domain_cookies(context, storage_state)

            # 🔍 DEBUG: Show which cookies will be sent to the target URL
            await self._debug_cookies_before_navigation(context, url)

            # Enhanced stealth navigation (works for both headless and real browser)
            if use_stealth:
                # Use longer timeout for stealth mode (Cloudflare challenges take time)
                stealth_timeout = 60000  # 60 seconds

                # Try multiple navigation strategies for sites with strong bot detection
                navigation_success = False
                last_error = None

                # Strategy 1: Try domcontentloaded first
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=stealth_timeout)
                    navigation_success = True
                except Exception as e:
                    last_error = e
                    error_msg = str(e)

                    # Check if it's HTTP2 protocol error (strong bot detection)
                    if 'ERR_HTTP2_PROTOCOL_ERROR' in error_msg or 'ERR_CONNECTION_REFUSED' in error_msg:
                        logger.warning(f"   ⚠️  Network-level bot detection detected, trying alternative approach...")

                        # Strategy 2: Try with 'load' event instead
                        try:
                            await page.goto(url, wait_until='load', timeout=stealth_timeout)
                            navigation_success = True
                            last_error = None
                        except Exception as e2:
                            last_error = e2
                            logger.warning(f"   ⚠️  Alternative approach failed, trying commit event...")

                            # Strategy 3: Try with 'commit' event (most lenient)
                            try:
                                await page.goto(url, wait_until='commit', timeout=stealth_timeout)
                                navigation_success = True
                                last_error = None
                            except Exception as e3:
                                last_error = e3

                # If all strategies failed, try session building approach
                if not navigation_success:
                    logger.error(f"   🔄 All direct navigation failed, trying session building...")

                    try:
                        # Extract domain from URL
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        homepage = f"{parsed.scheme}://{parsed.netloc}"

                        # Visit homepage first to establish session
                        logger.debug(f"   📍 Visiting homepage first: {homepage}")
                        await page.goto(homepage, wait_until='domcontentloaded', timeout=30000)
                        await asyncio.sleep(random.uniform(2, 4))

                        # Simulate human behavior on homepage
                        await page.evaluate('window.scrollTo(0, 300)')
                        await asyncio.sleep(random.uniform(1, 2))

                        # Now try target URL again
                        logger.debug(f"   📍 Now navigating to target: {url}")
                        await page.goto(url, wait_until='domcontentloaded', timeout=stealth_timeout)
                        navigation_success = True

                    except Exception as e:
                        # If session building also failed, raise original error
                        logger.error(f"   ❌ Session building failed: {e}")
                        raise last_error

                # Wait for initial content
                await asyncio.sleep(self.INITIAL_CONTENT_WAIT_SEC)

                # ✅ Simulate human behavior after page load
                if use_stealth:
                    logger.info(f"   🎭 Simulating human behavior...")
                    await self._simulate_human_behavior(page, use_stealth=use_stealth)

                # Check if Cloudflare challenge is present
                try:
                    cloudflare_present = await page.evaluate("""
                        () => {
                            try {
                                const title = document.title.toLowerCase();
                                const body = document.body ? document.body.innerText.toLowerCase() : '';
                                return title.includes('just a moment') ||
                                       body.includes('checking your browser') ||
                                       body.includes('cloudflare');
                            } catch (e) {
                                return false;
                            }
                        }
                    """)
                except Exception:
                    cloudflare_present = False

                if cloudflare_present:
                    # Wait longer for Cloudflare challenge to complete
                    logger.debug("Cloudflare challenge detected in stealth mode, waiting...")
                    await asyncio.sleep(self.CLOUDFLARE_CHALLENGE_WAIT_SEC)

                # ✅ Apply Phase 2: Behavioral randomization (human-like behavior)
                logger.debug("   🤖 Simulating human-like behavior...")
                await self._apply_behavioral_randomization(page)

                # Try to wait for network to be idle (but don't fail if it times out)
                try:
                    await page.wait_for_load_state('networkidle', timeout=15000)
                except Exception:
                    # If networkidle times out, that's okay - page is probably loaded enough
                    pass

                # Additional random delay (human reading time)
                await asyncio.sleep(random.uniform(1.5, 3.0))

                # Random scroll to simulate engagement
                await page.evaluate(f"window.scrollTo(0, {random.randint(100, 300)})")
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(random.uniform(0.3, 0.7))

                # Debug: Check what's actually on the page
                try:
                    page_info = await page.evaluate("""
                        () => {
                            return {
                                url: window.location.href,
                                title: document.title,
                                bodyText: document.body ? document.body.innerText.substring(0, 500) : 'NO BODY',
                                hasOktaLogin: document.body ? document.body.innerText.includes('Sign In') || document.body.innerText.includes('Okta') : false,
                                hasError: document.body ? document.body.innerText.includes('error') || document.body.innerText.includes('Error') : false
                            };
                        }
                    """)
                    logger.debug(f"   📄 Page loaded: {page_info['title']}")
                    logger.info(f"   🔗 Current URL: {page_info['url']}")
                    if page_info['hasOktaLogin']:
                        logger.warning(f"   ⚠️  WARNING: Okta login page detected! Auth state may have been rejected.")
                    if page_info['hasError']:
                        logger.warning(f"   ⚠️  WARNING: Error text detected on page!")
                        logger.debug(f"   📝 Page content preview: {page_info['bodyText'][:200]}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not check page content: {str(e)}")

                # Wait for React app to render (critical for SPAs like Tekion)
                logger.debug("   ⏳ Waiting for React app to render...")
                await asyncio.sleep(5.0)  # Give React time to render
                logger.info("   ✅ Initial render wait complete")

                # Check if page has actual content now
                try:
                    content_check = await page.evaluate("""
                        () => {
                            const bodyText = document.body ? document.body.innerText : '';
                            const hasContent = bodyText.length > 100;
                            const visibleElements = document.querySelectorAll('*').length;
                            const images = document.querySelectorAll('img').length;
                            const divs = document.querySelectorAll('div').length;
                            return {
                                textLength: bodyText.length,
                                hasContent: hasContent,
                                visibleElements: visibleElements,
                                images: images,
                                divs: divs,
                                bodyPreview: bodyText.substring(0, 200)
                            };
                        }
                    """)
                    logger.info(
                        f"   📊 Content check: {content_check['textLength']} chars, {content_check['visibleElements']} elements, {content_check['divs']} divs, {content_check['images']} images")
                    if not content_check['hasContent']:
                        logger.warning(f"   ⚠️  WARNING: Page has very little text content!")
                        logger.debug(f"   📝 Body preview: {content_check['bodyPreview']}")
                    else:
                        logger.info(f"   ✅ Page has substantial content")
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not check content: {str(e)}")

                # Additional wait for any lazy-loaded content
                await asyncio.sleep(2.0)
                logger.info("   ✅ Final wait complete, ready to capture")
            else:
                # Real browser mode - more lenient loading
                if use_real_browser:
                    # ✅ NEW: Log tab opening
                    from datetime import datetime
                    logger.info(f"   🌐 [{datetime.now().strftime('%H:%M:%S')}] Opening tab for: {url}")

                    # Use 'load' instead of 'networkidle' for better compatibility
                    await page.goto(url, wait_until='load', timeout=timeout)
                    logger.info(f"   ✅ [{datetime.now().strftime('%H:%M:%S')}] Tab loaded successfully")

                    # Wait for initial content
                    await asyncio.sleep(2.0)

                    # Check if Cloudflare challenge is present
                    try:
                        cloudflare_present = await page.evaluate("""
                            () => {
                                try {
                                    const title = document.title.toLowerCase();
                                    const body = document.body ? document.body.innerText.toLowerCase() : '';
                                    return title.includes('just a moment') ||
                                           body.includes('checking your browser') ||
                                           body.includes('cloudflare');
                                } catch (e) {
                                    return false;
                                }
                            }
                        """)
                    except Exception:
                        # If evaluation fails, assume no Cloudflare
                        cloudflare_present = False

                    if cloudflare_present:
                        # Wait longer for Cloudflare challenge to complete
                        logger.debug("Cloudflare challenge detected, waiting...")
                        await asyncio.sleep(8.0)
                    else:
                        # Normal wait
                        await asyncio.sleep(random.uniform(2.0, 4.0))

                    # Try to wait for networkidle but don't fail if it times out
                    try:
                        await page.wait_for_load_state('networkidle', timeout=15000)
                    except Exception:
                        # If networkidle times out, that's okay - page is probably loaded enough
                        pass
                else:
                    # ✅ NEW: Log tab opening (headless mode)
                    from datetime import datetime
                    logger.info(f"   🌐 [{datetime.now().strftime('%H:%M:%S')}] Opening headless browser for: {url}")

                    # Normal headless navigation
                    await page.goto(url, wait_until='networkidle', timeout=timeout)
                    await page.wait_for_load_state('networkidle')
                    logger.info(f"   ✅ [{datetime.now().strftime('%H:%M:%S')}] Page loaded successfully")

                    # Additional wait for dealer-specific data to load (Tekion app initialization)
                    logger.debug("   ⏳ Waiting for app to fully initialize (dealer data, etc.)...")
                    await asyncio.sleep(5.0)  # Give time for dealer context to load

                    # Check for common errors that indicate auth issues
                    try:
                        error_check = await page.evaluate("""
                            () => {
                                const bodyText = document.body.innerText;
                                return {
                                    hasRoleChangeError: bodyText.includes('Your role has been changed'),
                                    hasUnableToFetchError: bodyText.includes('Unable to fetch'),
                                    hasJSONError: bodyText.includes('Unexpected token') || bodyText.includes('valid JSON')
                                };
                            }
                        """)

                        if error_check['hasRoleChangeError']:
                            logger.warning(f"   ⚠️  WARNING: 'Your role has been changed' error detected!")
                            logger.info(f"   💡 This usually means auth state was saved before dealer selection.")
                        if error_check['hasUnableToFetchError']:
                            logger.warning(f"   ⚠️  WARNING: 'Unable to fetch' error detected!")
                        if error_check['hasJSONError']:
                            logger.warning(f"   ⚠️  WARNING: JSON parsing error detected!")
                    except Exception:
                        pass  # Ignore if error check fails

            # Verify localStorage is loaded (after page navigation)
            if storage_state:
                try:
                    ls_verification = await page.evaluate("""
                        () => {
                            const keys = Object.keys(localStorage);
                            const authKeys = keys.filter(k =>
                                k.toLowerCase().includes('token') ||
                                k.toLowerCase().includes('auth') ||
                                k.toLowerCase().includes('user') ||
                                k.toLowerCase().includes('session')
                            );
                            return {
                                totalKeys: keys.length,
                                authKeys: authKeys
                            };
                        }
                    """)
                    logger.info(f"   ✅ Runtime verification: {ls_verification['totalKeys']} localStorage items loaded")
                    if ls_verification['authKeys']:
                        logger.debug(f"   💾 Active localStorage auth items: {', '.join(ls_verification['authKeys'][:5])}")
                    else:
                        logger.warning(f"   ⚠️  WARNING: No auth items found in localStorage!")
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not verify localStorage: {str(e)}")

            # Auto-scroll to trigger lazy loading
            if full_page:
                await self._auto_scroll(page)

            # Generate filename based on base URL logic
            filename = self._generate_filename(url, base_url, words_to_remove, 1,
                                               1)  # segment_index=1, total_segments=1
            filepath = self.output_dir / filename

            # Final check before screenshot
            logger.info(f"   📸 About to capture screenshot...")
            try:
                final_check = await page.evaluate("""
                    () => {
                        // Check for scrollable containers (fixed height containers)
                        const scrollableContainers = [];
                        const prioritySelectors = [
                            '#tekion-workspace',
                            '[role="main"]',
                            'main',
                            '.main-content',
                            '#main',
                            '#content',
                            '.content'
                        ];

                        for (const selector of prioritySelectors) {
                            try {
                                const elements = document.querySelectorAll(selector);
                                elements.forEach(el => {
                                    const style = window.getComputedStyle(el);
                                    const hasOverflow = (
                                        style.overflow === 'auto' ||
                                        style.overflow === 'scroll' ||
                                        style.overflowY === 'auto' ||
                                        style.overflowY === 'scroll'
                                    );

                                    if (hasOverflow && el.scrollHeight > el.clientHeight + 100) {
                                        scrollableContainers.push({
                                            selector: selector,
                                            scrollHeight: el.scrollHeight,
                                            clientHeight: el.clientHeight,
                                            scrollPotential: el.scrollHeight - el.clientHeight
                                        });
                                    }
                                });
                            } catch (e) {
                                // Selector might be invalid, skip it
                            }
                        }

                        return {
                            url: window.location.href,
                            title: document.title,
                            bodyLength: document.body ? document.body.innerText.length : 0,
                            scrollHeight: document.body ? document.body.scrollHeight : 0,
                            viewportHeight: window.innerHeight,
                            backgroundColor: window.getComputedStyle(document.body).backgroundColor,
                            hasScrollableContainer: scrollableContainers.length > 0,
                            scrollableContainers: scrollableContainers
                        };
                    }
                """)
                logger.info(f"   📊 Final state: URL={final_check['url']}, Title={final_check['title']}")
                logger.info(
                    f"   📊 Content: {final_check['bodyLength']} chars, Height={final_check['scrollHeight']}px, BgColor={final_check['backgroundColor']}")

                # 🆕 IMPROVEMENT: Warn if fullpage mode won't work properly
                if full_page and final_check.get('hasScrollableContainer'):
                    containers = final_check.get('scrollableContainers', [])
                    if containers:
                        best_container = max(containers, key=lambda c: c['scrollPotential'])
                        logger.warning(f"   ⚠️  WARNING: Fixed-height scrollable container detected!")
                        logger.warning(
                            f"      Container: {best_container['selector']} ({best_container['scrollHeight']}px scrollable)")
                        logger.warning(f"      Document body: {final_check['scrollHeight']}px (viewport height)")
                        logger.info(f"      💡 RECOMMENDATION: Use 'Segmented' mode instead of 'Full page' mode")
                        logger.info(f"      💡 Full page mode will only capture {final_check['scrollHeight']}px (viewport)")
                        logger.info(f"      💡 Segmented mode will capture all {best_container['scrollHeight']}px of content")

            except Exception as e:
                logger.warning(f"   ⚠️  Could not get final state: {str(e)}")

            # ========================================
            # 🎯 Solution #5: Save cookies for future sessions
            # ========================================
            if use_stealth:
                await self._save_cookies(context)

            # ✅ NEW: Auto-expand dropdowns if enabled
            if auto_expand_dropdowns:
                await self._expand_all_dropdowns(page)
                # ⏱️ CRITICAL: Wait for page to settle after expansion
                # Dropdowns may trigger layout changes, lazy loading, or animations
                logger.debug("   ⏱️  Waiting for page to settle after dropdown expansion...")
                await asyncio.sleep(2.0)
                logger.info("   ✅ Page settled, ready to capture...")

                # ✅ NEW: Click elements - check URL config first, then manual parameter
                url_config = self._find_url_config(url)
                per_url_auto_expand = bool(url_config.get("auto_expand_dropdowns")) if url_config else False

                if url_config:
                    # Use saved URL-specific configuration
                    logger.info(f"📋 Found saved configuration: '{url_config.get('name', 'Unnamed')}'")
                    actions = url_config.get("actions", [])

                    for i, action in enumerate(actions, 1):
                        if action.get("type") == "click":
                            text = action.get("text", "")
                            wait_ms = action.get("wait_after_ms", 2000)
                            description = action.get("description", "")

                            logger.debug(f"   🖱️  Action {i}/{len(actions)}: Click '{text}'")
                            if description:
                                logger.debug(f"      ℹ️  {description}")

                            await self._click_elements_by_text(page, [text])
                            await asyncio.sleep(wait_ms / 1000)

                    logger.info("   ✅ All configured actions completed")

                    # 🔽 URL-specific dropdown expansion after configured actions
                    if per_url_auto_expand:
                        logger.info("   🔽 URL config requested dropdown auto-expansion after actions")
                        await self._expand_all_dropdowns(page)
                        logger.debug("   ⏱️  Waiting for page to settle after URL-specific dropdown expansion...")
                        await asyncio.sleep(2.0)
                        logger.info("   ✅ URL-specific dropdown expansion complete")

                elif click_elements:
                    # Use manual click_elements parameter (backward compatibility)
                    logger.debug(f"🖱️  Using manual click elements: {click_elements}")
                    await self._click_elements_by_text(page, click_elements)
                    logger.debug("   ⏱️  Waiting for modals/dialogs to appear...")
                    await asyncio.sleep(2.0)
                    logger.info("   ✅ Ready to capture...")

            # Capture screenshot
            # ✅ IMPORTANT: In fullpage mode, Playwright auto-detects new height after expansion
            from datetime import datetime
            logger.info(f"   📸 [{datetime.now().strftime('%H:%M:%S')}] Taking screenshot...")
            logger.debug(f"   💾 Saving to: {filepath}")

            await page.screenshot(
                path=str(filepath),
                full_page=full_page,
                type='png',
                timeout=screenshot_timeout  # ✅ NEW: Use dynamic timeout
            )

            # Verify screenshot was saved
            if filepath.exists():
                file_size = filepath.stat().st_size
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"   ✅ [{datetime.now().strftime('%H:%M:%S')}] Screenshot saved successfully!")
                logger.debug(f"   📁 File: {filepath}")
                logger.info(f"   📊 Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
                logger.debug(f"   🕐 Timestamp: {timestamp}")

                # Check if image is valid
                try:
                    from PIL import Image
                    img = Image.open(filepath)
                    width, height = img.size
                    logger.debug(f"   📐 Image dimensions: {width}x{height}")

                    # Check if image is blank (all white or all one color)
                    extrema = img.convert("L").getextrema()
                    if extrema[0] == extrema[1]:
                        logger.warning(f"   ⚠️  WARNING: Image appears to be blank or single color (value: {extrema[0]})")
                    else:
                        logger.info(f"   ✅ Image has content (brightness range: {extrema[0]}-{extrema[1]})")
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not verify image: {str(e)}")
            else:
                logger.error(f"   ❌ ERROR: Screenshot file not found!")

            # ✅ NEW: Summary log for full-page capture
            from datetime import datetime
            logger.debug(f"\n{'=' * 60}")
            logger.debug(f"🎉 [{datetime.now().strftime('%H:%M:%S')}] Full-page capture complete!")
            logger.debug(f"   📁 Output file: {filepath}")
            logger.debug(f"   🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.debug(f"{'=' * 60}\n")

            return str(filepath)

        finally:
            await page.close()
            # ✅ FIX: Don't close persistent contexts (they ARE the browser)
            # Only close contexts that we created (non-persistent mode)
            if not is_persistent_context:
                await context.close()

    async def _auto_scroll(self, page: Page):
        """Auto-scroll page to trigger lazy loading"""
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;

                        if(totalHeight >= scrollHeight){
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
        """)

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)

    async def capture_segmented(
            self,
            url: str,
            viewport_width: int = 1920,
            viewport_height: int = 1080,
            screenshot_timeout: int = 30000,  # ✅ NEW: Screenshot-specific timeout
            use_stealth: bool = False,
            use_real_browser: bool = False,
            headless: bool = False,  # ✅ FIX: Default to headful (visible browser) - Real Browser Mode is always visible
            browser_engine: str = "playwright",  # "playwright" or "camoufox"
            base_url: str = "",
            words_to_remove: str = "",
            cookies: str = "",
            local_storage: str = "",
            overlap_percent: int = 20,
            scroll_delay_ms: int = 1000,
            max_segments: int = 50,
            skip_duplicates: bool = True,
            smart_lazy_load: bool = True,
            track_network: bool = False,  # ✅ NEW: Network event tracking
            auto_expand_dropdowns: bool = False,  # ✅ NEW: Auto expand collapsed sections
            click_elements: list = None,  # ✅ NEW: Click elements before screenshot
            non_scrollable_urls: str = ""  # ✅ NEW: Non-scrollable URL patterns (JSON string)
    ) -> list[str]:
        """
        Capture page in viewport-sized segments (scroll-by-scroll)

        Args:
            url: URL to capture
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            use_stealth: Enable stealth mode
            use_real_browser: Use active tab from existing Chrome browser (CDP mode)
            headless: Run browser in headless mode (invisible) - only applies to Standard Mode
            browser_engine: Browser engine to use ("playwright" or "camoufox")
            overlap_percent: Percentage overlap between segments (0-50)
            scroll_delay_ms: Milliseconds to wait after scrolling
            max_segments: Maximum number of segments to capture
            skip_duplicates: Skip segments that are too similar to previous
            smart_lazy_load: Wait for lazy-loaded content before capturing

        Returns:
            List of paths to saved screenshots
        """
        logger.info(f"📸 Starting segmented capture for {url}")
        logger.info(f"   Settings: overlap={overlap_percent}%, delay={scroll_delay_ms}ms, max={max_segments}")
        logger.info(f"   🔧 Browser engine: {browser_engine}")
        logger.info(f"   🥷 Stealth mode: {use_stealth}")
        logger.info(f"   🔗 Real browser mode: {use_real_browser}")
        logger.info(f"   👁️ Headless mode: {headless}")

        # 🔗 ACTIVE TAB MODE: Connect to existing Chrome browser via CDP
        if use_real_browser:
            logger.info("🔗 Active Tab Mode: Using your existing Chrome browser")
            new_tab = None
            try:
                # Connect to Chrome via CDP if not already connected
                if self.cdp_browser is None:
                    await self._connect_to_chrome_cdp()

                # Create a new tab next to the active tab (don't navigate the current tab)
                new_tab = await self._create_new_tab_next_to_active()

                # ✅ Conditionally create network event handlers based on track_network setting
                handlers = None
                if track_network:
                    handlers = self._create_network_event_handlers()

                    # Attach listeners BEFORE navigation
                    new_tab.on('request', handlers['log_request'])
                    new_tab.on('response', handlers['log_response'])
                    new_tab.on('requestfailed', handlers['log_request_failed'])
                    new_tab.on('requestfinished', handlers['log_request_finished'])
                    logger.info(f"   📡 Network listeners attached BEFORE page load (tracking enabled)")
                else:
                    logger.info(f"   ⚠️  Network tracking disabled (faster capture, no API interception)")

                # Navigate to the URL in the new tab
                logger.info(f"🌐 Loading {url} in new tab...")
                try:
                    # Try networkidle first (best for fully loaded pages)
                    await new_tab.goto(url, wait_until='networkidle', timeout=30000)
                    logger.info("   ✅ Page loaded in new tab (network idle)")
                except Exception as e:
                    # If networkidle times out, fall back to load event
                    logger.warning(f"   ⚠️  Network idle timeout, using load event instead...")
                    await new_tab.goto(url, wait_until='load', timeout=30000)
                    logger.info("   ✅ Page loaded in new tab (load event)")

                # Print network events captured during page load (only if tracking was enabled)
                if handlers:
                    network_events = handlers['network_events']
                    api_responses = handlers['api_responses']  # ✅ NEW: Get intercepted API responses

                    logger.info(f"   📡 Network events captured during page load: {len(network_events)}")
                    if network_events:
                        logger.info(f"      🌐 Network activity during page load ({len(network_events)} events):")
                        xhr_count = sum(1 for e in network_events if
                                        e.get('type') in ['xhr', 'fetch'] and e.get('event') == 'request')
                        doc_count = sum(
                            1 for e in network_events if e.get('type') == 'document' and e.get('event') == 'request')
                        failed_count = sum(1 for e in network_events if e.get('event') == 'failed')
                        logger.debug(f"         📄 Document requests: {doc_count}")
                        logger.debug(f"         🔄 XHR/Fetch requests: {xhr_count}")
                        if failed_count > 0:
                            logger.error(f"         ❌ Failed requests: {failed_count}")

                        # Generate and print cURL commands
                        curl_commands = self._convert_network_events_to_curl(network_events)
                        if curl_commands:
                            logger.info(f"      🔗 cURL commands ({len(curl_commands)} API calls):")
                            for i, curl in enumerate(curl_commands[:5], 1):  # Show first 5
                                logger.debug(f"         {i}. {curl[:100]}...")
                            if len(curl_commands) > 5:
                                logger.debug(f"         ... and {len(curl_commands) - 5} more")

                    # ✅ NEW: Store intercepted API responses for Network tab
                    if api_responses:
                        # Add page URL context to each API response
                        for api in api_responses:
                            api['page_url'] = url
                            api['captured_from'] = 'real_browser_mode'

                        # Add to global storage (with limit)
                        self.intercepted_apis.extend(api_responses)
                        if len(self.intercepted_apis) > self.max_intercepted_apis:
                            # Keep only the most recent APIs
                            self.intercepted_apis = self.intercepted_apis[-self.max_intercepted_apis:]

                        logger.info(f"      🌐 Intercepted {len(api_responses)} API responses for Network tab")
                        logger.info(f"         📊 Total stored: {len(self.intercepted_apis)} APIs")

                # Wait for React app to fully render (critical for SPAs like Tekion)
                logger.info("   ⏳ Waiting for React app to render...")
                await asyncio.sleep(5.0)  # Increased from 3s to 5s for complex SPAs

                # Try to wait for network to be mostly idle
                try:
                    await new_tab.wait_for_load_state('networkidle', timeout=10000)
                    logger.info("   ✅ Network idle - content loaded")
                except Exception:
                    logger.warning("   ⚠️  Network still active, but continuing...")

                # ✅ NEW: Wait for Tekion-specific content to load
                logger.debug("   ⏳ Waiting for dynamic content to load...")
                await asyncio.sleep(3.0)  # Additional wait for Tekion

                # ✅ NEW: Trigger content loading by interacting with the page
                try:
                    await new_tab.evaluate("""() => {
                        // Find the main workspace div
                        const workspace = document.getElementById('tekion-workspace');
                        if (workspace) {
                            // Scroll it to trigger lazy loading
                            workspace.scrollTop = workspace.scrollHeight;
                        }
                    }""")
                    logger.debug("   🔄 Triggered content loading in workspace")
                    await asyncio.sleep(2.0)  # Wait for content to load
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not trigger content loading: {e}")

                # ✅ CRITICAL FIX: Detect actual viewport size instead of using parameters
                # Real browser mode connects to existing Chrome window which may have different size
                # than the parameters passed (e.g., Chrome window is 1366x768 but params are 1920x1080)
                logger.debug("   📐 Detecting actual Chrome window viewport...")
                try:
                    actual_viewport = new_tab.viewport_size
                    if actual_viewport:
                        viewport_width = actual_viewport['width']
                        viewport_height = actual_viewport['height']
                        logger.info(f"   ✅ Detected Chrome viewport: {viewport_width}x{viewport_height}")
                    else:
                        # Fallback to JavaScript detection if viewport_size is None
                        logger.warning("   ⚠️  viewport_size is None, using JavaScript detection...")
                        viewport_info = await new_tab.evaluate("""() => {
                            return {
                                width: window.innerWidth,
                                height: window.innerHeight,
                                outerWidth: window.outerWidth,
                                outerHeight: window.outerHeight,
                                screenWidth: window.screen.width,
                                screenHeight: window.screen.height,
                                availWidth: window.screen.availWidth,
                                availHeight: window.screen.availHeight,
                                devicePixelRatio: window.devicePixelRatio
                            };
                        }""")
                        viewport_width = viewport_info['width']
                        viewport_height = viewport_info['height']
                        logger.info(f"   ✅ Detected viewport from JS: {viewport_width}x{viewport_height}")
                        logger.info(
                            f"      📊 Window: {viewport_info['outerWidth']}x{viewport_info['outerHeight']}, Screen: {viewport_info['screenWidth']}x{viewport_info['screenHeight']}, DPR: {viewport_info['devicePixelRatio']}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not detect viewport: {e}")
                    logger.debug(f"   ℹ️  Using parameter values: {viewport_width}x{viewport_height}")

                # Continue with segmented capture using the new tab
                result = await self._capture_segments_from_page(
                    page=new_tab,
                    url=url,
                    viewport_width=viewport_width,
                    viewport_height=viewport_height,
                    overlap_percent=overlap_percent,
                    scroll_delay_ms=scroll_delay_ms,
                    max_segments=max_segments,
                    skip_duplicates=skip_duplicates,
                    smart_lazy_load=smart_lazy_load,
                    track_network=track_network,  # ✅ Pass network tracking setting from parameter
                    auto_expand_dropdowns=auto_expand_dropdowns,  # ✅ FIX: Pass dropdown expansion setting
                    base_url=base_url,  # ✅ FIX: Pass base_url parameter
                    words_to_remove=words_to_remove,  # ✅ FIX: Pass words_to_remove parameter
                    screenshot_timeout=screenshot_timeout,  # ✅ FIX: Pass screenshot_timeout parameter
                    non_scrollable_urls=non_scrollable_urls  # ✅ FIX: Pass non_scrollable_urls parameter
                )

                # ✅ IMPROVED: Better error handling for tab closing
                logger.info(f"📸 Capture complete for {url}, closing tab...")
                await self.tab_registry.mark_success(url)
                logger.info("⏱️  Waiting 1 second before closing tab...")
                await asyncio.sleep(1.0)

                try:
                    # Check if tab is still open before attempting to close
                    if not new_tab.is_closed():
                        await new_tab.close()
                        logger.info(f"✅ Tab closed successfully: {url}")
                    else:
                        logger.info(f"ℹ️  Tab was already closed: {url}")
                except Exception as close_error:
                    logger.warning(f"⚠️  Error closing tab for {url}: {close_error}")
                    logger.warning(f"   Tab state: is_closed={new_tab.is_closed() if hasattr(new_tab, 'is_closed') else 'unknown'}")
                finally:
                    # Always remove from registry, even if close failed
                    self.tab_registry.tabs.pop(url, None)
                    logger.info(f"🧹 Removed {url} from tab registry")

                return result

            except Exception as e:
                # ✅ NEW: Mark as failure (keep tab open for debugging)
                if url in self.tab_registry.tabs:
                    await self.tab_registry.mark_failure(url)
                    logger.warning(f"⚠️  Tab left open for debugging: {url}")

                logger.error(f"❌ Active Tab Mode failed: {e}")
                logger.debug("\n💡 Make sure Chrome is running with remote debugging enabled:")
                logger.debug(
                    "   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223")
                raise

        # ✅ STANDARD MODE: Launch new browser or use existing
        # Get browser (will auto-switch modes if needed)
        # ✅ 2025: Support Camoufox for maximum stealth
        browser = await self._get_browser(use_real_browser=False, browser_engine=browser_engine,
                                          use_stealth=use_stealth, headless=headless)

        # ✅ PHASE 3: Use helper method for stealth configuration
        viewport_width, viewport_height, user_agent, extra_headers = self._get_stealth_config(
            viewport_width, viewport_height, use_stealth and not use_real_browser
        )

        # ✅ PHASE 3: Use helper method for auth state loading
        storage_state = self._load_auth_state(cookies, local_storage)

        # 🦊 CAMOUFOX FIX: Camoufox returns a BrowserContext directly (persistent_context=True)
        # For Camoufox, browser IS the context. For Playwright, we need to create a context.
        use_camoufox = (browser_engine == "camoufox")

        logger.debug(
            f"   🔍 DEBUG: Setting up browser context (use_camoufox={use_camoufox}, storage_state={storage_state is not None})")

        if use_camoufox:
            # Camoufox: browser IS already a BrowserContext (persistent_context=True)
            context = browser
            logger.info(f"   ✅ DEBUG: Using Camoufox persistent context directly!")
        else:
            # Playwright: Create a new context from the browser
            try:
                context = await browser.new_context(
                    viewport={'width': viewport_width, 'height': viewport_height},
                    user_agent=user_agent,
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers=extra_headers,
                    permissions=['geolocation'] if use_stealth else [],
                    geolocation={'latitude': 40.7128, 'longitude': -74.0060} if use_stealth else None,
                    color_scheme='light' if use_stealth else None,
                    device_scale_factor=1,
                    has_touch=False,  # Desktop browser
                    is_mobile=False,  # Not mobile
                    storage_state=storage_state,  # Load saved auth state if available
                )
                logger.info(f"   ✅ DEBUG: Playwright context created successfully!")
            except Exception as e:
                logger.error(f"   ❌ ERROR: Failed to create browser context: {str(e)}")
                logger.info(f"   📊 Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                raise

        # Note: Manual stealth JavaScript removed - now using playwright-stealth library
        # The library handles all stealth techniques automatically and more comprehensively

        # ✅ PHASE 3: Use helper method for cookies and localStorage
        logger.debug(f"   🔍 DEBUG: Applying cookies and localStorage...")
        try:
            await self._apply_cookies_and_storage(context, cookies, local_storage)
            logger.info(f"   ✅ DEBUG: Cookies and localStorage applied!")
        except Exception as e:
            logger.error(f"   ❌ ERROR: Failed to apply cookies/localStorage: {str(e)}")
            logger.info(f"   📊 Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise

        logger.debug(f"   🔍 DEBUG: Creating new page...")
        try:
            page = await context.new_page()
            logger.info(f"   ✅ DEBUG: Page created successfully!")
        except Exception as e:
            logger.error(f"   ❌ ERROR: Failed to create page: {str(e)}")
            logger.info(f"   📊 Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise

        # 🦊 CAMOUFOX FIX: Set viewport size on the page (Camoufox persistent context doesn't support viewport in context creation)
        if use_camoufox:
            logger.debug(f"   📐 Setting Camoufox viewport to {viewport_width}x{viewport_height}...")
            try:
                await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
                logger.info(f"   ✅ Viewport set successfully!")
            except Exception as e:
                logger.warning(f"   ⚠️  Failed to set viewport: {str(e)}")

        # ⚡ OPTIMIZATION: Track page count for context reuse
        self.context_page_count += 1

        # 🦊 CAMOUFOX FIX: Manually inject cookies and localStorage from auth_state.json
        if use_camoufox and storage_state:
            logger.info(f"   🦊 Camoufox: Manually injecting auth state...")
            try:
                import json
                with open(storage_state, 'r') as f:
                    state_data = json.load(f)

                # Inject cookies
                cookies_to_add = state_data.get('cookies', [])
                if cookies_to_add:
                    await context.add_cookies(cookies_to_add)
                    logger.info(f"      ✅ Injected {len(cookies_to_add)} cookies")

                # Inject localStorage (need to navigate to a page first)
                # We'll do this after navigation in the cross-domain cookie setup

            except Exception as e:
                logger.warning(f"      ⚠️  Failed to inject auth state: {str(e)}")

        # Apply stealth mode using playwright-stealth library + 2024-2025 enhancements
        # ⚡ OPTIMIZATION: Only inject stealth scripts once per browser instance
        if use_stealth and not use_real_browser:
            if not self.stealth_injected or not self.ENABLE_BROWSER_REUSE:
                logger.debug("   🥷 Applying playwright-stealth library...")
                await stealth_async(page)
                logger.info("   ✅ Stealth mode activated!")

                # ========================================
                # 🎯 9 STEALTH SOLUTIONS - Applied Here
                # ========================================
                logger.info("   🚀 Applying 9 stealth solutions (2025)...")

                # Solution #1: Disable navigator.webdriver (CRITICAL)
                await self._disable_navigator_webdriver(page)

                # Solution #5: Load cookies from previous sessions
                # ✅ FIX: Only load cookies.json if we didn't already load auth state
                if not storage_state:
                    await self._load_cookies(context)

                # Apply 2024-2025 stealth enhancements (Phase 1 & 2)
                await self._apply_canvas_webgl_randomization(page)
                await self._apply_cdp_detection_bypass(page)
                await self._apply_audio_context_randomization(page)
                logger.info("   ✅ All 9 stealth solutions applied!")

                # ⚡ OPTIMIZATION: Mark stealth as injected
                self.stealth_injected = True
            else:
                logger.debug("   ⚡ Stealth already injected - reusing browser context!")

        try:
            # 🔧 CROSS-DOMAIN COOKIE SETUP: If auth state was loaded, set up cookies for all domains
            if storage_state:
                await self._setup_cross_domain_cookies(context, storage_state)

            # 🔍 DEBUG: Show which cookies will be sent to the target URL
            await self._debug_cookies_before_navigation(context, url)

            # 🔍 DEBUG: Add request/response logging
            async def log_request(request):
                headers = await request.all_headers()
                cookie_header = headers.get('cookie', 'NO COOKIES')
                logger.debug(f"   📤 REQUEST: {request.method} {request.url}")
                logger.info(f"      🍪 Cookie header: {cookie_header[:200]}...")

            async def log_response(response):
                logger.debug(f"   📥 RESPONSE: {response.status} {response.url}")
                if response.status >= 300 and response.status < 400:
                    location = response.headers.get('location', 'N/A')
                    logger.debug(f"      🔀 Redirect to: {location}")

            page.on('request', log_request)
            page.on('response', log_response)

            # Navigate to page
            from datetime import datetime
            logger.info(f"🌐 [{datetime.now().strftime('%H:%M:%S')}] Opening tab for segmented capture: {url}")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)  # Reduced to 30s
                logger.info(f"   ✅ [{datetime.now().strftime('%H:%M:%S')}] Page navigation complete")
            except Exception as nav_error:
                logger.warning(f"   ⚠️  Navigation error: {nav_error}")
                # Try to continue anyway - page might have partially loaded

            # ⏳ CRITICAL: Wait for SPA (React/Angular/Vue) to fully render
            # Many modern apps load content AFTER domcontentloaded via XHR/fetch
            logger.debug(f"   ⏳ Waiting for SPA content to render...")
            await asyncio.sleep(10.0)  # Increased from 2s to 10s for SPAs like Tekion

            # 🔍 DEBUG: Show final URL and cookies after navigation
            final_url = page.url
            logger.info(f"   🔗 Final URL after navigation: {final_url}")

            # Check if we got redirected to login
            if '/login' in final_url.lower():
                logger.warning(f"   ⚠️  WARNING: Redirected to login page!")
                logger.error(f"   💡 This means authentication failed - cookies may be invalid/expired")

            # Show cookies that are now active
            try:
                active_cookies = await context.cookies()
                auth_cookies = [c for c in active_cookies if any(keyword in c['name'].lower()
                                                                 for keyword in
                                                                 ['token', 'session', 'auth', 'sid', 'jsession'])]
                logger.info(f"   🍪 Active cookies after navigation: {len(active_cookies)} total, {len(auth_cookies)} auth")
                if auth_cookies:
                    logger.info(f"      🔑 Auth cookies: {', '.join([c['name'] for c in auth_cookies[:5]])}")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not check active cookies: {str(e)}")

            # Check for Cloudflare (same as regular capture)
            try:
                cloudflare_present = await page.evaluate("""
                    () => {
                        try {
                            const title = document.title.toLowerCase();
                            const body = document.body ? document.body.innerText.toLowerCase() : '';
                            return title.includes('just a moment') ||
                                   body.includes('checking your browser') ||
                                   body.includes('cloudflare');
                        } catch (e) {
                            return false;
                        }
                    }
                """)
            except Exception:
                cloudflare_present = False

            if cloudflare_present:
                logger.debug("🛡️ Cloudflare challenge detected, waiting...")
                await asyncio.sleep(8.0)

            # 🆕 IMPROVEMENT: Detect and log browser mode for diagnostics
            try:
                mode_info = await self._detect_browser_mode(page)
                mode_str = "Headless" if mode_info['isHeadless'] else "Headful"
                automation_str = "⚠️ DETECTED" if mode_info['hasAutomationSignals'] else "✅ HIDDEN"
                logger.debug(f"   🔍 Browser Mode: {mode_str}, Automation Signals: {automation_str}")
                logger.debug(
                    f"      Viewport: {mode_info['viewport']['width']}x{mode_info['viewport']['height']}, Plugins: {mode_info['indicators']['plugins']}, Languages: {mode_info['indicators']['languages']}")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not detect browser mode: {e}")

            # ========================================
            # 🎯 9 STEALTH SOLUTIONS - Human Behavior
            # ========================================
            if use_stealth and not use_real_browser:
                try:
                    # Add timeout to human behavior simulation (max 30 seconds)
                    await asyncio.wait_for(
                        self._simulate_human_behavior(page, use_stealth=True),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("   ⚠️  Human behavior simulation timed out (30s), continuing...")
                except Exception as sim_error:
                    logger.warning(f"   ⚠️  Human behavior simulation error: {sim_error}")

            # Debug: Check what's actually on the page
            try:
                page_info = await page.evaluate("""
                    () => {
                        return {
                            url: window.location.href,
                            title: document.title,
                            bodyText: document.body ? document.body.innerText.substring(0, 500) : 'NO BODY',
                            hasOktaLogin: document.body ? document.body.innerText.includes('Sign In') || document.body.innerText.includes('Okta') : false,
                            hasError: document.body ? document.body.innerText.includes('error') || document.body.innerText.includes('Error') : false
                        };
                    }
                """)
                logger.debug(f"   📄 Page loaded: {page_info['title']}")
                logger.info(f"   🔗 Current URL: {page_info['url']}")
                if page_info['hasOktaLogin']:
                    logger.warning(f"   ⚠️  WARNING: Okta login page detected! Auth state may have been rejected.")
                    logger.info(f"   💡 TIP: Try using Real Browser Mode instead.")
                if page_info['hasError']:
                    logger.warning(f"   ⚠️  WARNING: Error text detected on page!")
                    logger.debug(f"   📝 Page content preview: {page_info['bodyText'][:200]}")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not check page content: {str(e)}")

            # Wait for React app to render (critical for SPAs like Tekion)
            logger.debug("   ⏳ Waiting for React app to render...")
            await asyncio.sleep(self.REACT_RENDER_WAIT_SEC)  # Give React time to render
            logger.info("   ✅ Initial render wait complete")

            # Wait for network to be mostly idle
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
                logger.info("   ✅ Network idle - content loaded")
            except Exception as e:
                logger.warning(f"   ⚠️  Network still active: {str(e)}, but continuing...")

            # Check if page has actual content now
            try:
                content_check = await page.evaluate("""
                    () => {
                        const bodyText = document.body ? document.body.innerText : '';
                        const hasContent = bodyText.length > 100;
                        const visibleElements = document.querySelectorAll('*').length;
                        const images = document.querySelectorAll('img').length;
                        const divs = document.querySelectorAll('div').length;
                        return {
                            textLength: bodyText.length,
                            hasContent: hasContent,
                            visibleElements: visibleElements,
                            images: images,
                            divs: divs,
                            bodyPreview: bodyText.substring(0, 200)
                        };
                    }
                """)
                logger.info(
                    f"   📊 Content check: {content_check['textLength']} chars, {content_check['visibleElements']} elements, {content_check['divs']} divs, {content_check['images']} images")
                if not content_check['hasContent']:
                    logger.warning(f"   ⚠️  WARNING: Page has very little text content!")
                    logger.debug(f"   📝 Body preview: {content_check['bodyPreview']}")
                else:
                    logger.info(f"   ✅ Page has substantial content")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not check content: {str(e)}")

            # Additional wait for any lazy-loaded content
            await asyncio.sleep(self.FINAL_CONTENT_WAIT_SEC)
            logger.info("   ✅ Final wait complete, ready to capture")

            # ✅ NEW: Auto-expand dropdowns if enabled
            if auto_expand_dropdowns:
                await self._expand_all_dropdowns(page)
                # ⏱️ CRITICAL: Wait for page to settle after expansion
                # Dropdowns may trigger layout changes, lazy loading, or animations
                logger.debug("   ⏱️  Waiting for page to settle after dropdown expansion...")
                await asyncio.sleep(2.0)
                logger.info("   ✅ Page settled, recalculating height...")

            # ✅ NEW: Click elements by text if specified
            if click_elements:
                await self._click_elements_by_text(page, click_elements)
                # Wait for any modals/dialogs to appear
                logger.debug("   ⏱️  Waiting for modals/dialogs to appear...")
                await asyncio.sleep(2.0)
                logger.info("   ✅ Ready to capture...")

            # 🎯 DYNAMIC PAGE HEIGHT CALCULATION - Find ALL scrollable content
            # ✅ IMPORTANT: This runs AFTER dropdown expansion, so height includes expanded content
            # ✅ REAL-WORLD BEST PRACTICES: Based on browser scroll detection standards
            height_info = await page.evaluate("""() => {
                console.log('🔍 DEBUG: Starting page height calculation...');

                // 1. Get document height
                const docHeight = Math.max(
                    document.body.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.clientHeight,
                    document.documentElement.scrollHeight,
                    document.documentElement.offsetHeight
                );
                console.log('📄 Document height:', docHeight);

                // 🆕 IMPROVEMENT 1: Helper function to check if element is truly scrollable
                function isElementScrollable(el) {
                    const style = window.getComputedStyle(el);
                    const hasVerticalScroll = (
                        style.overflow === 'auto' ||
                        style.overflow === 'scroll' ||
                        style.overflowY === 'auto' ||
                        style.overflowY === 'scroll'
                    );
                    const hasScrollableContent = el.scrollHeight > el.clientHeight;

                    // 🆕 IMPROVEMENT 2: Check if element is visible (not display:none or visibility:hidden)
                    const isVisible = (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        el.offsetParent !== null  // Element is rendered
                    );

                    // 🆕 IMPROVEMENT 3: Calculate scroll potential (how much can be scrolled)
                    const scrollPotential = el.scrollHeight - el.clientHeight;

                    return {
                        isScrollable: hasVerticalScroll && hasScrollableContent && isVisible,
                        scrollPotential: scrollPotential,
                        scrollHeight: el.scrollHeight,
                        clientHeight: el.clientHeight
                    };
                }

                // 2. Find ALL potentially scrollable containers
                const scrollableSelectors = [
                    'main', '[role="main"]', '.main-content', '#main', '#content',
                    '.content', '.page-content', '.app-content', '[class*="content"]',
                    '[class*="scroll"]', '[style*="overflow"]', 'article', 'section',
                    'div'  // 🆕 IMPROVEMENT 4: Also check all divs (common scrollable container)
                ];

                let maxScrollHeight = docHeight;
                let scrollableContainer = null;
                let scrollableElement = null;
                let allScrollableContainers = [];

                console.log('🔍 Searching for scrollable containers...');

                // 🆕 IMPROVEMENT 5: Prioritize by scroll potential (largest scrollable area first)
                const candidates = [];

                for (const selector of scrollableSelectors) {
                    const elements = document.querySelectorAll(selector);

                    elements.forEach((el) => {
                        const scrollInfo = isElementScrollable(el);

                        if (scrollInfo.isScrollable && scrollInfo.scrollPotential > 100) {  // 🆕 Min 100px scroll
                            candidates.push({
                                element: el,
                                tag: el.tagName,
                                className: el.className,
                                id: el.id,
                                scrollHeight: scrollInfo.scrollHeight,
                                clientHeight: scrollInfo.clientHeight,
                                scrollPotential: scrollInfo.scrollPotential,
                                selector: selector
                            });
                        }
                    });
                }

                // 🆕 IMPROVEMENT 6: Sort by scroll potential (largest first)
                candidates.sort((a, b) => b.scrollPotential - a.scrollPotential);

                console.log(`📦 Found ${candidates.length} scrollable candidates`);

                // 🆕 IMPROVEMENT 7: Pick the best scrollable element (largest scroll potential)
                if (candidates.length > 0) {
                    const best = candidates[0];
                    scrollableElement = best.element;
                    maxScrollHeight = best.scrollHeight;
                    scrollableContainer = {
                        tag: best.tag,
                        className: best.className,
                        id: best.id,
                        scrollHeight: best.scrollHeight,
                        clientHeight: best.clientHeight,
                        scrollPotential: best.scrollPotential,
                        selector: best.selector
                    };

                    console.log(`✅ BEST scrollable: <${best.tag}> (${best.scrollPotential}px potential)`);

                    // Store top 5 for debugging
                    allScrollableContainers = candidates.slice(0, 5).map(c => ({
                        tag: c.tag,
                        className: c.className,
                        id: c.id,
                        scrollHeight: c.scrollHeight,
                        clientHeight: c.clientHeight,
                        scrollPotential: c.scrollPotential,
                        selector: c.selector
                    }));
                }

                // 3. Also check for elements with large offsetHeight (fallback)
                const allElements = document.querySelectorAll('*');
                let maxOffsetHeight = docHeight;
                let maxOffsetElement = null;

                allElements.forEach(el => {
                    if (el.offsetHeight > maxOffsetHeight) {
                        maxOffsetHeight = el.offsetHeight;
                        maxOffsetElement = {
                            tag: el.tagName,
                            className: el.className,
                            id: el.id,
                            offsetHeight: el.offsetHeight
                        };
                    }
                });

                const finalHeight = Math.max(docHeight, maxScrollHeight, maxOffsetHeight);
                console.log('✅ Final height:', finalHeight);

                // ✅ Store scrollable element in window for later use
                if (scrollableElement) {
                    window.__scrollableElement = scrollableElement;
                    console.log('✅ Stored scrollable element in window.__scrollableElement');
                } else {
                    window.__scrollableElement = null;
                    console.log('⚠️  No scrollable element found, will use window.scrollTo()');
                }

                return {
                    docHeight: docHeight,
                    maxScrollHeight: maxScrollHeight,
                    maxOffsetHeight: maxOffsetHeight,
                    finalHeight: finalHeight,
                    scrollableContainer: scrollableContainer,
                    allScrollableContainers: allScrollableContainers,
                    maxOffsetElement: maxOffsetElement,
                    hasScrollableElement: scrollableElement !== null
                };
            }""")

            total_height = height_info['finalHeight']
            has_scrollable_element = height_info.get('hasScrollableElement', False)

            logger.info(f"📏 Dynamic page height calculation:")
            logger.info(f"   📄 Document height: {height_info['docHeight']}px")
            logger.info(f"   📦 Max scrollable container: {height_info['maxScrollHeight']}px")
            logger.info(f"   📐 Max element offset: {height_info['maxOffsetHeight']}px")
            logger.info(f"   ✅ Final height: {total_height}px")
            logger.info(f"   🎯 Scroll target: {'ELEMENT' if has_scrollable_element else 'WINDOW'}")

            if height_info.get('allScrollableContainers'):
                logger.debug(
                    f"   🔍 Found {len(height_info['allScrollableContainers'])} scrollable containers (sorted by scroll potential):")
                for sc in height_info['allScrollableContainers'][:5]:  # Show top 5
                    scroll_potential = sc.get('scrollPotential', sc['scrollHeight'] - sc['clientHeight'])
                    logger.debug(
                        f"      - <{sc['tag']}> class='{sc['className'][:30]}...' ({scroll_potential}px potential, {sc['scrollHeight']}px total)"[
                            :120])

            if height_info['scrollableContainer']:
                sc = height_info['scrollableContainer']
                scroll_potential = sc.get('scrollPotential', sc['scrollHeight'] - sc['clientHeight'])
                logger.info(
                    f"   ✅ BEST scrollable: <{sc['tag']}> class='{sc['className'][:30]}...' ({scroll_potential}px potential, {sc['scrollHeight']}px total)")

            if height_info.get('maxOffsetElement'):
                el = height_info['maxOffsetElement']
                logger.debug(
                    f"   📐 Max offset element: <{el['tag']}> class='{el['className']}' id='{el['id']}' ({el['offsetHeight']}px)")

            # ✅ CRITICAL: Get actual viewport height (what's visible on screen)
            # 🆕 IMPROVEMENT: Also detect if we're in headless mode for better diagnostics
            viewport_diagnostics = await page.evaluate("""() => {
                const isHeadless = (
                    navigator.webdriver === true ||
                    /HeadlessChrome/.test(navigator.userAgent) ||
                    navigator.plugins.length === 0
                );

                return {
                    innerHeight: window.innerHeight,
                    clientHeight: document.documentElement.clientHeight,
                    actualHeight: Math.max(window.innerHeight, document.documentElement.clientHeight),
                    isHeadless: isHeadless,
                    userAgent: navigator.userAgent.substring(0, 50) + '...',
                    pluginCount: navigator.plugins.length
                };
            }""")
            actual_viewport_height = viewport_diagnostics['actualHeight']
            logger.debug(f"📐 Actual viewport height: {actual_viewport_height}px")
            logger.debug(
                f"   🔍 Mode: {'Headless' if viewport_diagnostics['isHeadless'] else 'Headful'}, Plugins: {viewport_diagnostics['pluginCount']}")

            # Calculate scroll step (with overlap) using ACTUAL viewport height
            scroll_step = int(actual_viewport_height * (1 - overlap_percent / 100))

            # ✅ NEW: Check if URL matches non-scrollable patterns
            import json
            non_scrollable_patterns = []
            logger.debug(f"   🔍 DEBUG: non_scrollable_urls parameter = '{non_scrollable_urls}'")
            if non_scrollable_urls:
                try:
                    non_scrollable_patterns = json.loads(non_scrollable_urls)
                    logger.debug(f"   🔍 DEBUG: Parsed patterns = {non_scrollable_patterns}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Failed to parse non_scrollable_urls: {e}")
                    non_scrollable_patterns = []

            logger.debug(f"   🔍 DEBUG: Current URL = {url}")
            is_non_scrollable = any(
                pattern in url for pattern in non_scrollable_patterns
            ) if non_scrollable_patterns else False
            logger.debug(f"   🔍 DEBUG: is_non_scrollable = {is_non_scrollable}")

            if is_non_scrollable:
                estimated_segments = 1
                logger.info(f"   🔒 URL matched non-scrollable list - forcing single segment")
            # ✅ FIX: Check if page fits in viewport (non-scrollable)
            elif total_height <= actual_viewport_height:
                estimated_segments = 1
                logger.info(
                    f"   ℹ️  Non-scrollable page detected (total: {total_height}px ≤ viewport: {actual_viewport_height}px)")
                logger.info(f"   📸 Capturing single segment (no scroll needed)")
            else:
                # Calculate segments for scrollable pages
                import math
                # Use ceiling division to ensure we capture all content
                # Formula: ceil((total_height - viewport_height) / scroll_step) + 1
                # The +1 accounts for the first viewport
                estimated_segments = min(max_segments,
                                         math.ceil((total_height - actual_viewport_height) / scroll_step) + 1)

            logger.info(
                f"📊 Estimated segments: {estimated_segments} (scroll step: {scroll_step}px, overlap: {overlap_percent}%)")

            # Capture segments
            screenshot_paths = []
            position = 0
            segment_index = 1
            previous_hash = None
            previous_scroll_position = None  # ✅ NEW: Track previous scroll position for duplicate detection

            while position < total_height and segment_index <= max_segments and segment_index <= estimated_segments:
                # ✅ FIX: Check if there are remaining pixels to capture
                remaining_pixels = total_height - position

                # ✅ CRITICAL: Use actual_viewport_height (what's visible), not viewport_height (browser parameter)
                # If remaining pixels are less than actual viewport, we need one more segment to capture them
                needs_final_segment = remaining_pixels > 0 and remaining_pixels < actual_viewport_height

                # ✅ FIX: For the last segment, scroll to the bottom to ensure we capture everything
                is_last_segment = needs_final_segment or (position + actual_viewport_height >= total_height)

                if is_last_segment:
                    # Scroll to bottom (total_height - actual_viewport_height) to capture the last viewport
                    final_position = max(0, total_height - actual_viewport_height)
                    logger.debug(
                        f"   📍 Last segment: scrolling to {final_position}px (bottom of page, remaining: {remaining_pixels}px, actual viewport: {actual_viewport_height}px)")
                else:
                    final_position = position

                # ✅ REAL-WORLD SCROLL: Scroll the correct element with smooth scroll detection
                logger.debug(f"   🔄 Scrolling to {final_position}px (has_scrollable_element={has_scrollable_element})...")

                if has_scrollable_element:
                    # 🆕 IMPROVEMENT: Scroll element and wait for scroll to settle
                    scroll_result = await page.evaluate(f"""
                        if (window.__scrollableElement) {{
                            const el = window.__scrollableElement;
                            const beforeScroll = el.scrollTop;

                            // Disable smooth scroll temporarily for instant positioning
                            const originalBehavior = el.style.scrollBehavior;
                            el.style.scrollBehavior = 'auto';

                            // Scroll to position
                            el.scrollTop = {final_position};

                            // Restore original scroll behavior
                            el.style.scrollBehavior = originalBehavior;

                            const afterScroll = el.scrollTop;

                            console.log('✅ Scrolled element from', beforeScroll, 'to', afterScroll, 'px (target:', {final_position}, 'px)');

                            return {{
                                success: true,
                                before: beforeScroll,
                                after: afterScroll,
                                target: {final_position},
                                elementFound: true
                            }};
                        }} else {{
                            console.error('❌ ERROR: __scrollableElement not found!');
                            window.scrollTo({{top: {final_position}, behavior: 'auto'}});
                            return {{
                                success: false,
                                elementFound: false,
                                target: {final_position}
                            }};
                        }}
                    """)
                    logger.info(f"   📊 Scroll result: {scroll_result}")
                else:
                    # 🆕 IMPROVEMENT: Scroll window with instant positioning (no smooth scroll)
                    await page.evaluate(f"window.scrollTo({{top: {final_position}, behavior: 'auto'}})")
                    logger.info(f"   📊 Scrolled window to {final_position}px")

                # 🆕 IMPROVEMENT: Wait for scroll to settle and content to render
                await asyncio.sleep(0.1)  # Short wait for scroll to complete

                # 🆕 IMPROVEMENT: Verify scroll position reached
                actual_scroll = await page.evaluate("""
                    window.__scrollableElement
                        ? window.__scrollableElement.scrollTop
                        : window.pageYOffset || document.documentElement.scrollTop
                """)

                logger.info(f"   ✅ Verified scroll position: {actual_scroll}px (target: {final_position}px)")

                if abs(actual_scroll - final_position) > 10:  # Allow 10px tolerance
                    logger.warning(f"   ⚠️  Scroll position mismatch: expected {final_position}px, got {actual_scroll}px")

                # Wait for content to load after scroll
                await asyncio.sleep(scroll_delay_ms / 1000.0)

                # Smart lazy-load detection
                if smart_lazy_load:
                    await self._wait_for_lazy_load(page)

                # Generate filename based on base URL logic
                filename = self._generate_filename(url, base_url, words_to_remove, segment_index, estimated_segments)
                filepath = self.output_dir / filename

                # Debug: Check viewport state before capture
                if segment_index == 1:  # Only log for first segment to avoid spam
                    try:
                        viewport_check = await page.evaluate("""
                            () => {
                                return {
                                    scrollY: window.scrollY,
                                    innerHeight: window.innerHeight,
                                    bodyHeight: document.body.scrollHeight,
                                    visibleText: document.body.innerText.substring(0, 100)
                                };
                            }
                        """)
                        logger.info(
                            f"   📊 Viewport: scrollY={viewport_check['scrollY']}, height={viewport_check['innerHeight']}")
                        logger.debug(f"   📝 Visible text: {viewport_check['visibleText'][:50]}...")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Could not check viewport: {str(e)}")

                # Capture screenshot
                from datetime import datetime
                logger.info(f"   📸 [{datetime.now().strftime('%H:%M:%S')}] Capturing segment {segment_index}...")

                # ✅ NEW: Send WebSocket notification for segment progress (only for multi-segment captures)
                if estimated_segments > 1:
                    # ✅ FIXED (Bug #11): Use helper method to properly track background task
                    self._send_websocket_message_background({
                        "type": "segment_progress",
                        "segment_index": segment_index,
                        "total_segments": estimated_segments,
                        "url": url
                    })

                await page.screenshot(path=str(filepath), full_page=False, type='png', timeout=screenshot_timeout)

                # ✅ NEW: Log file save with details
                if filepath.exists():
                    file_size = filepath.stat().st_size
                    logger.info(f"   ✅ [{datetime.now().strftime('%H:%M:%S')}] Segment {segment_index} saved!")
                    logger.debug(f"   📁 File: {filepath.name}")
                    logger.info(f"   📊 Size: {file_size / 1024:.1f} KB")

                # Verify screenshot (only for first segment to avoid spam)
                if segment_index == 1 and filepath.exists():
                    try:
                        from PIL import Image
                        img = Image.open(filepath)
                        width, height = img.size
                        extrema = img.convert("L").getextrema()
                        logger.debug(f"   📐 Segment 1 image: {width}x{height}, brightness: {extrema[0]}-{extrema[1]}")
                        if extrema[0] == extrema[1]:
                            logger.warning(f"   ⚠️  WARNING: Segment 1 appears blank (single color: {extrema[0]})")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Could not verify segment 1: {str(e)}")

                # ✅ IMPROVED: Use extracted duplicate detection method with scroll position check
                if skip_duplicates:
                    is_duplicate, current_hash = self._check_and_handle_duplicate(
                        filepath=filepath,
                        previous_hash=previous_hash,
                        segment_index=segment_index,
                        estimated_segments=estimated_segments,
                        current_scroll_position=actual_scroll,  # ✅ NEW: Pass current scroll position
                        previous_scroll_position=previous_scroll_position,  # ✅ NEW: Pass previous scroll position
                        scroll_position_tolerance=10  # ✅ NEW: 10px tolerance
                    )

                    if is_duplicate:
                        # Update hash and scroll position, then skip to next segment
                        previous_hash = current_hash
                        previous_scroll_position = actual_scroll  # ✅ NEW: Update previous scroll position
                        position += scroll_step
                        segment_index += 1
                        continue

                    # Update hash and scroll position for next comparison
                    previous_hash = current_hash
                    previous_scroll_position = actual_scroll  # ✅ NEW: Update previous scroll position

                screenshot_paths.append(str(filepath))
                logger.info(f"✅ Segment {segment_index}/{estimated_segments} captured: {filename}")

                # Move to next position
                position += scroll_step
                segment_index += 1

                # ✅ FIX: Break after capturing the last segment
                if is_last_segment:
                    break

            # ========================================
            # 🎯 Solution #5: Save cookies for future sessions
            # ========================================
            if use_stealth:
                await self._save_cookies(context)

            logger.debug(f"🎉 Segmented capture complete! {len(screenshot_paths)} segments saved")
            return screenshot_paths

        finally:
            await page.close()
            await context.close()

    async def _capture_segments_from_page(
            self,
            page: Page,
            url: str,
            viewport_width: int,
            viewport_height: int,
            overlap_percent: int,
            scroll_delay_ms: int,
            max_segments: int,
            skip_duplicates: bool,
            smart_lazy_load: bool,
            track_network: bool = False,  # ✅ NEW: Optional network tracking
            auto_expand_dropdowns: bool = False,  # ✅ NEW: Auto expand dropdowns
            base_url: str = "",  # ✅ FIX: Add base_url parameter
            words_to_remove: str = "",  # ✅ FIX: Add words_to_remove parameter
            screenshot_timeout: int = 30000,  # ✅ FIX: Add screenshot_timeout parameter
            non_scrollable_urls: str = ""  # ✅ FIX: Add non_scrollable_urls parameter
    ) -> list[str]:
        """
        🔗 Capture segments from an existing page (used for CDP active tab mode)

        This is a simplified version that works with an already-loaded page.

        Args:
            track_network: If True, capture and display network events during page load
        """
        # Wait for page to be ready
        await asyncio.sleep(1.0)

        # ✅ NEW: Initialize network_events list if tracking is enabled
        network_events = [] if track_network else None

        # ✅ FIX: Detect and wait for page reloads (common with SPAs)
        logger.debug("   🔄 Monitoring page for reloads/redirects...")

        # Get initial URL
        initial_url = page.url
        logger.debug(f"   📍 Initial URL: {initial_url}")

        reload_count = 0
        max_reload_wait = self.CDP_RELOAD_WAIT_SECONDS
        last_url = initial_url

        for i in range(max_reload_wait):
            await asyncio.sleep(1.0)

            # ✅ OPTIMIZATION: Batch multiple checks into single page.evaluate() call
            page_info = await page.evaluate("""() => {
                return {
                    url: window.location.href,
                    readyState: document.readyState,
                    title: document.title
                };
            }""")

            current_url = page_info['url']
            ready_state = page_info['readyState']

            # Detect URL change (redirect/reload)
            if current_url != last_url:
                reload_count += 1
                logger.debug(f"   🔄 URL changed (reload {reload_count}):")
                logger.debug(f"      From: {last_url}")
                logger.debug(f"      To:   {current_url}")
                last_url = current_url

                # Wait for new page to load
                try:
                    await page.wait_for_load_state('load', timeout=5000)
                    await page.wait_for_load_state('domcontentloaded', timeout=5000)
                    logger.info(f"   ✅ Reload {reload_count} complete (readyState: {ready_state})")
                except Exception as e:
                    logger.warning(f"   ⚠️  Timeout waiting for reload {reload_count}: {str(e)}")

                # Reset counter to wait for more potential reloads
                continue

            # Check if page is still loading
            if ready_state != 'complete':
                logger.debug(f"   ⏳ Page loading... (readyState: {ready_state})")
                continue

            # Page is stable (same URL, readyState complete)
            # Wait 2 more seconds to be sure
            if i >= 2:  # At least 2 seconds of stability
                logger.info(f"   ✅ Page stable for {i} seconds")
                break

        if reload_count > 0:
            logger.info(f"   ✅ All page reloads complete ({reload_count} reloads detected)")
            logger.debug(f"   📍 Final URL: {last_url}")
        else:
            logger.info(f"   ✅ No page reloads detected")

        # ✅ NOTE: Network listeners are removed automatically when the page is closed
        # No need to manually remove them here

        if network_events:
            logger.info(f"   🌐 Network activity during page load ({len(network_events)} events):")

            # Count by type
            xhr_count = sum(
                1 for e in network_events if e.get('type') in ['xhr', 'fetch'] and e.get('event') == 'request')
            doc_count = sum(1 for e in network_events if e.get('type') == 'document' and e.get('event') == 'request')
            ws_count = sum(1 for e in network_events if e.get('type') == 'websocket')
            failed_count = sum(1 for e in network_events if e.get('event') == 'failed')

            logger.debug(f"      📄 Document requests: {doc_count}")
            logger.debug(f"      🔄 XHR/Fetch requests: {xhr_count}")
            if ws_count > 0:
                logger.debug(f"      🔌 WebSocket connections: {ws_count}")
            if failed_count > 0:
                logger.error(f"      ❌ Failed requests: {failed_count}")

            # Show document navigations with timing and status
            doc_requests = [e for e in network_events if
                            e.get('type') == 'document' and e.get('event') in ['request', 'response']]
            if doc_requests:
                logger.info(f"      📋 Document navigations (chronological):")
                for i, req in enumerate(doc_requests[:10], 1):  # Show first 10
                    event_type = req.get('event')
                    timestamp = req.get('timestamp', 0)
                    url = req['url'][:70]

                    if event_type == 'request':
                        method = req.get('method', 'GET')
                        logger.debug(f"         {i}. [{timestamp:.1f}s] {method} {url}")
                    elif event_type == 'response':
                        status = req.get('status', '?')
                        status_text = req.get('statusText', '')
                        logger.debug(f"         {i}. [{timestamp:.1f}s] ← {status} {status_text} {url}")

            # Show XHR/Fetch requests with status codes
            xhr_requests = [e for e in network_events if e.get('type') in ['xhr', 'fetch']]
            if xhr_requests:
                logger.info(f"      📋 XHR/Fetch activity (last 10):")
                for i, req in enumerate(xhr_requests[-10:], 1):
                    event_type = req.get('event')
                    timestamp = req.get('timestamp', 0)
                    url = req['url'][:70]

                    if event_type == 'request':
                        method = req.get('method', 'GET')
                        logger.debug(f"         {i}. [{timestamp:.1f}s] → {method} {url}")
                    elif event_type == 'response':
                        status = req.get('status', '?')
                        logger.debug(f"         {i}. [{timestamp:.1f}s] ← {status} {url}")

            # Show failed requests
            failed_requests = [e for e in network_events if e.get('event') == 'failed']
            if failed_requests:
                logger.error(f"      ❌ Failed requests:")
                for i, req in enumerate(failed_requests[:5], 1):
                    timestamp = req.get('timestamp', 0)
                    url = req['url'][:70]
                    failure = req.get('failure', 'Unknown error')
                    logger.debug(f"         {i}. [{timestamp:.1f}s] {url}")
                    logger.debug(f"            Error: {failure}")

            # Show redirects (3xx responses)
            redirects = [e for e in network_events if e.get('event') == 'response' and 300 <= e.get('status', 0) < 400]
            if redirects:
                logger.debug(f"      🔀 Redirects detected:")
                for i, req in enumerate(redirects[:5], 1):
                    timestamp = req.get('timestamp', 0)
                    status = req.get('status')
                    url = req['url'][:70]
                    location = req.get('headers', {}).get('location', 'N/A')
                    logger.debug(f"         {i}. [{timestamp:.1f}s] {status} {url}")
                    if location != 'N/A':
                        logger.debug(f"            → {location}")

        # ✅ BEST PRACTICE: Disable animations AFTER reloads are complete
        logger.debug("   🎨 Disabling animations for stable capture...")
        await page.add_style_tag(content="""
            *, *::before, *::after {
                transition: none !important;
                animation: none !important;
                scroll-behavior: auto !important;
            }
        """)

        # ========================================
        # 🎯 DEBUG LOGGING: URL and Feature Status
        # ========================================
        logger.debug(f"\n{'=' * 80}")
        logger.info(f"🎯 URL: {url}")
        logger.info(f"🎯 Auto-expand dropdowns: {'ENABLED ✅' if auto_expand_dropdowns else 'DISABLED ❌'}")
        logger.debug(f"{'=' * 80}\n")

        # ✅ NEW: Auto-expand dropdowns if enabled (BEFORE height stabilization)
        if auto_expand_dropdowns:
            await self._expand_all_dropdowns(page)
            # ⏱️ CRITICAL: Wait for page to settle after expansion
            # Dropdowns may trigger layout changes, lazy loading, or animations
            logger.info("   ⏱️  Waiting for page to settle after dropdown expansion...")
            await asyncio.sleep(2.0)
            logger.info("   ✅ Page settled, ready to measure height...")

            # 🆕 NEW: Scroll all nested scrollable elements to reveal hidden content
            await self._scroll_all_nested_elements(page)
        else:
            logger.info("   ℹ️  Auto-expand dropdowns is DISABLED - skipping dropdown detection")

        # ========================================
        # 🎯 DEBUG LOGGING: URL Config Matching
        # ========================================
        logger.debug(f"\n🔍 Checking for URL-specific configuration...")
        logger.info(f"   🔗 URL to match: {url}")

        # ✅ NEW: Click elements - check URL config first, then manual parameter
        url_config = self._find_url_config(url)
        per_url_auto_expand = bool(url_config.get("auto_expand_dropdowns")) if url_config else False

        # ✅ FIX: Initialize list to collect form screenshots from click actions
        form_screenshots_from_actions = []

        if url_config:
            # Use saved URL-specific configuration
            config_name = url_config.get('name', 'Unnamed')
            actions_count = len(url_config.get('actions', []))

            logger.info(f"📋 ✅ Found saved configuration: '{config_name}'")
            logger.info(f"   🔗 Matched pattern: {url_config.get('url_pattern')}")
            logger.info(f"   🔍 Match type: {url_config.get('match_type')}")
            logger.debug(f"   🎬 Actions count: {actions_count}")

            # ✅ NEW: Send WebSocket notification for URL config detection
            # ✅ FIXED (Bug #11): Use helper method to properly track background task
            self._send_websocket_message_background({
                "type": "url_config_detected",
                "config_name": config_name,
                "url": url,
                "actions_count": actions_count,
                "url_pattern": url_config.get('url_pattern'),
                "match_type": url_config.get('match_type')
            })
            logger.info(f"   📡 WebSocket notification sent: URL config detected")

            actions = url_config.get("actions", [])

            for i, action in enumerate(actions, 1):
                action_type = action.get("type", "")

                if action_type == "click":
                    text = action.get("text", "")
                    wait_ms = action.get("wait_after_ms", 2000)
                    description = action.get("description", "")

                    logger.debug(f"   🖱️  Action {i}/{len(actions)}: Click '{text}'")
                    if description:
                        logger.debug(f"      ℹ️  {description}")

                    # ✅ NEW: Send WebSocket notification for action execution
                    # ✅ FIXED (Bug #11): Use helper method to properly track background task
                    self._send_websocket_message_background({
                        "type": "url_config_action",
                        "action_index": i,
                        "total_actions": len(actions),
                        "action_type": "click",
                        "description": description or f"Click '{text}'"
                    })
                    logger.info(f"      📡 WebSocket notification sent: Action execution")

                    await self._click_elements_by_text(page, [text])
                    await asyncio.sleep(wait_ms / 1000)

                elif action_type == "click_active_forms":
                    # 🆕 NEW: Advanced action - Click all active forms dynamically
                    form_name = action.get("form_name", "")
                    status_required = action.get("status_required", "Active")
                    scroll_opened = action.get("scroll_opened_page", True)
                    close_after = action.get("close_after_scroll", True)
                    wait_after_click = action.get("wait_after_click_ms", 2000)
                    wait_after_scroll = action.get("wait_after_scroll_ms", 1000)
                    description = action.get("description", "")

                    logger.info(f"   🎯 Action {i}/{len(actions)}: Click Active Forms")
                    if description:
                        logger.debug(f"      ℹ️  {description}")

                    # ✅ NEW: Send WebSocket notification for action execution
                    # ✅ FIXED (Bug #11): Use helper method to properly track background task
                    self._send_websocket_message_background({
                        "type": "url_config_action",
                        "action_index": i,
                        "total_actions": len(actions),
                        "action_type": "click_active_forms",
                        "description": description or "Click all active forms"
                    })
                    logger.info(f"      📡 WebSocket notification sent: Action execution")

                    form_screenshots = await self._click_active_forms(
                        page,
                        form_name=form_name,
                        status_required=status_required,
                        scroll_opened=scroll_opened,
                        close_after=close_after,
                        wait_after_click_ms=wait_after_click,
                        wait_after_scroll_ms=wait_after_scroll,
                        # Pass screenshot parameters
                        capture_screenshots=True,
                        url=url,
                        viewport_width=viewport_width,
                        viewport_height=viewport_height,
                        overlap_percent=overlap_percent,
                        scroll_delay_ms=scroll_delay_ms,
                        max_segments=max_segments,
                        base_url=base_url,
                        words_to_remove=words_to_remove,
                        non_scrollable_urls=non_scrollable_urls  # ✅ FIX: Pass non_scrollable_urls parameter
                    )
                    # ✅ FIX: Collect form screenshots to be included in Word document
                    if form_screenshots:
                        form_screenshots_from_actions.extend(form_screenshots)
                        logger.info(
                            f"   📸 Collected {len(form_screenshots)} form screenshot(s) for Word document"
                        )

            logger.info("   ✅ All configured actions completed")

            # 🔽 URL-specific dropdown expansion after configured actions
            if per_url_auto_expand:
                logger.info("   🔽 URL config requested dropdown auto-expansion after actions")
                await self._expand_all_dropdowns(page)
                logger.info(
                    "   ⏱️  Waiting for page to settle after URL-specific dropdown expansion..."
                )
                await asyncio.sleep(2.0)
                logger.info("   ✅ URL-specific dropdown expansion complete")

            if form_screenshots_from_actions:
                logger.info(
                    f"   📸 Total form screenshots from all actions: {len(form_screenshots_from_actions)}"
                )
        else:
            logger.error(f"ℹ️  ❌ No URL-specific configuration found for: {url}")
            logger.info(
                "   💡 Auto-expand dropdowns was the only expansion method used"
            )

        # ✅ BEST PRACTICE: Incremental scrolling to stabilize height (from Playwright best practices)
        # ✅ IMPORTANT: This runs AFTER dropdown expansion, so height includes expanded content
        logger.info("   🔄 Stabilizing page height with incremental scrolling...")

        # ✅ FIX: Find the ACTUAL scrollable element (not just tekion-workspace) and CACHE it
        # 🆕 IMPROVEMENT: Enhanced detection with better selector priority and visibility checks
        scrollable_info = await page.evaluate("""() => {
            // Find element with largest scrollable content
            let maxScrollableHeight = 0;
            let bestElement = null;
            let bestSelector = 'window';
            let candidates = [];

            // 🆕 IMPROVEMENT: Prioritize common scrollable container selectors first
            const prioritySelectors = [
                '#tekion-workspace',
                '[role="main"]',
                'main',
                '.main-content',
                '#main',
                '#content',
                '.content',
                '[class*="scroll"]',
                '[class*="content"]'
            ];

            // Check priority selectors first
            for (const selector of prioritySelectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const hasOverflow = (
                            style.overflow === 'auto' ||
                            style.overflow === 'scroll' ||
                            style.overflowY === 'auto' ||
                            style.overflowY === 'scroll'
                        );

                        // 🆕 IMPROVEMENT: Check visibility
                        const isVisible = (
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            el.offsetParent !== null
                        );

                        if (hasOverflow && el.scrollHeight > el.clientHeight && isVisible) {
                            candidates.push({
                                element: el,
                                scrollHeight: el.scrollHeight,
                                clientHeight: el.clientHeight,
                                scrollPotential: el.scrollHeight - el.clientHeight,
                                selector: selector,
                                priority: true
                            });
                        }
                    });
                } catch (e) {
                    // Selector might be invalid, skip it
                }
            }

            // If no priority selectors found, scan all elements
            if (candidates.length === 0) {
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const style = window.getComputedStyle(el);
                    const hasOverflow = (
                        style.overflow === 'auto' ||
                        style.overflow === 'scroll' ||
                        style.overflowY === 'auto' ||
                        style.overflowY === 'scroll'
                    );

                    const isVisible = (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        el.offsetParent !== null
                    );

                    if (hasOverflow && el.scrollHeight > el.clientHeight && isVisible) {
                        candidates.push({
                            element: el,
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight,
                            scrollPotential: el.scrollHeight - el.clientHeight,
                            selector: el.id ? `#${el.id}` : `.${el.className.split(' ')[0]}`,
                            priority: false
                        });
                    }
                }
            }

            // Sort by scroll potential (largest first)
            candidates.sort((a, b) => b.scrollPotential - a.scrollPotential);

            // Pick the best candidate
            if (candidates.length > 0) {
                const best = candidates[0];
                bestElement = best.element;
                maxScrollableHeight = best.scrollHeight;
                bestSelector = best.selector;
            }

            // ✅ CACHE the element in window object so we always use the same one
            window.__scrollableElement = bestElement;

            return {
                selector: bestSelector,
                scrollHeight: maxScrollableHeight,
                clientHeight: bestElement ? bestElement.clientHeight : window.innerHeight,
                hasElement: bestElement !== null,
                candidateCount: candidates.length,
                isPriority: candidates.length > 0 ? candidates[0].priority : false
            };
        }""")
        logger.debug(
            f"   📍 Scrollable element: {scrollable_info['selector']} (scrollHeight: {scrollable_info['scrollHeight']}px, clientHeight: {scrollable_info['clientHeight']}px)")
        logger.debug(
            f"      🔍 Found {scrollable_info['candidateCount']} candidates, using {'priority' if scrollable_info.get('isPriority') else 'fallback'} selector")

        last_height = 0
        stable_count = 0

        # 🆕 IMPROVEMENT: Adjust stabilization parameters based on browser mode
        # Headless mode: Faster, more aggressive (content loads instantly)
        # Headful mode: Slower, more patient (content may load gradually)
        try:
            mode_info = await self._detect_browser_mode(page)
            is_headless = mode_info['isHeadless']

            if is_headless:
                # Headless: Fast stabilization (content loads instantly)
                max_attempts = 20  # Max 10 seconds
                stabilize_delay = 0.3  # 300ms between checks
                logger.debug(f"   ⚡ Headless mode detected: using fast stabilization (20 attempts × 300ms)")
            else:
                # Headful: Patient stabilization (content may load gradually)
                max_attempts = 30  # Max 21 seconds
                stabilize_delay = 0.5  # 500ms between checks
                logger.debug(f"   🐢 Headful mode detected: using patient stabilization (30 attempts × 500ms)")
        except Exception:
            # Fallback to default values
            max_attempts = 30
            stabilize_delay = 0.5
            logger.debug(f"   ℹ️  Using default stabilization (30 attempts × 500ms)")

        for attempt in range(max_attempts):
            # Scroll by viewport height to trigger lazy loading
            # ✅ FIX: Use the CACHED scrollable element
            await page.evaluate(f"""() => {{
                const bestElement = window.__scrollableElement;
                if (bestElement) {{
                    bestElement.scrollBy(0, {viewport_height});
                }} else {{
                    window.scrollBy(0, {viewport_height});
                }}
            }}""")

            # Wait for content to load
            await asyncio.sleep(stabilize_delay)

            # Measure current height
            # ✅ FIX: Use the CACHED scrollable element and just return scrollHeight
            current_height = await page.evaluate("""() => {
                const bestElement = window.__scrollableElement;

                if (bestElement) {
                    return bestElement.scrollHeight;
                } else {
                    return Math.max(
                        document.documentElement.scrollHeight,
                        document.body.scrollHeight
                    );
                }
            }""")

            if attempt % 5 == 0:  # Log every 5th attempt
                logger.debug(f"   📐 Height check {attempt + 1}: {current_height}px (last: {last_height}px)")

            # Check if height has stabilized
            if current_height == last_height:
                stable_count += 1
            else:
                stable_count = 0
                last_height = current_height

            # ✅ FIX: Only check for stabilization after at least 5 attempts (reduced from 10)
            # This prevents early exit when content hasn't loaded yet
            if attempt >= 5:
                # If height is stable for 4 consecutive checks, we're done (reduced from 6)
                if stable_count >= 4:
                    logger.info(f"   ✅ Height stabilized at {current_height}px after {attempt + 1} attempts")
                    break

                # Check if we've reached the bottom
                # ✅ FIX: Use the CACHED scrollable element
                at_bottom = await page.evaluate("""() => {
                    const bestElement = window.__scrollableElement;

                    if (bestElement) {
                        return (bestElement.scrollTop + bestElement.clientHeight) >= (bestElement.scrollHeight - 5);
                    } else {
                        return (window.innerHeight + window.scrollY) >= (document.documentElement.scrollHeight - 5);
                    }
                }""")

                if at_bottom and stable_count > 2:  # Reduced from 3 to 2
                    logger.info(f"   ✅ Reached bottom and height stable at {current_height}px after {attempt + 1} attempts")
                    break

        # Scroll back to top
        # ✅ FIX: Use the CACHED scrollable element
        await page.evaluate("""() => {
            const bestElement = window.__scrollableElement;

            if (bestElement) {
                bestElement.scrollTop = 0;
            } else {
                window.scrollTo(0, 0);
            }
        }""")
        await asyncio.sleep(0.5)

        # ✅ Get final stabilized height (already calculated during stabilization)
        # ✅ FIX: Use the CACHED scrollable element and just return scrollHeight
        height_info = await page.evaluate("""() => {
            const bestElement = window.__scrollableElement;

            if (bestElement) {
                // Debug info
                const selector = bestElement.id ? `#${bestElement.id}` : `.${bestElement.className.split(' ')[0]}`;
                return {
                    height: bestElement.scrollHeight,
                    selector: selector,
                    scrollHeight: bestElement.scrollHeight,
                    clientHeight: bestElement.clientHeight,
                    cached: true
                };
            } else {
                return {
                    height: Math.max(
                        document.documentElement.scrollHeight,
                        document.body.scrollHeight
                    ),
                    selector: 'window',
                    cached: false
                };
            }
        }""")

        total_height = height_info['height']
        logger.debug(
            f"   🔍 Final height measurement: {total_height}px from {height_info['selector']} (cached: {height_info.get('cached', False)})")
        if height_info.get('cached'):
            logger.debug(
                f"      scrollHeight: {height_info.get('scrollHeight')}px, clientHeight: {height_info.get('clientHeight')}px")

        logger.info(f"📏 Final page height: {total_height}px")

        # ✅ CRITICAL FIX: Use ACTUAL measured viewport height, not parameter!
        # The scrollable element might have a different height than the browser viewport
        # Example: browser viewport = 1080px, but scrollable element = 675px
        actual_viewport_height = scrollable_info['clientHeight']

        # Calculate scroll step (with overlap)
        # Formula: scroll_step = viewport_height * (1 - overlap_percent / 100)
        # Example: 675px * 0.8 = 540px (with 20% overlap)
        scroll_step = int(actual_viewport_height * (1 - overlap_percent / 100))

        # Ensure scroll_step is positive
        if scroll_step <= 0:
            scroll_step = actual_viewport_height
            logger.warning(f"   ⚠️  Invalid scroll_step calculated, using viewport_height instead")

        # ✅ NEW: Check if URL matches non-scrollable patterns
        import json
        non_scrollable_patterns = []
        logger.debug(f"   🔍 DEBUG: non_scrollable_urls parameter = '{non_scrollable_urls}'")
        if non_scrollable_urls:
            try:
                non_scrollable_patterns = json.loads(non_scrollable_urls)
                logger.debug(f"   🔍 DEBUG: Parsed patterns = {non_scrollable_patterns}")
            except Exception as e:
                logger.warning(f"   ⚠️  Failed to parse non_scrollable_urls: {e}")
                non_scrollable_patterns = []

        logger.debug(f"   🔍 DEBUG: Current URL = {url}")
        is_non_scrollable = any(
            pattern in url for pattern in non_scrollable_patterns
        ) if non_scrollable_patterns else False
        logger.debug(f"   🔍 DEBUG: is_non_scrollable = {is_non_scrollable}")

        if is_non_scrollable:
            estimated_segments = 1
            logger.debug(f"   🔒 URL matched non-scrollable list - forcing single segment")
        # ✅ FIX: Check if page fits in viewport (non-scrollable)
        elif total_height <= actual_viewport_height:
            estimated_segments = 1
            logger.debug(
                f"   ℹ️  Non-scrollable page detected (total: {total_height}px ≤ viewport: {actual_viewport_height}px)")
            logger.info(f"   📸 Capturing single segment (no scroll needed)")
        else:
            # Calculate segments for scrollable pages
            import math
            estimated_segments = min(max_segments, math.ceil((total_height - actual_viewport_height) / scroll_step) + 1)

        logger.info(
            f"📊 Estimated segments: {estimated_segments} (scroll step: {scroll_step}px, overlap: {overlap_percent}%, actual viewport: {actual_viewport_height}px)")

        # Capture segments
        screenshot_paths = []
        position = 0
        segment_index = 1
        previous_hash = None
        previous_scroll_position = None  # ✅ NEW: Track previous scroll position for duplicate detection

        while position < total_height and segment_index <= max_segments and segment_index <= estimated_segments:
            # ✅ FIX: Check if there are remaining pixels to capture
            remaining_pixels = total_height - position

            # ✅ CRITICAL: Use actual_viewport_height (scrollable element), not viewport_height (browser)
            # If remaining pixels are less than actual viewport, we need one more segment to capture them
            needs_final_segment = remaining_pixels > 0 and remaining_pixels < actual_viewport_height

            # ✅ FIX: For the last segment, scroll to the bottom to ensure we capture everything
            is_last_segment = needs_final_segment or (position + actual_viewport_height >= total_height)

            if is_last_segment:
                # Scroll to bottom (total_height - actual_viewport_height) to capture the last viewport
                final_position = max(0, total_height - actual_viewport_height)
                logger.debug(
                    f"   📍 Last segment: scrolling to {final_position}px (bottom of page, remaining: {remaining_pixels}px, actual viewport: {actual_viewport_height}px)")
            else:
                final_position = position

            # Scroll to position with retry to ensure it sticks
            # ✅ FIX: Use the CACHED scrollable element and retry if scroll doesn't stick
            for retry in range(self.MAX_SCROLL_RETRIES):
                await page.evaluate(f"""() => {{
                    const bestElement = window.__scrollableElement;

                    if (bestElement) {{
                        bestElement.scrollTop = {final_position};
                        // Force immediate scroll (no smooth behavior)
                        bestElement.style.scrollBehavior = 'auto';
                    }} else {{
                        window.scrollTo(0, {final_position});
                    }}
                }}""")

                # Wait a bit for scroll to complete
                await asyncio.sleep(0.15)

                # Verify scroll position
                scroll_info = await page.evaluate("""() => {
                    const bestElement = window.__scrollableElement;

                    if (bestElement) {
                        return {
                            scrollTop: bestElement.scrollTop,
                            scrollHeight: bestElement.scrollHeight,
                            clientHeight: bestElement.clientHeight,
                            captureStart: bestElement.scrollTop,
                            captureEnd: bestElement.scrollTop + bestElement.clientHeight
                        };
                    } else {
                        return {
                            scrollTop: window.scrollY,
                            scrollHeight: document.documentElement.scrollHeight,
                            clientHeight: window.innerHeight,
                            captureStart: window.scrollY,
                            captureEnd: window.scrollY + window.innerHeight
                        };
                    }
                }""")

                # Check if scroll position is close enough (within 10px tolerance)
                if abs(scroll_info['scrollTop'] - final_position) <= 10:
                    break

                if retry < 2:
                    logger.debug(
                        f"   🔄 Retry {retry + 1}: scroll position {scroll_info['scrollTop']:.0f}px, target {final_position}px")

            if scroll_info['scrollTop'] != final_position:
                logger.warning(
                    f"   ⚠️  Segment {segment_index}: tried to scroll to {final_position}px but ended at {scroll_info['scrollTop']:.0f}px!")
            logger.debug(
                f"   🔍 Segment {segment_index}: capturing {scroll_info['captureStart']:.0f}-{scroll_info['captureEnd']:.0f}px (viewport: {scroll_info['clientHeight']}px)")

            # Wait for content to load
            await asyncio.sleep(scroll_delay_ms / 1000.0)

            # Smart lazy-load detection
            if smart_lazy_load:
                await self._wait_for_lazy_load(page)

            # ✅ FIX: Re-verify and force scroll position RIGHT BEFORE screenshot
            # Something is resetting the scroll during the wait!
            await page.evaluate(f"""() => {{
                const bestElement = window.__scrollableElement;

                if (bestElement) {{
                    bestElement.scrollTop = {final_position};
                    bestElement.style.scrollBehavior = 'auto';
                }} else {{
                    window.scrollTo(0, {final_position});
                }}
            }}""")

            # Verify it stuck
            actual_scroll = await page.evaluate("""() => {
                const bestElement = window.__scrollableElement;
                return bestElement ? bestElement.scrollTop : window.scrollY;
            }""")

            if abs(actual_scroll - final_position) > 10:
                logger.warning(
                    f"   ⚠️  SCROLL RESET DETECTED! Before screenshot: expected {final_position}px, got {actual_scroll:.0f}px")
                logger.info(f"   🔧 Forcing scroll position again...")
                # Force it one more time
                await page.evaluate(f"""() => {{
                    const bestElement = window.__scrollableElement;
                    if (bestElement) {{
                        bestElement.scrollTop = {final_position};
                    }} else {{
                        window.scrollTo(0, {final_position});
                    }}
                }}""")
                await asyncio.sleep(0.1)

            # Generate filename based on base URL logic
            filename = self._generate_filename(url, base_url, words_to_remove, segment_index, estimated_segments)
            filepath = self.output_dir / filename

            # ✅ DEBUG: Log exact scroll position at moment of screenshot
            final_scroll_check = await page.evaluate("""() => {
                const bestElement = window.__scrollableElement;
                if (bestElement) {
                    return {
                        scrollTop: bestElement.scrollTop,
                        scrollHeight: bestElement.scrollHeight,
                        clientHeight: bestElement.clientHeight,
                        offsetTop: bestElement.offsetTop,
                        offsetLeft: bestElement.offsetLeft
                    };
                } else {
                    return {
                        scrollTop: window.scrollY,
                        scrollHeight: document.documentElement.scrollHeight,
                        clientHeight: window.innerHeight,
                        offsetTop: 0,
                        offsetLeft: 0
                    };
                }
            }""")
            logger.info(
                f"   📸 Taking screenshot at scrollTop={final_scroll_check['scrollTop']:.0f}px (offset: {final_scroll_check['offsetTop']}, {final_scroll_check['offsetLeft']})")

            # ✅ ALWAYS capture the full viewport (includes header, sidebar, etc.)
            # The scrolling is handled by scrolling the element, but we capture the whole page
            from datetime import datetime
            logger.info(
                f"   📸 [{datetime.now().strftime('%H:%M:%S')}] Capturing segment {segment_index}/{estimated_segments}...")

            # ✅ NEW: Send WebSocket notification for segment progress (only for multi-segment captures)
            if estimated_segments > 1:
                # ✅ FIXED (Bug #11): Use helper method to properly track background task
                self._send_websocket_message_background({
                    "type": "segment_progress",
                    "segment_index": segment_index,
                    "total_segments": estimated_segments,
                    "url": url
                })

            # Capture screenshot IMMEDIATELY (no delays!)
            await page.screenshot(path=str(filepath), full_page=False, type='png', timeout=screenshot_timeout)

            # ✅ NEW: Log file save with details
            if filepath.exists():
                file_size = filepath.stat().st_size
                logger.info(f"   ✅ [{datetime.now().strftime('%H:%M:%S')}] Segment {segment_index} saved!")
                logger.debug(f"   📁 File: {filepath.name}")
                logger.info(f"   📊 Size: {file_size / 1024:.1f} KB")

            # ✅ IMPROVED: Use extracted duplicate detection method with scroll position check
            if skip_duplicates:
                is_duplicate, current_hash = self._check_and_handle_duplicate(
                    filepath=filepath,
                    previous_hash=previous_hash,
                    segment_index=segment_index,
                    estimated_segments=estimated_segments,
                    current_scroll_position=int(final_scroll_check['scrollTop']),  # ✅ NEW: Pass current scroll position
                    previous_scroll_position=previous_scroll_position,  # ✅ NEW: Pass previous scroll position
                    scroll_position_tolerance=10  # ✅ NEW: 10px tolerance
                )

                if is_duplicate:
                    # Update hash and scroll position, then skip to next segment
                    previous_hash = current_hash
                    previous_scroll_position = int(
                        final_scroll_check['scrollTop'])  # ✅ NEW: Update previous scroll position
                    position += scroll_step
                    segment_index += 1
                    continue

                # Update hash and scroll position for next comparison
                previous_hash = current_hash
                previous_scroll_position = int(
                    final_scroll_check['scrollTop'])  # ✅ NEW: Update previous scroll position

            screenshot_paths.append(str(filepath))
            logger.info(f"✅ Segment {segment_index}/{estimated_segments} captured: {filename}")

            # Move to next position
            position += scroll_step
            segment_index += 1

            # ✅ FIX: Break after capturing the last segment
            if is_last_segment:
                break

        # ✅ FIX: Add form screenshots from click actions to the main screenshot list
        # These screenshots were captured BEFORE the final table screenshot
        # Insert them at the beginning so they appear first in the Word document
        if form_screenshots_from_actions:
            screenshot_paths = form_screenshots_from_actions + screenshot_paths
            logger.info(f"   📸 Added {len(form_screenshots_from_actions)} form screenshot(s) to final list")

        # ✅ NEW: Summary log with timestamp and file locations
        from datetime import datetime
        logger.debug(f"\n{'=' * 60}")
        logger.debug(f"🎉 [{datetime.now().strftime('%H:%M:%S')}] Segmented capture complete!")
        logger.info(f"   📊 Total segments: {len(screenshot_paths)}")
        if form_screenshots_from_actions:
            logger.info(f"   📸 Including {len(form_screenshots_from_actions)} form screenshot(s)")
        logger.debug(f"   📁 Output directory: {self.output_dir}")
        logger.debug(f"   🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.debug(f"{'=' * 60}\n")
        return screenshot_paths

    async def _expand_all_dropdowns(self, page: Page, max_depth: int = 5, debug: bool = False):
        """
        🎯 AUTO DROPDOWN EXPANSION

        Automatically detect and expand all collapsed/collapsible sections on the page.
        This ensures screenshots capture the full content, not just collapsed headers.

        Detection Patterns:
        1. Arrow icons: icon-caret-right, chevron-right → icon-caret-down, chevron-down
        2. Plus/Minus: icon-plus, fa-plus → icon-minus, fa-minus
        3. ARIA states: aria-expanded="false" → aria-expanded="true"
        4. Ant Design: .ant-collapse-item (not active) → .ant-collapse-item-active
        5. Common classes: .collapsed, .expand, .accordion
        6. Info icons: Elements with info icons that might be expandable
        7. Clickable headers: Headers with counts like "Services (3)"

        Args:
            page: Playwright page object
            max_depth: Maximum number of expansion iterations (default: 5)
                      Some dropdowns reveal nested dropdowns, so we iterate
            debug: If True, log detailed information about detected elements
        """
        logger.debug("\n🔽 Auto-expanding collapsed sections...")
        logger.debug("   🔍 Detection patterns:")
        logger.debug("      1. Arrow icons: .icon-caret-right, .chevron-right, etc.")
        logger.debug("      2. Ant Design: .ant-collapse-item (not active)")
        logger.debug(f"   🔄 Max depth iterations: {max_depth}")

        # ✅ NEW: Wait for dropdown elements to appear before detection
        logger.debug("   ⏳ Waiting for dropdown elements to render...")
        try:
            # Wait for at least one common dropdown indicator to appear
            await page.wait_for_selector(
                '.icon-caret-right, .icon-caret-down, .ant-collapse-item, [aria-expanded], .chevron-right, .caret-right',
                timeout=10000,
                state='attached'
            )
            logger.info("   ✅ Dropdown elements detected on page!")
            # Additional wait for all dropdowns to fully render
            await asyncio.sleep(2.0)
        except Exception as e:
            logger.warning(f"   ⚠️  No dropdown elements found after 10s: {str(e)[:100]}")
            logger.debug("   ℹ️  Page may not have collapsible sections, continuing anyway...")
            # Don't return - still try detection in case elements appear later

        if debug:
            # Log all potential collapsible elements for debugging
            potential_elements = await page.evaluate("""() => {
                const elements = [];

                // Find elements with down arrows
                document.querySelectorAll('*').forEach(el => {
                    const classList = el.className || '';
                    const text = el.textContent?.trim() || '';

                    if (classList.includes('caret') ||
                        classList.includes('chevron') ||
                        classList.includes('arrow') ||
                        text.match(/▼|▲|►|▶|◀|◄/)) {
                        elements.push({
                            tag: el.tagName,
                            class: classList,
                            text: text.substring(0, 50),
                            ariaExpanded: el.getAttribute('aria-expanded')
                        });
                    }
                });

                return elements;
            }""")
            logger.debug(f"   🔍 DEBUG: Found {len(potential_elements)} potential collapsible elements:")
            for elem in potential_elements[:10]:  # Show first 10
                logger.debug(f"      - {elem}")

        total_expanded = 0

        for depth in range(max_depth):
            # Find all collapsed elements using comprehensive selectors
            result = await page.evaluate("""() => {
                let count = 0;
                const detectionLog = [];

                // ========================================
                // Helper: Check if element or parent is already expanded
                // ========================================
                function isAlreadyExpanded(element) {
                    // Check element and up to 3 parents
                    let current = element;
                    for (let i = 0; i < 4; i++) {
                        if (!current) break;

                        // Check ARIA state (most reliable)
                        if (current.getAttribute('aria-expanded') === 'true') {
                            return true;
                        }

                        // Check common "open" classes
                        const classList = current.className || '';
                        if (classList.includes('active') ||
                            classList.includes('open') ||
                            classList.includes('show') ||
                            classList.includes('expanded')) {
                            return true;
                        }

                        // NOTE: We DON'T check for down arrows here because some apps
                        // use down arrows to indicate collapsed state (opposite convention)
                        // We rely on aria-expanded and class names instead

                        current = current.parentElement;
                    }
                    return false;
                }

                // ========================================
                // Pattern 1: Arrow Icons (Caret/Chevron)
                // ========================================
                // Only target RIGHT arrows (collapsed state)
                const arrowSelectors = [
                    '.icon-caret-right',
                    '.caret-right',
                    '.fa-caret-right',
                    '.icon-chevron-right',
                    '.chevron-right',
                    '.fa-chevron-right'
                ];

                arrowSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    detectionLog.push({
                        selector: selector,
                        found: elements.length,
                        clicked: 0,
                        skipped: 0
                    });

                    const logEntry = detectionLog[detectionLog.length - 1];

                    elements.forEach(el => {
                        // Skip if already expanded
                        if (isAlreadyExpanded(el)) {
                            logEntry.skipped++;
                            return;
                        }

                        // Find the clickable parent (usually 1-3 levels up)
                        let clickTarget = el;
                        for (let i = 0; i < 3; i++) {
                            if (clickTarget.parentElement) {
                                clickTarget = clickTarget.parentElement;
                                // Check if this element looks clickable
                                const style = window.getComputedStyle(clickTarget);
                                if (style.cursor === 'pointer' ||
                                    clickTarget.onclick ||
                                    clickTarget.getAttribute('role') === 'button' ||
                                    clickTarget.classList.contains('collapse') ||
                                    clickTarget.classList.contains('accordion')) {
                                    break;
                                }
                            }
                        }

                        // Click to expand
                        try {
                            clickTarget.click();
                            count++;
                            logEntry.clicked++;
                        } catch (e) {
                            // Ignore click errors
                        }
                    });
                });

                // ========================================
                // Pattern 2: Plus/Minus Icons - DISABLED
                // ========================================
                // NOTE: This pattern could click on plus icons in various places
                // which might not be content dropdowns.
                // Pattern 1 (icon-caret-right) and Pattern 4 (ant-collapse-item) are sufficient.

                // ========================================
                // Pattern 2.5: Info Icons (ⓘ) - DISABLED
                // ========================================
                // NOTE: This pattern could click on info icons in various places
                // including side menu items, which could cause unwanted navigation.
                // Pattern 1 (icon-caret-right) and Pattern 4 (ant-collapse-item) are sufficient.

                // ========================================
                // Pattern 3: ARIA Expanded State - DISABLED
                // ========================================
                // NOTE: This pattern was clicking on ALL elements with aria-expanded="false"
                // including side menu items (.ant-menu-submenu-title) which are navigation,
                // not content dropdowns. This caused the side menu to expand and then click
                // on submenu items like "Tekion Pay", causing unwanted navigation.
                // Pattern 1 (icon-caret-right) and Pattern 4 (ant-collapse-item) are sufficient.

                // ========================================
                // Pattern 4: Ant Design Collapse
                // ========================================
                // Only targets inactive collapse items
                const antCollapse = document.querySelectorAll('.ant-collapse-item:not(.ant-collapse-item-active)');
                detectionLog.push({
                    selector: '.ant-collapse-item:not(.ant-collapse-item-active)',
                    found: antCollapse.length,
                    clicked: 0,
                    skipped: 0
                });

                const antLogEntry = detectionLog[detectionLog.length - 1];

                antCollapse.forEach(el => {
                    const header = el.querySelector('.ant-collapse-header');
                    if (header) {
                        try {
                            header.click();
                            count++;
                            antLogEntry.clicked++;
                        } catch (e) {
                            // Ignore
                        }
                    }
                });

                // ========================================
                // Pattern 4.5: Ant Design Menu Submenu - DISABLED
                // ========================================
                // NOTE: We DON'T expand side menu items (Variable Operations, Fixed Operations, etc.)
                // because they're navigation menus, not content dropdowns.
                // Only expand content panels (ant-collapse-item) that contain actual data.

                // ========================================
                // Pattern 5: Common Collapse Classes - DISABLED
                // ========================================
                // NOTE: This pattern could click on various collapsed elements
                // which might not be content dropdowns.
                // Pattern 1 (icon-caret-right) and Pattern 4 (ant-collapse-item) are sufficient.

                // ========================================
                // Pattern 6: Clickable Headers with Counts - DISABLED
                // ========================================
                // NOTE: This pattern could click on side menu items like "Services (3)"
                // which are navigation items, not content dropdowns.
                // Pattern 1 (icon-caret-right) is sufficient for content panels.

                // ========================================
                // Pattern 7: Unicode Arrow Symbols - DISABLED
                // ========================================
                // NOTE: This pattern could click on various UI elements with arrows
                // that aren't necessarily content dropdowns.
                // Pattern 1 (icon-caret-right) is sufficient for content panels.

                // ========================================
                // Pattern 8: Aggressive Pattern - DISABLED
                // ========================================
                // NOTE: This pattern was too aggressive and was clicking on side menu items
                // (Variable Operations, Fixed Operations, Payment Receipts) which are navigation,
                // not content dropdowns. Pattern 1 (icon-caret-right) is sufficient for expanding
                // content collapse panels.

                return { count, detectionLog };
            }""")

            expanded_count = result['count']
            detection_log = result['detectionLog']

            # Print detailed detection log
            if depth == 0:  # Only print on first iteration to avoid spam
                logger.info(f"\n   📊 Detection Results (Depth {depth + 1}):")
                for log_entry in detection_log:
                    if log_entry['found'] > 0:
                        logger.debug(f"      🔍 {log_entry['selector']}")
                        logger.debug(
                            f"         Found: {log_entry['found']} | Clicked: {log_entry['clicked']} | Skipped: {log_entry['skipped']}")
                    else:
                        logger.error(f"      ❌ {log_entry['selector']}: No elements found")

            if expanded_count > 0:
                total_expanded += expanded_count
                logger.debug(f"   🔽 Depth {depth + 1}: Expanded {expanded_count} sections")
                # Wait for animations and nested content to load
                await asyncio.sleep(0.5)
            else:
                # ✅ NEW: Retry logic if no dropdowns found on first attempt
                if depth == 0 and total_expanded == 0:
                    logger.debug(f"   ⏳ No dropdowns found on first try - page may still be loading")
                    logger.debug(f"   🔄 Waiting 3 seconds and retrying detection...")
                    await asyncio.sleep(3.0)
                    # Continue to next iteration (will retry detection)
                    continue
                else:
                    # No more collapsed sections found
                    logger.debug(f"   ⏹️  Depth {depth + 1}: No more collapsed sections found")
                    break

        if total_expanded > 0:
            logger.info(f"   ✅ Total expanded: {total_expanded} sections")
            # Final wait for all content to settle
            await asyncio.sleep(1.0)
        else:
            logger.debug(f"   ℹ️  No collapsed sections detected after all attempts")

        # 🔍 DEBUG: Log current URL after dropdown detection
        current_url = page.url
        logger.info(f"   🔗 Current URL after dropdown detection: {current_url}")

    async def _scroll_all_nested_elements(self, page: Page):
        """
        🔄 SCROLL ALL NESTED SCROLLABLE ELEMENTS

        Scroll all nested scrollable elements (tables, divs) to their bottom
        to reveal all hidden content before capturing screenshots.

        This handles cases like:
        - Tables with internal scrollbars inside expanded dropdowns
        - Nested divs with overflow:auto
        - Multiple scrollable sections on the same page

        Args:
            page: Playwright page object
        """
        logger.debug("   🔄 Scrolling all nested scrollable elements...")

        # Find and scroll ALL scrollable elements
        scroll_result = await page.evaluate("""() => {
            const scrolledElements = [];

            // Find all elements with overflow
            const allElements = document.querySelectorAll('*');

            for (const el of allElements) {
                const style = window.getComputedStyle(el);
                const hasOverflow = (
                    style.overflow === 'auto' ||
                    style.overflow === 'scroll' ||
                    style.overflowY === 'auto' ||
                    style.overflowY === 'scroll'
                );

                const isVisible = (
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    el.offsetParent !== null
                );

                const hasScrollableContent = el.scrollHeight > el.clientHeight;
                const scrollPotential = el.scrollHeight - el.clientHeight;

                // Skip elements that are likely navigation/menus
                const className = (typeof el.className === 'string' ? el.className : el.className?.toString() || '');
                const isNavigation = (
                    className.includes('menu') ||
                    className.includes('nav') ||
                    className.includes('sidebar') ||
                    className.includes('header') ||
                    className.includes('footer')
                );

                // Only scroll elements with significant content (>50px) and not navigation
                if (hasOverflow && hasScrollableContent && isVisible && scrollPotential > 50 && !isNavigation) {
                    // Scroll to bottom
                    const beforeScroll = el.scrollTop;
                    el.scrollTop = el.scrollHeight;
                    const afterScroll = el.scrollTop;

                    // Only record if we actually scrolled
                    if (afterScroll > beforeScroll) {
                        scrolledElements.push({
                            tag: el.tagName,
                            className: (typeof el.className === 'string' ? el.className.substring(0, 50) : String(el.className || '').substring(0, 50)),
                            id: el.id,
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight,
                            scrollPotential: scrollPotential,
                            scrolledFrom: beforeScroll,
                            scrolledTo: afterScroll,
                            actualScrolled: afterScroll - beforeScroll
                        });
                    }
                }
            }

            return scrolledElements;
        }""")

        if len(scroll_result) > 0:
            logger.info(f"   ✅ Scrolled {len(scroll_result)} nested elements to bottom:")
            for elem in scroll_result[:10]:  # Show first 10
                class_name = elem['className'][:30] if elem['className'] else '(no class)'
                logger.debug(
                    f"      - <{elem['tag']}> class='{class_name}' ({elem['actualScrolled']}px scrolled, {elem['scrollHeight']}px total)")

            # Wait for content to load after scrolling
            await asyncio.sleep(1.0)
            logger.info("   ✅ Nested elements scrolled, content loaded")
        else:
            logger.debug("   ℹ️  No nested scrollable elements found")

    async def _click_elements_by_text(self, page: Page, text_list: list):
        """
        Click elements that contain specific text

        Args:
            page: Playwright page object
            text_list: List of text strings to search for and click
        """
        if not text_list:
            return

        logger.debug(f"🖱️  Clicking elements with text: {text_list}")

        for text in text_list:
            logger.debug(f"   🔍 Searching for: '{text}'")

            # Try to find and click the element
            clicked = await page.evaluate("""(searchText) => {
                // Search for elements containing the text
                const allElements = document.querySelectorAll('*');
                let found = false;

                for (const el of allElements) {
                    // Check if element's text content matches (exact or contains)
                    const textContent = el.textContent?.trim() || '';

                    if (textContent === searchText || textContent.includes(searchText)) {
                        // Make sure it's a visible element (not a parent container)
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            // Try to find the clickable parent (row, cell, button, etc.)
                            let clickTarget = el;

                            // Walk up the tree to find a clickable element
                            for (let i = 0; i < 5; i++) {
                                if (!clickTarget) break;

                                const style = window.getComputedStyle(clickTarget);
                                const tagName = clickTarget.tagName.toLowerCase();

                                    // Check if this element is clickable
                                    if (style.cursor === 'pointer' ||
                                        clickTarget.onclick ||
                                        clickTarget.getAttribute('role') === 'button' ||
                                        clickTarget.getAttribute('role') === 'gridcell' ||
                                        clickTarget.getAttribute('role') === 'row' ||
                                        tagName === 'button' ||
                                        tagName === 'a' ||
                                        clickTarget.classList.contains('rt-tr') ||
                                        clickTarget.classList.contains('rt-td')) {

                                        try {
                                            // Scroll element into view (center) before clicking,
                                            // similar to scrollToCenter + click in Selenium BaseFunctions.
                                            if (typeof clickTarget.scrollIntoView === 'function') {
                                                clickTarget.scrollIntoView({
                                                    behavior: 'auto',
                                                    block: 'center',
                                                    inline: 'center'
                                                });
                                            }
                                            clickTarget.click();
                                            found = true;
                                            return {
                                                success: true,
                                                element: tagName,
                                                text: textContent.substring(0, 50)
                                            };
                                        } catch (e) {
                                            // Continue searching
                                        }
                                    }

                                clickTarget = clickTarget.parentElement;
                            }
                        }
                    }
                }

                return { success: false };
            }""", text)

            if clicked.get('success'):
                logger.info(f"   ✅ Clicked: {clicked.get('element')} - {clicked.get('text')}")
                # Wait for any modal/dialog to appear
                await asyncio.sleep(1.0)
            else:
                logger.warning(f"   ⚠️  Element not found: '{text}'")

    async def _capture_form_screenshots(
            self,
            page: Page,
            form_name: str,
            url: str,
            viewport_width: int,
            viewport_height: int,
            overlap_percent: int,
            scroll_delay_ms: int,
            max_segments: int,
            base_url: str = "",
            words_to_remove: str = "",
            non_scrollable_urls: str = ""  # ✅ FIX: Add non_scrollable_urls parameter
    ) -> list[str]:
        """
        📸 Capture screenshots of a single opened form

        Returns list of screenshot file paths
        """
        screenshot_paths = []

        # Stabilize and measure the form height
        logger.debug(f"      📐 Measuring form height...")

        # Find scrollable element and cache it
        scrollable_info = await page.evaluate("""() => {
            let maxScrollableHeight = 0;
            let bestElement = null;
            let bestSelector = 'window';

            const prioritySelectors = [
                '[class*="formContainer"]',
                '[class*="form-container"]',
                '[role="dialog"]',
                '[role="main"]',
                'main',
                '.main-content'
            ];

            for (const selector of prioritySelectors) {
                const elements = document.querySelectorAll(selector);
                for (const el of elements) {
                    const scrollHeight = el.scrollHeight;
                    const clientHeight = el.clientHeight;

                    if (scrollHeight > clientHeight && scrollHeight > maxScrollableHeight) {
                        maxScrollableHeight = scrollHeight;
                        bestElement = el;
                        bestSelector = selector;
                    }
                }
            }

            if (!bestElement) {
                return {
                    scrollHeight: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight),
                    clientHeight: window.innerHeight,
                    selector: 'window'
                };
            }

            window.__scrollableElement = bestElement;

            return {
                scrollHeight: bestElement.scrollHeight,
                clientHeight: bestElement.clientHeight,
                selector: bestSelector
            };
        }""")

        total_height = scrollable_info['scrollHeight']
        actual_viewport_height = scrollable_info['clientHeight']

        logger.info(f"      📏 Form height: {total_height}px (viewport: {actual_viewport_height}px)")

        # Calculate scroll step
        scroll_step = int(actual_viewport_height * (1 - overlap_percent / 100))
        if scroll_step <= 0:
            scroll_step = actual_viewport_height

        # ✅ NEW: Check if URL matches non-scrollable patterns
        import json
        non_scrollable_patterns = []
        logger.debug(f"      🔍 DEBUG: non_scrollable_urls parameter = '{non_scrollable_urls}'")
        if non_scrollable_urls:
            try:
                non_scrollable_patterns = json.loads(non_scrollable_urls)
                logger.debug(f"      🔍 DEBUG: Parsed patterns = {non_scrollable_patterns}")
            except Exception as e:
                logger.warning(f"      ⚠️  Failed to parse non_scrollable_urls: {e}")
                non_scrollable_patterns = []

        logger.debug(f"      🔍 DEBUG: Current URL = {url}")
        is_non_scrollable = any(
            pattern in url for pattern in non_scrollable_patterns
        ) if non_scrollable_patterns else False
        logger.debug(f"      🔍 DEBUG: is_non_scrollable = {is_non_scrollable}")

        if is_non_scrollable:
            estimated_segments = 1
            logger.debug(f"      🔒 URL matched non-scrollable list - forcing single segment")
        # ✅ FIX: Check if form fits in viewport (non-scrollable)
        elif total_height <= actual_viewport_height:
            estimated_segments = 1
            logger.debug(f"      ℹ️  Non-scrollable form (total: {total_height}px ≤ viewport: {actual_viewport_height}px)")
        else:
            # Calculate segments for scrollable forms
            import math
            estimated_segments = min(max_segments, math.ceil((total_height - actual_viewport_height) / scroll_step) + 1)

        logger.info(f"      📊 Capturing {estimated_segments} segments (scroll step: {scroll_step}px)")

        # Scroll to top first
        await page.evaluate("""() => {
            const bestElement = window.__scrollableElement;
            if (bestElement) {
                bestElement.scrollTop = 0;
            } else {
                window.scrollTo(0, 0);
            }
        }""")
        await asyncio.sleep(0.3)

        # Capture segments
        position = 0
        segment_index = 1

        while position < total_height and segment_index <= max_segments and segment_index <= estimated_segments:
            remaining_pixels = total_height - position
            is_last_segment = remaining_pixels > 0 and remaining_pixels < actual_viewport_height

            if is_last_segment:
                final_position = max(0, total_height - actual_viewport_height)
            else:
                final_position = position

            # Scroll to position
            await page.evaluate(f"""() => {{
                const bestElement = window.__scrollableElement;
                if (bestElement) {{
                    bestElement.scrollTop = {final_position};
                    bestElement.style.scrollBehavior = 'auto';
                }} else {{
                    window.scrollTo(0, {final_position});
                }}
            }}""")

            await asyncio.sleep(scroll_delay_ms / 1000.0)

            # Generate filename with form name
            # Format: domain_formname_001_timestamp.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace(":", "_")
            safe_form_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in form_name)

            if estimated_segments > 1:
                filename = f"{domain}_{safe_form_name}_{segment_index:03d}_{timestamp}.png"
            else:
                filename = f"{domain}_{safe_form_name}_{timestamp}.png"

            filepath = self.output_dir / filename

            # Take screenshot
            logger.info(
                f"      📸 [{datetime.now().strftime('%H:%M:%S')}] Capturing segment {segment_index}/{estimated_segments}...")

            try:
                await page.screenshot(path=str(filepath), full_page=False, timeout=30000)
                screenshot_paths.append(str(filepath))
                logger.info(f"      ✅ Segment {segment_index} saved!")
                logger.debug(f"      📁 File: {filename}")
            except Exception as e:
                logger.error(f"      ❌ Failed to capture segment {segment_index}: {e}")

            # Move to next segment
            if is_last_segment:
                break

            position += scroll_step
            segment_index += 1

        return screenshot_paths

    async def _click_active_forms(
            self,
            page: Page,
            form_name: str = "",
            status_required: str = "Active",
            scroll_opened: bool = True,
            close_after: bool = True,
            wait_after_click_ms: int = 2000,
            wait_after_scroll_ms: int = 1000,
            # NEW: Screenshot parameters
            capture_screenshots: bool = True,
            url: str = "",
            viewport_width: int = 1920,
            viewport_height: int = 1080,
            overlap_percent: int = 15,
            scroll_delay_ms: int = 500,
            max_segments: int = 50,
            base_url: str = "",
            words_to_remove: str = "",
            non_scrollable_urls: str = ""  # ✅ FIX: Add non_scrollable_urls parameter
    ) -> list[str]:
        """
        🎯 ADVANCED: Click all forms with specific name and status dynamically

        This method:
        1. Finds all rows in the table with matching form name
        2. Checks if each has the required status (e.g., "Active")
        3. Clicks each matching form
        4. Scrolls the opened page/modal
        5. Takes screenshots of the opened form (NEW!)
        6. Navigates back/closes the form
        7. Continues to next matching form

        Args:
            page: Playwright page object
            form_name: Name of the form to look for (e.g., "MPI")
            status_required: Required status (e.g., "Active")
            scroll_opened: Whether to scroll the opened page/modal
            close_after: Whether to close/go back after scrolling
            wait_after_click_ms: Wait time after clicking (ms)
            wait_after_scroll_ms: Wait time after scrolling (ms)
            capture_screenshots: Whether to capture screenshots of each form (NEW!)
            url: Current page URL (for screenshot naming)
            viewport_width/height: Viewport dimensions
            overlap_percent: Screenshot overlap percentage
            scroll_delay_ms: Delay between scroll and screenshot
            max_segments: Maximum number of segments per form
            base_url: Base URL for filename generation
            words_to_remove: Words to remove from filename

        Returns:
            List of screenshot file paths captured from all forms
        """
        all_form_screenshots = []  # ✅ NEW: Collect all form screenshots
        logger.info(f"🎯 Finding all '{form_name}' forms with status '{status_required}'...")

        # ✅ NEW: Wait for React table to render before detection
        logger.debug("   ⏳ Waiting for form table to load...")
        try:
            await page.wait_for_selector('[role="row"]', timeout=10000, state='attached')
            logger.info("   ✅ Form table detected!")
            # Additional wait for all rows to render
            await asyncio.sleep(2.0)
        except Exception as e:
            logger.warning(f"   ⚠️  No table rows found after 10s: {str(e)[:100]}")
            logger.debug(f"   ℹ️  Continuing anyway...")

        # Find all matching forms
        forms_info = await page.evaluate("""({formName, statusRequired}) => {
            const results = [];

            // Find all table rows (React Table structure)
            const rows = document.querySelectorAll('[role="row"]');

            for (const row of rows) {
                // Find cells in this row
                const cells = row.querySelectorAll('[role="gridcell"]');

                if (cells.length < 2) continue;

                // First cell should contain form name
                const formTitleCell = cells[0];
                const formTitleText = formTitleCell.textContent?.trim() || '';

                // Check if this row has the form we're looking for
                if (formTitleText === formName || formTitleText.includes(formName)) {
                    // Second or third cell should contain status
                    let statusText = '';
                    let hasActiveIndicator = false;

                    for (const cell of cells) {
                        const statusLabel = cell.querySelector('.root_label_label__fPnKtiGtmC');
                        if (statusLabel) {
                            statusText = statusLabel.textContent?.trim() || '';
                        }

                        // Check for green status indicator
                        const greenIndicator = cell.querySelector('.root_statusRenderer_green__nYQ6xRCozZ');
                        if (greenIndicator) {
                            hasActiveIndicator = true;
                        }
                    }

                    // Check if status matches
                    const statusMatches = (
                        statusText === statusRequired ||
                        (statusRequired === 'Active' && hasActiveIndicator)
                    );

                    if (statusMatches) {
                        results.push({
                            formName: formTitleText,
                            status: statusText || 'Active',
                            hasActiveIndicator: hasActiveIndicator,
                            rowIndex: results.length
                        });
                    }
                }
            }

            return results;
        }""", {"formName": form_name, "statusRequired": status_required})

        # ✅ NEW: Retry logic if no forms found on first attempt
        if not forms_info or len(forms_info) == 0:
            logger.debug(f"   ⏳ No forms found on first try - table may still be loading")
            logger.debug(f"   🔄 Waiting 3 seconds and retrying detection...")
            await asyncio.sleep(3.0)

            # Retry detection
            forms_info = await page.evaluate("""({formName, statusRequired}) => {
                const results = [];

                // Find all table rows (React Table structure)
                const rows = document.querySelectorAll('[role="row"]');

                for (const row of rows) {
                    // Find cells in this row
                    const cells = row.querySelectorAll('[role="gridcell"]');

                    if (cells.length < 2) continue;

                    // First cell should contain form name
                    const formTitleCell = cells[0];
                    const formTitleText = formTitleCell.textContent?.trim() || '';

                    // Check if this row has the form we're looking for
                    if (formTitleText === formName || formTitleText.includes(formName)) {
                        // Second or third cell should contain status
                        let statusText = '';
                        let hasActiveIndicator = false;

                        for (const cell of cells) {
                            const statusLabel = cell.querySelector('.root_label_label__fPnKtiGtmC');
                            if (statusLabel) {
                                statusText = statusLabel.textContent?.trim() || '';
                            }

                            // Check for green status indicator
                            const greenIndicator = cell.querySelector('.root_statusRenderer_green__nYQ6xRCozZ');
                            if (greenIndicator) {
                                hasActiveIndicator = true;
                            }
                        }

                        // Check if status matches
                        const statusMatches = (
                            statusText === statusRequired ||
                            (statusRequired === 'Active' && hasActiveIndicator)
                        );

                        if (statusMatches) {
                            results.push({
                                formName: formTitleText,
                                status: statusText || 'Active',
                                hasActiveIndicator: hasActiveIndicator,
                                rowIndex: results.length
                            });
                        }
                    }
                }

                return results;
            }""", {"formName": form_name, "statusRequired": status_required})

            if not forms_info or len(forms_info) == 0:
                logger.debug(f"   ℹ️  No '{form_name}' forms found with status '{status_required}' after retry")
                return all_form_screenshots  # ✅ FIX: Return empty list instead of None

        logger.info(f"   ✅ Found {len(forms_info)} matching form(s):")
        for i, form in enumerate(forms_info, 1):
            logger.debug(f"      {i}. {form['formName']} - {form['status']}")

        # Process each form
        for i, form in enumerate(forms_info, 1):
            logger.debug(f"\n   🔄 Processing form {i}/{len(forms_info)}: {form['formName']}")

            # ✅ NEW: Send WebSocket notification for form processing
            # ✅ FIXED (Bug #11): Use helper method to properly track background task
            self._send_websocket_message_background({
                "type": "form_processing",
                "form_index": i,
                "total_forms": len(forms_info),
                "form_name": form['formName'],
                "status": "processing"
            })
            logger.info(f"      📡 WebSocket notification sent: Form processing")

            # Click the form row by exact name match (not by index, since DOM may change after navigation)
            clicked = await page.evaluate("""({formName}) => {
                const rows = document.querySelectorAll('[role="row"]');

                for (const row of rows) {
                    const cells = row.querySelectorAll('[role="gridcell"]');
                    if (cells.length < 2) continue;

                    const formTitleCell = cells[0];
                    const formTitleText = formTitleCell.textContent?.trim() || '';

                    // Match by exact form name
                    if (formTitleText === formName) {
                        // Click the row
                        try {
                            row.click();
                            return { success: true, formName: formTitleText };
                        } catch (e) {
                            // Try clicking the first cell instead
                            try {
                                formTitleCell.click();
                                return { success: true, formName: formTitleText };
                            } catch (e2) {
                                return { success: false, error: e2.message };
                            }
                        }
                    }
                }

                return { success: false, error: 'Row not found' };
            }""", {"formName": form['formName']})

            if not clicked.get('success'):
                logger.warning(f"      ⚠️  Failed to click: {clicked.get('error', 'Unknown error')}")
                continue

            logger.info(f"      ✅ Clicked: {clicked.get('formName')}")

            # Wait for page/modal to load
            await asyncio.sleep(wait_after_click_ms / 1000)

            # Scroll the opened page/modal if enabled
            if scroll_opened:
                logger.debug(f"      📜 Scrolling opened form...")
                await self._scroll_all_nested_elements(page)
                await asyncio.sleep(wait_after_scroll_ms / 1000)

            # Capture screenshots if enabled
            if capture_screenshots:
                logger.info(f"      📸 Capturing screenshots of form...")
                try:
                    screenshots = await self._capture_form_screenshots(
                        page=page,
                        form_name=form['formName'],
                        url=url,
                        viewport_width=viewport_width,
                        viewport_height=viewport_height,
                        overlap_percent=overlap_percent,
                        scroll_delay_ms=scroll_delay_ms,
                        max_segments=max_segments,
                        base_url=base_url,
                        words_to_remove=words_to_remove,
                        non_scrollable_urls=non_scrollable_urls  # ✅ FIX: Pass non_scrollable_urls parameter
                    )
                    all_form_screenshots.extend(screenshots)  # ✅ FIX: Add form screenshots to collection
                    logger.info(f"      ✅ Captured {len(screenshots)} screenshot(s) for {form['formName']}")
                except Exception as e:
                    logger.error(f"      ❌ Failed to capture screenshots: {e}")

            # Navigate back/close if enabled
            if close_after:
                logger.debug(f"      ⬅️  Navigating back...")

                # Try multiple methods to go back
                back_success = await page.evaluate("""() => {
                    // Method 1: Try specific known back button first
                    const specificBackButton = document.querySelector('div[aria-label="icon-left-arrow-thin"]');
                    if (specificBackButton) {
                        try {
                            specificBackButton.click();
                            return { method: 'specific_back_button', success: true, ariaLabel: 'icon-left-arrow-thin' };
                        } catch (e) {
                            // Continue to generic search
                        }
                    }

                    // Method 2: Look for close/back/arrow buttons (generic)
                    const closeButtons = [
                        ...document.querySelectorAll('[aria-label*="close" i]'),
                        ...document.querySelectorAll('[aria-label*="back" i]'),
                        ...document.querySelectorAll('[aria-label*="arrow" i]'),
                        ...document.querySelectorAll('[aria-label*="left" i]'),
                        ...document.querySelectorAll('button:has(svg)'),
                        ...document.querySelectorAll('.close'),
                        ...document.querySelectorAll('[class*="close" i]'),
                        ...document.querySelectorAll('[class*="back" i]'),
                        ...document.querySelectorAll('[class*="arrow" i]'),
                        ...document.querySelectorAll('[class*="left-arrow" i]'),
                        ...document.querySelectorAll('[role="button"]')
                    ];

                    for (const btn of closeButtons) {
                        const text = btn.textContent?.toLowerCase() || '';
                        const ariaLabel = btn.getAttribute('aria-label')?.toLowerCase() || '';
                        const className = (typeof btn.className === 'string' ? btn.className.toLowerCase() : btn.className?.toString().toLowerCase() || '');

                        // Check if this looks like a close/back/arrow button
                        const isCloseButton = (
                            text.includes('close') || text.includes('cancel') || text.includes('back') ||
                            ariaLabel.includes('close') || ariaLabel.includes('back') ||
                            ariaLabel.includes('arrow') || ariaLabel.includes('left') ||
                            className.includes('left-arrow') || className.includes('back-arrow') ||
                            className.includes('arrow-thin') ||
                            btn.innerHTML.includes('svg')
                        );

                        if (isCloseButton) {
                            try {
                                btn.click();
                                return { method: 'close_button', success: true, ariaLabel: ariaLabel };
                            } catch (e) {
                                continue;
                            }
                        }
                    }

                    return { method: 'none', success: false };
                }""")

                if not back_success.get('success'):
                    # Try browser back navigation
                    try:
                        await page.go_back(wait_until='domcontentloaded', timeout=5000)
                        logger.info(f"      ✅ Navigated back (browser back)")
                    except Exception as e:  # ✅ FIXED: Specific exception instead of bare except
                        logger.warning(f"      ⚠️  Could not navigate back automatically: {e}")
                else:
                    aria_label = back_success.get('ariaLabel', 'unknown')
                    logger.info(f"      ✅ Clicked back button (aria-label: {aria_label})")

                # Wait for page to settle and table to reappear
                await asyncio.sleep(1.0)

                # Wait for the table to be visible again (important for next form click)
                try:
                    await page.wait_for_selector('[role="row"]', state='visible', timeout=5000)
                except Exception:  # ✅ FIXED: Specific exception instead of bare except
                    pass  # Continue even if table doesn't appear (timeout or element not found)

        logger.info(f"\n   ✅ Processed {len(forms_info)} form(s) successfully")
        return all_form_screenshots  # ✅ FIX: Return all collected form screenshots

    async def _wait_for_lazy_load(self, page: Page, max_wait_ms: int = None):
        """
        Wait for lazy-loaded content to appear

        ✅ OPTIMIZATION: Only counts DOM nodes in scrollable container instead of entire page
        for ~40% performance improvement
        """
        if max_wait_ms is None:
            max_wait_ms = self.CDP_LAZY_LOAD_MAX_MS

        start_time = asyncio.get_event_loop().time()
        previous_count = 0
        stable_count = 0

        while (asyncio.get_event_loop().time() - start_time) * 1000 < max_wait_ms:
            # ✅ OPTIMIZATION: Count DOM nodes only in scrollable container (faster than entire page)
            current_count = await page.evaluate("""() => {
                const container = window.__scrollableElement || document.body;
                return container.querySelectorAll('*').length;
            }""")

            if current_count == previous_count:
                stable_count += 1
                if stable_count >= self.CDP_LAZY_LOAD_STABLE_CHECKS:
                    break
            else:
                stable_count = 0

            previous_count = current_count
            await asyncio.sleep(self.CDP_LAZY_LOAD_CHECK_INTERVAL_MS / 1000)

    def _get_image_hash(self, filepath: Path) -> str:
        """
        Calculate perceptual hash of image with caching

        ✅ OPTIMIZATION: Caches hashes in memory to avoid recomputing
        for duplicate detection. Provides ~50% speedup for duplicate checks.

        ✅ FIXED: Implements LRU eviction when cache exceeds MAX_HASH_CACHE_SIZE
        to prevent unbounded memory growth.
        """
        # Check cache first
        filepath_str = str(filepath)
        if filepath_str in self._hash_cache:
            # ✅ FIXED: Move to end (mark as recently used in LRU cache)
            self._hash_cache.move_to_end(filepath_str)
            return self._hash_cache[filepath_str]

        # Compute hash if not cached
        try:
            img = Image.open(filepath)
            hash_val = str(imagehash.average_hash(img))

            # ✅ FIXED: Implement LRU eviction before adding new entry
            if len(self._hash_cache) >= self.MAX_HASH_CACHE_SIZE:
                # Remove oldest entry (first item in OrderedDict)
                oldest_key = next(iter(self._hash_cache))
                self._hash_cache.pop(oldest_key)
                logger.debug(f"   🗑️  Hash cache full - evicted oldest entry (size: {self.MAX_HASH_CACHE_SIZE})")

            # Store in cache for future use (both memory and disk)
            self._hash_cache[filepath_str] = hash_val
            self._save_hash_cache()  # ⚡ OPTIMIZATION: Persist to disk
            return hash_val
        except Exception:
            return ""

    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes (0.0 to 1.0)"""
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 0.0

        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / len(hash1)

    def _check_and_handle_duplicate(
            self,
            filepath: Path,
            previous_hash: Optional[str],
            segment_index: int,
            estimated_segments: int,
            current_scroll_position: Optional[int] = None,
            previous_scroll_position: Optional[int] = None,
            scroll_position_tolerance: int = 10
    ) -> Tuple[bool, str]:
        """
        Check if segment is duplicate and handle accordingly

        ✅ IMPROVED: Now checks BOTH scroll position AND image similarity

        A segment is only considered a duplicate if BOTH conditions are true:
        1. Scroll position is the same (within tolerance)
        2. Image similarity is above threshold (95%)

        ✅ OPTIMIZATION: Extracted duplicate detection logic to avoid code duplication

        Args:
            filepath: Path to the screenshot file
            previous_hash: Hash of the previous segment (or None for first segment)
            segment_index: Current segment index
            estimated_segments: Total estimated segments
            current_scroll_position: Current scroll position in pixels (optional)
            previous_scroll_position: Previous scroll position in pixels (optional)
            scroll_position_tolerance: Tolerance for scroll position comparison (default: 10px)

        Returns:
            Tuple of (is_duplicate, current_hash)
            - is_duplicate: True if segment was a duplicate and was deleted
            - current_hash: Hash of the current segment
        """
        current_hash = self._get_image_hash(filepath)

        if previous_hash:
            # ✅ NEW: Check scroll position first (if provided)
            if current_scroll_position is not None and previous_scroll_position is not None:
                scroll_diff = abs(current_scroll_position - previous_scroll_position)

                # If scroll positions are significantly different, NOT a duplicate
                # (even if images look similar due to fixed headers/sidebars)
                if scroll_diff > scroll_position_tolerance:
                    logger.info(f"   ✅ Segment {segment_index} kept (different scroll position: {scroll_diff}px difference)")
                    return False, current_hash

                # Scroll positions are same, now check image similarity
                similarity = self._hash_similarity(previous_hash, current_hash)

                if similarity > self.DUPLICATE_SIMILARITY_THRESHOLD:
                    logger.debug(
                        f"⏭️  Segment {segment_index} skipped (duplicate: same scroll position + {similarity:.1%} similar)")
                    os.remove(filepath)  # Delete duplicate
                    return True, current_hash
            else:
                # ✅ FALLBACK: Old behavior (image similarity only) if scroll positions not provided
                similarity = self._hash_similarity(previous_hash, current_hash)

                if similarity > self.DUPLICATE_SIMILARITY_THRESHOLD:
                    logger.debug(f"⏭️  Segment {segment_index} skipped (duplicate, {similarity:.1%} similar)")
                    os.remove(filepath)  # Delete duplicate
                    return True, current_hash

        return False, current_hash

    def _to_pascal_case(self, text: str) -> str:
        """
        Convert text to PascalCase

        Examples:
        - "autoPostingSettings" -> "AutoPostingSettings"
        - "auto-posting-settings" -> "AutoPostingSettings"
        - "auto_posting_settings" -> "AutoPostingSettings"
        - "_private" -> "Private" (removes leading symbols)
        - "-config" -> "Config" (removes leading symbols)
        """
        # Split by common separators (-, _, space, camelCase boundaries)
        import re

        # First, handle camelCase by inserting space before capitals
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Split by separators (-, _, space)
        words = re.split(r'[-_\s]+', text)

        # Capitalize first letter of each word, filter out empty strings
        pascal_words = [word.capitalize() for word in words if word]

        result = ''.join(pascal_words)

        # Safety: Remove any leading non-alphanumeric characters
        # This ensures filenames never start with symbols like _, -, etc.
        result = re.sub(r'^[^a-zA-Z0-9]+', '', result)

        # If result is empty after cleanup, use default
        if not result:
            result = "Unnamed"

        return result

    def _generate_filename(self, url: str, base_url: str, words_to_remove: str, segment_index: int,
                           total_segments: int) -> str:
        """
        Generate filename based on base URL logic with PascalCase naming

        Logic:
        - If base_url provided: subtract base_url from url, convert path to PascalCase filename
        - Remove specified words from path before conversion
        - Single segment: Module_Feature.png
        - Multiple segments: Module_Feature_001.png, Module_Feature_002.png, etc.
        - If no base_url: use domain + timestamp (old behavior)
        - Hash fragments (#): Removed by default, but preserved if '#' is in word transformations

        Examples:
        - base_url="https://example.com/", url="https://example.com/accounting/autoPostingSettings", segments=1
          -> "Accounting_AutoPostingSettings.png"
        - base_url="https://example.com/", url="https://example.com/dse-v2/scheduling/general", words_to_remove="dse-v2", segments=1
          -> "Scheduling_General.png"
        - base_url="https://example.com/", url="https://example.com/page#section", words_to_remove='[{"word":"#","replacement":" ","type":"space"}]'
          -> "Page_Section.png" (hash preserved and transformed)
        """
        if base_url and url.startswith(base_url):
            # Subtract base URL from full URL
            path = url[len(base_url):]

            # Remove leading/trailing slashes
            path = path.strip('/')

            # ✅ NEW: Check if '#' is in word transformations - if so, preserve hash fragments
            # This allows users to opt-in to preserving hash fragments by adding '#' transformation
            preserve_hash = False
            if words_to_remove:
                import json
                try:
                    parsed = json.loads(words_to_remove)
                    if isinstance(parsed, list):
                        # Check if any transformation targets '#'
                        preserve_hash = any(t.get("word") == "#" for t in parsed)
                except (json.JSONDecodeError, ValueError, TypeError):
                    # Old format or invalid - check if '#' is in comma-separated string
                    preserve_hash = '#' in words_to_remove

            # Remove fragments only if NOT preserving them
            # Query parameters like ?module=XXX are always preserved so URLs with different
            # query params generate different filenames
            if not preserve_hash and '#' in path:
                path = path.split('#')[0]

            # ✅ Apply word transformations (supports both old string format and new JSON array format)
            if words_to_remove:
                import re
                import json

                transformations = []

                # Try to parse as JSON array (new format)
                try:
                    parsed = json.loads(words_to_remove)
                    if isinstance(parsed, list):
                        # New format: [{"word": "dse-v2", "replacement": " ", "type": "space"}, ...]
                        transformations = parsed
                    else:
                        # Fallback to old format
                        transformations = [{"word": w.strip(), "replacement": " ", "type": "space"}
                                           for w in words_to_remove.split(',') if w.strip()]
                except (json.JSONDecodeError, ValueError):
                    # Old format: comma-separated string "dse-v2, .png, Accounting"
                    transformations = [{"word": w.strip(), "replacement": " ", "type": "space"}
                                       for w in words_to_remove.split(',') if w.strip()]

                # Apply each transformation
                for transform in transformations:
                    word = transform.get("word", "")
                    replacement = transform.get("replacement", " ")

                    if not word:
                        continue

                    # Apply transformation (case-insensitive)
                    pattern = re.compile(re.escape(word), re.IGNORECASE)
                    path = pattern.sub(replacement, path)

                # Clean up multiple slashes and spaces
                path = re.sub(r'/+', '/', path)  # Multiple slashes -> single slash
                path = re.sub(r'\s+', ' ', path)  # Multiple spaces -> single space
                path = path.strip('/ ')  # Remove leading/trailing slashes and spaces

            # If empty, use "Index"
            if not path:
                base_name = "Index"
            else:
                # Split path by / and convert each segment to PascalCase
                segments = path.split('/')
                pascal_segments = [self._to_pascal_case(segment) for segment in segments if segment]

                # Join with underscore
                base_name = '_'.join(pascal_segments)

            # Safety: Ensure base_name never starts with symbols
            import re
            base_name = re.sub(r'^[^a-zA-Z0-9]+', '', base_name)

            # If base_name is empty after cleanup, use default
            if not base_name:
                base_name = "Unnamed"

            # Generate filename based on segment count
            if total_segments == 1:
                # Single screenshot
                filename = f"{base_name}.png"
            else:
                # Multiple screenshots - add sequence number
                filename = f"{base_name}_{segment_index:03d}.png"
        else:
            # No base URL or URL doesn't match - use old behavior (domain + timestamp)
            domain = url.split("//")[1].split("/")[0].replace(":", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if total_segments == 1:
                filename = f"{domain}_{timestamp}.png"
            else:
                filename = f"{domain}_{segment_index:03d}_{timestamp}.png"

        return filename

    async def save_auth_state(self, url: str, storage_state_path: str, browser_engine: str = "playwright"):
        """
        Open a browser window for manual login and save the auth state

        Args:
            url: URL to navigate to for login
            storage_state_path: Path to save the storage state file
            browser_engine: "playwright" or "camoufox" - determines which browser to use
        """
        logger.debug(f"🔓 Opening browser for manual login...")
        logger.debug(f"📍 Navigate to: {url}")
        logger.debug(f"⏳ Waiting for you to log in...")

        use_camoufox = (browser_engine == "camoufox" and CAMOUFOX_AVAILABLE)

        # Clean up any existing login profile to avoid conflicts
        if use_camoufox:
            import shutil
            login_profile_dir = Path(self.output_dir).parent / "browser_sessions" / "camoufox_profile_login"
            if login_profile_dir.exists():
                logger.info(f"   🧹 Cleaning up old login profile...")
                try:
                    shutil.rmtree(login_profile_dir)
                    logger.info(f"   ✅ Old login profile removed")
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not remove old login profile: {str(e)}")
                    logger.info(f"   💡 Please close any open Camoufox windows and try again")

        if use_camoufox:
            # ✅ CAMOUFOX MODE: Use persistent context for maximum compatibility
            logger.info(f"🦊 Launching Camoufox browser (maximum stealth mode)...")

            # Setup persistent profile directory for login
            # Use a SEPARATE profile for login to avoid conflicts with screenshot captures
            persistent_profile_dir = Path(self.output_dir).parent / "browser_sessions" / "camoufox_profile_login"
            persistent_profile_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"   🔐 Using persistent Camoufox profile: {persistent_profile_dir}")
            logger.info(f"   💡 This maintains ALL auth state (cookies, localStorage, sessionStorage, etc.)")
            logger.debug(f"   ℹ️  Using separate login profile to avoid conflicts")

            # Launch Camoufox with persistent context
            login_browser = await AsyncCamoufox(
                headless=False,  # Always visible for manual login
                humanize=True,
                block_webrtc=True,
                persistent_context=True,  # ✅ Enable persistent context
                user_data_dir=str(persistent_profile_dir),  # ✅ Store profile data
            ).__aenter__()

            logger.info(f"✅ Camoufox browser ready with persistent profile!")

            # For Camoufox with persistent_context, the browser IS the context
            context = login_browser
            page = await context.new_page()

            # Navigate to URL first
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # ✅ Set distinctive title to help user identify this browser window
            await page.evaluate("""() => {
                document.title = '🔐 LOGIN BROWSER (Camoufox) - Screenshot Tool - ' + document.title;
            }""")

            # ✅ Add visual indicator banner at the top of the page
            await page.evaluate("""() => {
                const banner = document.createElement('div');
                banner.id = 'screenshot-tool-login-banner';
                banner.innerHTML = '🔐 LOGIN BROWSER (Camoufox) - Screenshot Tool Session';
                banner.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 20px;
                    text-align: center;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 14px;
                    font-weight: 600;
                    z-index: 999999;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    letter-spacing: 0.5px;
                `;
                document.body.insertBefore(banner, document.body.firstChild);

                // Adjust body padding to prevent content from hiding under banner
                document.body.style.paddingTop = '48px';
            }""")

        else:
            # ✅ PLAYWRIGHT MODE: Standard Chromium browser
            # Create a SEPARATE browser instance for login (not shared with screenshot captures)
            # This ensures the login window stays open even when screenshots are being captured
            login_playwright = await async_playwright().start()
            login_browser = await login_playwright.chromium.launch(
                headless=False,  # Always visible for manual login
                channel="chrome",  # Use real Chrome
            )

            # Create context without any auth (fresh login)
            # Use comfortable viewport size that fits on screen
            context = await login_browser.new_context(
                viewport={'width': 1366, 'height': 768},
                locale='en-US',
                timezone_id='America/New_York',
            )

            page = await context.new_page()

            # Navigate to URL for Playwright mode
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # ✅ Set distinctive title to help user identify this browser window
            await page.evaluate("""() => {
                document.title = '🔐 LOGIN BROWSER - Screenshot Tool - ' + document.title;
            }""")

            # ✅ Add visual indicator banner at the top of the page
            await page.evaluate("""() => {
                const banner = document.createElement('div');
                banner.id = 'screenshot-tool-login-banner';
                banner.innerHTML = '🔐 LOGIN BROWSER - Screenshot Tool Session';
                banner.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 20px;
                    text-align: center;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 14px;
                    font-weight: 600;
                    z-index: 999999;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    letter-spacing: 0.5px;
                `;
                document.body.insertBefore(banner, document.body.firstChild);

                // Adjust body padding to prevent content from hiding under banner
                document.body.style.paddingTop = '48px';
            }""")

        logger.info(f"✅ Browser opened!")
        logger.info(f"   🏷️  Window title: '🔐 LOGIN BROWSER - Screenshot Tool'")
        logger.debug(f"   🎨 Purple banner added at top of page for easy identification")
        logger.debug(f"")
        logger.info(f"📋 INSTRUCTIONS:")
        logger.debug(f"  1. Complete your login (Okta/MFA/etc.)")
        logger.debug(f"  2. Wait until you see your dashboard")
        logger.debug(f"  3. The tool will automatically detect when you're logged in")
        logger.debug(f"")
        logger.debug(f"⏳ Waiting for login... (checking every 5 seconds)")

        # Wait for user to login - check for common auth indicators
        max_wait_time = 300  # 5 minutes
        check_interval = 5  # Check every 5 seconds
        elapsed = 0

        logger.info(f"💡 TIP: Wait until you see your FULL dashboard (no loading spinners or errors)")
        logger.info(f"💡 IMPORTANT: Make sure you don't see 'Your role has been changed' message!")
        logger.debug(f"")

        while elapsed < max_wait_time:
            await asyncio.sleep(check_interval)
            elapsed += check_interval

            # Check if page has changed (user navigated after login)
            current_url = page.url

            # Check for common auth indicators in localStorage AND page readiness
            try:
                page_status = await page.evaluate("""
                    () => {
                        // Check for common auth tokens
                        const keys = Object.keys(localStorage);
                        const hasAuth = keys.some(k =>
                            k.toLowerCase().includes('token') ||
                            k.toLowerCase().includes('auth') ||
                            k.toLowerCase().includes('session')
                        );

                        // Check for the specific error messages
                        const bodyText = document.body.innerText;
                        const hasRoleChangeError = bodyText.includes('Your role has been changed');
                        const hasUnableToFetchError = bodyText.includes('Unable to fetch');
                        const hasJSONError = bodyText.includes('Unexpected token') || bodyText.includes('valid JSON');
                        const hasAnyError = hasRoleChangeError || hasUnableToFetchError || hasJSONError;

                        // Check if page is fully loaded (no loading indicators)
                        const hasLoadingSpinner = document.querySelector('[class*="loading"], [class*="spinner"], [class*="loader"]');

                        // Check if error dialogs are visible
                        const hasErrorDialog = document.querySelector('[class*="error"], [class*="Error"]');

                        return {
                            hasAuth: hasAuth,
                            hasRoleChangeError: hasRoleChangeError,
                            hasUnableToFetchError: hasUnableToFetchError,
                            hasJSONError: hasJSONError,
                            hasAnyError: hasAnyError,
                            hasLoadingSpinner: !!hasLoadingSpinner,
                            hasErrorDialog: !!hasErrorDialog,
                            ready: hasAuth && !hasLoadingSpinner && !hasAnyError && !hasErrorDialog
                        };
                    }
                """)

                if page_status['hasRoleChangeError']:
                    logger.warning(f"⚠️  Detected 'Your role has been changed' - waiting for it to clear... ({elapsed}s)")
                elif page_status['hasUnableToFetchError']:
                    logger.warning(f"⚠️  Detected 'Unable to fetch' errors - waiting for data to load... ({elapsed}s)")
                elif page_status['hasJSONError']:
                    logger.warning(f"⚠️  Detected JSON parsing errors - waiting for them to clear... ({elapsed}s)")
                elif page_status['hasErrorDialog']:
                    logger.warning(f"⚠️  Error dialogs visible - waiting for them to clear... ({elapsed}s)")
                elif page_status['hasLoadingSpinner']:
                    logger.debug(f"⏳ Loading spinner detected - waiting... ({elapsed}s)")
                elif not page_status['hasAuth']:
                    logger.debug(f"⏳ Waiting for login... ({elapsed}s)")
                elif page_status['ready']:
                    logger.info(f"✅ Login detected! (auth tokens found + page fully loaded + NO errors)")
                    break
                else:
                    logger.debug(f"⏳ Still waiting... ({elapsed}s)")
            except Exception as e:
                logger.error(f"⏳ Still waiting... ({elapsed}s) [check failed: {str(e)[:50]}]")

        if elapsed >= max_wait_time:
            raise Exception("Timeout waiting for login. Please try again.")

        # Wait MUCH longer to ensure ALL data is loaded (dealer info, language, location, etc.)
        logger.debug(f"⏳ Waiting 60 more seconds to ensure ALL data is fully loaded...")
        logger.debug(f"   (This ensures dealer info, language, location data, role initialization, etc. are ready)")
        logger.info(f"   💡 TIP: Watch the browser - make sure all errors disappear and data loads!")
        await asyncio.sleep(60)

        # Save the storage state IMMEDIATELY (before anything can close)
        logger.info(f"💾 Saving auth state to {storage_state_path}...")
        try:
            if use_camoufox:
                # For Camoufox with persistent context, auth is already saved in the profile
                # But we still save storage_state for compatibility with other tools
                logger.info(f"   ✅ Auth state automatically saved in login profile!")
                logger.info(f"   📁 Login profile location: {persistent_profile_dir}")

                # Copy the login profile to the main profile for screenshot captures
                import shutil
                main_profile_dir = Path(self.output_dir).parent / "browser_sessions" / "camoufox_profile"

                logger.info(f"   📋 Copying login profile to main profile...")
                logger.debug(f"   📁 Main profile location: {main_profile_dir}")

                # Remove old main profile if it exists
                if main_profile_dir.exists():
                    shutil.rmtree(main_profile_dir)

                # Copy login profile to main profile
                shutil.copytree(persistent_profile_dir, main_profile_dir)
                logger.info(f"   ✅ Profile copied successfully!")
                logger.info(f"   💡 Future captures will use this profile automatically")

                # Also save storage_state for compatibility (with retry)
                for attempt in range(self.MAX_STORAGE_STATE_RETRIES):
                    try:
                        await context.storage_state(path=storage_state_path)
                        break
                    except Exception as retry_error:
                        if attempt < 2:
                            logger.warning(f"   ⚠️  Retry {attempt + 1}/3: {str(retry_error)}")
                            await asyncio.sleep(1)
                        else:
                            raise

                # Get stats
                with open(storage_state_path, 'r') as f:
                    state = json.load(f)

                cookie_count = len(state.get('cookies', []))
                ls_count = sum(len(origin.get('localStorage', [])) for origin in state.get('origins', []))

                logger.info(f"   📊 Also saved to {storage_state_path}:")
                logger.debug(f"      Cookies: {cookie_count}")
                logger.debug(f"      localStorage items: {ls_count}")
            else:
                # Playwright mode - save storage_state normally (with retry)
                for attempt in range(3):
                    try:
                        await context.storage_state(path=storage_state_path)
                        break
                    except Exception as retry_error:
                        if attempt < 2:
                            logger.warning(f"   ⚠️  Retry {attempt + 1}/3: {str(retry_error)}")
                            await asyncio.sleep(1)
                        else:
                            raise

                # Get stats
                with open(storage_state_path, 'r') as f:
                    state = json.load(f)

                cookie_count = len(state.get('cookies', []))
                ls_count = sum(len(origin.get('localStorage', [])) for origin in state.get('origins', []))

                logger.info(f"✅ Auth state saved successfully!")
                logger.info(f"   📊 Cookies: {cookie_count}")
                logger.info(f"   📊 localStorage items: {ls_count}")
        except Exception as e:
            logger.error(f"❌ Failed to save auth state: {str(e)}")
            logger.info(f"💡 TIP: The browser/context may have closed too quickly.")
            logger.info(f"💡 Try again, or use Real Browser Mode instead.")
            raise Exception(f"Failed to save auth state: {str(e)}")

        logger.debug(f"")
        logger.debug(f"🎉 Browser window will STAY OPEN for you to verify!")
        logger.warning(f"   ⚠️  DO NOT CLOSE IT YET - verify your dashboard looks good!")
        logger.info(f"   ✅ When you're satisfied, close the browser window manually.")
        logger.debug(f"   Future captures will automatically use this saved auth state.")
        logger.debug(f"")
        logger.debug(f"⏳ Keeping browser open indefinitely... (close it manually when done)")

        # Keep browser open - wait indefinitely until user closes it
        # Don't close page or context - let user close the browser window
        try:
            # Wait for page to be closed by user (no timeout)
            while not page.is_closed():
                await asyncio.sleep(1)
            logger.info(f"✅ Browser closed by user. Auth state is ready to use!")
        except Exception as e:
            logger.warning(f"⚠️  Browser closed: {str(e)}")

        # Clean up the separate login browser instance
        try:
            if use_camoufox:
                # For Camoufox, the context IS the browser
                await login_browser.__aexit__(None, None, None)
                logger.info(f"🧹 Cleaned up Camoufox login browser instance")
            else:
                # For Playwright
                await context.close()
                await login_browser.close()
                await login_playwright.stop()
                logger.info(f"🧹 Cleaned up Playwright login browser instance")
        except Exception as e:
            logger.warning(f"⚠️  Cleanup warning: {str(e)}")

    async def cleanup_tabs_after_batch(self):
        """
        Clean up tabs after batch processing completes.

        This method:
        1. Closes all successful tabs (with 1 second wait)
        2. Keeps failed tabs open for debugging
        3. Removes stale tab references (disconnected browser)
        4. Runs periodic cleanup if interval elapsed
        """
        logger.info("\n🧹 Starting tab cleanup after batch...")
        await self.tab_registry.cleanup_successful_tabs()
        await self.tab_registry.periodic_cleanup()

        # Show stats
        stats = self.tab_registry.get_stats()
        if stats["total"] > 0:
            logger.info(f"📊 Tab Registry Stats:")
            logger.debug(f"   Total tabs: {stats['total']}")
            logger.info(f"   Success (should be 0): {stats['success']}")
            logger.error(f"   Failed (kept for debugging): {stats['failed']}")
            logger.debug(f"   Pending: {stats['pending']}")
        else:
            logger.info("✅ All tabs cleaned up successfully!")

    async def close(self):
        """Close browser instance (supports Playwright, Camoufox, and CDP)"""
        # ✅ NEW: Clean up all tabs first
        try:
            await self.tab_registry.clear_all()
        except Exception as e:
            logger.warning(f"⚠️  Error clearing tab registry: {e}")

        # Close CDP browser (disconnect, don't close the actual Chrome)
        if self.cdp_browser:
            try:
                await self.cdp_browser.close()
                logger.info("🔗 Disconnected from Chrome (browser remains open)")
            except Exception as e:  # ✅ FIXED: Specific exception instead of bare except
                logger.warning(f"⚠️  Error closing CDP browser: {e}")
            self.cdp_browser = None
            self.cdp_active_page = None

        # Close Camoufox browser
        if self.camoufox_browser:
            try:
                await self.camoufox_browser.__aexit__(None, None, None)
            except Exception as e:  # ✅ FIXED: Specific exception instead of bare except
                logger.warning(f"⚠️  Error closing Camoufox browser: {e}")
            self.camoufox_browser = None

        # Close standard Playwright browser
        # ✅ FIXED: Wrap in try-except to prevent resource leak if browser.close() fails
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"⚠️  Error closing Playwright browser: {e}")
            finally:
                self.browser = None

        # ✅ FIXED: Always stop playwright, even if browser.close() failed
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.warning(f"⚠️  Error stopping Playwright: {e}")
            finally:
                self.playwright = None

        # Reset mode tracking
        self.current_browser_mode = None
        self.current_mode_is_real_browser = None
