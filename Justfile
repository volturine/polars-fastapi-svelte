# Justfile for Svelte-FastAPI Template

# Default goal
default: dev

# Install all dependencies
install:
    @echo "Installing backend dependencies..."
    cd packages/shared && uv sync
    @echo "Installing frontend dependencies..."
    cd packages/frontend && bun install

# Update dependencies to latest available versions
update-deps:
    @echo "Updating backend dependencies to latest..."
    cd packages/shared && uv lock --upgrade && uv sync
    @echo "Updating frontend dependencies to latest..."
    cd packages/frontend && bun update --latest

# Run development frontend plus supervised backend runtime
dev:
    #!/usr/bin/env bash
    set -a; source packages/shared/dev.env; set +a
    (cd packages/backend && uv run --env-file ../shared/dev.env main.py) & \
    (cd packages/scheduler && uv run --env-file ../shared/dev.env main.py) & \
    (cd packages/worker-manager && uv run --env-file ../shared/dev.env main.py) & \
    (cd packages/frontend && bun run dev) & wait

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
	set -a; source packages/shared/dev.env; set +a
	cd packages/worker-manager && uv run --env-file ../shared/dev.env main.py

scheduler:
	#!/usr/bin/env bash
	set -a; source packages/shared/dev.env; set +a
	cd packages/scheduler && uv run --env-file ../shared/dev.env main.py

# Format code
format:
    @echo "Formatting backend..."
    cd packages/shared && uv run ruff format . ../backend ../scheduler ../worker-manager
    @echo "Formatting frontend..."
    cd packages/frontend && bun run format

# Run all linters and type checks
check:
    cd packages/shared && uv run ruff format --check . ../backend ../scheduler ../worker-manager && uv run ruff check . ../backend ../scheduler ../worker-manager && uv run python -m mypy . && uv run python -m mypy ../backend && uv run python -m mypy ../scheduler && uv run python -m mypy ../worker-manager
    cd packages/shared && uv run python ../../scripts/generate_ts_build_stream_types.py --check
    cd packages/frontend && bun run panda:codegen && bun run check && bun run lint


# Run e2e tests with backend + frontend lifecycle managed by Just
test-e2e:
    cd packages/shared && uv run python ../../scripts/scan_warnings.py --scope just-test-e2e --cwd . -- python ../../scripts/run_e2e_harness.py

test-e2e-raw:
    #!/usr/bin/env bash
    set -euo pipefail
    set -a; source packages/shared/e2e.env; set +a
    unset VIRTUAL_ENV
    DATA_DIR="${DATA_DIR}-run-$$"
    export DATA_DIR
    kill_tree() {
        local pid="$1"
        if [ -z "$pid" ] || ! kill -0 "$pid" >/dev/null 2>&1; then
            return
        fi
        local child
        while read -r child; do
            kill_tree "$child"
        done < <(pgrep -P "$pid" || true)
        kill "$pid" >/dev/null 2>&1 || true
    }
    kill_tree_force() {
        local pid="$1"
        if [ -z "$pid" ] || ! kill -0 "$pid" >/dev/null 2>&1; then
            return
        fi
        local child
        while read -r child; do
            kill_tree_force "$child"
        done < <(pgrep -P "$pid" || true)
        kill -9 "$pid" >/dev/null 2>&1 || true
    }
    cleanup() {
        status=$?
        for pid in ${FRONTEND_PID:-} ${SCHEDULER_PID:-} ${WORKER_PID:-} ${BACKEND_PID:-}; do
            kill_tree "$pid"
        done
        sleep 1
        for pid in ${FRONTEND_PID:-} ${SCHEDULER_PID:-} ${WORKER_PID:-} ${BACKEND_PID:-}; do
            kill_tree_force "$pid"
        done
        lsof -ti "tcp:${PORT}" | xargs -r kill >/dev/null 2>&1 || true
        lsof -ti "tcp:${FRONTEND_PORT}" | xargs -r kill >/dev/null 2>&1 || true
        exit "$status"
    }
    trap cleanup EXIT
    lsof -ti "tcp:${PORT}" | xargs -r kill >/dev/null 2>&1 || true
    lsof -ti "tcp:${FRONTEND_PORT}" | xargs -r kill >/dev/null 2>&1 || true
    (cd packages/backend && exec uv run --no-env-file main.py) & BACKEND_PID=$!
    (cd packages/worker-manager && exec uv run --no-env-file main.py) & WORKER_PID=$!
    (cd packages/scheduler && exec uv run --no-env-file main.py) & SCHEDULER_PID=$!
    (cd packages/frontend && bun run predev && exec node ./node_modules/vite/bin/vite.js dev) & FRONTEND_PID=$!
    wait_for_url() {
        local url="$1"
        local label="$2"
        local deadline=$((SECONDS + 90))
        until curl -fsS "$url" >/dev/null; do
            if [ "$SECONDS" -ge "$deadline" ]; then
                echo "Timed out waiting for ${label} at ${url}" >&2
                exit 1
            fi
            sleep 1
        done
    }
    wait_for_url "http://127.0.0.1:${PORT}/health/ready" "backend readiness"
    wait_for_url "http://127.0.0.1:${FRONTEND_PORT}" "frontend"
    cd packages/frontend && PLAYWRIGHT_DISABLE_WEB_SERVER=true npx playwright test

