---
name: "Command: Review"
description: "Review code for correctness and quality"
---

Review the following code or changes for:

1. Correctness: logic errors, edge cases, potential bugs.
2. Best practices: following project conventions (see `AGENTS.md` and `STYLE_GUIDE.md`).
3. Security: potential vulnerabilities.
4. Performance: obvious inefficiencies.
5. Maintainability: readability and complexity.

## Project-Specific Checks

### Frontend (Svelte)

- Using Svelte 5 runes (`$state`, `$derived`, `$props`, `$effect`).
- No legacy syntax (`export let`, `$:`, `onMount`).
- Proper TypeScript types.

### Backend (Python)

- Async/await for database operations.
- RORO pattern (Pydantic in/out).
- Type hints everywhere.

## Response Format

### Assessment

Agree / Partially Agree / Disagree with the approach.

### Strengths

What's good about the code.

### Issues Found

- Severity (High/Medium/Low).
- Location (file:line).
- Description.
- Suggested fix.

### Recommendations

Improvements or alternatives.

---

Code to review:
$ARGUMENTS
