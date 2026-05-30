"""Logging configuration for the Screenshot Tool.

Provides structured logging with file rotation and console output, and
adds a per-request correlation ID to every log record for easier
tracing across services.

IMPORTANT: Use Lazy Logging for Performance
==========================================
Always use % formatting instead of f-strings in logger calls:

✅ GOOD (Lazy):  logger.debug("Processing %d items", count)
❌ BAD (Eager):  logger.debug(f"Processing {count} items")

Why? F-strings are evaluated BEFORE the log level check, wasting CPU/memory
even when logs are disabled. With % formatting, strings are only formatted
if the log level is enabled.

See backend/LAZY_LOGGING_GUIDE.md for complete documentation.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
from contextvars import ContextVar
from typing import Optional


# Correlation ID used for request tracing across logs and microservices.
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


class CorrelationIdFilter(logging.Filter):
    """Ensure every log record has a ``correlation_id`` attribute.

    The value is taken from :data:`correlation_id_var` when set,
    otherwise "-". This allows format strings to always reference
    ``%(correlation_id)s`` safely.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple
        try:
            cid = correlation_id_var.get()
        except Exception:
            cid = None
        record.correlation_id = cid or "-"
        return True


def setup_logging(name: str = __name__) -> logging.Logger:
    """Configure structured logging for the application.

    This function is safe to call multiple times and guarantees that every
    :class:`logging.LogRecord` has a ``correlation_id`` attribute, avoiding
    formatting errors even when third-party libraries log early.

    Features:
    - Console output with rotating file handler
    - Log level from ``LOG_LEVEL`` env var (default: INFO)
    - Per-request correlation ID in all log lines
    """

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Install a LogRecord factory that always provides ``correlation_id``.
    # This is a belt-and-suspenders safeguard in case any handler or logger
    # bypasses our filters.
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):  # pragma: no cover - thin wrapper
        record = old_factory(*args, **kwargs)
        if not hasattr(record, "correlation_id"):
            try:
                cid = correlation_id_var.get()
            except Exception:
                cid = None
            record.correlation_id = cid or "-"
        return record

    logging.setLogRecordFactory(record_factory)

    # Get log level from environment (default: INFO)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=(
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "[cid=%(correlation_id)s] %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                "logs/screenshot_tool.log",
                maxBytes=10_485_760,  # 10MB
                backupCount=5,
                encoding="utf-8",
            ),
        ],
        force=True,  # Override any existing configuration
    )

    # Ensure correlation ID filter is attached to the root logger so all
    # records get the ``correlation_id`` attribute.
    root_logger = logging.getLogger()
    if not any(isinstance(f, CorrelationIdFilter) for f in root_logger.filters):
        root_logger.addFilter(CorrelationIdFilter())

    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return logging.getLogger(name)


# Create default logger
logger = setup_logging()


# Convenience functions for common log patterns
def log_capture_start(url: str, mode: str, stealth: bool = False):
    """Log screenshot capture start"""
    stealth_indicator = "🥷" if stealth else "📸"
    logger.info(f"{stealth_indicator} Starting {mode} capture: {url}")


def log_capture_success(url: str, path: str, duration: float = None):
    """Log successful screenshot capture"""
    duration_str = f" ({duration:.2f}s)" if duration else ""
    logger.info(f"✅ Captured: {url} → {path}{duration_str}")


def log_capture_error(url: str, error: str):
    """Log screenshot capture error"""
    logger.error(f"❌ Failed to capture {url}: {error}")


def log_auth_state(cookie_count: int, ls_count: int):
    """Log authentication state loading"""
    logger.info(f"🔐 Auth state loaded: {cookie_count} cookies, {ls_count} localStorage items")


def log_quality_check(url: str, score: float, passed: bool):
    """Log quality check result"""
    status = "✅ PASS" if passed else "⚠️  FAIL"
    logger.info(f"{status} Quality check for {url}: {score:.1f}/100")


def log_browser_launch(headless: bool, stealth: bool):
    """Log browser launch"""
    mode = "headless" if headless else "visible"
    stealth_str = " with stealth" if stealth else ""
    logger.info(f"🌐 Launching {mode} browser{stealth_str}")


def log_request_start(request_id: str, url_count: int):
    """Log API request start"""
    logger.info(f"🚀 Request {request_id[:8]}: Processing {url_count} URL(s)")


def log_request_complete(request_id: str, success_count: int, total_count: int, duration: float):
    """Log API request completion"""
    logger.info(
        f"🏁 Request {request_id[:8]} complete: "
        f"{success_count}/{total_count} successful ({duration:.2f}s)"
    )


def log_cancellation(request_id: str, completed: int, total: int):
    """Log request cancellation"""
    logger.warning(
        f"🛑 Request {request_id[:8]} cancelled: "
        f"{completed}/{total} completed before cancellation"
    )
