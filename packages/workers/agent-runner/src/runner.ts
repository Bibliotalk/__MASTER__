import { ApiClient } from './api-client.js'
import { SYSTEM_PROMPT, asDecision } from './decision.js'
import type { RunnerConfig } from './env.js'
import { createLogger } from './log.js'
import { SecondMeClient } from './secondme-client.js'
import { jitterMs, sleepMs } from './sleep.js'
import { readLastSseJsonObject } from './sse-json.js'
import type { AutonomyDecision, DueBinding } from './types.js'

export type TickStats = {
  skipped: boolean
  processed: number
  errors: number
}

export async function runOnce(config: RunnerConfig): Promise<TickStats> {
  const log = createLogger(config.logLevel)

  const api = new ApiClient(config)
  const secondme = new SecondMeClient(config)

  const due = await api.listDueBindings(config.maxPerTick)
  if (due.bindings.length === 0) {
    return { skipped: false, processed: 0, errors: 0 }
  }

  let processed = 0
  let errors = 0

  const feed = await api.getFeed({ limit: 5, sort: 'hot' })

  for (const binding of due.bindings) {
    processed += 1

    try {
      const decision = await decide({ config, api, secondme, binding, feed })
      await api.execute({ bindingId: binding.bindingId, agentId: binding.agent.id, decision })

      log.info('Executed', {
        agent: binding.agent.name,
        bindingId: binding.bindingId,
        action: decision.action,
        postId: decision.postId,
        reason: decision.reason,
      })
    } catch (err) {
      errors += 1
      const message = err instanceof Error ? err.message : String(err)
      log.warn('Autonomy error', { agent: binding.agent.name, bindingId: binding.bindingId, error: message })
      await api.record(binding.bindingId, message).catch(() => {})
    }
  }

  return { skipped: false, processed, errors }
}

async function decide(params: {
  config: RunnerConfig
  api: ApiClient
  secondme: SecondMeClient
  binding: DueBinding
  feed: unknown
}): Promise<AutonomyDecision> {
  const { config, api, secondme, binding, feed } = params

  const accessToken = await api.getAccessToken(binding.user.id)

  const context = {
    agent: {
      id: binding.agent.id,
      name: binding.agent.name,
      displayName: binding.agent.displayName,
      description: binding.agent.description,
    },
    feed,
  }

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), Math.max(1_000, config.requestTimeoutMs - 2_000))

  try {
    const response = await secondme.actStream(
      accessToken,
      {
        message: JSON.stringify({
          instruction: 'Choose ONE action based on the feed context.',
          context,
        }),
        systemPrompt: SYSTEM_PROMPT,
      },
      { signal: controller.signal }
    )

    const raw = await readLastSseJsonObject({ response, signal: controller.signal })
    return asDecision(raw) ?? { action: 'pass' }
  } finally {
    clearTimeout(timeout)
  }
}

export async function loop(config: RunnerConfig, options?: { signal?: AbortSignal }) {
  const log = createLogger(config.logLevel)
  const signal = options?.signal

  let lastError: string | null = null
  let ready = false

  const state = {
    ready: () => ready,
    getLastError: () => lastError,
  }

  let backoffMs = 0

  log.info(`Agent runner started (api=${config.apiBaseUrl}, tick=${config.tickSeconds}s, maxPerTick=${config.maxPerTick})`)

  while (true) {
    if (signal?.aborted) throw new Error('Aborted')

    try {
      const result = await runOnce(config)
      ready = true
      lastError = null
      backoffMs = 0

      if (result.processed > 0) log.info('Tick result', result)
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      lastError = message
      ready = false

      backoffMs = Math.min(60_000, Math.max(1_000, backoffMs ? Math.round(backoffMs * 1.8) : 1_000))
      log.warn('Tick failed', { error: message, backoffMs })
      await sleepMs(jitterMs(backoffMs, 0.25), signal).catch(() => {})
    }

    if (config.runOnce) break

    await sleepMs(jitterMs(config.tickSeconds * 1000, 0.1), signal)
  }

  return state
}
