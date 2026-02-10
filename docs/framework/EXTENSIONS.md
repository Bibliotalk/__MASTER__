# Extensions (OpenClaw plugins)

OpenClaw discovers plugins from:
- `plugins.load.paths` (config)
- `<workspace>/.openclaw/extensions/*` (workspace extensions)
- `~/.openclaw/extensions/*` (global extensions)

In this repo, we keep platform plugins under `extensions/` and load them via `plugins.load.paths`.

## Plugin boundaries

- `extensions/acquisition/` – source ingestion and conversion into canon markdown.
- `extensions/resurrection/` – create agent repos and write identity scaffolding.
- `extensions/moderation/` – policy enforcement and safety boundary checks.

Each plugin directory must contain:
- `openclaw.plugin.json` (manifest + config schema)
- `index.ts` (plugin entrypoint)

## Tool naming conventions

- Plugin id: `bibliotalk-<capability>`
- Tools: `snake_case` (e.g., `acquire_canon`, `resurrect_agent_repo`)
- RPC methods: `pluginId.action` (e.g., `bibliotalk-resurrection.create_repo`)
