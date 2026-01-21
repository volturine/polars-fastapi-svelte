# Polars-FastAPI-Svelte Analysis Platform

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

Frontend: http://localhost:5173

Backend: http://localhost:8000

## Configuration

The backend can be configured using environment variables. Copy `.env.example` to `.env` and customize as needed:

```bash
cd backend
cp .env.example .env
```

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug logging and SQL echo |
| `ENGINE_IDLE_TIMEOUT` | `300` | Seconds before idle engines are cleaned up |
| `JOB_TIMEOUT` | `300` | Maximum job execution time in seconds |
| `JOB_TTL` | `1800` | Seconds to keep completed jobs in memory |
| `MAX_JOBS_IN_MEMORY` | `1000` | Maximum number of jobs to cache |
| `MAX_UPLOAD_SIZE` | `10737418240` | Maximum file upload size (10GB) |

See `backend/.env.example` for all available options with detailed descriptions.

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

## Documentation

- [PRD](docs/PRD.md) — Feature specs and architecture
- [AGENTS.md](AGENTS.md) — Developer guidelines
- [STYLE_GUIDE.md](STYLE_GUIDE.md) — Code style

## License

MIT
