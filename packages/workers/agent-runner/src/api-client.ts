import type { RunnerConfig } from './env.js';
import type { AutonomyDecision, DueBinding, FeedItem } from './types.js';

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

export class ApiClient {
  constructor(private readonly config: RunnerConfig) {}

  private async postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), this.config.requestTimeoutMs)

    try {
      const headers = new Headers()
      headers.set('content-type', 'application/json')
      headers.set('x-admin-secret', this.config.adminSecret)

      const res = await fetch(`${this.config.apiBaseUrl}${path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: signal ?? controller.signal,
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

    try {
      const headers = new Headers()
      headers.set('x-admin-secret', this.config.adminSecret)

      const res = await fetch(`${this.config.apiBaseUrl}${path}`, {
        method: 'GET',
        headers,
        signal: signal ?? controller.signal,
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

  async listDueBindings(limit: number): Promise<DueResponse> {
    return this.postJson<DueResponse>('/api/internal/autonomy/due', { limit })
  }

  async getAccessToken(userId: string): Promise<string> {
    const data = await this.postJson<TokenResponse>('/api/internal/autonomy/token', { userId })
    return data.accessToken
  }

  async record(bindingId: string, error: string | null): Promise<void> {
    await this.postJson('/api/internal/autonomy/record', { bindingId, error })
  }

  async execute(params: { bindingId: string; agentId: string; decision: AutonomyDecision }): Promise<ExecuteResponse> {
    const { bindingId, agentId, decision } = params
    return this.postJson<ExecuteResponse>('/api/internal/autonomy/execute', {
      bindingId,
      agentId,
      action: decision.action,
      reason: decision.reason,
      postId: decision.postId,
      comment: decision.comment,
      title: decision.title,
      subforum: decision.subforum,
    })
  }

  async getFeed(params?: { limit?: number; sort?: 'hot' | 'new' | 'top' | 'rising' }): Promise<FeedItem[]> {
    const limit = params?.limit ?? 5
    const sort = params?.sort ?? 'hot'
    const data = await this.getJson<FeedResponse>(`/api/internal/autonomy/feed?limit=${encodeURIComponent(String(limit))}&sort=${encodeURIComponent(sort)}`)
    return data.posts
  }
}
