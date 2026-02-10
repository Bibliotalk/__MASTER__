You are planning the ingestion of digital texts into a canonical Markdown archive for the Bibliotalk project.

Person: {{name}}

Confirmed sources:
{{sources_json}}

Available tool adapters:
- **CrawlerAdapter** (type: web): Crawls a website, extracts text as Markdown. Good for blogs, essay collections, archived websites.
- **YouTubeAdapter** (type: youtube): Extracts transcripts from YouTube videos, playlists, or channels.
- **RSSAdapter** (type: rss): Parses RSS/Atom feeds and extracts full article text.
- **DocAdapter** (type: file): Handles uploaded documents — epub, pdf, docx, html, txt, md, and more. Converts to Markdown via markitdown.

Post-processing pipeline (applied automatically to all output):
- **TextCleaner**: Strips boilerplate, normalizes whitespace.
- **TextSplitter**: Splits long documents by heading or at ~4000 word boundaries.
- **CanonFormatter**: Produces `YYYY-title-slug.md` files with YAML frontmatter.
- **Deduplicator**: Skips entries whose content hash or source URL already exists.

{{existing_index_info}}

Write a step-by-step ingestion plan. For each source, specify:
1. Which adapter to use
2. Any special configuration or notes (max pages to crawl, language for transcripts, chapters to skip, etc.)
3. Expected output description

Keep the plan concise and actionable. Use numbered steps. Write in plain text, not code.
