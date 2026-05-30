"""Pydantic models facade for the Screenshot Tool backend.

Routers and services should import request/response models from this
package instead of ``backend.main`` to avoid tight coupling to the
application bootstrap module.
"""

from .screenshot import CancelRequest, URLRequest, ScreenshotResult, DocumentRequest
from .auth import LoginRequest
from .network import (
	ExportCurlRequest,
	GenerateMetadataRequest,
	ExtractFieldsRequest,
	ValidateResponseRequest,
	CompareEnvironmentsRequest,
	RefreshApisRequest,
	ManualApiRequest,
	APIExtractionRequest,
	APIExtractionResult,
)
from .config import (
	MAX_BATCH_TIMEOUT_SECONDS,
	BatchTimeoutRequest,
	FilePathsUpdateRequest,
	UrlConfig,
	UrlConfigUpdate,
)


__all__ = [
	"MAX_BATCH_TIMEOUT_SECONDS",
	"BatchTimeoutRequest",
	"ExportCurlRequest",
	"FilePathsUpdateRequest",
	"GenerateMetadataRequest",
	"ExtractFieldsRequest",
	"ValidateResponseRequest",
	"CompareEnvironmentsRequest",
	"RefreshApisRequest",
	"ManualApiRequest",
	"UrlConfig",
	"UrlConfigUpdate",
	"CancelRequest",
	"URLRequest",
	"ScreenshotResult",
	"DocumentRequest",
	"LoginRequest",
	"APIExtractionRequest",
	"APIExtractionResult",
]

