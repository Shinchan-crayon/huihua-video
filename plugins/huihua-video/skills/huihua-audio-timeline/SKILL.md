---
name: huihua-audio-timeline
description: 使用已配置的 MiniMax 或 Doubao 为已确认口播生成最终音频、原生字幕时间戳、可靠字幕时间轴和节奏点。
---

# 绘画视频音频时间轴

## 产品边界

仅处理 `workflow-state.json.product_id == "huihua-video"` 的当前项目。`narration.json` 必须位于同一项目目录内；不得读取或写入 Shin-video 仓库、`.shin-video-runtime` 或其配置与产物。

## 前置条件

`narration.json` 必须存在且 `approved: true`。支持 MiniMax `speech-2.8-hd` 与 Doubao `seed-tts-2.0`，两者都必须返回可映射回已确认口播的服务商原生时间戳；不得估算缺失时间。

首次使用时：

1. 运行 `python3 ../../scripts/doctor.py`。
2. 选择 MiniMax 时运行 `python3 ../../scripts/configure_minimax.py`，通过隐藏输入提供 API Key；在 https://www.minimaxi.com/audio/voices 试听后保存默认 `voice_id`。
3. 选择 Doubao 时运行 `python3 ../../scripts/configure_volcengine.py`，通过隐藏输入提供 API Key；在 https://console.volcengine.com/ark/region:cn-beijing/experience/voice?model=doubao-seed-tts-2-0 试听后保存默认 `voice_id`。

## 执行

运行：

MiniMax：

```bash
python3 ../../scripts/minimax_tts_timeline.py \
  --narration /absolute/path/narration.json \
  --project-dir /absolute/path/video-project \
  --leading-silence-seconds 1.5
```

Doubao：

```bash
python3 ../../scripts/volcengine_tts_timeline.py \
  --narration /absolute/path/narration.json \
  --project-dir /absolute/path/video-project \
  --leading-silence-seconds 1.5
```

两个脚本都固定请求服务商原生词级字幕，并将返回的时间映射回已确认口播。

## 核心契约

- 已选择服务商生成的最终音频是唯一计时依据。
- 字幕正文只来自 `narration.sentences`。
- 服务商原生字幕只提供时间，不拥有字幕正文。
- 服务商未返回有效字幕时间戳时立即停止，不伪造时间轴。
- 更换口播、音频、模型或 `voice_id` 后，旧 `subtitle-timeline.json` 立即失效。
- 用户要求开场停顿时，只能用 `--leading-silence-seconds`；它会同时修改最终音频、字幕和节奏点，不能只延后画面。

## 输出

项目目录内必须生成：

- `narration.mp3` 或 `narration.wav`
- `minimax-subtitles.json` 或 `volcengine-subtitles.json`
- `subtitle-timeline.json`

时间轴必须包含 `timing_source`、`text_source: approved_narration`、音频 SHA-256、服务商模型、`voice_id`、原生字幕文件校验信息、字幕条目和节奏点。

字幕可以跨场景持续显示，不能被场景 `Sequence` 截断。完整规则见 `../../references/制作规范/音频字幕契约.md`。
