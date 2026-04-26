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

        import subprocess
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: None)

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
