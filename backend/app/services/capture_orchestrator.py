"""Capture orchestration service for screenshot requests.

This module centralizes high-level orchestration of screenshot captures
(batching, cancellation checks, WebSocket notifications) behind a
dedicated service class. Behaviour is kept in sync with the previous
implementation in ``backend.main`` so external callers and routers keep
the same request/response shapes.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4
import logging
import traceback

import httpx

from logging_config import (
    log_request_start,
    log_request_complete,
    log_cancellation,
    correlation_id_var,
)
from backend.app.models.screenshot import ScreenshotResult, URLRequest
from config import settings


logger = logging.getLogger(__name__)


class CaptureOrchestrator:
    """Orchestrates screenshot capture for a logical request.

    Dependencies are injected so this class can be unit-tested with
    fakes/mocks instead of relying on globals from ``backend.main``.
    """

    def __init__(
        self,
        screenshot_service: Any,
        cancellation_registry: Any,
        manager: Any,
        quality_checker: Any,
        http_client: Any,
    ) -> None:
        self._screenshot_service = screenshot_service
        self._cancellation_registry = cancellation_registry
        self._manager = manager
        self._quality_checker = quality_checker
        self._http_client = http_client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start_capture_request(self, request: URLRequest) -> Tuple[str, datetime]:
        """Register a new capture request and return (request_id, start_time)."""

        # Reuse existing correlation ID when available so screenshot
        # requests can be traced end-to-end across services.
        try:
            correlation_id = correlation_id_var.get()
        except Exception:
            correlation_id = None

        request_id = correlation_id or str(uuid4())
        self._cancellation_registry.create(request_id)
        log_request_start(request_id, len(request.urls))
        return request_id, datetime.now()

    def _is_cancelled(self, request_id: str) -> bool:
        """Check whether a given request has been cancelled."""

        return self._cancellation_registry.is_cancelled(request_id)

    def _create_smart_batches(
        self,
        urls: List[str],
        enable_batch: bool,
        max_parallel: int,
        use_real_browser: bool,
        enable_rolling: bool = False,
    ) -> List[List[str]]:
        """Create batches for parallel processing.

        Mirrors the previous ``_create_smart_batches`` helper from
        ``backend.main`` but scopes behaviour to the injected
        ``screenshot_service`` (for ENABLE_BATCH_PROCESSING).

        ✅ ROLLING PARALLELIZATION MODE:
        - When enable_rolling=True, ALL URLs are processed in a single batch
        - Semaphore controls concurrency (only max_parallel URLs run at once)
        - As soon as one URL finishes, the next URL starts immediately
        - This eliminates idle time between batches
        """

        batch_processing_enabled = getattr(
            self._screenshot_service, "ENABLE_BATCH_PROCESSING", False
        )

        if not enable_batch or not batch_processing_enabled:
            # Sequential processing - one URL at a time
            return [[url] for url in urls]

        # ✅ ROLLING MODE: Process ALL URLs in a single batch with semaphore control
        if enable_rolling:
            logger.info(f"⚡ Rolling parallelization enabled: {len(urls)} URLs, {max_parallel} concurrent")
            return [urls]  # Single batch containing ALL URLs

        # Respect max_parallel for Real Browser Mode by chunking URLs.
        if use_real_browser and max_parallel > 0:
            return [urls[i : i + max_parallel] for i in range(0, len(urls), max_parallel)]

        # Non-real-browser mode: process all URLs in a single batch
        return [urls]

    def _resolve_capture_timeout(self, request: URLRequest) -> float:
        """Centralized capture timeout selection based on request settings."""

        if request.batch_timeout:
            # Keep previous behaviour: per-URL timeout is half batch timeout
            return float(request.batch_timeout) / 2
        if request.use_real_browser:
            return 90.0
        if request.browser_engine == "camoufox":
            return 120.0
        if request.use_stealth:
            return 90.0
        if request.capture_mode == "segmented":
            return 120.0
        return 35.0

    async def _check_quality(self, screenshot_path: str) -> Dict[str, Any]:
        """Check screenshot quality via Quality Service with local fallback."""

        try:
            client = self._http_client
            close_client = False
            if client is None:
                client = httpx.AsyncClient(timeout=30.0)
                close_client = True

            try:
                response = await client.post(
                    f"{settings.quality_service_url}/check",
                    json={"screenshot_path": screenshot_path},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error(
                        f"❌ Quality Service returned error: {response.status_code}"
                    )
                    logger.warning("⚠️  Falling back to local quality checker")
                    return await self._quality_checker.check(screenshot_path)

                result = response.json()
                return {
                    "passed": result["passed"],
                    "score": result["score"],
                    "issues": result["issues"],
                }
            finally:
                if close_client:
                    await client.aclose()
        except httpx.RequestError as e:
            logger.warning(
                f"⚠️  Quality Service unavailable: {e}. Using local checker."
            )
            return await self._quality_checker.check(screenshot_path)
        except Exception as e:  # pragma: no cover - defensive logging
            logger.error(
                f"❌ Error calling Quality Service: {e}. Using local checker."
            )
            return await self._quality_checker.check(screenshot_path)

    async def _capture_single_url(
        self,
        url: str,
        request: URLRequest,
        request_id: str,
        index: int,
        total: int,
        semaphore: asyncio.Semaphore,
    ) -> ScreenshotResult:
        """Capture a single URL with centralized timeout and quality checks.

        Mirrors ``backend.main._capture_single_url`` but uses injected
        dependencies instead of globals.
        """

        async with semaphore:
            url_start_time = datetime.now()

            # ✅ NEW: Send WebSocket notification that URL is starting
            await self._manager.send_message({
                "type": "url_status_change",
                "url": url,
                "status": "active",
                "index": index,
                "total": total,
                "request_id": request_id,
                "timestamp": url_start_time.isoformat(),
            })

            # Check cancellation before starting
            if self._is_cancelled(request_id):
                # ✅ NEW: Send WebSocket notification for early cancellation
                await self._manager.send_message({
                    "type": "url_status_change",
                    "url": url,
                    "status": "cancelled",
                    "duration": 0.0,
                    "screenshots": 0,
                    "error": "Operation cancelled by user",
                    "index": index,
                    "total": total,
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                })

                return ScreenshotResult(
                    url=url,
                    status="cancelled",
                    error="Operation cancelled by user",
                    timestamp=datetime.now().isoformat(),
                    processing_time=0.0,
                )

            try:
                # (Optional) progress hook – kept lightweight
                try:
                    await self._manager.send_message(
                        {
                            "type": "progress",
                            "current": index + 1,
                            "total": total,
                            "url": url,
                            "status": "capturing",
                            "request_id": request_id,
                        }
                    )
                except Exception:  # pragma: no cover - best effort
                    logger.debug("Progress message send failed", exc_info=True)

                capture_timeout = self._resolve_capture_timeout(request)
                screenshot_timeout_ms = int(capture_timeout * 1000)

                try:
                    if request.capture_mode == "segmented":
                        screenshot_paths = await asyncio.wait_for(
                            self._screenshot_service.capture_segmented(
                                url=url,
                                viewport_width=request.viewport_width,
                                viewport_height=request.viewport_height,
                                screenshot_timeout=screenshot_timeout_ms,
                                use_stealth=request.use_stealth,
                                use_real_browser=request.use_real_browser,
                                headless=request.headless,
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
                                track_network=request.track_network,
                                auto_expand_dropdowns=request.auto_expand_dropdowns,
                                click_elements=request.click_elements,
                                non_scrollable_urls=request.non_scrollable_urls,
                            ),
                            timeout=capture_timeout,
                        )
                        screenshot_path = (
                            screenshot_paths[0] if screenshot_paths else None
                        )
                    else:
                        full_page = request.capture_mode == "fullpage"
                        screenshot_path = await asyncio.wait_for(
                            self._screenshot_service.capture(
                                url=url,
                                viewport_width=request.viewport_width,
                                viewport_height=request.viewport_height,
                                full_page=full_page,
                                screenshot_timeout=screenshot_timeout_ms,
                                use_stealth=request.use_stealth,
                                use_real_browser=request.use_real_browser,
                                headless=request.headless,
                                browser_engine=request.browser_engine,
                                base_url=request.base_url,
                                words_to_remove=request.words_to_remove,
                                cookies=request.cookies,
                                local_storage=request.local_storage,
                                track_network=request.track_network,
                                auto_expand_dropdowns=request.auto_expand_dropdowns,
                                click_elements=request.click_elements,
                                non_scrollable_urls=request.non_scrollable_urls,
                            ),
                            timeout=capture_timeout,
                        )
                        screenshot_paths = None
                except asyncio.TimeoutError:
                    mode = "real browser" if request.use_real_browser else "headless"
                    error = (
                        f"Screenshot capture timed out after {capture_timeout}s "
                        f"({mode} mode)"
                    )
                    url_end_time = datetime.now()
                    processing_time = (url_end_time - url_start_time).total_seconds()

                    # ✅ NEW: Send WebSocket notification for timeout
                    await self._manager.send_message({
                        "type": "url_status_change",
                        "url": url,
                        "status": "failed",
                        "duration": processing_time,
                        "screenshots": 0,
                        "error": error,
                        "index": index,
                        "total": total,
                        "request_id": request_id,
                        "timestamp": url_end_time.isoformat(),
                    })

                    return ScreenshotResult(
                        url=url,
                        status="error",
                        error=error,
                        timestamp=datetime.now().isoformat(),
                        processing_time=processing_time,
                    )

                # Post-capture cancellation check
                if self._is_cancelled(request_id):
                    url_end_time = datetime.now()
                    processing_time = (
                        url_end_time - url_start_time
                    ).total_seconds()

                    # ✅ NEW: Send WebSocket notification for cancellation
                    await self._manager.send_message({
                        "type": "url_status_change",
                        "url": url,
                        "status": "cancelled",
                        "duration": processing_time,
                        "screenshots": 0,
                        "error": "Operation cancelled by user",
                        "index": index,
                        "total": total,
                        "request_id": request_id,
                        "timestamp": url_end_time.isoformat(),
                    })

                    return ScreenshotResult(
                        url=url,
                        status="cancelled",
                        error="Operation cancelled by user",
                        timestamp=datetime.now().isoformat(),
                        processing_time=processing_time,
                    )

                if not screenshot_path:
                    raise Exception("Screenshot capture returned no file path")

                # Quality check via Quality Service (with fallback)
                quality_result = await self._check_quality(screenshot_path)

                url_end_time = datetime.now()
                processing_time = (url_end_time - url_start_time).total_seconds()

                result_status = "success" if quality_result["passed"] else "failed"
                screenshot_count = len(screenshot_paths) if "screenshot_paths" in locals() and screenshot_paths else 1

                # ✅ NEW: Send WebSocket notification that URL completed
                await self._manager.send_message({
                    "type": "url_status_change",
                    "url": url,
                    "status": "completed" if result_status == "success" else "failed",
                    "duration": processing_time,
                    "screenshots": screenshot_count,
                    "index": index,
                    "total": total,
                    "request_id": request_id,
                    "timestamp": url_end_time.isoformat(),
                })

                return ScreenshotResult(
                    url=url,
                    status=result_status,
                    screenshot_path=screenshot_path,
                    screenshot_paths=screenshot_paths if "screenshot_paths" in locals() else None,
                    segment_count=len(screenshot_paths) if "screenshot_paths" in locals() and screenshot_paths else None,
                    quality_score=quality_result["score"],
                    quality_issues=quality_result["issues"],
                    timestamp=datetime.now().isoformat(),
                    processing_time=processing_time,
                )

            except Exception as e:
                url_end_time = datetime.now()
                processing_time = (url_end_time - url_start_time).total_seconds()

                logger.error(f"❌ Error capturing {url}: {e}")
                logger.error(traceback.format_exc())

                # ✅ NEW: Send WebSocket notification that URL failed
                await self._manager.send_message({
                    "type": "url_status_change",
                    "url": url,
                    "status": "failed",
                    "duration": processing_time,
                    "screenshots": 0,
                    "error": str(e),
                    "index": index,
                    "total": total,
                    "request_id": request_id,
                    "timestamp": url_end_time.isoformat(),
                })

                return ScreenshotResult(
                    url=url,
                    status="failed",
                    error=str(e),
                    timestamp=datetime.now().isoformat(),
                    processing_time=processing_time,
                )

    # ------------------------------------------------------------------
    # Public orchestration APIs
    # ------------------------------------------------------------------

    async def capture(self, request: URLRequest) -> Dict[str, Any]:
        """Capture screenshots for multiple URLs with smart batch processing."""

        # Create request-scoped cancellation flag and log request start
        request_id, start_time = self._start_capture_request(request)

        # Debug logging for request parameters
        logger.info(f"🔍 BASE URL RECEIVED: '{request.base_url}'")
        logger.info(f"🔍 WORDS TO REMOVE: '{request.words_to_remove}'")
        logger.info(f"🔍 URLS RECEIVED: {request.urls}")
        logger.info(f"🔍 AUTO EXPAND DROPDOWNS: {request.auto_expand_dropdowns}")
        logger.info(f"🔍 NON-SCROLLABLE URLS: '{request.non_scrollable_urls}'")

        # Create smart batches
        enable_batch = len(request.urls) > 1
        batches = self._create_smart_batches(
            request.urls,
            enable_batch,
            max_parallel=request.max_parallel_urls,
            use_real_browser=request.use_real_browser,
            enable_rolling=request.enable_rolling_parallelization,  # ✅ NEW: Rolling parallelization
        )

        if enable_batch and getattr(self._screenshot_service, "ENABLE_BATCH_PROCESSING", False):
            if request.enable_rolling_parallelization:
                logger.info(f"⚡ Rolling parallelization mode: {len(request.urls)} URLs, {request.max_parallel_urls} concurrent")
                logger.info(f"   🔄 URLs will start immediately as slots become available (no idle time)")
                if request.use_real_browser:
                    logger.info(f"   🌐 Real Browser Mode: Up to {request.max_parallel_urls} tabs open at once")
            else:
                logger.info(
                    f"⚡ Smart batch processing enabled: {len(batches)} batches for {len(request.urls)} URLs"
                )
                if request.use_real_browser:
                    logger.info(
                    f"   🌐 Real Browser Mode: Will open up to {request.max_parallel_urls} tabs at once"
                )
        else:
            logger.info(f"📋 Sequential processing: {len(request.urls)} URLs")

        try:
            results: List[ScreenshotResult] = []
            url_index = 0

            # Process each batch
            for batch_num, batch in enumerate(batches, 1):
                # Check cancellation before starting this batch
                if self._is_cancelled(request_id):
                    remaining_urls: List[str] = []
                    remaining_urls.extend(batch)
                    for next_batch in batches[batch_num:]:
                        remaining_urls.extend(next_batch)

                    for remaining_url in remaining_urls:
                        results.append(
                            ScreenshotResult(
                                url=remaining_url,
                                status="cancelled",
                                error="Operation cancelled by user",
                                timestamp=datetime.now().isoformat(),
                                processing_time=0.0,
                            )
                        )

                    # Log cancellation and notify WebSocket listeners
                    log_cancellation(request_id, url_index, len(request.urls))
                    await self._manager.send_message(
                        {
                            "type": "cancelled",
                            "message": "Screenshot capture cancelled",
                            "completed": url_index,
                            "total": len(request.urls),
                            "request_id": request_id,
                        }
                    )

                    break

                if len(batch) > 1:
                    if request.enable_rolling_parallelization:
                        logger.info(
                            f"🔄 Rolling mode: Processing {len(batch)} URLs ({request.max_parallel_urls} concurrent)..."
                        )
                    else:
                        logger.info(
                            f"🚀 Processing batch {batch_num}/{len(batches)} ({len(batch)} URLs in parallel)..."
                        )

                # Create tasks for this batch
                semaphore = asyncio.Semaphore(request.max_parallel_urls)
                batch_tasks = [
                    self._capture_single_url(
                        url,
                        request,
                        request_id,
                        url_index + i,
                        len(request.urls),
                        semaphore,
                    )
                    for i, url in enumerate(batch)
                ]

                # Calculate timeout for this batch
                # ✅ ROLLING MODE: Scale timeout based on total URLs and concurrency
                if request.enable_rolling_parallelization:
                    scaling_factor = len(batch) / request.max_parallel_urls
                    calculated_timeout = (request.batch_timeout if request.batch_timeout else 300) * scaling_factor
                    # ✅ FIX 2.2: Use configurable timeout cap from settings
                    batch_timeout_value = min(calculated_timeout, settings.max_batch_timeout_seconds)
                    logger.info(f"   ⏱️  Rolling mode timeout: {batch_timeout_value:.0f}s (scaled for {len(batch)} URLs, capped at {settings.max_batch_timeout_seconds}s)")
                else:
                    batch_timeout_value = request.batch_timeout if request.batch_timeout else 300

                # Execute batch in parallel with batch timeout
                batch_results: List[ScreenshotResult] = []
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*batch_tasks),
                        timeout=batch_timeout_value,
                    )
                    results.extend(batch_results)
                    url_index += len(batch)
                except asyncio.TimeoutError:
                    # Batch timed out - mark all URLs in batch as failed
                    timeout_msg = f"Rolling mode timeout after {batch_timeout_value:.0f}s" if request.enable_rolling_parallelization else f"Batch timed out after {batch_timeout_value}s"
                    for url in batch:
                        results.append(
                            ScreenshotResult(
                                url=url,
                                status="error",
                                error=timeout_msg,
                                timestamp=datetime.now().isoformat(),
                                processing_time=float(batch_timeout_value),
                            )
                        )
                    url_index += len(batch)

                # Send result updates for this batch (works for success and timeout)
                batch_slice = results[url_index - len(batch) : url_index]
                for result in batch_slice:
                    await self._manager.send_message(
                        {
                            "type": "result",
                            "result": result.model_dump(),
                            "request_id": request_id,
                        }
                    )

            # Automatic retry for failed URLs (Real Browser Mode only)
            if request.use_real_browser:
                failed_urls = [r.url for r in results if r.status == "failed"]

                if failed_urls and not self._is_cancelled(request_id):
                    logger.info(f"\n🔄 Retrying {len(failed_urls)} failed URLs...")

                    for url in failed_urls:
                        if self._is_cancelled(request_id):
                            break

                        try:
                            logger.info(f"   🔄 Retrying: {url}")
                            retry_result = await self._capture_single_url(
                                url,
                                request,
                                request_id,
                                0,
                                len(failed_urls),
                                asyncio.Semaphore(1),
                            )

                            # Replace original result
                            for i, r in enumerate(results):
                                if r.url == url:
                                    results[i] = retry_result
                                    break

                            await self._manager.send_message(
                                {
                                    "type": "result",
                                    "result": retry_result.model_dump(),
                                    "request_id": request_id,
                                    "is_retry": True,
                                }
                            )

                            if retry_result.status == "success":
                                logger.info(f"   ✅ Retry succeeded: {url}")
                            else:
                                logger.info(f"   ❌ Retry failed: {url}")

                        except Exception as e:  # pragma: no cover - defensive logging
                            logger.error(f"   ❌ Retry error for {url}: {e}")

                    success_count = sum(1 for r in results if r.status == "success")
                    failed_count = sum(1 for r in results if r.status == "failed")

                    logger.info("\n📊 Retry Summary:")
                    logger.info(
                        f"   ✅ Total successful: {success_count}/{len(request.urls)}"
                    )
                    logger.info(
                        f"   ❌ Still failed: {failed_count}/{len(request.urls)}"
                    )

                    try:
                        await self._screenshot_service.cleanup_tabs_after_batch()
                    except Exception as e:
                        logger.error(f"⚠️  Error during tab cleanup: {e}")

            # Log request completion
            duration = (datetime.now() - start_time).total_seconds()
            success_count = sum(1 for r in results if r.status == "success")
            log_request_complete(request_id, success_count, len(request.urls), duration)

            return {
                "results": results,
                "cancelled": self._is_cancelled(request_id),
                "request_id": request_id,
            }
        finally:
            # Cleanup request-scoped cancellation flag
            self._cancellation_registry.remove(request_id)

    async def capture_sequential(self, request: URLRequest) -> Dict[str, Any]:
        """Sequential screenshot capture (legacy behaviour)."""

        request_id, start_time = self._start_capture_request(request)

        results: List[ScreenshotResult] = []
        semaphore = asyncio.Semaphore(1)

        try:
            for i, url in enumerate(request.urls):
                if self._is_cancelled(request_id):
                    for remaining_url in request.urls[i:]:
                        results.append(
                            ScreenshotResult(
                                url=remaining_url,
                                status="cancelled",
                                error="Operation cancelled by user",
                                timestamp=datetime.now().isoformat(),
                                processing_time=0.0,
                            )
                        )

                    log_cancellation(request_id, i, len(request.urls))

                    await self._manager.send_message(
                        {
                            "type": "cancelled",
                            "message": "Screenshot capture cancelled",
                            "completed": i,
                            "total": len(request.urls),
                            "request_id": request_id,
                        }
                    )
                    break

                result = await self._capture_single_url(
                    url=url,
                    request=request,
                    request_id=request_id,
                    index=i,
                    total=len(request.urls),
                    semaphore=semaphore,
                )
                results.append(result)

                await self._manager.send_message(
                    {
                        "type": "result",
                        "result": result.model_dump(),
                        "request_id": request_id,
                    }
                )

            duration = (datetime.now() - start_time).total_seconds()
            success_count = sum(1 for r in results if r.status == "success")
            log_request_complete(request_id, success_count, len(request.urls), duration)

            return {
                "results": results,
                "cancelled": self._is_cancelled(request_id),
                "request_id": request_id,
            }
        finally:
            self._cancellation_registry.remove(request_id)
