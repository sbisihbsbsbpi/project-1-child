"""
FastAPI Backend for Screenshot Tool
Handles screenshot capture, quality checks, and document generation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware  # ⚡ OPTIMIZATION: Response compression
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, validator, Field
from typing import List, Optional, Dict
import asyncio
import json
from datetime import datetime
import os
import subprocess
from pathlib import Path
from uuid import uuid4
from cachetools import TTLCache
import psutil
import httpx  # For network proxy endpoint only

from screenshot_service import ScreenshotService
from document_service import DocumentService
from quality_checker import QualityChecker
from logging_config import setup_logging, log_request_start, log_request_complete, log_cancellation
from config import settings  # ✅ PHASE 3: Centralized configuration
from api_extraction_service import APIExtractionService  # 🌐 API extraction and documentation
from template_removal_service import template_removal_service  # 🎨 Template logo removal service
from template_logo_addition_service import template_logo_addition_service  # ✨ Template logo addition service
from template_page_detector import template_page_detector  # 🔍 Template page comprehensive detector
from app.core.exceptions import (
    CaptureTimeoutError,
    CaptureCancelledError,
    URLValidationError,
    PathValidationError,
    SSRFAttemptError,
    ScreenshotToolError,
    DocumentGenerationError,
)
from app.core.path_security import PathSecurityValidator

# ✅ FIXED: Structured logging instead of print statements
logger = setup_logging(__name__)

app = FastAPI(title="Screenshot Tool API")

# ⚡ OPTIMIZATION: Enable GZip compression for responses (60-80% size reduction)
# Compresses responses larger than 1000 bytes (1KB)
# Automatic decompression by browser - zero frontend changes needed
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ✅ PHASE 3: CORS configuration from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # ✅ From config.py
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],  # 🌐 Support all HTTP methods for API testing
    allow_headers=["*"],
)


# ✅ TYPED EXCEPTIONS: Exception handlers for structured error responses
@app.exception_handler(PathValidationError)
async def path_validation_handler(request: Request, exc: PathValidationError):
    """Handle path validation errors with 400 Bad Request."""
    logger.warning(f"Path validation failed: {exc.path} - {exc.reason}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "error_type": "PathValidationError",
            "context": {"path": exc.path, "reason": exc.reason}
        }
    )


@app.exception_handler(URLValidationError)
async def url_validation_handler(request: Request, exc: URLValidationError):
    """Handle URL validation errors with 400 Bad Request."""
    logger.warning(f"URL validation failed: {exc.url} - {exc.reason}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "error_type": "URLValidationError",
            "context": {"url": exc.url, "reason": exc.reason}
        }
    )


@app.exception_handler(SSRFAttemptError)
async def ssrf_handler(request: Request, exc: SSRFAttemptError):
    """Handle SSRF attempts with 403 Forbidden."""
    logger.error(f"SSRF attempt detected: {str(exc)}")
    return JSONResponse(
        status_code=403,
        content={
            "detail": str(exc),
            "error_type": "SSRFAttemptError",
            "context": {}
        }
    )


@app.exception_handler(CaptureTimeoutError)
async def capture_timeout_handler(request: Request, exc: CaptureTimeoutError):
    """Handle capture timeout errors with 500 Internal Server Error."""
    logger.error(f"Capture timeout: {exc.url} after {exc.timeout_s}s")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "error_type": "CaptureTimeoutError",
            "context": {
                "url": exc.url,
                "timeout_s": exc.timeout_s,
                "reason": exc.reason
            }
        }
    )


@app.exception_handler(CaptureCancelledError)
async def capture_cancelled_handler(request: Request, exc: CaptureCancelledError):
    """Handle cancelled operations with 499 Client Closed Request."""
    logger.info(f"Capture cancelled: {exc.url} (request_id={exc.request_id})")
    return JSONResponse(
        status_code=499,
        content={
            "detail": str(exc),
            "error_type": "CaptureCancelledError",
            "context": {
                "url": exc.url,
                "request_id": exc.request_id,
                "reason": exc.reason
            }
        }
    )


@app.exception_handler(DocumentGenerationError)
async def document_generation_handler(request: Request, exc: DocumentGenerationError):
    """Handle document generation errors with 500 Internal Server Error."""
    logger.error(f"Document generation failed: {exc.reason} (files={exc.file_count})")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "error_type": "DocumentGenerationError",
            "context": {
                "reason": exc.reason,
                "file_count": exc.file_count
            }
        }
    )


@app.exception_handler(ScreenshotToolError)
async def generic_screenshot_error_handler(request: Request, exc: ScreenshotToolError):
    """Generic handler for all other ScreenshotToolError subclasses."""
    logger.error(f"Screenshot tool error ({exc.__class__.__name__}): {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "error_type": exc.__class__.__name__,
            "context": vars(exc) if hasattr(exc, '__dict__') else {}
        }
    )


# Services
screenshot_service = ScreenshotService()
document_service = DocumentService()
quality_checker = QualityChecker()  # ✅ MONOLITH: Local quality checker
api_extraction_service = APIExtractionService()  # 🌐 API extraction and documentation

# 🎨 Initialize template removal service with screenshot service for resource sharing
template_removal_service.screenshot_service = screenshot_service

# ✅ FIXED: Request-scoped cancellation tracking with TTL to prevent memory leaks
# Key: request_id (UUID), Value: {"cancelled": bool}
# TTL: 1 hour (3600 seconds) - automatically removes old entries
cancellation_contexts: TTLCache = TTLCache(maxsize=1000, ttl=3600)


# ✅ MONOLITH: Direct call to quality checker (no HTTP overhead)
async def check_quality_via_service(screenshot_path: str) -> Dict:
    """
    Check screenshot quality using local quality checker

    Args:
        screenshot_path: Path to screenshot file

    Returns:
        Dict with quality check results
    """
    return await quality_checker.check(screenshot_path)


# ✅ MONOLITH: API Service helper removed - using direct calls instead


def _get_backend_resource_usage() -> Optional[dict]:
    """Get backend, system, and browser resource usage metrics.

    Returns a dict with (when available):
    - backend_rss_mb, backend_cpu_percent
    - system_ram_total_mb, system_ram_used_mb, system_ram_percent
    - system_cpu_percent
    - browser_rss_mb, browser_cpu_percent (aggregated across known browser processes)
    """

    try:
        # Backend process metrics
        process = psutil.Process(os.getpid())
        with process.oneshot():
            mem_info = process.memory_info()
            backend_rss_mb = mem_info.rss / (1024 * 1024)
            # interval=0.0 gives the last computed value without blocking
            backend_cpu_percent = process.cpu_percent(interval=0.0)

        # System-wide memory and CPU
        vm = psutil.virtual_memory()
        system_ram_total_mb = vm.total / (1024 * 1024)
        system_ram_used_mb = vm.used / (1024 * 1024)
        system_ram_percent = vm.percent

        system_cpu_percent = psutil.cpu_percent(interval=0.0)

        # Browser processes (Brave / Chrome / Firefox / Camoufox, etc.)
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
    except Exception as e:
        logger.warning(f"⚠️ Failed to get backend/system resource usage: {e}")
        return None


# ✅ SECURITY: Path validation helper
# ✅ PHASE 1 (Path Security): Using centralized PathSecurityValidator
def validate_screenshot_path(file_path: str) -> Path:
    """
    Validate file path to prevent directory traversal attacks.
    Ensures path is within screenshots directory.

    Args:
        file_path: Requested file path

    Returns:
        Validated Path object

    Raises:
        PathValidationError: If path is invalid or outside allowed directory
    """
    return PathSecurityValidator.validate_path(
        path=file_path,
        base_dir=settings.screenshots_dir,
        must_exist=True,
        allow_symlinks=False,
        allowed_extensions=PathSecurityValidator.SCREENSHOT_EXTENSIONS,
    )


# Models
class URLRequest(BaseModel):
    urls: List[str]
    viewport_width: int = Field(default=1920, ge=800, le=7680, description="Viewport width (800-7680)")
    viewport_height: int = Field(default=1080, ge=600, le=4320, description="Viewport height (600-4320)")
    capture_mode: str = "viewport"  # "viewport", "fullpage", "segmented"
    use_stealth: bool = False
    use_real_browser: bool = False  # Use CDP to connect to existing Chrome (Active Tab Mode)
    headless: bool = False  # ✅ FIX: Default to headful (visible browser) - Real Browser Mode is always visible
    browser_engine: str = "playwright"  # "playwright" or "camoufox"
    base_url: str = ""  # Base URL for screenshot naming
    words_to_remove: str = ""  # Comma-separated words to remove from naming
    cookies: Optional[str] = ""  # JSON string of cookies for authentication
    local_storage: Optional[str] = ""  # JSON string of localStorage data for authentication
    # Advanced segmented settings
    segment_overlap: int = Field(default=20, ge=0, le=50, description="Percentage overlap (0-50%)")
    segment_scroll_delay: int = Field(default=1000, ge=0, le=10000, description="Scroll delay in ms (0-10000)")
    segment_max_segments: int = Field(default=50, ge=1, le=200, description="Max segments (1-200)")
    segment_skip_duplicates: bool = True  # Skip duplicate segments
    segment_smart_lazy_load: bool = True  # Wait for lazy-loaded content
    # ✅ NEW: Network event tracking
    track_network: bool = False  # Capture HTTP requests during page load
    # ✅ NEW: Per-request batch timeout (extended to support up to 2 hours)
    batch_timeout: Optional[int] = Field(default=90, ge=10, le=7200,
                                         description="Batch timeout in seconds (10-7200, up to 2 hours)")
    # ✅ NEW: Max parallel URLs per text box (for Real Browser Mode)
    max_parallel_urls: int = Field(default=5, ge=1, le=10,
                                   description="Max parallel URLs (1-10, Real Browser Mode only)")
    # ✅ NEW: Rolling parallelization mode
    enable_rolling_parallelization: bool = Field(default=False,
                                                 description="Enable rolling parallelization (start next URL as soon as one finishes)")
    # ✅ NEW: Auto expand dropdowns/collapsible sections
    auto_expand_dropdowns: bool = False  # Automatically expand all collapsed sections before screenshot
    # ✅ NEW: Click elements before screenshot
    click_elements: Optional[List[str]] = []  # List of text to search for and click before screenshot
    # ✅ NEW: Non-scrollable URLs list
    non_scrollable_urls: str = ""  # JSON string of URL patterns to treat as non-scrollable

    @validator('urls')
    def validate_urls(cls, v: List[str]) -> List[str]:
        """
        ✅ SECURITY: Validate URLs to prevent SSRF and DoS attacks

        Args:
            v: List of URLs to validate

        Returns:
            Validated list of URLs

        Raises:
            URLValidationError: If URLs are invalid
            SSRFAttemptError: If dangerous URL patterns detected
        """
        if not v:
            raise URLValidationError(reason='URL list cannot be empty')
        if len(v) > 500:
            raise URLValidationError(reason='Too many URLs (max 500 per request)')

        for url in v:
            # Check protocol
            if not url.startswith(('http://', 'https://')):
                raise URLValidationError(
                    url=url,
                    reason='Invalid URL protocol (must be http:// or https://)'
                )

            # Check length
            if len(url) > 2048:
                raise URLValidationError(
                    url=url,
                    reason=f'URL too long (max 2048 characters)'
                )

            # Block dangerous protocols
            dangerous_patterns = ['file://', 'javascript:', 'data:', 'ftp://', 'file:', 'localhost', '127.0.0.1',
                                  '0.0.0.0']
            url_lower = url.lower()
            for pattern in dangerous_patterns:
                if pattern in url_lower and not url_lower.startswith('http'):
                    raise SSRFAttemptError(f'Dangerous URL pattern detected: {pattern}')

        return v


class ScreenshotResult(BaseModel):
    url: str
    status: str  # "success", "failed", "pending"
    screenshot_path: Optional[str] = None
    screenshot_paths: Optional[List[str]] = None  # For segmented captures
    segment_count: Optional[int] = None  # Number of segments captured
    error: Optional[str] = None
    quality_score: Optional[float] = None
    quality_issues: Optional[List[str]] = None
    timestamp: str
    processing_time: Optional[float] = None  # Time taken to process this URL in seconds


class DocumentRequest(BaseModel):
    screenshot_paths: List[str]
    output_path: str
    title: str = "Screenshot Report"


# WebSocket connection manager
class ConnectionManager:
    def __init__(self) -> None:
        """Initialize connection manager with empty connection list."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """
        ✅ FIXED: Safe disconnect with error handling

        Args:
            websocket: WebSocket connection to disconnect
        """
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            logger.warning("Attempted to remove WebSocket that was not in active connections")

    async def send_message(self, message: dict):
        """
        Send message to all active WebSocket connections.
        Handles disconnections and runtime errors gracefully.
        """
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect as e:
                # ✅ FIXED: Handle WebSocket disconnection specifically
                logger.info(f"WebSocket disconnected during send: {e}")
                dead_connections.append(connection)
            except RuntimeError as e:
                # ✅ FIXED: Handle runtime errors (e.g., connection already closed)
                logger.warning(f"Runtime error sending to WebSocket: {e}")
                dead_connections.append(connection)
            except Exception as e:
                # ✅ FIXED: Catch any other unexpected errors
                logger.error(f"Unexpected error sending to WebSocket: {e}", exc_info=True)
                dead_connections.append(connection)

        # Remove dead connections
        for conn in dead_connections:
            try:
                self.active_connections.remove(conn)
            except ValueError:
                pass


manager = ConnectionManager()


# Startup/Shutdown events
@app.on_event("startup")
async def startup_event() -> None:
    """Log application startup"""
    logger.info("🚀 Screenshot Tool API starting up...")
    logger.info(f"📁 Output directory: {Path('screenshots').resolve()}")
    logger.info(f"🔐 Auth state file: {Path('auth_state.json').resolve()}")
    logger.info(f"🌐 CORS allowed origins: {settings.allowed_origins_list}")
    logger.info("💡 Performance docs auto-generate only when batch timeout changes")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Log application shutdown"""
    logger.info("🛑 Screenshot Tool API shutting down...")


