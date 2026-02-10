from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from . import ai_client, executor
from .config import settings
from .models import (
    CreateSessionRequest,
    Session,
    SessionStage,
    Source,
    SourceType,
    UpdatePlanRequest,
    UpdateSourcesRequest,
)
from .session import store

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id: str) -> Session:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(404, f"Session {session_id} not found")
    return session


def _uploads_dir(session_id: str) -> Path:
    d = settings.data_dir / "uploads" / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------

@router.post("/sessions", status_code=201)
async def create_session(body: CreateSessionRequest) -> Session:
    session = Session(name=body.name, canon_path=body.canon_path)
    session.stage = SessionStage.INIT
    return store.create(session)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Session:
    return _get_session(session_id)


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/sources/suggest")
async def suggest_sources(session_id: str) -> list[dict]:
    session = _get_session(session_id)
    return await ai_client.suggest_sources(session.name)


@router.post("/sessions/{session_id}/sources")
async def update_sources(
    session_id: str, body: UpdateSourcesRequest
) -> Session:
    session = _get_session(session_id)
    session.sources = body.sources
    session.stage = SessionStage.SOURCES
    return store.update(session)


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/upload")
async def upload_file(session_id: str, file: UploadFile) -> Source:
    """Accept an uploaded document and register it as a source."""
    session = _get_session(session_id)

    dest_dir = _uploads_dir(session_id)
    filename = file.filename or "upload"
    dest = dest_dir / filename

    # Write uploaded bytes to disk.
    content = await file.read()
    dest.write_bytes(content)

    # Determine source type from extension.
    suffix = Path(filename).suffix.lower()
    if suffix == ".epub":
        src_type = SourceType.epub
    else:
        src_type = SourceType.text

    source = Source(type=src_type, url=str(dest), label=filename)
    session.sources.append(source)
    if session.stage == SessionStage.INIT:
        session.stage = SessionStage.SOURCES
    store.update(session)
    return source


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/plan")
async def generate_plan(session_id: str) -> dict:
    session = _get_session(session_id)
    if not session.sources:
        raise HTTPException(400, "No sources confirmed yet")

    plan = await ai_client.generate_plan(session)
    session.plan = plan
    session.stage = SessionStage.PLAN
    store.update(session)
    return {"plan": plan}


@router.patch("/sessions/{session_id}/plan")
async def edit_plan(session_id: str, body: UpdatePlanRequest) -> Session:
    session = _get_session(session_id)
    session.plan = body.plan
    return store.update(session)


@router.post("/sessions/{session_id}/plan/confirm")
async def confirm_plan(session_id: str) -> dict:
    """Confirm the plan and start execution directly."""
    session = _get_session(session_id)
    if not session.plan:
        raise HTTPException(400, "No plan to confirm")

    session.stage = SessionStage.EXECUTING
    store.update(session)

    # Launch execution in the background — no codegen, just run adapters.
    asyncio.create_task(executor.execute(session.id))

    return {"status": "executing", "session_id": session.id}


# ---------------------------------------------------------------------------
# Execution stream
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/execute/stream")
async def execution_stream(session_id: str) -> EventSourceResponse:
    session = _get_session(session_id)

    async def _event_generator() -> AsyncIterator[dict]:
        # If execution is already finished, replay the log.
        if session.stage in (SessionStage.DONE, SessionStage.ERROR):
            for line in session.log:
                yield {"data": line}
            yield {"data": f"[{session.stage.value}]"}
            return

        # Wait briefly for the stream queue to appear.
        queue = None
        for _ in range(50):
            queue = executor.get_stream(session_id)
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
# Output
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/output")
async def list_output(session_id: str) -> dict:
    output_dir = settings.output_dir / session_id
    if not output_dir.exists():
        return {"files": []}

    files = sorted(
        [
            {"filename": f.name, "size": f.stat().st_size}
            for f in output_dir.iterdir()
            if f.is_file()
        ],
        key=lambda x: x["filename"],
    )
    return {"files": files}
