# Playwright Pure E2E Scope

These tests are the true end-to-end suite.

Rules:

- No API seeding for auth, setup, or teardown.
- Resources are created through visible browser flows.
- Cleanup uses visible UI actions only.
- `just test-e2e` runs this suite.

This suite intentionally focuses on user-driven coverage. API-seeded browser tests belong in the separate browser-integration suite under `packages/frontend/tests/`.
