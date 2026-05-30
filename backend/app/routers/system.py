"""System-level routes for the Screenshot Tool backend.

This router handles health checks, root metadata and lightweight
system usage metrics. It now depends only on core helpers and
configuration, rather than importing from ``backend.main``.
"""

from datetime import datetime
from typing import Dict

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from logging_config import setup_logging

try:  # Core helper for resource usage metrics
	from backend.app.core.system import _get_backend_resource_usage  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
	from app.core.system import _get_backend_resource_usage  # type: ignore

try:
	from backend.config import settings  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
	from config import settings  # type: ignore


router = APIRouter()
logger = setup_logging(__name__)


@router.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with basic service metadata."""

    return {
        "name": "Screenshot Tool API",
        "version": "1.0.0",
        "status": "running",
    }


@router.get("/health")
async def health() -> Dict[str, str]:
    """Simple health check endpoint used by the desktop shell."""

    return {"status": "healthy"}


@router.get("/api/system/usage")
async def system_usage() -> Dict:
    """Return backend, system and browser usage metrics for the desktop UI.

    This endpoint is intentionally lightweight and read-only. It is polled
    every few seconds by the frontend to render the status bar. Metrics are
    approximate but good enough for understanding load and making decisions
    about parallelism.
    """

    # Offload psutil-based process iteration to a thread to avoid
    # blocking the event loop under load.
    loop = asyncio.get_running_loop()
    usage = await loop.run_in_executor(None, _get_backend_resource_usage)
    if not usage:
        return {
            "status": "error",
            "message": "Resource usage unavailable on this platform",
            "timestamp": datetime.now().isoformat(),
        }

    usage.update(
        {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        }
    )
    return usage


@router.post("/api/restart")
async def restart_backend():
	"""Restart the backend server (non-production only).

	This mirrors :func:`backend.main.restart_backend` but lives alongside
	the other system routes.
	"""

	# 👮 SECURITY: Restart can be toggled via configuration so that
	# production or shared environments can disable it while local
	# desktop use keeps it convenient.
	if not getattr(settings, "allow_restart_endpoint", True):
		raise HTTPException(
			status_code=403, detail="Restart endpoint is disabled in this environment"
		)

	try:
		logger.info("🔄 Backend restart requested")

		# Touch the main.py file to trigger uvicorn reload
		main_file = Path(__file__)
		main_file.touch()

		logger.info("✅ Backend restart triggered")

		return JSONResponse(
			{
				"status": "success",
				"message": "Backend is restarting...",
			}
		)
	except Exception as e:  # pragma: no cover - defensive
		logger.error(f"❌ Failed to restart backend: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))
