"""Unit-style tests for :class:`CaptureOrchestrator`.

These tests exercise the orchestration logic without calling the real
screenshot microservice or WebSocket layer. They are intentionally
lightweight and rely on fakes/stubs for all external dependencies.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import pytest


try:  # Support both package and script execution contexts
    from backend.app.models import URLRequest, ScreenshotResult  # type: ignore
    from backend.app.services.capture_orchestrator import CaptureOrchestrator  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/...)
    from app.models import URLRequest, ScreenshotResult  # type: ignore
    from app.services.capture_orchestrator import CaptureOrchestrator  # type: ignore


class FakeCancellationRegistry:
    def __init__(self) -> None:
        self.created_ids: List[str] = []
        self.removed_ids: List[str] = []
        self.always_cancel: bool = False

    def create(self, request_id: str) -> None:
        self.created_ids.append(request_id)

    def remove(self, request_id: str) -> None:
        self.removed_ids.append(request_id)

    def is_cancelled(self, request_id: str) -> bool:
        """Simulate cancellation status for a given request ID."""

        return self.always_cancel


class FakeScreenshotService:
    """Minimal stub of the real ScreenshotService.

    Only attributes/methods touched by the orchestrator are implemented.
    """

    ENABLE_BATCH_PROCESSING: bool = True

    async def cleanup_tabs_after_batch(self) -> None:  # pragma: no cover - simple stub
        return None


class FakeManager:
    def __init__(self) -> None:
        self.messages: List[Dict[str, Any]] = []

    async def send_message(self, payload: Dict[str, Any]) -> None:
        self.messages.append(payload)


@pytest.mark.anyio
async def test_parallel_success() -> None:
    """Basic happy-path test for parallel capture."""

    fake_registry = FakeCancellationRegistry()
    fake_service = FakeScreenshotService()
    fake_manager = FakeManager()

    async def fake_capture_single_url(
        url: str,
        request: URLRequest,
        request_id: str,
        index: int,
        total: int,
        semaphore: Any,
    ) -> ScreenshotResult:
        return ScreenshotResult(
            url=url,
            status="success",
            screenshot_path=None,
            screenshot_paths=None,
            segment_count=None,
            error=None,
            quality_score=None,
            quality_issues=None,
            timestamp=datetime.now().isoformat(),
            processing_time=0.1,
        )

    orchestrator = CaptureOrchestrator(
        fake_service,
        fake_registry,
        fake_manager,
        quality_checker=None,
        http_client=None,
    )

    # Patch instance method for this test only
    orchestrator._capture_single_url = fake_capture_single_url  # type: ignore[assignment]

    request = URLRequest(urls=["https://example.com", "https://example.org"])
    result = await orchestrator.capture(request)

    assert result["cancelled"] is False
    assert len(result["results"]) == 2
    assert [r.url for r in result["results"]] == request.urls
    assert any(m.get("type") == "result" for m in fake_manager.messages)
    assert len(fake_registry.created_ids) == 1
    assert len(fake_registry.removed_ids) == 1


@pytest.mark.anyio
async def test_parallel_cancellation() -> None:
    """Verify that cancellation short-circuits processing and marks URLs."""

    fake_registry = FakeCancellationRegistry()
    fake_service = FakeScreenshotService()
    fake_manager = FakeManager()

    async def fake_capture_single_url(
        url: str,
        request: URLRequest,
        request_id: str,
        index: int,
        total: int,
        semaphore: Any,
    ) -> ScreenshotResult:
        # Should not be called when cancellation triggers early
        return ScreenshotResult(
            url=url,
            status="unexpected",
            screenshot_path=None,
            screenshot_paths=None,
            segment_count=None,
            error=None,
            quality_score=None,
            quality_issues=None,
            timestamp=datetime.now().isoformat(),
            processing_time=0.1,
        )

    fake_registry.always_cancel = True

    orchestrator = CaptureOrchestrator(
        fake_service,
        fake_registry,
        fake_manager,
        quality_checker=None,
        http_client=None,
    )

    # Patch instance method for this test only
    orchestrator._capture_single_url = fake_capture_single_url  # type: ignore[assignment]

    request = URLRequest(urls=["https://example.com", "https://example.org"])
    result = await orchestrator.capture(request)

    # All URLs should be marked cancelled without calling fake_capture_single_url
    assert result["cancelled"] is True
    assert all(r.status == "cancelled" for r in result["results"])
    assert any(m.get("type") == "cancelled" for m in fake_manager.messages)
    assert len(fake_registry.created_ids) == 1
    assert len(fake_registry.removed_ids) == 1
