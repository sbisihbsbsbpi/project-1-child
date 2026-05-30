"""Browser / DevTools-related routes for the Screenshot Tool backend.

These endpoints launch Chrome/Brave with remote debugging enabled and
query Chrome DevTools Protocol (CDP) status.
"""

import asyncio
import os
import socket
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from logging_config import setup_logging
from app.core.browser_paths import BrowserPathDetector, get_browser_launch_args
from app.core.platform_utils import PlatformDetector, OperatingSystem


router = APIRouter()
logger = setup_logging(__name__)


@router.post("/api/launch-debug-chrome")
async def launch_debug_chrome():
	"""Launch Chrome with remote debugging enabled.

	This mirrors ``backend.main.launch_debug_chrome`` but keeps the
	implementation local to the router.
	"""

	try:
		logger.info("🔴 Debug Chrome launch requested")

		# ✅ FIXED (Bug #13): Validate and sanitize file path
		launcher_path_str = os.path.expanduser(
			"~/Library/Application Support/Google/Chrome-Debug/🔴 CLICK HERE TO LAUNCH DEBUG CHROME.command"
		)
		launcher_path = Path(launcher_path_str).resolve()

		# Validate path is within expected directory
		expected_base = Path.home() / "Library" / "Application Support" / "Google" / "Chrome-Debug"
		try:
			launcher_path.relative_to(expected_base)
		except ValueError:
			logger.error(f"❌ Launcher path outside expected directory: {launcher_path}")
			raise HTTPException(
				status_code=400,
				detail="Invalid launcher path - security violation",
			)

		if not launcher_path.exists():
			logger.error(f"❌ Debug Chrome launcher not found: {launcher_path}")
			raise HTTPException(
				status_code=404,
				detail=(
					"Debug Chrome launcher script not found. Make sure you have installed the "
					"Chrome-Debug launcher in the expected location."
				),
			)

		# Use subprocess without shell for security
		logger.info(f"🚀 Launching Debug Chrome from: {launcher_path}")
		try:
			subprocess.Popen(["open", str(launcher_path)])
		except Exception as e:  # pragma: no cover - defensive
			logger.error(f"❌ Failed to launch Debug Chrome: {e}")
			raise HTTPException(status_code=500, detail=str(e))

		return {"status": "success", "message": "Debug Chrome launch triggered"}
	except HTTPException:
		# Propagate explicit HTTP errors unchanged
		raise
	except Exception as e:  # pragma: no cover - defensive
		logger.error(f"❌ Unexpected error in launch_debug_chrome: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/launch-brave-cdp")
async def launch_brave_cdp():
	"""Ensure Brave is running with CDP on port 9223 using the *real* profile."""

	try:
		logger.info("🦁 Brave CDP launch requested")
		loop = asyncio.get_running_loop()

		# Helper: check if port 9223 is already open (run in executor to avoid blocking event loop)
		def _is_cdp_up() -> bool:
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				try:
					result = sock.connect_ex(("localhost", 9223))
				finally:
					sock.close()
				return result == 0
			except Exception:
				return False

		# First check if something is already listening on 9223
		already_up = await loop.run_in_executor(None, _is_cdp_up)
		if already_up:
			logger.info("🦁 Brave CDP already running on 9223")
			return {"status": "already_running", "port": 9223}

		# Not running - restart Brave with CDP enabled on 9223
		# Use cross-platform browser path detection
		brave_path = BrowserPathDetector.get_brave_path()

		if not brave_path or not brave_path.exists():
			logger.error("❌ Brave not found on this system")
			raise HTTPException(
				status_code=404,
				detail="Brave Browser not found. Please install Brave Browser.",
			)

		# Get platform-specific user data directory
		user_data_dir = BrowserPathDetector.get_browser_user_data_dir("brave")

		# Close all existing Brave instances (best-effort, platform-aware)
		try:
			logger.info("🦁 Killing existing Brave instances (if any)...")
			os_type = PlatformDetector.detect_os()

			if os_type == OperatingSystem.MACOS:
				subprocess.run(["pkill", "-x", "Brave Browser"], check=False)
			elif os_type == OperatingSystem.WINDOWS:
				subprocess.run(["taskkill", "/F", "/IM", "brave.exe"], check=False)
			else:  # Linux
				subprocess.run(["pkill", "-x", "brave"], check=False)
				subprocess.run(["pkill", "-x", "brave-browser"], check=False)
		except Exception as e:  # pragma: no cover - best-effort
			logger.warning(f"⚠️ Failed to kill Brave processes: {e}")

		# Launch Brave with CDP enabled on 9223 using the real profile directory
		logger.info(f"🦁 Launching Brave with CDP on 9223 from: {brave_path}")
		logger.info(f"📁 Using profile: {user_data_dir}")

		# Get platform-specific launch args
		args = get_browser_launch_args("brave", 9223, user_data_dir)
		cmd = [str(brave_path)] + args

		try:
			# Platform-specific process launching
			os_type = PlatformDetector.detect_os()
			if os_type == OperatingSystem.WINDOWS:
				# Windows: Use CREATE_NEW_PROCESS_GROUP
				subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
			else:
				# Unix/macOS: Use start_new_session
				subprocess.Popen(cmd, start_new_session=True)
		except Exception as e:  # pragma: no cover - defensive
			logger.error(f"❌ Failed to launch Brave with CDP: {e}")
			raise HTTPException(status_code=500, detail=str(e))

		return {"status": "started", "port": 9223}
	except HTTPException:
		raise
	except Exception as e:  # pragma: no cover - defensive
		logger.error(f"❌ Unexpected error in launch_brave_cdp: {e}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/cdp-status")
async def get_cdp_status():
	"""Check whether anything is exposing CDP on ``localhost:9223``."""

	try:
		# Offload blocking socket connect to a thread to avoid stalling the event loop
		def _check_cdp_status() -> int:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				return sock.connect_ex(("localhost", 9223))
			finally:
				sock.close()

		loop = asyncio.get_running_loop()
		result = await loop.run_in_executor(None, _check_cdp_status)

		is_listening = result == 0
		logger.info(
			f"CDP status check on 9223: {'UP' if is_listening else 'DOWN'} (code={result})"
		)

		return {
			"port": 9223,
			"is_listening": is_listening,
		}
	except Exception as e:  # pragma: no cover - defensive
		logger.error(f"❌ CDP status check failed: {e}")
		raise HTTPException(status_code=500, detail=str(e))
