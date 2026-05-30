"""System-level helpers for backend resource usage metrics.

This module exposes :func:`_get_backend_resource_usage`, which is used by
routers to report lightweight CPU/memory metrics for the status UI.
"""

from typing import Dict, Optional
from collections import deque

import os

import psutil

from logging_config import setup_logging


logger = setup_logging(__name__)

# ✅ CPU measurement initialization and smoothing
_backend_process = None
_cpu_history = deque(maxlen=5)  # Rolling average of last 5 measurements
_system_cpu_history = deque(maxlen=5)

def _initialize_cpu_monitoring():
    """Initialize CPU monitoring to ensure accurate measurements from first call."""
    global _backend_process

    if _backend_process is None:
        try:
            _backend_process = psutil.Process(os.getpid())
            # Prime the CPU measurement (first call with interval=None establishes baseline)
            _backend_process.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None)
            logger.info("✅ CPU monitoring initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize CPU monitoring: {e}")
            _backend_process = None

# Initialize on module import
_initialize_cpu_monitoring()


def _get_backend_resource_usage() -> Optional[dict]:
    """Get backend, system, and browser resource usage metrics.

    Returns a dict with (when available):
    - backend_rss_mb, backend_cpu_percent (smoothed with 5-sample rolling average)
    - system_ram_total_mb, system_ram_used_mb, system_ram_percent
    - system_cpu_percent (smoothed with 5-sample rolling average)
    - browser_rss_mb, browser_cpu_percent (aggregated across known browser processes)

    CPU measurements use interval=0.1 for accuracy and are smoothed with a
    rolling average to reduce noise from brief spikes.
    """
    global _backend_process, _cpu_history, _system_cpu_history

    try:
        # Backend process metrics
        if _backend_process is None:
            _initialize_cpu_monitoring()
            process = psutil.Process(os.getpid())
        else:
            process = _backend_process

        with process.oneshot():
            mem_info = process.memory_info()
            backend_rss_mb = mem_info.rss / (1024 * 1024)

            # ✅ FIXED: Use interval=0.1 for accurate CPU measurement (100ms sample)
            # This is fast enough for status bar updates but accurate
            current_backend_cpu = process.cpu_percent(interval=0.1)
            _cpu_history.append(current_backend_cpu)
            # Use rolling average to smooth out brief spikes
            backend_cpu_percent = sum(_cpu_history) / len(_cpu_history) if _cpu_history else 0.0

        # System-wide memory and CPU
        vm = psutil.virtual_memory()
        system_ram_total_mb = vm.total / (1024 * 1024)
        system_ram_used_mb = vm.used / (1024 * 1024)
        system_ram_percent = vm.percent

        # ✅ FIXED: Use interval=0.1 for accurate system CPU measurement
        current_system_cpu = psutil.cpu_percent(interval=0.1)
        _system_cpu_history.append(current_system_cpu)
        system_cpu_percent = sum(_system_cpu_history) / len(_system_cpu_history) if _system_cpu_history else 0.0

        # Browser processes (Brave / Chrome / Firefox / Camoufox, etc.)
        # ⚠️ NOTE: This captures ALL browser instances on the system, not just
        # those launched by this app. For more accurate tracking, we'd need to
        # store browser PIDs when launching and check against those.
        browser_rss_bytes = 0
        browser_cpu_percent = 0.0
        browser_keywords = ("brave", "chrome", "firefox", "camoufox")

        for proc in psutil.process_iter(["name", "memory_info"]):
            try:
                name = (proc.info.get("name") or "").lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

            if not name:
                continue

            if any(keyword in name for keyword in browser_keywords):
                try:
                    mem = proc.info.get("memory_info")
                    if mem is not None:
                        browser_rss_bytes += mem.rss
                    # Best-effort CPU percent; may be 0 on first call
                    browser_cpu_percent += proc.cpu_percent(interval=0.0)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        data: Dict[str, float] = {
            "backend_rss_mb": backend_rss_mb,
            "backend_cpu_percent": backend_cpu_percent,
            "system_ram_total_mb": system_ram_total_mb,
            "system_ram_used_mb": system_ram_used_mb,
            "system_ram_percent": system_ram_percent,
            "system_cpu_percent": system_cpu_percent,
        }

        if browser_rss_bytes > 0:
            data["browser_rss_mb"] = browser_rss_bytes / (1024 * 1024)
            data["browser_cpu_percent"] = browser_cpu_percent

        return data
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"⚠️ Failed to get backend/system resource usage: {e}")
        return None

