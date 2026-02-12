import { loadConfig } from './env.js'
import { startHealthServer } from './health.js'
import { createLogger } from './log.js'
import { loop } from './runner.js'

const config = loadConfig()
const log = createLogger(config.logLevel)

const abort = new AbortController()
let lastError: string | null = null
let ready = false

const health = config.healthPort
  ? startHealthServer({
      port: config.healthPort,
      ready: () => ready,
      getLastError: () => lastError,
    })
  : null

function shutdown(signal: string) {
  log.info(`Shutting down (${signal})...`)
  abort.abort()
  health?.close()
}

process.on('SIGTERM', () => shutdown('SIGTERM'))
process.on('SIGINT', () => shutdown('SIGINT'))

loop(config, {
  signal: abort.signal,
  onState: (s) => {
    ready = s.ready
    lastError = s.lastError
  },
})
  .then(() => {
    // loop only returns on RUN_ONCE or abort
  })
  .catch((err) => {
    lastError = err instanceof Error ? err.message : String(err)
    console.error('Fatal runner error:', err)
    process.exit(1)
  })
