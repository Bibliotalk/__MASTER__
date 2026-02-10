#!/usr/bin/env python3

import os
import re
import sys
from urllib.parse import urlparse

import requests
import trafilatura

OUTPUT_DIR = "docs/knowledge"


def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    base = f"{parsed.netloc}{parsed.path}".strip("/")
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return base or "document"


def download_html(url: str) -> str:
    resp = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        },
    )
    resp.raise_for_status()
    return resp.text


def fetch_and_save(url: str) -> None:
    html = download_html(url)

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        include_links=False,
        output_format="markdown",
    )

    if not text:
        raise RuntimeError("Failed to extract main content")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename = sanitize_filename(url) + ".md"
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved content to {path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python add-to-kb.py <url>", file=sys.stderr)
        sys.exit(1)

    fetch_and_save(sys.argv[1])


if __name__ == "__main__":
    main()