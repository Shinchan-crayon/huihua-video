# 绘画视频

面向 Codex 的文章转绘本式动态视频工作流。输入文章、口播文案或已有音频后，工作流会完成口播规划、最终音频、时间轴、插画场景、动态设计、Remotion 渲染和成片检查。

## 能解决什么问题

- 把文章压缩成适合短视频的口播文案。
- 为每个叙事段落设计完整插画，而不是重复使用卡片模板。
- 让线稿、上色、人物、道具和镜头运动在同一幅画中逐步发生。
- 让字幕严格跟随最终音频，同时保持字幕正文与已确认口播一致。
- 保留生成图片的原始比例，以完整显示为优先，不裁切主体。

## 工作流

```text
文章或口播
→ 口播规划
→ 最终音频
→ WhisperX 时间轴
→ 绘画场景
→ 完整插画
→ 线稿与图层素材
→ 动效方案
→ 生产门禁
→ Remotion 渲染
→ 音画检查
```

## Skill 组成

| Skill | 作用 |
| --- | --- |
| `huihua-video` | 唯一公开入口，维护状态并编排完整流程 |
| `huihua-script-planner` | 整理文章并生成可确认的口播与叙事节拍 |
| `huihua-audio-timeline` | 生成或接收最终音频，使用 WhisperX 提供时间 |
| `huihua-scene-designer` | 将口播拆成连续发展的绘画场景 |
| `huihua-image-director` | 生成完整插画提示词、素材清单和尺寸记录 |
| `huihua-motion-director` | 设计线稿、上色、分层、局部动作和镜头运动 |
| `huihua-remotion-renderer` | 执行门禁、渲染、检查并整理交付目录 |

## 环境要求

- Node.js 20 或更高版本
- FFmpeg 与 FFprobe
- 可用的 TTS 工具或用户提供的最终音频
- WhisperX，用于最终音频的词级或句级时间对齐
- 可用的图片生成工具

运行环境检查：

```bash
python3 scripts/doctor.py
```

## GitHub 安装

```bash
codex plugin marketplace add Shinchan-crayon/huihua-video --ref main
codex plugin add huihua-video@huihua-video
```

安装后新建 Codex 任务，在插件页面找到“绘画视频”，或直接输入：

```text
使用 $huihua-video，把这篇文章制作成绘本式动态视频：<文章或链接>
```

## 交付目录

```text
日期/视频标题/
├── 视频标题.mp4
├── 口播文案.md
├── workflow-state.json
├── subtitle-timeline.json
├── scene-manifest.json
├── image-manifest.json
├── motion-plan.json
└── production-gate.json
```

临时帧、线稿缓存、预览图和渲染缓存可在制作过程中保留，交付成功后由清理工具删除。

## 质量边界

- WhisperX 只提供时间，不改写字幕正文。
- 主画面负责解释和叙事，不重复整句字幕。
- 禁止为了“有动态”添加抖动、噪点或无意义漂移。
- 禁止把每个镜头做成相同排版的卡片。
- 图片按实际尺寸进入画布，使用 `contain` 完整显示。
- 生产门禁不通过时不得宣称视频已经完成。
