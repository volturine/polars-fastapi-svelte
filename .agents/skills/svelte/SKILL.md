---
name: svelte
description: Svelte and SvelteKit implementation workflow grounded in Svelte docs and tooling. Use when Claude needs Svelte-specific guidance for runes semantics, component authoring, SvelteKit patterns, reactive state fixes, or framework-aware edits in `.svelte`, `.svelte.ts`, or route files.
---

# Svelte

Implement Svelte 5 code directly, then escalate to framework-specific docs only when the API edge is genuinely unclear.

Keep changes local and minimal unless the feature clearly spans multiple files.

## Runtime Inputs

- MCP command: `npx -y @sveltejs/mcp`
- Working directory containing the Svelte project
- Optional section names or file paths for documentation queries
- File path or snippet content for autofix checks

## Automation

- Smoke test docs access: `bash <skill-dir>/scripts/check_svelte_mcp.sh <workdir>`
- List or fetch docs: `bash <skill-dir>/scripts/doc.sh <workdir> [section]`
- Autofix wrapper: `bash <skill-dir>/scripts/autofix.sh <workdir> <file-or-code>`
- Prefer `list-sections` first, then `get-documentation` for exact sections.
- Use `svelte-autofixer` after drafting code, not before understanding the component.

Read `references/operations.md` for the complete operation map.

## Capabilities

- Explain or apply rune behavior such as `$state`, `$derived`, and `$effect`.
- Implement component logic, bindings, events, snippets, and stores.
- Handle SvelteKit route, load, and client navigation patterns.
- Diagnose compile, type, or reactivity issues specific to Svelte.
- Validate Svelte code after edits.

## Workflow

1. Read the surrounding component, store, and shared types first.
2. Keep derived state pure.
3. Normalize data at module boundaries rather than pushing loose shapes through the tree.
4. Preserve accessible semantics when changing interactions.
5. Run framework-aware validation after edits.

## Rules

- Put `lang="ts"` on every `<script>`.
- Use runes mode throughout.
- Prefer `$derived` for computed state.
- Use `$effect` only for side effects such as DOM access, subscriptions, timers, or network work.
- Add a one-line comment when `$effect` is necessary.
- Avoid `as any` and unnecessary casts.

- Use Panda CSS.
- Prefer direct `class={css({...})}` usage in Svelte files.
- Do not hide styles behind extra helper constants.
- Never use `transition-all`.

## Output

Reach for Svelte documentation only when the API surface is version-sensitive or unclear. If documentation or autofix tooling is available, use it after attempting the minimal native implementation.
