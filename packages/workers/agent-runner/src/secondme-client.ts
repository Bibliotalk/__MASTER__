import type { RunnerConfig } from './env.js'

export type ActRequest = {
  message: string
  actionControl?: string
  sessionId?: string
  systemPrompt?: string
}

export class SecondMeClient {
  constructor(private readonly config: RunnerConfig) {}

  async actStream(accessToken: string, body: ActRequest, options?: { signal?: AbortSignal }): Promise<Response> {
    const url = `${this.config.secondmeApiBase}/api/secondme/act/stream`
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(body),
      signal: options?.signal,
    })

    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`SecondMe Act error (${res.status}): ${text || res.statusText}`)
    }

    return res
  }
}
