"""
Find potentially unused files in the repository.

Heuristics used (safe, conservative):
- Define entrypoint anchors (backend/main.py, frontend/src/main.*x, scripts/*.sh)
- Build a set of referenced basenames by scanning text files for filename mentions
- Anything not referenced by name and not under known entry trees is a candidate
- Always exclude common build/dep dirs: node_modules, dist, __pycache__, .git

Outputs:
- unused_files_report.json (machine-readable)
- unused_files_summary.txt (human summary)

This is a heuristic aid. Review before deletion.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parents[1]

TEXT_EXTS = {
    ".py", ".txt", ".md", ".json", ".csv", ".ts", ".tsx", ".js", ".jsx",
    ".html", ".css", ".scss", ".sh", ".toml", ".yml", ".yaml"
}

IGNORE_DIRS = {
    "node_modules", "dist", "build", "__pycache__", ".git", ".idea",
    ".pytest_cache", "frontend/dist", "backend/screenshots", "logs",
}

ANCHOR_FILES = [
    "backend/main.py",
    "backend/app/main.py",
    "frontend/src/main.tsx",
    "frontend/src/main.ts",
    "frontend/index.html",
    "start.sh",
    "start-monolith.sh",
]

REL_IMPORT_RE = re.compile(r"import\s+(?:[\w*,\s{}]+\s+from\s+)?['\"]([^'\"]+)['\"];?")
PY_IMPORT_RE_1 = re.compile(r"^\s*import\s+([\w.,\s_]+)")
PY_IMPORT_RE_2 = re.compile(r"^\s*from\s+([\w\.]+)\s+import\s+[\w\*,\s{}]+")


def is_text_file(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        # Try a small read to see if it's text-ish
        chunk = path.open("rb").read(2048)
        chunk.decode("utf-8")
        return True
    except Exception:
        return path.suffix.lower() in TEXT_EXTS


def should_ignore(path: Path) -> bool:
    parts = set(path.parts)
    return any(d in parts for d in IGNORE_DIRS)


def collect_all_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and not should_ignore(p):
            files.append(p)
    return files


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def scan_references(files: List[Path]) -> Set[str]:
    referenced: Set[str] = set()
    for f in files:
        if not is_text_file(f):
            continue
        text = read_text_safe(f)
        if not text:
            continue
        # record any bare filename-like tokens (simple heuristic)
        for m in re.finditer(r"[\w\-\.]{3,}\.[A-Za-z0-9]{1,6}", text):
            referenced.add(m.group(0))
        # JS/TS import paths (capture relative files too)
        for m in REL_IMPORT_RE.finditer(text):
            ref = m.group(1)
            # record possible filenames with common extensions
            for ext in (".ts", ".tsx", ".js", ".jsx", ".json"):
                name = Path(ref).name
                if Path(ref).suffix:
                    referenced.add(name)
                else:
                    referenced.add(name + ext)
        # Python imports (record module last segment guesses)
        for m in PY_IMPORT_RE_1.finditer(text):
            items = [s.strip() for s in m.group(1).split(",")]
            for it in items:
                if it:
                    referenced.add(it.split(".")[-1] + ".py")
        for m in PY_IMPORT_RE_2.finditer(text):
            mod = m.group(1)
            referenced.add(mod.split(".")[-1] + ".py")
    return referenced


def main() -> int:
    root = REPO_ROOT
    all_files = collect_all_files(root)
    referenced_names = scan_references(all_files)

    # Mark anchors as referenced
    for a in ANCHOR_FILES:
        p = (root / a)
        if p.exists():
            referenced_names.add(p.name)

    unused: List[Dict[str, str]] = []

    for f in all_files:
        bn = f.name
        if bn in referenced_names:
            continue
        unused.append({
            "path": str(f.relative_to(root)),
            "size": f.stat().st_size,
            "ext": f.suffix.lower(),
        })

    # Group summary by extension
    summary: Dict[str, Dict[str, int]] = {}
    for u in unused:
        ext = u["ext"] or "<none>"
        s = summary.setdefault(ext, {"count": 0, "bytes": 0})
        s["count"] += 1
        s["bytes"] += u["size"]

    report = {
        "root": str(root),
        "total_files": len(all_files),
        "referenced_basenames": len(referenced_names),
        "unused_candidates": len(unused),
        "summary_by_ext": summary,
        "unused": sorted(unused, key=lambda x: (-x["size"], x["path"]))[:5000],
    }

    (root / "unused_files_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    lines: List[str] = []
    lines.append(f"Root: {report['root']}")
    lines.append(f"Total files scanned: {report['total_files']}")
    lines.append(f"Unused candidates: {report['unused_candidates']}")
    lines.append("Top extensions (by count):")
    for ext, s in sorted(summary.items(), key=lambda kv: -kv[1]["count"])[:15]:
        lines.append(f"  {ext:8s}  count={s['count']:6d}  size={s['bytes']:,}")
    lines.append("")
    lines.append("Largest 50 candidates:")
    for u in report["unused"][:50]:
        lines.append(f"  {u['size']:>10,}  {u['path']}")

    (root / "unused_files_summary.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    print("Generated unused_files_report.json and unused_files_summary.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
