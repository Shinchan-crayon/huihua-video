#!/usr/bin/env python3
"""Create a clean line-art companion image using FFmpeg."""

from __future__ import annotations

import pathlib
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: extract_line_art.py <color-image> <line-image>", file=sys.stderr)
        return 2
    source = pathlib.Path(sys.argv[1]).resolve()
    target = pathlib.Path(sys.argv[2]).resolve()
    if not source.is_file():
        print(f"Source image does not exist: {source}", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vf",
            "format=gray,edgedetect=low=0.06:high=0.19,negate,eq=contrast=0.72:brightness=0.1",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(target),
        ],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
