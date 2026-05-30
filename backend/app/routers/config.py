"""Configuration-related routes for the Screenshot Tool backend.

This router groups endpoints that manage performance metrics,
filesystem paths and URL-specific click configurations. The
implementations now live here instead of ``backend.main``.
"""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from logging_config import setup_logging

try:  # Support both package and script execution contexts for models
	from backend.app import models  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
	from app import models  # type: ignore

try:  # Shared locks still live in backend.main
	from backend.main import update_batch_timeout_lock, url_configs_lock  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
	import main as _main  # type: ignore

	update_batch_timeout_lock = _main.update_batch_timeout_lock  # type: ignore[attr-defined]
	url_configs_lock = _main.url_configs_lock  # type: ignore[attr-defined]

try:
	from backend.app.services import get_screenshot_service  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
	from app.services import get_screenshot_service  # type: ignore

try:
	from backend.config import settings  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
	from config import settings  # type: ignore

try:
	from backend.app.core.path_security import PathSecurityValidator  # type: ignore
	from backend.app.core.exceptions import PathValidationError  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
	from app.core.path_security import PathSecurityValidator  # type: ignore
	from app.core.exceptions import PathValidationError  # type: ignore


router = APIRouter()
logger = setup_logging(__name__)


@router.post("/api/update-batch-timeout")
async def update_batch_timeout(request: models.BatchTimeoutRequest):
	"""Update batch timeout configuration and regenerate docs.

	This mirrors ``backend.main.update_batch_timeout`` but keeps the
	implementation in the router.
	"""

	async with update_batch_timeout_lock:
		try:
			timeout = request.timeout

			# Read current metrics
			from performance_metrics import metrics, save_batch_timeout  # type: ignore

			current_timeout = metrics.batch_timeout

			# Check if value changed
			if abs(current_timeout - timeout) < 0.1:  # Float comparison with tolerance
				logger.info(f"⏱️ Batch timeout unchanged ({timeout}s), skipping doc generation")
				return {
					"status": "success",
					"message": "Timeout unchanged, no update needed",
					"changed": False,
				}

			# Persist new timeout via configuration helper
			save_batch_timeout(timeout)
			metrics.batch_timeout = timeout
			logger.info(f"⏱️ Updated batch_timeout: {current_timeout}s → {timeout}s")

			# Regenerate documentation (offload to thread to avoid blocking event loop)
			from generate_docs import main as generate_docs  # type: ignore

			loop = asyncio.get_running_loop()
			await loop.run_in_executor(None, generate_docs, False)
			logger.info("📊 Performance documentation regenerated")

			return {
				"status": "success",
				"message": f"Batch timeout updated from {current_timeout}s to {timeout}s",
				"changed": True,
				"old_value": current_timeout,
				"new_value": timeout,
			}

		except Exception as e:  # pragma: no cover - defensive
			logger.error(f"❌ Failed to update batch timeout: {e}")
			raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/config/paths")
async def get_file_paths():
	"""Get current file path configuration.

	Returns all configurable directory paths including:
	- screenshots_dir: Where screenshots are saved
	- browser_sessions_dir: Where browser session data is stored
	- logs_dir: Where log files are written
	- auth_state_file: Authentication state storage
	"""
	screenshot_service = get_screenshot_service()

	return {
		"screenshots_dir": str(screenshot_service.output_dir),
		"screenshots_dir_absolute": str(screenshot_service.output_dir.resolve()),
		"browser_sessions_dir": str(screenshot_service.session_dir),
		"browser_sessions_dir_absolute": str(screenshot_service.session_dir.resolve()),
		"logs_dir": str(Path("logs")),
		"logs_dir_absolute": str(Path("logs").resolve()),
		"auth_state_file": str(settings.auth_state_file),
		"auth_state_file_absolute": str(settings.auth_state_file.resolve()),
		"defaults": {
			"screenshots_dir": "screenshots",
			"browser_sessions_dir": "browser_sessions",
			"logs_dir": "logs",
		}
	}


