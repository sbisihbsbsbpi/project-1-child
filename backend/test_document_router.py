"""Tests for the /api/document/generate endpoint.

These tests validate the behaviour of the document router in isolation
from the real Document Service microservice by monkeypatching the
internal helper used to call it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import httpx
import pytest
from fastapi.testclient import TestClient


try:  # Support both package and script-style imports
    from backend.app.routers import document as document_router  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
    from app.routers import document as document_router  # type: ignore


ClientFixture = TestClient


class FakeResponse:
    """Minimal stand-in for httpx.Response used in tests."""

    def __init__(self, status_code: int, json_data: Dict[str, Any], text: str | None = None) -> None:
        self.status_code = status_code
        self._json = json_data
        self.text = text or ""

    def json(self) -> Dict[str, Any]:  # pragma: no cover - trivial
        return self._json


@pytest.fixture(autouse=True)
def patch_validate_screenshot_path(monkeypatch, tmp_path: Path) -> None:
    """Avoid filesystem dependencies in tests.

    The real validate_screenshot_path enforces that paths exist inside the
    configured screenshots directory. For these tests we only care that
    the router *calls* it, not the actual filesystem checks, so we
    replace it with a lightweight version that returns a Path inside a
    temporary directory.
    """

    def _fake_validate(path: str) -> Path:
        return tmp_path / path

    monkeypatch.setattr(document_router, "validate_screenshot_path", _fake_validate)


def _base_payload() -> Dict[str, Any]:
    return {
        "screenshot_paths": ["a.png", "b.png"],
        "output_path": "out.docx",
        "title": "Test Document",
    }


def test_generate_document_happy_path(client: ClientFixture, monkeypatch) -> None:
    """Document generation returns success when microservice returns 200."""

    async def _fake_call(
        method: str,
        url: str,
        *,
        json_body: Dict[str, Any] | None = None,
        timeout: float,
        retries: int,
        backoff: float,
    ) -> FakeResponse:
        assert method == "POST"
        assert url.endswith("/generate")
        # Ensure router forwards the relevant payload fields
        assert json_body is not None
        assert "screenshot_paths" in json_body
        assert "output_path" in json_body
        assert "title" in json_body
        return FakeResponse(
            200,
            {
                "document_path": "/tmp/generated.docx",
                "screenshot_count": len(json_body["screenshot_paths"]),
                "generated_at": "2024-01-01T00:00:00",
            },
            text="ok",
        )

    monkeypatch.setattr(document_router, "_call_microservice", _fake_call)

    response = client.post("/api/document/generate", json=_base_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["output_path"] == "/tmp/generated.docx"
    assert body["screenshot_count"] == 2


def test_generate_document_non_200_maps_to_http_error(client: ClientFixture, monkeypatch) -> None:
    """Non-200 responses from Document Service surface as HTTP errors."""

    async def _fake_call(
        method: str,
        url: str,
        *,
        json_body: Dict[str, Any] | None = None,
        timeout: float,
        retries: int,
        backoff: float,
    ) -> FakeResponse:
        return FakeResponse(500, {"error": "boom"}, text="boom")

    monkeypatch.setattr(document_router, "_call_microservice", _fake_call)

    response = client.post("/api/document/generate", json=_base_payload())
    assert response.status_code == 500
    detail = response.json().get("detail", "")
    assert "Document Service error" in detail
    assert "boom" in detail


def test_generate_document_request_error_returns_503(client: ClientFixture, monkeypatch) -> None:
    """Network errors when calling Document Service return 503 to callers."""

    async def _raise_request_error(*args: Any, **kwargs: Any) -> FakeResponse:
        request = httpx.Request("POST", "http://document-service/generate")
        raise httpx.RequestError("network failure", request=request)

    monkeypatch.setattr(document_router, "_call_microservice", _raise_request_error)

    response = client.post("/api/document/generate", json=_base_payload())
    assert response.status_code == 503
    detail = response.json().get("detail", "")
    assert "Document Service unavailable" in detail

