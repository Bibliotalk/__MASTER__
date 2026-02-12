export async function readLastSseJsonObject(params: {
  response: Response
  signal?: AbortSignal
  maxBytes?: number
}): Promise<unknown | null> {
  const { response, signal, maxBytes = 512_000 } = params

  if (!response.body) return null

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let total = 0
  let lastJson: unknown | null = null

  while (true) {
    if (signal?.aborted) throw new Error('Aborted')

    const { value, done } = await reader.read()
    if (done) break
    if (!value) continue

    total += value.byteLength
    if (total > maxBytes) {
      throw new Error(`SSE output exceeded ${maxBytes} bytes`)
    }

    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split(/\r?\n/)
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      const data = line.slice('data:'.length).trim()
      if (!data) continue
      if (data === '[DONE]') return lastJson

      try {
        lastJson = JSON.parse(data)
      } catch {
        // ignore non-JSON chunks
      }
    }
  }

  return lastJson
}
