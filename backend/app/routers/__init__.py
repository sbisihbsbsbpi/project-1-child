"""Router package for the Screenshot Tool backend.

Phase 1: routers are introduced incrementally. Initially, system
routes and a subset of screenshot routes are registered here; other
functional areas (network, config) will be moved in later phases.
"""

from . import system  # noqa: F401
from . import screenshots  # noqa: F401
from . import network  # noqa: F401
from . import document  # noqa: F401
from . import config  # noqa: F401
from . import auth  # noqa: F401
from . import browser  # noqa: F401
from . import tabs  # noqa: F401

__all__ = [
    "system",
    "screenshots",
    "network",
    "document",
    "config",
    "auth",
    "browser",
    "tabs",
]

