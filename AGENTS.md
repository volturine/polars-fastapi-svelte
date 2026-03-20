# AGENTS.md

**Mandatory for all AI assistants.** Read fully before any work in this repository.

## Commands

```bash
just verify          # REQUIRED before declaring any task done (format + check)
just format          # ruff format + prettier
just test            # backend pytest
just check           # ruff + mypy + svelte-check + eslint
just dev             # start both servers
```

## Package Managers

- **Frontend**: `bun` — use `bun add` to install packages, never edit `package.json` directly
- **Backend**: `uv` — use `uv add` to install packages, never edit `pyproject.toml` directly

## Definition of Done

- Run `just verify` before declaring any task done or asking for review
- If `just verify` fails, fix the underlying issues immediately
- Do not ignore or suppress warnings, even if they seem unrelated
- Write backend Python tests for new/changed functionality
- Pre-existing warnings are tech debt — fix them, do not ignore them
- If a warning cannot be fixed (third-party stubs), suppress with an inline comment explaining why

## Workflow

1. **Explore** — Read relevant files, understand context
2. **Plan** — Produce a structured plan before coding
3. **Code** — Implement. Use parallel agents when possible
4. **Verify** — Run `just verify` mandatorily before declaring any task done
5. **Reviewer** — Ask for review and address feedback
6. **Finish** — Clean up, ensure tests pass
7. **Reflect** — Update `AGENTS.md` if you did anything wrong on first pass either prompted by user feedback or your own reflection

**Do not ask for confirmation on implementation details.** Make decisions, implement, verify. Stop and ask only on genuine ambiguity about requirements or conflicts with these rules.

**Reflect on your work.** After completing a task, review the process and outcome. If you made any mistakes or could have done something better, update this document to prevent future issues.

## Non-Negotiables

- **No workarounds.** Fix root causes or stop and ask
- **No hidden compromises.** State conflicts and propose alternatives
- **No silent behavior changes.** All changes explicit and intentional
- **Redesign over hotfix.** If existing code is wrong, redesign properly
- **Fix warnings, not just errors.** Treat warnings as bugs
- **Autonomous completion.** Continue until every requirement is implemented, tested, and verified
- **No legacy support.** New features/redesigns must not preserve legacy paths or backward compatibility

## Frontend Development

### Svelte / SvelteKit

- All Svelte components must have `lang="ts"` on the `<script>` tag
- Use Svelte 5 runes throughout — runes mode is enforced compiler-wide
- Prefer `$derived` over `$effect` for computed state
- `$effect` is only for side effects (DOM access, subscriptions, timers, network) — not for deriving state
- If `$effect` is used, include a one-line comment explaining why `$derived` is insufficient

### TypeScript

- Avoid `as any` — infer types from function signatures instead
- Avoid `as SomeType` casts unless absolutely necessary; prefer type guards
- Use `satisfies` for object literals that should conform to a type
- Prioritize type inference — let TypeScript figure it out from context

### Styling

- **Panda CSS** for all styling — custom inline styles only when Panda cannot express it
- Never use `transition-all` — use specific properties (see Transitions below)
- Use semantic color tokens from the design system, never raw hex/rgb values

### Transitions

**Never use `transition-all`.** Always use specific properties:

- `transition-colors` for hover effects
- `transition-opacity` for fades
- `transition-[color,background-color,border-color,opacity]` for combined
- Add `transform` to the list only when transform changes

## Backend Development

- FastAPI async patterns throughout — no blocking calls in route handlers
- Pydantic V2 models for all request/response schemas
- SQLAlchemy 2.0 async sessions — no sync DB calls
- Polars for all data computation — avoid pandas

## Code Style

See [`STYLE_GUIDE.md`](STYLE_GUIDE.md)

## Git

- NEVER push to remote unless explicitly asked
- Local commits only
- Create PRs for sharing changes

## Learnings

- When adding new API endpoints mirroring existing behavior (e.g., download vs preview), compare response payload shapes end-to-end. Don't assume fields like `columns` exist; follow the engine response (`data.schema` + `data.data`) to avoid false "no data" errors.
- `state_referenced_locally` and `non_reactive_update` Svelte warnings are tracked tech debt — fix them when touching affected components rather than suppressing

## OpenCode Agents

These are built-in OpenCode roles.

| Agent            | Purpose                                   | Permissions     |
| ---------------- | ----------------------------------------- | --------------- |
| **Orchestrator** | Coordinates tasks and delegations         | No write access |
| **Ask**          | Clarifies requirements and open questions | No write access |

## Specialized Subagents

| Subagents       | When to Use                                                              | Permissions     |
| --------------- | ------------------------------------------------------------------------ | --------------- |
| **Explorer**    | Reads files and gathers context                                          | Read-only       |
| **Planner**     | Produces structured plans                                                | No write access |
| **Implementer** | Edits code and applies changes                                           | Write access    |
| **Reviewer**    | Reviews diffs for correctness and quality — use before completing ANY task | Read-only       |
| **Senior**      | Senior developer for complex tasks                                       | Write access    |

## MCP Servers

| Server         | Purpose                     |
| -------------- | --------------------------- |
| **Svelte**     | Documentation and autofixer |
| **Perplexity** | Research                    |
