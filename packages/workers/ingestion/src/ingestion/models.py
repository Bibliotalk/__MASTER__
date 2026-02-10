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


class SessionStage(str, Enum):
    INIT = "INIT"
    SOURCES = "SOURCES"
    PLAN = "PLAN"
    EXECUTING = "EXECUTING"
    DONE = "DONE"
    ERROR = "ERROR"


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
    entries: list[IndexEntry] = []


# ---------------------------------------------------------------------------
# Extraction primitives (used by adapters & pipeline)
# ---------------------------------------------------------------------------

class ExtractedText(BaseModel):
    title: str
    body: str
    source_url: str
    date: str | None = None
    metadata: dict = {}


class ToolResult(BaseModel):
    source_id: str
    texts: list[ExtractedText] = []
    errors: list[str] = []


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class Session(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    canon_path: str | None = None
    stage: SessionStage = SessionStage.INIT
    sources: list[Source] = []
    plan: str = ""
    program: str = ""
    existing_index: CanonIndex | None = None
    log: list[str] = []
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Request / Response helpers
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    name: str
    canon_path: str | None = None


class UpdateSourcesRequest(BaseModel):
    sources: list[Source]


class UpdatePlanRequest(BaseModel):
    plan: str
