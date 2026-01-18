# Architecture Documentation

This section provides comprehensive documentation of the system architecture for the Polars-FastAPI-Svelte Analysis Platform.

## Overview

The platform follows a **monorepo architecture** with clear separation between frontend and backend, connected through a REST API. The system is designed for **local-first operation**, meaning all computation and data storage happens on the user's machine without cloud dependencies.

## Contents

| Document | Description |
|----------|-------------|
| [System Design](./system-design.md) | High-level architecture, layers, components |
| [Design Patterns](./design-patterns.md) | Architectural patterns used throughout |
| [Data Flow](./data-flow.md) | How data moves through the system |
| [Technology Decisions](./technology-decisions.md) | ADRs and rationale for tech choices |

## Architecture Principles

### 1. Local-First

- All data stays on the user's machine
- No cloud dependencies or external services
- SQLite for metadata, local filesystem for files
- Compute engines run as local processes

### 2. Separation of Concerns

- Frontend handles UI and user interaction
- Backend handles API, business logic, and persistence
- Compute layer handles data transformations
- Each module has single responsibility

### 3. Type Safety

- Pydantic schemas for all API contracts
- TypeScript for frontend type safety
- SQLAlchemy typed models for database
- Runtime validation at boundaries

### 4. Async by Default

- FastAPI with async/await throughout
- SQLAlchemy async sessions
- Non-blocking I/O operations
- Multiprocessing for CPU-bound work

### 5. Lazy Evaluation

- Polars LazyFrame for query optimization
- Schema prediction without execution
- Materialization only when needed

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    SvelteKit Application                             │   │
│   │                                                                      │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│   │  │   Routes    │  │ Components  │  │   Stores    │  │  API Client│  │   │
│   │  │  (Pages)    │  │  (UI)       │  │  (State)    │  │  (HTTP)    │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│   │                                                                      │   │
│   │  ┌─────────────────────────────────────────────────────────────────┐│   │
│   │  │              Schema Calculator (Client-Side Prediction)         ││   │
│   │  └─────────────────────────────────────────────────────────────────┘│   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ HTTP/REST (JSON)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVER LAYER                                    │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    FastAPI Application                               │   │
│   │                                                                      │   │
│   │  ┌───────────────────────────────────────────────────────────────┐  │   │
│   │  │                      Middleware Layer                          │  │   │
│   │  │                    (CORS, Logging, etc.)                       │  │   │
│   │  └───────────────────────────────────────────────────────────────┘  │   │
│   │                                                                      │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│   │  │Analysis │ │Datasource│ │ Compute │ │ Results │ │ Health  │       │   │
│   │  │ Module  │ │ Module  │ │ Module  │ │ Module  │ │ Module  │       │   │
│   │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │   │
│   │       │           │           │           │           │             │   │
│   │  ┌────┴───────────┴───────────┴───────────┴───────────┴────┐       │   │
│   │  │                   Service Layer                          │       │   │
│   │  │              (Business Logic, Validation)                │       │   │
│   │  └────┬───────────────────────────────────────────────┬────┘       │   │
│   │       │                                               │             │   │
│   │  ┌────┴────┐                                    ┌─────┴─────┐       │   │
│   │  │  ORM    │                                    │  Process  │       │   │
│   │  │ Models  │                                    │  Manager  │       │   │
│   │  └────┬────┘                                    └─────┬─────┘       │   │
│   │       │                                               │             │   │
│   └───────┼───────────────────────────────────────────────┼─────────────┘   │
│           │                                               │                 │
└───────────┼───────────────────────────────────────────────┼─────────────────┘
            │                                               │
            ▼                                               ▼
┌───────────────────────┐                     ┌───────────────────────────────┐
│    STORAGE LAYER      │                     │       COMPUTE LAYER           │
│                       │                     │                               │
│  ┌─────────────────┐  │                     │  ┌─────────────────────────┐  │
│  │   SQLite DB     │  │                     │  │  ProcessManager         │  │
│  │                 │  │                     │  │  (Singleton)            │  │
│  │  - analyses     │  │                     │  └───────────┬─────────────┘  │
│  │  - datasources  │  │                     │              │                │
│  │  - junctions    │  │                     │              ▼                │
│  └─────────────────┘  │                     │  ┌─────────────────────────┐  │
│                       │                     │  │  PolarsComputeEngine    │  │
│  ┌─────────────────┐  │                     │  │  (Subprocess)           │  │
│  │  File Storage   │  │                     │  │                         │  │
│  │                 │  │                     │  │  ┌───────────────────┐  │  │
│  │  ./data/uploads │◄─┼─────────────────────┼──┼──│ Polars LazyFrame  │  │  │
│  │  ./data/results │  │                     │  │  │ Transformations   │  │  │
│  └─────────────────┘  │                     │  │  └───────────────────┘  │  │
│                       │                     │  └─────────────────────────┘  │
└───────────────────────┘                     └───────────────────────────────┘
```

## Layer Responsibilities

### Client Layer (Frontend)

| Component | Responsibility |
|-----------|---------------|
| **Routes** | Page components, URL handling, data loading |
| **Components** | Reusable UI elements, user interaction |
| **Stores** | Application state, reactivity, caching |
| **API Client** | HTTP communication, error handling |
| **Schema Calculator** | Client-side schema prediction |

### Server Layer (Backend)

| Component | Responsibility |
|-----------|---------------|
| **Middleware** | CORS, logging, request processing |
| **Modules** | Feature-specific routes, schemas, services |
| **Service Layer** | Business logic, validation, orchestration |
| **ORM Models** | Database schema, relationships |
| **Process Manager** | Compute engine lifecycle |

### Storage Layer

| Component | Responsibility |
|-----------|---------------|
| **SQLite DB** | Metadata storage (analyses, datasources) |
| **File Storage** | Raw data files, computed results |

### Compute Layer

| Component | Responsibility |
|-----------|---------------|
| **ProcessManager** | Engine pool, lifecycle management |
| **PolarsComputeEngine** | Data transformations, execution |

## Module Structure

Each backend module follows a consistent structure:

```
module/
├── __init__.py      # Module exports
├── models.py        # SQLAlchemy ORM models
├── schemas.py       # Pydantic request/response schemas
├── routes.py        # FastAPI route handlers
└── service.py       # Business logic functions
```

## Key Architectural Decisions

1. **Monorepo over Polyrepo**: Simplified coordination, unified versioning
2. **Multiprocessing over Threading**: Bypass GIL for CPU-bound Polars operations
3. **SQLite over PostgreSQL**: Local-first design, zero configuration
4. **Polars over Pandas**: Better performance, lazy evaluation
5. **Client-side Schema Calculation**: Instant feedback without API calls

## See Also

- [System Design](./system-design.md) - Detailed component breakdown
- [Design Patterns](./design-patterns.md) - Pattern implementations
- [Data Flow](./data-flow.md) - Request/response lifecycles
- [Technology Decisions](./technology-decisions.md) - Full ADR documentation