@router.post("/api/config/paths")
async def update_file_paths(paths: models.FilePathsUpdateRequest):
	"""Update file path configuration with comprehensive security validation.

	Request body:
	{
		"screenshots_dir": "screenshots" or "~/Desktop/My Screenshots",
		"browser_sessions_dir": "browser_sessions" or "~/Documents/Sessions",
		"logs_dir": "logs" or "~/Documents/Logs"
	}

	Security features:
	- Path traversal prevention
	- System directory blocking
	- Depth limit enforcement (max 10 levels)
	- Must be within user home directory
	- Automatic directory creation with secure permissions (0o755)
	"""
	try:
		screenshot_service = get_screenshot_service()
		updated_paths = {}

		# ✅ PHASE 5 (Path Security): Update screenshots directory
		if paths.screenshots_dir:
			user_input = paths.screenshots_dir

			# Validate directory creation with security checks
			validated_dir = PathSecurityValidator.validate_directory_creation(
				path=user_input,
				allowed_parent=Path.home(),
				max_depth=10,
			)

			# Create directory with restricted permissions
			validated_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

			# Update the service's output directory
			screenshot_service.output_dir = validated_dir

			# Update hash cache file location
			screenshot_service._hash_cache_file = validated_dir / ".hash_cache.json"

			logger.info("📁 Updated screenshots directory to: %s", validated_dir)

			updated_paths["screenshots_dir"] = str(validated_dir)
			updated_paths["screenshots_dir_absolute"] = str(validated_dir.resolve())

		# ✅ PHASE 5 (Path Security): Update browser sessions directory
		if paths.browser_sessions_dir:
			user_input = paths.browser_sessions_dir

			# Validate directory creation with security checks
			validated_dir = PathSecurityValidator.validate_directory_creation(
				path=user_input,
				allowed_parent=Path.home(),
				max_depth=10,
			)

			# Create directory with restricted permissions
			validated_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

			# Update the service's session directory
			screenshot_service.session_dir = validated_dir

			# Update cookies file location
			screenshot_service.cookies_file = validated_dir / "cookies.json"

			logger.info("📁 Updated browser sessions directory to: %s", validated_dir)

			updated_paths["browser_sessions_dir"] = str(validated_dir)
			updated_paths["browser_sessions_dir_absolute"] = str(validated_dir.resolve())

		# ✅ PHASE 5 (Path Security): Update logs directory
		if paths.logs_dir:
			user_input = paths.logs_dir

			# Validate directory creation with security checks
			validated_dir = PathSecurityValidator.validate_directory_creation(
				path=user_input,
				allowed_parent=Path.home(),
				max_depth=10,
			)

			# Create directory with restricted permissions
			validated_dir.mkdir(parents=True, exist_ok=True, mode=0o755)

			logger.info("📁 Updated logs directory to: %s", validated_dir)

			updated_paths["logs_dir"] = str(validated_dir)
			updated_paths["logs_dir_absolute"] = str(validated_dir.resolve())

			# Note: Log directory update requires logging reconfiguration
			# This is typically done at startup, not runtime

		if not updated_paths:
			return {"status": "error", "message": "No valid paths provided"}

		return {
			"status": "success",
			"message": f"Updated {len(updated_paths)//2} director{'y' if len(updated_paths)==2 else 'ies'}",
			**updated_paths
		}

	except PathValidationError as e:
		logger.error("Path validation failed: %s", e)
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:  # pragma: no cover - defensive
		logger.error("Failed to update file paths: %s", e)
		raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/config/paths/reset")
async def reset_file_paths():
	"""Reset all file paths to default values.

	Default paths:
	- screenshots_dir: ./screenshots
	- browser_sessions_dir: ./browser_sessions
	- logs_dir: ./logs

	This is useful for recovering from misconfiguration or testing.
	"""
	try:
		screenshot_service = get_screenshot_service()

		# Reset to default paths
		default_screenshots = Path("screenshots").resolve()
		default_sessions = Path("browser_sessions").resolve()
		default_logs = Path("logs").resolve()

		# Create directories with secure permissions
		default_screenshots.mkdir(parents=True, exist_ok=True, mode=0o755)
		default_sessions.mkdir(parents=True, exist_ok=True, mode=0o755)
		default_logs.mkdir(parents=True, exist_ok=True, mode=0o755)

		# Update service paths
		screenshot_service.output_dir = default_screenshots
		screenshot_service.session_dir = default_sessions
		screenshot_service._hash_cache_file = default_screenshots / ".hash_cache.json"
		screenshot_service.cookies_file = default_sessions / "cookies.json"

		logger.info("🔄 Reset all paths to defaults")

		return {
			"status": "success",
			"message": "All paths reset to defaults",
			"screenshots_dir": str(default_screenshots),
			"browser_sessions_dir": str(default_sessions),
			"logs_dir": str(default_logs),
		}

	except Exception as e:  # pragma: no cover - defensive
		logger.error("Failed to reset file paths: %s", e)
		raise HTTPException(status_code=500, detail=str(e))



