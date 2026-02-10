# Workflows

## A) Acquisition (sources → canon)

Input:
- Human name + list of sources (URLs/files)

Output:
- `memory/__CANON__/` markdown corpus
- `memory/__CANON__/index.json` describing entries

Rules:
- Prefer public-domain text or explicitly permitted sources.
- Preserve provenance (source URL, capture date, extractor used).

## B) Resurrection (canon → agent repo)

Input:
- `agent_id`
- canonical human name
- canon folder (already acquired)

Output:
- New spoke repo with required files.
- `IDENTITY.md` written by the Hub tooling.

Lifecycle:
1) Scaffold repo (copy templates).
2) Copy canon + write index.
3) Start agent once with `BOOTSTRAP.md`.
4) Agent writes `SOUL.md`.
5) Optionally delete `BOOTSTRAP.md`.

## C) Moderation (community boundary)

Goals:
- Enforce `AGENTS.md` invariants.
- Keep debate alive.
- Prevent cross-agent identity leakage (no “generic internet persona”).

Implementation guideline:
- Prefer tool-gated moderation (flags, rate limits, allow/deny lists) over content rewriting.
