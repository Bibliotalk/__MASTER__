from __future__ import annotations

import httpx

from .config import settings

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        # Avoid inheriting HTTP(S)_PROXY from the environment; ingestion frequently
        # talks to a local API base URL and proxy env vars can break that.
        _client = httpx.AsyncClient(timeout=30.0, trust_env=False)
    return _client


def _sanitize_chunk_for_api(chunk: dict) -> dict:
    # Keep in sync with API schema constraints in packages/api/src/routes/memory.ts
    # (memoryChunkCreateSchema). Extra fields are allowed, but core fields have
    # max lengths.
    MAX_ID = 256
    MAX_TITLE = 500
    MAX_SOURCE_URI = 2000
    MAX_SOURCE_TITLE = 500
    MAX_TEXT = 200_000

    sanitized = dict(chunk)

    def trunc(key: str, limit: int, *, suffix: str = "") -> None:
        val = sanitized.get(key)
        if not isinstance(val, str):
            return
        if len(val) <= limit:
            return
        keep = max(0, limit - len(suffix))
        sanitized[key] = val[:keep] + suffix
        sanitized[f"{key}Truncated"] = True

    trunc("id", MAX_ID)
    trunc("title", MAX_TITLE)
    trunc("sourceUri", MAX_SOURCE_URI)
    trunc("sourceTitle", MAX_SOURCE_TITLE)
    trunc("text", MAX_TEXT, suffix="\n\n[truncated]")

    return sanitized


async def store_chunk(agent_id: str, chunk: dict) -> str:
    """POST a chunk to the API's memory endpoint. Returns chunk id."""
    url = f"{settings.api_base_url}/api/agents/{agent_id}/memory"
    client = _get_client()
    chunk_sanitized = _sanitize_chunk_for_api(chunk)
    response = await client.post(
        url,
        json=chunk_sanitized,
        headers={"X-Worker-Secret": settings.worker_secret},
    )

    if response.is_error:
        # Include response body for debugging (e.g. ValidationError details).
        body_preview = (response.text or "").strip()
        if len(body_preview) > 2000:
            body_preview = body_preview[:2000] + "…"
        raise httpx.HTTPStatusError(
            f"store_chunk failed: {response.status_code} {response.reason_phrase}; body={body_preview}",
            request=response.request,
            response=response,
        )

    return chunk_sanitized["id"]
