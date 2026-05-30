"""Network/API extraction and config-related models.

These were originally defined in backend.main and are now the
canonical definitions, re-exported via backend.app.models.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExportCurlRequest(BaseModel):
    """Request model for exporting network events as cURL commands."""

    network_events: List[Dict[str, Any]] = Field(default_factory=list)


class GenerateMetadataRequest(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)
    prefix: str = "data"
    max_depth: int = 10


class ExtractFieldsRequest(BaseModel):
    response_data: Dict[str, Any] = Field(default_factory=dict)
    field_mappings: Dict[str, Any] = Field(default_factory=dict)


class ValidateResponseRequest(BaseModel):
    response_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompareEnvironmentsRequest(BaseModel):
    extractions: Dict[str, Any] = Field(default_factory=dict)


class RefreshApisRequest(BaseModel):
    url: str


class ManualApiRequest(BaseModel):
    url: str
    method: str = "GET"
    status: int = 200
    response_json: Dict[str, Any] = Field(default_factory=dict)


class APIExtractionRequest(BaseModel):
    """Request model for API extraction."""

    url: str
    api_url_pattern: str
    auto_generate_metadata: bool = True
    existing_metadata: Optional[Dict[str, Any]] = None
    timeout_ms: int = 30000


class APIExtractionResult(BaseModel):
    """Response model for API extraction."""

    api_url: str
    method: str
    status: int
    timestamp: str
    metadata: Dict[str, Any]
    extracted_fields: Dict[str, Any]
    raw_response: Optional[Dict[str, Any]] = None


__all__ = [
    "ExportCurlRequest",
    "GenerateMetadataRequest",
    "ExtractFieldsRequest",
    "ValidateResponseRequest",
    "CompareEnvironmentsRequest",
    "RefreshApisRequest",
    "ManualApiRequest",
    "APIExtractionRequest",
    "APIExtractionResult",
]

