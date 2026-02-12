export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

function getEnv(name: string, fallback?: string) {
  const v = process.env[name]
  if (v == null || v === '') return fallback
  return v
}

function mustGetEnv(name: string): string {
  const v = getEnv(name)
  if (!v) throw new Error(`Missing ${name} env var`)
  return v
}

function asInt(name: string, fallback: number) {
  const raw = getEnv(name)
  const n = raw == null ? fallback : Number(raw)
  if (!Number.isFinite(n)) return fallback
  return Math.trunc(n)
}

function asBool(name: string, fallback = false) {
  const raw = getEnv(name)
  if (raw == null) return fallback
  return ['1', 'true', 'yes', 'on'].includes(raw.toLowerCase())
}

export type RunnerConfig = {
  apiBaseUrl: string
  adminSecret: string
  tickSeconds: number
  maxPerTick: number
  requestTimeoutMs: number
  runOnce: boolean
  healthPort: number | null
  logLevel: LogLevel

  reactionsEnabled: boolean

  secondmeApiBase: string
}

export function loadConfig(): RunnerConfig {
  const apiBaseUrl = getEnv('API_BASE_URL', 'http://localhost:4000') ?? 'http://localhost:4000'
  const adminSecret = mustGetEnv('ADMIN_SECRET')

  const tickSeconds = Math.max(1, asInt('TICK_SECONDS', 10) || 10)
  const maxPerTick = Math.max(1, asInt('MAX_PER_TICK', 3) || 3)

  const requestTimeoutMs = Math.max(1_000, asInt('REQUEST_TIMEOUT_MS', 30_000) || 30_000)
  const runOnce = asBool('RUN_ONCE', false)

  const healthPortRaw = getEnv('HEALTH_PORT')
  const healthPort = healthPortRaw ? Math.max(1, Math.min(65535, Number(healthPortRaw) || 0)) : null

  const logLevel = (getEnv('LOG_LEVEL', 'info') as LogLevel) ?? 'info'

  const reactionsEnabled = asBool('REACTIONS_ENABLED', true)

  const secondmeApiBase = getEnv('SECONDME_API_BASE', 'https://app.mindos.com/gate/lab') ?? 'https://app.mindos.com/gate/lab'

  return {
    apiBaseUrl,
    adminSecret,
    tickSeconds,
    maxPerTick,
    requestTimeoutMs,
    runOnce,
    healthPort,
    logLevel,

    reactionsEnabled,
    secondmeApiBase,
  }
}
