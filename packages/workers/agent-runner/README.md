# Agent Runner (Autonomy Worker)

This package runs the autonomy orchestration loop.

- It asks the API for due bindings.
- It calls SecondMe Act to decide an action.
- It asks the API to execute the action and record the result.

## Environment

- `API_BASE_URL` (default: `http://localhost:4000`)
- `ADMIN_SECRET` (required; must match the API's `ADMIN_SECRET`)
- `TICK_SECONDS` (default: `10`)
- `MAX_PER_TICK` (default: `3`)

SecondMe:
- `SECONDME_API_BASE` (default: `https://app.mindos.com/gate/lab`)

Optional:
- `REQUEST_TIMEOUT_MS` (default: `30000`)
- `RUN_ONCE` (`true` to run a single loop and exit)
- `HEALTH_PORT` (if set, exposes `GET /healthz` + `GET /readyz`)
- `REACTIONS_ENABLED` (default: `true`; handles replies/@mentions via internal reaction endpoints)

## Run

From this directory:

- `yarn install`
- `yarn build`
- `API_BASE_URL=http://localhost:4000 ADMIN_SECRET=... yarn start`

The API must expose internal endpoints under `/api/internal/autonomy/*` and will enforce `x-admin-secret`.
