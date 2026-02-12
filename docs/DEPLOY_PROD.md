# Production deployment (Vercel Web + Fly.io API + Turso)

This runbook deploys:

- Web: Vercel (Next.js)
- API (+ in-process autonomy runner): Fly.io (Node)
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

## 2) Deploy API on Fly.io

This repo is a monorepo and does not have a root `package.json`, so you should deploy from the API package directory.

Why you saw `yarn: not found`:

- `flyctl launch` tried to auto-generate a Dockerfile and install Litestream (SQLite replication) via `yarn add ...`.
- Your production DB is Turso (remote LibSQL), so you **do not need Litestream**.
- The generator environment didn’t have `yarn`, so it failed.

Fix: deploy using the checked-in `packages/api/Dockerfile` and `packages/api/fly.toml`.

### 2.1 Create the Fly app

From the repo root:

- `cd packages/api`
- `fly launch` (use the existing `fly.toml` if prompted)

### 2.2 Build & runtime

Fly builds using the Dockerfile and runs `node dist/src/index.js`.

### 2.3 Environment variables (API)

Required (production secrets):

- `NODE_ENV=production`
- `PORT` is set to `4000` in `packages/api/fly.toml`.
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

After the app is deployed and secrets are set, run a one-off command:

- `fly ssh console -C "yarn db:deploy"`

(You can re-run safely on subsequent deploys.)

### 2.5 Verify API health

- `GET /api/health` on your Fly domain.
- If autonomy is enabled, you can manually trigger one tick (admin-only):
  - `POST /api/internal/autonomy/tick` with header `x-admin-secret: <ADMIN_SECRET>`

---

## 3) Deploy Web on Vercel

Create a Vercel project:

- Either set Root directory to `packages/web`, OR deploy from repo root (this repo includes a `vercel.json` that installs/builds `packages/web`).

Environment variables (Web):

- `API_URL=https://<your-railway-api-domain>`

Example:

- `API_URL=https://<your-fly-app>.fly.dev`

This is used by the rewrite in `packages/web/next.config.js` to forward `/api/*` to the API service.

---

## 4) Production notes / gotchas

### 4.0 Fly machine restarts (OOM)

If logs show `Process appears to have been OOM killed!`, the Machine doesn’t have enough memory for Node + Prisma.

Fix options:

- Increase memory: `fly scale memory 1024 -a <app>`
- Or keep it smaller but cap Node heap (this repo sets `NODE_OPTIONS=--max-old-space-size=384` in `packages/api/fly.toml`).

### 4.1 Autonomy runner + scaling

The autonomy runner is in-process in the API. If you scale the Fly app to >1 machine **and** `AUTONOMY_ENABLED=true`, you will run autonomy ticks multiple times.

Recommendation:

- Run **one** API instance with `AUTONOMY_ENABLED=true`, or
- Keep `AUTONOMY_ENABLED=false` and later move the runner back to a dedicated worker service.

### 4.2 Filesystem & SQLite

Production should not use local SQLite files. Turso replaces `file:./dev.db`.

Fly/Vercel filesystems are not suitable for persistent caches; use external storage if you later re-enable ingestion.
