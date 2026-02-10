Generate a self-contained async Python script that executes the following ingestion plan.

Person: {{name}}
Output directory: {{output_dir}}

Plan:
{{plan}}

Sources:
{{sources_json}}

The script can import from these modules:

```python
from pathlib import Path
from ingestion.models import Source, SourceType, CanonIndex
from ingestion.adapters.crawler import CrawlerAdapter
from ingestion.adapters.youtube import YouTubeAdapter
from ingestion.adapters.rss import RSSAdapter
from ingestion.adapters.local_doc import DocAdapter  # handles epub, pdf, docx, txt, md, …
from ingestion.pipeline.formatter import format_and_write
from ingestion.pipeline.dedup import Deduplicator
```

{{existing_index_info}}

Requirements:
- Use `asyncio.run()` as the entry point.
- Print progress to stdout: one line per source when starting, one line per file written, and a summary at the end.
- Handle errors gracefully: print them and continue with other sources.
- Write output files to `{{output_dir}}`.
- Write/update `index.json` in `{{output_dir}}` at the end.
- Load the existing index from `{{output_dir}}/index.json` if it exists (for dedup).
- Use the adapters to extract text, then call `format_and_write()` for each extracted text.
- Initialize `Deduplicator` with the existing index if available.

Return ONLY the Python code. No markdown fences, no explanation.
