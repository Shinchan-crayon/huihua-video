# 绘画视频工作流

把文章或口播文案直接制作成带手绘风格、MiniMax 或 Doubao 配音、准确字幕、绘本式动态插画和 Remotion 成片的 Codex 插件。

当前版本：`0.3.2`

## 它能做什么

- 把长文章压缩成适合短视频的口播文案。
- 自动选择古风手绘、卡通手绘或采用用户指定风格，画面比例默认 `3:4`。
- 使用 MiniMax `speech-2.8-hd` 或 Doubao `seed-tts-2.0` 生成最终配音，并读取服务商原生字幕时间轴。
- 为每个叙事段落设计完整插画场景，而不是重复卡片模板。
- 由绘画视频插画导演直接生成 Prompt，并调用已配置的默认生图模型，以 3 张为上限并发生图。
- 设计线稿、上色、人物或道具进入、局部动作和镜头运动。
- 图片返回后立即使用 Remotion 渲染并交付 MP4。

## 适合谁

- 想把文章、观点稿或口播稿转成绘本式动态视频的创作者。
- 需要配音、字幕、插画、动效和渲染串成一个流程的内容团队。
- 希望一句话下达任务后直接拿到视频、不需要中间确认的人。

## 不适合什么

- 不适合一键自动发布视频。
- 不适合跳过服务商配音和字幕校验直接估算时间轴。
- 不适合把每个画面做成相同排版的卡片视频。
- 不适合没有配置所选音频模型 API Key、默认 `voice_id` 或图片工作流的环境直接运行。

## 安装

在 Codex 中发送：

```text
请安装“绘画视频工作流”插件：
https://github.com/Shinchan-crayon/huihua-video
```

也可以通过命令行安装：

```bash
codex plugin marketplace add Shinchan-crayon/huihua-video --ref main
codex plugin add huihua-video@huihua-video
```

## 使用

安装后新建 Codex 任务，输入：

```text
使用 $huihua-video，把这篇文章制作成绘本式动态视频：<文章或链接>
```

只有首次缺少模型配置时，插件才会引导设置默认音频模型、`voice_id` 和默认生图模型。音频配置可使用：

```bash
python3 scripts/doctor.py
python3 scripts/configure_minimax.py
python3 scripts/configure_volcengine.py
```

## 插件内容

真正的插件目录位于：

```text
plugins/huihua-video/
```

其中 `plugins/huihua-video/README.md` 包含完整工作流说明、环境要求、交付目录和质量边界。

## 能力边界

- `huihua-video` 与 `Shin-video` 是两个独立产品；不共享 Skill、配置、模板、缓存或运行产物。
- 中间产物只写入项目内 `.huihua-video-runtime/`，不写工作流状态台账。
- 服务商原生字幕只提供时间，不改写字幕正文。
- MiniMax 或 Doubao 未返回有效原生字幕文件时立即停止，不估算时间。
- 用户调用 `$huihua-video` 即授权本次 Prompt、付费生图、自动重试和渲染，不再次索要批准。
- 单张图片首次失败后自动重试 3 次，三次重试均未返回图片时才报告错误。
- 不运行生产门禁、验图、截图、抽帧、黑帧检查或成片质检。
