from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from .adapters import ADAPTERS
from .job import jobs
from .models import Job, JobStatus
from .pipeline.dedup import Deduplicator
from .pipeline.formatter import format_chunks
from . import memory_client

# Active execution streams: job_id -> asyncio.Queue of log lines.
_streams: dict[str, asyncio.Queue[str | None]] = {}


def get_stream(job_id: str) -> asyncio.Queue[str | None] | None:
    return _streams.get(job_id)


async def execute(job_id: str) -> None:
    """Run ingestion for all sources in the job."""
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    _streams[job_id] = queue

    async def log(msg: str) -> None:
        await queue.put(msg)

    try:
        job = jobs.get(job_id)
        if not job:
            await log("[ERROR] Job not found")
            return

        job.status = JobStatus.running
        job.progress.totalSources = len(job.sources)
        jobs.update(job)

        dedup = Deduplicator()

        for source in job.sources:
            adapter_cls = ADAPTERS.get(source.type.value)
            if adapter_cls is None:
                await log(f"[SKIP] Unknown source type: {source.type}")
                job.progress.errors.append(f"Unknown source type: {source.type}")
                job.progress.completedSources += 1
                jobs.update(job)
                continue

            job.progress.currentSource = source.label or source.url
            jobs.update(job)
            await log(f"[SOURCE] {source.label or source.url}")

            try:
                adapter = adapter_cls()
                result = await adapter.extract(source)

                for err in result.errors:
                    await log(f"  [WARN] {err}")
                    job.progress.errors.append(err)

                for extracted in result.texts:
                    chunks = format_chunks(
                        extracted,
                        source_type=source.type,
                        dedup=dedup,
                    )
                    for chunk in chunks:
                        chunk["jobId"] = job.id
                        chunk_id = await memory_client.store_chunk(
                            agent_id=job.agent_id,
                            chunk=chunk,
                        )
                        job.progress.chunksWritten += 1
                        await log(f"  [CHUNK] {chunk_id}")

                if not result.texts and not result.errors:
                    await log("  [WARN] No texts extracted")

            except Exception as exc:
                await log(f"  [ERROR] {exc}")
                job.progress.errors.append(str(exc))

            job.progress.completedSources += 1
            jobs.update(job)

        job.progress.currentSource = None
        job.status = JobStatus.done
        job.completed_at = datetime.now(timezone.utc)
        jobs.update(job)
        await log(f"\n[DONE] {job.progress.chunksWritten} chunks written")

    except Exception as exc:
        await log(f"[ERROR] {exc}")
        job = jobs.get(job_id)
        if job:
            job.status = JobStatus.error
            job.progress.errors.append(str(exc))
            job.completed_at = datetime.now(timezone.utc)
            jobs.update(job)
    finally:
        await queue.put(None)  # sentinel -- signals end of stream
        _streams.pop(job_id, None)
