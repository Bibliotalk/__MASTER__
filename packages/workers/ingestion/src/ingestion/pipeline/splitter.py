from __future__ import annotations

import re


def split_text(
    text: str,
    max_words: int = 4000,
) -> list[str]:
    """Split a long document into sections.

    Strategy:
    1. Split on top-level headings (``# …`` or ``## …``) when present.
    2. If a resulting section still exceeds *max_words*, split on blank-line
       paragraph boundaries.
    3. Never split mid-paragraph.
    """
    if _word_count(text) <= max_words:
        return [text]

    # Try heading-based split first.
    sections = _split_on_headings(text)
    if len(sections) > 1:
        return _enforce_limit(sections, max_words)

    # Fall back to paragraph-based split.
    return _split_on_paragraphs(text, max_words)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _word_count(text: str) -> int:
    return len(text.split())


def _split_on_headings(text: str) -> list[str]:
    """Split on lines starting with ``#`` or ``##``."""
    parts: list[str] = []
    current: list[str] = []
    for line in text.splitlines(keepends=True):
        if re.match(r"^#{1,2}\s", line) and current:
            parts.append("".join(current))
            current = []
        current.append(line)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _split_on_paragraphs(text: str, max_words: int) -> list[str]:
    paragraphs = re.split(r"\n{2,}", text)
    chunks: list[str] = []
    current: list[str] = []
    current_wc = 0
    for para in paragraphs:
        wc = _word_count(para)
        if current and current_wc + wc > max_words:
            chunks.append("\n\n".join(current))
            current = []
            current_wc = 0
        current.append(para)
        current_wc += wc
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _enforce_limit(sections: list[str], max_words: int) -> list[str]:
    """Recursively split any section that exceeds *max_words*."""
    result: list[str] = []
    for section in sections:
        if _word_count(section) <= max_words:
            result.append(section)
        else:
            result.extend(_split_on_paragraphs(section, max_words))
    return result
