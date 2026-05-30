"""Unit tests for APIExtractionService.

These tests are based on the manual test_network_api.py script but are
structured as regular pytest tests against the service class directly.
"""

from __future__ import annotations

from typing import Dict, Any

from api_extraction_service import APIExtractionService


def _sample_response() -> Dict[str, Any]:
    return {
        "data": {
            "dealerName": "ABC Motors",
            "id": "123",
            "universalDealerId": "UNI-123",
            "dealerAddress": [
                {"city": "New York", "state": "NY", "zipCode": "10001"},
                {"city": "Los Angeles", "state": "CA", "zipCode": "90001"},
            ],
            "inventoryConfig": {"agedInventory": True, "maxInventoryDays": 90},
            "features": [
                {
                    "name": "Parts Management",
                    "enabled": True,
                    "subFeatures": [
                        {"name": "Inventory Tracking", "enabled": True},
                        {"name": "Order Management", "enabled": False},
                    ],
                }
            ],
        }
    }


def test_auto_generate_metadata_produces_fields() -> None:
    service = APIExtractionService()
    response = _sample_response()

    metadata = service.auto_generate_metadata(response["data"], prefix="data")

    assert isinstance(metadata, dict)
    assert len(metadata) > 0
    # Spot-check one expected field ID exists
    assert any("dealerName" in field_id for field_id in metadata.keys())


def test_extract_fields_uses_metadata() -> None:
    service = APIExtractionService()
    response = _sample_response()
    metadata = service.auto_generate_metadata(response["data"], prefix="data")

    extracted = service.extract_fields_from_response(response, metadata)

    assert isinstance(extracted, dict)
    assert len(extracted) == len(metadata)


def test_validate_response_returns_summary() -> None:
    service = APIExtractionService()
    response = _sample_response()
    metadata = service.auto_generate_metadata(response["data"], prefix="data")

    validation = service.validate_response(response, metadata)

    assert validation["total_fields"] == len(metadata)
    assert validation["fields_found"] <= validation["total_fields"]


def test_compare_environments_detects_differences() -> None:
    service = APIExtractionService()
    base = _sample_response()

    dev = base
    staging = _sample_response()
    staging["data"]["dealerName"] = "ABC Motors (Staging)"
    prod = _sample_response()
    prod["data"]["dealerName"] = "ABC Motors (Production)"
    prod["data"]["inventoryConfig"]["maxInventoryDays"] = 60

    metadata = service.auto_generate_metadata(base["data"], prefix="data")

    def extract(resp):
        return {"extracted_fields": service.extract_fields_from_response(resp, metadata)}

    comparison = service.compare_environments(
        {
            "dev": extract(dev),
            "staging": extract(staging),
            "prod": extract(prod),
        }
    )

    assert comparison["summary"]["total_fields"] == len(metadata)
    assert comparison["summary"]["fields_with_differences"] >= 1

