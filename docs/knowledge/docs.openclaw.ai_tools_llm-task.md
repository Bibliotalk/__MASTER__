# LLM Task

`llm-task`

is an **optional plugin tool**that runs a JSON-only LLM task and returns structured output (optionally validated against JSON Schema). This is ideal for workflow engines like Lobster: you can add a single LLM step without writing custom OpenClaw code for each workflow.

## Enable the plugin

- Enable the plugin:

- Allowlist the tool (it is registered with
`optional: true`

):

## Config (optional)

`allowedModels`

is an allowlist of `provider/model`

strings. If set, any request
outside the list is rejected.
## Tool parameters

`prompt`

(string, required)`input`

(any, optional)`schema`

(object, optional JSON Schema)`provider`

(string, optional)`model`

(string, optional)`authProfileId`

(string, optional)`temperature`

(number, optional)`maxTokens`

(number, optional)`timeoutMs`

(number, optional)

## Output

Returns`details.json`

containing the parsed JSON (and validates against
`schema`

when provided).
## Example: Lobster workflow step

## Safety notes

- The tool is
**JSON-only**and instructs the model to output only JSON (no code fences, no commentary). - No tools are exposed to the model for this run.
- Treat output as untrusted unless you validate with
`schema`

. - Put approvals before any side-effecting step (send, post, exec).
