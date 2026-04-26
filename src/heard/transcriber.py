from dataclasses import dataclass, field
from pathlib import Path

import faster_whisper


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
    def __init__(self, model: str = "large-v3-turbo"):
        self.model = model

    def transcribe(self, audio_path: Path, video_name: str = "") -> Transcript:
        whisper = faster_whisper.WhisperModel(self.model, device="auto", compute_type="int8")

        segments_iter, info = whisper.transcribe(
            str(audio_path),
            language="zh",
            beam_size=5,
            vad_filter=True,
        )

        segments = []
        for seg in segments_iter:
            confidence = round(1.0 - abs(seg.avg_logprob), 2)
            segments.append(Segment(
                id=len(segments),
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
