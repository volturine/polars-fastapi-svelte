---
name: "Command: RMSlop"
description: "Remove AI-generated code slop"
---

Check the diff against dev, and remove all AI-generated slop introduced in this branch.

This includes:

- Extra comments that a human wouldn't add or are inconsistent with the file.
- Extra defensive checks or try/catch blocks that are abnormal for that area of the codebase.
- Casts to any to get around type issues.
- Any other style inconsistent with the file.
- Unnecessary emoji usage.

Report at the end with only a 1-3 sentence summary of what you changed.
