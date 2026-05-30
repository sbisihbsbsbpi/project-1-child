"""Document generation routes for the Screenshot Tool backend.

The /api/document/generate route is implemented here and calls the
external Document Service microservice.
"""

from typing import List

import httpx
from fastapi import APIRouter, HTTPException

from logging_config import setup_logging


try:  # Support both package and script execution contexts for models
    from backend.app import models  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
    from app import models  # type: ignore


try:
    from backend.main import (  # type: ignore
        validate_screenshot_path,
        http_client,
        logger,
        _call_microservice,
    )
except ModuleNotFoundError:  # pragma: no cover - script mode
    import main as _main  # type: ignore

    validate_screenshot_path = _main.validate_screenshot_path
    http_client = _main.http_client
    logger = _main.logger
    _call_microservice = _main._call_microservice


try:
    from backend.config import settings  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode
    from config import settings  # type: ignore


router = APIRouter()
router_logger = setup_logging(__name__)


@router.post("/api/document/generate")
async def generate_document(request: models.DocumentRequest):
    """Generate a Word document from screenshots via the Document Service.

    This mirrors the previous :mod:`backend.main` implementation while
    keeping the HTTP handler logic inside the router.
    """

    try:
        logger_to_use = logger if "logger" in globals() else router_logger
        logger_to_use.info(
            "\U0001f4c4 Calling Document Service to generate document with "
            f"{len(request.screenshot_paths)} screenshots"
        )

        # Normalise and validate screenshot paths so the Document Service
        # only ever receives safe, absolute paths within the screenshots
        # directory.
        normalized_paths: List[str] = []
        for raw in request.screenshot_paths:
            safe_path = validate_screenshot_path(raw)
            normalized_paths.append(str(safe_path))

        # Call Document Service via the shared microservice helper so we
        # benefit from connection pooling and basic retry/backoff.
        response = await _call_microservice(
            "POST",
            f"{settings.document_service_url}/generate",
            json_body={
                "screenshot_paths": normalized_paths,
                "output_path": request.output_path,
                "title": request.title,
            },
            timeout=60.0,
            retries=2,
            backoff=0.3,
        )

        # Check if request was successful
        if response.status_code != 200:
            logger_to_use.error(
                f"\u274c Document Service returned error: {response.status_code}"
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Document Service error: {response.text}",
            )

        result = response.json()
        logger_to_use.info(
            f"\u2705 Document generated successfully: {result.get('document_path')}"
        )

        return {
            "status": "success",
            "output_path": result.get("document_path"),
            "screenshot_count": result.get("screenshot_count"),
            "generated_at": result.get("generated_at"),
        }

    except HTTPException:
        # Propagate intentional HTTP errors (e.g., path validation failures)
        raise
    except httpx.RequestError as e:
        # Network/connection errors
        logger_to_use = logger if "logger" in globals() else router_logger
        logger_to_use.error(f"\u274c Failed to connect to Document Service: {e}")
        raise HTTPException(
            status_code=503,
            detail=(
                f"Document Service unavailable: {str(e)}. "
                "Make sure the service is running on port 8002."
            ),
        )
    except Exception as e:
        # Other errors
        logger_to_use = logger if "logger" in globals() else router_logger
        logger_to_use.error(f"\u274c Error generating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

