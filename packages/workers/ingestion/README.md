# Bibliotalk Ingestion Worker

A FastAPI service that orchestrates the acquisition of digital texts into canonical Markdown archives for the Bibliotalk multi-agent platform.

## Overview

The ingestion worker automates the workflow of acquiring, processing, and archiving texts from diverse sources:

- **Web crawling** (blogs, essay collections)
- **YouTube transcripts** (videos, playlists, channels)
- **RSS feeds** (full-text article extraction)
- **Document uploads** (EPUB, PDF, DOCX, TXT, MD, HTML, etc.)

Each source is processed through a unified pipeline:

```
Source → Extract → Clean → Split → Format → Deduplicate → Canon
```

Output is a canonical archive with:
- Individual Markdown files with YAML frontmatter
- `index.json` tracking all entries (title, source, date, content hash, word count)
- Automatic deduplication by content hash and source URL

## Quick Start

### 1. Install

```bash
cd packages/workers/ingestion
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your OpenAI API key:
#   OPENAI_API_KEY=sk-...
#   OPENAI_MODEL=gpt-4o-mini  # or your preferred model
```

### 3. Run Server

```bash
python -m ingestion.main
# Server starts at http://localhost:8000
```

### 4. Run TUI (in another terminal)

```bash
python tui.py
```

The TUI guides you through a 6-step workflow:

1. **Create session** — enter a person's name
2. **Source suggestions** — AI suggests URLs; you pick, add, or upload
3. **Confirm sources** — finalize the list
4. **Generate plan** — AI plans which adapter + configuration per source
5. **Execute** — AI generates a program and runs it, streaming progress
6. **Output** — view generated canon files

## API

All endpoints are under `/api/v1/ingestion`.

### Sessions

| Endpoint         | Method | Description                    |
| ---------------- | ------ | ------------------------------ |
| `/sessions`      | `POST` | Create a new ingestion session |
| `/sessions/{id}` | `GET`  | Get session state and progress |

### Sources

| Endpoint                         | Method | Description                               |
| -------------------------------- | ------ | ----------------------------------------- |
| `/sessions/{id}/sources/suggest` | `GET`  | AI suggests sources for the person's name |
| `/sessions/{id}/sources`         | `POST` | Submit confirmed sources                  |
| `/sessions/{id}/upload`          | `POST` | Upload a local document file              |

### Plan & Execution

| Endpoint                        | Method  | Description                                      |
| ------------------------------- | ------- | ------------------------------------------------ |
| `/sessions/{id}/plan`           | `GET`   | Generate an ingestion plan from sources          |
| `/sessions/{id}/plan`           | `PATCH` | Edit the plan                                    |
| `/sessions/{id}/plan/confirm`   | `POST`  | Confirm plan → auto-generate program and execute |
| `/sessions/{id}/execute/stream` | `GET`   | SSE stream of execution progress (real-time)     |
| `/sessions/{id}/output`         | `GET`   | List generated canon files                       |

### Example Workflow (cURL)

```bash
# 1. Create session
curl -X POST http://localhost:8000/api/v1/ingestion/sessions \
  -H "Content-Type: application/json" \
  -d '{"name":"Steve Jobs"}'
# Response: {"id":"abc123", "name":"Steve Jobs", "stage":"INIT", ...}

# 2. Get AI suggestions
curl http://localhost:8000/api/v1/ingestion/sessions/abc123/sources/suggest
# Response: [{"type":"web","url":"https://...", "label":"..."}, ...]

# 3. Submit sources
curl -X POST http://localhost:8000/api/v1/ingestion/sessions/abc123/sources \
  -H "Content-Type: application/json" \
  -d '{"sources":[{"type":"web","url":"https://example.com","label":"Blog"}]}'

# 4. Generate plan
curl http://localhost:8000/api/v1/ingestion/sessions/abc123/plan

# 5. Confirm & execute
curl -X POST http://localhost:8000/api/v1/ingestion/sessions/abc123/plan/confirm

# 6. Stream execution
curl http://localhost:8000/api/v1/ingestion/sessions/abc123/execute/stream

# 7. List output
curl http://localhost:8000/api/v1/ingestion/sessions/abc123/output
```

## Configuration

Environment variables (via `.env` or shell):

