"""HTTP-level tests for API interception endpoints.

These tests convert parts of test_api_interception.py into pytest
coverage using FastAPI's TestClient, with a fake ScreenshotService so
we do not depend on a real browser or network activity.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient


try:  # Support both package and script execution contexts
    from backend.app.routers import network as network_router  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
    from app.routers import network as network_router  # type: ignore


ClientFixture = TestClient


class FakeScreenshotService:
    def __init__(self) -> None:
        self.intercepted_apis: List[Dict[str, Any]] = []
        self.max_intercepted_apis: int = 100


@pytest.fixture
def fake_screenshot_service(monkeypatch) -> FakeScreenshotService:
    """Patch get_screenshot_service to return an in-memory fake."""

    fake = FakeScreenshotService()
    monkeypatch.setattr(network_router, "get_screenshot_service", lambda: fake)
    return fake


def _manual_api_payload() -> Dict[str, Any]:
    return {
        "url": "/api/test/dealer-master",
        "method": "GET",
        "status": 200,
        "response_json": {
            "data": {
                "dealerName": "Test Motors",
                "id": "TEST123",
                "dealerAddress": [
                    {"city": "San Francisco", "state": "CA", "zipCode": "94102"}
                ],
            }
        },
    }


def test_intercepted_apis_crud_flow(client: ClientFixture, fake_screenshot_service: FakeScreenshotService) -> None:
    """End-to-end flow: list -> add manual API -> list -> clear."""

    # Initially empty
    resp = client.get("/api/network/intercepted-apis")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0

    # Add a manual API
    resp = client.post("/api/network/add-manual-api", json=_manual_api_payload())
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["api"]["url"] == "/api/test/dealer-master"

    # List again – should see one API
    resp = client.get("/api/network/intercepted-apis")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert len(body["apis"]) == 1

    # Clear all APIs
    resp = client.delete("/api/network/intercepted-apis")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True

    # Verify cleared
    resp = client.get("/api/network/intercepted-apis")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0


def test_refresh_apis_returns_static_message(client: ClientFixture) -> None:
    """POST /api/network/refresh-apis returns the expected informational message."""

    resp = client.post(
        "/api/network/refresh-apis",
        json={"url": "https://example.com/page"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "Real Browser mode" in body["message"]

