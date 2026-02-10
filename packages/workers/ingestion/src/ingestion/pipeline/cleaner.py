from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Strip boilerplate, normalize whitespace, and tidy up extracted text."""
    # Remove common web boilerplate markers.
    patterns = [
        r"(?i)^(share|tweet|pin|email|print|subscribe|follow us|related posts?).*$",
        r"(?i)^(cookie|privacy|terms of service|copyright ©).*$",
        r"(?i)^(advertisement|sponsored|promoted).*$",
        r"(?i)^\[?\s*(menu|navigation|sidebar|footer|header)\s*\]?$",
    ]
    lines = text.splitlines()
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if any(re.match(p, stripped) for p in patterns):
            continue
        cleaned.append(line)

    result = "\n".join(cleaned)

    # Collapse runs of 3+ blank lines into 2.
    result = re.sub(r"\n{3,}", "\n\n", result)

    # Normalize non-breaking spaces and other whitespace oddities.
    result = result.replace("\u00a0", " ")
    result = re.sub(r"[ \t]+\n", "\n", result)  # trailing spaces

    return result.strip()
