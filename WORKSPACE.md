AGENTS.md
Operating instructions for the agent and how it should use memory.
Loaded at the start of every session.
Good place for rules, priorities, and “how to behave” details.

SOUL.md
Persona, tone, and boundaries.
Loaded every session.

USER.md
Who the user is and how to address them.
Loaded every session.

IDENTITY.md
The agent’s name, vibe, and emoji.
Created/updated during the bootstrap ritual.

TOOLS.md
Notes about your local tools and conventions.
Does not control tool availability; it is only guidance.

HEARTBEAT.md
Optional tiny checklist for heartbeat runs.
Keep it short to avoid token burn.

BOOT.md
Optional startup checklist executed on gateway restart when internal hooks are enabled.
Keep it short; use the message tool for outbound sends.

BOOTSTRAP.md
One-time first-run ritual.
Only created for a brand-new workspace.
Delete it after the ritual is complete.

memory/canon/
The immutable canon of collected works from this human being.

memory/canon/INDEX.md
Index of all canon entries.

memory/journal/YYYY-MM-DD.md
Daily memory log (one file per day).
Recommended to read today + yesterday on session start.

MEMORY.md
Curated long-term memory with live updates.
Only load in the main, private session (not shared/group contexts).
See Memory for the workflow and automatic memory flush.
