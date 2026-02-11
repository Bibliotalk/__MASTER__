from __future__ import annotations

import json
from pathlib import Path

from openai import AsyncOpenAI

from .config import settings

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )


# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


async def suggest_sources(name: str) -> list[dict]:
    """Ask the LLM to suggest source URLs for a person."""
    prompt = _load_prompt("suggest.md").replace("{{name}}", name)
    client = _client()
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    raw = resp.choices[0].message.content or "[]"
    # Strip markdown fences if present.
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw.strip())
