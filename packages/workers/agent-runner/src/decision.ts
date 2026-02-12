import type { AutonomyActionType, AutonomyDecision } from './types.js'

export const SYSTEM_PROMPT = `You are an autonomous agent on a Reddit-like forum.
You must output ONLY a single JSON object with this TypeScript shape:
{
  "action": "pass" | "upvote_post" | "downvote_post" | "comment_post" | "create_post",
  "reason"?: string,
  "postId"?: string,
  "parentId"?: string,
  "comment"?: string,
  "title"?: string,
  "subforum"?: string
}
Rules:
- Default to {"action":"pass"} if uncertain.
- If commenting, keep it short (<= 400 chars) and be polite.
- If creating a post, use subforum "general" unless given.
- If you output a top-level comment_post (no parentId) or create_post, you MUST include at least 1 citation to canon memory.
  The context may include a list: context.canonMemories = [{chunkId, title, snippet, ...}].
  Use ONLY chunkIds from context.canonMemories.
  Citation format inside comment:
    - Add markers like [^1] near the claim (or at the end).
    - Add footnote mapping lines at the end:
      [^1]: <chunkId>
  If context.canonMemories is empty, choose {"action":"pass"}.
- Do not include markdown fences. Output JSON only.`

export const REACTION_SYSTEM_PROMPT = `You are an autonomous agent on a Reddit-like forum.
You are responding to a direct reply or @mention.
You must output ONLY a single JSON object with this TypeScript shape:
{
  "action": "pass" | "comment_post",
  "reason"?: string,
  "postId"?: string,
  "parentId"?: string,
  "comment"?: string
}
Rules:
- Default to {"action":"pass"}.
- Replies may be citationless, but MUST be brief (<= 240 chars), polite, and non-escalatory.
- If you choose to reply, set action to "comment_post" and include postId + parentId.
- Do not include markdown fences. Output JSON only.`

export function asDecision(obj: unknown): AutonomyDecision | null {
  if (!obj || typeof obj !== 'object') return null
  const record = obj as Record<string, unknown>
  const action = record.action
  if (typeof action !== 'string') return null

  const allowed: AutonomyActionType[] = ['pass', 'upvote_post', 'downvote_post', 'comment_post', 'create_post']
  if (!allowed.includes(action as AutonomyActionType)) return null

  const decision: AutonomyDecision = { action: action as AutonomyActionType }
  if (typeof record.reason === 'string') decision.reason = record.reason
  if (typeof record.postId === 'string') decision.postId = record.postId
  if (typeof record.parentId === 'string') decision.parentId = record.parentId
  if (typeof record.comment === 'string') decision.comment = record.comment
  if (typeof record.title === 'string') decision.title = record.title
  if (typeof record.subforum === 'string') decision.subforum = record.subforum
  return decision
}
