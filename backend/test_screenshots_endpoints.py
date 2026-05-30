"""HTTP-level tests for screenshot capture endpoints.

These tests convert the manual test_screenshots_api.py script into
pytest tests that exercise the FastAPI routes via TestClient, while
monkeypatching the CaptureOrchestrator so no real browser or
screenshot microservice is required.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient


try:  # Support both package and script execution contexts
    import main  # type: ignore
    from backend.app import models  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
    import main  # type: ignore
    from app import models  # type: ignore


ClientFixture = TestClient


class FakeOrchestrator:
    """Minimal stand-in for CaptureOrchestrator used in endpoint tests."""

    async def capture(self, request: models.URLRequest) -> Dict[str, Any]:
        return {
            "results": [
                {
                    "url": url,
                    "status": "success",
                    "screenshot_path": f"/tmp/{idx}.png",
                }
                for idx, url in enumerate(request.urls)
            ],
            "request_id": "test-request",
            "cancelled": False,
        }

    async def capture_sequential(self, request: models.URLRequest) -> Dict[str, Any]:
        # For the purposes of this test, treat sequential the same as parallel
        return await self.capture(request)


@pytest.fixture(autouse=True)
def patch_capture_orchestrator(monkeypatch) -> None:
    """Ensure all screenshot capture routes use a fake orchestrator.

    We patch main.get_capture_orchestrator, which is what the runtime
    dependency helper in backend.app.services ultimately calls.
    """

    fake = FakeOrchestrator()

    def _get_fake_orchestrator() -> FakeOrchestrator:
        return fake

    monkeypatch.setattr(main, "get_capture_orchestrator", _get_fake_orchestrator)


def _base_request_body() -> Dict[str, Any]:
    """Minimal valid payload for URLRequest.

    URLRequest defines many optional fields with defaults; for these
    endpoint-shape tests we only need to provide the required "urls"
    list and rely on defaults for everything else.
    """

    return {
        "urls": ["https://example.com", "https://example.org"],
    }


def _assert_capture_shape(body: Dict[str, Any], expected_count: int) -> None:
    assert "results" in body
    assert isinstance(body["results"], list)
    assert len(body["results"]) == expected_count
    assert "request_id" in body
    assert "cancelled" in body


def test_parallel_capture_endpoint_shape(client: ClientFixture) -> None:
    """POST /api/screenshots/capture returns the expected shape."""

    resp = client.post("/api/screenshots/capture", json=_base_request_body())
    assert resp.status_code == 200
    body = resp.json()
    _assert_capture_shape(body, expected_count=2)


def test_sequential_capture_endpoint_shape(client: ClientFixture) -> None:
    """POST /api/screenshots/capture-sequential returns the expected shape."""

    resp = client.post("/api/screenshots/capture-sequential", json=_base_request_body())
    assert resp.status_code == 200
    body = resp.json()
    _assert_capture_shape(body, expected_count=2)

