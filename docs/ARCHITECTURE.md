# Polars-FastAPI-Svelte Analysis Platform — Architecture Overview

**Project Type:** Full-stack local-first data analysis platform with visual pipeline builder

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (SvelteKit 2)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Home/Gallery│  │Data Sources │  │   Analysis Editor       │  │
│  │   Dashboard  │  │  Management │  │  (Pipeline Canvas)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                 │
│  State Management:                                              │
│  • Svelte 5 Runes ($state, $derived, $effect)                  │
│  • TanStack Query (server state)                                │
│  • Runed utilities (PersistedState, FiniteStateMachine)         │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP API
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI + Python)                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Layer                            │    │
│  │  /api/v1/analysis  ·  /api/v1/datasource  ·  /compute   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  Analysis Module │  │Datasource Module │  │ Compute Module│  │
│  │  (CRUD + State)  │  │  (Upload/Manage) │  │  (Pipeline)   │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │   Results Module │  │  Health Module   │  │  Error Handler│  │
│  │  (Preview/Export)│  │  (Liveness)      │  │  (Custom Ex)  │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Database (SQLite)                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  analyses  │  datasources  │  jobs  │  engine_states    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                    (SQLAlchemy 2.0 async + Alembic)             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               Compute Engine (Isolated Processes)               │
│                                                                 │
│   Process Manager (Singleton)                                    │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  • Thread-safe engine lifecycle                         │   │
│   │  • Idle timeout cleanup                                 │   │
│   │  • Max concurrent engine limits                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Per-Analysis Engine (Multiprocess)                             │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Analysis_ID: uuid-123  │  Status: IDLE/RUNNING         │   │
│   │  Command Queue ───────►│  Polars Pipeline Execution    │   │
│   │  Result Queue ◄────────│  LazyFrame → DataFrame        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Supported Operations (20+ Polars operations):                  │
│   • Transform: filter, select, drop, rename, with_columns       │
│   • Aggregate: groupby, pivot, unpivot                          │
│   • Sort/Filter: sort, limit, topk, deduplicate                 │
│   • Time Series: extract, add, subtract, diff                   │
│   • String: uppercase, lowercase, replace, split, extract       │
│   • Join/Merge: join, union_by_name                             │
│   • Handle Nulls: fill_null, drop_rows                          │
│   • Export: csv, parquet, json, excel                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Upload Flow

```
User uploads  →  Frontend API  →  Datasource Service  →  File Storage (uploads/)
                                                            │
                                                            ▼
                                                    SQLite Metadata
```

### 2. Pipeline Execution Flow

```
Frontend Pipeline  →  Compute Service  →  Process Manager  →  Polars Engine (mp.Process)
                                                                        │
                        ┌───────────────────────────────────────────────┘
                        ▼
Preview (Table)  ←  Sample (5000 rows)  ←  Collect Final  ←  LazyFrame Pipeline
```

### 3. Export Flow

```
Export Request  →  Compute Service  →  Polars Export  →  Files (exports/)
```

---

## Key Components

| Layer | Component | Technology | Purpose |
|-------|-----------|------------|---------|
| **Frontend** | SvelteKit 2 | Svelte 5 + TypeScript | SPA with routing |
| | State | Runes + TanStack Query | Reactive UI state |
| | UI Components | Pipeline canvas, step configs, data viewers | Visual pipeline builder |
| **Backend** | FastAPI | Python 3.13 + async | REST API |
| | Database | SQLite + SQLAlchemy 2.0 + Alembic | Persistent storage |
| | Compute | Multiprocessing + Polars | Isolated pipeline execution |
| **File Storage** | Uploads | Local filesystem | Raw data files |
| | Results | Local filesystem | Execution results |
| | Exports | Local filesystem | Exported data |

---

## API Endpoints

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analysis` | List analyses |
| POST | `/api/v1/analysis` | Create analysis |
| GET | `/api/v1/analysis/{id}` | Get analysis |
| PUT | `/api/v1/analysis/{id}` | Update analysis |
| DELETE | `/api/v1/analysis/{id}` | Delete analysis |

### Datasource

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/datasource` | List datasources |
| POST | `/api/v1/datasource/upload` | Upload file |
| GET | `/api/v1/datasource/{id}` | Get datasource |
| DELETE | `/api/v1/datasource/{id}` | Delete datasource |

