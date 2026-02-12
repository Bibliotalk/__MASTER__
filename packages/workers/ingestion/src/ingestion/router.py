from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sse_starlette.sse import EventSourceResponse

from . import ai_client, executor
from .config import settings
from .job import jobs
from .models import CreateJobRequest, Job, JobStatus, Source, SourceType

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

async def verify_worker_secret(request: Request) -> None:
    """Check X-Worker-Secret header if worker_secret is configured."""
    if not settings.worker_secret:
        return  # dev mode — skip auth
    token = request.headers.get("X-Worker-Secret", "")
    if token != settings.worker_secret:
        raise HTTPException(403, "Invalid worker secret")


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


@router.get("/health", dependencies=[Depends(verify_worker_secret)])
async def health() -> dict:
    return {"status": "ok"}

@router.post("/sources/add", status_code=201, dependencies=[Depends(verify_worker_secret)])
async def create_job(body: CreateJobRequest) -> dict:
    """Create and start an ingestion job."""
    job = Job(agent_id=body.agent_id, sources=body.sources)
    job.progress.totalSources = len(body.sources)
    jobs.create(job)

    # Launch execution in the background.
    asyncio.create_task(executor.execute(job.id))

    return {"jobId": job.id, "status": job.status.value}


@router.get("/jobs/{job_id}", dependencies=[Depends(verify_worker_secret)])
async def get_job(job_id: str) -> Job:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, f"Job {job_id} not found")
    return job


@router.get("/jobs/{job_id}/stream", dependencies=[Depends(verify_worker_secret)])
async def job_stream(job_id: str) -> EventSourceResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, f"Job {job_id} not found")

    async def _event_generator() -> AsyncIterator[dict]:
        # If execution is already finished, emit final status.
        if job.status in (JobStatus.done, JobStatus.error):
            yield {"data": f"[{job.status.value.upper()}]"}
            return

        # Wait briefly for the stream queue to appear.
        queue = None
        for _ in range(50):
            queue = executor.get_stream(job_id)
            if queue is not None:
                break
            await asyncio.sleep(0.1)

        if queue is None:
            yield {"data": "[ERROR] No active execution stream"}
            return

        while True:
            line = await queue.get()
            if line is None:
                break
            yield {"data": line}

    return EventSourceResponse(_event_generator())


# ---------------------------------------------------------------------------
# Source suggestions
# ---------------------------------------------------------------------------

@router.get("/sources/suggest", dependencies=[Depends(verify_worker_secret)])
async def suggest_sources(name: str) -> list[dict]:
    return await ai_client.suggest_sources(name)


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

@router.post("/upload", dependencies=[Depends(verify_worker_secret)])
async def upload_file(file: UploadFile) -> dict:
    """Accept an uploaded file, compute SHA-256 hash, return digest URI."""
    content = await file.read()
    digest = hashlib.sha256(content).hexdigest()
    filename = file.filename or "upload"

    # Store to uploads dir
    uploads_dir = settings.data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(filename).name or "upload"
    dest = uploads_dir / f"{digest}_{safe_filename}"
    dest.write_bytes(content)

    return {
        "uri": f"digest:sha256:{digest}",
        "filename": filename,
        "size": len(content),
    }
