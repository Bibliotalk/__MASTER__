from __future__ import annotations

import asyncio
import re
import tempfile
from pathlib import Path

import yt_dlp

from ..models import ExtractedText, Source, ToolResult
from .base import ToolAdapter


def _parse_vtt(text: str) -> str:
    """Extract plain text from a WebVTT subtitle file."""
    lines: list[str] = []
    for line in text.splitlines():
        if (
            "-->" in line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or not line.strip()
        ):
            continue
        clean = re.sub(r"<[^>]+>", "", line.strip())
        # Collapse consecutive duplicate lines (common in auto-captions).
        if clean and (not lines or lines[-1] != clean):
            lines.append(clean)
    return "\n".join(lines)


class YouTubeAdapter(ToolAdapter):
    """Extract transcripts from YouTube videos, playlists, or channels."""

    async def extract(self, source: Source) -> ToolResult:
        return await asyncio.to_thread(self._extract_sync, source)

    def _extract_sync(self, source: Source) -> ToolResult:
        texts: list[ExtractedText] = []
        errors: list[str] = []

        try:
            # Resolve playlist / channel into individual video URLs.
            with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
                info = ydl.extract_info(source.url, download=False)

            entries = info.get("entries", [info]) if info else [info]
            video_urls = [
                e.get("url") or e.get("webpage_url")
                for e in entries
                if e
            ]
            if not video_urls:
                video_urls = [source.url]

            with tempfile.TemporaryDirectory() as tmpdir:
                for url in video_urls:
                    try:
                        self._process_video(url, tmpdir, texts, errors)
                    except Exception as exc:
                        errors.append(f"Error processing {url}: {exc}")
        except Exception as exc:
            errors.append(f"YouTubeAdapter error: {exc}")

        return ToolResult(source_id=source.id, texts=texts, errors=errors)

    @staticmethod
    def _process_video(
        url: str,
        tmpdir: str,
        texts: list[ExtractedText],
        errors: list[str],
    ) -> None:
        opts = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "zh-Hans", "zh-Hant", "zh"],
            "subtitlesformat": "vtt",
            "skip_download": True,
            "quiet": True,
            "outtmpl": str(Path(tmpdir) / "%(id)s.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            video_info = ydl.extract_info(url, download=True)
            vid_id = video_info.get("id", "")
            title = video_info.get("title", "Untitled")
            upload_date = video_info.get("upload_date", "")

            # Read the first VTT file we find for this video.
            transcript = ""
            for vtt_file in Path(tmpdir).glob(f"{vid_id}*.vtt"):
                transcript = _parse_vtt(vtt_file.read_text(encoding="utf-8"))
                break

            if not transcript:
                desc = video_info.get("description", "")
                transcript = desc or "[No transcript available]"

            date = None
            if upload_date and len(upload_date) == 8:
                date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

            texts.append(
                ExtractedText(
                    title=title,
                    body=transcript,
                    source_url=video_info.get("webpage_url", url),
                    date=date,
                    metadata={
                        "channel": video_info.get("channel", ""),
                        "duration": video_info.get("duration", 0),
                    },
                )
            )
