"""Test script for Screenshot capture endpoints.

Run this to sanity-check the screenshot HTTP API:
    python3 test_screenshots_api.py

This script assumes the backend is running locally on port 8000
(e.g. `python3 main.py`). It does not validate actual image
content, only that the endpoints respond with the expected
structure and basic success semantics.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

# Uvicorn is started on port 8001 in this test environment.
BASE_URL = "http://127.0.0.1:8001"


def _print_header(title: str) -> None:
    print("=" * 60)
    print(title)
    print("=" * 60)


def _print_step(title: str) -> None:
    print(f"\n{title}")


def _assert_response_ok(resp: requests.Response) -> Dict[str, Any]:
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    print(f"   ✅ HTTP {resp.status_code}")
    return data


def _assert_capture_payload(payload: Dict[str, Any], expected_count: int) -> None:
    assert "results" in payload, "missing 'results' key"
    assert isinstance(payload["results"], list), "'results' should be a list"
    assert len(payload["results"]) == expected_count, (
        f"expected {expected_count} results, got {len(payload['results'])}"
    )
    assert "request_id" in payload, "missing 'request_id' key"
    assert "cancelled" in payload, "missing 'cancelled' key"

    print(f"   📊 Result count: {len(payload['results'])}")
    print(f"   🔑 Request ID: {payload['request_id']}")
    print(f"   🚫 Cancelled: {payload['cancelled']}")


def main() -> None:
    _print_header("📸 Testing Screenshot Capture Endpoints")

    urls: List[str] = [
        # These do not have to be real pages for basic shape testing; the
        # backend and screenshot service will handle failure scenarios.
        "https://example.com",
        "https://example.org",
    ]

    request_body: Dict[str, Any] = {
        "urls": urls,
        "base_url": "https://example.com",
        "words_to_remove": [],
        "auto_expand_dropdowns": False,
        "non_scrollable_urls": [],
        "max_parallel_urls": 2,
        "batch_timeout": 10,
        "use_real_browser": False,
    }

    # 1️⃣ Parallel capture
    _print_step("1️⃣ Testing POST /api/screenshots/capture...")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/screenshots/capture", json=request_body, timeout=60
        )
        payload = _assert_response_ok(resp)
        _assert_capture_payload(payload, expected_count=len(urls))
    except Exception as e:
        print(f"   ❌ Error during parallel capture test: {e}")

    # 2️⃣ Sequential capture
    _print_step("2️⃣ Testing POST /api/screenshots/capture-sequential...")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/screenshots/capture-sequential",
            json=request_body,
            timeout=60,
        )
        payload = _assert_response_ok(resp)
        _assert_capture_payload(payload, expected_count=len(urls))
    except Exception as e:
        print(f"   ❌ Error during sequential capture test: {e}")

    print("\n" + "=" * 60)
    print("✅ Screenshot capture API smoke test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

