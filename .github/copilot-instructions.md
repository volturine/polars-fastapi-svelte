---
applyTo: "**"
description: Core guidelines and context for working within the Svelte 5 + FastAPI monorepo.
---

# Project Overview

You are working in a **Svelte 5 + FastAPI Monorepo**.

- **Frontend:** `frontend/` (SvelteKit, Svelte 5 Runes, TypeScript)
- **Backend:** `backend/` (FastAPI, Python 3.12+, uv)
- **Task Runner:** `Justfile`

# Core Principles for All Files

1.  **Strict Typing:** Use TypeScript for frontend and Python Type Hints for backend. No `any` or untyped code.
2.  **Functional Patterns:** Prefer functional programming over classes (except for Svelte 5 State Machines or Pydantic Models).
3.  **Modern Standards:** Use the latest stable versions (Svelte 5, Pydantic v2).
4.  **Error Handling:** Use `neverthrow` (Result types) where possible for predictable control flow.

# Development Workflow

- Run `just dev` to start the full stack.
- Run `just install` to setup dependencies.
- Run `just lint` to check code quality.
