export async function sleepMs(ms: number, signal?: AbortSignal) {
  if (ms <= 0) return

  await new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms)

    function onAbort() {
      clearTimeout(t)
      reject(new Error('Aborted'))
    }

    if (signal) {
      if (signal.aborted) return onAbort()
      signal.addEventListener('abort', onAbort, { once: true })
    }
  })
}

export function jitterMs(baseMs: number, ratio = 0.2) {
  const r = Math.max(0, ratio)
  const delta = baseMs * r
  const n = (Math.random() * 2 - 1) * delta
  return Math.max(0, Math.round(baseMs + n))
}
