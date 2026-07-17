#!/usr/bin/env python3
"""Initialize an isolated huihua-video project."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from project_boundary import (
    BoundaryViolation,
    PRODUCT_ID,
    RUNTIME_NAMESPACE,
    load_project_state,
    runtime_dir,
    validate_project_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化独立的 huihua-video 项目。")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--workflow-id", required=True)
    args = parser.parse_args()

    workflow_id = args.workflow_id.strip()
    if not workflow_id:
        raise SystemExit("--workflow-id 不能为空。")
    try:
        project = validate_project_root(args.project_dir)
    except BoundaryViolation as exc:
        raise SystemExit(f"无法初始化 huihua-video 项目：{exc}") from exc

    project.mkdir(parents=True, exist_ok=True)
    state_path = project / "workflow-state.json"
    if state_path.exists():
        try:
            state = load_project_state(project)
        except BoundaryViolation as exc:
            raise SystemExit(f"拒绝覆盖现有项目状态：{exc}") from exc
        if state.get("workflow_id") != workflow_id:
            raise SystemExit("现有 workflow-state.json 的 workflow_id 与参数不一致。")
        status = "existing"
    else:
        state = {
            "product_id": PRODUCT_ID,
            "runtime_namespace": RUNTIME_NAMESPACE,
            "workflow_id": workflow_id,
            "stage": "intake",
            "status": "IN_PROGRESS",
            "artifacts": {},
            "invalidated_artifacts": [],
            "blockers": [],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        status = "created"

    work_dir = runtime_dir(project)
    work_dir.mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "status": status,
                "product_id": PRODUCT_ID,
                "project_dir": str(project),
                "runtime_dir": str(work_dir),
                "workflow_state": str(state_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
