from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ..models import ExtractedText, SourceType
from .cleaner import clean_text
from .dedup import Deduplicator, compute_hash
from .splitter import split_text


def format_chunks(
    extracted: ExtractedText,
    *,
    source_type: SourceType,
    dedup: Deduplicator,
    max_words: int = 4000,
) -> list[dict]:
    """Clean, split, deduplicate, and return chunk dicts."""
    cleaned = clean_text(extracted.body)
    if not cleaned:
        return []

    sections = split_text(cleaned, max_words=max_words)
    chunks = []

    for i, section in enumerate(sections):
        content_hash = compute_hash(section)
        if dedup.is_duplicate(content_hash=content_hash, source_url=extracted.source_url):
            continue

        # TODO: startPos/endPos are computed by summing section lengths, which can be inaccurate if split_text drops/normalizes separators or whitespace between sections (and it is also O(n^2) across chunks). Consider having split_text return offsets, or maintain a running cursor that accounts for whatever delimiter/joining logic is used.
        word_count = len(section.split())
        # Calculate start/end positions
        start_pos = sum(len(s) for s in sections[:i])
        end_pos = start_pos + len(section)

        chunk = {
            "id": f"chunk_{uuid4().hex}",
            "kind": "canon",
            "title": extracted.title + (f" (Part {i+1})" if len(sections) > 1 else ""),
            "text": section,
            "sourceUri": extracted.source_url,
            "sourceTitle": extracted.title,
            "sourceType": source_type.value,
            "contentHash": f"sha256:{content_hash}",
            "startPos": start_pos,
            "endPos": end_pos,
            "sourceLength": len(cleaned),
            "wordCount": word_count,
            "tags": [],
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        dedup.add(content_hash=content_hash, source_url=extracted.source_url)
        chunks.append(chunk)

    return chunks
