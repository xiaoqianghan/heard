# Heard — 视频语音转录工具实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Python CLI 工具，从本地视频文件中提取语音并转录为结构化 JSON 文本。

**Architecture:** CLI 入口 → FFmpeg 提取音频 → faster-whisper 转录 → JSON 输出。Transcriber 为可插拔抽象接口，默认实现 Whisper 本地引擎。

**Tech Stack:** Python, Typer, ffmpeg-python, faster-whisper, Rich, uv

---

## File Structure

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | 项目元数据、依赖、入口点定义 |
| `src/heard/__init__.py` | 包初始化，版本号 |
| `src/heard/cli.py` | CLI 命令定义、参数解析 |
| `src/heard/audio.py` | FFmpeg 音频提取 |
| `src/heard/transcriber.py` | Transcriber 抽象接口 + WhisperTranscriber 实现 |
| `src/heard/output.py` | 转录结果序列化为 JSON |
| `tests/test_audio.py` | 音频提取模块测试 |
| `tests/test_transcriber.py` | 转录引擎测试 |
| `tests/test_output.py` | 输出格式化测试 |
| `tests/test_cli.py` | CLI 集成测试 |

---

### Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `src/heard/__init__.py`

- [ ] **Step 1: 初始化项目并创建 pyproject.toml**

```toml
[project]
name = "heard"
version = "0.1.0"
description = "Video speech-to-text transcription CLI tool"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.15.0",
    "ffmpeg-python>=0.2.0",
    "faster-whisper>=1.1.0",
    "rich>=13.0.0",
]

[project.scripts]
heard = "heard.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/heard"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 创建包初始化文件**

`src/heard/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: 创建 tests 目录和空 __init__.py**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 4: 安装依赖并验证**

Run: `uv sync --dev pytest`
Expected: 依赖安装成功，无报错

- [ ] **Step 5: 验证入口点**

Run: `uv run heard --help`
Expected: 显示 typer 帮助信息（或报错无 app，因为 cli.py 尚未创建，这是预期的）

- [ ] **Step 6: 提交**

```bash
git add pyproject.toml src/ tests/
git commit -m "chore: initialize project with pyproject.toml and package structure"
```

---

### Task 2: 音频提取模块

**Files:**
- Create: `src/heard/audio.py`
- Create: `tests/test_audio.py`

- [ ] **Step 1: 编写音频提取的失败测试**

`tests/test_audio.py`:

```python
import tempfile
from pathlib import Path

import pytest

from heard.audio import extract_audio, check_ffmpeg


class TestCheckFfmpeg:
    def test_check_ffmpeg_raises_when_not_installed(self, monkeypatch):
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("ffmpeg not found")

        import subprocess
        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(RuntimeError, match="ffmpeg is not installed"):
            check_ffmpeg()

    def test_check_ffmpeg_passes_when_installed(self, monkeypatch):
        import subprocess
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)

        check_ffmpeg()


class TestExtractAudio:
    def test_raises_when_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            extract_audio(Path("/nonexistent/video.mp4"))

    def test_raises_when_not_video_extension(self, tmp_path):
        text_file = tmp_path / "notes.txt"
        text_file.write_text("hello")

        with pytest.raises(ValueError, match="Unsupported video format"):
            extract_audio(text_file)

    def test_returns_wav_path(self, tmp_path, monkeypatch):
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"\x00" * 100)

        def mock_ffmpeg_input(filename):
            class MockOutput:
                def output(self, out_path, **kwargs):
                    class MockRun:
                        def overwrite_output(self):
                            return self
                        def run(self, capture_stderr=True):
                            # Simulate creating the wav file
                            Path(out_path).write_bytes(b"RIFF" + b"\x00" * 100)
                            return (None, None)
                    return MockRun()
            return MockOutput()

        import ffmpeg
        monkeypatch.setattr(ffmpeg, "input", mock_ffmpeg_input)

        result = extract_audio(video_file)
        assert result.suffix == ".wav"
        assert result.exists()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_audio.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'heard.audio'`

- [ ] **Step 3: 实现音频提取模块**

`src/heard/audio.py`:

```python
import subprocess
import tempfile
from pathlib import Path

import ffmpeg

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}


def check_ffmpeg() -> None:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg is not installed. Install it with: brew install ffmpeg"
        )


def extract_audio(video_path: Path) -> Path:
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if video_path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValueError(
            f"Unsupported video format: {video_path.suffix}. "
            f"Supported: {', '.join(sorted(VIDEO_EXTENSIONS))}"
        )

    check_ffmpeg()

    wav_path = Path(tempfile.mktemp(suffix=".wav"))

    (
        ffmpeg.input(str(video_path))
        .output(
            str(wav_path),
            acodec="pcm_s16le",
            ac=1,
            ar="16k",
        )
        .overwrite_output()
        .run(capture_stderr=True)
    )

    return wav_path
```

- [ ] **Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_audio.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add src/heard/audio.py tests/test_audio.py
git commit -m "feat: add audio extraction module with FFmpeg"
```

---

### Task 3: 转录引擎模块

**Files:**
- Create: `src/heard/transcriber.py`
- Create: `tests/test_transcriber.py`

- [ ] **Step 1: 编写转录引擎的失败测试**

`tests/test_transcriber.py`:

```python
from dataclasses import asdict
from pathlib import Path

import pytest

from heard.transcriber import Segment, Transcript, WhisperTranscriber


class TestSegment:
    def test_segment_creation(self):
        seg = Segment(id=0, start=0.0, end=8.5, text="你好世界", confidence=0.95)
        assert seg.id == 0
        assert seg.start == 0.0
        assert seg.end == 8.5
        assert seg.text == "你好世界"
        assert seg.confidence == 0.95

    def test_segment_to_dict(self):
        seg = Segment(id=0, start=0.0, end=8.5, text="你好", confidence=0.9)
        d = asdict(seg)
        assert d == {"id": 0, "start": 0.0, "end": 8.5, "text": "你好", "confidence": 0.9}


class TestTranscript:
    def test_transcript_creation(self):
        seg = Segment(id=0, start=0.0, end=8.5, text="你好", confidence=0.9)
        t = Transcript(
            video="test.mp4",
            duration=8.5,
            language="zh",
            model="large-v3-turbo",
            segments=[seg],
        )
        assert t.video == "test.mp4"
        assert t.duration == 8.5
        assert len(t.segments) == 1

    def test_transcript_to_dict(self):
        seg = Segment(id=0, start=0.0, end=8.5, text="你好", confidence=0.9)
        t = Transcript(
            video="test.mp4",
            duration=8.5,
            language="zh",
            model="large-v3-turbo",
            segments=[seg],
        )
        d = asdict(t)
        assert d["video"] == "test.mp4"
        assert d["segments"][0]["text"] == "你好"


class TestWhisperTranscriber:
    def test_transcribe_returns_transcript(self, tmp_path, monkeypatch):
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"\x00" * 100)

        class FakeSegment:
            def __init__(self, start, end, text, avg_logprob):
                self.start = start
                self.end = end
                self.text = text
                self.avg_logprob = avg_logprob
                self.no_speech_prob = 0.01

        class FakeInfo:
            language = "zh"
            language_probability = 0.98
            duration = 8.5
            duration_after_vad = 8.0

        class FakeModel:
            def transcribe(self, audio_path, **kwargs):
                return (
                    iter([
                        FakeSegment(0.0, 4.2, "你好世界", -0.2),
                        FakeSegment(4.2, 8.5, "测试转录", -0.3),
                    ]),
                    FakeInfo(),
                )

        def mock_whisper_model(model_size, **kwargs):
            return FakeModel()

        import faster_whisper
        monkeypatch.setattr(faster_whisper.WhisperModel, "__init__", lambda self, *a, **k: None)
        monkeypatch.setattr(faster_whisper, "WhisperModel", lambda *a, **k: FakeModel())

        transcriber = WhisperTranscriber(model="large-v3-turbo")
        result = transcriber.transcribe(audio_path, video_name="test.mp4")

        assert isinstance(result, Transcript)
        assert result.video == "test.mp4"
        assert result.language == "zh"
        assert len(result.segments) == 2
        assert result.segments[0].text == "你好世界"
        assert result.segments[1].text == "测试转录"

    def test_default_model_is_large_v3_turbo(self):
        transcriber = WhisperTranscriber()
        assert transcriber.model == "large-v3-turbo"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_transcriber.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'heard.transcriber'`

- [ ] **Step 3: 实现转录引擎模块**

`src/heard/transcriber.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path