# Routes
@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "name": "Screenshot Tool API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/system/usage")
async def system_usage() -> Dict:
    """Return backend, system and browser usage metrics for the desktop UI.

    This endpoint is intentionally lightweight and read-only. It is polled
    every few seconds by the frontend to render the status bar. Metrics are
    approximate but good enough for understanding load and making decisions
    about parallelism.
    """

    usage = _get_backend_resource_usage()
    if not usage:
        return {
            "status": "error",
            "message": "Resource usage unavailable on this platform",
            "timestamp": datetime.now().isoformat(),
        }

    usage.update(
        {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }
    )
    return usage


def _group_urls_by_domain(urls: List[str]) -> Dict[str, List[str]]:
    """
    Group URLs by domain for smart batch processing.

    Returns:
        Dict mapping domain to list of URLs
    """
    from urllib.parse import urlparse

    domain_groups = {}
    for url in urls:
        try:
            domain = urlparse(url).netloc
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(url)
        except Exception as e:  # ✅ FIXED: Log parsing failures instead of silent swallowing
            # If URL parsing fails, treat as unique domain
            logger.warning(f"⚠️  Failed to parse URL '{url}': {e} - treating as unique domain")
            domain_groups[url] = [url]

    return domain_groups


def _create_smart_batches(urls: List[str], enable_batch: bool = True, max_parallel: int = 5,
                          use_real_browser: bool = False, enable_rolling: bool = False) -> List[List[str]]:
    """
    Create smart batches based on domain detection and user settings.

    ✅ NEW BEHAVIOR (Cross-Text-Box Batching):
    - Frontend already batches URLs across text boxes (e.g., 5 URLs per batch)
    - Backend should process ALL URLs in the request in parallel (single batch)
    - This respects the frontend's batching strategy
    - max_parallel is used by Real Browser Mode to control browser tabs

    ✅ ROLLING PARALLELIZATION MODE:
    - When enable_rolling=True, ALL URLs are processed in a single batch
    - Semaphore controls concurrency (only max_parallel URLs run at once)
    - As soon as one URL finishes, the next URL starts immediately
    - This eliminates idle time between batches

    Args:
        urls: List of URLs to batch (already batched by frontend)
        enable_batch: Whether to enable batch processing
        max_parallel: Maximum parallel URLs (for Real Browser Mode tab control)
        use_real_browser: Whether using Real Browser Mode
        enable_rolling: Whether to enable rolling parallelization

    Returns:
        List of batches (each batch is a list of URLs)
    """
    if not enable_batch or not screenshot_service.ENABLE_BATCH_PROCESSING:
        # Sequential processing - one URL at a time
        return [[url] for url in urls]

    # ✅ ROLLING MODE: Process ALL URLs in a single batch with semaphore control
    # The semaphore ensures only max_parallel URLs run concurrently
    # As URLs complete, new ones start immediately (no idle time)
    if enable_rolling:
        logger.info(f"⚡ Rolling parallelization enabled: {len(urls)} URLs, {max_parallel} concurrent")
        return [urls]  # Single batch containing ALL URLs

    # ✅ FIXED BATCH MODE: Frontend already batched URLs across text boxes
    # Process all URLs in this request as a SINGLE batch
    # The frontend controls the batch size (e.g., 5 URLs per request)
    # The backend processes all URLs in the request in parallel

    return [urls]  # Single batch containing all URLs from frontend


async def _capture_single_url(
        url: str,
        request: URLRequest,
        request_id: str,
        index: int,
        total: int,
        semaphore: asyncio.Semaphore
) -> ScreenshotResult:
    """
    Capture a single URL with semaphore-based concurrency control.

    Args:
        url: URL to capture
        request: URLRequest with capture settings
        request_id: Unique request ID for cancellation tracking
        index: URL index (for progress reporting)
        total: Total number of URLs
        semaphore: Semaphore for limiting concurrent captures

    Returns:
        ScreenshotResult with capture outcome
    """
    async with semaphore:
        # ✅ NEW: Track processing time for this URL
        url_start_time = datetime.now()

        # Check cancellation before starting
        if cancellation_contexts[request_id]["cancelled"]:
            return ScreenshotResult(
                url=url,
                status="cancelled",
                error="Operation cancelled by user",
                timestamp=datetime.now().isoformat(),
                processing_time=0.0
            )

        try:
            # Send progress update
            await manager.send_message({
                "type": "progress",
                "current": index + 1,
                "total": total,
                "url": url,
                "status": "capturing",
                "request_id": request_id
            })

            # ✅ FIXED: Use per-request batch_timeout if provided, otherwise use mode-based defaults
            # Per-URL timeout is HALF of batch timeout to allow multiple URLs to complete within batch time
            if request.batch_timeout:
                capture_timeout = float(request.batch_timeout) / 2  # Half of batch timeout per URL
            elif request.use_real_browser:
                capture_timeout = 90.0  # Increased from 60s to 90s for height stabilization
            elif request.browser_engine == "camoufox":
                capture_timeout = 120.0  # Camoufox needs more time for first launch (downloads Firefox)
            elif request.use_stealth:
                capture_timeout = 90.0  # Increased for stealth mode
            elif request.capture_mode == "segmented":
                capture_timeout = 120.0
            else:
                capture_timeout = 35.0

            # Capture screenshot
            try:
                # ✅ NEW: Convert timeout to milliseconds for screenshot
                screenshot_timeout_ms = int(capture_timeout * 1000)

                if request.capture_mode == "segmented":
                    screenshot_paths = await asyncio.wait_for(
                        screenshot_service.capture_segmented(
                            url=url,
                            viewport_width=request.viewport_width,
                            viewport_height=request.viewport_height,
                            screenshot_timeout=screenshot_timeout_ms,  # ✅ NEW: Pass screenshot timeout
                            use_stealth=request.use_stealth,
                            use_real_browser=request.use_real_browser,
                            headless=request.headless,  # ✅ NEW: Pass headless mode setting
                            browser_engine=request.browser_engine,
                            base_url=request.base_url,
                            words_to_remove=request.words_to_remove,
                            cookies=request.cookies,
                            local_storage=request.local_storage,
                            overlap_percent=request.segment_overlap,
                            scroll_delay_ms=request.segment_scroll_delay,
                            max_segments=request.segment_max_segments,
                            skip_duplicates=request.segment_skip_duplicates,
                            smart_lazy_load=request.segment_smart_lazy_load,
                            track_network=request.track_network,  # ✅ NEW: Pass network tracking setting
                            auto_expand_dropdowns=request.auto_expand_dropdowns,
                            # ✅ NEW: Pass dropdown expansion setting
                            click_elements=request.click_elements,  # ✅ NEW: Pass click elements setting
                            non_scrollable_urls=request.non_scrollable_urls  # ✅ NEW: Pass non-scrollable URLs
                        ),
                        timeout=capture_timeout
                    )
                    screenshot_path = screenshot_paths[0] if screenshot_paths else None
                else:
                    full_page = request.capture_mode == "fullpage"
                    screenshot_path = await asyncio.wait_for(
                        screenshot_service.capture(
                            url=url,
                            viewport_width=request.viewport_width,
                            viewport_height=request.viewport_height,
                            full_page=full_page,
                            screenshot_timeout=screenshot_timeout_ms,  # ✅ NEW: Pass screenshot timeout
                            use_stealth=request.use_stealth,
                            use_real_browser=request.use_real_browser,
                            headless=request.headless,  # ✅ NEW: Pass headless mode setting
                            browser_engine=request.browser_engine,
                            base_url=request.base_url,
                            words_to_remove=request.words_to_remove,
                            cookies=request.cookies,
                            local_storage=request.local_storage,
                            track_network=request.track_network,  # ✅ NEW: Pass network tracking setting
                            auto_expand_dropdowns=request.auto_expand_dropdowns,
                            # ✅ NEW: Pass dropdown expansion setting
                            click_elements=request.click_elements,  # ✅ NEW: Pass click elements setting
                            non_scrollable_urls=request.non_scrollable_urls  # ✅ NEW: Pass non-scrollable URLs
                        ),
                        timeout=capture_timeout
                    )
                    screenshot_paths = None
            except asyncio.TimeoutError:
                raise CaptureTimeoutError(url=url, timeout_s=capture_timeout)

            # Check cancellation after capture
            if cancellation_contexts[request_id]["cancelled"]:
                raise CaptureCancelledError(url=url, request_id=request_id)

            # Quality check - ✅ MONOLITH: Direct call to quality checker
            quality_result = await check_quality_via_service(screenshot_path)

            # ✅ NEW: Calculate processing time
            url_end_time = datetime.now()
            processing_time = (url_end_time - url_start_time).total_seconds()

            return ScreenshotResult(
                url=url,
                status="success" if quality_result["passed"] else "failed",
                screenshot_path=screenshot_path,
                screenshot_paths=screenshot_paths,
                segment_count=len(screenshot_paths) if screenshot_paths else None,
                quality_score=quality_result["score"],
                quality_issues=quality_result["issues"],
                timestamp=datetime.now().isoformat(),
                processing_time=processing_time
            )

        except Exception as e:
            # ✅ NEW: Calculate processing time even for errors
            url_end_time = datetime.now()
            processing_time = (url_end_time - url_start_time).total_seconds()

            # Check if this was a cancellation
            if cancellation_contexts[request_id]["cancelled"] or "cancelled by user" in str(e).lower():
                return ScreenshotResult(
                    url=url,
                    status="cancelled",
                    error="Operation cancelled by user",
                    timestamp=datetime.now().isoformat(),
                    processing_time=processing_time
                )
            else:
                # 🔍 DEBUG: Log the actual error
                logger.error(f"❌ Screenshot failed for {url}: {str(e)}")
                logger.error(f"   Error type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")

                return ScreenshotResult(
                    url=url,
                    status="failed",
                    error=str(e),
                    timestamp=datetime.now().isoformat(),
                    processing_time=processing_time
                )


