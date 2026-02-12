import type { LogLevel } from './env.js'

export type Logger = {
  debug: (...args: unknown[]) => void
  info: (...args: unknown[]) => void
  warn: (...args: unknown[]) => void
  error: (...args: unknown[]) => void
}

const levels: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
}

export function createLogger(level: LogLevel): Logger {
  const min = levels[level] ?? levels.info

  function enabled(l: LogLevel) {
    return (levels[l] ?? 999) >= min
  }

  return {
    debug: (...args) => {
      if (enabled('debug')) console.log('[debug]', ...args)
    },
    info: (...args) => {
      if (enabled('info')) console.log('[info]', ...args)
    },
    warn: (...args) => {
      if (enabled('warn')) console.warn('[warn]', ...args)
    },
    error: (...args) => {
      if (enabled('error')) console.error('[error]', ...args)
    },
  }
}
