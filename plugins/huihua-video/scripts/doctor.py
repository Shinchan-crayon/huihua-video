#!/usr/bin/env python3
"""Check the local runtime required by huihua-video."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys


def main() -> int:
    checks = {
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "python": sys.executable,
        "whisperx_python_package": importlib.util.find_spec("whisperx") is not None,
    }
    required = ("node", "npm", "ffmpeg", "ffprobe", "python")
    missing = [name for name in required if not checks[name]]
    result = {
        "ok": not missing,
        "checks": checks,
        "missing_required": missing,
        "notes": [
            "WhisperX may run from a dedicated virtual environment even when the current Python cannot import it.",
            "TTS and image generation providers are selected by the executing agent and are not hard-coded here.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
