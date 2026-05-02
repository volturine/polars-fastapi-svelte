# Operations

This skill stands in for a remote Playwright MCP server.

Primary operations to mirror:

- `navigate`: open a page or route
- `snapshot`: inspect the accessibility tree
- `take_screenshot`: capture evidence
- `console_messages`: inspect browser console output
- `network_requests`: inspect request traffic
- `click`, `hover`, `drag`, `press_key`: drive interactions
- `type`, `fill_form`, `select_option`: populate inputs
- `file_upload`, `drop`: handle files and drag-drop flows
- `evaluate`, `run_code`: execute targeted browser logic
- `tabs`, `resize`, `wait_for`, `handle_dialog`, `close`: manage browser state

Wrapper scripts in this skill:

- `scripts/up.sh`: start a Playwright MCP server through a caller-provided compose file and wait for readiness
- `scripts/down.sh`: stop a Playwright MCP server through a caller-provided compose file
- `scripts/check_playwright_mcp.py`: send a real MCP `initialize` request and require `200 OK`
