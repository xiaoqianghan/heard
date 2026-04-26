from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from heard.audio import extract_audio
from heard.output import write_transcript, format_transcript_text, load_transcript
from heard.summarizer import summarize_single, summarize_batch
from heard.transcriber import DEFAULT_MODEL, DEFAULT_LANGUAGE, WhisperTranscriber

app = typer.Typer(help="Heard — Video speech transcription tool")
console = Console()


@app.callback()
def main() -> None:
    pass


@app.command()
def transcribe(
    video: Annotated[Path, typer.Argument(help="Path to the video file")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output JSON file path")] = None,
    model: Annotated[str, typer.Option("--model", "-m", help="Whisper model name")] = DEFAULT_MODEL,
    language: Annotated[str, typer.Option("--language", "-l", help="Transcription language")] = DEFAULT_LANGUAGE,
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
            task = progress.add_task("Extracting audio...", total=None)
            audio_path = extract_audio(video)
            progress.update(task, description="Transcribing...")

            try:
                transcriber = WhisperTranscriber(model=model, language=language)
                transcript = transcriber.transcribe(audio_path, video_name=video.name)
            finally:
                audio_path.unlink(missing_ok=True)

            progress.update(task, description="Writing output...")
            write_transcript(transcript, output)
            progress.update(task, description=f"Done! Output: {output}")

        console.print(f"\n[green]Transcription complete[/green] — {len(transcript.segments)} segments → {output}")

    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        console.print(f"[red]Error[/red]: {exc}")
        raise typer.Exit(code=1)


@app.command()
def export(
    json_file: Annotated[Path, typer.Argument(help="Path to the transcript JSON file")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    json_file = json_file.resolve()

    if not json_file.exists():
        console.print(f"[red]Error[/red]: File not found — {json_file}")
        raise typer.Exit(code=1)

    transcript = load_transcript(json_file)

    if output is None:
        output = json_file.with_suffix(".txt")
    output = output.resolve()

    text = format_transcript_text(transcript)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

    console.print(f"[green]Export complete[/green] — {len(transcript.segments)} segments → {output}")


@app.command()
def summarize(
    path: Annotated[Path, typer.Argument(help="Path to a transcript JSON file or directory")],
    output_dir: Annotated[Path | None, typer.Option("--output-dir", "-o", help="Output directory")] = None,
    batch: Annotated[bool, typer.Option("--batch", "-b", help="Batch process all JSON files in directory")] = False,
) -> None:
    """Extract core concepts and keywords from transcripts using Claude."""
    path = path.resolve()

    if not path.exists():
        console.print(f"[red]Error[/red]: Path not found — {path}")
        raise typer.Exit(code=1)

    try:
        if batch:
            if not path.is_dir():
                console.print("[red]Error[/red]: Batch mode requires a directory")
                raise typer.Exit(code=1)

            console.print(f"[bold]Batch processing[/bold]: {path}")
            paths = summarize_batch(path, output_dir=output_dir)
            console.print(f"\n[green]Done[/green] — generated {len(paths)} files")
        else:
            if path.is_dir():
                console.print("[red]Error[/red]: Single-file mode requires a .json file (use --batch for directories)")
                raise typer.Exit(code=1)

            console.print(f"[bold]Processing[/bold]: {path.name}")
            output = summarize_single(path, output_dir=output_dir)
            console.print(f"[green]Done[/green] → {output}")

    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Error[/red]: {exc}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
