# Repository Layout

## Hub repo (`__MASTER__`) layout

Required (this repo):
- `templates/` – canonical files copied into new agent repos.
- `extensions/` – OpenClaw plugins that implement platform capabilities.
- `scripts/` – local utilities (scaffold, validate, knowledge ingestion).
- `docs/framework/` – this contract + workflows.

Optional:
- `docs/knowledge/` – internal knowledge base (OpenClaw docs snapshots, notes).
- `skills/` – Hub-specific skills for the Master Librarian.

## Spoke repo (`[agent-id]`) layout

Required (new agent repos must contain):
- `IDENTITY.md` – issued by Master Librarian.
- `SOUL.md` – produced/maintained by the agent.
- `AGENTS.md` – community guidelines (read-only).
- `BOOTSTRAP.md` – one-time ritual prompt; may be deleted after first run.
- `memory/__CANON__/` – canon markdown corpus.
- `memory/__CANON__/index.json` – canon index (source-of-truth for tooling).
- `memory/YYYY-MM-DD.md` – daily journal (append-only).

Recommended:
- `MEMORY.md` – curated long-term memory.
- `HEARTBEAT.md` – tiny recurring checklist.
- `TOOLS.md` – workspace conventions for the agent.

## Naming

- Repo name == `agent_id` (kebab-case).
- Canon files: stable, deterministic names.
- Tools: snake_case.
- Plugin ids: kebab-case.
