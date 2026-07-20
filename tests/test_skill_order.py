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

    def test_default_flow_is_direct_delivery_without_review_or_qa_tools(self) -> None:
        controller = (SKILLS / "00-huihua-video" / "SKILL.md").read_text(encoding="utf-8")
        image_director = (SKILLS / "40-huihua-image-director" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        renderer = (SKILLS / "60-huihua-remotion-renderer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("唯一默认流程", controller)
        self.assertIn("最多 3 张并发生图", controller)
        self.assertIn("自动重新生成最多 3 次", image_director)
        self.assertIn("直接交付", renderer)
        self.assertNotIn("$image-prompt-generator", controller)
        self.assertNotIn("$image-prompt-generator", image_director)
        self.assertFalse((PLUGIN / "scripts" / "production_gate.py").exists())
        self.assertFalse((PLUGIN / "scripts" / "probe_image.py").exists())
        self.assertFalse((PLUGIN / "assets" / "workflow-state-schema.json").exists())

    def test_controller_defaults_to_finished_output_mode(self) -> None:
        controller = (SKILLS / "00-huihua-video" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("默认模式：成品执行模式", controller)
        self.assertIn("只有当前请求明确要求修改、开发、测试或发布 `huihua-video` 插件源码", controller)
        self.assertIn("运行失败不得切换为开发模式", controller)
        self.assertIn("当前工作目录位于插件仓库", controller)

        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn(
            "使用 $huihua-video，自由发挥并直接交付 MP4。",
            manifest["interface"]["defaultPrompt"],
        )

    def test_tts_runtime_does_not_write_request_or_response_logs(self) -> None:
        minimax = (PLUGIN / "scripts" / "minimax_tts_timeline.py").read_text(
            encoding="utf-8"
        )
        volcengine = (PLUGIN / "scripts" / "volcengine_tts_timeline.py").read_text(
            encoding="utf-8"
        )
        for source in (minimax, volcengine):
            self.assertNotIn("-request.json", source)
            self.assertNotIn("-response.json", source)


if __name__ == "__main__":
    unittest.main()
