# Production deployment (Vercel Web + Railway API + Turso)

This runbook deploys:

- Web: Vercel (Next.js)
- API (+ in-process autonomy runner): Railway (Node)
- DB: Turso (LibSQL)

Ingestion is omitted for now.

---

## 1) Create the Turso database

1. Create a new Turso database.
2. Get:
   - `DATABASE_URL` (LibSQL URL)
   - `DATABASE_AUTH_TOKEN` (token)

The API supports passing the token separately via `DATABASE_AUTH_TOKEN` (recommended).

---

## 2) Deploy API on Railway

### 2.1 Create the service

- Create a Railway project.
- Add a service from your GitHub repo.
- Set **Root Directory** to `packages/api`.

### 2.2 Build & start commands

Use:

- Build: `yarn build`
- Start: `yarn start`

Notes:
- `yarn build` runs `prisma generate && tsc`.
- `postinstall` also runs `prisma generate` for safety.

### 2.3 Environment variables (API)

Required (production):

- `NODE_ENV=production`
- `PORT` (Railway provides this automatically)
- `FRONTEND_URL=https://<your-vercel-domain>`
- `SESSION_SECRET=<random-long-secret>`
- `ADMIN_SECRET=<random-long-secret>`

Database:

- `DATABASE_URL=<your-turso-libsql-url>`
- `DATABASE_AUTH_TOKEN=<your-turso-token>`

SecondMe:

- `SECONDME_CLIENT_ID=...`
- `SECONDME_CLIENT_SECRET=...`
- `SECONDME_REDIRECT_URI=https://<your-vercel-domain>/api/auth/callback`
- `SECONDME_API_BASE=https://app.mindos.com/gate/lab` (default)
- `SECONDME_OAUTH_URL=https://go.second.me/oauth/` (default)

Meilisearch (if you’re using memory/citations):

- `MEILISEARCH_HOST=...`
- `MEILISEARCH_API_KEY=...`

Autonomy (optional):

- `AUTONOMY_ENABLED=true|false`
- `AUTONOMY_TICK_SECONDS=10` (or higher in prod)
- `AUTONOMY_MAX_PER_TICK=3`
- `AUTONOMY_DRY_RUN=true|false`

Ingestion (omitted):

- Leave `INGESTION_WORKER_URL` unset (defaults to `http://localhost:8000`), or set it to a placeholder.

### 2.4 Run database migrations

Railway doesn’t automatically run Prisma migrations.

After the service is deployed and env vars are set, run a one-off command in the Railway service shell:

- `yarn db:migrate:deploy`

(You can re-run safely on subsequent deploys.)

### 2.5 Verify API health

- `GET /api/health` on your Railway domain.
- If autonomy is enabled, you can manually trigger one tick (admin-only):
  - `POST /api/internal/autonomy/tick` with header `x-admin-secret: <ADMIN_SECRET>`

---

## 3) Deploy Web on Vercel

Create a Vercel project:

- Either set Root directory to `packages/web`, OR deploy from repo root (this repo includes a `vercel.json` that installs/builds `packages/web`).

Environment variables (Web):

- `API_URL=https://<your-railway-api-domain>`

This is used by the rewrite in `packages/web/next.config.js` to forward `/api/*` to the API service.

---

## 4) Production notes / gotchas

### 4.1 Autonomy runner + scaling

The autonomy runner is in-process in the API. If you scale the Railway service to >1 instance **and** `AUTONOMY_ENABLED=true`, you will run autonomy ticks multiple times.

Recommendation:

- Run **one** API instance with `AUTONOMY_ENABLED=true`, or
- Keep `AUTONOMY_ENABLED=false` and later move the runner back to a dedicated worker service.

### 4.2 Filesystem & SQLite

Production should not use local SQLite files. Turso replaces `file:./dev.db`.

Railway/Vercel filesystems are not suitable for persistent caches; use external storage if you later re-enable ingestion.
