#!/usr/bin/env python3
"""Quick smoke test for all four adapters."""

import asyncio

from ingestion.adapters import (CrawlerAdapter, DocAdapter, RSSAdapter,
                                YouTubeAdapter)
from ingestion.models import Source, SourceType

SOURCES = [
    Source(type=SourceType.web,     url="https://paulgraham.com/articles.html", label="Paul Graham Essays"),
    Source(type=SourceType.youtube, url="https://www.youtube.com/watch?v=UF8uR6Z6KLc", label="Steve Jobs Interview"),
    Source(type=SourceType.epub,    url="data/The old man and the sea.epub",    label="The Old Man and the Sea"),
    Source(type=SourceType.rss,     url="https://kk.org/thetechnium/feed",      label="KK Technium Feed"),
]

ADAPTERS = {
    SourceType.web:     CrawlerAdapter,
    SourceType.youtube: YouTubeAdapter,
    SourceType.rss:     RSSAdapter,
    SourceType.epub:    DocAdapter,
}


async def test_one(source: Source) -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  [{source.type.value.upper()}] {source.label}")
    print(f"  {source.url}")
    print(sep)

    adapter = ADAPTERS[source.type]()

    try:
        result = await adapter.extract(source)
    except Exception as exc:
        print(f"  EXCEPTION: {exc}")
        return

    if result.errors:
        for err in result.errors:
            print(f"  ERROR: {err}")

    if not result.texts:
        print("  No texts extracted.")
        return

    print(f"  Extracted {len(result.texts)} text(s):\n")
    for i, t in enumerate(result.texts, 1):
        body_preview = t.body[:200].replace("\n", " ")
        print(f"  {i}. {t.title}")
        print(f"     date: {t.date or '—'}  words: {len(t.body.split())}")
        print(f"     preview: {body_preview}…")
        print()


async def main() -> None:
    for source in SOURCES:
        await test_one(source)
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
