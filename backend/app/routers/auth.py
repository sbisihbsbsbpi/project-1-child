"""Authentication stub routes for the Screenshot Tool backend.

These endpoints are intentionally disabled but exposed for
backwards-compatibility with earlier desktop shells.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:  # Support both package and script execution contexts for models
	from backend.app import models  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
	from app import models  # type: ignore


router = APIRouter()


@router.post("/api/auth/start-login")
async def start_login(request: models.LoginRequest):
	"""Disabled auth start-login endpoint.

	Always returns HTTP 501 with a clear message.
	"""

	return JSONResponse(
		{
			"status": "disabled",
			"message": "Authentication features are disabled. This is a screenshot tool only.",
			"feature": "auth/start-login",
		},
		status_code=501,
	)


@router.get("/api/auth/status")
async def get_auth_status():
	"""Disabled auth status endpoint.

	Always returns HTTP 501 with a clear message.
	"""

	return JSONResponse(
		{
			"status": "disabled",
			"message": "Authentication features are disabled. This is a screenshot tool only.",
			"feature": "auth/status",
			"exists": False,
		},
		status_code=501,
	)


@router.delete("/api/auth/clear")
async def clear_auth_state():
	"""Disabled auth clear endpoint.

	Always returns HTTP 501 with a clear message.
	"""

	return JSONResponse(
		{
			"status": "disabled",
			"message": "Authentication features are disabled. This is a screenshot tool only.",
			"feature": "auth/clear",
		},
		status_code=501,
	)


@router.post("/api/auth/save-from-extension")
async def save_auth_from_extension(storage_state: dict):
	"""Disabled auth save-from-extension endpoint.

	Always returns HTTP 501 with a clear message.
	"""

	return JSONResponse(
		{
			"status": "disabled",
			"message": "Authentication features are disabled. This is a screenshot tool only.",
			"feature": "auth/save-from-extension",
		},
		status_code=501,
	)
