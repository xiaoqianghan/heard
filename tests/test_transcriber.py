from dataclasses import asdict
from pathlib import Path

import pytest

from heard.transcriber import Segment, Transcript, WhisperTranscriber, DEFAULT_MODEL, DEFAULT_LANGUAGE


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

        import faster_whisper
        monkeypatch.setattr(faster_whisper, "WhisperModel", lambda *a, **k: FakeModel())

        transcriber = WhisperTranscriber(model="large-v3-turbo")
        result = transcriber.transcribe(audio_path, video_name="test.mp4")

        assert isinstance(result, Transcript)
        assert result.video == "test.mp4"
        assert result.language == "zh"
        assert len(result.segments) == 2
        assert result.segments[0].text == "你好世界"
        assert result.segments[1].text == "测试转录"

    def test_default_model(self):
        transcriber = WhisperTranscriber()
        assert transcriber.model == DEFAULT_MODEL

    def test_default_language(self):
        transcriber = WhisperTranscriber()
        assert transcriber.language == DEFAULT_LANGUAGE

    def test_confidence_clamped_to_zero(self, tmp_path, monkeypatch):
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"\x00" * 100)

        class FakeSegment:
            def __init__(self, start, end, text, avg_logprob):
                self.start = start
                self.end = end
                self.text = text
                self.avg_logprob = avg_logprob
                self.no_speech_prob = 0.5

        class FakeInfo:
            language = "zh"
            language_probability = 0.98
            duration = 5.0
            duration_after_vad = 5.0

        class FakeModel:
            def transcribe(self, audio_path, **kwargs):
                return (
                    iter([FakeSegment(0.0, 5.0, "test", -2.5)]),
                    FakeInfo(),
                )

        import faster_whisper
        monkeypatch.setattr(faster_whisper, "WhisperModel", lambda *a, **k: FakeModel())

        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(audio_path, video_name="test.mp4")
        assert result.segments[0].confidence == 0.0
