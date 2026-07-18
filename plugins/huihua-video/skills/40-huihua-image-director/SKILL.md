---
name: huihua-image-director
description: 为每个绘画场景制定完整插画提示词、角色一致性、素材分层和目标比例记录，确保不裁切。
---

# 绘画视频插画导演

## 产品边界

图片和清单必须留在当前 huihua-video 项目内，不得读取或复用 Shin-video 仓库、`.shin-video-runtime`、旧图片和缓存。

## 职责

根据 `scene-manifest.json` 和视频项目根目录的 `style-profile.json` 生成一幅或多幅完整叙事插画。优先一次生成完整画面，再按需要提取线稿和局部图层，不把多个不一致的小图硬拼成场景。

**REQUIRED SUB-SKILL:** 必须调用 `$image-prompt-generator`。

## 生图流程

1. 读取 `style-profile.json`；缺失时停止，不猜测为古风或卡通风格。
2. 把 `scene-manifest.json` 转为文章级图片规划，每个场景明确画面任务、核心观点和一致性锚点。
3. 使用 `$image-prompt-generator` 的正文配图模式直接生成每个场景的提示词。
4. 每条 Prompt 都必须拼接 `style-profile.json` 的 `prompt_profile`。用户指定画面比例时，Prompt 必须显式写入该比例；不允许让模型自由决定比例。
5. 不展示图片规划和 Prompt，直接使用已配置的默认图片渠道生图。
6. 每批最多并发 3 张；当前批次完成后立即开始下一批。
7. 失败图片自动重试，单张最多连续重试 3 次；3 次仍未返回图片才报告错误。
8. 全部图片返回后立即把结果和场景绑定写入 `image-manifest.json`，交给渲染阶段。

用户调用 `$huihua-video` 制作视频，即视为授权本次 Prompt 生成、付费生图和自动重试。不得再次展示 Prompt、索要批准或插入审核步骤。不得读取 MiniMax 配置，不得把 MiniMax API Key 用于图片渠道。

## 图片契约

- 必须按 `style-profile.json.aspect_ratio` 生成；每条 Prompt 都要明确包含该比例。
- 不探测、不截图、不审看图片；图片渠道返回有效图片文件即视为成功。
- Remotion 画布由 `style-profile.json.aspect_ratio` 决定。
- 使用 `objectFit: contain`，禁止裁切主体。
- 图片必须没有字幕、UI、边框、水印和无意义噪点。
- 同一人物、地点和关键物体必须使用一致性描述。

## 输出

生成符合 `../../assets/image-manifest-schema.json` 的 `image-manifest.json`，包含图片路径、绑定场景、提示词、画面比例、素材角色和禁止裁切声明。

需要线稿时运行：

```bash
python3 ../../scripts/extract_line_art.py <project-dir> color.png line.png
```

参照 `../../references/制作规范/插画与动效语言.md`。
