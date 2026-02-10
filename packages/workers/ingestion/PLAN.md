# Ingestion Worker — Implementation Plan

Standalone Python FastAPI service that orchestrates the Canon acquisition workflow through a conversational, session-based API.

---

## 1. Workflow Overview

```
User: "Steve Jobs"
  │
  ▼
AI suggests source URLs (blogs, YouTube, RSS, ebooks, web files)
User adds/removes/confirms sources
  │
  ▼
AI produces an ingestion plan (which tool for each source, output structure)
User confirms or edits the plan
  │
  ▼
AI generates a program and executes it automatically
Worker streams progress via SSE
Outputs canonical **Markdown** files + index.json
```

The same workflow supports **adding sources to an existing canon** — the worker loads the existing `index.json`, deduplicates against it, and appends new entries.

---

## 2. Session Model

Each ingestion job is a **session** that progresses through stages:

```
INIT → SOURCES → PLAN → EXECUTING → DONE
                  ↑
                  └──  (user can loop back to edit)
```

Session state is persisted to disk (`data/sessions/{session_id}.json`) so the server can restart without losing progress.

### Session Schema

```jsonc
{
  "id": "uuid",
  "name": "Steve Jobs",                     // human being's name
  "canon_path": null,                       // path to existing canon dir, or null for new
  "stage": "SOURCES",
  "sources": [
    {
      "id": "src_1",
      "type": "web",                        // web | youtube | rss | file
      "url": "https://stevejobsarchive.com",
      "label": "Steve Jobs Archive"
    }
  ],
  "plan": "",                               // written at PLAN stage
  "program": "",                            // generated Python script
  "existing_index": {},                     // loaded from existing canon for dedup
  "log": []                                 // execution log lines
}
```

---

## 3. API Endpoints

All endpoints are under `/api/v1/ingestion`.

| Method  | Path                             | Description                                            |
| ------- | -------------------------------- | ------------------------------------------------------ |
| `POST`  | `/sessions`                      | Create session. Body: `{ name }`                       |
| `GET`   | `/sessions/{id}`                 | Get session state                                      |
| `GET`   | `/sessions/{id}/sources/suggest` | AI suggests sources for the name. Returns suggestions. |
| `POST`  | `/sessions/{id}/sources`         | Submit/update source list. Body: `{ sources: [...] }`  |
| `GET`   | `/sessions/{id}/plan`            | AI generates ingestion plan from confirmed sources     |
| `PATCH` | `/sessions/{id}/plan`            | User edits the plan                                    |
| `POST`  | `/sessions/{id}/plan/confirm`    | Confirm plan → AI generates program and executes it    |
| `GET`   | `/sessions/{id}/execute/stream`  | SSE stream of execution progress                       |
| `GET`   | `/sessions/{id}/output`          | List generated canon files                             |

---

## 4. Tool Adapters

Each adapter wraps an external tool behind a uniform interface:

```python
class ToolResult:
    source_id: str
    texts: list[ExtractedText]     # title, body, metadata, source_url
    errors: list[str]

class ExtractedText:
    title: str
    body: str                      # raw markdown
    source_url: str
    date: str | None
    metadata: dict
```

### 4.1 Adapters

| Adapter          | Wraps                        | Source Type | Notes                                     |
| ---------------- | ---------------------------- | ----------- | ----------------------------------------- |
| `CrawlerAdapter` | `crawl4ai`                   | `web`       | Crawls site, returns pages as Markdown    |
| `YouTubeAdapter` | `yt-dlp`                     | `youtube`   | Extracts transcript only (no video)       |
| `RSSAdapter`     | `feedparser` + `trafilatura` | `rss`       | Parses feed, fetches full text of entries |
| `DocAdapter`     | `markitdown`                 | `file`      | Extracts chapters as Markdown             |

### 4.2 Post-Processing Pipeline

Every adapter's output flows through:

1. **TextCleaner** — strip boilerplate, nav, ads, normalize whitespace
2. **TextSplitter** — split long documents into logical sections (by heading or special characters)
3. **CanonFormatter** — produce final `YYYY-title-slug.md` files with YAML frontmatter (long document split into multiple files with suffixes)
4. **Deduplicator** — skip entries whose `content_hash` or `source_url` already exist in `index.json`

---

## 5. AI Integration

