from __future__ import annotations

import asyncio
import os
import re
from datetime import timedelta
from urllib.parse import urljoin, urlparse

import httpx
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

    async def _fetch_html_fallback(self, url: str) -> str | None:
        """Best-effort HTML fetch for the seed URL.

        We intentionally avoid inheriting proxy env vars, because many dev
        machines set HTTP(S)_PROXY to a local port that may not be running.
        """

        proxy_keys = [
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "no_proxy",
        ]

        old_env: dict[str, str] = {}
        for k in proxy_keys:
            v = os.environ.get(k)
            if v is not None:
                old_env[k] = v
                os.environ.pop(k, None)

        try:
            # Try trafilatura's built-in fetcher first (often more tolerant).
            try:
                html = await asyncio.to_thread(trafilatura.fetch_url, url)
                if html:
                    return html
            except Exception:
                # Fall through to httpx.
                pass

            timeout = httpx.Timeout(90.0, connect=15.0, read=90.0)
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; BibliotalkIngestion/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            # Avoid proxy env vars by default.
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, trust_env=False) as client:
                last_exc: Exception | None = None
                for _attempt in range(3):
                    try:
                        res = await client.get(url, headers=headers)
                        res.raise_for_status()
                        return res.text
                    except (httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                        last_exc = exc
                        await asyncio.sleep(0.5)
                if last_exc:
                    raise last_exc

            return None
        finally:
            # Restore env vars (best-effort).
            for k in proxy_keys:
                os.environ.pop(k, None)
            os.environ.update(old_env)

    async def extract(self, source: Source) -> ToolResult:
        texts: list[ExtractedText] = []
        errors: list[str] = []
        allowed_domain = tldextract.extract(source.url).registered_domain

        crawler = BeautifulSoupCrawler(
            max_requests_per_crawl=self.max_pages,
            # Crawlee's underlying HTTP client can fail TLS handshakes on some sites
            # (e.g. SelectedUnusableCipherSuiteForVersion). Keep retries low so we
            # fall back quickly instead of stalling the entire ingestion job.
            max_request_retries=1,
            use_session_pool=False,
            request_handler_timeout=timedelta(seconds=30),
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

        # If Crawlee couldn't fetch anything (common with proxy/TLS handshake problems),
        # try a simple direct fetch of the seed URL so we can still ingest something.
        if not texts:
            try:
                html = await self._fetch_html_fallback(source.url)
                if html:
                    body = trafilatura.extract(
                        html,
                        output_format="markdown",
                        include_links=True,
                        include_tables=True,
                        url=source.url,
                    )
                    if body and len(body.split()) >= 50:
                        meta = trafilatura.metadata.extract_metadata(html)
                        title = (meta.title if meta else None) or source.url.rsplit("/", 1)[-1]
                        date = (meta.date if meta else None) or None
                        texts.append(
                            ExtractedText(
                                title=title,
                                body=body,
                                source_url=source.url,
                                date=date,
                            )
                        )
            except Exception as exc:
                errors.append(
                    f"CrawlerAdapter fallback fetch error ({type(exc).__name__}): {exc!s} ({exc!r})"
                )

        if not texts and not errors:
            errors.append(f"No content extracted from {source.url}")

        return ToolResult(source_id=source.id, texts=texts, errors=errors)
