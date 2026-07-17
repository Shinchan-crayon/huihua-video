#!/usr/bin/env python3
"""Configure Doubao Seed TTS for huihua-video without exposing credentials."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Optional


VOICE_AUDITION_URL = (
    "https://console.volcengine.com/ark/region:cn-beijing/experience/voice?model=doubao-seed-tts-2-0"
)
DEFAULT_CONFIG = {
    "api_url": "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse",
    "resource_id": "seed-tts-2.0",
    "format": "mp3",
    "sample_rate": 24000,
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
        raise SystemExit(f"现有 Doubao 配置不是有效 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("现有 Doubao 配置必须是 JSON 对象。")
    return value


def read_api_key(args: argparse.Namespace) -> str:
    if args.api_key_stdin:
        value = sys.stdin.readline().strip()
    elif args.from_env:
        value = os.environ.get("VOLCENGINE_TTS_API_KEY", "").strip()
    else:
        value = getpass.getpass("请输入火山引擎 API Key（输入内容不会显示）: ").strip()
    if not value:
        raise SystemExit("火山引擎 API Key 不能为空。")
    return value


def read_voice_id(value: Optional[str]) -> str:
    print(f"请先试听音色：{VOICE_AUDITION_URL}")
    voice_id = value.strip() if value else input("请粘贴试听页面中的完整 voice_id: ").strip()
    if not voice_id:
        raise SystemExit("voice_id 不能为空。")
    if any(character.isspace() for character in voice_id):
        raise SystemExit("voice_id 不能包含空格或换行。请完整复制试听页面中的值。")
    return voice_id


def write_json_private(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    os.chmod(path, 0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description="安全配置 huihua-video 使用的 Doubao 语音合成-2.0。")
    key_source = parser.add_mutually_exclusive_group()
    key_source.add_argument("--api-key-stdin", action="store_true", help="从标准输入读取 API Key")
    key_source.add_argument("--from-env", action="store_true", help="从 VOLCENGINE_TTS_API_KEY 读取 API Key")
    parser.add_argument("--voice-id", help="从 Doubao 音色试听页复制的完整 voice_id")
    parser.add_argument("--resource-id", default=DEFAULT_CONFIG["resource_id"], help="火山引擎资源 ID")
    args = parser.parse_args()

    destination_dir = config_dir()
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / "volcengine.json"
    config = {**DEFAULT_CONFIG, **load_existing(destination)}
    config.update(
        {
            "api_key": read_api_key(args),
            "voice_id": read_voice_id(args.voice_id),
            "resource_id": args.resource_id,
        }
    )
    write_json_private(destination, config)
    write_json_private(destination_dir / "audio.json", {"provider": "volcengine", "model": config["resource_id"]})
    print(f"Doubao 已配置完成：{destination}")
    print("Doubao 已设为默认音频模型。API Key 只保存在用户配置目录，不会写入视频项目或 Git 仓库。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