The service calls an LLM (via OpenAI-compatible API) for three tasks:

1. **Source Suggestion** — Given a person's name, suggest likely source URLs and types.
2. **Plan Generation** — Given confirmed sources, produce a step-by-step ingestion plan (tool selection, ordering, postprocessing, max pages, special handling notes).
3. **Program Generation** — Given the confirmed plan, generate a self-contained Python script that uses adapters and pipeline tools.

The LLM is called via a thin `ai_client.py` module that reads `OPENAI_BASE_URL` and `OPENAI_API_KEY` from env. Model is configurable (default: `gpt-4o-mini` or equivalent).

---

## 6. Deduplication Strategy

When `canon_path` is provided (adding to existing canon):

1. Load `{canon_path}/index.json` into `existing_index`.
2. For each new `ExtractedText`:
   - Compute `content_hash = sha256(normalize(body))`.
   - Check against existing `content_hash` set → **exact dedup**.
   - Check `source_url` against existing URLs → **source-level dedup**.
3. Only new, unique entries proceed to formatting and writing.
4. Append new entries to `index.json`.

---

## 7. Index Schema (`index.json`)

```jsonc
{
  "agent_id": "steve-jobs",
  "created": "2025-06-01T00:00:00Z",
  "updated": "2025-07-15T00:00:00Z",
  "entries": [
    {
      "id": "canon_001",
      "filename": "2005-stanford-commencement.md",
      "title": "Stanford Commencement Address",
      "source_url": "https://...",
      "source_type": "web",
      "date": "2005-06-12",
      "content_hash": "sha256:...",
      "word_count": 2300,
      "ingested_at": "2025-06-01T12:00:00Z"
    }
  ]
}
```

---

## 8. Project Structure

```
packages/workers/ingestion/
├── PLAN.md                     # this file
├── pyproject.toml              # project metadata, dependencies
├── README.md                   # (only if needed)
├── src/
│   └── ingestion/
│       ├── __init__.py
│       ├── main.py             # FastAPI app, lifespan, CORS
│       ├── config.py           # Settings via pydantic-settings
│       ├── models.py           # Pydantic schemas (Session, Source, Plan, etc.)
│       ├── session.py          # Session CRUD + persistence
│       ├── router.py           # API route handlers
│       ├── ai_client.py        # LLM calls (suggest, plan, program generation)
│       ├── prompts/            # Prompt templates
│       │   ├── suggest.md
│       │   ├── plan.md
│       │   └── program.md
│       ├── adapters/           # Tool wrappers
│       │   ├── base.py         # ToolAdapter ABC, ToolResult, ExtractedText
│       │   ├── crawler.py      # crawl4ai
│       │   ├── youtube.py      # yt-dlp
│       │   ├── rss.py          # feedparser + trafilatura
│       │   └── local_doc.py    # local document reader
│       ├── pipeline/           # Post-processing
│       │   ├── cleaner.py      # text cleaning
│       │   ├── splitter.py     # section splitting
│       │   ├── formatter.py    # canonical markdown + frontmatter
│       │   └── dedup.py        # deduplication logic
│       └── executor.py         # Script runner with streaming output
└── tests/
    ├── test_adapters.py
    ├── test_pipeline.py
    ├── test_session.py
    └── test_api.py
```

---

## 9. Dependencies

```
fastapi
uvicorn[standard]
pydantic>=2.0
pydantic-settings
httpx                           # async HTTP for AI client
openai                          # LLM calls
crawl4ai                        # web crawler
yt-dlp                          # youtube transcripts
feedparser                      # RSS parsing
trafilatura                     # article text extraction
markitdown                      # misc file → markdown
python-slugify                  # filename generation
sse-starlette                   # SSE streaming
```

---

## 10. Implementation Order

1. **Scaffold** — `pyproject.toml`, `main.py`, `config.py`, `models.py`
2. **Session management** — `session.py` (file-backed CRUD)
3. **API routes** — `router.py` (all endpoints, initially returning stubs)
4. **Adapters** — implement one at a time: `crawler` → `youtube` → `rss` → `local_doc`
5. **Pipeline** — `cleaner` → `splitter` → `formatter` → `dedup`
6. **AI client** — `ai_client.py` + prompt templates
7. **Executor** — script runner with SSE streaming
8. **Integration** — wire everything together, end-to-end test
