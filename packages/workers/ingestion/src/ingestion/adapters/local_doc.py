from __future__ import annotations

import asyncio
from pathlib import Path

from markitdown import MarkItDown

from ..config import settings
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
        source_url = source.url

        # Support `digest:sha256:<hex>` URIs produced by the upload endpoint.
        # We resolve them to a concrete file under data_dir/uploads for reading,
        # but preserve the digest URI as the canonical source_url stored in chunks.
        path = Path(source_url)
        if not path.exists() and source_url.startswith("digest:sha256:"):
            digest = source_url.split(":", 2)[2]
            uploads_dir = settings.data_dir / "uploads"
            matches = list(uploads_dir.glob(f"{digest}_*"))
            if matches:
                path = matches[0]

        if not path.exists():
            return ToolResult(source_id=source.id, errors=[f"File not found: {source.url}"])

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
                        source_url=source_url,
                    )
                )
            else:
                errors.append(f"No text extracted from: {path.name}")
        except Exception as exc:
            errors.append(f"DocAdapter error for {path.name}: {exc}")

        return ToolResult(source_id=source.id, texts=texts, errors=errors)
