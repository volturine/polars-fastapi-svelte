# Data-Forge Analysis Platform

A local-first, no-code data analysis tool for building data pipelines visually.

## Mission

Make data transformation and analysis accessible to people who aren't comfortable writing code, while still leveraging powerful tools like Polars under the hood. Runs entirely on your machine — no cloud, no subscriptions, no data leaving your computer.

## What This Is

- A visual pipeline builder for data transformations
- Support for CSV, Parquet, Excel, JSON, databases, and APIs
- Isolated compute environments (one analysis per process)
- Client-side schema calculation for instant feedback
- Built on Polars for performance

## Tech Stack

**Backend**: FastAPI + Python 3.13 + Polars + SQLAlchemy 2.0 (async) + SQLite + Pydantic V2

**Frontend**: SvelteKit 2 + Svelte 5 (runes) + TypeScript + TanStack Query

## Quick Start

### Option 1: Docker (Recommended for Production)

```bash
# Copy and configure environment
cp .env.example .env

# Deploy with Docker Compose
./scripts/deploy.sh

# Access the application
open http://localhost:8000
```

### Option 2: Local Development

```bash
# Install backend
cd backend
uv sync --extra dev

# Install frontend
cd ../frontend
npm install

# Run both
just dev
```

Frontend: http://localhost:3000 (Vite dev server — proxies /api to backend)

Backend API: http://localhost:8000

## Configuration

The app supports two deployment topologies with different configuration needs.

### Production (single port — `just prod` or Docker)

FastAPI serves the pre-built frontend and the API on the same port.

```bash
# Bare-metal
cp backend/.prod.env.example backend/.prod.env
# Edit backend/.prod.env with your host / secrets
cd frontend && bun run build   # build the frontend first
just prod

# Docker / compose
cp .env.example .env
# Edit .env with your host / secrets
docker compose up
```

### Development (two separate servers — `just dev`)

Vite dev server (port 3000) proxies `/api` to FastAPI (port 8000).

```bash
cd backend && cp .env.example .env && cd ..
cd frontend && cp .env.example .env && cd ..
just dev
```

### Key Configuration Options

| Variable              | Dev default | Prod note                                                                     |
| --------------------- | ----------- | ----------------------------------------------------------------------------- |
| `DEBUG`               | `false`     | Enable debug logging and SQL echo                                             |
| `PROD_MODE_ENABLED`   | `false`     | **Set to `true` in prod** — enables static-file serving from `frontend/build` |
| `ENGINE_IDLE_TIMEOUT` | `60`        | Seconds before idle engines are cleaned up                                    |
| `JOB_TIMEOUT`         | `300`       | Maximum job execution time in seconds                                         |
| `AUTH_REQUIRED`       | `false`     | Require login before accessing authenticated routes                           |
| `CORS_ORIGINS`        | dev origins | Not needed in prod (same-origin); required in dev for the Vite server         |
| `VITE_BACKEND_PORT`   | `8000`      | **Dev only** — not used in production                                         |

See **[ENV_VARIABLES.md](ENV_VARIABLES.md)** for the complete reference, topology diagrams, and all variables.

## Architecture

### Backend Components

- **Compute Engine**: Isolated multiprocess execution for each analysis
- **Process Manager**: Thread-safe singleton managing engine lifecycle
- **Job Tracking**: TTL-based cleanup with configurable size limits
- **Error Handling**: Custom exception hierarchy with structured error responses
- **Configuration**: Pydantic-based settings with validation

### Key Features

- **Thread-safe operations**: All shared state uses proper locking
- **Automatic cleanup**: Idle engines and old jobs are cleaned up automatically
- **Timeout protection**: All polling loops have configurable timeouts
- **Structured logging**: Comprehensive logging at INFO, DEBUG, and ERROR levels
- **Graceful shutdown**: Proper cleanup of all resources on application exit

## Docker Deployment

The application is fully dockerized and can be deployed as a single container containing both frontend and backend.

### Production Deployment

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Deploy
./scripts/deploy.sh

# 3. Check health
./scripts/health-check.sh
```

### Development with Docker

```bash
# Start with hot-reload
./scripts/dev.sh
```

### Resource Configuration

Configure resource limits in `.env`:

```bash
# CPU and memory per analysis engine
POLARS_MAX_THREADS=4
POLARS_MAX_MEMORY_MB=2048

# Maximum concurrent analyses
MAX_CONCURRENT_ENGINES=5

# API server workers
WORKERS=2
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide including:

- Resource planning
- Scaling strategies
- Monitoring and health checks
- Troubleshooting
- Production best practices

## Documentation

### Deployment & Configuration

- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Complete deployment guide with Docker
- **[ENV_VARIABLES.md](ENV_VARIABLES.md)** — Complete backend/frontend environment variable reference
- **[DOCKERIZATION_SUMMARY.md](DOCKERIZATION_SUMMARY.md)** — Dockerization implementation details
- **[DOCKERIZATION_PLAN.md](DOCKERIZATION_PLAN.md)** — Technical architecture plan

### Development

- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** — Code quality improvements summary
- [PRD](docs/PRD.md) — Feature specs and architecture
- [AGENTS.md](AGENTS.md) — Developer guidelines
- [STYLE_GUIDE.md](STYLE_GUIDE.md) — Code style
- [MCP Tool Contract](docs/mcp-tool-contract.md) — How API routes are exposed as MCP tools
