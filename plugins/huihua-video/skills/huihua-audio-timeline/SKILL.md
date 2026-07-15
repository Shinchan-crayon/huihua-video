---
name: huihua-audio-timeline
description: 生成或接收最终口播音频，并用 WhisperX 对齐已确认文案，输出可靠字幕时间轴和节奏点。
---

# 绘画视频音频时间轴

## 前置条件

`narration.json` 必须存在且 `approved: true`。音频可以由可用 TTS 生成，也可以由用户提供。

## 核心契约

- 最终音频是唯一计时依据。
- WhisperX 只输出识别区间、词级时间和停顿，不拥有字幕正文。
- 字幕正文必须按 `narration.sentences` 顺序回填。
- ASR 错词不得进入成片字幕。
- 更换音频后旧 `subtitle-timeline.json` 立即失效。

## 输出

`subtitle-timeline.json` 至少包含音频路径、音频 SHA-256、总时长、`timing_source: whisperx`、`text_source: approved_narration`、字幕条目和节奏点。

每个字幕条目包含 `id`、`sentence_id`、`start`、`end` 和 `text`。

## 对齐质量

- 每个字幕必须 `start < end`，按时间递增且不出现冲突重叠。
- 句子过长时可按语义标点分为连续显示段，但所有文字拼接后必须等于原句。
- 字幕可跨场景持续显示，不能被场景 `Sequence` 强制截断。
- 参照 `../../references/制作规范/音频字幕契约.md`。
