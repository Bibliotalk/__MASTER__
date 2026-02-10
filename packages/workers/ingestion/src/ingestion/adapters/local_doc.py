from __future__ import annotations

import asyncio
from pathlib import Path

from markitdown import MarkItDown

from ..models import ExtractedText, Source, ToolResult
from .base import ToolAdapter


class DocAdapter(ToolAdapter):
    """Extract text from uploaded documents (epub, pdf, docx, html, txt, md, …).

    Uses *markitdown* for all formats.  ``source.url`` must be a local file
    path (written by the upload endpoint).
    """

    async def extract(self, source: Source) -> ToolResult:
        return await asyncio.to_thread(self._extract_sync, source)

    def _extract_sync(self, source: Source) -> ToolResult:
        path = Path(source.url)
        if not path.exists():
            return ToolResult(
                source_id=source.id,
                errors=[f"File not found: {source.url}"],
            )

        texts: list[ExtractedText] = []
        errors: list[str] = []

        try:
            md = MarkItDown()
            result = md.convert(str(path))
            body = (result.text_content or "").strip()

            if body:
                texts.append(
                    ExtractedText(
                        title=source.label or path.stem,
                        body=body,
                        source_url=source.url,
                    )
                )
        except Exception as exc:
            errors.append(f"DocAdapter error for {path.name}: {exc}")

        return ToolResult(source_id=source.id, texts=texts, errors=errors)
