import json
from dataclasses import asdict
from pathlib import Path

from heard.transcriber import Segment, Transcript


def write_transcript(transcript: Transcript, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asdict(transcript), f, ensure_ascii=False, indent=2)


def format_transcript_text(transcript: Transcript) -> str:
    minutes, seconds = divmod(int(transcript.duration), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        duration_str = f"{hours}h {minutes}m {seconds}s"
    else:
        duration_str = f"{minutes}m {seconds}s"

    lines = [
        f"# {transcript.video}",
        "",
        f"Duration: {duration_str} | Language: {transcript.language} | Model: {transcript.model}",
        "",
        "---",
        "",
    ]

    paragraphs = _group_segments(transcript.segments)
    for para in paragraphs:
        lines.append(para)
        lines.append("")

    return "\n".join(lines)


def _group_segments(segments: list[Segment], gap_threshold: float = 2.0) -> list[str]:
    if not segments:
        return []

    paragraphs: list[list[str]] = []
    current_para: list[str] = [segments[0].text]
    last_end = segments[0].end

    for seg in segments[1:]:
        if seg.start - last_end >= gap_threshold:
            paragraphs.append(current_para)
            current_para = []
        current_para.append(seg.text)
        last_end = seg.end

    if current_para:
        paragraphs.append(current_para)

    return ["".join(texts) for texts in paragraphs]


def load_transcript(json_path: Path) -> Transcript:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    segments = [Segment(**s) for s in data.get("segments", [])]
    return Transcript(
        video=data.get("video", ""),
        duration=data.get("duration", 0.0),
        language=data.get("language", ""),
        model=data.get("model", ""),
        segments=segments,
    )
