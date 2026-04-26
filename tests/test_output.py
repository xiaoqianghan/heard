import json

from heard.output import write_transcript
from heard.transcriber import Segment, Transcript


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
        with open(output_path, encoding="utf-8") as f:
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