from faster_whisper import WhisperModel


@dataclass
class Segment:
    id: int
    start: float
    end: float
    text: str
    confidence: float


@dataclass
class Transcript:
    video: str
    duration: float
    language: str
    model: str
    segments: list[Segment] = field(default_factory=list)


class WhisperTranscriber:
    def __init__(self, model: str = "large-v3-turbo"):
        self.model = model

    def transcribe(self, audio_path: Path, video_name: str = "") -> Transcript:
        whisper = WhisperModel(self.model, device="auto", compute_type="int8")

        segments_iter, info = whisper.transcribe(
            str(audio_path),
            language="zh",
            beam_size=5,
            vad_filter=True,
        )

        segments = []
        for seg in segments_iter:
            confidence = round(1.0 - abs(seg.avg_logprob), 2)
            segments.append(Segment(
                id=len(segments),
                start=round(seg.start, 2),
                end=round(seg.end, 2),
                text=seg.text.strip(),
                confidence=confidence,
            ))

        return Transcript(
            video=video_name,
            duration=round(info.duration, 2),
            language=info.language,
            model=self.model,
            segments=segments,
        )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_transcriber.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add src/heard/transcriber.py tests/test_transcriber.py
git commit -m "feat: add transcriber module with WhisperTranscriber"
```

---

### Task 4: JSON 输出模块

**Files:**
- Create: `src/heard/output.py`
- Create: `tests/test_output.py`

- [ ] **Step 1: 编写输出格式化的失败测试**

`tests/test_output.py`:

```python
import json
from dataclasses import asdict
from pathlib import Path

from heard.output import write_transcript, format_transcript
from heard.transcriber import Segment, Transcript


class TestFormatTranscript:
    def test_formats_to_json_dict(self):
        seg = Segment(id=0, start=0.0, end=8.5, text="你好世界", confidence=0.95)
        t = Transcript(
            video="test.mp4",
            duration=8.5,
            language="zh",
            model="large-v3-turbo",
            segments=[seg],
        )
        result = format_transcript(t)

        assert result["video"] == "test.mp4"
        assert result["duration"] == 8.5
        assert result["language"] == "zh"
        assert result["model"] == "large-v3-turbo"
        assert len(result["segments"]) == 1
        assert result["segments"][0]["text"] == "你好世界"
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 8.5

    def test_empty_segments(self):
        t = Transcript(
            video="empty.mp4",
            duration=0.0,
            language="zh",
            model="large-v3-turbo",
            segments=[],
        )
        result = format_transcript(t)
        assert result["segments"] == []


