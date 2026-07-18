# 绘画视频

面向 Codex 的文章转绘本式动态视频工作流。输入选题、文章或口播后，使用已配置的默认模型连续完成口播、配音、字幕、插画和 Remotion 渲染，直接交付 MP4。

当前版本：`0.3.2`

## 能解决什么问题

- 自动选择古风手绘、卡通手绘，或直接采用用户指定的自定义方向。
- 使用 MiniMax `speech-2.8-hd` 或 Doubao `seed-tts-2.0` 配音，并保存用户选择的默认音色。
- 把文章压缩成适合短视频的口播文案。
- 为每个叙事段落设计完整插画，而不是重复使用卡片模板。
- 让线稿、上色、人物、道具和镜头运动在同一幅画中逐步发生。
- 让字幕严格跟随最终音频，同时保持字幕正文与本次最终口播一致。
- 保留生成图片的原始比例，以完整显示为优先，不裁切主体。

## 工作流

```text
选题、文章或口播
→ 自动确定口播、风格和比例
→ 最终音频
→ 服务商原生字幕时间轴
→ 绘画场景
→ Prompt 固定写入比例
→ Image Prompt Generator 每批最多 3 张并发生图
→ 线稿与图层素材
→ 动效方案
→ Remotion 渲染
→ 直接交付 MP4
```

## 与 Shin-video 的边界

`huihua-video` 和 `Shin-video` 是两个独立产品，不是同一工作流的两个名字或模式。安装 `huihua-video` 不会调用 `$shin-video-*`，也不会读取或写入 Shin-video 仓库、`.shin-video-runtime`、配置、模板和历史产物。

`huihua-video` 的用户配置固定在 `~/.config/huihua-video`，所有中间产物固定在当前项目的 `.huihua-video-runtime/`。路径边界会拒绝跨产品路径和项目目录之外的资产，不创建工作流状态台账。

## Skill 组成

| Skill | 作用 |
| --- | --- |
| `huihua-video` | 唯一公开入口，连续编排并直接交付完整视频 |
| `huihua-script-planner` | 整理文章并直接生成最终口播与叙事节拍 |
| `huihua-audio-timeline` | 使用已选 MiniMax 或 Doubao 生成最终音频和原生字幕时间轴 |
| `huihua-scene-designer` | 将口播拆成连续发展的绘画场景 |
| `huihua-image-director` | 调用 `$image-prompt-generator` 规划并生成完整插画 |
| `huihua-motion-director` | 设计线稿、上色、分层、局部动作和镜头运动 |
| `huihua-remotion-renderer` | 直接渲染 MP4 并整理交付目录 |

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

初始化每条新视频的独立项目，不生成状态台账：

```bash
python3 scripts/initialize_huihua_project.py \
  --project-dir /absolute/path/to/project
```

## 首次配置

只有首次缺少配置时才选择默认音频模型：

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

绘画场景的 Prompt 和生图统一调用 `$image-prompt-generator`。完成首次配置后直接使用默认图片渠道；图片渠道使用自己的密钥，不复用音频模型 API Key。用户调用 `$huihua-video` 即授权本次 Prompt、付费生图和自动重试。

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
├── style-profile.json
├── minimax-subtitles.json 或 volcengine-subtitles.json
├── subtitle-timeline.json
├── scene-manifest.json
├── image-manifest.json
└── motion-plan.json
```

临时帧、线稿缓存、预览图和渲染缓存可在制作过程中保留，交付成功后由清理工具删除。

制作期间的中间产物统一位于：

```text
日期/视频标题/.huihua-video-runtime/
```

## 执行边界

- 服务商原生字幕只提供时间，不改写字幕正文。
- MiniMax 或 Doubao 未返回有效原生字幕时间戳时立即停止，不估算时间。
- 每条 Prompt 固定写入 `style-profile.json.aspect_ratio`；未指定时使用 `3:4`。
- 生图每批最多并发 3 张，单张失败自动重试 3 次。
- 不展示或复审 Prompt，不再次询问生图批准。
- 主画面负责解释和叙事，不重复整句字幕。
- 禁止为了“有动态”添加抖动、噪点或无意义漂移。
- 禁止把每个镜头做成相同排版的卡片。
- 图片使用目标比例和 `contain` 完整显示。
- 不运行生产门禁、图片探测、截图、抽帧、黑帧检查或成片质检。