### Compute

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/compute/start/{analysis_id}` | Start engine |
| GET | `/compute/status/{analysis_id}` | Engine status |
| POST | `/compute/execute` | Execute pipeline |
| GET | `/compute/result/{job_id}` | Get result |
| POST | `/compute/export` | Export data |
| POST | `/compute/shutdown/{id}` | Shutdown engine |
| POST | `/compute/keepalive/{id}` | Keepalive ping |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic liveness |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/startup` | Startup probe |

---

## Data Source Support

| Format | Reader | Notes |
|--------|--------|-------|
| CSV | `pl.scan_csv()` | Configurable delimiter, quote char, encoding |
| Parquet | `pl.scan_parquet()` | Columnar format, efficient |
| JSON | `pl.read_json().lazy()` | Line-delimited or standard |
| NDJSON | `pl.scan_ndjson()` | Newline-delimited JSON |
| Excel | `pl.read_excel()` | XLSX/XLS support |
| Database | `pl.read_database()` | SQL query-based |
| DuckDB | `duckdb.execute()` | Embedded SQL database |

---

## Engine Lifecycle

```
SPAWN  →  IDLE  →  RUNNING  →  COMPLETE/FAIL
New     Waiting  Executing  Result
process for job   pipeline  returned
              │
              ▼
        CLEANUP
        • Idle timeout (default 300s)
        • Process termination
        • Job cache cleanup
```

---

## Environment Isolation

- **Each analysis** = separate `multiprocessing.Process`
- **No shared state** between engines
- **Thread-safe** ProcessManager with locks
- **Configurable limits**:
  - `MAX_CONCURRENT_ENGINES` (default: 10)
  - `ENGINE_IDLE_TIMEOUT` (default: 300s, reset on save)
  - `ENGINE_POOLING_INTERVAL` (default: 5s)
  - `JOB_TIMEOUT` (default: 300s, max job runtime)
  - `POLARS_MAX_THREADS` (per-engine)
  - `POLARS_MAX_MEMORY_MB` (per-engine)

---

## Tech Stack Summary

### Frontend
- **Framework:** SvelteKit 2
- **Language:** TypeScript
- **State:** Svelte 5 Runes ($state, $derived, $effect)
- **Data Fetching:** TanStack Query
- **Utilities:** Runed (PersistedState, FiniteStateMachine, Debounced, etc.)
- **Styling:** Scoped CSS

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.13
- **Database:** SQLite with SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Validation:** Pydantic V2
- **Compute:** Polars + multiprocessing

### Infrastructure
- **Container:** Docker + Docker Compose
- **Process Management:** Custom ProcessManager singleton
- **File Storage:** Local filesystem (uploads/, results/, exports/)
- **Health Checks:** Liveness, Readiness, Startup probes

---

## File Structure

```
polars-fastapi-svelte/
├── backend/
│   ├── api/                    # API routing
│   │   └── v1/
│   ├── core/                   # Core application code
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   └── error_handlers.py  # Custom error handling
│   ├── database/              # Database + migrations
│   │   └── alembic/
│   ├── modules/               # Feature modules
│   │   ├── analysis/          # Analysis CRUD
│   │   ├── compute/           # Pipeline execution
│   │   ├── datasource/        # File uploads
│   │   ├── results/           # Results/export
│   │   └── health/            # Health checks
│   └── main.py                # Application entry point
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/          # API client
│   │   │   ├── components/   # UI components
│   │   │   │   ├── operations/   # Operation configs
│   │   │   │   ├── pipeline/     # Pipeline builder
│   │   │   │   └── viewers/      # Data viewers
│   │   │   ├── stores/       # State stores (.svelte.ts)
│   │   │   └── types/        # TypeScript types
│   │   └── routes/           # SvelteKit pages
│   └── build/                # Production build
└── data/
    ├── uploads/              # Uploaded files
    ├── results/              # Execution results
    └── exports/              # Exported files
```
