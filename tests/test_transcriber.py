from dataclasses import asdict

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
            model="mlx-community/whisper-large-v3-turbo",
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
            model="mlx-community/whisper-large-v3-turbo",
            segments=[seg],
        )
        d = asdict(t)
        assert d["video"] == "test.mp4"
        assert d["segments"][0]["text"] == "你好"


class TestWhisperTranscriber:
    def test_transcribe_returns_transcript(self, tmp_path, monkeypatch):
        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"\x00" * 100)

        fake_result = {
            "text": "你好世界测试转录",
            "segments": [
                {"start": 0.0, "end": 4.2, "text": "你好世界", "avg_logprob": -0.2},
                {"start": 4.2, "end": 8.5, "text": "测试转录", "avg_logprob": -0.3},
            ],
            "language": "zh",
            "duration": 8.5,
        }

        import mlx_whisper
        monkeypatch.setattr(mlx_whisper, "transcribe", lambda *a, **k: fake_result)

        transcriber = WhisperTranscriber()
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

        fake_result = {
            "text": "test",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "test", "avg_logprob": -2.5},
            ],
            "language": "zh",
            "duration": 5.0,
        }

        import mlx_whisper
        monkeypatch.setattr(mlx_whisper, "transcribe", lambda *a, **k: fake_result)

        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(audio_path, video_name="test.mp4")
        assert result.segments[0].confidence == 0.0
