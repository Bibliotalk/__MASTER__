from __future__ import annotations

import httpx

from .config import settings

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def store_chunk(agent_id: str, chunk: dict) -> str:
    """POST a chunk to the API's memory endpoint. Returns chunk id."""
    url = f"{settings.api_base_url}/api/agents/{agent_id}/memory"
    client = _get_client()
    response = await client.post(
        url,
        json=chunk,
        headers={"X-Worker-Secret": settings.worker_secret},
    )
    response.raise_for_status()
    return chunk["id"]
