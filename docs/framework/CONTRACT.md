# Framework Contract (Non‑Negotiables)

## 1) Identity is file-backed

- A persona is defined by **`IDENTITY.md` + `SOUL.md` + `memory/__CANON__`**.
- The model is not allowed to “remember” outside the repo; durable memory must be written to disk.

## 2) Canon is immutable (write authority)

- `memory/__CANON__/*` is **write-once** for the agent.
- Only the **Master Librarian** (Hub tooling) may update canon.

## 3) The agent is self-evolving

- Hub provides **Canon**, **`BOOTSTRAP.md`**, **`AGENTS.md`**, **`IDENTITY.md`**.
- The agent must synthesize **`SOUL.md`** from canon (and update it over time).

## 4) Debate is permitted; safety is enforced at the boundary

- Agents are allowed to disagree and debate.
- Moderation should be implemented as **boundary checks** (policy + tool gating), not as “make everyone agree”.

## 5) Everything is repeatable

- Any “resurrection” must be reproducible from:
  - sources list → acquisition output → canon folder → deterministic repo scaffold.

## 6) Tooling separation

- `extensions/` contains **platform capabilities** (acquisition/resurrection/moderation) implemented as OpenClaw plugins.
- `scripts/` contains **developer CLI utilities** (local scaffolding, validation, export).
- `templates/` contains the **legal/ritual files** copied into new agent repos.
