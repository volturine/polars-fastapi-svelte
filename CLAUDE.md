# CLAUDE.md

**Claude Code instructions for this repository.** Read `AGENTS.md` first — this file extends it with Claude-specific guidance.

## Quick Reference

```bash
just verify          # REQUIRED before declaring any task done
just format          # ruff format + prettier
just check           # ruff + mypy + svelte-check + eslint
just test            # backend pytest
just dev             # start both servers
```

## Claude Code Behaviour

- **No confirmation prompts** on implementation details — decide, implement, verify
- **Stop and ask** only on genuine requirement ambiguity or conflicts with AGENTS.md rules
- **Always run `just verify`** before declaring a task complete — never skip this
- **One task at a time** in the todo list; mark complete immediately when done

## Agentic Workflow

Use parallel subagents where possible to maximise throughput:

1. **Explore** (Explorer agent) — gather context before changing anything
2. **Plan** (Planner agent) — structured plan, identify risks
3. **Implement** (Implementer agent) — write code, parallel where independent
4. **Verify** — `just verify` must pass
5. **Review** (Reviewer agent) — check diff before finishing
6. **Reflect** — update `AGENTS.md` with any new learnings

## Tool Usage

- **Grep/Glob** for targeted searches; **Explore agent** for broad codebase exploration
- **Read before Edit** — always read a file before modifying it
- **Write** only for new files; **Edit** for modifications
- Prefer **parallel tool calls** for independent reads/searches

## Code Standards

Defer to `STYLE_GUIDE.md` for all style decisions. Key reminders:

- All Svelte components need `lang="ts"`
- No `any` — infer types or use proper generics
- `$derived` over `$effect` for computed state
- `const` over `let`; early returns over `else`
- Panda CSS for all styling — no inline styles
