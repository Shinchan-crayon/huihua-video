#!/usr/bin/env python3
"""Check the local runtime required by huihua-video."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from project_boundary import PRODUCT_ID, RUNTIME_NAMESPACE


def config_dir() -> Path:
    override = os.environ.get("HUIHUA_VIDEO_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "huihua-video"


def provider_check(provider: str) -> dict:
    if provider not in {"minimax", "volcengine"}:
        return {
            "configured": False,
            "api_key_configured": False,
            "voice_id_configured": False,
            "config_path": "",
        }
    path = config_dir() / f"{provider}.json"
    configured = False
    voice_id_configured = False
    if path.is_file():
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                environment_key = "MINIMAX_API_KEY" if provider == "minimax" else "VOLCENGINE_TTS_API_KEY"
                configured = bool(os.environ.get(environment_key, "").strip() or value.get("api_key"))
                voice_id_configured = bool(value.get("voice_id"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "configured": configured and voice_id_configured,
        "api_key_configured": configured,
        "voice_id_configured": voice_id_configured,
        "config_path": str(path),
    }


def audio_check() -> dict:
    path = config_dir() / "audio.json"
    provider = ""
    if path.is_file():
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                provider = str(value.get("provider", "")).strip()
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "selected_provider": provider,
        "selection_path": str(path),
        "provider_configuration": provider_check(provider),
    }


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


def main() -> int:
    audio = audio_check()
    checks = {
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "python": sys.executable,
        "audio_configuration": audio,
        "minimax_configuration": minimax_check(),
        "product_boundary": {
            "product_id": PRODUCT_ID,
            "runtime_namespace": RUNTIME_NAMESPACE,
            "config_dir": str(config_dir()),
        },
    }
    required = ("node", "npm", "ffmpeg", "ffprobe", "python")
    missing = [name for name in required if not checks[name]]
    if not audio["provider_configuration"]["configured"]:
        missing.append("audio_configuration")
    result = {
        "ok": not missing,
        "checks": checks,
        "missing_required": missing,
        "notes": [
            "Configure MiniMax with scripts/configure_minimax.py or Doubao with scripts/configure_volcengine.py.",
            "Save an exact default voice_id after auditioning the selected provider voice library.",
            "huihua-image-director generates prompts and directly calls the agent's configured image provider.",
            "huihua-video does not share runtime files, templates, or configuration with Shin-video.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
