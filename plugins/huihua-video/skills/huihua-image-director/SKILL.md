---
name: huihua-image-director
description: 为每个绘画场景制定完整插画提示词、角色一致性、素材分层和实际尺寸记录，确保不裁切。
---

# 绘画视频插画导演

## 职责

根据 `scene-manifest.json` 生成一幅或多幅完整叙事插画。优先一次生成完整画面，再按需要提取线稿和局部图层，不把多个不一致的小图硬拼成场景。

**REQUIRED SUB-SKILL:** 必须调用 `$image-prompt-generator`。

## 生图流程

1. 把 `scene-manifest.json` 转为文章级图片规划，每个场景明确画面任务、核心观点和一致性锚点。
2. 使用 `$image-prompt-generator` 的正文配图模式生成每个场景的提示词。
3. 按该 Skill 的规则展示图片规划和逐图 Prompt，等待用户审核。
4. 用户明确批准后，才允许使用该 Skill 已配置的图片渠道生成图片。
5. 将生成结果、实际尺寸和场景绑定写入 `image-manifest.json`。

不得读取 MiniMax 配置，不得把 MiniMax API Key 用于图片渠道，也不得绕过 `$image-prompt-generator` 的审核和付费调用门禁。

## 图片契约

- 不强制生成比例。
- 每张图片生成后必须运行 `../../scripts/probe_image.py` 记录实际宽高。
- Remotion 画布和布局从实际宽高推导。
- 使用 `objectFit: contain`，禁止裁切主体。
- 图片必须没有字幕、UI、边框、水印和无意义噪点。
- 同一人物、地点和关键物体必须使用一致性描述。

## 输出

生成符合 `../../assets/image-manifest-schema.json` 的 `image-manifest.json`，包含图片路径、绑定场景、提示词、一致性锚点、实际宽高、素材角色、分层能力和禁止裁切声明。

需要线稿时运行：

```bash
python3 ../../scripts/extract_line_art.py color.png line.png
```

参照 `../../references/制作规范/插画与动效语言.md`。
