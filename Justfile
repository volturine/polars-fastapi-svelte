# Justfile for Svelte-FastAPI Template

# Default goal
default: dev

# Install all dependencies
install:
    @echo "Installing backend dependencies..."
    cd backend && uv sync
    @echo "Installing frontend dependencies..."
    cd frontend && bun install

# Update dependencies to latest available versions
update-deps:
    @echo "Updating backend dependencies to latest..."
    cd backend && uv lock --upgrade && uv sync
    @echo "Updating frontend dependencies to latest..."
    cd frontend && bun update --latest

# Run development frontend plus supervised backend runtime
dev:
    #!/usr/bin/env bash
    set -a; source backend/dev.env; set +a
    (cd backend && uv run --env-file dev.env ./app.py) & (cd frontend && bun run dev) & wait

# Run full development stack entirely in Docker
docker-dev:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    docker buildx build --load -f docker/Dockerfile --target api -t polars-analysis-api:latest .
    docker buildx build --load -f docker/Dockerfile --target scheduler -t polars-analysis-scheduler:latest .
    docker buildx build --load -f docker/Dockerfile --target worker -t polars-analysis-worker:latest .
    docker compose --env-file docker/env/dev.env -p dataforge-dev -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

docker-dev-down:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    docker compose --env-file docker/env/dev.env -p dataforge-dev -f docker/docker-compose.yml -f docker/docker-compose.dev.yml down -v --remove-orphans

docker-dev-logs:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    docker compose --env-file docker/env/dev.env -p dataforge-dev -f docker/docker-compose.yml -f docker/docker-compose.dev.yml logs -f

worker:
	#!/usr/bin/env bash
	set -a; source backend/dev.env; set +a
	cd backend && uv run --env-file dev.env ./worker.py

scheduler:
	#!/usr/bin/env bash
	set -a; source backend/dev.env; set +a
	cd backend && uv run --env-file dev.env ./scheduler.py

# Format code
format:
    @echo "Formatting backend..."
    cd backend && uv run ruff format .
    @echo "Formatting frontend..."
    cd frontend && bun run format

# Run all linters and type checks
check:
    cd backend && uv run ruff format --check . && uv run ruff check . && uv run mypy .
    cd backend && uv run python scripts/generate_ts_build_stream_types.py --check
    cd frontend && bun run panda:codegen && bun run check && bun run lint


# Run e2e tests with backend + frontend lifecycle managed by Just
test-e2e:
    cd backend && uv run python scripts/scan_warnings.py --scope just-test-e2e --cwd . -- just test-e2e-raw

test-e2e-raw:
    cd backend && uv run python scripts/run_e2e_harness.py

# Run backend tests
test:
    cd backend && uv run python scripts/scan_warnings.py --scope just-test --cwd . -- just test-raw

# Run backend and frontend tests entirely in Docker
docker-test:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    trap 'docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml down -v --remove-orphans >/dev/null 2>&1 || true' EXIT
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml down -v --remove-orphans >/dev/null 2>&1 || true
    docker buildx build --load --build-arg INSTALL_DEV=true --target api -f docker/Dockerfile -t polars-analysis-api:test .
    docker buildx build --load --build-arg INSTALL_DEV=true --target scheduler -f docker/Dockerfile -t polars-analysis-scheduler:test .
    docker buildx build --load --build-arg INSTALL_DEV=true --target worker -f docker/Dockerfile -t polars-analysis-worker:test .
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm frontend-test
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml up -d postgres api scheduler worker frontend-e2e
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm backend-test
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm runtime-test
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm e2e-test

test-raw:
    cd backend && uv run pytest --tb=short -q
    cd frontend && bun run test:unit

# Generate TypeScript types from Pydantic step schemas
generate-step-types:
    cd backend && uv run python scripts/generate_ts_step_types.py

# Generate TypeScript types from build runtime schemas
generate-build-stream-types:
    cd backend && uv run python scripts/generate_ts_build_stream_types.py

# Full verification gate -- must pass before any task is declared done
verify:
    cd backend && uv run python scripts/scan_warnings.py --scope just-verify --cwd . -- just verify-raw

verify-raw: format check test

# Build for production (single-port: FastAPI serves the built frontend)
# Setup: edit backend/prod.env.
prod:
    @echo "Building frontend..."
    cd frontend && bun run build
    @echo "Starting backend in production mode..."
    cd backend && uv run --env-file prod.env ./app.py

# Run production stack entirely in Docker
docker-prod:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    docker buildx build --load -f docker/Dockerfile --target api -t polars-analysis-api:latest .
    docker buildx build --load -f docker/Dockerfile --target scheduler -t polars-analysis-scheduler:latest .
    docker buildx build --load -f docker/Dockerfile --target worker -t polars-analysis-worker:latest .
    DF_API_IMAGE=polars-analysis-api:latest DF_SCHEDULER_IMAGE=polars-analysis-scheduler:latest DF_WORKER_IMAGE=polars-analysis-worker:latest DF_POSTGRES_PASSWORD=ChangeMe123! DF_DATABASE_URL=postgresql+psycopg://dataforge:ChangeMe123!@postgres:5432/dataforge DF_DEFAULT_USER_PASSWORD=Admin123! DF_SETTINGS_ENCRYPTION_KEY=dev-only-local-secret-key docker compose --env-file docker/env/prod.env -p dataforge-prod -f docker/docker-compose.yml up -d

docker-prod-down:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    DF_API_IMAGE=polars-analysis-api:latest DF_SCHEDULER_IMAGE=polars-analysis-scheduler:latest DF_WORKER_IMAGE=polars-analysis-worker:latest DF_POSTGRES_PASSWORD=ChangeMe123! DF_DATABASE_URL=postgresql+psycopg://dataforge:ChangeMe123!@postgres:5432/dataforge DF_DEFAULT_USER_PASSWORD=Admin123! DF_SETTINGS_ENCRYPTION_KEY=dev-only-local-secret-key docker compose --env-file docker/env/prod.env -p dataforge-prod -f docker/docker-compose.yml down -v --remove-orphans

docker-prod-logs:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    DF_API_IMAGE=polars-analysis-api:latest DF_SCHEDULER_IMAGE=polars-analysis-scheduler:latest DF_WORKER_IMAGE=polars-analysis-worker:latest DF_POSTGRES_PASSWORD=ChangeMe123! DF_DATABASE_URL=postgresql+psycopg://dataforge:ChangeMe123!@postgres:5432/dataforge DF_DEFAULT_USER_PASSWORD=Admin123! DF_SETTINGS_ENCRYPTION_KEY=dev-only-local-secret-key docker compose --env-file docker/env/prod.env -p dataforge-prod -f docker/docker-compose.yml logs -f

release version *args:
	#!/usr/bin/env bash
	bash scripts/release.sh {{version}} {{args}}

release-dry-run version:
	#!/usr/bin/env bash
	bash scripts/release.sh {{version}} --dry-run
