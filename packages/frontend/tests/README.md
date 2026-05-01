# Playwright Browser-Integration Scope

These tests are not the pure e2e suite.

They are browser-driven integration tests that still use API seed helpers in [utils/api.ts](utils/api.ts) to create or prepare state before the browser assertions run.

Implications:

- They are useful for broad browser coverage and fast scenario setup.
- They must not be presented as true end-to-end user-flow coverage.
- Pure user-driven coverage lives in `packages/frontend/tests-e2e/` and is what `just test-e2e` runs.

Naming:

- `bun run test:e2e` runs the pure user-driven suite.
- `bun run test:browser-integration` runs this API-seeded browser-integration suite.