@router.get("/api/url-configs")
async def get_url_configs():
	"""Get all URL-specific click configurations."""

	try:
		async with url_configs_lock:
			config_file = Path("url_click_config.json")

			if not config_file.exists():
				# Return default empty configuration
				return {
					"version": "1.0",
					"description": "URL-specific click action configurations for screenshot tool",
					"url_patterns": [],
				}

			with open(config_file, "r") as f:
				config = json.load(f)

			return config
	except Exception as e:  # pragma: no cover - defensive
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/url-configs")
async def create_url_config(config: models.UrlConfig):
	"""Create a new URL-specific click configuration."""

	try:
		async with url_configs_lock:
			config_file = Path("url_click_config.json")

			# Load existing configuration
			if config_file.exists():
				with open(config_file, "r") as f:
					full_config = json.load(f)
			else:
				full_config = {
					"version": "1.0",
					"description": "URL-specific click action configurations for screenshot tool",
					"url_patterns": [],
				}

			# Check if ID already exists
			existing_ids = [p.get("id") for p in full_config.get("url_patterns", [])]
			if config.id in existing_ids:
				raise HTTPException(
					status_code=400,
					detail=f"Configuration with ID '{config.id}' already exists",
				)

			# Add new configuration
			full_config["url_patterns"].append(config.model_dump())

			# Save to file
			with open(config_file, "w") as f:
				json.dump(full_config, f, indent=2)

			# Reload configuration in screenshot service
			screenshot_service = get_screenshot_service()
			screenshot_service.url_click_config = screenshot_service._load_url_click_config()

			return {
				"status": "success",
				"message": "Configuration created successfully",
				"config": config.model_dump(),
			}
	except HTTPException:
		# Preserve explicit HTTP errors (e.g., 400 for duplicate IDs)
		raise
	except Exception as e:  # pragma: no cover - defensive
		raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/url-configs/{config_id}")
async def update_url_config(config_id: str, config: models.UrlConfigUpdate):
	"""Update an existing URL-specific click configuration."""

	try:
		async with url_configs_lock:
			config_file = Path("url_click_config.json")

			if not config_file.exists():
				raise HTTPException(status_code=404, detail="Configuration file not found")

			# Load existing configuration
			with open(config_file, "r") as f:
				full_config = json.load(f)

			# Find and update configuration with partial fields
			found = False
			for i, pattern in enumerate(full_config.get("url_patterns", [])):
				if pattern.get("id") == config_id:
					updated = pattern.copy()
					data = config.model_dump(exclude_unset=True)
					# Allow explicit nulls (None) to clear fields such as notes/actions
					updated.update(data)
					full_config["url_patterns"][i] = updated
					found = True
					break

			if not found:
				raise HTTPException(
					status_code=404,
					detail=f"Configuration with ID '{config_id}' not found",
				)

			# Save to file
			with open(config_file, "w") as f:
				json.dump(full_config, f, indent=2)

			# Reload configuration in screenshot service
			screenshot_service = get_screenshot_service()
			screenshot_service.url_click_config = screenshot_service._load_url_click_config()

			return {
				"status": "success",
				"message": "Configuration updated successfully",
				"config": full_config,
			}
	except HTTPException:
		# Preserve explicit HTTP errors (e.g., 404 when config not found)
		raise
	except Exception as e:  # pragma: no cover - defensive
		raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/url-configs/{config_id}")
async def delete_url_config(config_id: str):
	"""Delete a URL-specific click configuration."""

	try:
		async with url_configs_lock:
			config_file = Path("url_click_config.json")

			if not config_file.exists():
				raise HTTPException(status_code=404, detail="Configuration file not found")

			# Load existing configuration
			with open(config_file, "r") as f:
				full_config = json.load(f)

			# Find and remove configuration
			original_length = len(full_config.get("url_patterns", []))
			full_config["url_patterns"] = [
				p
				for p in full_config.get("url_patterns", [])
				if p.get("id") != config_id
			]

			if len(full_config["url_patterns"]) == original_length:
				raise HTTPException(
					status_code=404,
					detail=f"Configuration with ID '{config_id}' not found",
				)

			# Save to file
			with open(config_file, "w") as f:
				json.dump(full_config, f, indent=2)

			# Reload configuration in screenshot service
			screenshot_service = get_screenshot_service()
			screenshot_service.url_click_config = screenshot_service._load_url_click_config()

			return {"status": "success", "message": "Configuration deleted successfully"}
	except HTTPException:
		# Preserve explicit HTTP errors (e.g., 404 when config not found)
		raise
	except Exception as e:  # pragma: no cover - defensive
		raise HTTPException(status_code=500, detail=str(e))
