"""Authentication-related Pydantic models.

These are small request models used by the (currently disabled)
authentication endpoints. They live in the models package to avoid
import-time circular dependencies with ``backend.main``.
"""

from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Request model for starting a login flow.

    Note: the corresponding auth routes are currently disabled and
    always return a 501 status, but we keep the model for backwards
    compatibility.
    """

    url: str
    browser_engine: str = "playwright"  # "playwright" or "camoufox"


__all__ = ["LoginRequest"]

