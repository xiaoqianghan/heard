# Heard — 视频语音转录工具设计文档

## 概述

Heard 是一个 Python CLI 工具，从本地视频文件中提取语音并转录为结构化 JSON 文本，方便后续 AI 总结和学习计划生成。

## 技术选型

| 项目 | 选择 | 理由 |
|------|------|------|
| 语言 | Python | ASR/AI 生态最成熟 |
| CLI 框架 | Typer | 类型安全，自动生成帮助文档 |
| 音频提取 | ffmpeg-python | FFmpeg 的成熟 Python 绑定 |
| 本地转录 | faster-whisper | CTranslate2 后端，Apple Silicon 加速 |
| 默认模型 | large-v3-turbo | 接近 large-v3 精度，速度显著更快 |
| 进度显示 | Rich | 进度条和格式化输出 |
| 包管理 | uv | 快速的现代 Python 包管理器 |

## 架构

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────┐
│  CLI 入口    │───▶│  音频提取     │───▶│  语音转录引擎    │───▶│ JSON 输出 │
│  (Typer)     │    │  (FFmpeg)    │    │  (可插拔)        │    │          │
└─────────────┘    └──────────────┘    ├─────────────────┤    └──────────┘
                                       │ Whisper 本地    │
                                       │ (faster-whisper)│
                                       ├─────────────────┤
                                       │ 云端 API        │
                                       │ (预留接口)      │
                                       └─────────────────┘
```

### 模块划分

| 模块 | 文件 | 职责 |
|------|------|------|
| CLI 入口 | `src/heard/cli.py` | 命令定义、参数解析 |
| 音频提取 | `src/heard/audio.py` | FFmpeg 调用，提取 WAV 音频 |
| 转录引擎 | `src/heard/transcriber.py` | Transcriber 抽象接口 + WhisperTranscriber 实现 |
| 输出格式化 | `src/heard/output.py` | 转录结果序列化为 JSON |

### Transcriber 抽象接口

```python
class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> Transcript: ...
```

`WhisperTranscriber` 实现：使用 faster-whisper，参数 `language="zh"`, `beam_size=5`, `vad_filter=True`。
`CloudTranscriber`（预留）：未来接入云端 API。

## CLI 接口

```bash
# 默认用法
heard transcribe video.mp4

# 指定输出路径
heard transcribe video.mp4 -o result.json

# 切换模型
heard transcribe video.mp4 --model medium
heard transcribe video.mp4 --model large-v3-turbo

# 切换引擎（未来）
heard transcribe video.mp4 --engine cloud --api-key xxx

# 显示进度
heard transcribe video.mp4 --verbose
```

## JSON 输出格式

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

## 音频处理流程

1. 校验视频文件存在性和格式
2. FFmpeg 提取音频为 16kHz 单声道 WAV
3. 临时音频文件存放在系统临时目录
4. 转录完成后自动清理临时文件

## 转录参数

- `language`: `"zh"`
- `beam_size`: 5
- `vad_filter`: True（语音活动检测，过滤静音段）
- 模型首次使用时自动下载并缓存到本地
- 长视频自动分段处理，Rich 显示实时进度条

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| FFmpeg 未安装 | 报错并提示 `brew install ffmpeg` |
| 视频文件不存在 | 明确报错 |
| 视频格式不支持 | 明确报错 |
| GPU/Metal 不可用 | 自动回退 CPU 并提示 |

## 不做的事

- 批量目录处理（未来可扩展）
- 实时流式转录
- 字幕文件格式（SRT/VTT）
- GUI 界面

## 硬件环境

目标机器：Mac Mini M4, 16GB 统一内存。large-v3-turbo 模型在此硬件上运行良好，内存充足，Metal 加速可用。

## 项目结构

```
heard/
├── pyproject.toml
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-26-video-transcription-design.md
├── src/
│   └── heard/
│       ├── __init__.py
│       ├── cli.py
│       ├── audio.py
│       ├── transcriber.py
│       └── output.py
└── tests/
```
