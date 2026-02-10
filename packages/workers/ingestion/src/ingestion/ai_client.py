from __future__ import annotations

import json
from pathlib import Path

from openai import AsyncOpenAI

from .config import settings
from .models import Session, Source

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )


def _sources_json(sources: list[Source]) -> str:
    return json.dumps(
        [s.model_dump(mode="json") for s in sources],
        indent=2,
        ensure_ascii=False,
    )


def _existing_index_info(session: Session) -> str:
    if session.existing_index and session.existing_index.entries:
        n = len(session.existing_index.entries)
        return (
            f"An existing canon with {n} entries is loaded. "
            f"The deduplicator will automatically skip entries that already "
            f"exist, so the plan should focus only on new content."
        )
    return "This is a fresh canon with no existing entries."


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


async def generate_plan(session: Session) -> str:
    """Generate an ingestion plan from confirmed sources."""
    template = _load_prompt("plan.md")
    prompt = (
        template
        .replace("{{name}}", session.name)
        .replace("{{sources_json}}", _sources_json(session.sources))
        .replace("{{existing_index_info}}", _existing_index_info(session))
    )
    client = _client()
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


async def generate_program(session: Session) -> str:
    """Generate a Python script that executes the ingestion plan."""
    output_dir = str(settings.output_dir / session.id)
    template = _load_prompt("program.md")
    prompt = (
        template
        .replace("{{name}}", session.name)
        .replace("{{output_dir}}", output_dir)
        .replace("{{plan}}", session.plan)
        .replace("{{sources_json}}", _sources_json(session.sources))
        .replace("{{existing_index_info}}", _existing_index_info(session))
    )
    client = _client()
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    code = resp.choices[0].message.content or ""
    # Strip markdown fences if the model wraps the code.
    code = code.strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[1]
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]
    return code.strip()
