"""Locate bundled resource files (works from source and from a Nuitka build)."""
from __future__ import annotations

import sys
from pathlib import Path


def resource_path(name: str) -> Path:
    """Return the path of a file that sits next to ``main.py``."""
    candidates = [
        Path(__file__).resolve().parent.parent / name,
        Path(sys.argv[0]).resolve().parent / name,
        Path.cwd() / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


APP_ICON = "satellite.ico"
