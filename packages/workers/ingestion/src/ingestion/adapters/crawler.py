from __future__ import annotations

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from ..models import ExtractedText, Source, ToolResult
from .base import ToolAdapter


class CrawlerAdapter(ToolAdapter):
    """Crawl a website and extract pages as Markdown via crawl4ai."""

    def __init__(self, max_pages: int = 50) -> None:
        self.max_pages = max_pages

    async def extract(self, source: Source) -> ToolResult:
        texts: list[ExtractedText] = []
        errors: list[str] = []

        try:
            config = CrawlerRunConfig()
            async with AsyncWebCrawler(browser_type="firefox", verbose=True, headless=True, fail_on_browser_error=True) as crawler:
                result = await crawler.arun(url=source.url, config=config)

                if result.success:
                    texts.append(
                        ExtractedText(
                            title=(
                                result.metadata.get("title", "")
                                if result.metadata
                                else ""
                            )
                            or source.label
                            or source.url,
                            body=result.markdown or "",
                            source_url=source.url,
                            date=None,
                            metadata=result.metadata or {},
                        )
                    )
                else:
                    errors.append(
                        f"Crawl failed for {source.url}: "
                        f"{getattr(result, 'error_message', 'unknown error')}"
                    )
        except Exception as exc:
            errors.append(f"CrawlerAdapter error: {exc}")

        return ToolResult(source_id=source.id, texts=texts, errors=errors)
