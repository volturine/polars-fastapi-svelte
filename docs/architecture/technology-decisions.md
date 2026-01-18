# Technology Decisions

This document records the key architectural decisions made for the Polars-FastAPI-Svelte Analysis Platform, following the Architecture Decision Record (ADR) format.

## Table of Contents

1. [ADR-001: Monorepo Structure](#adr-001-monorepo-structure)
2. [ADR-002: FastAPI as Backend Framework](#adr-002-fastapi-as-backend-framework)
3. [ADR-003: Polars over Pandas](#adr-003-polars-over-pandas)
4. [ADR-004: SvelteKit with Svelte 5](#adr-004-sveltekit-with-svelte-5)
5. [ADR-005: SQLite as Database](#adr-005-sqlite-as-database)
6. [ADR-006: Multiprocessing for Compute](#adr-006-multiprocessing-for-compute)
7. [ADR-007: Client-Side Schema Calculation](#adr-007-client-side-schema-calculation)
8. [ADR-008: Pydantic for Validation](#adr-008-pydantic-for-validation)
9. [ADR-009: UV Package Manager](#adr-009-uv-package-manager)
10. [ADR-010: Static Frontend Deployment](#adr-010-static-frontend-deployment)

---

## ADR-001: Monorepo Structure

### Status
**Accepted**

### Context
We need to decide how to organize the frontend and backend codebases. Options include:
- Monorepo (single repository with both frontend and backend)
- Polyrepo (separate repositories)
- Monolith (single codebase with shared code)

### Decision
Use a **monorepo** structure with separate `/frontend` and `/backend` directories, each with independent package management (npm and UV respectively).

### Rationale
1. **Atomic changes**: Changes that span frontend and backend can be made in a single commit
2. **Simplified coordination**: No version synchronization between repositories
3. **Unified CI/CD**: Single pipeline can build and test both components
4. **Code review**: Reviewers see full context of changes
5. **Shared documentation**: Single README, contributing guide, etc.

### Consequences
**Positive:**
- Easier refactoring across stack
- Single source of truth for versions
- Simplified developer setup

**Negative:**
- Larger repository size
- Developers need polyglot tooling knowledge
- Both apps versioned together even if only one changes

### Alternatives Considered
- **Polyrepo**: Rejected due to coordination overhead for a single-team project
- **Monolith with shared code**: Rejected because Python and TypeScript can't share code meaningfully

---

## ADR-002: FastAPI as Backend Framework

### Status
**Accepted**

### Context
We need a Python web framework for the backend API. Options include:
- Django (full-featured, batteries-included)
- Flask (lightweight, flexible)
- FastAPI (modern, async-first, type-safe)

### Decision
Use **FastAPI** as the backend web framework.

### Rationale
1. **Async support**: Native async/await for non-blocking I/O
2. **Type safety**: First-class Pydantic integration for validation
3. **OpenAPI**: Automatic documentation generation
4. **Performance**: One of the fastest Python frameworks
5. **Modern Python**: Leverages Python 3.10+ features
6. **Dependency injection**: Built-in DI system

### Consequences
**Positive:**
- Automatic request/response validation
- Self-documenting API (Swagger UI at `/docs`)
- Easy async database integration
- Strong typing reduces bugs

**Negative:**
- Smaller ecosystem than Django
- Less "batteries included" than Django
- Requires understanding of async programming

### Alternatives Considered
- **Django**: Rejected due to overhead for API-only application
- **Flask**: Rejected due to lack of native async and type validation

---

## ADR-003: Polars over Pandas

### Status
**Accepted**

### Context
We need a DataFrame library for data transformations. Options include:
- Pandas (established, widely used)
- Polars (modern, performance-focused)
- DuckDB (SQL-focused, in-process)

### Decision
Use **Polars** for all data transformations.

### Rationale
1. **Lazy evaluation**: Build query plans without executing, enabling optimization
2. **Performance**: Rust-based, multi-threaded, often 10-100x faster than Pandas
3. **Memory efficiency**: Columnar format, streaming support
4. **Consistent API**: All operations follow same patterns
5. **No index**: Simpler mental model than Pandas
6. **Type safety**: Strong typing of columns

### Consequences
**Positive:**
- Handles large datasets efficiently
- Single execution pass with lazy evaluation
- Query optimization by Polars engine
- Parallel execution automatic

**Negative:**
- Smaller ecosystem than Pandas
- Less documentation and community resources
- Some operations have different API than Pandas

### Alternatives Considered
- **Pandas**: Rejected due to performance and memory concerns with large datasets
- **DuckDB**: Rejected because we wanted a DataFrame API, not SQL

---

## ADR-004: SvelteKit with Svelte 5

### Status
**Accepted**

### Context
We need a frontend framework. Options include:
- React (most popular, large ecosystem)
- Vue (approachable, good DX)
- SvelteKit (compile-time, simple reactivity)
- Angular (enterprise, full-featured)

### Decision
Use **SvelteKit** with **Svelte 5** (runes) for the frontend.

### Rationale
1. **Compile-time**: No virtual DOM, smaller bundle size
2. **Simple reactivity**: Svelte 5 runes provide intuitive state management
3. **Less boilerplate**: More concise than React/Vue
4. **Built-in features**: Routing, SSR, static generation included
5. **TypeScript**: First-class TypeScript support
6. **Performance**: Excellent runtime performance

### Consequences
**Positive:**
- Smaller bundle sizes
- Simpler component code
- Built-in state management (no Redux/Vuex needed)
- Excellent developer experience

**Negative:**
- Smaller community than React
- Fewer third-party components
- Svelte 5 runes are relatively new

### Alternatives Considered
- **React**: Rejected due to boilerplate and virtual DOM overhead
- **Vue**: Rejected in favor of Svelte's simpler model
- **Angular**: Rejected due to complexity for this use case

---

## ADR-005: SQLite as Database

### Status
**Accepted**

### Context
We need a database for storing metadata (analyses, datasources). Options include:
- PostgreSQL (full-featured, scalable)
- MySQL (widely used, mature)
- SQLite (embedded, zero-config)

### Decision
Use **SQLite** with async support (aiosqlite) for metadata storage.

### Rationale
1. **Local-first**: Aligns with local-first design philosophy
2. **Zero configuration**: No database server to manage
3. **Portability**: Single file, easy to backup/move
4. **Sufficient for use case**: Metadata storage doesn't need distributed DB
5. **Async support**: aiosqlite provides async interface

### Consequences
**Positive:**
- No external dependencies
- Simple deployment
- Easy development setup
- Sufficient performance for metadata

**Negative:**
- Single writer limitation
- Not suitable for horizontal scaling
- Limited concurrent write performance

### Alternatives Considered
- **PostgreSQL**: Rejected due to operational overhead for local-first app
- **MySQL**: Same reasoning as PostgreSQL

---

## ADR-006: Multiprocessing for Compute

### Status
**Accepted**

### Context
We need to isolate CPU-intensive Polars operations from the main FastAPI process. Options include:
- Threading (shared memory, GIL limited)
- Multiprocessing (separate processes)
- Celery/RQ (distributed task queue)
- Async only (no isolation)

### Decision
Use **multiprocessing** with queue-based IPC for compute engines.

### Rationale
1. **GIL bypass**: Multiprocessing avoids Python's Global Interpreter Lock
2. **Isolation**: Compute errors don't crash the main API
3. **Resource control**: Each engine has own memory space
4. **Simplicity**: No external dependencies (Redis, RabbitMQ)
5. **Local-first**: Aligns with single-machine deployment

### Consequences
**Positive:**
- True parallelism for CPU-bound work
- Process isolation for stability
- Simple queue-based communication
- No external infrastructure needed

**Negative:**
- No horizontal scaling across machines
- Process startup overhead
- Serialization overhead for IPC

### Alternatives Considered
- **Threading**: Rejected due to GIL limitations for CPU-bound work
- **Celery**: Rejected due to external dependencies (Redis/RabbitMQ)
- **Async only**: Rejected because Polars operations are CPU-bound

---

## ADR-007: Client-Side Schema Calculation

### Status
**Accepted**

### Context
Users need to see the expected schema (columns, types) as they build pipelines. Options include:
- Server-side calculation (API call per change)
- Client-side calculation (local computation)
- Hybrid (cache server results, predict locally)

### Decision
Implement **client-side schema calculation** that predicts output schema without API calls.

### Rationale
1. **Instant feedback**: No network latency for schema preview
2. **Reduced server load**: No API calls for every pipeline change
3. **Offline capability**: Works without backend connection
4. **Consistency**: Same rules applied deterministically

### Consequences
**Positive:**
- Immediate UI updates
- No API rate limiting concerns
- Better user experience
- Works offline

**Negative:**
- Duplicate logic (frontend and backend)
- May diverge from actual results
- Complex transformation rules to maintain
- Row counts cannot be predicted

### Alternatives Considered
- **Server-side only**: Rejected due to latency concerns
- **Hybrid caching**: Rejected due to complexity

---

## ADR-008: Pydantic for Validation

### Status
**Accepted**

### Context
We need request/response validation and serialization. Options include:
- Manual validation
- Marshmallow (serialization library)
- Pydantic (validation with type hints)
- attrs + cattrs

### Decision
Use **Pydantic** (v2) for all validation and serialization.

### Rationale
1. **Type hints**: Validation from Python type annotations
2. **FastAPI integration**: First-class support in FastAPI
3. **Performance**: Pydantic v2 is significantly faster
4. **Pydantic Settings**: Environment configuration support
5. **ORM support**: `from_attributes=True` for SQLAlchemy models

### Consequences
**Positive:**
- Single source of truth for types
- Automatic documentation
- Fast validation
- Great error messages

**Negative:**
- Learning curve for advanced features
- Strict validation may require careful schema design

### Alternatives Considered
- **Marshmallow**: Rejected due to less tight FastAPI integration
- **Manual validation**: Rejected due to maintenance burden

---

## ADR-009: UV Package Manager

### Status
**Accepted**

### Context
We need a Python package manager. Options include:
- pip (standard, widely used)
- Poetry (dependency management)
- PDM (PEP 582)
- UV (Rust-based, fast)

### Decision
Use **UV** for Python package management.

### Rationale
1. **Speed**: 10-100x faster than pip
2. **Rust-based**: Reliable dependency resolution
3. **Lock file**: Reproducible builds
4. **Drop-in replacement**: Compatible with pip commands
5. **Modern**: Supports latest Python packaging standards

### Consequences
**Positive:**
- Fast dependency installation
- Better resolution algorithm
- Reproducible builds
- Simple `uv sync` command

**Negative:**
- Newer tool, less widespread
- Some edge cases may differ from pip
- Requires UV installation

### Alternatives Considered
- **pip**: Rejected due to slow resolution and no lock file
- **Poetry**: Rejected in favor of UV's speed and simplicity
- **PDM**: Rejected due to smaller community

---

## ADR-010: Static Frontend Deployment

### Status
**Accepted**

### Context
We need to decide how to deploy the frontend. Options include:
- Server-side rendering (SSR)
- Static site generation (SSG)
- Client-side only (SPA)
- Hybrid (mix of SSR and static)

### Decision
Use **static site generation** with SvelteKit's static adapter.

### Rationale
1. **Simplicity**: No Node.js server needed in production
2. **Performance**: Pre-built HTML, fast initial load
3. **Deployment**: Can serve from any static host
4. **SEO**: Not needed for this application
5. **Local-first**: Aligns with single-machine deployment

### Consequences
**Positive:**
- Simple deployment (any HTTP server)
- Fast initial page load
- No server runtime needed
- Easy caching

**Negative:**
- No server-side rendering
- All routes must be known at build time
- API data not pre-rendered

### Alternatives Considered
- **SSR**: Rejected due to operational complexity
- **Client-side only**: Static adapter already provides this with better DX
- **Hybrid**: Rejected due to complexity

---

## Summary Table

| ADR | Decision | Primary Rationale |
|-----|----------|-------------------|
| 001 | Monorepo | Simplified coordination |
| 002 | FastAPI | Async + type safety |
| 003 | Polars | Performance + lazy evaluation |
| 004 | SvelteKit | Simple reactivity + compile-time |
| 005 | SQLite | Local-first + zero-config |
| 006 | Multiprocessing | GIL bypass + isolation |
| 007 | Client-side schema | Instant feedback |
| 008 | Pydantic | Type hints + FastAPI integration |
| 009 | UV | Speed + reproducibility |
| 010 | Static deployment | Simplicity + no runtime |

---

## See Also

- [System Design](./system-design.md) - Architecture overview
- [Design Patterns](./design-patterns.md) - Pattern implementations
- [Data Flow](./data-flow.md) - Request/response flows
