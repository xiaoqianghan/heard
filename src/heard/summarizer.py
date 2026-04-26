"""Summarize video transcripts using Claude SDK."""

import asyncio
from pathlib import Path

from heard.output import format_transcript_text, load_transcript
from heard.transcriber import Transcript

SUMMARY_SYSTEM_PROMPT = """You are a course learning assistant. Extract core concepts and keywords from video transcripts.

Output format (strictly use the following Markdown structure):

# {video filename}

## Summary
{one-sentence summary of the video topic}

## Core Concepts
- {concept 1}: {brief explanation}
- {concept 2}: {brief explanation}

## Keywords
{keyword 1}, {keyword 2}, {keyword 3}

Requirements:
- Summary should be 1-2 sentences
- List 3-8 core concepts, each with a one-sentence explanation
- Keywords should be comma-separated, list 5-10
- Output in Chinese"""

OVERVIEW_SYSTEM_PROMPT = """You are a course learning assistant. Generate a course overview based on a series of video summaries.

Output format:

# Course Overview

## Course Structure
{description of the overall course content and structure}

## Video Summaries
{list one-sentence summaries for each video in order}

## Recommended Learning Order
{suggest a learning order if there are dependencies}

## Related Topics
{identify related themes or concepts across different videos}

Requirements:
- Output in Chinese
- Clear structure for quick browsing"""

MAX_CHUNK_SIZE = 50000


def _extract_text(transcript: Transcript) -> str:
    if not transcript.segments:
        return ""
    return format_transcript_text(transcript)


def _chunk_text(text: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    if not text:
        return []
    if len(text) <= max_size:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        if current_chunk and len(current_chunk) + len(para) + 2 > max_size:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


async def _call_claude(system_prompt: str, user_prompt: str) -> str:
    from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query  # pylint: disable=import-outside-toplevel

    options = ClaudeCodeOptions(
        allowed_tools=[],
        system_prompt=system_prompt,
    )
    result_text = ""
    async for event in query(prompt=user_prompt, options=options):
        if isinstance(event, ResultMessage) and event.result:
            result_text = event.result
    if not result_text:
        raise RuntimeError("Claude returned no valid result. Check your claude-code-sdk configuration.")
    return result_text


async def _summarize_text(text: str) -> str:
    chunks = _chunk_text(text)
    if len(chunks) == 1:
        return await _call_claude(SUMMARY_SYSTEM_PROMPT, chunks[0])
    partials = await asyncio.gather(
        *[_call_claude(SUMMARY_SYSTEM_PROMPT, ch) for ch in chunks]
    )
    merged = "Below are summaries of different parts of the video. Please merge them into a single complete summary:\n\n" + "\n---\n".join(partials)
    return await _call_claude(SUMMARY_SYSTEM_PROMPT, merged)


async def _summarize_file(json_path: Path, output_dir: Path | None = None) -> tuple[Path, str]:
    json_path = json_path.resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"Transcript file not found: {json_path}")

    transcript = load_transcript(json_path)
    text = _extract_text(transcript)
    if not text.strip():
        raise ValueError(f"Transcript file is empty: {json_path}")

    summary = await _summarize_text(text)

    if output_dir is None:
        output_dir = json_path.parent / "summaries"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{json_path.stem}.summary.md"
    output_path.write_text(summary, encoding="utf-8")

    return output_path, summary


def summarize_single(json_path: Path, output_dir: Path | None = None) -> Path:
    path, _ = asyncio.run(_summarize_file(json_path, output_dir))
    return path


async def _summarize_batch_async(directory: Path, output_dir: Path | None = None) -> list[Path]:
    directory = directory.resolve()
    if not directory.is_dir():
        raise ValueError(f"Directory does not exist: {directory}")

    json_files = sorted(directory.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found in directory: {directory}")

    if output_dir is None:
        output_dir = directory / "summaries"

    results = await asyncio.gather(
        *[_summarize_file(f, output_dir) for f in json_files]
    )

    summary_paths = []
    overview_parts = []
    for path, text in results:
        summary_paths.append(path)
        filename = path.stem.replace(".summary", "")
        overview_parts.append(f"### {filename}\n\n{text}")

    overview_prompt = "Below are summaries of each video in the course:\n\n" + "\n---\n".join(overview_parts)
    overview = await _call_claude(OVERVIEW_SYSTEM_PROMPT, overview_prompt)

    overview_path = output_dir / "course-overview.md"
    overview_path.write_text(overview, encoding="utf-8")
    summary_paths.append(overview_path)

    return summary_paths


def summarize_batch(directory: Path, output_dir: Path | None = None) -> list[Path]:
    return asyncio.run(_summarize_batch_async(directory, output_dir))
