from .base import ToolAdapter
from .crawler import CrawlerAdapter
from .local_doc import DocAdapter
from .rss import RSSAdapter
from .youtube import YouTubeAdapter

ADAPTERS: dict[str, type[ToolAdapter]] = {
    "web": CrawlerAdapter,
    "youtube": YouTubeAdapter,
    "rss": RSSAdapter,
    "epub": DocAdapter,
    "text": DocAdapter,
}

__all__ = [
    "ToolAdapter",
    "CrawlerAdapter",
    "YouTubeAdapter",
    "RSSAdapter",
    "DocAdapter",
    "ADAPTERS",
]
