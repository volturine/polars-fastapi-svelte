---
name: review
description: Review code or diffs for correctness, security, performance, maintainability, and project conventions. Use when asked to review code, changes, or provide QA feedback.
---

# Review

Review changes with findings first.

## Project-Specific Checks

- Read relevant `AGENTS.md` files before reviewing
- Apply language- and framework-specific conventions from the repo
- If no project-specific conventions are found, review against general best practices

## Response Format

Lead with concrete findings ordered by severity.

For each finding, use this exact format:

- Severity: High|Medium|Low; Location: file:line; Issue: <clear bug, risk, regression, or missing test>; Fix: <specific fix>

After findings, include only these optional sections when useful:

1. Open questions or assumptions
2. Brief change summary
3. Residual risks or testing gaps

If no findings are discovered, say that explicitly and mention any residual risk or missing verification.

## Review Priorities

1. Correctness and regressions
2. Security and data safety
3. Missing tests for changed behavior
4. Performance issues that matter at the changed scale
5. Maintainability and convention drift
