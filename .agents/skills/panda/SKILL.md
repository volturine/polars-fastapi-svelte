---
name: panda
description: Panda CSS styling workflow grounded in Panda docs and CLI. Use when Claude needs to inspect or change Panda tokens, semantic tokens, recipes, patterns, conditions, generated styled-system output, or usage analysis while styling or refactoring frontend UI.
---

# Panda

Use Panda as the source of truth for tokens, semantic tokens, recipes, patterns, and generated styling output.

Preserve the established visual language unless the user asks for a redesign.

Use official Panda config concepts and CLI workflows before inventing new styling structure.

## Runtime Inputs

- Working directory containing the Panda project
- Panda config path for that project
- Optional `panda` CLI flags for codegen or analysis

## Automation

- Config and CLI check: `bash <skill-dir>/scripts/check_panda_cli.sh <workdir> <panda-config-path>`
- Regenerate styled-system output: `bash <skill-dir>/scripts/codegen.sh <workdir> [--clean|--watch]`
- Analyze token or recipe usage: `bash <skill-dir>/scripts/analyze.sh <workdir> [--scope token|recipe] [paths...]`

Read `references/operations.md` for the complete operation map.

Panda docs and CLI facts to anchor the workflow:

1. `panda codegen` regenerates the `styled-system` output from `panda.config.ts`
2. Tokens belong in `theme.extend.tokens`
3. Semantic tokens belong in `theme.extend.semanticTokens`
4. Reusable variants belong in recipes
5. Layout primitives belong in generated patterns
6. `panda analyze` reports token and recipe usage across the project

## Capabilities

- Inspect the config model for tokens, semantic tokens, recipes, patterns, and conditions before introducing new styling.
- Reuse recipes and layout patterns before creating ad hoc styling structures.
- Use Panda CLI to regenerate `styled-system` output after config changes.
- Analyze token and recipe usage before adding new variants or names.
- Regenerate Panda output after config or token changes.

## Workflow

1. Inspect nearby components for existing token and recipe usage.
2. Inspect `panda.config.ts` for tokens, semantic tokens, recipes, patterns, and conditions when exact names matter.
3. Reuse the closest matching semantic token, recipe, or pattern.
4. Add new styling only where the existing system cannot express the change.
5. Run `panda codegen` after config-level changes.
6. Run `panda analyze` when deciding whether a token or recipe already exists in use.
7. Keep responsive and state styles explicit.

## Rules

- Use semantic tokens instead of raw color values.
- Prefer existing recipes and patterns before inventing new styling structures.
- Write direct `class={css({...})}` at the use site in Svelte files.
- Avoid wrapper helpers that only forward styling objects.
- Use specific transitions such as `transition-colors` or `transition-opacity`.
- Regenerate the generated Panda output after token, recipe, pattern, or config edits.
- Inspect Panda config and generated output when you need exact names or want to avoid drifting from the design system.
- Use usage reports to confirm whether a recipe or token already exists before adding new variants.

## Output

Report which tokens, semantic tokens, recipes, patterns, or generated outputs were reused or regenerated so later edits stay consistent.
