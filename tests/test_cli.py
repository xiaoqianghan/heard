from unittest.mock import patch

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
