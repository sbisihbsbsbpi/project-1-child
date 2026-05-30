"""Configuration-related Pydantic models.

These models were originally defined in ``backend.main`` but live here
to avoid import-time circular dependencies between the models package
and the application bootstrap module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Centralized batch timeout limit (shared by model and config routes)
MAX_BATCH_TIMEOUT_SECONDS = 7200


class BatchTimeoutRequest(BaseModel):
	"""Request model for updating batch timeout.

	Keeps the existing JSON shape: {"timeout": <number>}.
	"""

	timeout: float = Field(..., ge=10, le=MAX_BATCH_TIMEOUT_SECONDS)


class FilePathsUpdateRequest(BaseModel):
	"""Request model for updating file path configuration.

	All paths are validated with comprehensive security checks:
	- Path traversal prevention
	- System directory blocking
	- Depth limit enforcement (max 10 levels)
	- Must be within user home directory
	"""

	screenshots_dir: Optional[str] = Field(
		None,
		description="Directory for saving screenshots (e.g., 'screenshots' or '~/Desktop/Screenshots')"
	)
	browser_sessions_dir: Optional[str] = Field(
		None,
		description="Directory for browser session data (e.g., 'browser_sessions' or '~/Documents/Sessions')"
	)
	logs_dir: Optional[str] = Field(
		None,
		description="Directory for log files (e.g., 'logs' or '~/Documents/Logs')"
	)


class UrlConfig(BaseModel):
	id: str
	name: str
	url_pattern: str
	match_type: str
	actions: List[Dict[str, Any]] = Field(default_factory=list)
	enabled: bool = True
	notes: Optional[str] = None


class UrlConfigUpdate(BaseModel):
	name: Optional[str] = None
	url_pattern: Optional[str] = None
	match_type: Optional[str] = None
	actions: Optional[List[Dict[str, Any]]] = None
	enabled: Optional[bool] = None
	notes: Optional[str] = None


__all__ = [
	"MAX_BATCH_TIMEOUT_SECONDS",
	"BatchTimeoutRequest",
	"FilePathsUpdateRequest",
	"UrlConfig",
	"UrlConfigUpdate",
]
