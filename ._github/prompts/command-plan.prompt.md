---
name: "Command: Plan"
description: "Create an implementation plan before coding"
---

Before writing any code, create a comprehensive implementation plan.

Follow `AGENTS.md` and `STYLE_GUIDE.md`.

## Steps

1. Understand the requirement: summarize what needs to be built.
2. Research existing code: find relevant files and patterns.
3. Identify changes needed: list files to create/modify.
4. Define the approach: describe the technical approach.
5. List potential risks: note edge cases and concerns.

## Output Format

### Summary

1-2 sentences describing what will be built.

### Files to Modify/Create

- List each file with a brief description of changes.

### Implementation Steps

1. Step-by-step order of implementation.
2. Each step should be small and testable.

### Testing Strategy

- How to verify the implementation works.

### Risks & Considerations

- Edge cases to handle.
- Potential breaking changes.
- Performance concerns.

---

Do not write code yet. Wait for approval of the plan.
After approval, run `vibe_check` before coding.
