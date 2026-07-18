#!/usr/bin/env python3
"""Enforce the huihua-video project and runtime namespace."""

from __future__ import annotations

from pathlib import Path


PRODUCT_ID = "huihua-video"
RUNTIME_NAMESPACE = ".huihua-video-runtime"
FORBIDDEN_PATH_SEGMENTS = frozenset({"shin-video", ".shin-video-runtime"})
FORBIDDEN_URI_PREFIXES = ("shin-video://",)


class BoundaryViolation(ValueError):
    """Raised when a path crosses the huihua-video product boundary."""


def _raw_parts(value: str) -> tuple[str, ...]:
    return tuple(part.casefold() for part in value.replace("\\", "/").split("/") if part)


def _forbidden_segment(parts: tuple[str, ...]) -> str | None:
    return next((part for part in parts if part in FORBIDDEN_PATH_SEGMENTS), None)


def _check_path_identity(raw_value: str, resolved: Path, label: str) -> None:
    raw_segment = _forbidden_segment(_raw_parts(raw_value))
    resolved_segment = _forbidden_segment(tuple(part.casefold() for part in resolved.parts))
    forbidden = raw_segment or resolved_segment
    if forbidden:
        raise BoundaryViolation(
            f"{label} 指向 {forbidden}，huihua-video 不得读取或写入 Shin-video 的仓库、运行目录或产物。"
        )


def validate_project_root(project_dir: Path | str) -> Path:
    raw_value = str(project_dir).strip()
    if not raw_value:
        raise BoundaryViolation("huihua-video 项目目录不能为空。")
    if "://" in raw_value:
        raise BoundaryViolation("huihua-video 项目目录必须是本地文件路径。")
    resolved = Path(raw_value).expanduser().resolve()
    _check_path_identity(raw_value, resolved, "项目目录")
    if resolved.name.casefold() == RUNTIME_NAMESPACE:
        raise BoundaryViolation(
            f"项目根目录不能直接使用 {RUNTIME_NAMESPACE}；该目录只存放 huihua-video 中间产物。"
        )
    return resolved

def runtime_dir(project_dir: Path | str) -> Path:
    return validate_project_root(project_dir) / RUNTIME_NAMESPACE


def resolve_project_asset(project_dir: Path | str, reference: object, label: str) -> Path:
    root = validate_project_root(project_dir)
    raw_value = str(reference or "").strip()
    if not raw_value:
        raise BoundaryViolation(f"{label} 不能为空。")
    lowered = raw_value.casefold()
    if lowered.startswith(FORBIDDEN_URI_PREFIXES):
        raise BoundaryViolation(f"{label} 使用了 Shin-video URI，huihua-video 不接受跨产品资产引用。")
    candidate = Path(raw_value).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    _check_path_identity(raw_value, resolved, label)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise BoundaryViolation(f"{label} 必须位于当前 huihua-video 项目目录内。") from exc
    return resolved
