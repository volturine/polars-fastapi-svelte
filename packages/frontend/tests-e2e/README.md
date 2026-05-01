# Playwright Pure E2E Scope

These tests are the true end-to-end suite.

Rules:

- No API seeding for auth, setup, or teardown.
- Resources are created through visible browser flows.
- Cleanup uses visible UI actions only.
- `just test-e2e` runs this suite.

This suite intentionally focuses on user-driven coverage. There is no API-seeded Playwright suite in this repository.
