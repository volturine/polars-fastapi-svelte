# Operations

This skill is grounded in Panda CSS docs and CLI workflows.

Primary Panda concepts:

- `theme.extend.tokens`
- `theme.extend.semanticTokens`
- `theme.extend.recipes`
- generated patterns
- custom `conditions`
- generated `styled-system` output
- CLI usage analysis

Wrapper scripts in this skill:

- `scripts/check_panda_cli.sh`: verify Panda config exists and `panda --help` / `panda codegen --help` run successfully
- `scripts/codegen.sh`: run `panda codegen` with optional caller-provided flags in the target workdir
- `scripts/analyze.sh`: run `panda analyze` with optional caller-provided flags in the target workdir