class TestWriteTranscript:
    def test_writes_json_file(self, tmp_path):
        seg = Segment(id=0, start=0.0, end=8.5, text="你好", confidence=0.9)
        t = Transcript(
            video="test.mp4",
            duration=8.5,
            language="zh",
            model="large-v3-turbo",
            segments=[seg],
        )
        output_path = tmp_path / "result.json"
        write_transcript(t, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["video"] == "test.mp4"
        assert data["segments"][0]["text"] == "你好"

    def test_creates_parent_directories(self, tmp_path):
        t = Transcript(
            video="test.mp4",
            duration=0.0,
            language="zh",
            model="large-v3-turbo",
        )
        output_path = tmp_path / "sub" / "dir" / "result.json"
        write_transcript(t, output_path)
        assert output_path.exists()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_output.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'heard.output'`

- [ ] **Step 3: 实现输出模块**

`src/heard/output.py`:

```python
import json
from dataclasses import asdict
from pathlib import Path

from heard.transcriber import Transcript


def format_transcript(transcript: Transcript) -> dict:
    return asdict(transcript)


def write_transcript(transcript: Transcript, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(format_transcript(transcript), f, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `uv run pytest tests/test_output.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add src/heard/output.py tests/test_output.py
git commit -m "feat: add JSON output module"
```

---

### Task 5: CLI 集成

**Files:**
- Create: `src/heard/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: 编写 CLI 测试**

`tests/test_cli.py`:

```python
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from heard.cli import app


runner = CliRunner()


class TestTranscribeCommand:
    def test_shows_error_when_file_not_found(self):
        result = runner.invoke(app, ["transcribe", "/nonexistent/video.mp4"])
        assert result.exit_code != 0

    def test_shows_error_for_unsupported_format(self, tmp_path):
        text_file = tmp_path / "notes.txt"
        text_file.write_text("hello")

        result = runner.invoke(app, ["transcribe", str(text_file)])
        assert result.exit_code != 0
        assert "Unsupported" in result.output or "unsupported" in result.output.lower()

    def test_help_shows_options(self):
        result = runner.invoke(app, ["transcribe", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--output" in result.output

    def test_help_command(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "transcribe" in result.output.lower()


class TestSuccessfulTranscription:
    def test_full_pipeline(self, tmp_path):
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"\x00" * 100)
        output_file = tmp_path / "result.json"

        with patch("heard.cli.extract_audio") as mock_extract, \
             patch("heard.cli.WhisperTranscriber") as mock_transcriber_class:
            from heard.transcriber import Segment, Transcript

            wav_path = tmp_path / "audio.wav"
            wav_path.write_bytes(b"RIFF" + b"\x00" * 100)
            mock_extract.return_value = wav_path

            mock_transcriber = mock_transcriber_class.return_value
            mock_transcriber.transcribe.return_value = Transcript(
                video="video.mp4",
                duration=8.5,
                language="zh",
                model="large-v3-turbo",
                segments=[Segment(id=0, start=0.0, end=8.5, text="你好世界", confidence=0.95)],
            )

            result = runner.invoke(app, [
                "transcribe",
                str(video_file),
                "-o", str(output_file),
                "--model", "large-v3-turbo",
            ])

            assert result.exit_code == 0
            assert output_file.exists()

            import json
            data = json.loads(output_file.read_text())
            assert data["video"] == "video.mp4"
            assert data["segments"][0]["text"] == "你好世界"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'heard.cli'`

- [ ] **Step 3: 实现 CLI 模块**

`src/heard/cli.py`:

```python
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from heard.audio import extract_audio
from heard.output import write_transcript
from heard.transcriber import WhisperTranscriber

app = typer.Typer(help="Heard — 视频语音转录工具")
console = Console()


@app.command()
def transcribe(
    video: Annotated[Path, typer.Argument(help="视频文件路径", exists=True)],
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="输出 JSON 文件路径")] = None,
    model: Annotated[str, typer.Option("--model", "-m", help="Whisper 模型名称")] = "large-v3-turbo",
) -> None:
    video = video.resolve()

    if output is None:
        output = video.with_suffix(".json")
    output = output.resolve()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("提取音频...", total=None)
        audio_path = extract_audio(video)
        progress.update(task, description="转录中...")

        try:
            transcriber = WhisperTranscriber(model=model)
            transcript = transcriber.transcribe(audio_path, video_name=video.name)
        finally:
            audio_path.unlink(missing_ok=True)

        progress.update(task, description="写入输出...")
        write_transcript(transcript, output)
        progress.update(task, description=f"完成! 输出: {output}")

    console.print(f"\n[green]转录完成[/green] — {len(transcript.segments)} 个片段 → {output}")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: 运行所有测试确认通过**

Run: `uv run pytest -v`
Expected: 全部 PASS

- [ ] **Step 5: 验证 CLI 入口点**

Run: `uv run heard --help`
Expected: 显示帮助信息，包含 `transcribe` 子命令

Run: `uv run heard transcribe --help`
Expected: 显示 `--model`、`--output` 等选项

- [ ] **Step 6: 提交**

```bash
git add src/heard/cli.py tests/test_cli.py
git commit -m "feat: add CLI with transcribe command"
```

---

### Task 6: 端到端集成验证

**Files:**
- 无新文件

- [ ] **Step 1: 确认所有测试通过**

Run: `uv run pytest -v`
Expected: 全部 PASS，无 warning

- [ ] **Step 2: 确认 CLI 完整帮助输出**

Run: `uv run heard transcribe --help`
Expected: 输出包含 `VIDEO` 参数、`--output`、`--model` 选项

- [ ] **Step 3: 用不存在的文件触发错误处理**

Run: `uv run heard transcribe /nonexistent.mp4`
Expected: 报错提示文件不存在

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "chore: verify end-to-end integration"
```
