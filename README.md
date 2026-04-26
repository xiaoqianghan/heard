# Heard

A CLI tool for transcribing speech from video files into structured JSON text, designed for subsequent AI summarization and study plan generation.

[中文文档](#中文说明)

---

## Installation

Requires [FFmpeg](https://ffmpeg.org/) to be installed:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

Clone and set up:

```bash
git clone https://github.com/xiaoqianghan/heard.git && cd heard
uv sync
```

## Usage

```bash
# Transcribe a video (outputs JSON in the same directory by default)
heard transcribe video.mp4

# Specify output path
heard transcribe video.mp4 -o result.json

# Choose a model
heard transcribe video.mp4 --model medium
heard transcribe video.mp4 --model large-v3-turbo

# Export as plain text (for AI summarization, study plans, etc.)
heard export transcript.json

# Specify output path
heard export transcript.json -o output.txt
```

## Output Formats

### JSON (default from `transcribe`)

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

### Plain Text (from `export`)

```
# lesson01.mp4

Duration: 60m0s | Language: zh | Model: large-v3-turbo

---

今天我们来学习 Python 的基础语法...

[Auto-segmented by pauses, ready for AI summarization and study plans]
```

## Development

```bash
uv sync                          # Install dependencies (including dev)
uv run pytest -v                 # Run tests
uv run heard transcribe --help   # CLI help
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Supported Video Formats

mp4, mkv, avi, mov, wmv, flv, webm, m4v

## Tech Stack

- Python + Typer (CLI)
- ffmpeg-python (audio extraction)
- faster-whisper (speech transcription, CTranslate2 backend)
- Rich (progress bars)

## License

[MIT](LICENSE)

---

<a id="中文说明"></a>

## 中文说明

视频语音转录 CLI 工具。从本地视频文件中提取语音并转录为结构化 JSON 文本，方便后续 AI 总结和学习计划生成。

### 安装

```bash
brew install ffmpeg
git clone https://github.com/xiaoqianghan/heard.git && cd heard
uv sync
```

### 使用

```bash
heard transcribe video.mp4              # 转录视频
heard transcribe video.mp4 -o result.json  # 指定输出路径
heard transcribe video.mp4 --model medium  # 切换模型
heard export transcript.json             # 导出为纯文本
```

### 技术栈

- Python + Typer (CLI)
- ffmpeg-python (音频提取)
- faster-whisper (语音转录，CTranslate2 后端)
- Rich (进度条)
