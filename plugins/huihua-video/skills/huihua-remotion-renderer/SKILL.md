---
name: huihua-remotion-renderer
description: 校验绘画视频生产产物，使用自适应 Remotion 模板渲染，并完成音画与交付检查。
---

# 绘画视频 Remotion 渲染

## 输入

必须同时提供 `workflow-state.json`、`narration.json`、最终音频、`subtitle-timeline.json`、`scene-manifest.json`、`image-manifest.json` 和 `motion-plan.json`。

## 执行

1. 运行 `../../scripts/production_gate.py <project-dir>`。
2. 将模板 `../../templates/Remotion绘画视频模板` 复制到项目运行目录。
3. 把插画、线稿、音频和 JSON 复制到模板 `public/runtime`。
4. 安装依赖并运行模板的渲染命令。
5. 使用 FFprobe 检查分辨率、时长、帧率和音轨。
6. 抽取代表帧检查字幕安全区、图片完整显示和空白帧。
7. 成功后运行 `../../scripts/package_delivery.py <project-dir>` 清理临时文件。

## Remotion 规则

- 所有动画必须由 `useCurrentFrame()` 和输入 JSON 决定。
- 使用 `<Sequence>` 编排场景，字幕在独立的全片层渲染。
- 图片使用 `<Img>` 与 `staticFile()`。
- 画布元数据根据图片实际比例和目标发布方向计算。
- 图片使用 `contain`，不能为了填满画布裁切。
- 转场不得缩短字幕或场景的有效时长。
- 不在组件中写死用户绝对路径。

## 完成标准

只有门禁通过、渲染成功、视频包含音轨且检查未发现裁切、字幕越界或黑帧，才能把工作流写为 `completed`。
