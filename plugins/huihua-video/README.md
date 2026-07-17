# 绘画视频

面向 Codex 的文章转绘本式动态视频工作流。输入文章或口播文案后，工作流会先确认手绘风格和音频模型，再完成口播规划、配音、原生字幕时间轴、插画场景、动态设计、Remotion 渲染和成片检查。

当前版本：`0.3.0`

## 能解决什么问题

- 在每条视频开始前选择古风手绘、卡通手绘，或描述自定义手绘方向。
- 使用 MiniMax `speech-2.8-hd` 或 Doubao `seed-tts-2.0` 配音，并保存用户选择的默认音色。
- 把文章压缩成适合短视频的口播文案。
- 为每个叙事段落设计完整插画，而不是重复使用卡片模板。
- 让线稿、上色、人物、道具和镜头运动在同一幅画中逐步发生。
- 让字幕严格跟随最终音频，同时保持字幕正文与已确认口播一致。
- 保留生成图片的原始比例，以完整显示为优先，不裁切主体。

## 工作流

```text
文章或口播
→ 选择手绘风格
→ 选择与配置音频模型
→ 配置 Image Prompt Generator 默认生图模型
→ 口播规划
→ 最终音频
→ 服务商原生字幕时间轴
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
| `huihua-audio-timeline` | 使用已选 MiniMax 或 Doubao 生成最终音频和原生字幕时间轴 |
| `huihua-scene-designer` | 将口播拆成连续发展的绘画场景 |
| `huihua-image-director` | 调用 `$image-prompt-generator` 规划并生成完整插画 |
| `huihua-motion-director` | 设计线稿、上色、分层、局部动作和镜头运动 |
| `huihua-remotion-renderer` | 执行门禁、渲染、检查并整理交付目录 |

## 环境要求

- Node.js 20 或更高版本
- FFmpeg 与 FFprobe
- MiniMax API Key 或火山引擎 API Key
- 从音色库试听并复制的完整 `voice_id`
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

首次使用会先选择本条视频的手绘风格与画面比例，再选择音频模型：

1. `minimax-speech-2.8-hd`：打开 https://www.minimaxi.com/audio/voices，选择音色并设置默认 `voice_id`。
2. `Doubao-语音合成-2.0`：打开 https://console.volcengine.com/ark/region:cn-beijing/experience/voice?model=doubao-seed-tts-2-0，选择音色并设置默认 `voice_id`。
3. 其他：收集服务商与原生时间戳协议；未完成适配前不会开始渲染。

MiniMax 配置命令：

```bash
python3 scripts/configure_minimax.py
```

Doubao 配置命令：

```bash
python3 scripts/configure_volcengine.py
```

配置脚本通过隐藏输入接收 API Key，保存默认 `voice_id` 到用户配置目录，不会写入视频项目或 Git。

绘画场景的图片规划、提示词审核和受控生图统一调用 `$image-prompt-generator`。完成音频选择后，按照该 Skill 的引导配置图片渠道并设置默认生图模型；图片渠道使用自己的密钥，不复用音频模型 API Key。

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
├── style-profile.json
├── minimax-subtitles.json 或 volcengine-subtitles.json
├── subtitle-timeline.json
├── scene-manifest.json
├── image-manifest.json
├── motion-plan.json
└── production-gate.json
```

临时帧、线稿缓存、预览图和渲染缓存可在制作过程中保留，交付成功后由清理工具删除。

## 质量边界

- 服务商原生字幕只提供时间，不改写字幕正文。
- MiniMax 或 Doubao 未返回有效原生字幕时间戳时立即停止，不估算时间。
- 图片必须经过 `$image-prompt-generator` 的 Prompt 审核与生图批准流程。
- 主画面负责解释和叙事，不重复整句字幕。
- 禁止为了“有动态”添加抖动、噪点或无意义漂移。
- 禁止把每个镜头做成相同排版的卡片。
- 图片按实际尺寸进入画布，使用 `contain` 完整显示。
- 生产门禁不通过时不得宣称视频已经完成。
