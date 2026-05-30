"""App factory for the Screenshot Tool FastAPI backend.

This module simply re-exports the create_app() factory defined in
backend.main. The actual router wiring happens in backend.main to
support both package and script execution contexts.
"""

from fastapi import FastAPI

try:  # Support both package and script execution contexts
    from backend.main import create_app as _create_app  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - script mode (python backend/main.py)
    import main as _main  # type: ignore

    def _create_app() -> FastAPI:
        return _main.create_app()


def create_app() -> FastAPI:
    """Return the configured Screenshot Tool FastAPI application."""

    return _create_app()
