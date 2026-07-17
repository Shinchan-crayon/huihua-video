# 绘画视频工作流

把文章或口播文案制作成带可选手绘风格、MiniMax 或 Doubao 配音、准确字幕、绘本式动态插画和 Remotion 渲染成片的 Codex 插件。

当前版本：`0.3.0`

## 它能做什么

- 把长文章压缩成适合短视频的口播文案。
- 每条视频先引导选择古风手绘、卡通手绘或其他自定义风格，并明确画面比例。
- 使用 MiniMax `speech-2.8-hd` 或 Doubao `seed-tts-2.0` 生成最终配音，并读取服务商原生字幕时间轴。
- 为每个叙事段落设计完整插画场景，而不是重复卡片模板。
- 通过 Image Prompt Generator 生成并审核插画 Prompt。
- 设计线稿、上色、人物或道具进入、局部动作和镜头运动。
- 使用 Remotion 渲染视频，并在交付前执行生产门禁和音画检查。

## 适合谁

- 想把文章、观点稿或口播稿转成绘本式动态视频的创作者。
- 需要配音、字幕、插画、动效和渲染串成一个流程的内容团队。
- 希望保留人工确认节点，不想让工作流直接跳到渲染的人。

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

首次使用时，插件会依次引导选择本条视频风格、默认音频模型和默认生图模型。音频配置可使用：

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

- 服务商原生字幕只提供时间，不改写字幕正文。
- MiniMax 或 Doubao 未返回有效原生字幕文件时立即停止，不估算时间。
- 图片必须经过 `$image-prompt-generator` 的 Prompt 审核与生图批准流程。
- 渲染前必须运行生产门禁，未通过时不得宣称视频已经完成。
