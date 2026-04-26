# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                 # 安装依赖
uv run pytest -v        # 运行所有测试
uv run pytest tests/test_audio.py -v   # 运行单个测试文件
uv run heard --help     # 查看 CLI 帮助
uv run heard transcribe video.mp4      # 转录视频
```

## Architecture

Pipeline: CLI → Audio extraction → Transcription → JSON output

- `src/heard/cli.py` — Typer CLI 入口，`transcribe` 命令编排整个流程
- `src/heard/audio.py` — 用 ffmpeg-python 从视频提取 16kHz 单声道 WAV
- `src/heard/transcriber.py` — `Segment`/`Transcript` 数据类 + `WhisperTranscriber`（faster-whisper）
- `src/heard/output.py` — 将 Transcript 序列化为 JSON 写入文件

默认模型 `large-v3-turbo`，中文转录（`language="zh"`），VAD 过滤静音段。

## Prerequisites

系统需要安装 FFmpeg：`brew install ffmpeg`

## Project Conventions

- 包管理用 `uv`，构建用 `hatchling`
- 入口点：`heard = heard.cli:app`（pyproject.toml 中定义）
- 测试放在 `tests/`，文件命名 `test_<module>.py`
