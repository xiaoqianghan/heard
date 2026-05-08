from dataclasses import dataclass, field
from pathlib import Path

import mlx_whisper

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"
DEFAULT_LANGUAGE = None


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
    def __init__(self, model: str = DEFAULT_MODEL, language: str | None = DEFAULT_LANGUAGE):
        self.model = model
        self.language = language

    def transcribe(self, audio_path: Path, video_name: str = "") -> Transcript:
        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=self.model,
            language=self.language,
        )

        segments = []
        for i, seg in enumerate(result["segments"]):
            avg_logprob = seg.get("avg_logprob", 0.0)
            confidence = max(0.0, round(1.0 - abs(avg_logprob), 2))
            segments.append(Segment(
                id=i,
                start=round(seg["start"], 2),
                end=round(seg["end"], 2),
                text=seg["text"].strip(),
                confidence=confidence,
            ))

        return Transcript(
            video=video_name,
            duration=round(result.get("duration", segments[-1].end if segments else 0.0), 2),
            language=result.get("language", self.language),
            model=self.model,
            segments=segments,
        )
