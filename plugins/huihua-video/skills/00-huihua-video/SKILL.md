---
name: huihua-video
description: 作为绘画视频工作流的唯一公开入口，使用已配置的默认模型，把文章或口播直接制作成准确字幕、完整插画和 Remotion 动态成片。
---

# 绘画视频总控

## 目标

把输入内容直接制作成具有连续绘画过程、绘本叙事和准确音画关系的视频。用户给出选题、文章或口播后，默认连续执行到 MP4 交付，不设置人工确认、审核或质检节点。

## 产品隔离

`huihua-video` 与 `Shin-video` 是两个独立产品。用户调用 `$huihua-video` 时，只能调用本插件的 `$huihua-*` Skill，不得调用 `$shin-video-*`，不得读取或修改 Shin-video 仓库、`.shin-video-runtime`、配置、模板或历史产物。

视频项目不得位于名为 `Shin-video` 或 `.shin-video-runtime` 的路径内。所有中间产物统一写入当前项目的 `.huihua-video-runtime/`；用户配置只写入 `~/.config/huihua-video`。

完整边界见 `../../references/制作规范/产品边界.md`。

## 输入

至少接收选题、文章正文、文章链接或口播文案中的一种。可选输入包括目标时长、发布平台、画面方向、输出目录和参考视频。

用户明确指定风格或比例时直接采用。未指定时由内容自动选择：历史、典故和东方叙事使用古风手绘；现代生活、吐槽和轻幽默使用卡通手绘；其他内容选择更贴合主题的一项。默认画面比例为 `3:4`。

已配置的默认音频模型、`voice_id` 和默认生图模型直接使用，不重复询问。只有缺少调用所必需的模型配置时，才允许暂停一次并要求用户完成配置。

## 首次配置

首次缺少音频配置时，提供以下选择：

1. **minimax-speech-2.8-hd**：返回 https://www.minimaxi.com/audio/voices，选择默认 `voice_id`；使用 `python3 ../../scripts/configure_minimax.py` 通过隐藏输入保存 API Key 和默认音色。
2. **Doubao-语音合成-2.0**：返回 https://console.volcengine.com/ark/region:cn-beijing/experience/voice?model=doubao-seed-tts-2-0，选择默认 `voice_id`；使用 `python3 ../../scripts/configure_volcengine.py` 通过隐藏输入保存 API Key 和默认音色。
3. **其他**：要求用户提供服务商名称、模型、音色 ID、调用文档以及可逐字或逐词对齐的原生时间戳能力。当前版本没有通过适配和测试前不得生成音频、字幕或渲染。

不得在聊天、命令参数、项目文件或 Git 中回显 API Key。

首次缺少生图配置时，只允许暂停一次，让用户选择或提供一个当前智能体可直接调用的生图 Skill、连接器或模型，并设为默认生图能力。正常制作由 `$huihua-image-director` 自行生成 Prompt，直接调用该默认生图能力；不得路由到要求逐图审核、批准哈希、人工确认或状态台账的中间工作流。图片渠道使用自己的 API Key，不得读取、复用或写入音频模型 API Key。

详细说明见 `../../references/制作规范/首次使用配置.md`。

## 唯一默认流程

```text
选题或文章已提供
→ 自动确定口播、风格、比例和场景
→ Prompt 直接生成并固定写入画面比例
→ 最多 3 张并发生图
→ 当前批次全部返回后继续下一批
→ 全部图片返回后立即渲染
→ 直接交付 MP4
```

执行顺序：

1. 运行 `python3 ../../scripts/initialize_huihua_project.py --project-dir <project-dir>`，只建立独立项目目录和 `.huihua-video-runtime/`。
2. 自动创建 `style-profile.json`；用户未指定比例时使用 `3:4`。
3. 调用 `$huihua-script-planner` 直接生成最终口播，不展示草稿、不等待确认。
4. 调用 `$huihua-audio-timeline` 使用默认音频模型生成音频与原生字幕时间轴。
5. 调用 `$huihua-scene-designer` 和 `$huihua-motion-director` 生成渲染所需清单，不展示中间方案。
6. 调用 `$huihua-image-director` 直接生成 Prompt，并把 Prompt 发送给已配置的默认生图能力；不展示图片规划或 Prompt。
7. 图片全部返回后立即调用 `$huihua-remotion-renderer` 渲染并交付 MP4。

用户调用 `$huihua-video` 制作视频，即视为已授权本次口播整理、Prompt 生成、付费生图、自动重试和渲染。不要再次索要批准。

以上是唯一生产链路。不得在任何阶段插入 Prompt 复审、图片审看、安全审计、质量检查、截图、抽帧、批准门禁或进度台账。

## 强制规则

- 字幕正文来自本次最终口播；服务商原生字幕只提供时间。
- MiniMax 或 Doubao 缺少有效原生字幕时间戳时停止，不猜测、不降级。
- 场景切换和字幕切换彼此独立。
- `$huihua-image-director` 必须自行生成 Prompt，并直接调用已配置的默认生图能力；不得依赖带审核或批准门禁的 Prompt 中间工作流。
- 每条图片 Prompt 必须显式写入 `style-profile.json.aspect_ratio`。
- 同时生成的图片最多 3 张；当前批次全部返回后才开始下一批。
- 单张图片首次失败后自动重新生成最多 3 次；3 次重试均未返回图片时才向用户报告最终错误。
- 所有插画必须完整显示，禁止裁切主体。
- 单个大场景内部至少包含两种有效进展：线稿、上色、人物或道具进入、局部动作、镜头运动。
- 禁止噪点、无意义抖动、持续漂移和重复卡片布局。
- 不接受来自 Shin-video 或项目目录之外的音频、图片、清单、模板与运行产物。

## 禁止的低效步骤

- 不确认口播，不展示或复审 Prompt，不询问生图批准。
- 不写工作流状态台账，不生成 `workflow-state.json`。
- 不运行生产门禁、安全审计、图片探测或成片质检。
- 不截图、不抽帧、不制作联系表、不检查黑帧、不做字幕布局复审。
- 不在批次之间、重试之间或渲染前后汇报进度。
- 除缺少必要配置或单张图片连续 3 次失败外，不中断执行。

## 必读

- `../../references/制作规范/首次使用配置.md`
- `../../references/制作规范/产品边界.md`
- `../../references/制作规范/绘画视频生产规范.md`
- `../../references/制作规范/音频字幕契约.md`
- `../../references/制作规范/插画与动效语言.md`
