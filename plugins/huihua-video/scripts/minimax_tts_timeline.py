#!/usr/bin/env python3
"""Generate MiniMax narration and map native subtitles to approved narration."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


TIMESTAMP = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{3})"
)
SECRET_FIELD = re.compile(r"(api[_-]?key|authorization|token|secret|password)", re.IGNORECASE)
INLINE_AUDIO_FIELD = re.compile(r"^(audio|audio_data)$", re.IGNORECASE)
JSON_START_KEYS = ("time_begin", "begin_time", "start_time", "start")
JSON_END_KEYS = ("time_end", "end_time", "finish_time", "end")
JSON_TEXT_KEYS = ("text", "subtitle", "content", "word")


def config_dir() -> Path:
    override = os.environ.get("HUIHUA_VIDEO_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "huihua-video"


def load_config() -> dict[str, Any]:
    path = config_dir() / "minimax.json"
    if not path.is_file():
        raise SystemExit(
            "尚未配置 MiniMax。请先运行 scripts/configure_minimax.py，"
            "并在 https://www.minimaxi.com/audio/voices 试听后提供 voice_id。"
        )
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"MiniMax 配置不是有效 JSON：{exc}") from exc
    if not isinstance(config, dict):
        raise SystemExit("MiniMax 配置必须是 JSON 对象。")
    config["api_key"] = os.environ.get("MINIMAX_API_KEY", "").strip() or str(config.get("api_key", "")).strip()
    required = ("api_url", "api_key", "model", "voice_id", "format", "sample_rate")
    missing = [field for field in required if not config.get(field)]
    if missing:
        raise SystemExit(f"MiniMax 配置缺少字段：{', '.join(missing)}")
    if config["format"] not in {"mp3", "wav"}:
        raise SystemExit("huihua-video 仅支持 MiniMax 输出 mp3 或 wav。")
    return config


def load_narration(path: Path) -> dict[str, Any]:
    try:
        narration = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise SystemExit(f"无法读取 narration.json：{exc}") from exc
    if not isinstance(narration, dict) or narration.get("approved") is not True:
        raise SystemExit("narration.json 必须存在且 approved: true。")
    sentences = narration.get("sentences")
    if not isinstance(sentences, list) or not sentences:
        raise SystemExit("narration.json 必须包含非空 sentences。")
    full_text = str(narration.get("full_text", "")).strip()
    if not full_text:
        raise SystemExit("narration.json 的 full_text 不能为空。")
    sentence_text = "".join(str(item.get("text", "")) for item in sentences if isinstance(item, dict))
    if compact(sentence_text) != compact(full_text):
        raise SystemExit("narration.sentences 拼接后必须与 full_text 一致。")
    return narration


def compact(text: str) -> str:
    return "".join(text.split())


def comparable(text: str) -> str:
    return "".join(
        character.casefold()
        for character in text
        if unicodedata.category(character)[0] in {"L", "N"}
    )


def sanitize(value: Any, key: str = "") -> Any:
    if SECRET_FIELD.search(key):
        return "[REDACTED]"
    if INLINE_AUDIO_FIELD.fullmatch(key) and isinstance(value, str) and len(value) > 256:
        return "[REDACTED_INLINE_AUDIO]"
    if isinstance(value, dict):
        return {name: sanitize(item, name) for name, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item, key) for item in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_time(value: str) -> float:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def subtitle_format(path: Path) -> str:
    raw = path.read_text(encoding="utf-8-sig", errors="strict").lstrip()
    if raw.startswith(("{", "[")):
        return "json"
    if raw.startswith("WEBVTT"):
        return "vtt"
    return "srt"


def first_value(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    return next((record[key] for key in keys if key in record), None)


def json_time(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) / 1000
    if isinstance(value, str):
        stripped = value.strip()
        if ":" in stripped:
            return parse_time(stripped)
        return float(stripped) / 1000
    raise ValueError("MiniMax JSON 字幕包含无效毫秒时间戳。")


def find_json_cues(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        parsed: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            text = first_value(item, JSON_TEXT_KEYS)
            start = first_value(item, JSON_START_KEYS)
            end = first_value(item, JSON_END_KEYS)
            if isinstance(text, str) and start is not None and end is not None:
                parsed.append({"start": json_time(start), "end": json_time(end), "text": text.strip()})
        if parsed:
            return parsed
        for item in value:
            nested = find_json_cues(item)
            if nested:
                return nested
    if isinstance(value, dict):
        for item in value.values():
            nested = find_json_cues(item)
            if nested:
                return nested
    return []


def validate_cues(cues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not cues:
        raise ValueError("MiniMax 原生字幕没有可用时间条目。")
    previous_end = 0.0
    for cue in cues:
        if cue["end"] <= cue["start"] or not comparable(cue["text"]):
            raise ValueError("MiniMax 原生字幕包含无效时间区间或空文字。")
        if cue["start"] < previous_end - 0.02:
            raise ValueError("MiniMax 原生字幕时间发生冲突。")
        previous_end = cue["end"]
    return cues


def parse_subtitle(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig", errors="strict").replace("\r\n", "\n")
    if subtitle_format(path) == "json":
        try:
            return validate_cues(find_json_cues(json.loads(text)))
        except json.JSONDecodeError as exc:
            raise ValueError(f"MiniMax JSON 字幕无法解析：{exc}") from exc

    cues: list[dict[str, Any]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = TIMESTAMP.search(lines[index])
        if not match:
            index += 1
            continue
        start = parse_time(match.group("start"))
        end = parse_time(match.group("end"))
        index += 1
        body: list[str] = []
        while index < len(lines) and lines[index].strip():
            body.append(re.sub(r"<[^>]+>", "", lines[index]).strip())
            index += 1
        cue_text = "".join(body).strip()
        cues.append({"start": start, "end": end, "text": cue_text})
        index += 1
    return validate_cues(cues)


def character_intervals(cues: list[dict[str, Any]]) -> tuple[str, list[tuple[float, float]]]:
    source: list[str] = []
    intervals: list[tuple[float, float]] = []
    for cue in cues:
        normalized = comparable(cue["text"])
        step = (cue["end"] - cue["start"]) / len(normalized)
        for offset, character in enumerate(normalized):
            source.append(character)
            intervals.append((cue["start"] + step * offset, cue["start"] + step * (offset + 1)))
    return "".join(source), intervals


def sentence_items(
    narration: dict[str, Any],
    cues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source, intervals = character_intervals(cues)
    target = comparable(str(narration["full_text"]))
    if source != target:
        raise ValueError(
            "MiniMax 原生字幕文字无法与已确认口播一一对应；"
            "为避免伪造时间轴，流程已停止。请重新生成音频。"
        )
    items: list[dict[str, Any]] = []
    cursor = 0
    for item_index, sentence in enumerate(narration["sentences"], start=1):
        text = str(sentence["text"])
        length = len(comparable(text))
        if length <= 0:
            raise ValueError(f"口播句子没有可对齐文字：{sentence.get('id')}")
        segment = intervals[cursor : cursor + length]
        if len(segment) != length:
            raise ValueError(f"MiniMax 时间戳不足以覆盖口播句子：{sentence.get('id')}")
        items.append(
            {
                "id": f"subtitle-{item_index:03d}",
                "sentence_id": sentence["id"],
                "start": round(segment[0][0], 3),
                "end": round(segment[-1][1], 3),
                "text": text,
            }
        )
        cursor += length
    if cursor != len(intervals):
        raise ValueError("MiniMax 时间戳存在未映射内容。")
    return items


def rhythm_points(cues: list[dict[str, Any]], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points = [
        {"time": item["start"], "type": "sentence_start", "sentence_id": item["sentence_id"]}
        for item in items[1:]
    ]
    for previous, current in zip(cues, cues[1:]):
        gap = current["start"] - previous["end"]
        if gap >= 0.35:
            points.append({"time": round(previous["end"], 3), "type": "pause", "duration": round(gap, 3)})
    return sorted(points, key=lambda point: point["time"])


def relative_to_output(path: Path, output_path: Path) -> str:
    try:
        return str(path.resolve().relative_to(output_path.parent.resolve()))
    except ValueError as exc:
        raise ValueError("音频、原生字幕和时间轴必须位于同一个项目目录内。") from exc


def build_timeline(
    *,
    narration_path: Path,
    audio_path: Path,
    subtitle_path: Path,
    output_path: Path,
    duration: float,
    voice_id: str,
    model: str,
) -> dict[str, Any]:
    narration = load_narration(narration_path)
    if not audio_path.is_file() or not audio_path.read_bytes():
        raise ValueError("MiniMax 音频文件不存在或为空。")
    if duration <= 0:
        raise ValueError("MiniMax 音频时长必须大于 0。")
    cues = parse_subtitle(subtitle_path)
    items = sentence_items(narration, cues)
    if items[-1]["end"] > duration + 0.1:
        raise ValueError("MiniMax 原生字幕超出音频时长。")
    timeline = {
        "audio": relative_to_output(audio_path, output_path),
        "audio_sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
        "duration": round(duration, 3),
        "timing_source": "minimax_tts",
        "text_source": "approved_narration",
        "provider": "MiniMax",
        "model": model,
        "voice_id": voice_id,
        "native_subtitle": {
            "file": relative_to_output(subtitle_path, output_path),
            "sha256": hashlib.sha256(subtitle_path.read_bytes()).hexdigest(),
            "format": subtitle_format(subtitle_path),
            "cue_count": len(cues),
        },
        "items": items,
        "rhythm_points": rhythm_points(cues, items),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, timeline)
    return timeline


def ensure_provider_success(response: dict[str, Any]) -> None:
    base = response.get("base_resp")
    if isinstance(base, dict) and base.get("status_code") not in (None, 0):
        raise RuntimeError(f"MiniMax 错误 {base.get('status_code')}：{base.get('status_msg', '请求失败')}")
    code = response.get("code")
    if isinstance(code, int) and code not in (0, 200):
        raise RuntimeError(f"MiniMax 错误 {code}：{response.get('message') or response.get('msg') or '请求失败'}")


def post_json(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("MiniMax API 地址必须使用 HTTPS。")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"MiniMax HTTP {exc.code}：{detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"MiniMax 请求失败：{exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("MiniMax 返回内容不是 JSON 对象。")
    ensure_provider_success(value)
    return value


def download_https(url: str, accept: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("MiniMax 返回了非 HTTPS 文件地址。")
    request = urllib.request.Request(url, headers={"Accept": accept})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"下载 MiniMax 文件失败：{exc}") from exc


def extract_audio(response: dict[str, Any]) -> bytes:
    data = response.get("data") if isinstance(response.get("data"), dict) else response
    audio = data.get("audio") if isinstance(data, dict) else None
    if isinstance(audio, str) and audio:
        encoded = audio.split(",", 1)[1] if audio.startswith("data:") else audio
        try:
            return bytes.fromhex(encoded)
        except ValueError:
            try:
                return base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise RuntimeError("MiniMax 返回的音频编码无法解析。") from exc
    candidates = []
    if isinstance(data, dict):
        candidates.extend((data.get("audio_url"), data.get("url")))
    candidates.append(response.get("audio_url"))
    url = next((item for item in candidates if isinstance(item, str) and item), None)
    if not url:
        raise RuntimeError("MiniMax 响应没有音频数据。")
    return download_https(url, "audio/*")


def subtitle_url(response: dict[str, Any]) -> str:
    data = response.get("data") if isinstance(response.get("data"), dict) else response
    value = data.get("subtitle_file") if isinstance(data, dict) else None
    if not isinstance(value, str) or not value:
        raise RuntimeError("MiniMax 未返回原生字幕时间戳文件，流程已停止。")
    return value


def audio_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("未找到 FFprobe，无法验证 MiniMax 音频时长。")
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"FFprobe 无法读取 MiniMax 音频：{completed.stderr.strip()}")
    try:
        return float(completed.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("FFprobe 未返回有效音频时长。") from exc


def build_payload(config: dict[str, Any], text: str) -> dict[str, Any]:
    return {
        "model": config["model"],
        "text": text,
        "stream": False,
        "output_format": "hex",
        "subtitle_enable": True,
        "subtitle_type": "word",
        "voice_setting": {"voice_id": config["voice_id"]},
        "audio_setting": {
            "format": config["format"],
            "sample_rate": int(config["sample_rate"]),
            "channel": 1,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="使用 MiniMax 生成口播和原生字幕时间轴。")
    parser.add_argument("--narration", type=Path, required=True, help="已确认的 narration.json")
    parser.add_argument("--project-dir", type=Path, required=True, help="视频项目目录")
    parser.add_argument("--dry-run", action="store_true", help="只写入无密钥请求预览")
    args = parser.parse_args()

    config = load_config()
    narration = load_narration(args.narration)
    project = args.project_dir.resolve()
    project.mkdir(parents=True, exist_ok=True)
    payload = build_payload(config, narration["full_text"])
    request_path = project / "minimax-request.json"
    write_json(request_path, {"api_url": config["api_url"], "payload": payload})
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "request": str(request_path)}, ensure_ascii=False))
        return 0

    try:
        response = post_json(config["api_url"], config["api_key"], payload)
        write_json(project / "minimax-response.json", sanitize(response))
        audio = extract_audio(response)
        if not audio:
            raise RuntimeError("MiniMax 返回了空音频。")
        audio_path = project / f"narration.{config['format']}"
        audio_path.write_bytes(audio)
        native_path = project / "minimax-subtitles.json"
        native_path.write_bytes(download_https(subtitle_url(response), "text/*,application/json"))
        timeline = build_timeline(
            narration_path=args.narration,
            audio_path=audio_path,
            subtitle_path=native_path,
            output_path=project / "subtitle-timeline.json",
            duration=audio_duration(audio_path),
            voice_id=config["voice_id"],
            model=config["model"],
        )
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"MiniMax 音频时间轴生成失败：{exc}", file=sys.stderr)
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
