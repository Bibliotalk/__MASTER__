from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short_id() -> str:
    return uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceType(str, Enum):
    web = "web"
    youtube = "youtube"
    rss = "rss"
    epub = "epub"
    text = "text"


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    error = "error"


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

class Source(BaseModel):
    id: str = Field(default_factory=lambda: f"src_{_short_id()}")
    type: SourceType
    url: str
    label: str = ""


# ---------------------------------------------------------------------------
# Canon index (output artifact)
# ---------------------------------------------------------------------------

class IndexEntry(BaseModel):
    id: str
    filename: str
    title: str
    source_url: str
    source_type: SourceType
    date: str | None = None
    content_hash: str
    word_count: int
    ingested_at: datetime = Field(default_factory=_now)


class CanonIndex(BaseModel):
    agent_id: str
    created: datetime = Field(default_factory=_now)
    updated: datetime = Field(default_factory=_now)
    entries: list[IndexEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Extraction primitives (used by adapters & pipeline)
# ---------------------------------------------------------------------------

class ExtractedText(BaseModel):
    title: str
    body: str
    source_url: str
    date: str | None = None
    metadata: dict = Field(default_factory=dict)


class ToolResult(BaseModel):
    source_id: str
    texts: list[ExtractedText] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------

class JobProgress(BaseModel):
    totalSources: int = 0
    completedSources: int = 0
    currentSource: str | None = None
    chunksWritten: int = 0
    errors: list[str] = Field(default_factory=list)


class Job(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    agent_id: str
    sources: list[Source] = Field(default_factory=list)
    status: JobStatus = JobStatus.pending
    progress: JobProgress = Field(default_factory=JobProgress)
    started_at: datetime = Field(default_factory=_now)
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Request / Response helpers
# ---------------------------------------------------------------------------

class CreateJobRequest(BaseModel):
    agent_id: str
    sources: list[Source]