# Run backend tests
test:
    cd packages/shared && uv run python ../../scripts/scan_warnings.py --scope just-test --cwd . -- just test-raw

# Run backend and frontend tests entirely in Docker
docker-test:
    #!/usr/bin/env bash
    set -euo pipefail
    export DOCKER_CONFIG="${PWD}/.docker"
    cleanup() {
        status=$?
        if [ "$status" -ne 0 ]; then
            docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml ps -a || true
            docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml logs api scheduler worker || true
        fi
        docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml down -v --remove-orphans >/dev/null 2>&1 || true
        exit "$status"
    }
    trap cleanup EXIT
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml down -v --remove-orphans >/dev/null 2>&1 || true
    docker buildx build --load --build-arg INSTALL_DEV=true --target api -f docker/Dockerfile -t polars-analysis-api:test .
    docker buildx build --load --build-arg INSTALL_DEV=true --target scheduler -f docker/Dockerfile -t polars-analysis-scheduler:test .
    docker buildx build --load --build-arg INSTALL_DEV=true --target worker -f docker/Dockerfile -t polars-analysis-worker:test .
    docker buildx build --load --target frontend-test -f docker/Dockerfile -t polars-analysis-frontend-test:test .
    docker buildx build --load --target frontend-e2e -f docker/Dockerfile -t polars-analysis-frontend-e2e:test .
    docker buildx build --load --target e2e-test -f docker/Dockerfile -t polars-analysis-e2e-test:test .
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm frontend-test
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml up -d postgres api scheduler worker frontend-e2e
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm backend-test
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm runtime-test
    docker compose --env-file docker/env/test.env -p dataforge-test -f docker/docker-compose.test.yml run --rm e2e-test

test-raw:
    cd packages/shared && uv run python -m pytest --tb=short -q
    cd packages/frontend && bun run test:unit

# Generate TypeScript types from Pydantic step schemas
generate-step-types:
    cd packages/shared && uv run python ../../scripts/generate_ts_step_types.py

# Generate TypeScript types from build runtime schemas
generate-build-stream-types:
    cd packages/shared && uv run python ../../scripts/generate_ts_build_stream_types.py

# Full verification gate -- must pass before any task is declared done
verify:
    cd packages/shared && uv run python ../../scripts/scan_warnings.py --scope just-verify --cwd . -- just verify-raw

verify-raw: format check test

# Build for production (single-port: FastAPI serves the built frontend)
# Setup: edit packages/shared/prod.env.
prod:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Building frontend..."
    (cd packages/frontend && bun run build)
    set -a; source packages/shared/prod.env; set +a
    echo "Starting production runtime..."
    (cd packages/backend && uv run --env-file ../shared/prod.env main.py) & \
    (cd packages/scheduler && uv run --env-file ../shared/prod.env main.py) & \
    (cd packages/worker-manager && uv run --env-file ../shared/prod.env main.py) & wait

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
