---
applyTo: "**/*.svelte, **/*.ts"
description: Frontend development guidelines for Svelte 5 and SvelteKit files.
---

# Frontend Guidelines (Svelte 5 + SvelteKit)

**Code Style & Structure**

- Use **Svelte 5 Runes** for all reactivity (`$state`, `$derived`, `$effect`, `$props`, `$bindable`).
- **Do NOT** use legacy Svelte 3/4 APIs (`export let`, `$:`, `createEventDispatcher`).
- Use **TypeScript** for all script blocks (`<script lang="ts">`).
- Use **Standard CSS** or Svelte-scoped styles. **Do NOT use Tailwind CSS.**
- Organize files using SvelteKit's file-based routing.

**Core Libraries & Patterns**

- **`runed`:** Use for Svelte 5 runes utilities (e.g., reactive maps, sets, debounced values). PREFER `runed` primitives over custom implementations.
- **`neverthrow`:** Use for functional error handling. **ALL** services and logic functions must return a `Result<T, E>`. Avoid throwing exceptions for control flow.
- **`vite-plugin-pwa`:** Ensure Progressive Web App capabilities are maintained and configured.
- **`@sveltejs/adapter-static`:** This project is configured for static site generation (SSG) or SPA mode. Ensure `svelte.config.js` uses `adapter-static` with fallback for SPA routing if needed.

**Svelte 5 Runes Reference**

- State: `let count = $state(0);`
- Derived: `let doubled = $derived(count * 2);`
- Props: `let { title, count = 0 } = $props();`
- Effects: `$effect(() => { console.log(count); });`
- Events: Use standard DOM attributes (e.g., `onclick`) instead of `on:click`.

**Data Fetching**

- Use SvelteKit `load` functions (`+page.server.ts` or `+page.ts`) for initial data.
- For client-side interactions, fetch directly from the FastAPI backend.
- Handle fetch errors using `neverthrow`'s `ResultAsync` if complex, or simple try-catch mapped to Result.

**Project Structure**

```
frontend/
  src/
    lib/          # Shared utilities and components
    routes/       # File-based routing
    app.html
  static/
  svelte.config.js
```
