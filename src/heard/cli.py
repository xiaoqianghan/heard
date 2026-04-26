from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from heard.audio import extract_audio
from heard.output import write_transcript, format_transcript_text, load_transcript
from heard.summarizer import summarize_single, summarize_batch
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


@app.command()
def summarize(
    path: Annotated[Path, typer.Argument(help="转录 JSON 文件路径或目录")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir", "-o", help="输出目录")] = None,
    batch: Annotated[bool, typer.Option("--batch", "-b", help="批量处理目录下所有 JSON 文件")] = False,
) -> None:
    """使用 Claude 从转录中提取核心概念与关键词。"""
    path = path.resolve()

    if not path.exists():
        console.print(f"[red]错误[/red]: 路径不存在 — {path}")
        raise typer.Exit(code=1)

    try:
        if batch:
            if not path.is_dir():
                console.print("[red]错误[/red]: 批量模式需要指定目录")
                raise typer.Exit(code=1)

            console.print(f"[bold]批量处理[/bold]: {path}")
            paths = summarize_batch(path, output_dir=output_dir)
            console.print(f"\n[green]完成[/green] — 生成 {len(paths)} 个文件")
        else:
            if path.is_dir():
                console.print("[red]错误[/red]: 单文件模式需要指定 .json 文件（目录请使用 --batch）")
                raise typer.Exit(code=1)

            console.print(f"[bold]处理[/bold]: {path.name}")
            output = summarize_single(path, output_dir=output_dir)
            console.print(f"[green]完成[/green] → {output}")

    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]错误[/red]: {exc}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
