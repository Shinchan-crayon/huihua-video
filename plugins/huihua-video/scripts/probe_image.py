#!/usr/bin/env python3
"""Read image dimensions with ffprobe and return a manifest-ready record."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: probe_image.py <image>", file=sys.stderr)
        return 2
    image = pathlib.Path(sys.argv[1]).resolve()
    if not image.is_file():
        print(f"Image does not exist: {image}", file=sys.stderr)
        return 1
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(image),
    ]
    payload = json.loads(subprocess.check_output(command, text=True))
    stream = payload["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive.")
    print(
        json.dumps(
            {
                "file": str(image),
                "width": width,
                "height": height,
                "aspect_ratio": width / height,
                "fit": "contain",
                "crop_allowed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
