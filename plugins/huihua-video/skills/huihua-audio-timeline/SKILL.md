---
name: huihua-audio-timeline
description: 使用 MiniMax 为已确认口播生成最终音频、原生字幕时间戳、可靠字幕时间轴和节奏点。
---

# 绘画视频音频时间轴

## 前置条件

`narration.json` 必须存在且 `approved: true`。当前只支持 MiniMax TTS，不接收其他音频提供商，也不估算缺失时间。

首次使用时：

1. 运行 `python3 ../../scripts/doctor.py`。
2. 未配置 MiniMax 时运行 `python3 ../../scripts/configure_minimax.py`，通过隐藏输入提供 API Key。
3. 打开 https://www.minimaxi.com/audio/voices 试听音色。
4. 复制完整 `voice_id` 并按配置脚本提示粘贴。

## 执行

运行：

```bash
python3 ../../scripts/minimax_tts_timeline.py \
  --narration /absolute/path/narration.json \
  --project-dir /absolute/path/video-project
```

脚本固定启用 MiniMax 原生单词字幕，并将返回的原生字幕时间映射回已确认口播。

## 核心契约

- MiniMax 生成的最终音频是唯一计时依据。
- 字幕正文只来自 `narration.sentences`。
- MiniMax 原生字幕只提供时间，不拥有字幕正文。
- MiniMax 未返回有效字幕文件时立即停止，不伪造时间轴。
- 更换口播、音频、模型或 `voice_id` 后，旧 `subtitle-timeline.json` 立即失效。

## 输出

项目目录内必须生成：

- `narration.mp3` 或 `narration.wav`
- `minimax-subtitles.json`
- `subtitle-timeline.json`

时间轴必须包含 `timing_source: minimax_tts`、`text_source: approved_narration`、音频 SHA-256、MiniMax 模型、`voice_id`、原生字幕文件校验信息、字幕条目和节奏点。

字幕可以跨场景持续显示，不能被场景 `Sequence` 截断。完整规则见 `../../references/制作规范/音频字幕契约.md`。
