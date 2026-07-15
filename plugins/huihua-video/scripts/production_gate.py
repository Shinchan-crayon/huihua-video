#!/usr/bin/env python3
"""Validate a huihua-video project before rendering."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any


REQUIRED_JSON = {
    "workflow-state.json",
    "narration.json",
    "subtitle-timeline.json",
    "scene-manifest.json",
    "image-manifest.json",
    "motion-plan.json",
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
    root = pathlib.Path(sys.argv[1]).resolve()
    errors: list[str] = []
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
    if timeline.get("timing_source") != "whisperx":
        errors.append("timing_source must be whisperx")
    if timeline.get("text_source") != "approved_narration":
        errors.append("text_source must be approved_narration")

    audio_path = root / str(timeline.get("audio", ""))
    if not audio_path.is_file():
        errors.append(f"audio file does not exist: {timeline.get('audio')}")
    else:
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
    for image in images:
        if image.get("scene_id") not in scene_ids:
            errors.append(f"image references unknown scene: {image.get('id')}")
        if image.get("fit") != "contain" or image.get("crop_allowed") is not False:
            errors.append(f"image violates no-crop contract: {image.get('id')}")
        if not isinstance(image.get("width"), int) or not isinstance(image.get("height"), int):
            errors.append(f"image dimensions missing: {image.get('id')}")
        if not (root / str(image.get("file", ""))).is_file():
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

    result = {"ok": not errors, "errors": errors}
    (root / "production-gate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
