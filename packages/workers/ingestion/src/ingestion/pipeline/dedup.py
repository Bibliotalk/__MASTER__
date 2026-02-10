from __future__ import annotations

import hashlib
import re

from ..models import CanonIndex


def normalize(text: str) -> str:
    """Normalize text for hashing: lowercase, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compute_hash(text: str) -> str:
    """SHA-256 hex digest of the normalized text."""
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


class Deduplicator:
    """Track seen content hashes and source URLs for deduplication."""

    def __init__(self, existing_index: CanonIndex | None = None) -> None:
        self._hashes: set[str] = set()
        self._urls: set[str] = set()

        if existing_index:
            for entry in existing_index.entries:
                # Strip the "sha256:" prefix if present.
                h = entry.content_hash
                if h.startswith("sha256:"):
                    h = h[7:]
                self._hashes.add(h)
                self._urls.add(entry.source_url)

    def is_duplicate(
        self,
        *,
        content_hash: str,
        source_url: str,
    ) -> bool:
        return content_hash in self._hashes or source_url in self._urls

    def add(self, *, content_hash: str, source_url: str) -> None:
        self._hashes.add(content_hash)
        self._urls.add(source_url)
