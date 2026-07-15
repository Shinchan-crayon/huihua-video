# Remotion 绘画视频模板

这是 `huihua-video` 的清单驱动渲染模板。把项目音频和图片放入 `public/`，并准备输入属性 JSON：

```json
{
  "audio": "runtime/narration.mp3",
  "duration": 10,
  "fps": 30,
  "scenes": [],
  "images": [],
  "motion": [],
  "subtitles": []
}
```

图片路径相对于 `public/`。首张 `role: color` 图片的实际宽高用于确定输出画布，所有图片使用 `contain` 完整显示。

```bash
npm install
npm run render -- --props ./props.json --output ./output.mp4
```
