---
applyTo: "**/*.py"
description: Backend development guidelines for FastAPI and Python files.
---

# Backend Guidelines (FastAPI + Python)

**Core Principles**

- Use **FastAPI** for the web framework.
- Use **`uv`** for dependency management.
- Follow the **RORO (Receive an Object, Return an Object)** pattern for service functions.
- Use **Pydantic v2** for all data validation and schemas.

**Project Structure**

```
backend/
  api/
    v1/           # Versioned API routers
  modules/        # Feature-based modules
    health/       # Example module
      routes.py   # FastAPI router endpoints
      schemas.py  # Pydantic models (Input/Output)
      service.py  # Pure business logic
      models.py   # Database models (if applicable)
  main.py         # App entry point
```

**Coding Standards**

- **Type Hints:** Mandatory for all functions.
- **Async/Await:** Use `async def` for I/O bound operations (DB, Network).
- **Services:** Pure functions or stateless classes in `service.py`. Keep logic out of `routes.py`.
- **Routers:** Minimal logic. Validate input -> Call Service -> Return Response.
