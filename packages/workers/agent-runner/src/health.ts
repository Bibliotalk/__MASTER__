import http from 'node:http'

export function startHealthServer(params: {
  port: number
  ready: () => boolean
  getLastError: () => string | null
}) {
  const server = http.createServer((req, res) => {
    const url = req.url ?? '/'

    if (url.startsWith('/healthz')) {
      res.statusCode = 200
      res.setHeader('content-type', 'application/json')
      res.end(JSON.stringify({ ok: true }))
      return
    }

    if (url.startsWith('/readyz')) {
      const ok = params.ready()
      res.statusCode = ok ? 200 : 503
      res.setHeader('content-type', 'application/json')
      res.end(JSON.stringify({ ok, lastError: params.getLastError() }))
      return
    }

    res.statusCode = 404
    res.end('Not found')
  })

  server.listen(params.port)

  return {
    close: () => {
      server.close()
    },
  }
}
