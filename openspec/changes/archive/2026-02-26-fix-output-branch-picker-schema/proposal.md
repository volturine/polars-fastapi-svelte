## Why

Recent pipeline schema changes removed two key UI behaviors: creating a new branch from the output datasource branch picker and loading schema when creating derived analysis tabs. This blocks expected workflow for output configuration and prevents adding nodes when schema is missing.

## What Changes

- Restore branch creation prompt in the output datasource branch picker.
- Ensure derived analysis tabs load schema and populate nodes so step configs work.
- Add regression coverage for branch picker create flow and derived tab schema loading.

## Capabilities

### New Capabilities
- `pipeline-output-branch-picker`: Allow creating a new branch from the output datasource branch picker.
- `derived-analysis-schema-load`: Ensure derived analysis tabs load schema and populate nodes on creation.

### Modified Capabilities
- `pipeline-compute-schema`: Require schema population when derived tabs are created so node configs can resolve columns.

## Impact

- Frontend pipeline components (OutputNode, BranchPicker) and analysis tab creation flow.
- Backend schema/compute unaffected unless frontend payloads need updates.
- Tests: frontend checks and any relevant integration or store tests.
