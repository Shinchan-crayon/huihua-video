from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "huihua-video"
SKILLS = PLUGIN / "skills"


class SkillOrderTests(unittest.TestCase):
    def test_skill_directories_follow_workflow_order(self) -> None:
        expected = [
            "huihua-video",
            "huihua-script-planner",
            "huihua-audio-timeline",
            "huihua-scene-designer",
            "huihua-image-director",
            "huihua-motion-director",
            "huihua-remotion-renderer",
        ]
        actual = []
        for skill_dir in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
            contents = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            frontmatter = yaml.safe_load(contents.split("---", 2)[1])
            actual.append(frontmatter["name"])
        self.assertEqual(actual, expected)

    def test_legacy_manifest_paths_exist_and_start_with_controller(self) -> None:
        manifest = json.loads(
            (PLUGIN / "plugin-manifest" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["entry_skill"], "skills/00-huihua-video")
        self.assertEqual(manifest["skills"][0], manifest["entry_skill"])
        for relative_path in manifest["skills"]:
            self.assertTrue((PLUGIN / relative_path / "SKILL.md").is_file())

    def test_audio_skill_copy_supports_both_tts_providers(self) -> None:
        agent = yaml.safe_load(
            (
                SKILLS
                / "20-huihua-audio-timeline"
                / "agents"
                / "openai.yaml"
            ).read_text(encoding="utf-8")
        )
        description = agent["interface"]["short_description"]
        self.assertIn("MiniMax", description)
        self.assertIn("Doubao", description)


if __name__ == "__main__":
    unittest.main()
