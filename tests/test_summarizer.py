import json

import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from heard.summarizer import (
    Summarizer,
    _call_claude_async,
    _chunk_text,
    _extract_text_from_transcript,
)
from heard.transcriber import Segment, Transcript


class TestExtractText:
    def test_converts_segments_to_text(self):
        t = Transcript(
            video="test.mp4",
            duration=10.0,
            language="zh",
            model="large-v3-turbo",
            segments=[
                Segment(id=0, start=0.0, end=5.0, text="第一段内容", confidence=0.9),
                Segment(id=1, start=5.5, end=10.0, text="第二段内容", confidence=0.85),
            ],
        )
        result = _extract_text_from_transcript(t)
        assert "第一段内容" in result
        assert "第二段内容" in result

    def test_empty_transcript(self):
        t = Transcript(video="test.mp4", duration=0.0, language="zh", model="large-v3-turbo")
        result = _extract_text_from_transcript(t)
        assert result == ""


class TestChunkText:
    def test_short_text_not_chunked(self):
        result = _chunk_text("短文本", max_size=50000)
        assert result == ["短文本"]

    def test_long_text_split_into_chunks(self):
        text = "段落内容\n\n" * 10000
        result = _chunk_text(text, max_size=50000)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 50000

    def test_empty_text(self):
        result = _chunk_text("", max_size=50000)
        assert result == []


class TestSummarizer:
    def _make_transcript(self):
        return Transcript(
            video="lesson01.mp4",
            duration=60.0,
            language="zh",
            model="large-v3-turbo",
            segments=[
                Segment(id=0, start=0.0, end=30.0, text="Python 是一种动态类型的编程语言", confidence=0.95),
                Segment(id=1, start=30.5, end=60.0, text="列表和字典是常用的数据结构", confidence=0.90),
            ],
        )

    def test_summarize_single_calls_claude_and_writes_file(self, tmp_path):
        from heard.output import write_transcript

        transcript = self._make_transcript()
        json_path = tmp_path / "lesson01.json"
        write_transcript(transcript, json_path)

        with patch("heard.summarizer._call_claude_async", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (
                "# lesson01.mp4\n\n## 概要\nPython基础\n\n## 核心概念\n- 类型\n\n## 关键词\nPython"
            )
            summarizer = Summarizer()
            output = summarizer.summarize_single(json_path, output_dir=tmp_path / "summaries")

        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "Python基础" in content

    def test_summarize_single_reads_json_directly(self, tmp_path):
        from heard.output import write_transcript

        transcript = self._make_transcript()
        json_path = tmp_path / "lesson01.json"
        write_transcript(transcript, json_path)

        with patch("heard.summarizer._call_claude_async", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "# mock summary"
            summarizer = Summarizer()
            output = summarizer.summarize_single(json_path, output_dir=tmp_path)

        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][1]  # user_prompt is the second positional arg
        assert "Python" in call_args or "动态类型" in call_args


class TestSummarizeBatch:
    def test_processes_all_json_files(self, tmp_path):
        from heard.output import write_transcript

        for i in range(3):
            t = Transcript(
                video=f"lesson{i:02d}.mp4",
                duration=60.0,
                language="zh",
                model="large-v3-turbo",
                segments=[Segment(id=0, start=0.0, end=60.0, text=f"第{i}课内容", confidence=0.9)],
            )
            write_transcript(t, tmp_path / f"lesson{i:02d}.json")

        with patch("heard.summarizer._call_claude_async", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "# mock summary"
            summarizer = Summarizer()
            paths = summarizer.summarize_batch(tmp_path, output_dir=tmp_path / "summaries")

        assert len(paths) == 4  # 3 summaries + 1 overview
        summary_files = [p for p in paths if p.name != "course-overview.md"]
        assert len(summary_files) == 3
        overview = [p for p in paths if p.name == "course-overview.md"]
        assert len(overview) == 1

    def test_raises_on_empty_directory(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        summarizer = Summarizer()
        with pytest.raises(ValueError, match="没有 JSON"):
            summarizer.summarize_batch(empty_dir)

    def test_raises_on_nonexistent_directory(self):
        summarizer = Summarizer()
        with pytest.raises(ValueError, match="目录不存在"):
            summarizer.summarize_batch(Path("/nonexistent/dir"))
