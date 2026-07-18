#!/usr/bin/env python3
"""Initialize an isolated huihua-video project directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_boundary import (
    BoundaryViolation,
    PRODUCT_ID,
    RUNTIME_NAMESPACE,
    runtime_dir,
    validate_project_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化独立的 huihua-video 项目。")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument(
        "--workflow-id",
        help="兼容旧命令；直出流程不再创建或维护工作流状态台账。",
    )
    args = parser.parse_args()

    try:
        project = validate_project_root(args.project_dir)
    except BoundaryViolation as exc:
        raise SystemExit(f"无法初始化 huihua-video 项目：{exc}") from exc

    project.mkdir(parents=True, exist_ok=True)
    work_dir = runtime_dir(project)
    work_dir.mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "product_id": PRODUCT_ID,
                "project_dir": str(project),
                "runtime_dir": str(work_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
