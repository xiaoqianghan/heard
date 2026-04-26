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

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    wav_path = Path(tmp.name)

    try:
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
    except ffmpeg.Error as e:
        wav_path.unlink(missing_ok=True)
        stderr = e.stderr.decode(errors="replace") if e.stderr else str(e)
        raise RuntimeError(f"ffmpeg failed: {stderr}") from e

    return wav_path
