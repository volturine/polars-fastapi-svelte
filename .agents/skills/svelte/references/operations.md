# Operations

This skill is grounded in Svelte docs and tooling.

Primary operations to mirror:

- `list-sections`: list available Svelte and SvelteKit documentation sections
- `get-documentation`: fetch targeted documentation for one or more sections
- `svelte-autofixer`: validate a component or module and suggest fixes
- `playground-link`: use only for standalone snippets, not when editing files in this repo

Wrapper scripts in this skill:

- `scripts/doc.sh`: list sections when called with no args, or fetch docs for a section string
- `scripts/autofix.sh`: run the Svelte autofixer against a file or snippet path
- `scripts/check_svelte_mcp.sh`: smoke-test docs access
