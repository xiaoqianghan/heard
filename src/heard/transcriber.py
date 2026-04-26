from dataclasses import dataclass, field
from pathlib import Path

import faster_whisper

DEFAULT_MODEL = "large-v3-turbo"
DEFAULT_LANGUAGE = "zh"


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
    def __init__(self, model: str = DEFAULT_MODEL, language: str = DEFAULT_LANGUAGE):
        self.model = model
        self.language = language
        self._model: faster_whisper.WhisperModel | None = None

    @property
    def whisper(self) -> faster_whisper.WhisperModel:
        if self._model is None:
            self._model = faster_whisper.WhisperModel(self.model, device="auto", compute_type="int8")
        return self._model

    def transcribe(self, audio_path: Path, video_name: str = "") -> Transcript:
        segments_iter, info = self.whisper.transcribe(
            str(audio_path),
            language=self.language,
            beam_size=5,
            vad_filter=True,
        )

        segments = []
        for i, seg in enumerate(segments_iter):
            confidence = max(0.0, round(1.0 - abs(seg.avg_logprob), 2))
            segments.append(Segment(
                id=i,
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
