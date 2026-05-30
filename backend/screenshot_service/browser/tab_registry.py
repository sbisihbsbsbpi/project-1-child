"""
Tab lifecycle management for Real Browser Mode.

Extracted from screenshot_service.py (lines 123-292)
Part of Week 2 refactoring.
"""

import asyncio
import time
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class TabRegistry:
    """
    Manages browser tabs for Real Browser Mode with:
    - Disconnect detection
    - Memory leak prevention
    - Automatic cleanup
    """
    
    # Class constant (referenced from ScreenshotService)
    TAB_CLOSE_DELAY_SEC = 2

    def __init__(self, max_size=100, cleanup_interval=300, max_tab_age=1800):
        """
        Initialize tab registry with orphan cleanup capabilities.

        Args:
            max_size: Maximum number of tabs to track (prevents memory leaks)
            cleanup_interval: Seconds between periodic cleanups (default: 5 minutes)
            max_tab_age: Maximum age for pending tabs in seconds (default: 30 minutes)
        """
        self.tabs = {}  # {url: {"page": Page, "status": str, "created_at": float}}
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.max_tab_age = max_tab_age
        self.last_cleanup = 0  # Will be set on first cleanup
        self.time = time

        # ✅ RACE CONDITION FIX: Lock to prevent concurrent cleanup operations
        self._cleanup_lock = asyncio.Lock()

        # Orphan Cleanup Metrics
        self.cleanup_metrics = {
            "total_cleanups": 0,
            "total_orphans_removed": 0,
            "total_stale_removed": 0,
            "total_age_based_removed": 0,
            "total_successful_closed": 0,
            "last_cleanup_time": 0,
            "last_orphan_count": 0
        }

    async def register_tab(self, url: str, page: Page):
        """Register a new tab"""
        # Enforce size limit
        if len(self.tabs) >= self.max_size:
            logger.warning("⚠️  Tab registry at max size (%d), cleaning up...", self.max_size)
            await self.cleanup_successful_tabs()

        self.tabs[url] = {
            "page": page,
            "status": "pending",
            "created_at": self.time.time()
        }
        logger.debug("📋 Registered tab: %s", url)

    async def mark_success(self, url: str):
        """Mark tab as successfully captured"""
        if url in self.tabs:
            self.tabs[url]["status"] = "success"
            logger.debug("✅ Marked success: %s", url)

    async def mark_failure(self, url: str):
        """Mark tab as failed"""
        if url in self.tabs:
            self.tabs[url]["status"] = "failed"
            logger.debug("❌ Marked failure: %s", url)

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
        """Close tabs that successfully captured screenshots and remove orphans"""
        async with self._cleanup_lock:  # ✅ RACE CONDITION FIX: Prevent concurrent cleanup
            closed_count = 0
            kept_count = 0
            stale_count = 0

            for url, info in list(self.tabs.items()):
                # Check if tab is still alive (orphan detection)
                if not await self.is_tab_alive(url):
                    del self.tabs[url]
                    stale_count += 1
                    logger.info("🧹 Removed stale tab: %s", url)
                    continue

                # Close successful tabs
                if info["status"] == "success":
                    try:
                        # ⏱️ Wait before closing (user requested)
                        await asyncio.sleep(self.TAB_CLOSE_DELAY_SEC)
                        await info["page"].close()
                        del self.tabs[url]
                        closed_count += 1
                        logger.info("✅ Closed successful tab: %s", url)
                    except Exception as e:
                        logger.warning("⚠️  Error closing tab for %s: %s", url, e)
                        del self.tabs[url]  # Remove from registry anyway
                else:
                    kept_count += 1
                    logger.warning("⚠️  Keeping tab open for debugging: %s (Status: %s)", url, info['status'])

            # Update metrics
            if stale_count > 0:
                self.cleanup_metrics["total_stale_removed"] += stale_count
                self.cleanup_metrics["total_orphans_removed"] += stale_count

            if closed_count > 0:
                self.cleanup_metrics["total_successful_closed"] += closed_count

            if closed_count > 0 or kept_count > 0 or stale_count > 0:
                logger.info("📊 Cleanup complete: %d closed, %d kept for debugging, %d stale removed",
                           closed_count, kept_count, stale_count)

            return {"closed": closed_count, "kept": kept_count, "stale": stale_count}

    async def cleanup_stale_tabs(self):
        """Remove dead tab references (browser disconnected/crashed)"""
        async with self._cleanup_lock:  # ✅ RACE CONDITION FIX: Prevent concurrent cleanup
            stale_urls = []

            for url in list(self.tabs.keys()):
                if not await self.is_tab_alive(url):
                    stale_urls.append(url)

            for url in stale_urls:
                del self.tabs[url]

            if len(stale_urls) > 0:
                self.cleanup_metrics["total_stale_removed"] += len(stale_urls)
                self.cleanup_metrics["total_orphans_removed"] += len(stale_urls)
                logger.info("🧹 Removed %d stale tab references (browser disconnected)", len(stale_urls))

            return len(stale_urls)

    async def cleanup_old_pending_tabs(self):
        """Remove tabs that have been pending for too long (age-based cleanup)"""
        async with self._cleanup_lock:  # ✅ RACE CONDITION FIX: Prevent concurrent cleanup
            current_time = self.time.time()
            old_urls = []

            for url, info in list(self.tabs.items()):
                # Only cleanup pending tabs that are too old
                if info["status"] == "pending":
                    age = current_time - info["created_at"]
                    if age > self.max_tab_age:
                        old_urls.append(url)

            for url in old_urls:
                logger.warning("⏰ Removing old pending tab (age: %.1f min): %s",
                             (current_time - self.tabs[url]["created_at"]) / 60, url)
                try:
                    # Try to close the page if it's still alive
                    if not self.tabs[url]["page"].is_closed():
                        await self.tabs[url]["page"].close()
                except Exception:
                    pass  # Best effort

                del self.tabs[url]

            if len(old_urls) > 0:
                self.cleanup_metrics["total_age_based_removed"] += len(old_urls)
                self.cleanup_metrics["total_orphans_removed"] += len(old_urls)
                logger.info("⏰ Removed %d old pending tabs (max age: %d min)",
                           len(old_urls), self.max_tab_age // 60)

            return len(old_urls)

    async def periodic_cleanup(self):
        """Run comprehensive periodic cleanup if interval elapsed"""
        current_time = self.time.time()

        # Initialize last_cleanup on first call
        if self.last_cleanup == 0:
            self.last_cleanup = current_time
            return

        if current_time - self.last_cleanup > self.cleanup_interval:
            logger.info("🧹 Running periodic orphan cleanup...")

            # Track cleanup operation
            self.cleanup_metrics["total_cleanups"] += 1
            self.cleanup_metrics["last_cleanup_time"] = current_time

            # Run all cleanup operations
            stale_count = await self.cleanup_stale_tabs()
            old_count = await self.cleanup_old_pending_tabs()

            total_removed = stale_count + old_count
            self.cleanup_metrics["last_orphan_count"] = total_removed

            if total_removed > 0:
                logger.info("📊 Periodic cleanup complete: %d orphans removed (%d stale, %d old)",
                           total_removed, stale_count, old_count)

            self.last_cleanup = current_time
            return total_removed

        return 0

    async def clear_all(self):
        """Close all tabs and clear registry.

        Returns the number of tabs successfully closed.
        """
        async with self._cleanup_lock:  # ✅ RACE CONDITION FIX: Prevent concurrent cleanup
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
                logger.info("🧹 Cleared all tabs (%d closed)", closed_count)
            return closed_count

    def get_stats(self):
        """Get comprehensive registry statistics including orphan cleanup metrics"""
        total = len(self.tabs)
        success = sum(1 for info in self.tabs.values() if info["status"] == "success")
        failed = sum(1 for info in self.tabs.values() if info["status"] == "failed")
        pending = sum(1 for info in self.tabs.values() if info["status"] == "pending")

        # Calculate tab ages
        current_time = self.time.time()
        tab_ages = [(current_time - info["created_at"]) for info in self.tabs.values()]

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "pending": pending,
            "oldest_tab_age_sec": max(tab_ages) if tab_ages else 0,
            "newest_tab_age_sec": min(tab_ages) if tab_ages else 0,
            "avg_tab_age_sec": sum(tab_ages) / len(tab_ages) if tab_ages else 0,
            "cleanup_metrics": self.cleanup_metrics.copy()
        }

    def get_cleanup_summary(self):
        """Get orphan cleanup summary for monitoring"""
        current_time = self.time.time()
        time_since_cleanup = current_time - self.cleanup_metrics["last_cleanup_time"] if self.cleanup_metrics["last_cleanup_time"] > 0 else 0

        return {
            "total_cleanups_run": self.cleanup_metrics["total_cleanups"],
            "total_orphans_removed_lifetime": self.cleanup_metrics["total_orphans_removed"],
            "stale_removed": self.cleanup_metrics["total_stale_removed"],
            "age_based_removed": self.cleanup_metrics["total_age_based_removed"],
            "successful_closed": self.cleanup_metrics["total_successful_closed"],
            "last_cleanup_orphan_count": self.cleanup_metrics["last_orphan_count"],
            "seconds_since_last_cleanup": time_since_cleanup,
            "next_cleanup_in_sec": max(0, self.cleanup_interval - time_since_cleanup) if time_since_cleanup > 0 else self.cleanup_interval
        }


__all__ = ["TabRegistry"]
