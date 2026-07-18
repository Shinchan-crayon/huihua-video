#!/usr/bin/env python3
"""Generate Doubao TTS narration and map native word timings to the final narration."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from minimax_tts_timeline import (
    audio_duration,
    compact,
    load_narration,
    prepend_leading_silence,
    relative_to_output,
    rhythm_points,
    write_json,
)
from project_boundary import (
    BoundaryViolation,
    resolve_project_asset,
    runtime_dir,
    validate_project_root,
)


EVENT_SEPARATOR = re.compile(r"\r?\n\r?\n")
SECRET_FIELD = re.compile(r"(api[_-]?key|authorization|token|secret|password)", re.IGNORECASE)
KNOWN_EVENTS = {152, 153, 351, 352}


def config_dir() -> Path:
    override = os.environ.get("HUIHUA_VIDEO_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "huihua-video"


def load_config() -> dict[str, Any]:
    path = config_dir() / "volcengine.json"
    if not path.is_file():
        raise SystemExit(
            "尚未配置 Doubao。请先运行 scripts/configure_volcengine.py，"
            "并在音色试听页选择默认 voice_id。"
        )
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Doubao 配置不是有效 JSON：{exc}") from exc
    if not isinstance(config, dict):
        raise SystemExit("Doubao 配置必须是 JSON 对象。")
    config["api_key"] = os.environ.get("VOLCENGINE_TTS_API_KEY", "").strip() or str(
        config.get("api_key", "")
    ).strip()
    required = ("api_url", "api_key", "resource_id", "voice_id", "format", "sample_rate")
    missing = [field for field in required if not config.get(field)]
    if missing:
        raise SystemExit(f"Doubao 配置缺少字段：{', '.join(missing)}")
    if config["format"] not in {"mp3", "wav"}:
        raise SystemExit("huihua-video 仅支持 Doubao 输出 mp3 或 wav。")
    return config


def sanitize(value: Any, key: str = "") -> Any:
    if SECRET_FIELD.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {name: sanitize(item, name) for name, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item, key) for item in value]
    return value


def redact_secret(value: str, api_key: str) -> str:
    return value.replace(api_key, "[REDACTED]") if api_key else value


def parse_frame(frame: str) -> tuple[int, dict[str, Any]] | None:
    event: int | None = None
    payload_parts: list[str] = []
    for line in frame.splitlines():
        if not line or line.startswith(":"):
            continue
        name, separator, raw_value = line.partition(":")
        value = raw_value[1:] if separator and raw_value.startswith(" ") else raw_value
        if name.lower() == "event":
            try:
                event = int(value)
            except ValueError as exc:
                raise RuntimeError("Doubao 事件帧包含无效 Event 编号。") from exc
        elif name.lower() == "data":
            payload_parts.append(value)
    if event is None and not payload_parts:
        return None
    if event is None:
        raise RuntimeError("Doubao 事件帧缺少 Event 或 data。")
    if event not in KNOWN_EVENTS:
        return None
    if not payload_parts:
        raise RuntimeError(f"Doubao Event {event} 缺少 data。")
    try:
        payload = json.loads("\n".join(payload_parts))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Doubao Event {event} 返回了无效 JSON。") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Doubao Event {event} 的 data 不是 JSON 对象。")
    return event, payload


def request_events(config: dict[str, Any], text: str) -> list[tuple[int, dict[str, Any]]]:
    parsed = urllib.parse.urlparse(str(config["api_url"]))
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("Doubao API 地址必须使用 HTTPS。")
    request = urllib.request.Request(
        str(config["api_url"]),
        data=json.dumps(
            {
                "user": {"uid": "huihua-video"},
                "req_params": {
                    "speaker": config["voice_id"],
                    "text": text,
                    "audio_params": {
                        "format": config["format"],
                        "sample_rate": int(config["sample_rate"]),
                        "enable_subtitle": True,
                    },
                },
            },
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "X-Api-Key": str(config["api_key"]),
            "X-Api-Resource-Id": str(config["resource_id"]),
            "X-Api-Request-Id": str(uuid.uuid4()),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = redact_secret(exc.read().decode("utf-8", errors="replace")[:1000], str(config["api_key"]))
        raise RuntimeError(f"Doubao HTTP {exc.code}：{detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Doubao 请求失败：{redact_secret(str(exc), str(config['api_key']))}") from exc

    events: list[tuple[int, dict[str, Any]]] = []
    for frame in EVENT_SEPARATOR.split(payload):
        parsed_frame = parse_frame(frame)
        if parsed_frame:
            events.append(parsed_frame)
    if not events:
        raise RuntimeError("Doubao 没有返回事件流。")
    return events


def require_code(payload: dict[str, Any], expected: int, event: int, api_key: str) -> None:
    if payload.get("code") != expected:
        message = redact_secret(str(payload.get("message") or f"Event {event} 返回码无效"), api_key)
        raise RuntimeError(f"Doubao Event {event} 执行失败：{message}")


def decode_audio(payload: dict[str, Any]) -> bytes:
    encoded = str(payload.get("data") or "").replace("\n", "").replace("\r", "").strip()
    if not encoded:
        raise RuntimeError("Doubao 音频事件没有数据。")
    try:
        value = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise RuntimeError("Doubao 音频分片不是有效 Base64。") from exc
    if not value:
        raise RuntimeError("Doubao 音频分片为空。")
    return value


def word_cues(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sentence = payload.get("sentence")
    words = sentence.get("words") if isinstance(sentence, dict) else None
    if not isinstance(words, list) or not words:
        raise RuntimeError("Doubao 原生字幕事件缺少词级时间戳。")
    cues: list[dict[str, Any]] = []
    for word in words:
        if not isinstance(word, dict):
            raise RuntimeError("Doubao 原生字幕包含无效词条。")
        text = str(word.get("word") or "").strip()
        start, end = word.get("startTime"), word.get("endTime")
        if not text or not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise RuntimeError("Doubao 原生字幕包含无效词级时间戳。")
        if end <= start:
            raise RuntimeError("Doubao 原生字幕存在反向时间区间。")
        cues.append({"start": float(start), "end": float(end), "text": text})
    return cues


def sentence_items(narration: dict[str, Any], cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened = "".join(compact(item["text"]) for item in cues)
    expected = compact(str(narration["full_text"]))
    if flattened != expected:
        raise RuntimeError("Doubao 原生字幕文字无法与最终口播一一对应；流程已停止。")
    items: list[dict[str, Any]] = []
    cursor = 0
    for index, sentence in enumerate(narration["sentences"], start=1):
        text = str(sentence["text"])
        target_length = len(compact(text))
        start_cue = cues[cursor] if cursor < len(cues) else None
        consumed = 0
        end_cue: dict[str, Any] | None = None
        while cursor < len(cues) and consumed < target_length:
            current = cues[cursor]
            consumed += len(compact(current["text"]))
            end_cue = current
            cursor += 1
        if not start_cue or not end_cue or consumed != target_length:
            raise RuntimeError(f"Doubao 时间戳无法覆盖口播句子：{sentence.get('id')}")
        items.append(
            {
                "id": f"subtitle-{index:03d}",
                "sentence_id": sentence["id"],
                "start": round(start_cue["start"], 3),
                "end": round(end_cue["end"], 3),
                "text": text,
            }
        )
    if cursor != len(cues):
        raise RuntimeError("Doubao 原生字幕存在未映射内容。")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="使用 Doubao 生成口播和原生字幕时间轴。")
    parser.add_argument("--narration", type=Path, required=True, help="最终 narration.json")
    parser.add_argument("--project-dir", type=Path, required=True, help="视频项目目录")
    parser.add_argument(
        "--leading-silence-seconds",
        type=float,
        default=0.0,
        help="在最终音频前加入的静默秒数，并同步平移字幕和节奏点。",
    )
    parser.add_argument("--dry-run", action="store_true", help="只写入无密钥请求预览")
    args = parser.parse_args()
    if args.leading_silence_seconds < 0:
        raise SystemExit("--leading-silence-seconds 不能小于 0。")

    try:
        project = validate_project_root(args.project_dir)
        narration_path = resolve_project_asset(project, args.narration, "narration.json")
    except BoundaryViolation as exc:
        raise SystemExit(f"Doubao 音频时间轴生成失败：{exc}") from exc
    config = load_config()
    narration = load_narration(narration_path)
    project.mkdir(parents=True, exist_ok=True)
    transient_dir = runtime_dir(project)
    transient_dir.mkdir(parents=True, exist_ok=True)
    request_preview = {
        "api_url": config["api_url"],
        "resource_id": config["resource_id"],
        "voice_id": config["voice_id"],
        "subtitle_enabled": True,
    }
    request_path = transient_dir / "volcengine-request.json"
    write_json(request_path, request_preview)
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "request": str(request_path)}, ensure_ascii=False))
        return 0

    try:
        events = request_events(config, str(narration["full_text"]))
        audio_chunks: list[bytes] = []
        cues: list[dict[str, Any]] = []
        completed = False
        safe_events: list[dict[str, Any]] = []
        for event, payload in events:
            safe_payload = sanitize(payload)
            if event == 352 and isinstance(safe_payload, dict):
                safe_payload["data"] = "[REDACTED_INLINE_AUDIO]"
            safe_events.append({"event": event, "data": safe_payload})
            if completed:
                continue
            if event == 352:
                require_code(payload, 0, event, str(config["api_key"]))
                audio_chunks.append(decode_audio(payload))
            elif event == 351:
                require_code(payload, 0, event, str(config["api_key"]))
                cues.extend(word_cues(payload))
            elif event == 152:
                require_code(payload, 20000000, event, str(config["api_key"]))
                completed = True
            elif event == 153:
                message = redact_secret(str(payload.get("message") or "Doubao 音频生成失败"), str(config["api_key"]))
                raise RuntimeError(message)
        write_json(transient_dir / "volcengine-response.json", {"events": safe_events})
        if not completed:
            raise RuntimeError("Doubao 事件流缺少完成帧。")
        if not audio_chunks:
            raise RuntimeError("Doubao 没有返回有效音频。")
        if not cues:
            raise RuntimeError("Doubao 没有返回有效原生字幕时间戳。")
        previous_end = 0.0
        for cue in cues:
            if cue["start"] < previous_end - 0.02:
                raise RuntimeError("Doubao 原生字幕时间发生冲突。")
            previous_end = cue["end"]
        audio_path = project / f"narration.{config['format']}"
        audio_path.write_bytes(b"".join(audio_chunks))
        prepend_leading_silence(
            audio_path,
            args.leading_silence_seconds,
            int(config["sample_rate"]),
        )
        native_path = project / "volcengine-subtitles.json"
        write_json(native_path, {"provider": "Doubao-语音合成-2.0", "cues": cues})
        items = sentence_items(narration, cues)
        if args.leading_silence_seconds:
            for item in items:
                item["start"] = round(item["start"] + args.leading_silence_seconds, 3)
                item["end"] = round(item["end"] + args.leading_silence_seconds, 3)
        duration = audio_duration(audio_path)
        if items[-1]["end"] > duration + 0.1:
            raise RuntimeError("Doubao 原生字幕超出音频时长。")
        timeline = {
            "audio": relative_to_output(audio_path, project / "subtitle-timeline.json"),
            "audio_sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
            "duration": round(duration, 3),
            "timing_source": "volcengine_tts",
            "text_source": "narration",
            "provider": "Doubao-语音合成-2.0",
            "model": config["resource_id"],
            "voice_id": config["voice_id"],
            "leading_silence_seconds": round(args.leading_silence_seconds, 3),
            "native_subtitle": {
                "file": relative_to_output(native_path, project / "subtitle-timeline.json"),
                "sha256": hashlib.sha256(native_path.read_bytes()).hexdigest(),
                "format": "json",
                "cue_count": len(cues),
                "time_offset_seconds": round(args.leading_silence_seconds, 3),
            },
            "items": items,
            "rhythm_points": rhythm_points(cues, items, args.leading_silence_seconds),
        }
        write_json(project / "subtitle-timeline.json", timeline)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Doubao 音频时间轴生成失败：{exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "completed",
                "audio": timeline["audio"],
                "timeline": str(project / "subtitle-timeline.json"),
                "voice_id": timeline["voice_id"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
