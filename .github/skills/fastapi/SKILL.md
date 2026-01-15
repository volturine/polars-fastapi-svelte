---
name: fastapi
description: Expert guidance on FastAPI, Pydantic v2, and Python best practices.
tags:
  - fastapi
  - python
  - backend
  - pydantic
  - web-development
  - api
  - uv
  - roro
  - asyncio
  - type-hints
  - neverthrow
  - services
  - routers
---

# FastAPI & Python Backend Skill

## Core Architecture
- **RORO Pattern:** Receive Object, Return Object for all service functions.
- **Dependency Injection:** Use `Depends()` for shared resources (DB sessions, config).
- **Pydantic V2:** Use `model_validate`, `model_dump`, and strict typing.

## Error Handling
- Use `neverthrow` results in internal service logic where possible.
- Raise `HTTPException` only at the router level or in specific middleware.

## Tooling
- **uv:** Use `uv add/remove/sync` for all package management.
- **Ruff:** Follow strict linting rules configured in `pyproject.toml`.
