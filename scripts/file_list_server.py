"""
Simple file listing service on http://127.0.0.1:1234

Provides:
  GET /health -> {"status":"ok"}
  GET /files  -> {"files":["relative/path", ...]}

Designed for the frontend src/file-list-ui.ts panel.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, Iterable, List

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware


REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories to exclude from walking to keep it fast and noise-free
EXCLUDE_DIR_NAMES = {
    ".git",
    ".backup",
    "node_modules",
    "dist",
    "build",
    "target",
    "__pycache__",
}

# Paths (relative to repo root) to exclude entirely
EXCLUDE_PATH_PREFIXES = {
    "backend/.venv",
    "frontend/src-tauri/target",
    "GitNexus/gitnexus/node_modules",
}


def should_exclude(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    # Any excluded prefix?
    rel_str = rel.as_posix()
    if any(rel_str.startswith(pref + "/") or rel_str == pref for pref in EXCLUDE_PATH_PREFIXES):
        return True
    # Any excluded directory name in the chain?
    return any(part in EXCLUDE_DIR_NAMES for part in rel.parts)


def iter_files(root: Path) -> Generator[Path, None, None]:
    for base, dirnames, filenames in os.walk(root):
        base_path = Path(base)
        # In-place prune of dirnames to avoid descending into excluded dirs
        dirnames[:] = [d for d in dirnames if not should_exclude(base_path / d)]
        for fn in filenames:
            p = base_path / fn
            if not should_exclude(p):
                yield p


def list_relative_paths(paths: Iterable[Path]) -> List[str]:
    out: List[str] = []
    for p in paths:
        try:
            out.append(p.relative_to(REPO_ROOT).as_posix())
        except Exception:
            # Fallback to absolute if relative fails for any reason
            out.append(str(p))
    return sorted(out)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def _scope_of(rel_path: str) -> str:
    if rel_path.startswith("frontend/"):  # quick check
        return "frontend"
    if rel_path.startswith("backend/"):
        return "backend"
    # slower contains check
    if "/frontend/" in rel_path:
        return "frontend"
    if "/backend/" in rel_path:
        return "backend"
    return "other"


def _ext_of(rel_path: str) -> str:
    name = rel_path.rsplit("/", 1)[-1]
    i = name.rfind(".")
    return name[i:].lower() if i > 0 else ""


def _apply_filters(rel_paths: List[str], q: str | None, scope: str | None, ext: str | None) -> List[str]:
    out = rel_paths
    if scope and scope in ("frontend", "backend", "other"):
        out = [p for p in out if _scope_of(p) == scope]
    if ext and ext != "all":
        out = [p for p in out if _ext_of(p) == ext]
    if q:
        qq = q.lower()
        out = [p for p in out if qq in p.lower()]
    return out


@app.get("/filters")
def filters():
    rel = list_relative_paths(iter_files(REPO_ROOT))
    exts = sorted({e for e in (_ext_of(p) for p in rel) if e})
    return {"scopes": ["frontend", "backend", "other"], "extensions": exts}


@app.get("/files")
def files(q: str | None = Query(None), scope: str | None = Query(None), ext: str | None = Query(None),
          offset: int = Query(0, ge=0), limit: int = Query(500, ge=1, le=5000)):
    rel = list_relative_paths(iter_files(REPO_ROOT))
    filtered = _apply_filters(rel, q, scope, ext)
    total = len(filtered)
    page = filtered[offset: offset + limit]
    return {"files": page, "total": total, "offset": offset, "limit": limit}


if __name__ == "__main__":
    import uvicorn

    # Listen on IPv6 '::' to support localhost resolving to ::1 (macOS default)
    uvicorn.run(app, host="::", port=1234, reload=False)
