#!/usr/bin/env python3
"""Validate a huihua-video project before rendering."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any

from project_boundary import (
    BoundaryViolation,
    resolve_project_asset,
    validate_project_root,
    validate_state_identity,
)


REQUIRED_JSON = {
    "workflow-state.json",
    "narration.json",
    "subtitle-timeline.json",
    "scene-manifest.json",
    "image-manifest.json",
    "motion-plan.json",
    "style-profile.json",
}


def load(path: pathlib.Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return value


def compact(text: str) -> str:
    return "".join(text.split())


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: production_gate.py <project-dir>", file=sys.stderr)
        return 2
    errors: list[str] = []
    try:
        root = validate_project_root(pathlib.Path(sys.argv[1]))
    except BoundaryViolation as exc:
        result = {"ok": False, "errors": [str(exc)]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    missing = sorted(name for name in REQUIRED_JSON if not (root / name).is_file())
    errors.extend(f"missing required file: {name}" for name in missing)
    if missing:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    state = load(root / "workflow-state.json")
    narration = load(root / "narration.json")
    timeline = load(root / "subtitle-timeline.json")
    scenes_doc = load(root / "scene-manifest.json")
    images_doc = load(root / "image-manifest.json")
    motion_doc = load(root / "motion-plan.json")
    style_profile = load(root / "style-profile.json")
    errors.extend(validate_state_identity(state))

    if narration.get("approved") is not True:
        errors.append("narration.json is not approved")
    sentences = narration.get("sentences") or []
    sentence_text = {item.get("id"): item.get("text", "") for item in sentences}
    timeline_items = timeline.get("items") or []
    previous_end = 0.0
    rebuilt: dict[str, list[str]] = {}
    for item in timeline_items:
        start, end = item.get("start"), item.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or start < 0 or end <= start:
            errors.append(f"invalid subtitle interval: {item.get('id')}")
            continue
        if start < previous_end - 0.02:
            errors.append(f"overlapping subtitle interval: {item.get('id')}")
        previous_end = max(previous_end, end)
        rebuilt.setdefault(item.get("sentence_id"), []).append(item.get("text", ""))
    for sentence_id, expected in sentence_text.items():
        actual = "".join(rebuilt.get(sentence_id, []))
        if compact(actual) != compact(expected):
            errors.append(f"subtitle text differs from approved narration: {sentence_id}")

    duration = timeline.get("duration")
    if not isinstance(duration, (int, float)) or duration <= 0:
        errors.append("subtitle timeline has invalid duration")
    supported_providers = {
        "MiniMax": "minimax_tts",
        "Doubao-语音合成-2.0": "volcengine_tts",
    }
    expected_timing_source = supported_providers.get(timeline.get("provider"))
    if not expected_timing_source:
        errors.append("subtitle timeline provider is not supported")
    elif timeline.get("timing_source") != expected_timing_source:
        errors.append(f"timing_source must be {expected_timing_source}")
    if timeline.get("text_source") != "approved_narration":
        errors.append("text_source must be approved_narration")
    if not timeline.get("model"):
        errors.append("subtitle timeline has no provider model")
    if not timeline.get("voice_id"):
        errors.append("subtitle timeline has no provider voice_id")

    native = timeline.get("native_subtitle")
    if not isinstance(native, dict):
        errors.append("native provider subtitle metadata is missing")
    else:
        try:
            native_path = resolve_project_asset(root, native.get("file"), "native provider subtitle")
        except BoundaryViolation as exc:
            errors.append(str(exc))
            native_path = None
        if native_path is not None and not native_path.is_file():
            errors.append(f"native provider subtitle file does not exist: {native.get('file')}")
        elif native_path is not None:
            native_digest = hashlib.sha256(native_path.read_bytes()).hexdigest()
            if native_digest != native.get("sha256"):
                errors.append("native provider subtitle SHA-256 does not match timeline")
        if native.get("format") not in {"json", "srt", "vtt"}:
            errors.append("native provider subtitle format must be json, srt or vtt")
        if not isinstance(native.get("cue_count"), int) or native.get("cue_count") < 1:
            errors.append("native provider subtitle cue_count must be positive")

    try:
        audio_path = resolve_project_asset(root, timeline.get("audio"), "audio file")
    except BoundaryViolation as exc:
        errors.append(str(exc))
        audio_path = None
    if audio_path is not None and not audio_path.is_file():
        errors.append(f"audio file does not exist: {timeline.get('audio')}")
    elif audio_path is not None:
        digest = hashlib.sha256(audio_path.read_bytes()).hexdigest()
        if digest != timeline.get("audio_sha256"):
            errors.append("audio SHA-256 does not match subtitle timeline")

    scenes = scenes_doc.get("scenes") or []
    scene_ids = {scene.get("id") for scene in scenes}
    if not scenes:
        errors.append("scene manifest is empty")
    for scene in scenes:
        if scene.get("end", 0) <= scene.get("start", 0):
            errors.append(f"invalid scene interval: {scene.get('id')}")
        if not scene.get("safe_zones"):
            errors.append(f"scene has no safe zones: {scene.get('id')}")
        duration_s = scene.get("end", 0) - scene.get("start", 0)
        minimum_beats = 3 if duration_s >= 8 else 2 if duration_s >= 5 else 1
        if len(scene.get("beats") or []) < minimum_beats:
            errors.append(f"scene has too few internal beats: {scene.get('id')}")

    images = images_doc.get("images") or []
    color_scene_ids: set[str] = set()
    aspect_ratio = style_profile.get("aspect_ratio")
    for image in images:
        if image.get("scene_id") not in scene_ids:
            errors.append(f"image references unknown scene: {image.get('id')}")
        if image.get("fit") != "contain" or image.get("crop_allowed") is not False:
            errors.append(f"image violates no-crop contract: {image.get('id')}")
        if isinstance(aspect_ratio, str) and aspect_ratio and aspect_ratio not in str(image.get("prompt", "")):
            errors.append(f"image prompt has no explicit selected aspect ratio: {image.get('id')}")
        if not isinstance(image.get("width"), int) or not isinstance(image.get("height"), int):
            errors.append(f"image dimensions missing: {image.get('id')}")
        try:
            image_path = resolve_project_asset(root, image.get("file"), f"image file {image.get('id')}")
        except BoundaryViolation as exc:
            errors.append(str(exc))
            image_path = None
        if image_path is not None and not image_path.is_file():
            errors.append(f"image file does not exist: {image.get('file')}")
        if image.get("role") == "color":
            color_scene_ids.add(image.get("scene_id"))
    for scene_id in scene_ids - color_scene_ids:
        errors.append(f"scene has no full color illustration: {scene_id}")

    motion_scenes = motion_doc.get("scenes") or []
    motion_ids = {item.get("scene_id") for item in motion_scenes}
    for scene_id in scene_ids - motion_ids:
        errors.append(f"scene has no motion plan: {scene_id}")

    if state.get("stage") not in {"review", "render", "qa", "completed"}:
        errors.append("workflow is not ready for rendering")

    if not isinstance(style_profile.get("style_profile_version"), int):
        errors.append("style profile has no version")
    if not style_profile.get("style_id") or not style_profile.get("style_name"):
        errors.append("style profile has no selected style")
    if not aspect_ratio:
        errors.append("style profile has no explicit aspect ratio")
    if not style_profile.get("prompt_profile"):
        errors.append("style profile has no image prompt profile")

    result = {"ok": not errors, "errors": errors}
    (root / "production-gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
