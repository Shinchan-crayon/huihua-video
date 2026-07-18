---
name: huihua-remotion-renderer
description: 使用自带 Remotion 模板直接渲染 huihua-video 项目并交付 MP4。
---

# 绘画视频 Remotion 渲染

## 产品边界

仅渲染当前 huihua-video 项目目录内的素材，不接受 Shin-video 仓库、`.shin-video-runtime` 或项目目录之外的资产。

## 输入

必须同时提供最终音频、`subtitle-timeline.json`、`scene-manifest.json`、`image-manifest.json`、`motion-plan.json` 和 `style-profile.json`。

## 执行

1. 将模板 `../../templates/Remotion绘画视频模板` 复制到 `<project>/.huihua-video-runtime/remotion/`。
2. 把当前项目内的插画、线稿、音频和 JSON 复制到该模板的 `public/runtime`。
3. 根据 `style-profile.json.aspect_ratio` 设置 Remotion 画布，把清单合并为渲染属性。
4. 安装依赖并运行模板的渲染命令。
5. 渲染命令成功后立即把 MP4 放入交付目录。
6. 运行 `../../scripts/package_delivery.py <project-dir>` 删除临时文件。

## Remotion 规则

- 所有动画必须由 `useCurrentFrame()` 和输入 JSON 决定。
- 使用 `<Sequence>` 编排场景，字幕在独立的全片层渲染。
- 图片使用 `<Img>` 与 `staticFile()`。
- 画布元数据根据 `style-profile.json.aspect_ratio` 的目标比例计算。
- 图片使用 `contain`，不能为了填满画布裁切。
- 转场不得缩短字幕或场景的有效时长。
- 不在组件中写死用户绝对路径。
- 不调用 Shin-video 模板、Skill 或 `.shin-video-runtime`，也不接受项目目录之外的资产。

## 完成标准

Remotion 渲染命令成功并生成 MP4 后立即直接交付。不要运行生产门禁、FFprobe、抽帧、截图、黑帧检查、字幕布局检查、联系表或任何成片质检。
