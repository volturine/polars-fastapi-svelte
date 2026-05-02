---
name: playwright
description: Playwright-style browser automation and UI debugging workflow. Use when Claude would otherwise reach for a Playwright MCP server to navigate pages, click controls, fill forms, inspect accessibility trees, capture screenshots, inspect console or network activity, or reproduce frontend issues in a real browser session.
---

# Playwright

Use browser interaction as a structured tool surface, not merely as a testing concept.

Prefer the smallest flow that proves the bug or behavior.

## Runtime Inputs

- MCP server URL, for example `http://127.0.0.1:8931/mcp`
- Working directory where the server is managed
- Optional compose file or launch command if wrappers need to start or stop the server

## Automation

- Health check: `python3 <skill-dir>/scripts/check_playwright_mcp.py <server-url>`
- Wrapper start: `bash <skill-dir>/scripts/up.sh <workdir> <compose-file> <server-url>`
- Wrapper stop: `bash <skill-dir>/scripts/down.sh <workdir> <compose-file>`

Read `references/operations.md` for the complete operation map.

When using the server manually, treat only a real MCP `initialize` exchange returning `200 OK`, `text/event-stream`, and an `mcp-session-id` header as a passing health check.

## Workflow

1. Start from the exact route or page state the user cares about.
2. Navigate first, then inspect the rendered page before taking action.
3. Interact with the page in small steps: click, type, select, drag, upload, tab, confirm dialogs.
4. Read supporting browser signals when needed: accessibility snapshot, screenshot, console messages, network requests.
5. Only script a longer flow after the manual sequence is understood.

## Capabilities

- Navigate to local pages and wait for stable rendering.
- Click buttons, links, tabs, menus, toggles, and dialogs.
- Fill textboxes, comboboxes, radios, checkboxes, and file inputs.
- Read accessibility structure when selectors are unclear.
- Capture screenshots and console or network evidence for debugging.
- Open multiple tabs only when the flow truly needs them.

## Rules

- Follow the target project's preferred e2e command instead of assuming raw Playwright CLI use is allowed.
- Target current UI semantics instead of old panel names or DOM positions.

## Output

Report the exact page flow executed, the evidence gathered, and the minimal interaction sequence needed to reproduce or validate the behavior.
