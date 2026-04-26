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
