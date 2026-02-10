from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from .adapters import ADAPTERS
from .config import settings
from .models import CanonIndex, Session, SessionStage
from .pipeline.dedup import Deduplicator
from .pipeline.formatter import format_and_write
from .session import store

# Active execution streams: session_id → asyncio.Queue of log lines.
_streams: dict[str, asyncio.Queue[str | None]] = {}


def get_stream(session_id: str) -> asyncio.Queue[str | None] | None:
    return _streams.get(session_id)


async def execute(session_id: str) -> None:
    """Run ingestion for all sources in the session directly (no subprocess)."""
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    _streams[session_id] = queue

    async def log(msg: str) -> None:
        session = store.get(session_id)
        if session:
            session.log.append(msg)
            store.update(session)
        await queue.put(msg)

    try:
        session = store.get(session_id)
        if not session:
            await log("[ERROR] Session not found")
            return

        output_dir = settings.output_dir / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load or create index.
        index_path = output_dir / "index.json"
        if index_path.exists():
            index = CanonIndex.model_validate_json(index_path.read_text())
        else:
            index = CanonIndex(agent_id=session.name)

        dedup = Deduplicator(session.existing_index or index)

        total_written = 0

        for source in session.sources:
            adapter_cls = ADAPTERS.get(source.type.value)
            if adapter_cls is None:
                await log(f"[SKIP] Unknown source type: {source.type}")
                continue

            await log(f"[SOURCE] {source.label or source.url}")

            try:
                adapter = adapter_cls()
                result = await adapter.extract(source)

                for err in result.errors:
                    await log(f"  [WARN] {err}")

                for extracted in result.texts:
                    written = format_and_write(
                        extracted,
                        source_type=source.type,
                        output_dir=output_dir,
                        index=index,
                        dedup=dedup,
                    )
                    for filename in written:
                        await log(f"  [WROTE] {filename}")
                        total_written += 1

                if not result.texts and not result.errors:
                    await log("  [WARN] No texts extracted")

            except Exception as exc:
                await log(f"  [ERROR] {exc}")

        # Write final index.
        index.updated = datetime.now(timezone.utc)
        index_path.write_text(index.model_dump_json(indent=2))
        await log(f"\n[DONE] {total_written} files written, {len(index.entries)} total entries")

        session = store.get(session_id)
        if session:
            session.stage = SessionStage.DONE
            store.update(session)

    except Exception as exc:
        await log(f"[ERROR] {exc}")
        session = store.get(session_id)
        if session:
            session.stage = SessionStage.ERROR
            store.update(session)
    finally:
        await queue.put(None)  # sentinel — signals end of stream
        _streams.pop(session_id, None)
