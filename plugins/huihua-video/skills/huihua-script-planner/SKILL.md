---
name: huihua-script-planner
description: 将文章或主题整理为自然口播、叙事结构和可供绘画场景使用的语义节拍。
---

# 绘画视频口播规划

## 职责

读取原文，保留事实、人物、因果和情绪转折，输出适合配音的口播文案。不要在此阶段决定具体动画模板。

## 输出

生成 `narration.json`：

```json
{
  "title": "视频标题",
  "approved": false,
  "language": "zh-CN",
  "full_text": "完整口播",
  "sentences": [
    {
      "id": "sentence-001",
      "text": "完整句子",
      "function": "hook",
      "visual_hint": "这句话需要解释的画面意义"
    }
  ]
}
```

`sentences[].text` 必须来自 `full_text`，顺序一致，不得把一句话截断成残句。用户确认后把 `approved` 改为 `true`。

## 写作规则

- 口语化，但不制造口头禅和夸张事实。
- 每句话表达完整意思；字幕可按语义标点进一步显示，但正文不可被 ASR 替换。
- `visual_hint` 解释“画面要说明什么”，不复写整句口播。
- 明确钩子、铺垫、转折、证明、高潮和收束。
- 删除网页按钮、播放器文案、关注提示等污染内容。
