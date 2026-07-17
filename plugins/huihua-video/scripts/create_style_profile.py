#!/usr/bin/env python3
"""Create the explicit illustration style contract for one huihua-video project."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from project_boundary import BoundaryViolation, load_project_state, runtime_dir, validate_project_root


ASPECT_RATIO = re.compile(r"^(?P<width>[1-9]\d*):(?P<height>[1-9]\d*)$")


PRESETS = {
    "ancient-chinese-hand-drawn": {
        "style_name": "古风手绘风格",
        "prompt_profile": (
            "中国古风绘本完整插画，手工水墨线稿结合透明水彩，春秋至古代东方叙事气质；"
            "线条有自然笔触、墨色浓淡变化与留白，设色克制，以浅青、米白、赭石和淡墨为主；"
            "人物五官自然、衣纹简洁、环境具有时代感但不过度堆砌；画面是可被镜头完整展示的叙事插画，"
            "不是写实影视剧照、不是 3D、不是商业海报、不要现代 UI、不要水印、不要字幕文字。"
        ),
    },
    "restrained-childrens-coloring-paper": {
        "style_name": "卡通手绘风格",
        "prompt_profile": (
            "亮白真实纸上的纯人类手绘儿童涂色画照片，不是数字插画、不是商业绘本。"
            "普通大人徒手画的粗黑马克笔线稿，线条明显粗细不匀、抖动歪扭、偶有重复描线和接不齐；"
            "5 到 8 岁儿童式乱涂蜡笔或彩笔填色，主要色块保留 25% 到 35% 露白，色块深浅不均并有可见运笔方向，"
            "2 到 3 处明显越过黑线。背景极简、亮白真实纸面、少量纸纹与轻微折痕；低到中饱和配色，全画不超过 4 种彩色，"
            "只保留一个橙红强调色。禁止平滑稳定的数字线稿、完美透视、渐变、3D、体积光、完整装修背景、"
            "均匀数字噪点滤镜、商业绘本精致可爱感、画面内字幕或水印。"
        ),
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="创建绘画视频的风格档案。")
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--style", choices=(*PRESETS.keys(), "custom"), required=True)
    parser.add_argument("--aspect-ratio", required=True, help="用户确认的画面比例，例如 3:4。")
    parser.add_argument("--custom-name", help="选择 custom 时的风格名称。")
    parser.add_argument("--custom-prompt-profile", help="选择 custom 时的完整生图风格约束。")
    parser.add_argument("--custom-notes", default="", help="选择 custom 时的补充说明。")
    args = parser.parse_args()

    aspect_ratio = args.aspect_ratio.strip()
    if not ASPECT_RATIO.fullmatch(aspect_ratio):
        raise SystemExit("--aspect-ratio 必须是正整数比例，例如 3:4。")

    if args.style == "custom":
        style_name = (args.custom_name or "").strip()
        prompt_profile = (args.custom_prompt_profile or "").strip()
        if not style_name or not prompt_profile:
            raise SystemExit("custom 风格必须提供 --custom-name 与 --custom-prompt-profile。")
    else:
        preset = PRESETS[args.style]
        style_name = preset["style_name"]
        prompt_profile = preset["prompt_profile"]

    try:
        project = validate_project_root(args.project_dir)
        load_project_state(project)
    except BoundaryViolation as exc:
        raise SystemExit(f"无法创建 huihua-video 风格档案：{exc}") from exc
    project.mkdir(parents=True, exist_ok=True)
    runtime_dir(project).mkdir(parents=True, exist_ok=True)
    output = project / "style-profile.json"
    output.write_text(
        json.dumps(
            {
                "style_profile_version": 1,
                "style_id": args.style,
                "style_name": style_name,
                "aspect_ratio": aspect_ratio,
                "prompt_profile": prompt_profile,
                "custom_notes": args.custom_notes.strip(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "completed", "style_profile": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
