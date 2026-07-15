#!/usr/bin/env python3
"""Check the local runtime required by huihua-video."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def config_dir() -> Path:
    override = os.environ.get("HUIHUA_VIDEO_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "huihua-video"


def minimax_check() -> dict:
    path = config_dir() / "minimax.json"
    configured = False
    voice_id_configured = False
    if path.is_file():
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                configured = bool(os.environ.get("MINIMAX_API_KEY", "").strip() or value.get("api_key"))
                voice_id_configured = bool(value.get("voice_id"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "configured": configured and voice_id_configured,
        "api_key_configured": configured,
        "voice_id_configured": voice_id_configured,
        "config_path": str(path),
    }


def image_prompt_generator_check() -> dict:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    path = codex_home / "skills" / "image-prompt-generator" / "SKILL.md"
    return {"installed": path.is_file(), "skill_path": str(path)}


def main() -> int:
    checks = {
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "python": sys.executable,
        "minimax_configuration": minimax_check(),
        "image_prompt_generator": image_prompt_generator_check(),
    }
    required = ("node", "npm", "ffmpeg", "ffprobe", "python")
    missing = [name for name in required if not checks[name]]
    if not checks["minimax_configuration"]["configured"]:
        missing.append("minimax_configuration")
    if not checks["image_prompt_generator"]["installed"]:
        missing.append("image_prompt_generator")
    result = {
        "ok": not missing,
        "checks": checks,
        "missing_required": missing,
        "notes": [
            "MiniMax is the only supported TTS provider. Configure it with scripts/configure_minimax.py.",
            "Audition voices at https://www.minimaxi.com/audio/voices and save the exact voice_id.",
            "Illustration prompts and paid generation approvals are handled by $image-prompt-generator.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
