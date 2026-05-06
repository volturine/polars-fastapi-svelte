# Docker model

Data-Forge has one Docker deployment model:

```text
Postgres + API + Scheduler + Worker
```

The API container serves both the backend API and the built frontend on one port.
The scheduler and worker are separate Python role containers built from the same source tree.

## Files

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Production stack. This is the base compose file. |
| `docker-compose.test.yml` | Test/evaluation override for the production stack. Adds test runners and changes only test-mode settings. |
| `docker-compose.dev.yml` | Development override for the production stack. Adds source mounts and a Vite frontend dev server. |
| `env/prod.env` | Production image tags, ports, database credentials, auth, and service sizing. |
| `env/test.env` | Local verification config and local `:test` image tags. |
| `env/dev.env` | Local hot-reload development config and local `:latest` image tags. |
| `Dockerfile` | Builds all app role images and test runner images. |

## Production deployment

Edit `docker/env/prod.env`, especially:

- `DF_API_IMAGE`
- `DF_SCHEDULER_IMAGE`
- `DF_WORKER_IMAGE`
- `DF_POSTGRES_PASSWORD`
- `DF_DATABASE_URL`
- `DF_DEFAULT_USER_PASSWORD`
- `DF_SETTINGS_ENCRYPTION_KEY`
- `DF_AUTH_FRONTEND_URL`
- `DF_CORS_ORIGINS`

Then deploy:

```bash
just docker-prod
```

This is equivalent to:

```bash
docker compose --env-file docker/env/prod.env \
  -p dataforge-prod \
  -f docker/docker-compose.yml \
  up -d
```

Stop production:

```bash
just docker-prod-down
```

Logs:

```bash
just docker-prod-logs
```

## Local production-image deployment

For local image validation, build local images and run the production stack with those images:

```bash
just docker-prod-local
```

This builds:

- `polars-analysis-api:latest`
- `polars-analysis-scheduler:latest`
- `polars-analysis-worker:latest`

and then starts `docker-compose.yml` with those local image names.

## Full Docker evaluation

Run:

```bash
just docker-test
```

This does four things:

1. Builds local app images tagged `:test`.
2. Builds test runner images.
3. Starts the production stack with `docker-compose.yml` plus `docker-compose.test.yml`.
4. Runs backend, frontend unit, runtime, and Playwright e2e tests inside containers.

The test compose file is an override. It does not redefine the production app stack. It adds test runners and changes only test-mode settings such as worker counts, auth origins, and restart behavior.

Docker e2e runs with `--fail-on-flaky-tests`, so a retry-dependent pass fails the evaluation.

## Development stack

Run:

```bash
just docker-dev
```

This starts the production stack with `docker-compose.dev.yml` as a development override. The override adds:

- source mounts for Python packages,
- a shared uv virtualenv volume,
- a Vite frontend dev server,
- frontend node module/cache volumes.

Stop it:

```bash
just docker-dev-down
```

Logs:

```bash
just docker-dev-logs
```

## Image publishing

Pushes to `dev` and `master` publish:

- `ghcr.io/volturine/data-forge-api`
- `ghcr.io/volturine/data-forge-scheduler`
- `ghcr.io/volturine/data-forge-worker`

Tags:

- branch name (`dev` or `master`),
- `sha-<12 chars>`,
- `latest` for `master` only.
