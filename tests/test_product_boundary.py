from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins" / "huihua-video" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from project_boundary import (  # noqa: E402
    BoundaryViolation,
    RUNTIME_NAMESPACE,
    load_project_state,
    resolve_project_asset,
    runtime_dir,
    validate_project_root,
    validate_state_identity,
)


class ProductBoundaryTests(unittest.TestCase):
    def test_rejects_shin_video_project_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "Shin-video" / "project"
            with self.assertRaises(BoundaryViolation):
                validate_project_root(project)

    def test_rejects_shin_video_runtime_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / ".shin-video-runtime" / "project"
            with self.assertRaises(BoundaryViolation):
                validate_project_root(project)

    def test_uses_huihua_runtime_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "drawing-project"
            self.assertEqual(runtime_dir(project), project.resolve() / RUNTIME_NAMESPACE)

    def test_rejects_shin_video_uri(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(BoundaryViolation):
                resolve_project_asset(temporary, "shin-video://images/scene.png", "image")

    def test_rejects_asset_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            with self.assertRaises(BoundaryViolation):
                resolve_project_asset(root, "../shared/audio.mp3", "audio")

    def test_requires_huihua_state_identity(self) -> None:
        self.assertEqual(
            validate_state_identity(
                {
                    "product_id": "huihua-video",
                    "runtime_namespace": ".huihua-video-runtime",
                }
            ),
            [],
        )
        self.assertEqual(len(validate_state_identity({"product_id": "shin-video"})), 2)

    def test_load_project_state_rejects_missing_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            (project / "workflow-state.json").write_text(
                '{"workflow_id":"legacy"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(BoundaryViolation):
                load_project_state(project)

    def test_initializer_and_style_profile_share_huihua_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "drawing-project"
            initializer = SCRIPTS / "initialize_huihua_project.py"
            style_script = SCRIPTS / "create_style_profile.py"
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(initializer),
                    "--project-dir",
                    str(project),
                    "--workflow-id",
                    "test-video",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            styled = subprocess.run(
                [
                    sys.executable,
                    str(style_script),
                    "--project-dir",
                    str(project),
                    "--style",
                    "restrained-childrens-coloring-paper",
                    "--aspect-ratio",
                    "3:4",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(styled.returncode, 0, styled.stderr)
            self.assertTrue((project / RUNTIME_NAMESPACE).is_dir())
            self.assertTrue((project / "style-profile.json").is_file())
            self.assertEqual(load_project_state(project)["product_id"], "huihua-video")


if __name__ == "__main__":
    unittest.main()
