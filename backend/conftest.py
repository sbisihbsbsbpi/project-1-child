import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Ensure both the repository root and the backend directory are on
# sys.path so that "import main" (script-style) and "import backend.*"
# (package-style) work under pytest.
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

for entry in (str(ROOT_DIR), str(BACKEND_DIR)):
	if entry not in sys.path:
		sys.path.insert(0, entry)


from main import create_app  # type: ignore  # pragma: no cover - script-style main


@pytest.fixture(scope="session")
def app():
    """Create a FastAPI app instance for backend tests.

    Uses the canonical create_app factory so tests exercise the same
    wiring as production.
    """

    return create_app()


@pytest.fixture()
def client(app):
    """Return a TestClient bound to the backend app."""

    return TestClient(app)

