"""High-level HTTP smoke tests for the FastAPI routers.

These tests exercise a small, high-signal subset of endpoints using
FastAPI's TestClient. They are intentionally lightweight and avoid
hitting external microservices or launching real browsers.
"""

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient


# The client fixture is provided by backend/conftest.py
ClientFixture = TestClient


# -------------------- System router --------------------


def test_root_metadata(client: ClientFixture) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body: Dict[str, Any] = response.json()
    assert body.get("name") == "Screenshot Tool API"
    assert body.get("status") in {"running", "healthy", "ok"}


def test_health_ok(client: ClientFixture) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"


# -------------------- Browser router --------------------


def test_cdp_status_shape(client: ClientFixture) -> None:
    response = client.get("/api/cdp-status")
    assert response.status_code == 200
    body = response.json()
    assert body.get("port") == 9223
    # is_listening may be True or False depending on the environment
    assert isinstance(body.get("is_listening"), bool)


# -------------------- Screenshots router --------------------


def test_cancel_screenshots_without_request_id(client: ClientFixture) -> None:
    # Empty JSON body maps to CancelRequest with request_id=None
    response = client.post("/api/screenshots/cancel", json={})
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "success"
    assert "Cancellation requested" in body.get("message", "")


# -------------------- Network router --------------------


def test_network_extract_placeholder(client: ClientFixture) -> None:
    payload = {
        "url": "https://example.com/page",
        "api_url_pattern": "https://api.example.com/*",
    }
    response = client.post("/api/network/extract", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "success"
    assert body.get("message") == "API extraction feature coming soon"
    assert body.get("request", {}).get("url") == payload["url"]


# -------------------- Config router --------------------


def test_config_paths_basic_shape(client: ClientFixture) -> None:
    response = client.get("/api/config/paths")
    assert response.status_code == 200
    body = response.json()
    # Do not assert exact values; just ensure keys exist and are strings
    for key in [
        "screenshots_dir",
        "screenshots_dir_absolute",
        "browser_sessions_dir",
        "auth_state_file",
    ]:
        assert key in body
        assert isinstance(body[key], str)

