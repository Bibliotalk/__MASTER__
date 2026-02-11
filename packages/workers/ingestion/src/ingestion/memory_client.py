from __future__ import annotations

import httpx

from .config import settings


async def store_chunk(agent_id: str, chunk: dict) -> str:
    """POST a chunk to the API's memory endpoint. Returns chunk id."""
    url = f"{settings.api_base_url}/api/agents/{agent_id}/memory"
    # TODO: Creating a new httpx.AsyncClient per chunk adds overhead and may limit throughput. Consider reusing a single client (module-level, injected, or lifespan-managed) and configuring timeouts/retries for network resilience.
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=chunk,
            headers={"X-Worker-Secret": settings.worker_secret},
        )
        response.raise_for_status()
    # TODO: This returns the local chunk[\"id\"] rather than the id acknowledged/assigned by the API. If the server generates or transforms ids, logs and client state can diverge. Parse and return the id from the response payload (or document that the server accepts client-provided ids and returns 204).
    return chunk["id"]
