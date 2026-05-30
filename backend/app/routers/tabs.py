"""Browser tab cleanup and status routes for the Screenshot Tool backend.

These endpoints now contain their own implementations instead of
delegating to ``backend.main``.
"""

from fastapi import APIRouter, HTTPException

from logging_config import setup_logging

try:  # Service access (works in both package and script contexts)
	from backend.app.services import get_screenshot_service  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
	from app.services import get_screenshot_service  # type: ignore


router = APIRouter()
logger = setup_logging(__name__)


@router.post("/api/tabs/cleanup")
async def force_cleanup_tabs():
	"""Force cleanup **all** open tabs in the browser.

	This mirrors the previous ``backend.main.force_cleanup_tabs``
	behaviour but keeps the implementation local to the router.
	"""

	try:
		screenshot_service = get_screenshot_service()
		logger.info("🧹 Force cleanup requested - closing ALL tabs (including failed)...")

		# Delegate tab closing to TabRegistry for proper encapsulation
		closed_count = await screenshot_service.tab_registry.clear_all()
		logger.info(f"🧹 Cleanup complete: {closed_count} tabs closed")

		return {
			"success": True,
			"closed_count": closed_count,
			"message": f"Closed {closed_count} tab(s) successfully",
		}
	except Exception as e:  # pragma: no cover - defensive
		logger.error(f"❌ Tab cleanup error: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/tabs/status")
async def get_tabs_status():
	"""Return the current status of tracked browser tabs."""

	try:
		screenshot_service = get_screenshot_service()
		tab_registry = getattr(screenshot_service, "tab_registry", None)
		tracked = len(tab_registry.tabs) if tab_registry is not None else 0

		return {
			"success": True,
			"tracked_tabs": tracked,
			"message": f"Currently tracking {tracked} tab(s)",
		}
	except Exception as e:  # pragma: no cover - defensive
		logger.error(f"❌ Tab status error: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))
