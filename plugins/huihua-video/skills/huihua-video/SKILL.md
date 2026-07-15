---
name: huihua-video
description: 作为唯一公开入口，把文章或口播编排为 MiniMax 配音、准确字幕、完整插画和 Remotion 动态成片。
---

# 绘画视频总控

## 目标

把输入内容制作成具有连续绘画过程、绘本叙事和准确音画关系的视频。不得直接从文章跳到渲染，也不得复用与当前内容无关的旧模板。

## 输入

至少接收文章正文、文章链接或待确认口播文案中的一种。可选输入包括目标时长、发布平台、画面方向、输出目录和参考视频。

当前音频只支持 MiniMax。首次使用必须先完成 API Key、`voice_id` 和图片工作流配置。

## 首次使用引导

1. 运行 `python3 ../../scripts/doctor.py` 检查环境。
2. MiniMax 未配置时，运行 `python3 ../../scripts/configure_minimax.py`，让用户通过隐藏输入提供 API Key。禁止在聊天、命令参数、项目文件或 Git 中回显密钥。
3. 引导用户访问 https://www.minimaxi.com/audio/voices 试听音色，并复制完整 `voice_id`。
4. 检查 `$image-prompt-generator` 是否安装。图片提示词、渠道配置、API Key 和付费生成批准全部遵循该 Skill 自己的规则。
5. 完成配置后再次运行环境检查；未通过时不得进入制作。

详细说明见 `../../references/制作规范/首次使用配置.md`。

## 固定流程

1. 建立符合 `../../assets/workflow-state-schema.json` 的 `workflow-state.json`。
2. 调用 `$huihua-script-planner` 生成并确认口播文案。
3. 调用 `$huihua-audio-timeline` 使用 MiniMax 生成最终音频与原生字幕时间轴。
4. 调用 `$huihua-scene-designer` 生成 `scene-manifest.json`。
5. 调用 `$huihua-image-director`，由 `$image-prompt-generator` 完成图片规划、提示词审核和受控生图，再生成 `image-manifest.json`。
6. 调用 `$huihua-motion-director` 生成 `motion-plan.json`。
7. 用户要求审核时，先展示场景、插画与动效方案，不得提前渲染。
8. 调用 `$huihua-remotion-renderer` 执行生产门禁、渲染和成片检查。
9. 成功后更新状态为 `completed`，清理交付目录中的临时文件。

## 状态与失效

阶段只能是 `intake`、`script`、`audio_timeline`、`scene_design`、`image_production`、`motion_design`、`review`、`render`、`qa`、`completed`。

修改口播、MiniMax 模型或音色后，必须让旧音频、时间轴及下游产物失效。修改场景后，必须让旧图片与动效方案失效。禁止使用旧产物继续渲染。

## 强制规则

- 字幕正文来自已确认口播；MiniMax 原生字幕只提供时间。
- MiniMax 缺少有效原生字幕文件时停止，不猜测、不降级。
- 场景切换和字幕切换彼此独立。
- 生图必须调用 `$image-prompt-generator`，并保留其逐图审核与付费生成批准门禁。
- 生成图片不预设固定比例；记录实际宽高，并由实际比例驱动画布。
- 所有插画必须完整显示，禁止裁切主体。
- 单个大场景内部至少包含两种有效进展：线稿、上色、人物或道具进入、局部动作、镜头运动。
- 禁止噪点、无意义抖动、持续漂移和重复卡片布局。
- 渲染前必须运行 `../../scripts/production_gate.py`。

## 必读

- `../../references/制作规范/首次使用配置.md`
- `../../references/制作规范/绘画视频生产规范.md`
- `../../references/制作规范/音频字幕契约.md`
- `../../references/制作规范/插画与动效语言.md`
