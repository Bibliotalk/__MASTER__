from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from slugify import slugify

from ..models import CanonIndex, ExtractedText, IndexEntry, SourceType
from .cleaner import clean_text
from .dedup import Deduplicator, compute_hash
from .splitter import split_text


def format_and_write(
    extracted: ExtractedText,
    *,
    source_type: SourceType,
    output_dir: Path,
    index: CanonIndex,
    dedup: Deduplicator,
    max_words: int = 4000,
) -> list[str]:
    """Clean, split, deduplicate, format, and write canon files.

    Returns the list of filenames written (empty if all duplicates).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned = clean_text(extracted.body)
    if not cleaned:
        return []

    sections = split_text(cleaned, max_words=max_words)
    written: list[str] = []

    for i, section in enumerate(sections):
        content_hash = compute_hash(section)
        if dedup.is_duplicate(
            content_hash=content_hash, source_url=extracted.source_url
        ):
            continue

        # Build filename: YYYY-title-slug[-partN].md
        date_prefix = extracted.date[:4] if extracted.date else "0000"
        title_slug = slugify(extracted.title, max_length=60)
        suffix = f"-part{i + 1}" if len(sections) > 1 else ""
        filename = f"{date_prefix}-{title_slug}{suffix}.md"

        # YAML frontmatter
        frontmatter = (
            f"---\n"
            f"title: \"{_escape_yaml(extracted.title)}\"\n"
            f"source_url: \"{extracted.source_url}\"\n"
            f"source_type: \"{source_type.value}\"\n"
        )
        if extracted.date:
            frontmatter += f"date: \"{extracted.date}\"\n"
        frontmatter += f"---\n\n"

        full_content = frontmatter + section
        (output_dir / filename).write_text(full_content, encoding="utf-8")

        word_count = len(section.split())
        entry_id = f"canon_{len(index.entries) + 1:04d}"

        index.entries.append(
            IndexEntry(
                id=entry_id,
                filename=filename,
                title=extracted.title,
                source_url=extracted.source_url,
                source_type=source_type,
                date=extracted.date,
                content_hash=f"sha256:{content_hash}",
                word_count=word_count,
            )
        )
        dedup.add(content_hash=content_hash, source_url=extracted.source_url)
        written.append(filename)

    return written


def _escape_yaml(s: str) -> str:
    return s.replace('"', '\\"')
