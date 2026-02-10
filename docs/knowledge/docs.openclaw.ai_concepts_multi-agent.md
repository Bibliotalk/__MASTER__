# Multi-Agent Routing

Goal: multiple*isolated*agents (separate workspace +

`agentDir`

+ sessions), plus multiple channel accounts (e.g. two WhatsApps) in one running Gateway. Inbound is routed to an agent via bindings.
## What is “one agent”?

An**agent**is a fully scoped brain with its own:

**Workspace**(files, AGENTS.md/SOUL.md/USER.md, local notes, persona rules).**State directory**(`agentDir`

) for auth profiles, model registry, and per-agent config.**Session store**(chat history + routing state) under`~/.openclaw/agents/<agentId>/sessions`

.

**per-agent**. Each agent reads from its own:

**not**shared automatically. Never reuse

`agentDir`

across agents (it causes auth/session collisions). If you want to share creds,
copy `auth-profiles.json`

into the other agent’s `agentDir`

.
Skills are per-agent via each workspace’s `skills/`

folder, with shared skills
available from `~/.openclaw/skills`

. See Skills: per-agent vs shared.
The Gateway can host **one agent**(default) or

**many agents**side-by-side.

**Workspace note:**each agent’s workspace is the

**default cwd**, not a hard sandbox. Relative paths resolve inside the workspace, but absolute paths can reach other host locations unless sandboxing is enabled. See Sandboxing.

## Paths (quick map)

- Config:
`~/.openclaw/openclaw.json`

(or`OPENCLAW_CONFIG_PATH`

) - State dir:
`~/.openclaw`

(or`OPENCLAW_STATE_DIR`

) - Workspace:
`~/.openclaw/workspace`

(or`~/.openclaw/workspace-<agentId>`

) - Agent dir:
`~/.openclaw/agents/<agentId>/agent`

(or`agents.list[].agentDir`

) - Sessions:
`~/.openclaw/agents/<agentId>/sessions`


### Single-agent mode (default)

If you do nothing, OpenClaw runs a single agent:`agentId`

defaults to.`main`

- Sessions are keyed as
`agent:main:<mainKey>`

. - Workspace defaults to
`~/.openclaw/workspace`

(or`~/.openclaw/workspace-<profile>`

when`OPENCLAW_PROFILE`

is set). - State defaults to
`~/.openclaw/agents/main/agent`

.

## Agent helper

Use the agent wizard to add a new isolated agent:`bindings`

(or let the wizard do it) to route inbound messages.
Verify with:
## Multiple agents = multiple people, multiple personalities

With**multiple agents**, each

`agentId`

becomes a **fully isolated persona**:

**Different phone numbers/accounts**(per channel`accountId`

).**Different personalities**(per-agent workspace files like`AGENTS.md`

and`SOUL.md`

).**Separate auth + sessions**(no cross-talk unless explicitly enabled).

**multiple people**share one Gateway server while keeping their AI “brains” and data isolated.

## One WhatsApp number, multiple people (DM split)

You can route**different WhatsApp DMs**to different agents while staying on

**one WhatsApp account**. Match on sender E.164 (like

`+15551234567`

) with `peer.kind: "direct"`

. Replies still come from the same WhatsApp number (no per‑agent sender identity).
Important detail: direct chats collapse to the agent’s **main session key**, so true isolation requires

**one agent per person**. Example:

- DM access control is
**global per WhatsApp account**(pairing/allowlist), not per agent. - For shared groups, bind the group to one agent or use Broadcast groups.

## Routing rules (how messages pick an agent)

Bindings are**deterministic**and

**most-specific wins**:

`peer`

match (exact DM/group/channel id)`guildId`

(Discord)`teamId`

(Slack)`accountId`

match for a channel- channel-level match (
`accountId: "*"`

) - fallback to default agent (
`agents.list[].default`

, else first list entry, default:`main`

)

## Multiple accounts / phone numbers

Channels that support**multiple accounts**(e.g. WhatsApp) use

`accountId`

to identify
each login. Each `accountId`

can be routed to a different agent, so one server can host
multiple phone numbers without mixing sessions.
## Concepts

`agentId`

: one “brain” (workspace, per-agent auth, per-agent session store).`accountId`

: one channel account instance (e.g. WhatsApp account`"personal"`

vs`"biz"`

).`binding`

: routes inbound messages to an`agentId`

by`(channel, accountId, peer)`

and optionally guild/team ids.- Direct chats collapse to
`agent:<agentId>:<mainKey>`

(per-agent “main”;`session.mainKey`

).

## Example: two WhatsApps → two agents

`~/.openclaw/openclaw.json`

(JSON5):
## Example: WhatsApp daily chat + Telegram deep work

Split by channel: route WhatsApp to a fast everyday agent and Telegram to an Opus agent.- If you have multiple accounts for a channel, add
`accountId`

to the binding (for example`{ channel: "whatsapp", accountId: "personal" }`

). - To route a single DM/group to Opus while keeping the rest on chat, add a
`match.peer`

binding for that peer; peer matches always win over channel-wide rules.

## Example: same channel, one peer to Opus

Keep WhatsApp on the fast agent, but route one DM to Opus:## Family agent bound to a WhatsApp group

Bind a dedicated family agent to a single WhatsApp group, with mention gating and a tighter tool policy:- Tool allow/deny lists are
**tools**, not skills. If a skill needs to run a binary, ensure`exec`

is allowed and the binary exists in the sandbox. - For stricter gating, set
`agents.list[].groupChat.mentionPatterns`

and keep group allowlists enabled for the channel.

## Per-Agent Sandbox and Tool Configuration

Starting with v2026.1.6, each agent can have its own sandbox and tool restrictions:`setupCommand`

lives under `sandbox.docker`

and runs once on container creation.
Per-agent `sandbox.docker.*`

overrides are ignored when the resolved scope is `"shared"`

.
**Benefits:**

**Security isolation**: Restrict tools for untrusted agents**Resource control**: Sandbox specific agents while keeping others on host**Flexible policies**: Different permissions per agent

`tools.elevated`

is **global**and sender-based; it is not configurable per agent. If you need per-agent boundaries, use

`agents.list[].tools`

to deny `exec`

.
For group targeting, use `agents.list[].groupChat.mentionPatterns`

so @mentions map cleanly to the intended agent.
See Multi-Agent Sandbox & Tools for detailed examples.