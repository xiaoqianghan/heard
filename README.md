# Heard

视频语音转录 CLI 工具。从本地视频文件中提取语音并转录为结构化 JSON 文本，方便后续 AI 总结和学习计划生成。

## 安装

需要先安装 FFmpeg：

```bash
brew install ffmpeg
```

克隆并安装项目：

```bash
git clone <repo-url> && cd heard
uv sync
```

## 使用

```bash
# 转录视频（默认输出到同目录 .json 文件）
heard transcribe video.mp4

# 指定输出路径
heard transcribe video.mp4 -o result.json

# 切换模型
heard transcribe video.mp4 --model medium
heard transcribe video.mp4 --model large-v3-turbo

# 导出为纯文本（用于 AI 总结、学习计划等）
heard export transcript.json

# 指定输出路径
heard export transcript.json -o output.txt
```

## 输出格式

### JSON（transcribe 默认输出）

```json
{
  "video": "lesson01.mp4",
  "duration": 3600.5,
  "language": "zh",
  "model": "large-v3-turbo",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 8.5,
      "text": "今天我们来学习 Python 的基础语法",
      "confidence": 0.95
    }
  ]
}
```

### 纯文本（export 输出）

```
# lesson01.mp4

时长: 60分0秒 | 语言: zh | 模型: large-v3-turbo

---

今天我们来学习 Python 的基础语法...

[按停顿自动分段，适合喂给 AI 做总结和学习计划]
```

## 开发

```bash
uv sync                      # 安装依赖（含开发依赖）
uv run pytest -v             # 运行测试
uv run heard transcribe --help  # 查看 CLI 帮助
```

## 支持的视频格式

mp4, mkv, avi, mov, wmv, flv, webm, m4v

## 技术栈

- Python + Typer (CLI)
- ffmpeg-python (音频提取)
- faster-whisper (语音转录，CTranslate2 后端)
- Rich (进度条)
