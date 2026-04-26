from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from heard.audio import extract_audio
from heard.output import write_transcript
from heard.transcriber import WhisperTranscriber

app = typer.Typer(help="Heard — 视频语音转录工具")
console = Console()


@app.callback()
def main() -> None:
    pass


@app.command()
def transcribe(
    video: Annotated[Path, typer.Argument(help="视频文件路径")],
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="输出 JSON 文件路径")] = None,
    model: Annotated[str, typer.Option("--model", "-m", help="Whisper 模型名称")] = "large-v3-turbo",
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
                transcriber = WhisperTranscriber(model=model)
                transcript = transcriber.transcribe(audio_path, video_name=video.name)
            finally:
                audio_path.unlink(missing_ok=True)

            progress.update(task, description="写入输出...")
            write_transcript(transcript, output)
            progress.update(task, description=f"完成! 输出: {output}")

    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        console.print(f"[red]错误[/red]: {exc}")
        raise typer.Exit(code=1)

    console.print(f"\n[green]转录完成[/green] — {len(transcript.segments)} 个片段 → {output}")


if __name__ == "__main__":
    app()
