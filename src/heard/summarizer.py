"""Summarize video transcripts using Claude SDK."""

import asyncio
from pathlib import Path

from rich.console import Console

from heard.output import format_transcript_text, load_transcript
from heard.transcriber import Transcript

console = Console()

SUMMARY_SYSTEM_PROMPT = """你是一个课程学习助手。根据视频转录文本，提取核心概念与关键词。

输出格式（严格使用以下 Markdown 结构）：

# {视频文件名}

## 概要
{一句话概括视频主题}

## 核心概念
- {概念1}：{简要说明}
- {概念2}：{简要说明}

## 关键词
{关键词1}, {关键词2}, {关键词3}

要求：
- 概要控制在1-2句话
- 核心概念列出3-8个，每个附一句话说明
- 关键词用逗号分隔，列出5-10个
- 用中文输出"""

OVERVIEW_SYSTEM_PROMPT = """你是一个课程学习助手。根据一系列视频摘要，生成课程总览。

输出格式：

# 课程总览

## 课程结构
{对课程整体内容和结构的描述}

## 各视频概要
{按顺序列出每个视频的一句话概要}

## 推荐学习顺序
{如果有依赖关系，给出建议的学习顺序}

## 关联主题
{指出不同视频之间有关联的主题或概念}

要求：
- 用中文输出
- 结构清晰，便于快速浏览"""

MAX_CHUNK_SIZE = 50000


def _extract_text_from_transcript(transcript: Transcript) -> str:
    """Convert transcript to plain text using existing paragraph grouping."""
    if not transcript.segments:
        return ""
    return format_transcript_text(transcript)


def _chunk_text(text: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries, respecting max_size."""
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


async def _call_claude_async(system_prompt: str, user_prompt: str) -> str:
    """Call Claude via claude-code-sdk and return the result text."""
    from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query

    options = ClaudeCodeOptions(
        allowed_tools=[],
        system_prompt=system_prompt,
    )
    result_text = ""
    async for event in query(prompt=user_prompt, options=options):
        if isinstance(event, ResultMessage) and event.result:
            result_text = event.result
    return result_text


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Synchronous wrapper for _call_claude_async."""
    return asyncio.run(_call_claude_async(system_prompt, user_prompt))


class Summarizer:
    """Summarize video transcripts using Claude."""

    def summarize_single(self, json_path: Path, output_dir: Path | None = None) -> Path:
        """Summarize a single transcript JSON file."""
        json_path = json_path.resolve()
        if not json_path.exists():
            raise FileNotFoundError(f"转录文件不存在: {json_path}")

        transcript = load_transcript(json_path)
        text = _extract_text_from_transcript(transcript)

        if not text.strip():
            raise ValueError(f"转录文件内容为空: {json_path}")

        chunks = _chunk_text(text)

        if len(chunks) == 1:
            summary = _call_claude(SUMMARY_SYSTEM_PROMPT, chunks[0])
        else:
            partial_summaries = []
            for chunk in chunks:
                partial = _call_claude(SUMMARY_SYSTEM_PROMPT, chunk)
                partial_summaries.append(partial)
            merged_prompt = "以下是视频各部分的摘要，请合并为一份完整的摘要：\n\n" + "\n---\n".join(
                partial_summaries
            )
            summary = _call_claude(SUMMARY_SYSTEM_PROMPT, merged_prompt)

        if output_dir is None:
            output_dir = json_path.parent / "summaries"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{json_path.stem}.summary.md"
        output_path.write_text(summary, encoding="utf-8")

        return output_path

    def summarize_batch(self, directory: Path, output_dir: Path | None = None) -> list[Path]:
        """Summarize all transcript JSON files in a directory."""
        directory = directory.resolve()
        if not directory.is_dir():
            raise ValueError(f"目录不存在: {directory}")

        json_files = sorted(directory.glob("*.json"))
        if not json_files:
            raise ValueError(f"目录中没有 JSON 文件: {directory}")

        if output_dir is None:
            output_dir = directory / "summaries"

        summary_paths = []
        for json_file in json_files:
            output = self.summarize_single(json_file, output_dir=output_dir)
            summary_paths.append(output)
            console.print(f"  [green]✓[/green] {json_file.name} → {output.name}")

        # Generate course overview
        overview_parts = []
        for sp in summary_paths:
            content = sp.read_text(encoding="utf-8")
            filename = sp.stem.replace(".summary", "")
            overview_parts.append(f"### {filename}\n\n{content}")

        overview_prompt = "以下是课程中各视频的摘要：\n\n" + "\n---\n".join(overview_parts)
        overview = _call_claude(OVERVIEW_SYSTEM_PROMPT, overview_prompt)

        if output_dir is None:
            output_dir = directory / "summaries"
        output_dir.mkdir(parents=True, exist_ok=True)
        overview_path = output_dir / "course-overview.md"
        overview_path.write_text(overview, encoding="utf-8")
        summary_paths.append(overview_path)

        return summary_paths
