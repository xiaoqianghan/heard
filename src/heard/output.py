import json
from dataclasses import asdict
from pathlib import Path

from heard.transcriber import Transcript


def write_transcript(transcript: Transcript, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asdict(transcript), f, ensure_ascii=False, indent=2)
