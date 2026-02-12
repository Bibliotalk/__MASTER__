from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from markitdown import MarkItDown

from ..config import settings
from ..models import ExtractedText, Source, ToolResult
from .base import ToolAdapter


class DocAdapter(ToolAdapter):
    """Extract text from uploaded documents (epub, pdf, docx, html, txt, md, …).

    Uses *markitdown* for all formats.  ``source.url`` must be a local file
    path (written by the upload endpoint) or an HTTP(S) URL.
    """

    async def extract(self, source: Source) -> ToolResult:
        source_url = source.url

        try:
            path = self._resolve_local_path(source_url)
            if path is None:
                if self._is_http_url(source_url):
                    path = await self._download_remote(source_url)
                else:
                    return ToolResult(source_id=source.id, errors=[f"File not found: {source.url}"])
        except Exception as exc:
            return ToolResult(source_id=source.id, errors=[str(exc)])

        return await asyncio.to_thread(self._convert_local_sync, source, path, source_url)

    def _resolve_local_path(self, source_url: str) -> Path | None:
        """Resolve a local filesystem path for the given source_url.

        Supports:
        - direct file paths
        - digest:sha256:<hex> URIs produced by the upload endpoint
        """
        path = Path(source_url)
        if path.exists():
            return path

        # Support `digest:sha256:<hex>` URIs produced by the upload endpoint.
        # We resolve them to a concrete file under data_dir/uploads for reading,
        # but preserve the digest URI as the canonical source_url stored in chunks.
        if source_url.startswith("digest:sha256:"):
            digest = source_url.split(":", 2)[2]
            uploads_dir = settings.data_dir / "uploads"
            matches = list(uploads_dir.glob(f"{digest}_*"))
            if matches:
                candidate = matches[0]
                if candidate.exists():
                    return candidate

        return None

    def _is_http_url(self, url: str) -> bool:
        u = url.strip().lower()
        return u.startswith("http://") or u.startswith("https://")

    def _safe_filename_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        name = Path(unquote(parsed.path or "")).name
        name = Path(name).name  # extra safety
        return name or "download"

    async def _download_remote(self, url: str) -> Path:
        downloads_dir = settings.data_dir / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        filename = self._safe_filename_from_url(url)
        dest = downloads_dir / f"{url_hash}_{filename}"

        # Basic cache: if we already have a non-empty file, reuse it.
        try:
            if dest.exists() and dest.stat().st_size > 0:
                return dest
        except OSError:
            pass

        tmp = dest.with_name(dest.name + ".part")
        timeout = httpx.Timeout(settings.doc_download_timeout_s)
        headers = {"User-Agent": "BibliotalkIngestion/0.1"}

        total = 0
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=timeout,
                headers=headers,
            ) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    with tmp.open("wb") as f:
                        async for chunk in resp.aiter_bytes():
                            if not chunk:
                                continue
                            total += len(chunk)
                            if total > settings.doc_max_bytes:
                                raise ValueError(
                                    f"Remote document too large (> {settings.doc_max_bytes} bytes): {url}"
                                )
                            f.write(chunk)

            os.replace(tmp, dest)
            return dest
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"Download failed ({exc.response.status_code}) for {url}") from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"Download failed for {url}: {exc}") from exc
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass

    def _convert_local_sync(self, source: Source, path: Path, source_url: str) -> ToolResult:

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