@app.post("/api/screenshots/capture")
async def capture_screenshots(request: URLRequest):
    """
    Capture screenshots for multiple URLs with smart batch processing.

    ⚡ OPTIMIZATION: Unlimited batch processing (process ALL URLs in parallel!)
    - Different domains: Process ALL URLs at once (unlimited batch size)
    - Same domain: Process ALL URLs at once (unlimited batch size)
    - Real Browser Mode: Sequential (1 at a time)
    - Feature flag: Set ENABLE_BATCH_PROCESSING = False to disable

    ✅ Backward compatible: Falls back to sequential if batch disabled
    """
    # ✅ FIXED: Create request-scoped cancellation flag with unique ID
    request_id = str(uuid4())
    cancellation_contexts[request_id] = {"cancelled": False}

    # ✅ FIXED: Log request start
    log_request_start(request_id, len(request.urls))
    start_time = datetime.now()

    # 🔍 DEBUG: Log base URL and words to remove
    logger.info(f"🔍 BASE URL RECEIVED: '{request.base_url}'")
    logger.info(f"🔍 WORDS TO REMOVE: '{request.words_to_remove}'")
    logger.info(f"🔍 URLS RECEIVED: {request.urls}")
    logger.info(f"🔍 AUTO EXPAND DROPDOWNS: {request.auto_expand_dropdowns}")  # ✅ DEBUG
    logger.info(f"🔍 NON-SCROLLABLE URLS: '{request.non_scrollable_urls}'")  # ✅ DEBUG: Non-scrollable URLs

    # ⚡ OPTIMIZATION: Create smart batches
    # Auto-detect: 1 URL = sequential, 2+ URLs = batch processing
    # This works in both Real Browser Mode and Headless Mode
    enable_batch = len(request.urls) > 1
    batches = _create_smart_batches(
        request.urls,
        enable_batch,
        max_parallel=request.max_parallel_urls,  # ✅ NEW: User-configurable
        use_real_browser=request.use_real_browser,
        enable_rolling=request.enable_rolling_parallelization  # ✅ NEW: Rolling parallelization
    )

    if enable_batch and screenshot_service.ENABLE_BATCH_PROCESSING:
        if request.enable_rolling_parallelization:
            logger.info(f"⚡ Rolling parallelization mode: {len(request.urls)} URLs, {request.max_parallel_urls} concurrent")
            logger.info(f"   🔄 URLs will start immediately as slots become available (no idle time)")
            if request.use_real_browser:
                logger.info(f"   🌐 Real Browser Mode: Up to {request.max_parallel_urls} tabs open at once")
        else:
            logger.info(f"⚡ Smart batch processing enabled: {len(batches)} batches for {len(request.urls)} URLs")
            if request.use_real_browser:
                logger.info(f"   🌐 Real Browser Mode: Will open up to {request.max_parallel_urls} tabs at once")
    else:
        logger.info(f"📋 Sequential processing: {len(request.urls)} URLs")

    try:
        results = []
        url_index = 0

        # Process each batch
        for batch_num, batch in enumerate(batches, 1):
            # Check cancellation before each batch
            if cancellation_contexts[request_id]["cancelled"]:
                break

            if len(batch) > 1:
                if request.enable_rolling_parallelization:
                    logger.info(f"🔄 Rolling mode: Processing {len(batch)} URLs ({request.max_parallel_urls} concurrent)...")
                else:
                    logger.info(f"🚀 Processing batch {batch_num}/{len(batches)} ({len(batch)} URLs in parallel)...")

            # Create tasks for this batch
            # ✅ FIX: Use max_parallel_urls setting to control concurrency, not batch size
            semaphore = asyncio.Semaphore(request.max_parallel_urls)
            batch_tasks = [
                _capture_single_url(
                    url, request, request_id,
                    url_index + i, len(request.urls),
                    semaphore  # Respect user's max_parallel_urls setting
                )
                for i, url in enumerate(batch)
            ]

            # Calculate timeout for this batch
            # ✅ ROLLING MODE: Scale timeout based on total URLs and concurrency
            # Formula: batch_timeout × (total_urls / max_parallel)
            # Example: 900s × (49 / 7) = 6300s (~105 minutes)
            if request.enable_rolling_parallelization:
                # Scale timeout proportionally to number of URLs
                scaling_factor = len(batch) / request.max_parallel_urls
                calculated_timeout = (request.batch_timeout if request.batch_timeout else 300) * scaling_factor
                # Cap at 2 hours (7200s) for safety
                batch_timeout_value = min(calculated_timeout, 7200)
                logger.info(f"   ⏱️  Rolling mode timeout: {batch_timeout_value:.0f}s (scaled for {len(batch)} URLs)")
            else:
                # Fixed batch mode: use batch_timeout as-is
                batch_timeout_value = request.batch_timeout if request.batch_timeout else 300

            # Execute batch in parallel with batch timeout
            # ✅ FIXED: Apply batch_timeout to ENTIRE batch, not per URL
            try:
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*batch_tasks),
                    timeout=batch_timeout_value
                )
                results.extend(batch_results)
                url_index += len(batch)
            except asyncio.TimeoutError:
                # Batch timed out - mark all URLs in batch as failed
                timeout_msg = f"Rolling mode timeout after {batch_timeout_value:.0f}s" if request.enable_rolling_parallelization else f"Batch timed out after {batch_timeout_value}s"
                for i, url in enumerate(batch):
                    results.append(ScreenshotResult(
                        url=url,
                        status="error",
                        error=timeout_msg,
                        timestamp=datetime.now().isoformat(),
                        processing_time=float(batch_timeout_value)
                    ))
                url_index += len(batch)

            # Send result updates for this batch
            for result in batch_results:
                await manager.send_message({
                    "type": "result",
                    "result": result.model_dump(),
                    "request_id": request_id
                })

        # ✅ NEW: Automatic retry for failed URLs (Real Browser Mode only)
        if request.use_real_browser:
            failed_urls = [r.url for r in results if r.status == "failed"]

            if failed_urls and not cancellation_contexts[request_id]["cancelled"]:
                logger.info(f"\n🔄 Retrying {len(failed_urls)} failed URLs...")

                # 🔧 FIX: Removed unused retry_results list
                for url in failed_urls:
                    # Check cancellation before each retry
                    if cancellation_contexts[request_id]["cancelled"]:
                        break

                    try:
                        logger.info(f"   🔄 Retrying: {url}")

                        # Retry the URL (one at a time for retries)
                        retry_result = await _capture_single_url(
                            url, request, request_id,
                            0, len(failed_urls),
                            asyncio.Semaphore(1)  # One at a time for retries
                        )

                        # Update original result in the results list directly
                        for i, r in enumerate(results):
                            if r.url == url:
                                results[i] = retry_result
                                break

                        # Log retry outcome
                        if retry_result.status == "success":
                            logger.info(f"   ✅ Retry succeeded: {url}")
                        else:
                            logger.info(f"   ❌ Retry failed: {url}")

                    except Exception as e:
                        logger.error(f"   ❌ Retry error for {url}: {e}")

                # Recalculate success count after retries
                success_count = sum(1 for r in results if r.status == "success")
                failed_count = sum(1 for r in results if r.status == "failed")

                logger.info(f"\n📊 Retry Summary:")
                logger.info(f"   ✅ Total successful: {success_count}/{len(request.urls)}")
                logger.info(f"   ❌ Still failed: {failed_count}/{len(request.urls)}")

                # ✅ NEW: Clean up tabs after retry completes
                try:
                    await screenshot_service.cleanup_tabs_after_batch()
                except Exception as e:
                    logger.error(f"⚠️  Error during tab cleanup: {e}")

        # ✅ FIXED: Log request completion
        duration = (datetime.now() - start_time).total_seconds()
        success_count = sum(1 for r in results if r.status == "success")
        log_request_complete(request_id, success_count, len(request.urls), duration)

        return {
            "results": results,
            "cancelled": cancellation_contexts[request_id]["cancelled"],
            "request_id": request_id
        }

    finally:
        # ✅ FIXED: Cleanup request-scoped cancellation flag
        cancellation_contexts.pop(request_id, None)


