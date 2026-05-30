"""Screenshot-related routes for the Screenshot Tool backend.

Routers now host the HTTP implementations for screenshot operations,
while still reusing shared helpers and services from the core modules.
"""

from typing import Dict
from pathlib import Path
import asyncio
from datetime import datetime

import os
import platform
import subprocess

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

try:  # Support both package and script execution contexts for models
	from backend.app import models  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
	from app import models  # type: ignore

try:  # Shared helpers and cancellation registry still live in backend.main
	from backend.main import (  # type: ignore
		validate_screenshot_path,
		cancellation_registry,
		_validate_single_url,
		_resolve_capture_timeout,
		check_quality_via_service,
	)
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
	import main as _main  # type: ignore

	validate_screenshot_path = _main.validate_screenshot_path
	cancellation_registry = _main.cancellation_registry
	_validate_single_url = _main._validate_single_url  # type: ignore[attr-defined]
	_resolve_capture_timeout = _main._resolve_capture_timeout  # type: ignore[attr-defined]
	check_quality_via_service = _main.check_quality_via_service  # type: ignore[attr-defined]

try:  # Capture orchestration service
	from backend.app.services import (  # type: ignore
		CaptureOrchestrator,
		get_capture_orchestrator,
	)
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
	from app.services import CaptureOrchestrator, get_capture_orchestrator  # type: ignore

try:
	from backend.app.services import get_screenshot_service  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
	from app.services import get_screenshot_service  # type: ignore

try:
	from backend.config import settings  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
	from config import settings  # type: ignore


# Global concurrency cap for screenshot capture requests across both
# parallel and sequential endpoints. This prevents unbounded concurrent
# Real Browser sessions in long-running deployments.
_capture_concurrency_semaphore = asyncio.Semaphore(settings.max_concurrent_captures)


router = APIRouter()


@router.post("/api/screenshots/cancel")
async def cancel_screenshots(request: models.CancelRequest) -> Dict[str, str]:
	"""Cancel ongoing screenshot capture operations.

	Accepts an optional request_id in the JSON body. When omitted or null,
	all active requests are cancelled (backwards-compatible behaviour).
	"""

	request_id = request.request_id

	# Cancel specific request or all requests
	if request_id and cancellation_registry.cancel(request_id):
		return {
			"status": "success",
			"message": f"Cancellation requested for request {request_id}",
		}
	elif not request_id:
		# Cancel all active requests (backward compatibility)
		count = cancellation_registry.cancel_all()
		return {
			"status": "success",
			"message": f"Cancellation requested for {count} active request(s)",
		}
	else:
		return {
			"status": "not_found",
			"message": f"Request {request_id} not found or already completed",
		}


@router.post("/api/screenshots/capture")
async def capture_screenshots(
	request: models.URLRequest,
	orchestrator: CaptureOrchestrator = Depends(get_capture_orchestrator),
):
	"""Parallel screenshot capture using the CaptureOrchestrator service."""
	async with _capture_concurrency_semaphore:
		return await orchestrator.capture(request)


@router.post("/api/screenshots/capture-sequential")
async def capture_screenshots_sequential(
	request: models.URLRequest,
	orchestrator: CaptureOrchestrator = Depends(get_capture_orchestrator),
):
	"""Legacy sequential screenshot capture via CaptureOrchestrator."""
	async with _capture_concurrency_semaphore:
		return await orchestrator.capture_sequential(request)


@router.get("/api/screenshots/file/{file_path:path}")
async def get_screenshot_file(file_path: str) -> FileResponse:
    """Serve screenshot file for preview.

    Uses validate_screenshot_path to protect against directory traversal.
    """

    validated_path = validate_screenshot_path(file_path)
    return FileResponse(str(validated_path))


@router.post("/api/screenshots/open-file")
async def open_file(path: str) -> Dict[str, str]:
    """Open a screenshot file in the default image viewer."""

    validated_path = validate_screenshot_path(path)

    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(validated_path)], timeout=10)
        elif system == "Windows":
            os.startfile(str(validated_path))
        else:  # Linux
            subprocess.run(["xdg-open", str(validated_path)], timeout=10)

        return {"status": "success", "message": "File opened"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "File open timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/api/screenshots/open-folder")
async def open_folder(path: str) -> Dict[str, str]:
    """Open the folder containing the screenshot file."""

    validated_path = validate_screenshot_path(path)
    folder_path = Path(validated_path).parent

    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)], timeout=10)
        elif system == "Windows":
            os.startfile(str(folder_path))
        else:  # Linux
            subprocess.run(["xdg-open", str(folder_path)], timeout=10)

        return {"status": "success", "message": "Folder opened"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Folder open timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/api/screenshots/retry")
async def retry_screenshot(url: str, viewport_width: int = 1920, viewport_height: int = 1080):
	"""Retry capturing a single screenshot for the given URL.

	This inlines the former ``backend.main.retry_screenshot`` logic so
	the HTTP route and its implementation live together in the router.
	"""

	screenshot_service = get_screenshot_service()

	try:
		# Reuse shared URL validation rules to prevent SSRF/DoS
		_validate_single_url(url)

		# Construct a minimal URLRequest to reuse centralized timeout logic
		dummy_request = models.URLRequest(
			urls=[url], viewport_width=viewport_width, viewport_height=viewport_height
		)
		capture_timeout = _resolve_capture_timeout(
			batch_timeout=dummy_request.batch_timeout,
			use_real_browser=dummy_request.use_real_browser,
			browser_engine=dummy_request.browser_engine,
			use_stealth=dummy_request.use_stealth,
			capture_mode=dummy_request.capture_mode,
		)
		screenshot_timeout_ms = int(capture_timeout * 1000)

		try:
			screenshot_path = await asyncio.wait_for(
				screenshot_service.capture(
					url=url,
					viewport_width=dummy_request.viewport_width,
					viewport_height=dummy_request.viewport_height,
					full_page=True,
					screenshot_timeout=screenshot_timeout_ms,
					use_stealth=dummy_request.use_stealth,
					use_real_browser=dummy_request.use_real_browser,
					headless=dummy_request.headless,
					browser_engine=dummy_request.browser_engine,
					base_url=dummy_request.base_url,
					words_to_remove=dummy_request.words_to_remove,
					cookies=dummy_request.cookies,
					local_storage=dummy_request.local_storage,
					track_network=dummy_request.track_network,
					auto_expand_dropdowns=dummy_request.auto_expand_dropdowns,
					click_elements=dummy_request.click_elements,
					non_scrollable_urls=dummy_request.non_scrollable_urls,
				),
				timeout=capture_timeout,
			)
		except asyncio.TimeoutError:
			mode = "real browser" if dummy_request.use_real_browser else "headless"
			raise Exception(f"Screenshot capture timed out after {capture_timeout}s ({mode} mode)")

		if not screenshot_path:
			raise Exception("Screenshot capture returned no file path")

		# 🔄 MICROSERVICES: Call Quality Service
		quality_result = await check_quality_via_service(screenshot_path)

		return models.ScreenshotResult(
			url=url,
			status="success" if quality_result["passed"] else "failed",
			screenshot_path=screenshot_path,
			quality_score=quality_result["score"],
			quality_issues=quality_result["issues"],
			timestamp=datetime.now().isoformat(),
		)
	except Exception as e:
		return models.ScreenshotResult(
			url=url,
			status="failed",
			error=str(e),
			timestamp=datetime.now().isoformat(),
		)
