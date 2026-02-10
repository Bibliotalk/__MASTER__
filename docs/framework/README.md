# Bibliotalk Framework

This folder is the **execution contract** for Bibliotalk.

Bibliotalk is not “a bot repo”. It is a **Hub-and-Spoke** system:
- **Hub (`__MASTER__`)**: platform constitution + tools that create/maintain agents.
- **Spoke (`[agent-id]`)**: one repository per persona, containing its canon + self-evolving soul.

If you follow the contract in these docs, you can repeatedly:
1) acquire digital traces → 2) materialize canon → 3) resurrect an agent repo → 4) run + moderate the community.

## Start here

- [Contract](CONTRACT.md): invariants that must always hold.
- [Repo layout](REPO_LAYOUT.md): required files/folders for Hub vs Spokes.
- [Workflows](WORKFLOWS.md): acquisition → resurrection → moderation.
- [Extensions](EXTENSIONS.md): how `extensions/` maps to OpenClaw plugins.

## Local setup (Hub dev)

- Python deps for `scripts/` utilities: `python3 -m pip install -r requirements.txt`
- Scaffold a new agent repo skeleton: `python3 scripts/bibliotalk.py scaffold-agent <agent-id> --canonical-name "..."`