| Variable               | Default                     | Description                                     |
| ---------------------- | --------------------------- | ----------------------------------------------- |
| `OPENAI_API_KEY`       | (required)                  | Your OpenAI API key                             |
| `OPENAI_MODEL`         | `gpt-4o-mini`               | LLM model for planning & code generation        |
| `OPENAI_BASE_URL`      | `https://api.openai.com/v1` | LLM API endpoint (supports compatible services) |
| `INGESTION_DATA_DIR`   | `data`                      | Where sessions and uploads are stored           |
| `INGESTION_OUTPUT_DIR` | `output`                    | Where canon archives are written                |
| `INGESTION_HOST`       | `0.0.0.0`                   | Server host                                     |
| `INGESTION_PORT`       | `8000`                      | Server port                                     |

## Architecture

### Adapters

Each source type is handled by an adapter:

- **CrawlerAdapter** (`crawl4ai`) — Web crawling
- **YouTubeAdapter** (`yt-dlp`) — YouTube transcripts
- **RSSAdapter** (`feedparser` + `trafilatura`) — RSS feeds
- **DocAdapter** (`markitdown`) — Uploaded documents

### Pipeline

Post-processing applied to all extracted text:

1. **TextCleaner** — Strip boilerplate, normalize whitespace
2. **TextSplitter** — Split long docs by heading or at ~4000 word boundaries
3. **CanonFormatter** — Produce `YYYY-title-slug.md` files with YAML frontmatter
4. **Deduplicator** — Skip entries with duplicate content hash or source URL

### AI Integration

The service calls an LLM for:

1. **Source Suggestion** — Given a name, suggest likely URLs
2. **Plan Generation** — Choose adapters and configurations per source
3. **Program Generation** — Generate a Python script that executes the plan

The generated program imports adapters and pipeline modules, then runs in an isolated subprocess.

### Session Lifecycle

```
INIT
  ↓
SOURCES (sources list confirmed)
  ↓
PLAN (ingestion plan generated)
  ↓
EXECUTING (program running)
  ↓
DONE or ERROR (completion)
```

Session state is persisted to `data/sessions/{session_id}.json` — the server can restart without losing progress.

## Output

Canon files are written to `output/{session_id}/__CANON__/` with structure:

```
__CANON__/
├── index.json                    # Master index
├── 2025-stanford-commencement.md # YYYY-title-slug.md
├── 2024-interview.md
└── ...
```

Each file has YAML frontmatter:

```yaml
---
title: "Stanford Commencement Address"
source_url: "https://..."
source_type: "web"
date: "2025-06-15"
---

# Document body in Markdown
...
```

### Index Schema

```json
{
  "agent_id": "steve-jobs",
  "created": "2025-06-01T00:00:00Z",
  "updated": "2025-07-15T00:00:00Z",
  "entries": [
    {
      "id": "canon_0001",
      "filename": "2025-stanford-commencement.md",
      "title": "Stanford Commencement Address",
      "source_url": "https://example.com",
      "source_type": "web",
      "date": "2025-06-15",
      "content_hash": "sha256:...",
      "word_count": 2300,
      "ingested_at": "2025-06-01T12:00:00Z"
    }
  ]
}
```

## Adding to Existing Canon

Pass `canon_path` when creating a session:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Steve Jobs",
    "canon_path":"/path/to/existing/__CANON__"
  }'
```

The worker will:
1. Load the existing `index.json`
2. Initialize deduplicator with existing content hashes and source URLs
3. Skip any new entries that are duplicates
4. Append only new, unique entries to `index.json`

## Development

### Project Structure

```
src/ingestion/
├── main.py          # FastAPI app entrypoint
├── config.py        # Settings (env vars)
├── models.py        # Pydantic schemas
├── session.py       # Session CRUD
├── router.py        # API endpoints
├── ai_client.py     # LLM calls
├── executor.py      # Subprocess runner with SSE
├── adapters/        # Tool adapters
├── pipeline/        # Post-processing pipeline
└── prompts/         # LLM prompt templates
```

### Testing Locally

```bash
# Terminal 1
python -m ingestion.main

# Terminal 2
python tui.py
```

Or use curl/Postman to call the API directly.

## Limitations & Future Work

- Adapters are synchronous internally (wrapped in `asyncio.to_thread`)
- No persistent job queue; execution happens in-process
- No authentication or authorization
- No rate limiting on API endpoints
- YouTube adapter requires `yt-dlp` and may hit rate limits
- Document splitting is basic (heading/word-count based)

## License

Part of the Bibliotalk project.