@app.post("/api/screenshots/capture-sequential")
async def capture_screenshots_sequential(request: URLRequest):
    """
    Capture screenshots for multiple URLs sequentially (legacy endpoint).
    Use /api/screenshots/capture for parallel processing.
    """
    # ✅ FIXED: Create request-scoped cancellation flag with unique ID
    request_id = str(uuid4())
    cancellation_contexts[request_id] = {"cancelled": False}

    # ✅ FIXED: Log request start
    log_request_start(request_id, len(request.urls))
    start_time = datetime.now()

    results = []

    try:
        for i, url in enumerate(request.urls):
            # Check if operation was cancelled
            if cancellation_contexts[request_id]["cancelled"]:
                # Add remaining URLs as cancelled
                for remaining_url in request.urls[i:]:
                    results.append(ScreenshotResult(
                        url=remaining_url,
                        status="cancelled",
                        error="Operation cancelled by user",
                        timestamp=datetime.now().isoformat()
                    ))

                # ✅ FIXED: Log cancellation
                log_cancellation(request_id, i, len(request.urls))

                # Send cancellation message
                await manager.send_message({
                    "type": "cancelled",
                    "message": "Screenshot capture cancelled",
                    "completed": i,
                    "total": len(request.urls),
                    "request_id": request_id
                })
                break

            try:
                # Send progress update
                await manager.send_message({
                    "type": "progress",
                    "current": i + 1,
                    "total": len(request.urls),
                    "url": url,
                    "status": "capturing",
                    "request_id": request_id
                })

                # Check cancellation before starting capture
                if cancellation_contexts[request_id]["cancelled"]:
                    raise CaptureCancelledError(url=url, request_id=request_id)

                # Capture screenshot with timeout
                # Use longer timeout for real browser mode and stealth mode (needs more time to load)
                if request.use_real_browser:
                    capture_timeout = 90.0  # Real browser mode - increased from 60s to 90s for height stabilization
                elif request.browser_engine == "camoufox":
                    capture_timeout = 120.0  # Camoufox needs more time for first launch (downloads Firefox)
                elif request.use_stealth:
                    capture_timeout = 90.0  # Stealth mode (Cloudflare challenges take time)
                elif request.capture_mode == "segmented":
                    capture_timeout = 120.0  # Segmented mode (needs more time for multiple captures)
                else:
                    capture_timeout = 35.0  # Normal headless mode

                try:
                    # Handle different capture modes
                    if request.capture_mode == "segmented":
                        # Segmented capture returns list of paths
                        screenshot_paths = await asyncio.wait_for(
                            screenshot_service.capture_segmented(
                                url=url,
                                viewport_width=request.viewport_width,
                                viewport_height=request.viewport_height,
                                screenshot_timeout=screenshot_timeout_ms,  # ✅ FIX: Add screenshot_timeout parameter
                                use_stealth=request.use_stealth,
                                use_real_browser=request.use_real_browser,
                                headless=request.headless,  # ✅ NEW: Pass headless mode setting
                                browser_engine=request.browser_engine,  # ✅ FIX: Add browser_engine parameter
                                base_url=request.base_url,
                                words_to_remove=request.words_to_remove,
                                cookies=request.cookies,
                                local_storage=request.local_storage,
                                overlap_percent=request.segment_overlap,
                                scroll_delay_ms=request.segment_scroll_delay,
                                max_segments=request.segment_max_segments,
                                skip_duplicates=request.segment_skip_duplicates,
                                smart_lazy_load=request.segment_smart_lazy_load,
                                track_network=request.track_network,  # ✅ FIX: Add track_network parameter
                                auto_expand_dropdowns=request.auto_expand_dropdowns,
                                # ✅ NEW: Pass dropdown expansion setting
                                click_elements=request.click_elements,  # ✅ FIX: Add click_elements parameter
                                non_scrollable_urls=request.non_scrollable_urls  # ✅ NEW: Pass non-scrollable URLs
                            ),
                            timeout=capture_timeout
                        )
                        screenshot_path = screenshot_paths[0] if screenshot_paths else None
                    else:
                        # Regular capture (viewport or fullpage)
                        full_page = request.capture_mode == "fullpage"
                        screenshot_path = await asyncio.wait_for(
                            screenshot_service.capture(
                                url=url,
                                viewport_width=request.viewport_width,
                                viewport_height=request.viewport_height,
                                full_page=full_page,
                                use_stealth=request.use_stealth,
                                use_real_browser=request.use_real_browser,
                                headless=request.headless,  # ✅ NEW: Pass headless mode setting
                                base_url=request.base_url,
                                words_to_remove=request.words_to_remove,
                                cookies=request.cookies,
                                local_storage=request.local_storage,
                                auto_expand_dropdowns=request.auto_expand_dropdowns,
                                # ✅ NEW: Pass dropdown expansion setting
                                non_scrollable_urls=request.non_scrollable_urls  # ✅ NEW: Pass non-scrollable URLs
                            ),
                            timeout=capture_timeout
                        )
                        screenshot_paths = None
                except asyncio.TimeoutError:
                    raise CaptureTimeoutError(url=url, timeout_s=capture_timeout)

                # Check cancellation after capture
                if cancellation_contexts[request_id]["cancelled"]:
                    raise CaptureCancelledError(url=url, request_id=request_id)

                # Quality check (use first screenshot for segmented mode) - ✅ MONOLITH
                quality_result = await check_quality_via_service(screenshot_path)

                result = ScreenshotResult(
                    url=url,
                    status="success" if quality_result["passed"] else "failed",
                    screenshot_path=screenshot_path,
                    screenshot_paths=screenshot_paths,
                    segment_count=len(screenshot_paths) if screenshot_paths else None,
                    quality_score=quality_result["score"],
                    quality_issues=quality_result["issues"],
                    timestamp=datetime.now().isoformat()
                )

            except Exception as e:
                # Check if this was a cancellation
                if cancellation_contexts[request_id]["cancelled"] or "cancelled by user" in str(e).lower():
                    result = ScreenshotResult(
                        url=url,
                        status="cancelled",
                        error="Operation cancelled by user",
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = ScreenshotResult(
                        url=url,
                        status="failed",
                        error=str(e),
                        timestamp=datetime.now().isoformat()
                    )

            results.append(result)

            # Send result update
            await manager.send_message({
                "type": "result",
                "result": result.model_dump(),
                "request_id": request_id
            })

        # ✅ FIXED: Log request completion
        duration = (datetime.now() - start_time).total_seconds()
        success_count = sum(1 for r in results if r.status == "success")
        log_request_complete(request_id, success_count, len(request.urls), duration)

        return {
            "results": results,
            "cancelled": cancellation_contexts[request_id]["cancelled"],
            "request_id": request_id
        }

    finally:
        # ✅ FIXED: Cleanup request-scoped cancellation flag
        cancellation_contexts.pop(request_id, None)


@app.post("/api/screenshots/cancel")
async def cancel_screenshots(request_id: Optional[str] = None):
    """Cancel ongoing screenshot capture operation"""
    # ✅ FIXED: Cancel specific request or all requests
    if request_id and request_id in cancellation_contexts:
        cancellation_contexts[request_id]["cancelled"] = True
        return {
            "status": "success",
            "message": f"Cancellation requested for request {request_id}"
        }
    elif not request_id:
        # Cancel all active requests (backward compatibility)
        for ctx in cancellation_contexts.values():
            ctx["cancelled"] = True
        return {
            "status": "success",
            "message": f"Cancellation requested for {len(cancellation_contexts)} active request(s)"
        }
    else:
        return {
            "status": "not_found",
            "message": "Request not found or already completed"
        }


@app.get("/api/screenshots/file/{file_path:path}")
async def get_screenshot_file(file_path: str):
    """Serve screenshot file for preview"""
    # ✅ FIXED: Validate path to prevent directory traversal
    validated_path = validate_screenshot_path(file_path)
    return FileResponse(str(validated_path))


@app.post("/api/screenshots/open-file")
async def open_file(path: str):
    """Open a screenshot file in the default image viewer"""
    import subprocess
    import platform

    # ✅ FIXED: Validate path to prevent directory traversal
    validated_path = validate_screenshot_path(path)

    try:
        # Open file based on OS
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(validated_path)])
        elif system == "Windows":
            os.startfile(str(validated_path))
        else:  # Linux
            subprocess.run(["xdg-open", str(validated_path)])

        return {"status": "success", "message": "File opened"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/screenshots/open-folder")
async def open_folder(path: str):
    """Open the folder containing the screenshot file"""
    import subprocess
    import platform

    # ✅ FIXED: Validate path to prevent directory traversal
    validated_path = validate_screenshot_path(path)
    folder_path = validated_path.parent

    try:
        # Open folder based on OS
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)])
        elif system == "Windows":
            os.startfile(str(folder_path))
        else:  # Linux
            subprocess.run(["xdg-open", str(folder_path)])

        return {"status": "success", "message": "Folder opened"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/screenshots/retry")
async def retry_screenshot(url: str, viewport_width: int = 1920, viewport_height: int = 1080):
    """Retry capturing a single screenshot"""
    try:
        screenshot_path = await screenshot_service.capture(
            url=url,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            full_page=True
        )

        # ✅ MONOLITH: Direct call to quality checker
        quality_result = await check_quality_via_service(screenshot_path)

        return ScreenshotResult(
            url=url,
            status="success" if quality_result["passed"] else "failed",
            screenshot_path=screenshot_path,
            quality_score=quality_result["score"],
            quality_issues=quality_result["issues"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return ScreenshotResult(
            url=url,
            status="failed",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/api/document/generate")
async def generate_document(request: DocumentRequest):
    """
    Generate Word document from screenshots
    ✅ MONOLITH: Direct call to local document service
    """
    try:
        logger.info(f"📄 Generating document with {len(request.screenshot_paths)} screenshots")

        # ✅ MONOLITH: Direct call to local document service
        # ✅ FIXED: Added await for async function call
        output_path = await document_service.generate(
            screenshot_paths=request.screenshot_paths,
            output_path=request.output_path,
            title=request.title
        )

        logger.info(f"✅ Document generated successfully: {output_path}")

        return {
            "status": "success",
            "output_path": output_path,
            "screenshot_count": len(request.screenshot_paths),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error generating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/update-batch-timeout")
async def update_batch_timeout(request: dict):
    """
    Update batch timeout in performance_metrics.py and regenerate docs
    Only regenerates if the value actually changed
    """
    try:
        timeout = request.get("timeout")
        if timeout is None:
            return {"status": "error", "message": "Missing timeout parameter"}

        # Validate timeout
        if not isinstance(timeout, (int, float)) or timeout < 10 or timeout > 300:
            return {"status": "error", "message": "Timeout must be between 10 and 300 seconds"}

        # Read current metrics
        from performance_metrics import metrics
        current_timeout = metrics.batch_timeout

        # Check if value changed
        if abs(current_timeout - timeout) < 0.1:  # Float comparison with tolerance
            logger.info(f"⏱️ Batch timeout unchanged ({timeout}s), skipping doc generation")
            return {
                "status": "success",
                "message": "Timeout unchanged, no update needed",
                "changed": False
            }

        # Update performance_metrics.py
        metrics_file = Path(__file__).parent / "performance_metrics.py"
        content = metrics_file.read_text()

        # Replace the batch_timeout value
        import re
        new_content = re.sub(
            r'batch_timeout:\s*float\s*=\s*[\d.]+',
            f'batch_timeout: float = {timeout}',
            content
        )

        metrics_file.write_text(new_content)
        logger.info(f"⏱️ Updated batch_timeout: {current_timeout}s → {timeout}s")

        # Regenerate documentation
        from generate_docs import main as generate_docs
        generate_docs(verbose=False)
        logger.info("📊 Performance documentation regenerated")

        return {
            "status": "success",
            "message": f"Batch timeout updated from {current_timeout}s to {timeout}s",
            "changed": True,
            "old_value": current_timeout,
            "new_value": timeout
        }

    except Exception as e:
        logger.error(f"❌ Failed to update batch timeout: {e}")
        return {"status": "error", "message": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time progress updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Storage state file path
STORAGE_STATE_FILE = Path("auth_state.json")


class LoginRequest(BaseModel):
    url: str
    browser_engine: str = "playwright"  # "playwright" or "camoufox"


@app.post("/api/auth/start-login")
async def start_login(request: LoginRequest):
    """
    ❌ DISABLED: Authentication features not needed for screenshot tool
    """
    return JSONResponse({
        "status": "disabled",
        "message": "Authentication features are disabled. This is a screenshot tool only.",
        "feature": "auth/start-login"
    }, status_code=501)


@app.get("/api/auth/status")
async def get_auth_status():
    """
    ❌ DISABLED: Authentication features not needed for screenshot tool
    """
    return JSONResponse({
        "status": "disabled",
        "message": "Authentication features are disabled. This is a screenshot tool only.",
        "feature": "auth/status",
        "exists": False
    }, status_code=501)


@app.delete("/api/auth/clear")
async def clear_auth_state():
    """
    ❌ DISABLED: Authentication features not needed for screenshot tool
    """
    return JSONResponse({
        "status": "disabled",
        "message": "Authentication features are disabled. This is a screenshot tool only.",
        "feature": "auth/clear"
    }, status_code=501)


@app.post("/api/auth/save-from-extension")
async def save_auth_from_extension(storage_state: dict):
    """
    ❌ DISABLED: Authentication features not needed for screenshot tool
    """
    return JSONResponse({
        "status": "disabled",
        "message": "Authentication features are disabled. This is a screenshot tool only.",
        "feature": "auth/save-from-extension"
    }, status_code=501)


@app.post("/api/network/export-curl")
async def export_network_events_as_curl(request: dict):
    """
    Export captured network events as cURL commands

    Request body:
    {
        "network_events": [...]  # Array of network events
    }

    Returns:
    {
        "success": true,
        "curl_commands": [...],
        "count": 5,
        "file": "/path/to/curl_commands.sh"
    }
    """
    try:
        network_events = request.get('network_events', [])

        if not network_events:
            return {
                "success": False,
                "error": "No network events provided"
            }

        # Convert to cURL commands
        curl_commands = screenshot_service._convert_network_events_to_curl(network_events)

        if not curl_commands:
            return {
                "success": False,
                "error": "No API calls found in network events"
            }

        # Save to file
        curl_file = Path("screenshots/curl_commands.sh")
        curl_file.parent.mkdir(exist_ok=True)

        with open(curl_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# cURL commands exported from network events\n")
            f.write("# Generated by Screenshot Tool\n\n")
            for i, curl in enumerate(curl_commands, 1):
                f.write(f"# Request {i}\n")
                f.write(f"{curl}\n\n")

        return {
            "success": True,
            "curl_commands": curl_commands,
            "count": len(curl_commands),
            "file": str(curl_file)
        }

    except Exception as e:
        logger.error(f"❌ Export cURL error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/restart")
async def restart_backend():
    """
    Restart the backend server
    This endpoint triggers a server restart by touching the main.py file,
    which causes uvicorn's reload feature to restart the server.
    """
    try:
        import sys
        import signal

        logger.info("🔄 Backend restart requested")

        # Touch the main.py file to trigger uvicorn reload
        main_file = Path(__file__)
        main_file.touch()

        logger.info("✅ Backend restart triggered")

        return JSONResponse({
            "status": "success",
            "message": "Backend is restarting..."
        })
    except Exception as e:
        logger.error(f"❌ Failed to restart backend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/url-configs")
async def get_url_configs():
    """
    Get all URL-specific click configurations
    """
    try:
        config_file = Path("url_click_config.json")

        if not config_file.exists():
            # Return default empty configuration
            return {
                "version": "1.0",
                "description": "URL-specific click action configurations for screenshot tool",
                "url_patterns": []
            }

        with open(config_file, 'r') as f:
            config = json.load(f)

        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/url-configs")
async def create_url_config(config: dict):
    """
    Create a new URL-specific click configuration

    Request body:
    {
        "id": "unique-id",
        "name": "Configuration Name",
        "url_pattern": "https://example.com/page",
        "match_type": "exact",
        "actions": [
            {
                "type": "click",
                "text": "Button Text",
                "wait_after_ms": 2000,
                "description": "Optional description"
            }
        ],
        "enabled": true,
        "notes": "Optional notes"
    }
    """
    try:
        config_file = Path("url_click_config.json")

        # Load existing configuration
        if config_file.exists():
            with open(config_file, 'r') as f:
                full_config = json.load(f)
        else:
            full_config = {
                "version": "1.0",
                "description": "URL-specific click action configurations for screenshot tool",
                "url_patterns": []
            }

        # Check if ID already exists
        existing_ids = [p.get("id") for p in full_config.get("url_patterns", [])]
        if config.get("id") in existing_ids:
            raise HTTPException(status_code=400, detail=f"Configuration with ID '{config.get('id')}' already exists")

        # Add new configuration
        full_config["url_patterns"].append(config)

        # Save to file
        with open(config_file, 'w') as f:
            json.dump(full_config, f, indent=2)

        # Reload configuration in screenshot service
        screenshot_service.url_click_config = screenshot_service._load_url_click_config()

        return {"status": "success", "message": "Configuration created successfully", "config": config}
    except Exception as e:
        # ✅ FIXED: Removed redundant HTTPException re-raise for consistency
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/url-configs/{config_id}")
async def update_url_config(config_id: str, config: dict):
    """
    Update an existing URL-specific click configuration
    """
    try:
        config_file = Path("url_click_config.json")

        if not config_file.exists():
            raise HTTPException(status_code=404, detail="Configuration file not found")

        # Load existing configuration
        with open(config_file, 'r') as f:
            full_config = json.load(f)

        # Find and update configuration
        found = False
        for i, pattern in enumerate(full_config.get("url_patterns", [])):
            if pattern.get("id") == config_id:
                full_config["url_patterns"][i] = config
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail=f"Configuration with ID '{config_id}' not found")

        # Save to file
        with open(config_file, 'w') as f:
            json.dump(full_config, f, indent=2)

        # Reload configuration in screenshot service
        screenshot_service.url_click_config = screenshot_service._load_url_click_config()

        return {"status": "success", "message": "Configuration updated successfully", "config": config}
    except Exception as e:
        # ✅ FIXED: Removed redundant HTTPException re-raise for consistency
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/url-configs/{config_id}")
async def delete_url_config(config_id: str):
    """
    Delete a URL-specific click configuration
    """
    try:
        config_file = Path("url_click_config.json")

        if not config_file.exists():
            raise HTTPException(status_code=404, detail="Configuration file not found")

        # Load existing configuration
        with open(config_file, 'r') as f:
            full_config = json.load(f)

        # Find and remove configuration
        original_length = len(full_config.get("url_patterns", []))
        full_config["url_patterns"] = [
            p for p in full_config.get("url_patterns", [])
            if p.get("id") != config_id
        ]

        if len(full_config["url_patterns"]) == original_length:
            raise HTTPException(status_code=404, detail=f"Configuration with ID '{config_id}' not found")

        # Save to file
        with open(config_file, 'w') as f:
            json.dump(full_config, f, indent=2)

        # Reload configuration in screenshot service
        screenshot_service.url_click_config = screenshot_service._load_url_click_config()

        return {"status": "success", "message": "Configuration deleted successfully"}
    except Exception as e:
        # ✅ FIXED: Removed redundant HTTPException re-raise for consistency
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/launch-debug-chrome")
async def launch_debug_chrome():
    """
    Launch Chrome with remote debugging enabled
    This endpoint runs the launcher script that opens Chrome with all profiles
    """
    try:
        import subprocess
        import os

        logger.info("🔴 Debug Chrome launch requested")

        # ✅ PHASE 1 (Path Security): Validate launcher path
        launcher_path_str = os.path.expanduser(
            "~/Library/Application Support/Google/Chrome-Debug/🔴 CLICK HERE TO LAUNCH DEBUG CHROME.command"
        )

        expected_base = Path.home() / "Library" / "Application Support" / "Google" / "Chrome-Debug"

        try:
            launcher_path = PathSecurityValidator.validate_path(
                path=launcher_path_str,
                base_dir=expected_base,
                must_exist=True,
                allow_symlinks=False,
                allowed_extensions={".command"},
            )
        except PathValidationError as e:
            logger.error(f"❌ Launcher path validation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid launcher path: {e}"
            )

        # Additional check: must be a file
        if not launcher_path.is_file():
            logger.error(f"❌ Launcher path is not a file: {launcher_path}")
            raise HTTPException(
                status_code=400,
                detail="Launcher path must be a file"
            )

        # Check if Chrome is already running with remote debugging
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 9222))
            sock.close()

            if result == 0:
                logger.info("✅ Chrome already running with remote debugging on port 9222")
                return JSONResponse({
                    "status": "already_running",
                    "message": "Chrome is already running with remote debugging enabled",
                    "port": 9222
                })
        except Exception as e:
            logger.warning(f"⚠️ Error checking Chrome status: {str(e)}")

        # Launch Chrome in background
        logger.info(f"🚀 Launching debug Chrome from: {launcher_path}")

        # Run the launcher script in background (use str() for subprocess)
        subprocess.Popen(
            ["bash", str(launcher_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        logger.info("✅ Debug Chrome launch command sent")

        return JSONResponse({
            "status": "success",
            "message": "Debug Chrome is launching...",
            "port": 9222
        })

    except Exception as e:
        # ✅ FIXED: Removed redundant HTTPException re-raise for consistency
        logger.error(f"❌ Failed to launch debug Chrome: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/launch-brave-cdp")
async def launch_brave_cdp():
    """Ensure Brave is running with CDP on port 9223 using the *real* profile.

    Behaviour (non-interactive, safe for use from the desktop app):
    - If *anything* is already listening on localhost:9223 ->
        return status="already_running" and do nothing.
    - Otherwise:
        - Close all existing Brave instances.
        - Launch a NEW Brave instance with Chrome DevTools Protocol (CDP) enabled on 9223,
          using the user's real Brave profile directory.
    """

    try:
        import os
        import socket
        import subprocess
        import time

        logger.info("🦁 Brave CDP launch requested")

        # Helper: check if port 9223 is already open
        def _is_cdp_up() -> bool:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    result = sock.connect_ex(("localhost", 9223))
                finally:
                    sock.close()
                return result == 0
            except Exception as e:
                logger.warning(f"⚠️ Error checking CDP port 9223: {str(e)}")
                return False

        # 1) If CDP already up, don't touch anything
        if _is_cdp_up():
            logger.info("✅ CDP already running on port 9223")
            return JSONResponse(
                {
                    "status": "already_running",
                    "message": "A browser is already exposing CDP on port 9223",
                    "port": 9223,
                }
            )

        # 2) Prepare Brave paths (macOS)
        # ✅ PHASE 1 (Path Security): Validate browser executable path
        brave_path_str = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

        try:
            brave_path = PathSecurityValidator.validate_path(
                path=brave_path_str,
                base_dir=Path("/Applications"),
                must_exist=True,
                allow_symlinks=False,
            )
        except PathValidationError as e:
            logger.error(f"❌ Brave path validation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid browser path: {e}"
            )

        # Additional check: must be a file
        if not brave_path.is_file():
            logger.error(f"❌ Brave path is not a file: {brave_path}")
            raise HTTPException(
                status_code=400,
                detail="Browser path must be a file"
            )

        # ✅ PHASE 1 (Path Security): Validate user data directory
        user_data_dir = os.path.expanduser(
            "~/Library/Application Support/BraveSoftware/Brave-Browser"
        )

        try:
            user_data_path = PathSecurityValidator.validate_directory_creation(
                path=user_data_dir,
                allowed_parent=Path.home(),
                max_depth=10,
            )
        except PathValidationError as e:
            logger.error(f"❌ User data dir validation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid user data directory: {e}"
            )

        # ✅ FIX: Close existing Brave instances before launching with CDP
        logger.info("🔄 Closing existing Brave instances...")
        try:
            subprocess.run(
                ["killall", "Brave Browser"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            logger.info("✅ Closed existing Brave instances")
            time.sleep(1)  # Give it a moment to fully close
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ killall command timed out")
        except Exception as e:
            logger.warning(f"⚠️ Error closing Brave (may not be running): {str(e)}")

        logger.info("🚀 Launching Brave with CDP on port 9223")

        # 3) Launch Brave with the real profile and CDP flags on port 9223
        cmd = [
            str(brave_path),  # ✅ FIXED: Convert Path to str for subprocess
            "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=9223",  # ✅ Changed from 9222 to 9223
            f"--user-data-dir={user_data_dir}",
        ]

        logger.info(f"🚀 Launching Brave with CDP: {' '.join(cmd)}")

        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # 4) Poll for a few seconds for CDP to come up
        for i in range(10):  # up to ~10 seconds
            time.sleep(1)
            if _is_cdp_up():
                logger.info("✅ Brave CDP is UP on port 9223 after launch")
                return JSONResponse(
                    {
                        "status": "launched",
                        "message": "Brave has been launched with CDP enabled on port 9223",
                        "port": 9223,
                    }
                )

        # If we get here, we sent the launch command but port 9223 never opened
        logger.warning(
            "⚠️ Brave CDP launch command sent, but port 9223 is still not accepting connections"
        )
        return JSONResponse(
            {
                "status": "launching",
                "message": "Requested Brave CDP launch, but port 9223 is not yet reachable.",
                "port": 9223,
            }
        )

    except Exception as e:
        # ✅ FIXED: Removed redundant HTTPException re-raise for consistency
        logger.error(f"❌ Failed to launch Brave CDP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cdp-status")
async def get_cdp_status():
    """Check whether something is exposing CDP on localhost:9223.

    Returns a simple JSON payload with the port and a boolean flag.
    """

    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 9223))  # ✅ Changed from 9222 to 9223
        sock.close()

        is_listening = result == 0
        logger.info(
            f"CDP status check on 9223: {'UP' if is_listening else 'DOWN'} (code={result})"
        )

        return {
            "port": 9223,  # ✅ Changed from 9222 to 9223
            "is_listening": is_listening,
        }

    except Exception as e:
        logger.error(f"❌ Failed to check CDP status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/paths")
async def get_file_paths():
    """
    Get current file path configuration
    """
    return {
        "screenshots_dir": str(settings.screenshots_dir),
        "screenshots_dir_absolute": str(settings.screenshots_dir.resolve()),
        "browser_sessions_dir": str(settings.browser_sessions_dir),
        "auth_state_file": str(settings.auth_state_file),
    }


# ✅ PHASE 4: Security audit endpoints
@app.get("/api/security/audit-events")
async def get_security_audit_events(
    event_type: Optional[str] = None,
    limit: int = 100
):
    """
    Get recent security audit events

    Query parameters:
    - event_type: Filter by event type (optional)
    - limit: Maximum number of events (default: 100, max: 1000)
    """
    limit = min(limit, 1000)  # Cap at 1000
    events = PathSecurityValidator.get_audit_events(event_type=event_type, limit=limit)
    return {
        "events": events,
        "count": len(events),
        "event_type_filter": event_type
    }


@app.get("/api/security/audit-summary")
async def get_security_audit_summary():
    """Get summary statistics of security audit events"""
    summary = PathSecurityValidator.get_audit_summary()
    return summary


@app.delete("/api/security/audit-events")
async def clear_security_audit_events():
    """Clear all security audit events"""
    count = PathSecurityValidator.clear_audit_events()
    return {
        "status": "success",
        "events_cleared": count
    }




@app.post("/api/config/paths")
async def update_file_paths(paths: dict):
    """
    Update file path configuration

    Request body:
    {
        "screenshots_dir": "screenshots" or "~/Desktop/My Screenshots"
    }
    """
    try:
        if "screenshots_dir" in paths:
            # ✅ PHASE 1 (Path Security): Validate user-controlled directory path
            user_input = paths["screenshots_dir"]

            # Validate directory creation with security checks
            validated_dir = PathSecurityValidator.validate_directory_creation(
                path=user_input,
                allowed_parent=Path.home(),
                max_depth=10,
            )

            # Create directory with restricted permissions
            validated_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

            # Update the service's output directory
            screenshot_service.output_dir = validated_dir

            logger.info(f"📁 Updated screenshots directory to: {validated_dir}")

            return {
                "status": "success",
                "screenshots_dir": str(validated_dir),
                "screenshots_dir_absolute": str(validated_dir.resolve())
            }

        return {"status": "error", "message": "No valid paths provided"}

    except PathValidationError as e:
        logger.error(f"Path validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update file paths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 🌐 API EXTRACTION ENDPOINTS
# ========================================

class APIExtractionRequest(BaseModel):
    """Request model for API extraction"""
    url: str
    api_url_pattern: str
    auto_generate_metadata: bool = True
    existing_metadata: Optional[dict] = None
    timeout_ms: int = 30000


class APIExtractionResult(BaseModel):
    """Response model for API extraction"""
    api_url: str
    method: str
    status: int
    timestamp: str
    metadata: dict
    extracted_fields: dict
    raw_response: Optional[dict] = None


# ========================================
# 🌐 API PROXY (POSTMAN-LIKE) MODELS
# ========================================

class ProxyRequest(BaseModel):
    """Request model for API proxy - Postman-like functionality"""
    url: str = Field(..., description="Target API URL")
    method: str = Field("GET", description="HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    body: Optional[str] = Field(None, description="Request body (JSON string or raw text)")
    pre_request_script: Optional[str] = Field(None, description="JavaScript to run before request")
    post_response_script: Optional[str] = Field(None, description="JavaScript to run after response")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")


class ProxyResponse(BaseModel):
    """Response model for API proxy"""
    status: int
    status_text: str
    headers: Dict[str, str]
    body: str
    json: Optional[dict] = None
    size: int
    time: float  # milliseconds


@app.post("/api/proxy-request")
async def proxy_api_request(request: ProxyRequest):
    """
    🌐 API Proxy - Postman-like functionality

    Proxies API requests to bypass CORS restrictions.
    Supports all HTTP methods, custom headers, and request/response scripts.

    This is the core endpoint for the Business Apps API Testing tool.
    """
    import time as time_module

    try:
        logger.info(f"🌐 Proxying {request.method} request to: {request.url}")
        logger.info(f"📋 Headers count: {len(request.headers) if request.headers else 0}")
        logger.info(f"📦 Body size: {len(request.body) if request.body else 0} bytes")

        # Log body preview for debugging
        if request.body:
            logger.info(f"📄 Body preview: {request.body[:500]}")

        # Start timing
        start_time = time_module.time()

        # TODO: Execute pre-request script (Phase 2)
        # For now, we'll skip script execution and implement it in next iteration

        # Prepare request headers (convert to dict for httpx)
        headers = dict(request.headers) if request.headers else {}

        # Log headers before modification
        header_keys_lower = {k.lower() for k in headers.keys()}
        logger.info(f"📋 Received headers: {list(headers.keys())[:10]}...")  # Show first 10
        logger.info(f"🔍 Has content-type: {'content-type' in header_keys_lower}")

        # CRITICAL FIX: Ensure Content-Type is set for requests with body
        # HTTP 415 (Unsupported Media Type) occurs when this header is missing or wrong
        if request.body:
            if 'content-type' not in header_keys_lower:
                headers['Content-Type'] = 'application/json'
                logger.warning("⚠️ Added missing Content-Type: application/json header")
            else:
                # Find the actual key (could be 'Content-Type' or 'content-type')
                actual_ct_key = next((k for k in headers.keys() if k.lower() == 'content-type'), None)
                if actual_ct_key:
                    logger.info(f"✅ Content-Type already present: {headers[actual_ct_key]}")

        # Prepare request body
        body_content = None
        if request.body:
            body_content = request.body.encode('utf-8')

        # Make the proxied request
        async with httpx.AsyncClient(timeout=request.timeout, follow_redirects=True) as client:
            response = await client.request(
                method=request.method.upper(),
                url=request.url,
                headers=headers,
                content=body_content
            )

        # Calculate response time
        elapsed_ms = (time_module.time() - start_time) * 1000

        logger.info(f"📥 Response: {response.status_code} ({elapsed_ms:.0f}ms)")
        logger.info(f"📊 Response size: {len(response.content)} bytes")

        # Parse response body
        response_body = response.text
        response_json = None

        # Try to parse as JSON
        try:
            response_json = response.json()
            # Log error responses for debugging
            if response.status_code >= 400:
                logger.error(f"❌ Error response JSON: {response_json}")
        except Exception:
            # Not JSON, that's okay
            if response.status_code >= 400:
                logger.error(f"❌ Error response (non-JSON): {response_body[:500]}")

        # TODO: Execute post-response script (Phase 2)

        # Build response
        result = ProxyResponse(
            status=response.status_code,
            status_text=response.reason_phrase or str(response.status_code),
            headers=dict(response.headers),
            body=response_body,
            json=response_json,
            size=len(response.content),
            time=round(elapsed_ms, 2)
        )

        if response.status_code >= 400:
            logger.warning(f"⚠️ Proxy request completed with error: {response.status_code} in {elapsed_ms:.2f}ms")
        else:
            logger.info(f"✅ Proxy request completed: {response.status_code} in {elapsed_ms:.2f}ms")

        return result

    except httpx.TimeoutException as e:
        logger.error(f"❌ Proxy request timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail=f"Request timeout after {request.timeout}s"
        )
    except httpx.RequestError as e:
        logger.error(f"❌ Proxy request failed: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Proxy error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected proxy error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


# ========================================
# 🎯 PRIORITY CODE SYNC ENDPOINT
# ========================================

class PriorityCodeSyncResponse(BaseModel):
    """Response from priority code synchronization"""
    success: bool
    total_existing: int
    required_codes: List[str]
    deleted_codes: List[dict]
    created_codes: List[dict]
    failed_deletes: List[dict]
    failed_creates: List[dict]
    kept_codes: List[str]
    summary: str


@app.post("/api/priority-code/sync", response_model=PriorityCodeSyncResponse)
async def sync_priority_codes(request: Request):
    """
    🎯 Priority Code Synchronization

    Ensures exactly 5 required priority codes exist:
    - SPAC: Back Order Part Order
    - STK: Stock Order
    - KEY: Key Order
    - OVN: Over Night Order
    - CSO: Customer Order (default)

    Workflow:
    1. GET existing codes
    2. Soft-delete codes not in required list (SEQUENTIAL)
    3. Create missing required codes (SEQUENTIAL)

    Returns detailed summary of all operations.

    Note: This endpoint receives headers via HTTP request headers
    (forwarded by /api/proxy-request).
    """
    try:
        logger.info("=" * 80)
        logger.info("🎯 PRIORITY CODE SYNC - START")
        logger.info("=" * 80)

        # Define required codes
        REQUIRED_CODES = [
            {"code": "SPAC", "description": "Back Order Part Order", "default": False},
            {"code": "STK", "description": "Stock Order", "default": False},
            {"code": "KEY", "description": "Key Order", "default": False},
            {"code": "OVN", "description": "Over Night Order", "default": False},
            {"code": "CSO", "description": "Customer Order", "default": True}
        ]

        logger.info(f"📋 Required codes: {[c['code'] for c in REQUIRED_CODES]}")

        # Extract Tekion headers from incoming HTTP request headers
        # The /api/proxy-request endpoint forwards headers from the frontend
        tekion_headers = dict(request.headers)
        logger.info(f"📨 Received {len(tekion_headers)} total headers (including infrastructure)")

        # Remove FastAPI/infrastructure headers, keep only Tekion headers
        headers_to_remove = ['host', 'user-agent', 'accept-encoding', 'connection', 'content-length', 'content-type']
        for header in headers_to_remove:
            tekion_headers.pop(header, None)

        if not tekion_headers or len(tekion_headers) < 5:
            logger.error(f"❌ SYNC FAILED: Insufficient headers received: {len(tekion_headers)} headers")
            raise HTTPException(
                status_code=400,
                detail=f"No Tekion headers provided. Please ensure unified headers are configured in Parts Tab. Received: {list(tekion_headers.keys())}"
            )

        logger.info(f"✅ Validated {len(tekion_headers)} Tekion headers")
        logger.info(f"🔑 Key headers: dealerid={tekion_headers.get('dealerid')}, tenantname={tekion_headers.get('tenantname')}, userid={tekion_headers.get('userid')[:8]}...")

        base_url = "https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/priority-code"
        logger.info(f"🌐 Target API: {base_url}")

        # STEP 1: GET existing priority codes
        logger.info("")
        logger.info("─" * 80)
        logger.info("📥 STEP 1: FETCH EXISTING PRIORITY CODES")
        logger.info("─" * 80)
        logger.info(f"🌐 GET {base_url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            get_response = await client.get(base_url, headers=tekion_headers)

            logger.info(f"📥 Response status: {get_response.status_code}")
            logger.info(f"📊 Response size: {len(get_response.content)} bytes")

            if get_response.status_code != 200:
                logger.error(f"❌ FETCH FAILED: Status {get_response.status_code}")
                logger.error(f"📄 Error response: {get_response.text[:500]}")
                raise HTTPException(
                    status_code=get_response.status_code,
                    detail=f"Failed to fetch priority codes: {get_response.text}"
                )

            try:
                response_data = get_response.json()
                logger.info(f"📊 Response type: {type(response_data)}")
                logger.info(f"📄 Response preview: {str(response_data)[:300]}")

                # Handle both direct array and wrapped response
                if isinstance(response_data, list):
                    existing_codes = response_data
                elif isinstance(response_data, dict):
                    # Common API patterns: {"data": [...]} or {"results": [...]} or {"priorityCodes": [...]}
                    if "data" in response_data:
                        existing_codes = response_data["data"]
                    elif "results" in response_data:
                        existing_codes = response_data["results"]
                    elif "priorityCodes" in response_data:
                        existing_codes = response_data["priorityCodes"]
                    elif "items" in response_data:
                        existing_codes = response_data["items"]
                    else:
                        # Log all keys to help debug
                        logger.error(f"❌ Response is dict but no known wrapper key found. Keys: {list(response_data.keys())}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Unexpected response structure. Keys: {list(response_data.keys())[:10]}"
                        )
                else:
                    logger.error(f"❌ Expected list or dict, got {type(response_data)}: {str(response_data)[:200]}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid response type from Tekion API: {type(response_data).__name__}"
                    )

                # Validate that we now have a list
                if not isinstance(existing_codes, list):
                    logger.error(f"❌ After unwrapping, expected list, got {type(existing_codes)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid data structure: expected list, got {type(existing_codes).__name__}"
                    )

                logger.info(f"✅ Successfully fetched {len(existing_codes)} existing priority codes")
                if existing_codes:
                    sample_codes = [c.get('code', 'N/A') for c in existing_codes[:5] if isinstance(c, dict)]
                    logger.info(f"📋 Sample codes: {sample_codes}{' ...' if len(existing_codes) > 5 else ''}")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Failed to parse JSON response: {e}")
                logger.error(f"📄 Response text: {get_response.text[:500]}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse Tekion API response: {str(e)}"
                )

        # STEP 2: Identify codes to delete
        logger.info("")
        logger.info("─" * 80)
        logger.info("🔍 STEP 2: ANALYZE EXISTING CODES")
        logger.info("─" * 80)

        required_code_strings = [c["code"] for c in REQUIRED_CODES]
        logger.info(f"📋 Required codes: {required_code_strings}")

        unwanted_codes = [
            c for c in existing_codes
            if isinstance(c, dict) and c.get("code") not in required_code_strings and not c.get("deleted", False)
        ]

        kept_codes = [
            c["code"] for c in existing_codes
            if isinstance(c, dict) and c.get("code") in required_code_strings and not c.get("deleted", False)
        ]

        already_deleted = [
            c["code"] for c in existing_codes
            if isinstance(c, dict) and c.get("deleted", False)
        ]

        logger.info(f"✅ Keeping {len(kept_codes)} required codes: {kept_codes}")
        logger.info(f"⚠️ Found {len(unwanted_codes)} unwanted codes to delete: {[c['code'] for c in unwanted_codes if isinstance(c, dict)]}")
        if already_deleted:
            logger.info(f"🗑️ Already deleted: {already_deleted}")

        # STEP 3: Soft-delete unwanted codes (SEQUENTIAL)
        logger.info("")
        logger.info("─" * 80)
        logger.info("🗑️ STEP 3: DELETE UNWANTED CODES (SEQUENTIAL)")
        logger.info("─" * 80)

        deleted_codes = []
        failed_deletes = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            if unwanted_codes:
                logger.info(f"🔄 Processing {len(unwanted_codes)} deletions sequentially...")
            else:
                logger.info("✅ No unwanted codes to delete")

            for idx, unwanted in enumerate(unwanted_codes, 1):
                delete_url = f"{base_url}/{unwanted['id']}"
                delete_body = {
                    "id": unwanted["id"],
                    "priorityCode": unwanted["code"],  # API uses 'priorityCode' not 'code'
                    "description": unwanted["description"],
                    "isDefault": unwanted.get("default", False),  # API uses 'isDefault'
                    "deleted": True
                }

                logger.info(f"🗑️ [{idx}/{len(unwanted_codes)}] Deleting '{unwanted['code']}' (ID: {unwanted['id'][:8]}...)")
                logger.info(f"   🌐 PUT {delete_url}")

                try:
                    delete_response = await client.put(
                        delete_url,
                        json=delete_body,
                        headers=tekion_headers,
                        timeout=10.0
                    )

                    logger.info(f"   📥 Response: {delete_response.status_code}")

                    if delete_response.status_code in [200, 201, 204]:
                        deleted_codes.append({
                            "id": unwanted["id"],
                            "code": unwanted["code"],
                            "description": unwanted["description"]
                        })
                        logger.info(f"   ✅ Successfully deleted '{unwanted['code']}'")
                    else:
                        error_msg = delete_response.text[:200]
                        failed_deletes.append({
                            "code": unwanted["code"],
                            "status": delete_response.status_code,
                            "error": error_msg
                        })
                        logger.error(f"   ❌ Failed: {delete_response.status_code} - {error_msg}")

                except httpx.TimeoutError:
                    failed_deletes.append({
                        "code": unwanted["code"],
                        "error": "Timeout after 10s"
                    })
                    logger.error(f"   ❌ Timeout after 10s")

                except Exception as e:
                    failed_deletes.append({
                        "code": unwanted["code"],
                        "error": str(e)[:200]
                    })
                    logger.error(f"   ❌ Exception: {e}")

            if unwanted_codes:
                logger.info(f"📊 Delete summary: {len(deleted_codes)} succeeded, {len(failed_deletes)} failed")

        # STEP 4: Identify missing required codes
        logger.info("")
        logger.info("─" * 80)
        logger.info("🔍 STEP 4: IDENTIFY MISSING CODES")
        logger.info("─" * 80)

        existing_active_codes = [
            c["code"] for c in existing_codes
            if isinstance(c, dict) and not c.get("deleted", False)
        ]

        missing_codes = [
            c for c in REQUIRED_CODES
            if c["code"] not in existing_active_codes
        ]

        logger.info(f"📊 Existing active codes: {existing_active_codes}")
        logger.info(f"➕ Missing codes to create: {[c['code'] for c in missing_codes]}")

        # STEP 5: Create missing codes (SEQUENTIAL)
        logger.info("")
        logger.info("─" * 80)
        logger.info("➕ STEP 5: CREATE MISSING CODES (SEQUENTIAL)")
        logger.info("─" * 80)

        created_codes = []
        failed_creates = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            if missing_codes:
                logger.info(f"🔄 Processing {len(missing_codes)} creations sequentially...")
            else:
                logger.info("✅ No missing codes to create - all required codes exist")

            for idx, missing in enumerate(missing_codes, 1):
                create_body = {
                    "code": missing["code"],  # API uses 'code' for POST
                    "description": missing["description"]
                }

                logger.info(f"➕ [{idx}/{len(missing_codes)}] Creating '{missing['code']}' ({missing['description']})")
                logger.info(f"   🌐 POST {base_url}")

                try:
                    create_response = await client.post(
                        base_url,
                        json=create_body,
                        headers=tekion_headers,
                        timeout=10.0
                    )

                    logger.info(f"   📥 Response: {create_response.status_code}")

                    if create_response.status_code in [200, 201]:
                        response_data = create_response.json()
                        created_id = response_data.get("id", "unknown")
                        created_codes.append({
                            "code": missing["code"],
                            "description": missing["description"],
                            "id": created_id
                        })
                        logger.info(f"   ✅ Successfully created '{missing['code']}' (ID: {created_id[:8] if created_id != 'unknown' else 'unknown'}...)")
                    else:
                        error_msg = create_response.text[:200]
                        failed_creates.append({
                            "code": missing["code"],
                            "status": create_response.status_code,
                            "error": error_msg
                        })
                        logger.error(f"   ❌ Failed: {create_response.status_code} - {error_msg}")

                except httpx.TimeoutError:
                    failed_creates.append({
                        "code": missing["code"],
                        "error": "Timeout after 10s"
                    })
                    logger.error(f"   ❌ Timeout after 10s")

                except Exception as e:
                    failed_creates.append({
                        "code": missing["code"],
                        "error": str(e)[:200]
                    })
                    logger.error(f"   ❌ Exception: {e}")

            if missing_codes:
                logger.info(f"📊 Create summary: {len(created_codes)} succeeded, {len(failed_creates)} failed")

        # STEP 6: Build final summary
        logger.info("")
        logger.info("─" * 80)
        logger.info("📊 STEP 6: FINAL SUMMARY")
        logger.info("─" * 80)

        kept_codes = [
            c["code"] for c in existing_codes
            if isinstance(c, dict) and c.get("code") in required_code_strings and not c.get("deleted", False)
        ]

        # Build summary
        total_operations = len(deleted_codes) + len(created_codes)
        total_failures = len(failed_deletes) + len(failed_creates)

        summary = f"Sync complete: {len(deleted_codes)} deleted, {len(created_codes)} created, {len(kept_codes)} kept"
        if total_failures > 0:
            summary += f" ({total_failures} failures)"

        logger.info(f"📈 Operations Summary:")
        logger.info(f"   • Total existing codes before: {len(existing_codes)}")
        logger.info(f"   • Deleted: {len(deleted_codes)}")
        logger.info(f"   • Created: {len(created_codes)}")
        logger.info(f"   • Kept: {len(kept_codes)}")
        logger.info(f"   • Total operations: {total_operations}")
        logger.info(f"   • Failures: {total_failures}")
        logger.info(f"")
        logger.info(f"🎯 Final state: {len(kept_codes) + len(created_codes)} active codes")
        logger.info(f"✅ Required codes: {required_code_strings}")

        if total_failures == 0:
            logger.info(f"🎉 SUCCESS: {summary}")
        else:
            logger.warning(f"⚠️ PARTIAL SUCCESS: {summary}")
            if failed_deletes:
                logger.error(f"   Failed deletes: {[f['code'] for f in failed_deletes]}")
            if failed_creates:
                logger.error(f"   Failed creates: {[f['code'] for f in failed_creates]}")

        logger.info("=" * 80)
        logger.info("🎯 PRIORITY CODE SYNC - END")
        logger.info("=" * 80)

        return PriorityCodeSyncResponse(
            success=total_failures == 0,
            total_existing=len(existing_codes),
            required_codes=required_code_strings,
            deleted_codes=deleted_codes,
            created_codes=created_codes,
            failed_deletes=failed_deletes,
            failed_creates=failed_creates,
            kept_codes=kept_codes,
            summary=summary
        )

    except httpx.HTTPStatusError as e:
        logger.error("=" * 80)
        logger.error(f"❌ SYNC FAILED: HTTP Status Error")
        logger.error(f"   Status: {e.response.status_code}")
        logger.error(f"   Detail: {e.response.text[:300]}")
        logger.error("=" * 80)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Tekion API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error("=" * 80)
        logger.error(f"❌ SYNC FAILED: Network/Request Error")
        logger.error(f"   Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(
            status_code=502,
            detail=f"Network error: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTPExceptions without wrapping
        logger.error("=" * 80)
        logger.error(f"❌ SYNC FAILED: Validation/Business Logic Error")
        logger.error("=" * 80)
        raise
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ SYNC FAILED: Unexpected Error")
        logger.error(f"   Type: {type(e).__name__}")
        logger.error(f"   Message: {str(e)}")
        logger.error("=" * 80)
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@app.post("/api/network/extract")
async def extract_api_data(request: APIExtractionRequest):
    """
    Extract data from API response

    This endpoint intercepts an API call and extracts data based on metadata
    """
    try:
        logger.info(f"🌐 API extraction request: {request.url} -> {request.api_url_pattern}")

        # TODO: Implement actual API interception using Playwright
        # For now, return a mock response

        return JSONResponse({
            "status": "success",
            "message": "API extraction feature coming soon",
            "request": {
                "url": request.url,
                "api_pattern": request.api_url_pattern
            }
        })

    except Exception as e:
        logger.error(f"❌ API extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/network/generate-metadata")
async def generate_metadata(response_data: dict):
    """
    Auto-generate metadata from API response

    Request body:
    {
        "data": { ... API response ... },
        "prefix": "data",
        "max_depth": 10
    }
    """
    try:
        data = response_data.get("data", {})
        prefix = response_data.get("prefix", "data")
        max_depth = response_data.get("max_depth", 10)

        logger.info(f"🌐 Generating metadata for API response (prefix: {prefix})")

        # ✅ MONOLITH: Direct call to local API extraction service
        metadata = api_extraction_service.auto_generate_metadata(
            data,
            prefix=prefix,
            max_depth=max_depth
        )

        return JSONResponse({
            "status": "success",
            "metadata": metadata,
            "field_count": len(metadata)
        })

    except Exception as e:
        logger.error(f"❌ Metadata generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/network/extract-fields")
async def extract_fields(request_data: dict):
    """
    Extract fields from API response using metadata

    Request body:
    {
        "response_data": { ... API response ... },
        "field_mappings": { ... metadata ... }
    }
    """
    try:
        response_data = request_data.get("response_data", {})
        field_mappings = request_data.get("field_mappings", {})

        logger.info(f"🌐 Extracting {len(field_mappings)} fields from API response")

        # ✅ MONOLITH: Direct call to local API extraction service
        extracted = api_extraction_service.extract_fields_from_response(
            response_data,
            field_mappings
        )

        return JSONResponse({
            "status": "success",
            "extracted_fields": extracted,
            "field_count": len(extracted)
        })

    except Exception as e:
        logger.error(f"❌ Field extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/network/validate")
async def validate_response(request_data: dict):
    """
    Validate API response against metadata schema

    Request body:
    {
        "response_data": { ... API response ... },
        "metadata": { ... expected metadata ... }
    }
    """
    try:
        response_data = request_data.get("response_data", {})
        metadata = request_data.get("metadata", {})

        logger.info(f"🌐 Validating API response against {len(metadata)} fields")

        # ✅ MONOLITH: Direct call to local API extraction service
        validation = api_extraction_service.validate_response(
            response_data,
            metadata
        )

        return JSONResponse({
            "status": "success",
            "validation": validation
        })

    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/network/compare-environments")
async def compare_environments(request_data: dict):
    """
    Compare API responses across multiple environments

    Request body:
    {
        "extractions": {
            "dev": { ... extraction result ... },
            "staging": { ... extraction result ... },
            "prod": { ... extraction result ... }
        }
    }
    """
    try:
        extractions = request_data.get("extractions", {})

        logger.info(f"🌐 Comparing API responses across {len(extractions)} environments")

        # ✅ MONOLITH: Direct call to local API extraction service
        comparison = api_extraction_service.compare_environments(extractions)

        return JSONResponse({
            "status": "success",
            "comparison": comparison
        })

    except Exception as e:
        logger.error(f"❌ Environment comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 🌐 NETWORK TAB - API INTERCEPTION ENDPOINTS
# ========================================

@app.get("/api/network/intercepted-apis")
async def get_intercepted_apis():
    """
    Get all intercepted API responses
    Returns list of API calls captured during page loads
    """
    try:
        apis = screenshot_service.intercepted_apis

        # Return with metadata
        return JSONResponse({
            "success": True,
            "count": len(apis),
            "apis": apis
        })

    except Exception as e:
        logger.error(f"❌ Failed to get intercepted APIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/network/intercepted-apis")
async def clear_intercepted_apis():
    """
    Clear all intercepted API responses
    """
    try:
        count = len(screenshot_service.intercepted_apis)
        screenshot_service.intercepted_apis = []

        return JSONResponse({
            "success": True,
            "message": f"Cleared {count} intercepted APIs"
        })

    except Exception as e:
        logger.error(f"❌ Failed to clear intercepted APIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/network/intercepted-apis/{api_id}")
async def delete_intercepted_api(api_id: str):
    """
    Delete a specific intercepted API by ID
    """
    try:
        # Find and remove the API
        original_count = len(screenshot_service.intercepted_apis)
        screenshot_service.intercepted_apis = [
            api for api in screenshot_service.intercepted_apis
            if api.get("id") != api_id
        ]
        new_count = len(screenshot_service.intercepted_apis)

        if original_count == new_count:
            raise HTTPException(status_code=404, detail=f"API with ID {api_id} not found")

        return JSONResponse({
            "success": True,
            "message": f"Deleted API {api_id}",
            "remaining": new_count
        })

    except Exception as e:
        # ✅ FIXED: Removed redundant HTTPException re-raise for consistency
        logger.error(f"❌ Failed to delete intercepted API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/network/refresh-apis")
async def refresh_apis(request_data: dict):
    """
    Refresh API interception by reloading a URL

    Request body:
    {
        "url": "https://example.com/page"
    }
    """
    try:
        url = request_data.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        # This would trigger a page reload with API interception
        # For now, return a message that this requires real browser mode
        return JSONResponse({
            "success": True,
            "message": "API refresh requires loading the URL in Real Browser mode",
            "url": url
        })

    except Exception as e:
        logger.error(f"❌ Failed to refresh APIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/network/add-manual-api")
async def add_manual_api(request_data: dict):
    """
    Manually add an API response to the intercepted list

    Request body:
    {
        "url": "/api/example",
        "method": "GET",
        "status": 200,
        "response_json": {...}
    }
    """
    try:
        url = request_data.get("url", "")
        method = request_data.get("method", "GET")
        status = request_data.get("status", 200)
        response_json = request_data.get("response_json", {})

        # Create API entry
        import time
        api_entry = {
            'id': f"manual_{int(time.time() * 1000)}",
            'method': method,
            'url': url,
            'status': status,
            'statusText': 'OK',
            'timestamp': 0,
            'request_headers': {},
            'response_headers': {},
            'request_body': None,
            'response_body': json.dumps(response_json),
            'response_json': response_json,
            'captured_at': time.time(),
            'page_url': 'manual',
            'captured_from': 'manual_entry'
        }

        # Add to storage
        screenshot_service.intercepted_apis.append(api_entry)

        # Enforce limit
        if len(screenshot_service.intercepted_apis) > screenshot_service.max_intercepted_apis:
            screenshot_service.intercepted_apis = screenshot_service.intercepted_apis[
                -screenshot_service.max_intercepted_apis:]

        return JSONResponse({
            "success": True,
            "message": "API added successfully",
            "api": api_entry
        })

    except Exception as e:
        logger.error(f"❌ Failed to add manual API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TAB CLEANUP ENDPOINTS
# ============================================================================

@app.post("/api/tabs/cleanup")
async def force_cleanup_tabs():
    """
    Force cleanup ALL open tabs in the browser (including failed ones)

    This endpoint will close ALL tabs that were opened by the screenshot service,
    including failed/timed-out tabs that are normally kept for debugging.
    Useful when tabs are left open after timeouts or errors.
    """
    try:
        logger.info("🧹 Force cleanup requested - closing ALL tabs (including failed)...")

        # Close ALL tabs, not just successful ones
        closed_count = 0
        for url, info in list(screenshot_service.tab_registry.tabs.items()):
            try:
                await info["page"].close()
                del screenshot_service.tab_registry.tabs[url]
                closed_count += 1
                logger.info(f"✅ Closed tab: {url}")
            except Exception as e:
                logger.warning(f"⚠️  Error closing tab {url}: {e}")
                # Remove from registry anyway
                del screenshot_service.tab_registry.tabs[url]

        logger.info(f"🧹 Cleanup complete: {closed_count} tabs closed")

        return {
            "success": True,
            "closed_count": closed_count,
            "message": f"Closed {closed_count} tab(s) successfully"
        }
    except Exception as e:
        logger.error(f"❌ Tab cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tabs/status")
async def get_tabs_status():
    """
    Get the current status of open tabs

    Returns information about tabs currently tracked by the service.
    """
    try:
        # Get tab registry status
        tab_count = len(screenshot_service.tab_registry.tabs) if hasattr(screenshot_service, 'tab_registry') else 0

        return {
            "success": True,
            "tracked_tabs": tab_count,
            "message": f"Currently tracking {tab_count} tab(s)"
        }
    except Exception as e:
        logger.error(f"❌ Tab status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TEMPLATE LOGO REMOVAL ENDPOINTS
# ============================================================================

class TemplateRemovalRequest(BaseModel):
    base_url: str = Field(..., description="Base URL of Tekion app (e.g., https://preprodapp.tekioncloud.com)")
    max_rows: int = Field(200, description="Maximum number of templates to fetch from API (1-500)")
    custom_limit: Optional[int] = Field(None, description="Custom limit on how many templates to process (optional)")
    keep_tabs_open: bool = Field(False, description="Keep tabs open for manual verification (default: False)")


@app.post("/api/templates/start-logo-removal")
async def start_logo_removal(request: TemplateRemovalRequest):
    """
    Start bulk Tekion logo removal from all templates

    Returns job_id for tracking progress via WebSocket
    """
    job_id = str(uuid4())
    logger.info(f"🎨 ===============================================")
    logger.info(f"🎨 Starting template logo removal job")
    logger.info(f"🎨 Job ID: {job_id}")
    logger.info(f"🎨 Base URL: {request.base_url}")
    logger.info(f"🎨 ===============================================")

    # Start the job in background
    asyncio.create_task(
        template_removal_service.start_removal_job(
            base_url=request.base_url,
            job_id=job_id,
            max_parallel=5,  # Process 5 templates at once
            max_rows=request.max_rows,  # Max rows to fetch from API
            custom_limit=request.custom_limit,  # Custom limit on processing
            keep_tabs_open=request.keep_tabs_open  # ✅ Keep tabs open toggle
        )
    )

    logger.info(f"🎨 Job {job_id} started in background")

    return {
        "status": "started",
        "job_id": job_id,
        "message": "Template logo removal job started"
    }


@app.get("/api/templates/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a template removal job"""
    status = template_removal_service.get_job_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return status


@app.post("/api/templates/cancel-job/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running template removal job"""
    success = template_removal_service.cancel_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "status": "cancelled",
        "job_id": job_id
    }


# WebSocket for real-time progress updates
@app.websocket("/ws/template-removal/{job_id}")
async def websocket_template_removal(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time template removal progress updates
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for job {job_id}")

    try:
        # Send updates every second
        while True:
            status = template_removal_service.get_job_status(job_id)

            if not status:
                await websocket.send_json({"error": "Job not found"})
                break

            await websocket.send_json(status)

            # Stop if job is complete or failed
            if status.get("status") in ["completed", "failed", "cancelled"]:
                logger.info(f"Job {job_id} finished with status: {status.get('status')}")
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
        # ✅ Cancel the job when frontend disconnects (page reload, close, etc.)
        logger.info(f"🛑 Cancelling job {job_id} due to frontend disconnect...")
        template_removal_service.cancel_job(job_id)
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass


# ============================================================================
# TEMPLATE LOGO ADDITION ENDPOINTS
# ============================================================================

class TemplateAdditionRequest(BaseModel):
    base_url: str = Field(..., description="Base URL of Tekion app")
    max_rows: int = Field(200, description="Maximum number of templates to fetch (1-500)")
    custom_limit: Optional[int] = Field(None, description="Custom limit on processing")
    keep_tabs_open: bool = Field(True, description="Keep tabs open for verification")
    logo_media_id: str = Field("6a19132b6697f36de6236fb1", description="Media ID of logo to add (Tilton.png)")
    logo_width: int = Field(160, description="Width of logo in pixels")
    departments: Optional[List[str]] = Field(None, description="Departments to filter (Sales, Service, Parts)")
    auto_publish: bool = Field(True, description="Auto-publish templates after logo addition")


@app.post("/api/templates/start-logo-addition")
async def start_logo_addition(request: TemplateAdditionRequest):
    """
    Start bulk logo addition to all templates

    INTEGRATED WITH FINAL VERSION:
    - Department filtering (Service & Parts)
    - 4-layer logo detection
    - Auto-publish workflow
    - Center & enlarge logos

    Returns job_id for tracking progress via WebSocket
    """
    job_id = str(uuid4())
    logger.info(f"✨ ===============================================")
    logger.info(f"✨ Starting INTEGRATED template logo addition job")
    logger.info(f"✨ Job ID: {job_id}")
    logger.info(f"✨ Base URL: {request.base_url}")
    logger.info(f"✨ Departments: {', '.join(request.departments or ['Service', 'Parts'])}")
    logger.info(f"✨ Logo Media ID: {request.logo_media_id}")
    logger.info(f"✨ Logo Width: {request.logo_width}px")
    logger.info(f"✨ Auto-publish: {request.auto_publish}")
    logger.info(f"✨ ===============================================")

    # Create job with FINAL version features
    template_logo_addition_service.create_job(
        job_id=job_id,
        base_url=request.base_url,
        max_rows=request.max_rows,
        custom_limit=request.custom_limit,
        keep_tabs_open=request.keep_tabs_open,
        logo_media_id=request.logo_media_id,
        logo_width=request.logo_width,
        departments=request.departments,
        auto_publish=request.auto_publish
    )

    # Get browser instance from screenshot service
    from screenshot_service import screenshot_service
    browser = screenshot_service.browser

    if not browser:
        raise HTTPException(status_code=500, detail="Browser not connected")

    # Start job in background
    asyncio.create_task(
        template_logo_addition_service.run_logo_addition(job_id, browser)
    )

    logger.info(f"✨ Job {job_id} started in background")

    return {
        "status": "started",
        "job_id": job_id,
        "message": "Template logo addition job started"
    }


@app.get("/api/templates/addition-status/{job_id}")
async def get_addition_status(job_id: str):
    """Get status of a template logo addition job"""
    if job_id not in template_logo_addition_service.jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return template_logo_addition_service.jobs[job_id]


@app.websocket("/ws/template-addition/{job_id}")
async def websocket_template_addition(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time template logo addition progress updates
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for logo addition job {job_id}")

    try:
        while True:
            if job_id not in template_logo_addition_service.jobs:
                await websocket.send_json({"error": "Job not found"})
                break

            job = template_logo_addition_service.jobs[job_id]
            await websocket.send_json(job)

            # Stop if job is complete or failed
            if job.get("status") in ["completed", "failed"]:
                logger.info(f"Logo addition job {job_id} finished with status: {job.get('status')}")
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for logo addition job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for logo addition job {job_id}: {str(e)}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass


# ============================================================================
# TEMPLATE PAGE DETECTION ENDPOINT
# ============================================================================

@app.post("/api/templates/detect-all")
async def detect_all_page_elements():
    """
    Detect ALL elements on the Tekion templates list page
    Returns comprehensive analysis of filters, UI, API, templates, etc.
    """
    logger.info("🔍 ===============================================")
    logger.info("🔍 Starting comprehensive page detection")
    logger.info("🔍 ===============================================")

    # Get browser instance
    from screenshot_service import screenshot_service
    browser = screenshot_service.browser

    if not browser:
        raise HTTPException(status_code=500, detail="Browser not connected")

    # Run detection
    results = await template_page_detector.detect_all(browser)

    logger.info("🔍 Detection complete")

    return results


@app.get("/reports/{filename}")
async def download_report(filename: str):
    """
    Download an Excel report
    """
    file_path = os.path.join("backend/reports", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ============================================================================
# APPLICATION STARTUP
# ============================================================================


def create_app() -> FastAPI:
	"""Return the configured FastAPI application.

	For now this simply returns the module-level ``app`` instance so that
	tests and external tooling can import ``main:create_app`` without
	requiring a full application factory refactor yet.
	"""

	return app


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="127.0.0.1", port=settings.api_port, reload=True)
