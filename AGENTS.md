# AGENTS.md

**Mandatory for all AI assistants.** Read fully before any work in this repository.

## Commands

```bash
just verify          # format + static checks only
just format          # ruff format + prettier
just test            # backend pytest + frontend unit tests
just test-e2e        # e2e tests with Playwright
just check           # ruff + mypy + svelte-check + eslint
just dev             # start API, worker, scheduler, and frontend
```

- E2E must be run only via `just test-e2e`. Do not run Playwright e2e commands directly.

## Package Managers

- **Frontend**: `bun` — use `bun add` to install packages, never edit `package.json` directly
- **Backend**: `uv` — use `uv add` to install packages, never edit `pyproject.toml` directly

## Definition of Done

- For code or config changes, run `just verify`, `just test`, and `just test-e2e` before declaring any task done or asking for review
- For markdown-only changes, these commands are not required unless the user explicitly asks for them
- If `just verify` fails, fix the underlying issues immediately
- If `just test` or `just test-e2e` fails for a code/config change, fix the underlying issues immediately
- Do not ignore or suppress warnings, even if they seem unrelated
- Write backend Python tests for new/changed functionality
- Pre-existing warnings are tech debt — fix them, do not ignore them
- If a warning cannot be fixed (third-party stubs), suppress with an inline comment explaining why

## Workflow

1. **Explore** — Read relevant files, understand context
2. **Plan** — Produce a structured plan before coding
3. **Code** — Implement. Use parallel agents when possible
4. **Verify** — Run the required validation commands for the change type before declaring any task done
5. **Reviewer** — Ask for review and address feedback
6. **Finish** — Clean up, ensure tests pass

**Do not ask for confirmation on implementation details.** Make decisions, implement, verify. Stop and ask only on genuine ambiguity about requirements or conflicts with these rules.

## Non-Negotiables

- **No workarounds.** Fix root causes or stop and ask
- **No hidden compromises.** State conflicts and propose alternatives
- **No silent behavior changes.** All changes explicit and intentional
- **Redesign over hotfix.** If existing code is wrong, redesign properly
- **Fix warnings, not just errors.** Treat warnings as bugs
- **Autonomous completion.** Continue until every requirement is implemented, tested, and verified
- **No legacy support.** New features/redesigns must not preserve legacy paths or backward compatibility
- **No polling.** Do not add polling/interval refresh logic.
- **No fallback logic.** Do not add permissive fallback/defaulting behavior unless the user explicitly asks for it.
- **Build start is HTTP-only.** Never redesign build start around websockets.
- **Monitoring history is explicit.** Monitoring engine-run rows are history data and should only gain new rows on explicit refresh.
- **Live build websockets are scoped.** Websocket use for builds is limited to engine status in the left panel and live build preview/detail views, including the expanded Monitoring row for a running build.

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
- In Svelte files, do not hide styling behind helpers or intermediate style constants. Avoid `const foo = css(...)`, `const fooStyle = { ... }`, `css(fooStyle, ...)`, or wrapper functions that return `css(...)`; prefer direct `class={css({...})}` at the use site.

### Transitions

**Never use `transition-all`.** Always use specific properties:

- `transition-colors` for hover effects
- `transition-opacity` for fades
- `transition-[color,background-color,border-color,opacity]` for combined
- Add `transform` to the list only when transform changes


## Code Style

See [`STYLE_GUIDE.md`](STYLE_GUIDE.md)

## Git

- NEVER push to remote unless explicitly asked
- Local commits only
- Create PRs for sharing changes

