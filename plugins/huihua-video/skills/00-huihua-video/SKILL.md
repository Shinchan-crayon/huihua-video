---
name: huihua-video
description: 作为绘画视频工作流的唯一公开入口，引导选择手绘风格、音频模型与生图模型，再把文章或口播编排为准确字幕、完整插画和 Remotion 动态成片。
---

# 绘画视频总控

## 目标

把输入内容制作成具有连续绘画过程、绘本叙事和准确音画关系的视频。不得直接从文章跳到渲染，也不得复用与当前内容无关的旧模板。

## 产品隔离

`huihua-video` 与 `Shin-video` 是两个独立产品。用户调用 `$huihua-video` 时，只能调用本插件的 `$huihua-*` Skill，不得调用 `$shin-video-*`，不得读取或修改 Shin-video 仓库、`.shin-video-runtime`、配置、模板或历史产物。

视频项目不得位于名为 `Shin-video` 或 `.shin-video-runtime` 的路径内。所有中间产物统一写入当前项目的 `.huihua-video-runtime/`；用户配置只写入 `~/.config/huihua-video`。继续旧项目时必须先校验 `workflow-state.json.product_id == "huihua-video"` 与 `runtime_namespace == ".huihua-video-runtime"`，身份不匹配时停止。

完整边界见 `../../references/制作规范/产品边界.md`。

## 输入

至少接收文章正文、文章链接或待确认口播文案中的一种。可选输入包括目标时长、发布平台、画面方向、输出目录和参考视频。

首次制作一条新视频时，必须先完成风格选择；首次使用或用户要求更换默认配置时，必须完成音频模型、默认 `voice_id` 和图片工作流配置。

## 首次引导顺序

不得跳过以下顺序，也不得暗中替用户选择默认风格或音频模型。

### 1. 选择本条视频的手绘风格

向用户展示以下三个选项并等待确认：

1. **古风手绘风格**：使用《东施效颦》已跑通的中国绘本路径，水墨线稿、透明水彩、自然留白与东方叙事构图。
2. **卡通手绘风格**：使用低饱和克制儿童涂色纸路径，粗糙手绘线条、真实纸面、少量低饱和蜡笔填色与有节制的幽默感。
3. **其他**：要求用户用一句话描述视觉媒介、配色、人物表现与参考方向；描述不完整时继续追问，不能套用前两种预设。

确认后，在视频项目根目录创建 `style-profile.json`，记录 `style_id`、`style_name`、`prompt_profile`、用户要求的画面比例与自定义说明。预设的完整提示词规则在 `../../references/制作规范/风格预设.md`。选择变化后，旧 `scene-manifest.json`、`image-manifest.json` 和 `motion-plan.json` 必须失效。

### 2. 选择并配置默认音频模型

向用户展示以下三个选项并等待确认：

1. **minimax-speech-2.8-hd**：返回 https://www.minimaxi.com/audio/voices，请用户试听并选择一个默认 `voice_id`；使用 `python3 ../../scripts/configure_minimax.py` 通过隐藏输入保存 API Key 和默认音色。
2. **Doubao-语音合成-2.0**：返回 https://console.volcengine.com/ark/region:cn-beijing/experience/voice?model=doubao-seed-tts-2-0，请用户试听并选择一个默认 `voice_id`；使用 `python3 ../../scripts/configure_volcengine.py` 通过隐藏输入保存 API Key 和默认音色。
3. **其他**：要求用户提供服务商名称、模型、音色 ID、调用文档以及可逐字或逐词对齐的原生时间戳能力。当前版本没有通过适配和测试前不得生成音频、字幕或渲染。

不得在聊天、命令参数、项目文件或 Git 中回显 API Key。

### 3. 配置默认生图模型

调用 `$image-prompt-generator`，严格按其首次配置流程选择图片渠道、通过隐藏输入配置图片渠道自己的 API Key，并设置默认生图模型。不得读取、复用或写入音频模型 API Key。未完成此步骤时不得进入图片生成。

## 首次使用引导

1. 运行 `python3 ../../scripts/doctor.py` 检查环境。
2. 若没有已确认的音频模型配置，依照“首次引导顺序”的第 2 步完成选择与配置。
3. 检查 `$image-prompt-generator` 是否安装，依照“首次引导顺序”的第 3 步完成配置。
4. 完成配置后再次运行环境检查；未通过时不得进入制作。

详细说明见 `../../references/制作规范/首次使用配置.md`。

## 固定流程

1. 运行 `python3 ../../scripts/initialize_huihua_project.py --project-dir <project-dir> --workflow-id <workflow-id>`，建立符合 `../../assets/workflow-state-schema.json` 的 `workflow-state.json` 和项目内 `.huihua-video-runtime/`。
2. 先确认本条视频的手绘风格与画面比例，并创建 `style-profile.json`。
3. 确认或配置默认音频模型与 `voice_id`。
4. 调用 `$image-prompt-generator` 的原生首次配置流程，确认默认生图模型。
5. 调用 `$huihua-script-planner` 生成并确认口播文案。
6. 调用 `$huihua-audio-timeline` 使用已选择的音频模型生成最终音频与原生字幕时间轴。
7. 调用 `$huihua-scene-designer` 生成 `scene-manifest.json`。
8. 调用 `$huihua-image-director`，由 `$image-prompt-generator` 完成图片规划、提示词审核和受控生图，再生成 `image-manifest.json`。
9. 调用 `$huihua-motion-director` 生成 `motion-plan.json`。
10. 用户要求审核时，先展示场景、插画与动效方案，不得提前渲染。
11. 调用 `$huihua-remotion-renderer` 执行生产门禁、渲染和成片检查。
12. 成功后更新状态为 `completed`，清理交付目录中的临时文件。

## 状态与失效

阶段只能是 `intake`、`script`、`audio_timeline`、`scene_design`、`image_production`、`motion_design`、`review`、`render`、`qa`、`completed`。

修改口播、音频模型或音色后，必须让旧音频、时间轴及下游产物失效。修改风格或场景后，必须让旧图片与动效方案失效。禁止使用旧产物继续渲染。

## 强制规则

- 字幕正文来自已确认口播；服务商原生字幕只提供时间。
- MiniMax 或 Doubao 缺少有效原生字幕时间戳时停止，不猜测、不降级。
- 场景切换和字幕切换彼此独立。
- 生图必须调用 `$image-prompt-generator`，并保留其逐图审核与付费生成批准门禁。
- 用户确认画面比例后，每条图片 Prompt 必须显式写入该比例；生成后仍须记录实际宽高，并由实际比例驱动画布。
- 所有插画必须完整显示，禁止裁切主体。
- 单个大场景内部至少包含两种有效进展：线稿、上色、人物或道具进入、局部动作、镜头运动。
- 禁止噪点、无意义抖动、持续漂移和重复卡片布局。
- 渲染前必须运行 `../../scripts/production_gate.py`。
- 不接受来自 Shin-video 或项目目录之外的音频、图片、清单、模板与运行产物。

## 必读

- `../../references/制作规范/首次使用配置.md`
- `../../references/制作规范/产品边界.md`
- `../../references/制作规范/绘画视频生产规范.md`
- `../../references/制作规范/音频字幕契约.md`
- `../../references/制作规范/插画与动效语言.md`
