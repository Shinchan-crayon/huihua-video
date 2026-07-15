#!/usr/bin/env python3
"""Configure MiniMax TTS for huihua-video without exposing credentials."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Optional


VOICE_AUDITION_URL = "https://www.minimaxi.com/audio/voices"
DEFAULT_CONFIG = {
    "api_url": "https://api.minimaxi.com/v1/t2a_v2",
    "model": "speech-2.8-hd",
    "format": "mp3",
    "sample_rate": 32000,
}


def config_dir() -> Path:
    override = os.environ.get("HUIHUA_VIDEO_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "huihua-video"


def load_existing(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"现有 MiniMax 配置不是有效 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("现有 MiniMax 配置必须是 JSON 对象。")
    return value


def read_api_key(args: argparse.Namespace) -> str:
    if args.api_key_stdin:
        value = sys.stdin.readline().strip()
    elif args.from_env:
        value = os.environ.get("MINIMAX_API_KEY", "").strip()
    else:
        value = getpass.getpass("请输入 MiniMax API Key（输入内容不会显示）: ").strip()
    if not value:
        raise SystemExit("MiniMax API Key 不能为空。")
    return value


def read_voice_id(value: Optional[str]) -> str:
    print(f"请先试听音色：{VOICE_AUDITION_URL}")
    voice_id = value.strip() if value else input("请粘贴试听页面中的完整 voice_id: ").strip()
    if not voice_id:
        raise SystemExit("voice_id 不能为空。")
    if any(character.isspace() for character in voice_id):
        raise SystemExit("voice_id 不能包含空格或换行。请完整复制试听页面中的值。")
    return voice_id


def main() -> int:
    parser = argparse.ArgumentParser(description="安全配置 huihua-video 使用的 MiniMax TTS。")
    key_source = parser.add_mutually_exclusive_group()
    key_source.add_argument("--api-key-stdin", action="store_true", help="从标准输入读取 API Key")
    key_source.add_argument("--from-env", action="store_true", help="从 MINIMAX_API_KEY 读取 API Key")
    parser.add_argument("--voice-id", help="从 MiniMax 音色试听页复制的完整 voice_id")
    parser.add_argument("--model", default=DEFAULT_CONFIG["model"], help="MiniMax TTS 模型")
    args = parser.parse_args()

    destination = config_dir() / "minimax.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    config = {**DEFAULT_CONFIG, **load_existing(destination)}
    config.update(
        {
            "api_key": read_api_key(args),
            "voice_id": read_voice_id(args.voice_id),
            "model": args.model,
        }
    )
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(destination)
    os.chmod(destination, 0o600)
    print(f"MiniMax 已配置完成：{destination}")
    print("API Key 只保存在用户配置目录，不会写入视频项目或 Git 仓库。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
