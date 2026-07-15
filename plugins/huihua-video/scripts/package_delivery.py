#!/usr/bin/env python3
"""Remove transient render artifacts while preserving the delivery contract."""

from __future__ import annotations

import pathlib
import shutil
import sys


TRANSIENT_NAMES = {
    ".cache",
    ".remotion",
    "_frames",
    "_preview",
    "_runtime",
    "contact-sheet",
    "minimax-request.json",
    "minimax-response.json",
    "preview-sheet",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: package_delivery.py <project-dir>", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    if not (root / "production-gate.json").is_file():
        print("Refusing cleanup before production-gate.json exists.", file=sys.stderr)
        return 1
    for path in root.rglob("*"):
        if path.name in TRANSIENT_NAMES or path.suffix.lower() in {".tmp", ".log"}:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.exists():
                path.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
