# 绘画视频

面向 Codex 的文章转绘本式动态视频工作流。输入文章或口播文案后，工作流会完成口播规划、MiniMax 配音、原生字幕时间轴、插画场景、动态设计、Remotion 渲染和成片检查。

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
→ MiniMax 最终音频
→ MiniMax 原生字幕时间轴
→ 绘画场景
→ Image Prompt Generator 插画
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
| `huihua-audio-timeline` | 使用 MiniMax 生成最终音频和原生字幕时间轴 |
| `huihua-scene-designer` | 将口播拆成连续发展的绘画场景 |
| `huihua-image-director` | 调用 `$image-prompt-generator` 规划并生成完整插画 |
| `huihua-motion-director` | 设计线稿、上色、分层、局部动作和镜头运动 |
| `huihua-remotion-renderer` | 执行门禁、渲染、检查并整理交付目录 |

## 环境要求

- Node.js 20 或更高版本
- FFmpeg 与 FFprobe
- MiniMax API Key
- 从 https://www.minimaxi.com/audio/voices 试听并复制的完整 `voice_id`
- 已安装的 `$image-prompt-generator`

尚未安装图片工作流时，在 Codex 中安装：

```text
请从 https://github.com/Shinchan-crayon/image-prompt-generator 安装 image-prompt-generator Skill。
```

运行环境检查：

```bash
python3 scripts/doctor.py
```

## 首次配置

当前音频只支持 MiniMax。首次使用运行：

```bash
python3 scripts/configure_minimax.py
```

脚本会通过隐藏输入接收 API Key，然后引导你打开 https://www.minimaxi.com/audio/voices 试听音色并粘贴完整 `voice_id`。API Key 保存到用户配置目录，不会写入视频项目或 Git。

绘画场景的图片规划、提示词审核和受控生图统一调用 `$image-prompt-generator`。第一次实际生图时，按照该 Skill 的引导配置图片渠道；图片渠道使用自己的密钥，不复用 MiniMax API Key。

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
├── minimax-subtitles.json
├── subtitle-timeline.json
├── scene-manifest.json
├── image-manifest.json
├── motion-plan.json
└── production-gate.json
```

临时帧、线稿缓存、预览图和渲染缓存可在制作过程中保留，交付成功后由清理工具删除。

## 质量边界

- MiniMax 原生字幕只提供时间，不改写字幕正文。
- MiniMax 未返回有效原生字幕文件时立即停止，不估算时间。
- 图片必须经过 `$image-prompt-generator` 的 Prompt 审核与生图批准流程。
- 主画面负责解释和叙事，不重复整句字幕。
- 禁止为了“有动态”添加抖动、噪点或无意义漂移。
- 禁止把每个镜头做成相同排版的卡片。
- 图片按实际尺寸进入画布，使用 `contain` 完整显示。
- 生产门禁不通过时不得宣称视频已经完成。
