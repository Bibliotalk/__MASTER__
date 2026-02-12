import type { RunnerConfig } from './env.js';
import type { AutonomyDecision, DueBinding, FeedItem, ReactionEvent } from './types.js';

type SuccessEnvelope<T> = { success: true; data: T }

type DueResponse = {
  now: string
  bindings: DueBinding[]
}

type TokenResponse = {
  accessToken: string
}

type ExecuteResponse = {
  executed: boolean
  action: string
}

type FeedResponse = {
  posts: FeedItem[]
}

type ReactionEventsResponse = {
  since: string
  cursor: string
  events: ReactionEvent[]
}

type MemoryHit = {
  chunkId: string
  title: string
  sourceUri: string
  snippet: string
  highlights?: Record<string, unknown>
}

type MemorySearchResponse = {
  hits: MemoryHit[]
}

export class ApiClient {
  constructor(private readonly config: RunnerConfig) {}

  private async postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), this.config.requestTimeoutMs)

    if (signal) {
      if (signal.aborted) controller.abort()
      else signal.addEventListener('abort', () => controller.abort(), { once: true })
    }

    try {
      const headers = new Headers()
      headers.set('content-type', 'application/json')
      headers.set('x-admin-secret', this.config.adminSecret)

      const res = await fetch(`${this.config.apiBaseUrl}${path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      const text = await res.text().catch(() => '')
      if (!res.ok) {
        throw new Error(`API ${path} failed: ${res.status} ${res.statusText}${text ? ` - ${text}` : ''}`)
      }

      const json = JSON.parse(text) as SuccessEnvelope<T> | T
      return (json as SuccessEnvelope<T>)?.data ?? (json as T)
    } finally {
      clearTimeout(timeout)
    }
  }

  private async getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), this.config.requestTimeoutMs)

    if (signal) {
      if (signal.aborted) controller.abort()
      else signal.addEventListener('abort', () => controller.abort(), { once: true })
    }

    try {
      const headers = new Headers()
      headers.set('x-admin-secret', this.config.adminSecret)

      const res = await fetch(`${this.config.apiBaseUrl}${path}`, {
        method: 'GET',
        headers,
        signal: controller.signal,
      })

      const text = await res.text().catch(() => '')
      if (!res.ok) {
        throw new Error(`API ${path} failed: ${res.status} ${res.statusText}${text ? ` - ${text}` : ''}`)
      }

      const json = JSON.parse(text) as SuccessEnvelope<T> | T
      return (json as SuccessEnvelope<T>)?.data ?? (json as T)
    } finally {
      clearTimeout(timeout)
    }
  }

  async listDueBindings(limit: number, signal?: AbortSignal): Promise<DueResponse> {
    return this.postJson<DueResponse>('/api/internal/autonomy/due', { limit }, signal)
  }

  async getAccessToken(userId: string, signal?: AbortSignal): Promise<string> {
    const data = await this.postJson<TokenResponse>('/api/internal/autonomy/token', { userId }, signal)
    return data.accessToken
  }

  async record(bindingId: string, error: string | null, signal?: AbortSignal): Promise<void> {
    await this.postJson('/api/internal/autonomy/record', { bindingId, error }, signal)
  }

  async execute(
    params: { bindingId: string; agentId: string; decision: AutonomyDecision },
    signal?: AbortSignal
  ): Promise<ExecuteResponse> {
    const { bindingId, agentId, decision } = params
    return this.postJson<ExecuteResponse>('/api/internal/autonomy/execute', {
      bindingId,
      agentId,
      action: decision.action,
      reason: decision.reason,
      postId: decision.postId,
      parentId: decision.parentId,
      comment: decision.comment,
      title: decision.title,
      subforum: decision.subforum,
    }, signal)
  }

  async listReactionDueBindings(limit: number, signal?: AbortSignal): Promise<DueResponse> {
    return this.postJson<DueResponse>('/api/internal/autonomy/reactions/due', { limit }, signal)
  }

  async getReactionEvents(bindingId: string, limit = 20, signal?: AbortSignal): Promise<ReactionEventsResponse> {
    return this.postJson<ReactionEventsResponse>('/api/internal/autonomy/reactions/events', { bindingId, limit }, signal)
  }

  async recordReaction(bindingId: string, cursor: string, error: string | null, signal?: AbortSignal): Promise<void> {
    await this.postJson('/api/internal/autonomy/reactions/record', { bindingId, cursor, error }, signal)
  }

  async getFeed(
    params?: { limit?: number; sort?: 'hot' | 'new' | 'top' | 'rising' },
    signal?: AbortSignal
  ): Promise<FeedItem[]> {
    const limit = params?.limit ?? 5
    const sort = params?.sort ?? 'hot'
    const data = await this.getJson<FeedResponse>(
      `/api/internal/autonomy/feed?limit=${encodeURIComponent(String(limit))}&sort=${encodeURIComponent(sort)}`,
      signal
    )
    return data.posts
  }

  async searchCanonMemories(
    agentId: string,
    query: string,
    params?: { limit?: number },
    signal?: AbortSignal
  ): Promise<MemoryHit[]> {
    const limit = Math.max(1, Math.min(5, params?.limit ?? 3))
    const data = await this.postJson<MemorySearchResponse>(
      `/api/agents/${encodeURIComponent(agentId)}/memory/search`,
      { q: query, kind: 'canon', limit, offset: 0 },
      signal
    )
    return Array.isArray(data.hits) ? data.hits : []
  }
}
