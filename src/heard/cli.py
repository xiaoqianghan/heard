from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from heard.audio import extract_audio
from heard.output import write_transcript, format_transcript_text, load_transcript
from heard.transcriber import DEFAULT_MODEL, DEFAULT_LANGUAGE, WhisperTranscriber

app = typer.Typer(help="Heard — 视频语音转录工具")
console = Console()


@app.callback()
def main() -> None:
    pass


@app.command()
def transcribe(
    video: Annotated[Path, typer.Argument(help="视频文件路径")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="输出 JSON 文件路径")] = None,
    model: Annotated[str, typer.Option("--model", "-m", help="Whisper 模型名称")] = DEFAULT_MODEL,
    language: Annotated[str, typer.Option("--language", "-l", help="转录语言")] = DEFAULT_LANGUAGE,
) -> None:
    video = video.resolve()

    if output is None:
        output = video.with_suffix(".json")
    output = output.resolve()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("提取音频...", total=None)
            audio_path = extract_audio(video)
            progress.update(task, description="转录中...")

            try:
                transcriber = WhisperTranscriber(model=model, language=language)
                transcript = transcriber.transcribe(audio_path, video_name=video.name)
            finally:
                audio_path.unlink(missing_ok=True)

            progress.update(task, description="写入输出...")
            write_transcript(transcript, output)
            progress.update(task, description=f"完成! 输出: {output}")

        console.print(f"\n[green]转录完成[/green] — {len(transcript.segments)} 个片段 → {output}")

    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        console.print(f"[red]错误[/red]: {exc}")
        raise typer.Exit(code=1)


@app.command()
def export(
    json_file: Annotated[Path, typer.Argument(help="转录 JSON 文件路径")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="输出文件路径")] = None,
) -> None:
    json_file = json_file.resolve()

    if not json_file.exists():
        console.print(f"[red]错误[/red]: 文件不存在 — {json_file}")
        raise typer.Exit(code=1)

    transcript = load_transcript(json_file)

    if output is None:
        output = json_file.with_suffix(".txt")
    output = output.resolve()

    text = format_transcript_text(transcript)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

    console.print(f"[green]导出完成[/green] — {len(transcript.segments)} 个片段 → {output}")


if __name__ == "__main__":
    app()
