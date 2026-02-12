import { ApiClient } from './api-client.js'
import { REACTION_SYSTEM_PROMPT, SYSTEM_PROMPT, asDecision } from './decision.js'
import type { RunnerConfig } from './env.js'
import { createLogger } from './log.js'
import { SecondMeClient } from './secondme-client.js'
import { jitterMs, sleepMs } from './sleep.js'
import { readLastSseJsonObject } from './sse-json.js'
import type { AutonomyDecision, DueBinding, ReactionEvent } from './types.js'

export type TickStats = {
  skipped: boolean
  processed: number
  errors: number
}

export async function runOnce(config: RunnerConfig, options?: { signal?: AbortSignal }): Promise<TickStats> {
  const log = createLogger(config.logLevel)

  const signal = options?.signal

  const api = new ApiClient(config)
  const secondme = new SecondMeClient(config)

  const due = await api.listDueBindings(config.maxPerTick, signal)
  if (due.bindings.length === 0) {
    return { skipped: false, processed: 0, errors: 0 }
  }

  let processed = 0
  let errors = 0

  const feed = await api.getFeed({ limit: 5, sort: 'hot' }, signal)

  for (const binding of due.bindings) {
    processed += 1

    try {
      const decision = await decide({ config, api, secondme, binding, feed, signal })
      await api.execute({ bindingId: binding.bindingId, agentId: binding.agent.id, decision }, signal)

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
      await api.record(binding.bindingId, message, signal).catch(() => {})
    }
  }

  return { skipped: false, processed, errors }
}

async function runReactionsOnce(config: RunnerConfig, options?: { signal?: AbortSignal }) {
  const log = createLogger(config.logLevel)
  const signal = options?.signal

  const api = new ApiClient(config)
  const secondme = new SecondMeClient(config)

  const due = await api.listReactionDueBindings(config.maxPerTick, signal)
  if (due.bindings.length === 0) return { processed: 0, errors: 0 }

  let processed = 0
  let errors = 0

  for (const binding of due.bindings) {
    processed += 1

    try {
      const { cursor, events } = await api.getReactionEvents(binding.bindingId, 20, signal)

      if (!events.length) {
        await api.recordReaction(binding.bindingId, cursor, null, signal)
        continue
      }

      const chosen = events[events.length - 1]
      const decision = await decideReaction({ config, api, secondme, binding, event: chosen, signal })

      if (decision.action === 'comment_post') {
        // Enforce correct routing to the chosen event.
        decision.postId = chosen.postId
        decision.parentId = chosen.commentId
      }

      await api.execute({ bindingId: binding.bindingId, agentId: binding.agent.id, decision }, signal)
      await api.recordReaction(binding.bindingId, cursor, null, signal)

      log.info('Reaction handled', {
        agent: binding.agent.name,
        bindingId: binding.bindingId,
        type: chosen.type,
        action: decision.action,
        postId: chosen.postId,
        parentId: chosen.commentId,
      })
    } catch (err) {
      errors += 1
      const message = err instanceof Error ? err.message : String(err)
      log.warn('Reaction error', { agent: binding.agent.name, bindingId: binding.bindingId, error: message })
      // Best-effort: do not advance cursor on error.
      await api.recordReaction(binding.bindingId, new Date().toISOString(), message, signal).catch(() => {})
    }
  }

  return { processed, errors }
}

async function decide(params: {
  config: RunnerConfig
  api: ApiClient
  secondme: SecondMeClient
  binding: DueBinding
  feed: unknown
  signal?: AbortSignal
}): Promise<AutonomyDecision> {
  const { config, api, secondme, binding, feed, signal } = params

  const accessToken = await api.getAccessToken(binding.user.id, signal)

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

  if (signal) {
    if (signal.aborted) controller.abort()
    else signal.addEventListener('abort', () => controller.abort(), { once: true })
  }

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

async function decideReaction(params: {
  config: RunnerConfig
  api: ApiClient
  secondme: SecondMeClient
  binding: DueBinding
  event: ReactionEvent
  signal?: AbortSignal
}): Promise<AutonomyDecision> {
  const { config, api, secondme, binding, event, signal } = params

  const accessToken = await api.getAccessToken(binding.user.id, signal)

  const context = {
    agent: {
      id: binding.agent.id,
      name: binding.agent.name,
      displayName: binding.agent.displayName,
      description: binding.agent.description,
    },
    event,
  }

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), Math.max(1_000, config.requestTimeoutMs - 2_000))

  if (signal) {
    if (signal.aborted) controller.abort()
    else signal.addEventListener('abort', () => controller.abort(), { once: true })
  }

  try {
    const response = await secondme.actStream(
      accessToken,
      {
        message: JSON.stringify({
          instruction: 'Decide whether to reply. If replying, produce a brief reply.' ,
          context,
        }),
        systemPrompt: REACTION_SYSTEM_PROMPT,
      },
      { signal: controller.signal }
    )

    const raw = await readLastSseJsonObject({ response, signal: controller.signal })
    const decision = asDecision(raw) ?? { action: 'pass' }

    if (decision.action !== 'comment_post') return { action: 'pass', reason: decision.reason }
    const comment = (decision.comment ?? '').trim().slice(0, 240)
    if (!comment) return { action: 'pass', reason: 'Empty reply' }

    return { action: 'comment_post', comment }
  } finally {
    clearTimeout(timeout)
  }
}

export async function loop(
  config: RunnerConfig,
  options?: { signal?: AbortSignal; onState?: (s: { ready: boolean; lastError: string | null }) => void }
) {
  const log = createLogger(config.logLevel)
  const signal = options?.signal
  const onState = options?.onState

  let lastError: string | null = null
  let ready = false

  let backoffMs = 0

  onState?.({ ready, lastError })

  log.info(`Agent runner started (api=${config.apiBaseUrl}, tick=${config.tickSeconds}s, maxPerTick=${config.maxPerTick})`)

  while (true) {
    if (signal?.aborted) throw new Error('Aborted')

    try {
      if (config.reactionsEnabled) {
        await runReactionsOnce(config, { signal })
      }

      const result = await runOnce(config, { signal })
      ready = true
      lastError = null
      backoffMs = 0

      onState?.({ ready, lastError })

      if (result.processed > 0) log.info('Tick result', result)
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      lastError = message
      ready = false

      onState?.({ ready, lastError })

      backoffMs = Math.min(60_000, Math.max(1_000, backoffMs ? Math.round(backoffMs * 1.8) : 1_000))
      log.warn('Tick failed', { error: message, backoffMs })
      await sleepMs(jitterMs(backoffMs, 0.25), signal).catch(() => {})
    }

    if (config.runOnce) break

    await sleepMs(jitterMs(config.tickSeconds * 1000, 0.1), signal)
  }
}
