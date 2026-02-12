from __future__ import annotations

import asyncio
import re
from urllib.parse import urljoin, urlparse

import tldextract
import trafilatura
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

from ..config import settings
from ..models import ExtractedText, Source, ToolResult
from .base import ToolAdapter


class CrawlerAdapter(ToolAdapter):
    """Crawl a website, follow links, and extract article text as Markdown.

    Uses crawlee (BeautifulSoupCrawler) for link discovery and traversal,
    and trafilatura for content extraction. No browser required.
    """

    def __init__(self, max_pages: int | None = None) -> None:
        self.max_pages = max_pages if max_pages is not None else settings.crawler_max_pages

    async def extract(self, source: Source) -> ToolResult:
        texts: list[ExtractedText] = []
        errors: list[str] = []
        allowed_domain = tldextract.extract(source.url).registered_domain

        crawler = BeautifulSoupCrawler(
            max_requests_per_crawl=self.max_pages,
        )

        @crawler.router.default_handler
        async def handler(context: BeautifulSoupCrawlingContext) -> None:
            url = context.request.url

            # Enqueue same-domain links.
            await context.enqueue_links(
                strategy="all",
                include=[re.compile(rf"^https?://(.*\.)?{re.escape(allowed_domain)}(/.*)?$")],
            )

            # Extract article content via trafilatura.
            html = str(context.soup)
            body = trafilatura.extract(
                html,
                output_format="markdown",
                include_links=True,
                include_tables=True,
                url=url,
            )

            if not body or len(body.split()) < 50:
                return  # skip navigational / thin pages

            meta = trafilatura.metadata.extract_metadata(html)
            title = (meta.title if meta else None) or url.rsplit("/", 1)[-1]
            date = (meta.date if meta else None) or None

            texts.append(
                ExtractedText(
                    title=title,
                    body=body,
                    source_url=url,
                    date=date,
                )
            )

        try:
            await crawler.run([source.url])
        except Exception as exc:
            errors.append(f"CrawlerAdapter error: {exc}")

        if not texts and not errors:
            errors.append(f"No content extracted from {source.url}")

        return ToolResult(source_id=source.id, texts=texts, errors=errors)
