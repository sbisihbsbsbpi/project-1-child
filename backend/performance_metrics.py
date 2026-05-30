"""Performance Metrics Configuration.

Single source of truth for all performance-related constants used in
documentation generation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import json


CONFIG_PATH = Path(__file__).with_name("performance_config.json")


def _load_config() -> Dict[str, Any]:
    """Load performance configuration from JSON file, if present.

    Silently falls back to defaults on any error so docs generation
    never fails due to config corruption.
    """

    if not CONFIG_PATH.exists():
        return {}

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


@dataclass
class PerformanceMetrics:
    """Performance metrics for screenshot tool."""

    # ===== Batch Configuration =====
    batch_1_urls: int = 18
    batch_2_urls: int = 19
    batch_3_urls: int = 16

    # ===== Timing (seconds) =====
    batch_timeout: float = 90.0  # Real Browser Mode timeout
    ui_load_wait_min: float = 10.0
    ui_load_wait_max: float = 12.0

    # ===== Calculated Properties =====
    @property
    def total_urls(self) -> int:
        """Total number of URLs across all batches."""

        return self.batch_1_urls + self.batch_2_urls + self.batch_3_urls

    @property
    def total_time(self) -> float:
        """Total time for all batches (seconds)."""

        return self.batch_timeout * 3  # 3 batches

    @property
    def total_time_minutes(self) -> float:
        """Total time in minutes."""

        return self.total_time / 60

    @property
    def avg_time_per_url(self) -> float:
        """Average time per URL (seconds)."""

        return self.total_time / self.total_urls

    @property
    def sequential_time(self) -> float:
        """Time if processed sequentially (seconds)."""

        return self.total_urls * self.ui_load_wait_max

    @property
    def sequential_time_minutes(self) -> float:
        """Sequential time in minutes."""

        return self.sequential_time / 60

    @property
    def speedup(self) -> float:
        """Speedup factor vs sequential."""

        return self.sequential_time / self.total_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""

        return {
            # Batch config
            "batch_1_urls": self.batch_1_urls,
            "batch_2_urls": self.batch_2_urls,
            "batch_3_urls": self.batch_3_urls,
            "total_urls": self.total_urls,
            # Timing
            "batch_timeout": self.batch_timeout,
            "ui_load_wait_min": self.ui_load_wait_min,
            "ui_load_wait_max": self.ui_load_wait_max,
            # Calculated
            "total_time": self.total_time,
            "total_time_minutes": self.total_time_minutes,
            "avg_time_per_url": self.avg_time_per_url,
            "sequential_time": self.sequential_time,
            "sequential_time_minutes": self.sequential_time_minutes,
            "speedup": self.speedup,
        }


def _init_metrics() -> PerformanceMetrics:
    """Initialize metrics from optional JSON configuration."""

    config = _load_config()
    timeout = config.get("batch_timeout")
    if isinstance(timeout, (int, float)):
        return PerformanceMetrics(batch_timeout=float(timeout))
    return PerformanceMetrics()


# Global instance
metrics = _init_metrics()


def save_batch_timeout(timeout: float) -> None:
    """Persist batch_timeout in a JSON config file used by docs."""

    config = _load_config()
    config["batch_timeout"] = float(timeout)
    tmp_path = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    tmp_path.replace(CONFIG_PATH)


if __name__ == "__main__":
    # Print metrics for verification
    print("Performance Metrics:")
    print(f"  Total URLs: {metrics.total_urls}")
    print(f"  Batch timeout: {metrics.batch_timeout}s")
    print(f"  Total time: {metrics.total_time}s ({metrics.total_time_minutes:.1f} min)")
    print(f"  Avg per URL: {metrics.avg_time_per_url:.1f}s")
    print(f"  Sequential: {metrics.sequential_time}s ({metrics.sequential_time_minutes:.1f} min)")
    print(f"  Speedup: {metrics.speedup:.1f}x")

