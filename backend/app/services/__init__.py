"""Service facade and DI helpers for the Screenshot Tool backend.

Routers depend on this module for service *types* and dependency
providers instead of importing singletons from ``backend.main``
directly. The underlying instances are initialised lazily either in
``backend.main.lifespan`` or on first access via the helpers here.

This version avoids importing ``backend.main`` at module import time to
prevent circular import problems when :mod:`backend.main` imports
submodules from :mod:`backend.app.services`.
"""

from __future__ import annotations


from typing import TYPE_CHECKING
import sys


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from backend.main import (  # type: ignore
        ScreenshotService,
        QualityChecker,
        APIExtractionService,
    )
else:  # At runtime we only need the dependency providers below
    ScreenshotService = object  # type: ignore[assignment]
    QualityChecker = object  # type: ignore[assignment]
    APIExtractionService = object  # type: ignore[assignment]
    from backend.app.services.capture_orchestrator import CaptureOrchestrator  # type: ignore


def _get_main_module():
    """Return the active *main* module for the backend.

    Prefer the already-imported ``main`` module (used when running
    ``python backend/main.py`` or ``python main.py``) so that we share the
    same global singletons that FastAPI initialised via the lifespan
    handler. Fall back to importing :mod:`backend.main` for test and
    package-import contexts.
    """

    # Script / uvicorn mode: ``main`` is the module actually used by the
    # running server (uvicorn is started with "main:create_app"). In that
    # case we *must* use this module so that globals like
    # ``screenshot_service`` and ``quality_checker`` are the ones
    # initialised by the lifespan handler.
    main_mod = sys.modules.get("main")
    if main_mod is not None and hasattr(main_mod, "get_capture_orchestrator"):
        return main_mod

    # Fallback: import backend.main (pytest or library usage)
    try:
        import backend.main as _main  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - script mode edge cases
        import main as _main  # type: ignore

    return _main


def get_api_extraction_service() -> "APIExtractionService":
    """Return the shared :class:`APIExtractionService` instance.

    If the instance has not yet been created (for example when used
    outside of the FastAPI lifespan), it is initialised lazily here and
    stored back on ``backend.main``.
    """

    _main = _get_main_module()
    if _main.api_extraction_service is None:  # type: ignore[truthy-function]
        _main.api_extraction_service = _main.APIExtractionService()  # type: ignore[assignment]
    return _main.api_extraction_service  # type: ignore[return-value]


def get_screenshot_service() -> "ScreenshotService":
    """Return the shared :class:`ScreenshotService` instance.

    This helper mirrors :func:`get_api_extraction_service` but for the
    screenshot capture service. Instances are normally created in
    ``backend.main.lifespan``; this function initialises them lazily when
    used in tests or other non-lifespan contexts.
    """

    _main = _get_main_module()
    if _main.screenshot_service is None:  # type: ignore[truthy-function]
        _main.screenshot_service = _main.ScreenshotService()  # type: ignore[assignment]
    return _main.screenshot_service  # type: ignore[return-value]


def get_capture_orchestrator() -> "CaptureOrchestrator":
    """Return the shared :class:`CaptureOrchestrator` instance.

    This delegates to :func:`backend.main.get_capture_orchestrator` so there is
    a single source of truth for orchestrator lifecycle while keeping routers
    decoupled from :mod:`backend.main`.
    """

    _main = _get_main_module()
    return _main.get_capture_orchestrator()  # type: ignore[no-any-return]


__all__ = [
    "ScreenshotService",
    "QualityChecker",
    "APIExtractionService",
    "CaptureOrchestrator",
    "get_api_extraction_service",
    "get_screenshot_service",
    "get_capture_orchestrator",
]
