---
name: svelte
description: Expert guidance on Svelte 5 runes, SvelteKit routing, and state management.
tags:
  - svelte
  - sveltekit
  - frontend
  - typescript
  - runes
  - web-development
---

# Svelte 5 & SvelteKit Skill

## Svelte 5 Runes
- Always use `$state`, `$derived`, `$effect`, and `$props`.
- Avoid legacy reactive statements (`$:`) and `export let`.
- Use `runed` library for advanced reactivity patterns (e.g., `Debounced`).

## SvelteKit Patterns
- Use `+page.server.ts` for secure server-side data fetching.
- Use `+page.ts` for universal load functions (SSR + CSR).
- Use `neverthrow` for error handling in load functions.
- Static adapter enabled: ensure `prerender = true` or `ssr = false` where appropriate.
