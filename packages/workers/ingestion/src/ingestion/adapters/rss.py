from __future__ import annotations

import asyncio

import feedparser
import trafilatura

from ..models import ExtractedText, Source, ToolResult
from .base import ToolAdapter


class RSSAdapter(ToolAdapter):
    """Parse an RSS/Atom feed and extract full article text."""

    async def extract(self, source: Source) -> ToolResult:
        return await asyncio.to_thread(self._extract_sync, source)

    def _extract_sync(self, source: Source) -> ToolResult:
        texts: list[ExtractedText] = []
        errors: list[str] = []

        try:
            feed = feedparser.parse(source.url)
            for entry in feed.entries:
                link = entry.get("link", "")
                title = entry.get("title", "Untitled")
                published = entry.get("published", "")

                body = ""
                if link:
                    try:
                        downloaded = trafilatura.fetch_url(link)
                        if downloaded:
                            body = (
                                trafilatura.extract(
                                    downloaded, output_format="markdown"
                                )
                                or ""
                            )
                    except Exception as exc:
                        errors.append(
                            f"trafilatura error for {link}: {exc}"
                        )

                # Fall back to feed summary if full-text extraction failed.
                if not body:
                    body = entry.get("summary", "")

                if body:
                    texts.append(
                        ExtractedText(
                            title=title,
                            body=body,
                            source_url=link or source.url,
                            date=published or None,
                            metadata={"feed_url": source.url},
                        )
                    )
        except Exception as exc:
            errors.append(f"RSSAdapter error: {exc}")

        return ToolResult(source_id=source.id, texts=texts, errors=errors)
